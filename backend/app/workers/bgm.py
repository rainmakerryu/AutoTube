from __future__ import annotations

import os
import tempfile

import httpx

from app.celery_app import celery_app
from app.services.storage import StorageService, build_storage_key, save_local, save_to_output_dir

# Try importing moviepy (v2.x removed moviepy.editor)
try:
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False

BGM_DEFAULT_VOLUME = 0.15
BGM_MAX_VOLUME = 0.5
DOWNLOAD_TIMEOUT_SECONDS = 60.0
OUTPUT_FILENAME = "output_bgm.mp4"
AUDIO_CONTENT_TYPE = "video/mp4"

BGM_MOODS = {
    "calm": "calm ambient piano background music",
    "happy": "happy upbeat cheerful background music",
    "dramatic": "dramatic cinematic suspense background music",
    "corporate": "corporate professional business background music",
    "cinematic": "cinematic orchestral epic background music",
    "upbeat": "energetic pop dance background music",
}

BGM_LIBRARY_DIR = os.path.join(os.path.dirname(__file__), "bgm_library")


def _get_storage() -> StorageService | None:
    endpoint = os.environ.get("R2_ENDPOINT")
    access_key = os.environ.get("R2_ACCESS_KEY")
    secret_key = os.environ.get("R2_SECRET_KEY")
    bucket = os.environ.get("R2_BUCKET")
    if not all([endpoint, access_key, secret_key, bucket]):
        return None
    return StorageService(endpoint, access_key, secret_key, bucket)


def _upload_video(project_id: int, video_data: bytes) -> str | None:
    key = build_storage_key(project_id, "bgm", OUTPUT_FILENAME)
    storage = _get_storage()
    if storage is not None:
        url = storage.upload_file(key, video_data, AUDIO_CONTENT_TYPE)
    else:
        url = save_local(key, video_data)
    save_to_output_dir(project_id, OUTPUT_FILENAME, video_data)
    return url


def _download_file(url: str) -> bytes:
    response = httpx.get(url, timeout=DOWNLOAD_TIMEOUT_SECONDS, follow_redirects=True)
    response.raise_for_status()
    return response.content


def _get_bgm_audio_path(mood: str) -> str | None:
    """Get path to bundled BGM file for the given mood."""
    if not os.path.isdir(BGM_LIBRARY_DIR):
        return None
    filename = f"{mood}.mp3"
    filepath = os.path.join(BGM_LIBRARY_DIR, filename)
    if os.path.isfile(filepath):
        return filepath
    # Fallback to calm if requested mood not found
    fallback = os.path.join(BGM_LIBRARY_DIR, "calm.mp3")
    return fallback if os.path.isfile(fallback) else None


def mix_bgm_into_video(video_path: str, bgm_path: str, volume: float) -> str:
    """Mix BGM audio into existing video at reduced volume. Returns path to output."""
    if not MOVIEPY_AVAILABLE:
        raise ValueError(
            "moviepy 패키지가 설치되지 않았습니다. "
            "'pip install moviepy'로 설치하세요."
        )

    output_path = os.path.join(tempfile.mkdtemp(), OUTPUT_FILENAME)

    video = VideoFileClip(video_path)
    bgm = AudioFileClip(bgm_path)

    # Loop BGM to match video duration
    if bgm.duration < video.duration:
        loops_needed = int(video.duration / bgm.duration) + 1
        try:
            from moviepy import concatenate_audioclips
        except ImportError:
            from moviepy.editor import concatenate_audioclips
        bgm = concatenate_audioclips([bgm] * loops_needed)

    # Trim BGM to video duration and reduce volume (moviepy 2.x API)
    bgm = bgm.subclipped(0, video.duration).with_volume_scaled(volume)

    # Mix original audio with BGM
    if video.audio is not None:
        mixed_audio = CompositeAudioClip([video.audio, bgm])
    else:
        mixed_audio = bgm

    final_video = video.with_audio(mixed_audio)
    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )

    # Cleanup
    video.close()
    bgm.close()

    return output_path


@celery_app.task(name="pipeline.add_bgm")
def add_bgm_task(
    project_id: int,
    video_url: str,
    mood: str = "calm",
    provider: str = "library",
    api_key: str | None = None,
    volume: float = BGM_DEFAULT_VOLUME,
) -> dict:
    """Add background music to the video."""
    # Clamp volume
    volume = max(0.0, min(volume, BGM_MAX_VOLUME))

    # Get BGM audio
    bgm_path = _get_bgm_audio_path(mood)
    if bgm_path is None:
        # No BGM library available - return original video unchanged
        return {
            "video_url": video_url,
            "bgm_mood": mood,
            "bgm_volume": volume,
            "bgm_applied": False,
            "message": "BGM 라이브러리가 없어 원본 영상을 유지합니다.",
        }

    # Download video
    video_data = _download_file(video_url)
    video_tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    video_tmp.write(video_data)
    video_tmp.close()

    try:
        # Mix BGM
        output_path = mix_bgm_into_video(video_tmp.name, bgm_path, volume)

        # Read and upload result
        with open(output_path, "rb") as f:
            result_data = f.read()

        result_url = _upload_video(project_id, result_data)

        return {
            "video_url": result_url,
            "bgm_mood": mood,
            "bgm_volume": volume,
            "bgm_applied": True,
        }
    finally:
        os.unlink(video_tmp.name)
