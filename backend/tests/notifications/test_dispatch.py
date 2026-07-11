from __future__ import annotations

from datetime import UTC, datetime, time
from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.notifications.policy import NotificationPolicyEvaluator
from aether.notifications.service import NotificationService


class FakeNotificationsRepository:
    """Mock notification repository for synchronous unit testing."""

    def __init__(self) -> None:
        self.preferences: dict[UUID, dict[str, Any]] = {}
        self.notifications: list[dict[str, Any]] = []

    async def get_preferences(self, org: UUID, user: UUID) -> dict[str, Any]:
        return self.preferences.get(user, {
            "channels": ["in_app"],
            "quiet_hours_start": None,
            "quiet_hours_end": None,
            "unsubscribed": False,
        })

    async def get_last_matching_notification(
        self, dedupe_hash: str, window_seconds: int
    ) -> dict[str, Any] | None:
        # Simple list search
        for notif in reversed(self.notifications):
            if notif["dedupe_hash"] == dedupe_hash:
                return notif
        return None

    async def create_notification(
        self,
        org: UUID,
        user: UUID,
        title: str,
        message: str,
        level: str,
        sent_channels: list[str],
        dedupe_hash: str | None,
    ) -> UUID:
        notif_id = uuid4()
        self.notifications.append({
            "id": notif_id,
            "organization_id": org,
            "user_id": user,
            "title": title,
            "message": message,
            "level": level,
            "sent_channels": sent_channels,
            "dedupe_hash": dedupe_hash,
            "created_at": datetime.now(UTC),
        })
        return notif_id


def test_notifications_quiet_hours_midnight_crossings() -> None:
    policy = NotificationPolicyEvaluator()

    # Standard quiet window (no crossing)
    assert policy.is_in_quiet_hours(time(22, 0), time(23, 30), time(22, 30)) is True
    assert policy.is_in_quiet_hours(time(22, 0), time(23, 30), time(21, 0)) is False

    # Quiet window crossing midnight (e.g. 22:00 to 06:00)
    assert policy.is_in_quiet_hours(time(22, 0), time(6, 0), time(23, 0)) is True
    assert policy.is_in_quiet_hours(time(22, 0), time(6, 0), time(2, 0)) is True
    assert policy.is_in_quiet_hours(time(22, 0), time(6, 0), time(12, 0)) is False


@pytest.mark.asyncio
async def test_notifications_service_unsubscribed() -> None:
    repo = FakeNotificationsRepository()
    service = NotificationService(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    repo.preferences[user_id] = {
        "channels": ["in_app", "email"],
        "quiet_hours_start": None,
        "quiet_hours_end": None,
        "unsubscribed": True,  # User opted out
    }

    result_id = await service.dispatch_notification(org_id, user_id, "Alert", "Body", "info")
    assert result_id is None
    assert len(repo.notifications) == 0


@pytest.mark.asyncio
async def test_notifications_service_deduplication() -> None:
    repo = FakeNotificationsRepository()
    service = NotificationService(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    # Initial dispatch
    id1 = await service.dispatch_notification(
        org_id, user_id, "Workflow Error", "Connection failed", "error"
    )
    assert id1 is not None
    assert len(repo.notifications) == 1

    # Sequential identical dispatch (should dedupe/ignore within 5 minutes)
    id2 = await service.dispatch_notification(
        org_id, user_id, "Workflow Error", "Connection failed", "error"
    )
    assert id2 is None
    assert len(repo.notifications) == 1
