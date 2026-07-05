from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RECALLOPS_", env_file=".env", extra="ignore")

    database_path: Path = Path("data/recallops.db")
    cognee_mode: str = Field(default="demo", pattern=r"^(demo|http)$")
    cognee_base_url: str = "http://127.0.0.1:8000"
    cognee_api_key: str = ""
    cognee_tenant_id: str = ""
    request_timeout_seconds: float = Field(default=20.0, gt=0.0, le=120.0)
    demo_project: str = "auth-migration"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
