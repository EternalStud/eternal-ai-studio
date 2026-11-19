"""Produce the tight, mobile-readable (~10 min) 1920x1080 YouTube Master Edit from the raw 17m11s MOV.

Preserves the creator's REAL human voice (cleaned with noise reduction, warm broadcast EQ,
compression, and -14 LUFS normalization), moves the 724-students proof hook to 00:00,
removes dead PDF/RAM/login-fail/Inspect-fumble segments, zooms out black pillars & menu bars,
adds Gaussian privacy blur over live JSESSIONID/UDISE/EncryptKey strings, and overlays crisp
lower-third chapter & Telegram banners.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_MOV = ROOT / "input" / "udise+ automation GP, PEN search , Udise Import.mov"
OUT_MP4 = ROOT / "output" / "udise_automation_master_edited.mp4"
WORK_DIR = ROOT / "build" / "udise_edit" / "pro_master"

# Clean chronological segments (t_start, t_end, label, zoom_mode, blur_preset)
# Cuts out: 16.5-142.5 (static PDF ramble + giant Telegram text), 219.5-262.0 (GPU/RAM/disk monologue),
#           422.5-441.5 (failed login stumble), 659.5-665.8 (right-click 'sorry' fumble),
#           920.8-942.0 (moved to hook), 998.0-1031.6 (repetitive summer-vacation sign-off).
SEGMENTS = [
    (903.8, 920.8, "HOOK: 724 Students Updated in Just 30 Mins!", "colab_crop", "none"),
    (0.8, 16.5, "Intro: UDISE+ Bulk Automation Overview", "pdf_crop", "none"),
    (142.5, 175.0, "Only 3 Browser Inputs Needed + Free PDF Guide", "pdf_crop", "none"),
    (197.0, 219.5, "Step 1: Open Colab & Click Connect", "fcp_full", "none"),
    (262.0, 422.5, "Step 2: Notebook Workflow & Setup Environment", "fcp_full", "none"),
    (441.5, 486.0, "Step 3: Login UDISE+ & Open Network Tab (F12)", "fcp_full", "portal_id"),
    (486.0, 540.0, "Step 3b: Copy JSESSIONID Session Cookie", "fcp_full", "cookie_zoom"),
    (540.0, 659.5, "Step 4: Detect School URL & Copy Encrypt Key", "fcp_full", "none"),
    (665.8, 710.0, "Step 5: Paste Console Code -> Auto-Copy Key", "fcp_full", "none"),
    (710.0, 745.0, "Step 6: PEN Search Upload (Aadhaar + DOB)", "colab_crop", "pen_keys"),
    (745.0, 902.5, "Step 7 & 8: Bulk Student Import & GP Update", "colab_crop", "none"),
    (942.0, 998.0, "Wrap-Up: No Coding Required & Join Telegram", "colab_crop", "none"),
]


def _filter_for_segment(idx: int, zoom_mode: str, blur_preset: str, label: str, dur_s: float) -> str:
    # Base crop removes macOS top bar & outer black pillars -> crisp 1920x1080 16:9 mobile-readable
    if zoom_mode == "colab_crop":
        # Tighter Colab notebook crop (drops side black bars, menu bar, bottom status)
        base = "crop=1660:900:130:55"
        sx, sy = 1920.0 / 1660.0, 1080.0 / 900.0
        ox, oy = 130, 55
    elif zoom_mode == "pdf_crop":
        base = "crop=1680:905:120:50"
        sx, sy = 1920.0 / 1680.0, 1080.0 / 905.0
        ox, oy = 120, 50
    else:
        # Preserve Final Cut Pro zoom cuts while removing top/bottom black frame
        base = "crop=1720:930:100:25"
        sx, sy = 1920.0 / 1720.0, 1080.0 / 930.0
        ox, oy = 100, 25

    blur_boxes_raw = []
    if blur_preset == "portal_id":
        # Full portal view: UDISE code, School Name, School ID in URL
        blur_boxes_raw = [(690, 42, 460, 40), (610, 168, 880, 52)]
    elif blur_preset == "cookie_zoom":
        # Tight cookie view: blur secret token after 'JSESSIONID=' + UDISE digits
        blur_boxes_raw = [(675, 742, 345, 138), (1165, 270, 275, 58), (1080, 0, 460, 44)]
    elif blur_preset == "pen_keys":
        blur_boxes_raw = [(210, 412, 530, 40), (740, 412, 520, 40)]

    # Build filtergraph on native 1920x960 BEFORE crop+scale so coordinates stay exact!
    parts = []
    cur = "[0:v]"
    for bi, (bx, by, bw, bh) in enumerate(blur_boxes_raw):
        parts.append(
            f"{cur}split[m{bi}][b{bi}];"
            f"[b{bi}]crop={bw}:{bh}:{bx}:{by},avgblur=sizeX=12:sizeY=8[bl{bi}];"
            f"[m{bi}][bl{bi}]overlay={bx}:{by}[v{bi}]"
        )
        cur = f"[v{bi}]"

    # Crop & scale to standard 1080p YouTube 16:9
    parts.append(f"{cur}{base},scale=1920:1080:flags=lanczos[scaled]")

    # Sleek lower-third chapter / Telegram banner during first 7s of segment
    banner_end = min(dur_s - 0.3, 7.5 if idx != 0 else dur_s - 0.2)
    safe_lbl = label.replace(":", "\\:").replace("'", "")
    parts.append(
        f"[scaled]"
        f"drawbox=x=40:y=988:w=960:h=62:color=0x090D18@0.86:t=fill:enable='between(t,0.15,{banner_end:.2f})',"
        f"drawbox=x=40:y=988:w=8:h=62:color=0xFFD447@0.95:t=fill:enable='between(t,0.15,{banner_end:.2f})',"
        f"drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:text='{safe_lbl}':"
        f"fontcolor=white:fontsize=27:x=68:y=1006:enable='between(t,0.15,{banner_end:.2f})',"
        f"drawbox=x=1470:y=994:w=410:h=50:color=0x090D18@0.82:t=fill:enable='between(t,0.15,{dur_s-0.1:.2f})',"
        f"drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:text='Telegram\\: Eternal Student':"
        f"fontcolor=0xFFD447:fontsize=22:x=1510:y=1008:enable='between(t,0.15,{dur_s-0.1:.2f})',"
        f"format=yuv420p[vout]"
    )
    return ";".join(parts)


def main() -> None:
    t0 = time.time()
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    seg_files: list[Path] = []

    audio_polish = (
        "highpass=f=85,lowpass=f=12500,afftdn=nf=-24,"
        "equalizer=f=175:width_type=o:width=1.2:g=2.5,"
        "equalizer=f=2800:width_type=o:width=1.4:g=3.2,"
        "acompressor=threshold=-18dB:ratio=3.0:attack=5:release=65,"
        "afade=t=in:st=0:d=0.05"
    )

    total_kept_s = sum(e - s for s, e, *_ in SEGMENTS)
    print(f"Rendering {len(SEGMENTS)} edited segments -> target ~{total_kept_s/60:.1f} min (from 17.2 min)...", flush=True)

    for idx, (st, en, label, zmode, bpreset) in enumerate(SEGMENTS):
        dur_s = en - st
        seg_mp4 = WORK_DIR / f"seg_{idx:02d}.mp4"
        if seg_mp4.exists() and seg_mp4.stat().st_size > 100_000 and idx >= 1:
            seg_files.append(seg_mp4)
            print(f"  seg_{idx:02d} CACHED ({dur_s:5.1f}s) | {label}", flush=True)
            continue
        vf = _filter_for_segment(idx, zmode, bpreset, label, dur_s)
        af = f"{audio_polish},afade=t=out:st={max(0, dur_s-0.06):.2f}:d=0.06"
        fc = f"{vf};[0:a]{af}[aout]"

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", f"{st:.2f}",
                "-t", f"{dur_s:.2f}",
                "-i", str(INPUT_MOV),
                "-filter_complex", fc,
                "-map", "[vout]", "-map", "[aout]",
                "-c:v", "libx264", "-preset", "fast", "-crf", "17",
                "-r", "60",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                str(seg_mp4),
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        seg_files.append(seg_mp4)
        print(f"  seg_{idx:02d} DONE ({dur_s:5.1f}s) | {label}", flush=True)

    concat_txt = WORK_DIR / "concat.txt"
    concat_txt.write_text("\n".join(f"file '{p.resolve()}'" for p in seg_files), encoding="utf-8")

    raw_concat = WORK_DIR / "raw_concat.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(raw_concat)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    # Final loudness normalize to YouTube standard (-14 LUFS) copying video untouched
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(raw_concat),
            "-c:v", "copy",
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(OUT_MP4),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    print(f"PRO_MASTER_DONE: {OUT_MP4} ({OUT_MP4.stat().st_size/(1024*1024):.1f} MB, duration={total_kept_s/60:.2f}m, elapsed={time.time()-t0:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
