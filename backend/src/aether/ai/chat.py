"""Provider-neutral chat completion gateway with an OpenAI-compatible adapter."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from aether.shared.errors import AetherError


class ChatProviderError(AetherError):
    """A provider rejected or failed to complete a model request."""


class ChatSettings(BaseSettings):
    """Server-side configuration for the configured chat provider."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    base_url: str = Field(alias="AI_CHAT_BASE_URL")
    api_key: SecretStr = Field(alias="AI_CHAT_API_KEY")
    model: str = Field(alias="AI_CHAT_MODEL")


class ChatMessage(BaseModel):
    """A normalized chat message sent to or received from a provider."""

    role: str
    content: str


@dataclass(frozen=True, slots=True)
class ChatCompletion:
    content: str
    model: str
    usage: dict[str, int]


class OpenAICompatibleChatGateway:
    """Calls a standards-compatible `/chat/completions` endpoint with bounded requests."""

    def __init__(self, settings: ChatSettings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client

    async def complete(self, messages: list[ChatMessage]) -> ChatCompletion:
        """Request a non-streaming completion and validate its normalized response."""
        try:
            response = await self._client.post(
                f"{self._settings.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self._settings.api_key.get_secret_value()}"},
                json={
                    "model": self._settings.model,
                    "messages": [message.model_dump() for message in messages],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Provider returned an empty completion")
            raw_usage = payload.get("usage", {})
            usage = {key: int(value) for key, value in raw_usage.items() if isinstance(value, int)}
            return ChatCompletion(
                content=content, model=str(payload.get("model", self._settings.model)), usage=usage
            )
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
            raise ChatProviderError("The AI provider could not complete this request") from error
