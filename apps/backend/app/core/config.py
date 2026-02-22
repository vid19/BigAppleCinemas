from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.example", extra="ignore")

    app_name: str = "Big Apple Cinemas API"
    environment: str = "local"
    debug: bool = True
    database_url: str
    redis_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    reservation_hold_minutes: int = 8
    bootstrap_demo_data: bool = True
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 60
    reservation_expiry_sweep_seconds: int = 30
    stripe_webhook_secret: str = "change-me"
    webhook_idempotency_ttl_seconds: int = 86400
    staff_scan_token: str = "local-staff"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
