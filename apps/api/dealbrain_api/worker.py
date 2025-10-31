"""Celery application placeholder for Deal Brain."""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from dealbrain_api.settings import get_settings
from dealbrain_api.telemetry import get_logger, init_telemetry

celery_app = Celery("dealbrain")
celery_app.config_from_object(
    {
        "broker_url": "redis://redis:6379/0",
        "result_backend": "redis://redis:6379/0",
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "timezone": "UTC",
    }
)

init_telemetry(get_settings())
worker_logger = get_logger("dealbrain.celery")


@celery_app.task
def ping() -> str:
    """Simple task to verify the worker wiring."""
    return "pong"


# Import task modules to register with Celery
# Note: imports must be after celery_app definition to avoid circular imports
from .tasks import ingestion as _ingestion_tasks  # noqa: E402, F401
from .tasks import valuation as _valuation_tasks  # noqa: E402, F401

# Configure periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    "cleanup-expired-payloads-nightly": {
        "task": "ingestion.cleanup_expired_payloads",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
        "options": {"expires": 3600},  # Task expires if not run within 1 hour
    },
}

__all__ = ["celery_app"]
