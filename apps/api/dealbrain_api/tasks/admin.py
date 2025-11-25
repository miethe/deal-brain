"""Celery tasks for administrative maintenance actions."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable

from ..db import dispose_engine, session_scope
from ..importers.universal import ImporterError, load_seed_from_file
from ..seeds import apply_seed
from ..services import admin_tasks as admin_services
from ..services.listings import bulk_update_listing_metrics
from ..services.passmark import PassmarkImportSummary, import_passmark_file
from ..telemetry import get_logger
from ..worker import celery_app

logger = get_logger("dealbrain.tasks.admin")


async def _bulk_metrics_async(listing_ids: Iterable[int] | None) -> dict[str, int]:
    async with session_scope() as session:
        ids = list(listing_ids) if listing_ids else None
        count = await bulk_update_listing_metrics(session, ids)
        return {"updated": count}


@celery_app.task(name="admin.recalculate_metrics")
def recalculate_metrics_task(listing_ids: list[int] | None = None) -> dict[str, int]:
    """Celery task to recalculate listing metrics."""
    logger.info("admin.recalculate_metrics.start", listing_count=len(listing_ids or []))

    # Create fresh event loop for each task execution
    # This prevents "attached to a different loop" errors in forked worker processes
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)

        # Dispose existing engine if present to prevent "attached to a different loop" errors
        # The engine will be recreated with the new event loop on first use
        loop.run_until_complete(dispose_engine())

        result = loop.run_until_complete(_bulk_metrics_async(listing_ids))
        logger.info("admin.recalculate_metrics.complete", **result)
        return result
    finally:
        # Clean up loop after task completion
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
            asyncio.set_event_loop(None)


async def _cpu_mark_async(listing_ids: Iterable[int] | None) -> dict[str, int]:
    async with session_scope() as session:
        ids = list(listing_ids) if listing_ids else None
        summary = await admin_services.recalculate_cpu_mark_metrics(session, ids)
        return summary.to_dict()


@celery_app.task(name="admin.recalculate_cpu_mark_metrics")
def recalculate_cpu_mark_metrics_task(listing_ids: list[int] | None = None) -> dict[str, int]:
    """Celery task to recalculate CPU Mark metrics."""
    logger.info("admin.recalculate_cpu_mark_metrics.start", listing_count=len(listing_ids or []))

    # Create fresh event loop for each task execution
    # This prevents "attached to a different loop" errors in forked worker processes
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)

        # Dispose existing engine if present to prevent "attached to a different loop" errors
        # The engine will be recreated with the new event loop on first use
        loop.run_until_complete(dispose_engine())

        result = loop.run_until_complete(_cpu_mark_async(listing_ids))
        logger.info("admin.recalculate_cpu_mark_metrics.complete", **result)
        return result
    finally:
        # Clean up loop after task completion
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
            asyncio.set_event_loop(None)


async def _import_passmark_async(file_path: Path) -> dict[str, object]:
    summary: PassmarkImportSummary = await import_passmark_file(file_path)
    return summary.to_dict()


@celery_app.task(name="admin.import_passmark")
def import_passmark_task(file_path: str) -> dict[str, object]:
    """Celery task to import PassMark benchmark data."""
    path = Path(file_path)
    logger.info("admin.import_passmark.start", file_path=str(path))

    # Create fresh event loop for each task execution
    # This prevents "attached to a different loop" errors in forked worker processes
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)

        # Dispose existing engine if present to prevent "attached to a different loop" errors
        # The engine will be recreated with the new event loop on first use
        loop.run_until_complete(dispose_engine())

        result = loop.run_until_complete(_import_passmark_async(path))
        logger.info("admin.import_passmark.complete", **result)
        return result
    finally:
        # Clean up loop after task completion
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
            asyncio.set_event_loop(None)
            path.unlink(missing_ok=True)


async def _import_entities_async(entity: str, file_path: Path, dry_run: bool) -> dict[str, object]:
    try:
        seed, count = load_seed_from_file(file_path, entity)
    except ImporterError as exc:
        return {"status": "FAILURE", "error": str(exc)}

    if dry_run:
        return {"status": "dry_run", "records": count}

    await apply_seed(seed)
    return {"status": "imported", "records": count}


@celery_app.task(name="admin.import_entities")
def import_entities_task(entity: str, file_path: str, dry_run: bool = False) -> dict[str, object]:
    """Celery task to import entities from file."""
    path = Path(file_path)
    logger.info("admin.import_entities.start", entity=entity, file_path=str(path), dry_run=dry_run)

    # Create fresh event loop for each task execution
    # This prevents "attached to a different loop" errors in forked worker processes
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)

        # Dispose existing engine if present to prevent "attached to a different loop" errors
        # The engine will be recreated with the new event loop on first use
        loop.run_until_complete(dispose_engine())

        result = loop.run_until_complete(_import_entities_async(entity, path, dry_run))
        logger.info("admin.import_entities.complete", entity=entity, **result)
        return result
    finally:
        # Clean up loop after task completion
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
            asyncio.set_event_loop(None)
            path.unlink(missing_ok=True)
