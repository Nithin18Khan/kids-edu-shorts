from __future__ import annotations

import subprocess
from pathlib import Path

from pipeline.bgm import ensure_bgm
from pipeline.captions import episode_wants_captions
from pipeline.detect import find_ffmpeg, media_duration_sec


def _frame_pattern(frames_dir: Path) -> Path | None:
    for ext in ("png", "jpg", "jpeg"):
        if (frames_dir / f"frame_0001.{ext}").exists():
            return frames_dir / f"frame_%04d.{ext}"
    return None


def _count_frames(frames_dir: Path) -> int:
    n = 0
    for ext in ("png", "jpg", "jpeg"):
        n += len(list(frames_dir.glob(f"frame_*.{ext}")))
    return n


def assemble_short(
    episode: dict,
    out_dir: Path,
    voice_path: Path,
    frames_dir: Path,
    *,
    root: Path,
) -> Path:
    """Assemble 9:16 Short. Unique pictures cover the voice in real time."""
    final = out_dir / f"{episode['id']}_short.mp4"
    ffmpeg = find_ffmpeg()

    pattern = _frame_pattern(frames_dir)
    if pattern is not None:
        _assemble_sequence(
            ffmpeg, episode, out_dir, voice_path, frames_dir, pattern, final, root
        )
        return final
    frame_glob = sorted(frames_dir.glob("*.png")) + sorted(frames_dir.glob("*.jpg"))
    if frame_glob:
        still = frame_glob[0]
        cmd = [
            ffmpeg,
            "-y",
            "-loop",
            "1",
            "-i",
            str(still),
            "-i",
            str(voice_path),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            str(final),
        ]
        subprocess.run(cmd, check=True, cwd=str(out_dir))
        return final

    _assemble_slate(ffmpeg, episode, voice_path, final)
    return final


def _assemble_sequence(
    ffmpeg: str,
    episode: dict,
    out_dir: Path,
    voice_path: Path,
    frames_dir: Path,
    pattern: Path,
    final: Path,
    root: Path,
) -> None:
    n_frames = max(1, _count_frames(frames_dir))
    try:
        audio_sec = media_duration_sec(voice_path)
    except Exception:
        audio_sec = n_frames / 24.0
    # Unique stills span the full voice. Do not assume 24fps input (that
    # stretched a 4s CI clip into slow-mo). Play n_frames across audio_sec.
    end_sec = max(audio_sec, 0.04)
    in_fps = min(48.0, max(1.0, n_frames / end_sec))
    natural = n_frames / in_fps
    ratio = end_sec / natural
    print(
        f"Sync: voice {audio_sec:.2f}s, {n_frames} unique pictures at "
        f"{in_fps:.2f} fps ({natural:.2f}s) -> retiming {ratio:.4f}x"
    )

    scale = (
        "scale=1080:1920:flags=lanczos:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=24"
    )
    vf = scale if abs(ratio - 1.0) < 0.04 else f"setpts=PTS*{ratio:.8f},{scale}"
    burn = episode_wants_captions(episode)
    ass_path = out_dir / "captions.ass"
    if burn and ass_path.exists():
        vf = f"{vf},ass=captions.ass"
        print(f"Subtitles: {ass_path.name}")
    elif not burn:
        print("Subtitles: off")

    bgm = ensure_bgm(root, episode, out_dir)
    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        f"{in_fps:.6f}",
        "-i",
        str(pattern),
        "-i",
        str(voice_path),
    ]
    fade_out = max(0.05, end_sec - 1.35)
    if bgm is not None:
        print(f"BGM: {bgm.name} (under voice, fade out with narration)")
        cmd.extend(["-stream_loop", "-1", "-i", str(bgm)])
        fc = (
            f"[0:v]{vf}[v];"
            f"[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"volume=1.08[vo];"
            f"[2:a]atrim=0:{end_sec:.3f},asetpts=PTS-STARTPTS,"
            f"aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"volume=0.14,afade=t=in:st=0:d=1.15,"
            f"afade=t=out:st={fade_out:.3f}:d=1.3[bg];"
            f"[vo][bg]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.95[a]"
        )
        cmd.extend(
            [
                "-filter_complex",
                fc,
                "-map",
                "[v]",
                "-map",
                "[a]",
            ]
        )
    else:
        cmd.extend(["-vf", vf, "-map", "0:v", "-map", "1:a"])

    cmd.extend(
        [
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-t",
            f"{end_sec:.3f}",
            str(final),
        ]
    )
    subprocess.run(cmd, check=True, cwd=str(out_dir))


def _assemble_slate(ffmpeg: str, episode: dict, voice_path: Path, final: Path) -> None:
    title = episode.get("title", episode["id"]).replace(":", " -")
    vf = (
        "scale=1080:1920,"
        "drawtext=text='"
        + title.replace("'", "")
        + "':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2,"
        "drawtext=text='Blender template pending':fontcolor=gray:fontsize=32:"
        "x=(w-text_w)/2:y=(h-text_h)/2+60"
    )
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=0x101820:s=1080x1920:d=1",
        "-i",
        str(voice_path),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        "-vf",
        vf,
        str(final),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x101820:s=1080x1920:d=1",
            "-i",
            str(voice_path),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(final),
        ]
        subprocess.run(cmd, check=True)
    print(
        "NOTE: assembled voice + slate (no Blender frames yet). "
        "Add templates/*.blend for Zack-level visuals."
    )
