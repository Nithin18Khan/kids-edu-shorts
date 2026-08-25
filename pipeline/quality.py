"""Refuse to publish a stub that is not the full film."""

from __future__ import annotations

from pathlib import Path

from pipeline.detect import media_duration_sec

# Channel format.duration_sec_target floors, with a little slack.
MIN_SEC = {
    "age_01_05": 18.0,
    "age_06_10": 32.0,
    "age_11_16": 40.0,
}


def min_duration_sec(episode: dict) -> float:
    band = str(episode.get("age_band") or "age_06_10")
    return float(MIN_SEC.get(band, 32.0))


def assert_full_film(episode: dict, video_path: Path) -> float:
    sec = media_duration_sec(video_path)
    need = min_duration_sec(episode)
    if sec < need:
        raise RuntimeError(
            f"Refuse upload: {video_path.name} is {sec:.1f}s. "
            f"Need at least {need:.0f}s for {episode.get('age_band')} "
            f"(local ep_001_short.mp4 is ~59s). This was a calendar stub, not the full film."
        )
    print(f"Duration gate: {sec:.1f}s (min {need:.0f}s) OK")
    return sec
