STEP_ORDER = ["script", "tts", "images", "video", "subtitle", "metadata"]
REQUIRED_STEPS = {"video"}

STEP_INPUT_MAP = {
    "script": "스크립트 텍스트를 직접 입력하세요",
    "tts": "음성 파일(MP3)을 업로드하세요",
    "images": "이미지 파일들을 업로드하세요",
    "subtitle": "자막 파일(SRT)을 업로드하세요",
    "metadata": "제목, 설명, 태그를 직접 입력하세요",
}


class PipelineOrchestrator:
    def __init__(self, config: dict[str, bool]):
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
