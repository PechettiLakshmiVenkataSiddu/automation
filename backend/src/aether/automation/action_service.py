"""Mandatory policy, approval, audit, and idempotency gate for external actions."""

from __future__ import annotations

import json
from typing import Protocol
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aether.automation.contracts import ActionAdapter, ActionContext, ActionContract
from aether.automation.policy import ActionIntent, PolicyDecision, PolicyOutcome


class PolicyEvaluator(Protocol):
    def evaluate(self, action: ActionIntent, organization_id: UUID) -> PolicyDecision: ...


class ActionExecutionService:
    """The only adapter entrypoint; a duplicate never reaches the external adapter."""

    def __init__(self, session: AsyncSession, evaluator: PolicyEvaluator) -> None:
        self._session, self._evaluator = session, evaluator

    async def execute(
        self,
        context: ActionContext,
        action: ActionContract,
        adapter: ActionAdapter,
        actor_user_id: UUID | None,
    ) -> dict[str, object] | None:
        decision = self._evaluator.evaluate(
            ActionIntent(action.action_type, action.risk_class, action.idempotency_key),
            context.organization_id,
        )
        await self._audit(context, actor_user_id, action, decision)
        if decision.outcome is PolicyOutcome.DENY:
            raise PermissionError(decision.reason)
        if decision.outcome is PolicyOutcome.REQUIRE_APPROVAL:
            await self._approval(context, actor_user_id, action, decision)
            return None
        reserved = await self._session.execute(
            text("""
            INSERT INTO workflow_idempotency_records (organization_id, idempotency_key, operation, resource_id)
            VALUES (:org,:key,:operation,:resource) ON CONFLICT (organization_id, operation, idempotency_key) DO NOTHING RETURNING id
        """),
            {
                "org": context.organization_id,
                "key": action.idempotency_key,
                "operation": action.action_type,
                "resource": context.workflow_step_id,
            },
        )
        if reserved.scalar_one_or_none() is None:
            return None
        return await adapter.execute(context, action)

    async def _approval(
        self,
        context: ActionContext,
        actor: UUID | None,
        action: ActionContract,
        decision: PolicyDecision,
    ) -> None:
        await self._session.execute(
            text("""
            INSERT INTO approvals (organization_id, workflow_run_id, workflow_step_id, requested_by_user_id, action_summary, policy_version, expires_at)
            VALUES (:org,:run,:step,:actor,CAST(:summary AS jsonb),:policy,now() + interval '24 hours')
        """),
            {
                "org": context.organization_id,
                "run": context.workflow_run_id,
                "step": context.workflow_step_id,
                "actor": actor,
                "summary": json.dumps(
                    {"action_type": action.action_type, "risk_class": action.risk_class}
                ),
                "policy": decision.policy_version,
            },
        )

    async def _audit(
        self,
        context: ActionContext,
        actor: UUID | None,
        action: ActionContract,
        decision: PolicyDecision,
    ) -> None:
        await self._session.execute(
            text("""
            INSERT INTO audit_events (organization_id, actor_user_id, event_type, target_type, target_id, outcome, policy_version, correlation_id, metadata)
            VALUES (:org,:actor,'workflow.action.policy','workflow_step',:step,:outcome,:policy,:correlation,CAST(:metadata AS jsonb))
        """),
            {
                "org": context.organization_id,
                "actor": actor,
                "step": context.workflow_step_id,
                "outcome": "allowed"
                if decision.outcome is PolicyOutcome.ALLOW
                else (
                    "pending" if decision.outcome is PolicyOutcome.REQUIRE_APPROVAL else "denied"
                ),
                "policy": decision.policy_version,
                "correlation": context.correlation_id,
                "metadata": json.dumps(
                    {"action_type": action.action_type, "risk_class": action.risk_class}
                ),
            },
        )
