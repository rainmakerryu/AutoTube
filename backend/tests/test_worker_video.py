import pytest

from app.workers.video import (
    build_ken_burns_params,
    calculate_scene_durations,
    get_resolution,
    validate_inputs,
    MIN_IMAGE_DURATION_SECONDS,
    MAX_IMAGE_DURATION_SECONDS,
)


def test_get_resolution_shorts():
    assert get_resolution("shorts") == (1080, 1920)


def test_get_resolution_longform():
    assert get_resolution("longform") == (1920, 1080)


def test_get_resolution_invalid():
    with pytest.raises(ValueError, match="지원하지 않는"):
        get_resolution("unknown")


def test_calculate_scene_durations_even():
    durations = calculate_scene_durations(30.0, 6)
    assert len(durations) == 6
    assert all(d == pytest.approx(5.0) for d in durations)


def test_calculate_scene_durations_clamp_min():
    durations = calculate_scene_durations(3.0, 6)
    assert len(durations) == 6
    assert all(d == pytest.approx(MIN_IMAGE_DURATION_SECONDS) for d in durations)


def test_calculate_scene_durations_clamp_max():
    durations = calculate_scene_durations(300.0, 2)
    assert len(durations) == 2
    assert all(d == pytest.approx(MAX_IMAGE_DURATION_SECONDS) for d in durations)


def test_calculate_scene_durations_single():
    durations = calculate_scene_durations(10.0, 1)
    assert len(durations) == 1
    assert durations[0] == pytest.approx(10.0)


def test_build_ken_burns_alternating():
    params_even = build_ken_burns_params(0, 4)
    params_odd = build_ken_burns_params(1, 4)

    even_zooms_in = params_even["start_zoom"] < params_even["end_zoom"]
    odd_zooms_in = params_odd["start_zoom"] < params_odd["end_zoom"]
    assert even_zooms_in != odd_zooms_in


def test_build_ken_burns_params_structure():
    params = build_ken_burns_params(0, 4)
    assert "start_zoom" in params
    assert "end_zoom" in params
    assert "pan_direction" in params


def test_validate_inputs_valid():
    errors = validate_inputs(
        image_paths=["scene1.jpg", "scene2.png"],
        audio_path="narration.mp3",
        video_type="shorts",
    )
    assert errors == []


def test_validate_inputs_no_images():
    errors = validate_inputs(
        image_paths=[],
        audio_path="narration.mp3",
        video_type="shorts",
    )
    assert len(errors) > 0
    assert any("이미지" in e for e in errors)


def test_validate_inputs_invalid_format():
    errors = validate_inputs(
        image_paths=["animation.gif"],
        audio_path="narration.mp3",
        video_type="shorts",
    )
    assert len(errors) > 0
    assert any("gif" in e.lower() for e in errors)


def test_validate_inputs_invalid_video_type():
    errors = validate_inputs(
        image_paths=["scene.jpg"],
        audio_path="narration.mp3",
        video_type="unknown",
    )
    assert len(errors) > 0
    assert any("비디오 타입" in e or "video_type" in e for e in errors)
