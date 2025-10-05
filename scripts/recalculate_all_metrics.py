#!/usr/bin/env python3
"""Recalculate performance metrics for all listings.

This script recalculates dollar_per_cpu_mark metrics for all listings
after PassMark data has been imported or when adjusted prices have changed.

Usage:
    poetry run python scripts/recalculate_all_metrics.py
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add apps/api to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from dealbrain_api.services.listings import bulk_update_listing_metrics
from dealbrain_api.settings import get_settings


async def recalculate_all():
    """Recalculate metrics for all listings in the database."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Starting bulk metric recalculation for all listings...\n")

        try:
            count = await bulk_update_listing_metrics(session, listing_ids=None)
            print(f"\n=== Recalculation Complete ===")
            print(f"Updated {count} listing(s)")
        except Exception as e:
            print(f"Error during recalculation: {e}")
            await session.rollback()
            raise

    await engine.dispose()


if __name__ == "__main__":
    print("Recalculate Performance Metrics")
    print("=" * 50)
    print("This will update all listing performance metrics based on:")
    print("  - Current CPU benchmark data")
    print("  - Current adjusted prices")
    print("")

    asyncio.run(recalculate_all())
