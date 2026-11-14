"""Deterministic HTML5/CSS3D/Canvas documentary frame renderer via Playwright + Brave."""

from __future__ import annotations

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"


def _launch_and_prepare(p, html_path: Path, manifest: dict):
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
            for (const img of document.images) {
                if (!img.complete) await new Promise(r => { img.onload = r; img.onerror = r; });
            }
            window.initDoc(m);
        }""",
        manifest,
    )
    return browser, page


def render_spot_checks(
    html_path: Path,
    manifest_path: Path,
    out_dir: Path,
    timestamps_ms: list[int],
) -> list[Path]:
    """Render specific millisecond timestamps for quick visual inspection."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    with sync_playwright() as p:
        browser, page = _launch_and_prepare(p, html_path, manifest)
        try:
            for t_ms in timestamps_ms:
                out_png = out_dir / f"spot_{t_ms:05d}ms.png"
                page.evaluate("(ms) => window.seekToMs(ms)", t_ms)
                page.screenshot(path=str(out_png), type="png")
                outputs.append(out_png)
        finally:
            browser.close()
    return outputs


def render_all_frames(
    html_path: Path,
    manifest_path: Path,
    frames_dir: Path,
    fps: int = 30,
) -> int:
    """Render every frame at exact FPS synced to audio_manifest.json."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    total_ms = int(manifest["total_ms"])
    total_frames = max(1, int(round((total_ms / 1000.0) * fps)))
    frames_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser, page = _launch_and_prepare(p, html_path, manifest)
        try:
            for idx in range(total_frames):
                t_ms = int(round((idx * 1000.0) / fps))
                out_png = frames_dir / f"frame_{idx:05d}.png"
                page.evaluate("(ms) => window.seekToMs(ms)", t_ms)
                page.screenshot(path=str(out_png), type="png")
                if idx % 150 == 0:
                    print(f"RENDERED {idx}/{total_frames} frames ({t_ms}ms)", flush=True)
        finally:
            browser.close()
    return total_frames
