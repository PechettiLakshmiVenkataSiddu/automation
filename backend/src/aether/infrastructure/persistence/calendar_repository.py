"""PostgreSQL persistence authority for Google Calendar connections, events, and proposals."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyCalendarRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_connection(
        self,
        org: UUID,
        user: UUID,
        provider: str,
        access: str,
        refresh: str,
        scopes: list[str],
        permitted: list[str],
        expires_at: datetime,
    ) -> UUID:
        connection_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO calendar_connections (
                id, organization_id, user_id, provider, access_token,
                refresh_token, scopes, permitted_calendars, expires_at
            )
            VALUES (
                :id, :org, :user, :provider, :access, :refresh, :scopes, :permitted,
                :expires_at
            )
            ON CONFLICT (organization_id, user_id) DO UPDATE
            SET access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                scopes = EXCLUDED.scopes,
                permitted_calendars = EXCLUDED.permitted_calendars,
                status = 'active',
                expires_at = EXCLUDED.expires_at,
                updated_at = now()
            """),
            {
                "id": connection_id,
                "org": org,
                "user": user,
                "provider": provider,
                "access": access,
                "refresh": refresh,
                "scopes": scopes,
                "permitted": permitted,
                "expires_at": expires_at,
            },
        )
        return connection_id

    async def get_connection(self, org: UUID, user: UUID) -> dict[str, Any] | None:
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, user_id, provider, access_token,
                       refresh_token, scopes, permitted_calendars, status, expires_at,
                       created_at, updated_at
                FROM calendar_connections
                WHERE user_id = :user AND organization_id = :org AND status = 'active'
                """),
                {"user": user, "org": org},
            )
        ).mappings().one_or_none()
        return dict(row) if row else None

    async def revoke_connection(self, org: UUID, user: UUID) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE calendar_connections
            SET status = 'revoked', updated_at = now()
            WHERE user_id = :user AND organization_id = :org
            """),
            {"user": user, "org": org},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

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
        await self._session.execute(
            text("""
            INSERT INTO calendar_events (
                id, organization_id, user_id, google_event_id, summary,
                description, start_time, end_time, attendees, status
            )
            VALUES (:id, :org, :user, :google_event_id, :summary, :description,
                    :start_time, :end_time, CAST(:attendees AS jsonb), :status)
            ON CONFLICT (organization_id, google_event_id) DO UPDATE
            SET summary = EXCLUDED.summary,
                description = EXCLUDED.description,
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time,
                attendees = EXCLUDED.attendees,
                status = EXCLUDED.status,
                updated_at = now()
            """),
            {
                "id": event_id,
                "org": org,
                "user": user,
                "google_event_id": google_event_id,
                "summary": summary,
                "description": description,
                "start_time": start_time,
                "end_time": end_time,
                "attendees": json.dumps(attendees),
                "status": status,
            },
        )
        return event_id

    async def get_events_in_range(
        self, org: UUID, start_time: datetime, end_time: datetime
    ) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, organization_id, user_id, google_event_id, summary,
                   description, start_time, end_time, attendees, status, created_at, updated_at
            FROM calendar_events
            WHERE organization_id = :org AND status <> 'cancelled' AND (
                (start_time >= :start_time AND start_time < :end_time) OR
                (end_time > :start_time AND end_time <= :end_time) OR
                (start_time <= :start_time AND end_time >= :end_time)
            )
            ORDER BY start_time ASC
            """),
            {"org": org, "start_time": start_time, "end_time": end_time},
        )
        return [dict(row) for row in result.mappings().all()]

    async def create_proposal(
        self,
        org: UUID,
        user: UUID,
        summary: str,
        description: str | None,
        start_time: datetime,
        end_time: datetime,
        attendees: list[dict[str, Any]],
        conflict_detected: bool,
    ) -> UUID:
        proposal_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO calendar_proposals (
                id, organization_id, user_id, summary, description,
                start_time, end_time, attendees, status, conflict_detected
            )
            VALUES (:id, :org, :user, :summary, :description, :start_time,
                    :end_time, CAST(:attendees AS jsonb), 'pending', :conflict)
            """),
            {
                "id": proposal_id,
                "org": org,
                "user": user,
                "summary": summary,
                "description": description,
                "start_time": start_time,
                "end_time": end_time,
                "attendees": json.dumps(attendees),
                "conflict": conflict_detected,
            },
        )
        return proposal_id

    async def update_proposal_status(
        self, org: UUID, proposal_id: UUID, status: str, reason: str | None = None
    ) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE calendar_proposals
            SET status = :status, decision_reason = :reason, updated_at = now()
            WHERE id = :proposal_id AND organization_id = :org
            """),
            {"proposal_id": proposal_id, "org": org, "status": status, "reason": reason},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def get_proposal(self, org: UUID, proposal_id: UUID) -> dict[str, Any] | None:
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, user_id, summary, description,
                       start_time, end_time, attendees, status, conflict_detected,
                       decision_reason, created_at, updated_at
                FROM calendar_proposals
                WHERE id = :proposal_id AND organization_id = :org
                """),
                {"proposal_id": proposal_id, "org": org},
            )
        ).mappings().one_or_none()
        return dict(row) if row else None

    async def get_proposals(self, org: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, organization_id, user_id, summary, description,
                   start_time, end_time, attendees, status, conflict_detected,
                   decision_reason, created_at, updated_at
            FROM calendar_proposals
            WHERE organization_id = :org
            ORDER BY created_at DESC
            """),
            {"org": org},
        )
        return [dict(row) for row in result.mappings().all()]
