import pytest

from app.workers.tts import build_tts_request, ELEVENLABS_DEFAULT_VOICE_ID


def test_build_tts_request_elevenlabs():
    req = build_tts_request(
        text="안녕하세요, 오늘의 영상을 시작하겠습니다.",
        provider="elevenlabs",
        api_key="el-test-key",
    )
    assert "api.elevenlabs.io" in req["url"]
    assert req["headers"]["xi-api-key"] == "el-test-key"
    assert req["json"]["text"] == "안녕하세요, 오늘의 영상을 시작하겠습니다."


def test_build_tts_request_elevenlabs_custom_voice():
    req = build_tts_request(
        text="test",
        provider="elevenlabs",
        api_key="key",
        voice_id="custom_voice_123",
    )
    assert "custom_voice_123" in req["url"]


def test_build_tts_request_elevenlabs_default_voice():
    req = build_tts_request(
        text="test",
        provider="elevenlabs",
        api_key="key",
    )
    assert ELEVENLABS_DEFAULT_VOICE_ID in req["url"]


def test_build_tts_request_openai():
    req = build_tts_request(
        text="Hello world",
        provider="openai",
        api_key="sk-test-key",
    )
    assert "api.openai.com" in req["url"]
    assert req["json"]["input"] == "Hello world"
    assert req["json"]["model"] == "tts-1"


def test_build_tts_request_openai_custom_voice():
    req = build_tts_request(
        text="test",
        provider="openai",
        api_key="key",
        voice_id="nova",
    )
    assert req["json"]["voice"] == "nova"


def test_build_tts_request_invalid_provider():
    with pytest.raises(ValueError, match="지원하지 않는"):
        build_tts_request("text", "invalid", "key")


def test_split_text_for_tts_short():
    from app.workers.tts import split_text_for_tts

    chunks = split_text_for_tts("짧은 텍스트입니다.")
    assert len(chunks) == 1
    assert chunks[0] == "짧은 텍스트입니다."


def test_split_text_for_tts_long():
    from app.workers.tts import split_text_for_tts, MAX_TTS_CHUNK_LENGTH

    long_text = "이것은 테스트 문장입니다. " * 500
    chunks = split_text_for_tts(long_text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= MAX_TTS_CHUNK_LENGTH
