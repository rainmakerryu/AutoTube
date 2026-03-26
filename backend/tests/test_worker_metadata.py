import pytest

from app.workers.metadata import (
    build_metadata_prompt,
    parse_metadata_response,
    validate_metadata,
    build_metadata_api_request,
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_TAGS,
    MAX_TAG_LENGTH,
)


def test_build_metadata_prompt_shorts_ko():
    prompt = build_metadata_prompt(
        script_text="커피에 대한 놀라운 사실 5가지를 소개합니다.",
        video_type="shorts",
        language="ko",
    )
    assert "커피" in prompt
    assert "shorts" in prompt.lower() or "쇼츠" in prompt


def test_build_metadata_prompt_longform_en():
    prompt = build_metadata_prompt(
        script_text="Today we explore the history of coffee.",
        video_type="longform",
        language="en",
    )
    assert "coffee" in prompt.lower()
    assert "longform" in prompt.lower() or "긴" in prompt


def test_parse_metadata_response_valid_json():
    raw = '{"title": "커피의 비밀", "description": "커피에 대한 영상입니다.", "tags": ["커피", "카페인"]}'
    result = parse_metadata_response(raw)
    assert result["title"] == "커피의 비밀"
    assert result["description"] == "커피에 대한 영상입니다."
    assert result["tags"] == ["커피", "카페인"]


def test_parse_metadata_response_invalid_json():
    raw = "이것은 JSON이 아닌 일반 텍스트입니다."
    result = parse_metadata_response(raw)
    assert result["description"] == raw
    assert "title" in result
    assert "tags" in result


def test_validate_metadata_within_limits():
    metadata = {
        "title": "짧은 제목",
        "description": "짧은 설명",
        "tags": ["태그1", "태그2"],
    }
    result = validate_metadata(metadata)
    assert result == metadata


def test_validate_metadata_truncates():
    metadata = {
        "title": "T" * 200,
        "description": "D" * 6000,
        "tags": [f"tag{i}" for i in range(50)],
    }
    result = validate_metadata(metadata)
    assert len(result["title"]) == MAX_TITLE_LENGTH
    assert len(result["description"]) == MAX_DESCRIPTION_LENGTH
    assert len(result["tags"]) == MAX_TAGS
    for tag in result["tags"]:
        assert len(tag) <= MAX_TAG_LENGTH


def test_validate_metadata_empty_tags():
    metadata = {
        "title": "제목",
        "description": "설명",
        "tags": [],
    }
    result = validate_metadata(metadata)
    assert result["tags"] == []


def test_build_metadata_api_request_openai():
    req = build_metadata_api_request(
        prompt="test prompt",
        provider="openai",
        api_key="sk-test-key",
    )
    assert req["url"] == "https://api.openai.com/v1/chat/completions"
    assert "Bearer sk-test-key" in req["headers"]["Authorization"]
    assert req["json"]["messages"][0]["content"] == "test prompt"


def test_build_metadata_api_request_claude():
    req = build_metadata_api_request(
        prompt="test prompt",
        provider="claude",
        api_key="sk-ant-test",
    )
    assert req["url"] == "https://api.anthropic.com/v1/messages"
    assert req["headers"]["x-api-key"] == "sk-ant-test"


def test_build_metadata_api_request_invalid():
    with pytest.raises(ValueError, match="지원하지 않는"):
        build_metadata_api_request("prompt", "invalid", "key")
