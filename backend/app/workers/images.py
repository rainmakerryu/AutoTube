import httpx

from app.celery_app import celery_app

SHORTS_IMAGE_SIZE = "1024x1792"
LONGFORM_IMAGE_SIZE = "1792x1024"
PEXELS_IMAGE_SIZE = "large"
API_TIMEOUT_SECONDS = 120.0
MAX_IMAGES_PER_PROJECT = 30
PEXELS_PER_PAGE = 1
GEMINI_MODEL = "gemini-2.0-flash-exp"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def extract_visual_keywords(scene: dict) -> str:
    """Extract keywords from scene visual description for image search/generation.
    Combines visual and narration fields into a concise prompt."""
    visual = scene.get("visual", "")

    # Strip scene label prefix like "[장면 1]: " or "Scene 1: "
    if "]: " in visual:
        visual = visual.split("]: ", 1)[1]
    elif ": " in visual and (visual.startswith("[") or visual.lower().startswith("scene")):
        visual = visual.split(": ", 1)[1]

    narration = scene.get("narration", "").strip()

    if narration:
        return f"{visual} {narration}"
    return visual


def build_image_generation_request(
    prompt: str,
    provider: str,
    api_key: str,
    video_type: str = "shorts",
) -> dict:
    """Build API request dict for image generation.

    Provider options:
    - "gemini": POST to Gemini API with image generation config
    - "openai": POST to DALL-E 3 API
    - "pexels": GET to Pexels search API

    Returns dict with url, headers, json/params, method keys.
    """
    is_shorts = video_type == "shorts"
    image_size = SHORTS_IMAGE_SIZE if is_shorts else LONGFORM_IMAGE_SIZE

    if provider == "gemini":
        return {
            "method": "POST",
            "url": f"{GEMINI_BASE_URL}/{GEMINI_MODEL}:generateContent?key={api_key}",
            "headers": {
                "Content-Type": "application/json",
            },
            "json": {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                        ],
                    }
                ],
                "generationConfig": {
                    "responseModalities": ["TEXT", "IMAGE"],
                },
            },
        }
    elif provider == "openai":
        return {
            "method": "POST",
            "url": "https://api.openai.com/v1/images/generations",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            "json": {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": image_size,
            },
        }
    elif provider == "pexels":
        return {
            "method": "GET",
            "url": "https://api.pexels.com/v1/search",
            "headers": {
                "Authorization": api_key,
            },
            "params": {
                "query": prompt,
                "per_page": PEXELS_PER_PAGE,
            },
        }
    else:
        raise ValueError(
            f"지원하지 않는 이미지 provider입니다: {provider}. "
            "'gemini', 'openai' 또는 'pexels'를 사용하세요."
        )


def parse_image_response(provider: str, response_json: dict) -> str | None:
    """Extract image URL from provider response.
    Returns URL string or None if no image found."""
    if provider == "gemini":
        candidates = response_json.get("candidates", [])
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            if "inlineData" in part:
                return part["inlineData"].get("data")
        return None
    elif provider == "openai":
        data = response_json.get("data", [])
        if not data:
            return None
        return data[0].get("url")
    elif provider == "pexels":
        photos = response_json.get("photos", [])
        if not photos:
            return None
        return photos[0].get("src", {}).get(PEXELS_IMAGE_SIZE)
    else:
        raise ValueError(
            f"지원하지 않는 이미지 provider입니다: {provider}. "
            "'gemini', 'openai' 또는 'pexels'를 사용하세요."
        )


@celery_app.task(name="pipeline.generate_images")
def generate_images_task(
    project_id: int,
    scenes: list[dict],
    provider: str,
    api_key: str,
    video_type: str = "shorts",
) -> dict:
    """Generate images for each scene. Returns dict with image_urls list and metadata."""
    limited_scenes = scenes[:MAX_IMAGES_PER_PROJECT]
    image_urls: list[str | None] = []

    for scene in limited_scenes:
        prompt = extract_visual_keywords(scene)
        request = build_image_generation_request(prompt, provider, api_key, video_type)

        method = request["method"]
        if method == "GET":
            response = httpx.get(
                request["url"],
                headers=request["headers"],
                params=request.get("params"),
                timeout=API_TIMEOUT_SECONDS,
            )
        else:
            response = httpx.post(
                request["url"],
                headers=request["headers"],
                json=request.get("json"),
                timeout=API_TIMEOUT_SECONDS,
            )
        response.raise_for_status()

        image_url = parse_image_response(provider, response.json())
        image_urls.append(image_url)

    return {
        "image_urls": image_urls,
        "scene_count": len(limited_scenes),
        "provider": provider,
    }
