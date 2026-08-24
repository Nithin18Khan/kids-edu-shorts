# GitHub runs the factory (this PC is not yours)

Public repo: https://github.com/Nithin18Khan/kids-edu-shorts  
Branch: `github-actions`  
Actions: https://github.com/Nithin18Khan/kids-edu-shorts/actions

Do **not** leave OAuth files or overnight renders on a borrowed computer.

## What GitHub does every day (06:30 IST)

1. Build one unique English Blender Short  
2. Unique BGM + thumbnail + title + description  
3. Save the mp4 as an **Actions artifact** (download from the run)  
4. If YouTube secrets exist, upload to the **kids** channel (Made for Kids)  
5. Save queue state in `data/factory_state.json`

Manual run: **Actions → Daily kids Short → Run workflow**.

## YouTube upload (optional)

GitHub cannot log into YouTube by itself. YouTube’s API needs a Google Cloud OAuth client **once**. After that, only GitHub Secrets are used — not this PC.

If you cannot use Google Cloud yet: leave secrets empty. Actions still **renders** the Short. Download it from the workflow artifact. Upload by hand until secrets exist.

If you can use Google Cloud on a computer you **own**:

1. Enable **YouTube Data API v3** → OAuth **Desktop** client  
2. `python -m pipeline.oauth_bootstrap` (kids channel only)  
3. Repo → **Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|--------|
| `YOUTUBE_CLIENT_SECRET_JSON` | Full OAuth client JSON |
| `YOUTUBE_REFRESH_TOKEN` | Refresh token from bootstrap |

Never use Ghost of Sparta / gaming OAuth. Never commit these files.

## Limits

- Public repo = more free Actions minutes. Secrets stay hidden.  
- CPU Blender, 6-hour cap, fewer unique frames then stretch to voice.  
- Still a new scene every day.
