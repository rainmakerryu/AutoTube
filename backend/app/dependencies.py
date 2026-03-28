from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.config import settings
from app.services.encryption import EncryptionService


security = HTTPBearer()

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    try:
        if not settings.supabase_jwt_secret:
            raise HTTPException(status_code=500, detail="SUPABASE_JWT_SECRET not set")
            
        payload = jwt.decode(
            token, 
            settings.supabase_jwt_secret, 
            algorithms=["HS256"], 
            audience="authenticated"
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: sub claim missing")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def get_encryption_service() -> EncryptionService:
    if not settings.encryption_master_key:
        raise HTTPException(
            status_code=500,
            detail="ENCRYPTION_MASTER_KEY 환경변수가 설정되지 않았습니다.",
        )
    return EncryptionService(settings.encryption_master_key)
