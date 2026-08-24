"""Render/upload queue for the 365-day English calendar."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


STATE_NAME = "factory_state.json"


def state_path(root: Path) -> Path:
    data = root / "data" / STATE_NAME
    data.parent.mkdir(parents=True, exist_ok=True)
    return data


def load_state(root: Path) -> dict:
    path = state_path(root)
    if not path.exists():
        return {"rendered": {}, "uploaded": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(root: Path, state: dict) -> None:
    state_path(root).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def load_manifest(root: Path) -> dict:
    path = root / "scripts" / "calendar" / "manifest.json"
    if not path.exists():
        raise FileNotFoundError("No calendar yet. Run: python main.py --plan-year")
    return json.loads(path.read_text(encoding="utf-8"))


def episode_path_for_date(root: Path, day: date) -> Path:
    man = load_manifest(root)
    key = day.isoformat()
    for item in man.get("episodes") or []:
        if item.get("date") == key:
            return root / item["file"]
    raise FileNotFoundError(f"No episode scheduled for {key}")


def pending_dates(root: Path, *, need: str = "render") -> list[str]:
    man = load_manifest(root)
    st = load_state(root)
    done = st.get("uploaded" if need == "upload" else "rendered") or {}
    out = []
    for item in man.get("episodes") or []:
        d = item["date"]
        if d not in done:
            out.append(d)
    return out
