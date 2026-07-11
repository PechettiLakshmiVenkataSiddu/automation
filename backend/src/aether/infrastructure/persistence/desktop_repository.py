"""PostgreSQL authority for isolated desktop tasks, approvals, and redacted artifacts."""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aether.desktop.contracts import DesktopAction


class SqlAlchemyDesktopRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_task(self, org: UUID, user: UUID, action: DesktopAction, status: str) -> UUID:
        task_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO desktop_tasks (
                id, organization_id, requested_by_user_id, status, operation, target_application,
                allowed_applications, allowed_mounts, network_enabled, credential_reference,
                idempotency_key, timeout_seconds, risk_class, expires_at
            )
            VALUES (
                :id, :org, :user, :status, :operation, :target, CAST(:apps AS jsonb),
                CAST(:mounts AS jsonb), :network, :credential, :idempotency, :timeout,
                :risk, now() + interval '10 minutes'
            )
        """),
            {
                "id": task_id,
                "org": org,
                "user": user,
                "status": status,
                "operation": action.operation,
                "target": action.target_application,
                "apps": json.dumps(list(action.allowed_applications)),
                "mounts": json.dumps(list(action.allowed_mounts)),
                "network": action.network_enabled,
                "credential": action.credential_reference,
                "idempotency": action.idempotency_key,
                "timeout": action.timeout_seconds,
                "risk": action.risk_class,
            },
        )
        return task_id

    async def find_by_idempotency(self, org: UUID, idempotency_key: str) -> UUID | None:
        row = (
            await self._session.execute(
                text(
                    "SELECT id FROM desktop_tasks WHERE organization_id=:org AND idempotency_key=:key"
                ),
                {"org": org, "key": idempotency_key},
            )
        ).scalar_one_or_none()
        return row

    async def create_approval(
        self,
        org: UUID,
        task_id: UUID,
        user: UUID,
        action: DesktopAction,
        policy_version: str,
    ) -> UUID:
        approval_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO desktop_task_approvals (
                id, organization_id, desktop_task_id, requested_by_user_id,
                action_summary, policy_version, expires_at
            )
            VALUES (:id, :org, :task, :user, CAST(:summary AS jsonb), :policy, now() + interval '24 hours')
        """),
            {
                "id": approval_id,
                "org": org,
                "task": task_id,
                "user": user,
                "summary": json.dumps(
                    {
                        "operation": action.operation,
                        "target_application": action.target_application,
                        "risk_class": action.risk_class,
                    }
                ),
                "policy": policy_version,
            },
        )
        return approval_id

    async def decide_approval(
        self,
        org: UUID,
        approval_id: UUID,
        decided_by: UUID,
        approved: bool,
        reason: str | None,
    ) -> UUID | None:
        row = (
            (
                await self._session.execute(
                    text("""
                    UPDATE desktop_task_approvals
                    SET status=:status, decided_by_user_id=:decided_by, decision_reason=:reason,
                        decided_at=now()
                    WHERE id=:approval_id AND organization_id=:org AND status='pending'
                    RETURNING desktop_task_id
                """),
                    {
                        "approval_id": approval_id,
                        "org": org,
                        "decided_by": decided_by,
                        "status": "approved" if approved else "rejected",
                        "reason": reason,
                    },
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        task_id = UUID(str(row["desktop_task_id"]))
        await self._session.execute(
            text("""
            UPDATE desktop_tasks
            SET status=:status, updated_at=now()
            WHERE id=:task_id AND organization_id=:org AND status='awaiting_approval'
        """),
            {
                "task_id": task_id,
                "org": org,
                "status": "queued" if approved else "cancelled",
            },
        )
        return task_id

    async def cancel(self, org: UUID, task_id: UUID) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE desktop_tasks
            SET cancellation_requested_at=now(),
                status=CASE WHEN status='queued' THEN 'cancelled' ELSE status END,
                updated_at=now()
            WHERE id=:task_id AND organization_id=:org
              AND status NOT IN ('succeeded','failed','cancelled')
        """),
            {"task_id": task_id, "org": org},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def get_task(self, org: UUID, task_id: UUID) -> dict[str, object] | None:
        row = (
            (
                await self._session.execute(
                    text("""
                    SELECT id, status, operation, target_application, allowed_applications,
                           allowed_mounts, network_enabled, credential_reference,
                           cancellation_requested_at, cleanup_verified_at, expires_at
                    FROM desktop_tasks WHERE id=:task_id AND organization_id=:org
                """),
                    {"task_id": task_id, "org": org},
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row else None

    async def issue_grant_task(self, org: UUID, task_id: UUID) -> dict[str, object] | None:
        row = (
            (
                await self._session.execute(
                    text("""
                    SELECT id, status, operation, target_application, allowed_applications,
                           allowed_mounts, network_enabled, timeout_seconds,
                           cancellation_requested_at, expires_at
                    FROM desktop_tasks
                    WHERE id=:task_id AND organization_id=:org
                      AND status='queued' AND expires_at > now()
                      AND cancellation_requested_at IS NULL
                """),
                    {"task_id": task_id, "org": org},
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row else None

    async def mark_running(self, org: UUID, task_id: UUID) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE desktop_tasks SET status='running', updated_at=now()
            WHERE id=:task_id AND organization_id=:org AND status='queued'
              AND cancellation_requested_at IS NULL AND expires_at > now()
        """),
            {"task_id": task_id, "org": org},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def complete_task(
        self, org: UUID, task_id: UUID, succeeded: bool, cleanup_verified: bool
    ) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE desktop_tasks
            SET status=:status,
                cleanup_verified_at=CASE WHEN :cleanup THEN now() ELSE cleanup_verified_at END,
                updated_at=now()
            WHERE id=:task_id AND organization_id=:org AND status='running'
        """),
            {
                "task_id": task_id,
                "org": org,
                "status": "succeeded" if succeeded else "failed",
                "cleanup": cleanup_verified,
            },
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def add_artifact(
        self, org: UUID, task_id: UUID, artifact_type: str, object_key: str, sha256: str
    ) -> UUID:
        artifact_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO desktop_task_artifacts (
                id, organization_id, desktop_task_id, artifact_type, object_key, sha256, redacted
            )
            SELECT :id, :org, id, :type, :key, :sha, true
            FROM desktop_tasks WHERE id=:task_id AND organization_id=:org
        """),
            {
                "id": artifact_id,
                "org": org,
                "task_id": task_id,
                "type": artifact_type,
                "key": object_key,
                "sha": sha256,
            },
        )
        return artifact_id
