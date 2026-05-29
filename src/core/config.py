from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Backend HGAC PoC"
    app_env: str = "development"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "sqlite:///./data/hgac_poc.db"

    evidence_base_path: str = "./evidence/snapshots"
    evidence_public_base_url: str = "http://localhost:8000/evidence"

    ignition_base_url: str = "http://localhost:8088"
    ignition_event_endpoint: str = "/system/webdev/hgac/events/vehicle-observation"
    ignition_api_token: str = "change-me"
    ignition_timeout_seconds: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
