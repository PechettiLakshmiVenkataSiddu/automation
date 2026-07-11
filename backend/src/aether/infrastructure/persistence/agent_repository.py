"""PostgreSQL authority for agent runs, plans, and audit trails."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyAgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(
        self,
        org: UUID,
        user: UUID,
        goal: str,
        budget_limit_usd: float = 1.0000,
        time_limit_seconds: int = 600,
    ) -> UUID:
        run_id = uuid4()
        expires_at = datetime.now(UTC) + timedelta(seconds=time_limit_seconds)
        await self._session.execute(
            text("""
            INSERT INTO agent_runs (
                id, organization_id, user_id, goal, status,
                budget_limit_usd, budget_spent_usd, time_limit_seconds, expires_at
            )
            VALUES (
                :id, :org, :user, :goal, 'queued',
                :budget_limit, 0.0000, :time_limit, :expires_at
            )
            """),
            {
                "id": run_id,
                "org": org,
                "user": user,
                "goal": goal,
                "budget_limit": budget_limit_usd,
                "time_limit": time_limit_seconds,
                "expires_at": expires_at,
            },
        )
        return run_id

    async def get_run(self, org: UUID, run_id: UUID) -> dict[str, Any] | None:
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, user_id, goal, status,
                       budget_limit_usd, budget_spent_usd, time_limit_seconds, expires_at,
                       created_at, updated_at
                FROM agent_runs
                WHERE id = :run_id AND organization_id = :org
                """),
                {"run_id": run_id, "org": org},
            )
        ).mappings().one_or_none()
        return dict(row) if row else None

    async def update_run_status(
        self, org: UUID, run_id: UUID, status: str, budget_spent_usd: float | None = None
    ) -> bool:
        if budget_spent_usd is not None:
            query = """
                UPDATE agent_runs
                SET status = :status, budget_spent_usd = :budget_spent_usd, updated_at = now()
                WHERE id = :run_id AND organization_id = :org
            """
            params = {
                "run_id": run_id,
                "org": org,
                "status": status,
                "budget_spent_usd": budget_spent_usd,
            }
        else:
            query = """
                UPDATE agent_runs
                SET status = :status, updated_at = now()
                WHERE id = :run_id AND organization_id = :org
            """
            params = {"run_id": run_id, "org": org, "status": status}

        result = await self._session.execute(text(query), params)
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def create_plan_step(
        self,
        org: UUID,
        run_id: UUID,
        step_index: int,
        assigned_agent: str,
        description: str,
        requires_approval: bool = False,
    ) -> UUID:
        step_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO agent_plans (
                id, organization_id, agent_run_id, step_index,
                assigned_agent, description, requires_approval, status,
                input_payload, output_payload
            )
            VALUES (
                :id, :org, :run_id, :step_index,
                :agent, :description, :requires_approval, 'pending',
                '{}'::jsonb, '{}'::jsonb
            )
            """),
            {
                "id": step_id,
                "org": org,
                "run_id": run_id,
                "step_index": step_index,
                "agent": assigned_agent,
                "description": description,
                "requires_approval": requires_approval,
            },
        )
        return step_id

    async def update_step_status(
        self,
        org: UUID,
        step_id: UUID,
        status: str,
        input_payload: dict[str, Any] | None = None,
        output_payload: dict[str, Any] | None = None,
    ) -> bool:
        set_clauses = ["status = :status", "updated_at = now()"]
        params: dict[str, Any] = {"step_id": step_id, "org": org, "status": status}

        if input_payload is not None:
            set_clauses.append("input_payload = CAST(:input AS jsonb)")
            params["input"] = json.dumps(input_payload)

        if output_payload is not None:
            set_clauses.append("output_payload = CAST(:output AS jsonb)")
            params["output"] = json.dumps(output_payload)

        query = "UPDATE agent_plans SET " + ", ".join(set_clauses) + " WHERE id = :step_id AND organization_id = :org"  # noqa: S608, E501
        result = await self._session.execute(text(query), params)
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def get_plan(self, org: UUID, run_id: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, agent_run_id, step_index, assigned_agent, description,
                   requires_approval, status, input_payload, output_payload,
                   created_at, updated_at
            FROM agent_plans
            WHERE agent_run_id = :run_id AND organization_id = :org
            ORDER BY step_index ASC
            """),
            {"run_id": run_id, "org": org},
        )
        return [dict(row) for row in result.mappings()]

    async def add_audit_log(
        self,
        org: UUID,
        run_id: UUID,
        step_id: UUID | None,
        action_type: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> UUID:
        log_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO agent_audit_logs (
                id, organization_id, agent_run_id, step_id,
                action_type, message, payload
            )
            VALUES (
                :id, :org, :run_id, :step_id,
                :action_type, :message, CAST(:payload AS jsonb)
            )
            """),
            {
                "id": log_id,
                "org": org,
                "run_id": run_id,
                "step_id": step_id,
                "action_type": action_type,
                "message": message,
                "payload": json.dumps(payload or {}),
            },
        )
        return log_id

    async def get_audit_logs(self, org: UUID, run_id: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, agent_run_id, step_id, action_type, message, payload, created_at
            FROM agent_audit_logs
            WHERE agent_run_id = :run_id AND organization_id = :org
            ORDER BY created_at ASC, id ASC
            """),
            {"run_id": run_id, "org": org},
        )
        return [dict(row) for row in result.mappings()]
