# GitHub runs the factory (this PC is not yours)

Public repo: https://github.com/Nithin18Khan/kids-edu-shorts  
Kids YouTube Studio: https://studio.youtube.com/channel/UCJnH0aiSQRq2hODcMUwDJOg

Secrets live in **this repo only**. Never put them in a gaming repo.

## One click you must do (Google, not GitHub)

GitHub cannot publish your OAuth app. If the consent screen stays in **Testing**, the login token dies in ~7 days and uploads stop.

1. Open [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent?project=way-finder-417606)
2. Click **Publish app** → confirm **In production**
3. Ignore the “unverified app” warning. You are the only user.

Do this once. After that GitHub keeps logging in.

## What GitHub does every day (06:30 IST)

1. Prove login is the **kids** channel (`UCJnH0aiSQRq2hODcMUwDJOg`)
2. Build one unique English Blender Short (retries up to 3 times if Blender crashes)
3. Unique BGM + thumbnail + title + description
4. Upload to the kids channel (Made for Kids)
5. Record queue state so the next day continues even if today failed
6. Heartbeat commit so GitHub does not disable the daily cron

From **31 Aug 2026** the cron builds and uploads the rest of the 365-day English calendar: **one unique Short per IST day**, Made for Kids, kids channel only. It will not dump the year in one night. Gold films already on YouTube (sneeze, sky blue, rain) stay marked uploaded so they are not posted twice.

If a day fails, the next successful day publishes the next unpublished film (still max 1 upload per day).

Manual run: **Actions → Daily kids Short → Run workflow**.

## YouTube secrets (already set)

| Secret | Value |
|--------|--------|
| `YOUTUBE_CLIENT_SECRET_JSON` | Kids Edu Shorts Web JSON |
| `YOUTUBE_REFRESH_TOKEN` | Refresh token for that client |

Never use Ghost of Sparta / gaming OAuth. Never commit these files.

Turn on GitHub **Actions failure emails** once (GitHub → Settings → Notifications) so you are only pinged if something breaks.

## Limits

- Public repo = more free Actions minutes. Secrets stay hidden.
- CPU Blender, 6-hour cap. Automation uses the **same local cinematic grade** as the sneeze Short: Eevee, 1080×1920, 24fps, every frame, 8 camera cuts. Shots render in parallel on GitHub so it still fits the cap. Sneeze publishes the saved 59s file. Later days are unique sets with that same film look — not a 540p Workbench slideshow.
- Still a new scene every day.
