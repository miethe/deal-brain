"""Celery application placeholder for Deal Brain."""

from __future__ import annotations

from celery import Celery

celery_app = Celery("dealbrain")
celery_app.config_from_object({
    "broker_url": "redis://redis:6379/0",
    "result_backend": "redis://redis:6379/0",
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
})


@celery_app.task
def ping() -> str:
    """Simple task to verify the worker wiring."""
    return "pong"


# Import task modules to register with Celery
from .tasks import valuation as _valuation_tasks  # noqa: F401


__all__ = ["celery_app"]
