from aether.automation.queue import AutomationSettings, create_celery


def test_celery_uses_dedicated_durable_queues() -> None:
    app = create_celery(
        AutomationSettings(
            AUTOMATION_REDIS_URL="redis://localhost:6379/0",
            AUTOMATION_RESULT_BACKEND="redis://localhost:6379/1",
        )
    )
    assert app.conf.task_default_queue == "automation"
    assert app.conf.task_acks_late is True
