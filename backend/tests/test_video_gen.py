"""Tests for video_gen worker — builder selection, prompt construction, validation."""
from __future__ import annotations

import pytest

from app.workers.video_gen import (
    _get_builder,
    _extract_scene_prompt,
    _calculate_clip_duration,
    IMG2VID_BUILDERS,
    TXT2VID_BUILDERS,
    VALID_MODES,
)
from app.workers.comfyui_video_workflow import (
    build_animatediff_workflow,
    build_svd_workflow,
    build_wan21_img2vid_workflow,
    build_wan21_txt2vid_workflow,
    build_cogvideox_img2vid_workflow,
    build_cogvideox_txt2vid_workflow,
)


# --- Builder selection ---

class TestGetBuilder:
    def test_img2vid_animatediff(self):
        assert _get_builder("img2vid", "animatediff") is build_animatediff_workflow

    def test_img2vid_svd(self):
        assert _get_builder("img2vid", "svd") is build_svd_workflow

    def test_img2vid_wan21(self):
        assert _get_builder("img2vid", "wan21") is build_wan21_img2vid_workflow

    def test_img2vid_cogvideox(self):
        assert _get_builder("img2vid", "cogvideox") is build_cogvideox_img2vid_workflow

    def test_txt2vid_wan21(self):
        assert _get_builder("txt2vid", "wan21") is build_wan21_txt2vid_workflow

    def test_txt2vid_cogvideox(self):
        assert _get_builder("txt2vid", "cogvideox") is build_cogvideox_txt2vid_workflow

    def test_img2vid_invalid_model(self):
        with pytest.raises(ValueError, match="img2vid.*지원되지 않습니다"):
            _get_builder("img2vid", "nonexistent")

    def test_txt2vid_invalid_model(self):
        with pytest.raises(ValueError, match="txt2vid.*지원되지 않습니다"):
            _get_builder("txt2vid", "animatediff")

    def test_invalid_mode(self):
        with pytest.raises(ValueError, match="알 수 없는 생성 모드"):
            _get_builder("invalid_mode", "wan21")


# --- Prompt extraction ---

class TestExtractScenePrompt:
    def test_image_prompt_priority(self):
        scene = {"image_prompt": "a sunset", "narration": "the sun sets"}
        assert _extract_scene_prompt(scene) == "a sunset"

    def test_visual_fallback(self):
        scene = {"visual": "forest scene", "narration": "in the forest"}
        assert _extract_scene_prompt(scene) == "forest scene"

    def test_narration_fallback(self):
        scene = {"narration": "hello world"}
        assert _extract_scene_prompt(scene) == "hello world"

    def test_empty_scene(self):
        assert _extract_scene_prompt({}) == ""

    def test_style_prefix(self):
        scene = {"narration": "a cat"}
        result = _extract_scene_prompt(scene, style="anime style, ")
        assert result == "anime style, a cat"

    def test_style_prefix_empty_string(self):
        scene = {"narration": "a cat"}
        result = _extract_scene_prompt(scene, style="")
        assert result == "a cat"

    def test_image_prompt_over_visual(self):
        scene = {"image_prompt": "primary", "visual": "secondary"}
        assert _extract_scene_prompt(scene) == "primary"


# --- Clip duration calculation ---

class TestCalculateClipDuration:
    def test_animatediff(self):
        duration = _calculate_clip_duration("animatediff")
        assert duration == 16 / 8  # 2.0 seconds

    def test_svd(self):
        duration = _calculate_clip_duration("svd")
        assert abs(duration - 25 / 6) < 0.01  # ~4.17 seconds

    def test_wan21(self):
        duration = _calculate_clip_duration("wan21")
        assert abs(duration - 81 / 16) < 0.01  # ~5.06 seconds

    def test_cogvideox(self):
        duration = _calculate_clip_duration("cogvideox")
        assert duration == 49 / 8  # 6.125 seconds

    def test_unknown_model_defaults(self):
        duration = _calculate_clip_duration("unknown")
        assert duration == 16 / 8  # fallback: 2.0 seconds


# --- Builder maps consistency ---

class TestBuilderMaps:
    def test_img2vid_has_expected_models(self):
        assert set(IMG2VID_BUILDERS.keys()) == {"animatediff", "svd", "wan21", "cogvideox"}

    def test_txt2vid_has_expected_models(self):
        assert set(TXT2VID_BUILDERS.keys()) == {"wan21", "cogvideox"}

    def test_valid_modes(self):
        assert VALID_MODES == {"img2vid", "txt2vid"}
