from supabase import create_client, Client
from app.config import settings

def get_supabase_client() -> Client:
    """
    Returns a Supabase client using service_role key.
    The service_role key bypasses RLS for server-side operations.
    """
    url = settings.supabase_url
    # Prefer service_role key for backend ops to bypass RLS
    key = settings.supabase_service_role_key or settings.supabase_anon_key
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
    return create_client(url, key)
