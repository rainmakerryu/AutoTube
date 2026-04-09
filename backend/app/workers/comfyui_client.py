"""ComfyUI HTTP client for workflow submission, polling, and image transfer.

ComfyUI runs a local server (default http://127.0.0.1:8188) with async workflow execution:
  1. POST /prompt — submit workflow, get prompt_id
  2. GET /history/{prompt_id} — poll until completion
  3. GET /view — download generated image/video
  4. POST /upload/image — upload reference image for IP-Adapter
"""
from __future__ import annotations

import time

import httpx

COMFYUI_DEFAULT_URL = "http://127.0.0.1:8188"
POLL_INITIAL_INTERVAL = 1.0
POLL_MAX_INTERVAL = 5.0
POLL_TIMEOUT = 300.0
VIDEO_POLL_TIMEOUT = 600.0
HEALTH_TIMEOUT = 5.0
SUBMIT_TIMEOUT = 30.0
DOWNLOAD_TIMEOUT = 60.0
VIDEO_DOWNLOAD_TIMEOUT = 120.0


class ComfyUIError(Exception):
    """Raised when ComfyUI returns an error or is unreachable."""


def _normalize_url(url: str) -> str:
    """Remove trailing slashes from base URL to prevent double-slash issues."""
    return url.rstrip("/")


def check_comfyui_health(base_url: str = COMFYUI_DEFAULT_URL) -> bool:
    """Ping ComfyUI server. Returns True if reachable."""
    url = _normalize_url(base_url)
    try:
        response = httpx.get(f"{url}/system_stats", timeout=HEALTH_TIMEOUT)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def submit_workflow(base_url: str, workflow: dict) -> str:
    """Submit a workflow to ComfyUI's /prompt endpoint.

    Returns the prompt_id for polling.
    Raises ComfyUIError if submission fails.
    """
    base_url = _normalize_url(base_url)
    try:
        response = httpx.post(
            f"{base_url}/prompt",
            json={"prompt": workflow},
            timeout=SUBMIT_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise ComfyUIError(
                "ComfyUI가 prompt_id를 반환하지 않았습니다. "
                "워크플로우 형식을 확인하세요."
            )
        return prompt_id
    except httpx.HTTPStatusError as exc:
        raise ComfyUIError(
            f"ComfyUI 워크플로우 제출 실패 (HTTP {exc.response.status_code}): "
            f"{exc.response.text[:200]}"
        ) from exc
    except httpx.HTTPError as exc:
        raise ComfyUIError(
            f"ComfyUI 서버 연결 실패: {base_url}. "
            "ComfyUI가 실행 중인지 확인하세요."
        ) from exc


def poll_comfyui_result(
    base_url: str,
    prompt_id: str,
    timeout: float = POLL_TIMEOUT,
) -> dict:
    """Poll /history/{prompt_id} until workflow completes.

    Uses exponential backoff: 1s → 2s → 4s → 5s (capped).
    Returns the output dict for the prompt_id.
    Raises ComfyUIError on timeout or execution error.
    """
    base_url = _normalize_url(base_url)
    start = time.monotonic()
    interval = POLL_INITIAL_INTERVAL

    while (time.monotonic() - start) < timeout:
        try:
            response = httpx.get(
                f"{base_url}/history/{prompt_id}",
                timeout=HEALTH_TIMEOUT,
            )
            response.raise_for_status()
            history = response.json()
        except httpx.HTTPError:
            time.sleep(interval)
            interval = min(interval * 2, POLL_MAX_INTERVAL)
            continue

        if prompt_id not in history:
            time.sleep(interval)
            interval = min(interval * 2, POLL_MAX_INTERVAL)
            continue

        entry = history[prompt_id]

        # Check for execution error
        status = entry.get("status", {})
        if status.get("status_str") == "error":
            messages = status.get("messages", [])
            error_detail = str(messages[:3]) if messages else "알 수 없는 오류"
            raise ComfyUIError(
                f"ComfyUI 워크플로우 실행 오류: {error_detail}"
            )

        # Check for completed outputs
        outputs = entry.get("outputs")
        if outputs:
            return outputs

        # 성공했지만 출력이 비어있는 경우 (캐시 등) — 빈 결과 반환
        if status.get("completed") or status.get("status_str") == "success":
            return outputs or {}

        time.sleep(interval)
        interval = min(interval * 2, POLL_MAX_INTERVAL)

    elapsed = time.monotonic() - start
    raise ComfyUIError(
        f"ComfyUI 워크플로우 타임아웃: {elapsed:.0f}초 경과 "
        f"(제한: {timeout:.0f}초). prompt_id={prompt_id}"
    )


def download_comfyui_image(
    base_url: str,
    filename: str,
    subfolder: str = "",
    img_type: str = "output",
) -> bytes:
    """Download a generated image from ComfyUI's /view endpoint.

    Returns raw image bytes.
    Raises ComfyUIError if download fails.
    """
    base_url = _normalize_url(base_url)
    params = {"filename": filename, "type": img_type}
    if subfolder:
        params["subfolder"] = subfolder

    try:
        response = httpx.get(
            f"{base_url}/view",
            params=params,
            timeout=DOWNLOAD_TIMEOUT,
        )
        response.raise_for_status()
        return response.content
    except httpx.HTTPError as exc:
        raise ComfyUIError(
            f"ComfyUI 이미지 다운로드 실패: filename={filename}, "
            f"오류: {exc}"
        ) from exc


def download_comfyui_video(
    base_url: str,
    filename: str,
    subfolder: str = "",
    vid_type: str = "output",
) -> bytes:
    """Download a generated video from ComfyUI's /view endpoint.

    Same as download_comfyui_image but with a longer timeout for video files.
    Returns raw video bytes.
    Raises ComfyUIError if download fails.
    """
    base_url = _normalize_url(base_url)
    params = {"filename": filename, "type": vid_type}
    if subfolder:
        params["subfolder"] = subfolder

    try:
        response = httpx.get(
            f"{base_url}/view",
            params=params,
            timeout=VIDEO_DOWNLOAD_TIMEOUT,
        )
        response.raise_for_status()
        return response.content
    except httpx.HTTPError as exc:
        raise ComfyUIError(
            f"ComfyUI 영상 다운로드 실패: filename={filename}, "
            f"오류: {exc}"
        ) from exc


def extract_video_output(outputs: dict) -> dict | None:
    """Extract video file info from ComfyUI workflow outputs.

    VHS_VideoCombine stores results under the "gifs" key (despite the name,
    it contains MP4 info): {"gifs": [{"filename": "...", "subfolder": "", "type": "output"}]}

    Returns {"filename": str, "subfolder": str, "type": str} or None if not found.
    """
    for node_id, node_output in outputs.items():
        gifs = node_output.get("gifs")
        if gifs and len(gifs) > 0:
            entry = gifs[0]
            return {
                "filename": entry.get("filename", ""),
                "subfolder": entry.get("subfolder", ""),
                "type": entry.get("type", "output"),
            }
    return None


def upload_reference_image(
    base_url: str,
    image_bytes: bytes,
    filename: str,
) -> str:
    """Upload an image to ComfyUI's input directory for IP-Adapter reference.

    Returns the filename as stored by ComfyUI.
    Raises ComfyUIError if upload fails.
    """
    base_url = _normalize_url(base_url)
    try:
        response = httpx.post(
            f"{base_url}/upload/image",
            files={"image": (filename, image_bytes, "image/png")},
            data={"overwrite": "true"},
            timeout=SUBMIT_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        stored_name = data.get("name")
        if not stored_name:
            raise ComfyUIError(
                "ComfyUI 이미지 업로드 응답에 파일명이 없습니다."
            )
        return stored_name
    except httpx.HTTPStatusError as exc:
        raise ComfyUIError(
            f"ComfyUI 이미지 업로드 실패 (HTTP {exc.response.status_code}): "
            f"{exc.response.text[:200]}"
        ) from exc
    except httpx.HTTPError as exc:
        raise ComfyUIError(
            f"ComfyUI 서버 연결 실패: {base_url}. "
            "ComfyUI가 실행 중인지 확인하세요."
        ) from exc
