"""GitHub Actions helpers. Pictures use the same local Blender grade (no cheap pass)."""

from __future__ import annotations

import os


def running_on_ci() -> bool:
    return os.environ.get("KIDS_CI") == "1" or os.environ.get("GITHUB_ACTIONS") == "true"


def apply_ci_budget(episode: dict) -> dict:
    """Do not downgrade pictures. Same 1080x1920 / 24fps / Eevee as local.

    GitHub used to shrink shots to ~96 frames (slow-mo) or sample 540p stills.
    That is a different film. Automation keeps the real timeline; the workflow
    splits shots across jobs so the 6-hour cap still fits.
    """
    if running_on_ci():
        episode["_ci"] = True
        episode["_ci_frame_step"] = 1
        episode["_ci_resolution"] = [1080, 1920]
        print("CI pictures: same local Blender grade (Eevee, 1080x1920, 24fps, every frame)")
    return episode
