#!/usr/bin/env python
"""Universal seeding script that leverages the importer pipeline for Deal Brain.

This script imports entity data (CPUs, GPUs, etc.) from JSON or CSV files into the
Deal Brain database. It uses the universal importer pipeline to validate and persist
entities, supporting various hardware component types.

How it works:
    1. Parses the entity type and file path from command-line arguments
    2. Validates the file path is within the project root
    3. Loads and validates the data using the appropriate importer
    4. Creates database schema if needed
    5. Persists entities to the database (or validates only in dry-run mode)

Supported Entities:
    - cpu: CPU/Processor data
    - gpu: GPU/Graphics card data
    - (other entities as defined in SUPPORTED_ENTITIES)

File Formats:
    - JSON: Array of entity objects with appropriate fields
    - CSV: Rows with columns matching entity fields

Usage:
    # Import CPUs from JSON file
    poetry run python scripts/import_entities.py cpu scripts/templates/cpu.json

    # Import GPUs from JSON file
    poetry run python scripts/import_entities.py gpu scripts/templates/gpu.json

    # Dry run to validate without persisting
    poetry run python scripts/import_entities.py cpu data/cpus.json --dry-run

    # Import from CSV file
    poetry run python scripts/import_entities.py cpu data/cpu_catalog.csv

Examples:
    # Seed initial CPU catalog
    poetry run python scripts/import_entities.py cpu scripts/templates/cpu.json

    # Validate GPU data before importing
    poetry run python scripts/import_entities.py gpu data/new_gpus.json --dry-run

    # Import additional CPUs from external source
    poetry run python scripts/import_entities.py cpu data/passmark_cpus.csv
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any

# Ensure the project root is available on sys.path for absolute imports.
_SCRIPT_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

_PACKAGES_ROOT = _SCRIPT_ROOT / "packages"
if _PACKAGES_ROOT.exists():
    for package_dir in _PACKAGES_ROOT.iterdir():
        if package_dir.is_dir():
            candidate = str(package_dir)
            if candidate not in sys.path:
                sys.path.insert(0, candidate)

from apps.api.dealbrain_api.db import Base, get_engine
from apps.api.dealbrain_api.importers.universal import (
    SUPPORTED_ENTITIES,
    ImporterError,
    load_seed_from_file,
)
from apps.api.dealbrain_api.seeds import apply_seed
from apps.api.dealbrain_api.settings import PROJECT_ROOT as SETTINGS_PROJECT_ROOT

if SETTINGS_PROJECT_ROOT and str(SETTINGS_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(SETTINGS_PROJECT_ROOT))

PROJECT_ROOT = _SCRIPT_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import seed data for Deal Brain entities.")
    parser.add_argument(
        "entity",
        help=f"Entity to import ({', '.join(sorted(SUPPORTED_ENTITIES))})",
    )
    parser.add_argument(
        "path",
        help="Path to JSON/CSV payload relative to the project root (or absolute inside the project).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the payload without persisting changes.",
    )
    return parser.parse_args()


def _resolve_path(path_argument: str) -> Path:
    candidate = Path(path_argument)
    candidate = (
        (PROJECT_ROOT / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    )
    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ImporterError(
            f"Path '{candidate}' is outside of the project root {PROJECT_ROOT}."
        ) from exc
    return candidate


async def _ensure_schema() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def _summarize_seed(seed: Any) -> dict[str, int]:
    summary: dict[str, int] = {}
    for field in SUPPORTED_ENTITIES.values():
        items = getattr(seed, field.field_name, None)
        if items:
            summary[field.field_name] = len(items)
    return summary


async def main() -> None:
    args = parse_args()
    try:
        file_path = _resolve_path(args.path)
        seed, count = load_seed_from_file(file_path, args.entity)
    except ImporterError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    if args.dry_run:
        summary = _summarize_seed(seed)
        print("Dry run successful — no changes applied.")
        for name, total in summary.items():
            print(f"  {name}: {total}")
        return

    await _ensure_schema()
    await apply_seed(seed)
    summary = _summarize_seed(seed)
    print(f"Imported {count} {args.entity}(s) from {file_path}.")
    for name, total in summary.items():
        print(f"  {name}: {total}")


if __name__ == "__main__":
    asyncio.run(main())
