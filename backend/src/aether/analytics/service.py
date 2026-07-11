"""Business service managing analytics dispatches, metrics caches, and CSV logs formatting."""

from __future__ import annotations

import csv
import io
from typing import Any
from uuid import UUID

from aether.analytics.policy import AnalyticsPolicyEvaluator
from aether.infrastructure.persistence.analytics_repository import SqlAlchemyAnalyticsRepository


class AnalyticsService:
    def __init__(self, repository: SqlAlchemyAnalyticsRepository) -> None:
        self._repository = repository

    async def log_event(
        self,
        org: UUID,
        user: UUID | None,
        event_name: str,
        category: str,
        cost: float,
        units: int,
        metadata: dict[str, Any],
    ) -> UUID:
        policy = AnalyticsPolicyEvaluator()
        scrubbed_meta = policy.scrub_event_metadata(metadata) or {}

        event_id = await self._repository.create_usage_event(
            org,
            user,
            event_name,
            category,
            cost,
            units,
            scrubbed_meta,
        )
        return event_id

    async def generate_csv_export(self, org: UUID) -> str:
        events = await self._repository.get_all_usage_events(org)

        output = io.StringIO()
        writer = csv.writer(output)
        # Write headers
        writer.writerow(["id", "event_name", "category", "cost", "units", "created_at"])

        for e in events:
            writer.writerow([
                str(e["id"]),
                e["event_name"],
                e["category"],
                f"{e['cost']:.6f}",
                str(e["units"]),
                e["created_at"].isoformat(),
            ])

        return output.getvalue()
class AnalyticsServiceManager:
    """Namespace container class for helper methods."""
    pass
