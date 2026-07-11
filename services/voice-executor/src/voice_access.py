"""Audio validation inside the voice executor boundary."""

from __future__ import annotations

import base64
from typing import Any

SUPPORTED_FORMATS = frozenset({"wav", "webm", "ogg", "mp3"})
MAX_AUDIO_BYTES = 10_000_000


def validate_audio_payload(payload: dict[str, Any]) -> bytes:
    audio_format = str(payload.get("format", ""))
    if audio_format not in SUPPORTED_FORMATS:
        raise ValueError("Unsupported audio format")
    content = base64.b64decode(str(payload["content_base64"]), validate=True)
    if len(content) > MAX_AUDIO_BYTES:
        raise ValueError("Audio payload exceeds the allowed limit")
    return content


def validate_synthesis_text(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Synthesis text is required")
    if len(cleaned) > 5_000:
        raise ValueError("Synthesis text exceeds the allowed limit")
    return cleaned
