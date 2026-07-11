"""Enforcement of administrative access credentials and safety guidelines."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AdminPolicyEvaluator:
    """Enforces role checks to ensure only authorized administrators execute admin operations."""

    async def check_admin_access(
        self, session: AsyncSession, org: UUID, user: UUID
    ) -> bool:
        """Verify user membership has admin/owner privileges."""
        row = (
            await session.execute(
                text("""
                SELECT role FROM memberships
                WHERE organization_id = :org
                  AND user_id = :user
                  AND status = 'active'
                  AND role IN ('admin', 'owner')
                """),
                {"org": org, "user": user},
            )
        ).scalar_one_or_none()
        return row is not None
