"""Render ultra-crisp HTML5 screen textures for 3D Blender laptops & server racks."""

from __future__ import annotations

from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TEX_DIR = ROOT / "build" / "colab_doc" / "textures"
BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

HTML_OOM = """<!DOCTYPE html><html><body style="margin:0;width:1280px;height:800px;background:#0d0b10;color:#e5e7eb;font-family:-apple-system,ui-monospace,monospace;padding:34px;box-sizing:border-box;display:flex;flex-direction:column;gap:20px;">
<div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #3f1d24;padding-bottom:14px;">
  <div style="display:flex;gap:10px;align-items:center;"><span style="width:14px;height:14px;border-radius:50%;background:#ef4444;display:inline-block;"></span><span style="font-size:22px;font-weight:700;color:#fca5a5;">local_train.py — Terminal</span></div>
  <div style="background:#7f1d1d;color:#fecaca;padding:6px 16px;border-radius:8px;font-size:20px;font-weight:700;">RAM 7.96 / 8.00 GB (99.5%) · FAN 6840 RPM</div>
</div>
<div style="font-size:22px;line-height:1.55;color:#cbd5e1;">
  <div>$ python train_vision_model.py --batch-size 64</div>
  <div style="color:#94a3b8;">Loading pretrained weights (2.4 GB)...</div>
  <div style="color:#fbbf24;">[WARN] No NVIDIA CUDA device detected. Falling back to CPU threads.</div>
  <div style="color:#f87171;font-weight:700;margin-top:16px;">Traceback (most recent call last):</div>
  <div style="color:#fca5a5;">&nbsp;&nbsp;File "train_vision_model.py", line 84, in forward</div>
  <div style="background:#450a0a;border-left:6px solid #ef4444;padding:18px 22px;margin-top:14px;color:#fecaca;font-size:26px;font-weight:700;border-radius:6px;">
    MemoryError: Unable to allocate 3.84 GiB for array with shape (4096, 4096)<br/>
    <span style="font-size:20px;font-weight:400;color:#fda4af;">Process killed (SIGKILL) · System Unresponsive</span>
  </div>
</div>
<div style="margin-top:auto;display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;">
  <div style="background:#1c1116;border:1px solid #991b1b;border-radius:12px;padding:18px;"><div style="font-size:16px;color:#fca5a5;">CPU LOAD</div><div style="font-size:40px;font-weight:800;color:#ef4444;">100%</div></div>
  <div style="background:#1c1116;border:1px solid #991b1b;border-radius:12px;padding:18px;"><div style="font-size:16px;color:#fca5a5;">THERMAL CORE</div><div style="font-size:40px;font-weight:800;color:#fb923c;">98°C</div></div>
  <div style="background:#1c1116;border:1px solid #991b1b;border-radius:12px;padding:18px;"><div style="font-size:16px;color:#fca5a5;">ETA (LOCAL CPU)</div><div style="font-size:40px;font-weight:800;color:#f87171;">4h 12m</div></div>
</div>
</body></html>"""

HTML_COLAB_OK = """<!DOCTYPE html><html><body style="margin:0;width:1280px;height:800px;background:#091018;color:#e2e8f0;font-family:-apple-system,ui-sans-serif,sans-serif;padding:32px;box-sizing:border-box;display:flex;flex-direction:column;gap:22px;">
<div style="display:flex;justify-content:space-between;align-items:center;background:#0f172a;border:1px solid #1e293b;padding:14px 24px;border-radius:14px;">
  <div style="display:flex;align-items:center;gap:14px;"><span style="background:linear-gradient(135deg,#f59e0b,#ea580c);padding:6px 12px;border-radius:8px;font-weight:800;color:#fff;font-size:20px;">CO</span><span style="font-size:24px;font-weight:700;">AI_DeepDive_T4.ipynb</span></div>
  <div style="background:#064e3b;border:1px solid #10b981;color:#6ee7b7;padding:8px 18px;border-radius:99px;font-size:20px;font-weight:700;">● Connected · NVIDIA Tesla T4 GPU</div>
</div>
<div style="background:#0f172a;border:1px solid #334155;border-radius:14px;padding:24px;font-family:ui-monospace,monospace;font-size:22px;line-height:1.6;">
  <div style="color:#38bdf8;">[1] <span style="color:#f8fafc;">!nvidia-smi --query-gpu=name,memory.total --format=csv,noheader</span></div>
  <div style="color:#34d399;margin-top:8px;font-weight:700;">&nbsp;&nbsp;&nbsp;&nbsp;Tesla T4, 15360 MiB (Driver 580.82.07)</div>
  <div style="color:#38bdf8;margin-top:16px;">[2] <span style="color:#f8fafc;"># 4096x4096 FP32 Matrix Benchmark (x15)</span></div>
  <div style="color:#94a3b8;">&nbsp;&nbsp;&nbsp;&nbsp;Colab CPU Time: 17.94s &nbsp;|&nbsp; Tesla T4 GPU Time: <span style="color:#fbbf24;font-weight:800;">0.522s (34.4x FASTER!)</span></div>
</div>
<div style="margin-top:auto;display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;">
  <div style="background:#0a1929;border:1px solid #0284c7;border-radius:12px;padding:20px;"><div style="font-size:16px;color:#7dd3fc;">CLOUD VRAM</div><div style="font-size:40px;font-weight:800;color:#38bdf8;">15.3 GB</div></div>
  <div style="background:#052e22;border:1px solid #10b981;border-radius:12px;padding:20px;"><div style="font-size:16px;color:#6ee7b7;">LOCAL CPU LOAD</div><div style="font-size:40px;font-weight:800;color:#34d399;">8% COOL</div></div>
  <div style="background:#1e1b4b;border:1px solid #6366f1;border-radius:12px;padding:20px;"><div style="font-size:16px;color:#a5b4fc;">CLOUD SPEEDUP</div><div style="font-size:40px;font-weight:800;color:#fbbf24;">34.4x</div></div>
</div>
</body></html>"""

HTML_RACK = """<!DOCTYPE html><html><body style="margin:0;width:1024px;height:1024px;background:#030b14;color:#bae6fd;font-family:ui-monospace,monospace;padding:42px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;border:8px solid #0ea5e9;">
<div style="font-size:34px;font-weight:800;color:#38bdf8;">GOOGLE CLOUD · COLAB VM NODE</div>
<div style="font-size:28px;line-height:1.7;color:#6ee7b7;">
  <div>OS: Ubuntu 22.04 Container</div>
  <div>GPU: NVIDIA Tesla T4 (15.36 GB)</div>
  <div>CUDA Cores: 2,560 Parallel</div>
  <div>RAM: 12.7 GB · Disk: 107 GB</div>
  <div>Net: 400+ MB/s Backbone</div>
</div>
<div style="font-size:46px;font-weight:900;color:#fbbf24;">STATUS: ACTIVE ✓</div>
</body></html>"""


def main() -> None:
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    items = [
        ("tex_laptop_oom.png", HTML_OOM, 1280, 800),
        ("tex_laptop_colab_ok.png", HTML_COLAB_OK, 1280, 800),
        ("tex_datacenter_telemetry.png", HTML_RACK, 1024, 1024),
    ]
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=BRAVE_PATH, headless=True, args=["--no-sandbox"])
        try:
            for fname, doc, w, h in items:
                pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
                pg.set_content(doc)
                out = TEX_DIR / fname
                pg.screenshot(path=str(out))
                pg.close()
                print(f"TEXTURE: {out}")
        finally:
            br.close()


if __name__ == "__main__":
    main()
