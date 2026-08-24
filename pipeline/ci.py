"""GitHub Actions / headless budget so one Short can finish inside a runner."""

from __future__ import annotations

import os


def running_on_ci() -> bool:
    return os.environ.get("KIDS_CI") == "1" or os.environ.get("GITHUB_ACTIONS") == "true"


def apply_ci_budget(episode: dict) -> dict:
    """Fewer unique frames on GitHub CPU so the job does not hit the 6-hour cap."""
    if not running_on_ci():
        return episode
    shots = list(episode.get("shots") or [])
    if not shots:
        return episode
    total = sum(max(1, int(s.get("frames") or 24)) for s in shots)
    target = 96  # 4s @ 24fps, then ffmpeg stretches to the voice
    if total > target:
        scale = target / float(total)
        for shot in shots:
            shot["frames"] = max(12, int(int(shot.get("frames") or 24) * scale))
        episode["shots"] = shots
    episode["_ci"] = True
    return episode
