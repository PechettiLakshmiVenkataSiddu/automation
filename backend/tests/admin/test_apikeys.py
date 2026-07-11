from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.admin.service import AdminService


class FakeAdminRepository:
    def __init__(self) -> None:
        self.api_keys: dict[UUID, dict[str, Any]] = {}
        self.audit_events: list[dict[str, Any]] = []

    async def create_api_key(
        self,
        org: UUID,
        user_id: UUID,
        name: str,
        key_prefix: str,
        secret_hash: str,
        expires_at: datetime | None,
    ) -> UUID:
        key_id = uuid4()
        self.api_keys[key_id] = {
            "id": key_id,
            "organization_id": org,
            "created_by_user_id": user_id,
            "name": name,
            "key_prefix": key_prefix,
            "secret_hash": secret_hash,
            "expires_at": expires_at,
            "revoked_at": None,
        }
        return key_id

    async def revoke_api_key(self, org: UUID, key_id: UUID) -> bool:
        if key_id not in self.api_keys:
            return False
        self.api_keys[key_id]["revoked_at"] = datetime.now()
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
async def test_admin_api_key_lifecycle() -> None:
    repo = FakeAdminRepository()
    service = AdminService(repo)  # type: ignore[arg-type]
    org_id, actor_id = uuid4(), uuid4()

    # Generate key
    key_token, key_id = await service.generate_api_key(
        org_id, actor_id, "Staging Server Key", None
    )
    assert key_token.startswith("ak_")
    assert key_id in repo.api_keys

    # Revoke key
    revoked = await service.revoke_api_key(org_id, actor_id, key_id)
    assert revoked is True
    assert repo.api_keys[key_id]["revoked_at"] is not None
