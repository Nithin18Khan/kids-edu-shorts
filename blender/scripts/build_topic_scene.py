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
    obj, bm = _mesh(name, coll)
    bmesh.ops.create_torus(
        bm,
        major_radius=major,
        minor_radius=minor,
        major_segments=36,
        minor_segments=10,
    )
    _commit(obj, bm)
    obj.location = loc
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


def add_cam(name, coll, loc, target, lens=45, dof=False):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.clip_start = 0.05
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


def setup_eevee(scene, frames: int, bloom: float) -> None:
    ids = [e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items]
    ci = os.environ.get("KIDS_CI") == "1" or os.environ.get("GITHUB_ACTIONS") == "true"
    if ci and "BLENDER_WORKBENCH" in ids:
        # CPU-safe on GitHub runners (no GPU / EGL crash)
        scene.render.engine = "BLENDER_WORKBENCH"
    elif ci and "BLENDER_EEVEE" in ids:
        scene.render.engine = "BLENDER_EEVEE"
    elif "BLENDER_EEVEE_NEXT" in ids:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    else:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = max(frames, 24)
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if ci:
        return
    ee = getattr(scene, "eevee", None)
    samples = 16
    preview = 8
    if ee is not None:
        for attr, val in (("taa_render_samples", samples), ("taa_samples", preview), ("gi_cubemap_resolution", "128")):
            if hasattr(ee, attr):
                try:
                    setattr(ee, attr, val)
                except Exception:
                    pass
        if hasattr(ee, "use_bloom"):
            ee.use_bloom = True
            if hasattr(ee, "bloom_intensity"):
                ee.bloom_intensity = bloom


def set_world(scene, bg) -> None:
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        scene.world = world
    world.use_nodes = True
    bg_node = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg_node is not None:
        bg_node.inputs[0].default_value = (*bg, 1.0)
        bg_node.inputs[1].default_value = 0.28


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


def build_cinematic(episode: dict) -> None:
    reset_scene()
    scene = bpy.context.scene
    shots = episode.get("shots") or [{"camera": "CAM_HOOK", "frames": 72, "move": "push"}]
    frames = sum(int(s.get("frames", 48)) for s in shots) or 720
    world = episode.get("world") or {}
    bloom = float(world.get("bloom") or 0.05)
    setup_eevee(scene, frames, bloom)
    set_world(scene, tuple(world.get("bg") or (0.04, 0.07, 0.1)))
    rng = random.Random(int(episode.get("seed") or 1))

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
    fl = plane("SET_Floor", col, 14.0, (0, 0, 0))
    assign(fl, principled("Floor", floor_rgb, 0.55))
    back = cube("SET_Back", col, 1.0, (0, 3.6, 2.2))
    back.scale = (10, 0.2, 5)
    assign(back, principled("Back", tuple(max(0.0, c * 0.45) for c in floor_rgb), 0.7))

    hero = build_hero(str(episode.get("scene") or "shape"), col, rgb, origin, rng)
    hs = float(world.get("hero_scale") or 1.0)
    hero.scale = Vector(hero.scale) * hs
    scatter_particles(col, int(world.get("particles") or 8), rgb, rng)

    extra = cube("SUPPORT", col, 0.42, origin + Vector((1.45 + rng.uniform(-0.2, 0.2), 0.15, 0.5)))
    assign(extra, principled("Gold", (0.9, 0.75, 0.15), 0.3, metallic=0.35))
    extra2 = sphere("SUPPORT2", col, 0.24 + rng.random() * 0.1, origin + Vector((-1.4, 0.1, 0.5)))
    assign(extra2, principled("Accent2", rgb, 0.3, emission=rgb, emission_strength=0.8))

    lbl = (episode.get("hero_label") or episode.get("thumbnail_text") or episode.get("title") or "WOW")[:16]
    label("LBL", col, lbl, origin + Vector((0.0, -1.15, 2.15)), size=0.22 + rng.random() * 0.08, color=rgb)

    aim = origin + Vector((0.0, 0.0, 1.15))
    j = world.get("cam_jitter") or [0, 0, 0]
    jitter = Vector((float(j[0]), float(j[1]), float(j[2])))
    cams = {
        "CAM_HOOK": add_cam("CAM_HOOK", col_c, Vector((0.15, -3.55, 1.5)) + jitter, aim, 48),
        "CAM_EXPLAIN": add_cam("CAM_EXPLAIN", col_c, Vector((1.55, -3.05, 1.55)) + jitter * 0.7, aim, 38),
        "CAM_MACRO": add_cam("CAM_MACRO", col_c, Vector((0.05, -2.15, 1.32)) + jitter * 0.4, aim + Vector((0, 0, 0.1)), 58, dof=True),
        "CAM_CLOSE": add_cam("CAM_CLOSE", col_c, Vector((0.2, -2.65, 1.22)) + jitter * 0.5, aim + Vector((0, 0, -0.08)), 52, dof=True),
    }
    scene.camera = cams["CAM_HOOK"]
    add_area("LGT_Key", col_l, (2.6, -2.9, 3.4), aim, 520, 1.8, (1.0, 0.95, 0.88))
    add_area("LGT_Fill", col_l, (-2.6, -2.1, 1.7), aim, 140, 3.0, (0.55, 0.72, 1.0))
    add_area("LGT_Rim", col_l, (-0.8, 2.4, 2.4), aim, 280, 0.9, rgb)
    add_area("LGT_Kick", col_l, (0.2, -1.2, 3.6), aim, 90, 2.4, (0.9, 0.95, 1.0))

    for shot in shots:
        cam = cams.get(shot.get("camera") or "CAM_HOOK")
        if cam is None:
            continue
        animate_cam(cam, Vector(cam.location), aim, str(shot.get("move") or "push"), frames, rng)

    hero.keyframe_insert("scale", frame=1)
    s2 = Vector(hero.scale) * (1.05 + rng.random() * 0.08)
    hero.scale = s2
    hero.keyframe_insert("scale", frame=max(frames // 2, 12))
    hero.scale = Vector(hero.scale) / (1.05 + 0.01)
    hero.keyframe_insert("scale", frame=max(frames, 24))
    extra.keyframe_insert("location", frame=1)
    extra.location = Vector(extra.location) + Vector((0.12, -0.08, 0.16))
    extra.keyframe_insert("location", frame=max(frames, 24))


def render_shots(episode: dict, frames_dir: Path) -> None:
    scene = bpy.context.scene
    scene.render.filepath = str(frames_dir / "frame_")
    cameras = {o.name: o for o in bpy.data.objects if o.type == "CAMERA"}
    cursor = 1
    for shot in episode.get("shots") or []:
        name = shot.get("camera", "CAM_HOOK")
        length = int(shot.get("frames", 48))
        cam = cameras.get(name) or scene.camera
        scene.camera = cam
        scene.frame_start = cursor
        scene.frame_end = cursor + length - 1
        print(f"Rendering {shot.get('id')} {name} move={shot.get('move')} frames={length}")
        bpy.ops.render.render(animation=True)
        cursor += length
    print("Blender cinematic render complete →", frames_dir)


def main() -> None:
    job = _job()
    episode = job["episode"]
    frames_dir = Path(job["frames_dir"])
    frames_dir.mkdir(parents=True, exist_ok=True)
    build_cinematic(episode)
    render_shots(episode, frames_dir)


if __name__ == "__main__":
    main()
