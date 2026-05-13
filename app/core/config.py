"""Application configuration via pydantic-settings."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    app_host: str = Field(default="127.0.0.1", validation_alias=AliasChoices("APP_HOST", "HOST"))
    app_port: int = Field(default=8787, validation_alias=AliasChoices("APP_PORT", "PORT"))
    app_env: str = Field(default="development", validation_alias=AliasChoices("APP_ENV", "ENV"))
    app_version: str = "0.1.0"
    debug: bool | None = None

    # Database
    database_url: str | None = Field(default=None, validation_alias=AliasChoices("DATABASE_URL"))
    sqlite_path: str = Field(default="./data/basketscout.db", validation_alias=AliasChoices("SQLITE_PATH"))

    # Cache / TTL
    price_ttl_seconds: int = 21600
    availability_ttl_seconds: int = 3600

    # Admin
    admin_token: str | None = Field(default=None, validation_alias=AliasChoices("ADMIN_TOKEN"))
    require_admin_token_in_production: bool = Field(
        default=True,
        validation_alias=AliasChoices("REQUIRE_ADMIN_TOKEN_IN_PRODUCTION"),
    )

    # Provider
    default_provider: str = "mock"
    enable_scraping: bool = False
    scraping_rate_limit_seconds: float = 2.0

    # Open Food Facts
    off_user_agent: str = "BasketScoutDataService/0.1.0 (contact@example.com)"

    # Logging
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL"))
    log_format: str = "json"

    # CORS
    cors_allowed_origins: str = Field(
        default="http://localhost,http://127.0.0.1,http://localhost:3000,http://127.0.0.1:3000",
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS"),
    )

    @property
    def is_production(self) -> bool:
        return self.app_env in {"production", "prod"}

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        if not self.cors_allowed_origins.strip():
            return []
        return [
            item.strip()
            for item in self.cors_allowed_origins.split(",")
            if item.strip()
        ]

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"log_level {value!r} is invalid; allowed: {allowed}")
        return upper

    @field_validator("app_env")
    @classmethod
    def normalize_app_env(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized == "prod":
            return "production"
        if normalized == "dev":
            return "development"
        return normalized

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"dev", "development"}:
                return True
        return value

    @model_validator(mode="after")
    def finalize_settings(self) -> Settings:
        if self.debug is None:
            self.debug = not self.is_production
        if (
            ("SQLITE_PATH" in os.environ and "DATABASE_URL" not in os.environ)
            or not self.database_url
        ):
            self.database_url = f"sqlite:///{self.sqlite_path}"
        return self


@lru_cache
def get_settings() -> Settings:
    """Return singleton settings instance."""
    return Settings()
