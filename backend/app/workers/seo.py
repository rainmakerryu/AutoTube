from __future__ import annotations

import json
import re

import httpx

from app.celery_app import celery_app
from app.services.storage import save_to_output_dir

API_TIMEOUT_SECONDS = 60.0

OPTIMIZED_TITLE_MAX_LENGTH = 100
OPTIMIZED_DESCRIPTION_MAX_LENGTH = 5000
MAX_TAGS = 30


def build_seo_prompt(
    title: str,
    description: str,
    tags: list[str],
    script_text: str,
    video_type: str,
    language: str = "ko",
) -> str:
    return f"""당신은 YouTube SEO 전문가입니다.

아래 영상의 메타데이터를 SEO 관점에서 최적화하세요.

현재 제목: {title}
현재 설명: {description}
현재 태그: {', '.join(tags)}
영상 타입: {video_type}
언어: {language}
스크립트 요약: {script_text[:1000]}

반드시 아래 JSON 형식으로 응답하세요:
{{
    "optimized_title": "SEO 최적화된 제목 (100자 이내, 핵심 키워드를 앞쪽에 배치)",
    "optimized_description": "SEO 최적화된 설명 (5000자 이내, 키워드 포함, CTA 포함, 타임스탬프 제안)",
    "optimized_tags": ["태그1", "태그2", "...최대 30개, 롱테일 키워드 포함"],
    "keyword_suggestions": ["추천 키워드 1", "추천 키워드 2", "...5개"],
    "seo_score": 85,
    "improvements": ["개선사항 1", "개선사항 2"]
}}

주의사항:
- 제목은 클릭률(CTR)을 높이는 방향으로 최적화
- 설명 첫 2줄에 핵심 키워드와 CTA 포함
- 태그는 관련성 높은 롱테일 키워드 포함
- seo_score는 0-100 사이 정수 (현재 메타데이터의 SEO 점수)
- improvements는 구체적인 개선 제안"""


def parse_seo_response(raw_text: str) -> dict:
    """Parse LLM response to extract SEO data."""
    # Try to extract JSON from response
    json_match = re.search(r'\{[\s\S]*\}', raw_text)
    if json_match:
        try:
            data = json.loads(json_match.group())
            # Validate and sanitize
            result = {
                "optimized_title": str(data.get("optimized_title", ""))[:OPTIMIZED_TITLE_MAX_LENGTH],
                "optimized_description": str(data.get("optimized_description", ""))[:OPTIMIZED_DESCRIPTION_MAX_LENGTH],
                "optimized_tags": [str(t) for t in data.get("optimized_tags", [])][:MAX_TAGS],
                "keyword_suggestions": [str(k) for k in data.get("keyword_suggestions", [])],
                "seo_score": int(data.get("seo_score", 0)),
                "improvements": [str(i) for i in data.get("improvements", [])],
            }
            return result
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    return {
        "optimized_title": "",
        "optimized_description": "",
        "optimized_tags": [],
        "keyword_suggestions": [],
        "seo_score": 0,
        "improvements": ["SEO 분석 결과를 파싱할 수 없습니다."],
        "raw_response": raw_text,
    }


def build_seo_api_request(prompt: str, provider: str, api_key: str) -> dict:
    """Build API request for the given provider. Same pattern as metadata/script workers."""
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
            f"지원하지 않는 SEO provider입니다: {provider}. "
            "'openai', 'claude', 'deepseek' 또는 'ollama'를 사용하세요."
        )


OPENAI_COMPATIBLE_PROVIDERS = {"openai", "deepseek", "ollama"}


def extract_text_from_response(provider: str, response_json: dict) -> str:
    if provider in OPENAI_COMPATIBLE_PROVIDERS:
        return response_json["choices"][0]["message"]["content"]
    elif provider == "claude":
        return response_json["content"][0]["text"]
    raise ValueError(f"알 수 없는 provider: {provider}")


@celery_app.task(name="pipeline.optimize_seo")
def optimize_seo_task(
    project_id: int,
    title: str,
    description: str,
    tags: list[str],
    script_text: str,
    video_type: str,
    provider: str,
    api_key: str,
    language: str = "ko",
) -> dict:
    prompt = build_seo_prompt(title, description, tags, script_text, video_type, language)
    request = build_seo_api_request(prompt, provider, api_key)

    response = httpx.post(
        request["url"],
        headers=request["headers"],
        json=request["json"],
        timeout=API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    raw = extract_text_from_response(provider, response.json())
    result = parse_seo_response(raw)

    # Save to output directory
    result_json = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
    save_to_output_dir(project_id, "seo.json", result_json)

    return result
