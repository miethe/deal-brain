"""CPU and component matching utilities for import sessions."""

from __future__ import annotations

from typing import Any, Mapping

from pandas import DataFrame
from rapidfuzz import fuzz, process
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.core import Cpu, Gpu, ImportSession
from .utils import normalize_text


class CpuMatcher:
    """Handles CPU/GPU lookup, fuzzy matching, and auto-creation."""

    @staticmethod
    async def load_cpu_lookup(db: AsyncSession) -> dict[str, int]:
        """
        Load all CPUs into a normalized name -> ID lookup.

        Args:
            db: Database session

        Returns:
            Dictionary mapping normalized CPU names to CPU IDs
        """
        result = await db.execute(select(Cpu.id, Cpu.name))
        lookup: dict[str, int] = {}
        for cpu_id, name in result.all():
            if not name:
                continue
            lookup[normalize_text(str(name))] = cpu_id
        return lookup

    @staticmethod
    async def load_gpu_lookup(db: AsyncSession) -> dict[str, int]:
        """
        Load all GPUs into a normalized name -> ID lookup.

        Args:
            db: Database session

        Returns:
            Dictionary mapping normalized GPU names to GPU IDs
        """
        result = await db.execute(select(Gpu.id, Gpu.name))
        lookup: dict[str, int] = {}
        for gpu_id, name in result.all():
            if not name:
                continue
            lookup[normalize_text(str(name))] = gpu_id
        return lookup

    @staticmethod
    async def load_cpu_names(db: AsyncSession) -> list[str]:
        """
        Load all CPU names for fuzzy matching.

        Args:
            db: Database session

        Returns:
            List of CPU names
        """
        result = await db.execute(select(Cpu.name))
        return [row[0] for row in result.all() if row[0]]

    @staticmethod
    def match_components(
        dataframe: DataFrame,
        column: str,
        cpu_names: list[str],
        *,
        limit: int | None = 100,
    ) -> list[dict[str, Any]]:
        """
        Match component names from a DataFrame column to known CPU names.

        Args:
            dataframe: Source DataFrame
            column: Column name containing component names
            cpu_names: List of known CPU names for matching
            limit: Maximum number of rows to process (None for all)

        Returns:
            List of match results with suggestions and confidence scores
        """
        if column not in dataframe.columns:
            return []

        values = dataframe[column].fillna("").astype(str).tolist()
        matches: list[dict[str, Any]] = []
        iterable = values if limit is None else values[:limit]

        for idx, value in enumerate(iterable):
            normalized = value.strip()
            if not normalized:
                matches.append(
                    {
                        "row_index": idx,
                        "value": value,
                        "status": "unmatched",
                        "suggestions": [],
                    }
                )
                continue

            suggestions = process.extract(normalized, cpu_names, scorer=fuzz.WRatio, limit=3)
            structured = [
                {"match": suggestion[0], "confidence": round(suggestion[1] / 100, 4)}
                for suggestion in suggestions
            ]
            top_confidence = structured[0]["confidence"] if structured else 0.0
            status = "unmatched"
            auto = None

            if top_confidence >= 0.9:
                status = "auto"
                auto = structured[0]["match"]
            elif top_confidence >= 0.75:
                status = "review"

            matches.append(
                {
                    "row_index": idx,
                    "value": value,
                    "status": status,
                    "auto_match": auto,
                    "suggestions": structured,
                }
            )
        return matches

    @staticmethod
    def collect_missing_cpus(
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
        *,
        component_overrides: Mapping[int, dict[str, Any]],
        cpu_lookup: Mapping[str, int],
    ) -> list[dict[str, Any]]:
        """
        Identify CPUs that need to be auto-created.

        Args:
            dataframe: Source DataFrame
            field_mappings: Field mapping configuration
            component_overrides: User overrides for component assignments
            cpu_lookup: Existing CPU name -> ID lookup

        Returns:
            List of missing CPU entries to create
        """
        cpu_column = field_mappings.get("cpu_name", {}).get("column")
        if not cpu_column or cpu_column not in dataframe.columns:
            return []

        matches = CpuMatcher.match_components(dataframe, cpu_column, list(cpu_lookup.keys()), limit=None)
        match_lookup = {match["row_index"]: match for match in matches}
        normalized_lookup = set(cpu_lookup.keys())

        missing: dict[str, dict[str, Any]] = {}
        records = dataframe.fillna("").to_dict(orient="records")

        for index, row in enumerate(records):
            override = component_overrides.get(index)
            match_data = match_lookup.get(index)
            candidate = None

            if override and override.get("cpu_match"):
                candidate = str(override.get("cpu_match")).strip() or None
            elif match_data and match_data.get("status") == "auto":
                candidate = str(match_data.get("auto_match")).strip() or None
            else:
                candidate = str(row.get(cpu_column, "")).strip() or None

            if not candidate:
                continue

            normalized = normalize_text(candidate)
            if not normalized or normalized in normalized_lookup or normalized in missing:
                continue

            missing[normalized] = {
                "name": candidate,
                "row_index": index,
                "manufacturer": CpuMatcher._guess_cpu_manufacturer(candidate),
            }

        return list(missing.values())

    @staticmethod
    def _guess_cpu_manufacturer(cpu_name: str) -> str:
        """
        Guess the CPU manufacturer from the CPU name.

        Args:
            cpu_name: CPU name string

        Returns:
            Manufacturer name (Intel, AMD, Apple, etc.)
        """
        if not cpu_name:
            return "Unknown"
        tokens = cpu_name.strip().split()
        if not tokens:
            return "Unknown"

        first = tokens[0].lower()
        mapping = {
            "intel": "Intel",
            "amd": "AMD",
            "apple": "Apple",
            "ibm": "IBM",
            "qualcomm": "Qualcomm",
        }

        if first in mapping:
            return mapping[first]
        if "intel" in first:
            return "Intel"
        if "ryzen" in first or "epyc" in first:
            return "AMD"
        if "m" in first and tokens[0].lower().startswith("m") and "apple" in cpu_name.lower():
            return "Apple"

        return "Unknown"

    @staticmethod
    async def auto_create_cpus(
        db: AsyncSession,
        *,
        entries: list[dict[str, Any]],
        import_session: ImportSession,
    ) -> list[Cpu]:
        """
        Auto-create CPU records for missing components.

        Args:
            db: Database session
            entries: List of missing CPU entries to create
            import_session: Import session for audit trail

        Returns:
            List of created CPU records
        """
        created: list[Cpu] = []
        for entry in entries:
            name = entry.get("name")
            if not name:
                continue

            existing = await db.scalar(select(Cpu).where(Cpu.name.ilike(name)))
            if existing:
                continue

            cpu = Cpu(
                name=name,
                manufacturer=entry.get("manufacturer") or "Unknown",
                attributes_json={
                    "auto_created_from_import": str(import_session.id),
                    "source_row_index": entry.get("row_index"),
                },
            )
            db.add(cpu)
            await db.flush()
            await db.refresh(cpu)
            created.append(cpu)

        if created:
            await db.commit()

        return created

    @staticmethod
    def resolve_cpu_assignment(
        override: Mapping[str, Any] | None,
        match_data: Mapping[str, Any] | None,
    ) -> str | None:
        """
        Resolve the final CPU assignment for a listing.

        Args:
            override: User override data
            match_data: Automatic match data

        Returns:
            Final CPU name assignment or None
        """
        if override and override.get("cpu_match"):
            value = override.get("cpu_match")
            return str(value).strip() or None
        if match_data and match_data.get("status") == "auto":
            value = match_data.get("auto_match")
            return str(value).strip() or None
        return None


__all__ = ["CpuMatcher"]
