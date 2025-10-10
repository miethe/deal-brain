"""Celery tasks for listing valuation recalculation."""

from __future__ import annotations

import asyncio
import logging
from typing import Iterable, Sequence

from sqlalchemy import select

from ..db import session_scope
from ..models import Listing
from ..worker import celery_app
from ..services.listings import apply_listing_metrics
from dealbrain_core.enums import ListingStatus

logger = logging.getLogger(__name__)

RECALC_TASK_NAME = "valuation.recalculate_listings"


def _normalize_listing_ids(listing_ids: Iterable[int | str | None] | None) -> list[int]:
    if not listing_ids:
        return []
    normalized: list[int] = []
    seen: set[int] = set()
    for value in listing_ids:
        if value is None:
            continue
        try:
            listing_id = int(value)
        except (TypeError, ValueError):
            continue
        if listing_id < 0 or listing_id in seen:
            continue
        seen.add(listing_id)
        normalized.append(listing_id)
    return normalized


async def _recalculate_listings_async(
    *,
    listing_ids: Sequence[int] | None = None,
    ruleset_id: int | None = None,
    batch_size: int = 100,
    include_inactive: bool = False,
) -> dict[str, int]:
    """Asynchronously recalculate valuations for listings.

    Args:
        listing_ids: Explicit listing IDs to recalc. If omitted, all listings are processed.
        ruleset_id: Optional ruleset identifier for logging/metrics.
        batch_size: Number of listings to process per batch.
        include_inactive: If True, include inactive listings in automatic runs.
    """
    counters = {"processed": 0, "succeeded": 0, "failed": 0}

    async with session_scope() as session:
        stmt = select(Listing.id).order_by(Listing.id)
        if listing_ids:
            stmt = stmt.where(Listing.id.in_(listing_ids))
        elif not include_inactive:
            stmt = stmt.where(Listing.status == ListingStatus.ACTIVE.value)

        ids_batch: list[int] = []

        async for listing_id in session.stream_scalars(stmt):
            ids_batch.append(listing_id)
            if len(ids_batch) >= batch_size:
                await _process_batch(session, ids_batch, counters)
                ids_batch = []

        if ids_batch:
            await _process_batch(session, ids_batch, counters)

        await session.commit()

    logger.info(
        "Valuation recalculation complete",
        extra={
            "processed": counters["processed"],
            "succeeded": counters["succeeded"],
            "failed": counters["failed"],
            "ruleset_id": ruleset_id,
        },
    )
    return counters


async def _process_batch(session, listing_ids: Sequence[int], counters: dict[str, int]) -> None:
    """Process a single batch of listings."""
    if not listing_ids:
        return

    stmt = select(Listing).where(Listing.id.in_(listing_ids))
    result = await session.execute(stmt)
    listings = list(result.scalars().unique().all())

    for listing in listings:
        counters["processed"] += 1
        try:
            await apply_listing_metrics(session, listing)
            counters["succeeded"] += 1
        except Exception as exc:  # pragma: no cover - defensive logging
            counters["failed"] += 1
            logger.exception("Failed to recalculate listing %s", listing.id, exc_info=exc)


@celery_app.task(name=RECALC_TASK_NAME, bind=True)
def recalculate_listings_task(
    self,
    *,
    listing_ids: Iterable[int | str | None] | None = None,
    ruleset_id: int | None = None,
    batch_size: int = 100,
    include_inactive: bool = False,
    reason: str | None = None,
) -> dict[str, int]:
    """Celery task entry-point for listing recalculation."""
    normalized_ids = _normalize_listing_ids(listing_ids)
    logger.info(
        "Starting valuation recalculation",
        extra={
            "requested_ids": len(normalized_ids) or "all",
            "ruleset_id": ruleset_id,
            "batch_size": batch_size,
            "reason": reason,
        },
    )
    return asyncio.run(
        _recalculate_listings_async(
            listing_ids=normalized_ids or None,
            ruleset_id=ruleset_id,
            batch_size=batch_size,
            include_inactive=include_inactive,
        )
    )


def enqueue_listing_recalculation(
    *,
    listing_ids: Iterable[int | str | None] | None = None,
    ruleset_id: int | None = None,
    reason: str | None = None,
    use_celery: bool = True,
) -> None:
    """Schedule listing valuation recalculation.

    Falls back to synchronous execution in environments where Celery workers
    are unavailable (e.g., unit tests).
    """
    payload = {
        "listing_ids": list(listing_ids) if listing_ids else None,
        "ruleset_id": ruleset_id,
        "reason": reason,
    }

    try:
        if use_celery:
            recalculate_listings_task.delay(**payload)
            logger.debug("Queued valuation recalculation", extra=payload)
            return
    except Exception as exc:  # pragma: no cover - fallback path
        logger.warning("Falling back to synchronous recalculation: %s", exc, exc_info=exc)

    # Synchronous fallback (mostly used in tests/dev)
    recalculate_listings_task(**payload)
