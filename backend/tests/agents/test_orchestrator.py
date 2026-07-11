from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.agents.orchestrator import AgentOrchestrator


class FakeAgentRepository:
    """Mock repository mimicking SqlAlchemyAgentRepository with in-memory dicts."""

    def __init__(self) -> None:
        self.runs: dict[UUID, dict[str, Any]] = {}
        self.plans: dict[UUID, list[dict[str, Any]]] = {}
        self.logs: dict[UUID, list[dict[str, Any]]] = {}
        self._session = None  # Mock session

    async def create_run(
        self,
        org: UUID,
        user: UUID,
        goal: str,
        budget_limit_usd: float = 1.0000,
        time_limit_seconds: int = 600,
    ) -> UUID:
        run_id = uuid4()
        self.runs[run_id] = {
            "id": run_id,
            "organization_id": org,
            "user_id": user,
            "goal": goal,
            "status": "queued",
            "budget_limit_usd": budget_limit_usd,
            "budget_spent_usd": 0.0000,
            "time_limit_seconds": time_limit_seconds,
            "expires_at": datetime.now(UTC) + timedelta(seconds=time_limit_seconds),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        self.plans[run_id] = []
        self.logs[run_id] = []
        return run_id

    async def get_run(self, org: UUID, run_id: UUID) -> dict[str, Any] | None:
        return self.runs.get(run_id)

    async def update_run_status(
        self, org: UUID, run_id: UUID, status: str, budget_spent_usd: float | None = None
    ) -> bool:
        if run_id not in self.runs:
            return False
        self.runs[run_id]["status"] = status
        if budget_spent_usd is not None:
            self.runs[run_id]["budget_spent_usd"] = budget_spent_usd
        self.runs[run_id]["updated_at"] = datetime.now(UTC)
        return True

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
        self.plans[run_id].append(
            {
                "id": step_id,
                "organization_id": org,
                "agent_run_id": run_id,
                "step_index": step_index,
                "assigned_agent": assigned_agent,
                "description": description,
                "requires_approval": requires_approval,
                "status": "pending",
                "input_payload": {},
                "output_payload": {},
            }
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
        for _run_id, steps in self.plans.items():
            for step in steps:
                if step["id"] == step_id:
                    step["status"] = status
                    if input_payload is not None:
                        step["input_payload"] = input_payload
                    if output_payload is not None:
                        step["output_payload"] = output_payload
                    return True
        return False

    async def get_plan(self, org: UUID, run_id: UUID) -> list[dict[str, Any]]:
        return self.plans.get(run_id, [])

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
        self.logs[run_id].append(
            {
                "id": log_id,
                "organization_id": org,
                "agent_run_id": run_id,
                "step_id": step_id,
                "action_type": action_type,
                "message": message,
                "payload": payload or {},
                "created_at": datetime.now(UTC),
            }
        )
        return log_id

    async def get_audit_logs(self, org: UUID, run_id: UUID) -> list[dict[str, Any]]:
        return self.logs.get(run_id, [])


@pytest.mark.asyncio
async def test_orchestrator_successful_flow() -> None:
    repo = FakeAgentRepository()
    orchestrator = AgentOrchestrator(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    run_id = await orchestrator.start_run(org_id, user_id, "Analyze Aether architecture")
    assert run_id in repo.runs
    assert repo.runs[run_id]["status"] == "completed"

    plan = repo.plans[run_id]
    assert len(plan) == 2
    assert plan[0]["status"] == "completed"
    assert plan[1]["status"] == "completed"

    logs = repo.logs[run_id]
    assert any(log["action_type"] == "state_transition" for log in logs)
    assert any(log["action_type"] == "tool_call" for log in logs)


@pytest.mark.asyncio
async def test_orchestrator_budget_limit_gate() -> None:
    repo = FakeAgentRepository()
    orchestrator = AgentOrchestrator(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    # Very small budget limit ($0.01) to force a fail on execution
    # of the first step (which costs $0.05).
    run_id = await orchestrator.start_run(
        org_id, user_id, "Analyze architecture", budget_limit_usd=0.01
    )
    assert repo.runs[run_id]["status"] == "failed"

    logs = repo.logs[run_id]
    assert any("budget limit" in log["message"] for log in logs)


@pytest.mark.asyncio
async def test_orchestrator_time_limit_gate() -> None:
    repo = FakeAgentRepository()
    orchestrator = AgentOrchestrator(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    # Create run with expired timestamp
    run_id = await orchestrator.start_run(
        org_id, user_id, "Analyze architecture", time_limit_seconds=1
    )
    repo.runs[run_id]["status"] = "running"
    for step in repo.plans[run_id]:
        step["status"] = "pending"
    repo.runs[run_id]["expires_at"] = datetime.now(UTC) - timedelta(seconds=1)

    # Force execution of next step
    await orchestrator.execute_next_step(org_id, run_id)
    assert repo.runs[run_id]["status"] == "failed"

    logs = repo.logs[run_id]
    assert any("time limit" in log["message"] for log in logs)


@pytest.mark.asyncio
async def test_orchestrator_approval_decision_gate() -> None:
    repo = FakeAgentRepository()
    orchestrator = AgentOrchestrator(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    # A goal with "email" triggers an approval required step
    run_id = await orchestrator.start_run(org_id, user_id, "Send research summary by email")
    assert repo.runs[run_id]["status"] == "awaiting_approval"

    # User rejects the approval gate
    await orchestrator.decide_approval(org_id, run_id, approved=False, reason="Too expensive")
    assert repo.runs[run_id]["status"] == "cancelled"
    assert repo.plans[run_id][2]["status"] == "rejected"
