"""Tests for the baseline loader service."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

try:  # pragma: no cover - optional dependency
    import aiosqlite  # type: ignore  # noqa: F401

    AIOSQLITE_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - executed when optional dep missing
    AIOSQLITE_AVAILABLE = False

try:  # pragma: no cover - optional dependency
    import pytest_asyncio  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - executed when plugin missing
    pytest_asyncio = None

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.core import ValuationRuleGroup, ValuationRuleV2, ValuationRuleset
from apps.api.dealbrain_api.services.baseline_loader import BaselineLoaderService
from apps.api.dealbrain_api.services.rules import RulesService


pytestmark = pytest.mark.asyncio


if pytest_asyncio:

    @pytest_asyncio.fixture
    async def db_session() -> AsyncSession:
        """Provide an isolated in-memory database session for baseline tests."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping baseline loader tests")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session = async_session()
        try:
            yield session
        finally:
            await session.close()
            await engine.dispose()

else:

    @pytest.fixture
    def db_session() -> AsyncSession:
        pytest.skip("pytest-asyncio is not installed; skipping baseline loader tests")


@pytest.fixture(autouse=True)
def disable_recalculation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent recalculation tasks from firing during tests."""
    monkeypatch.setattr(
        "dealbrain_api.services.rules.enqueue_listing_recalculation",
        lambda **_: None,
    )


def _sample_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "generated_at": "2025-10-12",
        "entities": {
            "Listing": [
                {
                    "id": "base_adjustment",
                    "proper_name": "Base Adjustment",
                    "description": "Baseline additive adjustment",
                    "explanation": "Default offset applied to every listing.",
                    "valuation_buckets": [
                        {"label": "Default", "min_usd": 10, "max_usd": 25, "Formula": None}
                    ],
                    "Formula": None,
                    "unit": "USD",
                    "dependencies": None,
                    "notes": None,
                    "nullable": False,
                }
            ],
            "CPU": [
                {
                    "id": "cpu_mark_multi",
                    "proper_name": "CPU Mark (Multi)",
                    "description": "PassMark multi-thread score",
                    "explanation": "Baseline uplift based on multi-thread benchmark.",
                    "valuation_buckets": None,
                    "Formula": "usd ≈ (cpu_mark_multi/1000)*3.6",
                    "unit": "USD",
                    "dependencies": None,
                    "notes": None,
                    "nullable": True,
                }
            ],
        },
    }


async def test_load_creates_ruleset_and_groups(db_session: AsyncSession) -> None:
    """Loader should create baseline ruleset, groups, and placeholder rules."""
    service = BaselineLoaderService()
    payload = _sample_payload()

    result = await service.load_from_payload(db_session, payload, actor="tests")

    assert result.status == "created"
    assert result.created_groups == 2
    assert result.created_rules == 2
    assert result.ruleset_id is not None

    ruleset = await db_session.get(ValuationRuleset, result.ruleset_id)
    assert ruleset is not None
    assert ruleset.metadata_json["system_baseline"] is True
    assert ruleset.metadata_json["source_hash"] == result.source_hash

    groups = (
        await db_session.execute(
            select(ValuationRuleGroup).where(ValuationRuleGroup.ruleset_id == ruleset.id)
        )
    ).scalars().all()
    assert len(groups) == 2

    # Ensure rules were materialised with placeholder metadata
    rules = (
        await db_session.execute(
            select(ValuationRuleV2).where(ValuationRuleV2.group_id == groups[0].id)
        )
    ).scalars().all()
    assert rules


async def test_load_skips_when_hash_matches(db_session: AsyncSession) -> None:
    """Loader should skip creating duplicate baseline rulesets for same content."""
    service = BaselineLoaderService()
    payload = _sample_payload()

    first = await service.load_from_payload(db_session, payload, actor="tests")
    assert first.status == "created"

    second = await service.load_from_payload(db_session, payload, actor="tests")
    assert second.status == "skipped"
    assert second.ruleset_id == first.ruleset_id


async def test_ensure_basic_adjustments_group(db_session: AsyncSession) -> None:
    """Basic adjustments group should be provisioned on demand."""
    rules_service = RulesService()
    loader = BaselineLoaderService(rules_service)

    ruleset = await rules_service.create_ruleset(
        db_session,
        name="Standard Valuation",
        description="Primary user-managed ruleset",
        version="1.0.0",
        metadata={"default": True},
        priority=10,
    )

    group = await loader.ensure_basic_adjustments_group(db_session, ruleset.id, actor="tests")
    assert group is not None
    assert group.name == "Basic · Adjustments"
    assert group.metadata_json["basic_managed"] is True

    # Second invocation should reuse the same group
    again = await loader.ensure_basic_adjustments_group(db_session, ruleset.id, actor="tests")
    assert again.id == group.id
    assert again.metadata_json["basic_managed"] is True
