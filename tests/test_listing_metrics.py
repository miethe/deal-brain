"""Tests for listing performance metrics calculation."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import Base first
from apps.api.dealbrain_api.db import Base

# Import all models to ensure they're registered with Base.metadata
# Using the full path to avoid class conflicts
from apps.api.dealbrain_api.models.core import (
    ApplicationSettings,
    Cpu,
    CustomFieldAuditLog,
    CustomFieldAttributeHistory,
    CustomFieldDefinition,
    Gpu,
    ImportJob,
    ImportSession,
    ImportSessionAudit,
    Listing,
    ListingComponent,
    ListingScoreSnapshot,
    Port,
    PortsProfile,
    Profile,
    RamSpec,
    RawPayload,
    StorageProfile,
    TaskRun,
    ValuationRuleAction,
    ValuationRuleAudit,
    ValuationRuleCondition,
    ValuationRuleGroup,
    ValuationRuleV2,
    ValuationRuleset,
    ValuationRuleVersion,
)
from apps.api.dealbrain_api.services.listings import apply_listing_metrics

# Legacy function imports (may not exist - tests will be adjusted)
try:
    from apps.api.dealbrain_api.services.listings import (
        calculate_cpu_performance_metrics,
        update_listing_metrics,
        bulk_update_listing_metrics,
    )
    LEGACY_FUNCTIONS_AVAILABLE = True
except ImportError:
    LEGACY_FUNCTIONS_AVAILABLE = False

try:
    import aiosqlite  # type: ignore  # noqa: F401
    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def session():
    """Create an in-memory async database session for testing."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()


class TestCalculateCpuPerformanceMetrics:
    """Test calculate_cpu_performance_metrics function."""

    def test_calculate_metrics_with_valid_cpu(self):
        """Test metric calculation with valid CPU data using delta-based formula."""
        cpu = Cpu(
            name="Intel Core i7-12700K",
            manufacturer="Intel",
            cpu_mark_single=3985,
            cpu_mark_multi=35864,
        )
        listing = Listing(
            title="Test PC",
            price_usd=799.99,
            condition="used",
            # Using delta-based approach: base + adjustment = adjusted
            # 799.99 + (-150) = 649.99
            valuation_breakdown={'total_adjustment': -150.0}
        )
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Single-thread metrics
        assert "dollar_per_cpu_mark_single" in metrics
        assert "dollar_per_cpu_mark_single_adjusted" in metrics
        assert metrics["dollar_per_cpu_mark_single"] == pytest.approx(0.200, rel=0.01)
        # Adjusted: (799.99 + (-150)) / 3985 = 649.99 / 3985 = 0.163
        assert metrics["dollar_per_cpu_mark_single_adjusted"] == pytest.approx(
            0.163, rel=0.01
        )

        # Multi-thread metrics
        assert "dollar_per_cpu_mark_multi" in metrics
        assert "dollar_per_cpu_mark_multi_adjusted" in metrics
        assert metrics["dollar_per_cpu_mark_multi"] == pytest.approx(0.0223, rel=0.01)
        # Adjusted: (799.99 + (-150)) / 35864 = 649.99 / 35864 = 0.0181
        assert metrics["dollar_per_cpu_mark_multi_adjusted"] == pytest.approx(
            0.0181, rel=0.01
        )

    def test_calculate_metrics_no_cpu(self):
        """Test graceful handling when CPU not assigned."""
        listing = Listing(title="Test", price_usd=500, condition="used")
        metrics = calculate_cpu_performance_metrics(listing)
        assert metrics == {}

    def test_calculate_metrics_missing_single_thread(self):
        """Test handling when single-thread benchmark missing."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=None,  # Missing
            cpu_mark_multi=30000,
        )
        listing = Listing(title="Test", price_usd=800, condition="used")
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Should only have multi-thread metrics
        assert "dollar_per_cpu_mark_single" not in metrics
        assert "dollar_per_cpu_mark_single_adjusted" not in metrics
        assert "dollar_per_cpu_mark_multi" in metrics
        assert "dollar_per_cpu_mark_multi_adjusted" in metrics

    def test_calculate_metrics_zero_cpu_mark(self):
        """Test handling when CPU mark is zero (invalid data)."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=0,  # Zero (invalid)
            cpu_mark_multi=30000,
        )
        listing = Listing(title="Test", price_usd=800, condition="used")
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Should skip zero values
        assert "dollar_per_cpu_mark_single" not in metrics
        assert "dollar_per_cpu_mark_single_adjusted" not in metrics
        assert "dollar_per_cpu_mark_multi" in metrics

    def test_calculate_metrics_no_adjustment(self):
        """Test metrics when valuation_breakdown has zero adjustment."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        listing = Listing(
            title="Test",
            price_usd=800,
            condition="new",
            valuation_breakdown={'total_adjustment': 0.0}  # Zero adjustment
        )
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Should use base price for both raw and adjusted (base + 0 = base)
        assert metrics["dollar_per_cpu_mark_single"] == 0.2  # 800 / 4000
        assert metrics["dollar_per_cpu_mark_single_adjusted"] == 0.2  # Same
        assert metrics["dollar_per_cpu_mark_multi"] == pytest.approx(0.0267, rel=0.01)
        assert metrics["dollar_per_cpu_mark_multi_adjusted"] == pytest.approx(
            0.0267, rel=0.01
        )


class TestCpuMetricsDeltaFormula:
    """Comprehensive tests for delta-based CPU metrics calculation."""

    def test_cpu_metrics_delta_calculation(self):
        """Verify adjusted metrics use delta formula: (base + adjustment) / mark."""
        # Arrange: Create CPU with known benchmarks
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=1000,
            cpu_mark_multi=5000,
        )

        # Arrange: Create listing with $500 base, valuation_breakdown with -$100 adjustment
        listing = Listing(
            title="Test PC",
            price_usd=500.00,
            condition="used",
            valuation_breakdown={'total_adjustment': -100.0},  # Component deduction
        )
        listing.cpu = cpu

        # Act: Calculate metrics
        metrics = calculate_cpu_performance_metrics(listing)

        # Assert: Adjusted metrics use delta formula
        expected_adjusted_base = 500.00 + (-100.0)  # = 400.00
        expected_single_adjusted = expected_adjusted_base / 1000  # = 0.400
        expected_multi_adjusted = expected_adjusted_base / 5000   # = 0.080

        assert metrics['dollar_per_cpu_mark_single'] == pytest.approx(0.500, rel=0.01)
        assert metrics['dollar_per_cpu_mark_single_adjusted'] == pytest.approx(expected_single_adjusted, rel=0.01)
        assert metrics['dollar_per_cpu_mark_multi'] == pytest.approx(0.100, rel=0.01)
        assert metrics['dollar_per_cpu_mark_multi_adjusted'] == pytest.approx(expected_multi_adjusted, rel=0.01)

    def test_cpu_metrics_missing_valuation_breakdown(self):
        """Test graceful handling when valuation_breakdown is None."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=2000,
            cpu_mark_multi=10000,
        )

        listing = Listing(
            title="Test PC",
            price_usd=600.00,
            condition="new",
            valuation_breakdown=None,  # Missing breakdown
        )
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Should default adjustment to 0.0, so adjusted = base
        assert metrics['dollar_per_cpu_mark_single'] == pytest.approx(0.300, rel=0.01)
        assert metrics['dollar_per_cpu_mark_single_adjusted'] == pytest.approx(0.300, rel=0.01)
        assert metrics['dollar_per_cpu_mark_multi'] == pytest.approx(0.060, rel=0.01)
        assert metrics['dollar_per_cpu_mark_multi_adjusted'] == pytest.approx(0.060, rel=0.01)

    def test_cpu_metrics_multiple_adjustments(self):
        """Test with multiple component adjustments totaling to single delta."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=20000,
        )

        # Scenario: $50 RAM deduction + $30 storage deduction = -$80 total
        listing = Listing(
            title="Test PC",
            price_usd=1000.00,
            condition="used",
            valuation_breakdown={'total_adjustment': -80.0},  # Combined deductions
        )
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Base metrics
        assert metrics['dollar_per_cpu_mark_single'] == pytest.approx(0.250, rel=0.01)
        assert metrics['dollar_per_cpu_mark_multi'] == pytest.approx(0.050, rel=0.01)

        # Adjusted metrics: (1000 - 80) / marks
        expected_adjusted_base = 1000.00 - 80.0  # = 920.00
        assert metrics['dollar_per_cpu_mark_single_adjusted'] == pytest.approx(920.0 / 4000, rel=0.01)
        assert metrics['dollar_per_cpu_mark_multi_adjusted'] == pytest.approx(920.0 / 20000, rel=0.01)

    def test_cpu_metrics_positive_adjustment(self):
        """Test with positive adjustment (premium/bonus)."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=3000,
            cpu_mark_multi=15000,
        )

        listing = Listing(
            title="Test PC",
            price_usd=750.00,
            condition="new",
            valuation_breakdown={'total_adjustment': 150.0},  # Premium added
        )
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Adjusted should be higher: (750 + 150) / marks
        expected_adjusted_base = 750.00 + 150.0  # = 900.00
        assert metrics['dollar_per_cpu_mark_single_adjusted'] == pytest.approx(900.0 / 3000, rel=0.01)
        assert metrics['dollar_per_cpu_mark_multi_adjusted'] == pytest.approx(900.0 / 15000, rel=0.01)

    def test_cpu_metrics_negative_adjusted_price(self):
        """Test edge case where adjustment exceeds base price."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=2000,
            cpu_mark_multi=10000,
        )

        # Extreme deduction scenario
        listing = Listing(
            title="Test PC",
            price_usd=100.00,
            condition="for_parts",
            valuation_breakdown={'total_adjustment': -150.0},  # Deduction exceeds base
        )
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Should still calculate: (100 + (-150)) / marks = -50 / marks
        # This results in negative metrics, which is mathematically valid
        expected_adjusted_base = 100.00 - 150.0  # = -50.00
        assert metrics['dollar_per_cpu_mark_single_adjusted'] == pytest.approx(-50.0 / 2000, rel=0.01)
        assert metrics['dollar_per_cpu_mark_multi_adjusted'] == pytest.approx(-50.0 / 10000, rel=0.01)

    def test_cpu_metrics_valuation_breakdown_missing_total_adjustment_key(self):
        """Test when valuation_breakdown exists but lacks 'total_adjustment' key."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=5000,
            cpu_mark_multi=25000,
        )

        listing = Listing(
            title="Test PC",
            price_usd=1200.00,
            condition="used",
            valuation_breakdown={'other_key': 'value'},  # Missing total_adjustment
        )
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Should default to 0.0 adjustment
        assert metrics['dollar_per_cpu_mark_single_adjusted'] == pytest.approx(1200.0 / 5000, rel=0.01)
        assert metrics['dollar_per_cpu_mark_multi_adjusted'] == pytest.approx(1200.0 / 25000, rel=0.01)


@pytest.mark.asyncio
class TestUpdateListingMetrics:
    """Test update_listing_metrics function."""

    async def test_update_listing_metrics(self, session: AsyncSession):
        """Test metric persistence."""
        # Create CPU and listing
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        session.add(cpu)
        await session.flush()

        listing = Listing(
            title="Test", price_usd=800, condition="used", cpu_id=cpu.id
        )
        session.add(listing)
        await session.commit()

        # Update metrics
        updated = await update_listing_metrics(session, listing.id)

        assert updated.dollar_per_cpu_mark_single == 0.2  # 800 / 4000
        assert updated.dollar_per_cpu_mark_multi == pytest.approx(0.0267, rel=0.01)
        assert updated.dollar_per_cpu_mark_single_adjusted == 0.2
        assert updated.dollar_per_cpu_mark_multi_adjusted == pytest.approx(
            0.0267, rel=0.01
        )

    async def test_update_listing_metrics_not_found(self, session: AsyncSession):
        """Test error handling when listing not found."""
        with pytest.raises(ValueError, match="Listing .* not found"):
            await update_listing_metrics(session, 99999)


@pytest.mark.asyncio
class TestBulkUpdateListingMetrics:
    """Test bulk_update_listing_metrics function."""

    async def test_bulk_update_all_listings(self, session: AsyncSession):
        """Test bulk update for all listings."""
        # Create CPU
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        session.add(cpu)
        await session.flush()

        # Create multiple listings
        listing1 = Listing(
            title="Test 1", price_usd=800, condition="used", cpu_id=cpu.id
        )
        listing2 = Listing(
            title="Test 2", price_usd=600, condition="refurb", cpu_id=cpu.id
        )
        listing3 = Listing(
            title="Test 3", price_usd=1000, condition="new", cpu_id=cpu.id
        )
        session.add_all([listing1, listing2, listing3])
        await session.commit()

        # Bulk update all
        count = await bulk_update_listing_metrics(session, listing_ids=None)

        assert count == 3

    async def test_bulk_update_specific_listings(self, session: AsyncSession):
        """Test bulk update for specific listing IDs."""
        # Create CPU
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        session.add(cpu)
        await session.flush()

        # Create listings
        listing1 = Listing(
            title="Test 1", price_usd=800, condition="used", cpu_id=cpu.id
        )
        listing2 = Listing(
            title="Test 2", price_usd=600, condition="refurb", cpu_id=cpu.id
        )
        listing3 = Listing(
            title="Test 3", price_usd=1000, condition="new", cpu_id=cpu.id
        )
        session.add_all([listing1, listing2, listing3])
        await session.commit()

        # Update only listing1 and listing2
        count = await bulk_update_listing_metrics(
            session, listing_ids=[listing1.id, listing2.id]
        )

        assert count == 2


@pytest.mark.asyncio
class TestApplyListingMetricsCpuMarks:
    """Test apply_listing_metrics function for CPU Mark calculations."""

    async def test_cpu_mark_calculations_with_both_marks(self, session: AsyncSession):
        """Test CPU Mark metrics calculated with both single and multi marks."""
        # Create CPU with both marks
        cpu = Cpu(
            name="Intel Core i7-12700K",
            manufacturer="Intel",
            cpu_mark_single=3985,
            cpu_mark_multi=35864,
        )
        session.add(cpu)
        await session.flush()

        # Create listing with CPU and price
        listing = Listing(
            title="Test PC",
            price_usd=799.99,
            condition="used",
            cpu_id=cpu.id,
        )
        session.add(listing)
        await session.flush()

        # Apply metrics
        await apply_listing_metrics(session, listing)

        # Verify calculations
        assert listing.dollar_per_cpu_mark_single is not None
        assert listing.dollar_per_cpu_mark_multi is not None
        assert listing.dollar_per_cpu_mark_single == pytest.approx(
            listing.adjusted_price_usd / 3985, rel=0.01
        )
        assert listing.dollar_per_cpu_mark_multi == pytest.approx(
            listing.adjusted_price_usd / 35864, rel=0.01
        )

    async def test_cpu_mark_calculations_single_only(self, session: AsyncSession):
        """Test metrics when only single-thread mark available."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=None,  # No multi-thread mark
        )
        session.add(cpu)
        await session.flush()

        listing = Listing(
            title="Test",
            price_usd=800.0,
            condition="used",
            cpu_id=cpu.id,
        )
        session.add(listing)
        await session.flush()

        await apply_listing_metrics(session, listing)

        # Should have single but not multi
        assert listing.dollar_per_cpu_mark_single is not None
        assert listing.dollar_per_cpu_mark_multi is None
        assert listing.dollar_per_cpu_mark_single == pytest.approx(
            listing.adjusted_price_usd / 4000, rel=0.01
        )

    async def test_cpu_mark_calculations_multi_only(self, session: AsyncSession):
        """Test metrics when only multi-thread mark available."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=None,  # No single-thread mark
            cpu_mark_multi=30000,
        )
        session.add(cpu)
        await session.flush()

        listing = Listing(
            title="Test",
            price_usd=600.0,
            condition="refurb",
            cpu_id=cpu.id,
        )
        session.add(listing)
        await session.flush()

        await apply_listing_metrics(session, listing)

        # Should have multi but not single
        assert listing.dollar_per_cpu_mark_single is None
        assert listing.dollar_per_cpu_mark_multi is not None
        assert listing.dollar_per_cpu_mark_multi == pytest.approx(
            listing.adjusted_price_usd / 30000, rel=0.01
        )

    async def test_cpu_mark_calculations_no_cpu(self, session: AsyncSession):
        """Test metrics when no CPU assigned."""
        listing = Listing(
            title="Test",
            price_usd=500.0,
            condition="used",
            cpu_id=None,  # No CPU
        )
        session.add(listing)
        await session.flush()

        await apply_listing_metrics(session, listing)

        # Should be None
        assert listing.dollar_per_cpu_mark_single is None
        assert listing.dollar_per_cpu_mark_multi is None

    async def test_cpu_mark_recalculation_on_price_update(self, session: AsyncSession):
        """Test metrics recalculate when price changes."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        session.add(cpu)
        await session.flush()

        listing = Listing(
            title="Test",
            price_usd=800.0,
            condition="used",
            cpu_id=cpu.id,
        )
        session.add(listing)
        await session.flush()

        # Initial calculation
        await apply_listing_metrics(session, listing)
        initial_single = listing.dollar_per_cpu_mark_single
        initial_multi = listing.dollar_per_cpu_mark_multi

        # Update price
        listing.price_usd = 600.0

        # Recalculate
        await apply_listing_metrics(session, listing)

        # Metrics should have changed
        assert listing.dollar_per_cpu_mark_single != initial_single
        assert listing.dollar_per_cpu_mark_multi != initial_multi
        assert listing.dollar_per_cpu_mark_single == pytest.approx(
            listing.adjusted_price_usd / 4000, rel=0.01
        )

    async def test_cpu_mark_recalculation_on_cpu_change(self, session: AsyncSession):
        """Test metrics recalculate when CPU changes."""
        cpu1 = Cpu(
            name="CPU 1",
            manufacturer="Intel",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        cpu2 = Cpu(
            name="CPU 2",
            manufacturer="AMD",
            cpu_mark_single=5000,
            cpu_mark_multi=40000,
        )
        session.add_all([cpu1, cpu2])
        await session.flush()

        listing = Listing(
            title="Test",
            price_usd=800.0,
            condition="used",
            cpu_id=cpu1.id,
        )
        session.add(listing)
        await session.flush()

        # Initial calculation with CPU1
        await apply_listing_metrics(session, listing)
        initial_single = listing.dollar_per_cpu_mark_single
        initial_multi = listing.dollar_per_cpu_mark_multi

        # Change to CPU2
        listing.cpu_id = cpu2.id

        # Recalculate
        await apply_listing_metrics(session, listing)

        # Metrics should have changed
        assert listing.dollar_per_cpu_mark_single != initial_single
        assert listing.dollar_per_cpu_mark_multi != initial_multi
        assert listing.dollar_per_cpu_mark_single == pytest.approx(
            listing.adjusted_price_usd / 5000, rel=0.01
        )
        assert listing.dollar_per_cpu_mark_multi == pytest.approx(
            listing.adjusted_price_usd / 40000, rel=0.01
        )


@pytest.mark.asyncio
class TestApplyListingMetricsValuationRules:
    """Test integration between apply_listing_metrics and the valuation rule engine."""

    async def test_apply_listing_metrics_with_matching_ruleset(self, session: AsyncSession):
        """Adjusted price should incorporate rule engine adjustments."""
        ruleset = ValuationRuleset(
            name="Default Ruleset",
            priority=5,
            is_active=True,
        )
        session.add(ruleset)
        await session.flush()

        group = ValuationRuleGroup(
            ruleset_id=ruleset.id,
            name="Base Adjustments",
            category="base",
            display_order=1,
        )
        session.add(group)
        await session.flush()

        rule = ValuationRuleV2(
            group_id=group.id,
            name="Static Discount",
            evaluation_order=1,
            priority=1,
            is_active=True,
        )
        session.add(rule)
        await session.flush()

        action = ValuationRuleAction(
            rule_id=rule.id,
            action_type="fixed_value",
            value_usd=-100.0,
        )
        session.add(action)
        await session.commit()

        listing = Listing(
            title="Discounted Listing",
            price_usd=1000.0,
            condition="used",
        )
        session.add(listing)
        await session.flush()

        await apply_listing_metrics(session, listing)

        assert listing.adjusted_price_usd == pytest.approx(900.0, rel=0.001)
        breakdown = listing.valuation_breakdown or {}
        assert breakdown.get("ruleset", {}).get("id") == ruleset.id
        assert breakdown.get("ruleset_name") == ruleset.name
        assert breakdown.get("matched_rules_count") == 1
        adjustments = breakdown.get("adjustments") or []
        assert len(adjustments) == 1
        assert adjustments[0]["rule_id"] == rule.id
        assert adjustments[0]["adjustment_usd"] == pytest.approx(-100.0, rel=0.001)
        lines = breakdown.get("lines") or []
        assert len(lines) == 1
        assert lines[0]["deduction_usd"] == pytest.approx(100.0, rel=0.001)

    async def test_apply_listing_metrics_without_rulesets_defaults_to_list_price(
        self, session: AsyncSession
    ):
        """When no rulesets exist, adjusted price should equal the listing price."""
        listing = Listing(
            title="No Rules Listing",
            price_usd=750.0,
            condition="used",
        )
        session.add(listing)
        await session.flush()

        await apply_listing_metrics(session, listing)

        assert listing.adjusted_price_usd == pytest.approx(750.0, rel=0.001)
        breakdown = listing.valuation_breakdown or {}
        assert breakdown.get("adjusted_price") == pytest.approx(750.0, rel=0.001)
        assert breakdown.get("total_adjustment") == pytest.approx(0.0, rel=0.001)

    async def test_apply_listing_metrics_honors_static_override(self, session: AsyncSession):
        """Static ruleset assignment should take precedence over dynamic matching."""
        default_ruleset = ValuationRuleset(
            name="Default Auto Rules",
            priority=5,
            is_active=True,
        )
        static_ruleset = ValuationRuleset(
            name="Static Premium Rules",
            priority=10,
            is_active=True,
        )
        session.add_all([default_ruleset, static_ruleset])
        await session.flush()

        default_group = ValuationRuleGroup(
            ruleset_id=default_ruleset.id,
            name="Default Group",
            category="base",
            display_order=1,
        )
        static_group = ValuationRuleGroup(
            ruleset_id=static_ruleset.id,
            name="Static Group",
            category="base",
            display_order=1,
        )
        session.add_all([default_group, static_group])
        await session.flush()

        default_rule = ValuationRuleV2(
            group_id=default_group.id,
            name="Default Deduction",
            evaluation_order=1,
            priority=1,
            is_active=True,
        )
        static_rule = ValuationRuleV2(
            group_id=static_group.id,
            name="Static Bonus",
            evaluation_order=1,
            priority=1,
            is_active=True,
        )
        session.add_all([default_rule, static_rule])
        await session.flush()

        session.add_all(
            [
                ValuationRuleAction(
                    rule_id=default_rule.id,
                    action_type="fixed_value",
                    value_usd=-50.0,
                ),
                ValuationRuleAction(
                    rule_id=static_rule.id,
                    action_type="fixed_value",
                    value_usd=200.0,
                ),
            ]
        )
        await session.commit()

        listing = Listing(
            title="Static Override Listing",
            price_usd=1000.0,
            condition="used",
            ruleset_id=static_ruleset.id,
        )
        session.add(listing)
        await session.flush()

        await apply_listing_metrics(session, listing)

        # Should use static override (+200) rather than default ruleset (-50)
        assert listing.adjusted_price_usd == pytest.approx(1200.0, rel=0.001)
        breakdown = listing.valuation_breakdown or {}
        assert breakdown.get("ruleset", {}).get("id") == static_ruleset.id
        adjustments = breakdown.get("adjustments") or []
        assert adjustments and adjustments[0]["adjustment_usd"] == pytest.approx(200.0, rel=0.001)
