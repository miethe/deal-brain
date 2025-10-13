"""Service for loading baseline valuation rules from JSON artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from dealbrain_core.schemas.baseline import (
    BaselineDiffResponse,
    BaselineDiffSummary,
    BaselineEntityMetadata,
    BaselineFieldDiff,
    BaselineFieldMetadata,
    BaselineMetadataResponse,
)
from sqlalchemy import String, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.core import ValuationRuleAudit, ValuationRuleGroup, ValuationRuleset
from .rules import RulesService

BASIC_GROUP_NAME = "Basic · Adjustments"
BASIC_GROUP_CATEGORY = "baseline"


@dataclass(slots=True)
class BaselineLoadResult:
    """Summary of a baseline ingestion run."""

    status: str
    ruleset_id: int | None
    ruleset_name: str | None
    source_hash: str
    version: str
    created_groups: int
    created_rules: int
    skipped_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable representation."""
        return {
            "status": self.status,
            "ruleset_id": self.ruleset_id,
            "ruleset_name": self.ruleset_name,
            "source_hash": self.source_hash,
            "version": self.version,
            "created_groups": self.created_groups,
            "created_rules": self.created_rules,
            "skipped_reason": self.skipped_reason,
        }


class BaselineLoaderService:
    """Map curated baseline JSON into system rulesets."""

    def __init__(self, rules_service: RulesService | None = None) -> None:
        # Disable recalculation during baseline ingestion to avoid Redis dependency
        self.rules_service = rules_service or RulesService(trigger_recalculation=False)

    async def load_from_path(
        self,
        session: AsyncSession,
        source_path: Path | str,
        *,
        actor: str | None = "system",
        ensure_basic_for_ruleset: int | None = None,
    ) -> BaselineLoadResult:
        """Load baseline data from a JSON file."""
        path = Path(source_path)
        if not path.exists():
            raise FileNotFoundError(f"Baseline artifact not found: {path}")

        payload = json.loads(path.read_text(encoding="utf-8"))
        result = await self.load_from_payload(
            session,
            payload,
            actor=actor,
            ensure_basic_for_ruleset=ensure_basic_for_ruleset,
            source_reference=str(path),
        )
        return result

    async def load_from_payload(
        self,
        session: AsyncSession,
        payload: dict[str, Any],
        *,
        actor: str | None = "system",
        ensure_basic_for_ruleset: int | None = None,
        source_reference: str | None = None,
    ) -> BaselineLoadResult:
        """Create a baseline ruleset from an in-memory payload."""
        source_hash = self._calculate_hash(payload)
        existing = await self._find_ruleset_by_hash(session, source_hash)
        if existing:
            return BaselineLoadResult(
                status="skipped",
                ruleset_id=existing.id,
                ruleset_name=existing.name,
                source_hash=source_hash,
                version=existing.version,
                created_groups=0,
                created_rules=0,
                skipped_reason="ruleset_with_hash_exists",
            )

        version = self._derive_version(payload, source_hash)
        ruleset_name = f"System: Baseline v{version}"
        metadata = {
            "system_baseline": True,
            "source_hash": source_hash,
            "schema_version": str(payload.get("schema_version", "1.0")),
            "generated_at": payload.get("generated_at"),
            "source_reference": source_reference,
            "source_version": version,
            "read_only": True,
        }

        ruleset = await self.rules_service.create_ruleset(
            session=session,
            name=ruleset_name,
            description="System baseline valuation ruleset",
            version=version,
            created_by=actor,
            metadata=metadata,
            priority=5,
            is_active=True,
        )

        entities = payload.get("entities", {})
        created_groups = 0
        created_rules = 0

        for display_index, (entity_key, fields) in enumerate(entities.items(), start=1):
            if not isinstance(fields, (list, tuple)):
                continue

            group_metadata = {
                "system_baseline": True,
                "entity_key": entity_key,
                "basic_read_only": True,
            }
            group = await self.rules_service.create_rule_group(
                session=session,
                ruleset_id=ruleset.id,
                name=f"{entity_key} · Baseline",
                category=self._normalize_category(entity_key),
                description=f"Baseline valuations for {entity_key}",
                display_order=display_index,
                weight=1.0,
                is_active=True,
                metadata=group_metadata,
            )
            created_groups += 1

            for rule_index, field in enumerate(fields, start=1):
                rule_metadata = self._build_rule_metadata(field, entity_key, source_hash)
                actions = self._build_placeholder_actions(field)
                rule_name = self._build_rule_name(field)

                await self.rules_service.create_rule(
                    session=session,
                    group_id=group.id,
                    name=rule_name,
                    description=field.get("description"),
                    priority=rule_index,
                    evaluation_order=rule_index,
                    conditions=[],
                    actions=actions,
                    created_by=actor,
                    metadata=rule_metadata,
                )
                created_rules += 1

        await self._deactivate_previous_baseline_rulesets(session, ruleset.id)

        if ensure_basic_for_ruleset is not None:
            await self.ensure_basic_adjustments_group(
                session, ensure_basic_for_ruleset, actor=actor
            )

        return BaselineLoadResult(
            status="created",
            ruleset_id=ruleset.id,
            ruleset_name=ruleset.name,
            source_hash=source_hash,
            version=version,
            created_groups=created_groups,
            created_rules=created_rules,
        )

    async def ensure_basic_adjustments_group(
        self,
        session: AsyncSession,
        target_ruleset_id: int | None = None,
        *,
        actor: str | None = "system",
    ) -> ValuationRuleGroup | None:
        """Guarantee the presence of a managed Basic Adjustments group."""
        target_ruleset = await self._resolve_target_ruleset(session, target_ruleset_id)
        if not target_ruleset:
            return None

        group_stmt = select(ValuationRuleGroup).where(
            ValuationRuleGroup.ruleset_id == target_ruleset.id,
            ValuationRuleGroup.name == BASIC_GROUP_NAME,
        )
        group_result = await session.execute(group_stmt)
        existing_group = group_result.scalar_one_or_none()

        if existing_group:
            metadata = dict(existing_group.metadata_json or {})
            metadata["basic_managed"] = True
            metadata.setdefault("entity_key", "composite")
            existing_group.metadata_json = metadata
            await session.commit()
            await session.refresh(existing_group)
            return existing_group

        group = await self.rules_service.create_rule_group(
            session=session,
            ruleset_id=target_ruleset.id,
            name=BASIC_GROUP_NAME,
            category=BASIC_GROUP_CATEGORY,
            description="Managed adjustments authored from Basic mode",
            display_order=target_ruleset.priority + 1,
            weight=1.0,
            is_active=True,
            metadata={"basic_managed": True, "entity_key": "composite"},
        )
        return group

    @staticmethod
    def _calculate_hash(payload: dict[str, Any]) -> str:
        packed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(packed).hexdigest()

    async def _find_ruleset_by_hash(
        self, session: AsyncSession, source_hash: str
    ) -> ValuationRuleset | None:
        from sqlalchemy import String, cast
        stmt = select(ValuationRuleset).where(
            cast(ValuationRuleset.metadata_json["source_hash"], String) == source_hash
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _deactivate_previous_baseline_rulesets(
        self, session: AsyncSession, keep_ruleset_id: int
    ) -> None:
        from sqlalchemy import String, cast
        stmt = select(ValuationRuleset).where(
            cast(ValuationRuleset.metadata_json["system_baseline"], String) == "true"
        )
        result = await session.execute(stmt)
        for ruleset in result.scalars():
            if ruleset.id == keep_ruleset_id:
                continue
            ruleset.is_active = False
        await session.commit()

    async def _resolve_target_ruleset(
        self, session: AsyncSession, ruleset_id: int | None
    ) -> ValuationRuleset | None:
        from sqlalchemy import String, cast
        if ruleset_id:
            return await session.get(ValuationRuleset, ruleset_id)

        stmt = (
            select(ValuationRuleset)
            .where(cast(ValuationRuleset.metadata_json["system_baseline"], String) != "true")
            .order_by(ValuationRuleset.priority.asc(), ValuationRuleset.id.asc())
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    def _build_rule_metadata(
        field: dict[str, Any], entity_key: str, source_hash: str
    ) -> dict[str, Any]:
        return {
            "system_baseline": True,
            "entity_key": entity_key,
            "field_id": field.get("id"),
            "proper_name": field.get("proper_name"),
            "description": field.get("description"),
            "explanation": field.get("explanation"),
            "unit": field.get("unit"),
            "formula_text": field.get("Formula"),
            "nullable": field.get("nullable"),
            "notes": field.get("notes"),
            "dependencies": field.get("dependencies"),
            "valuation_buckets": field.get("valuation_buckets"),
            "source_hash": source_hash,
            "baseline_placeholder": True,
        }

    @staticmethod
    def _build_placeholder_actions(field: dict[str, Any]) -> list[dict[str, Any]]:
        unit = field.get("unit")
        action_type = "fixed_value"
        if isinstance(unit, str) and unit.lower() == "multiplier":
            action_type = "multiplier"

        return [
            {
                "action_type": action_type,
                "metric": None,
                "value_usd": 0.0,
                "unit_type": None,
                "formula": None,
                "modifiers": {
                    "baseline_placeholder": True,
                    "baseline_unit": unit,
                },
            }
        ]

    @staticmethod
    def _build_rule_name(field: dict[str, Any]) -> str:
        proper_name = str(field.get("proper_name") or field.get("id") or "Baseline Field")
        return f"{proper_name} · Baseline"

    @staticmethod
    def _normalize_category(entity_key: str) -> str:
        normalized = entity_key.replace(".", "_").replace(" ", "_")
        return normalized.lower()

    @staticmethod
    def _derive_version(payload: dict[str, Any], source_hash: str) -> str:
        schema_version = str(payload.get("schema_version", "1.0"))
        generated_at = payload.get("generated_at")
        suffix = source_hash[:8]
        if generated_at:
            try:
                parsed = datetime.fromisoformat(str(generated_at))
                suffix = parsed.strftime("%Y%m%d")
            except ValueError:
                suffix = str(generated_at).replace("-", "").replace(":", "")
        return f"{schema_version}.{suffix}"

    async def get_baseline_metadata(
        self,
        session: AsyncSession,
    ) -> BaselineMetadataResponse | None:
        """Extract metadata from the currently active baseline ruleset.

        Returns:
            BaselineMetadataResponse if active baseline exists, None otherwise.
        """
        # Find active baseline ruleset
        stmt = select(ValuationRuleset).where(
            cast(ValuationRuleset.metadata_json["system_baseline"], String) == "true",
            ValuationRuleset.is_active.is_(True)
        )
        result = await session.execute(stmt)
        ruleset = result.scalar_one_or_none()

        if not ruleset:
            return None

        # Extract metadata from ruleset
        metadata = ruleset.metadata_json or {}
        source_hash = metadata.get("source_hash", "")
        schema_version = metadata.get("schema_version", "1.0")
        generated_at = metadata.get("generated_at")

        # Reconstruct entities from rule groups
        entities: list[BaselineEntityMetadata] = []

        for group in ruleset.rule_groups:
            group_meta = group.metadata_json or {}
            entity_key = group_meta.get("entity_key", "Unknown")

            fields: list[BaselineFieldMetadata] = []

            for rule in group.rules:
                rule_meta = rule.metadata_json or {}

                # Extract min/max from valuation buckets if present
                min_value = None
                max_value = None
                valuation_buckets = rule_meta.get("valuation_buckets")

                if valuation_buckets and isinstance(valuation_buckets, list):
                    min_vals = [
                        b.get("min_usd") for b in valuation_buckets if b.get("min_usd") is not None
                    ]
                    max_vals = [
                        b.get("max_usd") for b in valuation_buckets if b.get("max_usd") is not None
                    ]
                    if min_vals:
                        min_value = min(min_vals)
                    if max_vals:
                        max_value = max(max_vals)

                field = BaselineFieldMetadata(
                    field_name=rule_meta.get("field_id", rule.name),
                    field_type=rule_meta.get("unit", "USD"),
                    proper_name=rule_meta.get("proper_name"),
                    description=rule_meta.get("description"),
                    explanation=rule_meta.get("explanation"),
                    unit=rule_meta.get("unit"),
                    min_value=min_value,
                    max_value=max_value,
                    formula=rule_meta.get("formula_text"),
                    dependencies=rule_meta.get("dependencies"),
                    nullable=rule_meta.get("nullable", False),
                    notes=rule_meta.get("notes"),
                    valuation_buckets=valuation_buckets,
                )
                fields.append(field)

            if fields:
                entities.append(BaselineEntityMetadata(
                    entity_key=entity_key,
                    fields=fields,
                ))

        return BaselineMetadataResponse(
            version=ruleset.version,
            entities=entities,
            source_hash=source_hash,
            is_active=ruleset.is_active,
            schema_version=schema_version,
            generated_at=generated_at,
            ruleset_id=ruleset.id,
            ruleset_name=ruleset.name,
        )

    async def diff_baseline(
        self,
        session: AsyncSession,
        candidate_json: dict[str, Any],
    ) -> BaselineDiffResponse:
        """Compare candidate baseline against the current active baseline.

        Args:
            session: Database session
            candidate_json: Candidate baseline JSON structure

        Returns:
            BaselineDiffResponse with added, changed, and removed fields
        """
        # Get current baseline metadata
        current_metadata = await self.get_baseline_metadata(session)

        # Build current fields map for comparison
        current_fields: dict[str, dict[str, Any]] = {}
        current_version = None

        if current_metadata:
            current_version = current_metadata.version
            for entity in current_metadata.entities:
                for field in entity.fields:
                    field_key = f"{entity.entity_key}.{field.field_name}"
                    current_fields[field_key] = {
                        "entity_key": entity.entity_key,
                        "field_name": field.field_name,
                        "proper_name": field.proper_name,
                        "description": field.description,
                        "explanation": field.explanation,
                        "unit": field.unit,
                        "min_value": field.min_value,
                        "max_value": field.max_value,
                        "formula": field.formula,
                        "dependencies": field.dependencies,
                        "nullable": field.nullable,
                        "notes": field.notes,
                        "valuation_buckets": field.valuation_buckets,
                    }

        # Build candidate fields map
        candidate_fields: dict[str, dict[str, Any]] = {}
        candidate_entities = candidate_json.get("entities", {})

        for entity_key, fields in candidate_entities.items():
            if not isinstance(fields, (list, tuple)):
                continue

            for field in fields:
                field_id = field.get("id")
                if not field_id:
                    continue

                field_key = f"{entity_key}.{field_id}"

                # Extract min/max from valuation buckets
                min_value = None
                max_value = None
                valuation_buckets = field.get("valuation_buckets")

                if valuation_buckets and isinstance(valuation_buckets, list):
                    min_vals = [
                        b.get("min_usd") for b in valuation_buckets if b.get("min_usd") is not None
                    ]
                    max_vals = [
                        b.get("max_usd") for b in valuation_buckets if b.get("max_usd") is not None
                    ]
                    if min_vals:
                        min_value = min(min_vals)
                    if max_vals:
                        max_value = max(max_vals)

                candidate_fields[field_key] = {
                    "entity_key": entity_key,
                    "field_name": field_id,
                    "proper_name": field.get("proper_name"),
                    "description": field.get("description"),
                    "explanation": field.get("explanation"),
                    "unit": field.get("unit"),
                    "min_value": min_value,
                    "max_value": max_value,
                    "formula": field.get("Formula"),
                    "dependencies": field.get("dependencies"),
                    "nullable": field.get("nullable", False),
                    "notes": field.get("notes"),
                    "valuation_buckets": valuation_buckets,
                }

        # Calculate diffs
        added: list[BaselineFieldDiff] = []
        changed: list[BaselineFieldDiff] = []
        removed: list[BaselineFieldDiff] = []

        # Find added and changed
        for field_key, candidate_field in candidate_fields.items():
            if field_key not in current_fields:
                # Field is added
                added.append(BaselineFieldDiff(
                    entity_key=candidate_field["entity_key"],
                    field_name=candidate_field["field_name"],
                    proper_name=candidate_field["proper_name"],
                    change_type="added",
                    old_value=None,
                    new_value=candidate_field,
                ))
            else:
                # Check if field changed
                current_field = current_fields[field_key]
                value_diff = self._calculate_field_diff(current_field, candidate_field)

                if value_diff:
                    changed.append(BaselineFieldDiff(
                        entity_key=candidate_field["entity_key"],
                        field_name=candidate_field["field_name"],
                        proper_name=candidate_field["proper_name"],
                        change_type="changed",
                        old_value=current_field,
                        new_value=candidate_field,
                        value_diff=value_diff,
                    ))

        # Find removed
        for field_key, current_field in current_fields.items():
            if field_key not in candidate_fields:
                removed.append(BaselineFieldDiff(
                    entity_key=current_field["entity_key"],
                    field_name=current_field["field_name"],
                    proper_name=current_field["proper_name"],
                    change_type="removed",
                    old_value=current_field,
                    new_value=None,
                ))

        summary = BaselineDiffSummary(
            added_count=len(added),
            changed_count=len(changed),
            removed_count=len(removed),
            total_changes=len(added) + len(changed) + len(removed),
        )

        candidate_version = self._derive_version(
            candidate_json, self._calculate_hash(candidate_json)
        )

        return BaselineDiffResponse(
            added=added,
            changed=changed,
            removed=removed,
            summary=summary,
            current_version=current_version,
            candidate_version=candidate_version,
        )

    async def adopt_baseline(
        self,
        session: AsyncSession,
        candidate_json: dict[str, Any],
        selected_changes: list[str] | None = None,
        actor: str | None = "system",
    ) -> dict[str, Any]:
        """Adopt selected changes from candidate baseline, creating a new version.

        Args:
            session: Database session
            candidate_json: Candidate baseline JSON structure
            selected_changes: Optional list of field IDs to adopt (entity.field format)
                            If None, all changes are adopted
            actor: User/system actor performing adoption

        Returns:
            Dict with adoption results including new ruleset ID, version, and audit log
        """
        # Get diff to understand what's changing
        diff_result = await self.diff_baseline(session, candidate_json)

        # Determine which changes to apply
        if selected_changes is None:
            # Adopt all changes
            fields_to_adopt = set()
            for diff in diff_result.added + diff_result.changed:
                fields_to_adopt.add(f"{diff.entity_key}.{diff.field_name}")
        else:
            fields_to_adopt = set(selected_changes)

        # Filter candidate_json to only include selected fields
        filtered_entities: dict[str, list[dict[str, Any]]] = {}
        candidate_entities = candidate_json.get("entities", {})

        for entity_key, fields in candidate_entities.items():
            if not isinstance(fields, (list, tuple)):
                continue

            filtered_fields = []
            for field in fields:
                field_id = field.get("id")
                if not field_id:
                    continue

                field_key = f"{entity_key}.{field_id}"
                if field_key in fields_to_adopt:
                    filtered_fields.append(field)

            if filtered_fields:
                filtered_entities[entity_key] = filtered_fields

        # Create filtered baseline payload
        filtered_payload = {
            "schema_version": candidate_json.get("schema_version", "1.0"),
            "generated_at": datetime.utcnow().isoformat(),
            "description": f"Adopted baseline changes - {len(fields_to_adopt)} fields",
            "entities": filtered_entities,
        }

        # Get current baseline ruleset ID before deactivation
        stmt = select(ValuationRuleset).where(
            cast(ValuationRuleset.metadata_json["system_baseline"], String) == "true",
            ValuationRuleset.is_active.is_(True)
        )
        result = await session.execute(stmt)
        previous_ruleset = result.scalar_one_or_none()
        previous_ruleset_id = previous_ruleset.id if previous_ruleset else None

        # Load the filtered baseline as a new ruleset
        load_result = await self.load_from_payload(
            session,
            filtered_payload,
            actor=actor,
            source_reference="adopted_from_candidate",
        )

        # Create audit log entry
        audit_entry = ValuationRuleAudit(
            rule_id=None,  # Ruleset-level change
            action="baseline_adopted",
            actor=actor,
            changes_json={
                "previous_ruleset_id": previous_ruleset_id,
                "new_ruleset_id": load_result.ruleset_id,
                "adopted_fields": list(fields_to_adopt),
                "total_changes": len(fields_to_adopt),
                "diff_summary": {
                    "added": len(
                        [
                            d
                            for d in diff_result.added
                            if f"{d.entity_key}.{d.field_name}" in fields_to_adopt
                        ]
                    ),
                    "changed": len(
                        [
                            d
                            for d in diff_result.changed
                            if f"{d.entity_key}.{d.field_name}" in fields_to_adopt
                        ]
                    ),
                },
            },
            impact_summary={
                "ruleset_created": load_result.status == "created",
                "groups_created": load_result.created_groups,
                "rules_created": load_result.created_rules,
            },
        )
        session.add(audit_entry)
        await session.commit()
        await session.refresh(audit_entry)

        # Calculate skipped fields
        all_candidate_fields = set()
        for entity_key, fields in candidate_entities.items():
            if isinstance(fields, (list, tuple)):
                for field in fields:
                    field_id = field.get("id")
                    if field_id:
                        all_candidate_fields.add(f"{entity_key}.{field_id}")

        skipped_fields = list(all_candidate_fields - fields_to_adopt)

        return {
            "new_ruleset_id": load_result.ruleset_id,
            "new_version": load_result.version,
            "changes_applied": len(fields_to_adopt),
            "recalculation_job_id": None,  # Implemented by caller if needed
            "adopted_fields": list(fields_to_adopt),
            "skipped_fields": skipped_fields,
            "previous_ruleset_id": previous_ruleset_id,
            "audit_log_id": audit_entry.id,
        }

    @staticmethod
    def _calculate_field_diff(
        current: dict[str, Any],
        candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Calculate specific differences between current and candidate field definitions.

        Returns:
            Dict of changed attributes, or None if no changes detected
        """
        changes: dict[str, Any] = {}

        # Compare relevant attributes
        compare_attrs = [
            "description",
            "explanation",
            "unit",
            "min_value",
            "max_value",
            "formula",
            "dependencies",
            "nullable",
            "notes",
            "valuation_buckets",
        ]

        for attr in compare_attrs:
            current_val = current.get(attr)
            candidate_val = candidate.get(attr)

            # Handle None vs empty list/dict comparisons
            if current_val != candidate_val:
                changes[attr] = {
                    "old": current_val,
                    "new": candidate_val,
                }

        return changes if changes else None
