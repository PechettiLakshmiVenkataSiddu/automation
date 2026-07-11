"""Application service for consented memory commands and bounded retrieval."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from aether.memory.models import Memory, MemoryConsent
from aether.memory.repository import MemoryRepository
from aether.shared.errors import AuthorizationError

MEMORY_POLICY_VERSION = "phase-10-v1"
MAX_RETRIEVED_MEMORIES = 8
MAX_RETRIEVED_CHARACTERS = 3_000


class MemoryService:
    """Enforces consent and owner-only scope before every memory operation."""

    def __init__(self, repository: MemoryRepository) -> None:
        self._repository = repository

    async def set_consent(
        self, organization_id: UUID, user_id: UUID, enabled: bool
    ) -> MemoryConsent:
        now = datetime.now(UTC)
        return await self._repository.set_consent(
            MemoryConsent(organization_id, user_id, enabled, MEMORY_POLICY_VERSION, now), now
        )

    async def create(
        self,
        organization_id: UUID,
        user_id: UUID,
        memory_type: str,
        text: str,
        source_reference: dict[str, object],
        expires_at: datetime | None,
    ) -> Memory:
        await self._require_consent(organization_id, user_id)
        now = datetime.now(UTC)
        return await self._repository.create(
            Memory(
                uuid4(),
                organization_id,
                user_id,
                memory_type,
                text,
                source_reference,
                None,
                expires_at,
                None,
                now,
                now,
            )
        )

    async def list_memories(
        self, organization_id: UUID, user_id: UUID, query: str | None, limit: int = 100
    ) -> list[Memory]:
        return await self._repository.list_memories(
            organization_id, user_id, query, min(limit, 100)
        )

    async def update(
        self, organization_id: UUID, user_id: UUID, memory_id: UUID, text: str, memory_type: str
    ) -> Memory:
        current = await self._get_owned(organization_id, user_id, memory_id)
        now = datetime.now(UTC)
        return await self._repository.update(
            Memory(
                current.id,
                current.organization_id,
                current.user_id,
                memory_type,
                text,
                current.source_reference,
                current.confidence,
                current.expires_at,
                current.retention_until,
                current.created_at,
                now,
            )
        )

    async def delete(self, organization_id: UUID, user_id: UUID, memory_id: UUID) -> None:
        await self._get_owned(organization_id, user_id, memory_id)
        await self._repository.delete(organization_id, user_id, memory_id, datetime.now(UTC))

    async def forget_all(self, organization_id: UUID, user_id: UUID) -> int:
        return await self._repository.delete_all(organization_id, user_id, datetime.now(UTC))

    async def retrieve_for_chat(
        self, organization_id: UUID, user_id: UUID, query: str
    ) -> list[Memory]:
        consent = await self._repository.get_consent(organization_id, user_id)
        if consent is None or not consent.enabled:
            return []
        candidates = await self._repository.list_memories(
            organization_id, user_id, query, MAX_RETRIEVED_MEMORIES
        )
        selected: list[Memory] = []
        remaining = MAX_RETRIEVED_CHARACTERS
        for memory in candidates:
            if memory.expires_at is not None and memory.expires_at <= datetime.now(UTC):
                continue
            if remaining <= 0:
                break
            text = memory.text[:remaining]
            selected.append(
                Memory(
                    memory.id,
                    memory.organization_id,
                    memory.user_id,
                    memory.memory_type,
                    text,
                    memory.source_reference,
                    memory.confidence,
                    memory.expires_at,
                    memory.retention_until,
                    memory.created_at,
                    memory.updated_at,
                )
            )
            remaining -= len(text)
        return selected

    async def _require_consent(self, organization_id: UUID, user_id: UUID) -> None:
        consent = await self._repository.get_consent(organization_id, user_id)
        if consent is None or not consent.enabled:
            raise AuthorizationError(
                "Long-term memory is disabled. Enable it before saving a memory."
            )

    async def _get_owned(self, organization_id: UUID, user_id: UUID, memory_id: UUID) -> Memory:
        memory = await self._repository.get(organization_id, user_id, memory_id)
        if memory is None:
            raise AuthorizationError("Memory was not found or is not available to this user.")
        return memory
