from __future__ import annotations

import logging
from typing import Any, Iterable
from urllib.parse import urlparse

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.enums import ComponentMetric, ComponentType, Condition
from dealbrain_core.gpu import compute_gpu_score
from dealbrain_core.scoring import ListingMetrics, compute_composite_score, dollar_per_metric
from dealbrain_core.valuation import ComponentValuationInput, compute_adjusted_price

from ..models import Cpu, Gpu, Listing, ListingComponent, Profile
from .rule_evaluation import RuleEvaluationService

VALUATION_DISABLED_RULESETS_KEY = "valuation_disabled_rulesets"

logger = logging.getLogger(__name__)
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
            raise ValueError("Supplemental link URLs must use http:// or https:// and include a host")
        if url in seen:
            continue
        seen.add(url)
        normalized.append({"url": url, "label": label})
    return normalized


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
                }
            )

        adjustments.append(
            {
                "rule_id": result.get("rule_id"),
                "rule_name": result.get("rule_name"),
                "adjustment_usd": adjustment_value,
                "actions": actions_breakdown,
            }
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
            }
        )

    matched_rules = []
    for entry in summary.get("matched_rules", []):
        matched_rules.append(
            {
                "rule_id": entry.get("rule_id"),
                "rule_name": entry.get("rule_name"),
                "adjustment": _as_float(entry.get("adjustment")),
                "breakdown": entry.get("breakdown"),
            }
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
                logger.warning("Rule evaluation failed for listing %s: %s", listing.id, exc)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Unexpected error evaluating rules for listing %s", listing.id)

    if evaluation_summary:
        logger.debug(
            "Rule evaluation produced adjustments",
            extra={
                "listing_id": listing.id,
                "ruleset_id": evaluation_summary.get("ruleset_id"),
                "matched_rules": evaluation_summary.get("matched_rules_count"),
                "total_adjustment": evaluation_summary.get("total_adjustment"),
            },
        )
        listing.adjusted_price_usd = float(evaluation_summary.get("adjusted_price") or 0.0)
        listing.valuation_breakdown = _format_rule_evaluation_breakdown(evaluation_summary)
    else:
        logger.debug(
            "Falling back to legacy valuation path",
            extra={"listing_id": listing.id, "reason": "rule_evaluation_empty"},
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

    # New dollar per CPU Mark metrics (single and multi-thread)
    if listing.adjusted_price_usd and cpu:
        if cpu.cpu_mark_single:
            listing.dollar_per_cpu_mark_single = listing.adjusted_price_usd / cpu.cpu_mark_single
        if cpu.cpu_mark_multi:
            listing.dollar_per_cpu_mark_multi = listing.adjusted_price_usd / cpu.cpu_mark_multi

    await session.flush()


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
    # Map 'attributes' to 'attributes_json' for SQLAlchemy model
    if 'attributes' in payload:
        payload['attributes_json'] = payload.pop('attributes')
    payload = _normalize_listing_payload(payload)
    listing = Listing(**payload)
    session.add(listing)
    await session.flush()
    return listing


async def update_listing(session: AsyncSession, listing: Listing, payload: dict) -> Listing:
    payload = _normalize_listing_payload(payload)
    for field, value in payload.items():
        setattr(listing, field, value)
    await session.flush()
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
            )
        )
    await session.flush()


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

    Returns:
        Dictionary with metric keys and calculated values.
        Empty dict if CPU not assigned or missing benchmark data.
    """
    if not listing.cpu:
        return {}

    cpu = listing.cpu
    base_price = float(listing.price_usd)
    adjusted_price = float(listing.adjusted_price_usd) if listing.adjusted_price_usd else base_price

    metrics = {}

    # Single-thread metrics
    if cpu.cpu_mark_single and cpu.cpu_mark_single > 0:
        metrics['dollar_per_cpu_mark_single'] = base_price / cpu.cpu_mark_single
        metrics['dollar_per_cpu_mark_single_adjusted'] = adjusted_price / cpu.cpu_mark_single

    # Multi-thread metrics
    if cpu.cpu_mark_multi and cpu.cpu_mark_multi > 0:
        metrics['dollar_per_cpu_mark_multi'] = base_price / cpu.cpu_mark_multi
        metrics['dollar_per_cpu_mark_multi_adjusted'] = adjusted_price / cpu.cpu_mark_multi

    return metrics


async def update_listing_metrics(
    session: AsyncSession,
    listing_id: int
) -> Listing:
    """Recalculate and persist all performance metrics for a listing.

    Args:
        session: Database session
        listing_id: ID of listing to update

    Returns:
        Updated listing with recalculated metrics

    Raises:
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
    listing_ids: list[int] | None = None
) -> int:
    """Recalculate metrics for multiple listings.

    Args:
        session: Database session
        listing_ids: List of IDs to update. If None, updates all listings.

    Returns:
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
