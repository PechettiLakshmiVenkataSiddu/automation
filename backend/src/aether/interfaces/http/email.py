"""Authenticated routes for Gmail OAuth connections and outgoing draft send validation gates."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from aether.email.contracts import (
    EmailConnectionRequest,
    EmailProposalRequest,
    ProposalDecisionRequest,
)
from aether.email.service import EmailSyncService
from aether.infrastructure.persistence.email_repository import (
    SqlAlchemyEmailRepository,
)
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal

router = APIRouter(prefix="/v1/email", tags=["email"])


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
    body: EmailConnectionRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyEmailRepository(session)
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
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, organization_id, principal.user_id, write=True)
    repo = SqlAlchemyEmailRepository(session)
    revoked = await repo.revoke_connection(organization_id, principal.user_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="No active connection found to revoke.")
    return {"status": "success"}


@router.get("/messages")
async def get_messages(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyEmailRepository(session)
    service = EmailSyncService(repo)

    # Sync trigger (mock synchronization on-demand)
    with contextlib.suppress(ValueError):
        await service.sync_emails(organization_id, principal.user_id)

    messages = await repo.get_messages(organization_id)
    return [
        {
            "id": str(msg["id"]),
            "google_message_id": msg["google_message_id"],
            "thread_id": msg["thread_id"],
            "from_address": msg["from_address"],
            "to_addresses": msg["to_addresses"],
            "subject": msg["subject"],
            "body_snippet": msg["body_snippet"],
            "body_text": msg["body_text"],
            "status": msg["status"],
            "received_at": msg["received_at"].isoformat(),
        }
        for msg in messages
    ]


@router.post("/proposals", status_code=status.HTTP_201_CREATED)
async def propose_email(
    body: EmailProposalRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyEmailRepository(session)
    service = EmailSyncService(repo)

    try:
        proposal_id = await service.propose_email(
            body.organization_id,
            principal.user_id,
            body.recipient_address,
            body.subject,
            body.body_text,
            body.attachments,
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
    repo = SqlAlchemyEmailRepository(session)
    proposals = await repo.get_proposals(organization_id)
    return [
        {
            "id": str(prop["id"]),
            "recipient_address": prop["recipient_address"],
            "subject": prop["subject"],
            "body_text": prop["body_text"],
            "attachments": prop["attachments"],
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
    repo = SqlAlchemyEmailRepository(session)
    service = EmailSyncService(repo)

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
