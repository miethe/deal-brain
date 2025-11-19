#!/usr/bin/env python3
"""
Seed test data for E2E tests

Creates test users, listings, and other data needed for E2E test suites.
"""

import asyncio
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

# Add project paths
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT / "packages" / "core"))

from dealbrain_api.db import session_scope
from dealbrain_api.models.core import User, Cpu, Listing, Collection
from sqlalchemy import select, delete


async def cleanup_test_data(session: AsyncSession):
    """Remove existing test data"""
    print("🧹 Cleaning up existing test data...")

    # Delete test users and their data (cascade should handle related records)
    await session.execute(
        delete(User).where(User.username.in_(["testuser", "recipient_user"]))
    )

    # Delete test listings
    await session.execute(
        delete(Listing).where(Listing.title.like("Test Listing%"))
    )

    await session.commit()
    print("✅ Cleanup complete")


async def create_test_users(session: AsyncSession) -> List[User]:
    """Create test users for E2E and load tests.

    Note: Current User model is minimal (no auth fields yet).
    Full authentication will be added in later phases.
    """
    print("👥 Creating test users...")

    users = [
        User(
            username="testuser",
            email="testuser@test.com",
            display_name="Test User",
        ),
        User(
            username="recipient_user",
            email="recipient@test.com",
            display_name="Recipient User",
        ),
    ]

    for user in users:
        session.add(user)

    await session.commit()

    # Refresh to get IDs
    for user in users:
        await session.refresh(user)

    print(f"✅ Created {len(users)} test users")
    return users


async def create_test_cpus(session: AsyncSession) -> List[Cpu]:
    """Create test CPUs for listings"""
    print("💻 Creating test CPUs...")

    cpus = [
        Cpu(
            name="AMD Ryzen 9 7940HS",
            manufacturer="AMD",
            socket="FP8",
            cores=8,
            threads=16,
            base_clock=4.0,
            boost_clock=5.2,
            tdp=35,
            cpu_mark=35000,
            single_thread_rating=4200,
        ),
        Cpu(
            name="Intel Core i7-13700H",
            manufacturer="Intel",
            socket="BGA",
            cores=14,
            threads=20,
            base_clock=3.7,
            boost_clock=5.0,
            tdp=45,
            cpu_mark=33000,
            single_thread_rating=4000,
        ),
        Cpu(
            name="AMD Ryzen 7 5700U",
            manufacturer="AMD",
            socket="FP6",
            cores=8,
            threads=16,
            base_clock=1.8,
            boost_clock=4.3,
            tdp=15,
            cpu_mark=18000,
            single_thread_rating=2800,
        ),
        Cpu(
            name="Intel Core i5-12450H",
            manufacturer="Intel",
            socket="BGA",
            cores=8,
            threads=12,
            base_clock=3.3,
            boost_clock=4.4,
            tdp=45,
            cpu_mark=22000,
            single_thread_rating=3400,
        ),
        Cpu(
            name="AMD Ryzen 5 5600G",
            manufacturer="AMD",
            socket="AM4",
            cores=6,
            threads=12,
            base_clock=3.9,
            boost_clock=4.4,
            tdp=65,
            cpu_mark=20000,
            single_thread_rating=3100,
        ),
    ]

    for cpu in cpus:
        # Check if CPU already exists
        result = await session.execute(
            select(Cpu).where(Cpu.name == cpu.name)
        )
        existing = result.scalar_one_or_none()

        if not existing:
            session.add(cpu)

    await session.commit()

    # Get all test CPUs
    result = await session.execute(
        select(Cpu).where(Cpu.name.in_([c.name for c in cpus]))
    )
    created_cpus = list(result.scalars().all())

    print(f"✅ Created/verified {len(created_cpus)} test CPUs")
    return created_cpus


async def create_test_listings(session: AsyncSession, cpus: List[Cpu], users: List[User]) -> List[Listing]:
    """Create test listings for load testing (100+ listings)"""
    print("📋 Creating test listings...")

    listings_data = [
        {
            "title": "Test Listing - Mini PC Ryzen 9 7940HS",
            "price_usd": 699.99,
            "cpu": cpus[0],
            "ram_gb": 32,
            "primary_storage_gb": 1000,
            "condition": "new",
            "manufacturer": "Minisforum",
            "model_number": "UM790 Pro",
            "form_factor": "mini_pc",
        },
        {
            "title": "Test Listing - NUC i7-13700H",
            "price_usd": 799.99,
            "cpu": cpus[1],
            "ram_gb": 16,
            "primary_storage_gb": 512,
            "condition": "new",
            "manufacturer": "Intel",
            "model_number": "NUC13ANHi7",
            "form_factor": "nuc",
        },
        {
            "title": "Test Listing - Budget Ryzen 7 5700U",
            "price_usd": 399.99,
            "cpu": cpus[2],
            "ram_gb": 16,
            "primary_storage_gb": 512,
            "condition": "refurbished",
            "manufacturer": "Beelink",
            "model_number": "SER5 5700U",
            "form_factor": "mini_pc",
        },
        {
            "title": "Test Listing - Mid-range i5-12450H",
            "price_usd": 549.99,
            "cpu": cpus[3],
            "ram_gb": 16,
            "primary_storage_gb": 512,
            "condition": "new",
            "manufacturer": "ASUS",
            "model_number": "PN53",
            "form_factor": "mini_pc",
        },
        {
            "title": "Test Listing - Desktop Ryzen 5 5600G",
            "price_usd": 449.99,
            "cpu": cpus[4],
            "ram_gb": 16,
            "primary_storage_gb": 256,
            "condition": "used",
            "manufacturer": "Custom Build",
            "form_factor": "desktop",
        },
        {
            "title": "Test Listing - High-end Ryzen 9",
            "price_usd": 999.99,
            "cpu": cpus[0],
            "ram_gb": 64,
            "primary_storage_gb": 2000,
            "condition": "new",
            "manufacturer": "Minisforum",
            "model_number": "UM790 Pro Max",
            "form_factor": "mini_pc",
        },
        {
            "title": "Test Listing - Budget i5",
            "price_usd": 299.99,
            "cpu": cpus[3],
            "ram_gb": 8,
            "primary_storage_gb": 256,
            "condition": "used",
            "manufacturer": "Dell",
            "form_factor": "sff",
        },
        {
            "title": "Test Listing - Compact Ryzen 7",
            "price_usd": 499.99,
            "cpu": cpus[2],
            "ram_gb": 32,
            "primary_storage_gb": 1000,
            "condition": "refurbished",
            "manufacturer": "Beelink",
            "model_number": "SER5 Pro",
            "form_factor": "mini_pc",
        },
        {
            "title": "Test Listing - Premium i7",
            "price_usd": 1199.99,
            "cpu": cpus[1],
            "ram_gb": 32,
            "primary_storage_gb": 2000,
            "condition": "new",
            "manufacturer": "Intel",
            "model_number": "NUC13 Extreme",
            "form_factor": "nuc",
        },
        {
            "title": "Test Listing - Entry Level AMD",
            "price_usd": 249.99,
            "cpu": cpus[4],
            "ram_gb": 8,
            "primary_storage_gb": 256,
            "condition": "refurbished",
            "manufacturer": "HP",
            "form_factor": "sff",
        },
    ]

    listings = []
    for data in listings_data:
        cpu = data.pop("cpu")

        listing = Listing(
            **data,
            cpu_id=cpu.id,
        )
        session.add(listing)
        listings.append(listing)

    # Create additional listings for load testing (target: 100+ total)
    print(f"  Creating additional listings for load testing...")
    manufacturers = ["Minisforum", "Beelink", "Intel", "ASUS", "Dell", "HP", "Lenovo"]
    conditions = ["new", "refurbished", "used"]
    form_factors = ["mini_pc", "nuc", "sff", "desktop"]

    for i in range(90):  # Create 90 more listings (10 base + 90 = 100)
        cpu_idx = i % len(cpus)
        listing = Listing(
            title=f"Test Listing - Load Test PC #{i+11}",
            price_usd=299.99 + (i * 10),
            cpu_id=cpus[cpu_idx].id,
            ram_gb=8 + ((i % 4) * 8),  # 8, 16, 24, 32 GB
            primary_storage_gb=256 + ((i % 3) * 256),  # 256, 512, 768 GB
            condition=conditions[i % len(conditions)],
            manufacturer=manufacturers[i % len(manufacturers)],
            model_number=f"LOAD-{i+1:03d}",
            form_factor=form_factors[i % len(form_factors)],
        )
        session.add(listing)
        listings.append(listing)

    await session.commit()

    # Refresh to get IDs
    for listing in listings:
        await session.refresh(listing)

    print(f"✅ Created {len(listings)} test listings (including load test data)")
    return listings


async def create_test_collections(session: AsyncSession, users: List[User]) -> List[Collection]:
    """Create test collections"""
    print("📁 Creating test collections...")

    collections = [
        Collection(
            name="Favorites",
            description="My favorite deals",
            user_id=users[0].id,
            visibility="private",
        ),
        Collection(
            name="Budget Builds",
            description="Affordable options under $500",
            user_id=users[0].id,
            visibility="private",
        ),
        Collection(
            name="Premium Systems",
            description="High-end configurations",
            user_id=users[1].id,
            visibility="private",
        ),
    ]

    for collection in collections:
        session.add(collection)

    await session.commit()

    # Refresh to get IDs
    for collection in collections:
        await session.refresh(collection)

    print(f"✅ Created {len(collections)} test collections")
    return collections


async def main():
    """Main seeding function"""
    print("\n🌱 Starting test data seeding for security & load testing...\n")

    async with session_scope() as session:
        # Clean up existing test data
        await cleanup_test_data(session)

        # Create test data
        users = await create_test_users(session)
        cpus = await create_test_cpus(session)
        listings = await create_test_listings(session, cpus, users)
        collections = await create_test_collections(session, users)

    print("\n✅ Test data seeding complete!")
    print("\nTest Users:")
    print("  - testuser (testuser@test.com)")
    print("  - recipient_user (recipient@test.com)")
    print("\nNote: Current User model is minimal (no passwords yet).")
    print("      Full authentication will be added in later phases.")
    print(f"\nCreated:")
    print(f"  - {len(users)} users")
    print(f"  - {len(cpus)} CPUs")
    print(f"  - {len(listings)} listings")
    print(f"  - {len(collections)} collections")
    print("\n🚀 Ready to run security audit and load tests!")
    print("\nRun tests:")
    print("  poetry run python scripts/security_audit.py")
    print("  poetry run python scripts/load_test.py")


if __name__ == "__main__":
    asyncio.run(main())
