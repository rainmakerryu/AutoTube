import httpx

from app.celery_app import celery_app

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


@celery_app.task(name="pipeline.generate_subtitles")
def generate_subtitles_task(
    project_id: int,
    audio_url: str,
    api_key: str,
    language: str = "ko",
) -> dict:
    """Generate SRT subtitles from audio. Returns dict with srt_content and segment_count."""
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

    return {
        "srt_content": srt_content,
        "segment_count": len(segments),
    }
