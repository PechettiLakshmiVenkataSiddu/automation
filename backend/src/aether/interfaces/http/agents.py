"""Authenticated routes for AI Agent orchestration and step-approval feedback."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from aether.agents.orchestrator import AgentOrchestrator
from aether.infrastructure.persistence.agent_repository import SqlAlchemyAgentRepository
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal

router = APIRouter(prefix="/v1/agents/runs", tags=["agents"])


class AgentRunCreateRequest(BaseModel):
    organization_id: UUID
    goal: str = Field(min_length=1)
    budget_limit_usd: float = Field(default=1.0000, gt=0.0)
    time_limit_seconds: int = Field(default=600, gt=0)


class AgentApprovalDecisionRequest(BaseModel):
    organization_id: UUID
    approved: bool
    reason: str | None = Field(default=None, max_length=2000)


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



@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent_run(
    body: AgentRunCreateRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyAgentRepository(session)
    orchestrator = AgentOrchestrator(repo)
    run_id = await orchestrator.start_run(
        body.organization_id,
        principal.user_id,
        body.goal,
        body.budget_limit_usd,
        body.time_limit_seconds,
    )
    return {"run_id": str(run_id)}


@router.get("/{id}")
async def get_agent_run(
    id: UUID,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyAgentRepository(session)
    run = await repo.get_run(organization_id, id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    plan = await repo.get_plan(organization_id, id)

    # Format dates as ISO-8601 strings
    return {
        "id": str(run["id"]),
        "organization_id": str(run["organization_id"]),
        "user_id": str(run["user_id"]),
        "goal": run["goal"],
        "status": run["status"],
        "budget_limit_usd": float(run["budget_limit_usd"]),
        "budget_spent_usd": float(run["budget_spent_usd"]),
        "time_limit_seconds": run["time_limit_seconds"],
        "expires_at": run["expires_at"].isoformat(),
        "created_at": run["created_at"].isoformat(),
        "updated_at": run["updated_at"].isoformat(),
        "plan": [
            {
                "id": str(step["id"]),
                "step_index": step["step_index"],
                "assigned_agent": step["assigned_agent"],
                "description": step["description"],
                "requires_approval": step["requires_approval"],
                "status": step["status"],
                "input_payload": step["input_payload"],
                "output_payload": step["output_payload"],
            }
            for step in plan
        ],
    }


@router.post("/{id}/approve")
async def decide_agent_run_approval(
    id: UUID,
    body: AgentApprovalDecisionRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyAgentRepository(session)
    orchestrator = AgentOrchestrator(repo)
    try:
        await orchestrator.decide_approval(
            body.organization_id, id, body.approved, body.reason
        )
        return {"status": "success"}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{id}/logs")
async def get_agent_run_logs(
    id: UUID,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyAgentRepository(session)
    logs = await repo.get_audit_logs(organization_id, id)
    return [
        {
            "id": str(log["id"]),
            "agent_run_id": str(log["agent_run_id"]),
            "step_id": str(log["step_id"]) if log["step_id"] else None,
            "action_type": log["action_type"],
            "message": log["message"],
            "payload": log["payload"],
            "created_at": log["created_at"].isoformat(),
        }
        for log in logs
    ]
