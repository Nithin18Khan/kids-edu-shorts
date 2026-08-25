"""Approved full films. GitHub must never replace these with a 15s calendar stub."""

from __future__ import annotations

import shutil
from pathlib import Path

# Local gold Shorts the factory is allowed to publish as-is.
BY_TITLE = {
    "Why Do We Sneeze?": Path("approved") / "ep_001_why_we_sneeze.mp4",
}

HAND_TUNED_JSON = {
    "Why Do We Sneeze?": Path("scripts") / "episodes" / "age_06_10" / "ep_001_why_we_sneeze.json",
    "Why Is the Sky Blue?": Path("scripts") / "episodes" / "age_06_10" / "ep_002_why_sky_blue.json",
    "How Does a Circuit Work?": Path("scripts") / "episodes" / "age_11_16" / "ep_s01_circuit.json",
}


def approved_video(root: Path, episode: dict) -> Path | None:
    title = str(episode.get("title") or "")
    rel = BY_TITLE.get(title)
    if rel:
        path = root / rel
        if path.exists() and path.stat().st_size > 100_000:
            return path
    if title == "Why Do We Sneeze?":
        gold = root / "output" / "ep_001" / "ep_001_short.mp4"
        if gold.exists() and gold.stat().st_size > 100_000:
            return gold
    return None


def install_approved(root: Path, episode: dict, out_dir: Path) -> Path | None:
    src = approved_video(root, episode)
    if src is None:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{episode['id']}_short.mp4"
    shutil.copy2(src, dest)
    for name in ("thumbnail.jpg", "ep_001_thumb.jpg"):
        thumb = src.parent / name
        if thumb.exists():
            shutil.copy2(thumb, out_dir / "thumbnail.jpg")
            break
    local_thumb = root / "output" / "ep_001" / "thumbnail.jpg"
    if not (out_dir / "thumbnail.jpg").exists() and local_thumb.exists():
        shutil.copy2(local_thumb, out_dir / "thumbnail.jpg")
    print(f"Using approved full film ({src.name}) — not the 15s calendar stub")
    return dest


def overlay_hand_tuned(root: Path, episode: dict) -> dict:
    rel = HAND_TUNED_JSON.get(str(episode.get("title") or ""))
    if rel is None:
        return episode
    path = root / rel
    if not path.exists():
        return episode
    import json

    gold = json.loads(path.read_text(encoding="utf-8"))
    episode["template"] = gold.get("template") or episode.get("template")
    episode["narration"] = list(gold.get("narration") or episode.get("narration") or [])
    episode["shots"] = list(gold.get("shots") or episode.get("shots") or [])
    episode["hook"] = gold.get("hook") or episode.get("hook")
    episode["accent_color"] = gold.get("accent_color") or episode.get("accent_color")
    episode["models"] = gold.get("models") or episode.get("models") or []
    episode["keep_shots"] = True
    episode["hand_tuned"] = True
    return episode
