"""Transactional outbox publication with lease-safe claiming."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class OutboxEvent:
    id: UUID
    organization_id: UUID | None
    event_type: str
    payload: dict[str, object]


class EventDispatcher(Protocol):
    async def dispatch(self, event: OutboxEvent) -> None: ...


class SqlAlchemyOutbox:
    """Claims unpublished records with `SKIP LOCKED` to avoid duplicate delivery."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def claim(self, limit: int = 100) -> list[OutboxEvent]:
        rows = await self._session.execute(
            text(
                "WITH candidates AS (SELECT id FROM outbox_events WHERE published_at IS NULL "
                "AND dead_lettered_at IS NULL AND next_attempt_at <= now() "
                "AND (dispatch_lease_expires_at IS NULL OR dispatch_lease_expires_at < now()) "
                "ORDER BY occurred_at FOR UPDATE SKIP LOCKED LIMIT :limit) "
                "UPDATE outbox_events o SET dispatch_lease_expires_at = now() + interval '60 seconds' "
                "FROM candidates c WHERE o.id = c.id "
                "RETURNING o.id, o.organization_id, o.event_type, o.payload"
            ),
            {"limit": min(limit, 100)},
        )
        return [
            OutboxEvent(row.id, row.organization_id, row.event_type, row.payload) for row in rows
        ]

    async def mark_published(self, event_id: UUID) -> None:
        await self._session.execute(
            text(
                "UPDATE outbox_events SET published_at = :now, attempts = attempts + 1, dispatch_lease_expires_at = NULL "
                "WHERE id = :id AND dispatch_lease_expires_at >= :now"
            ),
            {"id": event_id, "now": datetime.now(UTC)},
        )

    async def mark_failed(self, event_id: UUID, error: str) -> None:
        await self._session.execute(
            text(
                "UPDATE outbox_events SET attempts = attempts + 1, last_error = :error, dispatch_lease_expires_at = NULL, "
                "next_attempt_at = now() + (least(3600, power(2, attempts + 1)::integer) * interval '1 second'), "
                "dead_lettered_at = CASE WHEN attempts + 1 >= 10 THEN now() ELSE NULL END "
                "WHERE id = :id"
            ),
            {"id": event_id, "error": error[:1_000]},
        )


async def publish_claimed(outbox: SqlAlchemyOutbox, dispatcher: EventDispatcher) -> int:
    """Dispatch every claimed event, recording outcome for retry without loss."""
    published = 0
    for event in await outbox.claim():
        try:
            await dispatcher.dispatch(event)
        except Exception as error:
            await outbox.mark_failed(event.id, type(error).__name__)
        else:
            await outbox.mark_published(event.id)
            published += 1
    return published
