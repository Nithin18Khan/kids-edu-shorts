"""Build a 365-day English-only episode calendar. Unique script per day."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from pipeline.approved import overlay_hand_tuned
from pipeline.year_topics_kids import pack_kids
from pipeline.year_topics_pre import PRE_SCHOOL, _pack
from pipeline.year_topics_students import pack_students
from pipeline.identity import decorate_episode

START = date(2026, 8, 24)
DAYS = 365

TEMPLATE_BY_BAND = {
    "age_01_05": "topic_studio",
    "age_06_10": "topic_studio",
    "age_11_16": "topic_studio",
}


def band_for(day: date) -> str:
    wd = day.weekday()  # Mon=0
    if wd in (5, 6):
        return "age_01_05"
    if wd == 2:
        return "age_11_16"
    return "age_06_10"


def _queues() -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    pre = [_pack(r) for r in PRE_SCHOOL]
    kids = pack_kids()
    stu = pack_students()
    live = {"age_01_05": list(pre), "age_06_10": list(kids), "age_11_16": list(stu)}
    backup = {"age_01_05": pre, "age_06_10": kids, "age_11_16": stu}
    return live, backup


def _take(queue: list[dict], backup: list[dict], used: set[str]) -> dict:
    for i, item in enumerate(queue):
        if item["title"] not in used:
            used.add(item["title"])
            return queue.pop(i)
    if not backup:
        raise RuntimeError("Topic bank is empty")
    item = dict(backup[len(used) % len(backup)])
    n = 2
    title = item["title"]
    while title in used:
        title = f"{item['title']} ({n})"
        n += 1
    item["title"] = title
    item["hook"] = item["narration"][0]
    used.add(title)
    return item


def build_episode(day: date, topic: dict, band: str, *, root: Path) -> dict:
    ep_id = f"d{day.isoformat().replace('-', '')}"
    lines = topic["narration"]
    episode = {
        "id": ep_id,
        "date": day.isoformat(),
        "title": topic["title"],
        "age_band": band,
        "language": "en",
        "captions": True,
        "bgm": True,
        "made_for_kids": True,
        "never_reuse": True,
        "template": TEMPLATE_BY_BAND[band],
        "scene": topic["scene"],
        "hook": topic.get("hook") or lines[0],
        "accent_color": topic["accent"],
        "models": [],
        "narration": lines,
        "tags": [],
    }
    episode = overlay_hand_tuned(root, episode)
    return decorate_episode(episode)


def generate_year(*, root: Path, start: date = START, days: int = DAYS) -> list[dict]:
    live, backup = _queues()
    used: set[str] = set()
    episodes = []
    for i in range(days):
        day = start + timedelta(days=i)
        band = band_for(day)
        topic = _take(live[band], backup[band], used)
        episodes.append(build_episode(day, topic, band, root=root))
    return episodes


def write_calendar(root: Path, *, start: date = START, days: int = DAYS) -> Path:
    dest_dir = root / "scripts" / "calendar"
    dest_dir.mkdir(parents=True, exist_ok=True)
    episodes = generate_year(root=root, start=start, days=days)
    index = []
    for ep in episodes:
        path = dest_dir / f"{ep['date']}_{ep['id']}.json"
        path.write_text(json.dumps(ep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        index.append(
            {
                "date": ep["date"],
                "id": ep["id"],
                "title": ep["title"],
                "age_band": ep["age_band"],
                "scene": ep["scene"],
                "youtube_title": ep.get("youtube_title"),
                "world": (ep.get("world") or {}).get("preset"),
                "seed": ep.get("seed"),
                "file": str(path.relative_to(root)).replace("\\", "/"),
            }
        )
    manifest = dest_dir / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "language": "en",
                "start": start.isoformat(),
                "days": days,
                "count": len(index),
                "note": "English only. Unique cinematic Blender + unique title/description/thumbnail/BGM per day. Never reuse video or frames.",
                "episodes": index,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def expand_existing_calendar(root: Path) -> dict:
    """Rewrite every year JSON to a full-length script. Keep date, id, seed, title."""
    dest = root / "scripts" / "calendar"
    counts = {"files": 0, "words_min": 10**9, "words_max": 0, "words_sum": 0, "short": []}
    for path in sorted(dest.glob("*.json")):
        if path.name == "manifest.json":
            continue
        episode = json.loads(path.read_text(encoding="utf-8"))
        episode = overlay_hand_tuned(root, episode)
        episode = decorate_episode(episode)
        path.write_text(json.dumps(episode, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        n = len(" ".join(episode.get("narration") or []).split())
        counts["files"] += 1
        counts["words_min"] = min(counts["words_min"], n)
        counts["words_max"] = max(counts["words_max"], n)
        counts["words_sum"] += n
        band = episode.get("age_band") or "age_06_10"
        from pipeline.script_length import MIN_WORDS

        if n < MIN_WORDS.get(band, 125):
            counts["short"].append(f"{episode.get('id')} {n}w")
    if counts["files"]:
        counts["words_avg"] = round(counts["words_sum"] / counts["files"], 1)
    return counts
