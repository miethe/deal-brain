"""Celery tasks for URL ingestion."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select

from ..db import session_scope
from ..models.core import ImportSession, RawPayload
from ..services.ingestion import IngestionService
from ..settings import get_settings
from ..worker import celery_app

logger = logging.getLogger(__name__)

INGEST_TASK_NAME = "ingestion.ingest_url"
CLEANUP_TASK_NAME = "ingestion.cleanup_expired_payloads"


async def _ingest_url_async(
    *,
    job_id: str,
    url: str,
) -> dict[str, Any]:
    """Async implementation of URL ingestion.

    Args:
        job_id: ImportSession UUID as string
        url: URL to ingest

    Returns:
        Dict with keys: success, listing_id, status, provenance, quality, error, etc.

    Raises:
        ValueError: If ImportSession not found
    """
    job_uuid = UUID(job_id)

    async with session_scope() as session:
        # 1. Load ImportSession
        stmt = select(ImportSession).where(ImportSession.id == job_uuid)
        result = await session.execute(stmt)
        import_session = result.scalar_one_or_none()

        if not import_session:
            raise ValueError(f"ImportSession {job_id} not found")

        try:
            # Milestone 1: Job started (10%)
            import_session.status = "running"
            import_session.progress_pct = 10
            await session.flush()
            logger.info(f"[{job_id}] Progress: 10% - Job started")

            # Initialize service
            service = IngestionService(session)

            # Milestone 2: Adapter extraction started (30%)
            import_session.progress_pct = 30
            await session.flush()
            logger.info(f"[{job_id}] Progress: 30% - Extracting data from URL")

            # Execute the full ingestion (includes extraction, normalization, persistence)
            ingest_result = await service.ingest_single_url(url)

            # Milestone 3: Normalization complete (60%)
            import_session.progress_pct = 60
            await session.flush()
            logger.info(f"[{job_id}] Progress: 60% - Data normalized")

            # Milestone 4: Persistence starting (80%)
            import_session.progress_pct = 80
            await session.flush()
            logger.info(f"[{job_id}] Progress: 80% - Saving to database")

            # Milestone 5: Complete (100%)
            if ingest_result.success:
                # Map quality to status: full → complete, partial → partial
                import_session.status = "complete" if ingest_result.quality == "full" else "partial"
                import_session.progress_pct = 100
                import_session.conflicts_json = {
                    "listing_id": ingest_result.listing_id,
                    "provenance": ingest_result.provenance,
                    "quality": ingest_result.quality,
                    "title": ingest_result.title,
                    "price": float(ingest_result.price) if ingest_result.price else None,
                    "vendor_item_id": ingest_result.vendor_item_id,
                    "marketplace": ingest_result.marketplace,
                }
                logger.info(f"[{job_id}] Progress: 100% - Import complete")
            else:
                import_session.status = "failed"
                import_session.progress_pct = 30  # Failed during extraction phase
                import_session.conflicts_json = {"error": ingest_result.error}
                logger.error(
                    "[%s] Import failed at %s%%: %s",
                    job_id,
                    import_session.progress_pct,
                    ingest_result.error,
                )

            await session.commit()

            logger.info(
                "URL ingestion async complete",
                extra={
                    "job_id": job_id,
                    "success": ingest_result.success,
                    "status": import_session.status,
                    "progress_pct": import_session.progress_pct,
                },
            )

            # Return result dict
            return {
                "success": ingest_result.success,
                "listing_id": ingest_result.listing_id,
                "status": import_session.status,
                "provenance": ingest_result.provenance,
                "quality": ingest_result.quality,
                "error": ingest_result.error,
                "progress_pct": import_session.progress_pct,
            }

        except Exception as e:
            # Set progress to where failure occurred (keep current progress if set)
            if import_session.progress_pct is None or import_session.progress_pct == 0:
                import_session.progress_pct = 10  # Failed at startup
            # Otherwise keep the current progress to show where it failed
            import_session.status = "failed"
            import_session.conflicts_json = {"error": str(e)}
            await session.commit()
            logger.exception(
                "Exception in URL ingestion async",
                extra={"job_id": job_id, "progress_pct": import_session.progress_pct},
            )
            raise


@celery_app.task(name=INGEST_TASK_NAME, bind=True, max_retries=3)
def ingest_url_task(
    self,
    *,
    job_id: str,
    url: str,
    adapter_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Celery task for async URL ingestion.

    Follows the async event loop pattern from valuation.py for consistency.
    Implements retry logic with exponential backoff for transient errors.

    Args:
        job_id: ImportSession UUID as string
        url: URL to ingest
        adapter_config: Optional adapter configuration (reserved for future use)

    Returns:
        Dict with ingestion result containing:
        - success: bool
        - listing_id: int | None
        - status: str (complete|partial|failed)
        - provenance: str
        - quality: str
        - error: str | None

    Raises:
        Retry: For transient errors (timeout, connection errors)
    """
    logger.info(
        "Starting URL ingestion task",
        extra={"job_id": job_id, "url": url, "retry": self.request.retries},
    )

    # Create fresh event loop for each task execution
    # This prevents "attached to a different loop" errors in forked worker processes
    loop = asyncio.new_event_loop()

    try:
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_ingest_url_async(job_id=job_id, url=url))

        logger.info(
            "URL ingestion task complete",
            extra={"job_id": job_id, "success": result["success"]},
        )
        return result

    except ValueError as e:
        # Permanent error (invalid URL, missing session)
        logger.error(
            "Permanent error in URL ingestion",
            extra={"job_id": job_id, "error": str(e)},
        )
        # Don't retry - mark as failed
        return {
            "success": False,
            "listing_id": None,
            "error": str(e),
            "status": "failed",
            "provenance": "unknown",
            "quality": "partial",
        }

    except (TimeoutError, ConnectionError) as e:
        # Transient error - retry with exponential backoff
        retry_countdown = 2**self.request.retries * 5
        logger.warning(
            "Transient error in URL ingestion, retrying",
            extra={
                "job_id": job_id,
                "error": str(e),
                "retry_count": self.request.retries,
                "countdown": retry_countdown,
            },
        )
        raise self.retry(exc=e, countdown=retry_countdown) from e

    except Exception as e:
        # Unknown error - retry once, then fail
        if self.request.retries < self.max_retries:
            retry_countdown = 2**self.request.retries * 5
            logger.exception(
                "Unknown error in URL ingestion, retrying",
                extra={"job_id": job_id, "retry_count": self.request.retries},
            )
            raise self.retry(exc=e, countdown=retry_countdown) from e
        else:
            logger.exception("URL ingestion failed after max retries", extra={"job_id": job_id})
            return {
                "success": False,
                "listing_id": None,
                "error": str(e),
                "status": "failed",
                "provenance": "unknown",
                "quality": "partial",
            }
    finally:
        # Clean up loop after task completion
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
            asyncio.set_event_loop(None)


async def _cleanup_expired_payloads_async() -> dict[str, Any]:
    """Async implementation of expired payload cleanup.

    Deletes RawPayload records older than configured TTL.
    Returns cleanup statistics for monitoring and logging.

    Returns:
        Dict with keys: deleted_count, ttl_days, cutoff_date

    Example:
        >>> result = await _cleanup_expired_payloads_async()
        >>> print(f"Deleted {result['deleted_count']} payloads")
    """
    settings = get_settings()
    ttl_days = settings.ingestion.raw_payload_ttl_days
    cutoff_date = datetime.utcnow() - timedelta(days=ttl_days)

    async with session_scope() as session:
        # Count records to delete for statistics
        count_stmt = (
            select(func.count()).select_from(RawPayload).where(RawPayload.created_at < cutoff_date)
        )
        result = await session.execute(count_stmt)
        count = result.scalar() or 0

        # Delete expired records
        if count > 0:
            delete_stmt = delete(RawPayload).where(RawPayload.created_at < cutoff_date)
            await session.execute(delete_stmt)
            await session.commit()

            logger.info(
                "Cleanup completed: deleted expired raw payloads",
                extra={
                    "deleted_count": count,
                    "ttl_days": ttl_days,
                    "cutoff_date": cutoff_date.isoformat(),
                },
            )
        else:
            logger.info(
                "Cleanup completed: no expired payloads found",
                extra={
                    "ttl_days": ttl_days,
                    "cutoff_date": cutoff_date.isoformat(),
                },
            )

        return {
            "deleted_count": count,
            "ttl_days": ttl_days,
            "cutoff_date": cutoff_date.isoformat(),
        }


@celery_app.task(name=CLEANUP_TASK_NAME)
def cleanup_expired_payloads_task() -> dict[str, Any]:
    """Celery task for cleaning up expired raw payloads.

    Runs as a periodic task (configured via Celery Beat) to remove
    RawPayload records older than configured TTL. Prevents unbounded
    storage growth while preserving recent payloads for debugging.

    Returns:
        Dict with cleanup statistics containing:
        - deleted_count: Number of records deleted
        - ttl_days: Configured TTL in days
        - cutoff_date: ISO timestamp of cutoff date

    Example:
        >>> result = cleanup_expired_payloads_task.delay()
        >>> result.get()
        {'deleted_count': 42, 'ttl_days': 30, 'cutoff_date': '2025-09-19T...'}
    """
    logger.info("Starting raw payload cleanup task")

    # Create fresh event loop for each task execution
    # This prevents "attached to a different loop" errors in forked worker processes
    loop = asyncio.new_event_loop()

    try:
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_cleanup_expired_payloads_async())

        logger.info(
            "Raw payload cleanup task complete",
            extra={
                "deleted_count": result["deleted_count"],
                "ttl_days": result["ttl_days"],
            },
        )
        return result

    except Exception as e:
        logger.exception("Error in raw payload cleanup task", extra={"error": str(e)})
        # Return error result instead of raising to prevent beat schedule from stopping
        return {
            "deleted_count": 0,
            "ttl_days": 0,
            "cutoff_date": None,
            "error": str(e),
        }

    finally:
        # Clean up loop after task completion
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
            asyncio.set_event_loop(None)


__all__ = [
    "ingest_url_task",
    "cleanup_expired_payloads_task",
    "INGEST_TASK_NAME",
    "CLEANUP_TASK_NAME",
]
