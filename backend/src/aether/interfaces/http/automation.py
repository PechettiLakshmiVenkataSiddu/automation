"""Authenticated, organization-scoped controls for durable workflow runs."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from aether.infrastructure.persistence.automation_repository import SqlAlchemyWorkflowRunRepository
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal

from aether.automation.tools import TOOL_REGISTRY
router = APIRouter(prefix="/v1/automation", tags=["automation"])


class CreateRunRequest(BaseModel):
    organization_id: UUID
    workflow_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=255)
    input: dict[str, object] = Field(default_factory=dict)


class ApprovalDecisionRequest(BaseModel):
    organization_id: UUID
    approved: bool
    reason: str | None = Field(default=None, max_length=2_000)

class ToolInvokeRequest(BaseModel):
    organization_id: UUID
    tool_name: str = Field(min_length=1, max_length=128)
    payload: dict[str, object] = Field(default_factory=dict)

async def _membership(session: DatabaseSession, org: UUID, user: UUID, write: bool = False) -> str:
    row = (
        await session.execute(
            text(
                "SELECT role FROM memberships WHERE organization_id=:org AND user_id=:user AND status='active'"
            ),
            {"org": org, "user": user},
        )
    ).scalar_one_or_none()
    if row is None or (write and row == "viewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Organization access is denied"
        )
    return str(row)


def _repository(session: DatabaseSession) -> SqlAlchemyWorkflowRunRepository:
    return SqlAlchemyWorkflowRunRepository(session)


@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def create_run(
    body: CreateRunRequest, session: DatabaseSession, principal: Principal = Depends(get_principal)
) -> dict[str, str]:
    await _membership(session, body.organization_id, principal.user_id, write=True)
    try:
        run_id = await _repository(session).create_run(
            body.organization_id,
            body.workflow_id,
            principal.user_id,
            body.idempotency_key,
            body.input,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return {"id": str(run_id), "organization_id": str(body.organization_id)}


@router.get("/runs")
async def list_runs(
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _membership(session, organization_id, principal.user_id)
    rows = await session.execute(
        text(
            "SELECT id,status,workflow_id,correlation_id,execution_attempt,created_at,started_at,finished_at FROM workflow_runs WHERE organization_id=:org ORDER BY created_at DESC LIMIT 100"
        ),
        {"org": organization_id},
    )
    return [
        {
            "id": str(row.id),
            "workflow_id": str(row.workflow_id),
            "status": row.status,
            "correlation_id": str(row.correlation_id),
            "execution_attempt": row.execution_attempt,
            "created_at": row.created_at.isoformat(),
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        }
        for row in rows
    ]


@router.get("/runs/{run_id}/logs")
async def run_logs(
    run_id: UUID,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _membership(session, organization_id, principal.user_id)
    rows = await session.execute(
        text(
            "SELECT id,event_type,actor_user_id,detail,occurred_at FROM workflow_run_events WHERE organization_id=:org AND workflow_run_id=:run ORDER BY occurred_at"
        ),
        {"org": organization_id, "run": run_id},
    )
    return [
        {
            "id": str(row.id),
            "event_type": row.event_type,
            "actor_user_id": str(row.actor_user_id) if row.actor_user_id else None,
            "detail": row.detail,
            "occurred_at": row.occurred_at.isoformat(),
        }
        for row in rows
    ]


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: UUID,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> dict[str, bool]:
    await _membership(session, organization_id, principal.user_id, write=True)
    if not await _repository(session).request_cancel(organization_id, run_id, principal.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run is not cancellable")
    return {"cancelled": True}


@router.post("/runs/{run_id}/retry")
async def retry_run(
    run_id: UUID,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> dict[str, bool]:
    await _membership(session, organization_id, principal.user_id, write=True)
    if not await _repository(session).retry(organization_id, run_id, principal.user_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Only failed runs can be retried"
        )
    return {"queued": True}


@router.post("/approvals/{approval_id}/decision")
async def decide_approval(
    approval_id: UUID,
    body: ApprovalDecisionRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    role = await _membership(session, body.organization_id, principal.user_id, write=True)
    if role not in {"owner", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Approval requires an administrator"
        )
    run_id = await _repository(session).approve(
        body.organization_id, approval_id, principal.user_id, body.approved, body.reason
    )
    if run_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Approval is unavailable")
    return {"workflow_run_id": str(run_id), "decision": "approved" if body.approved else "rejected"}
@router.post("/tools/invoke")
async def invoke_tool(
    body: ToolInvokeRequest, session: DatabaseSession, principal: Principal = Depends(get_principal)
) -> dict[str, object]:
    await _membership(session, body.organization_id, principal.user_id, write=True)
    tool = TOOL_REGISTRY.get(body.tool_name)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown tool")
    return await tool.execute(body.payload)
