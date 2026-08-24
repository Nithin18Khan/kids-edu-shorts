"""
body_gentle.blend — sneeze explainer that READS as the script.

Each cut is a literal subject a 6–10 year old can name (60s / 1440f):
  CAM_HOOK    kid FACE + AIR (hurricane sneeze)
  CAM_PROFILE tickle in the nose — something does not belong
  CAM_DUST    labeled DUST specks
  CAM_MACRO   labeled POLLEN grain + flower
  CAM_BLAST   AIR arrows blasting out of the nose
  CAM_CAR     red CAR on a city street
  CAM_CLOSE   kid breathes easy / cover with elbow
  CAM_LUNGS   cartoon LUNGS — body superhero

Kid-safe: no gore. Cartoon diagram lungs only.
"""

from __future__ import annotations

from math import cos, radians, sin
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector


TEMPLATE_FRAMES = 1440
OUT = Path(__file__).resolve().parents[1] / "templates" / "body_gentle.blend"
PREVIEW_DIR = Path(__file__).resolve().parents[1] / "templates" / "previews"
FONT = Path(r"C:\Windows\Fonts\arialbd.ttf")


def _set_input(node, names, value) -> None:
    for name in names:
        sock = node.inputs.get(name)
        if sock is not None:
            sock.default_value = value
            return


def _smooth(obj) -> None:
    mesh = obj.data
    if hasattr(mesh, "polygons"):
        for poly in mesh.polygons:
            poly.use_smooth = True


def _new_mesh_obj(name, collection):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj, bmesh.new()


def _commit(obj, bm):
    bm.to_mesh(obj.data)
    bm.free()
    _smooth(obj)
    obj.data.update()
    return obj


def uv_sphere(name, collection, radius, location, u=32, v=16, scale=None):
    obj, bm = _new_mesh_obj(name, collection)
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=radius)
    _commit(obj, bm)
    obj.location = location
    if scale:
        obj.scale = scale
    return obj


def plane(name, collection, size, location, rotation=None):
    obj, bm = _new_mesh_obj(name, collection)
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size)
    _commit(obj, bm)
    obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    return obj


def cube(name, collection, size, location, scale=None):
    obj, bm = _new_mesh_obj(name, collection)
    bmesh.ops.create_cube(bm, size=size)
    _commit(obj, bm)
    obj.location = location
    if scale:
        obj.scale = scale
    return obj


def cylinder(name, collection, radius, depth, location, rotation=None):
    obj, bm = _new_mesh_obj(name, collection)
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=16, radius1=radius, radius2=radius, depth=depth
    )
    _commit(obj, bm)
    obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    return obj


def cone(name, collection, r1, r2, depth, location, rotation=None):
    obj, bm = _new_mesh_obj(name, collection)
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=12, radius1=r1, radius2=r2, depth=depth
    )
    _commit(obj, bm)
    obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    return obj


def principled(
    name,
    *,
    color,
    roughness=0.35,
    metallic=0.0,
    emission=None,
    emission_strength=0.0,
    alpha=1.0,
    transmission=0.0,
    sss=0.0,
):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF") or next(
        n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"
    )
    _set_input(bsdf, ["Base Color"], (*color[:3], 1.0))
    _set_input(bsdf, ["Roughness"], roughness)
    _set_input(bsdf, ["Metallic"], metallic)
    _set_input(bsdf, ["Alpha"], alpha)
    _set_input(bsdf, ["Transmission Weight", "Transmission"], transmission)
    _set_input(bsdf, ["Subsurface Weight", "Subsurface"], sss)
    if emission is not None:
        _set_input(bsdf, ["Emission Color", "Emission"], (*emission[:3], 1.0))
        _set_input(bsdf, ["Emission Strength"], emission_strength)
    if alpha < 1.0 or transmission > 0.0:
        mat.blend_method = "BLEND"
        if hasattr(mat, "shadow_method"):
            mat.shadow_method = "NONE"
    return mat


def emission_mat(name, color, strength: float):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color[:3], 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def assign(obj, mat) -> None:
    if obj.data is None:
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def ensure_collection(name, parent=None):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        if parent is not None:
            parent.children.link(coll)
        else:
            bpy.context.scene.collection.children.link(coll)
    return coll


def look_at(obj, target: Vector) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def key_loc(obj, frame, loc) -> None:
    obj.location = loc
    obj.keyframe_insert(data_path="location", frame=frame)


def key_scale(obj, frame, scale) -> None:
    obj.scale = scale
    obj.keyframe_insert(data_path="scale", frame=frame)


def key_rot(obj, frame, rot) -> None:
    obj.rotation_euler = rot
    obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def ease(obj) -> None:
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    fcurves = getattr(ad.action, "fcurves", None)
    if fcurves is None:
        return
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.easing = "EASE_IN_OUT"


def parent_local(child, parent, local_loc) -> None:
    child.parent = parent
    child.location = local_loc


def make_label(name, collection, text, location, *, size=0.28, color=(1, 1, 1)):
    curve = bpy.data.curves.new(name, type="FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.018
    curve.bevel_depth = 0.004
    if FONT.exists():
        try:
            curve.font = bpy.data.fonts.load(str(FONT))
        except Exception:
            pass
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.location = location
    # Face a camera sitting on -Y
    obj.rotation_euler = (radians(90), 0.0, 0.0)
    mat = emission_mat(f"{name}_mat", color, 2.2)
    obj.data.materials.append(mat)
    return obj


def clear_scene() -> None:
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    except Exception:
        bpy.ops.wm.read_homefile(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)
    for curve in list(bpy.data.curves):
        bpy.data.curves.remove(curve)


def setup_render(scene) -> None:
    engines = []
    try:
        engines = [e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items]
    except Exception:
        engines = []
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.fps = 24
    scene.render.image_settings.file_format = "PNG"
    scene.frame_start = 1
    scene.frame_end = TEMPLATE_FRAMES
    eevee = getattr(scene, "eevee", None)
    if eevee is not None:
        for attr, val in (("taa_render_samples", 8), ("taa_samples", 6), ("use_gtao", True)):
            if hasattr(eevee, attr):
                setattr(eevee, attr, val)
    scene.world = bpy.data.worlds.new("KidsWorld")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.10, 0.36, 0.40, 1.0)
        bg.inputs[1].default_value = 0.5
    try:
        scene.view_settings.view_transform = "AgX"
    except TypeError:
        pass
    scene.view_settings.exposure = 0.08
    scene.use_nodes = False
    scene.render.use_compositing = False


def add_camera(name, collection, location, target, fstop, lens=50):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_fit = "VERTICAL"
    data.dof.use_dof = True
    data.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new(name, data)
    collection.objects.link(cam)
    cam.location = location
    look_at(cam, Vector(target))
    return cam


def add_area(name, collection, location, target, energy, size, color):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    look_at(obj, Vector(target))
    return obj


def build_kid(coll, mats):
    """A cartoon child — must read as a PERSON with a nose, not a blob."""
    root = bpy.data.objects.new("CHAR_Kid", None)
    coll.objects.link(root)
    root.location = (0.0, 0.0, 0.0)

    body = uv_sphere("CHAR_Body", coll, 0.42, (0, 0, 0), 32, 16, scale=(0.95, 0.7, 1.15))
    shirt = cube("CHAR_Shirt", coll, 0.55, (0, 0, 0), scale=(1.05, 0.7, 0.85))
    head = uv_sphere("CHAR_Head", coll, 0.50, (0, 0, 0), 40, 20)
    hair = uv_sphere("CHAR_Hair", coll, 0.52, (0, 0, 0), 32, 16, scale=(1.05, 0.95, 0.55))
    nose = uv_sphere("CHAR_Nose", coll, 0.11, (0, 0, 0), 20, 12, scale=(0.85, 1.25, 0.9))
    eye_l = uv_sphere("CHAR_EyeL", coll, 0.12, (0, 0, 0), 20, 12)
    eye_r = uv_sphere("CHAR_EyeR", coll, 0.12, (0, 0, 0), 20, 12)
    pupil_l = uv_sphere("CHAR_PupilL", coll, 0.055, (0, 0, 0), 12, 8)
    pupil_r = uv_sphere("CHAR_PupilR", coll, 0.055, (0, 0, 0), 12, 8)
    brow_l = cube("CHAR_BrowL", coll, 0.10, (0, 0, 0), scale=(1.4, 0.22, 0.18))
    brow_r = cube("CHAR_BrowR", coll, 0.10, (0, 0, 0), scale=(1.4, 0.22, 0.18))
    mouth = uv_sphere("CHAR_Mouth", coll, 0.10, (0, 0, 0), 16, 10, scale=(1.5, 0.22, 0.35))
    cheek_l = uv_sphere("CHAR_CheekL", coll, 0.09, (0, 0, 0), 12, 8)
    cheek_r = uv_sphere("CHAR_CheekR", coll, 0.09, (0, 0, 0), 12, 8)

    assign(body, mats["skin"])
    assign(shirt, mats["shirt"])
    assign(head, mats["skin"])
    assign(hair, mats["hair"])
    assign(nose, mats["nose"])
    assign(eye_l, mats["eye"])
    assign(eye_r, mats["eye"])
    assign(pupil_l, mats["pupil"])
    assign(pupil_r, mats["pupil"])
    assign(brow_l, mats["hair"])
    assign(brow_r, mats["hair"])
    assign(mouth, mats["mouth"])
    assign(cheek_l, mats["blush"])
    assign(cheek_r, mats["blush"])

    parent_local(body, root, (0.0, 0.08, 0.48))
    parent_local(shirt, root, (0.0, 0.08, 0.52))
    parent_local(head, root, (0.0, 0.0, 1.28))
    parent_local(hair, head, (0.0, 0.08, 0.28))
    parent_local(nose, head, (0.0, -0.52, -0.02))
    parent_local(eye_l, head, (-0.16, -0.42, 0.12))
    parent_local(eye_r, head, (0.16, -0.42, 0.12))
    parent_local(pupil_l, head, (-0.16, -0.52, 0.12))
    parent_local(pupil_r, head, (0.16, -0.52, 0.12))
    parent_local(brow_l, head, (-0.16, -0.40, 0.28))
    parent_local(brow_r, head, (0.16, -0.40, 0.28))
    parent_local(mouth, head, (0.0, -0.45, -0.22))
    parent_local(cheek_l, head, (-0.32, -0.32, -0.06))
    parent_local(cheek_r, head, (0.32, -0.32, -0.06))
    return {"root": root, "head": head, "nose": nose}


def build_wind(coll, mats):
    """Cyan arrows = AIR coming out of the nose (readable, not random balls)."""
    root = bpy.data.objects.new("FX_Wind", None)
    coll.objects.link(root)
    root.location = (0.0, -0.62, 1.26)
    for i in range(9):
        empty = bpy.data.objects.new(f"FX_Arrow_{i}", None)
        coll.objects.link(empty)
        empty.parent = root
        empty.location = (0.08 * ((i % 3) - 1), -0.22 * i - 0.15, 0.04 * ((i % 2) - 0.5))
        empty.rotation_euler = (radians(-90), 0, 0)
        shaft = cylinder(f"FX_ArrowShaft_{i}", coll, 0.035, 0.22, (0, 0, 0))
        head = cone(f"FX_ArrowHead_{i}", coll, 0.09, 0.0, 0.16, (0, 0, 0.18))
        assign(shaft, mats["air"])
        assign(head, mats["air"])
        parent_local(shaft, empty, (0, 0, 0.0))
        parent_local(head, empty, (0, 0, 0.16))
    return root


def build_dust_set(coll, mats):
    """Isolated DUST insert — brown specks a kid can name."""
    root = bpy.data.objects.new("SET_Dust", None)
    coll.objects.link(root)
    root.location = (-11.0, 0.0, 1.05)
    for i, off in enumerate((
        (0, 0, 0), (0.28, -0.12, 0.14), (-0.22, 0.16, -0.08),
        (0.14, 0.24, 0.2), (-0.32, -0.14, 0.1), (0.2, -0.22, -0.16),
        (-0.1, 0.1, 0.24), (0.34, 0.06, -0.06), (-0.18, -0.2, 0.12),
        (0.08, 0.18, -0.18),
    )):
        speck = cube(f"FX_Dust_{i}", coll, 0.13 + (i % 3) * 0.03, off)
        assign(speck, mats["dust"])
        parent_local(speck, root, off)
        speck.rotation_euler = (0.4 * i, 0.3 * i, 0.2 * i)
    lbl = make_label("LBL_DUST", coll, "DUST", (0.0, -0.2, 1.1), size=0.38, color=(1.0, 0.88, 0.35))
    parent_local(lbl, root, (0.0, -0.15, 1.12))
    return root


def build_pollen_set(coll, mats):
    """Isolated POLLEN grain — textbook spikes + label."""
    root = bpy.data.objects.new("SET_Pollen", None)
    coll.objects.link(root)
    root.location = (-8.0, 0.0, 1.15)

    grain = uv_sphere("FX_PollenGrain", coll, 0.55, (0, 0, 0), 24, 16)
    assign(grain, mats["pollen"])
    parent_local(grain, root, (0.0, 0.0, 0.0))
    for i in range(14):
        a = radians(i * 26)
        b = radians((i * 47) % 180 - 90)
        loc = (0.62 * cos(b) * cos(a), 0.62 * cos(b) * sin(a), 0.62 * sin(b))
        spike = cone(f"FX_PollenSpike_{i}", coll, 0.07, 0.0, 0.28, loc)
        assign(spike, mats["pollen"])
        parent_local(spike, grain, loc)
        vec = Vector(loc)
        if vec.length_squared > 0:
            spike.rotation_euler = vec.to_track_quat("Z", "Y").to_euler()

    stem = cylinder("FX_FlowerStem", coll, 0.04, 0.7, (0, 0, 0))
    assign(stem, principled("Stem", color=(0.2, 0.55, 0.22), roughness=0.55))
    parent_local(stem, root, (1.1, 0.15, -0.55))
    bloom = uv_sphere("FX_Flower", coll, 0.22, (0, 0, 0), 16, 10)
    assign(bloom, principled("Flower", color=(0.95, 0.35, 0.55), roughness=0.4))
    parent_local(bloom, root, (1.1, 0.15, -0.12))

    lbl_p = make_label("LBL_POLLEN", coll, "POLLEN", (0.0, -0.95, 0.95), size=0.32, color=(1.0, 0.85, 0.15))
    parent_local(lbl_p, root, (0.0, -1.0, 0.95))
    return {"root": root, "grain": grain}


def build_car(coll, mats):
    """Matchbox-style red car on a street — must read as a CAR."""
    root = bpy.data.objects.new("PROP_Car", None)
    coll.objects.link(root)
    root.location = (12.0, 0.0, 0.42)

    body = cube("PROP_CarBody", coll, 0.9, (0, 0, 0), scale=(2.1, 1.0, 0.55))
    cabin = cube("PROP_CarCabin", coll, 0.7, (0, 0, 0), scale=(1.0, 0.9, 0.7))
    window = cube("PROP_Window", coll, 0.45, (0, 0, 0), scale=(0.85, 0.95, 0.55))
    light_l = uv_sphere("PROP_HeadL", coll, 0.08, (0, 0, 0), 12, 8)
    light_r = uv_sphere("PROP_HeadR", coll, 0.08, (0, 0, 0), 12, 8)
    assign(body, mats["car"])
    assign(cabin, mats["car_dark"])
    assign(window, mats["glass"])
    assign(light_l, mats["headlight"])
    assign(light_r, mats["headlight"])
    parent_local(body, root, (0.0, 0.0, 0.05))
    parent_local(cabin, root, (-0.15, 0.0, 0.42))
    parent_local(window, root, (-0.12, 0.0, 0.48))
    parent_local(light_l, root, (0.92, 0.32, 0.05))
    parent_local(light_r, root, (0.92, -0.32, 0.05))
    for i, loc in enumerate(((-0.6, 0.48, -0.22), (0.55, 0.48, -0.22), (-0.6, -0.48, -0.22), (0.55, -0.48, -0.22))):
        wheel = cylinder(f"PROP_Wheel_{i}", coll, 0.18, 0.12, loc, rotation=(radians(90), 0, 0))
        assign(wheel, mats["tire"])
        parent_local(wheel, root, loc)

    street = plane("PROP_Street", coll, 7.0, (12.0, 0.0, 0.0))
    assign(street, mats["street"])
    for i in range(5):
        dash = cube(f"PROP_Lane_{i}", coll, 0.25, (10.2 + i * 0.85, 0.0, 0.02), scale=(1.4, 0.18, 0.04))
        assign(dash, mats["lane"])
    bldg_l = cube("PROP_BldgL", coll, 1.0, (10.0, 2.5, 1.5), scale=(0.9, 0.7, 3.0))
    bldg_r = cube("PROP_BldgR", coll, 1.0, (14.0, 2.7, 1.7), scale=(0.8, 0.65, 3.4))
    assign(bldg_l, mats["building"])
    assign(bldg_r, mats["building"])
    lbl = make_label("LBL_CAR", coll, "CAR", (12.0, -1.2, 1.55), size=0.34, color=(1.0, 0.95, 0.2))
    return root, lbl


def build_lungs(coll, mats):
    """Kid-safe cartoon lungs (two balloons + tube), not medical gore."""
    root = bpy.data.objects.new("FX_Lungs", None)
    coll.objects.link(root)
    # Isolated insert (not hidden behind the kid) so CAM_LUNGS reads as LUNGS
    root.location = (6.5, 0.0, 1.15)
    lung_l = uv_sphere("FX_LungL", coll, 0.32, (0, 0, 0), 24, 14, scale=(0.85, 0.7, 1.25))
    lung_r = uv_sphere("FX_LungR", coll, 0.32, (0, 0, 0), 24, 14, scale=(0.85, 0.7, 1.25))
    tube = cylinder("FX_Trachea", coll, 0.05, 0.45, (0, 0, 0), rotation=(0, 0, 0))
    assign(lung_l, mats["lung"])
    assign(lung_r, mats["lung"])
    assign(tube, mats["lung"])
    parent_local(lung_l, root, (-0.28, 0.0, 0.0))
    parent_local(lung_r, root, (0.28, 0.0, 0.0))
    parent_local(tube, root, (0.0, 0.0, 0.38))
    star = cone("FX_HeroStar", coll, 0.18, 0.0, 0.12, (0, 0, 0))
    assign(star, mats["star"])
    parent_local(star, root, (0.0, -0.35, 0.55))
    lbl = make_label("LBL_LUNGS", coll, "LUNGS", (0.0, -0.7, 0.95), size=0.26, color=(1.0, 0.55, 0.65))
    parent_local(lbl, root, (0.0, -0.55, 0.72))
    return root


def animate(kid, wind, pollen, car, lungs) -> None:
    head = kid["head"]
    root = kid["root"]

    # 60s timeline @ 24fps (1440 frames)
    key_rot(head, 1, (0, 0, 0))
    key_scale(head, 1, (1, 1, 1))
    key_rot(head, 80, (0, 0, 0))
    key_rot(head, 140, (-0.1, 0, 0))
    key_scale(head, 140, (1.04, 0.95, 1.02))
    key_rot(head, 192, (0, 0, 0))
    key_scale(head, 192, (1, 1, 1))
    key_rot(head, 700, (0, 0, 0))
    key_scale(head, 700, (1.05, 0.92, 1.03))
    key_rot(head, 740, (-0.16, 0, 0))
    key_rot(head, 768, (0.18, 0, 0))
    key_scale(head, 768, (0.9, 1.18, 0.88))
    key_rot(head, 820, (0, 0, 0))
    key_scale(head, 820, (1, 1, 1))
    key_scale(head, 1200, (1.02, 1.02, 1.02))
    key_scale(head, 1440, (1, 1, 1))

    key_scale(wind, 1, (0, 0, 0))
    key_scale(wind, 24, (0, 0, 0))
    key_scale(wind, 48, (0.7, 0.7, 0.7))
    key_loc(wind, 48, (0.0, -0.7, 1.26))
    key_scale(wind, 180, (0.25, 0.25, 0.25))
    key_scale(wind, 360, (0, 0, 0))
    key_scale(wind, 720, (0, 0, 0))
    key_scale(wind, 748, (1.0, 1.3, 1.0))
    key_loc(wind, 748, (0.0, -0.7, 1.26))
    key_scale(wind, 820, (1.5, 2.4, 1.5))
    key_loc(wind, 820, (0.0, -1.8, 1.32))
    key_scale(wind, 912, (0.1, 0.1, 0.1))
    key_scale(wind, 1000, (0, 0, 0))

    key_loc(car, 1, (9.5, 0, 0.42))
    key_loc(car, 912, (9.5, 0, 0.42))
    key_loc(car, 996, (12.3, 0, 0.42))
    key_loc(car, 1080, (15.0, 0, 0.42))

    key_scale(lungs, 1, (1, 1, 1))
    key_scale(lungs, 1248, (1, 1, 1))
    key_scale(lungs, 1320, (1.14, 1.14, 1.14))
    key_scale(lungs, 1440, (1, 1, 1))

    key_loc(root, 1, (0, 0, 0))
    key_loc(root, 96, (0, 0, 0.04))
    key_loc(root, 192, (0, 0, 0))
    key_loc(root, 1100, (0, 0, 0))
    key_loc(root, 1200, (0, 0, 0.03))
    key_loc(root, 1440, (0, 0, 0))

    key_scale(pollen["root"], 1, (1, 1, 1))

    for obj in (head, root, wind, car, lungs, pollen["root"]):
        ease(obj)


def key_aim(scene, cam, frames, aim) -> None:
    for f in frames:
        scene.frame_set(f)
        look_at(cam, aim)
        cam.keyframe_insert(data_path="rotation_euler", frame=f)
    ease(cam)


def main() -> None:
    clear_scene()
    scene = bpy.context.scene
    setup_render(scene)
    master = scene.collection
    col_set = ensure_collection("SET", master)
    col_char = ensure_collection("CHAR", master)
    col_fx = ensure_collection("FX", master)
    col_prop = ensure_collection("PROPS", master)
    col_lbl = ensure_collection("LABELS", master)
    col_lights = ensure_collection("LIGHTS", master)
    col_cams = ensure_collection("CAMERAS", master)
    ensure_collection("SLOT_hero_prop", master)
    ensure_collection("SLOT_support_a", master)

    mats = {
        "skin": principled("Skin", color=(0.96, 0.74, 0.60), roughness=0.32, sss=0.35),
        "nose": principled("Nose", color=(0.92, 0.55, 0.48), roughness=0.3, sss=0.4),
        "shirt": principled("Shirt", color=(0.18, 0.45, 0.85), roughness=0.5),
        "hair": principled("Hair", color=(0.22, 0.12, 0.08), roughness=0.55),
        "eye": principled("Eye", color=(0.97, 0.98, 1.0), roughness=0.12),
        "pupil": principled("Pupil", color=(0.05, 0.05, 0.06), roughness=0.2),
        "mouth": principled("Mouth", color=(0.55, 0.18, 0.22), roughness=0.4),
        "blush": principled("Blush", color=(0.95, 0.5, 0.52), roughness=0.45, emission=(0.9, 0.4, 0.45), emission_strength=0.1),
        "floor": principled("Floor", color=(0.16, 0.42, 0.46), roughness=0.4),
        "dust": principled("Dust", color=(0.45, 0.32, 0.18), roughness=0.7),
        "pollen": principled("Pollen", color=(0.95, 0.82, 0.12), roughness=0.35, emission=(0.95, 0.75, 0.1), emission_strength=0.45),
        "air": principled("Air", color=(0.25, 0.75, 0.95), roughness=0.2, emission=(0.2, 0.7, 1.0), emission_strength=1.6),
        "lung": principled("Lung", color=(0.95, 0.45, 0.55), roughness=0.4, sss=0.35, emission=(0.9, 0.35, 0.45), emission_strength=0.25),
        "star": emission_mat("Star", (1.0, 0.85, 0.2), 4.0),
        "car": principled("Car", color=(0.85, 0.12, 0.12), roughness=0.22, metallic=0.2),
        "car_dark": principled("CarDark", color=(0.55, 0.08, 0.08), roughness=0.3),
        "glass": principled("Glass", color=(0.45, 0.7, 0.9), roughness=0.08, transmission=0.55, alpha=0.65),
        "headlight": emission_mat("Headlight", (1.0, 0.95, 0.7), 5.0),
        "tire": principled("Tire", color=(0.08, 0.08, 0.09), roughness=0.6),
        "street": principled("Street", color=(0.22, 0.24, 0.26), roughness=0.5),
        "lane": emission_mat("Lane", (0.95, 0.85, 0.2), 1.5),
        "building": principled("Building", color=(0.12, 0.28, 0.32), roughness=0.55),
        "accent": principled("Accent", color=(0.31, 0.76, 0.97), roughness=0.25, emission=(0.31, 0.76, 0.97), emission_strength=1.0),
    }

    floor = plane("SET_Floor", col_set, 36.0, (2.0, 0.0, 0.0))
    assign(floor, mats["floor"])

    kid = build_kid(col_char, mats)
    wind = build_wind(col_fx, mats)
    dust = build_dust_set(col_fx, mats)
    pollen = build_pollen_set(col_fx, mats)
    car, _car_lbl = build_car(col_prop, mats)
    lungs = build_lungs(col_fx, mats)
    lbl_air = make_label("LBL_AIR", col_lbl, "AIR", (0.0, 0.0, 0.0), size=0.28, color=(0.4, 0.9, 1.0))
    parent_local(lbl_air, wind, (0.0, 0.0, 0.55))
    animate(kid, wind, pollen, car, lungs)
    key_rot(dust, 1, (0, 0, 0))
    key_rot(dust, 528, (0, 0, 1.2))
    ease(dust)

    aim_face = Vector((0.0, -0.15, 1.22))
    aim_nose = Vector((0.0, -0.45, 1.26))
    aim_dust = Vector((-11.0, 0.0, 1.1))
    aim_pollen = Vector((-7.55, 0.05, 1.05))
    aim_car = Vector((12.2, 0.0, 0.55))
    aim_close = Vector((0.0, 0.05, 1.15))
    aim_lungs = Vector((6.5, 0.0, 1.2))

    cam_hook = add_camera("CAM_HOOK", col_cams, (0.15, -3.35, 1.35), aim_face, 4.0, lens=50)
    cam_profile = add_camera("CAM_PROFILE", col_cams, (1.45, -2.55, 1.32), aim_nose, 4.2, lens=55)
    cam_dust = add_camera("CAM_DUST", col_cams, (-11.0, -4.3, 1.45), aim_dust, 5.0, lens=40)
    cam_macro = add_camera("CAM_MACRO", col_cams, (-8.0, -4.4, 1.55), aim_pollen, 5.2, lens=40)
    cam_blast = add_camera("CAM_BLAST", col_cams, (0.25, -3.45, 1.42), aim_nose, 4.4, lens=40)
    cam_car = add_camera("CAM_CAR", col_cams, (12.3, -5.6, 1.85), aim_car, 5.0, lens=35)
    cam_close = add_camera("CAM_CLOSE", col_cams, (0.35, -3.05, 1.28), aim_close, 4.0, lens=50)
    cam_lungs = add_camera("CAM_LUNGS", col_cams, (6.5, -4.5, 1.55), aim_lungs, 5.0, lens=40)
    cam_hook.data.dof.focus_object = kid["head"]
    cam_profile.data.dof.focus_object = kid["nose"]
    cam_dust.data.dof.focus_object = dust
    cam_macro.data.dof.focus_object = pollen["grain"]
    cam_blast.data.dof.focus_object = kid["nose"]
    cam_car.data.dof.focus_object = car
    cam_close.data.dof.focus_object = kid["head"]
    cam_lungs.data.dof.focus_object = lungs
    scene.camera = cam_hook

    # Match episode shots: 192+168+168+192+192+168+168+192 = 1440
    key_loc(cam_hook, 1, (0.15, -3.35, 1.35))
    key_loc(cam_hook, 192, (0.08, -3.05, 1.32))
    key_loc(cam_profile, 193, (1.45, -2.55, 1.32))
    key_loc(cam_profile, 360, (1.25, -2.3, 1.3))
    key_loc(cam_dust, 361, (-11.0, -4.3, 1.45))
    key_loc(cam_dust, 528, (-10.7, -3.85, 1.32))
    key_loc(cam_macro, 529, (-8.0, -4.4, 1.55))
    key_loc(cam_macro, 720, (-7.75, -3.9, 1.42))
    key_loc(cam_blast, 721, (0.25, -3.45, 1.42))
    key_loc(cam_blast, 912, (0.12, -3.05, 1.36))
    key_loc(cam_car, 913, (12.3, -5.6, 1.85))
    key_loc(cam_car, 1080, (12.55, -4.85, 1.62))
    key_loc(cam_close, 1081, (0.35, -3.05, 1.28))
    key_loc(cam_close, 1248, (0.15, -2.7, 1.22))
    key_loc(cam_lungs, 1249, (6.5, -4.5, 1.55))
    key_loc(cam_lungs, 1440, (6.35, -3.95, 1.4))
    key_aim(scene, cam_hook, (1, 192), aim_face)
    key_aim(scene, cam_profile, (193, 360), aim_nose)
    key_aim(scene, cam_dust, (361, 528), aim_dust)
    key_aim(scene, cam_macro, (529, 720), aim_pollen)
    key_aim(scene, cam_blast, (721, 912), aim_nose)
    key_aim(scene, cam_car, (913, 1080), aim_car)
    key_aim(scene, cam_close, (1081, 1248), aim_close)
    key_aim(scene, cam_lungs, (1249, 1440), aim_lungs)

    add_area("LGT_Key", col_lights, (2.6, -3.0, 3.4), aim_face, 480, 2.2, (1.0, 0.96, 0.9))
    add_area("LGT_Fill", col_lights, (-2.6, -2.2, 1.9), aim_face, 130, 3.0, (0.75, 0.9, 1.0))
    add_area("LGT_Rim", col_lights, (-1.2, 2.4, 2.3), aim_face, 240, 1.1, (0.5, 0.9, 1.0))
    add_area("LGT_Dust", col_lights, (-9.4, -2.4, 2.9), aim_dust, 360, 2.0, (1.0, 0.9, 0.7))
    add_area("LGT_Pollen", col_lights, (-6.5, -2.5, 3.0), aim_pollen, 400, 2.0, (1.0, 0.95, 0.8))
    add_area("LGT_CarKey", col_lights, (14.2, -3.0, 3.2), aim_car, 380, 2.0, (1.0, 0.95, 0.88))
    add_area("LGT_Lungs", col_lights, (8.0, -2.4, 3.1), aim_lungs, 360, 2.0, (1.0, 0.75, 0.8))

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for frame, cam, name in (
        (48, cam_hook, "body_gentle_hook.png"),
        (440, cam_dust, "body_gentle_dust.png"),
        (600, cam_macro, "body_gentle_macro.png"),
        (780, cam_blast, "body_gentle_blast.png"),
        (980, cam_car, "body_gentle_car.png"),
        (1320, cam_lungs, "body_gentle_lungs.png"),
    ):
        scene.frame_set(frame)
        scene.camera = cam
        scene.render.filepath = str(PREVIEW_DIR / name)
        print("Preview →", scene.render.filepath)
        bpy.ops.render.render(write_still=True)

    scene.camera = cam_hook
    scene.frame_set(1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
    print("Saved template →", OUT)


if __name__ == "__main__":
    main()
