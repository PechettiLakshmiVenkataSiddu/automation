"""Authenticated routes for sandboxed shell execution and decision gates."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from aether.developer.contracts import (
    CommandApprovalDecision,
    CommandSubmitRequest,
    SandboxCreateRequest,
)
from aether.developer.executor import DeveloperCommandExecutor
from aether.developer.policy import DeveloperCommandPolicyEvaluator
from aether.developer.sandbox import DeveloperSandboxManager
from aether.infrastructure.persistence.developer_repository import (
    SqlAlchemyDeveloperRepository,
)
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal

router = APIRouter(prefix="/v1/developer", tags=["developer"])


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


async def _run_command_in_background(
    org: UUID,
    command_id: UUID,
    sandbox_path: str,
    command_line: str,
    timeout_seconds: int,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Background runner for queued commands updating statuses and streams."""
    async with session_factory() as session:
        repo = SqlAlchemyDeveloperRepository(session)
        await repo.update_command_status(org, command_id, "running")
        await session.commit()

        # Run command with timeout protection
        exit_code, stdout, stderr = await DeveloperCommandExecutor.execute(
            command_line, sandbox_path, timeout_seconds
        )

        status_result = "succeeded" if exit_code == 0 else "failed"
        await repo.update_command_status(
            org, command_id, status_result, exit_code, stdout, stderr
        )
        await session.commit()


@router.post("/sandboxes", status_code=status.HTTP_201_CREATED)
async def create_sandbox(
    body: SandboxCreateRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)

    # Enforce safe subdirectory confinement (using current app dir as workspace root)
    manager = DeveloperSandboxManager(workspace_root=".")
    try:
        resolved_path = manager.ensure_sandbox(body.sandbox_path)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    repo = SqlAlchemyDeveloperRepository(session)
    sandbox_id = await repo.create_sandbox(
        body.organization_id, body.name, resolved_path
    )
    return {"sandbox_id": str(sandbox_id)}


@router.post("/commands", status_code=status.HTTP_201_CREATED)
async def submit_command(
    body: CommandSubmitRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)

    repo = SqlAlchemyDeveloperRepository(session)
    sandbox = await repo.get_sandbox(body.organization_id, body.sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox environment not found")

    # Evaluate safety policy filters
    evaluator = DeveloperCommandPolicyEvaluator()
    policy_status = evaluator.evaluate(body.command_line)

    if policy_status == "blocked":
        raise HTTPException(
            status_code=400, detail="Command execution blocked by security filters."
        )

    # Save command execution metadata in database
    command_id = await repo.create_command(
        body.organization_id, body.sandbox_id, body.command_line, body.timeout_seconds
    )

    if policy_status == "awaiting_approval":
        # Create approval record
        await repo.create_approval(
            body.organization_id, command_id, principal.user_id, "v1"
        )
        await repo.update_command_status(
            body.organization_id, command_id, "awaiting_approval"
        )
        return {"command_id": str(command_id), "status": "awaiting_approval"}

    # Safe to execute directly
    background_tasks.add_task(
        _run_command_in_background,
        body.organization_id,
        command_id,
        sandbox["sandbox_path"],
        body.command_line,
        body.timeout_seconds,
        request.app.state.session_factory,
    )
    return {"command_id": str(command_id), "status": "queued"}


@router.get("/commands/{id}")
async def get_command(
    id: UUID,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _access(session, organization_id, principal.user_id)
    repo = SqlAlchemyDeveloperRepository(session)
    cmd = await repo.get_command(organization_id, id)
    if not cmd:
        raise HTTPException(status_code=404, detail="Developer command not found")

    return {
        "id": str(cmd["id"]),
        "sandbox_id": str(cmd["sandbox_id"]),
        "command_line": cmd["command_line"],
        "status": cmd["status"],
        "exit_code": cmd["exit_code"],
        "stdout_redacted": cmd["stdout_redacted"],
        "stderr_redacted": cmd["stderr_redacted"],
        "timeout_seconds": cmd["timeout_seconds"],
        "created_at": cmd["created_at"].isoformat(),
        "updated_at": cmd["updated_at"].isoformat(),
    }


@router.post("/commands/{id}/approve")
async def decide_command_approval(
    id: UUID,
    body: CommandApprovalDecision,
    request: Request,
    background_tasks: BackgroundTasks,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    repo = SqlAlchemyDeveloperRepository(session)

    command_id = await repo.decide_approval(
        body.organization_id,
        body.approval_id,
        principal.user_id,
        body.approved,
        body.reason,
    )
    if not command_id:
        raise HTTPException(status_code=400, detail="Decision could not be applied.")

    if body.approved:
        cmd = await repo.get_command(body.organization_id, command_id)
        if not cmd:
            raise HTTPException(status_code=404, detail="Gated command not found")
        sandbox = await repo.get_sandbox(body.organization_id, cmd["sandbox_id"])
        if not sandbox:
            raise HTTPException(status_code=404, detail="Sandbox environment not found")

        # Run command in background after user approval
        background_tasks.add_task(
            _run_command_in_background,
            body.organization_id,
            command_id,
            sandbox["sandbox_path"],
            cmd["command_line"],
            cmd["timeout_seconds"],
            request.app.state.session_factory,
        )

    return {"status": "success"}
