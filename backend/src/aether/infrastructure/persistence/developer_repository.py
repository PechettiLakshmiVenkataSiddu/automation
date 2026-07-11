"""PostgreSQL authority for Developer Tools sandboxes, commands, and approvals."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyDeveloperRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_sandbox(self, org: UUID, name: str, path: str) -> UUID:
        sandbox_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO developer_sandboxes (id, organization_id, name, sandbox_path, status)
            VALUES (:id, :org, :name, :path, 'active')
            """),
            {"id": sandbox_id, "org": org, "name": name, "path": path},
        )
        return sandbox_id

    async def get_sandbox(self, org: UUID, sandbox_id: UUID) -> dict[str, Any] | None:
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, name, sandbox_path, status, created_at, updated_at
                FROM developer_sandboxes
                WHERE id = :sandbox_id AND organization_id = :org
                """),
                {"sandbox_id": sandbox_id, "org": org},
            )
        ).mappings().one_or_none()
        return dict(row) if row else None

    async def find_sandbox_by_name(self, org: UUID, name: str) -> dict[str, Any] | None:
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, name, sandbox_path, status, created_at, updated_at
                FROM developer_sandboxes
                WHERE name = :name AND organization_id = :org AND status = 'active'
                """),
                {"name": name, "org": org},
            )
        ).mappings().one_or_none()
        return dict(row) if row else None

    async def create_command(
        self, org: UUID, sandbox_id: UUID, command_line: str, timeout_seconds: int = 30
    ) -> UUID:
        command_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO developer_commands (
                id, organization_id, sandbox_id, command_line, status, timeout_seconds
            )
            VALUES (:id, :org, :sandbox_id, :command_line, 'queued', :timeout)
            """),
            {
                "id": command_id,
                "org": org,
                "sandbox_id": sandbox_id,
                "command_line": command_line,
                "timeout": timeout_seconds,
            },
        )
        return command_id

    async def update_command_status(
        self,
        org: UUID,
        command_id: UUID,
        status: str,
        exit_code: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
    ) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE developer_commands
            SET status = :status, exit_code = :exit_code,
                stdout_redacted = :stdout, stderr_redacted = :stderr,
                updated_at = now()
            WHERE id = :command_id AND organization_id = :org
            """),
            {
                "command_id": command_id,
                "org": org,
                "status": status,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
            },
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def get_command(self, org: UUID, command_id: UUID) -> dict[str, Any] | None:
        row = (
            await self._session.execute(
                text("""
                SELECT id, organization_id, sandbox_id, command_line, status, exit_code,
                       stdout_redacted, stderr_redacted, timeout_seconds, created_at, updated_at
                FROM developer_commands
                WHERE id = :command_id AND organization_id = :org
                """),
                {"command_id": command_id, "org": org},
            )
        ).mappings().one_or_none()
        return dict(row) if row else None

    async def create_approval(
        self, org: UUID, command_id: UUID, user: UUID, policy_version: str
    ) -> UUID:
        approval_id = uuid4()
        expires_at = datetime.now(UTC) + timedelta(hours=24)
        await self._session.execute(
            text("""
            INSERT INTO developer_command_approvals (
                id, organization_id, command_id, requested_by_user_id,
                policy_version, status, expires_at
            )
            VALUES (:id, :org, :command_id, :user, :policy, 'pending', :expires_at)
            """),
            {
                "id": approval_id,
                "org": org,
                "command_id": command_id,
                "user": user,
                "policy": policy_version,
                "expires_at": expires_at,
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
                    UPDATE developer_command_approvals
                    SET status = :status, decided_by_user_id = :decided_by,
                        decision_reason = :reason, decided_at = now()
                    WHERE id = :approval_id AND organization_id = :org AND status = 'pending'
                    RETURNING command_id
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
        command_id = UUID(str(row["command_id"]))
        await self._session.execute(
            text("""
            UPDATE developer_commands
            SET status = :status, updated_at = now()
            WHERE id = :command_id AND organization_id = :org AND status = 'awaiting_approval'
            """),
            {
                "command_id": command_id,
                "org": org,
                "status": "queued" if approved else "cancelled",
            },
        )
        return command_id
