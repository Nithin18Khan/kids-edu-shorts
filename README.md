# Kids Edu Shorts — Blender 3D Channel (Zack D. Films quality bar)

**This borrowed PC is not the factory.** GitHub Actions renders and uploads one unique English Short each day. See `docs/GITHUB.md`.

**Separate project.** Not connected to the Ghost of Sparta / gaming YouTube factory.

| | |
|--|--|
| **Reference** | [Zack D. Films](https://www.youtube.com/@zackdfilms) |
| **Look** | Stylized **Blender 3D** Shorts (not AI image slideshow) |
| **Audience** | Students **1–16** (split age bands) |
| **Models** | Free / clearly licensed 3D assets only |
| **Quality goal** | Each Short must feel like a **mini 3D film**, not a PowerPoint |

---

## Quality bar (non‑negotiable)

We are aiming at **Zack D. Films production language**:

1. Real **Blender** scenes (templates + free models), not Ken Burns on stills  
2. Clean lighting, rim light, depth of field  
3. Friendly educational cutaways — **kid-safe** (no gore / shock anatomy)  
4. Tight Short length, curiosity hook → clear fact → satisfying close  
5. **Every episode different** — different topic, models, camera, and template  
6. Uploaded as **Made for Kids** when content is for children  

If a render looks “flat AI slideshow,” it **fails** the quality bar.

---

## Age bands

| Band | Ages | Folder |
|------|------|--------|
| Soft preschool | 1–5 | `scripts/episodes/age_01_05/` |
| Curious kids (start here) | 6–10 | `scripts/episodes/age_06_10/` |
| Student explainers | 11–16 | `scripts/episodes/age_11_16/` |

Configs: `config/age_bands.json`

---

## Pipeline (automated)

```
episode JSON
    → English voice (Edge-TTS)
    → Blender CLI render (unique topic scene per day)
    → ffmpeg assemble (9:16 Short + captions + BGM)
    → YouTube upload (Made for Kids, kids channel only)
```

English only. Malayalam is off.

### Year factory (365 unique Shorts)

Saturday + Sunday → ages 1–5. Wednesday → ages 11–16. Other weekdays → ages 6–10.

The factory runs on **GitHub**, not this PC. Full setup: `docs/GITHUB.md`

```powershell
python main.py --status
python main.py --daily --upload --dry-run
```

Do not save YouTube OAuth on a borrowed computer. Add secrets on GitHub, then **Actions → Daily kids Short → Run workflow**.

Each Short is a **new cinematic Blender film**: unique cameras, lighting, set, hero, BGM, thumbnail, title, and description. The factory never reuses another day's video or frames.

A 60-second Blender render is slow (often around an hour), so run `--run-next` or `--batch N` overnight. Do not expect 365 finished videos in one sitting.

YouTube upload needs **this kids channel** OAuth in `credentials/kids/client_secret.json` (see `credentials/kids/HOW_TO_AUTH.txt`). Never use gaming-channel secrets.

| Stage | Module |
|-------|--------|
| Year calendar | `pipeline/year_plan.py` + `scripts/calendar/` |
| Validate episode | `pipeline/validate_episode.py` |
| Voice | `pipeline/voice.py` |
| Blender render | `pipeline/blender_render.py` + `blender/scripts/build_topic_scene.py` |
| Assemble Short | `pipeline/assemble.py` |
| Queue | `pipeline/queue.py` |
| Upload | `pipeline/upload.py` |
| One-shot run | `main.py` |

---

## Setup

1. Install **Blender 4.x** → add to PATH or set `BLENDER_PATH`  
2. Python 3.11+  
3. `pip install -r requirements.txt`  
4. `ffmpeg` on PATH  
5. Drop free models into `blender/assets/free_models/` and log them in `MANIFEST.md`  
6. Build / import `.blend` templates into `blender/templates/` (see `docs/TEMPLATES.md`)

```powershell
cd "$env:USERPROFILE\OneDrive\Desktop\kids-edu-shorts"
pip install -r requirements.txt
python main.py --check
python main.py --episode scripts/episodes/age_06_10/ep_001_why_we_sneeze.json --dry-run
```

If Blender is missing:

```powershell
winget install --id BlenderFoundation.Blender.LTS.4.5 -e --accept-package-agreements --accept-source-agreements
python main.py --build-templates
```

Full render (needs Blender + a real `.blend` template):

```powershell
python main.py --episode scripts/episodes/age_06_10/ep_001_why_we_sneeze.json
```

---

## Free 3D models (license rules)

Allowed only if commercial YouTube use is clear:

- Poly Haven (CC0)  
- Sketchfab **CC0 / CC-BY** (credit when required)  
- Kenney / Quaternius kid-friendly packs  
- BlenderKit — **check each asset license**

Log every file in `blender/assets/free_models/MANIFEST.md`.  
No mystery “free download” sites.

---

## What is built vs what you still need

| Ready in this repo | You still provide for Zack-level quality |
|--------------------|------------------------------------------|
| Project structure + age configs | More templates (`space`, `animals`, …) |
| Episode JSON format + samples | Curated free model packs per template |
| Blender 4.5 portable detect + `body_gentle.blend` generator | Look-dev until lighting/models pass the Zack eye test |
| Voice + ffmpeg assembly (ends with narration) | YouTube OAuth for this **new** kids channel |
| 365 English scripts + calendar queue | Overnight `--batch` renders (about an hour per Short) |
| Topic-studio Blender scenes + kids-channel upload | Look-dev until lighting/models pass the Zack eye test |

Automation runs the **factory**. Templates + assets set the **quality**.

---

## Do not mix with gaming channel

- Different folder, credentials, channel ID, thumbnails, topics  
- No God of War / combat assets here  
- Kids content stays Made for Kids–compliant  

---

## Next steps

1. Watch `output/ep_001/ep_001_short.mp4` and iterate `body_gentle` lighting/face until it passes the eye test  
2. Build the next template (`space.blend` or `earth_weather.blend`) the same way  
3. Swap in curated CC0 models when they beat the in-house primitives  
4. Add YouTube upload secrets for the **kids** channel only (`credentials/kids/client_secret.json`)
5. `python main.py --plan-year` then `--run-next` / `--batch` for the English year queue  
