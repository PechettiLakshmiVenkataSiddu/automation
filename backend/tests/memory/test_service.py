from datetime import datetime
from uuid import UUID, uuid4

import pytest

from aether.memory.models import Memory, MemoryConsent
from aether.memory.service import MemoryService
from aether.shared.errors import AuthorizationError


class Repository:
    def __init__(self) -> None:
        self.consent: MemoryConsent | None = None
        self.memories: dict[UUID, Memory] = {}

    async def get_consent(self, organization_id: UUID, user_id: UUID) -> MemoryConsent | None:
        return self.consent

    async def set_consent(self, consent: MemoryConsent, changed_at: datetime) -> MemoryConsent:
        self.consent = consent
        return consent

    async def create(self, memory: Memory) -> Memory:
        self.memories[memory.id] = memory
        return memory

    async def get(self, organization_id: UUID, user_id: UUID, memory_id: UUID) -> Memory | None:
        return self.memories.get(memory_id)

    async def list_memories(
        self, organization_id: UUID, user_id: UUID, query: str | None, limit: int
    ) -> list[Memory]:
        return list(self.memories.values())[:limit]

    async def update(self, memory: Memory) -> Memory:
        self.memories[memory.id] = memory
        return memory

    async def delete(
        self, organization_id: UUID, user_id: UUID, memory_id: UUID, deleted_at: datetime
    ) -> bool:
        return self.memories.pop(memory_id, None) is not None

    async def delete_all(self, organization_id: UUID, user_id: UUID, deleted_at: datetime) -> int:
        count = len(self.memories)
        self.memories.clear()
        return count


@pytest.mark.asyncio
async def test_memory_requires_explicit_consent_and_retrieval_is_bounded() -> None:
    repository = Repository()
    service = MemoryService(repository)
    organization_id, user_id = uuid4(), uuid4()
    with pytest.raises(AuthorizationError):
        await service.create(organization_id, user_id, "preference", "private", {}, None)
    await service.set_consent(organization_id, user_id, True)
    created = await service.create(organization_id, user_id, "preference", "x" * 4_000, {}, None)
    retrieved = await service.retrieve_for_chat(organization_id, user_id, "x")
    assert retrieved[0].id == created.id
    assert len(retrieved[0].text) == 3_000
    await service.set_consent(organization_id, user_id, False)
    assert await service.retrieve_for_chat(organization_id, user_id, "x") == []


@pytest.mark.asyncio
async def test_owner_scoped_delete_rejects_missing_memory() -> None:
    repository = Repository()
    service = MemoryService(repository)
    organization_id, user_id = uuid4(), uuid4()
    await service.set_consent(organization_id, user_id, True)
    with pytest.raises(AuthorizationError):
        await service.delete(organization_id, user_id, uuid4())
