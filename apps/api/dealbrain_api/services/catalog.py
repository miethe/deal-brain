"""Catalog service for usage count queries and cascade validation.

This module provides methods to count listings using various catalog entities
(CPU, GPU, RamSpec, StorageProfile, PortsProfile, Profile). These counts are
used by DELETE endpoints to prevent orphaning listings.
"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Listing


async def get_cpu_usage_count(session: AsyncSession, cpu_id: int) -> int:
    """Count listings using this CPU.

    Args:
        session: Database session
        cpu_id: CPU ID to check

    Returns:
        Number of listings referencing this CPU
    """
    stmt = select(func.count(Listing.id)).where(Listing.cpu_id == cpu_id)
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_gpu_usage_count(session: AsyncSession, gpu_id: int) -> int:
    """Count listings using this GPU.

    Args:
        session: Database session
        gpu_id: GPU ID to check

    Returns:
        Number of listings referencing this GPU
    """
    stmt = select(func.count(Listing.id)).where(Listing.gpu_id == gpu_id)
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_ram_spec_usage_count(session: AsyncSession, ram_spec_id: int) -> int:
    """Count listings using this RAM specification.

    Note: RAM specs are only referenced via ram_spec_id field in Listing.

    Args:
        session: Database session
        ram_spec_id: RamSpec ID to check

    Returns:
        Number of listings referencing this RAM spec
    """
    stmt = select(func.count(Listing.id)).where(Listing.ram_spec_id == ram_spec_id)
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_storage_profile_usage_count(session: AsyncSession, storage_profile_id: int) -> int:
    """Count listings using this storage profile.

    Checks both primary and secondary storage profile references.

    Args:
        session: Database session
        storage_profile_id: StorageProfile ID to check

    Returns:
        Number of listings referencing this storage profile (primary or secondary)
    """
    stmt = select(func.count(Listing.id)).where(
        or_(
            Listing.primary_storage_profile_id == storage_profile_id,
            Listing.secondary_storage_profile_id == storage_profile_id,
        )
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_ports_profile_usage_count(session: AsyncSession, profile_id: int) -> int:
    """Count listings using this ports profile.

    Args:
        session: Database session
        profile_id: PortsProfile ID to check

    Returns:
        Number of listings referencing this ports profile
    """
    stmt = select(func.count(Listing.id)).where(Listing.ports_profile_id == profile_id)
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_scoring_profile_usage_count(session: AsyncSession, profile_id: int) -> int:
    """Count listings using this scoring profile.

    Args:
        session: Database session
        profile_id: Profile ID to check (scoring profile, not ports profile)

    Returns:
        Number of listings referencing this scoring profile
    """
    stmt = select(func.count(Listing.id)).where(Listing.active_profile_id == profile_id)
    result = await session.execute(stmt)
    return result.scalar() or 0
