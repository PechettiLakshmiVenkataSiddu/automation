from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest


class FakeAnalyticsRepository:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.metrics: dict[tuple[UUID, UUID], dict[str, Any]] = {}

    async def get_summary(self, org: UUID) -> dict[str, Any]:
        cost = sum(e["cost"] for e in self.events if e["organization_id"] == org)
        return {"total_cost": cost, "total_events": len(self.events)}

    async def upsert_workflow_run(
        self,
        org: UUID,
        workflow_id: UUID,
        success: bool,
        duration_seconds: float,
    ) -> bool:
        key = (org, workflow_id)
        if key not in self.metrics:
            self.metrics[key] = {
                "organization_id": org,
                "workflow_id": workflow_id,
                "run_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "avg_duration_seconds": 0.0,
            }
        m = self.metrics[key]
        m["run_count"] += 1
        if success:
            m["success_count"] += 1
        else:
            m["failure_count"] += 1
        m["avg_duration_seconds"] = duration_seconds
        return True


@pytest.mark.asyncio
async def test_analytics_metrics_kpi_and_workflows() -> None:
    repo = FakeAnalyticsRepository()
    org_id, workflow_uid = uuid4(), uuid4()

    # Log mock events directly
    repo.events.append({"organization_id": org_id, "cost": 0.02, "units": 100})
    repo.events.append({"organization_id": org_id, "cost": 0.015, "units": 150})

    summary = await repo.get_summary(org_id)
    assert summary["total_cost"] == 0.035
    assert summary["total_events"] == 2

    # Update workflow metrics
    await repo.upsert_workflow_run(org_id, workflow_uid, success=True, duration_seconds=5.4)
    await repo.upsert_workflow_run(org_id, workflow_uid, success=False, duration_seconds=6.2)

    metric = repo.metrics[(org_id, workflow_uid)]
    assert metric["run_count"] == 2
    assert metric["success_count"] == 1
    assert metric["failure_count"] == 1
