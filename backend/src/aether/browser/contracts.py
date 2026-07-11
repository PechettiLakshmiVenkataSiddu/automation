"""Typed browser work that contains no credential material."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BrowserAction:
    operation: str
    url: str
    timeout_seconds: int
    allowed_hosts: tuple[str, ...]
    credential_reference: UUID | None

    def __post_init__(self) -> None:
        if self.operation not in {"navigate", "click", "fill", "extract", "screenshot"}:
            raise ValueError("Unsupported browser operation")
        if not 1 <= self.timeout_seconds <= 120:
            raise ValueError("Browser timeout must be between 1 and 120 seconds")
        if not self.allowed_hosts:
            raise ValueError("Browser operation requires an egress allowlist")
