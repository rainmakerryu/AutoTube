"""썸네일 이미지 생성 워커.

메타데이터의 제목/설명과 스크립트 장면을 참고하여
유튜브 썸네일(1280x720)을 AI로 생성한다.
"""
from __future__ import annotations

import os

import httpx

from app.celery_app import celery_app
from app.services.storage import (
    StorageService,
    build_storage_key,
    save_local,
    save_to_output_dir,
)

THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720
THUMBNAIL_FILENAME = "thumbnail.png"
THUMBNAIL_CONTENT_TYPE = "image/png"
API_TIMEOUT_SECONDS = 120.0
PROMPT_MAX_LENGTH = 1000


def build_thumbnail_prompt(
    title: str,
    description: str,
    scenes: list[dict],
) -> str:
    """썸네일 생성 프롬프트를 구성한다."""
    # 핵심 장면의 시각 설명 추출
    visual_hints = []
    for scene in scenes[:3]:
        visual = scene.get("visual", scene.get("image_prompt", ""))
        if visual:
            visual_hints.append(visual)
    visual_text = "; ".join(visual_hints) if visual_hints else description[:200]

    prompt = (
        f"YouTube thumbnail for: {title}. "
        f"Key visual: {visual_text}. "
        "Style: eye-catching, high contrast, bold composition, "
        "vibrant colors, professional YouTube thumbnail. "
        "No text overlay. 1280x720 landscape."
    )
    return prompt[:PROMPT_MAX_LENGTH]


def _get_storage() -> StorageService | None:
    """R2 스토리지 서비스를 환경변수에서 초기화."""
    endpoint = os.environ.get("R2_ENDPOINT")
    access_key = os.environ.get("R2_ACCESS_KEY")
    secret_key = os.environ.get("R2_SECRET_KEY")
    bucket = os.environ.get("R2_BUCKET")
    if not all([endpoint, access_key, secret_key, bucket]):
        return None
    return StorageService(endpoint, access_key, secret_key, bucket)


def _generate_with_openai(api_key: str, prompt: str) -> bytes:
    """OpenAI DALL-E로 썸네일 생성."""
    response = httpx.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1792x1024",
            "response_format": "url",
        },
        timeout=API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    image_url = response.json()["data"][0]["url"]
    # 이미지 다운로드
    img_resp = httpx.get(image_url, timeout=API_TIMEOUT_SECONDS)
    img_resp.raise_for_status()
    return img_resp.content


def _generate_with_gemini(api_key: str, prompt: str) -> bytes:
    """Google Gemini로 썸네일 생성."""
    response = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"]},
        },
        timeout=API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    # Gemini 이미지 응답에서 base64 추출
    import base64
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for part in parts:
        inline = part.get("inlineData", {})
        if inline.get("data"):
            return base64.b64decode(inline["data"])
    raise ValueError("Gemini 응답에서 이미지 데이터를 찾을 수 없습니다.")


def _resize_thumbnail(image_data: bytes) -> bytes:
    """썸네일을 1280x720으로 리사이즈."""
    import io
    from PIL import Image

    img = Image.open(io.BytesIO(image_data)).convert("RGB")
    img = img.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


@celery_app.task(name="pipeline.generate_thumbnail")
def generate_thumbnail_task(
    project_id: int,
    title: str,
    description: str,
    scenes: list[dict],
    provider: str = "openai",
    api_key: str = "",
) -> dict:
    """AI로 유튜브 썸네일을 생성한다."""
    prompt = build_thumbnail_prompt(title, description, scenes)

    if provider == "gemini":
        image_data = _generate_with_gemini(api_key, prompt)
    else:
        image_data = _generate_with_openai(api_key, prompt)

    # 리사이즈
    image_data = _resize_thumbnail(image_data)

    # 저장
    key = build_storage_key(project_id, "thumbnail", THUMBNAIL_FILENAME)
    storage = _get_storage()
    if storage:
        thumbnail_url = storage.upload_file(key, image_data, THUMBNAIL_CONTENT_TYPE)
    else:
        thumbnail_url = save_local(key, image_data)

    save_to_output_dir(project_id, THUMBNAIL_FILENAME, image_data)

    return {
        "thumbnail_url": thumbnail_url,
        "prompt_used": prompt,
        "width": THUMBNAIL_WIDTH,
        "height": THUMBNAIL_HEIGHT,
        "provider": provider,
    }
