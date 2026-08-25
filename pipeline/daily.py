"""One unique Short per day. Catch up at most one upload. Pre-render the next film."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from pipeline.approved import approved_video
from pipeline.queue import episode_path_for_date, load_manifest, load_state, pending_dates
from pipeline.upload import youtube_auth_available


def growth_config(root: Path) -> dict:
    path = root / "config" / "growth.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def uploaded_on_local_day(state: dict, day: date) -> bool:
    key = day.isoformat()
    for meta in (state.get("uploaded") or {}).values():
        at = str((meta or {}).get("at") or "")
        if at.startswith(key):
            return True
    return False


def video_for_calendar_date(root: Path, day: date) -> Path | None:
    path = episode_path_for_date(root, day)
    episode = json.loads(path.read_text(encoding="utf-8"))
    gold = approved_video(root, episode)
    if gold is not None:
        return gold
    video = root / "output" / episode["id"] / f"{episode['id']}_short.mp4"
    if video.exists() and video.stat().st_size > 20_000:
        return video
    return None


def plan_daily(root: Path, *, do_upload: bool, pre_render: bool) -> dict:
    load_manifest(root)
    st = load_state(root)
    today = date.today()
    notes: list[str] = []
    publish = None
    pending_up = pending_dates(root, need="upload")
    if do_upload:
        if uploaded_on_local_day(st, today):
            notes.append("Already uploaded one Short today. Cap is 1 per day.")
        elif pending_up:
            publish = date.fromisoformat(pending_up[0])
            notes.append(f"Publish slot: {publish.isoformat()} (next unpublished unique film).")
        else:
            notes.append("Year upload queue is complete.")
    else:
        notes.append("Upload is off. Pass --upload after kids OAuth is in credentials/kids/.")

    pending_r = pending_dates(root, need="render")
    render = None
    if pending_r:
        render = date.fromisoformat(pending_r[0])
        notes.append(f"Render slot: {render.isoformat()} (next unique film without pictures yet).")

    pre = None
    if pre_render:
        for raw in pending_r:
            d = date.fromisoformat(raw)
            if (publish is not None and d == publish) or (render is not None and d == render):
                continue
            pre = d
            notes.append(f"Pre-render buffer: {pre.isoformat()} so tomorrow is ready.")
            break
        if pre is None and not pending_r:
            notes.append("No pre-render needed. Render queue is complete.")

    return {
        "today": today.isoformat(),
        "render": render.isoformat() if render else None,
        "publish": publish.isoformat() if publish else None,
        "publish_has_video": bool(publish and video_for_calendar_date(root, publish)),
        "pre_render": pre.isoformat() if pre else None,
        "oauth": youtube_auth_available(root),
        "notes": notes,
        "growth": growth_config(root),
    }


def print_growth_status(root: Path) -> None:
    g = growth_config(root)
    print("=== Revenue path (honest) ===")
    print(f"Ambition:  ${g.get('ambition_usd', 1000000):,}")
    print(g.get("honest") or "")
    print(f"Publish:   {g.get('publish_rule')}")
    print("Ladder:")
    for row in g.get("ladder") or []:
        print(f"  {row.get('step')}. {row.get('name')}")
        print(f"     You:     {row.get('you_do')}")
        print(f"     Factory: {row.get('factory')}")
    note = g.get("ads_math_note")
    if note:
        print(note)
    print(f"Clock:     {datetime.now().isoformat(timespec='seconds')} local")
