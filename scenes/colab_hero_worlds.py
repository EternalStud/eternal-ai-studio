"""Hero 16:9 (1920x1080) Blender 5.3 EEVEE worlds for the 6-min Google Colab Documentary.

4 separated dark-studio worlds along X = 0, 60, 120, 180:
  W1 (X=0):   2 AM Student Desk + Overheating 8GB Laptop (OOM texture) & Calm Return Shot
  W2 (X=60):  Google Cloud Data Center Server Corridor + Ubuntu VM Telemetry
  W3 (X=120): Physical Computing Lab — 4 Heavy Gold CPU Cores vs 2,560-Core T4 GPU Array + TPU
  W4 (X=180): Ephemeral 12h Container Pod -> Golden Bridge -> Persistent Google Drive + Secrets Vault

Uses engine/blender_studio_kit.py helpers and supports `--spot-only` and `--part N` batch rendering.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
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
    setup_world,
)

TEX_DIR = ROOT / "build" / "colab_doc" / "textures"


def _add_textured_plane(name: str, loc, size_xy: tuple[float, float], img_path: Path, rot=(0.0, 0.0, 0.0), emit_strength: float = 1.45):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size_xy[0], size_xy[1], 1.0)
    obj.rotation_euler = rot

    mat = bpy.data.materials.new(name=f"Mat_{name}")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(img_path), check_existing=True)

    # Set dark subtle specular screen + crisp emission so screen text stays clean
    for sock in ("Roughness",):
        if sock in bsdf.inputs:
            bsdf.inputs[sock].default_value = 0.22
    if "Base Color" in bsdf.inputs:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    elif "Emission" in bsdf.inputs:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission"])
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emit_strength

    obj.data.materials.append(mat)
    return obj


def build_world_1_night_desk(base_x: float = 0.0, screen_tex: str = "tex_laptop_oom.png") -> None:
    m_wood = mat_pbr("DeskWood", (0.078, 0.042, 0.022), rough=0.44, metal=0.04, bump_scale=14.0, bump_strength=0.14)
    m_wall = mat_pbr("NightWall", (0.016, 0.024, 0.042), rough=0.82, metal=0.02, bump_scale=6.0, bump_strength=0.05)
    m_alu = mat_pbr("DarkAlu", (0.18, 0.19, 0.22), rough=0.25, metal=0.88, bump_scale=28.0, bump_strength=0.03)
    m_key = mat_pbr("Keycap", (0.022, 0.024, 0.028), rough=0.45, metal=0.05)
    m_mug = mat_pbr("CeramicMug", (0.78, 0.72, 0.66), rough=0.22, metal=0.0)
    m_coffee = mat_pbr("DarkCoffee", (0.025, 0.012, 0.006), rough=0.05, metal=0.0)
    m_lamp = mat_pbr("LampMetal", (0.08, 0.10, 0.14), rough=0.25, metal=0.85)
    m_paper = mat_pbr("NotebookPaper", (0.78, 0.76, 0.70), rough=0.75, metal=0.0)
    m_cover = mat_pbr("NotebookCover", (0.05, 0.12, 0.24), rough=0.55, metal=0.05)

    is_ok = "ok" in screen_tex
    vent_col = (0.1, 0.85, 0.55) if is_ok else (1.0, 0.22, 0.04)
    m_vent = mat_pbr("ThermalVent", (0.1, 0.04, 0.02), rough=0.3, emit=vent_col, emit_strength=6.5)
    m_fiber = mat_pbr("FiberBlue", (0.05, 0.28, 0.48), rough=0.18, emit=(0.15, 0.72, 1.0), emit_strength=6.0)
    m_bulb = mat_pbr("LampBulb", (1.0, 0.85, 0.6), rough=0.1, emit=(1.0, 0.78, 0.45), emit_strength=11.0)

    add_cube("W1_DeskTop", (base_x, 0.0, -0.06), (7.0, 3.6, 0.12), m_wood, bevel=0.02)
    add_cube("W1_BackWall", (base_x, 1.55, 1.8), (8.5, 0.16, 4.8), m_wall, bevel=0.0)

    lx, ly = base_x - 0.12, -0.05
    add_cube("W1_LaptopBase", (lx, ly, 0.028), (1.32, 0.88, 0.046), m_alu, bevel=0.012)
    for row in range(5):
        for kcol in range(12):
            add_cube(
                f"W1_Key_{row}_{kcol}",
                (lx - 0.44 + kcol * 0.08, ly + 0.22 - row * 0.065, 0.052),
                (0.064, 0.052, 0.012), m_key, bevel=0.003,
            )
    add_cube("W1_Trackpad", (lx, ly - 0.24, 0.050), (0.38, 0.24, 0.006), m_key, bevel=0.004)
    add_cube("W1_ThermalGlow", (lx, ly + 0.42, 0.032), (0.94, 0.045, 0.022), m_vent, bevel=0.004)

    # Laptop Lid tilted -15 deg back; plane rotated +75 deg around X so normal faces camera (-Y/+Z)
    lid_tilt = math.radians(-15)
    add_cube("W1_LaptopLid", (lx, ly + 0.45, 0.44), (1.32, 0.036, 0.84), m_alu, bevel=0.012, rot=(lid_tilt, 0, 0))
    _add_textured_plane(
        "W1_ScreenTex",
        (lx, ly + 0.428, 0.442),
        (1.22, 0.762),
        TEX_DIR / screen_tex,
        rot=(math.radians(75), 0, 0),
        emit_strength=1.45,
    )

    # Desk lamp positioned left of screen so it never occludes display text
    lamp_x, lamp_y = base_x - 1.48, 0.38
    add_cyl("W1_LampBase", (lamp_x, lamp_y, 0.02), 0.19, 0.04, m_lamp)
    add_cyl("W1_LampStem1", (lamp_x - 0.05, lamp_y, 0.42), 0.022, 0.82, m_lamp, rot=(0, math.radians(8), 0))
    add_cyl("W1_LampStem2", (lamp_x + 0.14, lamp_y - 0.06, 0.92), 0.020, 0.56, m_lamp, rot=(math.radians(15), math.radians(-38), 0))
    bpy.ops.mesh.primitive_cone_add(
        vertices=36, radius1=0.18, radius2=0.06, depth=0.24,
        location=(lamp_x + 0.30, lamp_y - 0.12, 0.98),
    )
    shade = bpy.context.active_object
    shade.name = "W1_LampShade"
    shade.rotation_euler = (math.radians(22), math.radians(-35), 0)
    bpy.ops.object.shade_smooth()
    shade.data.materials.append(m_lamp)
    add_sphere("W1_LampBulb", (lamp_x + 0.35, lamp_y - 0.14, 0.91), 0.048, m_bulb)

    # Coffee mug + spiral notebook props
    mx, my = base_x + 0.98, -0.15
    add_cyl("W1_MugBody", (mx, my, 0.12), 0.125, 0.24, m_mug)
    add_cyl("W1_CoffeeTop", (mx, my, 0.236), 0.108, 0.01, m_coffee)
    add_torus("W1_MugHandle", (mx + 0.125, my, 0.12), 0.06, 0.016, m_mug, rot=(math.radians(90), 0, 0))

    add_cube("W1_NotebookCover", (base_x - 1.08, -0.28, 0.014), (0.42, 0.56, 0.026), m_cover, bevel=0.005, rot=(0, 0, math.radians(14)))
    add_cube("W1_NotebookPages", (base_x - 1.07, -0.28, 0.024), (0.40, 0.53, 0.016), m_paper, bevel=0.002, rot=(0, 0, math.radians(14)))

    # Glowing fiber cable exiting laptop toward Colab cloud
    pts = [
        Vector((lx + 0.66, ly + 0.25, 0.026)),
        Vector((lx + 1.08, ly + 0.38, 0.020)),
        Vector((lx + 1.58, ly + 0.78, 0.018)),
        Vector((lx + 2.50, ly + 1.10, 0.018)),
    ]
    c_data = bpy.data.curves.new("W1_FiberCable", type="CURVE")
    c_data.dimensions = "3D"
    c_data.bevel_depth = 0.016
    c_data.bevel_resolution = 4
    sp = c_data.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for idx, p in enumerate(pts):
        sp.points[idx].co = (p.x, p.y, p.z, 1.0)
    sp.use_endpoint_u = True
    cable_obj = bpy.data.objects.new("W1_FiberCable", c_data)
    cable_obj.data.materials.append(m_fiber)
    bpy.context.scene.collection.objects.link(cable_obj)

    # Lights: disable glossy on bounce fill so no square rectangle reflects in LCD screen!
    k = add_light("W1_LampKey", "SPOT", (lamp_x + 0.42, lamp_y - 0.14, 0.83), 180.0, (1.0, 0.75, 0.46), size=0.35, rot_deg=(48, -28, -20))
    k.data.spot_size = math.radians(82)
    k.data.spot_blend = 0.65

    rim = add_light("W1_MoonRim", "AREA", (base_x + 1.9, 1.15, 2.2), 140.0, (0.36, 0.68, 1.0), size=1.6, rot_deg=(-58, 25, -145))
    rim.visible_glossy = False
    fill = add_light("W1_DeskFill", "AREA", (base_x - 0.1, -1.6, 1.9), 42.0, (0.78, 0.86, 1.0), size=2.4, rot_deg=(42, 0, 0))
    fill.visible_glossy = False


def build_world_2_datacenter(base_x: float = 60.0) -> None:
    """World 2: Google Cloud Data Center Server Bay + Ubuntu VM Telemetry Screens."""
    m_floor = mat_pbr("DCFloor", (0.018, 0.022, 0.032), rough=0.14, metal=0.65, bump_scale=18.0, bump_strength=0.04)
    m_rack = mat_pbr("DCRack", (0.04, 0.045, 0.06), rough=0.32, metal=0.86, bump_scale=12.0, bump_strength=0.05)
    m_cyan = mat_pbr("DCCyan", (0.05, 0.4, 0.6), rough=0.2, emit=(0.18, 0.82, 1.0), emit_strength=7.5)
    m_em = mat_pbr("DCEmerald", (0.05, 0.5, 0.3), rough=0.2, emit=(0.15, 0.95, 0.58), emit_strength=6.5)
    m_gold = mat_pbr("DCGold", (0.7, 0.5, 0.15), rough=0.22, metal=0.92, emit=(1.0, 0.72, 0.2), emit_strength=3.5)

    add_cube("W2_Floor", (base_x, 0.0, -0.05), (12.0, 18.0, 0.1), m_floor, bevel=0.0)

    # Twin symmetrical server rack aisles
    for row in range(5):
        ry = -3.0 + row * 1.95
        for side in (-1, 1):
            rx = base_x + side * 2.15
            add_cube(f"W2_Rack_{side}_{row}", (rx, ry, 1.55), (1.1, 1.45, 3.1), m_rack, bevel=0.02)
            # Blade LEDs
            for blade in range(7):
                bz = 0.45 + blade * 0.36
                led_m = m_em if (blade + row) % 3 == 0 else m_cyan
                add_cube(
                    f"W2_LED_{side}_{row}_{blade}",
                    (rx - side * 0.56, ry, bz),
                    (0.02, 1.12, 0.045), led_m, bevel=0.004,
                )

    # Hero Center Google Cloud Container Pedestal + Elevated Telemetry Display (zero ring overlap!)
    add_cyl("W2_CorePedestal", (base_x, 1.15, 0.22), 1.05, 0.44, m_rack)
    add_torus("W2_CoreRing1", (base_x, 1.15, 0.52), 0.92, 0.032, m_cyan, rot=(math.radians(8), math.radians(6), 0))
    add_torus("W2_CoreRing2", (base_x, 1.15, 0.40), 1.12, 0.022, m_gold, rot=(math.radians(-6), math.radians(-8), 0))
    _add_textured_plane(
        "W2_TelemetryScreen",
        (base_x, 0.96, 1.56),
        (1.62, 1.62),
        TEX_DIR / "tex_datacenter_telemetry.png",
        rot=(math.radians(90), 0, 0),
        emit_strength=1.35,
    )

    # Central optical conduit channel along glass aisle floor
    add_cube("W2_AisleFiber", (base_x, -0.5, 0.01), (0.14, 10.5, 0.02), m_cyan, bevel=0.005)
    l1 = add_light("W2_OverheadKey", "AREA", (base_x, 0.2, 3.8), 260.0, (0.55, 0.82, 1.0), size=2.8, rot_deg=(0, 0, 0))
    l1.visible_glossy = False
    add_light("W2_CoreGlow", "POINT", (base_x, 0.4, 1.25), 95.0, (0.2, 0.85, 1.0), size=0.6)


def build_world_3_cpu_vs_gpu(base_x: float = 120.0) -> None:
    """World 3: 4 Gold Sequential CPU Cores (Left) vs 144 Crisp Emerald T4 CUDA Pillars (Right)."""
    m_floor = mat_pbr("W3Floor", (0.015, 0.018, 0.028), rough=0.32, metal=0.45, bump_scale=10.0, bump_strength=0.06)
    m_slate = mat_pbr("W3Slate", (0.04, 0.046, 0.064), rough=0.28, metal=0.80)
    m_gold = mat_pbr("W3GoldCPU", (0.85, 0.62, 0.18), rough=0.22, metal=0.94, emit=(1.0, 0.68, 0.15), emit_strength=0.18)
    m_gold_rim = mat_pbr("W3GoldRim", (1.0, 0.72, 0.22), rough=0.20, emit=(1.0, 0.68, 0.16), emit_strength=2.2)
    m_cuda = mat_pbr("W3CudaCore", (0.04, 0.28, 0.20), rough=0.25, metal=0.78, emit=(0.10, 0.88, 0.52), emit_strength=0.85)
    m_amber_blk = mat_pbr("W3QueueBlk", (0.8, 0.4, 0.1), rough=0.25, emit=(1.0, 0.52, 0.16), emit_strength=1.4)

    add_cube("W3_Floor", (base_x, 0.0, -0.05), (14.0, 9.0, 0.10), m_floor, bevel=0.0)

    # LEFT: CPU Pedestal — 4 Crisp Metallic Gold Cores + Serial Queue centered cleanly
    cx = base_x - 1.50
    add_cube("W3_CpuDeck", (cx, 0.0, 0.08), (2.2, 2.5, 0.16), m_slate, bevel=0.02)
    for i in range(4):
        ox = cx - 0.38 + (i % 2) * 0.76
        oy = 0.42 - (i // 2) * 0.76
        add_cube(f"W3_CpuCore_{i}", (ox, oy, 0.34), (0.56, 0.56, 0.34), m_gold, bevel=0.03)
        add_cube(f"W3_CpuCap_{i}", (ox, oy, 0.52), (0.34, 0.34, 0.025), m_gold_rim, bevel=0.006)
    for q in range(6):
        add_cube(f"W3_SerialBlk_{q}", (cx - 0.70 + q * 0.28, -0.92, 0.25), (0.16, 0.16, 0.16), m_amber_blk, bevel=0.015)

    # RIGHT: NVIDIA T4 GPU Die — 12x12 Crisp Individual Emerald CUDA Pillars
    gx = base_x + 1.50
    add_cube("W3_GpuPCB", (gx, 0.0, 0.08), (2.5, 2.5, 0.16), m_slate, bevel=0.02)
    for r in range(12):
        for c in range(12):
            px = gx - 0.90 + c * 0.164
            py = -0.90 + r * 0.164
            add_cube(f"W3_Cuda_{r}_{c}", (px, py, 0.25), (0.10, 0.10, 0.18), m_cuda, bevel=0.01)

    k1 = add_light("W3_CpuKey", "AREA", (cx, -1.4, 2.8), 220.0, (1.0, 0.80, 0.48), size=1.6, rot_deg=(35, 0, 0))
    k1.visible_glossy = False
    k2 = add_light("W3_GpuKey", "AREA", (gx, -1.4, 2.8), 220.0, (0.42, 1.0, 0.76), size=1.6, rot_deg=(35, 0, 0))
    k2.visible_glossy = False
    rim = add_light("W3_Rim", "AREA", (base_x, 2.5, 2.4), 180.0, (0.55, 0.78, 1.0), size=3.5, rot_deg=(-45, 0, 180))
    rim.visible_glossy = False


def build_world_4_drive_vault(base_x: float = 180.0) -> None:
    """World 4: Ephemeral 12h Container Pod bridged securely to Persistent Google Drive Server Cabinet."""
    m_floor = mat_pbr("W4Floor", (0.014, 0.018, 0.026), rough=0.20, metal=0.62)
    m_pod = mat_pbr("W4Pod", (0.06, 0.08, 0.12), rough=0.26, metal=0.86)
    m_warn = mat_pbr("W4Warn", (0.85, 0.35, 0.05), rough=0.22, emit=(1.0, 0.44, 0.08), emit_strength=3.8)
    m_vault = mat_pbr("W4Vault", (0.06, 0.10, 0.18), rough=0.22, metal=0.88)
    m_safe = mat_pbr("W4Safe", (0.1, 0.55, 0.35), rough=0.20, emit=(0.18, 0.92, 0.60), emit_strength=2.4)
    m_gold = mat_pbr("W4Gold", (0.85, 0.64, 0.18), rough=0.20, metal=0.92, emit=(1.0, 0.75, 0.22), emit_strength=1.2)

    add_cube("W4_Floor", (base_x, 0.0, -0.05), (14.0, 9.0, 0.10), m_floor, bevel=0.0)

    # Left: Ephemeral VM Container Pod + Stacked Amber 12h Timer Rings
    ex = base_x - 1.75
    add_cyl("W4_VmBase", (ex, 0.0, 0.12), 0.92, 0.24, m_pod, verts=32)
    for tier in range(3):
        add_cyl(f"W4_VmTier_{tier}", (ex, 0.0, 0.42 + tier * 0.32), 0.68, 0.22, m_pod, verts=16)
        add_torus(f"W4_TimerRing_{tier}", (ex, 0.0, 0.42 + tier * 0.32), 0.76, 0.018, m_warn)

    # Multi-strand Glowing Optical Drive-Mount Bridge
    for strand in (-0.14, 0.0, 0.14):
        add_cube(f"W4_Bridge_{strand:.2f}", (base_x, strand, 0.55), (2.4, 0.05, 0.04), m_safe, bevel=0.01)

    # Right: Persistent Armored Google Drive Storage Tower + Telemetry Screen + Lock Shackle
    vx = base_x + 1.65
    add_cube("W4_DriveBase", (vx, 0.0, 0.12), (1.75, 1.55, 0.24), m_pod, bevel=0.03)
    for slot in range(4):
        add_cube(f"W4_DriveBlade_{slot}", (vx, 0.0, 0.44 + slot * 0.28), (1.36, 1.24, 0.20), m_vault, bevel=0.02)
        add_cube(f"W4_BladeLED_{slot}", (vx, -0.63, 0.44 + slot * 0.28), (0.92, 0.02, 0.045), m_safe, bevel=0.005)
    add_torus("W4_KeyShackle", (vx, 0.0, 1.62), 0.28, 0.045, m_gold, rot=(math.radians(90), 0, 0))

    l1 = add_light("W4_Key", "AREA", (base_x, -2.2, 2.8), 260.0, (0.78, 0.90, 1.0), size=2.6, rot_deg=(45, 0, 0))
    l1.visible_glossy = False
    l2 = add_light("W4_Rim", "AREA", (base_x, 2.2, 2.4), 190.0, (0.28, 0.85, 0.68), size=2.6, rot_deg=(-45, 0, 180))
    l2.visible_glossy = False


def render_all_previews() -> None:
    """Render 1920x1080 single-frame previews for all 4 hero worlds + OK screen check."""
    out_dir = ROOT / "build" / "colab_doc" / "previews"
    out_dir.mkdir(parents=True, exist_ok=True)
    clear_scene()
    scene = bpy.context.scene
    setup_world(scene, total_frames=24, fps=24, res_x=1920, res_y=1080, samples=16, bg_color=(0.008, 0.012, 0.024), fog_density=0.007)

    build_world_1_night_desk(0.0, "tex_laptop_oom.png")
    build_world_2_datacenter(60.0)
    build_world_3_cpu_vs_gpu(120.0)
    build_world_4_drive_vault(180.0)

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = 32.0
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    shots = [
        ("w1_desk", Vector((-0.98, -2.55, 1.05)), Vector((-0.05, 0.05, 0.34))),
        ("w2_dc", Vector((60.0, -4.3, 1.55)), Vector((60.0, 1.2, 1.22))),
        ("w3_cpugpu", Vector((120.0, -4.15, 2.25)), Vector((120.0, 0.0, 0.22))),
        ("w4_vault", Vector((180.0, -4.35, 1.75)), Vector((180.0, 0.0, 0.65))),
    ]
    for name, cpos, tpos in shots:
        cam.location = cpos
        cam.rotation_euler = (tpos - cpos).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(out_dir / f"{name}.png")
        scene.frame_set(1)
        bpy.ops.render.render(write_still=True)
        print(f"PREVIEW_SAVED: {name}.png", flush=True)


def render_hero_clips(part: int | None = None) -> None:
    """Render looping hero 1920x1080 video frame sequences (4s slow dolly @ 24fps = 96 frames)."""
    fps = 24
    clip_specs = [
        ("w1_oom", 0.0, "tex_laptop_oom.png", Vector((-1.05, -2.65, 1.08)), Vector((-0.82, -2.28, 0.96)), Vector((-0.05, 0.05, 0.34)), Vector((-0.08, 0.18, 0.36)), 96),
        ("w1_ok", 0.0, "tex_laptop_colab_ok.png", Vector((-0.82, -2.30, 0.96)), Vector((-1.08, -2.72, 1.10)), Vector((-0.08, 0.18, 0.36)), Vector((-0.02, 0.05, 0.34)), 96),
        ("w2_dc", 60.0, None, Vector((60.0, -4.6, 1.65)), Vector((60.0, -2.6, 1.38)), Vector((60.0, 1.1, 1.35)), Vector((60.0, 1.1, 1.45)), 96),
        ("w3_cpugpu", 120.0, None, Vector((120.0, -4.95, 2.55)), Vector((120.3, -4.15, 2.05)), Vector((120.0, 0.0, 0.22)), Vector((120.4, 0.0, 0.24)), 96),
        ("w4_vault", 180.0, None, Vector((180.0, -5.25, 2.05)), Vector((180.2, -4.45, 1.75)), Vector((180.0, 0.0, 0.68)), Vector((180.2, 0.0, 0.72)), 96),
    ]
    indices = [part] if part is not None else list(range(len(clip_specs)))
    for idx in indices:
        cname, bx, tex_name, p0, p1, t0, t1, total_f = clip_specs[idx]
        clear_scene()
        scene = bpy.context.scene
        setup_world(scene, total_frames=total_f, fps=fps, res_x=1920, res_y=1080, samples=16, bg_color=(0.008, 0.012, 0.024), fog_density=0.007)
        if bx == 0.0:
            build_world_1_night_desk(0.0, tex_name or "tex_laptop_oom.png")
        elif bx == 60.0:
            build_world_2_datacenter(60.0)
        elif bx == 120.0:
            build_world_3_cpu_vs_gpu(120.0)
        else:
            build_world_4_drive_vault(180.0)

        cam_data = bpy.data.cameras.new("HeroCam")
        cam_data.lens = 32.0
        cam = bpy.data.objects.new("HeroCam", cam_data)
        scene.collection.objects.link(cam)
        scene.camera = cam

        tgt = bpy.data.objects.new("HeroTgt", None)
        tgt.location = t0
        scene.collection.objects.link(tgt)
        tr = cam.constraints.new(type="TRACK_TO")
        tr.target = tgt
        tr.track_axis = "TRACK_NEGATIVE_Z"
        tr.up_axis = "UP_Y"

        animate_shot_clamped(cam, tgt, 1, total_f + 1, tuple(p0), tuple(p1), tuple(t0), tuple(t1), 32.0, 34.0)
        finalize_clamped_camera_rig(cam, tgt, {total_f})

        clip_dir = ROOT / "build" / "colab_doc" / "clips3d" / cname
        clip_dir.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(clip_dir / "f_")
        bpy.ops.render.render(animation=True)
        print(f"CLIP3D_DONE: {cname} ({total_f} frames)", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--previews", action="store_true")
    ap.add_argument("--all-clips", action="store_true")
    ap.add_argument("--part", type=int, default=None)
    args, _ = ap.parse_known_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    if args.all_clips:
        render_hero_clips(part=None)
    elif args.part is not None:
        render_hero_clips(part=args.part)
    else:
        render_all_previews()
