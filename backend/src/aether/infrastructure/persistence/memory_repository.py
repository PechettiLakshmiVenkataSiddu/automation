"""SQLAlchemy implementation of the memory repository port."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import CursorResult, text
from sqlalchemy.ext.asyncio import AsyncSession

from aether.memory.models import Memory, MemoryConsent


class SqlAlchemyMemoryRepository:
    """Uses organization and user predicates on every memory query."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_consent(self, organization_id: UUID, user_id: UUID) -> MemoryConsent | None:
        result = await self._session.execute(
            text(
                "SELECT enabled, policy_version, updated_at FROM memory_consents WHERE organization_id = :organization_id AND user_id = :user_id"
            ),
            {"organization_id": organization_id, "user_id": user_id},
        )
        row = result.mappings().one_or_none()
        return (
            None
            if row is None
            else MemoryConsent(
                organization_id, user_id, row["enabled"], row["policy_version"], row["updated_at"]
            )
        )

    async def set_consent(self, consent: MemoryConsent, changed_at: datetime) -> MemoryConsent:
        await self._session.execute(
            text(
                "INSERT INTO memory_consents (organization_id, user_id, enabled, policy_version, granted_at, withdrawn_at, updated_at) VALUES (:organization_id, :user_id, :enabled, :policy_version, :granted_at, :withdrawn_at, :updated_at) ON CONFLICT (organization_id, user_id) DO UPDATE SET enabled = EXCLUDED.enabled, policy_version = EXCLUDED.policy_version, granted_at = EXCLUDED.granted_at, withdrawn_at = EXCLUDED.withdrawn_at, updated_at = EXCLUDED.updated_at"
            ),
            {
                "organization_id": consent.organization_id,
                "user_id": consent.user_id,
                "enabled": consent.enabled,
                "policy_version": consent.policy_version,
                "granted_at": changed_at if consent.enabled else None,
                "withdrawn_at": None if consent.enabled else changed_at,
                "updated_at": changed_at,
            },
        )
        return consent

    async def create(self, memory: Memory) -> Memory:
        await self._session.execute(
            text(
                "INSERT INTO memories (id, organization_id, user_id, memory_type, content, source_reference, expires_at) VALUES (:id, :organization_id, :user_id, :memory_type, CAST(:content AS jsonb), CAST(:source_reference AS jsonb), :expires_at)"
            ),
            {
                "id": memory.id,
                "organization_id": memory.organization_id,
                "user_id": memory.user_id,
                "memory_type": memory.memory_type,
                "content": json.dumps({"text": memory.text}),
                "source_reference": json.dumps(memory.source_reference),
                "expires_at": memory.expires_at,
            },
        )
        return memory

    async def get(self, organization_id: UUID, user_id: UUID, memory_id: UUID) -> Memory | None:
        result = await self._session.execute(
            text(
                "SELECT id, organization_id, user_id, memory_type, content, source_reference, confidence, expires_at, retention_until, created_at, updated_at FROM memories WHERE id = :id AND organization_id = :organization_id AND user_id = :user_id AND deleted_at IS NULL"
            ),
            {"id": memory_id, "organization_id": organization_id, "user_id": user_id},
        )
        row = result.mappings().one_or_none()
        return None if row is None else self._memory(row)

    async def list_memories(
        self, organization_id: UUID, user_id: UUID, query: str | None, limit: int
    ) -> list[Memory]:
        result = await self._session.execute(
            text(
                "SELECT id, organization_id, user_id, memory_type, content, source_reference, confidence, expires_at, retention_until, created_at, updated_at FROM memories WHERE organization_id = :organization_id AND user_id = :user_id AND deleted_at IS NULL AND (expires_at IS NULL OR expires_at > now()) AND (:query IS NULL OR content->>'text' ILIKE '%' || :query || '%') ORDER BY updated_at DESC LIMIT :limit"
            ),
            {
                "organization_id": organization_id,
                "user_id": user_id,
                "query": query or None,
                "limit": limit,
            },
        )
        return [self._memory(row) for row in result.mappings()]

    async def update(self, memory: Memory) -> Memory:
        await self._session.execute(
            text(
                "UPDATE memories SET memory_type = :memory_type, content = CAST(:content AS jsonb), updated_at = :updated_at WHERE id = :id AND organization_id = :organization_id AND user_id = :user_id AND deleted_at IS NULL"
            ),
            {
                "id": memory.id,
                "organization_id": memory.organization_id,
                "user_id": memory.user_id,
                "memory_type": memory.memory_type,
                "content": json.dumps({"text": memory.text}),
                "updated_at": memory.updated_at,
            },
        )
        return memory

    async def delete(
        self, organization_id: UUID, user_id: UUID, memory_id: UUID, deleted_at: datetime
    ) -> bool:
        result = await self._session.execute(
            text(
                "UPDATE memories SET deleted_at = :deleted_at, deleted_by_user_id = :user_id, deleted_reason = 'user_request' WHERE id = :id AND organization_id = :organization_id AND user_id = :user_id AND deleted_at IS NULL"
            ),
            {
                "id": memory_id,
                "organization_id": organization_id,
                "user_id": user_id,
                "deleted_at": deleted_at,
            },
        )
        await self._session.execute(
            text(
                "INSERT INTO memory_deletion_requests (organization_id, user_id, requested_by_user_id, scope, memory_id, completed_at) VALUES (:organization_id, :user_id, :user_id, 'memory', :memory_id, :deleted_at)"
            ),
            {
                "organization_id": organization_id,
                "user_id": user_id,
                "memory_id": memory_id,
                "deleted_at": deleted_at,
            },
        )
        return cast(CursorResult[Any], result).rowcount == 1

    async def delete_all(self, organization_id: UUID, user_id: UUID, deleted_at: datetime) -> int:
        result = await self._session.execute(
            text(
                "UPDATE memories SET deleted_at = :deleted_at, deleted_by_user_id = :user_id, deleted_reason = 'user_request' WHERE organization_id = :organization_id AND user_id = :user_id AND deleted_at IS NULL"
            ),
            {"organization_id": organization_id, "user_id": user_id, "deleted_at": deleted_at},
        )
        await self._session.execute(
            text(
                "INSERT INTO memory_deletion_requests (organization_id, user_id, requested_by_user_id, scope, completed_at) VALUES (:organization_id, :user_id, :user_id, 'all_memories', :deleted_at)"
            ),
            {"organization_id": organization_id, "user_id": user_id, "deleted_at": deleted_at},
        )
        return int(cast(CursorResult[Any], result).rowcount or 0)

    @staticmethod
    def _memory(row: Any) -> Memory:
        values = row
        return Memory(
            values["id"],
            values["organization_id"],
            values["user_id"],
            values["memory_type"],
            values["content"].get("text", ""),
            values["source_reference"],
            float(values["confidence"]) if values["confidence"] is not None else None,
            values["expires_at"],
            values["retention_until"],
            values["created_at"],
            values["updated_at"],
        )
