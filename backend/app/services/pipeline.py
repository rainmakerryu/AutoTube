from __future__ import annotations

STEP_ORDER = ["script", "tts", "audio_post", "images", "video", "bgm", "subtitle", "metadata", "thumbnail", "seo", "sns"]
REQUIRED_STEPS = {"video"}

# 기본 검토 대상 단계 (pipeline_config.review_steps 로 오버라이드 가능)
DEFAULT_REVIEW_STEPS = {"script", "images", "metadata", "seo"}

# 단계별 사용 가능한 프로바이더
STEP_PROVIDERS: dict[str, list[str]] = {
    "script":     ["openai", "claude", "deepseek", "ollama"],
    "tts":        ["elevenlabs", "openai", "edgetts"],
    "audio_post": ["local"],
    "images":     ["gemini", "openai", "pexels", "comfyui"],
    "video":      [],
    "subtitle":   ["openai", "script"],
    "metadata":   ["openai", "claude", "deepseek", "ollama"],
    "thumbnail":  ["openai", "gemini"],
    "bgm":        ["library"],
    "seo":        ["openai", "claude", "deepseek", "ollama"],
    "sns":        ["manual"],
}

STEP_INPUT_MAP = {
    "script": "스크립트 텍스트를 직접 입력하세요",
    "tts": "음성 파일(MP3)을 업로드하세요",
    "images": "이미지 파일들을 업로드하세요",
    "subtitle": "자막 파일(SRT)을 업로드하세요",
    "metadata": "제목, 설명, 태그를 직접 입력하세요",
    "bgm": "배경 음악 파일(MP3)을 업로드하세요",
    "seo": "SEO 키워드를 직접 입력하세요",
    "sns": "SNS 배포 내용을 직접 입력하세요",
}


class PipelineOrchestrator:
    def __init__(self, config: dict):
        self._config = config

    def get_active_steps(self) -> list[str]:
        return [
            step
            for step in STEP_ORDER
            if step in REQUIRED_STEPS or self._config.get(step, False)
        ]

    def get_required_user_inputs(self) -> dict[str, str]:
        return {
            step: STEP_INPUT_MAP[step]
            for step in STEP_ORDER
            if step in STEP_INPUT_MAP and not self._config.get(step, False)
        }

    def needs_review(self, step: str) -> bool:
        """해당 단계가 사용자 검토를 필요로 하는지 반환."""
        review_steps = self._config.get("review_steps")
        if review_steps is not None:
            return step in set(review_steps)
        return step in DEFAULT_REVIEW_STEPS

    def get_next_step(self, current_step: str) -> str | None:
        """현재 단계 다음의 활성 단계를 반환. 마지막이면 None."""
        active = self.get_active_steps()
        try:
            idx = active.index(current_step)
        except ValueError:
            return None
        return active[idx + 1] if idx + 1 < len(active) else None

    def get_step_providers(self, step: str) -> list[str]:
        """해당 단계에서 사용 가능한 프로바이더 목록 반환."""
        return STEP_PROVIDERS.get(step, [])
