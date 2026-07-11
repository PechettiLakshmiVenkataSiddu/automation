"""Typed voice session contracts with bounded audio limits."""

from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_AUDIO_FORMATS = frozenset({"wav", "webm", "ogg", "mp3"})
MAX_AUDIO_BYTES = 10_000_000
MAX_AUDIO_SECONDS = 120
MAX_TRANSCRIPT_CHARS = 5_000


@dataclass(frozen=True, slots=True)
class VoiceAudioUpload:
    format: str
    content_base64: str
    duration_seconds: int

    def __post_init__(self) -> None:
        if self.format not in SUPPORTED_AUDIO_FORMATS:
            raise ValueError("Unsupported audio format")
        if not 1 <= self.duration_seconds <= MAX_AUDIO_SECONDS:
            raise ValueError("Audio duration exceeds the allowed limit")
        if not self.content_base64:
            raise ValueError("Audio content is required")


@dataclass(frozen=True, slots=True)
class VoiceCommandIntent:
    intent_type: str
    transcript: str
    payload: dict[str, object]
    requires_confirmation: bool

    def __post_init__(self) -> None:
        if not self.transcript.strip():
            raise ValueError("Voice transcript is required")
        if len(self.transcript) > MAX_TRANSCRIPT_CHARS:
            raise ValueError("Voice transcript exceeds the allowed limit")
