"""
uploader.py
-----------
Handles the final upload payload for YouTube.

RULE: hashtags (e.g. #Shorts #DeepLearning) MUST appear
      - at the end of the description string
      - in the tags list as individual strings with the # prefix
"""

import os
import pickle
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ── OAuth config ─────────────────────────────────────────────────────────────
SCOPES              = ["https://www.googleapis.com/auth/youtube.upload"]
CREDENTIALS_FILE    = str(Path(__file__).parent / "youtube_credentials.json")
TOKEN_FILE          = str(Path(__file__).parent / "youtube_token.pickle")

# YouTube category IDs
CATEGORY_EDUCATION  = "27"
CATEGORY_ENTERTAINMENT = "24"


def _get_youtube_service():
    """Authenticate with YouTube Data API v3 using OAuth2."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"youtube_credentials.json not found at {CREDENTIALS_FILE}. "
                    "Download it from Google Cloud Console → Credentials."
                )
            flow  = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)


def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    hashtags: list[str],
    category_id: str = CATEGORY_EDUCATION,
) -> dict:
    """
    Upload `video_path` to YouTube as a Short.

    Args:
        video_path:   Absolute path to the final MP4.
        title:        Video title — will have  #Shorts appended if missing.
        description:  Main description text. Hashtags are appended automatically.
        hashtags:     List of hashtag strings WITH the # sign,
                      e.g. ["#Shorts", "#WeirdScience", "#Facts"]
        category_id:  YouTube category ID string (default: "27" = Education).

    Returns:
        {"status": "success", "video_id": str, "url": str}
        or
        {"status": "error",   "error": str}
    """
    # ── enforce #Shorts in title ──────────────────────────────────────────────
    if "#Shorts" not in title and "#shorts" not in title:
        title = title + " #Shorts"

    # ── enforce hashtags in description ──────────────────────────────────────
    tag_block = " ".join(hashtags)
    if tag_block not in description:
        description = description.rstrip() + "\n\n" + tag_block

    # ── enforce #Shorts in tags ───────────────────────────────────────────────
    if "#Shorts" not in hashtags:
        hashtags = ["#Shorts"] + hashtags

    try:
        youtube = _get_youtube_service()

        body = {
            "snippet": {
                "title":           title,
                "description":     description,
                "tags":            hashtags,
                "categoryId":      category_id,
                "defaultLanguage": "en",
            },
            "status": {
                "privacyStatus":              "public",
                "madeForKids":                False,
                "selfDeclaredMadeForKids":    False,
            },
        }

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=5 * 1024 * 1024,   # 5 MB chunks
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"[Upload] {pct}% …")

        vid_id  = response["id"]
        url     = f"https://www.youtube.com/shorts/{vid_id}"
        print(f"[Upload] ✓ Published → {url}")

        return {"status": "success", "video_id": vid_id, "url": url}

    except Exception as e:
        print(f"[Upload] ✗ Failed: {e}")
        return {"status": "error", "error": str(e)}
