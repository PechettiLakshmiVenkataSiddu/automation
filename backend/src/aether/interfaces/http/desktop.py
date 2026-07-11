"""Authenticated desktop-task controls; execution remains outside this process."""

from __future__ import annotations

import base64
import hmac
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from aether.desktop.access import UnsafeDesktopAccess, validate_desktop_target
from aether.desktop.artifacts import LocalArtifactStore
from aether.desktop.contracts import DesktopAction
from aether.desktop.grants import issue_grant
from aether.desktop.service import DesktopTaskService
from aether.infrastructure.persistence.desktop_repository import SqlAlchemyDesktopRepository
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal

router = APIRouter(prefix="/v1/desktop-tasks", tags=["desktop"])


class DesktopTaskRequest(BaseModel):
    organization_id: UUID
    operation: str
    target_application: str = Field(min_length=1, max_length=128)
    allowed_applications: tuple[str, ...] = Field(min_length=1, max_length=20)
    allowed_mounts: tuple[str, ...] = Field(default=(), max_length=10)
    network_enabled: bool = False
    timeout_seconds: int = Field(ge=1, le=120)
    credential_reference: UUID | None = None
    idempotency_key: str = Field(min_length=1, max_length=255)
    risk_class: str = Field(default="low", pattern="^(low|medium|high)$")


class ApprovalDecisionRequest(BaseModel):
    organization_id: UUID
    approved: bool
    reason: str | None = Field(default=None, max_length=2_000)


class ArtifactRequest(BaseModel):
    organization_id: UUID
    task_id: UUID
    artifact_type: str
    content_base64: str = Field(min_length=1, max_length=20_000_000)


class StatusRequest(BaseModel):
    organization_id: UUID
    task_id: UUID
    succeeded: bool
    cleanup_verified: bool


async def _access(session: DatabaseSession, org: UUID, user: UUID, write: bool = False) -> str:
    row = (
        await session.execute(
            text(
                "SELECT role FROM memberships WHERE organization_id=:org AND user_id=:user AND status='active'"
            ),
            {"org": org, "user": user},
        )
    ).scalar_one_or_none()
    if row is None or (write and row == "viewer"):
        raise HTTPException(status_code=403, detail="Organization access is denied")
    return str(row)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_desktop_task(
    body: DesktopTaskRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id, write=True)
    try:
        action = DesktopAction(
            body.operation,
            body.target_application,
            body.timeout_seconds,
            body.allowed_applications,
            body.allowed_mounts,
            body.network_enabled,
            body.credential_reference,
            body.idempotency_key,
            body.risk_class,
        )
        validate_desktop_target(
            action.target_application,
            action.allowed_applications,
            action.allowed_mounts,
            action.network_enabled,
        )
        task_id, task_status = await DesktopTaskService(session).create(
            body.organization_id, principal.user_id, action
        )
    except (ValueError, UnsafeDesktopAccess) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    return {"id": str(task_id), "status": task_status}


@router.get("/{task_id}")
async def get_desktop_task(
    task_id: UUID,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _access(session, organization_id, principal.user_id)
    task = await SqlAlchemyDesktopRepository(session).get_task(organization_id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Desktop task was not found")
    cancellation = task["cancellation_requested_at"]
    cleanup = task["cleanup_verified_at"]
    expires_at = task["expires_at"]
    return {
        "id": str(task["id"]),
        "status": task["status"],
        "operation": task["operation"],
        "target_application": task["target_application"],
        "cancellation_requested_at": (
            cancellation.isoformat() if isinstance(cancellation, datetime) else None
        ),
        "cleanup_verified_at": cleanup.isoformat() if isinstance(cleanup, datetime) else None,
        "expires_at": expires_at.isoformat()
        if isinstance(expires_at, datetime)
        else str(expires_at),
    }


@router.post("/{task_id}/cancel")
async def cancel_desktop_task(
    task_id: UUID,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, bool]:
    await _access(session, organization_id, principal.user_id, write=True)
    if not await SqlAlchemyDesktopRepository(session).cancel(organization_id, task_id):
        raise HTTPException(status_code=404, detail="Desktop task is not cancellable")
    return {"cancelled": True}


@router.post("/{task_id}/grant")
async def issue_desktop_grant(
    task_id: UUID,
    organization_id: UUID,
    request: Request,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    role = await _access(session, organization_id, principal.user_id, write=True)
    if role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Grant issuance requires an administrator")
    repository = SqlAlchemyDesktopRepository(session)
    task = await repository.issue_grant_task(organization_id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Desktop task is not grantable")
    if not await repository.mark_running(organization_id, task_id):
        raise HTTPException(status_code=409, detail="Desktop task could not be started")
    grant = issue_grant(
        request.app.state.application_settings.desktop_grant_secret.encode(),
        organization_id,
        task_id,
        ttl_seconds=300,
    )
    return {
        "grant": grant,
        "task_id": str(task_id),
        "action": {
            "organization_id": str(organization_id),
            "task_id": str(task_id),
            "operation": task["operation"],
            "target_application": task["target_application"],
            "allowed_applications": task["allowed_applications"],
            "allowed_mounts": task["allowed_mounts"],
            "network_enabled": task["network_enabled"],
            "timeout_seconds": task["timeout_seconds"],
        },
    }


@router.post("/approvals/{approval_id}/decision")
async def decide_desktop_approval(
    approval_id: UUID,
    body: ApprovalDecisionRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    role = await _access(session, body.organization_id, principal.user_id, write=True)
    if role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Approval requires an administrator")
    task_id = await DesktopTaskService(session).decide_approval(
        body.organization_id, approval_id, principal.user_id, body.approved, body.reason
    )
    if task_id is None:
        raise HTTPException(status_code=409, detail="Approval is unavailable")
    return {
        "desktop_task_id": str(task_id),
        "decision": "approved" if body.approved else "rejected",
    }


@router.post("/internal/artifacts", include_in_schema=False)
async def ingest_artifact(
    body: ArtifactRequest, request: Request, session: DatabaseSession
) -> dict[str, str]:
    supplied = request.headers.get("X-Desktop-Executor-Secret", "")
    expected = request.app.state.application_settings.desktop_executor_secret
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Executor authentication failed")
    try:
        content = base64.b64decode(body.content_base64, validate=True)
        key, digest = LocalArtifactStore(
            request.app.state.application_settings.desktop_artifact_root
        ).put(body.organization_id, body.task_id, body.artifact_type, content)
        artifact_id = await SqlAlchemyDesktopRepository(session).add_artifact(
            body.organization_id, body.task_id, body.artifact_type, key, digest
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Artifact is invalid") from error
    return {"id": str(artifact_id), "object_key": key}


@router.post("/internal/status", include_in_schema=False)
async def report_status(
    body: StatusRequest, request: Request, session: DatabaseSession
) -> dict[str, bool]:
    supplied = request.headers.get("X-Desktop-Executor-Secret", "")
    expected = request.app.state.application_settings.desktop_executor_secret
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Executor authentication failed")
    updated = await SqlAlchemyDesktopRepository(session).complete_task(
        body.organization_id, body.task_id, body.succeeded, body.cleanup_verified
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Desktop task status is not updatable")
    return {"updated": True}
