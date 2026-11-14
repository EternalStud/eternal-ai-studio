"""End-to-end POC #2 pipeline: HTML5/CSS3D documentary motion renderer + audio mux."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compositor.assemble_video import assemble_short
from compositor.html_motion_renderer import render_all_frames, render_spot_checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spot-only", action="store_true", help="Render 1 spot frame per beat and exit")
    args = parser.parse_args()

    html_path = ROOT / "scenes" / "knight_capital_doc.html"
    manifest_path = ROOT / "build" / "poc2_audio" / "audio_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if args.spot_only:
        spot_dir = ROOT / "build" / "poc2_spot"
        timestamps = [b["start_ms"] + int(b["duration_ms"] * 0.65) for b in manifest["beats"]]
        paths = render_spot_checks(html_path, manifest_path, spot_dir, timestamps)
        for p in paths:
            print("SPOT_PNG:", p)
        return

    t0 = time.time()
    frames_dir = ROOT / "build" / "poc2_frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    fps = 30
    total_frames = render_all_frames(html_path, manifest_path, frames_dir, fps=fps)
    t_render = time.time() - t0
    print(f"FRAME_RENDER_DONE frames={total_frames} elapsed={t_render:.1f}s")

    out_mp4 = ROOT / "output" / "poc2_knight_capital_1080x1920.mp4"
    assemble_short(
        frames_pattern=str(frames_dir / "frame_%05d.png"),
        fps=fps,
        narration_wav=Path(manifest["narration_wav"]),
        sfx_wav=Path(manifest["sfx_wav"]),
        ass_path=None,
        out_mp4=out_mp4,
    )
    print(f"POC2_DONE out={out_mp4} total_elapsed={time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
