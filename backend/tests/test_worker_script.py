from app.workers.script import build_script_prompt, parse_script_response


def test_build_prompt_shorts_ko():
    prompt = build_script_prompt(
        topic="커피에 대한 5가지 놀라운 사실",
        video_type="shorts",
        language="ko",
    )
    assert "커피" in prompt
    assert "shorts" in prompt.lower() or "30-60" in prompt


def test_build_prompt_longform_en():
    prompt = build_script_prompt(
        topic="History of coffee",
        video_type="longform",
        language="en",
    )
    assert "coffee" in prompt.lower()
    assert "5-15" in prompt or "longform" in prompt.lower()


def test_parse_script_response_korean():
    raw = """[장면 1]: 커피콩이 빨갛게 익어가는 모습
나레이션: 커피는 원래 에티오피아의 염소가 발견했다고 합니다.

[장면 2]: 핀란드 사람들이 커피를 마시는 모습
나레이션: 세계에서 커피를 가장 많이 마시는 나라는 핀란드입니다.

[장면 3]: 커피잔 클로즈업
나레이션: 커피 한 잔에는 약 95mg의 카페인이 들어있습니다."""

    result = parse_script_response(raw)
    assert result["full_text"] == raw
    assert result["scene_count"] == 3
    assert len(result["scenes"]) == 3
    assert "에티오피아" in result["scenes"][0]["narration"]


def test_parse_script_response_empty():
    result = parse_script_response("")
    assert result["full_text"] == ""
    assert result["scene_count"] == 0
    assert result["scenes"] == []


def test_build_api_request_openai():
    from app.workers.script import build_api_request

    req = build_api_request(
        prompt="test prompt",
        provider="openai",
        api_key="sk-test-key",
    )
    assert req["url"] == "https://api.openai.com/v1/chat/completions"
    assert "Bearer sk-test-key" in req["headers"]["Authorization"]
    assert req["json"]["messages"][0]["content"] == "test prompt"


def test_build_api_request_claude():
    from app.workers.script import build_api_request

    req = build_api_request(
        prompt="test prompt",
        provider="claude",
        api_key="sk-ant-test",
    )
    assert req["url"] == "https://api.anthropic.com/v1/messages"
    assert req["headers"]["x-api-key"] == "sk-ant-test"


def test_build_api_request_invalid_provider():
    from app.workers.script import build_api_request
    import pytest

    with pytest.raises(ValueError, match="지원하지 않는"):
        build_api_request("prompt", "invalid", "key")
