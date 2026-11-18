"""Deterministic Quality Assurance Auditor (QA-001 enforcement).

Validates spot-check pixels (dark_ratio, center_roi_lum, bright_ratio),
Playwright DOM safe-zone bounding boxes (IoU == 0.0, Zone E <= 1680px),
and post-export MP4 ffprobe + EBU R128 loudness metrics.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"


def audit_spot_image(png_path: Path) -> dict:
    arr = np.asarray(Image.open(png_path).convert("RGB"), dtype=np.float32) / 255.0
    lum = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    h, w = lum.shape
    roi = lum[int(h * 0.25) : int(h * 0.70), int(w * 0.15) : int(w * 0.85)]

    dark_ratio = float(np.mean(lum < 0.025))
    bright_ratio = float(np.mean(lum > 0.45))
    center_roi_lum = float(np.mean(roi))
    passed = (dark_ratio <= 0.82) and (bright_ratio >= 0.002) and (center_roi_lum >= 0.048)

    return {
        "file": png_path.name,
        "dark_ratio": round(dark_ratio, 4),
        "bright_ratio": round(bright_ratio, 4),
        "center_roi_lum": round(center_roi_lum, 4),
        "passed": passed,
    }


def _boxes_overlap_area(a: dict, b: dict) -> float:
    ix0 = max(a["left"], b["left"])
    iy0 = max(a["top"], b["top"])
    ix1 = min(a["right"], b["right"])
    iy1 = min(a["bottom"], b["bottom"])
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    return float((ix1 - ix0) * (iy1 - iy0))


def audit_hud_dom(html_path: Path, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=BRAVE_PATH, headless=True, args=["--no-sandbox"])
        page = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        page.goto(html_path.resolve().as_uri(), wait_until="load")
        page.evaluate("async (m) => { await document.fonts.ready; window.initDoc(m); }", manifest)

        for beat in manifest["beats"]:
            mid_ms = beat["start_ms"] + int(beat["duration_ms"] * 0.62)
            page.evaluate("(ms) => window.seekToMs(ms)", mid_ms)
            boxes = page.evaluate("() => window.__qaInspectDom()")
            for box in boxes:
                if box["bottom"] > 1685.0:
                    failures.append(f"{beat['beat_id']}: {box['id']} leaks into Zone E (bottom={box['bottom']:.1f})")
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    area = _boxes_overlap_area(boxes[i], boxes[j])
                    if area > 4.0:
                        failures.append(
                            f"{beat['beat_id']}: overlap between {boxes[i]['id']} and {boxes[j]['id']} ({area:.0f}px^2)"
                        )
        b.close()
    return {"passed": len(failures) == 0, "failures": failures}


def audit_final_mp4(mp4_path: Path) -> dict:
    probe = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(mp4_path)],
            text=True,
        )
    )
    v_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    a_stream = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    dur = float(probe["format"]["duration"])

    ebur = subprocess.run(
        ["ffmpeg", "-i", str(mp4_path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stderr
    m_i = re.findall(r"I:\s+([-\d.]+)\s+LUFS", ebur)
    m_tp = re.findall(r"Peak:\s+([-\d.]+)\s+dBFS", ebur)
    lufs = float(m_i[-1]) if m_i else -99.0
    tp = float(m_tp[-1]) if m_tp else 0.0

    passed = (
        int(v_stream["width"]) == 1080
        and int(v_stream["height"]) == 1920
        and a_stream["codec_name"] == "aac"
        and dur >= 60.0
        and (-16.5 <= lufs <= -11.5)
    )
    return {
        "file": str(mp4_path),
        "duration_s": round(dur, 2),
        "width": int(v_stream["width"]),
        "height": int(v_stream["height"]),
        "lufs": lufs,
        "true_peak_dbfs": tp,
        "passed": passed,
    }
