"""Turn 4-line calendar stubs into full-length spoken films."""

from __future__ import annotations

MIN_WORDS = {
    "age_01_05": 70,
    "age_06_10": 125,
    "age_11_16": 135,
}

MIN_LINES = {
    "age_01_05": 8,
    "age_06_10": 12,
    "age_11_16": 12,
}


def _word_count(lines: list[str]) -> int:
    return len(" ".join(lines).split())


def _plain_title(title: str) -> str:
    return str(title or "").replace("?", "").strip() or "today's idea"


def expand_full_script(episode: dict) -> list[str]:
    """Build an ep_001-length narration from the topic facts. Unique per title/scene."""
    band = str(episode.get("age_band") or "age_06_10")
    need_w = MIN_WORDS.get(band, 125)
    need_n = MIN_LINES.get(band, 12)
    facts = [str(x).strip() for x in (episode.get("narration") or []) if str(x).strip()]
    if not facts:
        facts = [str(episode.get("title") or "Today's 3D film.")]
    if _word_count(facts) >= need_w and len(facts) >= need_n:
        episode["full_script"] = True
        return facts

    title = _plain_title(str(episode.get("title") or ""))
    scene = str(episode.get("scene") or "studio")
    pads = [
        f"Stay to the end. The last shot is the takeaway for {title.lower()}.",
        "If a grown-up is with you, pause and tell them the cause in one sentence.",
        "Kid-safe 3D. English. Made for Kids.",
        "A new cinematic 3D Short every day. Brand new pictures every day.",
    ]

    if len(facts) >= 8:
        out = list(facts)
        for pad in pads:
            if _word_count(out) >= need_w:
                break
            if pad not in out:
                out.append(pad)
        episode["narration"] = out
        episode["full_script"] = True
        return out

    while len(facts) < 4:
        facts.append(facts[-1])
    f0, f1, f2, f3 = facts[0], facts[1], facts[2], facts[3]
    extra = facts[4:]

    if band == "age_01_05":
        out = [
            f0,
            "Look closely. This is 3D.",
            f1,
            "See it. Say it.",
            f2,
            f3,
            "You did great watching.",
            "Look again. You found it.",
            "A new 3D film tomorrow. New colors. New fun.",
        ]
    elif band == "age_11_16":
        out = [
            f0,
            f"Today's question: {episode.get('title') or title}.",
            f1,
            "Hold the cause in your head, then the effect.",
            f2,
            "This is the part most people skip. Do not skip it.",
            f3,
            f"If you can say why {title.lower()} works, you understood the film.",
            "No gore. Just the model. School-safe.",
            f"The pictures today are a new {scene} world. Not yesterday's film.",
            "Tomorrow a different 3D film. New scene. New true fact.",
            "Stay curious. The next film is a different true fact.",
        ]
    else:
        out = [
            f0,
            f"This 3D Short is only about this: {title}.",
            f1,
            "Let me show you that in 3D.",
            f2,
            "Watch this next bit closely. This is why it happens.",
            f3,
            "So the idea is simple: cause, then effect.",
            f"Remember: {f0.rstrip('.')}.",
            f"The pictures today are a new {scene} world. Not yesterday's film.",
            "That is the whole idea, in one short 3D film.",
            "Tomorrow a brand new 3D film. Same curious science. Brand new pictures.",
            "Stay curious. The next film is a different true fact.",
        ]

    insert_at = max(len(out) - 2, 1)
    for line in extra:
        out.insert(insert_at, line)
        insert_at += 1

    pads = [
        f"Stay to the end. The last shot is the takeaway for {title.lower()}.",
        "If a grown-up is with you, pause and tell them the cause in one sentence.",
        "Kid-safe 3D. English. Made for Kids.",
        "A new cinematic 3D Short every day. Brand new pictures every day.",
    ]
    for pad in pads:
        if _word_count(out) >= need_w and len(out) >= need_n:
            break
        out.insert(-1, pad)

    episode["narration"] = out
    episode["full_script"] = True
    return out


def ensure_narration_length(episode: dict) -> list[str]:
    return expand_full_script(episode)
