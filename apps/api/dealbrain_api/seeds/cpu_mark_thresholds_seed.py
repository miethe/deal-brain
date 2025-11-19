"""Seed default CPU Mark thresholds for performance efficiency color coding."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_CPU_MARK_THRESHOLDS = {
    "excellent": 20.0,  # ≥20% improvement (better price-to-performance)
    "good": 10.0,  # 10-20% improvement
    "fair": 5.0,  # 5-10% improvement
    "neutral": 0.0,  # 0-5% change
    "poor": -10.0,  # -10-0% degradation
    "premium": -20.0,  # <-10% degradation (worse price-to-performance)
}


async def seed_cpu_mark_thresholds(session: AsyncSession) -> None:
    """Insert default CPU Mark thresholds into ApplicationSettings.

    Uses ON CONFLICT DO NOTHING to avoid overwriting existing configuration.
    These are percentage improvement values representing price-to-performance efficiency.

    Args:
        session: Database session
    """
    await session.execute(
        text(
            """
            INSERT INTO application_settings (key, value_json, description)
            VALUES (
                'cpu_mark_thresholds',
                :value_json,
                'CPU Mark performance efficiency thresholds for color coding. '
                'Percentage improvement values: positive = better efficiency (lower $/mark), '
                'negative = worse efficiency (higher $/mark) compared to baseline.'
            )
            ON CONFLICT (key) DO NOTHING
        """
        ),
        {"value_json": DEFAULT_CPU_MARK_THRESHOLDS},
    )
    await session.commit()


__all__ = ["DEFAULT_CPU_MARK_THRESHOLDS", "seed_cpu_mark_thresholds"]
