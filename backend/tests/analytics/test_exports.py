from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.analytics.service import AnalyticsService


class FakeAnalyticsRepository:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def get_all_usage_events(self, org: UUID) -> list[dict[str, Any]]:
        return [e for e in self.events if e["organization_id"] == org]


@pytest.mark.asyncio
async def test_analytics_csv_export_formatting() -> None:
    repo = FakeAnalyticsRepository()
    service = AnalyticsService(repo)  # type: ignore[arg-type]
    org1, org2 = uuid4(), uuid4()

    # Seed events
    repo.events.append({
        "id": uuid4(),
        "organization_id": org1,
        "event_name": "LLM Call",
        "category": "model_call",
        "cost": 0.002,
        "units": 200,
        "created_at": datetime.now(UTC),
    })
    repo.events.append({
        "id": uuid4(),
        "organization_id": org2,
        "event_name": "Calendar Sync",
        "category": "api_sync",
        "cost": 0.0,
        "units": 1,
        "created_at": datetime.now(UTC),
    })

    # Export org1
    csv_str = await service.generate_csv_export(org1)
    assert "LLM Call" in csv_str
    assert "model_call" in csv_str
    assert "0.002000" in csv_str
    assert "Calendar Sync" not in csv_str  # Tenant scoping enforced
