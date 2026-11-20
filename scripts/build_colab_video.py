"""Assemble the 6-min (366s) 1920x1080 Google Colab Documentary Masterclass.

Combines:
  - 5 verified Blender 5.3 EEVEE 3D hero worlds (boomerang-looped for seamless motion)
  - 4 interactive Playwright/Brave 1920x1080 animated UI motion scenes
  - 28 beat-synced transparent RGBA HUD + Devanagari/English subtitle overlays
  - Stereo procedural ambient SFX bed + -14 LUFS dual-voice narration (Male + Veena Kavya)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audio.sfx_gen import generate_sfx_bed

BUILD = ROOT / "build" / "colab_doc"
CLIPS3D_DIR = BUILD / "clips3d"
SEGS_DIR = BUILD / "segs"
UI_DIR = BUILD / "ui_frames"
HUD_DIR = BUILD / "hud_pngs"
OUT_MP4 = ROOT / "output" / "google_colab_masterclass_16x9.mp4"
BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

# Visual mapping for every beat: cohesive alternation between 3D worlds & interactive UI
BEAT_VISUALS = {
    "b01": ("3d", "w1_oom"),
    "b02": ("3d", "w2_dc"),
    "b03": ("ui", "sc-arch"),
    "b04": ("3d", "w1_ok"),
    "b05": ("ui", "sc-arch"),
    "b06": ("ui", "sc-arch"),
    "b07": ("3d", "w2_dc"),
    "b08": ("3d", "w2_dc"),
    "b09": ("ui", "sc-arch"),
    "b10": ("3d", "w3_cpugpu"),
    "b11": ("3d", "w3_cpugpu"),
    "b12": ("3d", "w3_cpugpu"),
    "b13": ("ui", "sc-bench"),
    "b14": ("ui", "sc-bench"),
    "b15": ("3d", "w3_cpugpu"),
    "b16": ("ui", "sc-powers"),
    "b17": ("ui", "sc-powers"),
    "b18": ("3d", "w2_dc"),
    "b19": ("ui", "sc-powers"),
    "b20": ("ui", "sc-powers"),
    "b21": ("3d", "w4_vault"),
    "b22": ("3d", "w4_vault"),
    "b23": ("ui", "sc-safe"),
    "b24": ("3d", "w4_vault"),
    "b25": ("ui", "sc-safe"),
    "b26": ("ui", "sc-safe"),
    "b27": ("3d", "w1_ok"),
    "b28": ("3d", "w1_ok"),
}


def _build_3d_boomerangs() -> dict[str, Path]:
    """Turn 96-frame 3D PNG runs into seamless 8.0s boomerang loop MP4s (192 frames @ 24fps)."""
    SEGS_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    for name in ("w1_oom", "w1_ok", "w2_dc", "w3_cpugpu", "w4_vault"):
        dst = SEGS_DIR / f"loop_{name}.mp4"
        out[name] = dst
        if dst.exists():
            continue
        pat = str(CLIPS3D_DIR / name / "f_%04d.png")
        subprocess.run(
            [
                "ffmpeg", "-y", "-framerate", "24", "-i", pat,
                "-filter_complex", "[0:v]split[f][r];[r]reverse[rv];[f][rv]concat=n=2:v=1:a=0,format=yuv420p",
                "-c:v", "libx264", "-preset", "fast", "-crf", "14", str(dst),
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        print(f"BOOMERANG_3D: {dst.name}", flush=True)
    return out


def _build_ui_clips() -> dict[str, Path]:
    """Render all 4 animated 1920x1080 interactive UI scenes cleanly via Playwright/Brave."""
    UI_DIR.mkdir(parents=True, exist_ok=True)
    SEGS_DIR.mkdir(parents=True, exist_ok=True)
    html_p = ROOT / "scenes" / "colab_motion_ui.html"
    out = {}

    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=BRAVE_PATH, headless=True, args=["--no-sandbox", "--disable-gpu-sandbox"])
        try:
            pg = br.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
            pg.goto(html_p.resolve().as_uri(), wait_until="load")
            pg.evaluate("() => document.fonts.ready")

            # Animated 96-frame (4.0s) packet loop & benchmark race
            for sc_id, total_f in (("sc-arch", 96), ("sc-bench", 96)):
                dst = SEGS_DIR / f"loop_{sc_id}.mp4"
                out[sc_id] = dst
                if not dst.exists():
                    sdir = UI_DIR / sc_id
                    sdir.mkdir(parents=True, exist_ok=True)
                    pg.evaluate("(s) => window.initDoc({scene: s})", sc_id)
                    for idx in range(total_f):
                        pg.evaluate("(t) => window.seekToMs(t)", int(idx * 1000 / 24))
                        pg.screenshot(path=str(sdir / f"u_{idx+1:04d}.png"))
                    pad = ",tpad=stop_mode=clone:stop_duration=10" if sc_id == "sc-bench" else ""
                    subprocess.run(
                        [
                            "ffmpeg", "-y", "-framerate", "24", "-i", str(sdir / "u_%04d.png"),
                            "-vf", f"format=yuv420p{pad}", "-c:v", "libx264", "-preset", "fast", "-crf", "14", str(dst),
                        ],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    print(f"UI_ANIM_DONE: {dst.name}", flush=True)

            # High-detail dashboard cards (sc-powers, sc-safe) with subtle cinematic breathe zoom
            for sc_id in ("sc-powers", "sc-safe"):
                dst = SEGS_DIR / f"loop_{sc_id}.mp4"
                out[sc_id] = dst
                if not dst.exists():
                    png = UI_DIR / f"{sc_id}.png"
                    pg.evaluate("(s) => window.initDoc({scene: s})", sc_id)
                    pg.screenshot(path=str(png))
                    # Subtle smooth 1.00 -> 1.035 -> 1.00 8-sec breath @ 24fps (192 frames)
                    subprocess.run(
                        [
                            "ffmpeg", "-y", "-loop", "1", "-i", str(png), "-t", "8",
                            "-vf", "scale=3840:2160,zoompan=z='1.018+0.016*sin(2*PI*on/192)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24,format=yuv420p",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "14", str(dst),
                        ],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    print(f"UI_ZOOM_DONE: {dst.name}", flush=True)
        finally:
            br.close()
    return out


def _render_beat_huds(manifest: dict) -> list[Path]:
    """Render 1 crisp transparent 1920x1080 RGBA overlay PNG per beat (~4s total!)."""
    HUD_DIR.mkdir(parents=True, exist_ok=True)
    html_p = ROOT / "scenes" / "colab_hud_16x9.html"
    outs = []
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=BRAVE_PATH, headless=True, args=["--no-sandbox"])
        try:
            pg = br.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
            pg.goto(html_p.resolve().as_uri(), wait_until="load")
            pg.evaluate("(m) => document.fonts.ready.then(() => window.initDoc(m))", manifest)
            for idx, b in enumerate(manifest["beats"]):
                out_png = HUD_DIR / f"hud_{idx:02d}.png"
                outs.append(out_png)
                if not out_png.exists():
                    pg.evaluate("(t) => window.seekToMs(t)", b["start_ms"] + 300)
                    pg.screenshot(path=str(out_png), type="png", omit_background=True)
        finally:
            br.close()
    print(f"HUDS_DONE: {len(outs)} RGBA beat overlays", flush=True)
    return outs


def main() -> None:
    manifest = json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))
    total_ms = manifest["total_ms"]
    total_s = total_ms / 1000.0
    beats = manifest["beats"]

    print("[1/5] Preparing 3D boomerang segments...", flush=True)
    clips_3d = _build_3d_boomerangs()

    print("[2/5] Rendering 1920x1080 UI motion scenes...", flush=True)
    clips_ui = _build_ui_clips()

    print("[3/5] Rendering 28 transparent RGBA HUD beat overlays...", flush=True)
    hud_pngs = _render_beat_huds(manifest)

    print("[4/5] Building exact synced base video track...", flush=True)
    # Build individual duration-exact video chunks per beat so every cut aligns with narration
    beat_clips = []
    for idx, b in enumerate(beats):
        kind, cname = BEAT_VISUALS[b["id"]]
        src_clip = clips_3d[cname] if kind == "3d" else clips_ui[cname]
        start_s = 0.0 if idx == 0 else b["start_ms"] / 1000.0
        end_s = total_s if idx == len(beats) - 1 else beats[idx + 1]["start_ms"] / 1000.0
        dur_s = end_s - start_s
        chunk_mp4 = SEGS_DIR / f"chunk_{idx:02d}_{b['id']}.mp4"
        if not chunk_mp4.exists():
            # Overlay the beat's transparent HUD PNG on this chunk cleanly!
            vf = (
                f"[0:v]trim=0:{dur_s:.3f},setpts=PTS-STARTPTS[bg];"
                f"[bg][1:v]overlay=0:0:shortest=1,fps=24,format=yuv420p"
            )
            # For sc-bench hold final bar state cleanly by freezing last frame after 4s loop or gentle loop
            loop_flag = ["-stream_loop", "-1"]
            subprocess.run(
                [
                    "ffmpeg", "-y", *loop_flag, "-i", str(src_clip),
                    "-loop", "1", "-t", f"{dur_s:.3f}", "-i", str(hud_pngs[idx]),
                    "-filter_complex", vf,
                    "-t", f"{dur_s:.3f}", "-an",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "14", str(chunk_mp4),
                ],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        beat_clips.append(chunk_mp4)

    concat_txt = SEGS_DIR / "concat_video.txt"
    concat_txt.write_text("".join(f"file '{p.resolve()}'\n" for p in beat_clips), encoding="utf-8")
    raw_video = BUILD / "video_16x9_noaudio.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(raw_video)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    print("[5/5] Synthesizing ambient SFX + final -14 LUFS master mux...", flush=True)
    beat_starts = [b["start_ms"] for b in beats]
    pings = [(b["start_ms"] + 180, 980.0 if b["spk"] == "kavya" else 740.0) for b in beats if b["id"] in ("b02", "b03", "b06", "b10", "b13", "b15", "b16", "b19", "b21", "b23", "b26")]
    sfx_wav = BUILD / "audio" / "sfx_16x9.wav"
    if not sfx_wav.exists():
        generate_sfx_bed(total_ms, beat_starts, pings, sfx_wav)

    nar_wav = BUILD / "audio" / "full_narration_16x9.wav"
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(raw_video),
            "-i", str(nar_wav),
            "-i", str(sfx_wav),
            "-filter_complex", (
                "[1:a]aresample=48000[nar];"
                "[2:a]aresample=48000,volume=0.38[sfx];"
                "[nar][sfx]amix=inputs=2:duration=first:dropout_transition=0,"
                "loudnorm=I=-14:TP=-1.5:LRA=8[aout]"
            ),
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", str(OUT_MP4),
        ],
        check=True,
    )
    sz_mb = OUT_MP4.stat().st_size / (1024 * 1024)
    print(f"\nMASTERCLASS_DONE: {OUT_MP4} ({sz_mb:.1f} MB, {total_s:.2f}s)", flush=True)


if __name__ == "__main__":
    main()
