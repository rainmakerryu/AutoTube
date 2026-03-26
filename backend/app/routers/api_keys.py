from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id, get_encryption_service
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse
from app.services.encryption import EncryptionService

router = APIRouter(prefix="/api/settings/api-keys", tags=["api-keys"])

VALID_PROVIDERS = {"openai", "claude", "elevenlabs", "gemini", "pexels", "youtube"}


@router.post("", status_code=201, response_model=ApiKeyResponse)
async def create_api_key(
    body: ApiKeyCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    enc: EncryptionService = Depends(get_encryption_service),
):
    if body.provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"지원하지 않는 provider입니다: {body.provider}. "
                f"지원 목록: {', '.join(sorted(VALID_PROVIDERS))}"
            ),
        )

    existing = db.query(ApiKey).filter_by(user_id=user_id, provider=body.provider).first()
    if existing:
        db.delete(existing)
        db.flush()

    encrypted, nonce, tag = enc.encrypt(body.key)
    api_key = ApiKey(
        user_id=user_id,
        provider=body.provider,
        encrypted_key=encrypted,
        nonce=nonce,
        tag=tag,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return ApiKeyResponse(
        id=api_key.id,
        provider=api_key.provider,
        masked_key=EncryptionService.mask(body.key),
        is_valid=api_key.is_valid,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    keys = db.query(ApiKey).filter_by(user_id=user_id).all()
    return [
        ApiKeyResponse(
            id=k.id,
            provider=k.provider,
            masked_key="****",
            is_valid=k.is_valid,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(
    key_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    key = db.query(ApiKey).filter_by(id=key_id, user_id=user_id).first()
    if not key:
        raise HTTPException(
            status_code=404,
            detail=f"API 키를 찾을 수 없습니다: id={key_id}",
        )
    db.delete(key)
    db.commit()
