"""PostgreSQL-authoritative persistence for durable workflow execution."""

from __future__ import annotations

import json
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aether.automation.state_machine import RunStatus, require_transition


class SqlAlchemyWorkflowRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(
        self,
        organization_id: UUID,
        workflow_id: UUID,
        user_id: UUID,
        idempotency_key: str,
        input_value: dict[str, object],
    ) -> UUID:
        version_id = (
            await self._session.execute(
                text("""
            SELECT v.id FROM workflows w JOIN workflow_versions v
              ON v.workflow_id = w.id AND v.organization_id = w.organization_id
            WHERE w.id = :workflow_id AND w.organization_id = :organization_id
              AND w.status = 'active' AND v.version = w.current_version
        """),
                {"workflow_id": workflow_id, "organization_id": organization_id},
            )
        ).scalar_one_or_none()
        if version_id is None:
            raise ValueError("Workflow is not active in this organization")
        proposed_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO workflow_runs (id, organization_id, workflow_id, workflow_version_id,
              initiated_by_user_id, idempotency_key, trigger_type, status, input)
            VALUES (:id, :organization_id, :workflow_id, :version_id, :user_id, :key,
              'manual', 'queued', CAST(:input AS jsonb))
            ON CONFLICT (organization_id, idempotency_key) DO NOTHING
        """),
            {
                "id": proposed_id,
                "organization_id": organization_id,
                "workflow_id": workflow_id,
                "version_id": version_id,
                "user_id": user_id,
                "key": idempotency_key,
                "input": json.dumps(input_value),
            },
        )
        run_id = (
            await self._session.execute(
                text(
                    "SELECT id FROM workflow_runs WHERE organization_id = :organization_id AND idempotency_key = :key"
                ),
                {"organization_id": organization_id, "key": idempotency_key},
            )
        ).scalar_one()
        if run_id == proposed_id:
            await self._event(
                organization_id, run_id, "run.queued", user_id, {"idempotency_key": idempotency_key}
            )
            await self._outbox(
                organization_id,
                run_id,
                "workflow.run_requested",
                {"run_id": str(run_id), "organization_id": str(organization_id)},
            )
        return cast(UUID, run_id)

    async def claim(
        self, organization_id: UUID, run_id: UUID, lease_seconds: int = 60
    ) -> RunStatus | None:
        row = (
            await self._session.execute(
                text("""
            UPDATE workflow_runs SET execution_lease_expires_at = now() + (:lease_seconds * interval '1 second'),
              execution_attempt = execution_attempt + 1, updated_at = now()
            WHERE id = :run_id AND organization_id = :organization_id
              AND status IN ('queued', 'retry_scheduled')
              AND (execution_lease_expires_at IS NULL OR execution_lease_expires_at < now())
            RETURNING status
        """),
                {
                    "run_id": run_id,
                    "organization_id": organization_id,
                    "lease_seconds": lease_seconds,
                },
            )
        ).scalar_one_or_none()
        return RunStatus(row) if row is not None else None

    async def cancellation_requested(self, organization_id: UUID, run_id: UUID) -> bool:
        return bool(
            (
                await self._session.execute(
                    text(
                        "SELECT cancellation_requested_at IS NOT NULL FROM workflow_runs WHERE id = :run_id AND organization_id = :organization_id"
                    ),
                    {"run_id": run_id, "organization_id": organization_id},
                )
            ).scalar_one_or_none()
        )

    async def transition(
        self,
        organization_id: UUID,
        run_id: UUID,
        target: RunStatus,
        actor_user_id: UUID | None = None,
        detail: dict[str, object] | None = None,
    ) -> None:
        row = (
            await self._session.execute(
                text(
                    "SELECT status FROM workflow_runs WHERE id = :run_id AND organization_id = :organization_id FOR UPDATE"
                ),
                {"run_id": run_id, "organization_id": organization_id},
            )
        ).scalar_one_or_none()
        if row is None:
            raise ValueError("Workflow run was not found")
        require_transition(RunStatus(row), target)
        terminal = target in {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELLED}
        await self._session.execute(
            text("""
            UPDATE workflow_runs SET status = :status, started_at = CASE WHEN :status = 'running' THEN COALESCE(started_at, now()) ELSE started_at END,
              finished_at = CASE WHEN :terminal THEN now() ELSE finished_at END,
              execution_lease_expires_at = CASE WHEN :terminal OR :status = 'awaiting_approval' THEN NULL ELSE execution_lease_expires_at END, updated_at = now()
            WHERE id = :run_id AND organization_id = :organization_id
        """),
            {
                "status": target.value,
                "terminal": terminal,
                "run_id": run_id,
                "organization_id": organization_id,
            },
        )
        await self._event(
            organization_id, run_id, f"run.{target.value}", actor_user_id, detail or {}
        )

    async def request_cancel(
        self, organization_id: UUID, run_id: UUID, actor_user_id: UUID
    ) -> bool:
        row = (
            await self._session.execute(
                text("""
            UPDATE workflow_runs SET cancellation_requested_at = COALESCE(cancellation_requested_at, now()), updated_at = now()
            WHERE id = :run_id AND organization_id = :organization_id AND status NOT IN ('succeeded', 'failed', 'cancelled') RETURNING status
        """),
                {"run_id": run_id, "organization_id": organization_id},
            )
        ).scalar_one_or_none()
        if row is None:
            return False
        if RunStatus(row) in {
            RunStatus.QUEUED,
            RunStatus.RETRY_SCHEDULED,
            RunStatus.AWAITING_APPROVAL,
        }:
            await self.transition(organization_id, run_id, RunStatus.CANCELLED, actor_user_id)
        else:
            await self._event(
                organization_id, run_id, "run.cancellation_requested", actor_user_id, {}
            )
        return True

    async def retry(self, organization_id: UUID, run_id: UUID, actor_user_id: UUID) -> bool:
        row = (
            await self._session.execute(
                text(
                    "SELECT status FROM workflow_runs WHERE id=:run_id AND organization_id=:organization_id FOR UPDATE"
                ),
                {"run_id": run_id, "organization_id": organization_id},
            )
        ).scalar_one_or_none()
        if row != RunStatus.FAILED.value:
            return False
        await self._session.execute(
            text(
                "UPDATE workflow_runs SET status='queued', error_code=NULL, error_detail=NULL, finished_at=NULL, execution_lease_expires_at=NULL, updated_at=now() WHERE id=:run_id AND organization_id=:organization_id"
            ),
            {"run_id": run_id, "organization_id": organization_id},
        )
        await self._event(
            organization_id, run_id, "run.queued", actor_user_id, {"reason": "manual_retry"}
        )
        await self._outbox(
            organization_id,
            run_id,
            "workflow.run_requested",
            {"run_id": str(run_id), "organization_id": str(organization_id)},
        )
        return True

    async def recover_expired_leases(self, limit: int = 100) -> int:
        """Requeue abandoned work; the lease predicate prevents stealing live work."""
        rows = await self._session.execute(
            text("""
            WITH expired AS (
                SELECT id, organization_id FROM workflow_runs
                WHERE status = 'running' AND execution_lease_expires_at < now()
                ORDER BY execution_lease_expires_at FOR UPDATE SKIP LOCKED LIMIT :limit
            )
            UPDATE workflow_runs r SET status = 'retry_scheduled',
                execution_lease_expires_at = NULL, error_code = 'worker_lease_expired',
                updated_at = now()
            FROM expired e WHERE r.id = e.id AND r.organization_id = e.organization_id
            RETURNING r.id, r.organization_id
        """),
            {"limit": min(limit, 100)},
        )
        recovered = list(rows)
        for row in recovered:
            await self._event(
                row.organization_id,
                row.id,
                "run.retry_scheduled",
                None,
                {"reason": "worker_lease_expired"},
            )
            await self._session.execute(
                text("""
                UPDATE workflow_runs SET status = 'queued', updated_at = now()
                WHERE id = :run_id AND organization_id = :organization_id
                  AND status = 'retry_scheduled'
            """),
                {"run_id": row.id, "organization_id": row.organization_id},
            )
            await self._event(
                row.organization_id, row.id, "run.queued", None, {"reason": "lease_recovery"}
            )
            await self._outbox(
                row.organization_id,
                row.id,
                "workflow.run_requested",
                {"run_id": str(row.id), "organization_id": str(row.organization_id)},
            )
        return len(recovered)

    async def approve(
        self,
        organization_id: UUID,
        approval_id: UUID,
        user_id: UUID,
        approved: bool,
        reason: str | None,
    ) -> UUID | None:
        row = (
            await self._session.execute(
                text("""UPDATE approvals SET status=:status, decided_by_user_id=:user_id, decision_reason=:reason, decided_at=now()
            WHERE id=:approval_id AND organization_id=:organization_id AND status='pending' AND expires_at > now() RETURNING workflow_run_id"""),
                {
                    "status": "approved" if approved else "rejected",
                    "user_id": user_id,
                    "reason": reason,
                    "approval_id": approval_id,
                    "organization_id": organization_id,
                },
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        await self.transition(
            organization_id,
            row,
            RunStatus.QUEUED if approved else RunStatus.CANCELLED,
            user_id,
            {"approval_id": str(approval_id)},
        )
        if approved:
            await self._outbox(
                organization_id,
                row,
                "workflow.run_requested",
                {"run_id": str(row), "organization_id": str(organization_id)},
            )
        return cast(UUID, row)

    async def _event(
        self, org: UUID, run: UUID, event_type: str, actor: UUID | None, detail: dict[str, object]
    ) -> None:
        await self._session.execute(
            text(
                "INSERT INTO workflow_run_events (organization_id, workflow_run_id, event_type, actor_user_id, detail) VALUES (:org,:run,:event,:actor,CAST(:detail AS jsonb))"
            ),
            {
                "org": org,
                "run": run,
                "event": event_type,
                "actor": actor,
                "detail": json.dumps(detail),
            },
        )

    async def _outbox(
        self, org: UUID, run: UUID, event_type: str, payload: dict[str, object]
    ) -> None:
        await self._session.execute(
            text(
                "INSERT INTO outbox_events (organization_id, aggregate_type, aggregate_id, event_type, payload, correlation_id) SELECT organization_id, 'workflow_run', id, :event, CAST(:payload AS jsonb), correlation_id FROM workflow_runs WHERE id=:run AND organization_id=:org"
            ),
            {"org": org, "run": run, "event": event_type, "payload": json.dumps(payload)},
        )
