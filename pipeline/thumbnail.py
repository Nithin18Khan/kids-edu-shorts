"""Unique 16:9 YouTube thumbnail that matches this episode's topic."""

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
        .replace(",", " ")
    )
    return cleaned[:28]


def _font_file() -> Path | None:
    for p in (
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
    ):
        if p.exists():
            return p
    return None


def pick_unique_frame(frames_dir: Path, episode: dict) -> Path | None:
    if frames_dir is None or not frames_dir.exists():
        return None
    frames = (
        sorted(frames_dir.glob("frame_*.png"))
        + sorted(frames_dir.glob("frame_*.jpg"))
        + sorted(frames_dir.glob("frame_*.jpeg"))
    )
    if not frames:
        return None
    seed = int(episode.get("seed") or 1)
    idx = max(0, min(len(frames) - 1, int(len(frames) * 0.12) + (seed % 12)))
    return frames[idx]


def _still_from_video(video_path: Path, out_dir: Path) -> Path | None:
    if video_path is None or not video_path.exists():
        return None
    dest = out_dir / "thumb_src.jpg"
    ffmpeg = find_ffmpeg()
    cmd = [
        ffmpeg,
        "-y",
        "-ss",
        "2.5",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-q:v",
        "3",
        str(dest),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        return None
    return dest if dest.exists() and dest.stat().st_size > 1000 else None


def make_thumbnail(
    episode: dict,
    frames_dir: Path,
    out_dir: Path,
    *,
    video_path: Path | None = None,
) -> Path | None:
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "thumbnail.jpg"
    src = pick_unique_frame(frames_dir, episode)
    if src is None and video_path is not None:
        src = _still_from_video(video_path, out_dir)
    ffmpeg = find_ffmpeg()
    text = _safe_text(str(episode.get("thumbnail_text") or episode.get("title") or "KIDS SCIENCE"))
    font = _font_file()
    font_arg = f"fontfile='{font.as_posix()}':" if font is not None else ""
    seed = int(episode.get("seed") or 1)
    y_off = 280 + (seed % 420)
    title_filter = (
        f"drawtext={font_arg}text='{text}':fontcolor=yellow:fontsize=68:"
        f"borderw=5:bordercolor=black@0.75:x=(w-text_w)/2:y=h-150"
    )
    if src is not None:
        vf = (
            f"scale=1080:1920,"
            f"crop=1080:608:0:{y_off},"
            f"scale=1280:720,"
            f"{title_filter}"
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
    else:
        vf = f"scale=1280:720,{title_filter}"
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x0b3d4a:s=1280x720:d=1",
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
        fallback = [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x0b3d4a:s=1280x720:d=1",
            "-frames:v",
            "1",
            "-q:v",
            "3",
            str(dest),
        ]
        if src is not None:
            fallback = [
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
            ]
        subprocess.run(fallback, check=True, capture_output=True)
    print(f"Thumbnail: {dest.name} text='{text}'")
    return dest if dest.exists() else None
