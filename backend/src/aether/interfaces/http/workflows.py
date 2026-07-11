"""Authenticated organization-scoped workflow builder APIs."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from aether.infrastructure.persistence.workflow_repository import SqlAlchemyWorkflowRepository
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal
from aether.workflows.definition import InvalidWorkflowDefinition, validate_definition

router = APIRouter(prefix="/v1/workflows", tags=["workflows"])


class WorkflowRequest(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5_000)
    definition: dict[str, object]


class DefinitionRequest(BaseModel):
    organization_id: UUID
    definition: dict[str, object]


class ScheduleRequest(BaseModel):
    organization_id: UUID
    cron_expression: str = Field(pattern=r"^\S+(\s+\S+){4}$", max_length=255)
    timezone: str = Field(pattern=r"^[A-Za-z_]+/[A-Za-z_]+$", max_length=64)


class ImportRequest(WorkflowRequest):
    pass


async def _access(session: DatabaseSession, org: UUID, user: UUID, write: bool = False) -> None:
    role = (
        await session.execute(
            text(
                "SELECT role FROM memberships WHERE organization_id=:org AND user_id=:user AND status='active'"
            ),
            {"org": org, "user": user},
        )
    ).scalar_one_or_none()
    if role is None or (write and role == "viewer"):
        raise HTTPException(status_code=403, detail="Organization access is denied")


def _repo(session: DatabaseSession) -> SqlAlchemyWorkflowRepository:
    return SqlAlchemyWorkflowRepository(session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: WorkflowRequest, session: DatabaseSession, principal: Principal = Depends(get_principal)
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    try:
        workflow_id = await _repo(session).create(
            body.organization_id,
            principal.user_id,
            body.name,
            body.description,
            validate_definition(body.definition),
        )
    except InvalidWorkflowDefinition as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"id": str(workflow_id)}


@router.get("")
async def list_workflows(
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    return await _repo(session).list_workflows(organization_id)


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_workflow(
    body: ImportRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    return await create_workflow(body, session, principal)


@router.get("/templates")
async def templates() -> list[dict[str, object]]:
    return [
        {
            "id": "manual-approval",
            "name": "Manual approval",
            "definition": {
                "nodes": [
                    {"id": "trigger", "type": "trigger", "label": "Manual trigger"},
                    {"id": "approval", "type": "approval", "label": "Request approval"},
                ],
                "edges": [{"source": "trigger", "target": "approval"}],
            },
        }
    ]


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: UUID,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _access(session, organization_id, principal.user_id)
    item = await _repo(session).get(organization_id, workflow_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Workflow was not found")
    return item


@router.put("/{workflow_id}/draft")
async def save_draft(
    workflow_id: UUID,
    body: DefinitionRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, int]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    try:
        version = await _repo(session).save_draft(
            body.organization_id,
            workflow_id,
            principal.user_id,
            validate_definition(body.definition),
        )
    except (InvalidWorkflowDefinition, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"version": version}


@router.post("/{workflow_id}/{command}")
async def transition_workflow(
    workflow_id: UUID,
    command: str,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, organization_id, principal.user_id, write=True)
    statuses = {"activate": "active", "pause": "paused", "archive": "archived"}
    target = statuses.get(command)
    if target is None or not await _repo(session).set_status(organization_id, workflow_id, target):
        raise HTTPException(status_code=409, detail="Workflow lifecycle transition is unavailable")
    return {"status": target}


@router.get("/{workflow_id}/export")
async def export_workflow(
    workflow_id: UUID,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _access(session, organization_id, principal.user_id)
    item = await _repo(session).export(organization_id, workflow_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Workflow was not found")
    return item


@router.get("/{workflow_id}/runs")
async def workflow_runs(
    workflow_id: UUID,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    rows = await session.execute(
        text("""
        SELECT r.id,r.status,r.created_at,r.started_at,r.finished_at,r.error_code,
          COALESCE(jsonb_agg(jsonb_build_object('step_key',s.step_key,'status',s.status,'error_code',s.error_code)
            ORDER BY s.created_at) FILTER (WHERE s.id IS NOT NULL),'[]'::jsonb) AS steps
        FROM workflow_runs r LEFT JOIN workflow_steps s ON s.workflow_run_id=r.id AND s.organization_id=r.organization_id
        WHERE r.organization_id=:org AND r.workflow_id=:workflow_id
        GROUP BY r.id ORDER BY r.created_at DESC LIMIT 50
    """),
        {"org": organization_id, "workflow_id": workflow_id},
    )
    return [dict(row._mapping) for row in rows]


@router.get("/{workflow_id}/approvals")
async def workflow_approvals(
    workflow_id: UUID,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    rows = await session.execute(
        text("""
        SELECT a.id,a.workflow_run_id,a.status,a.action_summary,a.expires_at,a.created_at
        FROM approvals a JOIN workflow_runs r ON r.id=a.workflow_run_id AND r.organization_id=a.organization_id
        WHERE a.organization_id=:org AND r.workflow_id=:workflow_id ORDER BY a.created_at DESC
    """),
        {"org": organization_id, "workflow_id": workflow_id},
    )
    return [dict(row._mapping) for row in rows]


@router.get("/{workflow_id}/schedules")
async def list_schedules(
    workflow_id: UUID,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    return await _repo(session).list_schedules(organization_id, workflow_id)


@router.post("/{workflow_id}/schedules", status_code=status.HTTP_201_CREATED)
async def create_schedule(
    workflow_id: UUID,
    body: ScheduleRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    try:
        schedule_id = await _repo(session).create_schedule(
            body.organization_id,
            workflow_id,
            principal.user_id,
            body.cron_expression,
            body.timezone,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {"id": str(schedule_id)}


@router.patch("/{workflow_id}/schedules/{schedule_id}")
async def toggle_schedule(
    workflow_id: UUID,
    schedule_id: UUID,
    enabled: bool,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> dict[str, bool]:
    await _access(session, organization_id, principal.user_id, write=True)
    if not await _repo(session).set_schedule_enabled(
        organization_id, workflow_id, schedule_id, enabled
    ):
        raise HTTPException(status_code=404, detail="Schedule was not found")
    return {"enabled": enabled}


@router.delete("/{workflow_id}/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    workflow_id: UUID,
    schedule_id: UUID,
    session: DatabaseSession,
    organization_id: UUID = Query(),
    principal: Principal = Depends(get_principal),
) -> None:
    await _access(session, organization_id, principal.user_id, write=True)
    if not await _repo(session).delete_schedule(organization_id, workflow_id, schedule_id):
        raise HTTPException(status_code=404, detail="Schedule was not found")
