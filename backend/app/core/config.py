from functools import lru_cache
import os
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Career Twin"
    database_url: str = "sqlite:///./career_twin.db"
    secret_key: str = ""
    environment: str = "development"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    configured = Settings()
    is_production = configured.environment.lower() in {"production", "prod"} or bool(os.getenv("RENDER"))
    if is_production and (not configured.secret_key or len(configured.secret_key) < 32):
        raise RuntimeError("SECRET_KEY must be configured with at least 32 characters in production")
    if not configured.secret_key:
        configured.secret_key = secrets.token_urlsafe(32)
    return configured


settings = get_settings()
