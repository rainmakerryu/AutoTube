from app.services.pipeline import PipelineOrchestrator


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
