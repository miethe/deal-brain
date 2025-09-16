"""Seed utility to load initial catalog data from the spreadsheet."""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import select

from dealbrain_core.schemas import SpreadsheetSeed

from .db import Base, get_engine, session_scope
from .importers import SpreadsheetImporter
from .models import Cpu, Gpu, Listing, ListingComponent, PortsProfile, Port, Profile, ValuationRule
from .settings import get_settings


async def apply_seed(seed: SpreadsheetSeed) -> None:
    async with session_scope() as session:
        for cpu in seed.cpus:
            existing = await session.scalar(select(Cpu).where(Cpu.name == cpu.name))
            data = cpu.model_dump(exclude_none=True)
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
            else:
                session.add(Cpu(**data))

        for gpu in seed.gpus:
            existing = await session.scalar(select(Gpu).where(Gpu.name == gpu.name))
            data = gpu.model_dump(exclude_none=True)
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
            else:
                session.add(Gpu(**data))

        for rule in seed.valuation_rules:
            existing = await session.scalar(select(ValuationRule).where(ValuationRule.name == rule.name))
            data = rule.model_dump(exclude_none=True)
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
            else:
                session.add(ValuationRule(**data))

        for profile in seed.profiles:
            existing = await session.scalar(select(Profile).where(Profile.name == profile.name))
            data = profile.model_dump(exclude_none=True)
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
            else:
                session.add(Profile(**data))

        for ports_profile in seed.ports_profiles:
            existing = await session.scalar(select(PortsProfile).where(PortsProfile.name == ports_profile.name))
            data = ports_profile.model_dump(exclude={"ports"}, exclude_none=True)
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
                existing.ports.clear()
            else:
                existing = PortsProfile(**data)
                session.add(existing)

            for port in ports_profile.ports or []:
                existing.ports.append(Port(**port.model_dump(exclude_none=True)))

        for listing in seed.listings:
            existing = await session.scalar(select(Listing).where(Listing.title == listing.title))
            data = listing.model_dump(exclude={"components"}, exclude_none=True)
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
                existing.components.clear()
            else:
                existing = Listing(**data)
                session.add(existing)

            for component in listing.components or []:
                existing.components.append(ListingComponent(**component.model_dump(exclude_none=True)))


async def seed_from_workbook(path: Path) -> None:
    importer = SpreadsheetImporter(path)
    seed, summary = importer.load()
    await apply_seed(seed)
    print(
        "Seed import complete:"
        f" {summary.cpus} CPUs, {summary.gpus} GPUs, {summary.valuation_rules} rules,"
        f" {summary.listings} listings"
    )


async def run() -> None:
    settings = get_settings()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    import_root = Path(settings.import_root)
    workbook = next(import_root.glob("*.xlsx"), None)
    if not workbook:
        raise FileNotFoundError(
            f"No Excel workbook found in {import_root}. Place your source sheet there."
        )

    await seed_from_workbook(workbook)


if __name__ == "__main__":
    asyncio.run(run())

