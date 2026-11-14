"""End-to-end runner for POC #1: Audio + Kinetic Captions + Blender 3D + FFmpeg Master."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compositor.assemble_video import assemble_short


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("stills", "anim"), default="stills")
    parser.add_argument("--res", default="1080x1920", help="WxH resolution")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--skip-audio", action="store_true")
    args = parser.parse_args()

    res_x, res_y = (int(v) for v in args.res.lower().split("x"))
    work_dir = ROOT / "tmp" / "poc1_upi"
    frames_dir = work_dir / ("stills" if args.mode == "stills" else "frames")
    frames_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    if not args.skip_audio:
        print("[1/3] Synthesizing beat-aligned narration, SFX, and kinetic captions...")
        subprocess.run(
            [str(ROOT / ".venv/bin/python3"), str(ROOT / "scripts/generate_audio_poc1.py")],
            check=True,
        )

    manifest_path = work_dir / "audio_manifest.json"
    print(f"[2/3] Running Blender 3D render ({args.mode}, {res_x}x{res_y} @ {args.fps}fps, {args.samples} samples)...")
    subprocess.run(
        [
            "blender",
            "--background",
            "--python",
            str(ROOT / "scenes/upi_vs_banks_3d.py"),
            "--",
            str(manifest_path),
            str(frames_dir),
            str(res_x),
            str(res_y),
            str(args.fps),
            str(args.samples),
            args.mode,
        ],
        check=True,
    )

    if args.mode == "anim":
        out_mp4 = ROOT / "output" / f"poc1_upi_vs_banks_{res_x}x{res_y}.mp4"
        print(f"[3/3] Compositing audio + kinetic captions -> {out_mp4}...")
        assemble_short(
            frames_pattern=str(frames_dir / "frame_%04d.png"),
            fps=args.fps,
            narration_wav=work_dir / "narration_full.wav",
            sfx_wav=work_dir / "sfx_bed.wav",
            ass_path=work_dir / "captions.ass",
            out_mp4=out_mp4,
        )
        print(f"DONE in {time.time() - t0:.1f}s -> {out_mp4}")
    else:
        print(f"STILLS DONE in {time.time() - t0:.1f}s -> {frames_dir}")


if __name__ == "__main__":
    main()
