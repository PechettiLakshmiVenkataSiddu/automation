"""PostgreSQL persistence authority for usage logging metrics."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyAnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_usage_event(
        self,
        org: UUID,
        user: UUID | None,
        event_name: str,
        category: str,
        cost: float,
        units: int,
        metadata: dict[str, Any],
    ) -> UUID:
        event_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO usage_events (
                id, organization_id, user_id, event_name,
                category, cost, units, metadata
            )
            VALUES (
                :id, :org, :user, :event_name, :category, :cost, :units, :metadata
            )
            """),
            {
                "id": event_id,
                "org": org,
                "user": user,
                "event_name": event_name,
                "category": category,
                "cost": cost,
                "units": units,
                "metadata": metadata,
            },
        )
        return event_id

    async def get_summary(self, org: UUID) -> dict[str, Any]:
        row = (
            await self._session.execute(
                text("""
                SELECT COALESCE(SUM(cost), 0.0) as total_cost,
                       COALESCE(COUNT(id), 0) as total_events
                FROM usage_events
                WHERE organization_id = :org
                """),
                {"org": org},
            )
        ).mappings().one_or_none()

        if row:
            return dict(row)

        return {"total_cost": 0.0, "total_events": 0}

    async def get_breakdown_by_category(self, org: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT category,
                   COALESCE(SUM(cost), 0.0) as total_cost,
                   COALESCE(SUM(units), 0) as total_units,
                   COUNT(id) as event_count
            FROM usage_events
            WHERE organization_id = :org
            GROUP BY category
            ORDER BY total_cost DESC
            """),
            {"org": org},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_breakdown_by_user(self, org: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT COALESCE(u.email, 'System') as email,
                   COALESCE(SUM(ue.cost), 0.0) as total_cost,
                   COUNT(ue.id) as event_count
            FROM usage_events ue
            LEFT JOIN users u ON ue.user_id = u.id
            WHERE ue.organization_id = :org
            GROUP BY u.email
            ORDER BY total_cost DESC
            """),
            {"org": org},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_workflow_metrics(self, org: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, organization_id, workflow_id,
                   run_count, success_count, failure_count,
                   avg_duration_seconds
            FROM workflow_metrics
            WHERE organization_id = :org
            ORDER BY run_count DESC
            """),
            {"org": org},
        )
        return [dict(row) for row in result.mappings().all()]

    async def upsert_workflow_run(
        self,
        org: UUID,
        workflow_id: UUID,
        success: bool,
        duration_seconds: float,
    ) -> bool:
        result = await self._session.execute(
            text("""
            INSERT INTO workflow_metrics (
                id, organization_id, workflow_id, run_count,
                success_count, failure_count, avg_duration_seconds
            )
            VALUES (
                gen_random_uuid(), :org, :workflow_id, 1,
                :success_val, :failure_val, :duration
            )
            ON CONFLICT (organization_id, workflow_id) DO UPDATE
            SET run_count = workflow_metrics.run_count + 1,
                success_count = workflow_metrics.success_count + :success_val,
                failure_count = workflow_metrics.failure_count + :failure_val,
                avg_duration_seconds = (
                    (
                        workflow_metrics.avg_duration_seconds * workflow_metrics.run_count
                        + :duration
                    ) / (workflow_metrics.run_count + 1)
                ),
                updated_at = now()
            """),
            {
                "org": org,
                "workflow_id": workflow_id,
                "success_val": 1 if success else 0,
                "failure_val": 0 if success else 1,
                "duration": duration_seconds,
            },
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def get_all_usage_events(self, org: UUID) -> list[dict[str, Any]]:
        result = await self._session.execute(
            text("""
            SELECT id, organization_id, user_id, event_name,
                   category, cost, units, metadata, created_at
            FROM usage_events
            WHERE organization_id = :org
            ORDER BY created_at DESC
            """),
            {"org": org},
        )
        return [dict(row) for row in result.mappings().all()]
class SqlAlchemyAnalyticsRepositoryManager:
    """Namespace container class for helper methods."""
    pass
