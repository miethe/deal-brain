"""Application settings service."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.core import ApplicationSettings


class SettingsService:
    """Service for managing application settings."""

    async def get_setting(self, session: AsyncSession, key: str) -> dict[str, Any] | None:
        """Get a setting by key.

        Args:
            session: Database session
            key: Setting key

        Returns:
            Setting value as dict, or None if not found
        """
        result = await session.execute(
            select(ApplicationSettings).where(ApplicationSettings.key == key)
        )
        setting = result.scalar_one_or_none()
        return setting.value_json if setting else None

    async def update_setting(
        self, session: AsyncSession, key: str, value: dict[str, Any], description: str | None = None
    ) -> dict[str, Any]:
        """Update or create a setting.

        Args:
            session: Database session
            key: Setting key
            value: Setting value as dict
            description: Optional description

        Returns:
            Updated setting value
        """
        result = await session.execute(
            select(ApplicationSettings).where(ApplicationSettings.key == key)
        )
        setting = result.scalar_one_or_none()

        if setting:
            setting.value_json = value
            if description is not None:
                setting.description = description
        else:
            setting = ApplicationSettings(key=key, value_json=value, description=description)
            session.add(setting)

        await session.commit()
        await session.refresh(setting)
        return setting.value_json

    async def get_valuation_thresholds(self, session: AsyncSession) -> dict[str, float]:
        """Get valuation thresholds with defaults.

        Args:
            session: Database session

        Returns:
            Thresholds dict with good_deal, great_deal, premium_warning
        """
        thresholds = await self.get_setting(session, "valuation_thresholds")
        if not thresholds:
            # Return defaults if not configured
            return {"good_deal": 15.0, "great_deal": 25.0, "premium_warning": 10.0}
        return thresholds

    async def get_cpu_mark_thresholds(self, session: AsyncSession) -> dict[str, float]:
        """Get CPU Mark thresholds with defaults.

        These are percentage improvement values representing price-to-performance efficiency.
        Positive values indicate better efficiency (lower $/mark), negative values indicate
        worse efficiency (higher $/mark) compared to baseline.

        Args:
            session: Database session

        Returns:
            Thresholds dict with excellent, good, fair, neutral, poor, premium
        """
        thresholds = await self.get_setting(session, "cpu_mark_thresholds")
        if not thresholds:
            # Return defaults if not configured
            return {
                "excellent": 20.0,
                "good": 10.0,
                "fair": 5.0,
                "neutral": 0.0,
                "poor": -10.0,
                "premium": -20.0,
            }
        return thresholds
