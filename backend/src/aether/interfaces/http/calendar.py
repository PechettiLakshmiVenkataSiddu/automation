"""Authenticated routes for Google Calendar OAuth sync and manual proposal approval gates."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from aether.calendar.contracts import (
    CalendarConnectionRequest,
    EventProposalRequest,
    ProposalDecisionRequest,
)
from aether.calendar.service import CalendarSyncService
from aether.infrastructure.persistence.calendar_repository import (
    SqlAlchemyCalendarRepository,
)
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal

router = APIRouter(prefix="/v1/calendar", tags=["calendar"])


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
    body: CalendarConnectionRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyCalendarRepository(session)
    expires_at = datetime.now(UTC) + timedelta(seconds=body.expires_in_seconds)

    conn_id = await repo.create_connection(
        body.organization_id,
        principal.user_id,
        body.provider,
        body.access_token,
        body.refresh_token,
        body.scopes,
        body.permitted_calendars,
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
    repo = SqlAlchemyCalendarRepository(session)
    revoked = await repo.revoke_connection(organization_id, principal.user_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="No active connection found to revoke.")
    return {"status": "success"}


@router.get("/events")
async def get_events(
    organization_id: UUID,
    start_time: datetime,
    end_time: datetime,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyCalendarRepository(session)
    service = CalendarSyncService(repo)

    # Sync trigger (mock synchronization on-demand)
    with contextlib.suppress(ValueError):
        await service.sync_events(organization_id, principal.user_id)

    events = await repo.get_events_in_range(organization_id, start_time, end_time)
    return [
        {
            "id": str(ev["id"]),
            "google_event_id": ev["google_event_id"],
            "summary": ev["summary"],
            "description": ev["description"],
            "start_time": ev["start_time"].isoformat(),
            "end_time": ev["end_time"].isoformat(),
            "attendees": ev["attendees"],
            "status": ev["status"],
        }
        for ev in events
    ]


@router.post("/proposals", status_code=status.HTTP_201_CREATED)
async def propose_event(
    body: EventProposalRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyCalendarRepository(session)
    service = CalendarSyncService(repo)

    try:
        result = await service.propose_event(
            body.organization_id,
            principal.user_id,
            body.summary,
            body.description,
            body.start_time,
            body.end_time,
            body.attendees,
        )
        return result
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/proposals")
async def get_proposals(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyCalendarRepository(session)
    proposals = await repo.get_proposals(organization_id)
    return [
        {
            "id": str(prop["id"]),
            "summary": prop["summary"],
            "description": prop["description"],
            "start_time": prop["start_time"].isoformat(),
            "end_time": prop["end_time"].isoformat(),
            "attendees": prop["attendees"],
            "status": prop["status"],
            "conflict_detected": prop["conflict_detected"],
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
    repo = SqlAlchemyCalendarRepository(session)
    service = CalendarSyncService(repo)

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
