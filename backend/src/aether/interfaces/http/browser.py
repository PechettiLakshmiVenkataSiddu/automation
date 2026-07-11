"""Authenticated browser-task controls; execution remains outside this process."""

from __future__ import annotations

import base64
import hmac
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from aether.browser.artifacts import LocalArtifactStore
from aether.browser.contracts import BrowserAction
from aether.browser.egress import UnsafeBrowserEgress, validate_browser_url
from aether.infrastructure.persistence.browser_repository import SqlAlchemyBrowserRepository
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal

router = APIRouter(prefix="/v1/browser-tasks", tags=["browser"])


class BrowserTaskRequest(BaseModel):
    organization_id: UUID
    operation: str
    url: str
    allowed_hosts: tuple[str, ...] = Field(min_length=1, max_length=20)
    timeout_seconds: int = Field(ge=1, le=120)
    credential_reference: UUID | None = None


class ArtifactRequest(BaseModel):
    organization_id: UUID
    task_id: UUID
    artifact_type: str
    content_base64: str = Field(min_length=1, max_length=20_000_000)


async def _access(session: DatabaseSession, org: UUID, user: UUID) -> None:
    found = (
        await session.execute(
            text(
                "SELECT 1 FROM memberships WHERE organization_id=:org AND user_id=:user AND status='active' AND role IN ('owner','admin','member')"
            ),
            {"org": org, "user": user},
        )
    ).scalar_one_or_none()
    if found is None:
        raise HTTPException(status_code=403, detail="Organization access is denied")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_browser_task(
    body: BrowserTaskRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _access(session, body.organization_id, principal.user_id)
    try:
        action = BrowserAction(
            body.operation,
            body.url,
            body.timeout_seconds,
            body.allowed_hosts,
            body.credential_reference,
        )
        validate_browser_url(action.url, action.allowed_hosts)
    except (ValueError, UnsafeBrowserEgress) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    task_id = await SqlAlchemyBrowserRepository(session).create_task(
        body.organization_id, principal.user_id, body.allowed_hosts, body.credential_reference
    )
    return {"id": str(task_id)}


@router.post("/{task_id}/cancel")
async def cancel_browser_task(
    task_id: UUID,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, bool]:
    await _access(session, organization_id, principal.user_id)
    if not await SqlAlchemyBrowserRepository(session).cancel(organization_id, task_id):
        raise HTTPException(status_code=404, detail="Browser task is not cancellable")
    return {"cancelled": True}


@router.post("/internal/artifacts", include_in_schema=False)
async def ingest_artifact(
    body: ArtifactRequest, request: Request, session: DatabaseSession
) -> dict[str, str]:
    supplied = request.headers.get("X-Browser-Executor-Secret", "")
    expected = request.app.state.application_settings.browser_executor_secret
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Executor authentication failed")
    try:
        content = base64.b64decode(body.content_base64, validate=True)
        key, digest = LocalArtifactStore(
            request.app.state.application_settings.browser_artifact_root
        ).put(body.organization_id, body.task_id, body.artifact_type, content)
        artifact_id = await SqlAlchemyBrowserRepository(session).add_artifact(
            body.organization_id, body.task_id, body.artifact_type, key, digest
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Artifact is invalid") from error
    return {"id": str(artifact_id), "object_key": key}
