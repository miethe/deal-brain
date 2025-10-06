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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.db import async_session_scope
from dealbrain_api.models.core import Listing


async def recalculate_all_cpu_marks() -> None:
    """Recalculate CPU Mark metrics for all listings with CPUs."""
    async with async_session_scope() as session:
        # Fetch all listings with CPUs
        result = await session.execute(
            select(Listing).where(Listing.cpu_id.is_not(None))
        )
        listings = result.scalars().all()

        updated_count = 0
        skipped_count = 0

        print(f"Found {len(listings)} listings with CPUs")

        for listing in listings:
            # Eager load CPU relationship
            await session.refresh(listing, ["cpu"])

            if not listing.cpu:
                print(f"  [SKIP] Listing {listing.id}: No CPU found")
                skipped_count += 1
                continue

            if not listing.adjusted_price_usd:
                print(f"  [SKIP] Listing {listing.id}: No adjusted price")
                skipped_count += 1
                continue

            cpu = listing.cpu

            # Calculate metrics
            updated = False
            if cpu.cpu_mark_single:
                listing.dollar_per_cpu_mark_single = listing.adjusted_price_usd / cpu.cpu_mark_single
                updated = True

            if cpu.cpu_mark_multi:
                listing.dollar_per_cpu_mark_multi = listing.adjusted_price_usd / cpu.cpu_mark_multi
                updated = True

            if updated:
                print(
                    f"  [UPDATE] Listing {listing.id} ({listing.title[:50]}): "
                    f"single={listing.dollar_per_cpu_mark_single:.4f if listing.dollar_per_cpu_mark_single else 'N/A'}, "
                    f"multi={listing.dollar_per_cpu_mark_multi:.4f if listing.dollar_per_cpu_mark_multi else 'N/A'}"
                )
                updated_count += 1
            else:
                print(f"  [SKIP] Listing {listing.id}: No CPU Mark data available")
                skipped_count += 1

        await session.commit()

        print(f"\nRecalculation complete:")
        print(f"  Updated: {updated_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Total:   {len(listings)}")


if __name__ == "__main__":
    print("Starting CPU Mark metric recalculation...")
    asyncio.run(recalculate_all_cpu_marks())
    print("Done!")
