from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.admin.service import AdminService


class FakeAdminRepository:
    def __init__(self, session: Any) -> None:
        self._session = session
        self.memberships: dict[tuple[UUID, UUID], str] = {}
        self.audit_events: list[dict[str, Any]] = []

    async def upsert_membership(self, org: UUID, user_id: UUID, role: str) -> bool:
        self.memberships[(org, user_id)] = role
        return True

    async def delete_membership(self, org: UUID, user_id: UUID) -> bool:
        key = (org, user_id)
        if key in self.memberships:
            del self.memberships[key]
            return True
        return False

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


class FakeSession:
    """Mock Database Session matching scalar results for user lookup."""

    def __init__(self) -> None:
        self.users: dict[str, UUID] = {}

    async def execute(self, statement: Any, parameters: dict[str, Any] | None = None) -> Any:
        # Simple parser simulation
        query_str = str(statement)
        if "SELECT id FROM users" in query_str and parameters:
            email = parameters["email"]
            user_id = self.users.get(email)
            return FakeResult(user_id)
        elif "INSERT INTO users" in query_str and parameters:
            user_id = parameters["id"]
            email = parameters["email"]
            self.users[email] = user_id
            return None
        return None


class FakeResult:
    def __init__(self, value: Any) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value


@pytest.mark.asyncio
async def test_admin_invite_and_role_management() -> None:
    session = FakeSession()
    repo = FakeAdminRepository(session)
    service = AdminService(repo)  # type: ignore[arg-type]
    org_id, actor_id = uuid4(), uuid4()

    # Invite user
    invited_uid = await service.invite_member(org_id, actor_id, "newuser@aether.com", "member")
    assert invited_uid is not None
    assert repo.memberships[(org_id, invited_uid)] == "member"

    # Update role
    await service.update_member_role(org_id, actor_id, invited_uid, "admin")
    assert repo.memberships[(org_id, invited_uid)] == "admin"

    # Revoke membership
    revoked = await service.remove_member(org_id, actor_id, invited_uid)
    assert revoked is True
    assert (org_id, invited_uid) not in repo.memberships
