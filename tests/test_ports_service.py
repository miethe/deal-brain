"""Tests for ports management service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models.core import Listing, PortsProfile, Port
from dealbrain_api.services.ports import (
    get_or_create_ports_profile,
    update_listing_ports,
    get_listing_ports,
)


@pytest.mark.asyncio
class TestGetOrCreatePortsProfile:
    """Test get_or_create_ports_profile function."""

    async def test_create_new_profile(self, session: AsyncSession):
        """Test creating new ports profile for listing."""
        listing = Listing(title="Test PC", price_usd=500, condition="used")
        session.add(listing)
        await session.commit()

        profile = await get_or_create_ports_profile(session, listing.id)

        assert profile is not None
        assert profile.id is not None
        assert profile.name == f"Listing {listing.id} Ports"

    async def test_get_existing_profile(self, session: AsyncSession):
        """Test getting existing ports profile."""
        # Create listing with ports profile
        profile = PortsProfile(name="Existing Profile")
        session.add(profile)
        await session.flush()

        listing = Listing(
            title="Test PC",
            price_usd=500,
            condition="used",
            ports_profile_id=profile.id,
        )
        session.add(listing)
        await session.commit()

        retrieved = await get_or_create_ports_profile(session, listing.id)

        assert retrieved.id == profile.id
        assert retrieved.name == "Existing Profile"

    async def test_listing_not_found(self, session: AsyncSession):
        """Test error when listing doesn't exist."""
        with pytest.raises(ValueError, match="Listing .* not found"):
            await get_or_create_ports_profile(session, 99999)


@pytest.mark.asyncio
class TestUpdateListingPorts:
    """Test update_listing_ports function."""

    async def test_create_ports(self, session: AsyncSession):
        """Test creating ports for listing."""
        listing = Listing(title="Test PC", price_usd=500, condition="used")
        session.add(listing)
        await session.commit()

        ports_data = [
            {"port_type": "USB-A", "quantity": 4},
            {"port_type": "HDMI", "quantity": 2},
            {"port_type": "Ethernet", "quantity": 1},
        ]

        profile = await update_listing_ports(session, listing.id, ports_data)

        assert len(profile.ports) == 3
        assert profile.ports[0].port_type == "USB-A"
        assert profile.ports[0].quantity == 4
        assert profile.ports[1].port_type == "HDMI"
        assert profile.ports[1].quantity == 2
        assert profile.ports[2].port_type == "Ethernet"
        assert profile.ports[2].quantity == 1

    async def test_update_existing_ports(self, session: AsyncSession):
        """Test updating existing ports (clear and replace)."""
        # Create listing with initial ports
        profile = PortsProfile(name="Test Profile")
        session.add(profile)
        await session.flush()

        port1 = Port(port_profile_id=profile.id, port_type="USB-A", quantity=2)
        port2 = Port(port_profile_id=profile.id, port_type="HDMI", quantity=1)
        session.add_all([port1, port2])

        listing = Listing(
            title="Test PC",
            price_usd=500,
            condition="used",
            ports_profile_id=profile.id,
        )
        session.add(listing)
        await session.commit()

        # Update with new ports
        new_ports_data = [
            {"port_type": "USB-C", "quantity": 3},
            {"port_type": "DisplayPort", "quantity": 2},
        ]

        updated_profile = await update_listing_ports(session, listing.id, new_ports_data)

        assert len(updated_profile.ports) == 2
        assert updated_profile.ports[0].port_type == "USB-C"
        assert updated_profile.ports[0].quantity == 3
        assert updated_profile.ports[1].port_type == "DisplayPort"
        assert updated_profile.ports[1].quantity == 2

    async def test_empty_ports_list(self, session: AsyncSession):
        """Test updating with empty ports list (clears all ports)."""
        # Create listing with ports
        profile = PortsProfile(name="Test Profile")
        session.add(profile)
        await session.flush()

        port = Port(port_profile_id=profile.id, port_type="USB-A", quantity=4)
        session.add(port)

        listing = Listing(
            title="Test PC",
            price_usd=500,
            condition="used",
            ports_profile_id=profile.id,
        )
        session.add(listing)
        await session.commit()

        # Clear all ports
        updated_profile = await update_listing_ports(session, listing.id, [])

        assert len(updated_profile.ports) == 0


@pytest.mark.asyncio
class TestGetListingPorts:
    """Test get_listing_ports function."""

    async def test_get_ports(self, session: AsyncSession):
        """Test getting ports for listing."""
        # Create listing with ports
        profile = PortsProfile(name="Test Profile")
        session.add(profile)
        await session.flush()

        port1 = Port(port_profile_id=profile.id, port_type="USB-A", quantity=4)
        port2 = Port(port_profile_id=profile.id, port_type="HDMI", quantity=1)
        session.add_all([port1, port2])

        listing = Listing(
            title="Test PC",
            price_usd=500,
            condition="used",
            ports_profile_id=profile.id,
        )
        session.add(listing)
        await session.commit()

        ports = await get_listing_ports(session, listing.id)

        assert len(ports) == 2
        assert ports[0] == {"port_type": "USB-A", "quantity": 4}
        assert ports[1] == {"port_type": "HDMI", "quantity": 1}

    async def test_get_ports_empty(self, session: AsyncSession):
        """Test getting ports when none exist."""
        listing = Listing(title="Test", price_usd=500, condition="used")
        session.add(listing)
        await session.commit()

        ports = await get_listing_ports(session, listing.id)

        assert ports == []

    async def test_get_ports_listing_not_found(self, session: AsyncSession):
        """Test getting ports when listing doesn't exist."""
        ports = await get_listing_ports(session, 99999)
        assert ports == []
