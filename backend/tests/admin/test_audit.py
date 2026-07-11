from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from aether.admin.policy import AdminPolicyEvaluator


class FakeSession:
    def __init__(self, role: str | None) -> None:
        self._role = role

    async def execute(self, statement: Any, parameters: dict[str, Any] | None = None) -> Any:
        if self._role in ("admin", "owner"):
            return FakeResult(self._role)
        return FakeResult(None)


class FakeResult:
    def __init__(self, value: Any) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value


@pytest.mark.asyncio
async def test_admin_policy_evaluator_role_restrictions() -> None:
    evaluator = AdminPolicyEvaluator()
    org_id, user_id = uuid4(), uuid4()

    # User is Admin
    admin_session = FakeSession("admin")
    has_access = await evaluator.check_admin_access(admin_session, org_id, user_id)  # type: ignore[arg-type]
    assert has_access is True

    # User is Owner
    owner_session = FakeSession("owner")
    has_access = await evaluator.check_admin_access(owner_session, org_id, user_id)  # type: ignore[arg-type]
    assert has_access is True

    # User is Member (Not Admin)
    member_session = FakeSession("member")
    has_access = await evaluator.check_admin_access(member_session, org_id, user_id)  # type: ignore[arg-type]
    assert has_access is False

    # User is not a member
    guest_session = FakeSession(None)
    has_access = await evaluator.check_admin_access(guest_session, org_id, user_id)  # type: ignore[arg-type]
    assert has_access is False
