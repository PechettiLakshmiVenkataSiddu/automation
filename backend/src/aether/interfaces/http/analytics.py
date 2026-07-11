"""Authenticated endpoints for usage logging and CSV exports."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import text

from aether.analytics.contracts import UsageLogRequest
from aether.analytics.service import AnalyticsService
from aether.infrastructure.persistence.analytics_repository import (
    SqlAlchemyAnalyticsRepository,
)
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal

router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


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


@router.get("/summary")
async def get_summary(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyAnalyticsRepository(session)
    summary = await repo.get_summary(organization_id)
    return {
        "total_cost": float(summary["total_cost"]),
        "total_events": int(summary["total_events"]),
    }


@router.get("/breakdown")
async def get_breakdown(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, list[dict[str, object]]]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyAnalyticsRepository(session)
    categories = await repo.get_breakdown_by_category(organization_id)
    users = await repo.get_breakdown_by_user(organization_id)
    return {
        "categories": [
            {
                "category": c["category"],
                "total_cost": float(c["total_cost"]),
                "total_units": int(c["total_units"]),
                "event_count": int(c["event_count"]),
            }
            for c in categories
        ],
        "users": [
            {
                "email": u["email"],
                "total_cost": float(u["total_cost"]),
                "event_count": int(u["event_count"]),
            }
            for u in users
        ],
    }


@router.get("/workflows")
async def get_workflow_metrics(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyAnalyticsRepository(session)
    metrics = await repo.get_workflow_metrics(organization_id)
    return [
        {
            "id": str(m["id"]),
            "workflow_id": str(m["workflow_id"]),
            "run_count": int(m["run_count"]),
            "success_count": int(m["success_count"]),
            "failure_count": int(m["failure_count"]),
            "avg_duration_seconds": float(m["avg_duration_seconds"]),
        }
        for m in metrics
    ]


@router.post("/log", status_code=status.HTTP_201_CREATED)
async def log_usage_event(
    body: UsageLogRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyAnalyticsRepository(session)
    service = AnalyticsService(repo)
    event_id = await service.log_event(
        body.organization_id,
        body.user_id or principal.user_id,
        body.event_name,
        body.category,
        body.cost,
        body.units,
        body.metadata,
    )
    return {"status": "logged", "event_id": str(event_id)}


@router.get("/export")
async def export_usage_events(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> PlainTextResponse:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyAnalyticsRepository(session)
    service = AnalyticsService(repo)
    csv_data = await service.generate_csv_export(organization_id)

    return PlainTextResponse(
        csv_data,
        headers={
            "Content-Disposition": "attachment; filename=usage_export.csv",
            "Content-Type": "text/csv",
        },
    )
