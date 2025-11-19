"""Shared helpers for RAM specification and storage profile catalog management."""

from __future__ import annotations

from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.enums import RamGeneration, StorageMedium

from ..models import RamSpec, StorageProfile


def normalize_int(value: Any) -> int | None:
    """Convert arbitrary value to non-negative integer or ``None``."""
    if value in (None, "", [], {}):
        return None
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return None
    return numeric if numeric >= 0 else None


def normalize_str(value: Any) -> str | None:
    """Coerce arbitrary value to trimmed string or ``None``."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_ram_generation(value: Any) -> RamGeneration:
    """Resolve various user inputs into a canonical ``RamGeneration``."""
    if isinstance(value, RamGeneration):
        return value
    normalized = (normalize_str(value) or "").lower()
    if not normalized:
        return RamGeneration.UNKNOWN
    for generation in RamGeneration:
        if generation.value == normalized or generation.name.lower() == normalized:
            return generation
    if normalized in {"ddr", "ddr4/3200"}:
        return RamGeneration.DDR4
    if normalized.startswith("ddr3"):
        return RamGeneration.DDR3
    if normalized.startswith("ddr4"):
        return RamGeneration.DDR4
    if normalized.startswith("ddr5"):
        return RamGeneration.DDR5
    if "lpddr5" in normalized:
        return RamGeneration.LPDDR5
    if "lpddr4" in normalized:
        return RamGeneration.LPDDR4
    return RamGeneration.UNKNOWN


def format_ram_label(
    generation: RamGeneration,
    speed_mhz: int | None,
    total_capacity_gb: int | None,
    module_count: int | None,
    capacity_per_module_gb: int | None,
) -> str | None:
    """Construct a human-readable RAM label."""
    parts: list[str] = []
    if generation and generation != RamGeneration.UNKNOWN:
        parts.append(generation.value.upper())
    if speed_mhz:
        parts.append(f"{speed_mhz}MHz")
    if total_capacity_gb:
        capacity_label = f"{total_capacity_gb}GB"
        if module_count and capacity_per_module_gb:
            capacity_label += f" ({module_count}x{capacity_per_module_gb}GB)"
        parts.append(capacity_label)
    if not parts:
        return None
    return " ".join(parts)


def normalize_ram_spec_payload(
    data: dict[str, Any] | None,
    *,
    fallback_total_gb: int | None = None,
    fallback_generation: RamGeneration | None = None,
    fallback_speed: int | None = None,
) -> dict[str, Any] | None:
    """Normalize raw RAM spec payload into ORM-ready fields."""
    if not data:
        data = {}

    generation = normalize_ram_generation(
        data.get("ddr_generation")
        or data.get("ram_type")
        or data.get("generation")
        or fallback_generation
    )
    speed_mhz = normalize_int(data.get("speed_mhz") or data.get("speed") or fallback_speed)
    module_count = normalize_int(data.get("module_count") or data.get("modules"))
    capacity_per_module = normalize_int(
        data.get("capacity_per_module_gb")
        or data.get("module_capacity_gb")
        or data.get("capacity_per_module")
    )
    total_capacity = normalize_int(
        data.get("total_capacity_gb")
        or data.get("total_gb")
        or data.get("ram_gb")
        or fallback_total_gb
    )
    if total_capacity is None and capacity_per_module and module_count:
        total_capacity = capacity_per_module * module_count

    if total_capacity is None:
        return None

    label = normalize_str(data.get("label")) or format_ram_label(
        generation,
        speed_mhz,
        total_capacity,
        module_count,
        capacity_per_module,
    )

    notes = normalize_str(data.get("notes"))
    attributes = data.get("attributes") or data.get("attributes_json")
    attributes_json = attributes if isinstance(attributes, dict) else {}

    return {
        "label": label,
        "ddr_generation": generation,
        "speed_mhz": speed_mhz,
        "module_count": module_count,
        "capacity_per_module_gb": capacity_per_module,
        "total_capacity_gb": total_capacity,
        "attributes_json": attributes_json,
        "notes": notes,
    }


async def get_or_create_ram_spec(session: AsyncSession, spec_data: dict[str, Any]) -> RamSpec:
    """Return existing RAM spec matching payload or create a new one."""
    normalized = normalize_ram_spec_payload(
        spec_data, fallback_total_gb=spec_data.get("total_capacity_gb")
    )
    if not normalized:
        raise ValueError("Unable to determine RAM specification from payload")

    conditions = [
        RamSpec.ddr_generation == normalized["ddr_generation"],
        (
            (RamSpec.speed_mhz == normalized["speed_mhz"])
            if normalized["speed_mhz"] is not None
            else RamSpec.speed_mhz.is_(None)
        ),
        (
            (RamSpec.module_count == normalized["module_count"])
            if normalized["module_count"] is not None
            else RamSpec.module_count.is_(None)
        ),
        (
            (RamSpec.capacity_per_module_gb == normalized["capacity_per_module_gb"])
            if normalized["capacity_per_module_gb"] is not None
            else RamSpec.capacity_per_module_gb.is_(None)
        ),
        (
            (RamSpec.total_capacity_gb == normalized["total_capacity_gb"])
            if normalized["total_capacity_gb"] is not None
            else RamSpec.total_capacity_gb.is_(None)
        ),
    ]

    existing = await session.scalar(select(RamSpec).where(and_(*conditions)))
    if existing:
        return existing

    payload = dict(normalized)
    label = payload.pop("label", None)
    attributes_json = payload.pop("attributes_json", {})
    notes = payload.pop("notes", None)

    ram_spec = RamSpec(
        label=label
        or format_ram_label(
            payload["ddr_generation"],
            payload.get("speed_mhz"),
            payload.get("total_capacity_gb"),
            payload.get("module_count"),
            payload.get("capacity_per_module_gb"),
        ),
        attributes_json=attributes_json or {},
        notes=notes,
        **payload,
    )
    session.add(ram_spec)
    await session.flush()
    await session.refresh(ram_spec)
    return ram_spec


def normalize_storage_medium(value: Any) -> StorageMedium:
    """Map free-form storage descriptors to canonical medium enum."""
    if isinstance(value, StorageMedium):
        return value
    normalized = (normalize_str(value) or "").lower()
    if not normalized:
        return StorageMedium.UNKNOWN
    mapping = {
        "nvme": StorageMedium.NVME,
        "ssd": StorageMedium.SATA_SSD,
        "sata": StorageMedium.SATA_SSD,
        "sata ssd": StorageMedium.SATA_SSD,
        "hard drive": StorageMedium.HDD,
        "hard disk": StorageMedium.HDD,
        "hdd": StorageMedium.HDD,
        "hybrid": StorageMedium.HYBRID,
        "emmc": StorageMedium.EMMC,
        "ufs": StorageMedium.UFS,
        "flash": StorageMedium.EMMC,
        "pcie": StorageMedium.NVME,
    }
    for key, medium in mapping.items():
        if key in normalized:
            return medium
    return StorageMedium.UNKNOWN


def format_storage_label(
    medium: StorageMedium,
    capacity_gb: int | None,
    interface: str | None,
    form_factor: str | None,
) -> str | None:
    """Construct a concise storage profile label."""
    parts: list[str] = []
    if medium and medium != StorageMedium.UNKNOWN:
        parts.append(medium.value.replace("_", " ").upper())
    if interface:
        parts.append(interface)
    if capacity_gb:
        parts.append(f"{capacity_gb}GB")
    if form_factor:
        parts.append(form_factor)
    if not parts:
        return None
    return " · ".join(parts)


def normalize_storage_profile_payload(
    data: dict[str, Any] | None,
    *,
    fallback_capacity_gb: int | None = None,
    fallback_type: Any | None = None,
) -> dict[str, Any] | None:
    """Normalize raw storage profile payload into ORM-ready fields."""
    if not data:
        data = {}

    medium = normalize_storage_medium(
        data.get("medium") or data.get("storage_type") or fallback_type
    )
    interface = normalize_str(data.get("interface") or data.get("bus"))
    form_factor = normalize_str(data.get("form_factor") or data.get("size"))
    capacity_gb = normalize_int(
        data.get("capacity_gb")
        or data.get("capacity")
        or data.get("storage_gb")
        or fallback_capacity_gb
    )
    performance_tier = normalize_str(data.get("performance_tier") or data.get("tier"))
    if capacity_gb is None:
        return None

    attributes = data.get("attributes") or data.get("attributes_json")
    attributes_json = attributes if isinstance(attributes, dict) else {}
    label = normalize_str(data.get("label")) or format_storage_label(
        medium, capacity_gb, interface, form_factor
    )
    notes = normalize_str(data.get("notes"))

    return {
        "label": label,
        "medium": medium,
        "interface": interface,
        "form_factor": form_factor,
        "capacity_gb": capacity_gb,
        "performance_tier": performance_tier,
        "attributes_json": attributes_json,
        "notes": notes,
    }


async def get_or_create_storage_profile(
    session: AsyncSession, profile_data: dict[str, Any]
) -> StorageProfile:
    """Return existing storage profile matching payload or create a new one."""
    normalized = normalize_storage_profile_payload(
        profile_data, fallback_capacity_gb=profile_data.get("capacity_gb")
    )
    if not normalized:
        raise ValueError("Unable to determine storage profile from payload")

    conditions = [
        StorageProfile.medium == normalized["medium"],
        (
            (StorageProfile.interface == normalized["interface"])
            if normalized["interface"] is not None
            else StorageProfile.interface.is_(None)
        ),
        (
            (StorageProfile.form_factor == normalized["form_factor"])
            if normalized["form_factor"] is not None
            else StorageProfile.form_factor.is_(None)
        ),
        (
            (StorageProfile.capacity_gb == normalized["capacity_gb"])
            if normalized["capacity_gb"] is not None
            else StorageProfile.capacity_gb.is_(None)
        ),
        (
            (StorageProfile.performance_tier == normalized["performance_tier"])
            if normalized["performance_tier"] is not None
            else StorageProfile.performance_tier.is_(None)
        ),
    ]

    existing = await session.scalar(select(StorageProfile).where(and_(*conditions)))
    if existing:
        return existing

    attributes_json = normalized.pop("attributes_json", {})
    notes = normalized.pop("notes", None)
    label = normalized.pop("label", None)
    storage_profile = StorageProfile(
        label=label
        or format_storage_label(
            normalized["medium"],
            normalized.get("capacity_gb"),
            normalized.get("interface"),
            normalized.get("form_factor"),
        ),
        attributes_json=attributes_json or {},
        notes=notes,
        **normalized,
    )
    session.add(storage_profile)
    await session.flush()
    await session.refresh(storage_profile)
    return storage_profile


def storage_medium_display(medium: StorageMedium) -> str | None:
    """Provide human-friendly medium label for UI surfaces."""
    mapping = {
        StorageMedium.NVME: "NVMe",
        StorageMedium.SATA_SSD: "SSD",
        StorageMedium.HDD: "HDD",
        StorageMedium.HYBRID: "Hybrid",
        StorageMedium.EMMC: "eMMC",
        StorageMedium.UFS: "UFS",
    }
    return mapping.get(medium, None)


__all__ = [
    "format_ram_label",
    "format_storage_label",
    "get_or_create_ram_spec",
    "get_or_create_storage_profile",
    "normalize_int",
    "normalize_ram_generation",
    "normalize_ram_spec_payload",
    "normalize_storage_medium",
    "normalize_storage_profile_payload",
    "normalize_str",
    "storage_medium_display",
]
