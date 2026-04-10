from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from app.celery_app import celery_app

SHORTS_DURATION = "30-60초"
LONGFORM_DURATION = "5-15분"
SQUARE_DURATION = "30-90초"
SHORTS_SCENES = "3-5"
LONGFORM_SCENES = "15-25"
SQUARE_SCENES = "3-7"


TONE_MAP = {
    "ko": {
        "humor": "가벼운 유머러스한",
        "honest": "솔직하고 진솔한",
        "persuasive": "설득력 있는",
        "calm": "차분하고 안정된",
        "friendly": "친절하고 따뜻한",
    },
    "en": {
        "humor": "light and humorous",
        "honest": "honest and sincere",
        "persuasive": "persuasive",
        "calm": "calm and steady",
        "friendly": "friendly and warm",
    },
    "ja": {
        "humor": "軽くユーモラスな",
        "honest": "正直で誠実な",
        "persuasive": "説得力のある",
        "calm": "落ち着いた安定した",
        "friendly": "親切で温かい",
    },
}

PURPOSE_MAP = {
    "ko": {
        "sales": "제품 판매를 위한",
        "promotion": "브랜드/서비스 홍보를 위한",
        "daily": "일상/브이로그 느낌의",
    },
    "en": {
        "sales": "product sales",
        "promotion": "brand/service promotion",
        "daily": "daily life / vlog style",
    },
    "ja": {
        "sales": "商品販売のための",
        "promotion": "ブランド/サービス宣伝のための",
        "daily": "日常/ブイログ風の",
    },
}

SPEECH_STYLE_MAP = {
    "ko": {
        "formal": "합니다체 (격식 존댓말)",
        "polite": "해요체 (비격식 존댓말)",
        "casual": "반말 (비격식체)",
    },
    "en": {
        "formal": "formal English",
        "polite": "polite conversational English",
        "casual": "casual English",
    },
    "ja": {
        "formal": "です・ます調 (丁寧語)",
        "polite": "ですよ調 (カジュアル丁寧)",
        "casual": "タメ口 (カジュアル)",
    },
}

# 언어별 프롬프트 라벨
LANG_LABELS = {
    "ko": {
        "scene": "장면",
        "narration": "나레이션",
        "image_prompt": "이미지프롬프트",
        "tone_label": "톤",
        "purpose_label": "목적",
        "speech_label": "말투",
        "opening_label": "오프닝 멘트: 첫 장면 나레이션에 다음 멘트를 포함하세요",
        "closing_label": "클로징 멘트: 마지막 장면 나레이션에 다음 멘트를 포함하세요",
        "product_label": "을 자연스럽게 언급하세요",
        "required_label": "필수 정보: 다음 내용을 반드시 포함하세요",
        "reference_label": "벤치마킹 참고 대본",
    },
    "en": {
        "scene": "Scene",
        "narration": "Narration",
        "image_prompt": "ImagePrompt",
        "tone_label": "Tone",
        "purpose_label": "Purpose",
        "speech_label": "Speech style",
        "opening_label": "Opening: include this line in the first scene narration",
        "closing_label": "Closing: include this line in the last scene narration",
        "product_label": " — mention naturally",
        "required_label": "Required info: must include the following",
        "reference_label": "Reference script",
    },
    "ja": {
        "scene": "シーン",
        "narration": "ナレーション",
        "image_prompt": "画像プロンプト",
        "tone_label": "トーン",
        "purpose_label": "目的",
        "speech_label": "話し方",
        "opening_label": "オープニング: 最初のシーンのナレーションに次のセリフを含めてください",
        "closing_label": "クロージング: 最後のシーンのナレーションに次のセリフを含めてください",
        "product_label": "を自然に言及してください",
        "required_label": "必須情報: 以下の内容を必ず含めてください",
        "reference_label": "参考スクリプト",
    },
}

SUPPORTED_LANGUAGES = {"ko", "en", "ja"}
DEFAULT_LANGUAGE = "ko"


def _get_lang(language: str) -> str:
    """지원 언어 코드를 반환. 미지원 시 기본값."""
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def _build_extra_instructions(
    cfg: dict, lang: str, labels: dict,
) -> str:
    """언어별 추가 요구사항 블록 생성."""
    instructions: list[str] = []
    tone_map = TONE_MAP.get(lang, TONE_MAP[DEFAULT_LANGUAGE])
    purpose_map = PURPOSE_MAP.get(lang, PURPOSE_MAP[DEFAULT_LANGUAGE])
    speech_map = SPEECH_STYLE_MAP.get(lang, SPEECH_STYLE_MAP[DEFAULT_LANGUAGE])

    tone_id = cfg.get("tone", "auto")
    if tone_id != "auto" and tone_id in tone_map:
        instructions.append(f"- {labels['tone_label']}: {tone_map[tone_id]}")

    purpose_id = cfg.get("purpose", "auto")
    if purpose_id != "auto" and purpose_id in purpose_map:
        instructions.append(f"- {labels['purpose_label']}: {purpose_map[purpose_id]}")

    speech_id = cfg.get("speech_style", "auto")
    if speech_id != "auto" and speech_id in speech_map:
        instructions.append(f"- {labels['speech_label']}: {speech_map[speech_id]}")

    opening = cfg.get("opening_comment", "").strip()
    if opening:
        instructions.append(f"- {labels['opening_label']}: \"{opening}\"")

    closing = cfg.get("closing_comment", "").strip()
    if closing:
        instructions.append(f"- {labels['closing_label']}: \"{closing}\"")

    product_name = cfg.get("product_name", "").strip()
    if product_name:
        instructions.append(f"- \"{product_name}\"{labels['product_label']}")

    required_info = cfg.get("required_info", "").strip()
    if required_info:
        instructions.append(f"- {labels['required_label']}: {required_info}")

    reference_script = cfg.get("reference_script", "").strip()
    if reference_script:
        instructions.append(f"- {labels['reference_label']}:\n{reference_script}")

    block = "\n".join(instructions)
    if not block:
        return ""
    if lang == "en":
        return f"\n\nAdditional requirements:\n{block}"
    if lang == "ja":
        return f"\n\n追加要件:\n{block}"
    return f"\n\n추가 요구사항:\n{block}"


# 언어별 프롬프트 템플릿
_PROMPT_TEMPLATE_KO = """당신은 YouTube {video_type} 영상 스크립트 작가입니다.

주제: {topic}
길이: {duration}
장면 수: {scene_count}개
언어: {language}

반드시 아래 형식을 정확히 따르세요. 다른 형식은 절대 사용하지 마세요:

[장면 1]: (이 장면에서 화면에 보여줄 이미지/영상 설명)
나레이션: (이 장면에서 읽을 대사)
이미지프롬프트: (이 장면의 이미지를 AI로 생성하기 위한 영어 프롬프트. Stable Diffusion에 최적화된 구체적이고 시각적인 영어 설명)

[장면 2]: (화면 설명)
나레이션: (대사)
이미지프롬프트: (영어 이미지 생성 프롬프트)

예시:
[장면 1]: 귀여운 고양이가 노트북 키보드 위에 앉아있는 모습
나레이션: 여러분, 고양이가 왜 키보드 위를 좋아하는지 아시나요?
이미지프롬프트: A cute fluffy orange cat sitting on a laptop keyboard, soft natural lighting, cozy home office background, photorealistic

[장면 2]: 고양이가 높은 곳에서 아래를 내려다보는 장엄한 모습
나레이션: 그건 바로 고양이의 지배 본능 때문입니다!
이미지프롬프트: A majestic cat perched on a tall bookshelf looking down with piercing eyes, dramatic low angle, cinematic lighting

주의사항:
- 반드시 [장면 N]: 으로 시작하세요
- 각 장면에 나레이션: 과 이미지프롬프트: 를 반드시 포함하세요
- 이미지프롬프트는 반드시 영어로 작성하세요 (AI 이미지 생성 모델이 영어만 이해합니다)
- 이미지프롬프트는 구체적이고 시각적으로 묘사하세요 (주체, 배경, 조명, 분위기, 카메라 앵글 등)
- 첫 3초 안에 시청자의 주의를 끌어야 합니다
- 각 장면은 명확한 비주얼 설명을 포함해야 합니다
- 나레이션은 자연스러운 구어체로 작성하세요{extra_section}"""

_PROMPT_TEMPLATE_EN = """You are a YouTube {video_type} video script writer.

Topic: {topic}
Duration: {duration}
Number of scenes: {scene_count}
Language: {language}

Follow this format exactly. Do not use any other format:

[Scene 1]: (visual description for this scene)
Narration: (dialogue for this scene)
ImagePrompt: (a detailed English prompt for AI image generation. Optimized for Stable Diffusion with specific visual details)

[Scene 2]: (visual description)
Narration: (dialogue)
ImagePrompt: (English image generation prompt)

Example:
[Scene 1]: A cute cat sitting on a laptop keyboard
Narration: Have you ever wondered why cats love sitting on keyboards?
ImagePrompt: A cute fluffy orange cat sitting on a laptop keyboard, soft natural lighting, cozy home office background, photorealistic

[Scene 2]: A cat perched high up, looking down majestically
Narration: It's because of their natural instinct to dominate!
ImagePrompt: A majestic cat perched on a tall bookshelf looking down with piercing eyes, dramatic low angle, cinematic lighting

Rules:
- Always start with [Scene N]:
- Each scene must include Narration: and ImagePrompt:
- ImagePrompt must be in English with specific visual details (subject, background, lighting, mood, camera angle)
- Capture attention within the first 3 seconds
- Each scene needs a clear visual description
- Narration should be natural and conversational{extra_section}"""

_PROMPT_TEMPLATE_JA = """あなたはYouTube {video_type}動画のスクリプトライターです。

テーマ: {topic}
長さ: {duration}
シーン数: {scene_count}
言語: {language}

必ず以下の形式に従ってください。他の形式は使用しないでください:

[シーン 1]: (このシーンで画面に表示する画像/映像の説明)
ナレーション: (このシーンで読むセリフ)
画像プロンプト: (このシーンの画像をAIで生成するための英語プロンプト。Stable Diffusionに最適化された具体的で視覚的な英語の説明)

[シーン 2]: (画面の説明)
ナレーション: (セリフ)
画像プロンプト: (英語の画像生成プロンプト)

例:
[シーン 1]: かわいい猫がノートパソコンのキーボードの上に座っている様子
ナレーション: 皆さん、猫がなぜキーボードの上が好きか知っていますか？
画像プロンプト: A cute fluffy orange cat sitting on a laptop keyboard, soft natural lighting, cozy home office background, photorealistic

[シーン 2]: 猫が高い場所から見下ろしている壮大な姿
ナレーション: それは猫の支配本能のせいなんです！
画像プロンプト: A majestic cat perched on a tall bookshelf looking down with piercing eyes, dramatic low angle, cinematic lighting

注意事項:
- 必ず[シーン N]: で始めてください
- 各シーンにナレーション: と画像プロンプト: を必ず含めてください
- 画像プロンプトは必ず英語で書いてください（AI画像生成モデルは英語のみ理解します）
- 画像プロンプトは具体的かつ視覚的に描写してください（主体、背景、照明、雰囲気、カメラアングルなど）
- 最初の3秒で視聴者の注意を引く必要があります
- 各シーンには明確なビジュアル説明を含めてください
- ナレーションは自然な口語体で書いてください{extra_section}"""

_PROMPT_TEMPLATES = {
    "ko": _PROMPT_TEMPLATE_KO,
    "en": _PROMPT_TEMPLATE_EN,
    "ja": _PROMPT_TEMPLATE_JA,
}


def build_script_prompt(
    topic: str,
    video_type: str,
    language: str = "ko",
    script_config: dict | None = None,
) -> str:
    DURATION_MAP = {
        "shorts": SHORTS_DURATION,
        "long": LONGFORM_DURATION,
        "square": SQUARE_DURATION,
    }
    SCENE_COUNT_MAP = {
        "shorts": SHORTS_SCENES,
        "long": LONGFORM_SCENES,
        "square": SQUARE_SCENES,
    }
    duration = DURATION_MAP.get(video_type, LONGFORM_DURATION)
    scene_count = SCENE_COUNT_MAP.get(video_type, LONGFORM_SCENES)
    cfg = script_config or {}
    lang = _get_lang(language)
    labels = LANG_LABELS.get(lang, LANG_LABELS[DEFAULT_LANGUAGE])

    extra_section = _build_extra_instructions(cfg, lang, labels)
    template = _PROMPT_TEMPLATES.get(lang, _PROMPT_TEMPLATES[DEFAULT_LANGUAGE])

    return template.format(
        video_type=video_type,
        topic=topic,
        duration=duration,
        scene_count=scene_count,
        language=language,
        extra_section=extra_section,
    )


# 장면 헤더 인식 패턴 (한국어, 영어, 일본어)
_SCENE_PREFIXES = ("[장면", "Scene", "[Scene", "[シーン")
_NARRATION_PREFIXES = ("나레이션:", "Narration:", "ナレーション:")
_IMAGE_PROMPT_PREFIXES = (
    "이미지프롬프트:", "ImagePrompt:", "Image Prompt:",
    "画像プロンプト:", "image_prompt:",
)


def parse_script_response(raw_text: str) -> dict:
    if not raw_text.strip():
        return {"full_text": raw_text, "scenes": [], "scene_count": 0}

    lines = raw_text.strip().split("\n")
    scenes: list[dict] = []
    current_scene: dict | None = None
    last_field = ""  # "narration" | "image_prompt" — 여러 줄 이어쓰기 추적

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 장면 헤더
        if any(line.startswith(p) for p in _SCENE_PREFIXES):
            if current_scene:
                scenes.append(current_scene)
            current_scene = {"visual": line, "narration": "", "image_prompt": ""}
            last_field = ""
            continue

        # 나레이션
        if any(line.startswith(p) for p in _NARRATION_PREFIXES):
            narration_text = line.split(":", 1)[1].strip()
            if current_scene is not None:
                current_scene["narration"] = narration_text
                last_field = "narration"
            else:
                # 폴백: [장면] 없이 나레이션만 있는 경우 자동 장면 생성
                scene_num = len(scenes) + 1
                scenes.append({
                    "visual": f"[장면 {scene_num}]: {narration_text[:50]}",
                    "narration": narration_text,
                    "image_prompt": "",
                })
                last_field = ""
            continue

        # 이미지 프롬프트
        if any(line.startswith(p) for p in _IMAGE_PROMPT_PREFIXES):
            if current_scene is not None:
                current_scene["image_prompt"] = line.split(":", 1)[1].strip()
                last_field = "image_prompt"
            continue

        # 이어쓰기 (나레이션이나 이미지 프롬프트가 여러 줄인 경우)
        if current_scene is not None and last_field:
            current_scene[last_field] += " " + line

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
URL_FETCH_TIMEOUT = 30.0
MAX_ARTICLE_CHARS = 8000

_HTML_NOISE_TAGS = {"script", "style", "nav", "footer", "header", "aside", "iframe"}


def fetch_article_text(url: str) -> str:
    """Fetch and extract main text content from a URL.

    Strips HTML tags, navigation, scripts, and other noise.
    Returns plain text limited to MAX_ARTICLE_CHARS.
    """
    response = httpx.get(
        url,
        timeout=URL_FETCH_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": "AutoTube/1.0 (article-to-video)"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup.find_all(_HTML_NOISE_TAGS):
        tag.decompose()

    # article 태그 우선, 없으면 body 전체
    article = soup.find("article") or soup.find("main") or soup.body or soup
    text = article.get_text(separator="\n", strip=True)

    # 빈 줄 정리
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text[:MAX_ARTICLE_CHARS]


def build_url_script_prompt(
    article_text: str,
    video_type: str,
    language: str = "ko",
    script_config: dict | None = None,
) -> str:
    """Build a prompt that converts article text into a video script."""
    DURATION_MAP = {
        "shorts": SHORTS_DURATION,
        "long": LONGFORM_DURATION,
        "square": SQUARE_DURATION,
    }
    SCENE_COUNT_MAP = {
        "shorts": SHORTS_SCENES,
        "long": LONGFORM_SCENES,
        "square": SQUARE_SCENES,
    }
    duration = DURATION_MAP.get(video_type, LONGFORM_DURATION)
    scene_count = SCENE_COUNT_MAP.get(video_type, LONGFORM_SCENES)
    cfg = script_config or {}
    lang = _get_lang(language)
    labels = LANG_LABELS.get(lang, LANG_LABELS[DEFAULT_LANGUAGE])

    extra_section = _build_extra_instructions(cfg, lang, labels)

    url_templates = {
        "ko": (
            "아래 기사/글을 {video_type} 영상 대본으로 변환해주세요.\n\n"
            "원문 내용:\n---\n{article_text}\n---\n\n"
            "영상 길이: {duration}\n"
            "장면 수: {scene_count}개\n"
            "언어: {language}\n\n"
            "각 장면 형식:\n"
            "[장면 N]: 시각적 설명\n"
            "나레이션: 나레이션 텍스트\n"
            "이미지프롬프트: (영어로) Stable Diffusion에 최적화된 시각 프롬프트\n\n"
            "{extra_section}"
            "원문의 핵심 내용을 유지하되, 영상에 맞게 재구성하세요. "
            "자연스러운 흐름과 시각적 설명을 포함해주세요."
        ),
        "en": (
            "Convert the article/text below into a {video_type} video script.\n\n"
            "Source content:\n---\n{article_text}\n---\n\n"
            "Video duration: {duration}\n"
            "Number of scenes: {scene_count}\n"
            "Language: {language}\n\n"
            "Format per scene:\n"
            "Scene N: Visual description\n"
            "Narration: Narration text\n"
            "ImagePrompt: (in English) Visual prompt optimized for Stable Diffusion\n\n"
            "{extra_section}"
            "Keep the core content but restructure for video format. "
            "Include natural flow and visual descriptions."
        ),
        "ja": (
            "以下の記事/テキストを{video_type}動画の台本に変換してください。\n\n"
            "原文:\n---\n{article_text}\n---\n\n"
            "動画の長さ: {duration}\n"
            "シーン数: {scene_count}\n"
            "言語: {language}\n\n"
            "各シーンの形式:\n"
            "[シーン N]: 視覚的説明\n"
            "ナレーション: ナレーションテキスト\n"
            "画像プロンプト: (英語で) Stable Diffusion最適化ビジュアルプロンプト\n\n"
            "{extra_section}"
            "原文の核心内容を保ちつつ、動画に適した構成にしてください。"
        ),
    }

    template = url_templates.get(lang, url_templates[DEFAULT_LANGUAGE])
    return template.format(
        video_type=video_type,
        article_text=article_text,
        duration=duration,
        scene_count=scene_count,
        language=language,
        extra_section=extra_section,
    )


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

    # url 모드: URL에서 기사를 가져와서 대본으로 변환
    if cfg.get("mode") == "url":
        source_url = cfg.get("source_url", "").strip()
        if not source_url:
            raise ValueError(
                "URL 모드에서는 source_url이 필요합니다. "
                "script_config에 source_url을 포함해주세요."
            )
        article_text = fetch_article_text(source_url)
        prompt = build_url_script_prompt(
            article_text, video_type, language, script_config=cfg,
        )
    else:
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
