"""Uygulama konfigürasyon ayarları — pydantic-settings ile."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Sunucu
    app_host: str = "127.0.0.1"
    app_port: int = 8787
    app_env: str = "development"
    app_version: str = "0.1.0"
    debug: bool = True

    # Veritabanı
    database_url: str = "sqlite:///./data/basketscout.db"

    # Cache / TTL
    price_ttl_seconds: int = 21600  # 6 saat
    availability_ttl_seconds: int = 3600  # 1 saat

    # Admin
    admin_token: str | None = None

    # Provider
    default_provider: str = "mock"
    enable_scraping: bool = False
    scraping_rate_limit_seconds: float = 2.0

    # Open Food Facts
    off_user_agent: str = "BasketScoutDataService/0.1.0 (contact@example.com)"

    # Loglama
    log_level: str = "INFO"
    log_format: str = "json"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level {v!r} geçersiz; izin verilenler: {allowed}")
        return upper

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"dev", "development"}:
                return True
        return value


@lru_cache
def get_settings() -> Settings:
    """Singleton Settings nesnesi döndürür."""
    return Settings()
