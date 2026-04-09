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
from app.workers.video_gen import generate_video_clips_task
from app.workers.bgm import add_bgm_task
from app.workers.thumbnail import generate_thumbnail_task
from app.workers.audio_postprocess import audio_postprocess_task
from app.workers.seo import optimize_seo_task
from app.workers.sns import generate_sns_task


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
        "audio_post": _dispatch_audio_post,
        "images": _dispatch_images,
        "video_gen": _dispatch_video_gen,
        "video": _dispatch_video,
        "subtitle": _dispatch_subtitle,
        "metadata": _dispatch_metadata,
        "thumbnail": _dispatch_thumbnail,
        "bgm": _dispatch_bgm,
        "seo": _dispatch_seo,
        "sns": _dispatch_sns,
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


def _get_pipeline_sub_config(project: dict, key: str) -> dict:
    """pipeline_config에서 하위 설정(script_config, voice_config 등)을 가져온다."""
    pipeline_config = project.get("pipeline_config") or {}
    return pipeline_config.get(key) or {}


def _dispatch_script(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    script_cfg = _get_pipeline_sub_config(project, "script_config")
    language = config.get("language") or script_cfg.get("language", "ko")

    return generate_script_task.apply_async(
        args=[
            project_id,
            project["topic"],
            project.get("type", "shorts"),
            provider,
            api_key or "",
            language,
        ],
        kwargs={"script_config": script_cfg},
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_tts(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    voice_cfg = _get_pipeline_sub_config(project, "voice_config")

    # 외부 음성 업로드: TTS 생성을 스킵하고 업로드된 URL을 바로 반환
    custom_audio_url = voice_cfg.get("custom_audio_url")
    if custom_audio_url and custom_audio_url != "pending":
        return generate_tts_task.apply_async(
            args=[project_id, "", "custom", None, None],
            kwargs={"custom_audio_url": custom_audio_url},
            link=success_cb,
            link_error=error_cb,
        )

    script_output = prev_outputs.get("script", {})
    scenes = script_output.get("scenes", [])
    narration_text = "\n\n".join(
        scene.get("narration", "") for scene in scenes
    )
    voice_id = config.get("voice_id") or voice_cfg.get("voice_id")
    speed = voice_cfg.get("speed", 1.0)
    emotion = voice_cfg.get("emotion", "normal")
    return generate_tts_task.apply_async(
        args=[project_id, narration_text, provider, api_key, voice_id],
        kwargs={"speed": speed, "emotion": emotion},
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_images(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    image_cfg = _get_pipeline_sub_config(project, "image_config")
    script_output = prev_outputs.get("script", {})
    scenes = script_output.get("scenes", [])
    video_type = project.get("type", "shorts")
    style = image_cfg.get("style", "")
    return generate_images_task.apply_async(
        args=[project_id, scenes, provider, api_key or "", video_type],
        kwargs={"style": style},
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_video_gen(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    video_gen_cfg = _get_pipeline_sub_config(project, "video_gen_config")
    gen_mode = video_gen_cfg.get("gen_mode", "img2vid")
    model = video_gen_cfg.get("model", "animatediff")
    images_output = prev_outputs.get("images", {})
    image_urls = images_output.get("image_urls", [])
    script_output = prev_outputs.get("script", {})
    scenes = script_output.get("scenes", [])
    video_type = project.get("type", "shorts")
    image_cfg = _get_pipeline_sub_config(project, "image_config")
    style = image_cfg.get("style", "")
    return generate_video_clips_task.apply_async(
        args=[project_id, scenes, image_urls, api_key or "", video_type,
              gen_mode, model],
        kwargs={"style": style},
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_video(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    images_output = prev_outputs.get("images", {})
    tts_output = prev_outputs.get("tts", {})
    audio_post_output = prev_outputs.get("audio_post", {})
    video_gen_output = prev_outputs.get("video_gen", {})
    image_urls = images_output.get("image_urls", [])
    video_clip_urls = video_gen_output.get("video_clip_urls")
    # 오디오 후처리 결과가 있으면 그것을 사용, 없으면 TTS 원본
    audio_url = audio_post_output.get("audio_url") or tts_output.get("audio_url")
    video_type = project.get("type", "shorts")
    video_cfg = _get_pipeline_sub_config(project, "video_config")
    sync_mode = video_cfg.get("sync_mode", "normal")
    speed_factor = video_cfg.get("speed_factor", 1.0)
    intro_cfg = _get_pipeline_sub_config(project, "intro_config")
    intro_video_url = intro_cfg.get("intro_video_url")
    logo_url = intro_cfg.get("logo_url")
    logo_position = intro_cfg.get("logo_position", "top-right")
    logo_opacity = intro_cfg.get("logo_opacity", 0.8)
    return compose_video_task.apply_async(
        args=[project_id, image_urls, audio_url, video_type],
        kwargs={
            "sync_mode": sync_mode,
            "speed_factor": speed_factor,
            "video_clip_urls": video_clip_urls,
            "intro_video_url": intro_video_url,
            "logo_url": logo_url,
            "logo_position": logo_position,
            "logo_opacity": logo_opacity,
        },
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
    script_output = prev_outputs.get("script", {})
    scenes = script_output.get("scenes", [])
    subtitle_cfg = _get_pipeline_sub_config(project, "subtitle_config")
    # BGM 적용된 영상 우선, 없으면 원본 영상 URL
    bgm_output = prev_outputs.get("bgm", {})
    video_output = prev_outputs.get("video", {})
    video_url = bgm_output.get("video_url") or video_output.get("video_url")
    return generate_subtitles_task.apply_async(
        args=[project_id, audio_url, api_key or "", language],
        kwargs={
            "scenes": scenes,
            "subtitle_config": subtitle_cfg,
            "video_url": video_url,
        },
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


def _dispatch_audio_post(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    audio_post_cfg = _get_pipeline_sub_config(project, "audio_post_config")
    tts_output = prev_outputs.get("tts", {})
    audio_url = tts_output.get("audio_url", "")
    mode = audio_post_cfg.get("mode", "normalize")
    return audio_postprocess_task.apply_async(
        args=[project_id, audio_url, mode],
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_thumbnail(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    metadata_output = prev_outputs.get("metadata", {})
    script_output = prev_outputs.get("script", {})
    title = metadata_output.get("title", "")
    description = metadata_output.get("description", "")
    scenes = script_output.get("scenes", [])
    return generate_thumbnail_task.apply_async(
        args=[project_id, title, description, scenes, provider, api_key or ""],
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_bgm(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    bgm_cfg = _get_pipeline_sub_config(project, "bgm_config")
    video_output = prev_outputs.get("video", {})
    video_url = video_output.get("video_url", "")
    mood = config.get("mood") or bgm_cfg.get("mood", "calm")
    volume = bgm_cfg.get("volume", 0.15)
    return add_bgm_task.apply_async(
        args=[project_id, video_url, mood, provider, api_key or ""],
        kwargs={"volume": volume},
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_seo(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    metadata_output = prev_outputs.get("metadata", {})
    script_output = prev_outputs.get("script", {})
    title = metadata_output.get("title", "")
    description = metadata_output.get("description", "")
    tags = metadata_output.get("tags", [])
    script_text = script_output.get("full_text", "")
    video_type = project.get("type", "shorts")
    language = config.get("language", "ko")
    return optimize_seo_task.apply_async(
        args=[project_id, title, description, tags, script_text, video_type, provider, api_key or "", language],
        link=success_cb,
        link_error=error_cb,
    )


def _dispatch_sns(
    *, project_id, project, provider, api_key, config, prev_outputs,
    success_cb, error_cb,
):
    # Prefer SEO-optimized metadata if available, fallback to original metadata
    seo_output = prev_outputs.get("seo", {})
    metadata_output = prev_outputs.get("metadata", {})
    title = seo_output.get("optimized_title") or metadata_output.get("title", "")
    description = seo_output.get("optimized_description") or metadata_output.get("description", "")
    tags = seo_output.get("optimized_tags") or metadata_output.get("tags", [])
    # Get video URL from bgm (if applied) or original video
    bgm_output = prev_outputs.get("bgm", {})
    video_output = prev_outputs.get("video", {})
    video_url = bgm_output.get("video_url") or video_output.get("video_url")
    return generate_sns_task.apply_async(
        args=[project_id, title, description, tags, video_url],
        link=success_cb,
        link_error=error_cb,
    )
