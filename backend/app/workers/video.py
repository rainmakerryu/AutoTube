import httpx

from app.celery_app import celery_app

SHORTS_RESOLUTION = (1080, 1920)
LONGFORM_RESOLUTION = (1920, 1080)
DEFAULT_FPS = 30
DEFAULT_IMAGE_DURATION_SECONDS = 5.0
MIN_IMAGE_DURATION_SECONDS = 2.0
MAX_IMAGE_DURATION_SECONDS = 15.0
FADE_DURATION_SECONDS = 0.5
KEN_BURNS_ZOOM_FACTOR = 1.15
SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "webp"}
SUPPORTED_AUDIO_FORMATS = {"mp3", "wav", "m4a", "aac"}

PAN_DIRECTIONS = ["left", "right", "up", "down"]
DOWNLOAD_TIMEOUT_SECONDS = 60.0


def get_resolution(video_type: str) -> tuple[int, int]:
    """Return (width, height) for video type. Raises ValueError for invalid type."""
    if video_type == "shorts":
        return SHORTS_RESOLUTION
    elif video_type == "longform":
        return LONGFORM_RESOLUTION
    raise ValueError(
        f"지원하지 않는 video_type입니다: '{video_type}'. "
        "'shorts' 또는 'longform'을 사용하세요."
    )


def calculate_scene_durations(
    total_audio_duration: float,
    scene_count: int,
) -> list[float]:
    """Calculate duration for each scene image based on total audio length.
    Distributes audio duration evenly across scenes, clamped to min/max."""
    raw_duration = total_audio_duration / scene_count
    clamped_duration = max(
        MIN_IMAGE_DURATION_SECONDS,
        min(raw_duration, MAX_IMAGE_DURATION_SECONDS),
    )
    return [clamped_duration] * scene_count


def build_ken_burns_params(
    scene_index: int,
    total_scenes: int,
) -> dict:
    """Generate Ken Burns effect parameters (start_zoom, end_zoom, pan_direction).
    Alternates between zoom-in and zoom-out, varies pan direction."""
    is_zoom_in = scene_index % 2 == 0
    if is_zoom_in:
        start_zoom = 1.0
        end_zoom = KEN_BURNS_ZOOM_FACTOR
    else:
        start_zoom = KEN_BURNS_ZOOM_FACTOR
        end_zoom = 1.0

    pan_direction = PAN_DIRECTIONS[scene_index % len(PAN_DIRECTIONS)]

    return {
        "start_zoom": start_zoom,
        "end_zoom": end_zoom,
        "pan_direction": pan_direction,
    }


def validate_inputs(
    image_paths: list[str],
    audio_path: str | None,
    video_type: str,
) -> list[str]:
    """Validate input files. Returns list of error messages (empty = valid).
    Checks: at least 1 image, valid formats, valid video type."""
    errors: list[str] = []

    if not image_paths:
        errors.append("최소 1개의 이미지가 필요합니다.")

    for path in image_paths:
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext not in SUPPORTED_IMAGE_FORMATS:
            errors.append(
                f"지원하지 않는 이미지 형식입니다: '{path}'. "
                f"지원 형식: {', '.join(sorted(SUPPORTED_IMAGE_FORMATS))}"
            )

    if audio_path is not None:
        ext = audio_path.rsplit(".", 1)[-1].lower() if "." in audio_path else ""
        if ext not in SUPPORTED_AUDIO_FORMATS:
            errors.append(
                f"지원하지 않는 오디오 형식입니다: '{audio_path}'. "
                f"지원 형식: {', '.join(sorted(SUPPORTED_AUDIO_FORMATS))}"
            )

    valid_video_types = {"shorts", "longform"}
    if video_type not in valid_video_types:
        errors.append(
            f"지원하지 않는 비디오 타입입니다: '{video_type}'. "
            f"'shorts' 또는 'longform'을 사용하세요."
        )

    return errors


@celery_app.task(name="pipeline.compose_video")
def compose_video_task(
    project_id: int,
    image_urls: list[str],
    audio_url: str | None,
    video_type: str = "shorts",
) -> dict:
    """Compose video from images and audio.
    Returns dict with video metadata (resolution, duration, fps, scene_count)."""
    resolution = get_resolution(video_type)
    scene_count = len(image_urls)

    image_paths: list[str] = []
    for url in image_urls:
        response = httpx.get(url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
        response.raise_for_status()
        image_paths.append(url)

    total_audio_duration = DEFAULT_IMAGE_DURATION_SECONDS * scene_count
    if audio_url is not None:
        response = httpx.get(audio_url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
        response.raise_for_status()

    scene_durations = calculate_scene_durations(total_audio_duration, scene_count)
    total_duration = sum(scene_durations)

    return {
        "project_id": project_id,
        "resolution": resolution,
        "duration": total_duration,
        "fps": DEFAULT_FPS,
        "scene_count": scene_count,
        "video_type": video_type,
    }
