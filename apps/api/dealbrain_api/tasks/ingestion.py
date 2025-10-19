"""Celery tasks for URL ingestion."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select

from ..db import session_scope
from ..models.core import ImportSession
from ..services.ingestion import IngestionService
from ..worker import celery_app

logger = logging.getLogger(__name__)

INGEST_TASK_NAME = "ingestion.ingest_url"
_INGEST_LOOP: asyncio.AbstractEventLoop | None = None


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

        # 2. Update status to running
        import_session.status = "running"
        await session.flush()

        try:
            # 3. Execute ingestion
            service = IngestionService(session)
            ingest_result = await service.ingest_single_url(url)

            # 4. Update ImportSession with result
            if ingest_result.success:
                # Map quality to status: full → complete, partial → partial
                import_session.status = (
                    "complete" if ingest_result.quality == "full" else "partial"
                )
                import_session.conflicts_json = {
                    "listing_id": ingest_result.listing_id,
                    "provenance": ingest_result.provenance,
                    "quality": ingest_result.quality,
                    "title": ingest_result.title,
                    "price": float(ingest_result.price) if ingest_result.price else None,
                    "vendor_item_id": ingest_result.vendor_item_id,
                    "marketplace": ingest_result.marketplace,
                }
            else:
                import_session.status = "failed"
                import_session.conflicts_json = {
                    "error": ingest_result.error,
                }

            await session.commit()

            logger.info(
                "URL ingestion async complete",
                extra={
                    "job_id": job_id,
                    "success": ingest_result.success,
                    "status": import_session.status,
                },
            )

            # 5. Return result dict
            return {
                "success": ingest_result.success,
                "listing_id": ingest_result.listing_id,
                "status": import_session.status,
                "provenance": ingest_result.provenance,
                "quality": ingest_result.quality,
                "error": ingest_result.error,
            }

        except Exception:
            # Roll back and re-raise
            await session.rollback()
            logger.exception(
                "Exception in URL ingestion async",
                extra={"job_id": job_id},
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

    # Set up async event loop (pattern from valuation.py)
    global _INGEST_LOOP
    loop = _INGEST_LOOP
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _INGEST_LOOP = loop

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
        asyncio.set_event_loop(None)


__all__ = ["ingest_url_task", "INGEST_TASK_NAME"]
