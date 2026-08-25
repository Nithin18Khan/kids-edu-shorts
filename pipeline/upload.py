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


def _project_id(kids: Path) -> str:
    secret = kids / CLIENT_SECRET
    if not secret.exists():
        return "way-finder-417606"
    try:
        blob = json.loads(secret.read_text(encoding="utf-8"))
        body = blob.get("installed") or blob.get("web") or blob
        return str(body.get("project_id") or "way-finder-417606")
    except Exception:
        return "way-finder-417606"


def _refresh_dead_message(kids: Path) -> str:
    project = _project_id(kids)
    return (
        "YouTube refresh token was rejected. GitHub cannot log in until this is fixed once.\n"
        "1. Open OAuth consent screen → Publish (In production):\n"
        f"   https://console.cloud.google.com/apis/credentials/consent?project={project}\n"
        "   Testing mode kills tokens after ~7 days. Production tokens stay valid.\n"
        "2. Get a new refresh token (Kids Edu Shorts Web client, kids channel only).\n"
        "3. Update GitHub secret YOUTUBE_REFRESH_TOKEN.\n"
        "Never use the gaming channel OAuth."
    )


def assert_kids_youtube_login(root: Path) -> str:
    """Refresh the token and prove it is the kids channel. No upload."""
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    kids = _kids_dir(root / "credentials")
    _hydrate_from_env(kids)
    creds = _creds_from_refresh(kids)
    token_path = kids / TOKEN_FILE
    if creds is None and token_path.exists():
        from google.oauth2.credentials import Credentials

        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds is None:
        raise RuntimeError(
            "GitHub has no YouTube refresh token. "
            "Add YOUTUBE_CLIENT_SECRET_JSON and YOUTUBE_REFRESH_TOKEN to this repo only."
        )
    try:
        if not creds.valid:
            if not creds.refresh_token:
                raise RuntimeError(_refresh_dead_message(kids))
            creds.refresh(Request())
    except RefreshError as exc:
        raise RuntimeError(_refresh_dead_message(kids)) from exc
    token_path.write_text(creds.to_json(), encoding="utf-8")
    youtube = build("youtube", "v3", credentials=creds)
    expected = ""
    ch_cfg = root / "config" / "channel.json"
    if ch_cfg.exists():
        expected = str(
            (json.loads(ch_cfg.read_text(encoding="utf-8")).get("youtube_channel_id") or "")
        ).strip()
    mine = youtube.channels().list(part="id,snippet", mine=True).execute()
    items = mine.get("items") or []
    return _assert_kids_channel(expected, items)


def _channel_label(item: dict) -> str:
    cid = str(item.get("id") or "")
    title = str(((item.get("snippet") or {}).get("title")) or "").strip()
    return f"{title or '(unnamed)'} ({cid})" if cid else "(none)"


def _assert_kids_channel(expected: str, items: list) -> str:
    actual_item = items[0] if items else {}
    actual = str((actual_item or {}).get("id") or "")
    if expected and actual != expected:
        raise RuntimeError(
            "YouTube token is logged into "
            f"{_channel_label(actual_item)}, not the kids channel {expected}. "
            "Re-run OAuth Playground. When Google asks which channel, pick ONLY "
            "https://studio.youtube.com/channel/UCJnH0aiSQRq2hODcMUwDJOg "
            "— not Malayalam, gaming, or Buy or Skip. Then update GitHub secret "
            "YOUTUBE_REFRESH_TOKEN."
        )
    print(f"YouTube: kids channel {actual or expected} OK")
    return actual or expected


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

    from pipeline.quality import assert_full_film

    assert_full_film(episode, video_path)

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
            try:
                from google.auth.exceptions import RefreshError

                creds.refresh(Request())
            except RefreshError as exc:
                raise RuntimeError(_refresh_dead_message(kids)) from exc
        elif ci:
            raise RuntimeError(_refresh_dead_message(kids))
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
        _assert_kids_channel(expected, mine.get("items") or [])
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


def delete_youtube_video(video_id: str, *, root: Path) -> dict:
    """Remove a bad upload from the kids channel only."""
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    vid = str(video_id or "").strip()
    if not vid:
        raise ValueError("Need a YouTube video id")
    creds_dir = root / "credentials"
    kids = _kids_dir(creds_dir)
    _hydrate_from_env(kids)
    assert_kids_youtube_login(root)
    creds = _creds_from_refresh(kids)
    token_path = kids / TOKEN_FILE
    if creds is None and token_path.exists():
        from google.oauth2.credentials import Credentials

        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds is None:
        raise RuntimeError("No YouTube token to delete with.")
    youtube = build("youtube", "v3", credentials=creds)
    try:
        youtube.videos().delete(id=vid).execute()
        print(f"Deleted YouTube video {vid}")
        return {"id": vid, "deleted": True, "private": False}
    except HttpError as exc:
        print(f"Delete not allowed ({exc}). Setting privacy to private instead.")
        youtube.videos().update(
            part="status",
            body={"id": vid, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": True}},
        ).execute()
        print(f"Unlisted/private now: https://youtu.be/{vid}")
        return {"id": vid, "deleted": False, "private": True}
