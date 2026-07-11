from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest

from aether.analytics.policy import AnalyticsPolicyEvaluator
from aether.analytics.service import AnalyticsService


class FakeAnalyticsRepository:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

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
        self.events.append({
            "id": event_id,
            "organization_id": org,
            "user_id": user,
            "event_name": event_name,
            "category": category,
            "cost": cost,
            "units": units,
            "metadata": metadata,
        })
        return event_id


def test_analytics_policy_scrub_sensitive_meta() -> None:
    policy = AnalyticsPolicyEvaluator()

    safe_meta = {"model_name": "gpt-4o", "tokens_prompt": 120}
    assert policy.scrub_event_metadata(safe_meta) == safe_meta

    dangerous_meta = {"access_token": "secret_abc123", "normal_field": "hello"}
    scrubbed = policy.scrub_event_metadata(dangerous_meta)
    assert scrubbed is not None
    assert scrubbed["access_token"] == "[REDACTED]"  # noqa: S105
    assert scrubbed["normal_field"] == "hello"


@pytest.mark.asyncio
async def test_analytics_service_log_and_scrub() -> None:
    repo = FakeAnalyticsRepository()
    service = AnalyticsService(repo)  # type: ignore[arg-type]
    org_id, user_id = uuid4(), uuid4()

    meta = {"password_key": "raw_pass", "execution_mode": "secure"}
    event_id = await service.log_event(
        org_id,
        user_id,
        "Subprocess execution",
        "tool_execution",
        0.005,
        1,
        meta
    )

    assert event_id is not None
    assert len(repo.events) == 1
    assert repo.events[0]["metadata"]["password_key"] == "[REDACTED]"  # noqa: S105
    assert repo.events[0]["metadata"]["execution_mode"] == "secure"
