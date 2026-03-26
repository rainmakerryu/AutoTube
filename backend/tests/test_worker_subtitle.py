from app.workers.subtitle import (
    format_srt_timestamp,
    build_whisper_request,
    parse_whisper_response,
    segments_to_srt,
    split_long_subtitle,
    WHISPER_API_URL,
    MAX_SUBTITLE_LINE_LENGTH,
)


def test_format_srt_timestamp_zero():
    assert format_srt_timestamp(0.0) == "00:00:00,000"


def test_format_srt_timestamp_with_minutes():
    assert format_srt_timestamp(65.5) == "00:01:05,500"


def test_format_srt_timestamp_with_hours():
    assert format_srt_timestamp(3661.123) == "01:01:01,123"


def test_build_whisper_request():
    req = build_whisper_request(api_key="sk-test-key", language="ko")
    assert req["url"] == WHISPER_API_URL
    assert "Bearer sk-test-key" in req["headers"]["Authorization"]
    assert req["language"] == "ko"


def test_parse_whisper_response():
    response_json = {
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "안녕하세요."},
            {"start": 2.5, "end": 5.0, "text": "오늘의 영상입니다."},
        ]
    }
    segments = parse_whisper_response(response_json)
    assert len(segments) == 2
    assert segments[0]["start"] == 0.0
    assert segments[0]["end"] == 2.5
    assert segments[0]["text"] == "안녕하세요."
    assert segments[1]["text"] == "오늘의 영상입니다."


def test_parse_whisper_response_empty():
    segments = parse_whisper_response({})
    assert segments == []


def test_segments_to_srt():
    segments = [
        {"start": 0.0, "end": 2.5, "text": "안녕하세요."},
        {"start": 2.5, "end": 5.0, "text": "오늘의 영상입니다."},
    ]
    srt = segments_to_srt(segments)
    lines = srt.strip().split("\n")
    assert lines[0] == "1"
    assert lines[1] == "00:00:00,000 --> 00:00:02,500"
    assert lines[2] == "안녕하세요."
    assert lines[4] == "2"
    assert lines[5] == "00:00:02,500 --> 00:00:05,000"
    assert lines[6] == "오늘의 영상입니다."


def test_segments_to_srt_empty():
    assert segments_to_srt([]) == ""


def test_split_long_subtitle_short():
    short_text = "짧은 자막입니다."
    result = split_long_subtitle(short_text)
    assert result == [short_text]


def test_split_long_subtitle_long():
    long_text = "This is a very long subtitle text that should be split into multiple lines at word boundaries"
    assert len(long_text) > MAX_SUBTITLE_LINE_LENGTH
    result = split_long_subtitle(long_text)
    assert len(result) > 1
    for line in result:
        assert len(line) <= MAX_SUBTITLE_LINE_LENGTH
