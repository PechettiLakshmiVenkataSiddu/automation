"""Workflow state transitions, kept independent of transport and workers."""

from __future__ import annotations

from enum import StrEnum

from aether.shared.errors import AetherError


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    RETRY_SCHEDULED = "retry_scheduled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InvalidRunTransition(AetherError):
    """A worker or API attempted a state transition that is not permitted."""


_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.QUEUED: {RunStatus.RUNNING, RunStatus.CANCELLED},
    RunStatus.RUNNING: {
        RunStatus.AWAITING_APPROVAL,
        RunStatus.RETRY_SCHEDULED,
        RunStatus.SUCCEEDED,
        RunStatus.FAILED,
        RunStatus.CANCELLED,
    },
    RunStatus.AWAITING_APPROVAL: {RunStatus.QUEUED, RunStatus.CANCELLED},
    RunStatus.RETRY_SCHEDULED: {RunStatus.QUEUED, RunStatus.CANCELLED},
    RunStatus.SUCCEEDED: set(),
    RunStatus.FAILED: set(),
    RunStatus.CANCELLED: set(),
}


def require_transition(current: RunStatus, target: RunStatus) -> None:
    """Reject invalid or terminal-state transitions before persistence."""
    if target not in _TRANSITIONS[current]:
        raise InvalidRunTransition(f"Cannot transition workflow run from {current} to {target}")
