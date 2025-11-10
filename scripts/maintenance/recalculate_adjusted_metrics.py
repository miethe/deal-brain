#!/usr/bin/env python3
"""Recalculate adjusted CPU performance metrics for all listings.

This script updates all listings with CPU assignments to use the new
delta-based adjusted metrics formula:

    adjusted_base_price = base_price + total_adjustment
    metric_adjusted = adjusted_base_price / cpu_mark

Where total_adjustment comes from valuation_breakdown['total_adjustment'].

Usage:
    poetry run python scripts/recalculate_adjusted_metrics.py

    # Dry run (show what would be updated without committing)
    poetry run python scripts/recalculate_adjusted_metrics.py --dry-run

    # Process only specific listing IDs
    poetry run python scripts/recalculate_adjusted_metrics.py --ids 1,2,3

    # Custom batch size
    poetry run python scripts/recalculate_adjusted_metrics.py --batch-size 50
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add packages to Python path
PROJECT_ROOT = Path(__file__).parent.parent
PACKAGES_ROOT = PROJECT_ROOT / "packages" / "core"
API_ROOT = PROJECT_ROOT / "apps" / "api"

if str(PACKAGES_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGES_ROOT))
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, joinedload

from dealbrain_api.models.core import Listing
from dealbrain_api.services.listings import update_listing_metrics
from dealbrain_api.settings import get_settings


async def recalculate_all_metrics(
    dry_run: bool = False,
    listing_ids: list[int] | None = None,
    batch_size: int = 100,
) -> dict[str, int]:
    """Recalculate adjusted metrics for all listings with CPUs.

    Args:
        dry_run: If True, show what would be updated without committing
        listing_ids: If provided, only process these specific listing IDs
        batch_size: Number of listings to process before committing (default 100)

    Returns:
        dict with counts: total, updated, skipped, failed
    """
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        # Query listings with CPU
        query = select(Listing).where(Listing.cpu_id.isnot(None)).options(joinedload(Listing.cpu))

        if listing_ids:
            query = query.where(Listing.id.in_(listing_ids))

        result = await session.execute(query)
        listings = result.scalars().unique().all()

        total = len(listings)
        updated = 0
        skipped = 0
        failed = 0

        print(f"{'DRY RUN: ' if dry_run else ''}Found {total} listings with CPU assignments")
        print(f"Batch size: {batch_size} (commit every {batch_size} listings)")
        print("-" * 80)

        for i, listing in enumerate(listings, 1):
            try:
                # Skip if no valuation_breakdown (can't calculate delta)
                if not listing.valuation_breakdown:
                    skipped += 1
                    if i % batch_size == 0 or i == total:
                        print(f"  [{i}/{total}] Listing {listing.id}: Skipped (no valuation_breakdown)")
                    continue

                # Recalculate metrics
                if not dry_run:
                    await update_listing_metrics(session, listing.id)
                updated += 1

                # Progress logging
                if i % batch_size == 0 or i == total:
                    print(f"  [{i}/{total}] Progress - Updated: {updated}, Skipped: {skipped}, Failed: {failed}")

                # Commit in batches
                if not dry_run and i % batch_size == 0:
                    await session.commit()
                    print(f"  ✓ Committed batch (listings 1-{i})")

            except Exception as e:
                failed += 1
                print(f"  ✗ Error updating listing {listing.id}: {e}")
                # Don't rollback, just skip this listing and continue
                continue

        # Final commit for remaining listings
        if not dry_run and (total % batch_size != 0) and updated > 0:
            await session.commit()
            print(f"  ✓ Committed final batch")

        print("-" * 80)
        print(f"{'DRY RUN: ' if dry_run else ''}Recalculation complete!")
        print(f"  Total listings: {total}")
        print(f"  Updated: {updated}")
        print(f"  Skipped: {skipped} (no valuation_breakdown)")
        print(f"  Failed: {failed}")

    await engine.dispose()

    return {
        "total": total,
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
    }


def main():
    """Parse CLI arguments and run recalculation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Recalculate adjusted CPU performance metrics for all listings",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without committing changes",
    )
    parser.add_argument(
        "--ids",
        type=str,
        help="Comma-separated list of listing IDs to process (default: all)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of listings to process before committing (default: 100)",
    )

    args = parser.parse_args()

    # Parse listing IDs if provided
    listing_ids = None
    if args.ids:
        try:
            listing_ids = [int(id.strip()) for id in args.ids.split(",")]
            print(f"Processing specific listing IDs: {listing_ids}")
        except ValueError:
            print("Error: --ids must be comma-separated integers")
            sys.exit(1)

    # Run recalculation
    result = asyncio.run(
        recalculate_all_metrics(
            dry_run=args.dry_run,
            listing_ids=listing_ids,
            batch_size=args.batch_size,
        ),
    )

    # Exit code based on failures
    sys.exit(0 if result["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
