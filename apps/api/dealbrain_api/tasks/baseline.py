"""Celery tasks for managing baseline valuation artifacts."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from ..db import session_scope
from ..worker import celery_app

if TYPE_CHECKING:
    from ..services.baseline_loader import BaselineLoaderService


async def _load_baseline_async(
    source: Path,
    *,
    actor: str | None = "system",
    ensure_basic_for_ruleset: int | None = None,
) -> dict[str, object]:
    # Import here to avoid circular dependency
    from ..services.baseline_loader import BaselineLoaderService

    async with session_scope() as session:
        service = BaselineLoaderService()
        result = await service.load_from_path(
            session,
            source,
            actor=actor,
            ensure_basic_for_ruleset=ensure_basic_for_ruleset,
        )
        return result.to_dict()


@celery_app.task(name="baseline.load_ruleset")
def load_baseline_task(
    source_path: str,
    actor: str | None = "system",
    ensure_basic_for_ruleset: int | None = None,
) -> dict[str, object]:
    """Ingest a baseline JSON artifact into the system."""
    path = Path(source_path)
    try:
        return asyncio.run(
            _load_baseline_async(
                path,
                actor=actor,
                ensure_basic_for_ruleset=ensure_basic_for_ruleset,
            )
        )
    finally:
        path.unlink(missing_ok=True)
