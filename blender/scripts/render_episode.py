"""
Blender-side episode renderer.
Invoked as: blender --background template.blend --python render_episode.py -- job.json

Quality target: Zack D. Films — stylized 3D Shorts, kid-safe.
Switches cameras, tints Accent, optionally imports free models into SLOT_* collections.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


SKIP_SUFFIXES = {".md", ".txt", ""}


def _argv_job() -> Path:
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        args = sys.argv[idx + 1 :]
    else:
        args = sys.argv[1:]
    if not args:
        raise SystemExit("Usage: blender ... --python render_episode.py -- job.json")
    return Path(args[0])


def _hex_rgb(accent: str) -> tuple[float, float, float]:
    hex_color = accent.lstrip("#")
    if len(hex_color) != 6:
        return (0.31, 0.76, 0.97)
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return r, g, b


def _apply_accent(bpy, accent: str) -> None:
    r, g, b = _hex_rgb(accent)
    mat = bpy.data.materials.get("Accent")
    if mat and mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if "Base Color" in node.inputs:
                    node.inputs["Base Color"].default_value = (r, g, b, 1.0)
                for key in ("Emission Color", "Emission"):
                    if key in node.inputs:
                        try:
                            node.inputs[key].default_value = (r, g, b, 1.0)
                        except Exception:
                            pass
    rim = bpy.data.objects.get("LGT_Rim")
    if rim is not None and getattr(rim, "data", None) is not None and hasattr(rim.data, "color"):
        rim.data.color = (r, g, b)


def _import_into_slot(bpy, path: Path, slot: str) -> None:
    if not path.exists() or path.suffix.lower() in SKIP_SUFFIXES:
        print(f"Skip model slot={slot} path={path}")
        return
    coll_name = f"SLOT_{slot}"
    coll = bpy.data.collections.get(coll_name)
    if coll is None:
        coll = bpy.data.collections.new(coll_name)
        bpy.context.scene.collection.children.link(coll)

    before = set(bpy.data.objects)
    suffix = path.suffix.lower()
    try:
        if suffix in {".glb", ".gltf"}:
            bpy.ops.import_scene.gltf(filepath=str(path))
        elif suffix == ".fbx":
            bpy.ops.import_scene.fbx(filepath=str(path))
        elif suffix == ".obj":
            if hasattr(bpy.ops.wm, "obj_import"):
                bpy.ops.wm.obj_import(filepath=str(path))
            else:
                bpy.ops.import_scene.obj(filepath=str(path))
        elif suffix == ".blend":
            with bpy.data.libraries.load(str(path), link=False) as (src, dst):
                dst.objects = list(src.objects)
            for obj in dst.objects:
                if obj is not None:
                    coll.objects.link(obj)
            print(f"Appended .blend into {coll_name}: {path.name}")
            return
        else:
            print(f"Unknown model type for slot={slot}: {path}")
            return
    except Exception as exc:  # noqa: BLE001 — keep render going
        print(f"Model import failed slot={slot}: {exc}")
        return

    for obj in bpy.data.objects:
        if obj in before:
            continue
        for existing in list(obj.users_collection):
            existing.objects.unlink(obj)
        if obj.name not in coll.objects:
            coll.objects.link(obj)
    print(f"Imported {path.name} → {coll_name}")


def _link_models(bpy, episode: dict, root: Path) -> None:
    for item in episode.get("models") or []:
        slot = item.get("slot", "hero_prop")
        rel = item.get("path")
        if not rel:
            continue
        path = Path(rel)
        if not path.is_absolute():
            path = root / path
        _import_into_slot(bpy, path, slot)


def main() -> None:
    import bpy

    job_path = _argv_job()
    job = json.loads(job_path.read_text(encoding="utf-8"))
    episode = job["episode"]
    frames_dir = Path(job["frames_dir"])
    frames_dir.mkdir(parents=True, exist_ok=True)
    root = Path(job.get("root", "."))

    scene = bpy.context.scene
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.fps = 24
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(frames_dir / "frame_")

    try:
        _apply_accent(bpy, episode.get("accent_color", "#4FC3F7"))
    except Exception as exc:  # noqa: BLE001
        print("Accent tint skipped:", exc)

    try:
        _link_models(bpy, episode, root)
    except Exception as exc:  # noqa: BLE001
        print("Model link skipped:", exc)

    cameras = {obj.name: obj for obj in bpy.data.objects if obj.type == "CAMERA"}
    frame_cursor = 1
    for shot in episode.get("shots", []):
        cam_name = shot.get("camera", "CAM_HOOK")
        length = int(shot.get("frames", 48))
        cam = cameras.get(cam_name)
        if cam is not None:
            scene.camera = cam
        else:
            print(f"Camera {cam_name} missing — using {getattr(scene.camera, 'name', None)}")
        scene.frame_start = frame_cursor
        scene.frame_end = frame_cursor + length - 1
        print(f"Rendering shot {shot.get('id')} camera={cam_name} frames={length}")
        bpy.ops.render.render(animation=True)
        frame_cursor += length

    print("Blender render complete →", frames_dir)


if __name__ == "__main__":
    main()
