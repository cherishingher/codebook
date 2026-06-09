from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    device_code: str = "MACMINI-A-GATE-001"
    device_secret: str = "change-me"
    api_base_url: str = "http://127.0.0.1:8000/api/v1"
    camera_index: int = 0
    frame_width: int = 1280
    frame_height: int = 720
    recognition_threshold: float = 0.82
    dedup_seconds: int = 30
    save_snapshots: bool = True
    storage_root: str = "/Volumes/AttendanceData/storage"


@lru_cache
def get_settings() -> AgentSettings:
    return AgentSettings()


settings = get_settings()

