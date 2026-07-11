"""Lease-guarded workflow run execution orchestration."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from aether.automation.state_machine import RunStatus, require_transition


class RunStore(Protocol):
    async def claim(self, organization_id: UUID, run_id: UUID) -> RunStatus | None: ...
    async def cancellation_requested(self, organization_id: UUID, run_id: UUID) -> bool: ...
    async def transition(self, organization_id: UUID, run_id: UUID, status: RunStatus) -> None: ...


class WorkflowRunner:
    """Never executes work without a lease or after cancellation."""

    def __init__(self, store: RunStore) -> None:
        self._store = store

    async def begin(self, organization_id: UUID, run_id: UUID) -> bool:
        current = await self._store.claim(organization_id, run_id)
        if current is None or current is not RunStatus.QUEUED:
            return False
        if await self._store.cancellation_requested(organization_id, run_id):
            require_transition(current, RunStatus.CANCELLED)
            await self._store.transition(organization_id, run_id, RunStatus.CANCELLED)
            return False
        require_transition(current, RunStatus.RUNNING)
        await self._store.transition(organization_id, run_id, RunStatus.RUNNING)
        return True
