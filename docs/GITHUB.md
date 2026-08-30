# This PC renders. GitHub only uploads.

Public repo: https://github.com/Nithin18Khan/kids-edu-shorts  
Kids YouTube Studio: https://studio.youtube.com/channel/UCJnH0aiSQRq2hODcMUwDJOg

Secrets live in **this repo only**. Never put them in a gaming repo.

**Quality rule:** GitHub must never publish a CPU / software-GL Blender stub. This laptop renders the Short (`scripts/pc_daily.ps1`). GitHub uploads only if `approved/{id}_short.mp4` is already in the repo.

## One click you must do (Google, not GitHub)

GitHub cannot publish your OAuth app. If the consent screen stays in **Testing**, the login token dies in ~7 days and uploads stop.

1. Open [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent?project=way-finder-417606)
2. Click **Publish app** → confirm **In production**
3. Ignore the “unverified app” warning. You are the only user.

Do this once. After that GitHub keeps logging in.

## What happens each day (1 Short, quality only)

1. **This PC:** `scripts/pc_daily.ps1`  
   - Renders the next unpublished year-script on local Blender  
   - Saves `approved/{id}_short.mp4`  
   - Pushes that file  
   - Asks GitHub to upload  
2. **GitHub** (06:30 IST + 09:00 backup): if that gold file is in the repo, upload to the kids channel. If it is missing, **skip** — no CPU film.

Sneeze, sky blue, and rain stay marked uploaded so they are not posted twice.

Cap is still **1 unique Short per IST day**. The year queue is not dumped in one night.

Manual: `python main.py --daily --no-pre-render` then push `approved/`, then **Actions → Daily kids Short → Run workflow**.

## YouTube secrets (already set)

| Secret | Value |
|--------|--------|
| `YOUTUBE_CLIENT_SECRET_JSON` | Kids Edu Shorts Web JSON |
| `YOUTUBE_REFRESH_TOKEN` | Refresh token for that client |

Never use Ghost of Sparta / gaming OAuth. Never commit these files.

Turn on GitHub **Actions failure emails** once (GitHub → Settings → Notifications) so you are only pinged if something breaks.

## Limits

- Public repo = more free Actions minutes. Secrets stay hidden.
- YouTube login stays on GitHub (local OAuth is a Web client and cannot use `localhost`).
- Still a new scene every day. One film per day.
