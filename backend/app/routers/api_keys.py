from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.dependencies import get_current_user_id, get_encryption_service
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse
from app.services.encryption import EncryptionService
from app.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])

VALID_PROVIDERS = {
    "openai", "claude", "elevenlabs", "gemini", "pexels", "youtube",
    "deepseek", "ollama", "edgetts", "comfyui",
}


@router.post("", status_code=201, response_model=ApiKeyResponse)
async def create_api_key(
    body: ApiKeyCreate,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
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

    # Encrypt the key
    encrypted_key, nonce, tag = enc.encrypt(body.key)

    # Save to Supabase (Upsert based on user_id and provider)
    data = {
        "user_id": user_id,
        "provider": body.provider,
        "encrypted_key": encrypted_key,
        "nonce": nonce,
        "tag": tag,
        "is_valid": True
    }
    
    res = supabase.table("api_keys").upsert(
        data, on_conflict="user_id,provider"
    ).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="API 키 저장에 실패했습니다.")

    saved_key = res.data[0]

    return ApiKeyResponse(
        id=saved_key["id"],
        provider=saved_key["provider"],
        masked_key=EncryptionService.mask(body.key),
        is_valid=saved_key["is_valid"],
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    res = supabase.table("api_keys").select("*").filter("user_id", "eq", user_id).execute()
    
    return [
        ApiKeyResponse(
            id=k["id"],
            provider=k["provider"],
            masked_key="****",
            is_valid=k["is_valid"],
        )
        for k in res.data
    ]


@router.delete("/{provider}", status_code=204)
async def delete_api_key(
    provider: str,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    # Search for the key by provider for this user
    res = supabase.table("api_keys").delete().filter("user_id", "eq", user_id).filter("provider", "eq", provider).execute()
    
    if not res.data:
        raise HTTPException(
            status_code=404,
            detail=f"API 키를 찾을 수 없습니다: provider={provider}",
        )
