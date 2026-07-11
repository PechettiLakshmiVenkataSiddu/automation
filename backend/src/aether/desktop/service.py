"""Policy, approval, audit, and idempotency gate for desktop task creation."""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aether.automation.policy import PolicyDecision, PolicyOutcome
from aether.desktop.contracts import DesktopAction
from aether.desktop.policy import DesktopPolicyEvaluator
from aether.infrastructure.persistence.desktop_repository import SqlAlchemyDesktopRepository


class DesktopTaskService:
    """Creates durable desktop tasks after policy, audit, approval, and idempotency checks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = SqlAlchemyDesktopRepository(session)
        self._evaluator = DesktopPolicyEvaluator()

    async def create(
        self, organization_id: UUID, user_id: UUID, action: DesktopAction
    ) -> tuple[UUID, str]:
        existing = await self._repository.find_by_idempotency(
            organization_id, action.idempotency_key
        )
        if existing is not None:
            return existing, "existing"

        decision = self._evaluator.evaluate(action, organization_id)
        correlation_id = uuid4()
        await self._audit(organization_id, user_id, action, decision, correlation_id)

        if decision.outcome is PolicyOutcome.DENY:
            raise PermissionError(decision.reason)

        status = "queued"
        if decision.outcome is PolicyOutcome.REQUIRE_APPROVAL:
            status = "awaiting_approval"

        task_id = await self._repository.create_task(
            organization_id,
            user_id,
            action,
            status,
        )

        if status == "awaiting_approval":
            await self._repository.create_approval(
                organization_id, task_id, user_id, action, decision.policy_version
            )

        return task_id, status

    async def decide_approval(
        self,
        organization_id: UUID,
        approval_id: UUID,
        decided_by: UUID,
        approved: bool,
        reason: str | None,
    ) -> UUID | None:
        return await self._repository.decide_approval(
            organization_id, approval_id, decided_by, approved, reason
        )

    async def _audit(
        self,
        organization_id: UUID,
        user_id: UUID,
        action: DesktopAction,
        decision: PolicyDecision,
        correlation_id: UUID,
    ) -> None:
        outcome = (
            "allowed"
            if decision.outcome is PolicyOutcome.ALLOW
            else ("pending" if decision.outcome is PolicyOutcome.REQUIRE_APPROVAL else "denied")
        )
        await self._session.execute(
            text("""
            INSERT INTO audit_events (organization_id, actor_user_id, event_type, target_type, target_id, outcome, policy_version, correlation_id, metadata)
            VALUES (:org,:actor,'desktop.action.policy','desktop_task',NULL,:outcome,:policy,:correlation,CAST(:metadata AS jsonb))
        """),
            {
                "org": organization_id,
                "actor": user_id,
                "outcome": outcome,
                "policy": decision.policy_version,
                "correlation": correlation_id,
                "metadata": json.dumps(
                    {
                        "operation": action.operation,
                        "risk_class": action.risk_class,
                        "target_application": action.target_application,
                    }
                ),
            },
        )
