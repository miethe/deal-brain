#!/usr/bin/env python3
"""Import PassMark benchmark data from CSV or JSON into the catalog."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure apps/api is on path for service imports
API_ROOT = Path(__file__).parent.parent / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from dealbrain_api.services.passmark import import_passmark_file


async def _run(path: Path) -> None:
    summary = await import_passmark_file(path)
    result = summary.to_dict()

    print("\n=== PassMark Import Complete ===")
    print(f"Updated: {result['updated']}")
    print(f"Created: {result['created']}")
    print(f"Failed:  {result['failed']}")
    if result["not_found"]:
        print("\nEntries that could not be matched or created:")
        for name in result["not_found"][:20]:
            print(f"  - {name}")
        remaining = len(result["not_found"]) - 20
        if remaining > 0:
            print(f"  ... and {remaining} more")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: poetry run python scripts/import_passmark_data.py <csv_or_json_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1]).resolve()
    if not input_file.exists():
        print(f"Error: file not found: {input_file}")
        sys.exit(1)

    asyncio.run(_run(input_file))


if __name__ == "__main__":
    main()
