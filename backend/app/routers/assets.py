"""에셋 파일 업로드 엔드포인트.

오디오, 인트로 영상, 로고 이미지 등을 업로드하여 파이프라인에서 사용한다.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.dependencies import get_current_user_id
from app.services.storage import (
    build_storage_key,
    get_content_type,
    save_local,
    MEDIA_ROOT,
)

router = APIRouter(prefix="/api/assets", tags=["assets"])

ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    "audio": {"mp3", "wav", "ogg", "m4a"},
    "intro_video": {"mp4", "mov", "webm"},
    "logo": {"png", "jpg", "jpeg", "webp", "svg"},
}

MAX_ASSET_SIZES: dict[str, int] = {
    "audio": 50 * 1024 * 1024,        # 50MB
    "intro_video": 200 * 1024 * 1024,  # 200MB
    "logo": 10 * 1024 * 1024,          # 10MB
}

VALID_ASSET_TYPES = set(ALLOWED_EXTENSIONS.keys())


class AssetUploadResponse(BaseModel):
    asset_url: str
    asset_type: str
    filename: str
    size: int


def _get_extension(filename: str) -> str:
    """파일명에서 확장자를 추출한다 (소문자)."""
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


@router.post("/{project_id}/{asset_type}", response_model=AssetUploadResponse)
async def upload_asset(
    project_id: int,
    asset_type: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    """프로젝트에 에셋 파일을 업로드한다.

    Args:
        project_id: 프로젝트 ID
        asset_type: 에셋 타입 ("audio", "intro_video", "logo")
        file: 업로드할 파일
    """
    # 1. 에셋 타입 검증
    if asset_type not in VALID_ASSET_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"지원하지 않는 에셋 타입입니다: '{asset_type}'. "
                f"허용: {', '.join(sorted(VALID_ASSET_TYPES))}"
            ),
        )

    # 2. 파일 확장자 검증
    filename = file.filename or "unknown"
    ext = _get_extension(filename)
    allowed_exts = ALLOWED_EXTENSIONS[asset_type]
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=(
                f"지원하지 않는 파일 형식입니다: .{ext}. "
                f"허용 형식: {', '.join(sorted(allowed_exts))}"
            ),
        )

    # 3. 파일 읽기 + 크기 검증
    max_size = MAX_ASSET_SIZES[asset_type]
    data = await file.read()
    if len(data) > max_size:
        max_mb = max_size // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=(
                f"파일 크기가 제한을 초과했습니다. "
                f"최대 {max_mb}MB까지 업로드할 수 있습니다."
            ),
        )

    if len(data) == 0:
        raise HTTPException(
            status_code=400,
            detail="빈 파일은 업로드할 수 없습니다.",
        )

    # 4. 저장
    safe_filename = f"{asset_type}.{ext}"
    key = build_storage_key(project_id, "assets", safe_filename)
    asset_url = save_local(key, data)

    return AssetUploadResponse(
        asset_url=asset_url,
        asset_type=asset_type,
        filename=filename,
        size=len(data),
    )
