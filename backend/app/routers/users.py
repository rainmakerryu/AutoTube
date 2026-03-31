from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from app.dependencies import get_current_user_id
from app.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/users", tags=["users"])


class UserProfile(BaseModel):
    id: str
    email: str | None
    plan: str
    updated_at: str


@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    # Fetch user from public.users table
    res = supabase.table("users").select("*").filter("id", "eq", user_id).execute()
    
    if not res.data:
        # If user doesn't exist in public.users, they might be new.
        # We should probably have a trigger/auth hook to create them,
        # but for now, we'll just return a default 'free' profile if they exist in auth.users
        return UserProfile(
            id=user_id,
            email=None,
            plan="free",
            updated_at="now"
        )
        
    user = res.data[0]
    return UserProfile(
        id=user["id"],
        email=user.get("email"),
        plan=user.get("plan", "free"),
        updated_at=user.get("updated_at")
    )


@router.post("/upgrade", response_model=UserProfile)
async def upgrade_to_pro(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    # Mock upgrade: directly set plan to 'pro'
    res = supabase.table("users").upsert({
        "id": user_id,
        "plan": "pro"
    }, on_conflict="id").execute()
    
    if not res.data:
        raise HTTPException(status_code=500, detail="등급 업그레이드에 실패했습니다.")
        
    user = res.data[0]
    return UserProfile(
        id=user["id"],
        email=user.get("email"),
        plan=user["plan"],
        updated_at=user["updated_at"]
    )
