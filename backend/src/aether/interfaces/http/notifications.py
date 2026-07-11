"""Authenticated routes for notification feeds, preference updates, and dispatching alerts."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from aether.infrastructure.persistence.notifications_repository import (
    SqlAlchemyNotificationsRepository,
)
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal
from aether.notifications.contracts import (
    NotificationDispatchRequest,
    NotificationPreferencesUpdateRequest,
)
from aether.notifications.service import NotificationService

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


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


@router.get("")
async def get_notifications(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyNotificationsRepository(session)
    notifications = await repo.get_active_notifications(organization_id, principal.user_id)
    return [
        {
            "id": str(notif["id"]),
            "title": notif["title"],
            "message": notif["message"],
            "level": notif["level"],
            "status": notif["status"],
            "sent_channels": notif["sent_channels"],
            "created_at": notif["created_at"].isoformat(),
        }
        for notif in notifications
    ]


@router.post("/{id}/read")
async def mark_read(
    id: UUID,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, organization_id, principal.user_id, write=True)
    repo = SqlAlchemyNotificationsRepository(session)
    success = await repo.mark_read(organization_id, id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"status": "success"}


@router.get("/preferences")
async def get_preferences(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyNotificationsRepository(session)
    prefs = await repo.get_preferences(organization_id, principal.user_id)
    return {
        "channels": prefs["channels"],
        "quiet_hours_start": (
            prefs["quiet_hours_start"].isoformat() if prefs["quiet_hours_start"] else None
        ),
        "quiet_hours_end": (
            prefs["quiet_hours_end"].isoformat() if prefs["quiet_hours_end"] else None
        ),
        "unsubscribed": prefs["unsubscribed"],
    }


@router.post("/preferences")
async def update_preferences(
    body: NotificationPreferencesUpdateRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyNotificationsRepository(session)
    await repo.upsert_preferences(
        body.organization_id,
        principal.user_id,
        [str(c) for c in body.channels],
        body.quiet_hours_start,
        body.quiet_hours_end,
        body.unsubscribed,
    )
    return {"status": "success"}


@router.post("/dispatch", status_code=status.HTTP_201_CREATED)
async def dispatch_notification(
    body: NotificationDispatchRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str | None]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyNotificationsRepository(session)
    service = NotificationService(repo)

    notif_id = await service.dispatch_notification(
        body.organization_id,
        principal.user_id,
        body.title,
        body.message,
        body.level,
    )
    return {"notification_id": str(notif_id) if notif_id else None}
