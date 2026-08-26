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
    # Same 8-cut language as the local body_gentle sneeze film.
    cams = [
        "CAM_HOOK",
        "CAM_PROFILE",
        "CAM_DUST",
        "CAM_MACRO",
        "CAM_BLAST",
        "CAM_CAR",
        "CAM_CLOSE",
        "CAM_LUNGS",
    ]
    if band == "age_01_05":
        base = [120, 168, 144, 168, 144, 144, 144, 168]
        n = 6
    elif band == "age_11_16":
        base = [168, 192, 168, 192, 192, 168, 168, 192]
        n = 8
    else:
        base = [192, 168, 168, 192, 192, 168, 168, 192]
        n = 8
    order = list(range(n))
    rng.shuffle(order[1:-1])
    shots = []
    for i, idx in enumerate(order):
        jitter = rng.randint(-12, 16)
        shots.append(
            {
                "id": i + 1,
                "camera": cams[idx],
                "frames": max(48, base[idx] + jitter),
                "move": rng.choice(["push", "orbit", "slide", "rise", "hold"]),
            }
        )
    return shots


def fit_shots_to_voice(episode: dict, voice_sec: float) -> dict:
    """Grow/shrink shot lengths so camera animation lasts the whole narration."""
    shots = list(episode.get("shots") or [])
    if not shots or voice_sec <= 0:
        return episode
    total = sum(max(1, int(s.get("frames") or 24)) for s in shots)
    target = max(48, int(round(float(voice_sec) * 24.0)))
    if total < 1 or abs(target - total) < 24:
        return episode
    scale = target / float(total)
    for shot in shots:
        shot["frames"] = max(24, int(round(int(shot.get("frames") or 24) * scale)))
    episode["shots"] = shots
    new_total = sum(int(s.get("frames") or 24) for s in shots)
    episode["duration_target_sec"] = round(new_total / 24.0, 1)
    print(
        f"Shot timeline {total} -> {new_total} frames so cameras cover "
        f"{voice_sec:.1f}s of voice (not a short clip stretched in ffmpeg)"
    )
    return episode


def _hook_line(episode: dict) -> str:
    hook = str(episode.get("hook") or (episode.get("narration") or [""])[0]).strip()
    return hook.rstrip(".")


def _topic_words(episode: dict) -> list[str]:
    title = str(episode.get("title") or "")
    skip = {
        "why", "how", "the", "and", "for", "does", "what", "do", "we", "is", "a",
        "an", "to", "of", "in", "on", "our", "your",
    }
    words = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", title)]
    return [w for w in words if w not in skip]


def content_hashtag(episode: dict) -> str:
    parts = [w.title() for w in _topic_words(episode)]
    if not parts:
        return "#KidsScience"
    return "#" + "".join(parts)[:28]


def youtube_hashtags(episode: dict) -> list[str]:
    topic = content_hashtag(episode)
    extras = [f"#{w.title()}" for w in _topic_words(episode)[:3]]
    tags = ["#Shorts", "#KidsScience", topic, "#3DShorts", "#Education"] + extras
    out = []
    seen = set()
    for t in tags:
        key = t.lower()
        if key in seen or len(t) < 2:
            continue
        seen.add(key)
        out.append(t)
    return out[:8]


def youtube_title(episode: dict) -> str:
    """Topic first so the Short matches the film. Always include #Shorts."""
    title = str(episode.get("title") or episode.get("id") or "Kids Science").strip()
    title = re.sub(r"\s+#Shorts\b", "", title, flags=re.I).strip()
    topic = content_hashtag(episode)
    out = f"{title} #Shorts"
    if topic.lower() not in {"#shorts", "#kidsscience"} and len(out) + 1 + len(topic) <= 100:
        out = f"{out} {topic}"
    return out[:100]


def youtube_description(episode: dict) -> str:
    title = str(episode.get("title") or "Kids Science").strip()
    hook = _hook_line(episode)
    lines = [str(x) for x in (episode.get("narration") or []) if str(x).strip()]
    band = episode.get("age_band") or "age_06_10"
    ages = band.replace("age_", "").replace("_", "-")
    hashes = " ".join(youtube_hashtags(episode))
    bullets = "\n".join(f"- {line}" for line in lines[:8])
    return (
        f"{title}\n"
        f"{hook}.\n\n"
        f"This 3D Short is only about this: {title}\n\n"
        f"{bullets}\n\n"
        f"Kid-safe cinematic Blender 3D. English narration. Original kids BGM.\n"
        f"Ages {ages}. Made for Kids. A brand new 3D film tomorrow.\n\n"
        f"{hashes}"
    )


def youtube_tags(episode: dict) -> list[str]:
    words = _topic_words(episode)
    title = str(episode.get("title") or "")
    core = [
        "shorts",
        "kids science",
        "kids education",
        "science shorts",
        "3d animation",
        "blender 3d",
        "made for kids",
        "education",
        str(episode.get("scene") or "science"),
        title.lower()[:30],
    ]
    extra = words[:8] + [f"kids {w}" for w in words[:4]]
    tags = []
    seen = set()
    for t in core + extra:
        key = str(t).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        tags.append(str(t).strip()[:30])
    return tags[:15]


def thumbnail_text(episode: dict) -> str:
    raw = str(episode.get("title") or "KIDS SCIENCE")
    raw = raw.replace("?", "")
    for prefix in (
        "Why Do We ",
        "Why Does ",
        "Why Is ",
        "Why Do ",
        "What Is ",
        "How Does ",
        "How Do ",
    ):
        if raw.lower().startswith(prefix.lower()):
            raw = raw[len(prefix) :]
            break
    words = raw.split()
    if words and words[0].lower() == "the":
        words = words[1:]
    if len(words) > 5:
        words = words[:5]
    return " ".join(words).upper()[:26]


def pack_for_youtube(episode: dict) -> dict:
    """Always stamp title, description, hashtags, tags, thumbnail text to this topic."""
    episode["youtube_title"] = youtube_title(episode)
    episode["description"] = youtube_description(episode)
    episode["tags"] = youtube_tags(episode)
    episode["hashtags"] = youtube_hashtags(episode)
    episode["thumbnail_text"] = thumbnail_text(episode)
    episode["hero_label"] = episode["thumbnail_text"]
    return episode


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
        episode["template"] = "topic_studio"
        episode["shots"] = unique_shots(episode)
    episode["duration_target_sec"] = round(
        sum(int(s.get("frames") or 24) for s in (episode.get("shots") or [])) / 24.0, 1
    )
    episode["world"] = world_look(episode)
    episode["bgm_spec"] = bgm_spec(episode)
    return pack_for_youtube(episode)
