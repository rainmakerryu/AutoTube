from supabase import create_client, Client
from app.config import settings

def get_supabase_client() -> Client:
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise ValueError("SUPABASE_URL or SUPABASE_ANON_KEY not set")
    return create_client(settings.supabase_url, settings.supabase_anon_key)
