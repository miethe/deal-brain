#!/usr/bin/env python3
"""Seed sample listings with metadata fields and ports data.

Usage:
    poetry run python scripts/seed_sample_listings.py
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add apps/api to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from dealbrain_api.models.core import Cpu, Listing, PortsProfile, Port
from dealbrain_api.services.listings import bulk_update_listing_metrics
from dealbrain_api.settings import get_settings


SAMPLE_LISTINGS = [
    {
        "title": "Dell OptiPlex 7090 SFF - i7-12700/16GB/512GB",
        "manufacturer": "Dell",
        "series": "OptiPlex",
        "model_number": "7090",
        "form_factor": "Desktop",
        "price_usd": 699.99,
        "condition": "refurb",
        "cpu_name": "Intel Core i7-12700K",
        "ram_gb": 16,
        "primary_storage_gb": 512,
        "primary_storage_type": "NVMe SSD",
        "ports": [
            {"port_type": "USB-A", "quantity": 6},
            {"port_type": "USB-C", "quantity": 1},
            {"port_type": "HDMI", "quantity": 1},
            {"port_type": "DisplayPort", "quantity": 1},
            {"port_type": "Ethernet", "quantity": 1},
            {"port_type": "Audio", "quantity": 2},
        ],
    },
    {
        "title": "Lenovo ThinkCentre M75q Gen 2 - Ryzen 7/32GB/1TB",
        "manufacturer": "Lenovo",
        "series": "ThinkCentre",
        "model_number": "M75q",
        "form_factor": "Mini-PC",
        "price_usd": 549.99,
        "condition": "used",
        "cpu_name": "AMD Ryzen 7 5800X",
        "ram_gb": 32,
        "primary_storage_gb": 1024,
        "primary_storage_type": "NVMe SSD",
        "ports": [
            {"port_type": "USB-A", "quantity": 4},
            {"port_type": "USB-C", "quantity": 2},
            {"port_type": "HDMI", "quantity": 2},
            {"port_type": "DisplayPort", "quantity": 1},
            {"port_type": "Ethernet", "quantity": 1},
        ],
    },
    {
        "title": "HP EliteDesk 800 G9 Mini - i5-12600K/16GB/256GB",
        "manufacturer": "HP",
        "series": "EliteDesk",
        "model_number": "800 G9",
        "form_factor": "Mini-PC",
        "price_usd": 479.99,
        "condition": "refurb",
        "cpu_name": "Intel Core i5-12600K",
        "ram_gb": 16,
        "primary_storage_gb": 256,
        "primary_storage_type": "NVMe SSD",
        "ports": [
            {"port_type": "USB-A", "quantity": 4},
            {"port_type": "USB-C", "quantity": 1},
            {"port_type": "DisplayPort", "quantity": 2},
            {"port_type": "Ethernet", "quantity": 1},
            {"port_type": "Audio", "quantity": 1},
        ],
    },
    {
        "title": "Custom Gaming Desktop - Ryzen 9 5950X/64GB/2TB+4TB",
        "manufacturer": "Custom Build",
        "series": None,
        "model_number": None,
        "form_factor": "Desktop",
        "price_usd": 1299.99,
        "condition": "new",
        "cpu_name": "AMD Ryzen 9 5950X",
        "ram_gb": 64,
        "primary_storage_gb": 2048,
        "primary_storage_type": "NVMe SSD",
        "secondary_storage_gb": 4096,
        "secondary_storage_type": "SATA HDD",
        "ports": [
            {"port_type": "USB-A", "quantity": 8},
            {"port_type": "USB-C", "quantity": 2},
            {"port_type": "HDMI", "quantity": 1},
            {"port_type": "DisplayPort", "quantity": 3},
            {"port_type": "Ethernet", "quantity": 2},
            {"port_type": "Audio", "quantity": 5},
        ],
    },
    {
        "title": "ASUS Zenbook Pro 14 OLED - Ryzen 9 7940HS/32GB/1TB",
        "manufacturer": "ASUS",
        "series": "Zenbook Pro",
        "model_number": "UX6404",
        "form_factor": "Laptop",
        "price_usd": 1599.99,
        "condition": "new",
        "cpu_name": "AMD Ryzen 9 7940HS",
        "ram_gb": 32,
        "primary_storage_gb": 1024,
        "primary_storage_type": "NVMe SSD",
        "ports": [
            {"port_type": "USB-A", "quantity": 1},
            {"port_type": "USB-C", "quantity": 2},
            {"port_type": "HDMI", "quantity": 1},
            {"port_type": "SD Card", "quantity": 1},
            {"port_type": "Audio", "quantity": 1},
        ],
    },
]


async def seed_sample_listings():
    """Create sample listings with metadata and ports."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    created_count = 0
    listing_ids = []

    async with async_session() as session:
        for sample in SAMPLE_LISTINGS:
            # Check if listing already exists
            existing = await session.scalar(
                select(Listing).where(Listing.title == sample["title"])
            )
            if existing:
                print(f"Skipping existing listing: {sample['title']}")
                continue

            # Find CPU by name
            cpu = await session.scalar(
                select(Cpu).where(Cpu.name == sample["cpu_name"])
            )
            if not cpu:
                print(f"Warning: CPU not found '{sample['cpu_name']}' for {sample['title']}")
                continue

            # Create ports profile
            ports_profile = None
            if sample.get("ports"):
                ports_profile = PortsProfile(
                    name=f"{sample['title']} Ports"
                )
                session.add(ports_profile)
                await session.flush()

                for port_data in sample["ports"]:
                    port = Port(
                        port_profile_id=ports_profile.id,
                        port_type=port_data["port_type"],
                        quantity=port_data["quantity"],
                    )
                    session.add(port)

            # Create listing
            listing = Listing(
                title=sample["title"],
                manufacturer=sample.get("manufacturer"),
                series=sample.get("series"),
                model_number=sample.get("model_number"),
                form_factor=sample.get("form_factor"),
                price_usd=sample["price_usd"],
                condition=sample["condition"],
                cpu_id=cpu.id,
                ram_gb=sample.get("ram_gb"),
                primary_storage_gb=sample.get("primary_storage_gb"),
                primary_storage_type=sample.get("primary_storage_type"),
                secondary_storage_gb=sample.get("secondary_storage_gb"),
                secondary_storage_type=sample.get("secondary_storage_type"),
                ports_profile_id=ports_profile.id if ports_profile else None,
            )
            session.add(listing)
            await session.flush()

            listing_ids.append(listing.id)
            created_count += 1
            print(f"Created: {sample['title']}")

        await session.commit()

    # Recalculate metrics for all created listings
    if listing_ids:
        print(f"\nRecalculating metrics for {len(listing_ids)} listings...")
        async with async_session() as session:
            await bulk_update_listing_metrics(session, listing_ids=listing_ids)

    await engine.dispose()

    print(f"\n=== Seed Complete ===")
    print(f"Created {created_count} sample listings")


if __name__ == "__main__":
    print("Seeding Sample Listings with Metadata")
    print("=" * 50)
    print("")

    asyncio.run(seed_sample_listings())
