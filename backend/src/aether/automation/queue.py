"""Celery configuration for durable workflow execution queues."""

from __future__ import annotations

from celery import Celery, shared_task  # type: ignore[import-untyped]
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from aether.automation.outbox import OutboxEvent


class AutomationSettings(BaseSettings):
    """Queue configuration; Redis contains transport state only."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    broker_url: str = Field(alias="AUTOMATION_REDIS_URL")
    result_backend: str = Field(alias="AUTOMATION_RESULT_BACKEND")


def create_celery(settings: AutomationSettings) -> Celery:
    """Create workers with separate durable execution and outbox queues."""
    app = Celery("aether", broker=settings.broker_url, backend=settings.result_backend)
    app.conf.update(
        task_default_queue="automation",
        task_routes={
            "aether.automation.publish_outbox": {"queue": "outbox"},
            "aether.automation.workflow.run_requested": {"queue": "automation"},
            "aether.automation.recover_runs": {"queue": "automation"},
        },
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_time_limit=300,
        task_soft_time_limit=270,
    )
    return app


class CeleryEventDispatcher:
    """Publishes only the immutable organization-scoped outbox envelope."""

    def __init__(self, app: Celery) -> None:
        self._app = app

    async def dispatch(self, event: OutboxEvent) -> None:
        organization_id = event.organization_id
        payload = event.payload
        event_type = event.event_type
        if organization_id is None or not isinstance(payload, dict):
            raise ValueError("Automation events require an organization-scoped payload")
        if payload.get("organization_id") != str(organization_id):
            raise ValueError("Outbox payload organization does not match envelope")
        self._app.send_task(f"aether.automation.{event_type}", args=[payload], queue="automation")


@shared_task(name="aether.automation.workflow.run_requested")  # type: ignore[untyped-decorator]
def execute_run(payload: dict[str, str]) -> None:
    """Worker entrypoint; the database lease makes duplicate deliveries harmless."""
    import asyncio
    from uuid import UUID

    from aether.automation.runner import WorkflowRunner
    from aether.bootstrap.database import create_engine, create_session_factory, session_scope
    from aether.bootstrap.settings import ApplicationSettings
    from aether.infrastructure.persistence.automation_repository import (
        SqlAlchemyWorkflowRunRepository,
    )

    async def work() -> None:
        settings = ApplicationSettings()  # type: ignore[call-arg]
        engine = create_engine(settings.database_url)
        try:
            async for session in session_scope(create_session_factory(engine)):
                runner = WorkflowRunner(SqlAlchemyWorkflowRunRepository(session))
                await runner.begin(UUID(payload["organization_id"]), UUID(payload["run_id"]))
        finally:
            await engine.dispose()

    asyncio.run(work())


@shared_task(name="aether.automation.publish_outbox")  # type: ignore[untyped-decorator]
def publish_outbox() -> int:
    """Dispatch pending events; unsuccessful events remain in PostgreSQL for backoff."""
    import asyncio

    from aether.automation.outbox import SqlAlchemyOutbox, publish_claimed
    from aether.bootstrap.database import create_engine, create_session_factory, session_scope
    from aether.bootstrap.settings import ApplicationSettings

    async def work() -> int:
        settings = ApplicationSettings()  # type: ignore[call-arg]
        engine = create_engine(settings.database_url)
        try:
            async for session in session_scope(create_session_factory(engine)):
                app = create_celery(AutomationSettings())  # type: ignore[call-arg]
                return await publish_claimed(SqlAlchemyOutbox(session), CeleryEventDispatcher(app))
        finally:
            await engine.dispose()
        return 0

    return asyncio.run(work())


@shared_task(name="aether.automation.recover_runs")  # type: ignore[untyped-decorator]
def recover_runs() -> int:
    """Periodic recovery task for work abandoned by a lost worker."""
    import asyncio

    from aether.bootstrap.database import create_engine, create_session_factory, session_scope
    from aether.bootstrap.settings import ApplicationSettings
    from aether.infrastructure.persistence.automation_repository import (
        SqlAlchemyWorkflowRunRepository,
    )

    async def work() -> int:
        settings = ApplicationSettings()  # type: ignore[call-arg]
        engine = create_engine(settings.database_url)
        try:
            async for session in session_scope(create_session_factory(engine)):
                return await SqlAlchemyWorkflowRunRepository(session).recover_expired_leases()
        finally:
            await engine.dispose()
        return 0

    return asyncio.run(work())
