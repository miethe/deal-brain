#!/usr/bin/env python3
"""Import PassMark benchmark data from CSV into CPU catalog.

Usage:
    poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv

CSV Format:
    cpu_name,cpu_mark_single,cpu_mark_multi,igpu_model,igpu_mark,tdp_w,release_year

Example:
    "Intel Core i7-12700K",3985,35864,"Intel UHD 770",1850,125,2021
    "AMD Ryzen 7 5800X",3605,30862,"",0,105,2020
"""

import asyncio
import csv
import sys
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add apps/api to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from dealbrain_api.models.core import Cpu
from dealbrain_api.settings import get_settings


async def import_passmark_csv(csv_path: str):
    """Import PassMark data from CSV file.

    Args:
        csv_path: Path to CSV file with PassMark benchmark data

    Returns:
        Tuple of (updated_count, not_found_count)
    """
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    updated_count = 0
    not_found = []

    async with async_session() as session:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                cpu_name = row['cpu_name'].strip()

                if not cpu_name:
                    print(f"Line {row_num}: Skipping empty CPU name")
                    continue

                # Find CPU by name (case-insensitive)
                stmt = select(Cpu).where(func.lower(Cpu.name) == func.lower(cpu_name))
                result = await session.execute(stmt)
                cpu = result.scalar_one_or_none()

                if cpu:
                    # Update CPU with PassMark data
                    try:
                        if row.get('cpu_mark_single'):
                            cpu.cpu_mark_single = int(row['cpu_mark_single'])
                        if row.get('cpu_mark_multi'):
                            cpu.cpu_mark_multi = int(row['cpu_mark_multi'])
                        if row.get('igpu_model') and row['igpu_model'].strip():
                            cpu.igpu_model = row['igpu_model'].strip()
                        if row.get('igpu_mark') and int(row['igpu_mark']) > 0:
                            cpu.igpu_mark = int(row['igpu_mark'])
                        if row.get('tdp_w'):
                            cpu.tdp_w = int(row['tdp_w'])
                        if row.get('release_year'):
                            cpu.release_year = int(row['release_year'])

                        updated_count += 1
                        if updated_count % 10 == 0:
                            print(f"Updated {updated_count} CPUs...")
                    except (ValueError, KeyError) as e:
                        print(f"Line {row_num}: Error parsing data for '{cpu_name}': {e}")
                else:
                    not_found.append(cpu_name)
                    print(f"Line {row_num}: CPU not found in database: {cpu_name}")

        await session.commit()

    print(f"\n=== Import Complete ===")
    print(f"Updated {updated_count} CPUs with PassMark data")
    print(f"Not found: {len(not_found)} CPUs")

    if not_found:
        print(f"\nCPUs not found in database ({len(not_found)} total):")
        for cpu_name in not_found[:20]:  # Show first 20
            print(f"  - {cpu_name}")
        if len(not_found) > 20:
            print(f"  ... and {len(not_found) - 20} more")

    await engine.dispose()

    return updated_count, len(not_found)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_passmark_data.py <csv_file>")
        print("\nCSV Format:")
        print("  cpu_name,cpu_mark_single,cpu_mark_multi,igpu_model,igpu_mark,tdp_w,release_year")
        print("\nExample:")
        print('  "Intel Core i7-12700K",3985,35864,"Intel UHD 770",1850,125,2021')
        sys.exit(1)

    csv_file = sys.argv[1]
    if not Path(csv_file).exists():
        print(f"Error: File not found: {csv_file}")
        sys.exit(1)

    print(f"Importing PassMark data from: {csv_file}\n")
    asyncio.run(import_passmark_csv(csv_file))
