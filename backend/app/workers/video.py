from __future__ import annotations

import base64
import io
import os
import shutil
import tempfile

import httpx
from PIL import Image

from app.celery_app import celery_app
from app.services.storage import StorageService, build_storage_key

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
VIDEO_FILENAME = "output.mp4"
VIDEO_CONTENT_TYPE = "video/mp4"
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"


def get_resolution(video_type: str) -> tuple[int, int]:
    """Return (width, height) for video type."""
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
    """Calculate duration for each scene based on total audio length."""
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
    """Generate Ken Burns effect parameters (start_zoom, end_zoom, pan_direction)."""
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


def _is_downloadable_url(value: str | None) -> bool:
    """Check if the value is an HTTP(S) URL that can be downloaded."""
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _decode_image(value: str) -> bytes:
    """HTTP URL 또는 base64 문자열에서 이미지 bytes를 가져온다."""
    if _is_downloadable_url(value):
        resp = httpx.get(value, timeout=DOWNLOAD_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.content
    # base64 (data:image/png;base64,... 또는 raw base64)
    data = value
    if data.startswith("data:"):
        data = data.split(",", 1)[1]
    return base64.b64decode(data)


def _prepare_image(
    image_bytes: bytes,
    resolution: tuple[int, int],
    output_path: str,
) -> str:
    """이미지를 target resolution에 맞게 center-crop + resize 후 저장."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    target_w, target_h = resolution
    target_ratio = target_w / target_h

    # Center crop to target aspect ratio
    src_w, src_h = img.size
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # 원본이 더 넓음 — 좌우 자르기
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    elif src_ratio < target_ratio:
        # 원본이 더 높음 — 상하 자르기
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))

    img = img.resize((target_w, target_h), Image.LANCZOS)
    img.save(output_path, "PNG")
    return output_path


def _get_storage() -> StorageService | None:
    """R2 스토리지 서비스를 환경변수에서 초기화."""
    endpoint = os.environ.get("R2_ENDPOINT")
    access_key = os.environ.get("R2_ACCESS_KEY")
    secret_key = os.environ.get("R2_SECRET_KEY")
    bucket = os.environ.get("R2_BUCKET")
    if not all([endpoint, access_key, secret_key, bucket]):
        return None
    return StorageService(endpoint, access_key, secret_key, bucket)


def _apply_ken_burns(clip, params: dict, resolution: tuple[int, int]):
    """Ken Burns (zoom + pan) 효과를 moviepy clip에 적용.

    Returns a new clip with zoom/pan effect via make_frame.
    """
    import numpy as np

    start_zoom = params["start_zoom"]
    end_zoom = params["end_zoom"]
    duration = clip.duration
    w, h = resolution

    original_frame = clip.get_frame(0)

    def make_frame(t):
        progress = t / duration if duration > 0 else 0
        zoom = start_zoom + (end_zoom - start_zoom) * progress

        # 줌된 크기에서 중앙 crop
        zh = int(h / zoom)
        zw = int(w / zoom)
        y_offset = (h - zh) // 2
        x_offset = (w - zw) // 2

        cropped = original_frame[y_offset:y_offset + zh, x_offset:x_offset + zw]

        # resize back to target resolution
        from PIL import Image as PILImage
        pil_img = PILImage.fromarray(cropped)
        pil_img = pil_img.resize((w, h), PILImage.LANCZOS)
        return np.array(pil_img)

    from moviepy import VideoClip
    return VideoClip(make_frame, duration=duration).with_fps(clip.fps or DEFAULT_FPS)


@celery_app.task(name="pipeline.compose_video")
def compose_video_task(
    project_id: int,
    image_urls: list[str | None],
    audio_url: str | None,
    video_type: str = "shorts",
) -> dict:
    """이미지와 오디오로 실제 영상을 합성한다.

    1. 이미지 다운로드/디코딩 + resize
    2. moviepy ImageClip + Ken Burns 효과
    3. crossfade 전환으로 concat
    4. 오디오 합성
    5. R2 업로드
    """
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

    resolution = get_resolution(video_type)

    # None 필터링
    valid_images = [url for url in image_urls if url is not None]
    scene_count = len(valid_images)

    if scene_count == 0:
        raise ValueError(
            "유효한 이미지가 없습니다. 이미지 생성 단계를 다시 실행하세요."
        )

    work_dir = tempfile.mkdtemp(prefix="autotube_video_")
    try:
        # 1. 이미지 다운로드 + resize
        image_paths: list[str] = []
        for i, img_data in enumerate(valid_images):
            img_bytes = _decode_image(img_data)
            img_path = os.path.join(work_dir, f"scene_{i:03d}.png")
            _prepare_image(img_bytes, resolution, img_path)
            image_paths.append(img_path)

        # 2. 오디오 다운로드 (있으면)
        audio_path = None
        audio_duration = None
        if _is_downloadable_url(audio_url):
            audio_path = os.path.join(work_dir, "audio.mp3")
            resp = httpx.get(audio_url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
            resp.raise_for_status()
            with open(audio_path, "wb") as f:
                f.write(resp.content)
            audio_clip_tmp = AudioFileClip(audio_path)
            audio_duration = audio_clip_tmp.duration
            audio_clip_tmp.close()

        # 3. 장면 duration 계산
        total_audio = audio_duration or (DEFAULT_IMAGE_DURATION_SECONDS * scene_count)
        scene_durations = calculate_scene_durations(total_audio, scene_count)

        # 4. 장면 clips 생성
        clips = []
        for i, (img_path, duration) in enumerate(zip(image_paths, scene_durations)):
            clip = ImageClip(img_path).with_duration(duration).with_fps(DEFAULT_FPS)

            # Ken Burns 효과
            kb_params = build_ken_burns_params(i, scene_count)
            clip = _apply_ken_burns(clip, kb_params, resolution)

            clips.append(clip)

        # 5. Crossfade concat
        if len(clips) > 1:
            # crossfadein/crossfadeout 을 사용한 부드러운 전환
            transition_clips = [clips[0]]
            for clip in clips[1:]:
                transition_clips.append(clip.crossfadein(FADE_DURATION_SECONDS))
            final_video = concatenate_videoclips(
                transition_clips,
                method="compose",
                padding=-FADE_DURATION_SECONDS,
            )
        else:
            final_video = clips[0]

        # 6. 오디오 합성
        if audio_path:
            audio_clip = AudioFileClip(audio_path)
            # 영상 길이에 맞춰 오디오 자르기
            if audio_clip.duration > final_video.duration:
                audio_clip = audio_clip.subclipped(0, final_video.duration)
            final_video = final_video.with_audio(audio_clip)

        # 7. 영상 파일 렌더링
        output_path = os.path.join(work_dir, VIDEO_FILENAME)
        final_video.write_videofile(
            output_path,
            fps=DEFAULT_FPS,
            codec=VIDEO_CODEC,
            audio_codec=AUDIO_CODEC if audio_path else None,
            logger=None,  # Celery 워커에서 tqdm 출력 억제
        )

        total_duration = final_video.duration

        # clip 리소스 해제
        final_video.close()
        for clip in clips:
            clip.close()

        # 8. R2 업로드
        video_url = None
        storage = _get_storage()
        if storage:
            with open(output_path, "rb") as f:
                video_data = f.read()
            key = build_storage_key(project_id, "video", VIDEO_FILENAME)
            video_url = storage.upload_file(key, video_data, VIDEO_CONTENT_TYPE)

        return {
            "video_url": video_url,
            "resolution": list(resolution),
            "duration": round(total_duration, 2),
            "fps": DEFAULT_FPS,
            "scene_count": scene_count,
            "video_type": video_type,
        }
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
