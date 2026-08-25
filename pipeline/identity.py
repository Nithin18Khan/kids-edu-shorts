"""Per-episode cinematic identity. Nothing is shared across days."""

from __future__ import annotations

import hashlib
import random
import re

from pipeline.script_length import ensure_narration_length


WORLDS = (
    ("teal_night", (0.04, 0.08, 0.10), (0.12, 0.28, 0.32)),
    ("indigo", (0.035, 0.04, 0.12), (0.10, 0.10, 0.30)),
    ("warm_dusk", (0.10, 0.045, 0.03), (0.30, 0.14, 0.07)),
    ("forest", (0.035, 0.08, 0.045), (0.10, 0.24, 0.12)),
    ("studio_blue", (0.04, 0.06, 0.11), (0.08, 0.16, 0.30)),
    ("amber", (0.08, 0.055, 0.025), (0.34, 0.22, 0.07)),
    ("ice", (0.05, 0.08, 0.11), (0.16, 0.28, 0.34)),
    ("magenta_night", (0.08, 0.03, 0.07), (0.26, 0.08, 0.22)),
)

MOOD_BPM = {
    "gentle": 64,
    "wonder": 76,
    "warm": 80,
    "storm": 88,
    "pulse": 96,
    "space": 70,
}

LAYOUTS = ("center", "left_hero", "right_hero", "high_hero", "low_hero", "wide")


def episode_seed(episode: dict) -> int:
    if episode.get("seed") is not None:
        return int(episode["seed"])
    raw = f"{episode.get('id')}|{episode.get('date')}|{episode.get('title')}|{episode.get('scene')}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def rng_for(episode: dict) -> random.Random:
    return random.Random(episode_seed(episode))


def mood_for(episode: dict) -> str:
    band = episode.get("age_band") or ""
    scene = (episode.get("scene") or "").lower()
    if band == "age_01_05":
        return "gentle"
    if scene in {"sky", "star", "moon", "rocket", "sun", "earth"}:
        return "space"
    if scene in {"rain", "cloud", "snow", "wave", "wind", "thunder"}:
        return "storm"
    if scene in {"circuit", "lock", "clock", "magnet"}:
        return "pulse"
    if scene in {"heart", "animal", "cat", "bird", "whale", "frog", "bee"}:
        return "warm"
    return "wonder"


def unique_shots(episode: dict) -> list[dict]:
    rng = rng_for(episode)
    band = episode.get("age_band") or "age_06_10"
    if band == "age_01_05":
        cams = ["CAM_HOOK", "CAM_EXPLAIN", "CAM_CLOSE"]
        base = [144, 288, 216]
    elif band == "age_11_16":
        cams = ["CAM_HOOK", "CAM_EXPLAIN", "CAM_MACRO", "CAM_CLOSE"]
        base = [192, 384, 312, 264]
    else:
        cams = ["CAM_HOOK", "CAM_EXPLAIN", "CAM_MACRO", "CAM_CLOSE"]
        base = [192, 360, 288, 240]
    if len(cams) > 2 and rng.random() < 0.45:
        cams[1], cams[2] = cams[2], cams[1]
        base[1], base[2] = base[2], base[1]
    shots = []
    for i, (cam, frames) in enumerate(zip(cams, base)):
        jitter = rng.randint(-18, 22)
        shots.append(
            {
                "id": i + 1,
                "camera": cam,
                "frames": max(48, frames + jitter),
                "move": rng.choice(["push", "orbit", "slide", "rise", "hold"]),
            }
        )
    return shots


def _hook_line(episode: dict) -> str:
    hook = str(episode.get("hook") or (episode.get("narration") or [""])[0]).strip()
    return hook.rstrip(".")


def youtube_title(episode: dict) -> str:
    title = str(episode.get("title") or episode.get("id") or "Kids Science")
    hook = _hook_line(episode)
    short_hook = hook if len(hook) <= 58 else hook[:55].rsplit(" ", 1)[0]
    rng = rng_for(episode)
    variants = [
        f"{title} #Shorts",
        f"{short_hook} #Shorts",
        f"{title} — 3D Kids Science",
        f"Today: {title}",
        f"{title} | Cinematic 3D Short",
        f"{short_hook} | {title.split('?')[0][:28]}",
    ]
    chosen = variants[rng.randrange(len(variants))]
    if "short" not in chosen.lower():
        chosen = f"{chosen} #Shorts"
    return chosen[:100]


def youtube_description(episode: dict) -> str:
    rng = rng_for(episode)
    title = episode.get("title") or "Kids Science"
    hook = _hook_line(episode)
    lines = [str(x) for x in (episode.get("narration") or []) if str(x).strip()]
    band = episode.get("age_band") or "age_06_10"
    ages = band.replace("age_", "").replace("_", "-")
    scene = episode.get("scene") or "studio"
    closers = [
        "A new cinematic 3D Short tomorrow. Same curious science. Brand new pictures.",
        "Come back tomorrow for a different 3D world and a new true fact.",
        "This Short is one original Blender film. Tomorrow's film is a different one.",
        "Kid-safe 3D. English. Made for Kids. A fresh scene every day.",
    ]
    openers = [
        f"{hook}.",
        f"This 3D Short is only about this: {title}",
        f"Watch this original Blender scene: {title}",
    ]
    bullets = "\n".join(f"- {line}" for line in lines[:8])
    return (
        f"{openers[rng.randrange(len(openers))]}\n\n"
        f"{bullets}\n\n"
        f"Cinematic Blender 3D. Original English narration. Original kids BGM.\n"
        f"Scene: {scene}. Ages {ages}. Made for Kids.\n\n"
        f"{closers[rng.randrange(len(closers))]}"
    )


def youtube_tags(episode: dict) -> list[str]:
    title = str(episode.get("title") or "")
    words = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", title)]
    core = [
        "kids science",
        "education",
        "blender 3d",
        "cinematic shorts",
        "made for kids",
        str(episode.get("scene") or "science"),
        str(episode.get("age_band") or "kids"),
    ]
    extra = [w for w in words if w not in {"why", "how", "the", "and", "for", "does", "what"}]
    tags = []
    seen = set()
    for t in core + extra[:8] + [f"kids {w}" for w in extra[:4]]:
        key = t.lower()
        if key in seen or not t.strip():
            continue
        seen.add(key)
        tags.append(t[:30])
    return tags[:15]


def thumbnail_text(episode: dict) -> str:
    raw = str(episode.get("title") or "WOW")
    raw = raw.replace("?", "").replace("Why Do We ", "").replace("Why Does ", "")
    raw = raw.replace("Why Is ", "").replace("Why Do ", "").replace("What Is ", "")
    raw = raw.replace("How Does ", "").replace("How Do ", "")
    words = raw.split()
    if len(words) > 4:
        words = words[:4]
    return " ".join(words).upper()[:22]


def world_look(episode: dict) -> dict:
    rng = rng_for(episode)
    name, bg, floor = WORLDS[rng.randrange(len(WORLDS))]
    layout = LAYOUTS[rng.randrange(len(LAYOUTS))]
    return {
        "preset": name,
        "bg": list(bg),
        "floor": list(floor),
        "layout": layout,
        "fog": round(0.04 + rng.random() * 0.08, 3),
        "bloom": round(0.03 + rng.random() * 0.06, 3),
        "hero_scale": round(0.82 + rng.random() * 0.4, 3),
        "orbit": round(8.0 + rng.random() * 18.0, 2),
        "push": round(0.12 + rng.random() * 0.35, 3),
        "particles": 5 + rng.randrange(8),
        "cam_jitter": [
            round(rng.uniform(-0.45, 0.45), 3),
            round(rng.uniform(-0.35, 0.2), 3),
            round(rng.uniform(-0.22, 0.28), 3),
        ],
    }


def bgm_spec(episode: dict) -> dict:
    mood = mood_for(episode)
    rng = rng_for(episode)
    keys = ("C", "G", "D", "A", "F", "Eb")
    return {
        "mood": mood,
        "key": keys[rng.randrange(len(keys))],
        "bpm": MOOD_BPM[mood] + rng.choice((-4, -2, 0, 2, 4)),
        "seed": episode_seed(episode),
    }


def decorate_episode(episode: dict) -> dict:
    """Stamp uniqueness onto an episode. Never reuse video, frames, or packaging."""
    episode["seed"] = episode_seed(episode)
    episode["never_reuse"] = True
    episode["reuse_frames_from"] = None
    episode["language"] = "en"
    episode["captions"] = True
    episode["bgm"] = True
    episode["made_for_kids"] = True
    episode["narration"] = ensure_narration_length(episode)
    if not (episode.get("keep_shots") or episode.get("hand_tuned")):
        episode["shots"] = unique_shots(episode)
    episode["duration_target_sec"] = round(
        sum(int(s.get("frames") or 24) for s in (episode.get("shots") or [])) / 24.0, 1
    )
    episode["world"] = world_look(episode)
    episode["bgm_spec"] = bgm_spec(episode)
    episode["youtube_title"] = youtube_title(episode)
    episode["description"] = youtube_description(episode)
    episode["tags"] = youtube_tags(episode)
    episode["thumbnail_text"] = thumbnail_text(episode)
    episode["hero_label"] = thumbnail_text(episode)
    return episode
