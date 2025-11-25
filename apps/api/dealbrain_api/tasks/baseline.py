"""Celery tasks for managing baseline valuation artifacts."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from ..db import dispose_engine, session_scope
from ..telemetry import get_logger
from ..worker import celery_app

logger = get_logger("dealbrain.tasks.baseline")

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
    """Celery task to ingest a baseline JSON artifact into the system."""
    path = Path(source_path)
    logger.info("baseline.load_ruleset.start", source_path=str(path), actor=actor)

    # Create fresh event loop for each task execution
    # This prevents "attached to a different loop" errors in forked worker processes
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)

        # Dispose existing engine if present to prevent "attached to a different loop" errors
        # The engine will be recreated with the new event loop on first use
        loop.run_until_complete(dispose_engine())

        result = loop.run_until_complete(
            _load_baseline_async(
                path,
                actor=actor,
                ensure_basic_for_ruleset=ensure_basic_for_ruleset,
            )
        )
        logger.info("baseline.load_ruleset.complete", **result)
        return result
    finally:
        # Clean up loop after task completion
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
            asyncio.set_event_loop(None)
            path.unlink(missing_ok=True)
