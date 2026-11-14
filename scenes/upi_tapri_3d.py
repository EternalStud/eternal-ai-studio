"""Procedural Blender 5.x (EEVEE) Multi-World 3D Scene for POC #3:
'800 ms Mein Chai Tapri UPI Payment Kaise Kaam Karta Hai?' (1080x1920 Vertical).
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
MANIFEST_PATH = Path(argv[0]) if len(argv) >= 1 else Path("build/poc3_audio/audio_manifest.json")
OUT_DIR = Path(argv[1]) if len(argv) >= 2 else Path("build/poc3_3d_spot")
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


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def set_input(node, names: list[str], val) -> None:
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = val
            return


def make_mat(
    name: str,
    base=(0.08, 0.09, 0.12, 1.0),
    metallic: float = 0.25,
    roughness: float = 0.28,
    emit=(0.0, 0.0, 0.0, 1.0),
    emit_str: float = 0.0,
    alpha: float = 1.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, ["Base Color"], base)
    set_input(bsdf, ["Metallic"], metallic)
    set_input(bsdf, ["Roughness"], roughness)
    set_input(bsdf, ["Emission Color", "Emission"], emit)
    set_input(bsdf, ["Emission Strength"], emit_str)
    set_input(bsdf, ["Alpha"], alpha)
    return mat


def add_bevel(obj, width: float = 0.03, segments: int = 3) -> None:
    mod = obj.modifiers.new(name="Bevel", type="BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"


def add_cube(name: str, loc, scale, mat, bevel: float = 0.0, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.rotation_euler = rot
    if bevel > 0:
        add_bevel(o, width=bevel, segments=2)
    o.data.materials.append(mat)
    return o


def add_cyl(name: str, loc, radius: float, depth: float, mat, rot=(0.0, 0.0, 0.0), verts: int = 40):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = rot
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o


def add_torus(name: str, loc, major: float, minor: float, mat, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major, minor_radius=minor, major_segments=56, minor_segments=18, location=loc
    )
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = rot
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o


def add_sphere(name: str, loc, radius: float, mat, scale=(1.0, 1.0, 1.0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=18, radius=radius, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o


def add_light(name: str, ltype: str, loc, energy: float, color=(1.0, 1.0, 1.0), size: float = 3.0, rot_deg=(0, 0, 0)):
    bpy.ops.object.light_add(type=ltype, location=loc)
    lt = bpy.context.active_object
    lt.name = name
    lt.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    lt.data.energy = energy
    lt.data.color = color
    if ltype == "AREA":
        lt.data.size = size
    elif ltype == "POINT":
        lt.data.shadow_soft_size = size
    return lt


def setup_world() -> None:
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.render.fps = FPS
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    scene.render.engine = "BLENDER_EEVEE"
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = SAMPLES
    if hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing = False

    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        scene.view_settings.view_transform = "Filmic"

    world = bpy.data.worlds.new("NightStoryWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.008, 0.011, 0.022, 1.0)
        bg.inputs[1].default_value = 1.0

    try:
        scene.use_nodes = True
        g = bpy.data.node_groups.new("TapriComp", "CompositorNodeTree")
        scene.compositing_node_group = g
        rl = g.nodes.new("CompositorNodeRLayers")
        gl = g.nodes.new("CompositorNodeGlare")
        out = g.nodes.new("NodeGroupOutput")
        g.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        gl.inputs["Type"].default_value = "Fog Glow"
        set_input(gl, ["Quality"], "Medium")
        set_input(gl, ["Threshold"], 1.05)
        set_input(gl, ["Strength"], 0.42)
        set_input(gl, ["Size"], 0.6)
        g.links.new(rl.outputs["Image"], gl.inputs["Image"])
        g.links.new(gl.outputs["Image"], out.inputs[0])
    except Exception as exc:
        print(f"Warning: compositor skipped: {exc}")


# Shared materials palette
def make_palette() -> dict[str, bpy.types.Material]:
    return {
        "asphalt": make_mat("Asphalt", (0.025, 0.028, 0.036, 1), 0.1, 0.42),
        "soil": make_mat("Soil", (0.04, 0.028, 0.02, 1), 0.0, 0.85),
        "wood": make_mat("WoodCounter", (0.14, 0.068, 0.032, 1), 0.08, 0.34),
        "steel": make_mat("Steel", (0.58, 0.62, 0.68, 1), 0.88, 0.22),
        "brass": make_mat("Brass", (0.72, 0.48, 0.16, 1), 0.85, 0.25),
        "chai_liquid": make_mat("ChaiLiquid", (0.45, 0.19, 0.05, 1), 0.05, 0.14, (0.5, 0.2, 0.05, 1), 0.35),
        "glass_clear": make_mat("GlassRim", (0.72, 0.85, 0.96, 1), 0.75, 0.08, (0.2, 0.35, 0.5, 1), 0.15),
        "soundbox_green": make_mat("SoundboxGreen", (0.04, 0.52, 0.28, 1), 0.25, 0.28),
        "dark_grill": make_mat("DarkGrill", (0.018, 0.022, 0.03, 1), 0.4, 0.45),
        "phone_body": make_mat("PhoneBody", (0.02, 0.024, 0.034, 1), 0.85, 0.18),
        "screen_pay": make_mat("ScreenPay", (0.04, 0.14, 0.28, 1), 0.1, 0.15, (0.15, 0.65, 1.0, 1), 1.8),
        "ivory": make_mat("IvoryCard", (0.86, 0.87, 0.90, 1), 0.05, 0.25),
        "obsidian": make_mat("Obsidian", (0.022, 0.024, 0.032, 1), 0.35, 0.28),
        "gold_emit": make_mat("GoldEmit", (1.0, 0.72, 0.14, 1), 0.2, 0.2, (1.0, 0.68, 0.12, 1), 7.5),
        "bulb_emit": make_mat("BulbEmit", (1.0, 0.82, 0.45, 1), 0.0, 0.1, (1.0, 0.68, 0.24, 1), 11.0),
        "emerald_emit": make_mat("EmeraldEmit", (0.1, 0.95, 0.52, 1), 0.1, 0.2, (0.08, 0.95, 0.48, 1), 6.5),
        "cyan_emit": make_mat("CyanEmit", (0.15, 0.82, 1.0, 1), 0.1, 0.2, (0.12, 0.78, 1.0, 1), 5.0),
        "red_emit": make_mat("RedEmit", (1.0, 0.22, 0.18, 1), 0.1, 0.2, (1.0, 0.18, 0.14, 1), 7.0),
        "window_warm": make_mat("WindowWarm", (1.0, 0.78, 0.35, 1), 0.0, 0.2, (1.0, 0.75, 0.30, 1), 3.4),
        "fiber_jacket": make_mat("FiberJacket", (0.05, 0.06, 0.08, 1), 0.55, 0.32),
        "chai_spill": make_mat("ChaiSpill", (0.58, 0.24, 0.05, 1), 0.12, 0.08, (0.65, 0.26, 0.04, 1), 0.85, alpha=1.0),
    }


def build_zone_a_underground(M: dict[str, bpy.types.Material]) -> dict:
    # X = 0: Street cutaway + subterranean fiber cable + glowing light beam
    cx = 0.0
    add_cube("RoadSlab", (cx, 0, 2.2), (16.0, 24.0, 0.45), M["asphalt"])
    for y in range(-10, 12, 4):
        add_cube(f"RoadDash_{y}", (cx, y, 2.46), (0.28, 1.8, 0.05), M["ivory"])
    add_cube("EarthFloor", (cx, 0, -2.5), (18.0, 26.0, 0.5), M["soil"])

    # Cable trench walls (subtle framing)
    add_cube("TrenchBack", (cx + 2.8, 0, -0.2), (0.4, 24.0, 4.4), M["soil"])
    # Optical cable core + translucent glowing inner tube
    add_cyl("FiberCableOuter", (cx, 0, -0.6), 0.22, 24.0, M["fiber_jacket"], rot=(math.radians(90), 0, 0))
    add_cyl("FiberCore", (cx, 0, -0.6), 0.11, 24.2, M["cyan_emit"], rot=(math.radians(90), 0, 0))
    # Armored junction rings
    for y in range(-8, 10, 4):
        add_torus(f"CableBand_{y}", (cx, y, -0.6), 0.27, 0.045, M["steel"], rot=(math.radians(90), 0, 0))

    # Hero Light Pulse Orb + streak (sleek size so it reads as optical beam in trench)
    orb = add_sphere("FiberPulseOrb", (cx, 8.0, -0.6), 0.22, M["gold_emit"], scale=(1.0, 3.2, 1.0))
    halo = add_torus("FiberPulseHalo", (cx, 8.0, -0.6), 0.42, 0.03, M["gold_emit"], rot=(math.radians(90), 0, 0))
    add_light("UnderLamp", "POINT", (cx - 2.0, -2.0, 1.4), 260, (0.25, 0.78, 1.0), size=1.5)
    add_light("StreetTop", "AREA", (cx - 1.5, 0.0, 6.0), 550, (1.0, 0.72, 0.38), size=5.0, rot_deg=(0, 0, 0))
    return {"orb": orb, "halo": halo}


def build_city_bokeh_backdrop(prefix: str, cx: float, cy: float, cz: float, M: dict):
    rng = random.Random(int(cx * 17))
    for i in range(9):
        bx = cx - 8.5 + i * 2.1
        bh = rng.uniform(5.0, 10.5)
        by = cy + rng.uniform(0.0, 3.0)
        add_cube(f"{prefix}_Bldg_{i}", (bx, by, cz + bh * 0.5), (1.7, 1.6, bh), M["obsidian"])
        for row in range(int(bh * 1.1)):
            if rng.random() < 0.42:
                wx = bx + rng.choice([-0.4, 0.0, 0.4])
                wz = cz + 1.0 + row * 0.75
                add_cube(f"{prefix}_Win_{i}_{row}", (wx, by - 0.82, wz), (0.26, 0.04, 0.34), M["window_warm"])


def build_zone_b_tapri(M: dict[str, bpy.types.Material]) -> dict:
    # X = 60: Rainy Evening Chai Tapri Counter
    cx = 60.0
    add_cube("TapriCounter", (cx, 0.0, -0.35), (8.2, 3.6, 0.7), M["wood"], bevel=0.04)
    add_cube("CounterTray", (cx - 1.5, 0.1, 0.03), (2.2, 1.5, 0.06), M["steel"], bevel=0.015)

    # Tea Kettle (left side)
    add_cyl("KettleBody", (cx - 1.9, 0.25, 0.55), 0.52, 0.95, M["brass"])
    add_sphere("KettleDome", (cx - 1.9, 0.25, 1.02), 0.46, M["brass"], scale=(1.0, 1.0, 0.45))
    add_cyl("KettleSpout", (cx - 1.32, 0.25, 0.72), 0.07, 0.75, M["brass"], rot=(0, math.radians(52), 0))
    add_torus("KettleHandle", (cx - 2.38, 0.25, 0.72), 0.32, 0.05, M["obsidian"], rot=(math.radians(90), 0, 0))

    # 2 Cutting Chai Glasses
    for k, gx in enumerate([cx - 0.85, cx - 0.25]):
        add_cyl(f"GlassOuter_{k}", (gx, -0.35, 0.28), 0.17, 0.52, M["glass_clear"], verts=20)
        add_cyl(f"GlassTea_{k}", (gx, -0.35, 0.22), 0.14, 0.36, M["chai_liquid"], verts=20)

    # Hanging Tapri Bulb above counter
    add_cyl("BulbCord", (cx - 0.2, 0.0, 3.6), 0.02, 2.2, M["obsidian"])
    add_cyl("BulbShade", (cx - 0.2, 0.0, 2.55), 0.48, 0.28, M["dark_grill"])
    add_sphere("BulbCore", (cx - 0.2, 0.0, 2.36), 0.16, M["bulb_emit"])
    add_light("TapriWarmBulb", "POINT", (cx - 0.2, -0.3, 2.2), 260, (1.0, 0.68, 0.26), size=0.6)

    # Acrylic QR Standee (center-right)
    add_cube("QRBase", (cx + 0.55, 0.0, 0.08), (1.1, 0.42, 0.14), M["obsidian"], bevel=0.02)
    add_cube("QRPlaque", (cx + 0.55, 0.05, 0.78), (0.98, 0.06, 1.25), M["ivory"], bevel=0.02, rot=(math.radians(-10), 0, 0))
    # Mini QR dark tiles on standee front face
    rng = random.Random(42)
    for r in range(7):
        for c in range(7):
            is_finder = (r < 2 and c < 2) or (r < 2 and c > 4) or (r > 4 and c < 2)
            if is_finder or rng.random() > 0.42:
                tx = cx + 0.55 + (c - 3) * 0.105
                tz = 0.85 + (r - 3) * 0.105
                add_cube(f"MiniQR_{r}_{c}", (tx, 0.005, tz), (0.085, 0.03, 0.085), M["obsidian"])

    # Green Soundbox (right side)
    sb_x = cx + 1.85
    sb_body = add_cube("Soundbox", (sb_x, 0.05, 0.55), (0.85, 0.52, 1.08), M["soundbox_green"], bevel=0.05)
    add_cyl("SoundboxGrill", (sb_x, -0.22, 0.62), 0.30, 0.04, M["dark_grill"], rot=(math.radians(90), 0, 0))
    sb_cone = add_torus("SoundboxCone", (sb_x, -0.24, 0.62), 0.22, 0.03, M["emerald_emit"], rot=(math.radians(90), 0, 0))
    add_cyl("SoundboxAnt", (sb_x + 0.30, 0.10, 1.22), 0.025, 0.40, M["obsidian"])
    # Expanding 3D sound rings + sky beam for 'soundbox' beat
    waves = []
    for k in range(3):
        w = add_torus(f"SBWave_{k}", (sb_x, -0.35 - k * 0.15, 0.62), 0.35 + k * 0.22, 0.025, M["emerald_emit"], rot=(math.radians(90), 0, 0))
        waves.append(w)
    sky_beam = add_cyl("SBSkyBeam", (sb_x + 0.30, 0.10, 4.5), 0.04, 6.2, M["emerald_emit"])

    # Smartphone held in front scanning QR
    phone = add_cube("TapriPhone", (cx + 0.45, -1.55, 0.85), (0.72, 0.07, 1.38), M["phone_body"], bevel=0.03, rot=(math.radians(62), 0, math.radians(-8)))
    add_cube("TapriPhoneScr", (cx + 0.45, -1.52, 0.87), (0.64, 0.02, 1.24), M["screen_pay"], rot=(math.radians(62), 0, math.radians(-8)))
    scan_beam = add_cube("TapriScanLaser", (cx + 0.50, -0.75, 0.82), (0.75, 0.04, 0.03), M["emerald_emit"])

    # 5 Ascending Architecture Rings for Finale beat
    layer_rings = []
    for k in range(5):
        lr = add_torus(f"FinaleRing_{k}", (cx + 0.4, 0.0, 1.35 + k * 0.48), 0.52 - k * 0.04, 0.028, M["gold_emit"])
        layer_rings.append(lr)

    build_city_bokeh_backdrop("TapriCity", cx, 8.5, -1.2, M)
    add_light("TapriRim", "AREA", (cx + 3.5, 3.0, 3.5), 350, (0.25, 0.65, 1.0), size=4.0, rot_deg=(115, 0, 145))
    return {"sb_cone": sb_cone, "waves": waves, "sky_beam": sky_beam, "scan_beam": scan_beam, "layer_rings": layer_rings}


def build_zone_c_qr_macro(M: dict[str, bpy.types.Material]) -> dict:
    # X = 120: Giant 3D QR Matrix + Chai Stain Error Correction
    cx = 120.0
    add_cube("MacroQRCard", (cx, 0.25, 0.0), (5.8, 0.28, 5.8), M["ivory"], bevel=0.08)
    rng = random.Random(101)
    size = 15
    step = 0.32
    backup_blocks = []
    for r in range(size):
        for c in range(size):
            px = cx + (c - (size - 1) / 2.0) * step
            pz = (r - (size - 1) / 2.0) * step
            # Corner finders
            in_tl = (r >= size - 4 and c <= 3)
            in_tr = (r >= size - 4 and c >= size - 4)
            in_bl = (r <= 3 and c <= 3)
            is_finder = in_tl or in_tr or in_bl
            if is_finder:
                border = (
                    (r in (size - 1, size - 4) and c <= 3) or (c in (0, 3) and r >= size - 4) or (r >= size - 2 and c in (1,))
                    or (r in (size - 1, size - 4) and c >= size - 4) or (c in (size - 1, size - 4) and r >= size - 4)
                    or (r in (0, 3) and c <= 3) or (c in (0, 3) and r <= 3)
                )
                center = (r in (size - 2, size - 3) and c in (1, 2)) or (r in (size - 2, size - 3) and c in (size - 2, size - 3)) or (r in (1, 2) and c in (1, 2))
                if border or center:
                    add_cube(f"QRF_{r}_{c}", (px, 0.04, pz), (0.25, 0.18, 0.25), M["gold_emit"] if center else M["obsidian"], bevel=0.015)
            elif rng.random() > 0.45:
                in_damage = (r <= 5 and c >= 9)
                blk = add_cube(f"QRB_{r}_{c}", (px, 0.04, pz), (0.24, 0.16, 0.24), M["emerald_emit"] if in_damage else M["obsidian"], bevel=0.015)
                if in_damage:
                    backup_blocks.append(blk)

    chai_spill = add_cyl("ChaiSpillBlob", (cx + 1.35, -0.04, -1.15), 1.35, 0.08, M["chai_spill"], rot=(math.radians(90), 0, 0))
    laser = add_cube("QRLaserSweep", (cx, -0.22, 2.2), (6.0, 0.06, 0.07), M["cyan_emit"])
    add_light("QRKey", "AREA", (cx - 2.0, -5.0, 4.0), 600, (1.0, 0.92, 0.82), size=6.0, rot_deg=(45, 0, -18))
    add_light("QRRim", "AREA", (cx + 4.0, 3.0, 2.0), 400, (0.2, 0.85, 1.0), size=4.0, rot_deg=(95, 0, 130))
    return {"chai_spill": chai_spill, "laser": laser, "backup_blocks": backup_blocks}


def build_zone_d_encrypt_tower(M: dict[str, bpy.types.Material]) -> dict:
    # X = 180: Phone Lock + Expanding Radio Waves -> City Telecom Tower
    cx = 180.0
    build_city_bokeh_backdrop("TowerCity", cx, 6.0, -4.0, M)
    add_cube("RoofDeck", (cx, 0.0, -2.5), (14.0, 10.0, 0.5), M["asphalt"])

    # Left: Phone launching encrypted orb
    add_cube("EncPhone", (cx - 1.5, -1.0, -1.1), (0.95, 0.12, 1.85), M["phone_body"], bevel=0.04, rot=(math.radians(52), 0, math.radians(-18)))
    add_cube("EncScreen", (cx - 1.5, -0.94, -1.08), (0.82, 0.04, 1.65), M["screen_pay"], rot=(math.radians(52), 0, math.radians(-18)))

    lock_ring = add_torus("EncLockRing", (cx - 1.1, -0.6, 0.45), 0.58, 0.07, M["gold_emit"], rot=(math.radians(15), math.radians(20), 0))
    lock_core = add_sphere("EncDataOrb", (cx - 1.1, -0.6, 0.45), 0.28, M["cyan_emit"])

    # Right: Telecom Tower lattice mast
    tx, ty = cx + 1.9, 1.8
    add_cyl("TowerMast", (tx, ty, 0.8), 0.14, 6.2, M["steel"])
    for kz in [-1.2, 0.2, 1.6, 2.8]:
        w = 0.8 - (kz + 1.2) * 0.14
        add_torus(f"TowerRing_{kz}", (tx, ty, kz), max(0.18, w), 0.035, M["steel"])
    beacon = add_sphere("TowerBeacon", (tx, ty, 4.0), 0.16, M["red_emit"])

    # Expanding RF torus arcs
    rf_waves = []
    for k in range(4):
        rw = add_torus(f"RFWave_{k}", (cx - 1.0, -0.4, 0.45), 0.8 + k * 0.85, 0.035, M["gold_emit"], rot=(math.radians(78), math.radians(-35), 0))
        rf_waves.append(rw)

    add_light("TowerKey", "AREA", (cx - 3.0, -6.0, 5.0), 500, (0.65, 0.82, 1.0), size=6.0, rot_deg=(45, 0, -25))
    return {"lock_ring": lock_ring, "lock_core": lock_core, "rf_waves": rf_waves, "beacon": beacon}


def build_zone_e_npci_grid(M: dict[str, bpy.types.Material]) -> dict:
    # X = 240: Expansive Midnight Fiber Grid + 3-Way Bank Switch
    cx = 240.0
    add_cube("GridFloor", (cx, 2.0, -1.5), (36.0, 36.0, 0.2), M["obsidian"])
    # Subtle glowing floor grid strips
    for g in range(-12, 14, 3):
        add_cube(f"GridX_{g}", (cx, g + 2.0, -1.39), (32.0, 0.03, 0.02), M["fiber_jacket"])
        add_cube(f"GridY_{g}", (cx + g, 2.0, -1.39), (0.03, 32.0, 0.02), M["fiber_jacket"])

    # Distant background server towers
    rng = random.Random(77)
    for k in range(14):
        sx = cx + rng.uniform(-9.0, 9.0)
        sy = rng.uniform(5.0, 14.0)
        sh = rng.uniform(1.6, 3.8)
        add_cube(f"FarRack_{k}", (sx, sy, -1.4 + sh * 0.5), (0.7, 0.7, sh), M["dark_grill"], bevel=0.03)
        add_cube(f"FarTop_{k}", (sx, sy, -1.4 + sh + 0.05), (0.6, 0.6, 0.06), M["cyan_emit"])

    # 3 Hero Towers: YOUR BANK (L), NPCI SWITCH (Center), CHAIWALA BANK (R)
    def hero_rack(name, rx, ry, h, accent_mat):
        add_cube(name, (rx, ry, -1.4 + h * 0.5), (1.15, 1.15, h), M["dark_grill"], bevel=0.05)
        for s in range(4):
            add_cube(f"{name}_LED_{s}", (rx, ry - 0.59, -0.7 + s * 0.55), (0.82, 0.04, 0.12), accent_mat)
        return add_sphere(f"{name}_Crown", (rx, ry, -1.4 + h + 0.42), 0.28, accent_mat)

    c_you = hero_rack("YourBank", cx - 2.2, -0.8, 2.4, M["cyan_emit"])
    c_npci = hero_rack("NPCISwitch", cx, 2.2, 3.4, M["gold_emit"])
    c_chai = hero_rack("ChaiBank", cx + 2.2, -0.8, 2.4, M["emerald_emit"])

    # Fiber conduits on ground between them
    add_cube("PipeLeft", (cx - 1.1, 0.7, -1.35), (0.09, 3.8, 0.06), M["cyan_emit"], rot=(0, 0, math.radians(-36)))
    add_cube("PipeRight", (cx + 1.1, 0.7, -1.35), (0.09, 3.8, 0.06), M["emerald_emit"], rot=(0, 0, math.radians(36)))

    pkt_sphere = add_sphere("NPCIPulse", (cx - 2.2, -0.8, -1.1), 0.24, M["gold_emit"])
    npci_ring = add_torus("NPCIHalo", (cx, 2.2, 2.55), 0.85, 0.045, M["gold_emit"], rot=(math.radians(75), 0, 0))
    add_light("GridKey", "AREA", (cx, -6.0, 7.0), 650, (0.5, 0.78, 1.0), size=8.0, rot_deg=(48, 0, 0))
    return {"c_you": c_you, "c_npci": c_npci, "c_chai": c_chai, "pkt": pkt_sphere, "npci_ring": npci_ring}


def animate_all(rig: dict) -> None:
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    cam_tgt = bpy.context.active_object
    cam_tgt.name = "CamTarget"

    bpy.ops.object.camera_add(location=(0, -8, 1))
    cam = bpy.context.active_object
    cam.name = "MainCam"
    bpy.context.scene.camera = cam
    cam.data.lens = 36
    c = cam.constraints.new(type="TRACK_TO")
    c.target = cam_tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"

    def cut_cam(frame: int, cloc, tloc, lens: float = 36.0):
        # Hold previous pose up to frame-1 if frame > 1 so camera jumps instantaneously cleanly at cuts!
        cam.location = cloc
        cam.keyframe_insert("location", frame=frame)
        cam_tgt.location = tloc
        cam_tgt.keyframe_insert("location", frame=frame)
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=frame)

    # Map each beat cleanly
    b0 = BEAT_MAP["underground_hook"]
    f0s, f0e = ms_to_frame(0), ms_to_frame(b0["end_ms"])
    cut_cam(f0s, (-4.2, -6.2, 0.9), (0.0, 1.5, 0.2), 34)
    cut_cam(f0e, (-3.4, -3.5, 0.4), (0.0, -2.5, -0.2), 32)
    rig["a"]["orb"].location = (0, 9.0, -0.6)
    rig["a"]["orb"].keyframe_insert("location", frame=f0s)
    rig["a"]["orb"].location = (0, -7.0, -0.6)
    rig["a"]["orb"].keyframe_insert("location", frame=f0e)
    rig["a"]["halo"].location = (0, 9.0, -0.6)
    rig["a"]["halo"].keyframe_insert("location", frame=f0s)
    rig["a"]["halo"].location = (0, -7.0, -0.6)
    rig["a"]["halo"].keyframe_insert("location", frame=f0e)

    # Tapri Intro (X=60)
    b1 = BEAT_MAP["tapri_intro"]
    f1s, f1e = ms_to_frame(b1["start_ms"]), ms_to_frame(b1["end_ms"])
    cut_cam(f1s, (56.5, -5.2, 2.2), (59.5, 0.0, 0.65), 34)
    cut_cam(f1e, (60.2, -5.0, 1.75), (60.2, -0.1, 0.72), 36)

    # QR Repair (X=120)
    b2 = BEAT_MAP["qr_repair"]
    f2s, f2e = ms_to_frame(b2["start_ms"]), ms_to_frame(b2["end_ms"])
    f2m = int((f2s + f2e) / 2)
    cut_cam(f2s, (118.4, -7.8, 0.4), (120.0, 0.0, 0.0), 42)
    cut_cam(f2e, (121.4, -7.2, -0.5), (120.2, 0.0, -0.1), 44)
    rig["c"]["laser"].location = (120.0, -0.22, 2.4)
    rig["c"]["laser"].keyframe_insert("location", frame=f2s)
    rig["c"]["laser"].location = (120.0, -0.22, -2.4)
    rig["c"]["laser"].keyframe_insert("location", frame=f2e)
    rig["c"]["chai_spill"].scale = (0.01, 0.01, 0.01)
    rig["c"]["chai_spill"].keyframe_insert("scale", frame=f2s)
    rig["c"]["chai_spill"].scale = (0.01, 0.01, 0.01)
    rig["c"]["chai_spill"].keyframe_insert("scale", frame=f2m - 8)
    rig["c"]["chai_spill"].scale = (1.15, 1.15, 1.0)
    rig["c"]["chai_spill"].keyframe_insert("scale", frame=f2m + 10)

    # Encrypt & Cell Tower (X=180)
    b3 = BEAT_MAP["encrypt_tower"]
    f3s, f3e = ms_to_frame(b3["start_ms"]), ms_to_frame(b3["end_ms"])
    cut_cam(f3s, (177.8, -6.2, 0.4), (179.3, 0.0, 0.2), 34)
    cut_cam(f3e, (181.6, -7.4, 1.2), (180.6, 0.6, 1.3), 32)
    rig["d"]["lock_ring"].rotation_euler = (0.2, 0.3, 0.0)
    rig["d"]["lock_ring"].keyframe_insert("rotation_euler", frame=f3s)
    rig["d"]["lock_ring"].rotation_euler = (0.2, 0.3, math.pi * 2.5)
    rig["d"]["lock_ring"].keyframe_insert("rotation_euler", frame=f3e)
    for k, w in enumerate(rig["d"]["rf_waves"]):
        sc0 = 0.25 + k * 0.15
        w.scale = (sc0, sc0, 1.0)
        w.keyframe_insert("scale", frame=f3s)
        w.scale = (sc0 + 1.6, sc0 + 1.6, 1.0)
        w.keyframe_insert("scale", frame=f3e)

    # NPCI Grid (X=240)
    b4 = BEAT_MAP["npci_grid"]
    f4s, f4e = ms_to_frame(b4["start_ms"]), ms_to_frame(b4["end_ms"])
    f4m = int((f4s + f4e) / 2)
    cut_cam(f4s, (238.5, -9.2, 4.2), (240.0, 0.6, 0.3), 30)
    cut_cam(f4e, (241.5, -8.8, 3.6), (240.0, 0.6, 0.5), 31)
    rig["e"]["pkt"].location = (237.8, -0.8, -1.1)
    rig["e"]["pkt"].keyframe_insert("location", frame=f4s)
    rig["e"]["pkt"].location = (240.0, 2.2, 0.4)
    rig["e"]["pkt"].keyframe_insert("location", frame=f4m)
    rig["e"]["pkt"].location = (242.2, -0.8, -1.1)
    rig["e"]["pkt"].keyframe_insert("location", frame=f4e)
    rig["e"]["npci_ring"].rotation_euler = (math.radians(75), 0, 0)
    rig["e"]["npci_ring"].keyframe_insert("rotation_euler", frame=f4s)
    rig["e"]["npci_ring"].rotation_euler = (math.radians(75), 0, math.pi * 3)
    rig["e"]["npci_ring"].keyframe_insert("rotation_euler", frame=f4e)

    # Soundbox Hero Shot (back to X=60!)
    b5 = BEAT_MAP["soundbox"]
    f5s, f5e = ms_to_frame(b5["start_ms"]), ms_to_frame(b5["end_ms"])
    cut_cam(f5s, (62.8, -3.5, 1.15), (61.85, 0.0, 0.65), 42)
    cut_cam(f5e, (62.35, -2.85, 0.95), (61.85, 0.0, 0.65), 46)

    # Finale Layers Elevated Shot (X=60!)
    b6 = BEAT_MAP["finale_layers"]
    f6s, f6e = ms_to_frame(b6["start_ms"]), TOTAL_FRAMES
    cut_cam(f6s, (60.2, -6.6, 2.8), (60.0, 0.0, 1.45), 31)
    cut_cam(f6e, (59.0, -7.2, 3.1), (60.0, 0.0, 1.55), 30)

    # Show soundbox waves & sky beam ONLY during 'soundbox', and finale rings ONLY during 'finale_layers'
    rig["b"]["sky_beam"].scale = (0.0, 0.0, 0.0)
    rig["b"]["sky_beam"].keyframe_insert("scale", frame=1)
    rig["b"]["sky_beam"].scale = (0.0, 0.0, 0.0)
    rig["b"]["sky_beam"].keyframe_insert("scale", frame=f5s - 1)
    rig["b"]["sky_beam"].scale = (1.0, 1.0, 1.0)
    rig["b"]["sky_beam"].keyframe_insert("scale", frame=f5s)
    rig["b"]["sky_beam"].scale = (1.0, 1.0, 1.0)
    rig["b"]["sky_beam"].keyframe_insert("scale", frame=f6s - 1)
    rig["b"]["sky_beam"].scale = (0.0, 0.0, 0.0)
    rig["b"]["sky_beam"].keyframe_insert("scale", frame=f6s)

    for k, w in enumerate(rig["b"]["waves"]):
        w.scale = (0.0, 0.0, 0.0)
        w.keyframe_insert("scale", frame=1)
        w.scale = (0.0, 0.0, 0.0)
        w.keyframe_insert("scale", frame=f5s - 1)
        w.scale = (0.35 + k * 0.2, 0.35 + k * 0.2, 1.0)
        w.keyframe_insert("scale", frame=f5s)
        w.scale = (1.1 + k * 0.4, 1.1 + k * 0.4, 1.0)
        w.keyframe_insert("scale", frame=f6s - 1)
        w.scale = (0.0, 0.0, 0.0)
        w.keyframe_insert("scale", frame=f6s)

    for lr in rig["b"]["layer_rings"]:
        lr.scale = (0.0, 0.0, 0.0)
        lr.keyframe_insert("scale", frame=1)
        lr.scale = (0.0, 0.0, 0.0)
        lr.keyframe_insert("scale", frame=f6s - 1)
        lr.scale = (1.0, 1.0, 1.0)
        lr.keyframe_insert("scale", frame=f6s)

    # Set CONSTANT interpolation ONLY across the 1-frame cut gaps so camera never flies across X=0->60!
    cut_frames = {f1s, f2s, f3s, f4s, f5s, f6s}
    for action in bpy.data.actions:
        layers = getattr(action, "layers", None)
        fcurves_list = []
        if getattr(action, "fcurves", None):
            fcurves_list.extend(action.fcurves)
        if layers:
            for layer in layers:
                for strip in getattr(layer, "strips", []):
                    for bag in getattr(strip, "channelbags", []):
                        fcurves_list.extend(bag.fcurves)
        for fc in fcurves_list:
            for kp in fc.keyframe_points:
                fr = int(round(kp.co[0]))
                if (fr + 1) in cut_frames or fr in cut_frames:
                    # Handle cleanly: incoming segment before cut stays CONSTANT
                    if (fr + 1) in cut_frames:
                        kp.interpolation = "CONSTANT"
                    else:
                        kp.interpolation = "BEZIER"
                else:
                    kp.interpolation = "BEZIER"


def main() -> None:
    clear_scene()
    setup_world()
    M = make_palette()
    rig = {
        "a": build_zone_a_underground(M),
        "b": build_zone_b_tapri(M),
        "c": build_zone_c_qr_macro(M),
        "d": build_zone_d_encrypt_tower(M),
        "e": build_zone_e_npci_grid(M),
    }
    animate_all(rig)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene

    if MODE == "spot":
        for idx, beat in enumerate(MANIFEST["beats"]):
            mid_ms = beat["start_ms"] + int(beat["duration_ms"] * 0.62)
            fr = ms_to_frame(mid_ms)
            scene.frame_set(fr)
            out_png = OUT_DIR / f"spot3d_{idx:02d}_{beat['beat_id']}.png"
            scene.render.filepath = str(out_png)
            bpy.ops.render.render(write_still=True)
            print(f"SPOT3D_SAVED {out_png} (frame={fr})", flush=True)
    else:
        scene.render.filepath = str(OUT_DIR / "frame_")
        bpy.ops.render.render(animation=True)
        print(f"ANIM3D_DONE frames={TOTAL_FRAMES}", flush=True)


if __name__ == "__main__":
    main()
