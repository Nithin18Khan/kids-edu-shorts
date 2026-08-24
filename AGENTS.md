# AGENTS.md — Kids Edu Shorts

This is a **standalone** Cursor project for a **kids educational YouTube Shorts** channel.

## What this project is

| | |
|--|--|
| Reference look | [Zack D. Films](https://www.youtube.com/@zackdfilms) |
| Engine | **Blender 3D** (automated CLI) + Edge-TTS + ffmpeg |
| Audience | Ages **1–16** (banded) |
| Assets | Free / licensed 3D models only |
| Not this | Gaming / God of War channel (`youtube channel` folder) |

## Current status

- Scaffold + episode JSON + pipeline code: **done**
- Blender 4.5.10 portable: detected via `python main.py --check`
- First template: `blender/templates/body_gentle.blend` (look-dev vinyl-toy, **not** Zack-level yet)
- `ep_001_why_we_sneeze` has been run end-to-end → `output/ep_001/ep_001_short.mp4`
- YouTube upload for this kids channel: **OAuth in `credentials/kids/`** (Made for Kids, English only)
- Year factory: GitHub Actions daily (`docs/GITHUB.md`). Do not run overnight batches on a borrowed PC.

## What to do next when asked

1. Confirm Blender via `python main.py --check` (install 4.5 LTS if missing)
2. Build first template: `python main.py --build-templates` → `blender/templates/body_gentle.blend`
3. Add curated free models + update `MANIFEST.md` when something beats the primitives
4. `python main.py --plan-year` then `--daily --upload` (1 unique Short per day)
5. Keep Made for Kids + age-band safety rules. English only. Do not dump the year queue.

## Key paths

- `main.py` — run one episode
- `scripts/calendar/` — 365 English episode JSON files (after `--plan-year`)
- `scripts/episodes/age_*/` — hand-tuned sample scripts
- `pipeline/` — voice, blender, assemble, upload
- `docs/TEMPLATES.md` — quality checklist
- `docs/KIDS_POLICY.md` — kids / YouTube rules

New chats in this folder should read this file + `.cursor/rules/project.mdc` for full context.
