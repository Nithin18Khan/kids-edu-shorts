"""YouTube upload for the KIDS channel only. Never use gaming-channel secrets."""

from __future__ import annotations

import json
import os
from pathlib import Path


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
CLIENT_SECRET = "client_secret.json"
TOKEN_FILE = "token.json"


def _kids_dir(credentials_dir: Path) -> Path:
    kids = credentials_dir / "kids"
    kids.mkdir(parents=True, exist_ok=True)
    return kids


def youtube_auth_available(root: Path) -> bool:
    if (root / "credentials" / "kids" / CLIENT_SECRET).exists():
        return True
    if os.environ.get("YOUTUBE_CLIENT_SECRET_JSON", "").strip() and (
        os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()
        or os.environ.get("YOUTUBE_TOKEN_JSON", "").strip()
    ):
        return True
    return False


def _hydrate_from_env(kids: Path) -> None:
    secret_json = os.environ.get("YOUTUBE_CLIENT_SECRET_JSON", "").strip()
    if secret_json:
        (kids / CLIENT_SECRET).write_text(secret_json, encoding="utf-8")
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON", "").strip()
    if token_json:
        (kids / TOKEN_FILE).write_text(token_json, encoding="utf-8")


def _creds_from_refresh(kids: Path):
    from google.oauth2.credentials import Credentials

    refresh = os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()
    if not refresh:
        return None
    secret = kids / CLIENT_SECRET
    if not secret.exists():
        return None
    blob = json.loads(secret.read_text(encoding="utf-8"))
    installed = blob.get("installed") or blob.get("web") or blob
    return Credentials(
        token=None,
        refresh_token=refresh,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=installed["client_id"],
        client_secret=installed["client_secret"],
        scopes=SCOPES,
    )


def upload_short(episode: dict, video_path: Path, *, credentials_dir: Path, root: Path | None = None) -> dict:
    if not episode.get("made_for_kids", True):
        raise ValueError("Kids channel uploads must set made_for_kids true")
    if str(episode.get("language") or "en") != "en":
        raise ValueError("This factory uploads English only")
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    kids = _kids_dir(credentials_dir)
    _hydrate_from_env(kids)
    secret = kids / CLIENT_SECRET
    if not secret.exists():
        hint = kids / "HOW_TO_AUTH.txt"
        hint.write_text(
            "Kids channel YouTube upload (English only)\n\n"
            "On a computer YOU own: python -m pipeline.oauth_bootstrap\n"
            "Then put YOUTUBE_CLIENT_SECRET_JSON and YOUTUBE_REFRESH_TOKEN\n"
            "in GitHub Actions secrets. See docs/GITHUB.md\n"
            "Do NOT use Ghost of Sparta / gaming OAuth files.\n",
            encoding="utf-8",
        )
        raise FileNotFoundError(
            f"Missing {secret} and GitHub secrets. See docs/GITHUB.md"
        )

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise RuntimeError(
            "Install upload libs: pip install google-api-python-client "
            "google-auth-oauthlib google-auth-httplib2"
        ) from exc

    ci = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("KIDS_CI") == "1"
    token_path = kids / TOKEN_FILE
    creds = _creds_from_refresh(kids)
    if creds is None and token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds is None:
        if ci:
            raise RuntimeError(
                "GitHub has no valid YouTube refresh token. "
                "On a computer you own run: python -m pipeline.oauth_bootstrap "
                "then add YOUTUBE_REFRESH_TOKEN to repo secrets. See docs/GITHUB.md"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
        creds = flow.run_local_server(port=0)
    if not creds.valid:
        if creds.refresh_token:
            creds.refresh(Request())
        elif ci:
            raise RuntimeError(
                "YouTube token is dead and there is no refresh token. Re-run oauth_bootstrap."
            )
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
            creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json(), encoding="utf-8")

    youtube = build("youtube", "v3", credentials=creds)
    channel = {}
    repo = root or credentials_dir.parent
    ch_cfg = repo / "config" / "channel.json"
    if ch_cfg.exists():
        channel = json.loads(ch_cfg.read_text(encoding="utf-8"))
    expected = str(channel.get("youtube_channel_id") or "").strip()
    if expected:
        mine = youtube.channels().list(part="id,snippet", mine=True).execute()
        items = mine.get("items") or []
        actual = str((items[0] or {}).get("id") or "") if items else ""
        if actual != expected:
            raise RuntimeError(
                f"YouTube login is channel {actual or '(none)'}, not the kids channel {expected}. "
                "Sign in as https://studio.youtube.com/channel/UCJnH0aiSQRq2hODcMUwDJOg "
                "and never use the gaming channel."
            )
        print(f"YouTube: kids channel {actual} OK")
    privacy = (channel.get("upload") or {}).get("privacy_status") or "public"
    title = str(episode.get("youtube_title") or episode.get("title") or episode["id"])[:100]
    if "short" not in title.lower():
        title = f"{title} #Shorts"[:100]
    body = {
        "snippet": {
            "title": title,
            "description": episode.get("description") or title,
            "tags": list(episode.get("tags") or ["kids", "education", "shorts"]),
            "categoryId": str((channel.get("upload") or {}).get("category_id") or "27"),
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": True,
        },
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    print(f"Uploading kids Short → {video_path.name} (Made for Kids, English)")
    response = request.execute()
    video_id = response.get("id")
    url = f"https://youtu.be/{video_id}" if video_id else ""
    print(f"Uploaded: {url}")
    thumb = video_path.parent / "thumbnail.jpg"
    if video_id and thumb.exists():
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumb), mimetype="image/jpeg"),
            ).execute()
            print(f"Thumbnail uploaded: {thumb.name}")
        except Exception as exc:
            print(f"WARNING: thumbnail upload failed: {exc}")
    return {"id": video_id, "url": url, "title": title}
