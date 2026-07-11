"""PostgreSQL persistence authority for admin control room settings."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_policy(self, org: UUID) -> dict[str, Any]:
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, retention_days_notifications,
                       retention_days_audit_logs, allow_unsecure_sandboxes,
                       break_glass_active, break_glass_reason, break_glass_activated_at
                FROM system_policies
                WHERE organization_id = :org
                """),
                {"org": org},
            )
        ).mappings().one_or_none()

        if row:
            return dict(row)

        # Default fallback policy settings
        return {
            "id": None,
            "organization_id": org,
            "retention_days_notifications": 30,
            "retention_days_audit_logs": 365,
            "allow_unsecure_sandboxes": False,
            "break_glass_active": False,
            "break_glass_reason": None,
            "break_glass_activated_at": None,
        }

    async def upsert_policy(
        self,
        org: UUID,
        retention_notifs: int,
        retention_audit: int,
        allow_unsecure: bool,
    ) -> UUID:
        policy_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO system_policies (
                id, organization_id, retention_days_notifications,
                retention_days_audit_logs, allow_unsecure_sandboxes
            )
            VALUES (
                :id, :org, :retention_notifs, :retention_audit, :allow_unsecure
            )
            ON CONFLICT (organization_id) DO UPDATE
            SET retention_days_notifications = EXCLUDED.retention_days_notifications,
                retention_days_audit_logs = EXCLUDED.retention_days_audit_logs,
                allow_unsecure_sandboxes = EXCLUDED.allow_unsecure_sandboxes,
                updated_at = now()
            """),
            {
                "id": policy_id,
                "org": org,
                "retention_notifs": retention_notifs,
                "retention_audit": retention_audit,
                "allow_unsecure": allow_unsecure,
            },
        )
        return policy_id

    async def set_break_glass(self, org: UUID, active: bool, reason: str | None) -> bool:
        activated_at = datetime.now(UTC) if active else None
        result = await self._session.execute(
            text("""
            INSERT INTO system_policies (
                id, organization_id, break_glass_active,
                break_glass_reason, break_glass_activated_at
            )
            VALUES (
                gen_random_uuid(), :org, :active, :reason, :activated_at
            )
            ON CONFLICT (organization_id) DO UPDATE
            SET break_glass_active = EXCLUDED.break_glass_active,
                break_glass_reason = EXCLUDED.break_glass_reason,
                break_glass_activated_at = EXCLUDED.break_glass_activated_at,
                updated_at = now()
            """),
            {
                "org": org,
                "active": active,
                "reason": reason,
                "activated_at": activated_at,
            },
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def get_members(self, org: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT m.user_id, u.email, m.role, m.status, m.created_at
            FROM memberships m
            JOIN users u ON m.user_id = u.id
            WHERE m.organization_id = :org
            ORDER BY m.created_at ASC
            """),
            {"org": org},
        )
        return [dict(row) for row in result.mappings().all()]

    async def upsert_membership(self, org: UUID, user_id: UUID, role: str) -> bool:
        result = await self._session.execute(
            text("""
            INSERT INTO memberships (organization_id, user_id, role, status)
            VALUES (:org, :user_id, :role, 'active')
            ON CONFLICT (organization_id, user_id) DO UPDATE
            SET role = EXCLUDED.role, updated_at = now()
            """),
            {"org": org, "user_id": user_id, "role": role},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def delete_membership(self, org: UUID, user_id: UUID) -> bool:
        result = await self._session.execute(
            text("""
            DELETE FROM memberships
            WHERE organization_id = :org AND user_id = :user_id
            """),
            {"org": org, "user_id": user_id},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def get_api_keys(self, org: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, organization_id, created_by_user_id, name,
                   key_prefix, last_used_at, expires_at, revoked_at, created_at
            FROM api_keys
            WHERE organization_id = :org
            ORDER BY created_at DESC
            """),
            {"org": org},
        )
        return [dict(row) for row in result.mappings().all()]

    async def create_api_key(
        self,
        org: UUID,
        user_id: UUID,
        name: str,
        key_prefix: str,
        secret_hash: str,
        expires_at: datetime | None,
    ) -> UUID:
        key_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO api_keys (
                id, organization_id, created_by_user_id, name,
                key_prefix, secret_hash, expires_at
            )
            VALUES (
                :id, :org, :user_id, :name, :key_prefix, :secret_hash, :expires_at
            )
            """),
            {
                "id": key_id,
                "org": org,
                "user_id": user_id,
                "name": name,
                "key_prefix": key_prefix,
                "secret_hash": secret_hash,
                "expires_at": expires_at,
            },
        )
        return key_id

    async def revoke_api_key(self, org: UUID, key_id: UUID) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE api_keys
            SET revoked_at = now()
            WHERE id = :key_id AND organization_id = :org AND revoked_at IS NULL
            """),
            {"key_id": key_id, "org": org},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def get_connections(self, org: UUID) -> list[dict[str, Any]]:
        # Union email_connections, calendar_connections, chat_connections
        result = await self._session.execute(
            text("""
            SELECT id, organization_id, provider, scopes, status, created_at
            FROM email_connections WHERE organization_id = :org AND status = 'active'
            UNION ALL
            SELECT id, organization_id, provider, scopes, status, created_at
            FROM calendar_connections WHERE organization_id = :org AND status = 'active'
            UNION ALL
            SELECT id, organization_id, provider, scopes, status, created_at
            FROM chat_connections WHERE organization_id = :org AND status = 'active'
            ORDER BY created_at DESC
            """),
            {"org": org},
        )
        return [dict(row) for row in result.mappings().all()]

    async def delete_connection(self, org: UUID, provider: str) -> bool:
        # Revoke across all tables
        result1 = await self._session.execute(
            text("UPDATE email_connections SET status = 'revoked', updated_at = now() "
                 "WHERE organization_id = :org AND provider = :provider AND status = 'active'"),
            {"org": org, "provider": provider},
        )
        result2 = await self._session.execute(
            text("UPDATE calendar_connections SET status = 'revoked', updated_at = now() "
                 "WHERE organization_id = :org AND provider = :provider AND status = 'active'"),
            {"org": org, "provider": provider},
        )
        result3 = await self._session.execute(
            text("UPDATE chat_connections SET status = 'revoked', updated_at = now() "
                 "WHERE organization_id = :org AND provider = :provider AND status = 'active'"),
            {"org": org, "provider": provider},
        )
        return bool(result1.rowcount or result2.rowcount or result3.rowcount)  # type: ignore[attr-defined]

    async def search_audit_events(
        self,
        org: UUID,
        event_type: str | None,
        target_type: str | None,
        actor_user_id: UUID | None,
    ) -> list[dict[str, Any]]:
        query = """
        SELECT id, organization_id, actor_user_id, delegated_actor,
               event_type, target_type, target_id, outcome,
               policy_version, correlation_id, metadata, occurred_at
        FROM audit_events
        WHERE organization_id = :org
        """
        params: dict[str, Any] = {"org": org}

        if event_type:
            query += " AND event_type = :event_type"
            params["event_type"] = event_type
        if target_type:
            query += " AND target_type = :target_type"
            params["target_type"] = target_type
        if actor_user_id:
            query += " AND actor_user_id = :actor_user_id"
            params["actor_user_id"] = actor_user_id

        query += " ORDER BY occurred_at DESC LIMIT 100"

        result = await self._session.execute(text(query), params)
        return [dict(row) for row in result.mappings().all()]

    async def create_audit_event(
        self,
        org: UUID,
        actor_id: UUID | None,
        event_type: str,
        target_type: str,
        target_id: UUID | None,
        outcome: str,
        correlation_id: UUID,
        metadata: dict[str, Any],
    ) -> UUID:
        event_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO audit_events (
                id, organization_id, actor_user_id, event_type,
                target_type, target_id, outcome, correlation_id, metadata
            )
            VALUES (
                :id, :org, :actor_id, :event_type, :target_type,
                :target_id, :outcome, :correlation_id, :metadata
            )
            """),
            {
                "id": event_id,
                "org": org,
                "actor_id": actor_id,
                "event_type": event_type,
                "target_type": target_type,
                "target_id": target_id,
                "outcome": outcome,
                "correlation_id": correlation_id,
                "metadata": metadata,
            },
        )
        return event_id
class SqlAlchemyAdminRepositoryManager:
    """Namespace container class for helper methods."""
    pass
