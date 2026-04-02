from __future__ import annotations

import base64

import httpx

from app.celery_app import celery_app
from app.workers.comfyui_client import COMFYUI_DEFAULT_URL

SHORTS_IMAGE_SIZE = "1024x1792"
LONGFORM_IMAGE_SIZE = "1792x1024"
PEXELS_IMAGE_SIZE = "large"
API_TIMEOUT_SECONDS = 120.0
MAX_IMAGES_PER_PROJECT = 30
PEXELS_PER_PAGE = 1
GEMINI_MODEL = "gemini-2.0-flash-exp"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

CONSISTENCY_PROMPT_PREFIX = (
    "Maintain consistent visual style throughout all images. "
    "Use the same art style, color palette, lighting, and character appearance. "
)
CONSISTENCY_STYLE_REFERENCE = "Match the established style: {style}. "

IMAGE_STYLE_PROMPTS: dict[str, str] = {
    "realistic": "Photorealistic, high quality photograph, detailed, natural lighting. ",
    "cinematic": "Cinematic style, dramatic lighting, film grain, movie-like composition, widescreen feel. ",
    "anime": "Japanese anime style, vibrant colors, cel shading, manga-inspired illustration. ",
    "watercolor": "Watercolor painting style, soft colors, fluid brushstrokes, artistic. ",
    "3d": "3D rendered, CGI quality, volumetric lighting, modern 3D graphics. ",
    "minimal": "Minimalist design, clean lines, simple shapes, limited color palette, modern. ",
}


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


def build_consistent_prompts(
    scenes: list[dict],
    style: str = "",
) -> list[str]:
    """Build prompts with style consistency instructions.

    First scene sets the style reference. Subsequent scenes include
    the reference to maintain visual coherence across the video.
    If style is provided, prepend style-specific prompt prefix.
    """
    style_prefix = IMAGE_STYLE_PROMPTS.get(style, "")
    prompts: list[str] = []
    style_description = ""

    for i, scene in enumerate(scenes):
        keywords = extract_visual_keywords(scene)
        if i == 0:
            style_description = keywords
            prompt = f"{style_prefix}{CONSISTENCY_PROMPT_PREFIX}Style reference: {keywords}"
        else:
            style_ref = CONSISTENCY_STYLE_REFERENCE.format(style=style_description)
            prompt = f"{style_prefix}{CONSISTENCY_PROMPT_PREFIX}{style_ref}Scene: {keywords}"
        prompts.append(prompt)

    return prompts


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
    elif provider == "comfyui":
        # Sentinel — ComfyUI uses async workflow submission, handled separately
        return {"method": "COMFYUI"}
    else:
        raise ValueError(
            f"지원하지 않는 이미지 provider입니다: {provider}. "
            "'gemini', 'openai', 'pexels' 또는 'comfyui'를 사용하세요."
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
    elif provider == "comfyui":
        # ComfyUI responses are handled by comfyui_client, not this function
        return None
    else:
        raise ValueError(
            f"지원하지 않는 이미지 provider입니다: {provider}. "
            "'gemini', 'openai', 'pexels' 또는 'comfyui'를 사용하세요."
        )


def _parse_comfyui_dimensions(video_type: str) -> tuple[int, int]:
    """Convert video type to (width, height) for ComfyUI."""
    size_str = SHORTS_IMAGE_SIZE if video_type == "shorts" else LONGFORM_IMAGE_SIZE
    w, h = size_str.split("x")
    return int(w), int(h)


def _extract_output_filename(outputs: dict) -> str | None:
    """Extract the first output image filename from ComfyUI history outputs."""
    for _node_id, node_output in outputs.items():
        images = node_output.get("images", [])
        if images:
            return images[0].get("filename")
    return None


def _generate_comfyui_images(
    prompts: list[str],
    base_url: str,
    video_type: str,
) -> list[str | None]:
    """Generate images via ComfyUI with IP-Adapter style consistency.

    First scene: text-only SDXL generation.
    Subsequent scenes: IP-Adapter with first scene as style reference.
    Returns list of base64-encoded image data (same format as Gemini provider).
    """
    from app.workers.comfyui_client import (
        ComfyUIError,
        check_comfyui_health,
        download_comfyui_image,
        poll_comfyui_result,
        submit_workflow,
        upload_reference_image,
    )
    from app.workers.comfyui_workflow import (
        build_ipadapter_workflow,
        build_txt2img_workflow,
    )

    url = base_url or COMFYUI_DEFAULT_URL

    if not check_comfyui_health(url):
        raise ComfyUIError(
            f"ComfyUI 서버에 연결할 수 없습니다: {url}. "
            "ComfyUI가 실행 중인지 확인하세요."
        )

    width, height = _parse_comfyui_dimensions(video_type)
    image_urls: list[str | None] = []
    reference_filename: str | None = None

    for i, prompt in enumerate(prompts):
        workflow = build_txt2img_workflow(prompt, width, height, seed=i)

        # IP-Adapter가 설치된 경우에만 스타일 일관성 워크플로우 사용
        if i > 0 and reference_filename is not None:
            ipadapter_workflow = build_ipadapter_workflow(
                prompt, reference_filename, width, height, seed=i,
            )
            try:
                prompt_id = submit_workflow(url, ipadapter_workflow)
            except ComfyUIError:
                # IP-Adapter 노드 미설치 시 txt2img로 폴백
                prompt_id = submit_workflow(url, workflow)
        else:
            prompt_id = submit_workflow(url, workflow)
        outputs = poll_comfyui_result(url, prompt_id)

        output_filename = _extract_output_filename(outputs)
        if output_filename is None:
            image_urls.append(None)
            continue

        image_bytes = download_comfyui_image(url, output_filename)

        # First scene: upload as IP-Adapter reference for subsequent scenes
        if i == 0:
            reference_filename = upload_reference_image(
                url, image_bytes, "autotube_ref_scene_0.png",
            )

        b64 = base64.b64encode(image_bytes).decode()
        image_urls.append(b64)

    return image_urls


def _generate_standard_images(
    prompts: list[str],
    provider: str,
    api_key: str,
    video_type: str,
) -> list[str | None]:
    """Generate images via standard HTTP API providers (Gemini, OpenAI, Pexels)."""
    image_urls: list[str | None] = []

    for prompt in prompts:
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

    return image_urls


@celery_app.task(name="pipeline.generate_images")
def generate_images_task(
    project_id: int,
    scenes: list[dict],
    provider: str,
    api_key: str,
    video_type: str = "shorts",
    style: str = "",
) -> dict:
    """Generate images for each scene. Returns dict with image_urls list and metadata."""
    limited_scenes = scenes[:MAX_IMAGES_PER_PROJECT]
    prompts = build_consistent_prompts(limited_scenes, style=style)

    if provider == "comfyui":
        image_urls = _generate_comfyui_images(prompts, api_key, video_type)
    else:
        image_urls = _generate_standard_images(prompts, provider, api_key, video_type)

    return {
        "image_urls": image_urls,
        "scene_count": len(limited_scenes),
        "provider": provider,
    }
