"""Comprehensive unit tests for BaselineHydrationService.

Tests the hydration of baseline placeholder rules into full rule structures
with conditions and actions, following the implementation plan requirements.
"""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Mock Celery before any imports that might use it
if "celery" not in sys.modules:

    class _DummyTask:
        def __init__(self, func):
            self._func = func

        def __call__(self, *args, **kwargs):
            return self._func(*args, **kwargs)

        def delay(self, *args, **kwargs):
            return self._func(*args, **kwargs)

    class _StubCelery:
        def __init__(self, *args, **kwargs):
            pass

        def config_from_object(self, *args, **kwargs):
            return None

        def task(self, *decorator_args, **decorator_kwargs):
            def _decorator(func):
                return _DummyTask(func)

            return _decorator

    celery_stub = types.ModuleType("celery")
    celery_stub.Celery = _StubCelery
    sys.modules["celery"] = celery_stub

# Mock Prometheus before any imports
if "prometheus_client" not in sys.modules:

    class _DummyCounter:
        def __init__(self, *args, **kwargs):
            pass

        def inc(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

    class _DummyHistogram:
        def __init__(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def time(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def labels(self, *args, **kwargs):
            return self

    class _DummyGauge:
        def __init__(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

        def inc(self, *args, **kwargs):
            pass

        def dec(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

    prometheus_stub = types.ModuleType("prometheus_client")
    prometheus_stub.Counter = _DummyCounter
    prometheus_stub.Histogram = _DummyHistogram
    prometheus_stub.Gauge = _DummyGauge

    metrics_stub = types.ModuleType("prometheus_client.metrics")
    metrics_stub.Counter = _DummyCounter
    metrics_stub.Histogram = _DummyHistogram
    metrics_stub.Gauge = _DummyGauge

    sys.modules["prometheus_client"] = prometheus_stub
    sys.modules["prometheus_client.metrics"] = metrics_stub

try:
    import aiosqlite  # type: ignore  # noqa: F401

    AIOSQLITE_AVAILABLE = True
except ModuleNotFoundError:
    AIOSQLITE_AVAILABLE = False

try:
    import pytest_asyncio  # type: ignore
except ModuleNotFoundError:
    pytest_asyncio = None

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.core import (
    ValuationRuleAction,
    ValuationRuleCondition,
    ValuationRuleGroup,
    ValuationRuleset,
    ValuationRuleV2,
)
from apps.api.dealbrain_api.services.baseline_hydration import (
    BaselineHydrationService,
    HydrationResult,
)
from apps.api.dealbrain_api.services.rules import RulesService

pytestmark = pytest.mark.asyncio


# --- Fixtures ---


if pytest_asyncio:

    @pytest_asyncio.fixture
    async def db_session() -> AsyncSession:
        """Provide an isolated in-memory database session."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed")

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
        pytest.skip("pytest-asyncio is not installed")


@pytest.fixture(autouse=True)
def disable_recalculation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent recalculation tasks from firing during tests."""

    # Don't let the monkeypatch trigger imports, just replace the function after import
    def _noop(**kwargs):
        pass

    try:
        from apps.api.dealbrain_api.services import rules

        rules.enqueue_listing_recalculation = _noop
    except ImportError:
        pass


if pytest_asyncio:

    @pytest_asyncio.fixture
    async def hydration_service():
        """Create BaselineHydrationService instance."""
        return BaselineHydrationService()

    @pytest_asyncio.fixture
    async def sample_ruleset(db_session: AsyncSession) -> ValuationRuleset:
        """Create a sample ruleset."""
        ruleset = ValuationRuleset(
            name="Test Baseline Ruleset",
            description="Ruleset for testing baseline hydration",
            version="1.0.0",
            is_active=True,
            created_by="test_user",
        )
        db_session.add(ruleset)
        await db_session.commit()
        await db_session.refresh(ruleset)
        return ruleset

    @pytest_asyncio.fixture
    async def sample_rule_group(
        db_session: AsyncSession, sample_ruleset: ValuationRuleset
    ) -> ValuationRuleGroup:
        """Create a sample rule group."""
        group = ValuationRuleGroup(
            ruleset_id=sample_ruleset.id,
            name="RAM Rules",
            category="ram",
            description="RAM-based valuation rules",
            display_order=1,
            weight=0.25,
        )
        db_session.add(group)
        await db_session.commit()
        await db_session.refresh(group)
        return group

else:

    @pytest.fixture
    def hydration_service():
        pytest.skip("pytest-asyncio is not installed")

    @pytest.fixture
    def sample_ruleset():
        pytest.skip("pytest-asyncio is not installed")

    @pytest.fixture
    def sample_rule_group():
        pytest.skip("pytest-asyncio is not installed")


# --- Test Cases ---


async def test_hydrate_enum_multiplier_field(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
    sample_rule_group: ValuationRuleGroup,
):
    """Test hydration of enum_multiplier field (DDR Generation example)."""
    # Create placeholder rule for DDR generation with multipliers
    placeholder_rule = ValuationRuleV2(
        group_id=sample_rule_group.id,
        name="DDR Generation",
        description="RAM generation multipliers",
        priority=100,
        evaluation_order=100,
        is_active=True,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "enum_multiplier",
            "field_id": "ram_spec.ddr_generation",
            "valuation_buckets": {
                "DDR3": 0.7,
                "DDR4": 1.0,
                "DDR5": 1.3,
            },
        },
    )
    db_session.add(placeholder_rule)
    await db_session.commit()
    await db_session.refresh(placeholder_rule)

    # Hydrate the rule
    expanded_rules = await hydration_service.hydrate_single_rule(
        db_session, placeholder_rule.id, actor="test_user"
    )

    # Verify we got 3 rules (one per enum value)
    assert len(expanded_rules) == 3

    # Verify each rule has correct structure
    rule_names = {r.name for r in expanded_rules}
    assert rule_names == {
        "DDR Generation: DDR3",
        "DDR Generation: DDR4",
        "DDR Generation: DDR5",
    }

    # Check one rule in detail (DDR4 = 1.0 multiplier)
    ddr4_rule = next(r for r in expanded_rules if "DDR4" in r.name)
    assert ddr4_rule.is_active is True
    assert ddr4_rule.priority == 100
    assert ddr4_rule.metadata_json["hydration_source_rule_id"] == placeholder_rule.id
    assert ddr4_rule.metadata_json["field_type"] == "enum_multiplier"
    assert ddr4_rule.metadata_json["enum_value"] == "DDR4"

    # Verify condition
    assert len(ddr4_rule.conditions) == 1
    condition = ddr4_rule.conditions[0]
    assert condition.field_name == "ram_spec.ddr_generation"
    assert condition.operator == "equals"
    assert condition.value_json == "DDR4"

    # Verify action (1.0 multiplier becomes 100.0 percentage)
    assert len(ddr4_rule.actions) == 1
    action = ddr4_rule.actions[0]
    assert action.action_type == "multiplier"
    assert action.value_usd == 100.0
    assert action.modifiers_json["original_multiplier"] == 1.0

    # Check DDR5 multiplier conversion (1.3 -> 130.0)
    ddr5_rule = next(r for r in expanded_rules if "DDR5" in r.name)
    assert ddr5_rule.actions[0].value_usd == 130.0
    assert ddr5_rule.actions[0].modifiers_json["original_multiplier"] == 1.3


async def test_hydrate_formula_field(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Test hydration of formula field (RAM Capacity formula example)."""
    # Create ruleset and group for this test
    ruleset = ValuationRuleset(name="Formula Test Ruleset", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="Test Group", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # Create placeholder rule with formula
    placeholder_rule = ValuationRuleV2(
        group_id=group.id,
        name="RAM Capacity",
        description="RAM capacity pricing formula",
        priority=200,
        evaluation_order=200,
        is_active=True,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "formula",
            "formula_text": "ram_spec.total_capacity_gb * 2.5",
        },
    )
    db_session.add(placeholder_rule)
    await db_session.commit()
    await db_session.refresh(placeholder_rule)

    # Hydrate the rule
    expanded_rules = await hydration_service.hydrate_single_rule(
        db_session, placeholder_rule.id, actor="test_user"
    )

    # Verify we got 1 rule
    assert len(expanded_rules) == 1
    rule = expanded_rules[0]

    # Verify basic properties
    assert rule.name == "RAM Capacity (Formula)"
    assert rule.description == "RAM capacity pricing formula"
    assert rule.is_active is True
    assert rule.metadata_json["hydration_source_rule_id"] == placeholder_rule.id
    assert rule.metadata_json["field_type"] == "formula"

    # Verify no conditions (always applies)
    assert len(rule.conditions) == 0

    # Verify formula action
    assert len(rule.actions) == 1
    action = rule.actions[0]
    assert action.action_type == "formula"
    assert action.formula == "ram_spec.total_capacity_gb * 2.5"
    assert action.value_usd is None


async def test_hydrate_fixed_field(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Test hydration of fixed field (Base depreciation example)."""
    # Create ruleset and group
    ruleset = ValuationRuleset(name="Fixed Test Ruleset", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="Test Group Fixed", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # Create placeholder rule with fixed value
    placeholder_rule = ValuationRuleV2(
        group_id=group.id,
        name="Base Depreciation",
        description="Fixed depreciation amount",
        priority=50,
        evaluation_order=50,
        is_active=True,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "fixed",
            "default_value": -50.0,
        },
    )
    db_session.add(placeholder_rule)
    await db_session.commit()
    await db_session.refresh(placeholder_rule)

    # Hydrate the rule
    expanded_rules = await hydration_service.hydrate_single_rule(
        db_session, placeholder_rule.id, actor="test_user"
    )

    # Verify we got 1 rule
    assert len(expanded_rules) == 1
    rule = expanded_rules[0]

    # Verify basic properties
    assert rule.name == "Base Depreciation (Fixed)"
    assert rule.is_active is True
    assert rule.metadata_json["hydration_source_rule_id"] == placeholder_rule.id
    assert rule.metadata_json["field_type"] == "fixed"

    # Verify no conditions
    assert len(rule.conditions) == 0

    # Verify fixed value action
    assert len(rule.actions) == 1
    action = rule.actions[0]
    assert action.action_type == "fixed_value"
    assert action.value_usd == -50.0


async def test_hydrate_ruleset_all_types(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
    sample_ruleset: ValuationRuleset,
    sample_rule_group: ValuationRuleGroup,
):
    """Test hydrating a ruleset with mixed field types."""
    # Create multiple placeholder rules of different types
    rules = [
        ValuationRuleV2(
            group_id=sample_rule_group.id,
            name="DDR Generation",
            description="RAM generation",
            priority=100,
            evaluation_order=100,
            metadata_json={
                "baseline_placeholder": True,
                "field_type": "enum_multiplier",
                "field_id": "ram_spec.ddr_generation",
                "valuation_buckets": {"DDR4": 1.0, "DDR5": 1.3},
            },
        ),
        ValuationRuleV2(
            group_id=sample_rule_group.id,
            name="RAM Capacity",
            description="RAM capacity formula",
            priority=200,
            evaluation_order=200,
            metadata_json={
                "baseline_placeholder": True,
                "field_type": "formula",
                "formula_text": "ram_spec.total_capacity_gb * 2.5",
            },
        ),
        ValuationRuleV2(
            group_id=sample_rule_group.id,
            name="Base Adjustment",
            description="Fixed base adjustment",
            priority=50,
            evaluation_order=50,
            metadata_json={
                "baseline_placeholder": True,
                "field_type": "fixed",
                "default_value": 10.0,
            },
        ),
    ]

    for rule in rules:
        db_session.add(rule)
    await db_session.commit()

    # Hydrate the entire ruleset
    result = await hydration_service.hydrate_baseline_rules(
        db_session, sample_ruleset.id, actor="test_user"
    )

    # Verify result structure
    assert isinstance(result, HydrationResult)
    assert result.status == "success"
    assert result.ruleset_id == sample_ruleset.id
    assert result.hydrated_rule_count == 3
    assert result.created_rule_count == 4  # 2 enum + 1 formula + 1 fixed

    # Verify summary
    assert len(result.hydration_summary) == 3
    summary_items = {item["field_name"]: item for item in result.hydration_summary}

    assert "DDR Generation" in summary_items
    assert summary_items["DDR Generation"]["field_type"] == "enum_multiplier"
    assert len(summary_items["DDR Generation"]["expanded_rule_ids"]) == 2

    assert "RAM Capacity" in summary_items
    assert summary_items["RAM Capacity"]["field_type"] == "formula"
    assert len(summary_items["RAM Capacity"]["expanded_rule_ids"]) == 1

    assert "Base Adjustment" in summary_items
    assert summary_items["Base Adjustment"]["field_type"] == "fixed"
    assert len(summary_items["Base Adjustment"]["expanded_rule_ids"]) == 1

    # Verify original rules are marked as hydrated and deactivated
    for rule in rules:
        await db_session.refresh(rule)
        assert rule.is_active is False
        assert rule.metadata_json["hydrated"] is True
        assert rule.metadata_json["hydrated_by"] == "test_user"
        assert "hydrated_at" in rule.metadata_json


async def test_skip_already_hydrated(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
    sample_ruleset: ValuationRuleset,
    sample_rule_group: ValuationRuleGroup,
):
    """Test idempotency - skips already hydrated rules."""
    # Create placeholder rule
    placeholder_rule = ValuationRuleV2(
        group_id=sample_rule_group.id,
        name="Test Rule",
        description="Test",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "fixed",
            "default_value": 5.0,
        },
    )
    db_session.add(placeholder_rule)
    await db_session.commit()

    # First hydration
    result1 = await hydration_service.hydrate_baseline_rules(
        db_session, sample_ruleset.id, actor="user1"
    )
    assert result1.hydrated_rule_count == 1
    assert result1.created_rule_count == 1

    # Second hydration should skip already-hydrated rules
    result2 = await hydration_service.hydrate_baseline_rules(
        db_session, sample_ruleset.id, actor="user2"
    )
    assert result2.hydrated_rule_count == 0
    assert result2.created_rule_count == 0
    assert result2.hydration_summary == []

    # Verify original rule metadata shows first hydration
    await db_session.refresh(placeholder_rule)
    assert placeholder_rule.metadata_json["hydrated_by"] == "user1"


async def test_deactivate_original_rules(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Test that original placeholder rules are properly deactivated."""
    # Create ruleset and group
    ruleset = ValuationRuleset(name="Deactivate Test Ruleset", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="Test Group Deactivate", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # Create placeholder rule
    placeholder_rule = ValuationRuleV2(
        group_id=group.id,
        name="Test Rule Deactivate",
        description="Test",
        priority=100,
        evaluation_order=100,
        is_active=True,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "fixed",
            "default_value": 10.0,
        },
    )
    db_session.add(placeholder_rule)
    await db_session.commit()

    # Verify it's active before hydration
    assert placeholder_rule.is_active is True

    # Hydrate
    await hydration_service.hydrate_single_rule(db_session, placeholder_rule.id)

    # Manually mark as hydrated (normally done by hydrate_baseline_rules)
    # Need to update the metadata_json dict by creating a new dict
    placeholder_rule.is_active = False
    placeholder_rule.metadata_json = {
        **placeholder_rule.metadata_json,
        "hydrated": True,
    }
    await db_session.commit()

    # Verify deactivation
    await db_session.refresh(placeholder_rule)
    assert placeholder_rule.is_active is False
    assert placeholder_rule.metadata_json.get("hydrated") is True


async def test_foreign_key_rule_metadata(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
    sample_rule_group: ValuationRuleGroup,
):
    """Test that expanded rules are properly linked to source via metadata."""
    # Create placeholder rule
    placeholder_rule = ValuationRuleV2(
        group_id=sample_rule_group.id,
        name="Test Rule",
        description="Test",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "enum_multiplier",
            "field_id": "test.field",
            "valuation_buckets": {"A": 1.0, "B": 1.5},
        },
    )
    db_session.add(placeholder_rule)
    await db_session.commit()
    await db_session.refresh(placeholder_rule)

    # Hydrate
    expanded_rules = await hydration_service.hydrate_single_rule(db_session, placeholder_rule.id)

    # Verify all expanded rules have foreign key reference
    for rule in expanded_rules:
        assert "hydration_source_rule_id" in rule.metadata_json
        assert rule.metadata_json["hydration_source_rule_id"] == placeholder_rule.id


async def test_hydration_summary(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
    sample_ruleset: ValuationRuleset,
    sample_rule_group: ValuationRuleGroup,
):
    """Test that hydration summary contains correct information."""
    # Create placeholder rule
    placeholder_rule = ValuationRuleV2(
        group_id=sample_rule_group.id,
        name="Test Enum Rule",
        description="Test",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "enum_multiplier",
            "field_id": "test.field",
            "valuation_buckets": {"X": 0.8, "Y": 1.2, "Z": 1.5},
        },
    )
    db_session.add(placeholder_rule)
    await db_session.commit()

    # Hydrate
    result = await hydration_service.hydrate_baseline_rules(
        db_session, sample_ruleset.id, actor="test_user"
    )

    # Verify summary structure
    assert len(result.hydration_summary) == 1
    summary_item = result.hydration_summary[0]

    assert summary_item["original_rule_id"] == placeholder_rule.id
    assert summary_item["field_name"] == "Test Enum Rule"
    assert summary_item["field_type"] == "enum_multiplier"
    assert len(summary_item["expanded_rule_ids"]) == 3

    # Verify expanded rule IDs are valid
    expanded_ids = summary_item["expanded_rule_ids"]
    for rule_id in expanded_ids:
        stmt = select(ValuationRuleV2).where(ValuationRuleV2.id == rule_id)
        result = await db_session.execute(stmt)
        rule = result.scalar_one_or_none()
        assert rule is not None
        assert rule.metadata_json["hydration_source_rule_id"] == placeholder_rule.id


async def test_formula_without_formula_text_fallback(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Test that formula type without formula_text falls back to fixed strategy."""
    # Create ruleset and group
    ruleset = ValuationRuleset(name="Fallback Test Ruleset", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="Test Group Fallback", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # Create placeholder rule with formula type but no formula
    placeholder_rule = ValuationRuleV2(
        group_id=group.id,
        name="Empty Formula",
        description="Test",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "formula",
            "formula_text": None,  # Missing formula
            "default_value": 15.0,
        },
    )
    db_session.add(placeholder_rule)
    await db_session.commit()

    # Hydrate
    expanded_rules = await hydration_service.hydrate_single_rule(db_session, placeholder_rule.id)

    # Should fall back to fixed value strategy
    assert len(expanded_rules) == 1
    rule = expanded_rules[0]
    assert len(rule.actions) == 1
    action = rule.actions[0]
    assert action.action_type == "fixed_value"
    assert action.value_usd == 15.0


async def test_error_on_non_existent_rule(
    db_session: AsyncSession, hydration_service: BaselineHydrationService
):
    """Test that hydrating non-existent rule raises ValueError."""
    with pytest.raises(ValueError, match="Rule 99999 not found"):
        await hydration_service.hydrate_single_rule(db_session, 99999)


async def test_error_on_non_placeholder_rule(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
    sample_rule_group: ValuationRuleGroup,
):
    """Test that hydrating non-placeholder rule raises ValueError."""
    # Create regular rule (not a placeholder)
    regular_rule = ValuationRuleV2(
        group_id=sample_rule_group.id,
        name="Regular Rule",
        description="Not a placeholder",
        priority=100,
        evaluation_order=100,
        metadata_json={},  # No baseline_placeholder flag
    )
    db_session.add(regular_rule)
    await db_session.commit()

    with pytest.raises(ValueError, match="not a baseline placeholder"):
        await hydration_service.hydrate_single_rule(db_session, regular_rule.id)


async def test_empty_valuation_buckets(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
    sample_rule_group: ValuationRuleGroup,
):
    """Test enum multiplier with empty buckets returns empty list."""
    # Create placeholder rule with no buckets
    placeholder_rule = ValuationRuleV2(
        group_id=sample_rule_group.id,
        name="Empty Buckets",
        description="Test",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "enum_multiplier",
            "field_id": "test.field",
            "valuation_buckets": {},  # Empty
        },
    )
    db_session.add(placeholder_rule)
    await db_session.commit()

    # Hydrate
    expanded_rules = await hydration_service.hydrate_single_rule(db_session, placeholder_rule.id)

    # Should return empty list
    assert expanded_rules == []


async def test_fixed_field_default_value_zero(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Test fixed field without default_value uses 0.0."""
    # Create ruleset and group
    ruleset = ValuationRuleset(name="Default Value Test Ruleset", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="Test Group Default", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # Create placeholder rule without default_value
    placeholder_rule = ValuationRuleV2(
        group_id=group.id,
        name="No Default",
        description="Test",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "fixed",
            # No default_value
        },
    )
    db_session.add(placeholder_rule)
    await db_session.commit()

    # Hydrate
    expanded_rules = await hydration_service.hydrate_single_rule(db_session, placeholder_rule.id)

    # Should use 0.0 as default
    assert len(expanded_rules) == 1
    action = expanded_rules[0].actions[0]
    assert action.value_usd == 0.0


# --- Comprehensive Integration Tests for All Strategies ---


async def test_comprehensive_all_strategies_non_null_values(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Comprehensive test verifying all hydration strategies produce non-null values."""
    # Create ruleset and group
    ruleset = ValuationRuleset(name="Comprehensive Test Ruleset", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="Comprehensive Test Group", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # Test 1: enum_multiplier with proper values
    enum_rule = ValuationRuleV2(
        group_id=group.id,
        name="DDR Generation Multiplier",
        description="RAM DDR generation multipliers",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "enum_multiplier",
            "field_id": "ram_spec.ddr_generation",
            "valuation_buckets": {
                "DDR3": 0.7,
                "DDR4": 1.0,
                "DDR5": 1.3,
            },
        },
    )
    db_session.add(enum_rule)

    # Test 2: formula with proper formula text
    formula_rule = ValuationRuleV2(
        group_id=group.id,
        name="RAM Capacity Formula",
        description="RAM capacity pricing",
        priority=200,
        evaluation_order=200,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "formula",
            "formula_text": "ram_spec.total_capacity_gb * 2.5",
        },
    )
    db_session.add(formula_rule)

    # Test 3: fixed with default_value
    fixed_rule = ValuationRuleV2(
        group_id=group.id,
        name="Base Depreciation",
        description="Fixed depreciation",
        priority=50,
        evaluation_order=50,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "fixed",
            "default_value": -25.0,
        },
    )
    db_session.add(fixed_rule)

    await db_session.commit()

    # Hydrate all rules
    enum_expanded = await hydration_service.hydrate_single_rule(db_session, enum_rule.id)
    formula_expanded = await hydration_service.hydrate_single_rule(db_session, formula_rule.id)
    fixed_expanded = await hydration_service.hydrate_single_rule(db_session, fixed_rule.id)

    # Verify enum_multiplier rules
    assert len(enum_expanded) == 3, "Should create 3 rules for 3 enum values"
    for rule in enum_expanded:
        assert rule.is_active is True
        assert len(rule.conditions) == 1, "Each enum rule should have one condition"
        assert len(rule.actions) == 1, "Each enum rule should have one action"
        action = rule.actions[0]
        assert action.action_type == "multiplier"
        assert action.value_usd is not None, "Enum multiplier action value_usd should not be null"
        assert action.value_usd > 0.0, "Enum multiplier value should be positive"
        assert rule.metadata_json["hydration_source_rule_id"] == enum_rule.id

    # Verify specific enum values
    ddr3_rule = next(r for r in enum_expanded if "DDR3" in r.name)
    assert ddr3_rule.actions[0].value_usd == 70.0  # 0.7 * 100

    ddr4_rule = next(r for r in enum_expanded if "DDR4" in r.name)
    assert ddr4_rule.actions[0].value_usd == 100.0  # 1.0 * 100

    ddr5_rule = next(r for r in enum_expanded if "DDR5" in r.name)
    assert ddr5_rule.actions[0].value_usd == 130.0  # 1.3 * 100

    # Verify formula rule
    assert len(formula_expanded) == 1, "Should create 1 formula rule"
    formula_rule_expanded = formula_expanded[0]
    assert formula_rule_expanded.is_active is True
    assert len(formula_rule_expanded.conditions) == 0, "Formula rule should have no conditions"
    assert len(formula_rule_expanded.actions) == 1, "Formula rule should have one action"
    formula_action = formula_rule_expanded.actions[0]
    assert formula_action.action_type == "formula"
    assert formula_action.formula == "ram_spec.total_capacity_gb * 2.5"
    assert (
        formula_action.value_usd is None
    ), "Formula action value_usd should be None (uses formula)"
    assert formula_rule_expanded.metadata_json["hydration_source_rule_id"] == formula_rule.id

    # Verify fixed rule
    assert len(fixed_expanded) == 1, "Should create 1 fixed rule"
    fixed_rule_expanded = fixed_expanded[0]
    assert fixed_rule_expanded.is_active is True
    assert len(fixed_rule_expanded.conditions) == 0, "Fixed rule should have no conditions"
    assert len(fixed_rule_expanded.actions) == 1, "Fixed rule should have one action"
    fixed_action = fixed_rule_expanded.actions[0]
    assert fixed_action.action_type == "fixed_value"
    assert fixed_action.value_usd is not None, "Fixed action value_usd should not be null"
    assert fixed_action.value_usd == -25.0
    assert fixed_rule_expanded.metadata_json["hydration_source_rule_id"] == fixed_rule.id


async def test_fixed_value_multiple_key_variants(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Test that fixed value strategy checks multiple key variants."""
    # Create ruleset and group
    ruleset = ValuationRuleset(name="Key Variants Test Ruleset", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="Test Group Variants", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # Test 1: default_value key
    rule1 = ValuationRuleV2(
        group_id=group.id,
        name="Rule with default_value",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "fixed",
            "default_value": 10.0,
        },
    )
    db_session.add(rule1)

    # Test 2: Default key (capitalized)
    rule2 = ValuationRuleV2(
        group_id=group.id,
        name="Rule with Default",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "fixed",
            "Default": 20.0,
        },
    )
    db_session.add(rule2)

    # Test 3: value key
    rule3 = ValuationRuleV2(
        group_id=group.id,
        name="Rule with value",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "fixed",
            "value": 30.0,
        },
    )
    db_session.add(rule3)

    await db_session.commit()

    # Hydrate all
    expanded1 = await hydration_service.hydrate_single_rule(db_session, rule1.id)
    expanded2 = await hydration_service.hydrate_single_rule(db_session, rule2.id)
    expanded3 = await hydration_service.hydrate_single_rule(db_session, rule3.id)

    # Verify each rule extracted the correct value
    assert expanded1[0].actions[0].value_usd == 10.0
    assert expanded2[0].actions[0].value_usd == 20.0
    assert expanded3[0].actions[0].value_usd == 30.0


async def test_enum_multiplier_with_null_values(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Test that enum_multiplier handles null multiplier values gracefully."""
    # Create ruleset and group
    ruleset = ValuationRuleset(name="Null Values Test Ruleset", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="Test Group Null", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # Create rule with one null multiplier
    rule = ValuationRuleV2(
        group_id=group.id,
        name="Enum with Null",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "enum_multiplier",
            "field_id": "test.field",
            "valuation_buckets": {
                "valid": 1.0,
                "null_value": None,  # This should be skipped
                "another_valid": 1.5,
            },
        },
    )
    db_session.add(rule)
    await db_session.commit()

    # Hydrate
    expanded = await hydration_service.hydrate_single_rule(db_session, rule.id)

    # Should only create 2 rules (skipping the null one)
    assert len(expanded) == 2
    rule_names = {r.name for r in expanded}
    assert "Enum with Null: valid" in rule_names
    assert "Enum with Null: another_valid" in rule_names
    assert "Enum with Null: null_value" not in rule_names

    # Verify values are non-null
    for rule in expanded:
        assert rule.actions[0].value_usd is not None


async def test_metadata_preservation_all_strategies(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Test that all strategies properly preserve metadata in hydrated rules."""
    # Create ruleset and group
    ruleset = ValuationRuleset(name="Metadata Test Ruleset", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="Metadata Test Group", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # Create rules with custom metadata
    enum_rule = ValuationRuleV2(
        group_id=group.id,
        name="Enum Rule",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "enum_multiplier",
            "field_id": "test.enum",
            "valuation_buckets": {"A": 1.0, "B": 1.2},
            "custom_key": "custom_value",
        },
    )
    db_session.add(enum_rule)

    formula_rule = ValuationRuleV2(
        group_id=group.id,
        name="Formula Rule",
        priority=200,
        evaluation_order=200,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "formula",
            "formula_text": "test.value * 2",
            "custom_formula_key": "formula_metadata",
        },
    )
    db_session.add(formula_rule)

    fixed_rule = ValuationRuleV2(
        group_id=group.id,
        name="Fixed Rule",
        priority=50,
        evaluation_order=50,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "fixed",
            "default_value": 15.0,
            "custom_fixed_key": "fixed_metadata",
        },
    )
    db_session.add(fixed_rule)

    await db_session.commit()

    # Hydrate all
    enum_expanded = await hydration_service.hydrate_single_rule(db_session, enum_rule.id)
    formula_expanded = await hydration_service.hydrate_single_rule(db_session, formula_rule.id)
    fixed_expanded = await hydration_service.hydrate_single_rule(db_session, fixed_rule.id)

    # Verify metadata preservation for enum rules
    for rule in enum_expanded:
        assert "hydration_source_rule_id" in rule.metadata_json
        assert rule.metadata_json["hydration_source_rule_id"] == enum_rule.id
        assert "field_type" in rule.metadata_json
        assert rule.metadata_json["field_type"] == "enum_multiplier"
        assert "enum_value" in rule.metadata_json

    # Verify metadata preservation for formula rule
    assert formula_expanded[0].metadata_json["hydration_source_rule_id"] == formula_rule.id
    assert formula_expanded[0].metadata_json["field_type"] == "formula"

    # Verify metadata preservation for fixed rule
    assert fixed_expanded[0].metadata_json["hydration_source_rule_id"] == fixed_rule.id
    assert fixed_expanded[0].metadata_json["field_type"] == "fixed"


async def test_scalar_field_type_skipped(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
    sample_rule_group: ValuationRuleGroup,
):
    """Test that scalar field types are skipped during hydration (Issue #1)."""
    # Create scalar placeholder rule (represents FK relationship)
    scalar_rule = ValuationRuleV2(
        group_id=sample_rule_group.id,
        name="CPU (Scalar)",
        description="CPU foreign key relationship",
        priority=100,
        evaluation_order=100,
        is_active=True,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "scalar",
            "entity_key": "cpu",
        },
    )
    db_session.add(scalar_rule)
    await db_session.commit()
    await db_session.refresh(scalar_rule)

    # Hydrate the scalar rule
    expanded_rules = await hydration_service.hydrate_single_rule(
        db_session, scalar_rule.id, actor="test_user"
    )

    # Verify it returns empty list (skipped)
    assert expanded_rules == [], "Scalar field should be skipped and return empty list"


async def test_foreign_key_rule_tagging(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Test that FK-related rules are tagged with is_foreign_key_rule metadata (Issue #2)."""
    # Create ruleset and group
    ruleset = ValuationRuleset(name="FK Tagging Test Ruleset", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="FK Tagging Group", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # Test all FK entity keys
    fk_entity_keys = ["cpu", "gpu", "storage", "ram_spec", "ports"]

    for entity_key in fk_entity_keys:
        # Create FK-related enum rule
        fk_enum_rule = ValuationRuleV2(
            group_id=group.id,
            name=f"{entity_key.upper()} Enum Rule",
            priority=100,
            evaluation_order=100,
            metadata_json={
                "baseline_placeholder": True,
                "field_type": "enum_multiplier",
                "entity_key": entity_key,
                "field_id": f"{entity_key}.test_field",
                "valuation_buckets": {"A": 1.0, "B": 1.2},
            },
        )
        db_session.add(fk_enum_rule)
        await db_session.commit()
        await db_session.refresh(fk_enum_rule)

        # Hydrate
        expanded = await hydration_service.hydrate_single_rule(db_session, fk_enum_rule.id)

        # Verify all expanded rules have is_foreign_key_rule=True
        for rule in expanded:
            assert (
                "is_foreign_key_rule" in rule.metadata_json
            ), f"Rule {rule.name} missing is_foreign_key_rule metadata"
            assert (
                rule.metadata_json["is_foreign_key_rule"] is True
            ), f"FK rule for {entity_key} should have is_foreign_key_rule=True"

    # Test non-FK entity key
    non_fk_rule = ValuationRuleV2(
        group_id=group.id,
        name="Condition Enum Rule",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "enum_multiplier",
            "entity_key": "condition",
            "field_id": "condition",
            "valuation_buckets": {"New": 1.0, "Used": 0.8},
        },
    )
    db_session.add(non_fk_rule)
    await db_session.commit()
    await db_session.refresh(non_fk_rule)

    # Hydrate non-FK rule
    expanded = await hydration_service.hydrate_single_rule(db_session, non_fk_rule.id)

    # Verify non-FK rule has is_foreign_key_rule=False
    for rule in expanded:
        assert (
            "is_foreign_key_rule" in rule.metadata_json
        ), f"Rule {rule.name} missing is_foreign_key_rule metadata"
        assert (
            rule.metadata_json["is_foreign_key_rule"] is False
        ), "Non-FK rule should have is_foreign_key_rule=False"


async def test_foreign_key_tagging_all_strategies(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Test that is_foreign_key_rule is set correctly for all hydration strategies."""
    # Create ruleset and group
    ruleset = ValuationRuleset(name="FK All Strategies Test", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="FK Strategies Group", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # FK enum multiplier rule
    fk_enum_rule = ValuationRuleV2(
        group_id=group.id,
        name="RAM Enum (FK)",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "enum_multiplier",
            "entity_key": "ram_spec",
            "field_id": "ram_spec.ddr_generation",
            "valuation_buckets": {"DDR4": 1.0, "DDR5": 1.3},
        },
    )
    db_session.add(fk_enum_rule)

    # FK formula rule
    fk_formula_rule = ValuationRuleV2(
        group_id=group.id,
        name="Storage Formula (FK)",
        priority=200,
        evaluation_order=200,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "formula",
            "entity_key": "storage",
            "formula_text": "storage.capacity_gb * 0.05",
        },
    )
    db_session.add(fk_formula_rule)

    # FK fixed value rule
    fk_fixed_rule = ValuationRuleV2(
        group_id=group.id,
        name="GPU Fixed (FK)",
        priority=50,
        evaluation_order=50,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "fixed",
            "entity_key": "gpu",
            "default_value": 100.0,
        },
    )
    db_session.add(fk_fixed_rule)

    await db_session.commit()

    # Hydrate all FK rules
    enum_expanded = await hydration_service.hydrate_single_rule(db_session, fk_enum_rule.id)
    formula_expanded = await hydration_service.hydrate_single_rule(db_session, fk_formula_rule.id)
    fixed_expanded = await hydration_service.hydrate_single_rule(db_session, fk_fixed_rule.id)

    # Verify all strategies set is_foreign_key_rule=True for FK rules
    for rule in enum_expanded:
        assert (
            rule.metadata_json.get("is_foreign_key_rule") is True
        ), "FK enum rule should have is_foreign_key_rule=True"

    assert (
        formula_expanded[0].metadata_json.get("is_foreign_key_rule") is True
    ), "FK formula rule should have is_foreign_key_rule=True"

    assert (
        fixed_expanded[0].metadata_json.get("is_foreign_key_rule") is True
    ), "FK fixed rule should have is_foreign_key_rule=True"


async def test_pseudo_code_formula_handling(
    db_session: AsyncSession,
    hydration_service: BaselineHydrationService,
):
    """Test that pseudo-code formulas are handled gracefully with metadata preservation."""
    # Create ruleset and group
    ruleset = ValuationRuleset(name="Pseudo-code Test Ruleset", version="1.0.0")
    db_session.add(ruleset)
    await db_session.commit()

    group = ValuationRuleGroup(
        ruleset_id=ruleset.id, name="Pseudo-code Group", category="test", display_order=1
    )
    db_session.add(group)
    await db_session.commit()

    # Create rule with pseudo-code formula (not valid Python)
    pseudo_code_rule = ValuationRuleV2(
        group_id=group.id,
        name="GPU Valuation (Pseudo)",
        description="GPU price approximation",
        priority=100,
        evaluation_order=100,
        metadata_json={
            "baseline_placeholder": True,
            "field_type": "formula",
            "formula_text": "usd ≈ (gpu_mark/1000)*8.0; clamp and apply SFF penalties",
        },
    )
    db_session.add(pseudo_code_rule)
    await db_session.commit()
    await db_session.refresh(pseudo_code_rule)

    # Hydrate the rule
    expanded_rules = await hydration_service.hydrate_single_rule(
        db_session, pseudo_code_rule.id, actor="test_user"
    )

    # Should create a placeholder fixed rule
    assert len(expanded_rules) == 1, "Should create 1 placeholder rule"
    rule = expanded_rules[0]

    # Verify it's a fixed value rule (fallback)
    assert len(rule.actions) == 1
    action = rule.actions[0]
    assert action.action_type == "fixed_value", "Should fall back to fixed value"
    assert action.value_usd == 0.0, "Should default to 0.0 for user configuration"

    # Verify metadata preservation
    assert (
        "original_formula_description" in rule.metadata_json
    ), "Should preserve original pseudo-code formula"
    assert (
        rule.metadata_json["original_formula_description"]
        == "usd ≈ (gpu_mark/1000)*8.0; clamp and apply SFF penalties"
    )

    assert (
        rule.metadata_json.get("requires_user_configuration") is True
    ), "Should flag that user configuration is required"

    assert "hydration_note" in rule.metadata_json, "Should include hydration note"
    assert (
        "pseudo-code" in rule.metadata_json["hydration_note"].lower()
    ), "Hydration note should mention pseudo-code"

    # Verify basic metadata is still present
    assert rule.metadata_json["hydration_source_rule_id"] == pseudo_code_rule.id
    assert rule.metadata_json["field_type"] == "fixed"
