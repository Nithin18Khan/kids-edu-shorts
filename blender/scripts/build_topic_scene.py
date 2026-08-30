"""
Cinematic unique 9:16 topic studio.
Every episode seed builds a different world, cameras, and hero.
Invoked: blender --background --python build_topic_scene.py -- job.json
"""

from __future__ import annotations

import json
import os
import random
import sys
from math import radians
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from ci_render import apply_output_settings, render_timeline  # noqa: E402
from local_grade import apply_local_grade  # noqa: E402


def _font_path() -> Path:
    for p in (
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
    ):
        if p.exists():
            return p
    return Path(r"C:\Windows\Fonts\arialbd.ttf")


FONT = _font_path()


def _job() -> dict:
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1 :]
    else:
        args = sys.argv[1:]
    if not args:
        raise SystemExit("Usage: blender --python build_topic_scene.py -- job.json")
    return json.loads(Path(args[0]).read_text(encoding="utf-8"))


def _hex(s: str) -> tuple[float, float, float]:
    h = (s or "#4FC3F7").lstrip("#")
    if len(h) != 6:
        return (0.31, 0.76, 0.97)
    return int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0


def _smooth(obj) -> None:
    if hasattr(obj.data, "polygons"):
        for p in obj.data.polygons:
            p.use_smooth = True


def _mesh(name, coll):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    return obj, bmesh.new()


def _commit(obj, bm):
    bm.to_mesh(obj.data)
    bm.free()
    _smooth(obj)
    obj.data.update()
    return obj


def sphere(name, coll, r, loc, u=28, v=14):
    obj, bm = _mesh(name, coll)
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)
    _commit(obj, bm)
    obj.location = loc
    return obj


def cube(name, coll, size, loc):
    obj, bm = _mesh(name, coll)
    bmesh.ops.create_cube(bm, size=size)
    _commit(obj, bm)
    obj.location = loc
    return obj


def plane(name, coll, size, loc):
    obj, bm = _mesh(name, coll)
    bmesh.ops.create_grid(bm, x_segments=8, y_segments=8, size=size)
    _commit(obj, bm)
    obj.location = loc
    return obj


def cylinder(name, coll, r, depth, loc):
    obj, bm = _mesh(name, coll)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=r, radius2=r, depth=depth)
    _commit(obj, bm)
    obj.location = loc
    return obj


def cone(name, coll, r, depth, loc):
    obj, bm = _mesh(name, coll)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=r, radius2=0.02, depth=depth)
    _commit(obj, bm)
    obj.location = loc
    return obj


def torus(name, coll, major, minor, loc):
    # bmesh has no create_torus in Blender 4.x
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major,
        minor_radius=minor,
        major_segments=36,
        minor_segments=10,
        location=loc,
    )
    obj = bpy.context.active_object
    obj.name = name
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    coll.objects.link(obj)
    if hasattr(obj.data, "polygons"):
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def principled(name, color, roughness=0.35, emission=None, emission_strength=0.0, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    c = (*color, 1.0)
    if "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = c
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = roughness
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metallic
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.22
    elif "Subsurface" in bsdf.inputs:
        bsdf.inputs["Subsurface"].default_value = 0.22
    if emission:
        for key in ("Emission Color", "Emission"):
            if key in bsdf.inputs:
                try:
                    bsdf.inputs[key].default_value = (*emission, 1.0)
                except Exception:
                    pass
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def assign(obj, mat) -> None:
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def look_at(obj, target) -> None:
    direction = Vector(target) - obj.location
    if direction.length < 0.001:
        return
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_cam(name, coll, loc, target, lens=45, dof=True):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.clip_start = 0.05
    data.sensor_fit = "VERTICAL"
    if dof:
        data.dof.use_dof = True
        data.dof.focus_distance = max(0.4, (Vector(loc) - Vector(target)).length)
        data.dof.aperture_fstop = 2.4
    cam = bpy.data.objects.new(name, data)
    coll.objects.link(cam)
    cam.location = loc
    look_at(cam, target)
    return cam


def key_cam(cam, loc, target, frame: int) -> None:
    cam.location = loc
    look_at(cam, target)
    cam.keyframe_insert("location", frame=frame)
    cam.keyframe_insert("rotation_euler", frame=frame)


def add_area(name, coll, loc, target, energy, size, color):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    coll.objects.link(obj)
    obj.location = loc
    look_at(obj, target)
    return obj


def label(name, coll, text, loc, size=0.24, color=(1, 1, 1)):
    curve = bpy.data.curves.new(name, type="FONT")
    curve.body = (text or "HELLO")[:18]
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.016
    if FONT.exists():
        try:
            curve.font = bpy.data.fonts.load(str(FONT))
        except Exception:
            pass
    obj = bpy.data.objects.new(name, curve)
    coll.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (radians(90), 0, 0)
    mat = principled(name + "_m", color, emission=color, emission_strength=2.4)
    obj.data.materials.append(mat)
    return obj


def reset_scene() -> None:
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    except Exception:
        bpy.ops.wm.read_homefile(use_empty=True)


def setup_eevee(scene, frames: int, bloom: float, episode: dict | None = None) -> None:
    scene.frame_start = 1
    scene.frame_end = max(frames, 24)
    apply_local_grade(scene)
    apply_output_settings(scene, episode or {})
    ee = getattr(scene, "eevee", None)
    if ee is not None and hasattr(ee, "bloom_intensity"):
        try:
            ee.bloom_intensity = bloom
        except Exception:
            pass


def set_world(scene, bg, strength: float = 0.35) -> None:
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        scene.world = world
    world.use_nodes = True
    bg_node = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg_node is not None:
        bg_node.inputs[0].default_value = (*bg, 1.0)
        bg_node.inputs[1].default_value = float(strength)


def layout_offset(layout: str) -> Vector:
    return {
        "center": Vector((0.0, 0.0, 0.0)),
        "left_hero": Vector((-0.55, 0.0, 0.0)),
        "right_hero": Vector((0.55, 0.0, 0.05)),
        "high_hero": Vector((0.0, 0.0, 0.35)),
        "low_hero": Vector((0.0, 0.15, -0.2)),
        "wide": Vector((0.25, -0.1, 0.1)),
    }.get(layout, Vector((0.0, 0.0, 0.0)))


def build_hero(kind: str, col, rgb, origin: Vector, rng: random.Random):
    hero_c = principled("Hero", rgb, 0.28, emission=rgb, emission_strength=0.45)
    support_c = principled("Support", (0.92, 0.78, 0.18), 0.38, metallic=0.15)
    o = origin
    kind = (kind or "shape").lower()

    if kind in {"sky", "sun"}:
        sky = sphere("SKY_DOME", col, 7.2, (0, 1.2, 0.4), u=36, v=18)
        assign(sky, principled("Sky", (0.18, 0.38, 0.85), 0.92, emission=(0.25, 0.45, 0.95), emission_strength=0.55))
        sky.scale = (1, 1, 0.42)
        hero = sphere("HERO", col, 0.95, o + Vector((0.55, -0.15, 1.7)))
        assign(hero, principled("Sun", (1.0, 0.82, 0.18), 0.15, emission=(1.0, 0.9, 0.25), emission_strength=6.0))
        return hero
    if kind in {"rain", "cloud", "snow"}:
        hero = sphere("HERO", col, 0.72, o + Vector((0, 0, 1.85)))
        hero.scale = (1.7, 1.15, 0.85)
        assign(hero, hero_c)
        for i in range(5):
            drop = sphere(f"DROP{i}", col, 0.09 + rng.random() * 0.06, o + Vector((rng.uniform(-0.9, 0.9), 0.1, 0.4 + i * 0.18)))
            assign(drop, principled(f"Drop{i}", (0.35, 0.7, 1.0), 0.12, emission=(0.4, 0.75, 1), emission_strength=0.4))
        return hero
    if kind == "circuit":
        hero = cube("HERO", col, 0.72, o + Vector((0, 0, 0.7)))
        assign(hero, hero_c)
        loop = torus("LOOP", col, 0.95, 0.07, o + Vector((0, 0, 1.15)))
        assign(loop, principled("Wire", (0.95, 0.75, 0.1), 0.2, emission=(1, 0.85, 0.15), emission_strength=2.0, metallic=0.7))
        return hero
    if kind in {"tree", "leaf", "seed"}:
        hero = cylinder("HERO", col, 0.2, 1.7, o + Vector((0, 0, 0.95)))
        assign(hero, principled("Bark", (0.28, 0.16, 0.08), 0.7))
        canopy = sphere("CANOPY", col, 0.9, o + Vector((0, 0, 2.05)))
        assign(canopy, principled("Canopy", (0.18, 0.55, 0.22), 0.48, emission=(0.15, 0.4, 0.15), emission_strength=0.25))
        return hero
    if kind in {"car", "clock"}:
        hero = cube("HERO", col, 1.1, o + Vector((0, 0, 0.82)))
        hero.scale = (1.55, 0.78, 0.68)
        assign(hero, hero_c)
        wheel_m = principled("Wheel", (0.08, 0.08, 0.08), 0.45, metallic=0.4)
        for name, x in (("W1", -0.52), ("W2", 0.52)):
            w = cylinder(name, col, 0.26, 0.16, o + Vector((x, 0.42, 0.26)))
            w.rotation_euler = (radians(90), 0, 0)
            assign(w, wheel_m)
        return hero
    if kind == "rocket":
        hero = cone("HERO", col, 0.38, 1.8, o + Vector((0, 0, 1.2)))
        assign(hero, hero_c)
        fin = cube("FIN", col, 0.4, o + Vector((0.35, 0, 0.45)))
        assign(fin, support_c)
        return hero
    if kind in {"rainbow"}:
        hero = torus("HERO", col, 1.15, 0.08, o + Vector((0, 0, 1.1)))
        hero.rotation_euler = (radians(70), 0, 0)
        assign(hero, hero_c)
        return hero
    if kind in {"magnet"}:
        a = cube("HERO", col, 0.85, o + Vector((-0.25, 0, 0.9)))
        a.scale = (0.35, 0.35, 1.3)
        b = cube("ARM", col, 0.85, o + Vector((0.35, 0, 0.9)))
        b.scale = (0.35, 0.35, 1.3)
        assign(a, hero_c)
        assign(b, support_c)
        return a
    if kind in {"fire"}:
        hero = cone("HERO", col, 0.55, 1.5, o + Vector((0, 0, 1.0)))
        assign(hero, principled("Fire", rgb, 0.25, emission=rgb, emission_strength=3.5))
        return hero
    if kind in {"heart"}:
        a = sphere("HERO", col, 0.55, o + Vector((-0.28, 0, 1.25)))
        b = sphere("HEART2", col, 0.55, o + Vector((0.28, 0, 1.25)))
        c = cube("HEART3", col, 0.85, o + Vector((0, 0, 0.85)))
        c.rotation_euler = (0, 0, radians(45))
        assign(a, hero_c)
        assign(b, hero_c)
        assign(c, hero_c)
        return a
    if kind in {"eye"}:
        hero = sphere("HERO", col, 0.85, o + Vector((0, 0, 1.15)))
        iris = sphere("IRIS", col, 0.38, o + Vector((0, -0.55, 1.15)))
        assign(hero, principled("Eye", (0.95, 0.95, 0.97), 0.12))
        assign(iris, hero_c)
        return hero
    if kind in {"book"}:
        hero = cube("HERO", col, 1.15, o + Vector((0, 0, 0.55)))
        hero.scale = (1.4, 0.2, 1.0)
        assign(hero, hero_c)
        return hero
    if kind in {"wave", "water"}:
        hero = sphere("HERO", col, 0.7, o + Vector((0, 0, 0.7)))
        hero.scale = (2.2, 1.4, 0.35)
        assign(hero, principled("Water", (0.12, 0.45, 0.85), 0.08, emission=(0.1, 0.4, 0.9), emission_strength=0.5))
        return hero
    if kind in {"ball", "bubble", "apple", "egg", "moon", "star", "earth"}:
        hero = sphere("HERO", col, 0.88, o + Vector((0, 0, 1.15)))
        assign(hero, hero_c)
        if kind == "star":
            spike = cone("SPIKE", col, 0.18, 0.7, o + Vector((0, 0, 1.85)))
            assign(spike, support_c)
        return hero
    if kind in {"ice", "rock", "lock", "shape"}:
        hero = cube("HERO", col, 1.05, o + Vector((0, 0, 0.9)))
        hero.rotation_euler = (0, 0, radians(rng.uniform(-18, 18)))
        assign(hero, hero_c)
        return hero
    if kind in {"hand", "bone", "ant"}:
        hero = cylinder("HERO", col, 0.26, 1.55, o + Vector((0, 0, 1.0)))
        assign(hero, hero_c)
        return hero
    hero = sphere("HERO", col, 0.72, o + Vector((0, 0, 1.1)))
    hero.scale = (1.0, 0.82, 1.18)
    assign(hero, hero_c)
    return hero


def scatter_particles(col, n: int, rgb, rng: random.Random) -> None:
    mat = principled("Dust", rgb, 0.2, emission=rgb, emission_strength=1.1)
    for i in range(n):
        p = sphere(
            f"PT{i}",
            col,
            0.04 + rng.random() * 0.07,
            (
                rng.uniform(-1.8, 1.8),
                rng.uniform(-0.6, 1.2),
                rng.uniform(0.3, 2.6),
            ),
            u=12,
            v=8,
        )
        assign(p, mat)


def animate_cam(cam, start, target, move: str, frames: int, rng: random.Random) -> None:
    start = Vector(start)
    target = Vector(target)
    end = Vector(start)
    if move == "push":
        end = start.lerp(target, 0.12 + rng.random() * 0.18)
    elif move == "orbit":
        end = Vector((start.x + rng.choice((-1, 1)) * (0.35 + rng.random() * 0.45), start.y + 0.12, start.z + 0.08))
    elif move == "slide":
        end = Vector((start.x + rng.choice((-1, 1)) * 0.55, start.y, start.z + rng.uniform(-0.1, 0.15)))
    elif move == "rise":
        end = Vector((start.x, start.y + 0.08, start.z + 0.28 + rng.random() * 0.2))
    else:
        end = Vector((start.x + rng.uniform(-0.08, 0.08), start.y, start.z + rng.uniform(-0.05, 0.08)))
    key_cam(cam, start, target, 1)
    key_cam(cam, end, target, max(frames, 24))


def cinematic_cameras(col_c, aim, hero_loc):
    """Readable 9:16 coverage of the hero — never jammed into a wall of mesh."""
    aim = Vector(aim)
    h = Vector(hero_loc)
    hook = add_cam("CAM_HOOK", col_c, Vector((0.05, -5.4, 1.85)), aim, 32)
    wide = add_cam("CAM_WIDE", col_c, Vector((0.35, -6.2, 2.35)), aim, 26)
    profile = add_cam("CAM_PROFILE", col_c, Vector((3.4, -4.1, 1.7)), h, 38)
    macro = add_cam("CAM_MACRO", col_c, h + Vector((1.15, -2.35, 0.35)), h, 50)
    orbit = add_cam("CAM_ORBIT", col_c, Vector((-3.5, -4.3, 1.75)), h, 36)
    detail = add_cam("CAM_DETAIL", col_c, Vector((1.7, -3.5, 1.25)), h, 44)
    close = add_cam("CAM_CLOSE", col_c, Vector((0.25, -3.8, 1.55)), h, 40)
    hero = add_cam("CAM_HERO", col_c, Vector((0.15, -4.6, 1.7)), h, 34)
    return {
        "CAM_HOOK": hook,
        "CAM_WIDE": wide,
        "CAM_PROFILE": profile,
        "CAM_MACRO": macro,
        "CAM_ORBIT": orbit,
        "CAM_DETAIL": detail,
        "CAM_CLOSE": close,
        "CAM_HERO": hero,
        "CAM_EXPLAIN": profile,
        "CAM_DUST": macro,
        "CAM_BLAST": wide,
        "CAM_CAR": orbit,
        "CAM_LUNGS": hero,
    }


def dress_sky(col, rgb, origin, rng):
    sun = sphere("HERO", col, 0.95, origin + Vector((0.35, -0.2, 2.05)), u=40, v=20)
    assign(sun, principled("Sun", (1.0, 0.84, 0.22), 0.12, emission=(1.0, 0.9, 0.3), emission_strength=8.0))
    earth = sphere("EARTH", col, 0.62, origin + Vector((-1.55, 0.55, 0.95)), u=32, v=16)
    assign(earth, principled("Earth", (0.12, 0.38, 0.78), 0.42, emission=(0.1, 0.35, 0.8), emission_strength=0.35))
    land = sphere("LAND", col, 0.63, origin + Vector((-1.52, 0.48, 0.98)), u=24, v=12)
    land.scale = (0.55, 0.4, 0.35)
    assign(land, principled("Land", (0.18, 0.48, 0.16), 0.55))
    mote = principled("Scatter", (0.45, 0.72, 1.0), 0.15, emission=(0.4, 0.7, 1.0), emission_strength=1.6)
    for i in range(22):
        p = sphere(
            f"AIR{i}",
            col,
            0.05 + rng.random() * 0.07,
            origin
            + Vector((rng.uniform(-1.6, 1.6), rng.uniform(-0.8, 1.4), rng.uniform(0.5, 2.4))),
            u=14,
            v=8,
        )
        assign(p, mote)
    return sun


def dress_rain(col, rgb, origin, rng):
    fl = plane("SET_Floor", col, 16.0, (0, 0, 0))
    assign(fl, principled("Wet", (0.07, 0.09, 0.12), 0.12, metallic=0.25))
    cloud = sphere("HERO", col, 0.78, origin + Vector((0.0, 0.1, 2.15)), u=28, v=16)
    cloud.scale = (1.85, 1.2, 0.78)
    assign(cloud, principled("Cloud", (0.82, 0.86, 0.92), 0.55, emission=(0.7, 0.8, 0.95), emission_strength=0.2))
    drop_m = principled("Drop", (0.35, 0.7, 1.0), 0.08, emission=(0.4, 0.75, 1), emission_strength=0.55)
    for i in range(10):
        d = sphere(
            f"DROP{i}",
            col,
            0.08 + rng.random() * 0.05,
            origin + Vector((rng.uniform(-1.1, 1.1), rng.uniform(-0.3, 0.4), 0.25 + i * 0.16)),
            u=14,
            v=8,
        )
        assign(d, drop_m)
    return cloud


def dress_studio(col, rgb, origin, rng, floor_rgb, kind):
    fl = plane("SET_Floor", col, 16.0, (0, 0, 0))
    assign(fl, principled("Floor", floor_rgb, 0.42))
    hero = build_hero(kind, col, rgb, origin, rng)
    scatter_particles(col, 10, rgb, rng)
    extra = sphere("SUPPORT", col, 0.28, origin + Vector((1.35, 0.2, 0.55)), u=20, v=12)
    assign(extra, principled("Accent", rgb, 0.28, emission=rgb, emission_strength=0.7))
    return hero


def build_cinematic(episode: dict) -> None:
    reset_scene()
    scene = bpy.context.scene
    shots = episode.get("shots") or [{"camera": "CAM_HOOK", "frames": 72, "move": "push"}]
    frames = sum(int(s.get("frames", 48)) for s in shots) or 720
    world = episode.get("world") or {}
    bloom = float(world.get("bloom") or 0.05)
    setup_eevee(scene, frames, bloom, episode)
    rng = random.Random(int(episode.get("seed") or 1))
    kind = str(episode.get("scene") or "shape").lower()
    bg = tuple(world.get("bg") or (0.04, 0.07, 0.1))
    if kind in {"sky", "sun"}:
        set_world(scene, (0.16, 0.40, 0.92), strength=1.15)
    elif kind in {"rain", "cloud", "snow"}:
        set_world(scene, (0.06, 0.09, 0.14), strength=0.32)
    elif kind in {"star", "moon", "rocket", "earth"}:
        set_world(scene, (0.015, 0.02, 0.06), strength=0.18)
    else:
        set_world(scene, bg, strength=0.22)

    master = scene.collection
    col = bpy.data.collections.new("SET")
    master.children.link(col)
    col_c = bpy.data.collections.new("CAMERAS")
    master.children.link(col_c)
    col_l = bpy.data.collections.new("LIGHTS")
    master.children.link(col_l)

    rgb = _hex(episode.get("accent_color", "#4FC3F7"))
    origin = layout_offset(str(world.get("layout") or "center"))
    floor_rgb = tuple(world.get("floor") or (0.12, 0.26, 0.30))
    if kind in {"sky", "sun"}:
        hero = dress_sky(col, rgb, origin, rng)
    elif kind in {"rain", "cloud", "snow"}:
        hero = dress_rain(col, rgb, origin, rng)
    else:
        hero = dress_studio(col, rgb, origin, rng, floor_rgb, kind)

    hs = float(world.get("hero_scale") or 1.0)
    hero.scale = Vector(hero.scale) * hs
    aim = Vector(hero.location)
    cams = cinematic_cameras(col_c, aim, hero.location)
    scene.camera = cams["CAM_HOOK"]
    add_area("LGT_Key", col_l, (2.8, -4.2, 3.6), aim, 520, 2.4, (1.0, 0.96, 0.9))
    add_area("LGT_Fill", col_l, (-3.0, -2.6, 2.0), aim, 150, 3.2, (0.7, 0.88, 1.0))
    add_area("LGT_Rim", col_l, (-1.4, 2.8, 2.6), aim, 280, 1.2, rgb)
    add_area("LGT_Kick", col_l, (0.2, -1.4, 4.0), aim, 110, 2.6, (0.9, 0.95, 1.0))
    if kind in {"sky", "sun"}:
        add_area("LGT_Sun", col_l, tuple(Vector(hero.location) + Vector((0.2, -1.2, 0.8))), aim, 700, 1.6, (1.0, 0.92, 0.55))

    hero.keyframe_insert("scale", frame=1)
    s2 = Vector(hero.scale) * (1.04 + rng.random() * 0.05)
    hero.scale = s2
    hero.keyframe_insert("scale", frame=max(frames // 2, 12))
    hero.scale = Vector(hero.scale) / 1.04
    hero.keyframe_insert("scale", frame=max(frames, 24))


def render_shots(episode: dict, frames_dir: Path) -> None:
    scene = bpy.context.scene
    cameras = {o.name: o for o in bpy.data.objects if o.type == "CAMERA"}
    render_timeline(bpy, scene, episode, frames_dir, cameras)


def main() -> None:
    job = _job()
    episode = job["episode"]
    frames_dir = Path(job["frames_dir"])
    frames_dir.mkdir(parents=True, exist_ok=True)
    build_cinematic(episode)
    render_shots(episode, frames_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)
