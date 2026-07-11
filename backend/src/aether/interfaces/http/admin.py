"""Authenticated endpoints for administrative control room settings."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from aether.admin.contracts import (
    BreakGlassRequest,
    CreateApiKeyRequest,
    InviteMemberRequest,
    PolicyUpdateRequest,
    UpdateMemberRequest,
)
from aether.admin.policy import AdminPolicyEvaluator
from aether.admin.service import AdminService
from aether.infrastructure.persistence.admin_repository import SqlAlchemyAdminRepository
from aether.interfaces.http.dependencies import DatabaseSession
from aether.interfaces.http.principal import Principal, get_principal

router = APIRouter(prefix="/v1/admin", tags=["admin"])


async def _check_admin(session: DatabaseSession, org: UUID, user: UUID) -> None:
    evaluator = AdminPolicyEvaluator()
    has_access = await evaluator.check_admin_access(session, org, user)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires administrator privileges.",
        )


@router.get("/policy")
async def get_policy(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, object]:
    await _check_admin(session, organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    policy = await repo.get_policy(organization_id)
    return {
        "retention_days_notifications": policy["retention_days_notifications"],
        "retention_days_audit_logs": policy["retention_days_audit_logs"],
        "allow_unsecure_sandboxes": policy["allow_unsecure_sandboxes"],
        "break_glass_active": policy["break_glass_active"],
        "break_glass_reason": policy["break_glass_reason"],
        "break_glass_activated_at": (
            policy["break_glass_activated_at"].isoformat()
            if policy["break_glass_activated_at"]
            else None
        ),
    }


@router.post("/policy")
async def update_policy(
    body: PolicyUpdateRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _check_admin(session, body.organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    service = AdminService(repo)
    await service.update_policy(
        body.organization_id,
        principal.user_id,
        body.retention_days_notifications,
        body.retention_days_audit_logs,
        body.allow_unsecure_sandboxes,
    )
    return {"status": "success"}


@router.post("/break-glass")
async def toggle_break_glass(
    body: BreakGlassRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _check_admin(session, body.organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    service = AdminService(repo)
    success = await service.toggle_break_glass(
        body.organization_id, principal.user_id, body.active, body.reason
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle break-glass mode.",
        )
    return {"status": "success"}


@router.get("/members")
async def get_members(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _check_admin(session, organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    members = await repo.get_members(organization_id)
    return [
        {
            "user_id": str(m["user_id"]),
            "email": m["email"],
            "role": m["role"],
            "status": m["status"],
            "created_at": m["created_at"].isoformat(),
        }
        for m in members
    ]


@router.post("/members")
async def invite_member(
    body: InviteMemberRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _check_admin(session, body.organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    service = AdminService(repo)
    user_id = await service.invite_member(
        body.organization_id, principal.user_id, body.email, body.role
    )
    return {"user_id": str(user_id)}


@router.put("/members")
async def update_member_role(
    body: UpdateMemberRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _check_admin(session, body.organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    service = AdminService(repo)
    success = await service.update_member_role(
        body.organization_id, principal.user_id, body.user_id, body.role
    )
    if not success:
        raise HTTPException(status_code=404, detail="Member was not found.")
    return {"status": "success"}


@router.delete("/members/{user_id}")
async def remove_member(
    user_id: UUID,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _check_admin(session, organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    service = AdminService(repo)
    success = await service.remove_member(organization_id, principal.user_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member was not found.")
    return {"status": "success"}


@router.get("/apikeys")
async def get_api_keys(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _check_admin(session, organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    keys = await repo.get_api_keys(organization_id)
    return [
        {
            "id": str(k["id"]),
            "organization_id": str(k["organization_id"]),
            "created_by_user_id": str(k["created_by_user_id"]),
            "name": k["name"],
            "key_prefix": k["key_prefix"],
            "last_used_at": k["last_used_at"].isoformat() if k["last_used_at"] else None,
            "expires_at": k["expires_at"].isoformat() if k["expires_at"] else None,
            "revoked_at": k["revoked_at"].isoformat() if k["revoked_at"] else None,
            "created_at": k["created_at"].isoformat(),
        }
        for k in keys
    ]


@router.post("/apikeys")
async def create_api_key(
    body: CreateApiKeyRequest,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _check_admin(session, body.organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    service = AdminService(repo)
    combined_key, key_id = await service.generate_api_key(
        body.organization_id, principal.user_id, body.name, body.expires_at
    )
    return {"id": str(key_id), "key": combined_key}


@router.delete("/apikeys/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _check_admin(session, organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    service = AdminService(repo)
    success = await service.revoke_api_key(organization_id, principal.user_id, key_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="API Key was not found or already revoked."
        )
    return {"status": "success"}


@router.get("/connections")
async def get_connections(
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _check_admin(session, organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    conns = await repo.get_connections(organization_id)
    return [
        {
            "id": str(c["id"]),
            "organization_id": str(c["organization_id"]),
            "provider": c["provider"],
            "scopes": c["scopes"],
            "status": c["status"],
            "created_at": c["created_at"].isoformat(),
        }
        for c in conns
    ]


@router.delete("/connections/{provider}")
async def revoke_connection(
    provider: str,
    organization_id: UUID,
    session: DatabaseSession,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    await _check_admin(session, organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    service = AdminService(repo)
    success = await service.revoke_connection(
        organization_id, principal.user_id, provider
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No active connection found for {provider}.",
        )
    return {"status": "success"}


@router.get("/audit")
async def search_audit_events(
    organization_id: UUID,
    session: DatabaseSession,
    event_type: str | None = None,
    target_type: str | None = None,
    actor_user_id: UUID | None = None,
    principal: Principal = Depends(get_principal),
) -> list[dict[str, object]]:
    await _check_admin(session, organization_id, principal.user_id)
    repo = SqlAlchemyAdminRepository(session)
    events = await repo.search_audit_events(
        organization_id, event_type, target_type, actor_user_id
    )
    return [
        {
            "id": str(e["id"]),
            "actor_user_id": str(e["actor_user_id"]) if e["actor_user_id"] else None,
            "delegated_actor": e["delegated_actor"],
            "event_type": e["event_type"],
            "target_type": e["target_type"],
            "target_id": str(e["target_id"]) if e["target_id"] else None,
            "outcome": e["outcome"],
            "policy_version": e["policy_version"],
            "correlation_id": str(e["correlation_id"]),
            "metadata": e["metadata"],
            "occurred_at": e["occurred_at"].isoformat(),
        }
        for e in events
    ]
