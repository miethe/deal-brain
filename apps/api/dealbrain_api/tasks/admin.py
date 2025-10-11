"""Celery tasks for administrative maintenance actions."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable

from ..db import session_scope
from ..importers.universal import ImporterError, load_seed_from_file
from ..seeds import apply_seed
from ..services import admin_tasks as admin_services
from ..services.listings import bulk_update_listing_metrics
from ..services.passmark import PassmarkImportSummary, import_passmark_file
from ..worker import celery_app


async def _bulk_metrics_async(listing_ids: Iterable[int] | None) -> dict[str, int]:
    async with session_scope() as session:
        ids = list(listing_ids) if listing_ids else None
        count = await bulk_update_listing_metrics(session, ids)
        return {"updated": count}


@celery_app.task(name="admin.recalculate_metrics")
def recalculate_metrics_task(listing_ids: list[int] | None = None) -> dict[str, int]:
    return asyncio.run(_bulk_metrics_async(listing_ids))


async def _cpu_mark_async(listing_ids: Iterable[int] | None) -> dict[str, int]:
    async with session_scope() as session:
        ids = list(listing_ids) if listing_ids else None
        summary = await admin_services.recalculate_cpu_mark_metrics(session, ids)
        return summary.to_dict()


@celery_app.task(name="admin.recalculate_cpu_mark_metrics")
def recalculate_cpu_mark_metrics_task(listing_ids: list[int] | None = None) -> dict[str, int]:
    return asyncio.run(_cpu_mark_async(listing_ids))


async def _import_passmark_async(file_path: Path) -> dict[str, object]:
    summary: PassmarkImportSummary = await import_passmark_file(file_path)
    return summary.to_dict()


@celery_app.task(name="admin.import_passmark")
def import_passmark_task(file_path: str) -> dict[str, object]:
    path = Path(file_path)
    try:
        return asyncio.run(_import_passmark_async(path))
    finally:
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
    path = Path(file_path)
    try:
        return asyncio.run(_import_entities_async(entity, path, dry_run))
    finally:
        path.unlink(missing_ok=True)
