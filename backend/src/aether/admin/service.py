"""Business service handling administrative control room settings."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import text

from aether.infrastructure.persistence.admin_repository import SqlAlchemyAdminRepository


class AdminService:
    def __init__(self, repository: SqlAlchemyAdminRepository) -> None:
        self._repository = repository

    async def update_policy(
        self,
        org: UUID,
        actor_id: UUID,
        retention_notifs: int,
        retention_audit: int,
        allow_unsecure: bool,
    ) -> UUID:
        policy_id = await self._repository.upsert_policy(
            org, retention_notifs, retention_audit, allow_unsecure
        )
        await self._repository.create_audit_event(
            org,
            actor_id,
            "policy_updated",
            "organization",
            org,
            "succeeded",
            uuid4(),
            {
                "retention_days_notifications": retention_notifs,
                "retention_days_audit_logs": retention_audit,
                "allow_unsecure_sandboxes": allow_unsecure,
            },
        )
        return policy_id

    async def toggle_break_glass(
        self, org: UUID, actor_id: UUID, active: bool, reason: str | None
    ) -> bool:
        success = await self._repository.set_break_glass(org, active, reason)
        await self._repository.create_audit_event(
            org,
            actor_id,
            "break_glass_toggled",
            "organization",
            org,
            "succeeded",
            uuid4(),
            {"active": active, "reason": reason},
        )
        return success

    async def invite_member(
        self, org: UUID, actor_id: UUID, email: str, role: str
    ) -> UUID:
        # Resolve email to user
        session = self._repository._session
        row = (
            await session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email},
            )
        ).scalar_one_or_none()

        if row:
            user_id = UUID(str(row))
        else:
            user_id = uuid4()
            # Create user placeholder
            await session.execute(
                text("""
                INSERT INTO users (id, email, password_hash, status)
                VALUES (:id, :email, 'N/A', 'active')
                """),
                {"id": user_id, "email": email},
            )

        await self._repository.upsert_membership(org, user_id, role)
        await self._repository.create_audit_event(
            org,
            actor_id,
            "member_invited",
            "user",
            user_id,
            "succeeded",
            uuid4(),
            {"email": email, "role": role},
        )
        return user_id

    async def update_member_role(
        self, org: UUID, actor_id: UUID, target_user_id: UUID, role: str
    ) -> bool:
        success = await self._repository.upsert_membership(org, target_user_id, role)
        await self._repository.create_audit_event(
            org,
            actor_id,
            "member_role_updated",
            "user",
            target_user_id,
            "succeeded",
            uuid4(),
            {"role": role},
        )
        return success

    async def remove_member(
        self, org: UUID, actor_id: UUID, target_user_id: UUID
    ) -> bool:
        success = await self._repository.delete_membership(org, target_user_id)
        await self._repository.create_audit_event(
            org,
            actor_id,
            "member_removed",
            "user",
            target_user_id,
            "succeeded",
            uuid4(),
            {},
        )
        return success

    async def generate_api_key(
        self,
        org: UUID,
        actor_id: UUID,
        name: str,
        expires_at: datetime | None,
    ) -> tuple[str, UUID]:
        prefix = "ak_" + secrets.token_hex(4)
        secret = secrets.token_urlsafe(32)
        combined_key = f"{prefix}_{secret}"
        secret_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()

        key_id = await self._repository.create_api_key(
            org, actor_id, name, prefix, secret_hash, expires_at
        )

        await self._repository.create_audit_event(
            org,
            actor_id,
            "api_key_created",
            "api_key",
            key_id,
            "succeeded",
            uuid4(),
            {"name": name},
        )
        return combined_key, key_id

    async def revoke_api_key(self, org: UUID, actor_id: UUID, key_id: UUID) -> bool:
        success = await self._repository.revoke_api_key(org, key_id)
        await self._repository.create_audit_event(
            org,
            actor_id,
            "api_key_revoked",
            "api_key",
            key_id,
            "succeeded",
            uuid4(),
            {},
        )
        return success

    async def revoke_connection(self, org: UUID, actor_id: UUID, provider: str) -> bool:
        success = await self._repository.delete_connection(org, provider)
        await self._repository.create_audit_event(
            org,
            actor_id,
            "connection_revoked",
            "connection",
            None,
            "succeeded",
            uuid4(),
            {"provider": provider},
        )
        return success
