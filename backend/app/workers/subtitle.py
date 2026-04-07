from __future__ import annotations

import httpx

from app.celery_app import celery_app
from app.services.storage import build_storage_key, save_local, save_to_output_dir

WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-1"
API_TIMEOUT_SECONDS = 120.0
MAX_SUBTITLE_LINE_LENGTH = 42
DEFAULT_LANGUAGE = "ko"


def format_srt_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format: HH:MM:SS,mmm
    Example: 65.5 -> '00:01:05,500'"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_whisper_request(api_key: str, language: str = "ko") -> dict:
    """Build Whisper API request config (url, headers).
    Note: actual file upload happens in the task, this just builds auth/url."""
    return {
        "url": WHISPER_API_URL,
        "headers": {
            "Authorization": f"Bearer {api_key}",
        },
        "language": language,
    }


def parse_whisper_response(response_json: dict) -> list[dict]:
    """Parse Whisper verbose_json response into subtitle segments.
    Each segment: {start: float, end: float, text: str}"""
    raw_segments = response_json.get("segments", [])
    return [
        {
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
        }
        for seg in raw_segments
    ]


def segments_to_srt(segments: list[dict]) -> str:
    """Convert segments to SRT format string.
    Each entry: index, timestamp range, text."""
    if not segments:
        return ""

    entries: list[str] = []
    for idx, seg in enumerate(segments, start=1):
        start_ts = format_srt_timestamp(seg["start"])
        end_ts = format_srt_timestamp(seg["end"])
        text_lines = split_long_subtitle(seg["text"])
        text_block = "\n".join(text_lines)
        entries.append(f"{idx}\n{start_ts} --> {end_ts}\n{text_block}")

    return "\n\n".join(entries) + "\n"


def split_long_subtitle(text: str) -> list[str]:
    """Split subtitle text longer than MAX_SUBTITLE_LINE_LENGTH into multiple lines.
    Split at word boundaries (spaces)."""
    if len(text) <= MAX_SUBTITLE_LINE_LENGTH:
        return [text]

    words = text.split(" ")
    lines: list[str] = []
    current_line = ""

    for word in words:
        candidate = f"{current_line} {word}" if current_line else word
        if len(candidate) <= MAX_SUBTITLE_LINE_LENGTH:
            current_line = candidate
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


DEFAULT_SCENE_DURATION_SECONDS = 5.0
SRT_FILENAME = "subtitle.srt"
ASS_FILENAME = "subtitle.ass"
DEFAULT_ASS_FONT = "Arial"

# ASS subtitle style presets (ASS color format: &HAABBGGRR)
ASS_STYLE_PRESETS: dict[str, dict] = {
    "youtube": {
        "primary_color": "&H00FFFFFF",
        "back_color": "&HCC000000",
        "border_style": 3,
        "outline": 0,
        "bold": 0,
        "shadow": 0,
    },
    "yellow_bold": {
        "primary_color": "&H0000D7FF",
        "back_color": "&H00000000",
        "border_style": 1,
        "outline": 2,
        "bold": 1,
        "shadow": 0,
    },
    "white_outline": {
        "primary_color": "&H00FFFFFF",
        "back_color": "&H00000000",
        "border_style": 1,
        "outline": 3,
        "bold": 0,
        "shadow": 0,
    },
    "neon_green": {
        "primary_color": "&H0014FF39",
        "back_color": "&H00000000",
        "border_style": 1,
        "outline": 2,
        "bold": 1,
        "shadow": 3,
    },
    "cinema": {
        "primary_color": "&H00FFFFFF",
        "back_color": "&H80000000",
        "border_style": 3,
        "outline": 0,
        "bold": 0,
        "shadow": 0,
    },
}

ASS_POSITION_ALIGNMENT: dict[str, int] = {
    "bottom": 2,
    "center": 5,
    "top": 8,
}


def format_ass_timestamp(seconds: float) -> str:
    """Convert seconds to ASS timestamp format: H:MM:SS.cc"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int(round((seconds - int(seconds)) * 100))
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def segments_to_ass(
    segments: list[dict],
    style_id: str = "youtube",
    font_size: int = 36,
    position: str = "bottom",
    outline_width: int = 2,
    opacity: float = 1.0,
) -> str:
    """Convert segments to ASS (Advanced SubStation Alpha) format with style."""
    preset = ASS_STYLE_PRESETS.get(style_id, ASS_STYLE_PRESETS["youtube"])
    alignment = ASS_POSITION_ALIGNMENT.get(position, 2)

    alpha_hex = f"{int((1.0 - opacity) * 255):02X}"
    primary_with_alpha = f"&H{alpha_hex}{preset['primary_color'][4:]}"

    effective_outline = preset.get("outline", outline_width)
    if style_id in ("white_outline", "yellow_bold", "neon_green"):
        effective_outline = outline_width

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1920\n"
        "PlayResY: 1080\n"
        "WrapStyle: 0\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{DEFAULT_ASS_FONT},{font_size},"
        f"{primary_with_alpha},&H000000FF,&H00000000,"
        f"{preset['back_color']},"
        f"{preset.get('bold', 0)},0,0,0,"
        f"100,100,0,0,"
        f"{preset['border_style']},{effective_outline},{preset.get('shadow', 0)},"
        f"{alignment},20,20,40,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    events: list[str] = []
    for seg in segments:
        start_ts = format_ass_timestamp(seg["start"])
        end_ts = format_ass_timestamp(seg["end"])
        text = seg["text"].replace("\n", "\\N")
        events.append(
            f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{text}"
        )

    return header + "\n".join(events) + "\n"


def _save_subtitle(project_id: int, content: str, filename: str) -> str | None:
    """자막 파일을 로컬 media + 사용자 출력 디렉토리에 저장하고 서빙 URL을 반환."""
    content_bytes = content.encode("utf-8")
    key = build_storage_key(project_id, "subtitle", filename)
    url = save_local(key, content_bytes)
    save_to_output_dir(project_id, filename, content_bytes)
    return url


def _save_srt(project_id: int, srt_content: str) -> str | None:
    """SRT 파일을 로컬 media + 사용자 출력 디렉토리에 저장하고 서빙 URL을 반환."""
    srt_bytes = srt_content.encode("utf-8")
    key = build_storage_key(project_id, "subtitle", SRT_FILENAME)
    url = save_local(key, srt_bytes)
    save_to_output_dir(project_id, SRT_FILENAME, srt_bytes)
    return url


def generate_script_based_subtitles(scenes: list[dict]) -> list[dict]:
    """Generate subtitle segments from script scenes (no API needed).

    Each scene's narration becomes a subtitle segment with evenly spaced timing.
    """
    segments: list[dict] = []
    current_time = 0.0

    for scene in scenes:
        narration = scene.get("narration", "").strip()
        if not narration:
            current_time += DEFAULT_SCENE_DURATION_SECONDS
            continue

        duration = DEFAULT_SCENE_DURATION_SECONDS
        segments.append({
            "start": current_time,
            "end": current_time + duration,
            "text": narration,
        })
        current_time += duration

    return segments


@celery_app.task(name="pipeline.generate_subtitles")
def generate_subtitles_task(
    project_id: int,
    audio_url: str,
    api_key: str,
    language: str = "ko",
    scenes: list[dict] | None = None,
    subtitle_config: dict | None = None,
) -> dict:
    """Generate subtitles in SRT or ASS format.

    If subtitle_config is provided with a style, generates ASS format.
    If scenes are provided and no api_key, generates from script text.
    Otherwise uses Whisper API for speech-to-text.
    """
    config = subtitle_config or {}
    style_id = config.get("style", "")
    use_ass = style_id and style_id != "none" and style_id in ASS_STYLE_PRESETS

    # style="none" → 자막 생성 스킵
    if style_id == "none" or config.get("enabled") is False:
        return {
            "srt_content": "",
            "subtitle_url": None,
            "segment_count": 0,
            "provider": "skipped",
            "format": "none",
        }

    # Script-based fallback (free, no API needed)
    if scenes and not api_key:
        segments = generate_script_based_subtitles(scenes)
    else:
        # Whisper API
        audio_response = httpx.get(audio_url, timeout=API_TIMEOUT_SECONDS)
        audio_response.raise_for_status()

        request_config = build_whisper_request(api_key, language)

        response = httpx.post(
            request_config["url"],
            headers=request_config["headers"],
            data={
                "model": WHISPER_MODEL,
                "language": request_config["language"],
                "response_format": "verbose_json",
            },
            files={"file": ("audio.mp3", audio_response.content, "audio/mpeg")},
            timeout=API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        segments = parse_whisper_response(response.json())

    provider = "script" if (scenes and not api_key) else "openai"

    # ASS 포맷 (스타일 적용)
    if use_ass:
        ass_content = segments_to_ass(
            segments,
            style_id=style_id,
            font_size=config.get("font_size", 36),
            position=config.get("position", "bottom"),
            outline_width=config.get("outline_width", 2),
            opacity=config.get("opacity", 1.0),
        )
        subtitle_url = _save_subtitle(project_id, ass_content, ASS_FILENAME)
        # SRT도 함께 저장 (호환성)
        srt_content = segments_to_srt(segments)
        _save_subtitle(project_id, srt_content, SRT_FILENAME)
        return {
            "srt_content": srt_content,
            "ass_content": ass_content,
            "subtitle_url": subtitle_url,
            "segment_count": len(segments),
            "provider": provider,
            "format": "ass",
            "style": style_id,
        }

    # SRT 포맷 (기본)
    srt_content = segments_to_srt(segments)
    subtitle_url = _save_subtitle(project_id, srt_content, SRT_FILENAME)
    return {
        "srt_content": srt_content,
        "subtitle_url": subtitle_url,
        "segment_count": len(segments),
        "provider": provider,
        "format": "srt",
    }
