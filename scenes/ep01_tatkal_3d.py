"""Episode 01 Blender 5.3 Multi-World 3D Scene: IRCTC 10:00 AM Tatkal Concurrency Funnel.

Built strictly on engine/blender_studio_kit.py:
- Procedural Noise->Bump PBR materials (zero flat plastic)
- Working Blender 5.3 Bloom Glare + Volume Scatter atmosphere
- Clamped animate_shot_clamped() + CONSTANT holds on f_next_cut - 1 (zero fly-across)
- Real 3D Metallic Padlock (LockBody + animated LockShackle snap)
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.blender_studio_kit import (
    add_cube,
    add_cyl,
    add_light,
    add_sphere,
    add_torus,
    animate_shot_clamped,
    clear_scene,
    finalize_clamped_camera_rig,
    mat_pbr,
    project_world_point,
    setup_world,
)

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
MANIFEST_PATH = Path(argv[0]) if len(argv) >= 1 else ROOT / "build" / "ep01_audio" / "audio_manifest.json"
OUT_DIR = Path(argv[1]) if len(argv) >= 2 else ROOT / "build" / "ep01_3d_spot"
RES_X = int(argv[2]) if len(argv) >= 3 else 1080
RES_Y = int(argv[3]) if len(argv) >= 4 else 1920
FPS = int(argv[4]) if len(argv) >= 5 else 24
SAMPLES = int(argv[5]) if len(argv) >= 6 else 16
MODE = argv[6] if len(argv) >= 7 else "spot"

MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
TOTAL_MS = MANIFEST["total_ms"]
TOTAL_FRAMES = max(24, int(math.ceil((TOTAL_MS / 1000.0) * FPS)))
BEAT_MAP = {b["beat_id"]: b for b in MANIFEST["beats"]}


def ms_to_frame(ms: float) -> int:
    return max(1, min(TOTAL_FRAMES, int(round((ms / 1000.0) * FPS)) + 1))


def build_palette() -> dict[str, bpy.types.Material]:
    return {
        "asphalt": mat_pbr("Asphalt", (0.03, 0.035, 0.045), rough=0.48, metal=0.1, bump_scale=35.0, bump_strength=0.45),
        "concrete": mat_pbr("Concrete", (0.06, 0.07, 0.09), rough=0.65, metal=0.05, bump_scale=24.0, bump_strength=0.40),
        "steel_dark": mat_pbr("SteelDark", (0.04, 0.05, 0.07), rough=0.28, metal=0.85, bump_scale=55.0, bump_strength=0.14),
        "aluminum": mat_pbr("Aluminum", (0.68, 0.72, 0.78), rough=0.20, metal=0.92, bump_scale=60.0, bump_strength=0.10),
        "gold_metal": mat_pbr("GoldMetal", (0.85, 0.62, 0.14), rough=0.22, metal=0.90, bump_scale=45.0, bump_strength=0.12),
        "gold_emit": mat_pbr("GoldEmit", (1.0, 0.72, 0.14), rough=0.2, emit=(1.0, 0.68, 0.10), emit_strength=3.6),
        "cyan_emit": mat_pbr("CyanEmit", (0.14, 0.78, 1.0), rough=0.2, emit=(0.10, 0.72, 1.0), emit_strength=3.4),
        "emerald_emit": mat_pbr("EmeraldEmit", (0.08, 0.88, 0.48), rough=0.2, emit=(0.06, 0.84, 0.44), emit_strength=3.4),
        "red_emit": mat_pbr("RedEmit", (1.0, 0.22, 0.24), rough=0.2, emit=(1.0, 0.18, 0.20), emit_strength=3.8),
    }


def build_zone0_corridor(M: dict) -> None:
    """X = 0: Volumetric moody rail/fiber backdrop for stick-card beats & finale."""
    cx = 0.0
    add_cube("Z0_Floor", (cx, 2.0, -2.0), (26.0, 28.0, 0.4), M["asphalt"], bevel=0.02)
    # Parallel optical rails
    for dx in (-1.6, 1.6):
        add_cube(f"Z0_Rail_{dx}", (cx + dx, 3.0, -1.72), (0.14, 24.0, 0.18), M["aluminum"], bevel=0.02)
        add_cube(f"Z0_RailGlow_{dx}", (cx + dx * 1.65, 3.0, -1.76), (0.06, 24.0, 0.05), M["cyan_emit"])
    # Cross sleepers
    for y in range(-6, 14, 2):
        add_cube(f"Z0_Tie_{y}", (cx, y, -1.78), (4.4, 0.32, 0.08), M["concrete"])
    # Vertical signal gantries
    for k, y in enumerate([1.0, 6.0, 11.0]):
        add_cube(f"Z0_PostL_{k}", (cx - 3.6, y, 1.0), (0.35, 0.35, 6.0), M["steel_dark"], bevel=0.03)
        add_cube(f"Z0_PostR_{k}", (cx + 3.6, y, 1.0), (0.35, 0.35, 6.0), M["steel_dark"], bevel=0.03)
        add_cube(f"Z0_Beam_{k}", (cx, y, 3.8), (7.6, 0.28, 0.28), M["steel_dark"], bevel=0.02)
        add_sphere(f"Z0_Signal_{k}", (cx + (1.4 if k % 2 == 0 else -1.4), y - 0.2, 3.3), 0.22, M["gold_emit"])

    add_light("Z0_Key", "AREA", (cx - 3.0, -5.0, 5.5), 550, (0.75, 0.88, 1.0), size=6.0, rot_deg=(48, 0, -24))
    add_light("Z0_AmberRim", "AREA", (cx + 3.5, 4.0, 4.0), 420, (1.0, 0.68, 0.24), size=5.0, rot_deg=(110, 0, 145))


def build_zone1_funnel(M: dict) -> dict:
    """X = 60: Million-to-One Funnel + Auth Shield + Swarming Request Cubes."""
    cx = 60.0
    add_cube("Z1_Floor", (cx, 2.0, -2.5), (28.0, 28.0, 0.4), M["asphalt"])
    # Angled metallic funnel walls narrowing toward (cx, 3.5, 0)
    add_cube("Z1_FunnelL", (cx - 2.6, 0.2, 0.2), (0.28, 8.2, 3.6), M["steel_dark"], bevel=0.04, rot=(0, 0, math.radians(-26)))
    add_cube("Z1_FunnelR", (cx + 2.6, 0.2, 0.2), (0.28, 8.2, 3.6), M["steel_dark"], bevel=0.04, rot=(0, 0, math.radians(26)))
    add_cube("Z1_TrimL", (cx - 2.45, 0.2, 1.9), (0.09, 8.2, 0.09), M["cyan_emit"], rot=(0, 0, math.radians(-26)))
    add_cube("Z1_TrimR", (cx + 2.45, 0.2, 1.9), (0.09, 8.2, 0.09), M["cyan_emit"], rot=(0, 0, math.radians(26)))

    # Edge Auth / CAPTCHA glowing gate across throat
    shield = add_cube("Z1_AuthGate", (cx, 3.6, 0.2), (1.4, 0.14, 3.4), M["gold_emit"], bevel=0.02)

    # Swarm of incoming request blocks + bot cubes
    rng = random.Random(1001)
    swarm_cubes = []
    bot_cubes = []
    for i in range(18):
        px = cx + rng.uniform(-3.2, 3.2)
        py = rng.uniform(-4.5, 1.2)
        pz = rng.uniform(-1.2, 1.6)
        c = add_cube(f"Z1_Req_{i}", (px, py, pz), (0.34, 0.34, 0.34), M["cyan_emit"], bevel=0.04)
        swarm_cubes.append((c, px, py, pz))
    for j in range(6):
        bx = cx + rng.uniform(-1.8, 1.8)
        by = rng.uniform(1.6, 3.1)
        bz = rng.uniform(-0.8, 1.2)
        b = add_cube(f"Z1_Bot_{j}", (bx, by, bz), (0.36, 0.36, 0.36), M["red_emit"], bevel=0.04)
        bot_cubes.append((b, bx, by, bz))

    add_light("Z1_Key", "AREA", (cx, -6.5, 6.0), 700, (0.7, 0.88, 1.0), size=7.0, rot_deg=(45, 0, 0))
    return {"shield": shield, "swarm": swarm_cubes, "bots": bot_cubes}


def build_zone2_cache_vault(M: dict) -> dict:
    """X = 120: Left Redis Mirror vs Right ACID Vault + Real 3D Metallic Padlock."""
    cx = 120.0
    add_cube("Z2_Floor", (cx, 1.5, -2.2), (28.0, 26.0, 0.4), M["asphalt"])

    # Left: Fast Redis Cache Tower
    add_cube("Z2_CacheRack", (cx - 2.3, 1.2, -0.3), (1.3, 1.3, 3.4), M["steel_dark"], bevel=0.04)
    for k in range(4):
        add_cube(f"Z2_CacheLED_{k}", (cx - 2.3, 0.53, -1.1 + k * 0.65), (0.9, 0.04, 0.14), M["cyan_emit"])

    # Right: Real ACID SQL Berth Vault + Real 3D Padlock (LockBody + Shackle)
    add_cube("Z2_VaultRack", (cx + 1.8, 1.2, 0.1), (1.6, 1.6, 4.2), M["steel_dark"], bevel=0.05)
    for k in range(5):
        add_cube(f"Z2_VaultLED_{k}", (cx + 1.8, 0.38, -1.2 + k * 0.65), (1.1, 0.04, 0.14), M["emerald_emit"])

    # Fiber link connecting them
    add_cube("Z2_Bridge", (cx - 0.2, 1.2, -1.9), (4.2, 0.16, 0.08), M["gold_emit"])

    # Real 3D Metallic Padlock floating in front of Vault
    lx, ly, lz = cx + 1.8, -0.35, 0.35
    lock_body = add_cube("LockBody", (lx, ly, lz), (0.72, 0.28, 0.62), M["gold_metal"], bevel=0.06)
    add_cube("LockKeyhole", (lx, ly - 0.15, lz), (0.12, 0.04, 0.24), M["cyan_emit"])
    # U-Shackle made from torus segment + twin vertical stems
    shackle_top = add_torus("LockShackleArch", (lx, ly, lz + 0.56), 0.22, 0.055, M["aluminum"], rot=(math.radians(90), 0, 0))
    shackle_l = add_cyl("LockStemL", (lx - 0.22, ly, lz + 0.40), 0.055, 0.34, M["aluminum"])
    shackle_r = add_cyl("LockStemR", (lx + 0.22, ly, lz + 0.40), 0.055, 0.34, M["aluminum"])

    add_light("Z2_Key", "AREA", (cx - 2.0, -6.0, 5.5), 680, (0.85, 0.92, 1.0), size=6.0, rot_deg=(48, 0, -15))
    add_light("Z2_GoldRim", "AREA", (cx + 4.5, 2.5, 4.0), 460, (1.0, 0.72, 0.24), size=4.0, rot_deg=(100, 0, 125))
    return {"shackle_parts": [shackle_top, shackle_l, shackle_r], "shackle_base_z": [lz + 0.56, lz + 0.40, lz + 0.40], "lock_body": lock_body}


def build_zone3_queue_trench(M: dict) -> dict:
    """X = 180: 300ms Latency Queue Trench (40 ahead vs 1 lagging red packet)."""
    cx = 180.0
    add_cube("Z3_Floor", (cx, 4.0, -2.0), (24.0, 32.0, 0.4), M["asphalt"])
    add_cube("Z3_WallL", (cx - 2.8, 4.0, 0.0), (0.3, 28.0, 3.8), M["concrete"], bevel=0.03)
    add_cube("Z3_WallR", (cx + 2.8, 4.0, 0.0), (0.3, 28.0, 3.8), M["concrete"], bevel=0.03)
    add_cube("Z3_GoalPortal", (cx, 13.5, 0.2), (5.2, 0.24, 3.2), M["emerald_emit"], bevel=0.04)

    fast_orbs = []
    for k in range(10):
        ox = cx + (-1.6 + (k % 5) * 0.8)
        oy = 2.0 + k * 0.9
        oz = -0.8 + (k % 3) * 0.55
        o = add_sphere(f"Z3_Fast_{k}", (ox, oy, oz), 0.22, M["gold_emit"])
        fast_orbs.append((o, ox, oy, oz))

    lag_orb = add_sphere("Z3_LagOrb", (cx, -3.5, -0.4), 0.30, M["red_emit"])
    add_light("Z3_Key", "AREA", (cx, -6.0, 5.5), 620, (0.72, 0.88, 1.0), size=6.0, rot_deg=(48, 0, 0))
    return {"fast": fast_orbs, "lag": lag_orb}


def animate_all(rig: dict) -> dict[str, tuple[int, int]]:
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    cam_tgt = bpy.context.active_object
    cam_tgt.name = "CamTarget"

    bpy.ops.object.camera_add(location=(0, -8, 1))
    cam = bpy.context.active_object
    cam.name = "MainCam"
    bpy.context.scene.camera = cam
    c = cam.constraints.new(type="TRACK_TO")
    c.target = cam_tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"

    beats = MANIFEST["beats"]
    ranges = {}
    for idx, b in enumerate(beats):
        f_start = 1 if idx == 0 else ms_to_frame(b["start_ms"])
        f_next_cut = (TOTAL_FRAMES + 1) if idx == len(beats) - 1 else ms_to_frame(beats[idx + 1]["start_ms"])
        ranges[b["beat_id"]] = (f_start, f_next_cut)

    shot_end_frames: set[int] = set()

    # Shot 0: hook_0959 -> Zone 0 behind StickCard (low target so 3D corridor glows cleanly below/around Zone B)
    fs, fnc = ranges["hook_0959"]
    _, fe = animate_shot_clamped(cam, cam_tgt, fs, fnc, (-1.2, -7.2, 1.4), (0.8, -5.8, 1.1), (0.0, 4.0, 0.6), (0.0, 5.0, 0.7), 32, 34)
    shot_end_frames.add(fe)

    # Shot 1: scale_illusion -> Zone 1 Funnel Wide Shot
    fs, fnc = ranges["scale_illusion"]
    _, fe = animate_shot_clamped(cam, cam_tgt, fs, fnc, (56.8, -8.5, 3.6), (59.2, -7.0, 2.8), (60.0, 1.2, 0.1), (60.0, 2.0, 0.2), 32, 34)
    shot_end_frames.add(fe)

    # Shot 2: gate1_bot_shield -> Zone 1 Push onto Golden Edge Shield
    fs, fnc = ranges["gate1_bot_shield"]
    _, fe = animate_shot_clamped(cam, cam_tgt, fs, fnc, (62.2, -4.5, 2.2), (61.2, -1.6, 1.4), (60.0, 3.6, 0.2), (60.0, 3.6, 0.3), 34, 38)
    shot_end_frames.add(fe)

    # Animate Swarm & Deflecting Bots across Zone 1 [scale_illusion .. gate1_bot_shield]
    f1s = ranges["scale_illusion"][0]
    f2e = ranges["gate1_bot_shield"][1] - 1
    for orb, px, py, pz in rig["z1"]["swarm"]:
        orb.location = (px, py, pz)
        orb.keyframe_insert("location", frame=f1s)
        orb.location = (60.0 + (px - 60.0) * 0.22, 3.0, pz * 0.5)
        orb.keyframe_insert("location", frame=f2e)
    for b, bx, by, bz in rig["z1"]["bots"]:
        b.location = (bx, by, bz)
        b.keyframe_insert("location", frame=f1s)
        b.location = (bx + (1.8 if bx > 60 else -1.8), by - 3.2, bz + 1.4)
        b.keyframe_insert("location", frame=f2e)

    # Shot 3: cache_vs_truth -> Zone 2 Cache vs ACID Vault wide framing
    fs, fnc = ranges["cache_vs_truth"]
    _, fe = animate_shot_clamped(cam, cam_tgt, fs, fnc, (117.5, -7.8, 2.6), (119.5, -7.0, 2.0), (119.8, 1.0, 0.0), (119.8, 1.0, 0.1), 32, 34)
    shot_end_frames.add(fe)

    # Shot 4: row_lock_mutex -> Zone 2 Close-Up on Real 3D Padlock snapping shut
    fs, fnc = ranges["row_lock_mutex"]
    _, fe = animate_shot_clamped(cam, cam_tgt, fs, fnc, (121.2, -4.8, 1.6), (121.8, -3.5, 0.9), (121.8, -0.35, 0.45), (121.8, -0.35, 0.45), 38, 42)
    shot_end_frames.add(fe)
    snap_f = fs + int((fe - fs) * 0.45)
    for part, base_z in zip(rig["z2"]["shackle_parts"], rig["z2"]["shackle_base_z"]):
        part.location.z = base_z + 0.18
        part.keyframe_insert("location", frame=fs)
        part.location.z = base_z + 0.18
        part.keyframe_insert("location", frame=snap_f - 4)
        part.location.z = base_z
        part.keyframe_insert("location", frame=snap_f + 4)

    # Shot 5: why_300ms_kills -> Zone 3 Trench Lagging Red Sphere vs Gold Fast Spheres
    fs, fnc = ranges["why_300ms_kills"]
    _, fe = animate_shot_clamped(cam, cam_tgt, fs, fnc, (177.8, -7.5, 2.4), (179.4, -5.0, 1.6), (180.0, 4.0, -0.2), (180.0, 6.5, 0.0), 32, 35)
    shot_end_frames.add(fe)
    rig["z3"]["lag"].location = (180.0, -4.0, -0.4)
    rig["z3"]["lag"].keyframe_insert("location", frame=fs)
    rig["z3"]["lag"].location = (180.0, 1.8, -0.4)
    rig["z3"]["lag"].keyframe_insert("location", frame=fe)
    for o, ox, oy, oz in rig["z3"]["fast"]:
        o.location = (ox, oy, oz)
        o.keyframe_insert("location", frame=fs)
        o.location = (ox, oy + 7.5, oz)
        o.keyframe_insert("location", frame=fe)

    # Shot 6: race_recap -> Zone 0 Dramatic Station Pullback behind Stick Race
    fs, fnc = ranges["race_recap"]
    _, fe = animate_shot_clamped(cam, cam_tgt, fs, fnc, (2.2, -6.8, 1.8), (-1.4, -7.4, 2.2), (0.0, 4.5, 0.8), (0.0, 5.5, 0.9), 34, 32)
    shot_end_frames.add(fe)

    # Shot 7: cs_law_takeaway -> Zone 0 Finale Center Corridor Glow
    fs, fnc = ranges["cs_law_takeaway"]
    _, fe = animate_shot_clamped(cam, cam_tgt, fs, fnc, (0.0, -7.8, 2.6), (0.0, -9.2, 3.2), (0.0, 4.0, 0.5), (0.0, 4.0, 0.6), 32, 30)
    shot_end_frames.add(fe)

    finalize_clamped_camera_rig(cam, cam_tgt, shot_end_frames)
    return ranges


def main() -> None:
    clear_scene()
    scene = bpy.context.scene
    setup_world(scene, TOTAL_FRAMES, fps=FPS, res_x=RES_X, res_y=RES_Y, samples=SAMPLES)
    M = build_palette()
    rig = {
        "z0": build_zone0_corridor(M),
        "z1": build_zone1_funnel(M),
        "z2": build_zone2_cache_vault(M),
        "z3": build_zone3_queue_trench(M),
    }
    ranges = animate_all(rig)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cam = scene.camera
    tgt = bpy.data.objects["CamTarget"]

    if MODE == "spot":
        spot_meta = []
        for idx, b in enumerate(MANIFEST["beats"]):
            fs, fnc = ranges[b["beat_id"]]
            mid_ms = b["start_ms"] + int(b["duration_ms"] * 0.62)
            fr = min(fnc - 1, ms_to_frame(mid_ms))
            scene.frame_set(fr)
            u, v, z = project_world_point(scene, cam, tuple(tgt.location))
            out_png = OUT_DIR / f"spot3d_{idx:02d}_{b['beat_id']}.png"
            scene.render.filepath = str(out_png)
            bpy.ops.render.render(write_still=True)
            spot_meta.append({"beat": b["beat_id"], "frame": fr, "u": round(u, 3), "v": round(v, 3), "file": str(out_png)})
            print(f"SPOT3D_OK {b['beat_id']} frame={fr} proj=({u:.2f},{v:.2f})", flush=True)
        # Boundary cut frame test on Beat 0 -> Beat 1 cut!
        b1_cut = ranges[MANIFEST["beats"][1]["beat_id"]][0]
        for bfr in (b1_cut - 1, b1_cut):
            scene.frame_set(bfr)
            b_png = OUT_DIR / f"cut_test_{bfr:04d}.png"
            scene.render.filepath = str(b_png)
            bpy.ops.render.render(write_still=True)
            print(f"CUT_FRAME_SAVED {b_png}", flush=True)
        (OUT_DIR / "spot_meta.json").write_text(json.dumps(spot_meta, indent=2), encoding="utf-8")
    else:
        scene.render.filepath = str(OUT_DIR / "frame_")
        bpy.ops.render.render(animation=True)
        print(f"ANIM3D_DONE frames={TOTAL_FRAMES}", flush=True)


if __name__ == "__main__":
    main()
