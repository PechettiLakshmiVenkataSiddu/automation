"""PostgreSQL persistence authority for notification logs and preferences."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyNotificationsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        await self._session.execute(
            text("""
            INSERT INTO notification_preferences (
                id, organization_id, user_id, channels,
                quiet_hours_start, quiet_hours_end, unsubscribed
            )
            VALUES (
                :id, :org, :user, :channels, :quiet_hours_start, :quiet_hours_end, :unsubscribed
            )
            ON CONFLICT (organization_id, user_id) DO UPDATE
            SET channels = EXCLUDED.channels,
                quiet_hours_start = EXCLUDED.quiet_hours_start,
                quiet_hours_end = EXCLUDED.quiet_hours_end,
                unsubscribed = EXCLUDED.unsubscribed,
                updated_at = now()
            """),
            {
                "id": pref_id,
                "org": org,
                "user": user,
                "channels": channels,
                "quiet_hours_start": quiet_hours_start,
                "quiet_hours_end": quiet_hours_end,
                "unsubscribed": unsubscribed,
            },
        )
        return pref_id

    async def get_preferences(self, org: UUID, user: UUID) -> dict[str, Any]:
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, user_id, channels,
                       quiet_hours_start, quiet_hours_end, unsubscribed
                FROM notification_preferences
                WHERE user_id = :user AND organization_id = :org
                """),
                {"user": user, "org": org},
            )
        ).mappings().one_or_none()

        if row:
            return dict(row)

        # Default fallback settings
        return {
            "id": None,
            "organization_id": org,
            "user_id": user,
            "channels": ["in_app"],
            "quiet_hours_start": None,
            "quiet_hours_end": None,
            "unsubscribed": False,
        }

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
        notification_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO notifications (
                id, organization_id, user_id, title, message,
                level, status, sent_channels, dedupe_hash
            )
            VALUES (
                :id, :org, :user, :title, :message, :level, 'unread', :sent_channels, :dedupe_hash
            )
            """),
            {
                "id": notification_id,
                "org": org,
                "user": user,
                "title": title,
                "message": message,
                "level": level,
                "sent_channels": sent_channels,
                "dedupe_hash": dedupe_hash,
            },
        )
        return notification_id

    async def get_active_notifications(self, org: UUID, user: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, organization_id, user_id, title, message,
                   level, status, sent_channels, created_at, updated_at
            FROM notifications
            WHERE user_id = :user AND organization_id = :org
            ORDER BY created_at DESC
            """),
            {"user": user, "org": org},
        )
        return [dict(row) for row in result.mappings().all()]

    async def mark_read(self, org: UUID, notification_id: UUID) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE notifications
            SET status = 'read', updated_at = now()
            WHERE id = :notification_id AND organization_id = :org
            """),
            {"notification_id": notification_id, "org": org},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def get_last_matching_notification(
        self, dedupe_hash: str, window_seconds: int
    ) -> dict[str, Any] | None:
        threshold = datetime.now(UTC) - timedelta(seconds=window_seconds)
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, user_id, title, message,
                       level, status, sent_channels, created_at, updated_at
                FROM notifications
                WHERE dedupe_hash = :hash AND created_at >= :threshold
                ORDER BY created_at DESC
                LIMIT 1
                """),
                {"hash": dedupe_hash, "threshold": threshold},
            )
        ).mappings().one_or_none()
        return dict(row) if row else None
class SqlAlchemyNotificationsRepositoryManager:
    """Namespace container class for helper methods."""
    pass
