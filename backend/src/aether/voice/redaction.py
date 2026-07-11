"""Redact credential-shaped values from voice transcripts and artifacts."""

from __future__ import annotations

import re

_SECRET_PATTERNS = (
    re.compile(r"(?i)(password|token|authorization|cookie|api[_-]?key)\s*[:=]\s*[^\s\"']+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._~-]+"),
)


def redact_transcript(value: str) -> str:
    for pattern in _SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value
