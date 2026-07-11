"""PostgreSQL persistence authority for Slack/Teams integrations."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyChatRepository:
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
        expires_at: datetime,
    ) -> UUID:
        connection_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO chat_connections (
                id, organization_id, user_id, provider, access_token,
                refresh_token, scopes, expires_at
            )
            VALUES (
                :id, :org, :user, :provider, :access, :refresh, :scopes, :expires_at
            )
            ON CONFLICT (organization_id, user_id, provider) DO UPDATE
            SET access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                scopes = EXCLUDED.scopes,
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
                "expires_at": expires_at,
            },
        )
        return connection_id

    async def get_connection(self, org: UUID, user: UUID, provider: str) -> dict[str, Any] | None:
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, user_id, provider, access_token,
                       refresh_token, scopes, status, expires_at, created_at, updated_at
                FROM chat_connections
                WHERE user_id = :user
                  AND organization_id = :org
                  AND provider = :provider
                  AND status = 'active'
                """),
                {"user": user, "org": org, "provider": provider},
            )
        ).mappings().one_or_none()
        return dict(row) if row else None

    async def revoke_connection(self, org: UUID, user: UUID, provider: str) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE chat_connections
            SET status = 'revoked', updated_at = now()
            WHERE user_id = :user AND organization_id = :org AND provider = :provider
            """),
            {"user": user, "org": org, "provider": provider},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def upsert_message(
        self,
        org: UUID,
        user: UUID,
        provider: str,
        channel_id: str,
        thread_ts: str | None,
        message_text: str,
        sender_id: str,
        status: str,
        received_at: datetime,
    ) -> UUID:
        message_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO chat_messages (
                id, organization_id, user_id, provider, channel_id,
                thread_ts, message_text, sender_id, status, received_at
            )
            VALUES (
                :id, :org, :user, :provider, :channel_id, :thread_ts,
                :message_text, :sender_id, :status, :received_at
            )
            """),
            {
                "id": message_id,
                "org": org,
                "user": user,
                "provider": provider,
                "channel_id": channel_id,
                "thread_ts": thread_ts,
                "message_text": message_text,
                "sender_id": sender_id,
                "status": status,
                "received_at": received_at,
            },
        )
        return message_id

    async def get_messages(self, org: UUID, channel_id: str) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, provider, channel_id, thread_ts, message_text,
                   sender_id, status, received_at, created_at, updated_at
            FROM chat_messages
            WHERE organization_id = :org AND channel_id = :channel_id
            ORDER BY received_at ASC
            """),
            {"org": org, "channel_id": channel_id},
        )
        return [dict(row) for row in result.mappings().all()]

    async def create_proposal(
        self,
        org: UUID,
        user: UUID,
        channel_id: str,
        message_text: str,
    ) -> UUID:
        proposal_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO chat_proposals (
                id, organization_id, user_id, channel_id, message_text, status
            )
            VALUES (
                :id, :org, :user, :channel_id, :message_text, 'pending'
            )
            """),
            {
                "id": proposal_id,
                "org": org,
                "user": user,
                "channel_id": channel_id,
                "message_text": message_text,
            },
        )
        return proposal_id

    async def update_proposal_status(
        self,
        org: UUID,
        proposal_id: UUID,
        status: str,
        approved_by: UUID | None = None,
        reason: str | None = None,
    ) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE chat_proposals
            SET status = :status, approved_by_user_id = :approved_by,
                decision_reason = :reason, updated_at = now()
            WHERE id = :proposal_id AND organization_id = :org
            """),
            {
                "proposal_id": proposal_id,
                "org": org,
                "status": status,
                "approved_by": approved_by,
                "reason": reason,
            },
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def get_proposal(self, org: UUID, proposal_id: UUID) -> dict[str, Any] | None:
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, user_id, channel_id, message_text,
                       status, approved_by_user_id, decision_reason, created_at, updated_at
                FROM chat_proposals
                WHERE id = :proposal_id AND organization_id = :org
                """),
                {"proposal_id": proposal_id, "org": org},
            )
        ).mappings().one_or_none()
        return dict(row) if row else None

    async def get_proposals(self, org: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, organization_id, user_id, channel_id, message_text,
                   status, approved_by_user_id, decision_reason, created_at, updated_at
            FROM chat_proposals
            WHERE organization_id = :org
            ORDER BY created_at DESC
            """),
            {"org": org},
        )
        return [dict(row) for row in result.mappings().all()]
