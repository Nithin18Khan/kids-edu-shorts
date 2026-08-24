from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

from pipeline.captions import episode_wants_captions, words_from_narration, write_ass, write_words_json
from pipeline.detect import find_ffmpeg, media_duration_sec


def _voice_profile(episode: dict, root: Path) -> tuple[str, str, str]:
    bands = json.loads((root / "config" / "age_bands.json").read_text(encoding="utf-8"))
    band = bands[episode["age_band"]]
    voice_cfg = band["voice"]
    lang = episode.get("language", "en")
    voice = episode.get("voice") or voice_cfg.get(lang) or voice_cfg.get("en")
    rate = (
        episode.get("voice_rate")
        or (voice_cfg.get("ml_rate") if lang == "ml" else None)
        or voice_cfg.get("rate", "-3%")
    )
    pitch = (
        episode.get("voice_pitch")
        or (voice_cfg.get("ml_pitch") if lang == "ml" else None)
        or voice_cfg.get("pitch", "+0Hz")
    )
    return str(voice), str(rate), str(pitch)


def _pause_ms(episode: dict) -> int:
    if "voice_pause_ms" in episode:
        return max(0, int(episode["voice_pause_ms"]))
    return 0


async def _edge_tts_save(text: str, voice: str, rate: str, pitch: str, dest: Path) -> list[dict]:
    import edge_tts

    dest.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    audio = bytearray()
    words: list[dict] = []
    async for chunk in communicate.stream():
        kind = chunk.get("type")
        if kind == "audio":
            audio.extend(chunk.get("data") or b"")
        elif kind == "WordBoundary":
            words.append(
                {
                    "text": str(chunk.get("text") or "").strip(),
                    "offset": float(chunk.get("offset", 0)) / 10_000_000.0,
                    "duration": float(chunk.get("duration", 0)) / 10_000_000.0,
                }
            )
    dest.write_bytes(bytes(audio))
    return words


def _concat_with_pauses(parts: list[Path], dest: Path, pause_ms: int) -> None:
    ffmpeg = find_ffmpeg()
    if len(parts) == 1:
        dest.write_bytes(parts[0].read_bytes())
        return
    work = dest.parent / "_tts_concat"
    work.mkdir(parents=True, exist_ok=True)
    wavs: list[Path] = []
    for i, part in enumerate(parts):
        wav = work / f"p{i:02d}.wav"
        subprocess.run(
            [ffmpeg, "-y", "-i", str(part), "-ar", "24000", "-ac", "1", str(wav)],
            check=True,
            capture_output=True,
        )
        wavs.append(wav)
    silence = work / "silence.wav"
    gap = max(pause_ms, 80) / 1000.0
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=24000:cl=mono",
            "-t",
            f"{gap:.3f}",
            str(silence),
        ],
        check=True,
        capture_output=True,
    )
    concat_list = work / "list.txt"
    lines: list[str] = []
    for i, wav in enumerate(wavs):
        lines.append(f"file '{wav.resolve().as_posix()}'")
        if i < len(wavs) - 1:
            lines.append(f"file '{silence.resolve().as_posix()}'")
    concat_list.write_text("\n".join(lines) + "\n", encoding="utf-8")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )


def generate_voiceover(episode: dict, out_dir: Path, *, root: Path) -> Path:
    lines = [line.strip() for line in episode["narration"] if line.strip()]
    voice, rate, pitch = _voice_profile(episode, root)
    dest = out_dir / "voice.mp3"
    print(f"TTS voice={voice} rate={rate} pitch={pitch}")
    pause_ms = _pause_ms(episode)
    words: list[dict] = []

    if pause_ms > 0 and len(lines) > 1:
        part_dir = out_dir / "_tts_parts"
        part_dir.mkdir(parents=True, exist_ok=True)
        parts: list[Path] = []
        offset = 0.0
        for i, line in enumerate(lines):
            part = part_dir / f"line_{i:02d}.mp3"
            line_words = asyncio.run(_edge_tts_save(line, voice, rate, pitch, part))
            if not part.exists() or part.stat().st_size == 0:
                raise RuntimeError(f"Voice line failed: {line[:40]}")
            for w in line_words:
                words.append(
                    {
                        "text": w["text"],
                        "offset": w["offset"] + offset,
                        "duration": w["duration"],
                    }
                )
            try:
                offset += media_duration_sec(part) + (pause_ms / 1000.0)
            except Exception:
                offset += 2.0 + (pause_ms / 1000.0)
            parts.append(part)
        _concat_with_pauses(parts, dest, pause_ms)
        print(f"TTS pauses {pause_ms}ms between {len(lines)} lines (clearer for kids)")
    else:
        if str(episode.get("language") or "en") == "ml":
            # Full Malayalam sentences (period), one take — commas make TTS sound un-Malayalam
            text = " ".join(
                (line.rstrip("., ") + ".") for line in lines
            )
        else:
            text = " ".join(lines)
        words = asyncio.run(_edge_tts_save(text, voice, rate, pitch, dest))

    if not dest.exists() or dest.stat().st_size == 0:
        raise RuntimeError(f"Voice generation failed: {dest}")

    if not words:
        try:
            duration = media_duration_sec(dest)
        except Exception:
            duration = float(episode.get("duration_target_sec") or 18)
        words = words_from_narration(episode["narration"], duration)
        print("TTS word timings missing — estimated captions from narration")

    write_words_json(words, out_dir / "captions_words.json")
    if episode_wants_captions(episode):
        ass_path = write_ass(words, out_dir / "captions.ass")
        print(f"Captions:  {ass_path} ({len(words)} words)")
    else:
        stale = out_dir / "captions.ass"
        if stale.exists():
            stale.unlink()
        print("Captions:  off")
    return dest
