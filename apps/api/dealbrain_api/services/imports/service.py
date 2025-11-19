"""Service helpers that orchestrate spreadsheet import sessions."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.core import CustomFieldDefinition, ImportSession, ImportSessionAudit
from ...seeds import apply_seed
from ...settings import Settings, get_settings
from .builders import SeedBuilder
from .cpu_matcher import CpuMatcher
from .preview_builder import PreviewBuilder
from .schema_mapper import SchemaMapper
from .utils import checksum_bytes, ensure_directory
from .validators import ImportValidator
from .workbook_parser import WorkbookParser


class ImportSessionService:
    """
    Coordinates the importer workflow: upload, mapping, preview, and conflicts.

    This is the main facade that delegates to specialized modules:
    - WorkbookParser: Excel/CSV file parsing
    - SchemaMapper: Schema inference and field mapping
    - PreviewBuilder: Preview data generation
    - CpuMatcher: Component matching and auto-creation
    - ImportValidator: Conflict detection and validation
    - SeedBuilder: Entity seed construction
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def create_session(
        self,
        db: AsyncSession,
        *,
        upload: UploadFile,
        declared_entities: Mapping[str, str] | None = None,
        created_by: str | None = None,
    ) -> ImportSession:
        """
        Create a new import session from an uploaded file.

        Args:
            db: Database session
            upload: Uploaded file (Excel or CSV)
            declared_entities: Optional mapping of sheet names to entity types
            created_by: User ID of session creator

        Returns:
            Newly created ImportSession

        Raises:
            ValueError: If file is empty or invalid
        """
        raw_bytes = await upload.read()
        if not raw_bytes:
            raise ValueError("Uploaded file is empty")

        declared_entities = dict(declared_entities or {})
        session_id = uuid4()
        filename = upload.filename or f"import-{session_id}.xlsx"
        upload_root = self.settings.upload_root / str(session_id) / "source"
        ensure_directory(upload_root)
        file_path = upload_root / filename
        file_path.write_bytes(raw_bytes)

        # Parse workbook and infer schema
        workbook = WorkbookParser.load_workbook(file_path)
        sheet_meta = SchemaMapper.inspect_workbook(workbook, declared_entities=declared_entities)
        mappings = SchemaMapper.generate_initial_mappings(sheet_meta)
        preview = PreviewBuilder.build_preview(workbook, mappings)

        import_session = ImportSession(
            id=session_id,
            filename=filename,
            content_type=upload.content_type,
            checksum=checksum_bytes(raw_bytes),
            upload_path=str(file_path),
            status="mapping_required",
            sheet_meta_json=sheet_meta,
            mappings_json=mappings,
            preview_json=preview,
            conflicts_json={},
            declared_entities_json=declared_entities,
            created_by=created_by,
        )
        db.add(import_session)
        await db.flush()
        await db.refresh(import_session)

        self._record_audit(
            db,
            import_session,
            event="session_created",
            payload={
                "filename": filename,
                "sheet_count": len(workbook),
            },
        )

        # Check for declared entity mismatches
        mismatches = [
            {
                "sheet": meta.get("sheet_name"),
                "declared": meta.get("declared_entity"),
                "inferred": meta.get("entity"),
                "confidence": meta.get("confidence"),
            }
            for meta in sheet_meta
            if meta.get("declared_entity")
            and meta.get("entity")
            and meta.get("entity") != meta.get("declared_entity")
        ]
        if mismatches:
            self._record_audit(
                db,
                import_session,
                event="declared_entity_mismatch",
                payload={"mismatches": mismatches},
            )

        return import_session

    async def refresh_preview(
        self,
        db: AsyncSession,
        import_session: ImportSession,
        *,
        limit: int = 5,
    ) -> dict[str, Any]:
        """
        Refresh the preview data for an import session.

        Args:
            db: Database session
            import_session: Import session to refresh
            limit: Maximum rows per entity preview

        Returns:
            Updated preview data
        """
        workbook = WorkbookParser.load_workbook(Path(import_session.upload_path))
        preview = PreviewBuilder.build_preview(workbook, import_session.mappings_json, limit=limit)
        preview = await PreviewBuilder.enrich_listing_preview(db, preview, import_session, workbook)
        import_session.preview_json = preview
        await db.flush()
        return preview

    async def update_mappings(
        self,
        db: AsyncSession,
        import_session: ImportSession,
        *,
        mappings: dict[str, Any],
    ) -> ImportSession:
        """
        Update field mappings for an import session.

        Args:
            db: Database session
            import_session: Import session to update
            mappings: New mapping configuration

        Returns:
            Updated import session
        """
        merged_mappings = SchemaMapper.merge_mappings(import_session.mappings_json, mappings)
        import_session.mappings_json = merged_mappings
        await self.refresh_preview(db, import_session)
        self._record_audit(
            db,
            import_session,
            event="mappings_updated",
            payload={"entities": list(mappings.keys())},
        )
        return import_session

    async def compute_conflicts(
        self,
        db: AsyncSession,
        import_session: ImportSession,
    ) -> dict[str, Any]:
        """
        Detect conflicts between import data and existing database records.

        Args:
            db: Database session
            import_session: Import session to analyze

        Returns:
            Dictionary of conflicts by entity type
        """
        workbook = WorkbookParser.load_workbook(Path(import_session.upload_path))
        conflicts: dict[str, Any] = {}
        if cpu_conflicts := await ImportValidator.detect_cpu_conflicts(
            db, workbook, import_session.mappings_json
        ):
            conflicts["cpu"] = cpu_conflicts
        import_session.conflicts_json = conflicts
        await db.flush()
        return conflicts

    async def commit(
        self,
        db: AsyncSession,
        import_session: ImportSession,
        *,
        conflict_resolutions: Mapping[str, str],
        component_overrides: Mapping[int, dict[str, Any]],
    ) -> tuple[dict[str, int], list[str]]:
        """
        Commit the import session and apply data to the database.

        Args:
            db: Database session
            import_session: Import session to commit
            conflict_resolutions: User resolutions for detected conflicts
            component_overrides: Component assignment overrides by row index

        Returns:
            Tuple of (entity counts, auto-created CPU names)

        Raises:
            ValueError: If conflicts are unresolved or data is invalid
        """
        workbook = WorkbookParser.load_workbook(Path(import_session.upload_path))
        ImportValidator.validate_conflicts(import_session.conflicts_json, conflict_resolutions)

        # Load component lookups
        cpu_lookup = await CpuMatcher.load_cpu_lookup(db)
        gpu_lookup = await CpuMatcher.load_gpu_lookup(db)

        # Auto-create missing CPUs if needed
        auto_created_cpus: list[str] = []
        listing_mapping = (
            import_session.mappings_json.get("listing") if import_session.mappings_json else None
        )
        if listing_mapping:
            dataframe = workbook.get(listing_mapping.get("sheet"))
            if dataframe is not None:
                missing_cpu_entries = CpuMatcher.collect_missing_cpus(
                    dataframe,
                    listing_mapping.get("fields", {}),
                    component_overrides=component_overrides,
                    cpu_lookup=cpu_lookup,
                )
                if missing_cpu_entries:
                    created_cpus = await CpuMatcher.auto_create_cpus(
                        db,
                        entries=missing_cpu_entries,
                        import_session=import_session,
                    )
                    if created_cpus:
                        auto_created_cpus = [cpu.name for cpu in created_cpus]
                        cpu_lookup = await CpuMatcher.load_cpu_lookup(db)
                        self._record_audit(
                            db,
                            import_session,
                            event="cpu_auto_created",
                            payload={"cpus": auto_created_cpus},
                        )

        # Build seed and apply
        seed = SeedBuilder.build_seed(
            workbook,
            import_session.mappings_json,
            conflict_resolutions=conflict_resolutions,
            component_overrides=component_overrides,
            cpu_lookup=cpu_lookup,
            gpu_lookup=gpu_lookup,
        )

        await apply_seed(seed)

        counts = {
            "cpus": len(seed.cpus),
            "gpus": len(seed.gpus),
            "valuation_rules": len(seed.valuation_rules),
            "ports_profiles": len(seed.ports_profiles),
            "listings": len(seed.listings),
        }

        import_session.status = "completed"
        import_session.conflicts_json = {}
        self._record_audit(
            db,
            import_session,
            event="commit_success",
            payload={**counts, "auto_created_cpus": auto_created_cpus},
        )
        await db.flush()

        return counts, auto_created_cpus

    async def attach_custom_field(
        self,
        db: AsyncSession,
        import_session: ImportSession,
        field: CustomFieldDefinition,
    ) -> ImportSession:
        """
        Attach a custom field definition to an import session's mappings.

        Args:
            db: Database session
            import_session: Import session to update
            field: Custom field definition to attach

        Returns:
            Updated import session
        """
        existing_mappings = import_session.mappings_json or {}
        updated_mappings = deepcopy(existing_mappings)
        entity_config = updated_mappings.setdefault(field.entity, {"sheet": None, "fields": {}})
        fields = entity_config.setdefault("fields", {})

        if field.key not in fields:
            fields[field.key] = {
                "field": field.key,
                "label": field.label,
                "required": field.required,
                "data_type": field.data_type,
                "column": None,
                "status": "missing",
                "confidence": 0.0,
                "suggestions": [],
            }
            import_session.mappings_json = updated_mappings
            self._record_audit(
                db,
                import_session,
                event="custom_field_attached",
                payload={"field": field.key, "entity": field.entity},
            )
        else:
            import_session.mappings_json = updated_mappings

        await db.flush()
        return import_session

    def _record_audit(
        self,
        db: AsyncSession,
        import_session: ImportSession,
        *,
        event: str,
        payload: Mapping[str, Any] | None = None,
        message: str | None = None,
    ) -> None:
        """
        Record an audit event for an import session.

        Args:
            db: Database session
            import_session: Import session
            event: Event type identifier
            payload: Optional event data
            message: Optional human-readable message
        """
        audit = ImportSessionAudit(
            session_id=import_session.id,
            event=event,
            message=message,
            payload_json=payload if payload is not None else None,
        )
        db.add(audit)


__all__ = ["ImportSessionService"]
