"""Same render grade as the local sneeze film (body_gentle).

1080x1920, 24fps, PNG, EEVEE, AgX, GTAO. Never Workbench / 540p / frame-skip.
"""

from __future__ import annotations

from mathutils import Vector

CAM_ALIAS = {
    "CAM_EXPLAIN": "CAM_PROFILE",
}


def apply_local_grade(scene) -> None:
    engines = []
    try:
        engines = [e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items]
    except Exception:
        engines = []
    if "BLENDER_EEVEE_NEXT" in engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in engines:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.fps = 24
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    eevee = getattr(scene, "eevee", None)
    if eevee is not None:
        for attr, val in (("taa_render_samples", 8), ("taa_samples", 6), ("use_gtao", True)):
            if hasattr(eevee, attr):
                try:
                    setattr(eevee, attr, val)
                except Exception:
                    pass
        if hasattr(eevee, "use_bloom"):
            eevee.use_bloom = True
            if hasattr(eevee, "bloom_intensity"):
                eevee.bloom_intensity = 0.05
    try:
        scene.view_settings.view_transform = "AgX"
    except TypeError:
        pass
    scene.view_settings.exposure = 0.08


def resolve_camera(cameras: dict, name: str):
    want = CAM_ALIAS.get(name, name)
    return (
        cameras.get(want)
        or cameras.get(name)
        or cameras.get("CAM_HOOK")
        or next(iter(cameras.values()), None)
    )


def push_camera(cam, start_f: int, end_f: int, move: str) -> None:
    if cam is None:
        return
    if cam.animation_data:
        cam.animation_data_clear()
    start = Vector(cam.location)
    end = Vector(start)
    move = (move or "push").lower()
    if move == "orbit":
        end.x += 0.28
        end.y += 0.18
    elif move == "slide":
        end.x += 0.32
    elif move == "rise":
        end.z += 0.18
        end.y += 0.12
    elif move == "hold":
        end.y += 0.06
    else:
        end.y += 0.30
        end.z -= 0.04
        end.x -= 0.06
    cam.location = start
    cam.keyframe_insert("location", frame=start_f)
    cam.location = end
    cam.keyframe_insert("location", frame=end_f)
