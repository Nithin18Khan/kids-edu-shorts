"""
Kids Edu Shorts — Blender 3D factory (Zack D. Films quality bar).
Separate from the gaming YouTube channel. English only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pipeline.assemble import assemble_short
from pipeline.blender_render import render_blender_episode
from pipeline.daily import plan_daily, print_growth_status
from pipeline.detect import find_blender, print_tool_report
from pipeline.queue import (
    episode_path_for_date,
    load_manifest,
    load_state,
    pending_dates,
    save_state,
)
from pipeline.identity import decorate_episode
from pipeline.thumbnail import make_thumbnail
from pipeline.upload import upload_short
from pipeline.validate_episode import load_and_validate
from pipeline.voice import generate_voiceover
from pipeline.year_plan import write_calendar


BUILDERS = {
    "body_gentle": "blender/scripts/build_body_gentle_template.py",
}


def _require_english(episode: dict, lang_override: str | None) -> dict:
    lang = (lang_override or episode.get("language") or "en").lower()
    if lang != "en":
        raise SystemExit(
            "English only. Malayalam audio is turned off for this channel."
        )
    episode["language"] = "en"
    episode.setdefault("captions", True)
    episode.setdefault("bgm", True)
    episode.setdefault("made_for_kids", True)
    return episode


def run_episode(
    episode_path: Path,
    *,
    skip_blender: bool = False,
    dry_run: bool = False,
    do_upload: bool = False,
    lang: str | None = None,
) -> Path | None:
    if not episode_path.is_absolute():
        episode_path = ROOT / episode_path

    episode = load_and_validate(episode_path, root=ROOT)
    episode = _require_english(episode, lang)
    episode = decorate_episode(episode)
    # Cinematic USP: never reuse another day's Blender frames or video.
    episode["reuse_frames_from"] = None

    print("=== Kids Edu Shorts ===", flush=True)
    print(f"ID:        {episode['id']}", flush=True)
    print(f"Title:     {episode['title']}", flush=True)
    print(f"Age band:  {episode['age_band']}", flush=True)
    print(f"Template:  {episode['template']}", flush=True)
    print(f"Language:  {episode['language']}", flush=True)
    if episode.get("scene"):
        print(f"Scene:     {episode['scene']}", flush=True)
    print("Quality:   cinematic Blender 3D + unique BGM — never reused footage", flush=True)
    print(f"Shots:     {len(episode.get('shots', []))}", flush=True)
    if episode.get("youtube_title"):
        print(f"YT title:  {episode['youtube_title']}", flush=True)
    if episode.get("world"):
        print(f"World:     {episode['world'].get('preset')} / {episode.get('scene')}", flush=True)

    out_dir = ROOT / "output" / episode["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "episode.json").write_text(
        json.dumps(episode, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if dry_run:
        print("Dry run OK — episode validated. No render.")
        return None

    voice_path = generate_voiceover(episode, out_dir, root=ROOT)
    print(f"Voice:     {voice_path}")

    frames_dir = out_dir / "frames"
    if not skip_blender:
        render_blender_episode(episode, out_dir, root=ROOT)
        frames_dir = out_dir / "frames"
    else:
        print("Skipping Blender (--skip-blender)")

    final_mp4 = assemble_short(episode, out_dir, voice_path, frames_dir, root=ROOT)
    print(f"Output:    {final_mp4}")
    thumb = make_thumbnail(episode, frames_dir, out_dir)
    if thumb:
        print(f"Thumb:     {thumb}")

    if do_upload:
        info = upload_short(
            episode,
            final_mp4,
            credentials_dir=ROOT / "credentials",
            root=ROOT,
        )
        print(f"YouTube:   {info.get('url')}")

    print("Done. Compare against Zack D. Films before publishing.")
    return final_mp4


def _mark(kind: str, day: date, payload: dict) -> None:
    st = load_state(ROOT)
    bucket = st.setdefault("rendered" if kind == "render" else "uploaded", {})
    bucket[day.isoformat()] = payload
    save_state(ROOT, st)


def run_daily_operator(
    *,
    do_upload: bool,
    skip_blender: bool,
    dry_run: bool,
    pre_render: bool,
) -> int:
    try:
        plan = plan_daily(ROOT, do_upload=do_upload, pre_render=pre_render)
    except FileNotFoundError as exc:
        print(exc)
        print("Run: python main.py --plan-year")
        return 1
    print_growth_status(ROOT)
    print("=== Today's factory plan ===")
    for note in plan["notes"]:
        print(f"- {note}")
    print(f"OAuth:     {'yes' if plan['oauth'] else 'NO — add credentials/kids/client_secret.json'}")
    if dry_run:
        print(f"Dry daily publish={plan['publish']} pre_render={plan['pre_render']}")
        return 0

    pub = plan["publish"]
    if pub:
        day = date.fromisoformat(pub)
        if plan["publish_has_video"] and do_upload:
            if not plan["oauth"]:
                print("Skipping upload: kids OAuth file is missing.")
            else:
                try:
                    info = upload_existing_date(day)
                    print(f"Published {pub} → {info.get('url')}")
                except Exception as exc:
                    print(f"Upload failed: {exc}")
                    return 1
        elif plan["publish_has_video"]:
            print(f"Video already rendered for {pub}. Pass --upload to publish.")
        else:
            print(f"Rendering unique film for {pub} …")
            run_scheduled_date(
                day,
                skip_blender=skip_blender,
                dry_run=False,
                do_upload=do_upload and plan["oauth"],
            )

    pre = plan["pre_render"]
    if pre:
        print(f"Pre-rendering next unique film {pre} …")
        run_scheduled_date(
            date.fromisoformat(pre),
            skip_blender=skip_blender,
            dry_run=False,
            do_upload=False,
        )
    print("Daily operator done.")
    return 0


def run_scheduled_date(
    day: date,
    *,
    skip_blender: bool = False,
    dry_run: bool = False,
    do_upload: bool = False,
) -> Path | None:
    path = episode_path_for_date(ROOT, day)
    print(f"Calendar date {day.isoformat()} → {path}")
    episode = json.loads(path.read_text(encoding="utf-8"))
    final = run_episode(
        path,
        skip_blender=skip_blender,
        dry_run=dry_run,
        do_upload=do_upload,
    )
    if dry_run:
        return None
    video = ROOT / "output" / episode["id"] / f"{episode['id']}_short.mp4"
    _mark(
        "render",
        day,
        {
            "id": episode["id"],
            "title": episode["title"],
            "video": str(video.relative_to(ROOT)).replace("\\", "/"),
            "at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    if do_upload and video.exists():
        _mark(
            "upload",
            day,
            {
                "id": episode["id"],
                "video": str(video.relative_to(ROOT)).replace("\\", "/"),
                "at": datetime.now().isoformat(timespec="seconds"),
            },
        )
    return final


def upload_existing_date(day: date) -> dict:
    path = episode_path_for_date(ROOT, day)
    episode = load_and_validate(path, root=ROOT)
    episode = _require_english(episode, None)
    episode = decorate_episode(episode)
    out_dir = ROOT / "output" / episode["id"]
    video = out_dir / f"{episode['id']}_short.mp4"
    if not (out_dir / "thumbnail.jpg").exists():
        make_thumbnail(episode, out_dir / "frames", out_dir)
    info = upload_short(
        episode, video, credentials_dir=ROOT / "credentials", root=ROOT
    )
    _mark(
        "upload",
        day,
        {
            "id": episode["id"],
            "youtube": info,
            "at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    return info


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Kids Edu Shorts factory — English only, Made for Kids"
    )
    parser.add_argument("--episode", default=None, help="Path to episode JSON")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate + print plan only (no Blender / TTS)",
    )
    parser.add_argument(
        "--skip-blender",
        action="store_true",
        help="Voice + assemble only (use existing render frames if present)",
    )
    parser.add_argument(
        "--lang",
        default=None,
        help="Language override. Only en is allowed.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print Blender / ffmpeg / template status and exit",
    )
    parser.add_argument(
        "--build-templates",
        action="store_true",
        help="Generate starter .blend files (needs Blender)",
    )
    parser.add_argument(
        "--plan-year",
        action="store_true",
        help="Write 365 unique English episode JSON files (scripts/calendar/)",
    )
    parser.add_argument(
        "--run-date",
        default=None,
        help="Render the calendar episode for YYYY-MM-DD",
    )
    parser.add_argument(
        "--run-next",
        action="store_true",
        help="Render the next un-rendered calendar date",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=0,
        help="Render the next N un-rendered calendar dates",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="After a successful render, upload to the kids YouTube channel",
    )
    parser.add_argument(
        "--upload-date",
        default=None,
        help="Upload an already-rendered calendar Short for YYYY-MM-DD",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print year-factory queue status and revenue ladder",
    )
    parser.add_argument(
        "--daily",
        action="store_true",
        help="Daily operator: publish at most 1 unique Short, then pre-render the next",
    )
    parser.add_argument(
        "--no-pre-render",
        action="store_true",
        help="With --daily, skip rendering tomorrow's film after today's publish",
    )
    args = parser.parse_args()

    if args.lang and args.lang.lower() != "en":
        print("English only. Malayalam audio is turned off for this channel.")
        return 1

    if args.check:
        return print_tool_report(ROOT)

    if args.build_templates:
        blender = find_blender()
        for name, rel in BUILDERS.items():
            script = ROOT / rel
            print(f"Building template {name} …")
            subprocess.run(
                [blender, "--background", "--python", str(script)],
                check=True,
                cwd=str(ROOT),
            )
        print("Templates built.")
        return 0

    if args.plan_year:
        manifest = write_calendar(ROOT)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        print(f"Wrote {data['count']} English episodes → {manifest}")
        print("Band split: Sat+Sun preschool, Wed students, other weekdays kids 6-10.")
        print("Next: python main.py --run-next")
        print("Full year Blender time is long (about an hour per Short). Use --batch overnight.")
        return 0

    if args.status:
        print_growth_status(ROOT)
        try:
            man = load_manifest(ROOT)
        except FileNotFoundError as exc:
            print(exc)
            return 1
        st = load_state(ROOT)
        print("=== Factory queue ===")
        print(f"Calendar:  {man['count']} English days from {man['start']}")
        print(f"Rendered:  {len(st.get('rendered') or {})}")
        print(f"Uploaded:  {len(st.get('uploaded') or {})}")
        pending = pending_dates(ROOT, need="render")
        pending_up = pending_dates(ROOT, need="upload")
        print(f"Next render: {pending[0] if pending else 'none'}")
        print(f"Next upload: {pending_up[0] if pending_up else 'none'}")
        kids_secret = ROOT / "credentials" / "kids" / "client_secret.json"
        print(f"YouTube:   {'OAuth ready' if kids_secret.exists() else 'add credentials/kids/client_secret.json'}")
        print("Automate:  powershell -File scripts\\install_daily_task.ps1")
        print("Manual:    python main.py --daily --upload")
        return 0

    if args.daily:
        return run_daily_operator(
            do_upload=args.upload,
            skip_blender=args.skip_blender,
            dry_run=args.dry_run,
            pre_render=not args.no_pre_render,
        )

    if args.upload_date:
        day = date.fromisoformat(args.upload_date)
        info = upload_existing_date(day)
        print(f"Uploaded {day.isoformat()} → {info.get('url')}")
        return 0

    dates: list[date] = []
    if args.run_date:
        dates.append(date.fromisoformat(args.run_date))
    elif args.run_next:
        pending = pending_dates(ROOT, need="render")
        if not pending:
            print("Nothing pending. Year queue is complete.")
            return 0
        dates.append(date.fromisoformat(pending[0]))
    elif args.batch:
        pending = pending_dates(ROOT, need="render")
        dates.extend(date.fromisoformat(d) for d in pending[: args.batch])
        if not dates:
            print("Nothing pending. Year queue is complete.")
            return 0

    if dates:
        for day in dates:
            print(f"\n----- {day.isoformat()} -----", flush=True)
            run_scheduled_date(
                day,
                skip_blender=args.skip_blender,
                dry_run=args.dry_run,
                do_upload=args.upload,
            )
        print(f"\nFinished {len(dates)} calendar day(s).")
        return 0

    if not args.episode:
        parser.error(
            "Pass --daily, --episode, --plan-year, --run-date, --run-next, --batch, --status, or --check"
        )

    run_episode(
        Path(args.episode),
        skip_blender=args.skip_blender,
        dry_run=args.dry_run,
        do_upload=args.upload,
        lang=args.lang,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
