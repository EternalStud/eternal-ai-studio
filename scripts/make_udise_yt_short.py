"""Build a crisp 1080x1920 YouTube Short promo from real zoomed clips of the UDISE+ Automation MOV."""

from __future__ import annotations

import asyncio
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio.sfx_gen import generate_sfx_bed
from audio.tts_and_captions import synthesize_beats
from compositor.hybrid_overlay import render_hud_frames

INPUT_MOV = ROOT / "input" / "udise+ automation GP, PEN search , Udise Import.mov"
HUD_HTML = ROOT / "scenes" / "udise_short_hud.html"
OUT_MP4 = ROOT / "output" / "udise_automation_yt_short_1080x1920.mp4"
WORK_DIR = ROOT / "build" / "udise_edit" / "yt_short"

SHORT_BEATS = [
    {
        "id": "hook",
        "src_start": 952.0,
        "narration": "सात सौ चौबीस बच्चों का यू-डाइस प्लस जनरल प्रोफ़ाइल, मात्र तीस मिनट में अपडेट! बिना किसी कोडिंग के!",
    },
    {
        "id": "colab",
        "src_start": 295.0,
        "narration": "अब लोकल कंप्यूटर पर पायथन या सेलेनियम इंस्टॉल करने का झंझट ख़त्म। यह पूरा ऑटोमेशन सूट सीधे गूगल कोलैब पर फ्री में चलता है।",
    },
    {
        "id": "safe_auth",
        "src_start": 476.0,
        "narration": "कोई यूज़र आई-डी या पासवर्ड नहीं देना है! बस ब्राउज़र से टेम्पररी सेशन कुकी और स्कूल यू-आर-एल पेस्ट करें — सौ प्रतिशत सुरक्षित।",
    },
    {
        "id": "three_in_one",
        "src_start": 714.0,
        "narration": "एक ही टूल में तीन बड़े काम — आधार से बल्क पेन सर्च, ऑटो एलिजिबिलिटी चेक के साथ बल्क स्टूडेंट इम्पोर्ट, और प्री-फ़िल्ड एक्सेल से जनरल प्रोफ़ाइल अपडेट!",
    },
    {
        "id": "cta",
        "src_start": 12.0,
        "narration": "पूरा स्टेप-बाय-स्टेप गाइड और फ्री कोलैब लिंक फुल वीडियो और हमारे टेलीग्राम चैनल पर है। अभी चैनल पर पूरा वीडियो देखें!",
    },
]


def cut_vertical_clip(src_start: float, dur_s: float, out_clip: Path) -> None:
    """Create a 1080x1920 vertical segment: blurred ambient BG + crisp zoomed center UI window."""
    vf = (
        "split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=26,eq=brightness=-0.22:saturation=0.85[bg2];"
        "[fg]crop=1600:900:160:30,scale=1020:608:flags=lanczos[fg2];"
        "[bg2][fg2]overlay=30:536,fps=30,format=yuv420p"
    )
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", f"{src_start:.2f}",
            "-t", f"{dur_s:.3f}",
            "-i", str(INPUT_MOV),
            "-an",
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "16",
            str(out_clip),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def main() -> None:
    t0 = time.time()
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    audio_dir = WORK_DIR / "audio"
    clips_dir = WORK_DIR / "clips"
    hud_dir = WORK_DIR / "hud_frames"
    for d in (clips_dir, hud_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    print("[1/4] Synthesizing energetic Hindi Short narration + SFX...", flush=True)
    manifest = asyncio.run(
        synthesize_beats(
            SHORT_BEATS,
            work_dir=audio_dir,
            voice="hi-IN-MadhurNeural",
            rate="+16%",
            pitch="-1Hz",
            gap_ms=150,
        )
    )
    beat_starts = [b["start_ms"] for b in manifest["beats"]]
    pings = [(b["start_ms"] + 120, 740.0 + idx * 110.0) for idx, b in enumerate(manifest["beats"])]
    sfx_wav = audio_dir / "sfx_bed.wav"
    generate_sfx_bed(manifest["total_ms"], beat_starts, pings, sfx_wav)
    manifest["sfx_wav"] = str(sfx_wav)
    manifest_path = audio_dir / "audio_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    total_ms = manifest["total_ms"]
    fps = 30
    total_frames = max(30, int(math.ceil((total_ms / 1000.0) * fps)))
    print(f"SHORT_DURATION={total_ms/1000:.2f}s ({total_frames} frames @ 30fps)", flush=True)

    print("[2/4] Cutting real zoomed vertical screen clips from MOV...", flush=True)
    concat_lines = []
    for idx, (cfg, bm) in enumerate(zip(SHORT_BEATS, manifest["beats"])):
        next_start = manifest["beats"][idx + 1]["start_ms"] if idx + 1 < len(manifest["beats"]) else total_ms
        clip_start_ms = 0 if idx == 0 else bm["start_ms"]
        clip_dur_s = max(1.0, (next_start - clip_start_ms) / 1000.0)
        clip_path = clips_dir / f"clip_{idx:02d}.mp4"
        cut_vertical_clip(cfg["src_start"], clip_dur_s, clip_path)
        concat_lines.append(f"file '{clip_path.resolve()}'")

    concat_txt = clips_dir / "concat.txt"
    concat_txt.write_text("\n".join(concat_lines), encoding="utf-8")
    bg_video = WORK_DIR / "short_bg_vertical.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(bg_video)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    print(f"[3/4] Rendering {total_frames} transparent Glass HUD + Hindi caption frames...", flush=True)
    render_hud_frames(HUD_HTML, manifest_path, hud_dir, total_frames, fps=fps)

    print("[4/4] Overlaying HUD onto real screen clips + -14 LUFS mastering...", flush=True)
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    filter_complex = (
        "[0:v][1:v]overlay=0:0:shortest=1,format=yuv420p[vout];"
        "[2:a]aresample=48000,highpass=f=75,acompressor=threshold=-16dB:ratio=3:attack=5:release=60[nar];"
        "[3:a]aresample=48000[sfx];"
        "[nar][sfx]amix=inputs=2:duration=first:dropout_transition=0:weights=1.0 0.70,"
        "loudnorm=I=-14:TP=-1.5:LRA=9[aout]"
    )
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(bg_video),
            "-framerate", str(fps), "-i", str(hud_dir / "hud_%04d.png"),
            "-i", str(manifest["narration_wav"]),
            "-i", str(sfx_wav),
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "17",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest",
            str(OUT_MP4),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    print(f"YT_SHORT_DONE: {OUT_MP4} ({OUT_MP4.stat().st_size / (1024*1024):.1f} MB, elapsed={time.time()-t0:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
