"""One-time YouTube OAuth on a TRUSTED computer. Never on a borrowed PC."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.upload import SCOPES, CLIENT_SECRET, TOKEN_FILE, _kids_dir


def main() -> int:
    print("Run this ONLY on a computer you own (or a private GitHub Codespace).")
    print("Do not save tokens on a borrowed PC.")
    kids = _kids_dir(ROOT / "credentials")
    secret = kids / CLIENT_SECRET
    if not secret.exists():
        print(f"Missing {secret}")
        print("Put the kids-channel Desktop OAuth JSON there first.")
        print("Then paste the printed JSON into GitHub Secrets.")
        return 1
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
    creds = flow.run_local_server(port=0)
    (kids / TOKEN_FILE).write_text(creds.to_json(), encoding="utf-8")
    data = json.loads(creds.to_json())
    print("\n=== GitHub secret YOUTUBE_CLIENT_SECRET_JSON ===")
    print(secret.read_text(encoding="utf-8").strip())
    print("\n=== GitHub secret YOUTUBE_REFRESH_TOKEN ===")
    print(data.get("refresh_token") or "(none — re-run and tick consent)")
    print("\n=== Optional GitHub secret YOUTUBE_TOKEN_JSON ===")
    print(json.dumps(data))
    print("\nRepo → Settings → Secrets and variables → Actions → New repository secret")
    print("Never commit these files. Never use gaming-channel OAuth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
