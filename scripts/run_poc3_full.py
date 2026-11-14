"""End-to-end POC #3 pipeline: Blender 3D multi-world + transparent Glass HUD + warm Hindi audio."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compositor.hybrid_overlay import assemble_hybrid_short, render_hud_frames


def main() -> None:
    t0 = time.time()
    manifest_path = ROOT / "build" / "poc3_audio" / "audio_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    fps = 24
    samples = 16
    total_frames = max(24, int(math.ceil((manifest["total_ms"] / 1000.0) * fps)))

    bg_dir = ROOT / "build" / "poc3_3d_frames"
    hud_dir = ROOT / "build" / "poc3_hud_frames"
    for d in (bg_dir, hud_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] Rendering {total_frames} Blender 3D frames ({fps}fps, {samples} samples)...", flush=True)
    subprocess.run(
        [
            "/opt/homebrew/bin/blender",
            "-b",
            "-P",
            str(ROOT / "scenes" / "upi_tapri_3d.py"),
            "--",
            str(manifest_path),
            str(bg_dir),
            "1080",
            "1920",
            str(fps),
            str(samples),
            "anim",
        ],
        check=True,
    )
    print(f"BLENDER_DONE elapsed={time.time() - t0:.1f}s", flush=True)

    print(f"[2/3] Rendering {total_frames} transparent Glass HUD frames...", flush=True)
    t1 = time.time()
    render_hud_frames(ROOT / "scenes" / "upi_tapri_hud.html", manifest_path, hud_dir, total_frames, fps=fps)
    print(f"HUD_DONE elapsed={time.time() - t1:.1f}s", flush=True)

    print("[3/3] Compositing Blender 3D + Glass HUD + -14 LUFS Hindi Audio...", flush=True)
    out_mp4 = ROOT / "output" / "poc3_chai_tapri_upi_800ms.mp4"
    assemble_hybrid_short(
        bg_frames_pattern=str(bg_dir / "frame_%04d.png"),
        hud_frames_pattern=str(hud_dir / "hud_%04d.png"),
        fps=fps,
        narration_wav=Path(manifest["narration_wav"]),
        sfx_wav=Path(manifest["sfx_wav"]),
        out_mp4=out_mp4,
    )
    print(f"POC3_DONE out={out_mp4} total_elapsed={time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
