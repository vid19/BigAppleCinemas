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
    jwt_access_token_minutes: int = 240
    reservation_hold_minutes: int = 8
    bootstrap_demo_data: bool = True
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 60
    reservation_expiry_sweep_seconds: int = 30
    stripe_webhook_secret: str = "change-me"
    webhook_idempotency_ttl_seconds: int = 86400
    staff_scan_token: str = "local-staff"
    rate_limit_auth_login: int = 10
    rate_limit_auth_window_seconds: int = 60
    rate_limit_reservations_create: int = 20
    rate_limit_reservations_window_seconds: int = 60
    rate_limit_checkout_session: int = 20
    rate_limit_checkout_window_seconds: int = 60
    rate_limit_ticket_scan: int = 60
    rate_limit_ticket_scan_window_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
