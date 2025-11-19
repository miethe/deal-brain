"""Validation and conflict detection for import sessions."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
from pandas import DataFrame
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.core import Cpu


class ImportValidator:
    """Handles validation and conflict detection for imports."""

    @staticmethod
    def validate_conflicts(
        conflicts: Mapping[str, Any] | None,
        resolutions: Mapping[str, str],
    ) -> None:
        """
        Validate that all conflicts have valid resolutions.

        Args:
            conflicts: Dictionary of detected conflicts
            resolutions: User-provided conflict resolutions

        Raises:
            ValueError: If conflicts are unresolved or resolutions are invalid
        """
        if not conflicts:
            return

        cpu_conflicts = conflicts.get("cpu") or []
        unresolved = [
            conflict["name"] for conflict in cpu_conflicts if conflict["name"] not in resolutions
        ]
        if unresolved:
            raise ValueError(f"Unresolved CPU conflicts: {', '.join(unresolved)}")

        invalid = [
            name for name, action in resolutions.items() if action not in {"update", "skip", "keep"}
        ]
        if invalid:
            raise ValueError(f"Invalid resolution actions for: {', '.join(invalid)}")

    @staticmethod
    async def detect_cpu_conflicts(
        db: AsyncSession,
        workbook: Mapping[str, DataFrame],
        mappings: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Detect conflicts between incoming CPUs and existing database records.

        Args:
            db: Database session
            workbook: Dictionary of sheet DataFrames
            mappings: Field mapping configuration

        Returns:
            List of conflict details with existing/incoming values
        """
        cpu_mapping = mappings.get("cpu") if mappings else None
        if not cpu_mapping:
            return []

        sheet = cpu_mapping.get("sheet")
        dataframe = workbook.get(sheet)
        if dataframe is None:
            return []

        fields = cpu_mapping.get("fields", {})
        name_column = fields.get("name", {}).get("column")
        if not name_column or name_column not in dataframe.columns:
            return []

        records = dataframe.fillna("").to_dict(orient="records")
        incoming: dict[str, dict[str, Any]] = {}

        for row in records:
            name = str(row.get(name_column, "")).strip()
            if not name:
                continue
            incoming[name] = {
                key: (
                    ImportValidator._coerce_value(row.get(mapping.get("column")))
                    if mapping.get("column")
                    else None
                )
                for key, mapping in fields.items()
            }

        if not incoming:
            return []

        existing = await db.execute(select(Cpu).where(Cpu.name.in_(incoming.keys())))
        conflicts: list[dict[str, Any]] = []

        for cpu in existing.scalars():
            desired = incoming.get(cpu.name)
            if not desired:
                continue
            diff = ImportValidator._cpu_differences(cpu, desired)
            if diff:
                conflicts.append(
                    {
                        "name": cpu.name,
                        "existing": diff["existing"],
                        "incoming": diff["incoming"],
                        "fields": diff["fields"],
                    }
                )

        return conflicts

    @staticmethod
    def _cpu_differences(cpu: Cpu, incoming: Mapping[str, Any]) -> dict[str, Any] | None:
        """
        Compare existing CPU record with incoming data.

        Args:
            cpu: Existing CPU database record
            incoming: Incoming CPU data from spreadsheet

        Returns:
            Dictionary of differences or None if no changes
        """
        tracked_fields = [
            "manufacturer",
            "socket",
            "cores",
            "threads",
            "tdp_w",
            "igpu_model",
            "cpu_mark_multi",
            "cpu_mark_single",
            "release_year",
            "notes",
        ]

        diffs: list[dict[str, Any]] = []
        for field in tracked_fields:
            new_value = ImportValidator._normalize_numeric(incoming.get(field), field)
            existing_value = getattr(cpu, field)
            if new_value in (None, "") and existing_value in (None, ""):
                continue
            if str(existing_value) != str(new_value):
                diffs.append(
                    {
                        "field": field,
                        "existing": existing_value,
                        "incoming": new_value,
                    }
                )

        if not diffs:
            return None

        return {
            "existing": {field: getattr(cpu, field) for field in tracked_fields},
            "incoming": {
                field: ImportValidator._normalize_numeric(incoming.get(field), field)
                for field in tracked_fields
            },
            "fields": diffs,
        }

    @staticmethod
    def _normalize_numeric(value: Any, field: str) -> Any:
        """
        Normalize numeric values for comparison.

        Args:
            value: Raw value from spreadsheet
            field: Field name to determine type

        Returns:
            Normalized value (int for numeric fields, raw for others)
        """
        if value in (None, ""):
            return None
        if field in {
            "cores",
            "threads",
            "tdp_w",
            "cpu_mark_multi",
            "cpu_mark_single",
            "release_year",
        }:
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return value
        return value

    @staticmethod
    def _coerce_value(value: Any) -> Any:
        """
        Coerce spreadsheet values to appropriate Python types.

        Args:
            value: Raw value from pandas DataFrame

        Returns:
            Coerced value (None for empty/NA values)
        """
        if value is None:
            return None
        if value == "":
            return None
        try:
            if pd.isna(value):
                return None
        except TypeError:
            # pd.isna() raises TypeError for unhashable types (e.g., dict, list);
            # these are valid non-NA values, so continue with normal processing.
            pass
        return value


__all__ = ["ImportValidator"]
