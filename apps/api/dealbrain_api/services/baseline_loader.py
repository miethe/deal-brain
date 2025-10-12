"""Service for loading baseline valuation rules from JSON artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.core import ValuationRuleGroup, ValuationRuleset
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
        from sqlalchemy import cast, String
        stmt = select(ValuationRuleset).where(
            cast(ValuationRuleset.metadata_json["source_hash"], String) == source_hash
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _deactivate_previous_baseline_rulesets(
        self, session: AsyncSession, keep_ruleset_id: int
    ) -> None:
        from sqlalchemy import cast, String
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
        from sqlalchemy import cast, String
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
    def _build_rule_metadata(field: dict[str, Any], entity_key: str, source_hash: str) -> dict[str, Any]:
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
