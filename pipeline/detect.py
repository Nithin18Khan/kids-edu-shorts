"""Find Blender / ffmpeg on this machine (Windows-friendly)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    winget = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if winget.exists():
        hits = sorted(winget.glob("**/ffmpeg.exe"))
        if hits:
            return str(hits[0])
    raise FileNotFoundError("ffmpeg not found on PATH")


def find_ffprobe() -> str:
    ffmpeg = find_ffmpeg()
    sibling = Path(ffmpeg).with_name("ffprobe.exe" if ffmpeg.lower().endswith(".exe") else "ffprobe")
    if sibling.exists():
        return str(sibling)
    found = shutil.which("ffprobe")
    if found:
        return found
    raise FileNotFoundError("ffprobe not found next to ffmpeg")


def media_duration_sec(path: Path) -> float:
    import subprocess

    probe = find_ffprobe()
    result = subprocess.run(
        [
            probe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def _windows_blender_exes() -> list[Path]:
    roots = [
        Path(r"C:\Program Files\Blender Foundation"),
        Path(r"C:\Program Files (x86)\Blender Foundation"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Blender-4.5.10",
        Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages",
    ]
    found: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        found.extend(root.glob("Blender */blender.exe"))
        found.extend(root.glob("**/blender.exe"))
    # Prefer newest-looking folder names (4.5 before 4.2, etc.)
    uniq = []
    seen = set()
    for path in sorted(found, key=lambda p: p.as_posix().lower(), reverse=True):
        key = str(path.resolve()).lower() if path.exists() else str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(path)
    return uniq


def find_blender() -> str:
    env = os.environ.get("BLENDER_PATH", "").strip()
    if env and Path(env).exists():
        return env
    found = shutil.which("blender")
    if found:
        return found
    explicit = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Blender-4.5.10" / "blender.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Blender-4.2" / "blender.exe",
        Path(r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"),
    ]
    for path in explicit:
        if path.exists():
            return str(path)
    for path in _windows_blender_exes():
        if path.exists():
            return str(path)
    raise FileNotFoundError(
        "Blender not found. Install Blender 4.x (portable zip or "
        "winget install BlenderFoundation.Blender.LTS.4.5) and set BLENDER_PATH, "
        "or add blender.exe to PATH."
    )


def tool_report(root: Path) -> dict:
    report: dict = {"root": str(root)}
    try:
        report["blender"] = find_blender()
        report["blender_ok"] = True
    except FileNotFoundError as exc:
        report["blender"] = str(exc)
        report["blender_ok"] = False
    try:
        report["ffmpeg"] = find_ffmpeg()
        report["ffmpeg_ok"] = True
    except FileNotFoundError as exc:
        report["ffmpeg"] = str(exc)
        report["ffmpeg_ok"] = False
    templates = root / "blender" / "templates"
    blends = sorted(templates.glob("*.blend")) if templates.exists() else []
    report["templates"] = [p.name for p in blends]
    report["body_gentle"] = (templates / "body_gentle.blend").exists()
    return report


def print_tool_report(root: Path) -> int:
    report = tool_report(root)
    print("=== Kids Edu Shorts — environment ===")
    print(f"Blender:   {report['blender']}")
    print(f"ffmpeg:    {report['ffmpeg']}")
    print(f"Templates: {', '.join(report['templates']) or '(none yet)'}")
    print(f"body_gentle.blend: {'yes' if report['body_gentle'] else 'NO — will auto-build when Blender is available'}")
    if report["blender_ok"] and report["ffmpeg_ok"]:
        print("Ready to render.")
        return 0
    print("Not ready for a full Blender Short yet.")
    return 1
