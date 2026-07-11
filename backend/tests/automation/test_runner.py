from uuid import uuid4

import pytest

from aether.automation.runner import WorkflowRunner
from aether.automation.state_machine import RunStatus


class Store:
    def __init__(self, cancelled: bool) -> None:
        self.cancelled = cancelled
        self.states: list[RunStatus] = []

    async def claim(self, organization_id: object, run_id: object) -> RunStatus:
        return RunStatus.QUEUED

    async def cancellation_requested(self, organization_id: object, run_id: object) -> bool:
        return self.cancelled

    async def transition(self, organization_id: object, run_id: object, status: RunStatus) -> None:
        self.states.append(status)


@pytest.mark.asyncio
async def test_runner_honors_cancellation_before_execution() -> None:
    store = Store(True)
    assert not await WorkflowRunner(store).begin(uuid4(), uuid4())
    assert store.states == [RunStatus.CANCELLED]


@pytest.mark.asyncio
async def test_runner_requires_lease_and_starts_queued_run() -> None:
    store = Store(False)
    assert await WorkflowRunner(store).begin(uuid4(), uuid4())
    assert store.states == [RunStatus.RUNNING]
