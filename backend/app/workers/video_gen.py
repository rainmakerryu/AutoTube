"""ComfyUI 기반 영상 클립 생성 워커 (img2vid + txt2vid).

장면별로 ComfyUI 워크플로우를 실행하여 영상 클립을 생성한다.
- img2vid: 이미 생성된 이미지를 영상 클립으로 변환
- txt2vid: 텍스트 프롬프트에서 직접 영상 클립 생성

생성된 클립은 로컬 저장 후 URL로 반환한다.
"""
from __future__ import annotations

import base64
import logging
import tempfile

from app.celery_app import celery_app as celery
from app.services.storage import build_storage_key, save_local
from app.workers.comfyui_client import (
    COMFYUI_DEFAULT_URL,
    VIDEO_POLL_TIMEOUT,
    ComfyUIError,
    check_comfyui_health,
    download_comfyui_video,
    extract_video_output,
    poll_comfyui_result,
    submit_workflow,
    upload_reference_image,
)
from app.workers.comfyui_video_workflow import (
    DEFAULT_VIDEO_PARAMS,
    build_animatediff_workflow,
    build_cogvideox_img2vid_workflow,
    build_cogvideox_txt2vid_workflow,
    build_svd_workflow,
    build_wan21_img2vid_workflow,
    build_wan21_txt2vid_workflow,
    get_video_resolution,
)

logger = logging.getLogger(__name__)

# --- 모드-모델별 워크플로우 빌더 매핑 ---

IMG2VID_BUILDERS = {
    "animatediff": build_animatediff_workflow,
    "svd": build_svd_workflow,
    "wan21": build_wan21_img2vid_workflow,
    "cogvideox": build_cogvideox_img2vid_workflow,
}

TXT2VID_BUILDERS = {
    "wan21": build_wan21_txt2vid_workflow,
    "cogvideox": build_cogvideox_txt2vid_workflow,
}

VALID_MODES = {"img2vid", "txt2vid"}


def _get_builder(gen_mode: str, model: str):
    """모드와 모델에 맞는 워크플로우 빌더를 반환한다."""
    if gen_mode == "img2vid":
        builder = IMG2VID_BUILDERS.get(model)
        if builder is None:
            supported = ", ".join(IMG2VID_BUILDERS.keys())
            raise ValueError(
                f"img2vid 모드에서 '{model}' 모델은 지원되지 않습니다. "
                f"지원 모델: {supported}"
            )
        return builder
    elif gen_mode == "txt2vid":
        builder = TXT2VID_BUILDERS.get(model)
        if builder is None:
            supported = ", ".join(TXT2VID_BUILDERS.keys())
            raise ValueError(
                f"txt2vid 모드에서 '{model}' 모델은 지원되지 않습니다. "
                f"지원 모델: {supported}"
            )
        return builder
    else:
        raise ValueError(
            f"알 수 없는 생성 모드: '{gen_mode}'. "
            f"지원 모드: {', '.join(VALID_MODES)}"
        )


def _extract_scene_prompt(scene: dict, style: str = "") -> str:
    """장면 데이터에서 영상 생성용 프롬프트를 추출한다."""
    visual = scene.get("image_prompt", "") or scene.get("visual", "")
    narration = scene.get("narration", "")
    prompt = visual or narration
    if style:
        prompt = f"{style}{prompt}"
    return prompt


def _download_image_from_url(url: str) -> bytes:
    """이미지 URL 또는 base64 데이터에서 바이트를 가져온다."""
    import httpx

    if url.startswith("data:"):
        # data:image/png;base64,xxxx
        b64_data = url.split(",", 1)[1] if "," in url else url
        return base64.b64decode(b64_data)
    elif len(url) > 200 and not url.startswith("http"):
        # base64 인코딩된 이미지 (URL이 아닌 경우)
        return base64.b64decode(url)
    else:
        resp = httpx.get(url, timeout=60.0)
        resp.raise_for_status()
        return resp.content


def _calculate_clip_duration(model: str) -> float:
    """모델 기본 파라미터로 클립 길이를 계산한다 (frames / fps)."""
    params = DEFAULT_VIDEO_PARAMS.get(model, {"frames": 16, "fps": 8})
    return params["frames"] / params["fps"]


@celery.task(name="pipeline.generate_video_clips", bind=True)
def generate_video_clips_task(
    self,
    project_id: int,
    scenes: list,
    image_urls: list,
    api_key: str,
    video_type: str,
    gen_mode: str,
    model: str,
    style: str = "",
) -> dict:
    """ComfyUI로 장면별 영상 클립을 생성한다.

    Args:
        project_id: 프로젝트 ID
        scenes: 스크립트 장면 리스트 (image_prompt, narration 등)
        image_urls: 이전 이미지 단계의 출력 (img2vid에서 사용)
        api_key: ComfyUI 서버 URL
        video_type: "shorts" | "long"
        gen_mode: "img2vid" | "txt2vid"
        model: "animatediff" | "svd" | "wan21" | "cogvideox"
        style: 스타일 프롬프트 접두사

    Returns:
        {"video_clip_urls": [...], "clip_durations": [...], "gen_mode": str, "model": str, "scene_count": int}
    """
    base_url = api_key or COMFYUI_DEFAULT_URL

    if not check_comfyui_health(base_url):
        raise ComfyUIError(
            f"ComfyUI 서버에 연결할 수 없습니다: {base_url}. "
            "ComfyUI가 실행 중인지 확인하세요."
        )

    builder = _get_builder(gen_mode, model)
    width, height = get_video_resolution(video_type, model)
    clip_duration = _calculate_clip_duration(model)
    params = DEFAULT_VIDEO_PARAMS.get(model, {})

    video_clip_urls = []
    clip_durations = []

    for i, scene in enumerate(scenes):
        prompt = _extract_scene_prompt(scene, style)
        if not prompt.strip():
            logger.warning("장면 %d에 프롬프트가 없어 건너뜁니다.", i)
            continue

        try:
            workflow = _build_scene_workflow(
                builder=builder,
                gen_mode=gen_mode,
                model=model,
                scene_index=i,
                prompt=prompt,
                image_urls=image_urls,
                base_url=base_url,
                width=width,
                height=height,
                params=params,
            )

            prompt_id = submit_workflow(base_url, workflow)
            outputs = poll_comfyui_result(base_url, prompt_id, timeout=VIDEO_POLL_TIMEOUT)

            video_info = extract_video_output(outputs)
            if video_info is None:
                logger.error("장면 %d: ComfyUI 영상 출력을 찾을 수 없습니다.", i)
                continue

            video_bytes = download_comfyui_video(
                base_url,
                video_info["filename"],
                subfolder=video_info.get("subfolder", ""),
                vid_type=video_info.get("type", "output"),
            )

            key = build_storage_key(project_id, "video_gen", f"clip_{i:03d}.mp4")
            clip_url = save_local(key, video_bytes)
            video_clip_urls.append(clip_url)
            clip_durations.append(clip_duration)

            logger.info("장면 %d 영상 클립 생성 완료: %s", i, clip_url)

        except ComfyUIError as exc:
            logger.error("장면 %d 영상 생성 실패: %s", i, exc)
            continue

    if not video_clip_urls:
        raise ComfyUIError(
            f"프로젝트 {project_id}: 모든 장면의 영상 클립 생성에 실패했습니다."
        )

    return {
        "video_clip_urls": video_clip_urls,
        "clip_durations": clip_durations,
        "gen_mode": gen_mode,
        "model": model,
        "scene_count": len(video_clip_urls),
    }


def _build_scene_workflow(
    *,
    builder,
    gen_mode: str,
    model: str,
    scene_index: int,
    prompt: str,
    image_urls: list,
    base_url: str,
    width: int,
    height: int,
    params: dict,
) -> dict:
    """장면별 워크플로우를 빌드한다."""
    seed = scene_index
    frames = params.get("frames", 16)
    fps = params.get("fps", 8)

    if gen_mode == "img2vid":
        image_filename = _upload_scene_image(
            scene_index, image_urls, base_url,
        )

        if model == "svd":
            return builder(
                image_filename=image_filename,
                width=width,
                height=height,
                frames=frames,
                fps=fps,
                motion_bucket_id=params.get("motion_bucket_id", 127),
                augmentation_level=params.get("augmentation_level", 0.0),
                seed=seed,
            )
        else:
            return builder(
                image_filename=image_filename,
                prompt=prompt,
                width=width,
                height=height,
                frames=frames,
                fps=fps,
                seed=seed,
            )
    else:
        # txt2vid
        return builder(
            prompt=prompt,
            width=width,
            height=height,
            frames=frames,
            fps=fps,
            seed=seed,
        )


def _upload_scene_image(
    scene_index: int,
    image_urls: list,
    base_url: str,
) -> str:
    """img2vid 모드: 장면 이미지를 ComfyUI에 업로드하고 파일명을 반환한다."""
    if scene_index >= len(image_urls) or image_urls[scene_index] is None:
        raise ComfyUIError(
            f"장면 {scene_index}의 이미지가 없습니다. "
            "img2vid 모드에서는 이미지 생성 단계가 먼저 완료되어야 합니다."
        )

    image_data = _download_image_from_url(image_urls[scene_index])
    filename = f"autotube_scene_{scene_index:03d}.png"
    return upload_reference_image(base_url, image_data, filename)
