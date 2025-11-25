"""Ports profile management service."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import Listing, Port, PortsProfile


async def get_or_create_ports_profile(session: AsyncSession, listing_id: int) -> PortsProfile:
    """Get existing ports profile or create new one for listing.

    Args:
        session: Database session
        listing_id: Listing ID

    Returns:
        PortsProfile instance (existing or new)

    Raises:
        ValueError: If listing not found
    """
    stmt = (
        select(Listing)
        .where(Listing.id == listing_id)
        .options(joinedload(Listing.ports_profile).joinedload(PortsProfile.ports))
    )
    result = await session.execute(stmt)
    listing = result.unique().scalar_one_or_none()

    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    if listing.ports_profile:
        return listing.ports_profile

    # Create new profile
    profile = PortsProfile(name=f"Listing {listing_id} Ports")
    session.add(profile)
    await session.flush()

    listing.ports_profile_id = profile.id
    await session.commit()
    await session.refresh(profile)
    return profile


async def update_listing_ports(
    session: AsyncSession, listing_id: int, ports_data: list[dict]
) -> PortsProfile:
    """Update ports for a listing.

    Args:
        session: Database session
        listing_id: Listing ID
        ports_data: List of dicts with 'port_type' and 'quantity' keys

    Returns:
        Updated PortsProfile with ports

    Example:
        ports_data = [
            {"port_type": "USB-A", "quantity": 4},
            {"port_type": "HDMI", "quantity": 1}
        ]
    """
    profile = await get_or_create_ports_profile(session, listing_id)

    # Clear existing ports
    await session.execute(delete(Port).where(Port.ports_profile_id == profile.id))

    # Add new ports
    for port_data in ports_data:
        port = Port(
            ports_profile_id=profile.id, type=port_data["port_type"], count=port_data["quantity"]
        )
        session.add(port)

    await session.commit()
    await session.refresh(profile)
    return profile


async def get_listing_ports(session: AsyncSession, listing_id: int) -> list[dict]:
    """Get ports for a listing as simple dict list.

    Returns:
        List of dicts with port_type and quantity, or empty list if none.
    """
    stmt = (
        select(Listing)
        .where(Listing.id == listing_id)
        .options(joinedload(Listing.ports_profile).joinedload(PortsProfile.ports))
    )
    result = await session.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing or not listing.ports_profile:
        return []

    return [
        {"port_type": port.type, "quantity": port.count} for port in listing.ports_profile.ports
    ]
