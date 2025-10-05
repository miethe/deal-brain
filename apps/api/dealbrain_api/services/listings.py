from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.enums import ComponentMetric, ComponentType, Condition
from dealbrain_core.gpu import compute_gpu_score
from dealbrain_core.scoring import ListingMetrics, compute_composite_score, dollar_per_metric
from dealbrain_core.valuation import ComponentValuationInput, ValuationRuleData, compute_adjusted_price

from ..models import Cpu, Gpu, Listing, ListingComponent, Profile


MUTABLE_LISTING_FIELDS: set[str] = {
    "title",
    "url",
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
}


async def apply_listing_metrics(session: AsyncSession, listing: Listing) -> None:
    # TODO: Update to use new ValuationRuleV2 system
    # For now, use empty rules list
    rule_data: list[ValuationRuleData] = []

    # Eagerly load components to avoid lazy-load in async context
    await session.refresh(listing, ['components'])

    components: list[ComponentValuationInput] = list(build_component_inputs(listing))
    valuation = compute_adjusted_price(
        listing_price_usd=float(listing.price_usd or 0),
        condition=_coerce_condition(listing.condition),
        rules=rule_data,
        components=components,
    )

    listing.adjusted_price_usd = valuation.adjusted_price_usd
    listing.valuation_breakdown = {
        "listing_price": valuation.listing_price_usd,
        "adjusted_price": valuation.adjusted_price_usd,
        "lines": [line.__dict__ for line in valuation.lines],
        "total_deductions": valuation.total_deductions,
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
    listing = Listing(**payload)
    session.add(listing)
    await session.flush()
    return listing


async def update_listing(session: AsyncSession, listing: Listing, payload: dict) -> Listing:
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
