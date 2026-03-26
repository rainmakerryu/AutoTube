from fastapi import Header, HTTPException

from app.config import settings
from app.services.encryption import EncryptionService


async def get_current_user_id(x_user_id: str = Header(...)) -> str:
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail="X-User-Id 헤더가 필요합니다.",
        )
    return x_user_id


def get_encryption_service() -> EncryptionService:
    if not settings.encryption_master_key:
        raise HTTPException(
            status_code=500,
            detail="ENCRYPTION_MASTER_KEY 환경변수가 설정되지 않았습니다.",
        )
    return EncryptionService(settings.encryption_master_key)
