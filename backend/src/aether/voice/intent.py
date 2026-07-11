"""Parse voice transcripts into typed command intents."""

from __future__ import annotations

import re

from aether.voice.contracts import VoiceCommandIntent
from aether.voice.redaction import redact_transcript

_AUTOMATION_PATTERNS = (
    re.compile(r"\b(run|start|trigger)\b.*\b(workflow|automation)\b", re.IGNORECASE),
    re.compile(r"\bautomate\b", re.IGNORECASE),
)
_CHAT_PATTERNS = (
    re.compile(r"\b(ask|tell|say|send message)\b", re.IGNORECASE),
    re.compile(r"\bwhat\b", re.IGNORECASE),
)


def parse_transcript(transcript: str) -> VoiceCommandIntent:
    cleaned = redact_transcript(transcript.strip())
    lowered = cleaned.lower()
    for pattern in _AUTOMATION_PATTERNS:
        if pattern.search(lowered):
            return VoiceCommandIntent(
                "automation_action",
                cleaned,
                {"transcript": cleaned},
                requires_confirmation=True,
            )
    for pattern in _CHAT_PATTERNS:
        if pattern.search(lowered):
            return VoiceCommandIntent(
                "chat_message",
                cleaned,
                {"message": cleaned},
                requires_confirmation=True,
            )
    return VoiceCommandIntent(
        "chat_message",
        cleaned,
        {"message": cleaned},
        requires_confirmation=True,
    )
