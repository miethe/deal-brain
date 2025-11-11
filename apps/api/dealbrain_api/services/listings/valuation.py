"""Valuation and pricing logic for listings.

This module handles valuation rule application, price adjustments,
and valuation breakdown formatting.
"""

from __future__ import annotations

from typing import Any, Iterable

from dealbrain_core.enums import ComponentMetric, ComponentType, Condition
from dealbrain_core.gpu import compute_gpu_score
from dealbrain_core.scoring import ListingMetrics, compute_composite_score, dollar_per_metric
from dealbrain_core.valuation import compute_adjusted_price
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import Cpu, Gpu, Listing, Profile
from ...telemetry import get_logger
from ..rule_evaluation import RuleEvaluationService

logger = get_logger("dealbrain.listings.valuation")
_RULE_EVALUATION_SERVICE = RuleEvaluationService()

VALUATION_DISABLED_RULESETS_KEY = "valuation_disabled_rulesets"


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
    """Apply valuation rules and calculate performance metrics for a listing.

    Requires listing.price_usd to be set. If price is None, this function
    should not be called (partial imports should skip metrics calculation).

    Args:
        session: Database session
        listing: Listing instance with price_usd set

    Raises:
        ValueError: If listing.price_usd is None
    """
    from .components import build_component_inputs
    from .crud import get_default_profile
    from .metrics import calculate_cpu_performance_metrics

    if listing.price_usd is None:
        raise ValueError(
            f"Cannot apply metrics to listing {listing.id} with price_usd=None. "
            "Metrics calculation requires a price."
        )

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

        components = list(build_component_inputs(listing))
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


def storage_component_type(storage_type: str | None) -> ComponentType:
    """Determine ComponentType from storage type string.

    Args:
        storage_type: Storage type string (e.g., "SSD", "HDD", "NVMe")

    Returns:
        ComponentType.HDD if storage type contains "hdd" or "hard", else ComponentType.SSD
    """
    if not storage_type:
        return ComponentType.SSD
    lowered = storage_type.lower()
    if "hdd" in lowered or "hard" in lowered:
        return ComponentType.HDD
    return ComponentType.SSD


def _coerce_component_type(value: Any) -> ComponentType:
    """Coerce value to ComponentType enum."""
    if isinstance(value, ComponentType):
        return value
    if isinstance(value, str) and value in ComponentType._value2member_map_:
        return ComponentType(value)
    return ComponentType.MISC


def _coerce_component_metric(value: Any) -> ComponentMetric:
    """Coerce value to ComponentMetric enum."""
    if isinstance(value, ComponentMetric):
        return value
    if isinstance(value, str) and value in ComponentMetric._value2member_map_:
        return ComponentMetric(value)
    return ComponentMetric.FLAT


def _coerce_condition(value: Any) -> Condition:
    """Coerce value to Condition enum."""
    if isinstance(value, Condition):
        return value
    if isinstance(value, str) and value in Condition._value2member_map_:
        return Condition(value)
    return Condition.USED


def _normalize_disabled_rulesets(values: Iterable[Any] | None) -> list[int]:
    """Normalize disabled rulesets list for valuation overrides."""
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
    """Update listing valuation overrides (static assignment and disabled dynamic rulesets).

    Args:
        session: Database session
        listing: Listing to update
        mode: Override mode ("auto" or "static")
        ruleset_id: Ruleset ID for static mode (required if mode="static")
        disabled_rulesets: List of disabled ruleset IDs

    Returns:
        Updated listing

    Raises:
        ValueError: If mode is "static" but ruleset_id not provided
        ValueError: If mode is unsupported
    """
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
