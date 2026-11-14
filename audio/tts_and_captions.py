"""Generate beat-aligned narration audio and word-level ASS kinetic captions."""

from __future__ import annotations

import asyncio
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import edge_tts


@dataclass
class WordCue:
    text: str
    start_ms: int
    end_ms: int


@dataclass
class BeatAudioResult:
    beat_id: str
    audio_path: str
    start_ms: int
    end_ms: int
    duration_ms: int
    words: list[WordCue]


def _probe_duration_ms(media_path: Path) -> int:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return int(round(float(out) * 1000))


async def _synthesize_one(
    text: str,
    out_mp3: Path,
    voice: str,
    rate: str,
    pitch: str,
) -> tuple[int, list[WordCue]]:
    comm = edge_tts.Communicate(
        text, voice=voice, rate=rate, pitch=pitch, boundary="WordBoundary"
    )
    cues: list[WordCue] = []
    with open(out_mp3, "wb") as fp:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                fp.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start_ms = int(chunk["offset"] // 10_000)
                dur_ms = int(chunk["duration"] // 10_000)
                cues.append(
                    WordCue(
                        text=chunk["text"].strip(),
                        start_ms=start_ms,
                        end_ms=start_ms + max(dur_ms, 80),
                    )
                )
    dur_ms = _probe_duration_ms(out_mp3)
    return dur_ms, cues


def _fmt_ass_time(ms: int) -> str:
    ms = max(0, ms)
    cs = (ms % 1000) // 10
    sec_total = ms // 1000
    s = sec_total % 60
    m = (sec_total // 60) % 60
    h = sec_total // 3600
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _escape_ass(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def build_kinetic_ass(
    words: Iterable[WordCue],
    out_ass: Path,
    play_res_x: int = 1080,
    play_res_y: int = 1920,
    font_name: str = "Arial Rounded Bold",
) -> Path:
    """Create punchy 2-3 word kinetic captions with active-word highlight."""
    word_list = [w for w in words if w.text]
    groups: list[list[WordCue]] = []
    cur: list[WordCue] = []
    for w in word_list:
        cur.append(w)
        ends_sentence = w.text.endswith((".", "!", "?", ",", "—", ":"))
        char_count = sum(len(x.text) for x in cur)
        if len(cur) >= 3 or char_count >= 18 or (ends_sentence and len(cur) >= 2):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kinetic,{font_name},74,&H00FFFFFF,&H0000FFFF,&H00120E0A,&HB0000000,-1,0,0,0,100,100,1,0,1,6,2,2,80,80,340,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for g_idx, group in enumerate(groups):
        next_group_start = (
            groups[g_idx + 1][0].start_ms if g_idx + 1 < len(groups) else group[-1].end_ms + 250
        )
        for active_idx, active_word in enumerate(group):
            seg_start = active_word.start_ms
            if active_idx + 1 < len(group):
                seg_end = group[active_idx + 1].start_ms
            else:
                seg_end = min(active_word.end_ms + 160, next_group_start)
            if seg_end <= seg_start:
                seg_end = seg_start + 90

            rendered_tokens = []
            for idx, w in enumerate(group):
                tok = _escape_ass(w.text)
                if idx == active_idx:
                    # Highlighted active word in crisp Electric Cyan / Gold pop
                    rendered_tokens.append(r"{\c&H00FFE600&\fscx110\fscy110}" + tok + r"{\r}")
                else:
                    rendered_tokens.append(tok)
            text_line = " ".join(rendered_tokens)
            lines.append(
                f"Dialogue: 0,{_fmt_ass_time(seg_start)},{_fmt_ass_time(seg_end)},Kinetic,,0,0,0,,{text_line}\n"
            )

    out_ass.write_text("".join(lines), encoding="utf-8")
    return out_ass


async def synthesize_beats(
    beats: list[dict],
    work_dir: Path,
    voice: str = "en-US-AndrewMultilingualNeural",
    rate: str = "+6%",
    pitch: str = "+0Hz",
    gap_ms: int = 320,
) -> dict:
    """Synthesize each beat, concatenate cleanly, and export timing manifest."""
    work_dir.mkdir(parents=True, exist_ok=True)
    results: list[BeatAudioResult] = []
    all_words: list[WordCue] = []
    cursor_ms = 250  # brief dramatic lead-in

    concat_inputs: list[tuple[Path, int]] = []
    for i, beat in enumerate(beats):
        beat_id = beat["id"]
        beat_mp3 = work_dir / f"beat_{i:02d}_{beat_id}.mp3"
        dur_ms, cues = await _synthesize_one(
            beat["narration"], beat_mp3, voice=voice, rate=rate, pitch=pitch
        )
        shifted_cues = [
            WordCue(
                text=c.text,
                start_ms=c.start_ms + cursor_ms,
                end_ms=c.end_ms + cursor_ms,
            )
            for c in cues
        ]
        all_words.extend(shifted_cues)
        results.append(
            BeatAudioResult(
                beat_id=beat_id,
                audio_path=str(beat_mp3),
                start_ms=cursor_ms,
                end_ms=cursor_ms + dur_ms,
                duration_ms=dur_ms,
                words=shifted_cues,
            )
        )
        concat_inputs.append((beat_mp3, cursor_ms))
        cursor_ms += dur_ms + gap_ms
        await asyncio.sleep(0.15)

    total_ms = cursor_ms + 450
    narration_wav = work_dir / "narration_full.wav"

    # Mix each beat at its exact millisecond offset so visual & audio stay 100% locked
    cmd = ["ffmpeg", "-y"]
    filter_parts = []
    mix_labels = []
    for idx, (mp3_path, delay_ms) in enumerate(concat_inputs):
        cmd.extend(["-i", str(mp3_path)])
        lbl = f"a{idx}"
        filter_parts.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms},aresample=48000[{lbl}]")
        mix_labels.append(f"[{lbl}]")

    filter_parts.append(
        f"{''.join(mix_labels)}amix=inputs={len(concat_inputs)}:duration=longest:normalize=0,apad=pad_dur=0.6[out]"
    )
    cmd.extend(
        [
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "[out]",
            "-t",
            f"{total_ms / 1000:.3f}",
            str(narration_wav),
        ]
    )
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ass_path = work_dir / "captions.ass"
    build_kinetic_ass(all_words, ass_path)

    manifest = {
        "voice": voice,
        "total_ms": total_ms,
        "narration_wav": str(narration_wav),
        "ass_path": str(ass_path),
        "beats": [
            {
                **{k: v for k, v in asdict(r).items() if k != "words"},
                "word_count": len(r.words),
            }
            for r in results
        ],
    }
    manifest_path = work_dir / "audio_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
