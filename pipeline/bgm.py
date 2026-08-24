"""In-house CC0 kids BGM — soft pentatonic bed under narration (no vocals)."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SR = 44100


def _midi(n: float) -> float:
    return 440.0 * (2.0 ** ((n - 69.0) / 12.0))


def _clip(x: float) -> float:
    return max(-0.98, min(0.98, x))


def _pad_tone(t: float, freq: float, amp: float) -> float:
    # Warm pad: fundamental + quiet 5th harmonic, slow chorus
    wobble = 1.0 + 0.003 * math.sin(2 * math.pi * 0.18 * t)
    a = math.sin(2 * math.pi * freq * wobble * t)
    b = 0.22 * math.sin(2 * math.pi * freq * 1.5 * t + 0.4)
    c = 0.08 * math.sin(2 * math.pi * freq * 2.0 * t)
    return amp * (a + b + c)


def _bell(t: float, freq: float, amp: float, decay: float) -> float:
    if t < 0.0:
        return 0.0
    env = math.exp(-t * decay)
    attack = min(1.0, t / 0.012)
    return amp * attack * env * (
        math.sin(2 * math.pi * freq * t)
        + 0.18 * math.sin(2 * math.pi * freq * 2.01 * t)
    )


def write_curious_kids_bed(dest: Path, seconds: float = 96.0) -> Path:
    """Write a gentle G-major pentatonic loop. Kid-safe, no lyrics, CC0."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    n = int(SR * seconds)

    # I – vi – IV – V in G: G  Em  C  D  (2 bars each at 72 bpm → 6.667s/chord)
    bpm = 72.0
    beat = 60.0 / bpm
    bar = beat * 4.0
    chord_len = bar * 2.0
    chords = (
        (55, 62, 71),  # G3 D4 B4
        (52, 59, 67),  # E3 B3 G4
        (48, 55, 64),  # C3 G3 E4
        (50, 57, 66),  # D3 A3 F#4
    )
    pent = (67, 69, 71, 74, 76, 79, 74, 71)  # G pentatonic walk

    samples_l = []
    samples_r = []
    for i in range(n):
        t = i / SR
        chord = chords[int(t / chord_len) % len(chords)]
        pad = 0.0
        for midi_n in chord:
            pad += _pad_tone(t, _midi(midi_n), 0.07)
        # Slow amplitude breathe so it stays under the voice
        pad *= 0.55 + 0.45 * (0.5 + 0.5 * math.sin(2 * math.pi * t / 11.0))

        # Sparse bells on beats 1 and 3 of each bar
        pos_in_bar = t % bar
        note_i = int(t / beat) % len(pent)
        bell = 0.0
        if pos_in_bar < beat * 0.95:
            bell += _bell(pos_in_bar, _midi(pent[note_i]), 0.16, 3.4)
        third = pos_in_bar - beat * 2.0
        if 0.0 <= third < beat * 0.95:
            bell += _bell(third, _midi(pent[(note_i + 2) % len(pent)]), 0.11, 3.8)

        # Soft noise floor (air / room)
        noise = (((i * 1103515245 + 12345) & 0x7FFF) / 32768.0 - 0.5) * 0.012
        left = _clip(pad + bell + noise)
        right = _clip(pad + 0.92 * bell + noise * 0.8)
        samples_l.append(left)
        samples_r.append(right)

    # Fade edges so looping is clean
    fade = int(SR * 1.4)
    for i in range(fade):
        g = i / fade
        samples_l[i] *= g
        samples_r[i] *= g
        samples_l[-1 - i] *= g
        samples_r[-1 - i] *= g

    with wave.open(str(dest), "w") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        frames = bytearray()
        for l, r in zip(samples_l, samples_r):
            frames += struct.pack("<hh", int(l * 30000), int(r * 30000))
        wav.writeframes(frames)
    print(f"BGM wrote {dest} ({seconds:.0f}s, in-house CC0)")
    return dest


_KEY_ROOT = {"C": 48, "G": 55, "D": 50, "A": 57, "F": 53, "Eb": 51}


def write_cinematic_bed(
    dest: Path,
    *,
    seed: int,
    key: str = "G",
    bpm: float = 76.0,
    mood: str = "wonder",
    seconds: float = 32.0,
) -> Path:
    """Unique in-house CC0 cinematic loop for one episode. Never the shared bed."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    n = int(SR * seconds)
    rng = __import__("random").Random(int(seed) & 0xFFFFFFFF)
    root = _KEY_ROOT.get(key, 55)
    # I vi IV V relative to key
    degrees = (0, 9, 5, 7)
    chords = tuple(tuple(root + d + extra for extra in (0, 7, 16)) for d in degrees)
    pent = (root + 12, root + 14, root + 16, root + 19, root + 21, root + 24, root + 19, root + 16)
    beat = 60.0 / max(48.0, float(bpm))
    bar = beat * 4.0
    chord_len = bar * 2.0
    pad_amp = {"gentle": 0.055, "space": 0.05, "storm": 0.07, "pulse": 0.065}.get(mood, 0.06)
    bell_amp = {"gentle": 0.10, "pulse": 0.18, "storm": 0.14}.get(mood, 0.13)
    swirl = 0.12 + rng.random() * 0.22

    samples_l = []
    samples_r = []
    for i in range(n):
        t = i / SR
        chord = chords[int(t / chord_len) % len(chords)]
        pad = 0.0
        for midi_n in chord:
            pad += _pad_tone(t, _midi(midi_n), pad_amp)
        pad *= 0.5 + 0.5 * (0.5 + 0.5 * math.sin(2 * math.pi * t / (9.0 + swirl * 8)))
        pos_in_bar = t % bar
        note_i = int(t / beat) % len(pent)
        bell = 0.0
        if pos_in_bar < beat * 0.9:
            bell += _bell(pos_in_bar, _midi(pent[note_i]), bell_amp, 3.1 + swirl)
        third = pos_in_bar - beat * 2.0
        if 0.0 <= third < beat * 0.9:
            bell += _bell(third, _midi(pent[(note_i + 3) % len(pent)]), bell_amp * 0.7, 3.6)
        if mood == "pulse" and pos_in_bar < 0.04:
            bell += _bell(pos_in_bar, _midi(root + 24), 0.08, 8.0)
        noise = (((i * 1103515245 + (seed & 0xFFFF) + 12345) & 0x7FFF) / 32768.0 - 0.5) * 0.01
        width = 0.85 + 0.12 * math.sin(2 * math.pi * t * swirl)
        left = _clip(pad + bell + noise)
        right = _clip(pad * width + 0.9 * bell + noise * 0.75)
        samples_l.append(left)
        samples_r.append(right)

    fade = int(SR * 0.9)
    for i in range(fade):
        g = i / fade
        samples_l[i] *= g
        samples_r[i] *= g
        samples_l[-1 - i] *= g
        samples_r[-1 - i] *= g

    with wave.open(str(dest), "w") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        frames = bytearray()
        for l, r in zip(samples_l, samples_r):
            frames += struct.pack("<hh", int(l * 30000), int(r * 30000))
        wav.writeframes(frames)
    print(f"BGM wrote unique {dest.name} ({mood} {key} {bpm:.0f}bpm, CC0)")
    return dest


def ensure_bgm(root: Path, episode: dict, out_dir: Path | None = None) -> Path | None:
    flag = episode.get("bgm", True)
    if flag is False:
        return None
    if isinstance(flag, str) and flag.strip():
        path = Path(flag)
        if not path.is_absolute():
            path = root / path
        return path if path.exists() else None
    spec = episode.get("bgm_spec") or {}
    dest_dir = Path(out_dir) if out_dir is not None else (root / "output" / str(episode.get("id") or "bgm"))
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "bgm.wav"
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    write_cinematic_bed(
        dest,
        seed=int(spec.get("seed") or episode.get("seed") or 1),
        key=str(spec.get("key") or "G"),
        bpm=float(spec.get("bpm") or 76),
        mood=str(spec.get("mood") or "wonder"),
    )
    return dest
