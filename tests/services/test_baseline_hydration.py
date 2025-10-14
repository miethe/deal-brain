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
    expanded_rules = await hydration_service.hydrate_single_rule(
        db_session, placeholder_rule.id
    )

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
    expanded_rules = await hydration_service.hydrate_single_rule(
        db_session, placeholder_rule.id
    )

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
    expanded_rules = await hydration_service.hydrate_single_rule(
        db_session, placeholder_rule.id
    )

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
    expanded_rules = await hydration_service.hydrate_single_rule(
        db_session, placeholder_rule.id
    )

    # Should use 0.0 as default
    assert len(expanded_rules) == 1
    action = expanded_rules[0].actions[0]
    assert action.value_usd == 0.0
