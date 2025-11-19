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
from .tasks import card_images as _card_images_tasks  # noqa: E402, F401
from .tasks import cpu_metrics as _cpu_metrics_tasks  # noqa: E402, F401
from .tasks import ingestion as _ingestion_tasks  # noqa: E402, F401
from .tasks import notifications as _notification_tasks  # noqa: E402, F401
from .tasks import valuation as _valuation_tasks  # noqa: E402, F401

# Configure periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    "cleanup-expired-payloads-nightly": {
        "task": "ingestion.cleanup_expired_payloads",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
        "options": {"expires": 3600},  # Task expires if not run within 1 hour
    },
    "recalculate-cpu-metrics-nightly": {
        "task": "cpu_metrics.recalculate_all",
        "schedule": crontab(hour=2, minute=30),  # Run at 2:30 AM UTC daily
        "options": {
            "expires": 3600 * 2,  # Task expires if not run within 2 hours
        },
    },
    "warm-cache-top-listings-nightly": {
        "task": "card_images.warm_cache_top_listings",
        "schedule": crontab(hour=3, minute=0),  # Run at 3 AM UTC daily (off-peak)
        "kwargs": {
            "limit": 100,  # Top 100 listings
            "metric": "cpu_mark_per_dollar",
        },
        "options": {
            "expires": 3600 * 2,  # Task expires if not run within 2 hours
        },
    },
    "cleanup-expired-card-cache-weekly": {
        "task": "card_images.cleanup_expired_cache",
        "schedule": crontab(hour=4, minute=0, day_of_week=0),  # Run Sundays at 4 AM UTC
        "options": {
            "expires": 3600 * 4,  # Task expires if not run within 4 hours
        },
    },
}

__all__ = ["celery_app"]
