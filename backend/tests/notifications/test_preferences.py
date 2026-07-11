from __future__ import annotations

from datetime import time
from typing import Any
from uuid import UUID, uuid4

import pytest


class FakeNotificationsRepository:
    def __init__(self) -> None:
        self.preferences: dict[UUID, dict[str, Any]] = {}

    async def upsert_preferences(
        self,
        org: UUID,
        user: UUID,
        channels: list[str],
        quiet_hours_start: time | None,
        quiet_hours_end: time | None,
        unsubscribed: bool,
    ) -> UUID:
        pref_id = uuid4()
        self.preferences[user] = {
            "id": pref_id,
            "organization_id": org,
            "user_id": user,
            "channels": channels,
            "quiet_hours_start": quiet_hours_start,
            "quiet_hours_end": quiet_hours_end,
            "unsubscribed": unsubscribed,
        }
        return pref_id

    async def get_preferences(self, org: UUID, user: UUID) -> dict[str, Any]:
        return self.preferences.get(user, {
            "channels": ["in_app"],
            "quiet_hours_start": None,
            "quiet_hours_end": None,
            "unsubscribed": False,
        })


@pytest.mark.asyncio
async def test_notifications_preferences_defaults_and_crud() -> None:
    repo = FakeNotificationsRepository()
    org_id, user_id = uuid4(), uuid4()

    # Get defaults
    default_prefs = await repo.get_preferences(org_id, user_id)
    assert default_prefs["channels"] == ["in_app"]
    assert default_prefs["quiet_hours_start"] is None
    assert default_prefs["unsubscribed"] is False

    # Update preferences
    await repo.upsert_preferences(
        org_id,
        user_id,
        ["in_app", "email"],
        time(23, 0),
        time(7, 0),
        False
    )

    updated_prefs = await repo.get_preferences(org_id, user_id)
    assert updated_prefs["channels"] == ["in_app", "email"]
    assert updated_prefs["quiet_hours_start"] == time(23, 0)
    assert updated_prefs["unsubscribed"] is False
