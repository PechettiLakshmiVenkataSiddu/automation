"""Authenticated organization dashboard read models."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text

from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal

router = APIRouter(tags=["dashboard"])


@router.get("/v1/me/organizations")
async def organizations(
    session: DatabaseSession, principal: Principal = Depends(get_principal)
) -> list[dict[str, str]]:
    """List active organizations in which the authenticated user is a member."""
    result = await session.execute(
        text(
            "SELECT o.id, o.name, m.role FROM organizations o "
            "JOIN memberships m ON m.organization_id = o.id "
            "WHERE m.user_id = :user_id AND m.status = 'active' "
            "AND o.status = 'active' ORDER BY o.name"
        ),
        {"user_id": principal.user_id},
    )
    return [{"id": str(row.id), "name": row.name, "role": row.role} for row in result]


@router.get("/v1/dashboard/summary")
async def summary(
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    """Return aggregate and recent-run data after membership validation."""
    membership = await session.execute(
        text(
            "SELECT 1 FROM memberships "
            "WHERE organization_id = :organization_id "
            "AND user_id = :user_id AND status = 'active'"
        ),
        {"organization_id": organization_id, "user_id": principal.user_id},
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Organization access is denied"
        )
    counts = await session.execute(
        text(
            "SELECT status, count(*) AS total FROM workflow_runs "
            "WHERE organization_id = :organization_id GROUP BY status"
        ),
        {"organization_id": organization_id},
    )
    runs_by_status = {row.status: row.total for row in counts}
    approvals = await session.execute(
        text(
            "SELECT count(*) FROM approvals "
            "WHERE organization_id = :organization_id AND status = 'pending'"
        ),
        {"organization_id": organization_id},
    )
    recent = await session.execute(
        text(
            "SELECT r.id, w.name AS workflow_name, r.status, r.created_at "
            "FROM workflow_runs r JOIN workflows w ON w.id = r.workflow_id "
            "WHERE r.organization_id = :organization_id "
            "ORDER BY r.created_at DESC LIMIT 5"
        ),
        {"organization_id": organization_id},
    )
    return {
        "runs_by_status": runs_by_status,
        "pending_approvals": approvals.scalar_one(),
        "recent_runs": [
            {
                "id": str(row.id),
                "workflow_name": row.workflow_name,
                "status": row.status,
                "created_at": row.created_at.isoformat(),
            }
            for row in recent
        ],
    }
