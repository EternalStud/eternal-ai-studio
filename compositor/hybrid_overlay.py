"""Transparent RGBA HTML HUD renderer & Blender+HUD FFmpeg overlay compositor."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"


def _prep(p, html_path: Path, manifest: dict):
    browser = p.chromium.launch(
        executable_path=BRAVE_PATH,
        headless=True,
        args=["--no-sandbox", "--disable-gpu-sandbox", "--use-gl=angle"],
    )
    page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
    page.goto(html_path.resolve().as_uri(), wait_until="load")
    page.evaluate(
        """async (m) => {
            await document.fonts.ready;
            window.initDoc(m);
        }""",
        manifest,
    )
    return browser, page


def render_hud_spot(html_path: Path, manifest_path: Path, out_dir: Path, timestamps_ms: list[int]) -> list[Path]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    outs: list[Path] = []
    with sync_playwright() as p:
        browser, page = _prep(p, html_path, manifest)
        try:
            for idx, ms in enumerate(timestamps_ms):
                out_png = out_dir / f"hud_spot_{idx:02d}.png"
                page.evaluate("(t) => window.seekToMs(t)", ms)
                page.screenshot(path=str(out_png), type="png", omit_background=True)
                outs.append(out_png)
        finally:
            browser.close()
    return outs


def render_hud_frames(html_path: Path, manifest_path: Path, hud_dir: Path, total_frames: int, fps: int = 24) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    hud_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = _prep(p, html_path, manifest)
        try:
            for idx in range(total_frames):
                # Frame numbers match Blender 1-based frame_%04d.png!
                frame_num = idx + 1
                t_ms = int(round((idx * 1000.0) / fps))
                out_png = hud_dir / f"hud_{frame_num:04d}.png"
                page.evaluate("(t) => window.seekToMs(t)", t_ms)
                page.screenshot(path=str(out_png), type="png", omit_background=True)
                if frame_num % 150 == 0:
                    print(f"HUD_RENDERED {frame_num}/{total_frames}", flush=True)
        finally:
            browser.close()
    return total_frames


def assemble_hybrid_short(
    bg_frames_pattern: str,
    hud_frames_pattern: str,
    fps: int,
    narration_wav: Path,
    sfx_wav: Path,
    out_mp4: Path,
) -> Path:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    filter_complex = (
        "[0:v][1:v]overlay=0:0:shortest=1,format=yuv420p[vout];"
        "[2:a]aresample=48000,highpass=f=75,acompressor=threshold=-16dB:ratio=3:attack=5:release=60[nar];"
        "[3:a]aresample=48000[sfx];"
        "[nar][sfx]amix=inputs=2:duration=first:dropout_transition=0:weights=1.0 0.85,"
        "loudnorm=I=-14:TP=-1.5:LRA=9[aout]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        bg_frames_pattern,
        "-framerate",
        str(fps),
        "-i",
        hud_frames_pattern,
        "-i",
        str(narration_wav),
        "-i",
        str(sfx_wav),
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-map",
        "[aout]",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "17",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        "-shortest",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    return out_mp4
