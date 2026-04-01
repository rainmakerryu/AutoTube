from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://localhost:5432/autotube"
    redis_url: str = "redis://localhost:6379/0"
    r2_endpoint: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_bucket: str = "autotube"
    encryption_master_key: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    cors_origins: list[str] = ["http://localhost:3000"]
    output_dir: str = "~/Downloads/AutoTube"

    model_config = {"env_file": ".env"}


settings = Settings()
