from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta
from typing import Any, Iterable
from urllib.parse import urlparse

from dealbrain_core.enums import ComponentMetric, ComponentType, Condition, StorageMedium
from dealbrain_core.gpu import compute_gpu_score
from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from dealbrain_core.scoring import ListingMetrics, compute_composite_score, dollar_per_metric
from dealbrain_core.valuation import ComponentValuationInput, compute_adjusted_price
from sqlalchemy import and_, asc, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..cache import cache_manager
from ..models import Cpu, Gpu, Listing, ListingComponent, Profile
from ..telemetry import get_logger
from .component_catalog import (
    get_or_create_ram_spec,
    get_or_create_storage_profile,
    normalize_int,
    normalize_ram_generation,
    normalize_ram_spec_payload,
    normalize_storage_profile_payload,
    storage_medium_display,
)
from .ingestion import DeduplicationResult
from .rule_evaluation import RuleEvaluationService

VALUATION_DISABLED_RULESETS_KEY = "valuation_disabled_rulesets"

logger = get_logger("dealbrain.listings")
_RULE_EVALUATION_SERVICE = RuleEvaluationService()


MUTABLE_LISTING_FIELDS: set[str] = {
    "title",
    "listing_url",
    "other_urls",
    "seller",
    "price_usd",
    "price_date",
    "condition",
    "status",
    "cpu_id",
    "gpu_id",
    "ports_profile_id",
    "ram_spec_id",
    "primary_storage_profile_id",
    "secondary_storage_profile_id",
    "device_model",
    "ram_gb",
    "ram_notes",
    "primary_storage_gb",
    "primary_storage_type",
    "secondary_storage_gb",
    "secondary_storage_type",
    "os_license",
    "notes",
    "ruleset_id",
}


def _normalize_listing_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle legacy field aliases and normalize payload keys."""
    if "url" in payload and "listing_url" not in payload:
        payload["listing_url"] = payload.pop("url")
    if "listing_url" in payload:
        payload["listing_url"] = _sanitize_primary_url(payload["listing_url"])
    if "other_urls" in payload:
        payload["other_urls"] = _normalize_other_urls(payload["other_urls"])
    return payload


def _sanitize_primary_url(value: Any) -> str | None:
    if value in (None, "", []):
        return None
    url_str = str(value).strip()
    parsed = urlparse(url_str)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("listing_url must use http:// or https:// and include a host")
    return url_str


def _normalize_other_urls(value: Any) -> list[dict[str, str | None]]:
    if not value:
        return []
    normalized: list[dict[str, str | None]] = []
    items = value if isinstance(value, (list, tuple)) else [value]
    seen: set[str] = set()
    for item in items:
        if item in (None, "", {}):
            continue
        if isinstance(item, str):
            url = item.strip()
            label = None
        elif isinstance(item, dict):
            url = str(item.get("url") or item.get("href") or "").strip()
            label_value = item.get("label") or item.get("text")
            label = str(label_value).strip() if label_value else None
        else:
            url = str(item).strip()
            label = None
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(
                "Supplemental link URLs must use http:// or https:// and include a host"
            )
        if url in seen:
            continue
        seen.add(url)
        normalized.append({"url": url, "label": label})
    return normalized


async def _prepare_component_relationships(
    session: AsyncSession,
    payload: dict[str, Any],
    *,
    listing: Listing | None = None,
) -> None:
    """Resolve or create component relationships for a listing payload."""
    ram_type_hint = payload.pop("ram_type", None)
    ram_speed_hint = payload.pop("ram_speed_mhz", None)
    ram_spec_payload = payload.pop("ram_spec", None)

    if "ram_spec_id" not in payload:
        total_capacity = normalize_int(payload.get("ram_gb"))
        if total_capacity is None and listing:
            total_capacity = (
                listing.ram_spec.total_capacity_gb if listing.ram_spec else listing.ram_gb
            )
        spec_input = normalize_ram_spec_payload(
            ram_spec_payload,
            fallback_total_gb=total_capacity,
            fallback_generation=normalize_ram_generation(ram_type_hint)
            if ram_type_hint
            else (listing.ram_spec.ddr_generation if listing and listing.ram_spec else None),
            fallback_speed=
            normalize_int(ram_speed_hint)
            or (listing.ram_spec.speed_mhz if listing and listing.ram_spec else None),
        )
        if spec_input:
            ram_spec = await get_or_create_ram_spec(session, spec_input)
            payload["ram_spec_id"] = ram_spec.id
            if payload.get("ram_gb") is None and ram_spec.total_capacity_gb is not None:
                payload["ram_gb"] = ram_spec.total_capacity_gb
        elif ram_spec_payload or ram_type_hint or ram_speed_hint:
            # If hints were provided but unusable, raise to surface validation issues
            raise ValueError("RAM specification details were provided but could not be resolved")

    for prefix in ("primary", "secondary"):
        profile_key = f"{prefix}_storage_profile"
        profile_id_key = f"{prefix}_storage_profile_id"
        storage_type_key = f"{prefix}_storage_type"
        capacity_key = f"{prefix}_storage_gb"
        existing_profile = getattr(listing, f"{prefix}_storage_profile") if listing else None

        profile_payload = payload.pop(profile_key, None)
        if profile_id_key in payload:
            continue

        fallback_capacity = normalize_int(payload.get(capacity_key))
        if fallback_capacity is None:
            if existing_profile and existing_profile.capacity_gb is not None:
                fallback_capacity = existing_profile.capacity_gb
            elif listing:
                fallback_capacity = normalize_int(getattr(listing, f"{prefix}_storage_gb", None))

        fallback_type = payload.get(storage_type_key)
        if fallback_type is None:
            if existing_profile and existing_profile.medium:
                fallback_type = existing_profile.medium
            elif listing:
                fallback_type = getattr(listing, storage_type_key, None)

        profile_input = normalize_storage_profile_payload(
            profile_payload,
            fallback_capacity_gb=fallback_capacity,
            fallback_type=fallback_type,
        )

        if not profile_input:
            continue

        storage_profile = await get_or_create_storage_profile(session, profile_input)
        payload[profile_id_key] = storage_profile.id

        if (
            payload.get(capacity_key) is None
            and storage_profile.capacity_gb is not None
        ):
            payload[capacity_key] = storage_profile.capacity_gb

        if storage_profile.medium and storage_profile.medium != StorageMedium.UNKNOWN:
            payload[storage_type_key] = payload.get(storage_type_key) or storage_medium_display(
                storage_profile.medium
            )
def _format_rule_evaluation_breakdown(summary: dict[str, Any]) -> dict[str, Any]:
    """Normalize rule evaluation summary for storage on the listing record."""
    def _as_float(value: Any) -> float:
        try:
            return float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    listing_price = _as_float(summary.get("original_price"))
    adjusted_price = _as_float(summary.get("adjusted_price"))
    total_adjustment = _as_float(summary.get("total_adjustment"))

    adjustments: list[dict[str, Any]] = []
    lines: list[dict[str, Any]] = []

    for result in summary.get("evaluation_results", []):
        if not result or not result.get("matched") or result.get("error"):
            continue

        adjustment_value = _as_float(result.get("adjustment_value"))
        actions_breakdown = []
        for action in result.get("breakdown") or []:
            action_value = _as_float(action.get("value"))
            actions_breakdown.append(
                {
                    "action_type": action.get("action_type"),
                    "metric": action.get("metric"),
                    "value": action_value,
                    "details": action.get("details"),
                    "error": action.get("error"),
                },
            )

        adjustments.append(
            {
                "rule_id": result.get("rule_id"),
                "rule_name": result.get("rule_name"),
                "adjustment_usd": adjustment_value,
                "actions": actions_breakdown,
            },
        )

        lines.append(
            {
                "label": result.get("rule_name"),
                "component_type": "rule",
                "quantity": 1,
                "unit_value": abs(adjustment_value),
                "condition_multiplier": 1.0,
                "deduction_usd": round(max(-adjustment_value, 0.0), 2),
                "adjustment_usd": adjustment_value,
            },
        )

    matched_rules = []
    for entry in summary.get("matched_rules", []):
        matched_rules.append(
            {
                "rule_id": entry.get("rule_id"),
                "rule_name": entry.get("rule_name"),
                "adjustment": _as_float(entry.get("adjustment")),
                "breakdown": entry.get("breakdown"),
            },
        )

    total_deductions = round(sum(line["deduction_usd"] for line in lines), 2)

    return {
        "listing_price": listing_price,
        "adjusted_price": adjusted_price,
        "total_adjustment": total_adjustment,
        "total_deductions": total_deductions,
        "matched_rules_count": summary.get("matched_rules_count", len(adjustments)),
        "matched_rules": matched_rules,
        "adjustments": adjustments,
        "lines": lines,
        "ruleset": {
            "id": summary.get("ruleset_id"),
            "name": summary.get("ruleset_name"),
        },
        "ruleset_name": summary.get("ruleset_name"),
    }


async def apply_listing_metrics(session: AsyncSession, listing: Listing) -> None:
    evaluation_summary: dict[str, Any] | None = None

    logger.debug(
        "listing.metrics.start",
        listing_id=listing.id,
        ruleset_id=listing.ruleset_id,
        price=listing.price_usd,
    )

    if listing.id:
        try:
            ruleset_override = listing.ruleset_id if listing.ruleset_id else None
            evaluation_summary = await _RULE_EVALUATION_SERVICE.evaluate_listing(
                session=session,
                listing_id=listing.id,
                ruleset_id=ruleset_override,
            )
        except ValueError as exc:
            # Expected when no active rulesets are available; fall back to legacy valuation path.
            if "No active ruleset found" not in str(exc):
                logger.warning(
                    "listing.metrics.rule_evaluation_failed",
                    listing_id=listing.id,
                    ruleset_id=ruleset_override,
                    error=str(exc),
                )
        except Exception:  # pragma: no cover - defensive logging
            logger.exception(
                "listing.metrics.rule_evaluation_error",
                listing_id=listing.id,
                ruleset_id=ruleset_override,
            )

    if evaluation_summary:
        logger.info(
            "listing.metrics.ruleset_applied",
            listing_id=listing.id,
            ruleset_id=evaluation_summary.get("ruleset_id"),
            matched_rules=evaluation_summary.get("matched_rules_count"),
            total_adjustment=float(evaluation_summary.get("total_adjustment") or 0.0),
        )
        listing.adjusted_price_usd = float(evaluation_summary.get("adjusted_price") or 0.0)
        listing.valuation_breakdown = _format_rule_evaluation_breakdown(evaluation_summary)
    else:
        logger.info(
            "listing.metrics.legacy_path",
            listing_id=listing.id,
            reason="rule_evaluation_empty",
        )
        # Eagerly load components to avoid lazy-load in async context for legacy valuation fallback.
        await session.refresh(listing, ["components"])

        components: list[ComponentValuationInput] = list(build_component_inputs(listing))
        valuation = compute_adjusted_price(
            listing_price_usd=float(listing.price_usd or 0),
            condition=_coerce_condition(listing.condition),
            rules=[],
            components=components,
        )

        listing.adjusted_price_usd = valuation.adjusted_price_usd
        listing.valuation_breakdown = {
            "listing_price": valuation.listing_price_usd,
            "adjusted_price": valuation.adjusted_price_usd,
            "lines": [line.__dict__ for line in valuation.lines],
            "total_deductions": valuation.total_deductions,
            "total_adjustment": float(valuation.adjusted_price_usd - valuation.listing_price_usd),
            "matched_rules_count": 0,
            "matched_rules": [],
            "adjustments": [],
            "ruleset": {"id": None, "name": None},
        }

    await session.flush()

    # Eagerly load CPU and GPU relationships to avoid lazy-load in async context
    if listing.cpu_id:
        cpu = await session.get(Cpu, listing.cpu_id)
        listing.cpu = cpu
    else:
        cpu = None

    if listing.gpu_id:
        gpu = await session.get(Gpu, listing.gpu_id)
    else:
        gpu = None

    cpu_multi = float(cpu.cpu_mark_multi) if cpu and cpu.cpu_mark_multi else None
    cpu_single = float(cpu.cpu_mark_single) if cpu and cpu.cpu_mark_single else None
    gpu_score = None
    if gpu:
        is_apple = bool(cpu and cpu.manufacturer and cpu.manufacturer.lower() == "apple")
        gpu_score = compute_gpu_score(
            gpu_mark=float(gpu.gpu_mark) if gpu.gpu_mark else None,
            metal_score=float(gpu.metal_score) if gpu.metal_score else None,
            is_apple=is_apple,
        )

    listing.score_cpu_multi = cpu_multi
    listing.score_cpu_single = cpu_single
    listing.score_gpu = gpu_score

    perf_per_watt = None
    if cpu and cpu.tdp_w and cpu.tdp_w > 0 and cpu_multi:
        perf_per_watt = cpu_multi / cpu.tdp_w
    listing.perf_per_watt = perf_per_watt

    default_profile = await get_default_profile(session)
    if default_profile:
        metrics = ListingMetrics(
            cpu_mark_multi=cpu_multi or 0,
            cpu_mark_single=cpu_single or 0,
            gpu_score=gpu_score or 0,
            perf_per_watt=perf_per_watt or 0,
            ram_capacity=float(listing.ram_gb or 0),
        )
        listing.score_composite = compute_composite_score(default_profile.weights_json, metrics)
        if not listing.active_profile_id:
            listing.active_profile_id = default_profile.id

    listing.dollar_per_cpu_mark = (
        dollar_per_metric(listing.adjusted_price_usd, cpu_multi) if cpu_multi else None
    )
    listing.dollar_per_single_mark = (
        dollar_per_metric(listing.adjusted_price_usd, cpu_single) if cpu_single else None
    )

    # Calculate all CPU performance metrics (base and adjusted)
    if cpu:
        metrics = calculate_cpu_performance_metrics(listing)
        for key, value in metrics.items():
            setattr(listing, key, value)

    await session.flush()
    logger.info(
        "listing.metrics.computed",
        listing_id=listing.id,
        adjusted_price=float(listing.adjusted_price_usd or 0.0),
        score_composite=
        float(listing.score_composite or 0.0)
        if listing.score_composite is not None
        else None,
        ruleset_id=listing.ruleset_id,
    )


def build_component_inputs(listing: Listing) -> Iterable[ComponentValuationInput]:
    if listing.ram_gb:
        yield ComponentValuationInput(
            component_type=ComponentType.RAM,
            quantity=float(listing.ram_gb),
            label=f"RAM {listing.ram_gb}GB",
        )
    if listing.primary_storage_gb:
        yield ComponentValuationInput(
            component_type=storage_component_type(listing.primary_storage_type),
            quantity=float(listing.primary_storage_gb),
            label=f"Primary Storage {listing.primary_storage_gb}GB",
        )
    if listing.secondary_storage_gb:
        yield ComponentValuationInput(
            component_type=storage_component_type(listing.secondary_storage_type),
            quantity=float(listing.secondary_storage_gb),
            label=f"Secondary Storage {listing.secondary_storage_gb}GB",
        )
    if listing.os_license:
        yield ComponentValuationInput(
            component_type=ComponentType.OS_LICENSE,
            quantity=1,
            label=f"OS License {listing.os_license}",
        )
    for component in listing.components:
        component_type = _coerce_component_type(component.component_type)
        quantity = float(component.quantity or 1)
        yield ComponentValuationInput(
            component_type=component_type,
            quantity=quantity,
            label=component.name or component_type.value,
        )


def storage_component_type(storage_type: str | None) -> ComponentType:
    if not storage_type:
        return ComponentType.SSD
    lowered = storage_type.lower()
    if "hdd" in lowered or "hard" in lowered:
        return ComponentType.HDD
    return ComponentType.SSD


async def get_default_profile(session: AsyncSession) -> Profile | None:
    result = await session.execute(select(Profile).where(Profile.is_default == True))  # noqa: E712
    profile = result.scalars().first()
    if profile:
        return profile
    result = await session.execute(select(Profile).order_by(Profile.id))
    return result.scalars().first()


async def create_listing(session: AsyncSession, payload: dict) -> Listing:
    # Map "attributes" to "attributes_json" for SQLAlchemy model
    if "attributes" in payload:
        payload["attributes_json"] = payload.pop("attributes")
    payload = _normalize_listing_payload(payload)
    await _prepare_component_relationships(session, payload)
    listing = Listing(**payload)
    session.add(listing)
    await session.flush()
    logger.info(
        "listing.created",
        listing_id=listing.id,
        title=listing.title,
        price=listing.price_usd,
        ruleset_id=listing.ruleset_id,
    )
    return listing


async def update_listing(session: AsyncSession, listing: Listing, payload: dict) -> Listing:
    payload = _normalize_listing_payload(payload)
    await _prepare_component_relationships(session, payload, listing=listing)
    for field, value in payload.items():
        setattr(listing, field, value)
    await session.flush()
    logger.info(
        "listing.updated",
        listing_id=listing.id,
        updated_fields=list(payload.keys()),
        ruleset_id=listing.ruleset_id,
    )
    return listing


async def sync_listing_components(
    session: AsyncSession,
    listing: Listing,
    components_payload: list[dict] | None,
) -> None:
    """Replace listing components using explicit SQL to avoid lazy relationship access."""
    if components_payload is None:
        return

    await session.execute(delete(ListingComponent).where(ListingComponent.listing_id == listing.id))
    await session.flush()

    for component in components_payload:
        payload = dict(component)
        component_type = payload.get("component_type")
        if not component_type:
            fallback = getattr(ComponentType, "OTHER", None)
            component_type = fallback.value if fallback else "misc"
        session.add(
            ListingComponent(
                listing_id=listing.id,
                rule_id=payload.get("rule_id"),
                component_type=component_type,
                name=payload.get("name"),
                quantity=payload.get("quantity", 1),
                metadata_json=payload.get("metadata_json"),
                adjustment_value_usd=payload.get("adjustment_value_usd"),
            ),
        )
    await session.flush()
    logger.info(
        "listing.components.synced",
        listing_id=listing.id,
        component_count=len(components_payload),
    )


async def partial_update_listing(
    session: AsyncSession,
    listing: Listing,
    fields: dict[str, Any] | None = None,
    attributes: dict[str, Any] | None = None,
    *,
    run_metrics: bool = True,
) -> Listing:
    fields = fields or {}
    attributes = attributes or {}
    fields = _normalize_listing_payload(dict(fields))
    await _prepare_component_relationships(session, fields, listing=listing)

    for field, value in fields.items():
        if field in MUTABLE_LISTING_FIELDS:
            setattr(listing, field, value)

    if attributes:
        merged = dict(listing.attributes_json or {})
        for key, value in attributes.items():
            if value is None:
                merged.pop(key, None)
            else:
                merged[key] = value
        listing.attributes_json = merged

    logger.info(
        "listing.partial_update",
        listing_id=listing.id,
        updated_fields=list(fields.keys()),
        attribute_keys=list(attributes.keys()),
        run_metrics=run_metrics,
    )

    await session.flush()

    if run_metrics:
        await apply_listing_metrics(session, listing)
        await session.refresh(listing)
    return listing


def _normalize_disabled_rulesets(values: Iterable[Any] | None) -> list[int]:
    if not values:
        return []
    normalized: list[int] = []
    seen: set[int] = set()
    for value in values:
        try:
            ruleset_id = int(value)
        except (TypeError, ValueError):
            continue
        if ruleset_id < 0 or ruleset_id in seen:
            continue
        seen.add(ruleset_id)
        normalized.append(ruleset_id)
    return normalized


async def update_listing_overrides(
    session: AsyncSession,
    listing: Listing,
    *,
    mode: str,
    ruleset_id: int | None,
    disabled_rulesets: Iterable[Any] | None = None,
) -> Listing:
    """Update listing valuation overrides (static assignment and disabled dynamic rulesets)."""
    normalized_disabled = _normalize_disabled_rulesets(disabled_rulesets)

    if mode == "auto":
        listing.ruleset_id = None
    elif mode == "static":
        if ruleset_id is None:
            raise ValueError("Static mode requires a ruleset_id")
        listing.ruleset_id = ruleset_id
    else:
        raise ValueError("Unsupported override mode")

    attributes = dict(listing.attributes_json or {})
    attributes[VALUATION_DISABLED_RULESETS_KEY] = normalized_disabled
    listing.attributes_json = attributes

    await session.flush()
    return listing


async def bulk_update_listings(
    session: AsyncSession,
    listing_ids: list[int],
    fields: dict[str, Any] | None = None,
    attributes: dict[str, Any] | None = None,
) -> list[Listing]:
    if not listing_ids:
        return []

    result = await session.execute(select(Listing).where(Listing.id.in_(listing_ids)))
    listings = result.scalars().unique().all()
    if not listings:
        return []

    for listing in listings:
        await partial_update_listing(
            session,
            listing,
            fields,
            attributes,
            run_metrics=False,
        )

    await session.flush()
    for listing in listings:
        await apply_listing_metrics(session, listing)
    await session.flush()
    for listing in listings:
        await session.refresh(listing)
    return listings


def _coerce_component_type(value: Any) -> ComponentType:
    if isinstance(value, ComponentType):
        return value
    if isinstance(value, str) and value in ComponentType._value2member_map_:
        return ComponentType(value)
    return ComponentType.MISC


def _coerce_component_metric(value: Any) -> ComponentMetric:
    if isinstance(value, ComponentMetric):
        return value
    if isinstance(value, str) and value in ComponentMetric._value2member_map_:
        return ComponentMetric(value)
    return ComponentMetric.FLAT


def _coerce_condition(value: Any) -> Condition:
    if isinstance(value, Condition):
        return value
    if isinstance(value, str) and value in Condition._value2member_map_:
        return Condition(value)
    return Condition.USED


# ============================================================================
# Performance Metrics Calculation (New)
# ============================================================================

def calculate_cpu_performance_metrics(listing: Listing) -> dict[str, float]:
    """Calculate all CPU-based performance metrics for a listing.

    Adjusted metrics use component-based adjustment delta:
    adjusted_base_price = base_price + total_adjustment

    Where total_adjustment comes from valuation_breakdown['total_adjustment']
    (negative values decrease price, positive values increase price)

    Returns
    -------
        Dictionary with metric keys and calculated values.
        Empty dict if CPU not assigned or missing benchmark data.

    """
    if not listing.cpu:
        return {}

    cpu = listing.cpu
    base_price = float(listing.price_usd)

    # Extract adjustment delta from valuation breakdown
    total_adjustment = 0.0
    if listing.valuation_breakdown:
        total_adjustment = float(listing.valuation_breakdown.get('total_adjustment', 0.0))

    adjusted_base_price = base_price - total_adjustment

    metrics = {}

    # Single-thread metrics
    if cpu.cpu_mark_single and cpu.cpu_mark_single > 0:
        metrics['dollar_per_cpu_mark_single'] = base_price / cpu.cpu_mark_single
        metrics['dollar_per_cpu_mark_single_adjusted'] = adjusted_base_price / cpu.cpu_mark_single

    # Multi-thread metrics
    if cpu.cpu_mark_multi and cpu.cpu_mark_multi > 0:
        metrics['dollar_per_cpu_mark_multi'] = base_price / cpu.cpu_mark_multi
        metrics['dollar_per_cpu_mark_multi_adjusted'] = adjusted_base_price / cpu.cpu_mark_multi

    return metrics


async def update_listing_metrics(
    session: AsyncSession,
    listing_id: int,
) -> Listing:
    """Recalculate and persist all performance metrics for a listing.

    Args:
    ----
        session: Database session
        listing_id: ID of listing to update

    Returns:
    -------
        Updated listing with recalculated metrics

    Raises:
    ------
        ValueError: If listing not found
    
    """
    from sqlalchemy.orm import joinedload

    # Fetch with CPU relationship
    stmt = select(Listing).where(Listing.id == listing_id).options(joinedload(Listing.cpu))
    result = await session.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    # Calculate metrics
    metrics = calculate_cpu_performance_metrics(listing)

    # Update listing
    for key, value in metrics.items():
        setattr(listing, key, value)

    await session.commit()
    await session.refresh(listing)
    return listing


async def bulk_update_listing_metrics(
    session: AsyncSession,
    listing_ids: list[int] | None = None,
) -> int:
    """Recalculate metrics for multiple listings.

    Args:
    ----
        session: Database session
        listing_ids: List of IDs to update. If None, updates all listings.

    Returns:
    -------
        Count of listings updated

    """
    from sqlalchemy.orm import joinedload

    stmt = select(Listing).options(joinedload(Listing.cpu))
    if listing_ids:
        stmt = stmt.where(Listing.id.in_(listing_ids))

    result = await session.execute(stmt)
    listings = result.scalars().all()

    updated_count = 0
    for listing in listings:
        metrics = calculate_cpu_performance_metrics(listing)
        for key, value in metrics.items():
            setattr(listing, key, value)
        updated_count += 1

    await session.commit()
    return updated_count


async def delete_listing(
    session: AsyncSession,
    listing_id: int,
) -> None:
    """Delete listing and cascade related records.

    Cascades delete to:
    - ListingComponent records
    - ListingScoreSnapshot records
    - RawPayload records
    - EntityFieldValue records (custom fields) via DB FK cascade

    Args:
    ----
        session: Database session
        listing_id: ID of listing to delete

    Raises:
    ------
        ValueError: Listing not found
    """
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    logger.info(
        "listing.delete",
        listing_id=listing_id,
        title=listing.title,
    )

    await session.delete(listing)
    await session.commit()

    logger.info(
        "listing.deleted",
        listing_id=listing_id,
    )


# ============================================================================
# URL Ingestion Integration (Phase 3 - Task ID-020)
# ============================================================================


async def upsert_from_url(
    session: AsyncSession,
    normalized: NormalizedListingSchema,
    dedupe_result: DeduplicationResult,
) -> Listing:
    """Upsert listing from URL ingestion.

    If dedup match found, updates existing listing with new data.
    If new listing, creates listing with URL ingestion metadata.

    This method integrates URL ingestion with existing ListingsService,
    maintaining backward compatibility with Excel import flow.

    Args:
    ----
        session: Database session (caller controls transaction)
        normalized: Normalized listing data from adapter
        dedupe_result: Deduplication result with match info

    Returns:
    -------
        Created or updated Listing instance

    Raises:
    ------
        ValueError: If normalized data invalid or condition cannot be mapped

    Example:
    -------
        >>> from dealbrain_core.schemas.ingestion import NormalizedListingSchema
        >>> from dealbrain_api.services.ingestion import DeduplicationResult
        >>>
        >>> normalized = NormalizedListingSchema(
        ...     title="Gaming PC",
        ...     price=Decimal("599.99"),
        ...     currency="USD",
        ...     condition="new",
        ...     marketplace="ebay",
        ...     vendor_item_id="123456789012",
        ...     provenance="ebay_api",
        ...     dedup_hash="abc123...",
        ... )
        >>> dedupe_result = DeduplicationResult(
        ...     exists=False,
        ...     existing_listing=None,
        ...     is_exact_match=False,
        ...     confidence=0.0,
        ...     dedup_hash="abc123...",
        ... )
        >>> listing = await upsert_from_url(session, normalized, dedupe_result)
    
    """
    from decimal import Decimal

    from dealbrain_core.enums import Condition
    from dealbrain_core.schemas.ingestion import NormalizedListingSchema

    # Import IngestionEventService locally to avoid circular imports
    from .ingestion import IngestionEventService

    # Validate input
    if not isinstance(normalized, NormalizedListingSchema):
        raise ValueError("normalized must be a NormalizedListingSchema instance")

    # Initialize event service for price change tracking
    event_service = IngestionEventService()

    # Map condition string to enum
    condition_map = {
        "new": Condition.NEW,
        "refurb": Condition.REFURB,
        "used": Condition.USED,
    }
    condition_enum = condition_map.get(normalized.condition.lower(), Condition.USED)

    if dedupe_result.exists and dedupe_result.existing_listing:
        # UPDATE PATH: Update existing listing
        existing = dedupe_result.existing_listing

        # Check if price changed for event emission
        old_price = Decimal(str(existing.price_usd))
        new_price = normalized.price

        # Update mutable fields
        existing.price_usd = float(new_price)
        existing.condition = condition_enum.value

        # Update images if provided
        if normalized.images:
            # Store images as JSON array (need to check model schema)
            # For now, store in attributes_json as the Listing model doesn't have images field
            attrs = dict(existing.attributes_json or {})
            attrs["images"] = normalized.images
            existing.attributes_json = attrs

        # Update timestamps
        existing.last_seen_at = datetime.utcnow()

        await session.flush()

        # Emit price.changed event if threshold met
        if old_price != new_price:
            emitted = event_service.check_and_emit_price_change(
                existing, old_price, new_price,
            )
            logger.debug(
                "Price change event emission",
                extra={
                    "listing_id": existing.id,
                    "old_price": float(old_price),
                    "new_price": float(new_price),
                    "emitted": emitted,
                },
            )

        return existing

    # CREATE PATH: Create new listing
    # Get dedup hash from DeduplicationResult (generated by DeduplicationService)
    dedup_hash = dedupe_result.dedup_hash

    listing = Listing(
        title=normalized.title,
        price_usd=float(normalized.price),
        condition=condition_enum.value,
        marketplace=normalized.marketplace,
        vendor_item_id=normalized.vendor_item_id,
        seller=normalized.seller,
        dedup_hash=dedup_hash,
        last_seen_at=datetime.utcnow(),
    )

    # Store images in attributes_json if provided
    if normalized.images:
        listing.attributes_json = {"images": normalized.images}

    # Store provenance if available in normalized data
    # Note: provenance is not in NormalizedListingSchema but should be tracked
    # It will be set by the caller (IngestionService)

    session.add(listing)
    await session.flush()  # Get ID without committing

    # Apply valuation rules and calculate metrics
    await apply_listing_metrics(session, listing)

    # Emit listing.created event
    # Note: We don't have provenance or quality in this method
    # Those should be emitted by the caller (IngestionService)
    logger.info(
        "Created new listing from URL ingestion",
        extra={
            "listing_id": listing.id,
            "title": listing.title,
            "price": listing.price_usd,
            "marketplace": listing.marketplace,
        },
    )

    return listing


# ============================================================================
# Cursor-based Pagination (PERF-003)
# ============================================================================


def encode_cursor(listing_id: int, sort_value: Any) -> str:
    """Encode cursor for keyset pagination.

    Args:
        listing_id: Listing ID
        sort_value: Value of the sort column (converted to string for serialization)

    Returns:
        Base64-encoded cursor string
    """
    cursor_data = {
        "id": listing_id,
        "sort_value": str(sort_value) if sort_value is not None else None,
    }
    cursor_json = json.dumps(cursor_data)
    cursor_bytes = cursor_json.encode("utf-8")
    return base64.urlsafe_b64encode(cursor_bytes).decode("utf-8")


def decode_cursor(cursor: str) -> tuple[int, str | None]:
    """Decode cursor for keyset pagination.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Tuple of (listing_id, sort_value)

    Raises:
        ValueError: If cursor is invalid
    """
    try:
        cursor_bytes = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        cursor_json = cursor_bytes.decode("utf-8")
        cursor_data = json.loads(cursor_json)
        return cursor_data["id"], cursor_data.get("sort_value")
    except Exception as exc:
        raise ValueError(f"Invalid cursor format: {exc}") from exc


async def get_paginated_listings(
    session: AsyncSession,
    *,
    limit: int = 50,
    cursor: str | None = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    form_factor: str | None = None,
    manufacturer: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> dict[str, Any]:
    """Get paginated listings using cursor-based (keyset) pagination.

    Implements high-performance cursor-based pagination with:
    - Composite key (sort_column, id) for stable pagination
    - Base64-encoded cursors to prevent manipulation
    - Cached total count (5 minutes TTL)
    - Support for dynamic sorting and filtering

    Args:
        session: Database session
        limit: Number of items per page (1-500, default 50)
        cursor: Pagination cursor from previous response
        sort_by: Column to sort by (default "updated_at")
        sort_order: Sort direction ("asc" or "desc", default "desc")
        form_factor: Filter by form factor
        manufacturer: Filter by manufacturer
        min_price: Filter by minimum price
        max_price: Filter by maximum price

    Returns:
        Dictionary with:
        - items: List of Listing objects
        - total: Total count (cached)
        - limit: Requested limit
        - next_cursor: Cursor for next page (None if last page)
        - has_next: Boolean indicating if more pages exist

    Raises:
        ValueError: If sort_by contains invalid characters or cursor is malformed
    """
    # Validate sort_by to prevent SQL injection
    if not sort_by.replace("_", "").isalpha():
        raise ValueError(f"Invalid sort column: {sort_by}")

    # Validate limit
    if limit < 1 or limit > 500:
        raise ValueError("Limit must be between 1 and 500")

    # Get sortable column
    sort_column = getattr(Listing, sort_by, None)
    if sort_column is None:
        raise ValueError(f"Invalid sort column: {sort_by}")

    # Build base query with eager loading
    stmt = (
        select(Listing)
        .options(
            selectinload(Listing.cpu),
            selectinload(Listing.gpu),
            selectinload(Listing.ports_profile),
        )
    )

    # Apply filters
    filters = []
    if form_factor:
        filters.append(Listing.form_factor == form_factor)
    if manufacturer:
        filters.append(Listing.manufacturer == manufacturer)
    if min_price is not None:
        filters.append(Listing.price_usd >= min_price)
    if max_price is not None:
        filters.append(Listing.price_usd <= max_price)

    if filters:
        stmt = stmt.where(and_(*filters))

    # Apply cursor-based filtering (keyset pagination)
    if cursor:
        cursor_id, cursor_sort_value = decode_cursor(cursor)

        # Build keyset condition based on sort order
        if sort_order.lower() == "desc":
            # For DESC: (sort_col < cursor_value) OR (sort_col = cursor_value AND id < cursor_id)
            if cursor_sort_value is not None:
                # Convert cursor_sort_value back to appropriate type
                if isinstance(sort_column.type, type(Listing.id.type)):  # Integer column
                    cursor_sort_value = int(cursor_sort_value)
                elif hasattr(sort_column.type, 'python_type'):
                    # For datetime columns
                    if sort_column.type.python_type == datetime:
                        cursor_sort_value = datetime.fromisoformat(cursor_sort_value)
                    else:
                        cursor_sort_value = float(cursor_sort_value)

                stmt = stmt.where(
                    or_(
                        sort_column < cursor_sort_value,
                        and_(sort_column == cursor_sort_value, Listing.id < cursor_id)
                    )
                )
            else:
                # If sort_value is NULL, only filter by ID
                stmt = stmt.where(Listing.id < cursor_id)
        else:
            # For ASC: (sort_col > cursor_value) OR (sort_col = cursor_value AND id > cursor_id)
            if cursor_sort_value is not None:
                # Convert cursor_sort_value back to appropriate type
                if isinstance(sort_column.type, type(Listing.id.type)):  # Integer column
                    cursor_sort_value = int(cursor_sort_value)
                elif hasattr(sort_column.type, 'python_type'):
                    # For datetime columns
                    if sort_column.type.python_type == datetime:
                        cursor_sort_value = datetime.fromisoformat(cursor_sort_value)
                    else:
                        cursor_sort_value = float(cursor_sort_value)

                stmt = stmt.where(
                    or_(
                        sort_column > cursor_sort_value,
                        and_(sort_column == cursor_sort_value, Listing.id > cursor_id)
                    )
                )
            else:
                # If sort_value is NULL, only filter by ID
                stmt = stmt.where(Listing.id > cursor_id)

    # Apply sorting (composite key: sort_column, id)
    if sort_order.lower() == "desc":
        stmt = stmt.order_by(desc(sort_column), desc(Listing.id))
    else:
        stmt = stmt.order_by(asc(sort_column), asc(Listing.id))

    # Fetch limit+1 to determine has_next (without separate count query per page)
    stmt = stmt.limit(limit + 1)

    result = await session.execute(stmt)
    listings = list(result.scalars().unique().all())

    # Determine if there's a next page
    has_next = len(listings) > limit
    if has_next:
        listings = listings[:limit]  # Remove the extra item

    # Generate next_cursor from last item
    next_cursor = None
    if has_next and listings:
        last_listing = listings[-1]
        last_sort_value = getattr(last_listing, sort_by)
        # Handle datetime serialization for cursor
        if isinstance(last_sort_value, datetime):
            last_sort_value = last_sort_value.isoformat()
        next_cursor = encode_cursor(last_listing.id, last_sort_value)

    # Get cached total count
    cache_key = "listings:total_count"
    cached_total = await cache_manager.get(cache_key)

    if cached_total is not None:
        total = int(cached_total)
    else:
        # Calculate total and cache it
        count_stmt = select(func.count()).select_from(Listing)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Cache for 5 minutes
        await cache_manager.set(cache_key, str(total), ttl=timedelta(minutes=5))

    return {
        "items": listings,
        "total": total,
        "limit": limit,
        "next_cursor": next_cursor,
        "has_next": has_next,
    }
