"""Celery tasks for CPU metrics recalculation."""

from __future__ import annotations

import asyncio

from ..db import dispose_engine, session_scope
from ..services.cpu_analytics import CPUAnalyticsService
from ..telemetry import bind_request_context, clear_context, get_logger, new_request_id
from ..worker import celery_app

logger = get_logger("dealbrain.tasks.cpu_metrics")

RECALC_CPU_TASK_NAME = "cpu_metrics.recalculate_all"


async def _recalculate_all_cpu_metrics_async() -> dict[str, int]:
    """Asynchronously recalculate all CPU analytics.

    Processes all CPUs in the system, updating their price targets
    and performance metrics based on current listing data.

    Returns:
        Summary dict with total, success, and error counts
    """
    logger.info("cpu_metrics.recalc.start")

    async with session_scope() as session:
        result = await CPUAnalyticsService.recalculate_all_cpu_metrics(session)

    logger.info(
        "cpu_metrics.recalc.complete",
        total=result["total"],
        success=result["success"],
        errors=result["errors"],
    )

    # Alert if >10% failed
    if result["total"] > 0 and result["errors"] > result["total"] * 0.1:
        logger.error(
            "cpu_metrics.recalc.high_error_rate",
            error_count=result["errors"],
            total_count=result["total"],
            error_rate=f"{(result['errors'] / result['total'] * 100):.1f}%",
        )

    return result


@celery_app.task(name=RECALC_CPU_TASK_NAME, bind=True)
def recalculate_all_cpu_metrics(self) -> dict[str, int]:
    """Celery task entry-point for CPU metrics recalculation.

    Scheduled for nightly execution at 2:00 AM UTC via Celery Beat.
    Recalculates price targets and performance metrics for all CPUs
    based on current listing data.

    This task:
    1. Fetches all CPU IDs from the database
    2. For each CPU, calculates:
       - Price targets (good, great, fair) from active listing prices
       - Performance value ($/PassMark) metrics
    3. Updates CPU records with new analytics
    4. Returns summary with success/error counts

    Returns:
        dict: Summary with 'total', 'success', and 'errors' counts

    Raises:
        Exception: If task fails completely (individual CPU errors are logged but don't fail the task)
    """
    correlation_id = new_request_id()
    bind_request_context(correlation_id, task=RECALC_CPU_TASK_NAME, reason="scheduled_nightly")

    logger.info("cpu_metrics.recalc.dispatch", correlation_id=correlation_id)

    # Create fresh event loop for each task execution
    # This prevents "attached to a different loop" errors in forked worker processes
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)

        # Dispose existing engine if present to prevent "attached to a different loop" errors
        # The engine will be recreated with the new event loop on first use
        loop.run_until_complete(dispose_engine())

        return loop.run_until_complete(_recalculate_all_cpu_metrics_async())

    except Exception as exc:
        logger.error(
            "cpu_metrics.recalc.failed",
            error=str(exc),
            correlation_id=correlation_id,
            exc_info=True,
        )
        raise

    finally:
        # Clean up loop after task completion
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
            asyncio.set_event_loop(None)
            clear_context()


__all__ = ["recalculate_all_cpu_metrics"]
