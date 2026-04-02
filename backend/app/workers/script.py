from __future__ import annotations

import httpx

from app.celery_app import celery_app

SHORTS_DURATION = "30-60초"
LONGFORM_DURATION = "5-15분"
SHORTS_SCENES = "3-5"
LONGFORM_SCENES = "15-25"


TONE_MAP = {
    "humor": "가벼운 유머러스한",
    "honest": "솔직하고 진솔한",
    "persuasive": "설득력 있는",
    "calm": "차분하고 안정된",
    "friendly": "친절하고 따뜻한",
}

PURPOSE_MAP = {
    "sales": "제품 판매를 위한",
    "promotion": "브랜드/서비스 홍보를 위한",
    "daily": "일상/브이로그 느낌의",
}

SPEECH_STYLE_MAP = {
    "formal": "합니다체 (격식 존댓말)",
    "polite": "해요체 (비격식 존댓말)",
    "casual": "반말 (비격식체)",
}


def build_script_prompt(
    topic: str,
    video_type: str,
    language: str = "ko",
    script_config: dict | None = None,
) -> str:
    is_shorts = video_type == "shorts"
    duration = SHORTS_DURATION if is_shorts else LONGFORM_DURATION
    scene_count = SHORTS_SCENES if is_shorts else LONGFORM_SCENES
    cfg = script_config or {}

    # 톤, 목적, 말투 지시문 생성
    extra_instructions: list[str] = []

    tone_id = cfg.get("tone", "auto")
    if tone_id != "auto" and tone_id in TONE_MAP:
        extra_instructions.append(f"- 톤: {TONE_MAP[tone_id]} 톤으로 작성하세요")

    purpose_id = cfg.get("purpose", "auto")
    if purpose_id != "auto" and purpose_id in PURPOSE_MAP:
        extra_instructions.append(f"- 목적: {PURPOSE_MAP[purpose_id]} 영상입니다")

    speech_id = cfg.get("speech_style", "auto")
    if speech_id != "auto" and speech_id in SPEECH_STYLE_MAP:
        extra_instructions.append(f"- 말투: {SPEECH_STYLE_MAP[speech_id]}로 작성하세요")

    opening = cfg.get("opening_comment", "").strip()
    if opening:
        extra_instructions.append(f"- 오프닝 멘트: 첫 장면 나레이션에 다음 멘트를 포함하세요: \"{opening}\"")

    closing = cfg.get("closing_comment", "").strip()
    if closing:
        extra_instructions.append(f"- 클로징 멘트: 마지막 장면 나레이션에 다음 멘트를 포함하세요: \"{closing}\"")

    product_name = cfg.get("product_name", "").strip()
    if product_name:
        extra_instructions.append(f"- 제품명: \"{product_name}\"을 자연스럽게 언급하세요")

    required_info = cfg.get("required_info", "").strip()
    if required_info:
        extra_instructions.append(f"- 필수 정보: 다음 내용을 반드시 포함하세요: {required_info}")

    reference_script = cfg.get("reference_script", "").strip()
    if reference_script:
        extra_instructions.append(f"- 벤치마킹 참고 대본:\n{reference_script}")

    extra_block = "\n".join(extra_instructions)
    extra_section = f"\n\n추가 요구사항:\n{extra_block}" if extra_block else ""

    return f"""당신은 YouTube {video_type} 영상 스크립트 작가입니다.

주제: {topic}
길이: {duration}
장면 수: {scene_count}개
언어: {language}

반드시 아래 형식을 정확히 따르세요. 다른 형식은 절대 사용하지 마세요:

[장면 1]: (이 장면에서 화면에 보여줄 이미지/영상 설명)
나레이션: (이 장면에서 읽을 대사)

[장면 2]: (화면 설명)
나레이션: (대사)

예시:
[장면 1]: 귀여운 고양이가 노트북 키보드 위에 앉아있는 모습
나레이션: 여러분, 고양이가 왜 키보드 위를 좋아하는지 아시나요?

[장면 2]: 고양이가 높은 곳에서 아래를 내려다보는 장엄한 모습
나레이션: 그건 바로 고양이의 지배 본능 때문입니다!

주의사항:
- 반드시 [장면 N]: 으로 시작하세요
- 각 장면에 나레이션: 을 반드시 포함하세요
- 첫 3초 안에 시청자의 주의를 끌어야 합니다
- 각 장면은 명확한 비주얼 설명을 포함해야 합니다
- 나레이션은 자연스러운 구어체로 작성하세요
- [장면 N]: 과 나레이션: 외에 다른 텍스트를 추가하지 마세요{extra_section}"""


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
            else:
                # 폴백: [장면] 없이 나레이션만 있는 경우 자동 장면 생성
                scene_num = len(scenes) + 1
                narration = line.split(":", 1)[1].strip()
                scenes.append({
                    "visual": f"[장면 {scene_num}]: {narration[:50]}",
                    "narration": narration,
                })
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
    script_config: dict | None = None,
) -> dict:
    cfg = script_config or {}

    # manual 모드: API 호출 없이 입력된 대본을 바로 파싱
    if cfg.get("mode") == "manual":
        manual_text = cfg.get("manual_script", "")
        return parse_script_response(manual_text)

    prompt = build_script_prompt(topic, video_type, language, script_config=cfg)
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
