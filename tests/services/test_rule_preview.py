"""
Integration tests for RulePreviewService.

Tests rule impact preview and analysis with real data.
"""

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models.core import Listing, CPU, GPU
from dealbrain_api.services.rules import RulesService
from dealbrain_api.services.rule_preview import RulePreviewService
from dealbrain_api.schemas.rules import (
    RulesetCreate,
    RuleGroupCreate,
    RuleCreate,
    ConditionCreate,
    ActionCreate,
    ConditionOperator,
    ActionType,
)


@pytest.fixture
async def preview_service():
    """Create RulePreviewService instance."""
    return RulePreviewService()


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
async def multiple_listings(db_session: AsyncSession, sample_cpu: CPU) -> list[Listing]:
    """Create multiple listings for preview testing."""
    listings = []

    # High-end listing: 32GB RAM, NVMe
    listing1 = Listing(
        source="test",
        seller="Seller A",
        device_model="Gaming PC",
        condition="used",
        price_usd=Decimal("1200.00"),
        base_price_usd=Decimal("1200.00"),
        adjusted_price_usd=Decimal("1200.00"),
        cpu_id=sample_cpu.id,
        ram_gb=32,
        primary_storage_capacity_gb=1000,
        primary_storage_type="NVMe SSD",
        has_wifi=True,
        valuation_breakdown={},
    )

    # Mid-range listing: 16GB RAM, SATA SSD
    listing2 = Listing(
        source="test",
        seller="Seller B",
        device_model="Office PC",
        condition="used",
        price_usd=Decimal("800.00"),
        base_price_usd=Decimal("800.00"),
        adjusted_price_usd=Decimal("800.00"),
        cpu_id=sample_cpu.id,
        ram_gb=16,
        primary_storage_capacity_gb=500,
        primary_storage_type="SATA SSD",
        has_wifi=True,
        valuation_breakdown={},
    )

    # Budget listing: 8GB RAM, HDD
    listing3 = Listing(
        source="test",
        seller="Seller C",
        device_model="Budget PC",
        condition="used",
        price_usd=Decimal("500.00"),
        base_price_usd=Decimal("500.00"),
        adjusted_price_usd=Decimal("500.00"),
        cpu_id=sample_cpu.id,
        ram_gb=8,
        primary_storage_capacity_gb=500,
        primary_storage_type="HDD",
        has_wifi=False,
        valuation_breakdown={},
    )

    db_session.add_all([listing1, listing2, listing3])
    await db_session.commit()

    for listing in [listing1, listing2, listing3]:
        await db_session.refresh(listing)
        listings.append(listing)

    return listings


class TestPreviewImpact:
    """Test rule impact preview functionality."""

    @pytest.mark.asyncio
    async def test_preview_single_rule(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        preview_service: RulePreviewService,
        multiple_listings: list[Listing],
    ):
        """Test preview impact of a single rule."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="Preview Test", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="RAM", category="ram", weight=1.0),
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
                    )
                ],
            ),
        )

        # Preview impact
        preview = await preview_service.preview_rule_impact(db_session, rule.id)

        assert preview is not None
        assert preview.total_listings_affected == 1  # Only listing1 has 32GB
        assert preview.average_adjustment == Decimal("50.00")
        assert preview.total_adjustment == Decimal("50.00")
        assert len(preview.sample_listings) > 0

    @pytest.mark.asyncio
    async def test_preview_ruleset_impact(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        preview_service: RulePreviewService,
        multiple_listings: list[Listing],
    ):
        """Test preview impact of entire ruleset."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="Multi-Rule Preview", version="1.0.0", is_active=True),
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

        # RAM rule: 16GB+ adds $30
        await rules_service.create_rule(
            db_session,
            ram_group.id,
            RuleCreate(
                name="16GB RAM",
                category="ram",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                    value=16,
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=30.00)],
            ),
        )

        # Storage rule: NVMe adds $40
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
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=40.00)],
            ),
        )

        # Preview entire ruleset
        preview = await preview_service.preview_ruleset_impact(db_session, ruleset.id)

        assert preview is not None
        # listing1: $30 (RAM) + $40 (NVMe) = $70
        # listing2: $30 (RAM) = $30
        # listing3: $0 (no matches)
        assert preview.total_listings_affected == 2
        assert preview.total_adjustment == Decimal("100.00")  # 70 + 30

    @pytest.mark.asyncio
    async def test_preview_with_filters(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        preview_service: RulePreviewService,
        multiple_listings: list[Listing],
    ):
        """Test preview with filtered listings."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="Filtered Preview", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="RAM", category="ram", weight=1.0),
        )

        rule = await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="Any RAM",
                category="ram",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN,
                    value=0,
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=10.00)],
            ),
        )

        # Preview with price filter
        preview = await preview_service.preview_rule_impact(
            db_session,
            rule.id,
            filters={"min_price": 700.00},
        )

        # Only listing1 ($1200) and listing2 ($800) should be included
        assert preview.total_listings_affected == 2

    @pytest.mark.asyncio
    async def test_preview_sample_listings(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        preview_service: RulePreviewService,
        multiple_listings: list[Listing],
    ):
        """Test that preview includes sample affected listings."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="Sample Test", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="RAM", category="ram", weight=1.0),
        )

        rule = await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="16GB+ RAM",
                category="ram",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                    value=16,
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=25.00)],
            ),
        )

        preview = await preview_service.preview_rule_impact(
            db_session, rule.id, sample_limit=5
        )

        assert len(preview.sample_listings) <= 5
        assert preview.total_listings_affected == 2  # listing1 and listing2

        # Verify sample listings have before/after values
        for sample in preview.sample_listings:
            assert sample.listing_id is not None
            assert sample.before_value is not None
            assert sample.after_value is not None
            assert sample.adjustment == Decimal("25.00")


class TestPreviewStatistics:
    """Test preview statistics calculations."""

    @pytest.mark.asyncio
    async def test_average_adjustment_calculation(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        preview_service: RulePreviewService,
        multiple_listings: list[Listing],
    ):
        """Test average adjustment calculation."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="Stats Test", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="RAM", category="ram", weight=1.0),
        )

        # Per-unit rule: $2 per GB
        rule = await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="RAM Per-GB",
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
                        value_usd=2.00,
                        unit_type="ram_gb",
                    )
                ],
            ),
        )

        preview = await preview_service.preview_rule_impact(db_session, rule.id)

        # listing1: 32GB * $2 = $64
        # listing2: 16GB * $2 = $32
        # listing3: 8GB * $2 = $16
        # Total: $112, Average: $37.33
        assert preview.total_adjustment == Decimal("112.00")
        assert preview.average_adjustment == pytest.approx(Decimal("37.33"), rel=0.01)

    @pytest.mark.asyncio
    async def test_min_max_adjustments(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        preview_service: RulePreviewService,
        multiple_listings: list[Listing],
    ):
        """Test min/max adjustment tracking."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="MinMax Test", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="RAM", category="ram", weight=1.0),
        )

        rule = await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="RAM Per-GB",
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
                    )
                ],
            ),
        )

        preview = await preview_service.preview_rule_impact(db_session, rule.id)

        # Min: 8GB * $3 = $24
        # Max: 32GB * $3 = $96
        assert preview.min_adjustment == Decimal("24.00")
        assert preview.max_adjustment == Decimal("96.00")


class TestPreviewEdgeCases:
    """Test edge cases in preview functionality."""

    @pytest.mark.asyncio
    async def test_preview_inactive_rule(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        preview_service: RulePreviewService,
        multiple_listings: list[Listing],
    ):
        """Test preview of inactive rule."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="Inactive Test", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="RAM", category="ram", weight=1.0),
        )

        rule = await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="Inactive Rule",
                category="ram",
                evaluation_order=100,
                is_active=False,  # Inactive
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN,
                    value=0,
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=50.00)],
            ),
        )

        # Preview should still work for inactive rules (to see what would happen if activated)
        preview = await preview_service.preview_rule_impact(db_session, rule.id)

        assert preview is not None
        assert preview.total_listings_affected == 3

    @pytest.mark.asyncio
    async def test_preview_with_no_listings(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        preview_service: RulePreviewService,
    ):
        """Test preview when no listings exist."""
        ruleset = await rules_service.create_ruleset(
            db_session,
            RulesetCreate(name="Empty Test", version="1.0.0", is_active=True),
        )

        group = await rules_service.create_rule_group(
            db_session,
            ruleset.id,
            RuleGroupCreate(name="RAM", category="ram", weight=1.0),
        )

        rule = await rules_service.create_rule(
            db_session,
            group.id,
            RuleCreate(
                name="Any Rule",
                category="ram",
                evaluation_order=100,
                is_active=True,
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN,
                    value=0,
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=10.00)],
            ),
        )

        preview = await preview_service.preview_rule_impact(db_session, rule.id)

        assert preview.total_listings_affected == 0
        assert preview.total_adjustment == Decimal("0.00")
        assert len(preview.sample_listings) == 0
