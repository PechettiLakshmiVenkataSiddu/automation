"""PostgreSQL persistence authority for Gmail connections, inbox/sent messages, and drafts."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyEmailRepository:
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
            INSERT INTO email_connections (
                id, organization_id, user_id, provider, access_token,
                refresh_token, scopes, expires_at
            )
            VALUES (:id, :org, :user, :provider, :access, :refresh, :scopes, :expires_at)
            ON CONFLICT (organization_id, user_id) DO UPDATE
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

    async def get_connection(self, org: UUID, user: UUID) -> dict[str, Any] | None:
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, user_id, provider, access_token,
                       refresh_token, scopes, status, expires_at, created_at, updated_at
                FROM email_connections
                WHERE user_id = :user AND organization_id = :org AND status = 'active'
                """),
                {"user": user, "org": org},
            )
        ).mappings().one_or_none()
        return dict(row) if row else None

    async def revoke_connection(self, org: UUID, user: UUID) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE email_connections
            SET status = 'revoked', updated_at = now()
            WHERE user_id = :user AND organization_id = :org
            """),
            {"user": user, "org": org},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def upsert_message(
        self,
        org: UUID,
        user: UUID,
        google_message_id: str,
        thread_id: str,
        from_address: str,
        to_addresses: list[str],
        subject: str | None,
        body_snippet: str | None,
        body_text: str | None,
        status: str,
        received_at: datetime,
    ) -> UUID:
        message_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO email_messages (
                id, organization_id, user_id, google_message_id, thread_id,
                from_address, to_addresses, subject, body_snippet, body_text,
                status, received_at
            )
            VALUES (:id, :org, :user, :google_message_id, :thread_id, :from_address,
                    :to_addresses, :subject, :snippet, :body, :status, :received_at)
            ON CONFLICT (organization_id, google_message_id) DO UPDATE
            SET summary = EXCLUDED.subject,
                body_snippet = EXCLUDED.body_snippet,
                body_text = EXCLUDED.body_text,
                status = EXCLUDED.status,
                updated_at = now()
            """),
            {
                "id": message_id,
                "org": org,
                "user": user,
                "google_message_id": google_message_id,
                "thread_id": thread_id,
                "from_address": from_address,
                "to_addresses": to_addresses,
                "subject": subject,
                "snippet": body_snippet,
                "body": body_text,
                "status": status,
                "received_at": received_at,
            },
        )
        return message_id

    async def get_messages(self, org: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, google_message_id, thread_id, from_address, to_addresses,
                   subject, body_snippet, body_text, status, received_at, created_at, updated_at
            FROM email_messages
            WHERE organization_id = :org
            ORDER BY received_at DESC
            """),
            {"org": org},
        )
        return [dict(row) for row in result.mappings().all()]

    async def create_proposal(
        self,
        org: UUID,
        user: UUID,
        recipient_address: str,
        subject: str | None,
        body_text: str,
        attachments: list[dict[str, Any]],
    ) -> UUID:
        proposal_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO email_proposals (
                id, organization_id, user_id, recipient_address, subject,
                body_text, attachments, status
            )
            VALUES (
                :id, :org, :user, :recipient, :subject, :body,
                CAST(:attachments AS jsonb), 'pending'
            )
            """),
            {
                "id": proposal_id,
                "org": org,
                "user": user,
                "recipient": recipient_address,
                "subject": subject,
                "body": body_text,
                "attachments": json.dumps(attachments),
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
            UPDATE email_proposals
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
                SELECT id, organization_id, user_id, recipient_address, subject,
                       body_text, attachments, status, approved_by_user_id,
                       decision_reason, created_at, updated_at
                FROM email_proposals
                WHERE id = :proposal_id AND organization_id = :org
                """),
                {"proposal_id": proposal_id, "org": org},
            )
        ).mappings().one_or_none()
        return dict(row) if row else None

    async def get_proposals(self, org: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, organization_id, user_id, recipient_address, subject,
                   body_text, attachments, status, approved_by_user_id,
                   decision_reason, created_at, updated_at
            FROM email_proposals
            WHERE organization_id = :org
            ORDER BY created_at DESC
            """),
            {"org": org},
        )
        return [dict(row) for row in result.mappings().all()]
