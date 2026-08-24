# GitHub runs the factory (this PC is not yours)

Do **not** leave OAuth files, tokens, or overnight renders on a borrowed computer.

## What GitHub does

Every day at **06:30 IST** (Actions cron `01:00 UTC`):

1. Build one unique English Blender Short  
2. Unique BGM + thumbnail + title + description  
3. Upload to the **kids** YouTube channel (Made for Kids)  
4. Save queue state in `data/factory_state.json`

Trigger manually: repo → **Actions** → **Daily kids Short** → **Run workflow**.

## One-time secrets (on a computer you own)

1. Google Cloud → enable **YouTube Data API v3** → OAuth **Desktop** client  
2. On **your** laptop or a private Codespace (never this borrowed PC):

```powershell
pip install -r requirements.txt
# save Desktop OAuth JSON as credentials/kids/client_secret.json
python -m pipeline.oauth_bootstrap
```

3. GitHub repo → **Settings** → **Secrets and variables** → **Actions**:

| Secret | Value |
|--------|--------|
| `YOUTUBE_CLIENT_SECRET_JSON` | Full OAuth client JSON |
| `YOUTUBE_REFRESH_TOKEN` | Refresh token printed by bootstrap |

Optional: `YOUTUBE_TOKEN_JSON` (full `token.json`).

Never use Ghost of Sparta / gaming OAuth.

## Limits (honest)

- GitHub-hosted runners have a **6-hour** cap and **CPU** Blender (no GPU).  
- CI uses fewer unique frames, then stretches them to the voice. Still a **new scene every day**.  
- A **private** repo has limited free Actions minutes. If jobs die at timeout, turn the repo **public** (secrets stay hidden) or add a paid runner.  
- $1M revenue is not automated. GitHub only ships the daily film.

## Do not do on this PC

- Save `client_secret.json` / `token.json`  
- Run overnight `--batch`  
- `git add` anything under `credentials/` except `HOW_TO_AUTH.txt`
