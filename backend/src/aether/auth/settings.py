"""Security-sensitive authentication configuration."""

from __future__ import annotations

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from aether.shared.errors import ConfigurationError


class AuthenticationSettings(BaseSettings):
    """Authentication settings sourced from the environment, never from user input."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    jwt_secret: SecretStr = Field(alias="AUTH_JWT_SECRET")
    jwt_issuer: str = Field(default="aether-api", alias="AUTH_JWT_ISSUER")
    jwt_audience: str = Field(default="aether-web", alias="AUTH_JWT_AUDIENCE")
    access_token_ttl_seconds: int = Field(
        default=900, ge=60, le=3600, alias="AUTH_ACCESS_TOKEN_TTL_SECONDS"
    )
    refresh_token_ttl_days: int = Field(
        default=30, ge=1, le=90, alias="AUTH_REFRESH_TOKEN_TTL_DAYS"
    )
    google_client_id: str = Field(alias="GOOGLE_OAUTH_CLIENT_ID")
    google_client_secret: SecretStr = Field(alias="GOOGLE_OAUTH_CLIENT_SECRET")
    github_client_id: str = Field(alias="GITHUB_OAUTH_CLIENT_ID")
    github_client_secret: SecretStr = Field(alias="GITHUB_OAUTH_CLIENT_SECRET")

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: SecretStr) -> SecretStr:
        """Require a secret with sufficient raw-byte length for HS256."""
        if len(value.get_secret_value().encode("utf-8")) < 32:
            raise ConfigurationError("AUTH_JWT_SECRET must contain at least 32 bytes")
        return value
