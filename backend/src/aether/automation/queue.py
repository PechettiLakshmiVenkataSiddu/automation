from celery import Celery, shared_task
from aether.automation.outbox import OutboxEvent
from pydantic_settings import BaseSettings

class AutomationSettings(BaseSettings):
    broker_url: str = "redis://redis:6379/0"
    result_backend: str = "redis://redis:6379/0"

def create_celery() -> Celery:
    settings = AutomationSettings()
    app = Celery("aether", broker=settings.broker_url, backend=settings.result_backend)
    app.conf.update(task_default_queue="automation")
    return app

# The required global instance
celery = create_celery()

@shared_task(name="aether.automation.workflow.run_requested")
def execute_run(payload: dict) -> None:
    pass # Add your workflow runner logic here