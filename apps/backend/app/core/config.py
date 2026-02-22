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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
