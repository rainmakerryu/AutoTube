import json

import httpx

from app.celery_app import celery_app

MAX_TITLE_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 5000
MAX_TAGS = 30
MAX_TAG_LENGTH = 100
API_TIMEOUT_SECONDS = 60.0


def build_metadata_prompt(
    script_text: str,
    video_type: str,
    language: str = "ko",
) -> str:
    """Build prompt for AI to generate YouTube metadata.
    Asks for: title, description, tags (as JSON)."""
    is_shorts = video_type == "shorts"
    format_label = "YouTube Shorts(쇼츠)" if is_shorts else "YouTube longform 영상"

    return f"""당신은 YouTube SEO 전문가입니다.

다음 스크립트를 바탕으로 {format_label}에 최적화된 메타데이터를 생성하세요.

스크립트:
{script_text}

영상 유형: {video_type}
언어: {language}

다음 JSON 형식으로 응답하세요:
{{
  "title": "SEO에 최적화된 제목 (100자 이내)",
  "description": "영상 설명 (키워드 포함, 5000자 이내)",
  "tags": ["태그1", "태그2", "태그3", ...]
}}

주의사항:
- 제목은 클릭을 유도하되 과장하지 마세요
- 설명은 핵심 키워드를 자연스럽게 포함하세요
- 태그는 관련성 높은 것부터 최대 30개까지 작성하세요"""


def parse_metadata_response(raw_text: str) -> dict:
    """Parse AI response into structured metadata.
    Expected format: JSON with title, description, tags keys.
    Falls back to extracting from raw text if JSON parsing fails."""
    try:
        parsed = json.loads(raw_text)
        return {
            "title": parsed.get("title", ""),
            "description": parsed.get("description", ""),
            "tags": parsed.get("tags", []),
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "title": "",
            "description": raw_text,
            "tags": [],
        }


def validate_metadata(metadata: dict) -> dict:
    """Validate and truncate metadata to YouTube limits.
    Truncates title to MAX_TITLE_LENGTH, description to MAX_DESCRIPTION_LENGTH,
    tags to MAX_TAGS items each truncated to MAX_TAG_LENGTH."""
    title = metadata.get("title", "")[:MAX_TITLE_LENGTH]
    description = metadata.get("description", "")[:MAX_DESCRIPTION_LENGTH]
    raw_tags = metadata.get("tags", [])[:MAX_TAGS]
    tags = [tag[:MAX_TAG_LENGTH] for tag in raw_tags]

    return {
        "title": title,
        "description": description,
        "tags": tags,
    }


def build_metadata_api_request(prompt: str, provider: str, api_key: str) -> dict:
    """Build API request for metadata generation.
    Supports 'openai' and 'claude' providers (same as script worker)."""
    if provider == "openai":
        return {
            "url": "https://api.openai.com/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            "json": {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
            },
        }
    elif provider == "claude":
        return {
            "url": "https://api.anthropic.com/v1/messages",
            "headers": {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            "json": {
                "model": "claude-sonnet-4-6-20250514",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
            },
        }
    elif provider == "deepseek":
        return {
            "url": "https://api.deepseek.com/chat/completions",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            "json": {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
            },
        }
    elif provider == "ollama":
        base_url = api_key or "http://localhost:11434"
        return {
            "url": f"{base_url}/v1/chat/completions",
            "headers": {"Content-Type": "application/json"},
            "json": {
                "model": "llama3",
                "messages": [{"role": "user", "content": prompt}],
            },
        }
    else:
        raise ValueError(
            f"지원하지 않는 메타데이터 API provider입니다: {provider}. "
            "'openai', 'claude', 'deepseek' 또는 'ollama'를 사용하세요."
        )


OPENAI_COMPATIBLE_PROVIDERS = {"openai", "deepseek", "ollama"}


def extract_text_from_response(provider: str, response_json: dict) -> str:
    """Extract text content from API response."""
    if provider in OPENAI_COMPATIBLE_PROVIDERS:
        return response_json["choices"][0]["message"]["content"]
    elif provider == "claude":
        return response_json["content"][0]["text"]
    raise ValueError(f"알 수 없는 provider: {provider}")


@celery_app.task(name="pipeline.generate_metadata")
def generate_metadata_task(
    project_id: int,
    script_text: str,
    video_type: str,
    api_provider: str,
    api_key: str,
    language: str = "ko",
) -> dict:
    """Generate YouTube metadata. Returns dict with title, description, tags."""
    prompt = build_metadata_prompt(script_text, video_type, language)
    request = build_metadata_api_request(prompt, api_provider, api_key)

    response = httpx.post(
        request["url"],
        headers=request["headers"],
        json=request["json"],
        timeout=API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    raw = extract_text_from_response(api_provider, response.json())
    metadata = parse_metadata_response(raw)
    return validate_metadata(metadata)
