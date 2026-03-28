from typing import Optional
from app.supabase_client import get_supabase_client
from app.services.encryption import EncryptionService

class UserSettingsService:
    def __init__(self, encryption_service: EncryptionService):
        self.encryption_service = encryption_service
        self.supabase = get_supabase_client()

    async def get_api_key(self, user_id: str, key_name: str) -> Optional[str]:
        # Supabase에서 해당 유저의 설정 가져오기
        result = self.supabase.table("user_settings").select("*").eq("user_id", user_id).execute()
        
        if not result.data:
            return None
            
        settings = result.data[0]
        encrypted_val = settings.get(f"{key_name}_encrypted")
        nonce = settings.get(f"{key_name}_nonce")
        tag = settings.get(f"{key_name}_tag")
        
        if not all([encrypted_val, nonce, tag]):
            return None
            
        # 복호화
        try:
            return self.encryption_service.decrypt(
                bytes.fromhex(encrypted_val),
                bytes.fromhex(nonce),
                bytes.fromhex(tag)
            )
        except Exception:
            return None

    async def save_api_key(self, user_id: str, key_name: str, api_key: str):
        # 암호화
        encrypted_val, nonce, tag = self.encryption_service.encrypt(api_key)
        
        data = {
            "user_id": user_id,
            f"{key_name}_encrypted": encrypted_val.hex(),
            f"{key_name}_nonce": nonce.hex(),
            f"{key_name}_tag": tag.hex(),
        }
        
        # upsert (user_id가 PK인 경우)
        self.supabase.table("user_settings").upsert(data).execute()
