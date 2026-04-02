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
) -> dict:
    """Generate SRT subtitles.

    If scenes are provided and no api_key, generates subtitles from script text.
    Otherwise uses Whisper API for speech-to-text.
    """
    # Script-based fallback (free, no API needed)
    if scenes and not api_key:
        segments = generate_script_based_subtitles(scenes)
        srt_content = segments_to_srt(segments)
        subtitle_url = _save_srt(project_id, srt_content)
        return {
            "srt_content": srt_content,
            "subtitle_url": subtitle_url,
            "segment_count": len(segments),
            "provider": "script",
        }

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
    srt_content = segments_to_srt(segments)
    subtitle_url = _save_srt(project_id, srt_content)

    return {
        "srt_content": srt_content,
        "subtitle_url": subtitle_url,
        "segment_count": len(segments),
        "provider": "openai",
    }
