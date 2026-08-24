"""Unique 16:9 YouTube thumbnail from a unique Blender frame. Never reuse another episode's still."""

from __future__ import annotations

import subprocess
from pathlib import Path

from pipeline.detect import find_ffmpeg


def _safe_text(text: str) -> str:
    cleaned = (
        (text or "KIDS SCIENCE")
        .replace("\\", " ")
        .replace("'", "")
        .replace(":", " ")
        .replace("%", " ")
        .replace("=", " ")
    )
    return cleaned[:28]


def pick_unique_frame(frames_dir: Path, episode: dict) -> Path | None:
    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames:
        return None
    seed = int(episode.get("seed") or 1)
    return frames[seed % len(frames)]


def make_thumbnail(episode: dict, frames_dir: Path, out_dir: Path) -> Path | None:
    src = pick_unique_frame(frames_dir, episode)
    if src is None:
        return None
    dest = out_dir / "thumbnail.jpg"
    ffmpeg = find_ffmpeg()
    text = _safe_text(str(episode.get("thumbnail_text") or episode.get("title") or "WOW"))
    font = Path(r"C:\Windows\Fonts\arialbd.ttf")
    font_arg = f"fontfile='{font.as_posix()}':" if font.exists() else ""
    # Unique crop window so two 9:16 films do not share the same 16:9 slice.
    seed = int(episode.get("seed") or 1)
    y_off = 280 + (seed % 420)
    vf = (
        f"scale=1080:1920,"
        f"crop=1080:608:0:{y_off},"
        f"scale=1280:720,"
        f"drawtext={font_arg}text='{text}':fontcolor=white:fontsize=64:"
        f"borderw=4:bordercolor=black@0.65:x=(w-text_w)/2:y=h-140"
    )
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(src),
        "-vf",
        vf,
        "-frames:v",
        "1",
        "-q:v",
        "3",
        str(dest),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(src),
                "-vf",
                f"scale=1080:1920,crop=1080:608:0:{y_off},scale=1280:720",
                "-frames:v",
                "1",
                "-q:v",
                "3",
                str(dest),
            ],
            check=True,
        )
    print(f"Thumbnail: {dest.name} from {src.name} (unique crop {y_off})")
    return dest
