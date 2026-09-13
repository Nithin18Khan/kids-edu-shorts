"""Render the episode timeline at local cinematic grade."""

from __future__ import annotations

import os
from pathlib import Path

from local_grade import apply_local_grade, push_camera, resolve_camera

_MIN_FRAME_BYTES = 20_000


def is_ci() -> bool:
    return os.environ.get("KIDS_CI") == "1" or os.environ.get("GITHUB_ACTIONS") == "true"


def _frame_done(frames_dir: Path, frame: int) -> bool:
    for ext in ("png", "jpg", "jpeg"):
        path = frames_dir / f"frame_{frame:04d}.{ext}"
        if path.exists() and path.stat().st_size > _MIN_FRAME_BYTES:
            return True
    return False


def frame_step(episode: dict) -> int:
    return 1


def apply_output_settings(scene, episode: dict) -> None:
    apply_local_grade(scene)


def render_timeline(bpy, scene, episode: dict, frames_dir: Path, cameras: dict) -> None:
    frames_dir = Path(frames_dir)
    shots = list(episode.get("shots") or [])
    shot_index = episode.get("_shot_index")
    if shot_index is None:
        raw = os.environ.get("KIDS_SHOT_INDEX")
        shot_index = int(raw) if raw not in (None, "") else None
    cursor = 1
    scene.render.filepath = str(frames_dir / "frame_")
    for i, shot in enumerate(shots):
        name = shot.get("camera", "CAM_HOOK")
        length = int(shot.get("frames", 48))
        start = cursor
        end = cursor + length - 1
        cursor += length
        if shot_index is not None and i != int(shot_index):
            continue
        cam = resolve_camera(cameras, name)
        if cam is not None:
            scene.camera = cam
        else:
            print(f"Camera {name} missing — using {getattr(scene.camera, 'name', None)}")
        push_camera(cam, start, end, str(shot.get("move") or "push"))
        missing = [f for f in range(start, end + 1) if not _frame_done(frames_dir, f)]
        if not missing:
            print(f"Skip {shot.get('id')} {name} frames={start}-{end} (already on disk)")
            continue
        first_miss = missing[0]
        if missing == list(range(first_miss, end + 1)):
            scene.frame_start = first_miss
            scene.frame_end = end
            print(
                f"Rendering {shot.get('id')} {name} frames={first_miss}-{end} "
                "(resume, local 1080 Eevee 24fps)"
            )
            bpy.ops.render.render(animation=True)
        else:
            print(
                f"Rendering {shot.get('id')} {name} holes={len(missing)} "
                "(local 1080 Eevee 24fps)"
            )
            for f in missing:
                scene.frame_set(f)
                scene.render.filepath = str(frames_dir / f"frame_{f:04d}")
                bpy.ops.render.render(write_still=True)
            scene.render.filepath = str(frames_dir / "frame_")
    print("Blender render complete ->", frames_dir)
