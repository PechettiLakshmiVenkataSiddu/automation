from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest


class FakeNotificationsRepository:
    def __init__(self) -> None:
        self.notifications: dict[UUID, dict[str, Any]] = {}

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
        self.notifications[notif_id] = {
            "id": notif_id,
            "organization_id": org,
            "user_id": user,
            "title": title,
            "message": message,
            "level": level,
            "status": "unread",
            "sent_channels": sent_channels,
            "dedupe_hash": dedupe_hash,
        }
        return notif_id

    async def mark_read(self, org: UUID, notification_id: UUID) -> bool:
        if notification_id not in self.notifications:
            return False
        notif = self.notifications[notification_id]
        if notif["organization_id"] != org:
            return False
        notif["status"] = "read"
        return True


@pytest.mark.asyncio
async def test_notifications_read_toggle_and_scoping() -> None:
    repo = FakeNotificationsRepository()
    org1, org2, user_id = uuid4(), uuid4(), uuid4()

    # Create unread notification under org1
    notif_id = await repo.create_notification(
        org1, user_id, "Hello", "Content", "info", ["in_app"], None
    )
    assert repo.notifications[notif_id]["status"] == "unread"

    # Attempt to mark read under org2 (should fail scoping check)
    scoped_fail = await repo.mark_read(org2, notif_id)
    assert scoped_fail is False
    assert repo.notifications[notif_id]["status"] == "unread"

    # Mark read under correct org1 (should succeed)
    scoped_success = await repo.mark_read(org1, notif_id)
    assert scoped_success is True
    assert repo.notifications[notif_id]["status"] == "read"
