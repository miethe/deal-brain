"""
Integration tests for RuleEvaluationService.

Tests rule evaluation with real database data and complex scenarios.
"""

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models.core import Listing, CPU, GPU
from dealbrain_api.services.rules import RulesService
from dealbrain_api.services.rule_evaluation import RuleEvaluationService
from dealbrain_api.schemas.rules import (
    RulesetCreate,
    RuleGroupCreate,
    RuleCreate,
    ConditionCreate,
    ActionCreate,
    ConditionOperator,
    ActionType,
    LogicalOperator,
)


@pytest.fixture
async def evaluation_service():
    """Create RuleEvaluationService instance."""
    return RuleEvaluationService()


@pytest.fixture
async def rules_service():
    """Create RulesService instance."""
    return RulesService()


@pytest.fixture
async def sample_cpu(db_session: AsyncSession) -> CPU:
    """Create a sample CPU for testing."""
    cpu = CPU(
        name="Intel Core i7-12700K",
        cores=12,
        threads=20,
        base_clock_ghz=3.6,
        boost_clock_ghz=5.0,
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
async def sample_gpu(db_session: AsyncSession) -> GPU:
    """Create a sample GPU for testing."""
    gpu = GPU(
        name="NVIDIA RTX 3070",
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
async def sample_listing(
    db_session: AsyncSession, sample_cpu: CPU, sample_gpu: GPU
) -> Listing:
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
        primary_storage_capacity_gb=1000,
        primary_storage_type="NVMe SSD",
        has_wifi=True,
        has_bluetooth=True,
        valuation_breakdown={},
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)
    return listing


class TestBasicEvaluation:
    """Test basic rule evaluation scenarios."""

    @pytest.mark.asyncio
    async def test_evaluate_simple_condition(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
    ):
        """Test evaluating a simple condition rule."""
        # Create ruleset with simple condition
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(
                name="Simple Test Ruleset",
                version="1.0.0",
                is_active=True,
            ),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(
                name="RAM Valuation",
                category="ram",
                weight=1.0,
            ),
        )

        # Rule: If RAM >= 32GB, add $50
        rule = await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="32GB RAM Premium",
                category="ram",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                    value=32,
                ),
                actions=[
                    ActionCreate(
                        action_type=ActionType.FIXED_VALUE,
                        value_usd=50.00,
                        description="Premium for 32GB+ RAM",
                    )
                ],
            ),
        )

        # Evaluate
        result = await evaluation_service.evaluate_listing(
            db_session, sample_listing.id, ruleset.id
        )

        assert result is not None
        assert result.total_adjustment == Decimal("50.00")
        assert len(result.matched_rules) == 1
        assert result.matched_rules[0].rule_id == rule.id

    @pytest.mark.asyncio
    async def test_evaluate_no_match(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
    ):
        """Test evaluation when no rules match."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(
                name="No Match Ruleset",
                version="1.0.0",
                is_active=True,
            ),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(
                name="RAM Valuation",
                category="ram",
                weight=1.0,
            ),
        )

        # Rule: If RAM >= 64GB (won't match our 32GB listing)
        await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="64GB RAM Premium",
                category="ram",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                    value=64,
                ),
                actions=[
                    ActionCreate(
                        action_type=ActionType.FIXED_VALUE,
                        value_usd=100.00,
                    )
                ],
            ),
        )

        result = await evaluation_service.evaluate_listing(
            db_session, sample_listing.id, ruleset.id
        )

        assert result.total_adjustment == Decimal("0.00")
        assert len(result.matched_rules) == 0

    @pytest.mark.asyncio
    async def test_evaluate_multiple_rules(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
    ):
        """Test evaluation with multiple matching rules."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(
                name="Multi-Rule Ruleset",
                version="1.0.0",
                is_active=True,
            ),
        )

        ram_group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="RAM", category="ram", weight=0.5),
        )

        storage_group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="Storage", category="storage", weight=0.5),
        )

        # RAM rule: 32GB+ adds $50
        await rules_service.create_rule(
            db_session,
            ram_group.id,
            RuleCreate(
                name="32GB RAM",
                category="ram",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                    value=32,
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=50.00)],
            ),
        )

        # Storage rule: NVMe SSD adds $30
        await rules_service.create_rule(
            db_session,
            storage_group.id,
            RuleCreate(
                name="NVMe Premium",
                category="storage",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    field_name="primary_storage_type",
                    operator=ConditionOperator.CONTAINS,
                    value="NVMe",
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=30.00)],
            ),
        )

        result = await evaluation_service.evaluate_listing(
            db_session, sample_listing.id, ruleset.id
        )

        assert result.total_adjustment == Decimal("80.00")  # 50 + 30
        assert len(result.matched_rules) == 2


class TestComplexConditions:
    """Test evaluation with complex nested conditions."""

    @pytest.mark.asyncio
    async def test_evaluate_nested_and_conditions(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
    ):
        """Test evaluation with nested AND conditions."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="AND Test", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="Combined", category="cpu", weight=1.0),
        )

        # Rule: (cpu.cores >= 12 AND ram_gb >= 32)
        await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="High-Performance Config",
                category="cpu",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    logical_operator=LogicalOperator.AND,
                    conditions=[
                        ConditionCreate(
                            field_name="cpu.cores",
                            operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                            value=12,
                        ),
                        ConditionCreate(
                            field_name="ram_gb",
                            operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                            value=32,
                        ),
                    ],
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=100.00)],
            ),
        )

        result = await evaluation_service.evaluate_listing(
            db_session, sample_listing.id, ruleset.id
        )

        assert result.total_adjustment == Decimal("100.00")
        assert len(result.matched_rules) == 1

    @pytest.mark.asyncio
    async def test_evaluate_nested_or_conditions(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
    ):
        """Test evaluation with nested OR conditions."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="OR Test", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="Either", category="cpu", weight=1.0),
        )

        # Rule: (cpu.cpu_mark_multi > 30000 OR ram_gb >= 64)
        # Should match because cpu_mark_multi = 35228
        await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="High CPU or Lots of RAM",
                category="cpu",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    logical_operator=LogicalOperator.OR,
                    conditions=[
                        ConditionCreate(
                            field_name="cpu.cpu_mark_multi",
                            operator=ConditionOperator.GREATER_THAN,
                            value=30000,
                        ),
                        ConditionCreate(
                            field_name="ram_gb",
                            operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                            value=64,
                        ),
                    ],
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=75.00)],
            ),
        )

        result = await evaluation_service.evaluate_listing(
            db_session, sample_listing.id, ruleset.id
        )

        assert result.total_adjustment == Decimal("75.00")
        assert len(result.matched_rules) == 1


class TestActionTypes:
    """Test different action types."""

    @pytest.mark.asyncio
    async def test_per_unit_action(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
    ):
        """Test per-unit pricing action."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="Per-Unit Test", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="RAM", category="ram", weight=1.0),
        )

        # Rule: $3 per GB of RAM
        await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="RAM Per-GB Pricing",
                category="ram",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN,
                    value=0,
                ),
                actions=[
                    ActionCreate(
                        action_type=ActionType.PER_UNIT,
                        value_usd=3.00,
                        unit_type="ram_gb",
                        description="$3 per GB of RAM",
                    )
                ],
            ),
        )

        result = await evaluation_service.evaluate_listing(
            db_session, sample_listing.id, ruleset.id
        )

        # 32GB * $3 = $96
        assert result.total_adjustment == Decimal("96.00")

    @pytest.mark.asyncio
    async def test_multiplier_action(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
    ):
        """Test multiplier action."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="Multiplier Test", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="CPU", category="cpu", weight=1.0),
        )

        # Rule: Multiply price by 1.15 for high-end CPU
        await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="High-End CPU Multiplier",
                category="cpu",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    field_name="cpu.cpu_mark_multi",
                    operator=ConditionOperator.GREATER_THAN,
                    value=30000,
                ),
                actions=[
                    ActionCreate(
                        action_type=ActionType.MULTIPLIER,
                        value_usd=1.15,
                        description="15% premium for high-end CPU",
                    )
                ],
            ),
        )

        result = await evaluation_service.evaluate_listing(
            db_session, sample_listing.id, ruleset.id
        )

        # $1200 * 1.15 = $1380, adjustment = $180
        assert result.total_adjustment == Decimal("180.00")


class TestPriorityOrdering:
    """Test rule evaluation order based on priority."""

    @pytest.mark.asyncio
    async def test_rules_evaluated_by_priority(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        evaluation_service: RuleEvaluationService,
        sample_listing: Listing,
    ):
        """Test that rules are evaluated in priority order (higher first)."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="Priority Test", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="RAM", category="ram", weight=1.0),
        )

        # Low priority rule
        low_priority = await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="Low Priority",
                category="ram",
                evaluation_order=10,  # Lower priority
                is_active=True,
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN,
                    value=0,
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=10.00)],
            ),
        )

        # High priority rule
        high_priority = await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="High Priority",
                category="ram",
                evaluation_order=100,  # Higher priority
                is_active=True,
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN,
                    value=0,
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=50.00)],
            ),
        )

        result = await evaluation_service.evaluate_listing(
            db_session, sample_listing.id, ruleset.id
        )

        # Verify high priority rule was evaluated first
        assert result.matched_rules[0].rule_id == high_priority.id
        assert result.matched_rules[1].rule_id == low_priority.id
