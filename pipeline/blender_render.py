from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from pipeline.ci import apply_ci_budget
from pipeline.detect import find_blender


def _builder_for(template_name: str, root: Path) -> Path | None:
    script = root / "blender" / "scripts" / f"build_{template_name}_template.py"
    return script if script.exists() else None


def ensure_template(template_name: str, blend: Path, *, root: Path, blender: str) -> bool:
    builder = _builder_for(template_name, root)
    needs_build = False
    if not blend.exists():
        needs_build = builder is not None
    elif builder is not None and builder.stat().st_mtime > blend.stat().st_mtime:
        print(f"Template script newer than {blend.name} — rebuilding")
        needs_build = True
    if needs_build:
        if builder is None:
            return False
        print(f"Building template {template_name} via {builder.name}")
        subprocess.run(
            [blender, "--background", "--python", str(builder)],
            check=True,
            cwd=str(root),
        )
        return blend.exists()
    return blend.exists()


def _uses_topic_studio(episode: dict) -> bool:
    return str(episode.get("template") or "") == "topic_studio"


def _run_blender(cmd: list[str], *, root: Path) -> None:
    if os.environ.get("KIDS_CI") == "1" or os.environ.get("GITHUB_ACTIONS") == "true":
        xvfb = shutil.which("xvfb-run")
        if xvfb:
            cmd = [xvfb, "-a", *cmd]
        os.environ.setdefault("KIDS_CI", "1")
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(root))


def render_blender_episode(episode: dict, out_dir: Path, *, root: Path) -> Path:
    """Launch Blender in background mode to render this episode."""
    episode = apply_ci_budget(dict(episode))
    template_name = episode["template"]
    blend = root / "blender" / "templates" / f"{template_name}.blend"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for stale in frames_dir.glob("frame_*.png"):
        stale.unlink()

    job_path = out_dir / "blender_job.json"
    job = {
        "episode": episode,
        "root": str(root),
        "frames_dir": str(frames_dir),
        "blend_file": str(blend),
    }
    job_path.write_text(json.dumps(job, indent=2), encoding="utf-8")

    try:
        blender = find_blender()
    except FileNotFoundError as exc:
        note = frames_dir / "MISSING_BLENDER.txt"
        note.write_text(
            f"{exc}\n\nInstall Blender 4.x LTS, then re-run:\n"
            "  python main.py --check\n"
            "  python main.py --episode scripts/episodes/age_06_10/ep_001_why_we_sneeze.json\n",
            encoding="utf-8",
        )
        print(f"WARNING: {exc}")
        return frames_dir

    if _uses_topic_studio(episode):
        build_py = root / "blender" / "scripts" / "build_topic_scene.py"
        _run_blender(
            [blender, "--background", "--python", str(build_py), "--", str(job_path)],
            root=root,
        )
        return frames_dir

    if not ensure_template(template_name, blend, root=root, blender=blender):
        readme = frames_dir / "MISSING_TEMPLATE.txt"
        readme.write_text(
            f"Missing template: {blend}\n\n"
            "Quality bar = Zack D. Films. Create this .blend with kid-safe lighting,\n"
            "CAM_HOOK / CAM_EXPLAIN / CAM_CLOSE, then re-run.\n"
            "See docs/TEMPLATES.md\n",
            encoding="utf-8",
        )
        print(f"WARNING: template missing → {blend}")
        print("Wrote placeholder note. Pipeline continues so voice/assemble can be tested.")
        return frames_dir

    render_py = root / "blender" / "scripts" / "render_episode.py"
    _run_blender(
        [blender, "--background", str(blend), "--python", str(render_py), "--", str(job_path)],
        root=root,
    )
    return frames_dir
