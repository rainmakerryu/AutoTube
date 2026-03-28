from app.services.pipeline import (
    PipelineOrchestrator,
    DEFAULT_REVIEW_STEPS,
    STEP_PROVIDERS,
)


def test_all_steps_enabled():
    config = {
        "script": True,
        "tts": True,
        "images": True,
        "video": True,
        "subtitle": True,
        "metadata": True,
    }
    orchestrator = PipelineOrchestrator(config)
    steps = orchestrator.get_active_steps()
    assert steps == ["script", "tts", "images", "video", "subtitle", "metadata"]


def test_partial_steps():
    config = {
        "script": False,
        "tts": True,
        "images": False,
        "video": True,
        "subtitle": False,
        "metadata": True,
    }
    orchestrator = PipelineOrchestrator(config)
    steps = orchestrator.get_active_steps()
    assert steps == ["tts", "video", "metadata"]


def test_video_always_included():
    config = {
        "script": False,
        "tts": False,
        "images": False,
        "video": False,
        "subtitle": False,
        "metadata": False,
    }
    orchestrator = PipelineOrchestrator(config)
    steps = orchestrator.get_active_steps()
    assert steps == ["video"]


def test_empty_config_includes_video():
    orchestrator = PipelineOrchestrator({})
    steps = orchestrator.get_active_steps()
    assert "video" in steps


def test_get_required_inputs_for_disabled_steps():
    config = {"script": False, "tts": True, "images": False, "video": True}
    orchestrator = PipelineOrchestrator(config)
    required = orchestrator.get_required_user_inputs()
    assert "script" in required
    assert "images" in required
    assert "tts" not in required


# ─── 신규: needs_review 테스트 ───


def test_needs_review_default():
    orchestrator = PipelineOrchestrator({})
    assert orchestrator.needs_review("script") is True
    assert orchestrator.needs_review("images") is True
    assert orchestrator.needs_review("metadata") is True
    assert orchestrator.needs_review("tts") is False
    assert orchestrator.needs_review("video") is False
    assert orchestrator.needs_review("subtitle") is False


def test_needs_review_custom_override():
    config = {"review_steps": ["tts", "video"]}
    orchestrator = PipelineOrchestrator(config)
    assert orchestrator.needs_review("tts") is True
    assert orchestrator.needs_review("video") is True
    assert orchestrator.needs_review("script") is False
    assert orchestrator.needs_review("images") is False


def test_needs_review_empty_override():
    config = {"review_steps": []}
    orchestrator = PipelineOrchestrator(config)
    assert orchestrator.needs_review("script") is False
    assert orchestrator.needs_review("images") is False


# ─── 신규: get_next_step 테스트 ───


def test_get_next_step():
    config = {
        "script": True, "tts": True, "images": True,
        "video": True, "subtitle": True, "metadata": True,
    }
    orchestrator = PipelineOrchestrator(config)
    assert orchestrator.get_next_step("script") == "tts"
    assert orchestrator.get_next_step("tts") == "images"
    assert orchestrator.get_next_step("metadata") is None


def test_get_next_step_partial():
    config = {"tts": True, "video": True, "metadata": True}
    orchestrator = PipelineOrchestrator(config)
    assert orchestrator.get_next_step("tts") == "video"
    assert orchestrator.get_next_step("video") == "metadata"
    assert orchestrator.get_next_step("metadata") is None


def test_get_next_step_unknown():
    orchestrator = PipelineOrchestrator({"video": True})
    assert orchestrator.get_next_step("nonexistent") is None


# ─── 신규: get_step_providers 테스트 ───


def test_get_step_providers():
    orchestrator = PipelineOrchestrator({})
    assert "openai" in orchestrator.get_step_providers("script")
    assert "claude" in orchestrator.get_step_providers("script")
    assert orchestrator.get_step_providers("video") == []
    assert "openai" in orchestrator.get_step_providers("subtitle")


def test_step_providers_constant():
    assert "script" in STEP_PROVIDERS
    assert "tts" in STEP_PROVIDERS
    assert "images" in STEP_PROVIDERS
    assert len(STEP_PROVIDERS["video"]) == 0


def test_default_review_steps_constant():
    assert "script" in DEFAULT_REVIEW_STEPS
    assert "images" in DEFAULT_REVIEW_STEPS
    assert "metadata" in DEFAULT_REVIEW_STEPS
    assert "tts" not in DEFAULT_REVIEW_STEPS
