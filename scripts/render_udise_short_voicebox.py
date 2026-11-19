"""Render UDISE+ YouTube Short (1080x1920) using Voicebox Chatterbox human-cloned Hindi voice."""

from __future__ import annotations

import json
import math
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio.sfx_gen import generate_sfx_bed
from audio.tts_and_captions import _probe_duration_ms
from compositor.hybrid_overlay import render_hud_frames

VB_DB = Path.home() / "Library" / "Application Support" / "sh.voicebox.app" / "voicebox.db"
VB_GEN_DIR = Path.home() / "Library" / "Application Support" / "sh.voicebox.app" / "generations"
PROFILE_ID = "555e2132-b157-464d-8967-cf569e6e35af"  # Notebook LLM hindi

INPUT_MOV = ROOT / "input" / "udise+ automation GP, PEN search , Udise Import.mov"
HUD_HTML = ROOT / "scenes" / "udise_short_hud.html"
OUT_MP4 = ROOT / "output" / "udise_automation_yt_short_1080x1920.mp4"
WORK_DIR = ROOT / "build" / "udise_edit" / "yt_short_vb"

BEATS = [
    {
        "id": "hook",
        "src_start": 904.0,
        "cached_gid": "6e58d5d1-b4ac-4459-93bf-e39afc4b09bf",
        "text": "आज हम देखेंगे कैसे 724 छात्रों का यूडाइस जनरल प्रोफ़ाइल सिर्फ़ 30 मिनट में अपडेट कर सकते हैं, बिना पायथन इंस्टॉल किए।",
        "display_words": "आज हम देखेंगे कैसे 724 छात्रों का यू-डाइस जनरल प्रोफ़ाइल सिर्फ़ 30 मिनट में अपडेट कर सकते हैं बिना पायथन इंस्टॉल किए",
    },
    {
        "id": "colab",
        "src_start": 295.0,
        "cached_gid": "2478457c-b8b5-454e-a9f4-eba27852ed08",
        "text": "यह पूरा ऑटोमेशन गूगल कोलैब पर फ्री में चलता है, इसलिए विंडोज़ या मैक में कोई सॉफ्टवेयर एरर नहीं आता।",
        "display_words": "यह पूरा ऑटोमेशन गूगल कोलैब पर फ्री में चलता है इसलिए विंडोज़ या मैक में कोई एरर नहीं आता",
    },
    {
        "id": "safe_auth",
        "src_start": 488.0,
        "cached_gid": "34276855-11f6-4b5a-91b8-56cdeb00b23d",
        "text": "इसमें कोई आईडी या पासवर्ड नहीं देना होता, बस ब्राउज़र से अस्थायी सेशन कुकी और स्कूल लिंक पेस्ट करना है।",
        "display_words": "इसमें कोई पासवर्ड नहीं देना होता बस ब्राउज़र से सेशन कुकी और स्कूल लिंक पेस्ट करना है",
    },
    {
        "id": "three_in_one",
        "src_start": 714.0,
        "cached_gid": "10fb42c0-96f1-4485-a7a2-eeb00af91f3e",
        "text": "एक ही टूल से आधार पेन सर्च, ऑटो एलिजिबिलिटी स्टूडेंट इम्पोर्ट, और जनरल प्रोफ़ाइल बल्क अपडेट तीनों काम हो जाते हैं।",
        "display_words": "एक ही टूल से आधार पेन सर्च बल्क स्टूडेंट इम्पोर्ट और जनरल प्रोफ़ाइल अपडेट तीनों काम होते हैं",
    },
    {
        "id": "cta",
        "src_start": 144.0,
        "cached_gid": "0e6e9241-2305-4c48-bb61-55512d3cd83c",
        "text": "पूरा ट्यूटोरियल और फ्री कोलैब लिंक चैनल और टेलीग्राम ग्रुप में है, अभी जाकर ज़रूर देखें।",
        "display_words": "पूरा ट्यूटोरियल और फ्री कोलैब लिंक चैनल व टेलीग्राम ग्रुप में है अभी ज़रूर देखें",
    },
]


def vb_generate_or_reuse(beat: dict, out_wav: Path) -> int:
    gid = beat.get("cached_gid")
    raw_wav = (VB_GEN_DIR / f"{gid}.wav") if gid else None

    if raw_wav is None or not raw_wav.exists():
        req = urllib.request.Request(
            "http://127.0.0.1:17493/generate",
            data=json.dumps({
                "profile_id": PROFILE_ID,
                "text": beat["text"],
                "language": "hi",
                "engine": "chatterbox",
                "normalize": True,
                "max_chunk_chars": 240,
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            res = json.loads(r.read())
        gid = res["id"]
        print(f"  [{beat['id']}] queued Voicebox gid={gid}...", flush=True)
        for _ in range(180):
            conn = sqlite3.connect(str(VB_DB))
            row = conn.execute("SELECT status, audio_path FROM generations WHERE id=?", (gid,)).fetchone()
            conn.close()
            if row and row[0] == "completed":
                raw_wav = VB_GEN_DIR / f"{gid}.wav"
                break
            if row and row[0] == "failed":
                raise RuntimeError(f"Voicebox failed for {beat['id']}")
            time.sleep(2)

    assert raw_wav is not None and raw_wav.exists(), f"Missing {raw_wav}"
    # Trim trailing glitch/puff (~0.45s end trim via silenceremove + tiny clean fadeout)
    raw_ms = _probe_duration_ms(raw_wav)
    safe_trim_s = max(1.0, (raw_ms - 450) / 1000.0) if raw_ms > 2000 else raw_ms / 1000.0
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw_wav),
            "-af", f"atrim=0:{safe_trim_s:.3f},asetpts=PTS-STARTPTS,highpass=f=75,afade=t=out:st={max(0, safe_trim_s-0.06):.3f}:d=0.06",
            "-ar", "48000", "-ac", "1",
            str(out_wav),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return _probe_duration_ms(out_wav)


def cut_vertical_clip(src_start: float, dur_s: float, out_clip: Path, blur_cookie: bool = False) -> None:
    if blur_cookie:
        fg_blur = (
            "[fg]split[m][b1];"
            "[b1]crop=345:138:675:742,avgblur=sizeX=14:sizeY=10[bl1];"
            "[m][bl1]overlay=675:742,split[m2][b2];"
            "[b2]crop=305:62:1135:258,avgblur=sizeX=14:sizeY=10[bl2];"
            "[m2][bl2]overlay=1135:258,"
        )
    else:
        fg_blur = "[fg]"
    vf = (
        "split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=26,eq=brightness=-0.22:saturation=0.85[bg2];"
        f"{fg_blur}crop=1600:900:160:30,scale=1020:608:flags=lanczos[fg2];"
        "[bg2][fg2]overlay=30:536,fps=30,format=yuv420p"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-ss", f"{src_start:.2f}", "-t", f"{dur_s:.3f}",
            "-i", str(INPUT_MOV), "-an", "-vf", vf,
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
    for d in (audio_dir, clips_dir, hud_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    print("[1/4] Synthesizing Voicebox human-cloned Hindi narration...", flush=True)
    cursor_ms = 220
    gap_ms = 220
    beat_results = []
    all_words = []
    concat_inputs = []

    for idx, b in enumerate(BEATS):
        wav = audio_dir / f"vb_{idx:02d}_{b['id']}.wav"
        dur_ms = vb_generate_or_reuse(b, wav)
        words = b["display_words"].split()
        # Proportional word timestamps across actual spoken audio span
        span_ms = max(400, dur_ms - 180)
        total_chars = max(1, sum(len(w) for w in words))
        w_cursor = cursor_ms + 80
        for w in words:
            w_dur = int(round(span_ms * (len(w) / total_chars)))
            all_words.append({"text": w, "start_ms": w_cursor, "end_ms": w_cursor + max(80, w_dur)})
            w_cursor += w_dur
        beat_results.append({
            "beat_id": b["id"], "audio_path": str(wav),
            "start_ms": cursor_ms, "end_ms": cursor_ms + dur_ms, "duration_ms": dur_ms, "word_count": len(words),
        })
        concat_inputs.append((wav, cursor_ms))
        cursor_ms += dur_ms + gap_ms
        print(f"  vb_{idx:02d} READY: {dur_ms/1000:.2f}s", flush=True)

    total_ms = cursor_ms + 300
    narration_wav = audio_dir / "narration_full.wav"
    cmd = ["ffmpeg", "-y"]
    fparts, labels = [], []
    for i, (wp, dms) in enumerate(concat_inputs):
        cmd.extend(["-i", str(wp)])
        fparts.append(f"[{i}:a]adelay={dms}|{dms},aresample=48000[a{i}]")
        labels.append(f"[a{i}]")
    fparts.append(f"{''.join(labels)}amix=inputs={len(concat_inputs)}:duration=longest:normalize=0,apad=pad_dur=0.5[out]")
    cmd.extend(["-filter_complex", ";".join(fparts), "-map", "[out]", "-t", f"{total_ms/1000:.3f}", str(narration_wav)])
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    sfx_wav = audio_dir / "sfx_bed.wav"
    generate_sfx_bed(total_ms, [b["start_ms"] for b in beat_results], [(b["start_ms"] + 100, 720.0 + idx * 100.0) for idx, b in enumerate(beat_results)], sfx_wav)

    manifest = {"voice": "voicebox-chatterbox-NotebookLLM-hi", "total_ms": total_ms, "narration_wav": str(narration_wav), "sfx_wav": str(sfx_wav), "words": all_words, "beats": beat_results}
    manifest_path = audio_dir / "audio_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    fps = 30
    total_frames = max(30, int(math.ceil((total_ms / 1000.0) * fps)))
    print(f"[2/4] Cutting real screen clips ({total_ms/1000:.2f}s, {total_frames} frames)...", flush=True)
    clines = []
    for idx, (cfg, bm) in enumerate(zip(BEATS, beat_results)):
        next_st = beat_results[idx + 1]["start_ms"] if idx + 1 < len(beat_results) else total_ms
        st_ms = 0 if idx == 0 else bm["start_ms"]
        cp = clips_dir / f"clip_{idx:02d}.mp4"
        cut_vertical_clip(cfg["src_start"], max(1.0, (next_st - st_ms) / 1000.0), cp, blur_cookie=(cfg["id"] == "safe_auth"))
        clines.append(f"file '{cp.resolve()}'")
    ctxt = clips_dir / "concat.txt"
    ctxt.write_text("\n".join(clines), encoding="utf-8")
    bg_vid = WORK_DIR / "short_bg.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(ctxt), "-c", "copy", str(bg_vid)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[3/4] Rendering HUD frames...", flush=True)
    render_hud_frames(HUD_HTML, manifest_path, hud_dir, total_frames, fps=fps)

    print("[4/4] Final mux (-14 LUFS)...", flush=True)
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    fc = "[0:v][1:v]overlay=0:0:shortest=1,format=yuv420p[vout];[2:a]aresample=48000,highpass=f=75,acompressor=threshold=-16dB:ratio=2.8:attack=5:release=60[nar];[3:a]aresample=48000[sfx];[nar][sfx]amix=inputs=2:duration=first:dropout_transition=0:weights=1.0 0.55,loudnorm=I=-14:TP=-1.5:LRA=9[aout]"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(bg_vid), "-framerate", str(fps), "-i", str(hud_dir / "hud_%04d.png"), "-i", str(narration_wav), "-i", str(sfx_wav),
         "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(OUT_MP4)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    print(f"YT_SHORT_VB_DONE: {OUT_MP4} ({OUT_MP4.stat().st_size/(1024*1024):.1f} MB, elapsed={time.time()-t0:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
