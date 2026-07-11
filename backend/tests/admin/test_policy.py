from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.admin.service import AdminService


class FakeAdminRepository:
    def __init__(self) -> None:
        self.policies: dict[UUID, dict[str, Any]] = {}
        self.audit_events: list[dict[str, Any]] = []

    async def get_policy(self, org: UUID) -> dict[str, Any]:
        return self.policies.get(org, {
            "retention_days_notifications": 30,
            "retention_days_audit_logs": 365,
            "allow_unsecure_sandboxes": False,
            "break_glass_active": False,
            "break_glass_reason": None,
            "break_glass_activated_at": None,
        })

    async def upsert_policy(
        self,
        org: UUID,
        retention_notifs: int,
        retention_audit: int,
        allow_unsecure: bool,
    ) -> UUID:
        policy_id = uuid4()
        self.policies[org] = {
            "id": policy_id,
            "organization_id": org,
            "retention_days_notifications": retention_notifs,
            "retention_days_audit_logs": retention_audit,
            "allow_unsecure_sandboxes": allow_unsecure,
            "break_glass_active": False,
            "break_glass_reason": None,
            "break_glass_activated_at": None,
        }
        return policy_id

    async def set_break_glass(self, org: UUID, active: bool, reason: str | None) -> bool:
        if org not in self.policies:
            self.policies[org] = {
                "organization_id": org,
                "retention_days_notifications": 30,
                "retention_days_audit_logs": 365,
                "allow_unsecure_sandboxes": False,
            }
        self.policies[org]["break_glass_active"] = active
        self.policies[org]["break_glass_reason"] = reason
        return True

    async def create_audit_event(
        self,
        org: UUID,
        actor_id: UUID | None,
        event_type: str,
        target_type: str,
        target_id: UUID | None,
        outcome: str,
        correlation_id: UUID,
        metadata: dict[str, Any],
    ) -> UUID:
        event_id = uuid4()
        self.audit_events.append({
            "id": event_id,
            "organization_id": org,
            "actor_user_id": actor_id,
            "event_type": event_type,
            "target_type": target_type,
            "target_id": target_id,
            "outcome": outcome,
            "correlation_id": correlation_id,
            "metadata": metadata,
        })
        return event_id


@pytest.mark.asyncio
async def test_admin_update_policy_and_audit() -> None:
    repo = FakeAdminRepository()
    service = AdminService(repo)  # type: ignore[arg-type]
    org_id, actor_id = uuid4(), uuid4()

    # Initial update
    await service.update_policy(org_id, actor_id, 45, 180, True)

    policy = await repo.get_policy(org_id)
    assert policy["retention_days_notifications"] == 45
    assert policy["retention_days_audit_logs"] == 180
    assert policy["allow_unsecure_sandboxes"] is True

    # Audit validation
    assert len(repo.audit_events) == 1
    assert repo.audit_events[0]["event_type"] == "policy_updated"
    assert repo.audit_events[0]["actor_user_id"] == actor_id


@pytest.mark.asyncio
async def test_admin_break_glass_override() -> None:
    repo = FakeAdminRepository()
    service = AdminService(repo)  # type: ignore[arg-type]
    org_id, actor_id = uuid4(), uuid4()

    await service.toggle_break_glass(
        org_id, actor_id, active=True, reason="Database connection lock issue"
    )

    policy = await repo.get_policy(org_id)
    assert policy["break_glass_active"] is True
    assert policy["break_glass_reason"] == "Database connection lock issue"

    assert len(repo.audit_events) == 1
    assert repo.audit_events[0]["event_type"] == "break_glass_toggled"
