"""Tests for images worker — visual keyword extraction with image_prompt priority."""
from __future__ import annotations

from app.workers.images import (
    extract_visual_keywords,
    build_consistent_prompts,
)


class TestExtractVisualKeywords:
    def test_image_prompt_priority(self):
        """image_prompt가 있으면 최우선 사용."""
        scene = {
            "visual": "[장면 1]: 한국어 설명",
            "narration": "한국어 나레이션",
            "image_prompt": "A cat sitting on keyboard, natural light",
        }
        result = extract_visual_keywords(scene)
        assert result == "A cat sitting on keyboard, natural light"

    def test_fallback_without_image_prompt(self):
        """image_prompt가 없으면 visual + narration 사용."""
        scene = {
            "visual": "[장면 1]: 고양이",
            "narration": "안녕하세요",
        }
        result = extract_visual_keywords(scene)
        assert "고양이" in result
        assert "안녕하세요" in result

    def test_empty_image_prompt_falls_back(self):
        """빈 image_prompt는 무시하고 폴백."""
        scene = {
            "visual": "[장면 1]: 고양이",
            "narration": "텍스트",
            "image_prompt": "",
        }
        result = extract_visual_keywords(scene)
        assert "고양이" in result

    def test_whitespace_image_prompt_falls_back(self):
        """공백만 있는 image_prompt는 무시."""
        scene = {
            "visual": "Scene 1: a cat",
            "narration": "hello",
            "image_prompt": "   ",
        }
        result = extract_visual_keywords(scene)
        assert "cat" in result

    def test_scene_prefix_stripped_korean(self):
        scene = {"visual": "[장면 1]: 고양이 모습", "narration": ""}
        result = extract_visual_keywords(scene)
        assert result == "고양이 모습"

    def test_scene_prefix_stripped_english(self):
        scene = {"visual": "Scene 1: cat on desk", "narration": ""}
        result = extract_visual_keywords(scene)
        assert result == "cat on desk"

    def test_visual_only(self):
        scene = {"visual": "pretty flowers"}
        result = extract_visual_keywords(scene)
        assert result == "pretty flowers"


class TestBuildConsistentPrompts:
    def test_uses_image_prompt_for_keywords(self):
        """image_prompt가 있는 장면은 영어 프롬프트를 사용해야 한다."""
        scenes = [
            {
                "visual": "[장면 1]: 한국어",
                "narration": "한국어 나레이션",
                "image_prompt": "A sunset over mountains, golden hour",
            },
            {
                "visual": "[장면 2]: 한국어2",
                "narration": "한국어 나레이션2",
                "image_prompt": "A forest path with morning mist",
            },
        ]
        prompts = build_consistent_prompts(scenes, style="realistic")
        # 첫 번째 프롬프트에 영어 image_prompt가 포함되어야 한다
        assert "sunset" in prompts[0]
        assert "한국어" not in prompts[0]
        # 두 번째 프롬프트에도 영어 image_prompt가 포함되어야 한다
        assert "forest" in prompts[1]

    def test_style_prefix_applied(self):
        scenes = [{"image_prompt": "a cat"}]
        prompts = build_consistent_prompts(scenes, style="anime")
        assert "anime" in prompts[0].lower()

    def test_no_image_prompt_uses_visual(self):
        """image_prompt 없는 기존 형식도 동작해야 한다."""
        scenes = [{"visual": "[장면 1]: pretty flowers", "narration": "hello"}]
        prompts = build_consistent_prompts(scenes)
        assert "pretty flowers" in prompts[0]
