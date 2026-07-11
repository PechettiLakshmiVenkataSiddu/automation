"""Typed desktop work that contains no credential material."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

SAFE_OPERATIONS = frozenset({"focus_app", "screenshot", "read_window"})
SENSITIVE_OPERATIONS = frozenset({"click", "type_text", "paste"})
SUPPORTED_OPERATIONS = SAFE_OPERATIONS | SENSITIVE_OPERATIONS


@dataclass(frozen=True, slots=True)
class DesktopAction:
    operation: str
    target_application: str
    timeout_seconds: int
    allowed_applications: tuple[str, ...]
    allowed_mounts: tuple[str, ...]
    network_enabled: bool
    credential_reference: UUID | None
    idempotency_key: str
    risk_class: str

    def __post_init__(self) -> None:
        if self.operation not in SUPPORTED_OPERATIONS:
            raise ValueError("Unsupported desktop operation")
        if not 1 <= self.timeout_seconds <= 120:
            raise ValueError("Desktop timeout must be between 1 and 120 seconds")
        if not self.allowed_applications:
            raise ValueError("Desktop operation requires an application allowlist")
        if not self.target_application:
            raise ValueError("Desktop operation requires a target application")
        if self.risk_class not in {"low", "medium", "high"}:
            raise ValueError("Desktop risk class must be low, medium, or high")
        if not self.idempotency_key:
            raise ValueError("Desktop operation requires an idempotency key")

    @property
    def requires_approval(self) -> bool:
        return self.operation in SENSITIVE_OPERATIONS
