"""Zack D. Films–style captions: big Arial Black, yellow word highlight, 9:16 safe area."""

from __future__ import annotations

import json
from pathlib import Path


HIGHLIGHT = r"{\c&H0000D4FF&}"  # yellow (ASS BGR)


def episode_wants_captions(episode: dict) -> bool:
    if "captions" in episode:
        return bool(episode["captions"])
    return str(episode.get("language") or "en").lower() != "ml"
WHITE = r"{\c&H00FFFFFF&}"
WORDS_PER_LINE = 5


def ass_time(t: float) -> str:
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    cs = int(round((t - int(t)) * 100))
    if cs >= 100:
        s += cs // 100
        cs = cs % 100
        if s >= 60:
            m += s // 60
            s = s % 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _esc(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("{", "(")
        .replace("}", ")")
        .replace("\n", " ")
    )


def _chunk_words(words: list[dict], size: int = WORDS_PER_LINE) -> list[list[dict]]:
    chunks: list[list[dict]] = []
    buf: list[dict] = []
    for w in words:
        token = (w.get("text") or "").strip()
        if not token:
            continue
        buf.append(w)
        end_punct = token[-1] in ".?!,"
        if len(buf) >= size or end_punct:
            chunks.append(buf)
            buf = []
    if buf:
        chunks.append(buf)
    return chunks


def _line_with_highlight(chunk: list[dict], active_idx: int) -> str:
    parts = []
    for i, w in enumerate(chunk):
        token = _esc((w.get("text") or "").strip())
        if i == active_idx:
            parts.append(f"{HIGHLIGHT}{token}{WHITE}")
        else:
            parts.append(token)
    return " ".join(parts)


def words_from_narration(lines: list[str], duration: float) -> list[dict]:
    """Fallback if Edge-TTS word timings are missing."""
    tokens: list[str] = []
    for line in lines:
        for t in line.replace("—", " ").replace("…", " ").split():
            if t.strip():
                tokens.append(t.strip())
    if not tokens:
        return []
    weights = [max(len(t), 2) for t in tokens]
    total = sum(weights)
    t = 0.0
    out = []
    for tok, w in zip(tokens, weights):
        dur = duration * (w / total)
        out.append({"text": tok, "offset": t, "duration": dur})
        t += dur
    return out


def write_ass(words: list[dict], dest: Path, *, play_res=(1080, 1920)) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    chunks = _chunk_words(words)
    events = []
    for chunk in chunks:
        if not chunk:
            continue
        for i, w in enumerate(chunk):
            start = float(w["offset"])
            if i + 1 < len(chunk):
                end = float(chunk[i + 1]["offset"])
            else:
                end = float(w["offset"]) + max(float(w.get("duration", 0.18)), 0.12)
            if end <= start:
                end = start + 0.12
            text = _line_with_highlight(chunk, i)
            events.append(
                f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Zack,,0,0,0,,{text}"
            )

    header = f"""[Script Info]
Title: Kids Edu Shorts captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {play_res[0]}
PlayResY: {play_res[1]}
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Zack,Arial Black,76,&H00FFFFFF,&H0000D4FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,5.5,1.5,2,48,48,268,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dest.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return dest


def write_words_json(words: list[dict], dest: Path) -> None:
    dest.write_text(json.dumps(words, indent=2), encoding="utf-8")
