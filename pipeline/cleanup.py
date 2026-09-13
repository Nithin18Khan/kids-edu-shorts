"""Delete heavy local files after a Short is live on YouTube."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from pipeline.approved import BY_TITLE, HAND_TUNED_JSON
from pipeline.queue import load_state


def _episode_ids(root: Path, episode: dict) -> set[str]:
    ids: set[str] = set()
    eid = str(episode.get("id") or "").strip()
    if eid:
        ids.add(eid)
    title = str(episode.get("title") or "")
    rel = HAND_TUNED_JSON.get(title)
    if rel:
        path = root / rel
        if path.exists():
            try:
                gold = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                gold = {}
            hid = str(gold.get("id") or "").strip()
            if hid:
                ids.add(hid)
    return ids


def _unlink(path: Path, removed: list[str]) -> None:
    if not path.exists() or not path.is_file():
        return
    path.unlink()
    removed.append(str(path).replace("\\", "/"))


def _rmtree(path: Path, removed: list[str]) -> None:
    if not path.exists() or not path.is_dir():
        return
    shutil.rmtree(path, ignore_errors=True)
    removed.append(str(path).replace("\\", "/"))


def cleanup_after_upload(root: Path, episode: dict) -> list[str]:
    """Remove frames, working folder, and approved copy once YouTube has the film.

    Does not delete scripts, Blender templates, or credentials.
    """
    removed: list[str] = []
    ids = _episode_ids(root, episode)
    for eid in ids:
        _rmtree(root / "output" / eid, removed)
        _unlink(root / "approved" / f"{eid}_short.mp4", removed)
        _unlink(root / "approved" / f"{eid}_thumb.jpg", removed)
        _unlink(root / "approved" / f"{eid}.mp4", removed)
    title = str(episode.get("title") or "")
    rel = BY_TITLE.get(title)
    if rel:
        gold = root / rel
        _unlink(gold, removed)
        _unlink(gold.with_name(gold.stem + "_thumb.jpg"), removed)
        _unlink(gold.with_suffix(".jpg"), removed)
    if removed:
        print("Deleted after YouTube upload:")
        for item in removed:
            print(f"  - {item}")
    return removed


def cleanup_uploaded_local(root: Path) -> list[str]:
    """On this PC: wipe output folders for films already live on YouTube."""
    removed: list[str] = []
    st = load_state(root)
    for meta in (st.get("uploaded") or {}).values():
        eid = str((meta or {}).get("id") or "").strip()
        if not eid:
            continue
        _rmtree(root / "output" / eid, removed)
    if removed:
        print("Cleared local working folders for uploaded Shorts:")
        for item in removed:
            print(f"  - {item}")
    return removed
