"""Orchestrator for notification dispatches, quiet hours routing, and deduplication throttling."""

from __future__ import annotations

import hashlib
from datetime import datetime
from uuid import UUID

from aether.infrastructure.persistence.notifications_repository import (
    SqlAlchemyNotificationsRepository,
)
from aether.notifications.policy import NotificationPolicyEvaluator


class NotificationService:
    def __init__(self, repository: SqlAlchemyNotificationsRepository) -> None:
        self._repository = repository

    async def dispatch_notification(
        self,
        org: UUID,
        user: UUID,
        title: str,
        message: str,
        level: str,
    ) -> UUID | None:
        """Evaluate preferences, quiet hours, and deduplication. Registers and delivers log."""
        # 1. Deduplication Guard (5-minute sliding window)
        raw_hash = f"{title}:{message}:{user}"
        dedupe_hash = hashlib.sha256(raw_hash.encode("utf-8")).hexdigest()

        last_matching = await self._repository.get_last_matching_notification(
            dedupe_hash, window_seconds=300
        )
        if last_matching is not None:
            # Throttle duplicate alerts
            return None

        # 2. Retrieve user preferences
        prefs = await self._repository.get_preferences(org, user)
        if prefs["unsubscribed"]:
            return None

        # 3. Quiet Hours evaluation
        current_dt = datetime.now()  # Use local system time matching DB time formats
        current_time = current_dt.time()

        policy = NotificationPolicyEvaluator()
        in_quiet_hours = policy.is_in_quiet_hours(
            prefs["quiet_hours_start"], prefs["quiet_hours_end"], current_time
        )

        sent_channels = policy.determine_active_channels(
            prefs["channels"], in_quiet_hours
        )

        # 4. Save notification
        notification_id = await self._repository.create_notification(
            org,
            user,
            title,
            message,
            level,
            sent_channels,
            dedupe_hash,
        )

        # 5. Dispatch via adapters (Mock channels execution)
        for channel in sent_channels:
            if channel == "email":
                # Mock email send action
                pass
            elif channel == "push":
                # Mock push action
                pass

        return notification_id
