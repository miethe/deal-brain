"""PassMark import utilities shared between CLI scripts and admin tasks."""

from __future__ import annotations

import csv
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_scope
from ..models import Cpu

NUMERIC_NA = {"", "na", "n/a", "null", "none"}


@dataclass(frozen=True, slots=True)
class PassmarkImportSummary:
    updated: int
    created: int
    failed: int
    not_found: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "updated": self.updated,
            "created": self.created,
            "failed": self.failed,
            "not_found": self.not_found,
        }


def parse_int(value: str | int | float | None) -> int | None:
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
    if not href:
        return None, None
    decoded = html.unescape(href.strip())
    if decoded.startswith("http://") or decoded.startswith("https://"):
        return None, decoded

    slug = decoded
    if slug.startswith("cpu="):
        slug = slug[len("cpu=") :]
    base_url = "https://www.cpubenchmark.net/cpu.php"
    if decoded.startswith("cpu="):
        url = f"{base_url}?{decoded}"
    else:
        url = f"{base_url}?cpu={decoded}"
    return slug, url


def update_cpu_from_passmark(cpu: Cpu, data: dict[str, Any]) -> None:
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
    igpu_model = parse_string(
        data.get("igpu_model") or data.get("igpuModel") or data.get("gpuModel")
    )
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

    attributes = dict(cpu.attributes_json or {})
    slug, url = build_passmark_url(parse_string(data.get("href") or data.get("url")))
    if slug:
        attributes["passmark_slug"] = slug
    if url:
        attributes["passmark_url"] = url
    if attributes:
        cpu.attributes_json = attributes


async def import_passmark_file(path: Path) -> PassmarkImportSummary:
    suffix = path.suffix.lower()
    if suffix not in {".csv", ".json"}:
        raise ValueError("Unsupported PassMark file type; expected CSV or JSON.")

    if suffix == ".csv":
        return await _import_csv(path)
    return await _import_json(path)


async def _import_csv(path: Path) -> PassmarkImportSummary:
    updated_count = 0
    created_count = 0
    not_found: list[str] = []
    failed = 0

    async with session_scope() as session:
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row_num, row in enumerate(reader, start=2):
                cpu_name = (row.get("cpu_name") or "").strip()
                if not cpu_name:
                    failed += 1
                    continue

                cpu = await _get_cpu_by_name(session, cpu_name)

                try:
                    row_data = dict(row)
                    row_data["name"] = cpu_name
                    if cpu:
                        update_cpu_from_passmark(cpu, row_data)
                        updated_count += 1
                    else:
                        manufacturer = infer_manufacturer(cpu_name) or "Unknown"
                        cpu = Cpu(name=cpu_name, manufacturer=manufacturer)
                        update_cpu_from_passmark(cpu, row_data)
                        session.add(cpu)
                        created_count += 1
                except Exception:
                    failed += 1
                    not_found.append(cpu_name)

    return PassmarkImportSummary(
        updated=updated_count,
        created=created_count,
        failed=failed,
        not_found=not_found,
    )


async def _import_json(path: Path) -> PassmarkImportSummary:
    updated_count = 0
    created_count = 0
    not_found: list[str] = []
    failed = 0

    payload = json.loads(path.read_text())

    if isinstance(payload, dict):
        for candidate in ("cpus", "items", "data"):
            if candidate in payload and isinstance(payload[candidate], list):
                entries = payload[candidate]
                break
        else:
            entries = list(payload.values())
    else:
        entries = payload

    if not isinstance(entries, list):
        raise ValueError("Expected a list of CPU entries in PassMark JSON payload.")

    async with session_scope() as session:
        for entry in entries:
            if not isinstance(entry, dict):
                failed += 1
                continue
            cpu_name = parse_string(
                entry.get("name")
                or entry.get("cpu_name")
                or entry.get("CPU Name")
                or entry.get("model")
            )
            if not cpu_name:
                failed += 1
                continue

            cpu = await _get_cpu_by_name(session, cpu_name)
            try:
                if cpu:
                    update_cpu_from_passmark(cpu, entry)
                    updated_count += 1
                else:
                    manufacturer = (
                        parse_string(entry.get("manufacturer"))
                        or infer_manufacturer(cpu_name)
                        or "Unknown"
                    )
                    cpu = Cpu(name=cpu_name, manufacturer=manufacturer)
                    update_cpu_from_passmark(cpu, entry)
                    session.add(cpu)
                    created_count += 1
            except Exception:
                failed += 1
                not_found.append(cpu_name)

    return PassmarkImportSummary(
        updated=updated_count,
        created=created_count,
        failed=failed,
        not_found=not_found,
    )


async def _get_cpu_by_name(session: AsyncSession, name: str) -> Cpu | None:
    stmt = select(Cpu).where(func.lower(Cpu.name) == func.lower(name))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
