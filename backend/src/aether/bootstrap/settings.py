"""Application-level configuration assembled from environment variables."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationSettings(BaseSettings):
    """Non-secret operational settings for the FastAPI application."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    environment: str = Field(default="development", alias="APP_ENVIRONMENT")
    database_url: str = Field(alias="DATABASE_URL")
    cors_origins: tuple[str, ...] = Field(default=(), alias="CORS_ORIGINS")
    cookie_secure: bool = Field(default=True, alias="AUTH_COOKIE_SECURE")
    oauth_state_ttl_seconds: int = Field(
        default=600, ge=60, le=1800, alias="OAUTH_STATE_TTL_SECONDS"
    )
    browser_artifact_root: Path = Field(default=Path(".artifacts"), alias="BROWSER_ARTIFACT_ROOT")
    browser_executor_secret: str = Field(min_length=32, alias="BROWSER_EXECUTOR_SECRET")
    desktop_artifact_root: Path = Field(default=Path(".artifacts"), alias="DESKTOP_ARTIFACT_ROOT")
    desktop_grant_secret: str = Field(min_length=32, alias="DESKTOP_GRANT_SECRET")
    desktop_executor_secret: str = Field(min_length=32, alias="DESKTOP_EXECUTOR_SECRET")
    voice_artifact_root: Path = Field(default=Path(".artifacts"), alias="VOICE_ARTIFACT_ROOT")
    voice_grant_secret: str = Field(min_length=32, alias="VOICE_GRANT_SECRET")
    voice_executor_secret: str = Field(min_length=32, alias="VOICE_EXECUTOR_SECRET")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | tuple[str, ...] | list[str]) -> tuple[str, ...]:
        """Accept a JSON array only, preventing ambiguous comma-separated origins."""
        if isinstance(value, tuple):
            return value
        if isinstance(value, list):
            return tuple(value)
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError("CORS_ORIGINS must be a JSON array") from error
        if not isinstance(parsed, list) or not all(isinstance(origin, str) for origin in parsed):
            raise ValueError("CORS_ORIGINS must be a JSON array of origins")
        return tuple(parsed)
