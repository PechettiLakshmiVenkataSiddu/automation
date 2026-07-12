"""Authenticated routes for sandboxed shell execution and decision gates."""

from __future__ import annotations
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Import your new Tool Registry
from aether.automation.tools import TOOL_REGISTRY 
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

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/developer", tags=["developer"])

async def _access(session: DatabaseSession, org: UUID, user: UUID, write: bool = False) -> str:
    row = (await session.execute(
        text("SELECT role FROM memberships WHERE organization_id=:org AND user_id=:user AND status='active'"),
        {"org": org, "user": user},
    )).scalar_one_or_none()
    if row is None or (write and row == "viewer"):
        raise HTTPException(status_code=403, detail="Organization access is denied")
    return str(row)

async def _run_command_in_background(
    org: UUID, command_id: UUID, sandbox_path: str, command_line: str,
    timeout_seconds: int, session_factory: async_sessionmaker[AsyncSession],
    task_type: str | None = None
) -> None:
    """Background runner supporting both legacy shell commands and new TOOL_REGISTRY tasks."""
    async with session_factory() as session:
        repo = SqlAlchemyDeveloperRepository(session)
        await repo.update_command_status(org, command_id, "running")
        await session.commit()

        # Dynamic Dispatch: If task_type is provided, route to TOOL_REGISTRY
        if task_type and task_type in TOOL_REGISTRY:
            try:
                output = await TOOL_REGISTRY[task_type].execute({"command": command_line})
                status_result = "succeeded"
                stdout = str(output)
                stderr = None
            except Exception as e:
                status_result = "failed"
                stdout = None
                stderr = str(e)
        else:
            # Legacy shell execution path
            exit_code, stdout, stderr = await DeveloperCommandExecutor.execute(
                command_line, sandbox_path, timeout_seconds
            )
            status_result = "succeeded" if exit_code == 0 else "failed"

        await repo.update_command_status(org, command_id, status_result, 0 if status_result=="succeeded" else 1, stdout, stderr)
        await session.commit()

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

    # Determine task type from request body (ensure your frontend sends this)
    task_type = getattr(body, "task_type", None)

    # Security policy evaluation (only for raw shell commands)
    if not task_type:
        evaluator = DeveloperCommandPolicyEvaluator()
        if evaluator.evaluate(body.command_line) == "blocked":
            raise HTTPException(status_code=400, detail="Command execution blocked.")

    command_id = await repo.create_command(
        body.organization_id, body.sandbox_id, body.command_line, body.timeout_seconds
    )

    background_tasks.add_task(
        _run_command_in_background,
        body.organization_id,
        command_id,
        sandbox["sandbox_path"],
        body.command_line,
        body.timeout_seconds,
        request.app.state.session_factory,
        task_type=task_type
    )
    return {"command_id": str(command_id), "status": "queued"}

# ... (retain your existing get_command and decide_command_approval endpoints)