"""Preview generation utilities for import sessions."""

from __future__ import annotations

from typing import Any, Mapping

from pandas import DataFrame
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.core import ImportSession
from .cpu_matcher import CpuMatcher
from .specs import IMPORT_SCHEMAS
from .utils import load_dataframe_preview


class PreviewBuilder:
    """Handles preview generation for import data."""

    @staticmethod
    def build_preview(
        workbook: Mapping[str, DataFrame],
        mappings: Mapping[str, Any],
        limit: int = 5,
    ) -> dict[str, Any]:
        """
        Build preview data for all mapped entities.

        Args:
            workbook: Dictionary of sheet DataFrames
            mappings: Field mapping configuration
            limit: Maximum rows per preview

        Returns:
            Dictionary of entity previews
        """
        preview: dict[str, Any] = {}
        for entity, config in mappings.items():
            sheet = config.get("sheet")
            fields = config.get("fields", {})
            schema = IMPORT_SCHEMAS.get(entity)
            dataframe = workbook.get(sheet)
            if not schema or dataframe is None:
                continue
            rows = PreviewBuilder._preview_rows(schema, dataframe, fields, limit=limit)
            preview[entity] = rows
        return preview

    @staticmethod
    def _preview_rows(
        schema: Any,
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
        *,
        limit: int,
    ) -> dict[str, Any]:
        """
        Generate preview rows for a specific entity.

        Args:
            schema: Import schema definition
            dataframe: Source DataFrame
            field_mappings: Field mapping configuration
            limit: Maximum number of rows

        Returns:
            Preview data with rows and metadata
        """
        required_missing = [
            field.key
            for field in schema.fields
            if field.required and not field_mappings.get(field.key, {}).get("column")
        ]

        rows: list[dict[str, Any]] = []
        for index, row in enumerate(load_dataframe_preview(dataframe, limit=limit)):
            mapped_row: dict[str, Any] = {"__row": index}
            for field in schema.fields:
                column = field_mappings.get(field.key, {}).get("column")
                mapped_row[field.key] = row.get(column) if column else None
            rows.append(mapped_row)

        return {
            "rows": rows,
            "missing_required_fields": required_missing,
            "total_rows": int(dataframe.shape[0]),
            "mapped_field_count": sum(1 for field in schema.fields if field_mappings.get(field.key, {}).get("column")),
        }

    @staticmethod
    async def enrich_listing_preview(
        db: AsyncSession,
        preview: dict[str, Any],
        import_session: ImportSession,
        workbook: Mapping[str, DataFrame],
    ) -> dict[str, Any]:
        """
        Enrich listing previews with CPU matching suggestions.

        Args:
            db: Database session
            preview: Current preview data
            import_session: Import session
            workbook: Dictionary of sheet DataFrames

        Returns:
            Enriched preview data with component matches
        """
        listing_preview = preview.get("listing")
        mapping = import_session.mappings_json.get("listing") if import_session.mappings_json else None
        if not listing_preview or not mapping:
            return preview

        sheet_cpu_column = mapping.get("fields", {}).get("cpu_name", {}).get("column")
        if not sheet_cpu_column:
            return preview

        dataframe = workbook.get(mapping.get("sheet"))
        if dataframe is None:
            return preview

        cpu_names = await CpuMatcher.load_cpu_names(db)
        suggestions = CpuMatcher.match_components(dataframe, sheet_cpu_column, cpu_names)
        listing_preview["component_matches"] = suggestions
        preview["listing"] = listing_preview
        return preview


__all__ = ["PreviewBuilder"]
