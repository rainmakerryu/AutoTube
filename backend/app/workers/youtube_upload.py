from __future__ import annotations

import json
import tempfile
from typing import Optional

import httpx

from app.celery_app import celery_app

YOUTUBE_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"
API_TIMEOUT_SECONDS = 300.0
MAX_TITLE_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 5000
MAX_TAGS_COUNT = 30

PRIVACY_OPTIONS = {"public", "private", "unlisted"}
DEFAULT_PRIVACY = "private"
DEFAULT_CATEGORY_ID = "22"  # People & Blogs

CATEGORY_MAP = {
    "entertainment": "24",
    "education": "27",
    "science": "28",
    "howto": "26",
    "news": "25",
    "comedy": "23",
    "people": "22",
    "music": "10",
    "gaming": "20",
    "sports": "17",
}


def build_video_metadata(
    title: str,
    description: str = "",
    tags: Optional[list[str]] = None,
    privacy: str = DEFAULT_PRIVACY,
    category_id: str = DEFAULT_CATEGORY_ID,
    language: str = "ko",
    scheduled_at: Optional[str] = None,
) -> dict:
    """Build YouTube video metadata for upload.

    Args:
        title: Video title (max 100 chars)
        description: Video description (max 5000 chars)
        tags: List of tags (max 30)
        privacy: "public", "private", or "unlisted"
        category_id: YouTube category ID
        language: Default language code
        scheduled_at: ISO 8601 datetime for scheduled publishing (e.g., "2026-04-10T15:00:00Z")

    Returns:
        Metadata dict for YouTube API
    """
    if privacy not in PRIVACY_OPTIONS:
        raise ValueError(
            f"올바르지 않은 공개 설정입니다: {privacy}. "
            f"'{', '.join(sorted(PRIVACY_OPTIONS))}' 중 하나를 사용하세요."
        )

    safe_title = title[:MAX_TITLE_LENGTH]
    safe_description = description[:MAX_DESCRIPTION_LENGTH]
    safe_tags = (tags or [])[:MAX_TAGS_COUNT]

    status: dict = {"privacyStatus": privacy}

    # 예약 공개: scheduled_at이 있으면 private으로 설정하고 publishAt 추가
    if scheduled_at:
        status["privacyStatus"] = "private"
        status["publishAt"] = scheduled_at

    metadata = {
        "snippet": {
            "title": safe_title,
            "description": safe_description,
            "tags": safe_tags,
            "categoryId": category_id,
            "defaultLanguage": language,
        },
        "status": status,
    }

    return metadata


def _download_video_file(video_url: str) -> bytes:
    """Download video file from URL for upload."""
    response = httpx.get(video_url, timeout=API_TIMEOUT_SECONDS, follow_redirects=True)
    response.raise_for_status()
    return response.content


def upload_to_youtube(
    access_token: str,
    video_data: bytes,
    metadata: dict,
) -> dict:
    """Upload video to YouTube using resumable upload protocol.

    Args:
        access_token: OAuth2 access token with youtube.upload scope
        video_data: Video file bytes
        metadata: Video metadata dict from build_video_metadata()

    Returns:
        YouTube API response with video ID and details
    """
    # Step 1: Initiate resumable upload
    init_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": "video/mp4",
        "X-Upload-Content-Length": str(len(video_data)),
    }

    init_response = httpx.post(
        f"{YOUTUBE_UPLOAD_URL}?uploadType=resumable&part=snippet,status",
        headers=init_headers,
        json=metadata,
        timeout=API_TIMEOUT_SECONDS,
    )
    init_response.raise_for_status()

    upload_url = init_response.headers.get("Location")
    if not upload_url:
        raise ValueError(
            "YouTube API에서 업로드 URL을 받지 못했습니다. "
            "OAuth 토큰과 API 권한을 확인하세요."
        )

    # Step 2: Upload video data
    upload_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "video/mp4",
        "Content-Length": str(len(video_data)),
    }

    upload_response = httpx.put(
        upload_url,
        headers=upload_headers,
        content=video_data,
        timeout=API_TIMEOUT_SECONDS,
    )
    upload_response.raise_for_status()

    return upload_response.json()


def set_video_thumbnail(
    access_token: str,
    video_id: str,
    thumbnail_data: bytes,
) -> dict:
    """Set custom thumbnail for an uploaded video.

    Args:
        access_token: OAuth2 access token
        video_id: YouTube video ID
        thumbnail_data: Thumbnail image bytes (JPEG/PNG)

    Returns:
        YouTube API thumbnail response
    """
    response = httpx.post(
        f"{YOUTUBE_API_URL}/thumbnails/set?videoId={video_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "image/jpeg",
        },
        content=thumbnail_data,
        timeout=API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


@celery_app.task(name="pipeline.youtube_upload")
def youtube_upload_task(
    project_id: int,
    video_url: str,
    access_token: str,
    title: str,
    description: str = "",
    tags: Optional[list[str]] = None,
    privacy: str = DEFAULT_PRIVACY,
    category: str = "people",
    language: str = "ko",
    thumbnail_url: Optional[str] = None,
    scheduled_at: Optional[str] = None,
) -> dict:
    """Upload completed video to YouTube.

    Returns dict with youtube_video_id, youtube_url, and upload status.
    """
    category_id = CATEGORY_MAP.get(category, DEFAULT_CATEGORY_ID)

    metadata = build_video_metadata(
        title=title,
        description=description,
        tags=tags,
        privacy=privacy,
        category_id=category_id,
        language=language,
        scheduled_at=scheduled_at,
    )

    video_data = _download_video_file(video_url)
    result = upload_to_youtube(access_token, video_data, metadata)

    video_id = result.get("id", "")
    youtube_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""

    # 썸네일 업로드 (있으면)
    if thumbnail_url and video_id:
        try:
            thumb_response = httpx.get(
                thumbnail_url, timeout=60.0, follow_redirects=True,
            )
            thumb_response.raise_for_status()
            set_video_thumbnail(access_token, video_id, thumb_response.content)
        except Exception:
            pass  # 썸네일 실패는 전체 업로드를 중단하지 않음

    return {
        "youtube_video_id": video_id,
        "youtube_url": youtube_url,
        "privacy": metadata["status"]["privacyStatus"],
        "scheduled_at": scheduled_at,
    }
