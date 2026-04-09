"""Tests for script worker — prompt building, response parsing, multi-language."""
from __future__ import annotations

import pytest

from app.workers.script import (
    build_script_prompt,
    parse_script_response,
    _get_lang,
    _build_extra_instructions,
    LANG_LABELS,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
)


# --- Language helper ---

class TestGetLang:
    def test_supported_ko(self):
        assert _get_lang("ko") == "ko"

    def test_supported_en(self):
        assert _get_lang("en") == "en"

    def test_supported_ja(self):
        assert _get_lang("ja") == "ja"

    def test_unsupported_falls_back(self):
        assert _get_lang("fr") == DEFAULT_LANGUAGE

    def test_empty_falls_back(self):
        assert _get_lang("") == DEFAULT_LANGUAGE


# --- Prompt building ---

class TestBuildScriptPrompt:
    def test_korean_prompt_has_image_prompt_field(self):
        prompt = build_script_prompt("고양이", "shorts", "ko")
        assert "이미지프롬프트:" in prompt
        assert "영어로 작성하세요" in prompt

    def test_english_prompt_has_image_prompt_field(self):
        prompt = build_script_prompt("cats", "shorts", "en")
        assert "ImagePrompt:" in prompt
        assert "English" in prompt

    def test_japanese_prompt_has_image_prompt_field(self):
        prompt = build_script_prompt("猫", "shorts", "ja")
        assert "画像プロンプト:" in prompt
        assert "英語で書いてください" in prompt

    def test_shorts_duration(self):
        prompt = build_script_prompt("test", "shorts", "en")
        assert "30-60" in prompt

    def test_longform_duration(self):
        prompt = build_script_prompt("test", "long", "en")
        assert "5-15" in prompt

    def test_unsupported_language_uses_korean(self):
        prompt = build_script_prompt("test", "shorts", "zh")
        assert "이미지프롬프트:" in prompt

    def test_extra_instructions_tone(self):
        cfg = {"tone": "humor"}
        prompt = build_script_prompt("test", "shorts", "ko", script_config=cfg)
        assert "유머러스" in prompt

    def test_extra_instructions_tone_en(self):
        cfg = {"tone": "humor"}
        prompt = build_script_prompt("test", "shorts", "en", script_config=cfg)
        assert "humorous" in prompt

    def test_extra_instructions_product(self):
        cfg = {"product_name": "SuperCat"}
        prompt = build_script_prompt("test", "shorts", "ko", script_config=cfg)
        assert "SuperCat" in prompt

    def test_extra_instructions_opening(self):
        cfg = {"opening_comment": "Hello everyone!"}
        prompt = build_script_prompt("test", "shorts", "en", script_config=cfg)
        assert "Hello everyone!" in prompt

    def test_no_extra_when_auto(self):
        cfg = {"tone": "auto", "purpose": "auto", "speech_style": "auto"}
        prompt = build_script_prompt("test", "shorts", "ko", script_config=cfg)
        assert "추가 요구사항" not in prompt


# --- Response parsing ---

class TestParseScriptResponse:
    def test_empty_input(self):
        result = parse_script_response("")
        assert result["scenes"] == []
        assert result["scene_count"] == 0

    def test_korean_format_with_image_prompt(self):
        text = (
            "[장면 1]: 고양이가 키보드 위에 앉아있는 모습\n"
            "나레이션: 고양이가 왜 키보드를 좋아할까요?\n"
            "이미지프롬프트: A cute cat sitting on keyboard, natural light\n"
            "\n"
            "[장면 2]: 고양이가 높은 곳에서 내려다보는 모습\n"
            "나레이션: 지배 본능 때문입니다!\n"
            "이미지프롬프트: Majestic cat on bookshelf, dramatic lighting\n"
        )
        result = parse_script_response(text)
        assert result["scene_count"] == 2
        assert result["scenes"][0]["image_prompt"] == "A cute cat sitting on keyboard, natural light"
        assert result["scenes"][1]["image_prompt"] == "Majestic cat on bookshelf, dramatic lighting"
        assert result["scenes"][0]["narration"] == "고양이가 왜 키보드를 좋아할까요?"

    def test_english_format_with_image_prompt(self):
        text = (
            "[Scene 1]: A cat on a keyboard\n"
            "Narration: Why do cats love keyboards?\n"
            "ImagePrompt: Fluffy cat on laptop keyboard, soft lighting\n"
        )
        result = parse_script_response(text)
        assert result["scene_count"] == 1
        assert result["scenes"][0]["image_prompt"] == "Fluffy cat on laptop keyboard, soft lighting"
        assert result["scenes"][0]["narration"] == "Why do cats love keyboards?"

    def test_japanese_format_with_image_prompt(self):
        text = (
            "[シーン 1]: 猫がキーボードの上に座っている\n"
            "ナレーション: 猫はなぜキーボードが好きなのでしょうか？\n"
            "画像プロンプト: Cat sitting on keyboard, cozy atmosphere\n"
        )
        result = parse_script_response(text)
        assert result["scene_count"] == 1
        assert result["scenes"][0]["image_prompt"] == "Cat sitting on keyboard, cozy atmosphere"

    def test_backward_compatible_without_image_prompt(self):
        """기존 형식 (image_prompt 없음)도 정상 파싱되어야 한다."""
        text = (
            "[장면 1]: 고양이\n"
            "나레이션: 안녕하세요\n"
        )
        result = parse_script_response(text)
        assert result["scene_count"] == 1
        assert result["scenes"][0]["image_prompt"] == ""
        assert result["scenes"][0]["narration"] == "안녕하세요"

    def test_narration_without_scene_header(self):
        """장면 헤더 없이 나레이션만 있는 경우 자동 장면 생성."""
        text = "나레이션: 테스트 문장입니다\n"
        result = parse_script_response(text)
        assert result["scene_count"] == 1
        assert result["scenes"][0]["narration"] == "테스트 문장입니다"
        assert result["scenes"][0]["image_prompt"] == ""

    def test_multiline_narration(self):
        text = (
            "[장면 1]: 시작\n"
            "나레이션: 첫째 줄\n"
            "둘째 줄 이어서\n"
            "이미지프롬프트: A beautiful scene\n"
        )
        result = parse_script_response(text)
        assert "첫째 줄" in result["scenes"][0]["narration"]
        assert "둘째 줄 이어서" in result["scenes"][0]["narration"]
        assert result["scenes"][0]["image_prompt"] == "A beautiful scene"

    def test_multiline_image_prompt(self):
        text = (
            "[장면 1]: 시작\n"
            "나레이션: 안녕\n"
            "이미지프롬프트: A beautiful sunset over the ocean,\n"
            "golden hour, dramatic clouds, photorealistic\n"
        )
        result = parse_script_response(text)
        prompt = result["scenes"][0]["image_prompt"]
        assert "sunset" in prompt
        assert "photorealistic" in prompt

    def test_scene_prefix_variations(self):
        """Scene 헤더의 다양한 형식 인식."""
        text = "Scene 1: test\nNarration: hello\n"
        result = parse_script_response(text)
        assert result["scene_count"] == 1

    def test_image_prompt_prefix_variations(self):
        """image_prompt 다양한 형식 인식."""
        text = (
            "[Scene 1]: test\n"
            "Narration: hello\n"
            "Image Prompt: a cat in space\n"
        )
        result = parse_script_response(text)
        assert result["scenes"][0]["image_prompt"] == "a cat in space"


# --- Extra instructions ---

class TestBuildExtraInstructions:
    def test_empty_config(self):
        result = _build_extra_instructions({}, "ko", LANG_LABELS["ko"])
        assert result == ""

    def test_tone_ko(self):
        result = _build_extra_instructions(
            {"tone": "calm"}, "ko", LANG_LABELS["ko"],
        )
        assert "차분" in result

    def test_tone_en(self):
        result = _build_extra_instructions(
            {"tone": "calm"}, "en", LANG_LABELS["en"],
        )
        assert "calm" in result

    def test_auto_tone_ignored(self):
        result = _build_extra_instructions(
            {"tone": "auto"}, "ko", LANG_LABELS["ko"],
        )
        assert result == ""

    def test_reference_script(self):
        result = _build_extra_instructions(
            {"reference_script": "sample text"}, "ko", LANG_LABELS["ko"],
        )
        assert "sample text" in result
