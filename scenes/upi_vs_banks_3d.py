"""Procedural Blender 5.x (EEVEE) 3D Scene: Legacy 2-Day Banking vs 0.8s Instant Rail (9:16 Vertical Optimized)."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
MANIFEST_PATH = Path(argv[0]) if len(argv) >= 1 else Path("tmp/poc1_upi/audio_manifest.json")
OUT_DIR = Path(argv[1]) if len(argv) >= 2 else Path("tmp/poc1_upi/frames")
RES_X = int(argv[2]) if len(argv) >= 3 else 1080
RES_Y = int(argv[3]) if len(argv) >= 4 else 1920
FPS = int(argv[4]) if len(argv) >= 5 else 30
SAMPLES = int(argv[5]) if len(argv) >= 6 else 24
MODE = argv[6] if len(argv) >= 7 else "anim"

MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
TOTAL_MS = MANIFEST["total_ms"]
TOTAL_FRAMES = max(30, int(math.ceil((TOTAL_MS / 1000.0) * FPS)))


def ms_to_frame(ms: float) -> int:
    return max(1, min(TOTAL_FRAMES, int(round((ms / 1000.0) * FPS)) + 1))


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def set_input(node, name_candidates: list[str], value) -> None:
    for name in name_candidates:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return


def make_pbr_mat(
    name: str,
    base_color=(0.05, 0.07, 0.12, 1.0),
    metallic: float = 0.35,
    roughness: float = 0.22,
    emission_color=(0.0, 0.0, 0.0, 1.0),
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, ["Base Color"], base_color)
    set_input(bsdf, ["Metallic"], metallic)
    set_input(bsdf, ["Roughness"], roughness)
    set_input(bsdf, ["Emission Color", "Emission"], emission_color)
    set_input(bsdf, ["Emission Strength"], emission_strength)
    return mat


def smooth_all_fcurves() -> None:
    for action in bpy.data.actions:
        fcurves = getattr(action, "fcurves", None)
        if fcurves:
            for fc in fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"
                    kp.handle_left_type = "AUTO_CLAMPED"
                    kp.handle_right_type = "AUTO_CLAMPED"
        layers = getattr(action, "layers", None)
        if layers:
            for layer in layers:
                for strip in getattr(layer, "strips", []):
                    for bag in getattr(strip, "channelbags", []):
                        for fc in getattr(bag, "fcurves", []):
                            for kp in fc.keyframe_points:
                                kp.interpolation = "BEZIER"
                                kp.handle_left_type = "AUTO_CLAMPED"
                                kp.handle_right_type = "AUTO_CLAMPED"


def add_bevel(obj, width: float = 0.035, segments: int = 3) -> None:
    mod = obj.modifiers.new(name="Bevel", type="BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"


def add_text_3d(
    name: str,
    text: str,
    location: tuple[float, float, float],
    size: float,
    mat: bpy.types.Material,
    extrude: float = 0.035,
    rot_euler=(math.radians(90), 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.object.text_add(location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.body = text
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = extrude
    obj.data.bevel_depth = 0.008
    obj.rotation_euler = rot_euler
    obj.data.materials.append(mat)
    return obj


def setup_world_and_compositor() -> None:
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
    # Disable noisy screen-space GI raytracing on fast Eevee studio shots for crisp clean metal/glow
    if hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing = False

    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        scene.view_settings.view_transform = "Filmic"

    world = bpy.data.worlds.new("StudioWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.007, 0.012, 0.028, 1.0)
        bg.inputs[1].default_value = 1.0

    try:
        scene.use_nodes = True
        g = bpy.data.node_groups.new("StudioComp", "CompositorNodeTree")
        scene.compositing_node_group = g
        rl = g.nodes.new("CompositorNodeRLayers")
        gl = g.nodes.new("CompositorNodeGlare")
        out = g.nodes.new("NodeGroupOutput")
        g.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        gl.inputs["Type"].default_value = "Fog Glow"
        set_input(gl, ["Quality"], "Medium")
        set_input(gl, ["Threshold"], 1.1)
        set_input(gl, ["Strength"], 0.48)
        set_input(gl, ["Size"], 0.65)
        g.links.new(rl.outputs["Image"], gl.inputs["Image"])
        g.links.new(gl.outputs["Image"], out.inputs[0])
    except Exception as exc:
        print(f"Warning: compositor bloom skipped: {exc}")


def setup_lights() -> None:
    def add_area(name, loc, rot_deg, energy, size, color):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lt = bpy.context.active_object
        lt.name = name
        lt.rotation_euler = tuple(math.radians(a) for a in rot_deg)
        lt.data.energy = energy
        lt.data.size = size
        lt.data.color = color

    add_area("KeyLight", (0.0, -7.5, 11.5), (32, 0, 0), 1600, 9.0, (0.88, 0.94, 1.0))
    add_area("CyanRim", (6.5, 8.0, 6.0), (118, 0, 150), 1200, 6.0, (0.12, 0.85, 1.0))
    add_area("AmberRim", (-6.0, 5.5, 5.5), (115, 0, -145), 1100, 5.5, (1.0, 0.58, 0.16))


def build_studio_floor(mat_floor, mat_grid) -> None:
    bpy.ops.mesh.primitive_plane_add(size=90, location=(0.0, 2.0, 0.0))
    floor = bpy.context.active_object
    floor.name = "StudioFloor"
    floor.data.materials.append(mat_floor)

    for i in range(-12, 16, 2):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(float(i), 2.0, 0.004))
        bar_x = bpy.context.active_object
        bar_x.scale = (0.014, 30.0, 0.004)
        bar_x.data.materials.append(mat_grid)

        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, float(i), 0.004))
        bar_y = bpy.context.active_object
        bar_y.scale = (30.0, 0.014, 0.004)
        bar_y.data.materials.append(mat_grid)


def build_legacy_vault(beats: list[dict]) -> Vector:
    """Zone A (Left-Back): Open-cage Legacy Batch Vault filled with shiny stacked gold bullion."""
    mat_metal = make_pbr_mat("DarkGunmetal", (0.08, 0.09, 0.13, 1.0), metallic=0.90, roughness=0.22)
    mat_gold = make_pbr_mat(
        "LegacyGold",
        (1.0, 0.72, 0.18, 1.0),
        metallic=0.96,
        roughness=0.16,
        emission_color=(1.0, 0.55, 0.10, 1.0),
        emission_strength=0.35,
    )
    mat_red = make_pbr_mat(
        "GateCrimson",
        (1.0, 0.10, 0.16, 1.0),
        metallic=0.2,
        roughness=0.15,
        emission_color=(1.0, 0.10, 0.16, 1.0),
        emission_strength=5.0,
    )
    mat_amber_txt = make_pbr_mat(
        "AmberText",
        (1.0, 0.68, 0.16, 1.0),
        metallic=0.6,
        roughness=0.2,
        emission_color=(1.0, 0.55, 0.12, 1.0),
        emission_strength=2.2,
    )

    cx, cy = -3.4, 2.2

    # Heavy octagonal plinth
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=2.3, depth=0.32, location=(cx, cy, 0.16))
    base = bpy.context.active_object
    add_bevel(base, 0.04)
    base.data.materials.append(mat_metal)

    # Top open-frame collar so gold bars stay clearly visible inside!
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=2.1, depth=0.18, location=(cx, cy, 2.55))
    roof = bpy.context.active_object
    add_bevel(roof, 0.03)
    roof.data.materials.append(mat_metal)

    # 4 corner steel stanchions
    for dx in (-1.45, 1.45):
        for dy in (-1.2, 1.2):
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx + dx, cy + dy, 1.4))
            p = bpy.context.active_object
            p.scale = (0.14, 0.14, 2.3)
            add_bevel(p, 0.02)
            p.data.materials.append(mat_metal)

    # 3 glowing red horizontal laser lock bars across the front of the cage
    b2_start = ms_to_frame(beats[1]["start_ms"])
    b2_end = ms_to_frame(beats[1]["end_ms"])
    for idx, lz in enumerate((0.85, 1.40, 1.95)):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16,
            radius=0.045,
            depth=2.85,
            location=(cx + 1.46, cy, lz),
            rotation=(math.radians(90), 0.0, 0.0),
        )
        laser = bpy.context.active_object
        laser.data.materials.append(mat_red)
        # Also across the -Y face (facing camera)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16,
            radius=0.045,
            depth=2.85,
            location=(cx, cy - 1.22, lz),
            rotation=(0.0, math.radians(90), 0.0),
        )
        laser_front = bpy.context.active_object
        laser_front.data.materials.append(mat_red)
        laser_front.keyframe_insert("location", frame=1)
        laser_front.keyframe_insert("location", frame=b2_end - 12)
        laser_front.location = (cx, cy - 1.22, lz + (0.45 if idx == 2 else 0.0))
        laser_front.keyframe_insert("location", frame=b2_end + 8)

    # Stacked shiny gold bullion bars dropping into the vault
    for row in range(3):
        for col in range(3):
            for lvl in range(2):
                bx = cx - 0.72 + col * 0.72
                by = cy - 0.62 + row * 0.62
                bz = 0.50 + lvl * 0.42
                bpy.ops.mesh.primitive_cube_add(size=0.36, location=(bx, by, bz + 1.2))
                bar = bpy.context.active_object
                bar.scale = (1.25, 0.85, 0.70)
                add_bevel(bar, 0.03)
                bar.data.materials.append(mat_gold)

                drop_f = b2_start + (row * 3 + col + lvl * 2) * 4
                bar.location = (bx, by, bz + 1.2)
                bar.keyframe_insert("location", frame=max(1, drop_f - 8))
                bar.location = (bx, by, bz)
                bar.keyframe_insert("location", frame=min(TOTAL_FRAMES, drop_f + 4))

    # Rotating warning ring above vault
    bpy.ops.mesh.primitive_torus_add(major_radius=1.35, minor_radius=0.045, location=(cx, cy, 3.05))
    ring = bpy.context.active_object
    ring.rotation_euler = (math.radians(16), 0.0, 0.0)
    ring.data.materials.append(mat_red)
    ring.keyframe_insert("rotation_euler", frame=1)
    ring.rotation_euler = (math.radians(16), 0.0, math.radians(180))
    ring.keyframe_insert("rotation_euler", frame=TOTAL_FRAMES)

    add_text_3d(
        "LabelLegacy",
        "2 DAYS",
        (cx, cy, 3.85),
        size=0.72,
        mat=mat_amber_txt,
        rot_euler=(math.radians(90), 0.0, math.radians(12)),
    )
    return Vector((cx, cy, 1.5))


def build_instant_rail(beats: list[dict], ping_events_ms: list[int]) -> list[Vector]:
    """Zone B (Right-Front sweeping into depth): 4-node Instant Payment Rail."""
    mat_dark = make_pbr_mat("NodeFrame", (0.05, 0.07, 0.13, 1.0), metallic=0.88, roughness=0.20)
    mat_screen = make_pbr_mat(
        "PhoneScreen",
        (0.05, 0.35, 0.55, 1.0),
        metallic=0.1,
        roughness=0.1,
        emission_color=(0.08, 0.75, 1.0, 1.0),
        emission_strength=2.2,
    )
    mat_cyan = make_pbr_mat(
        "NeonCyan",
        (0.05, 0.88, 1.0, 1.0),
        metallic=0.1,
        roughness=0.15,
        emission_color=(0.05, 0.88, 1.0, 1.0),
        emission_strength=5.2,
    )
    mat_packet = make_pbr_mat(
        "PacketCore",
        (1.0, 1.0, 1.0, 1.0),
        metallic=0.0,
        roughness=0.05,
        emission_color=(0.40, 0.96, 1.0, 1.0),
        emission_strength=13.0,
    )
    mat_cyan_txt = make_pbr_mat(
        "CyanText",
        (0.22, 0.92, 1.0, 1.0),
        metallic=0.3,
        roughness=0.2,
        emission_color=(0.15, 0.88, 1.0, 1.0),
        emission_strength=2.4,
    )
    mat_green_txt = make_pbr_mat(
        "GreenText",
        (0.15, 1.0, 0.55, 1.0),
        metallic=0.3,
        roughness=0.2,
        emission_color=(0.12, 1.0, 0.48, 1.0),
        emission_strength=2.8,
    )

    # Arranged in a 9:16-friendly staggered curve so labels never overlap from front angle
    nodes_meta = [
        ("PHONE", Vector((1.5, -3.4, 0.0)), 1.65),
        ("APP NODE", Vector((3.9, -0.6, 0.0)), 2.15),
        ("NPCI SWITCH", Vector((4.2, 2.8, 0.0)), 3.05),
        ("RECEIVER", Vector((1.6, 6.2, 0.0)), 2.40),
    ]

    receiver_glow_mat = make_pbr_mat(
        "ReceiverHalo",
        (0.05, 0.80, 1.0, 1.0),
        metallic=0.1,
        roughness=0.15,
        emission_color=(0.05, 0.80, 1.0, 1.0),
        emission_strength=3.5,
    )

    rail_points: list[Vector] = []
    b3_start = ms_to_frame(beats[2]["start_ms"])
    hop_frames = [ms_to_frame(ms) for ms in ping_events_ms]

    for idx, (label, pos, height) in enumerate(nodes_meta):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6 if idx == 2 else 8,
            radius=1.15 if idx == 2 else 0.88,
            depth=0.26,
            location=(pos.x, pos.y, 0.13),
        )
        ped = bpy.context.active_object
        add_bevel(ped, 0.03)
        ped.data.materials.append(mat_dark)

        if idx == 0:
            # Sleek 3D Smartphone monolith
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pos.x, pos.y, 0.26 + height * 0.5))
            phone = bpy.context.active_object
            phone.scale = (0.78, 0.12, height)
            phone.rotation_euler = (0.0, 0.0, math.radians(-22))
            add_bevel(phone, 0.035)
            phone.data.materials.append(mat_dark)

            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pos.x, pos.y, 0.26 + height * 0.5))
            scr = bpy.context.active_object
            scr.scale = (0.68, 0.135, height * 0.86)
            scr.rotation_euler = (0.0, 0.0, math.radians(-22))
            scr.data.materials.append(mat_screen)
        elif idx == 2:
            # Hero NPCI Switch: hexagonal tower + 4 vertical neon light blades + floating core
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=6, radius=0.52, depth=height, location=(pos.x, pos.y, 0.26 + height * 0.5)
            )
            core = bpy.context.active_object
            add_bevel(core, 0.03)
            core.data.materials.append(mat_dark)

            for b in range(4):
                ang = b * (math.pi / 2.0) + math.pi / 4.0
                bpy.ops.mesh.primitive_cube_add(
                    size=1.0,
                    location=(
                        pos.x + 0.52 * math.cos(ang),
                        pos.y + 0.52 * math.sin(ang),
                        0.26 + height * 0.5,
                    ),
                )
                blade = bpy.context.active_object
                blade.scale = (0.05, 0.14, height * 0.82)
                blade.rotation_euler = (0.0, 0.0, ang)
                blade.data.materials.append(mat_cyan)
        else:
            # Dark metallic bank/app server column with glowing horizontal crown strip
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=16 if idx == 1 else 8,
                radius=0.40,
                depth=height,
                location=(pos.x, pos.y, 0.26 + height * 0.5),
            )
            col = bpy.context.active_object
            add_bevel(col, 0.03)
            col.data.materials.append(mat_dark)

            bpy.ops.mesh.primitive_cylinder_add(
                vertices=16 if idx == 1 else 8,
                radius=0.42,
                depth=0.22,
                location=(pos.x, pos.y, 0.26 + height * 0.85),
            )
            crown = bpy.context.active_object
            crown.data.materials.append(receiver_glow_mat if idx == 3 else mat_cyan)

        ring_z = 0.26 + height * 0.65
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.82 if idx == 2 else 0.58,
            minor_radius=0.032,
            location=(pos.x, pos.y, ring_z),
        )
        halo = bpy.context.active_object
        halo.rotation_euler = (math.radians(16), math.radians(-12), 0.0)
        halo.data.materials.append(receiver_glow_mat if idx == 3 else mat_cyan)
        halo.keyframe_insert("rotation_euler", frame=1)
        halo.rotation_euler = (math.radians(16), math.radians(-12), math.radians(720))
        halo.keyframe_insert("rotation_euler", frame=TOTAL_FRAMES)

        add_text_3d(
            f"NodeLbl_{idx}",
            label,
            (pos.x, pos.y, 0.26 + height + 0.55),
            size=0.27,
            mat=mat_green_txt if idx == 3 else mat_cyan_txt,
            rot_euler=(math.radians(90), 0.0, math.radians(-12)),
        )

        rail_points.append(Vector((pos.x, pos.y, ring_z)))

        if idx < len(hop_frames):
            hf = hop_frames[idx]
            bpy.ops.mesh.primitive_torus_add(
                major_radius=0.65,
                minor_radius=0.04,
                location=(pos.x, pos.y, ring_z),
            )
            wave = bpy.context.active_object
            wave_mat = make_pbr_mat(
                f"WaveMat_{idx}",
                (0.1, 1.0, 0.50, 1.0) if idx == 3 else (0.1, 0.9, 1.0, 1.0),
                emission_color=(0.1, 1.0, 0.50, 1.0) if idx == 3 else (0.1, 0.9, 1.0, 1.0),
                emission_strength=7.5,
            )
            wave.data.materials.append(wave_mat)
            wave.scale = (0.01, 0.01, 0.01)
            wave.keyframe_insert("scale", frame=max(1, hf - 2))
            wave.scale = (2.7, 2.7, 2.7)
            wave.keyframe_insert("scale", frame=min(TOTAL_FRAMES, hf + 16))
            wave.scale = (0.01, 0.01, 0.01)
            wave.keyframe_insert("scale", frame=min(TOTAL_FRAMES, hf + 20))

    # Receiver glows Emerald Green on final hop
    if len(hop_frames) >= 4:
        final_hop = hop_frames[3]
        bsdf = receiver_glow_mat.node_tree.nodes.get("Principled BSDF")
        em_col = bsdf.inputs["Emission Color"]
        em_str = bsdf.inputs["Emission Strength"]
        em_col.default_value = (0.05, 0.80, 1.0, 1.0)
        em_str.default_value = 3.5
        em_col.keyframe_insert("default_value", frame=max(1, final_hop - 3))
        em_str.keyframe_insert("default_value", frame=max(1, final_hop - 3))
        em_col.default_value = (0.10, 1.0, 0.45, 1.0)
        em_str.default_value = 9.5
        em_col.keyframe_insert("default_value", frame=min(TOTAL_FRAMES, final_hop + 4))
        em_str.keyframe_insert("default_value", frame=min(TOTAL_FRAMES, final_hop + 4))

    # Curved fiber-optic conduit connecting all 4 nodes
    curve_data = bpy.data.curves.new("InstantFiberCurve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = 0.055
    curve_data.bevel_resolution = 6
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(len(rail_points) - 1)
    for i, pt in enumerate(rail_points):
        bp = spline.bezier_points[i]
        bp.co = pt
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    curve_obj = bpy.data.objects.new("InstantFiberRail", curve_data)
    bpy.context.collection.objects.link(curve_obj)
    curve_obj.data.materials.append(mat_cyan)

    # Hero Data Packet Sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.27, location=rail_points[0])
    packet = bpy.context.active_object
    packet.data.materials.append(mat_packet)

    bpy.ops.mesh.primitive_torus_add(major_radius=0.42, minor_radius=0.03, location=rail_points[0])
    packet_ring = bpy.context.active_object
    packet_ring.parent = packet
    packet_ring.location = (0, 0, 0)
    packet_ring.data.materials.append(mat_cyan)
    packet_ring.keyframe_insert("rotation_euler", frame=1)
    packet_ring.rotation_euler = (math.radians(360), math.radians(720), 0.0)
    packet_ring.keyframe_insert("rotation_euler", frame=TOTAL_FRAMES)

    packet.location = rail_points[0]
    packet.keyframe_insert("location", frame=1)
    packet.keyframe_insert("location", frame=max(1, b3_start))
    for i, pt in enumerate(rail_points):
        if i < len(hop_frames):
            packet.location = pt
            packet.keyframe_insert("location", frame=hop_frames[i])

    # Hero Title positioned well above NPCI SWITCH so zero overlap!
    add_text_3d(
        "LabelUPI",
        "0.8 SEC",
        (3.4, 2.2, 5.15),
        size=0.80,
        mat=mat_cyan_txt,
        rot_euler=(math.radians(90), 0.0, math.radians(-18)),
    )
    return rail_points


def setup_camera(
    beats: list[dict],
    ping_events_ms: list[int],
    vault_center: Vector,
    rail_points: list[Vector],
) -> None:
    scene = bpy.context.scene

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0.0, 0.8, 2.0))
    target = bpy.context.active_object
    target.name = "CamTarget"

    bpy.ops.object.camera_add(location=(0.0, -14.5, 5.5))
    cam = bpy.context.active_object
    cam.name = "HeroCamera"
    scene.camera = cam
    cam.data.lens = 25.0  # 25mm wide lens fits both sides cleanly inside vertical 9:16!
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = target
    cam.data.dof.aperture_fstop = 4.8

    track = cam.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    b1_s = ms_to_frame(beats[0]["start_ms"])
    b2_s = ms_to_frame(beats[1]["start_ms"])
    b2_e = ms_to_frame(beats[1]["end_ms"])
    b3_s = ms_to_frame(beats[2]["start_ms"])
    b4_s = ms_to_frame(beats[3]["start_ms"])
    b4_e = TOTAL_FRAMES

    # Beat 1 (Hook): Balanced wide split framing both 2 DAYS vault & 0.8 SEC rail in 9:16
    cam.location = (-0.2, -12.6, 5.2)
    target.location = (-0.1, 0.9, 2.0)
    cam.keyframe_insert("location", frame=b1_s)
    target.keyframe_insert("location", frame=b1_s)

    # Beat 2 (Legacy Batch): Smooth push-in on Legacy Bullion Cage
    cam.location = (-2.2, -6.2, 3.6)
    target.location = vault_center
    cam.keyframe_insert("location", frame=b2_s + 14)
    target.keyframe_insert("location", frame=b2_s + 14)

    cam.location = (-5.6, -5.2, 4.2)
    target.location = vault_center + Vector((0, 0, 0.3))
    cam.keyframe_insert("location", frame=b2_e)
    target.keyframe_insert("location", frame=b2_e)

    # Beat 3 (Instant Rail): Whip across and ride alongside the 4 glowing nodes!
    cam.location = (-1.6, -8.8, 3.4)
    target.location = rail_points[0]
    cam.keyframe_insert("location", frame=b3_s + 6)
    target.keyframe_insert("location", frame=b3_s + 6)

    if len(ping_events_ms) >= 4:
        cam.location = (-1.4, -3.5, 4.0)
        target.location = rail_points[2]
        cam.keyframe_insert("location", frame=ms_to_frame(ping_events_ms[2]))
        target.keyframe_insert("location", frame=ms_to_frame(ping_events_ms[2]))

        cam.location = (-1.2, 0.2, 4.4)
        target.location = rail_points[3]
        cam.keyframe_insert("location", frame=ms_to_frame(ping_events_ms[3]) + 6)
        target.keyframe_insert("location", frame=ms_to_frame(ping_events_ms[3]) + 6)

    # Beat 4 (Payoff): Elevated 3/4 hero overview capturing the full network inside 9:16
    cam.location = (-0.3, -13.2, 8.6)
    target.location = (-0.1, 1.4, 1.9)
    cam.keyframe_insert("location", frame=b4_s + 15)
    target.keyframe_insert("location", frame=b4_s + 15)

    cam.location = (1.1, -13.8, 9.2)
    target.location = (-0.1, 1.4, 1.9)
    cam.keyframe_insert("location", frame=b4_e)
    target.keyframe_insert("location", frame=b4_e)


def main() -> None:
    clear_scene()
    setup_world_and_compositor()
    setup_lights()

    mat_floor = make_pbr_mat("ObsidianFloor", (0.012, 0.016, 0.032, 1.0), metallic=0.78, roughness=0.20)
    mat_grid = make_pbr_mat(
        "CircuitGrid",
        (0.05, 0.45, 0.78, 1.0),
        emission_color=(0.04, 0.50, 0.85, 1.0),
        emission_strength=1.1,
    )
    build_studio_floor(mat_floor, mat_grid)

    beats = MANIFEST["beats"]
    ping_events_ms = MANIFEST.get("ping_events_ms", [])

    vault_center = build_legacy_vault(beats)
    rail_points = build_instant_rail(beats, ping_events_ms)
    setup_camera(beats, ping_events_ms, vault_center, rail_points)
    smooth_all_fcurves()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    blend_path = OUT_DIR.parent / "upi_vs_banks_3d.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    scene = bpy.context.scene
    if MODE == "stills":
        sample_frames = [
            ms_to_frame(beats[0]["start_ms"] + 800),
            ms_to_frame(beats[1]["start_ms"] + 2500),
            ms_to_frame(ping_events_ms[2]) if len(ping_events_ms) >= 3 else ms_to_frame(beats[2]["start_ms"] + 2000),
            ms_to_frame(beats[3]["start_ms"] + 1500),
        ]
        for idx, fr in enumerate(sample_frames, 1):
            scene.frame_set(fr)
            scene.render.filepath = str(OUT_DIR / f"still_{idx:02d}_f{fr:04d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        scene.render.filepath = str(OUT_DIR / "frame_")
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
