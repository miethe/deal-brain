#!/usr/bin/env python3
"""Import PassMark benchmark data from CSV or JSON into CPU catalog.

Usage:
    poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv
    poetry run python scripts/import_passmark_data.py data/passmark_cpus.json

Supported inputs:
  • CSV Format:
    cpu_name,cpu_mark_single,cpu_mark_multi,igpu_model,igpu_mark,tdp_w,release_year

Example:
    "Intel Core i7-12700K",3985,35864,"Intel UHD 770",1850,125,2021
    "AMD Ryzen 7 5800X",3605,30862,"",0,105,2020
  • JSON Format (array of objects):
    {
      "id": "4749",
      "name": "AMD Ryzen 7 6800H",
      "thread": "3,206",
      "cpumark": "22,984",
      "cat": "Laptop",
      ...
    }
"""

import asyncio
import csv
import html
import json
import re
import sys
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add apps/api to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from dealbrain_api.models.core import Cpu
from dealbrain_api.settings import get_settings


NUMERIC_NA = {"", "na", "n/a", "null", "none"}


def parse_int(value: str | int | float | None) -> int | None:
    """Convert known PassMark numeric strings (e.g. '22,984', 'NA') to int."""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    lowered = text.lower()
    if lowered in NUMERIC_NA:
        return None
    cleaned = text.replace(",", "")
    try:
        return int(float(cleaned))
    except (TypeError, ValueError):
        return None


def parse_string(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def extract_release_year(raw_date: str | None) -> int | None:
    if not raw_date:
        return None
    match = re.search(r"(20\d{2}|19\d{2})", raw_date)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def infer_manufacturer(name: str | None) -> str | None:
    if not name:
        return None
    lowered = name.lower()
    for prefix, manufacturer in (
        ("intel", "Intel"),
        ("amd", "AMD"),
        ("apple", "Apple"),
        ("qualcomm", "Qualcomm"),
        ("arm", "ARM"),
        ("mediatek", "MediaTek"),
    ):
        if lowered.startswith(prefix):
            return manufacturer
    return None


def build_passmark_url(href: str | None) -> tuple[str | None, str | None]:
    """Return (slug, url) tuple derived from PassMark href field."""
    if not href:
        return None, None
    decoded = html.unescape(href.strip())
    if decoded.startswith("http://") or decoded.startswith("https://"):
        # Already a full URL
        return None, decoded

    slug = decoded
    if slug.startswith("cpu="):
        slug = slug[len("cpu="):]
    base_url = "https://www.cpubenchmark.net/cpu.php"
    if decoded.startswith("cpu="):
        url = f"{base_url}?{decoded}"
    else:
        url = f"{base_url}?cpu={decoded}"
    return slug, url


def update_cpu_from_passmark(cpu: Cpu, data: dict[str, object]) -> None:
    """Mutate Cpu instance using PassMark data entry."""
    # Numeric fields
    cpu_mark_multi = parse_int(
        data.get("rating")
        or data.get("cpumark")
        or data.get("cpu_mark_multi")
        or data.get("cpuMark")
    )
    cpu_mark_single = parse_int(
        data.get("thread")
        or data.get("singleThread")
        or data.get("cpu_mark_single")
        or data.get("singleThreadScore")
    )
    igpu_mark = parse_int(data.get("igpu_mark") or data.get("igpuMark") or data.get("gpuMark"))
    tdp_w = parse_int(data.get("tdp") or data.get("tdp_w") or data.get("maxTDP"))
    release_year = parse_int(data.get("release_year") or data.get("releaseYear"))
    if release_year is None:
        release_year = extract_release_year(parse_string(data.get("date")))
    cores = parse_int(data.get("cores") or data.get("coreCount") or data.get("numCores"))
    threads = parse_int(data.get("threads") or data.get("threadCount") or data.get("numThreads"))
    if threads is None:
        logicals = parse_int(data.get("logicals") or data.get("logicalCount"))
        secondary_logicals = parse_int(data.get("secondaryLogicals"))
        cpu_count = parse_int(data.get("cpuCount")) or 1
        primary_total = None
        if cores and logicals:
            primary_total = cores * logicals * cpu_count
        elif logicals:
            primary_total = logicals * cpu_count
        secondary_total = 0
        secondary_cores = parse_int(data.get("secondaryCores"))
        if secondary_logicals and secondary_cores:
            secondary_total = secondary_logicals * secondary_cores * cpu_count
        threads = primary_total or None
        if threads is not None and secondary_total:
            threads += secondary_total

    manufacturer = parse_string(data.get("manufacturer") or data.get("brand"))
    if manufacturer is None:
        manufacturer = infer_manufacturer(cpu.name)

    socket = parse_string(data.get("socket") or data.get("socketType"))
    igpu_model = parse_string(data.get("igpu_model") or data.get("igpuModel") or data.get("gpuModel"))
    notes = parse_string(data.get("notes") or data.get("comment"))

    if cpu_mark_single is not None:
        cpu.cpu_mark_single = cpu_mark_single
    if cpu_mark_multi is not None:
        cpu.cpu_mark_multi = cpu_mark_multi
    if igpu_mark is not None:
        cpu.igpu_mark = igpu_mark
    if tdp_w is not None:
        cpu.tdp_w = tdp_w
    if release_year is not None:
        cpu.release_year = release_year
    if cores is not None:
        cpu.cores = cores
    if threads is not None:
        cpu.threads = threads
    if socket is not None:
        cpu.socket = socket
    if igpu_model is not None:
        cpu.igpu_model = igpu_model
    if notes:
        cpu.notes = notes
    if manufacturer and manufacturer != cpu.manufacturer:
        cpu.manufacturer = manufacturer

    # Attributes
    attributes = dict(cpu.attributes_json or {})
    slug, url = build_passmark_url(parse_string(data.get("href") or data.get("url")))
    passmark_id = parse_string(data.get("id") or data.get("passmark_id"))
    category = parse_string(data.get("cat") or data.get("category"))
    samples = parse_int(data.get("samples"))
    rank = parse_int(data.get("rank"))
    value = parse_string(data.get("value"))
    thread_value = parse_string(data.get("threadValue"))
    power_perf = parse_string(data.get("powerPerf"))
    speed = parse_string(data.get("speed") or data.get("baseClock"))
    turbo = parse_string(data.get("turbo") or data.get("boostClock"))

    if slug:
        cpu.passmark_slug = slug
    if category:
        cpu.passmark_category = category
    if passmark_id:
        cpu.passmark_id = passmark_id

    if url:
        attributes["passmark_url"] = url
    if samples is not None:
        attributes["passmark_samples"] = samples
    if rank is not None:
        attributes["passmark_rank"] = rank
    if value:
        attributes["passmark_value"] = value
    if thread_value:
        attributes["passmark_thread_value"] = thread_value
    if power_perf:
        attributes["passmark_power_perf"] = power_perf
    if speed:
        attributes["passmark_base_clock"] = speed
    if turbo:
        attributes["passmark_turbo_clock"] = turbo

    cpu.attributes_json = attributes


async def import_passmark_csv(csv_path: str):
    """Import PassMark data from CSV file.

    Args:
        csv_path: Path to CSV file with PassMark benchmark data

    Returns:
        Tuple of (updated_count, created_count, not_found_count)
    """
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    updated_count = 0
    not_found = []
    created_count = 0

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
                        row_data = dict(row)
                        row_data["name"] = cpu_name
                        update_cpu_from_passmark(cpu, row_data)

                        updated_count += 1
                        if updated_count % 10 == 0:
                            print(f"Updated {updated_count} CPUs...")
                    except Exception as e:
                        print(f"Line {row_num}: Error parsing data for '{cpu_name}': {e}")
                else:
                    try:
                        row_data = dict(row)
                        row_data["name"] = cpu_name
                        manufacturer = infer_manufacturer(cpu_name) or "Unknown"
                        cpu = Cpu(name=cpu_name, manufacturer=manufacturer)
                        update_cpu_from_passmark(cpu, row_data)
                        session.add(cpu)
                        created_count += 1
                        print(f"Line {row_num}: Created new CPU '{cpu_name}'")
                    except Exception as e:
                        not_found.append(cpu_name)
                        print(f"Line {row_num}: Could not create CPU '{cpu_name}': {e}")

        await session.commit()

    print(f"\n=== Import Complete ===")
    print(f"Updated {updated_count} CPUs with PassMark data")
    print(f"Created {created_count} CPUs")
    print(f"Not found: {len(not_found)} CPUs")

    if not_found:
        print(f"\nCPUs not found in database ({len(not_found)} total):")
        for cpu_name in not_found[:20]:  # Show first 20
            print(f"  - {cpu_name}")
        if len(not_found) > 20:
            print(f"  ... and {len(not_found) - 20} more")

    await engine.dispose()

    return updated_count, created_count, len(not_found)


async def import_passmark_json(json_path: str):
    """Import PassMark data from JSON file of CPU objects."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    updated_count = 0
    not_found: list[str] = []
    created_count = 0

    async with async_session() as session:
        with open(json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        if isinstance(payload, dict):
            # Some exports wrap CPUs under a key like "items" or "cpus"
            if "cpus" in payload and isinstance(payload["cpus"], list):
                entries = payload["cpus"]
            elif "items" in payload and isinstance(payload["items"], list):
                entries = payload["items"]
            elif "data" in payload and isinstance(payload["data"], list):
                entries = payload["data"]
            else:
                entries = list(payload.values())
        else:
            entries = payload

        if not isinstance(entries, list):
            print(f"Unsupported JSON structure in {json_path}. Expected list of CPU objects.")
            return 0, 0

        for index, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                print(f"Item {index}: Skipping non-object entry")
                continue
            cpu_name = parse_string(
                entry.get("name")
                or entry.get("cpu_name")
                or entry.get("CPU Name")
                or entry.get("model")
            )
            if not cpu_name:
                print(f"Item {index}: Skipping entry without CPU name")
                continue

            stmt = select(Cpu).where(func.lower(Cpu.name) == func.lower(cpu_name))
            result = await session.execute(stmt)
            cpu = result.scalar_one_or_none()

            if cpu:
                try:
                    update_cpu_from_passmark(cpu, entry)
                    updated_count += 1
                    if updated_count % 10 == 0:
                        print(f"Updated {updated_count} CPUs...")
                except Exception as exc:  # Log and continue
                    print(f"Item {index}: Error updating '{cpu_name}': {exc}")
            else:
                try:
                    manufacturer = parse_string(entry.get("manufacturer")) or infer_manufacturer(cpu_name) or "Unknown"
                    cpu = Cpu(name=cpu_name, manufacturer=manufacturer)
                    update_cpu_from_passmark(cpu, entry)
                    session.add(cpu)
                    created_count += 1
                    print(f"Item {index}: Created new CPU '{cpu_name}'")
                except Exception as exc:
                    not_found.append(cpu_name)
                    print(f"Item {index}: Could not create CPU '{cpu_name}': {exc}")

        await session.commit()

    print(f"\n=== Import Complete ===")
    print(f"Updated {updated_count} CPUs with PassMark data")
    print(f"Created {created_count} CPUs")
    print(f"Not found: {len(not_found)} CPUs")

    if not_found:
        print(f"\nCPUs not found in database ({len(not_found)} total):")
        for cpu_name in not_found[:20]:
            print(f"  - {cpu_name}")
        if len(not_found) > 20:
            print(f"  ... and {len(not_found) - 20} more")

    await engine.dispose()

    return updated_count, created_count, len(not_found)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_passmark_data.py <csv_or_json_file>")
        print("\nCSV Format:")
        print("  cpu_name,cpu_mark_single,cpu_mark_multi,igpu_model,igpu_mark,tdp_w,release_year")
        print("\nJSON: Expected an array (or object with 'cpus') of PassMark CPU entries.")
        sys.exit(1)

    input_file = sys.argv[1]
    if not Path(input_file).exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    print(f"Importing PassMark data from: {input_file}\n")
    if input_file.lower().endswith(".json"):
        asyncio.run(import_passmark_json(input_file))
    else:
        asyncio.run(import_passmark_csv(input_file))
