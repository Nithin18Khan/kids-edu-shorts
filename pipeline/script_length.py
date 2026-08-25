"""Kid-safe extra spoken beats so a 4-line stub is not a 15-second YouTube Short."""

from __future__ import annotations

MIN_WORDS = {
    "age_01_05": 48,
    "age_06_10": 95,
    "age_11_16": 110,
}

CLOSERS = {
    "age_01_05": (
        "You did great watching.",
        "A new 3D film tomorrow. New colors. New fun.",
    ),
    "age_06_10": (
        "That is the whole idea, in one short 3D film.",
        "Tomorrow a brand new 3D film. Same curious science. Brand new pictures.",
    ),
    "age_11_16": (
        "Hold that model in your head: cause, then effect.",
        "Tomorrow a different 3D film. New scene. New true fact.",
    ),
}


def _word_count(lines: list[str]) -> int:
    return len(" ".join(lines).split())


def ensure_narration_length(episode: dict) -> list[str]:
    lines = [str(x).strip() for x in (episode.get("narration") or []) if str(x).strip()]
    if episode.get("hand_tuned") or episode.get("keep_shots"):
        return lines
    band = str(episode.get("age_band") or "age_06_10")
    need = MIN_WORDS.get(band, 95)
    if _word_count(lines) >= need:
        return lines
    out: list[str] = []
    bridges = [
        "Let me show you that in 3D.",
        "Here is the true part.",
        "Watch this next bit closely.",
        "That is why it feels this way.",
    ]
    for i, line in enumerate(lines):
        out.append(line)
        if i < len(bridges):
            out.append(bridges[i])
    for closer in CLOSERS.get(band, CLOSERS["age_06_10"]):
        out.append(closer)
        if _word_count(out) >= need:
            break
    while _word_count(out) < need:
        out.append("A new cinematic 3D Short tomorrow. Same curious science.")
        if len(out) > 24:
            break
    episode["narration"] = out
    return out
