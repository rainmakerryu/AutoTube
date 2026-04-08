from __future__ import annotations

import json

from app.celery_app import celery_app
from app.services.storage import save_to_output_dir

YOUTUBE_DESCRIPTION_MAX = 5000
INSTAGRAM_CAPTION_MAX = 2200
TIKTOK_CAPTION_MAX = 150
TWITTER_TEXT_MAX = 280
MAX_HASHTAGS = 30


def _build_hashtags(tags: list[str], max_count: int = MAX_HASHTAGS) -> list[str]:
    """Convert tags to hashtag format."""
    hashtags = []
    for tag in tags[:max_count]:
        cleaned = tag.strip().replace(" ", "")
        if cleaned:
            hashtags.append(f"#{cleaned}")
    return hashtags


def _build_youtube_content(title: str, description: str, tags: list[str]) -> dict:
    return {
        "title": title[:100],
        "description": description[:YOUTUBE_DESCRIPTION_MAX],
        "tags": tags[:MAX_HASHTAGS],
    }


def _build_instagram_content(title: str, description: str, tags: list[str]) -> dict:
    hashtags = _build_hashtags(tags, 30)
    hashtag_text = " ".join(hashtags)
    # Build caption: title + short description + hashtags
    short_desc = description[:500] if len(description) > 500 else description
    caption = f"{title}\n\n{short_desc}\n\n{hashtag_text}"
    return {
        "caption": caption[:INSTAGRAM_CAPTION_MAX],
        "hashtags": hashtags,
    }


def _build_tiktok_content(title: str, tags: list[str]) -> dict:
    hashtags = _build_hashtags(tags, 10)
    hashtag_text = " ".join(hashtags)
    # TikTok: very short caption
    available_length = TIKTOK_CAPTION_MAX - len(hashtag_text) - 1
    short_title = title[:available_length] if len(title) > available_length else title
    caption = f"{short_title} {hashtag_text}".strip()
    return {
        "caption": caption[:TIKTOK_CAPTION_MAX],
        "hashtags": hashtags,
    }


def _build_twitter_content(title: str, description: str, tags: list[str]) -> dict:
    hashtags = _build_hashtags(tags, 5)
    hashtag_text = " ".join(hashtags)
    # Twitter: title + short blurb + hashtags within 280 chars
    available = TWITTER_TEXT_MAX - len(hashtag_text) - 2  # 2 for newlines
    short_text = title[:available]
    text = f"{short_text}\n\n{hashtag_text}".strip()
    return {
        "text": text[:TWITTER_TEXT_MAX],
    }


@celery_app.task(name="pipeline.generate_sns")
def generate_sns_task(
    project_id: int,
    title: str,
    description: str,
    tags: list[str],
    video_url: str | None = None,
) -> dict:
    """Generate platform-specific share content for SNS distribution."""
    result = {
        "platforms": {
            "youtube": _build_youtube_content(title, description, tags),
            "instagram": _build_instagram_content(title, description, tags),
            "tiktok": _build_tiktok_content(title, tags),
            "twitter": _build_twitter_content(title, description, tags),
        },
        "video_url": video_url,
    }

    # Save to output directory
    result_json = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
    save_to_output_dir(project_id, "sns.json", result_json)

    return result
