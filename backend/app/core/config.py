from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Codebook"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://codebook:codebook@127.0.0.1:5432/codebook"
    jwt_secret: str = Field(default="change-me", min_length=8)
    jwt_expire_minutes: int = 60 * 24 * 7
    device_signature_tolerance_seconds: int = 300
    storage_root: str = "/Volumes/AttendanceData/storage"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

