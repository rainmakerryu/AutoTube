"""단계별 Celery 태스크 디스패치.

파이프라인 단계 이름을 받아 적절한 Celery 워커 태스크를 실행한다.
이전 단계의 출력을 다음 단계의 입력으로 연결한다.
"""
from __future__ import annotations

from supabase import Client

from app.services.encryption import EncryptionService
from app.services.pipeline import STEP_ORDER
from app.services.task_callback import on_step_complete, on_step_failed
from app.workers.images import generate_images_task
from app.workers.metadata import generate_metadata_task
from app.workers.script import generate_script_task
from app.workers.subtitle import generate_subtitles_task
from app.workers.tts import generate_tts_task
from app.workers.video import compose_video_task


def _get_api_key(
    user_id: str, provider: str, supabase: Client, enc: EncryptionService
) -> str | None:
    """암호화된 API 키를 복호화하여 반환. 없으면 None."""
    res = (
        supabase.table("api_keys")
        .select("encrypted_key, nonce, tag")
        .filter("user_id", "eq", user_id)
        .filter("provider", "eq", provider)
        .execute()
    )
    if not res.data:
        return None
    row = res.data[0]
    return enc.decrypt(row["encrypted_key"], row["nonce"], row["tag"])


def _get_previous_outputs(
    project_id: int, current_step: str, supabase: Client
) -> dict[str, dict]:
    """현재 단계 이전의 모든 완료/승인된 단계 출력을 수집."""
    res = (
        supabase.table("pipeline_steps")
        .select("step, output_data")
        .filter("project_id", "eq", project_id)
        .in_("status", ["completed", "approved"])
        .execute()
    )
    outputs = {}
    for row in res.data:
        if row.get("output_data"):
            outputs[row["step"]] = row["output_data"]
    return outputs


def dispatch_step(
    project_id: int,
    step: str,
    provider: str,
    provider_config: dict | None,
    user_id: str,
    supabase: Client,
    enc: EncryptionService,
) -> str:
    """단일 파이프라인 단계를 Celery 태스크로 디스패치.

    Returns:
        Celery task ID.
    """
    project_res = (
        supabase.table("projects")
        .select("*")
        .filter("id", "eq", project_id)
        .execute()
    )
    project = project_res.data[0]

    prev_outputs = _get_previous_outputs(project_id, step, supabase)
    config = provider_config or {}

    # API 키 조회 (프로바이더 불필요 단계는 건너뜀)
    api_key = None
    if provider and provider not in ("edgetts",):
        api_key = _get_api_key(user_id, provider, supabase, enc)
        # ollama, comfyui는 URL을 키로 사용
        if provider in ("ollama", "comfyui") and not api_key:
            api_key = config.get("url", "")

    # 파이프라인 단계 상태를 running으로 변경
    supabase.table("pipeline_steps").update(
        {"status": "running", "provider": provider}
    ).filter("project_id", "eq", project_id).filter(
        "step", "eq", step
    ).execute()

    # Celery 콜백 설정
    success_cb = on_step_complete.s(project_id, step)
    error_cb = on_step_failed.s(project_id, step)

    dispatch_map = {
        "script": _dispatch_script,
        "tts": _dispatch_tts,
        "images": _dispatch_images,
        "video": _dispatch_video,
        "subtitle": _dispatch_subtitle,
        "metadata": _dispatch_metadata,
    }

    dispatch_fn = dispatch_map[step]
    task = dispatch_fn(
        project_id=project_id,
        project=project,
        provider=provider,
        api_key=api_key,
        config=config,
        prev_outputs=prev_outputs,
        success_cb=success_cb,
        error_cb=error_cb,
    )
    return task.id


def _dispatch_script(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    language = config.get("language", "ko")
    return generate_script_task.apply_async(
        args=[
            project_id,
            project["topic"],
            project.get("type", "shorts"),
            provider,
            api_key or "",
            language,
        ],
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_tts(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    script_output = prev_outputs.get("script", {})
    scenes = script_output.get("scenes", [])
    # 모든 장면의 내레이션을 합쳐 TTS 입력으로 사용
    narration_text = "\n\n".join(
        scene.get("narration", "") for scene in scenes
    )
    voice_id = config.get("voice_id")
    return generate_tts_task.apply_async(
        args=[project_id, narration_text, provider, api_key, voice_id],
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_images(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    script_output = prev_outputs.get("script", {})
    scenes = script_output.get("scenes", [])
    video_type = project.get("type", "shorts")
    return generate_images_task.apply_async(
        args=[project_id, scenes, provider, api_key or "", video_type],
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_video(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    images_output = prev_outputs.get("images", {})
    tts_output = prev_outputs.get("tts", {})
    image_urls = images_output.get("image_urls", [])
    audio_url = tts_output.get("audio_url")
    video_type = project.get("type", "shorts")
    return compose_video_task.apply_async(
        args=[project_id, image_urls, audio_url, video_type],
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_subtitle(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    tts_output = prev_outputs.get("tts", {})
    audio_url = tts_output.get("audio_url", "")
    language = config.get("language", "ko")
    # script 프로바이더: 스크립트 나레이션으로 자막 생성 (무료)
    script_output = prev_outputs.get("script", {})
    scenes = script_output.get("scenes", [])
    return generate_subtitles_task.apply_async(
        args=[project_id, audio_url, api_key or "", language],
        kwargs={"scenes": scenes},
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_metadata(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    script_output = prev_outputs.get("script", {})
    script_text = script_output.get("full_text", "")
    video_type = project.get("type", "shorts")
    language = config.get("language", "ko")
    return generate_metadata_task.apply_async(
        args=[project_id, script_text, video_type, provider, api_key or "", language],
        link=success_cb,
        link_error=error_cb,
    )
