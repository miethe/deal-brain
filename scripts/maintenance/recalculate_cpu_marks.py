#!/usr/bin/env python3
"""
Bulk recalculate CPU Mark metrics for all existing listings.

This script updates dollar_per_cpu_mark_single and dollar_per_cpu_mark_multi
for all listings that have both a CPU and an adjusted price.
"""

import asyncio
import sys
from pathlib import Path

# Add apps/api to path for imports
api_path = Path(__file__).parent.parent / "apps" / "api"
sys.path.insert(0, str(api_path))

from dealbrain_api.db import session_scope
from dealbrain_api.services.admin_tasks import recalculate_cpu_mark_metrics


async def recalculate_all_cpu_marks() -> None:
    """Recalculate CPU Mark metrics for all listings with CPUs."""
    async with session_scope() as session:
        summary = await recalculate_cpu_mark_metrics(session)

    print("\nRecalculation complete:")
    print(f"  Total listings processed: {summary.total}")
    print(f"  Updated: {summary.updated}")
    print(f"  Skipped (no CPU): {summary.skipped_no_cpu}")
    print(f"  Skipped (no adjusted price): {summary.skipped_no_adjusted_price}")
    print(f"  Skipped (no metrics available): {summary.skipped_no_metrics}")


if __name__ == "__main__":
    print("Starting CPU Mark metric recalculation...")
    asyncio.run(recalculate_all_cpu_marks())
    print("Done!")
