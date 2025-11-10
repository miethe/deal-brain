"""Tests for settings service."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.core import ApplicationSettings
from apps.api.dealbrain_api.services.settings import SettingsService

try:
    import aiosqlite  # type: ignore  # noqa: F401
    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio("asyncio")
class TestGetCpuMarkThresholds:
    """Test get_cpu_mark_thresholds method."""

    async def test_returns_defaults_when_not_in_db(self):
        """Test that default thresholds are returned when not configured in database."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        service = SettingsService()

        async with async_session() as session:
            thresholds = await service.get_cpu_mark_thresholds(session)

            assert thresholds == {
                "excellent": 20.0,
                "good": 10.0,
                "fair": 5.0,
                "neutral": 0.0,
                "poor": -10.0,
                "premium": -20.0
            }

    async def test_returns_stored_values_when_in_db(self):
        """Test that stored thresholds are returned when configured in database."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        service = SettingsService()
        custom_thresholds = {
            "excellent": 25.0,
            "good": 15.0,
            "fair": 7.5,
            "neutral": 2.5,
            "poor": -5.0,
            "premium": -15.0
        }

        async with async_session() as session:
            # Store custom thresholds
            await service.update_setting(
                session,
                "cpu_mark_thresholds",
                custom_thresholds,
                "Custom CPU Mark thresholds"
            )

            # Retrieve and verify
            thresholds = await service.get_cpu_mark_thresholds(session)
            assert thresholds == custom_thresholds

    async def test_value_persistence(self):
        """Test that values persist across sessions."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        service = SettingsService()
        custom_thresholds = {
            "excellent": 30.0,
            "good": 20.0,
            "fair": 10.0,
            "neutral": 5.0,
            "poor": -10.0,
            "premium": -25.0
        }

        # First session: store values
        async with async_session() as session:
            await service.update_setting(
                session,
                "cpu_mark_thresholds",
                custom_thresholds
            )

        # Second session: retrieve values
        async with async_session() as session:
            thresholds = await service.get_cpu_mark_thresholds(session)
            assert thresholds == custom_thresholds

    async def test_database_storage_format(self):
        """Test that values are stored correctly in database."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        service = SettingsService()
        custom_thresholds = {
            "excellent": 22.5,
            "good": 12.5,
            "fair": 6.0,
            "neutral": 1.0,
            "poor": -8.0,
            "premium": -18.0
        }

        async with async_session() as session:
            await service.update_setting(
                session,
                "cpu_mark_thresholds",
                custom_thresholds,
                "Test description"
            )

            # Query database directly
            result = await session.execute(
                select(ApplicationSettings).where(
                    ApplicationSettings.key == "cpu_mark_thresholds"
                )
            )
            setting = result.scalar_one()

            assert setting.key == "cpu_mark_thresholds"
            assert setting.value_json == custom_thresholds
            assert setting.description == "Test description"


@pytest.mark.anyio("asyncio")
class TestGetValuationThresholds:
    """Test get_valuation_thresholds method for comparison."""

    async def test_returns_defaults_when_not_in_db(self):
        """Test that default valuation thresholds are returned when not configured."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        service = SettingsService()

        async with async_session() as session:
            thresholds = await service.get_valuation_thresholds(session)

            assert thresholds == {
                "good_deal": 15.0,
                "great_deal": 25.0,
                "premium_warning": 10.0
            }
