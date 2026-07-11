"""Redact credential-shaped values from desktop artifacts before persistence."""

from __future__ import annotations

import re

_SECRET_PATTERNS = (
    re.compile(r"(?i)(password|token|authorization|cookie|clipboard)\s*[:=]\s*[^\s\"']+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._~-]+"),
    re.compile(r"(?i)(ssn|social security|credit card)\s*[:=]?\s*[\d\s-]+"),
)


def redact_artifact_text(value: str) -> str:
    for pattern in _SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value
