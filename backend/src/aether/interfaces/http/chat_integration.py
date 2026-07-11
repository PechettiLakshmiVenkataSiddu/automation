"""Authenticated routes for Slack/Teams connections and outgoing message approvals."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from aether.chat_integration.contracts import (
    ChatConnectionRequest,
    ChatProposalRequest,
    ProposalDecisionRequest,
)
from aether.chat_integration.service import ChatSyncService
from aether.infrastructure.persistence.chat_repository import (
    SqlAlchemyChatRepository,
)
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal

router = APIRouter(prefix="/v1/chat-integration", tags=["chat_integration"])


async def _access(session: DatabaseSession, org: UUID, user: UUID, write: bool = False) -> str:
    """Helper to check organization membership and write access."""
    row = (
        await session.execute(
            text(
                "SELECT role FROM memberships "
                "WHERE organization_id=:org AND user_id=:user AND status='active'"
            ),
            {"org": org, "user": user},
        )
    ).scalar_one_or_none()
    if row is None or (write and row == "viewer"):
        raise HTTPException(status_code=403, detail="Organization access is denied")
    return str(row)


@router.post("/connections", status_code=status.HTTP_201_CREATED)
async def create_connection(
    body: ChatConnectionRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyChatRepository(session)
    expires_at = datetime.now(UTC) + timedelta(seconds=body.expires_in_seconds)

    conn_id = await repo.create_connection(
        body.organization_id,
        principal.user_id,
        body.provider,
        body.access_token,
        body.refresh_token,
        body.scopes,
        expires_at,
    )
    return {"connection_id": str(conn_id)}


@router.delete("/connections")
async def revoke_connection(
    organization_id: UUID,
    provider: str,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, organization_id, principal.user_id, write=True)
    repo = SqlAlchemyChatRepository(session)
    revoked = await repo.revoke_connection(organization_id, principal.user_id, provider)
    if not revoked:
        raise HTTPException(status_code=404, detail="No active connection found to revoke.")
    return {"status": "success"}


@router.get("/messages")
async def get_messages(
    organization_id: UUID,
    provider: str,
    channel_id: str,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyChatRepository(session)
    service = ChatSyncService(repo)

    # Sync trigger (mock synchronization on-demand)
    with contextlib.suppress(ValueError):
        await service.sync_messages(organization_id, principal.user_id, provider, channel_id)

    messages = await repo.get_messages(organization_id, channel_id)
    return [
        {
            "id": str(msg["id"]),
            "provider": msg["provider"],
            "channel_id": msg["channel_id"],
            "thread_ts": msg["thread_ts"],
            "message_text": msg["message_text"],
            "sender_id": msg["sender_id"],
            "status": msg["status"],
            "received_at": msg["received_at"].isoformat(),
        }
        for msg in messages
    ]


@router.post("/proposals", status_code=status.HTTP_201_CREATED)
async def propose_message(
    body: ChatProposalRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyChatRepository(session)
    service = ChatSyncService(repo)

    # Check connection first to identify provider (default slack, fallback teams)
    connection = await repo.get_connection(body.organization_id, principal.user_id, "slack")
    if not connection:
        connection = await repo.get_connection(body.organization_id, principal.user_id, "teams")
    provider = connection["provider"] if connection else "slack"

    try:
        proposal_id = await service.propose_message(
            body.organization_id,
            principal.user_id,
            provider,
            body.channel_id,
            body.message_text,
        )
        return {"proposal_id": str(proposal_id)}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/proposals")
async def get_proposals(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyChatRepository(session)
    proposals = await repo.get_proposals(organization_id)
    return [
        {
            "id": str(prop["id"]),
            "channel_id": prop["channel_id"],
            "message_text": prop["message_text"],
            "status": prop["status"],
            "decision_reason": prop["decision_reason"],
            "created_at": prop["created_at"].isoformat(),
        }
        for prop in proposals
    ]


@router.post("/proposals/{id}/approve")
async def decide_proposal(
    id: UUID,
    body: ProposalDecisionRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyChatRepository(session)
    service = ChatSyncService(repo)

    try:
        await service.approve_proposal(
            body.organization_id,
            id,
            principal.user_id,
            body.approved,
            body.reason,
        )
        return {"status": "success"}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
