"""Authenticated owner-only HTTP API for long-term memory."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from aether.infrastructure.persistence.memory_repository import SqlAlchemyMemoryRepository
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal
from aether.memory.models import Memory
from aether.memory.service import MemoryService

router = APIRouter(prefix="/v1/memories", tags=["memories"])


class ConsentRequest(BaseModel):
    organization_id: UUID
    enabled: bool


class CreateMemoryRequest(BaseModel):
    organization_id: UUID
    memory_type: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=4_000)
    source_reference: dict[str, object] = Field(default_factory=dict)
    expires_at: datetime | None = None


class UpdateMemoryRequest(BaseModel):
    memory_type: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=4_000)


async def _require_membership(
    session: DatabaseSession, organization_id: UUID, user_id: UUID
) -> None:
    result = await session.execute(
        text(
            "SELECT 1 FROM memberships WHERE organization_id = :organization_id "
            "AND user_id = :user_id AND status = 'active'"
        ),
        {"organization_id": organization_id, "user_id": user_id},
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Organization access is denied"
        )


def _service(session: DatabaseSession) -> MemoryService:
    return MemoryService(SqlAlchemyMemoryRepository(session))


def _serialize(memory: Memory) -> dict[str, object]:
    return {
        "id": str(memory.id),
        "organization_id": str(memory.organization_id),
        "memory_type": memory.memory_type,
        "text": memory.text,
        "source_reference": memory.source_reference,
        "expires_at": memory.expires_at.isoformat() if memory.expires_at else None,
        "created_at": memory.created_at.isoformat(),
        "updated_at": memory.updated_at.isoformat(),
    }


@router.put("/consent")
async def set_consent(
    body: ConsentRequest, session: DatabaseSession, principal: Principal = Depends(get_principal)
) -> dict[str, object]:
    await _require_membership(session, body.organization_id, principal.user_id)
    consent = await _service(session).set_consent(
        body.organization_id, principal.user_id, body.enabled
    )
    return {
        "enabled": consent.enabled,
        "policy_version": consent.policy_version,
        "updated_at": consent.updated_at.isoformat(),
    }


@router.get("/consent")
async def get_consent(
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _require_membership(session, organization_id, principal.user_id)
    consent = await SqlAlchemyMemoryRepository(session).get_consent(
        organization_id, principal.user_id
    )
    return {
        "enabled": consent.enabled if consent else False,
        "policy_version": consent.policy_version if consent else None,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_memory(
    body: CreateMemoryRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _require_membership(session, body.organization_id, principal.user_id)
    memory = await _service(session).create(
        body.organization_id,
        principal.user_id,
        body.memory_type,
        body.text,
        body.source_reference,
        body.expires_at,
    )
    return _serialize(memory)


@router.get("/export")
async def export_memories(
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _require_membership(session, organization_id, principal.user_id)
    memories = await _service(session).list_memories(organization_id, principal.user_id, None)
    return {
        "organization_id": str(organization_id),
        "user_id": str(principal.user_id),
        "memories": [_serialize(item) for item in memories],
    }


@router.get("")
async def list_memories(
    session: DatabaseSession,
    organization_id: UUID = Query(),
    query: str | None = Query(default=None, max_length=200),
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _require_membership(session, organization_id, principal.user_id)
    return [
        _serialize(item)
        for item in await _service(session).list_memories(organization_id, principal.user_id, query)
    ]


@router.patch("/{memory_id}")
async def update_memory(
    memory_id: UUID,
    body: UpdateMemoryRequest,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _require_membership(session, organization_id, principal.user_id)
    return _serialize(
        await _service(session).update(
            organization_id, principal.user_id, memory_id, body.text, body.memory_type
        )
    )


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: UUID,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> Response:
    await _require_membership(session, organization_id, principal.user_id)
    await _service(session).delete(organization_id, principal.user_id, memory_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def forget_all(
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> Response:
    await _require_membership(session, organization_id, principal.user_id)
    await _service(session).forget_all(organization_id, principal.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
