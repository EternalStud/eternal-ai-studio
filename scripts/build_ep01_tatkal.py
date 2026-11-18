"""End-to-end Episode 01 Orchestrator: Spot-QA Gate -> Full 3D Render -> HUD + Stick Render -> Hybrid Export -> Post-QA."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compositor.hybrid_overlay import assemble_hybrid_short, render_hud_frames, render_hud_spot
from engine.qa_auditor import audit_final_mp4, audit_hud_dom, audit_spot_image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spot-only", action="store_true", help="Render 8 beat spot frames + cut check + QA audit")
    args = parser.parse_args()

    manifest_path = ROOT / "build" / "ep01_audio" / "audio_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    html_path = ROOT / "engine" / "universal_hud.html"
    scene_py = ROOT / "scenes" / "ep01_tatkal_3d.py"

    fps = 24
    samples = 16
    total_frames = max(24, int(math.ceil((manifest["total_ms"] / 1000.0) * fps)))

    if args.spot_only:
        spot_3d = ROOT / "build" / "ep01_3d_spot"
        spot_hud = ROOT / "build" / "ep01_hud_spot"
        spot_comp = ROOT / "build" / "ep01_comp_spot"
        for d in (spot_3d, spot_hud, spot_comp):
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True, exist_ok=True)

        print("[1/4] Rendering Blender 5.3 Spot Frames + Cut Boundary Check...", flush=True)
        subprocess.run(
            ["/opt/homebrew/bin/blender", "-b", "-P", str(scene_py), "--", str(manifest_path), str(spot_3d), "1080", "1920", str(fps), str(samples), "spot"],
            check=True,
        )

        print("[2/4] Auditing Universal HUD DOM Bounding Boxes...", flush=True)
        dom_qa = audit_hud_dom(html_path, manifest_path)
        print("DOM_QA:", json.dumps(dom_qa), flush=True)

        print("[3/4] Rendering Transparent HUD + Stick-Figure Spot Frames...", flush=True)
        timestamps = [b["start_ms"] + int(b["duration_ms"] * 0.62) for b in manifest["beats"]]
        hud_pngs = render_hud_spot(html_path, manifest_path, spot_hud, timestamps)

        print("[4/4] Compositing & Auditing Spot Pixels...", flush=True)
        bg_pngs = sorted(spot_3d.glob("spot3d_*.png"))
        pixel_reports = []
        for idx, (bg, hud) in enumerate(zip(bg_pngs, hud_pngs)):
            out = spot_comp / f"comp_{idx:02d}_{bg.stem}.png"
            subprocess.run(["ffmpeg", "-y", "-i", str(bg), "-i", str(hud), "-filter_complex", "[0:v][1:v]overlay=0:0", str(out)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            rep = audit_spot_image(out)
            pixel_reports.append(rep)
            print("PIXEL_QA:", json.dumps(rep), flush=True)

        all_ok = dom_qa["passed"] and all(r["passed"] for r in pixel_reports)
        (spot_comp / "qa_spot_report.json").write_text(
            json.dumps({"dom_qa": dom_qa, "pixel_reports": pixel_reports, "overall_passed": all_ok}, indent=2),
            encoding="utf-8",
        )
        print(f"SPOT_QA_OVERALL={'PASSED' if all_ok else 'FAILED'}", flush=True)
        if not all_ok:
            sys.exit(2)
        return

    # FULL PRODUCTION PIPELINE (Strict Sequential Memory Isolation on 8GB Mac Mini)
    t0 = time.time()
    bg_dir = ROOT / "build" / "ep01_3d_frames"
    hud_dir = ROOT / "build" / "ep01_hud_frames"
    for d in (bg_dir, hud_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] Rendering {total_frames} Blender 3D frames ({fps}fps, {samples} samples)...", flush=True)
    subprocess.run(
        ["/opt/homebrew/bin/blender", "-b", "-P", str(scene_py), "--", str(manifest_path), str(bg_dir), "1080", "1920", str(fps), str(samples), "anim"],
        check=True,
    )
    print(f"BLENDER_DONE elapsed={time.time() - t0:.1f}s", flush=True)

    print(f"[2/4] Rendering {total_frames} Universal HUD + Stick-Figure RGBA frames...", flush=True)
    t1 = time.time()
    render_hud_frames(html_path, manifest_path, hud_dir, total_frames, fps=fps)
    print(f"HUD_DONE elapsed={time.time() - t1:.1f}s", flush=True)

    out_mp4 = ROOT / "output" / "ep01_tatkal_concurrency_1080x1920.mp4"
    print("[3/4] Compositing Hybrid MP4 + -14 LUFS Audio...", flush=True)
    assemble_hybrid_short(
        bg_frames_pattern=str(bg_dir / "frame_%04d.png"),
        hud_frames_pattern=str(hud_dir / "hud_%04d.png"),
        fps=fps,
        narration_wav=Path(manifest["narration_wav"]),
        sfx_wav=Path(manifest["sfx_wav"]),
        out_mp4=out_mp4,
    )

    print("[4/4] Post-Export MP4 & LUFS QA Audit...", flush=True)
    post_qa = audit_final_mp4(out_mp4)
    print("POST_QA:", json.dumps(post_qa), flush=True)
    (ROOT / "build" / "ep01_post_qa.json").write_text(json.dumps(post_qa, indent=2), encoding="utf-8")
    print(f"EP01_DONE out={out_mp4} total_elapsed={time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
