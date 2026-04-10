from app.workers.subtitle import (
    format_srt_timestamp,
    format_ass_timestamp,
    build_whisper_request,
    parse_whisper_response,
    segments_to_srt,
    segments_to_ass,
    split_long_subtitle,
    generate_script_based_subtitles,
    _build_burnin_style,
    WHISPER_API_URL,
    MAX_SUBTITLE_LINE_LENGTH,
    ASS_STYLE_PRESETS,
    ASS_POSITION_ALIGNMENT,
    BURNIN_STYLE_COLORS,
    DEFAULT_SCENE_DURATION_SECONDS,
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


# --- ASS format tests ---


def test_format_ass_timestamp_zero():
    assert format_ass_timestamp(0.0) == "0:00:00.00"


def test_format_ass_timestamp_with_minutes():
    assert format_ass_timestamp(65.5) == "0:01:05.50"


def test_format_ass_timestamp_with_hours():
    assert format_ass_timestamp(3661.0) == "1:01:01.00"


def test_segments_to_ass_contains_header():
    segments = [{"start": 0.0, "end": 2.5, "text": "테스트"}]
    ass = segments_to_ass(segments)
    assert "[Script Info]" in ass
    assert "[V4+ Styles]" in ass
    assert "[Events]" in ass
    assert "Dialogue:" in ass


def test_segments_to_ass_default_style():
    segments = [{"start": 1.0, "end": 3.0, "text": "안녕"}]
    ass = segments_to_ass(segments, style_id="youtube")
    assert "Style: Default,Arial," in ass
    assert "Dialogue: 0," in ass
    assert "안녕" in ass


def test_segments_to_ass_all_presets():
    segments = [{"start": 0.0, "end": 1.0, "text": "test"}]
    for style_id in ASS_STYLE_PRESETS:
        ass = segments_to_ass(segments, style_id=style_id)
        assert "[Events]" in ass
        assert "test" in ass


def test_segments_to_ass_position_alignment():
    segments = [{"start": 0.0, "end": 1.0, "text": "pos test"}]
    for position, alignment in ASS_POSITION_ALIGNMENT.items():
        ass = segments_to_ass(segments, position=position)
        assert f",{alignment},20,20,40,1" in ass


def test_segments_to_ass_custom_font_size():
    segments = [{"start": 0.0, "end": 1.0, "text": "big"}]
    ass = segments_to_ass(segments, font_size=72)
    assert ",72," in ass


# --- Script-based subtitles ---


def test_generate_script_based_subtitles():
    scenes = [
        {"narration": "첫 번째 장면입니다."},
        {"narration": "두 번째 장면입니다."},
    ]
    segments = generate_script_based_subtitles(scenes)
    assert len(segments) == 2
    assert segments[0]["text"] == "첫 번째 장면입니다."
    assert segments[0]["start"] == 0.0
    assert segments[0]["end"] == DEFAULT_SCENE_DURATION_SECONDS
    assert segments[1]["start"] == DEFAULT_SCENE_DURATION_SECONDS


def test_generate_script_based_subtitles_skips_empty():
    scenes = [
        {"narration": "있는 자막"},
        {"narration": ""},
        {"narration": "   "},
        {"narration": "마지막 자막"},
    ]
    segments = generate_script_based_subtitles(scenes)
    assert len(segments) == 2
    assert segments[0]["text"] == "있는 자막"
    assert segments[1]["text"] == "마지막 자막"


def test_generate_script_based_subtitles_empty_scenes():
    segments = generate_script_based_subtitles([])
    assert segments == []


# --- Burn-in style builder ---


def test_build_burnin_style_youtube():
    style = _build_burnin_style({}, "youtube")
    assert style["color"] == "white"
    assert style["stroke_color"] == "black"
    assert style["font_size"] == 36
    assert style["position"] == "bottom"


def test_build_burnin_style_yellow_bold():
    style = _build_burnin_style({}, "yellow_bold")
    assert style["color"] == "yellow"
    assert style["stroke_width"] == 2


def test_build_burnin_style_neon_green():
    style = _build_burnin_style({}, "neon_green")
    assert style["color"] == "#39FF14"


def test_build_burnin_style_custom_config():
    config = {"font_size": 48, "position": "top"}
    style = _build_burnin_style(config, "youtube")
    assert style["font_size"] == 48
    assert style["position"] == "top"


def test_build_burnin_style_unknown_falls_back_to_youtube():
    style = _build_burnin_style({}, "unknown_style")
    assert style["color"] == "white"
    assert style["stroke_color"] == "black"


def test_all_burnin_presets_have_required_keys():
    for style_id in BURNIN_STYLE_COLORS:
        style = _build_burnin_style({}, style_id)
        assert "color" in style
        assert "stroke_color" in style
        assert "stroke_width" in style
        assert "font_size" in style
        assert "position" in style
