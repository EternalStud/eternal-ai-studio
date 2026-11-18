"""Cross-version safe Blender 4.2+ / 5.3+ studio kit.

Provides procedural Noise->Bump PBR shaders, Volume Scatter atmosphere,
cross-version Glare/Bloom compositor setup, and clamped camera cuts with
CONSTANT holds at shot boundaries (f_next_cut - 1) so zero fly-across occurs.
"""

from __future__ import annotations

import math
from typing import Iterable

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def set_input(node, names: Iterable[str], value) -> bool:
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return True
    return False


def iter_action_fcurves(action) -> list:
    """Iterate fcurves safely across Blender 4.x legacy and 5.x layered/slotted actions."""
    curves: list = []
    if action is None:
        return curves
    legacy = getattr(action, "fcurves", None)
    if legacy:
        curves.extend(legacy)
    layers = getattr(action, "layers", None)
    if layers:
        for layer in layers:
            for strip in getattr(layer, "strips", []):
                for bag in getattr(strip, "channelbags", []):
                    curves.extend(getattr(bag, "fcurves", []))
    return curves


def setup_world(
    scene: bpy.types.Scene,
    total_frames: int,
    fps: int = 24,
    res_x: int = 1080,
    res_y: int = 1920,
    samples: int = 16,
    bg_color=(0.008, 0.014, 0.028),
    bg_strength: float = 0.45,
    fog_density: float = 0.010,
    bloom_threshold: float = 0.72,
    bloom_strength: float = 0.52,
    bloom_size: float = 0.65,
) -> None:
    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.render.fps = fps
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.use_persistent_data = False

    scene.render.engine = "BLENDER_EEVEE"
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = samples
    if hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing = False

    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        scene.view_settings.view_transform = "Filmic"

    # Atmospheric dark world + subtle Volume Scatter for optical beam cones
    world = bpy.data.worlds.new("StudioWorld")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (*bg_color, 1.0)
    bg.inputs["Strength"].default_value = bg_strength

    vol = nt.nodes.new("ShaderNodeVolumeScatter")
    vol.inputs["Color"].default_value = (0.14, 0.24, 0.42, 1.0)
    vol.inputs["Density"].default_value = fog_density
    vol.inputs["Anisotropy"].default_value = 0.62

    out_w = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs["Background"], out_w.inputs["Surface"])
    nt.links.new(vol.outputs["Volume"], out_w.inputs["Volume"])

    # Cross-version Compositor Bloom / Fog Glow (Blender 5.3 + 4.2 safe, never silenced)
    scene.use_nodes = True
    c_tree = getattr(scene, "node_tree", None)
    use_group_output = False
    if c_tree is None:
        c_tree = bpy.data.node_groups.new("StudioComp", "CompositorNodeTree")
        scene.compositing_node_group = c_tree
        use_group_output = True
    else:
        c_tree.nodes.clear()

    rl = c_tree.nodes.new("CompositorNodeRLayers")
    gl = c_tree.nodes.new("CompositorNodeGlare")

    if hasattr(gl, "glare_type"):
        gl.glare_type = "BLOOM"
        if hasattr(gl, "quality"):
            gl.quality = "HIGH"
        if hasattr(gl, "threshold"):
            gl.threshold = bloom_threshold
        if hasattr(gl, "size"):
            gl.size = 7
    else:
        set_input(gl, ["Type"], "Bloom")
        set_input(gl, ["Quality"], "Medium")
        set_input(gl, ["Threshold"], bloom_threshold)
        set_input(gl, ["Strength"], bloom_strength)
        set_input(gl, ["Size"], bloom_size)

    if use_group_output:
        out_c = c_tree.nodes.new("NodeGroupOutput")
        c_tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        c_tree.links.new(rl.outputs["Image"], gl.inputs["Image"])
        c_tree.links.new(gl.outputs["Image"], out_c.inputs[0])
    else:
        out_c = c_tree.nodes.new("CompositorNodeComposite")
        c_tree.links.new(rl.outputs["Image"], gl.inputs["Image"])
        c_tree.links.new(gl.outputs["Image"], out_c.inputs["Image"])


def mat_pbr(
    name: str,
    color=(0.08, 0.09, 0.12),
    rough: float = 0.42,
    metal: float = 0.15,
    bump_scale: float = 0.0,
    bump_strength: float = 0.0,
    emit=(0.0, 0.0, 0.0),
    emit_strength: float = 0.0,
) -> bpy.types.Material:
    """Create Principled BSDF material with optional Noise->Bump micro-surface texture."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    set_input(bsdf, ["Base Color"], (*color, 1.0))
    set_input(bsdf, ["Roughness"], rough)
    set_input(bsdf, ["Metallic"], metal)
    set_input(bsdf, ["Emission Color", "Emission"], (*emit, 1.0))
    set_input(bsdf, ["Emission Strength"], emit_strength)

    if bump_scale > 0.0 and bump_strength > 0.0:
        tex = nt.nodes.new("ShaderNodeTexCoord")
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = bump_scale
        noise.inputs["Detail"].default_value = 7.0
        noise.inputs["Roughness"].default_value = 0.65
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = bump_strength
        bump.inputs["Distance"].default_value = 0.02
        nt.links.new(tex.outputs["Object"], noise.inputs["Vector"])
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def add_bevel(obj, width: float = 0.03, segments: int = 2) -> None:
    mod = obj.modifiers.new(name="Bevel", type="BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"


def add_cube(name: str, loc, scale, mat, bevel: float = 0.02, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.rotation_euler = rot
    if bevel > 0:
        add_bevel(o, width=bevel, segments=2)
    o.data.materials.append(mat)
    return o


def add_cyl(name: str, loc, radius: float, depth: float, mat, rot=(0.0, 0.0, 0.0), verts: int = 36):
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


def animate_shot_clamped(
    cam: bpy.types.Object,
    cam_tgt: bpy.types.Object,
    f_start: int,
    f_next_cut: int,
    cam_pos_start: tuple,
    cam_pos_end: tuple,
    tgt_pos_start: tuple,
    tgt_pos_end: tuple,
    lens_start: float = 34.0,
    lens_end: float = 34.0,
) -> tuple[int, int]:
    """Keyframe camera move strictly over [f_start, f_next_cut - 1] with zero cross-zone drift."""
    f_end = max(f_start + 1, f_next_cut - 1)

    for fr, cp, tp, ln in (
        (f_start, cam_pos_start, tgt_pos_start, lens_start),
        (f_end, cam_pos_end, tgt_pos_end, lens_end),
    ):
        cam.location = cp
        cam.keyframe_insert(data_path="location", frame=fr)
        cam_tgt.location = tp
        cam_tgt.keyframe_insert(data_path="location", frame=fr)
        cam.data.lens = ln
        cam.data.keyframe_insert(data_path="lens", frame=fr)

    return f_start, f_end


def finalize_clamped_camera_rig(cam: bpy.types.Object, cam_tgt: bpy.types.Object, shot_end_frames: set[int]) -> None:
    """Force AUTO_CLAMPED Bezier handles inside shots and CONSTANT hold at shot_end_frames."""
    for obj in (cam, cam_tgt, cam.data):
        anim = getattr(obj, "animation_data", None)
        if not anim or not anim.action:
            continue
        for fc in iter_action_fcurves(anim.action):
            for kp in fc.keyframe_points:
                kp.handle_left_type = "AUTO_CLAMPED"
                kp.handle_right_type = "AUTO_CLAMPED"
                fr = int(round(kp.co[0]))
                kp.interpolation = "CONSTANT" if fr in shot_end_frames else "BEZIER"
            fc.update()


def project_world_point(scene: bpy.types.Scene, cam: bpy.types.Object, world_pt: tuple[float, float, float]) -> tuple[float, float, float]:
    """Return normalized screen coords (u in 0..1 left-right, v in 0..1 bottom-top, depth)."""
    co = world_to_camera_view(scene, cam, Vector(world_pt))
    return float(co.x), float(co.y), float(co.z)
