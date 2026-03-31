from __future__ import annotations

import jwt as pyjwt
import httpx
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt as jose_jwt, JWTError

from app.config import settings
from app.services.encryption import EncryptionService

security = HTTPBearer()

# Cache JWKS to avoid repeated network requests
_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    supabase_url = settings.supabase_url.rstrip("/")
    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        return _jwks_cache


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    try:
        # Peek at the token header to determine algorithm
        unverified_header = pyjwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "HS256")

        if alg in ("RS256", "ES256"):
            # Verify using Supabase JWKS (public key)
            jwks = await _get_jwks()
            payload = jose_jwt.decode(
                token,
                jwks,
                algorithms=["RS256", "ES256"],
                options={"verify_aud": False},
            )
        else:
            # Verify using JWT Secret (HS256)
            secret = settings.supabase_jwt_secret.strip()
            payload = jose_jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing sub claim")
        return user_id

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token signature")
    except pyjwt.exceptions.PyJWTError:
        raise HTTPException(status_code=401, detail="Malformed token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")


from app.supabase_client import get_supabase_client
from supabase import Client

async def get_pro_user(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
) -> str:
    res = supabase.table("users").select("plan").filter("id", "eq", user_id).execute()
    if not res.data or res.data[0].get("plan") != "pro":
        raise HTTPException(
            status_code=402,
            detail="이 기능은 Pro 요금제 전용입니다. 업그레이드 후 이용해 주세요.",
        )
    return user_id


def get_encryption_service() -> EncryptionService:
    if not settings.encryption_master_key:
        raise HTTPException(
            status_code=500,
            detail="ENCRYPTION_MASTER_KEY 환경변수가 설정되지 않았습니다.",
        )
    return EncryptionService(settings.encryption_master_key)
