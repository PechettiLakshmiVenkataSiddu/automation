from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.calendar.service import CalendarSyncService


class FakeCalendarRepository:
    """Mock calendar repository for synchronous database-free unit testing."""

    def __init__(self) -> None:
        self.connections: dict[UUID, dict[str, Any]] = {}
        self.events: dict[str, dict[str, Any]] = {}
        self.proposals: dict[UUID, dict[str, Any]] = {}

    async def get_connection(self, org: UUID, user: UUID) -> dict[str, Any] | None:
        return self.connections.get(user)

    async def upsert_event(
        self,
        org: UUID,
        user: UUID,
        google_event_id: str,
        summary: str,
        description: str | None,
        start_time: datetime,
        end_time: datetime,
        attendees: list[dict[str, Any]],
        status: str,
    ) -> UUID:
        event_id = uuid4()
        self.events[google_event_id] = {
            "id": event_id,
            "organization_id": org,
            "user_id": user,
            "google_event_id": google_event_id,
            "summary": summary,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "attendees": attendees,
            "status": status,
        }
        return event_id

    async def get_events_in_range(
        self, org: UUID, start_time: datetime, end_time: datetime
    ) -> list[dict[str, Any]]:
        return [
            ev
            for ev in self.events.values()
            if ev["organization_id"] == org
            and ev["status"] != "cancelled"
            and (
                (ev["start_time"] >= start_time and ev["start_time"] < end_time)
                or (ev["end_time"] > start_time and ev["end_time"] <= end_time)
                or (ev["start_time"] <= start_time and ev["end_time"] >= end_time)
            )
        ]


@pytest.mark.asyncio
async def test_calendar_sync_successful_cache() -> None:
    repo = FakeCalendarRepository()
    service = CalendarSyncService(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    # Enable connection
    repo.connections[user_id] = {
        "permitted_calendars": ["*"],
        "scopes": ["https://www.googleapis.com/auth/calendar"],
    }

    synced = await service.sync_events(org_id, user_id)
    assert synced == 1
    assert "google-mock-event-1" in repo.events
    assert repo.events["google-mock-event-1"]["summary"] == "Synchronized Status Meeting"
