import httpx

from app.celery_app import celery_app

SHORTS_DURATION = "30-60초"
LONGFORM_DURATION = "5-15분"
SHORTS_SCENES = "3-5"
LONGFORM_SCENES = "15-25"


def build_script_prompt(topic: str, video_type: str, language: str = "ko") -> str:
    is_shorts = video_type == "shorts"
    duration = SHORTS_DURATION if is_shorts else LONGFORM_DURATION
    scene_count = SHORTS_SCENES if is_shorts else LONGFORM_SCENES

    return f"""당신은 YouTube {video_type} 영상 스크립트 작가입니다.

주제: {topic}
길이: {duration}
장면 수: {scene_count}개
언어: {language}

다음 형식으로 스크립트를 작성하세요:
[장면 N]: (화면 설명)
나레이션: (읽을 내용)

주의사항:
- 첫 3초 안에 시청자의 주의를 끌어야 합니다
- 각 장면은 명확한 비주얼 설명을 포함해야 합니다
- 나레이션은 자연스러운 구어체로 작성하세요"""


def parse_script_response(raw_text: str) -> dict:
    if not raw_text.strip():
        return {"full_text": raw_text, "scenes": [], "scene_count": 0}

    lines = raw_text.strip().split("\n")
    scenes: list[dict] = []
    current_scene: dict | None = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("[장면") or line.startswith("Scene"):
            if current_scene:
                scenes.append(current_scene)
            current_scene = {"visual": line, "narration": ""}
        elif line.startswith("나레이션:") or line.startswith("Narration:"):
            if current_scene is not None:
                current_scene["narration"] = line.split(":", 1)[1].strip()
        elif current_scene is not None:
            current_scene["narration"] += " " + line

    if current_scene:
        scenes.append(current_scene)

    return {
        "full_text": raw_text,
        "scenes": scenes,
        "scene_count": len(scenes),
    }


def build_api_request(prompt: str, provider: str, api_key: str) -> dict:
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
            f"지원하지 않는 스크립트 API provider입니다: {provider}. "
            "'openai', 'claude', 'deepseek' 또는 'ollama'를 사용하세요."
        )


OPENAI_COMPATIBLE_PROVIDERS = {"openai", "deepseek", "ollama"}


def extract_text_from_response(provider: str, response_json: dict) -> str:
    if provider in OPENAI_COMPATIBLE_PROVIDERS:
        return response_json["choices"][0]["message"]["content"]
    elif provider == "claude":
        return response_json["content"][0]["text"]
    raise ValueError(f"알 수 없는 provider: {provider}")


API_TIMEOUT_SECONDS = 60.0


@celery_app.task(name="pipeline.generate_script")
def generate_script_task(
    project_id: int,
    topic: str,
    video_type: str,
    api_provider: str,
    api_key: str,
    language: str = "ko",
) -> dict:
    prompt = build_script_prompt(topic, video_type, language)
    request = build_api_request(prompt, api_provider, api_key)

    response = httpx.post(
        request["url"],
        headers=request["headers"],
        json=request["json"],
        timeout=API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    raw = extract_text_from_response(api_provider, response.json())
    return parse_script_response(raw)
