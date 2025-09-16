from __future__ import annotations

from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.enums import ComponentType
from dealbrain_core.gpu import compute_gpu_score
from dealbrain_core.scoring import ListingMetrics, compute_composite_score, dollar_per_metric
from dealbrain_core.valuation import ComponentValuationInput, ValuationRuleData, compute_adjusted_price

from ..models import Cpu, Gpu, Listing, ListingComponent, Profile, ValuationRule


async def apply_listing_metrics(session: AsyncSession, listing: Listing) -> None:
    rules = await session.execute(select(ValuationRule))
    rule_data = [
        ValuationRuleData(
            component_type=row.component_type,
            metric=row.metric,
            unit_value_usd=float(row.unit_value_usd or 0),
            condition_new=row.condition_new,
            condition_refurb=row.condition_refurb,
            condition_used=row.condition_used,
        )
        for row in rules.scalars().all()
    ]

    components: list[ComponentValuationInput] = list(build_component_inputs(listing))
    valuation = compute_adjusted_price(
        listing_price_usd=float(listing.price_usd or 0),
        condition=listing.condition,
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

    if listing.cpu_id:
        listing.cpu = listing.cpu or await session.get(Cpu, listing.cpu_id)
    if listing.gpu_id:
        listing.gpu = listing.gpu or await session.get(Gpu, listing.gpu_id)

    cpu_multi = float(listing.cpu.cpu_mark_multi) if listing.cpu and listing.cpu.cpu_mark_multi else None
    cpu_single = float(listing.cpu.cpu_mark_single) if listing.cpu and listing.cpu.cpu_mark_single else None
    gpu_score = None
    if listing.gpu:
        is_apple = bool(listing.cpu and listing.cpu.manufacturer and listing.cpu.manufacturer.lower() == "apple")
        gpu_score = compute_gpu_score(
            gpu_mark=float(listing.gpu.gpu_mark) if listing.gpu.gpu_mark else None,
            metal_score=float(listing.gpu.metal_score) if listing.gpu.metal_score else None,
            is_apple=is_apple,
        )

    listing.score_cpu_multi = cpu_multi
    listing.score_cpu_single = cpu_single
    listing.score_gpu = gpu_score

    perf_per_watt = None
    if listing.cpu and listing.cpu.tdp_w and listing.cpu.tdp_w > 0 and cpu_multi:
        perf_per_watt = cpu_multi / listing.cpu.tdp_w
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
        component_type = component.component_type
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
    session: AsyncSession, listing: Listing, components_payload: list[dict] | None
) -> None:
    if components_payload is None:
        return
    listing.components.clear()
    await session.flush()
    for component in components_payload:
        component_type = component.get("component_type")
        listing.components.append(
            ListingComponent(
                component_type=ComponentType(component_type) if component_type else ComponentType.MISC,
                name=component.get("name"),
                quantity=component.get("quantity") or 1,
                metadata_json=component.get("metadata_json"),
                adjustment_value_usd=component.get("adjustment_value_usd"),
                rule_id=component.get("rule_id"),
            )
        )
    await session.flush()

