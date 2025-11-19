"""
Integration tests for multi-ruleset evaluation with baseline precedence.

Tests that the system properly evaluates multiple rulesets in priority order
and maintains correct layer attribution in valuation breakdowns.
"""

import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from dealbrain_api.models.core import (
    Listing,
    Cpu,
    Gpu,
    ValuationRuleset,
    ValuationRuleGroup,
    ValuationRuleV2,
    ValuationRuleCondition,
    ValuationRuleAction,
)
from dealbrain_api.services.rule_evaluation import RuleEvaluationService
from dealbrain_api.services.baseline_loader import BaselineLoaderService
from dealbrain_api.db import Base

# Try to import aiosqlite
try:
    import aiosqlite

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide an isolated in-memory database session for tests."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping multi-ruleset evaluation tests")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.fixture
async def evaluation_service():
    """Create RuleEvaluationService instance."""
    return RuleEvaluationService()


@pytest.fixture
async def baseline_loader():
    """Create BaselineLoaderService instance."""
    return BaselineLoaderService()


@pytest.fixture
async def sample_cpu(db_session: AsyncSession) -> Cpu:
    """Create a sample CPU for testing."""
    cpu = Cpu(
        name="Intel Core i7-12700K",
        manufacturer="Intel",
        cores=12,
        threads=20,
        tdp_w=125,
        cpu_mark_single=4116,
        cpu_mark_multi=35228,
        release_year=2021,
    )
    db_session.add(cpu)
    await db_session.commit()
    await db_session.refresh(cpu)
    return cpu


@pytest.fixture
async def sample_gpu(db_session: AsyncSession) -> Gpu:
    """Create a sample GPU for testing."""
    gpu = Gpu(
        name="NVIDIA RTX 3070",
        manufacturer="NVIDIA",
        vram_gb=8,
        tdp_w=220,
        gpu_mark=22699,
        release_year=2020,
    )
    db_session.add(gpu)
    await db_session.commit()
    await db_session.refresh(gpu)
    return gpu


@pytest.fixture
async def sample_listing(db_session: AsyncSession, sample_cpu: Cpu, sample_gpu: Gpu) -> Listing:
    """Create a sample listing for testing."""
    listing = Listing(
        source="test",
        seller="Test Seller",
        device_model="Gaming PC",
        condition="used",
        price_usd=Decimal("1200.00"),
        base_price_usd=Decimal("1200.00"),
        adjusted_price_usd=Decimal("1200.00"),
        cpu_id=sample_cpu.id,
        gpu_id=sample_gpu.id,
        ram_gb=32,
        primary_storage_gb=1000,
        primary_storage_type="NVMe SSD",
        has_wifi=True,
        has_bluetooth=True,
        valuation_breakdown={},
        status="active",
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)
    return listing


@pytest.fixture
async def baseline_ruleset(db_session: AsyncSession) -> ValuationRuleset:
    """Create a baseline ruleset with priority=5."""
    ruleset = ValuationRuleset(
        name="System: Baseline v1.0",
        description="System baseline valuation ruleset",
        version="1.0",
        priority=5,  # Baseline priority
        is_active=True,
        metadata_json={
            "system_baseline": True,
            "source_version": "1.0",
            "read_only": True,
        },
        created_by="system",
    )
    db_session.add(ruleset)
    await db_session.commit()
    await db_session.refresh(ruleset)
    return ruleset


@pytest.fixture
async def standard_ruleset(db_session: AsyncSession) -> ValuationRuleset:
    """Create a standard ruleset with priority=10."""
    ruleset = ValuationRuleset(
        name="Standard Valuation",
        description="Standard valuation rules",
        version="1.0",
        priority=10,  # Standard priority
        is_active=True,
        metadata_json={},
        created_by="admin",
    )
    db_session.add(ruleset)
    await db_session.commit()
    await db_session.refresh(ruleset)
    return ruleset


@pytest.fixture
async def advanced_ruleset(db_session: AsyncSession) -> ValuationRuleset:
    """Create an advanced ruleset with priority=20."""
    ruleset = ValuationRuleset(
        name="Advanced Valuation",
        description="Advanced custom rules",
        version="1.0",
        priority=20,  # Advanced priority
        is_active=True,
        metadata_json={},
        created_by="power_user",
    )
    db_session.add(ruleset)
    await db_session.commit()
    await db_session.refresh(ruleset)
    return ruleset


async def create_simple_rule(
    db_session: AsyncSession,
    ruleset_id: int,
    group_name: str,
    rule_name: str,
    adjustment_value: float,
    condition_field: str = "ram_gb",
    condition_value: int = 32,
) -> ValuationRuleV2:
    """Helper to create a simple rule with a single condition and action."""
    # Create group
    group = ValuationRuleGroup(
        ruleset_id=ruleset_id,
        name=group_name,
        category="test",
        display_order=1,
        is_active=True,
    )
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    # Create rule
    rule = ValuationRuleV2(
        group_id=group.id,
        name=rule_name,
        description=f"Test rule: {rule_name}",
        priority=100,
        evaluation_order=100,
        is_active=True,
        created_by="test",
    )
    db_session.add(rule)
    await db_session.commit()
    await db_session.refresh(rule)

    # Create condition
    condition = ValuationRuleCondition(
        rule_id=rule.id,
        field_name=condition_field,
        field_type="numeric",
        operator=">=",
        value_json=condition_value,
        logical_operator="AND",
    )
    db_session.add(condition)

    # Create action
    action = ValuationRuleAction(
        rule_id=rule.id,
        action_type="fixed_value",
        value_usd=Decimal(str(adjustment_value)),
        description=f"Add ${adjustment_value}",
    )
    db_session.add(action)

    await db_session.commit()
    await db_session.refresh(rule)
    return rule


class TestMultiRulesetEvaluation:
    """Test multi-ruleset evaluation with proper precedence."""

    @pytest.mark.asyncio
    async def test_evaluates_multiple_rulesets_in_priority_order(
        self,
        db_session: AsyncSession,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
        baseline_ruleset: ValuationRuleset,
        standard_ruleset: ValuationRuleset,
        advanced_ruleset: ValuationRuleset,
    ):
        """Test that multiple active rulesets are evaluated in priority order."""
        # Create rules in each ruleset
        await create_simple_rule(
            db_session,
            baseline_ruleset.id,
            "Baseline RAM",
            "Baseline RAM Adjustment",
            50.0,  # $50 baseline adjustment
        )

        await create_simple_rule(
            db_session,
            standard_ruleset.id,
            "Standard RAM",
            "Standard RAM Bonus",
            25.0,  # $25 standard adjustment
        )

        await create_simple_rule(
            db_session,
            advanced_ruleset.id,
            "Advanced RAM",
            "Advanced RAM Premium",
            10.0,  # $10 advanced adjustment
        )

        # Evaluate listing (should evaluate all rulesets)
        result = await evaluation_service.evaluate_listing(db_session, sample_listing.id)

        # Verify results
        assert result["total_adjustment"] == 85.0  # 50 + 25 + 10
        assert result["adjusted_price"] == 1285.0  # 1200 + 85
        assert result["matched_rules_count"] == 3

        # Verify layer attribution
        assert "layers" in result
        layers = result["layers"]

        # Check baseline layer
        assert "baseline" in layers
        assert layers["baseline"]["adjustment"] == 50.0
        assert layers["baseline"]["ruleset_id"] == baseline_ruleset.id
        assert len(layers["baseline"]["matched_rules"]) == 1

        # Check basic layer (standard ruleset with priority=10)
        assert "basic" in layers
        assert layers["basic"]["adjustment"] == 25.0
        assert layers["basic"]["ruleset_id"] == standard_ruleset.id
        assert len(layers["basic"]["matched_rules"]) == 1

        # Check advanced layer
        assert "advanced" in layers
        assert layers["advanced"]["adjustment"] == 10.0
        assert layers["advanced"]["ruleset_id"] == advanced_ruleset.id
        assert len(layers["advanced"]["matched_rules"]) == 1

        # Verify rulesets were evaluated in correct order
        rulesets_evaluated = result["rulesets_evaluated"]
        assert len(rulesets_evaluated) == 3
        assert rulesets_evaluated[0]["priority"] == 5  # Baseline first
        assert rulesets_evaluated[1]["priority"] == 10  # Standard second
        assert rulesets_evaluated[2]["priority"] == 20  # Advanced third

    @pytest.mark.asyncio
    async def test_single_ruleset_evaluation_when_specified(
        self,
        db_session: AsyncSession,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
        baseline_ruleset: ValuationRuleset,
        standard_ruleset: ValuationRuleset,
    ):
        """Test that only specified ruleset is evaluated when ruleset_id is provided."""
        # Create rules in both rulesets
        await create_simple_rule(
            db_session,
            baseline_ruleset.id,
            "Baseline RAM",
            "Baseline RAM Adjustment",
            50.0,
        )

        await create_simple_rule(
            db_session,
            standard_ruleset.id,
            "Standard RAM",
            "Standard RAM Bonus",
            25.0,
        )

        # Evaluate with specific ruleset
        result = await evaluation_service.evaluate_listing(
            db_session, sample_listing.id, ruleset_id=standard_ruleset.id
        )

        # Should only evaluate the specified ruleset
        assert result["total_adjustment"] == 25.0  # Only standard adjustment
        assert result["matched_rules_count"] == 1
        assert len(result["rulesets_evaluated"]) == 1
        assert result["rulesets_evaluated"][0]["id"] == standard_ruleset.id

    @pytest.mark.asyncio
    async def test_breakdown_stored_with_layer_attribution(
        self,
        db_session: AsyncSession,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
        baseline_ruleset: ValuationRuleset,
        standard_ruleset: ValuationRuleset,
    ):
        """Test that valuation breakdown is stored with proper layer attribution."""
        # Create rules
        await create_simple_rule(
            db_session,
            baseline_ruleset.id,
            "Baseline RAM",
            "Baseline RAM Adjustment",
            50.0,
        )

        await create_simple_rule(
            db_session,
            standard_ruleset.id,
            "Standard RAM",
            "Standard RAM Bonus",
            25.0,
        )

        # Apply rulesets to listing
        result = await evaluation_service.apply_ruleset_to_listing(db_session, sample_listing.id)

        # Refresh listing to get updated data
        await db_session.refresh(sample_listing)

        # Verify breakdown structure
        breakdown = sample_listing.valuation_breakdown
        assert breakdown is not None
        assert breakdown["total_adjustment"] == 75.0
        assert "layers" in breakdown
        assert "baseline" in breakdown["layers"]
        assert "basic" in breakdown["layers"]
        assert "rulesets_evaluated" in breakdown
        assert "evaluated_at" in breakdown

        # Verify flattened matched_rules for backward compatibility
        assert "matched_rules" in breakdown
        matched_rules = breakdown["matched_rules"]
        assert len(matched_rules) == 2

        # Each rule should have layer attribution
        for rule in matched_rules:
            assert "layer" in rule
            assert "ruleset_id" in rule
            assert "ruleset_name" in rule

    @pytest.mark.asyncio
    async def test_inactive_rulesets_are_skipped(
        self,
        db_session: AsyncSession,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
        baseline_ruleset: ValuationRuleset,
        standard_ruleset: ValuationRuleset,
    ):
        """Test that inactive rulesets are not evaluated."""
        # Create rules
        await create_simple_rule(
            db_session,
            baseline_ruleset.id,
            "Baseline RAM",
            "Baseline RAM Adjustment",
            50.0,
        )

        await create_simple_rule(
            db_session,
            standard_ruleset.id,
            "Standard RAM",
            "Standard RAM Bonus",
            25.0,
        )

        # Deactivate standard ruleset
        standard_ruleset.is_active = False
        await db_session.commit()

        # Evaluate
        result = await evaluation_service.evaluate_listing(db_session, sample_listing.id)

        # Should only evaluate baseline
        assert result["total_adjustment"] == 50.0
        assert result["matched_rules_count"] == 1
        assert len(result["rulesets_evaluated"]) == 1
        assert result["rulesets_evaluated"][0]["id"] == baseline_ruleset.id

    @pytest.mark.asyncio
    async def test_excluded_rulesets_are_skipped(
        self,
        db_session: AsyncSession,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
        baseline_ruleset: ValuationRuleset,
        standard_ruleset: ValuationRuleset,
    ):
        """Test that excluded rulesets are not evaluated."""
        # Create rules
        await create_simple_rule(
            db_session,
            baseline_ruleset.id,
            "Baseline RAM",
            "Baseline RAM Adjustment",
            50.0,
        )

        await create_simple_rule(
            db_session,
            standard_ruleset.id,
            "Standard RAM",
            "Standard RAM Bonus",
            25.0,
        )

        # Add baseline to excluded rulesets for this listing
        sample_listing.attributes_json = {"valuation_disabled_rulesets": [baseline_ruleset.id]}
        await db_session.commit()

        # Evaluate
        result = await evaluation_service.evaluate_listing(db_session, sample_listing.id)

        # Should only evaluate standard
        assert result["total_adjustment"] == 25.0
        assert result["matched_rules_count"] == 1
        assert len(result["rulesets_evaluated"]) == 1
        assert result["rulesets_evaluated"][0]["id"] == standard_ruleset.id

    @pytest.mark.asyncio
    async def test_conditional_ruleset_matching(
        self,
        db_session: AsyncSession,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
        baseline_ruleset: ValuationRuleset,
    ):
        """Test that rulesets with conditions are only evaluated when conditions match."""
        # Create a conditional ruleset that matches high-end systems
        conditional_ruleset = ValuationRuleset(
            name="High-End System Rules",
            description="Rules for high-end systems",
            version="1.0",
            priority=15,
            is_active=True,
            conditions_json={
                "field_name": "ram_gb",
                "operator": ">=",
                "value": 64,  # Only for 64GB+ systems
            },
            created_by="admin",
        )
        db_session.add(conditional_ruleset)
        await db_session.commit()

        await create_simple_rule(
            db_session,
            baseline_ruleset.id,
            "Baseline",
            "Baseline Adjustment",
            50.0,
        )

        await create_simple_rule(
            db_session,
            conditional_ruleset.id,
            "High-End",
            "High-End Bonus",
            100.0,
        )

        # Evaluate with 32GB listing (doesn't match conditional)
        result = await evaluation_service.evaluate_listing(db_session, sample_listing.id)

        # Should only get baseline
        assert result["total_adjustment"] == 50.0
        assert len(result["rulesets_evaluated"]) == 1

        # Update listing to 64GB
        sample_listing.ram_gb = 64
        await db_session.commit()

        # Re-evaluate
        result = await evaluation_service.evaluate_listing(db_session, sample_listing.id)

        # Now should get both rulesets
        assert result["total_adjustment"] == 150.0  # 50 + 100
        assert len(result["rulesets_evaluated"]) == 2

    @pytest.mark.asyncio
    async def test_layer_type_detection(
        self,
        db_session: AsyncSession,
        evaluation_service: RuleEvaluationService,
    ):
        """Test that layer types are correctly detected based on metadata and priority."""
        service = evaluation_service

        # Test baseline detection via metadata
        baseline_meta = ValuationRuleset(
            name="Test",
            priority=10,  # Higher priority but metadata marks it as baseline
            metadata_json={"system_baseline": True},
        )
        assert service._get_layer_type(baseline_meta) == "baseline"

        # Test baseline detection via priority
        baseline_priority = ValuationRuleset(
            name="Test",
            priority=5,
            metadata_json={},
        )
        assert service._get_layer_type(baseline_priority) == "baseline"

        # Test basic detection
        basic = ValuationRuleset(
            name="Test",
            priority=10,
            metadata_json={},
        )
        assert service._get_layer_type(basic) == "basic"

        # Test advanced detection
        advanced = ValuationRuleset(
            name="Test",
            priority=20,
            metadata_json={},
        )
        assert service._get_layer_type(advanced) == "advanced"

    @pytest.mark.asyncio
    async def test_empty_ruleset_handling(
        self,
        db_session: AsyncSession,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
        baseline_ruleset: ValuationRuleset,
        standard_ruleset: ValuationRuleset,
    ):
        """Test that empty rulesets (no rules) are handled gracefully."""
        # Create rule only in baseline
        await create_simple_rule(
            db_session,
            baseline_ruleset.id,
            "Baseline RAM",
            "Baseline RAM Adjustment",
            50.0,
        )

        # Standard ruleset has no rules

        # Evaluate
        result = await evaluation_service.evaluate_listing(db_session, sample_listing.id)

        # Should handle empty ruleset gracefully
        assert result["total_adjustment"] == 50.0
        assert result["matched_rules_count"] == 1
        assert len(result["layers"]) == 1  # Only baseline has matched rules
        assert "baseline" in result["layers"]

        # Both rulesets should be in evaluated list
        assert len(result["rulesets_evaluated"]) == 2
