"""AI Agent execution engine coordinating runs, plans, policies, and audits."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text

from aether.agents.contracts import AgentType
from aether.agents.policy import AgentPolicyEvaluator
from aether.agents.registry import get_agent_orchestrator
from aether.infrastructure.persistence.agent_repository import SqlAlchemyAgentRepository

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Manages the lifecycle, planning, budget/time limits, and safety policies of agent runs."""

    def __init__(self, repository: SqlAlchemyAgentRepository) -> None:
        self._repository = repository

    async def start_run(
        self,
        org: UUID,
        user: UUID,
        goal: str,
        budget_limit_usd: float = 1.0000,
        time_limit_seconds: int = 600,
    ) -> UUID:
        """Initialize an agent run, generate its plan using the Planner agent,
        and begin execution."""
        # 1. Create run record
        run_id = await self._repository.create_run(
            org, user, goal, budget_limit_usd, time_limit_seconds
        )

        # 2. Add audit log of goal start
        await self._repository.add_audit_log(
            org,
            run_id,
            None,
            "state_transition",
            f"Agent run initialized with goal: '{goal}'",
            {"budget_limit": budget_limit_usd, "time_limit_seconds": time_limit_seconds},
        )

        try:
            # 3. Generate plan steps using Planner
            planner = get_agent_orchestrator(AgentType.PLANNER, org)
            plan_data = await planner.execute({"goal": goal})
            steps = plan_data.get("steps", [])

            if not steps:
                raise ValueError("Planner failed to generate any plan steps.")

            # 4. Save steps
            for idx, step in enumerate(steps):
                await self._repository.create_plan_step(
                    org,
                    run_id,
                    idx,
                    step["assigned_agent"],
                    step["description"],
                    step.get("requires_approval", False),
                )

            await self._repository.add_audit_log(
                org,
                run_id,
                None,
                "state_transition",
                f"Generated plan with {len(steps)} steps.",
                {"steps": steps},
            )

            # 5. Start executing
            await self._repository.update_run_status(org, run_id, "running")
            await self.execute_next_step(org, run_id)

        except Exception as error:
            logger.exception("Failed to initialize plan for run %s", run_id)
            await self._repository.update_run_status(org, run_id, "failed")
            await self._repository.add_audit_log(
                org, run_id, None, "error", f"Plan generation failed: {str(error)}"
            )

        return run_id

    async def execute_next_step(self, org: UUID, run_id: UUID) -> None:
        """Process the next pending plan step, validating limits and policies."""
        run = await self._repository.get_run(org, run_id)
        if not run or run["status"] != "running":
            return

        # 1. Enforce Time Limit
        now = datetime.now(UTC)
        if now > run["expires_at"]:
            await self._fail_run(org, run_id, "Execution time limit exceeded (timeout)")
            return

        # 2. Enforce Budget Limit
        budget_spent = float(run["budget_spent_usd"])
        budget_limit = float(run["budget_limit_usd"])
        if budget_spent >= budget_limit:
            await self._fail_run(
                org, run_id, f"Execution budget limit of ${budget_limit:.4f} exceeded"
            )
            return

        # 3. Get steps
        steps = await self._repository.get_plan(org, run_id)
        pending_step = None
        for step in steps:
            if step["status"] == "pending":
                pending_step = step
                break

        if pending_step is None:
            # All steps completed successfully
            await self._repository.update_run_status(org, run_id, "completed")
            await self._repository.add_audit_log(
                org, run_id, None, "state_transition", "Agent run completed successfully."
            )
            return

        # 4. Check for approval gate
        if pending_step["requires_approval"]:
            await self._repository.update_run_status(org, run_id, "awaiting_approval")
            await self._repository.add_audit_log(
                org,
                run_id,
                pending_step["id"],
                "policy_check",
                f"Step {pending_step['step_index']} requires user approval before execution.",
            )
            return

        # 5. Execute step
        await self._execute_step(org, run_id, pending_step, budget_spent)

    async def decide_approval(
        self, org: UUID, run_id: UUID, approved: bool, reason: str | None = None
    ) -> None:
        """Resolve user approval decisions for execution gates."""
        run = await self._repository.get_run(org, run_id)
        if not run or run["status"] != "awaiting_approval":
            raise ValueError("Run is not awaiting approval.")

        steps = await self._repository.get_plan(org, run_id)
        target_step = None
        for step in steps:
            if step["status"] == "pending":
                target_step = step
                break

        if not target_step:
            raise ValueError("No pending step found to approve.")

        if approved:
            await self._repository.add_audit_log(
                org,
                run_id,
                target_step["id"],
                "policy_check",
                f"User approved execution of step {target_step['step_index']}.",
                {"reason": reason},
            )
            # Remove approval block and run
            await self._repository.update_step_status(org, target_step["id"], "pending")
            await self._repository._session.execute(
                text(
                    "UPDATE agent_plans SET requires_approval = false "
                    "WHERE id = :id AND organization_id = :org"
                ),
                {"id": target_step["id"], "org": org},
            )
            await self._repository.update_run_status(org, run_id, "running")
            await self.execute_next_step(org, run_id)
        else:
            await self._repository.add_audit_log(
                org,
                run_id,
                target_step["id"],
                "policy_check",
                f"User rejected execution of step {target_step['step_index']}. "
                "Cancelling run.",
                {"reason": reason},
            )
            await self._repository.update_step_status(org, target_step["id"], "rejected")
            await self._repository.update_run_status(org, run_id, "cancelled")

    async def _execute_step(
        self, org: UUID, run_id: UUID, step: dict[str, Any], current_budget: float
    ) -> None:
        step_id = step["id"]
        assigned_agent = AgentType(step["assigned_agent"])
        input_payload = step["input_payload"]

        # Mark step as running
        await self._repository.update_step_status(org, step_id, "running")

        # Create policy evaluator
        policy = AgentPolicyEvaluator(org)

        try:
            # Evaluate tool call permissions
            # In a full model loop, tools are derived from inputs, but we validate mock tools here
            policy.validate_tool_call(assigned_agent, "read_file", input_payload)

            # Invoke agent execution
            agent = get_agent_orchestrator(assigned_agent, org)
            output = await agent.execute(input_payload)

            # Mark step as completed and save output
            await self._repository.update_step_status(
                org, step_id, "completed", output_payload=output
            )

            # Calculate and save budget spent (standard mock transaction charge of $0.05)
            step_cost = 0.0500
            new_budget = current_budget + step_cost
            await self._repository.update_run_status(
                org, run_id, "running", budget_spent_usd=new_budget
            )

            await self._repository.add_audit_log(
                org,
                run_id,
                step_id,
                "tool_call",
                f"Step {step['step_index']} ({assigned_agent.value}) completed successfully.",
                {"cost": step_cost, "output": output},
            )

            # Continue to next step
            await self.execute_next_step(org, run_id)

        except Exception as error:
            logger.exception("Step %s failed execution", step_id)
            await self._repository.update_step_status(org, step_id, "failed")
            await self._fail_run(org, run_id, f"Step {step['step_index']} failed: {str(error)}")

    async def _fail_run(self, org: UUID, run_id: UUID, reason: str) -> None:
        await self._repository.update_run_status(org, run_id, "failed")
        await self._repository.add_audit_log(org, run_id, None, "error", reason)
