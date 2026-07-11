"""Typed memory domain values independent of persistence and HTTP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Memory:
    """A user-owned, consented long-term memory."""

    id: UUID
    organization_id: UUID
    user_id: UUID
    memory_type: str
    text: str
    source_reference: dict[str, object]
    confidence: float | None
    expires_at: datetime | None
    retention_until: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class MemoryConsent:
    """The current retrieval and creation preference for one user/workspace pair."""

    organization_id: UUID
    user_id: UUID
    enabled: bool
    policy_version: str
    updated_at: datetime
