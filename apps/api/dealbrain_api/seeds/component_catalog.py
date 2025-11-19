"""Canonical RAM spec and storage profile seed data."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.enums import RamGeneration, StorageMedium

from ..services.component_catalog import get_or_create_ram_spec, get_or_create_storage_profile

CANONICAL_RAM_SPECS: list[dict[str, object]] = [
    {
        "label": "DDR4 16GB (2x8GB) 3200MHz",
        "ddr_generation": RamGeneration.DDR4,
        "speed_mhz": 3200,
        "module_count": 2,
        "capacity_per_module_gb": 8,
        "total_capacity_gb": 16,
    },
    {
        "label": "DDR4 32GB (2x16GB) 3200MHz",
        "ddr_generation": RamGeneration.DDR4,
        "speed_mhz": 3200,
        "module_count": 2,
        "capacity_per_module_gb": 16,
        "total_capacity_gb": 32,
    },
    {
        "label": "DDR4 64GB (2x32GB) 3200MHz",
        "ddr_generation": RamGeneration.DDR4,
        "speed_mhz": 3200,
        "module_count": 2,
        "capacity_per_module_gb": 32,
        "total_capacity_gb": 64,
    },
    {
        "label": "DDR5 32GB (2x16GB) 5600MHz",
        "ddr_generation": RamGeneration.DDR5,
        "speed_mhz": 5600,
        "module_count": 2,
        "capacity_per_module_gb": 16,
        "total_capacity_gb": 32,
    },
    {
        "label": "DDR5 64GB (2x32GB) 6000MHz",
        "ddr_generation": RamGeneration.DDR5,
        "speed_mhz": 6000,
        "module_count": 2,
        "capacity_per_module_gb": 32,
        "total_capacity_gb": 64,
        "attributes": {"xmp": True},
    },
    {
        "label": "DDR5 96GB (2x48GB) 5600MHz",
        "ddr_generation": RamGeneration.DDR5,
        "speed_mhz": 5600,
        "module_count": 2,
        "capacity_per_module_gb": 48,
        "total_capacity_gb": 96,
    },
]

CANONICAL_STORAGE_PROFILES: list[dict[str, object]] = [
    {
        "label": "NVMe · PCIe 4.0 x4 · 512GB",
        "medium": StorageMedium.NVME,
        "interface": "PCIe 4.0 x4",
        "form_factor": "M.2 2280",
        "capacity_gb": 512,
        "performance_tier": "performance",
    },
    {
        "label": "NVMe · PCIe 4.0 x4 · 1024GB",
        "medium": StorageMedium.NVME,
        "interface": "PCIe 4.0 x4",
        "form_factor": "M.2 2280",
        "capacity_gb": 1024,
        "performance_tier": "performance",
    },
    {
        "label": "NVMe · PCIe 3.0 x4 · 2048GB",
        "medium": StorageMedium.NVME,
        "interface": "PCIe 3.0 x4",
        "form_factor": "M.2 2280",
        "capacity_gb": 2048,
        "performance_tier": "standard",
    },
    {
        "label": 'SATA SSD · 2.5" · 512GB',
        "medium": StorageMedium.SATA_SSD,
        "interface": "SATA III",
        "form_factor": '2.5"',
        "capacity_gb": 512,
        "performance_tier": "standard",
    },
    {
        "label": 'SATA SSD · 2.5" · 1024GB',
        "medium": StorageMedium.SATA_SSD,
        "interface": "SATA III",
        "form_factor": '2.5"',
        "capacity_gb": 1024,
        "performance_tier": "standard",
    },
    {
        "label": 'HDD · 3.5" · 2048GB',
        "medium": StorageMedium.HDD,
        "interface": "SATA III",
        "form_factor": '3.5"',
        "capacity_gb": 2048,
        "performance_tier": "archive",
    },
]


async def seed_component_catalog(session: AsyncSession) -> None:
    """Ensure canonical RAM specs and storage profiles exist."""
    for spec in CANONICAL_RAM_SPECS:
        await get_or_create_ram_spec(session, dict(spec))
    for profile in CANONICAL_STORAGE_PROFILES:
        await get_or_create_storage_profile(session, dict(profile))


__all__ = ["CANONICAL_RAM_SPECS", "CANONICAL_STORAGE_PROFILES", "seed_component_catalog"]
