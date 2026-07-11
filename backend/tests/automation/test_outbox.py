from uuid import uuid4

import pytest

from aether.automation.outbox import OutboxEvent, publish_claimed


class Outbox:
    def __init__(self) -> None:
        self.event = OutboxEvent(uuid4(), uuid4(), "workflow.run_requested", {})
        self.published: list[str] = []
        self.failed: list[str] = []

    async def claim(self) -> list[OutboxEvent]:
        return [self.event]

    async def mark_published(self, event_id: object) -> None:
        self.published.append(str(event_id))

    async def mark_failed(self, event_id: object, error: str) -> None:
        self.failed.append(error)


class Dispatcher:
    async def dispatch(self, event: OutboxEvent) -> None:
        return None


@pytest.mark.asyncio
async def test_publisher_marks_success_only_after_dispatch() -> None:
    outbox = Outbox()
    assert await publish_claimed(outbox, Dispatcher()) == 1  # type: ignore[arg-type]
    assert outbox.published == [str(outbox.event.id)]
