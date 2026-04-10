from __future__ import annotations

import os
import tempfile

import httpx

from app.celery_app import celery_app
from app.services.storage import build_storage_key, save_local, save_to_output_dir

WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-1"
API_TIMEOUT_SECONDS = 120.0
DOWNLOAD_TIMEOUT_SECONDS = 60.0
MAX_SUBTITLE_LINE_LENGTH = 42
DEFAULT_LANGUAGE = "ko"
BURNIN_OUTPUT_FILENAME = "output.mp4"
BURNIN_CONTENT_TYPE = "video/mp4"


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


# moviepy TextClip에서 사용할 색상 매핑 (ASS 프리셋 → CSS 색상)
BURNIN_STYLE_COLORS: dict[str, dict] = {
    "youtube": {"color": "white", "stroke_color": "black", "stroke_width": 0},
    "yellow_bold": {"color": "yellow", "stroke_color": "black", "stroke_width": 2},
    "white_outline": {"color": "white", "stroke_color": "black", "stroke_width": 3},
    "neon_green": {"color": "#39FF14", "stroke_color": "black", "stroke_width": 2},
    "cinema": {"color": "white", "stroke_color": "black", "stroke_width": 0},
}


def _build_burnin_style(config: dict, style_id: str) -> dict:
    """자막 번인용 스타일 설정을 빌드."""
    colors = BURNIN_STYLE_COLORS.get(style_id, BURNIN_STYLE_COLORS["youtube"])
    return {
        "font_size": config.get("font_size", 36),
        "color": colors["color"],
        "stroke_color": colors["stroke_color"],
        "stroke_width": colors.get("stroke_width", 2),
        "position": config.get("position", "bottom"),
    }


def _download_file(url: str) -> bytes:
    """URL에서 파일을 다운로드."""
    response = httpx.get(url, timeout=DOWNLOAD_TIMEOUT_SECONDS, follow_redirects=True)
    response.raise_for_status()
    return response.content


def _burn_subtitles_moviepy(video_path: str, segments: list[dict], style_cfg: dict) -> str:
    """moviepy TextClip으로 자막을 영상에 번인. 결과 파일 경로 반환."""
    from moviepy import VideoFileClip, TextClip, CompositeVideoClip

    output_path = os.path.join(tempfile.mkdtemp(), BURNIN_OUTPUT_FILENAME)

    video = VideoFileClip(video_path)
    font_size = style_cfg.get("font_size", 36)
    color = style_cfg.get("color", "white")
    stroke_color = style_cfg.get("stroke_color", "black")
    stroke_width = style_cfg.get("stroke_width", 2)
    position = style_cfg.get("position", "bottom")

    # 위치 매핑
    pos_map = {
        "bottom": ("center", video.h - 80),
        "center": ("center", "center"),
        "top": ("center", 40),
    }
    pos = pos_map.get(position, pos_map["bottom"])

    text_clips = []
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        start = seg["start"]
        end = seg["end"]
        duration = end - start
        if duration <= 0:
            continue

        tc = TextClip(
            text=text,
            font_size=font_size,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            font="Arial",
            method="caption",
            size=(video.w - 40, None),
        )
        tc = tc.with_position(pos).with_start(start).with_duration(duration)
        text_clips.append(tc)

    if text_clips:
        final = CompositeVideoClip([video] + text_clips)
    else:
        final = video

    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )
    video.close()
    for tc in text_clips:
        tc.close()

    return output_path


def _save_burnin_video(project_id: int, video_data: bytes) -> str:
    """자막이 번인된 영상을 저장하고 URL 반환."""
    key = build_storage_key(project_id, "subtitle", BURNIN_OUTPUT_FILENAME)
    url = save_local(key, video_data)
    # 최종 출력 디렉토리에도 output.mp4로 저장 (덮어쓰기)
    save_to_output_dir(project_id, BURNIN_OUTPUT_FILENAME, video_data)
    return url


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


def _burnin_subtitle_to_video(
    project_id: int,
    video_url: str,
    segments: list[dict],
    style_cfg: dict,
) -> str | None:
    """영상을 다운로드하고 자막을 번인한 뒤 업로드. URL 반환."""
    video_data = _download_file(video_url)
    video_tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    video_tmp.write(video_data)
    video_tmp.close()

    try:
        output_path = _burn_subtitles_moviepy(video_tmp.name, segments, style_cfg)
        with open(output_path, "rb") as f:
            result_data = f.read()
        return _save_burnin_video(project_id, result_data)
    finally:
        os.unlink(video_tmp.name)


@celery_app.task(name="pipeline.generate_subtitles")
def generate_subtitles_task(
    project_id: int,
    audio_url: str,
    api_key: str,
    language: str = "ko",
    scenes: list[dict] | None = None,
    subtitle_config: dict | None = None,
    video_url: str | None = None,
) -> dict:
    """Generate subtitles and burn them into the video.

    If subtitle_config is provided with a style, generates ASS format.
    If scenes are provided and no api_key, generates from script text.
    Otherwise uses Whisper API for speech-to-text.
    After generating subtitles, burns them into the video using ffmpeg.
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

        result = {
            "srt_content": srt_content,
            "ass_content": ass_content,
            "subtitle_url": subtitle_url,
            "segment_count": len(segments),
            "provider": provider,
            "format": "ass",
            "style": style_id,
        }

        # 영상에 자막 번인
        if video_url:
            burnin_style = _build_burnin_style(config, style_id)
            burnin_url = _burnin_subtitle_to_video(
                project_id, video_url, segments, burnin_style
            )
            if burnin_url:
                result["video_url"] = burnin_url

        return result

    # SRT 포맷 (기본) — 기본 스타일로 번인
    srt_content = segments_to_srt(segments)
    subtitle_url = _save_subtitle(project_id, srt_content, SRT_FILENAME)

    result = {
        "srt_content": srt_content,
        "subtitle_url": subtitle_url,
        "segment_count": len(segments),
        "provider": provider,
        "format": "srt",
    }

    # SRT인 경우에도 기본 스타일로 번인
    if video_url:
        # ASS 파일도 저장 (호환성)
        ass_for_save = segments_to_ass(segments)
        _save_subtitle(project_id, ass_for_save, ASS_FILENAME)
        burnin_style = _build_burnin_style(config, "youtube")
        burnin_url = _burnin_subtitle_to_video(
            project_id, video_url, segments, burnin_style
        )
        if burnin_url:
            result["video_url"] = burnin_url

    return result
