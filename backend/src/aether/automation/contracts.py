"""Typed, intentionally narrow contracts for external workflow actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ActionContract:
    action_type: str
    risk_class: str
    idempotency_key: str
    input: dict[str, object]


@dataclass(frozen=True, slots=True)
class ActionContext:
    organization_id: UUID
    workflow_run_id: UUID
    workflow_step_id: UUID
    correlation_id: UUID


class ActionAdapter(Protocol):
    action_type: str

    async def execute(
        self, context: ActionContext, action: ActionContract
    ) -> dict[str, object]: ...


class ActionRegistry(Protocol):
    def get(self, action_type: str) -> ActionAdapter | None: ...
