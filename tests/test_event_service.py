"""Tests for IngestionEventService (Task ID-014).

This module tests event emission for URL ingestion, including:
- ListingCreatedEvent creation
- PriceChangedEvent creation
- Price change detection logic
- Settings integration
- Decimal precision
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from dealbrain_api.models.core import Listing
from dealbrain_api.services.ingestion import (
    IngestionEventService,
    ListingCreatedEvent,
    PriceChangedEvent,
    should_emit_price_change,
)


class TestEventDataStructures:
    """Test event dataclass creation."""

    def test_create_listing_created_event(self):
        """Test ListingCreatedEvent dataclass."""
        now = datetime.utcnow()
        event = ListingCreatedEvent(
            listing_id=1,
            title="Gaming PC",
            price=Decimal("599.99"),
            marketplace="ebay",
            vendor_item_id="123",
            provenance="ebay_api",
            quality="full",
            created_at=now,
        )

        assert event.listing_id == 1
        assert event.title == "Gaming PC"
        assert event.price == Decimal("599.99")
        assert event.marketplace == "ebay"
        assert event.vendor_item_id == "123"
        assert event.provenance == "ebay_api"
        assert event.quality == "full"
        assert event.created_at == now

    def test_create_price_changed_event(self):
        """Test PriceChangedEvent dataclass."""
        now = datetime.utcnow()
        event = PriceChangedEvent(
            listing_id=1,
            title="Gaming PC",
            old_price=Decimal("599.99"),
            new_price=Decimal("549.99"),
            change_amount=Decimal("-50.00"),
            change_percent=Decimal("-8.33"),
            marketplace="ebay",
            vendor_item_id="123",
            changed_at=now,
        )

        assert event.listing_id == 1
        assert event.title == "Gaming PC"
        assert event.old_price == Decimal("599.99")
        assert event.new_price == Decimal("549.99")
        assert event.change_amount == Decimal("-50.00")
        assert event.change_percent == Decimal("-8.33")
        assert event.marketplace == "ebay"
        assert event.vendor_item_id == "123"
        assert event.changed_at == now

    def test_listing_created_event_with_none_vendor_id(self):
        """Test ListingCreatedEvent with None vendor_item_id."""
        now = datetime.utcnow()
        event = ListingCreatedEvent(
            listing_id=1,
            title="PC",
            price=Decimal("599.99"),
            marketplace="other",
            vendor_item_id=None,
            provenance="jsonld",
            quality="partial",
            created_at=now,
        )

        assert event.vendor_item_id is None
        assert event.marketplace == "other"

    def test_price_changed_event_with_none_vendor_id(self):
        """Test PriceChangedEvent with None vendor_item_id."""
        now = datetime.utcnow()
        event = PriceChangedEvent(
            listing_id=1,
            title="PC",
            old_price=Decimal("100.00"),
            new_price=Decimal("90.00"),
            change_amount=Decimal("-10.00"),
            change_percent=Decimal("-10.00"),
            marketplace="other",
            vendor_item_id=None,
            changed_at=now,
        )

        assert event.vendor_item_id is None
        assert event.change_amount == Decimal("-10.00")


class TestPriceChangeDetection:
    """Test should_emit_price_change() logic."""

    def test_should_emit_price_change_absolute_threshold(self):
        """Test emission when absolute change meets threshold."""
        # Change: $100 → $98 = $2 change
        # Threshold: $1 abs, 5% pct
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("98.00"),
            Decimal("1.00"),
            Decimal("5.0"),
        )
        assert result is True  # $2 >= $1 ✓

    def test_should_emit_price_change_percent_threshold(self):
        """Test emission when percent change meets threshold."""
        # Change: $100 → $97 = 3% change
        # Threshold: $10 abs, 2% pct
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("97.00"),
            Decimal("10.00"),  # Absolute threshold NOT met ($3 < $10)
            Decimal("2.0"),  # But percent threshold met (3% >= 2%) ✓
        )
        assert result is True

    def test_should_not_emit_price_change_below_thresholds(self):
        """Test no emission when both thresholds not met."""
        # Change: $100 → $99 = 1% change, $1 absolute
        # Threshold: $2 abs, 2% pct
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("99.00"),
            Decimal("2.00"),  # $1 < $2 ✗
            Decimal("2.0"),  # 1% < 2% ✗
        )
        assert result is False

    def test_should_emit_price_increase(self):
        """Test that price increases also trigger events."""
        # Change: $100 → $110 = 10% increase
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("110.00"),
            Decimal("5.00"),
            Decimal("5.0"),
        )
        assert result is True

    def test_should_emit_exact_threshold_match(self):
        """Test emission when change exactly matches threshold."""
        # Change: $100 → $98 = $2 change, 2%
        # Threshold: $2 abs, 2% pct
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("98.00"),
            Decimal("2.00"),  # Exact match ✓
            Decimal("2.0"),  # Exact match ✓
        )
        assert result is True

    def test_should_emit_zero_old_price(self):
        """Test price change detection when old price is zero."""
        # Should only check absolute threshold
        result = should_emit_price_change(
            Decimal("0.00"),
            Decimal("10.00"),
            Decimal("5.00"),
            Decimal("50.0"),  # Percent threshold irrelevant when old=0
        )
        assert result is True  # $10 >= $5 ✓

    def test_should_not_emit_zero_old_price_below_threshold(self):
        """Test no emission when old price is zero and absolute threshold not met."""
        result = should_emit_price_change(
            Decimal("0.00"),
            Decimal("10.00"),
            Decimal("20.00"),  # $10 < $20 ✗
            Decimal("50.0"),  # Irrelevant
        )
        assert result is False

    def test_should_emit_small_price_drop(self):
        """Test small price drop that meets percent threshold."""
        # Change: $50 → $48 = 4% change
        result = should_emit_price_change(
            Decimal("50.00"),
            Decimal("48.00"),
            Decimal("5.00"),  # $2 < $5 ✗
            Decimal("3.0"),  # 4% >= 3% ✓
        )
        assert result is True

    def test_should_emit_large_absolute_small_percent(self):
        """Test large absolute change with small percentage."""
        # Change: $1000 → $995 = 0.5% change, $5 absolute
        result = should_emit_price_change(
            Decimal("1000.00"),
            Decimal("995.00"),
            Decimal("3.00"),  # $5 >= $3 ✓
            Decimal("1.0"),  # 0.5% < 1% ✗
        )
        assert result is True

    def test_decimal_precision_calculation(self):
        """Test precise decimal calculations for percentage."""
        # Change: $99.99 → $100.00 = 0.01% change
        result = should_emit_price_change(
            Decimal("99.99"),
            Decimal("100.00"),
            Decimal("0.50"),  # $0.01 < $0.50 ✗
            Decimal("0.005"),  # 0.01% >= 0.005% ✓
        )
        assert result is True


class TestIngestionEventService:
    """Test IngestionEventService methods."""

    def test_emit_listing_created(self):
        """Test emitting listing.created event."""
        service = IngestionEventService()

        # Create a mock Listing
        now = datetime.utcnow()
        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "Gaming PC"
        listing.price_usd = 599.99
        listing.marketplace = "ebay"
        listing.vendor_item_id = "123"
        listing.created_at = now

        service.emit_listing_created(listing, provenance="ebay_api", quality="full")

        events = service.get_events()
        assert len(events) == 1
        assert isinstance(events[0], ListingCreatedEvent)
        assert events[0].listing_id == 1
        assert events[0].title == "Gaming PC"
        assert events[0].price == Decimal("599.99")
        assert events[0].marketplace == "ebay"
        assert events[0].vendor_item_id == "123"
        assert events[0].provenance == "ebay_api"
        assert events[0].quality == "full"
        assert events[0].created_at == now

    def test_emit_price_changed(self):
        """Test emitting price.changed event."""
        service = IngestionEventService()

        # Create a mock Listing
        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "Gaming PC"
        listing.price_usd = 549.99  # New price
        listing.marketplace = "ebay"
        listing.vendor_item_id = "123"

        old_price = Decimal("599.99")

        service.emit_price_changed(listing, old_price, Decimal("549.99"))

        events = service.get_events()
        assert len(events) == 1
        assert isinstance(events[0], PriceChangedEvent)
        assert events[0].listing_id == 1
        assert events[0].title == "Gaming PC"
        assert events[0].old_price == Decimal("599.99")
        assert events[0].new_price == Decimal("549.99")
        assert events[0].change_amount == Decimal("-50.00")
        assert events[0].marketplace == "ebay"
        assert events[0].vendor_item_id == "123"

    def test_emit_price_changed_calculates_percentage(self):
        """Test price.changed event calculates percentage correctly."""
        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.marketplace = "ebay"
        listing.vendor_item_id = None

        # $100 → $90 = -10% change
        service.emit_price_changed(listing, Decimal("100.00"), Decimal("90.00"))

        events = service.get_events()
        event = events[0]
        assert event.change_amount == Decimal("-10.00")
        assert event.change_percent == Decimal("-10.00")

    def test_emit_price_changed_with_zero_old_price(self):
        """Test price.changed event with zero old price."""
        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.marketplace = "other"
        listing.vendor_item_id = None

        service.emit_price_changed(listing, Decimal("0.00"), Decimal("50.00"))

        events = service.get_events()
        event = events[0]
        assert event.old_price == Decimal("0.00")
        assert event.new_price == Decimal("50.00")
        assert event.change_amount == Decimal("50.00")
        assert event.change_percent == Decimal("0.00")  # Can't calculate % from zero

    def test_emit_multiple_events(self):
        """Test emitting multiple events of different types."""
        service = IngestionEventService()

        # Create two mock listings
        now = datetime.utcnow()

        listing1 = MagicMock(spec=Listing)
        listing1.id = 1
        listing1.title = "PC 1"
        listing1.price_usd = 599.99
        listing1.marketplace = "ebay"
        listing1.vendor_item_id = "123"
        listing1.created_at = now

        listing2 = MagicMock(spec=Listing)
        listing2.id = 2
        listing2.title = "PC 2"
        listing2.price_usd = 499.99
        listing2.marketplace = "other"
        listing2.vendor_item_id = None

        # Emit listing.created
        service.emit_listing_created(listing1, "ebay_api", "full")

        # Emit price.changed
        service.emit_price_changed(listing2, Decimal("599.99"), Decimal("499.99"))

        events = service.get_events()
        assert len(events) == 2
        assert isinstance(events[0], ListingCreatedEvent)
        assert isinstance(events[1], PriceChangedEvent)

    def test_get_events_returns_copy(self):
        """Test that get_events() returns a copy, not the original list."""
        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.price_usd = 599.99
        listing.marketplace = "ebay"
        listing.vendor_item_id = "123"
        listing.created_at = datetime.utcnow()

        service.emit_listing_created(listing, "ebay_api", "full")

        events1 = service.get_events()
        events2 = service.get_events()

        # Should be equal but not the same object
        assert events1 == events2
        assert events1 is not events2

    def test_clear_events(self):
        """Test clearing all events."""
        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.price_usd = 599.99
        listing.marketplace = "ebay"
        listing.vendor_item_id = "123"
        listing.created_at = datetime.utcnow()

        service.emit_listing_created(listing, "ebay_api", "full")
        assert len(service.get_events()) == 1

        service.clear_events()
        assert len(service.get_events()) == 0


class TestCheckAndEmitPriceChange:
    """Test check_and_emit_price_change() with settings integration."""

    def test_check_and_emit_with_settings(self, monkeypatch):
        """Test check_and_emit_price_change uses settings thresholds."""
        # Mock settings
        mock_settings = MagicMock()
        mock_settings.ingestion.price_change_threshold_abs = 1.0
        mock_settings.ingestion.price_change_threshold_pct = 2.0

        mock_get_settings = MagicMock(return_value=mock_settings)
        monkeypatch.setattr("dealbrain_api.settings.get_settings", mock_get_settings)

        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.price_usd = 98.00
        listing.marketplace = "ebay"
        listing.vendor_item_id = None

        # Should emit: $100 → $98 = $2 change (>= $1 threshold)
        emitted = service.check_and_emit_price_change(listing, Decimal("100.00"), Decimal("98.00"))

        assert emitted is True
        assert len(service.get_events()) == 1
        assert isinstance(service.get_events()[0], PriceChangedEvent)

    def test_check_and_emit_does_not_emit_below_threshold(self, monkeypatch):
        """Test check_and_emit_price_change does not emit below threshold."""
        # Mock settings with higher thresholds
        mock_settings = MagicMock()
        mock_settings.ingestion.price_change_threshold_abs = 5.0
        mock_settings.ingestion.price_change_threshold_pct = 5.0

        mock_get_settings = MagicMock(return_value=mock_settings)
        monkeypatch.setattr("dealbrain_api.settings.get_settings", mock_get_settings)

        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.price_usd = 99.00
        listing.marketplace = "ebay"
        listing.vendor_item_id = None

        # Should NOT emit: $100 → $99 = $1 change (<$5) and 1% (<5%)
        emitted = service.check_and_emit_price_change(listing, Decimal("100.00"), Decimal("99.00"))

        assert emitted is False
        assert len(service.get_events()) == 0

    def test_check_and_emit_meets_percent_threshold_only(self, monkeypatch):
        """Test emission when only percent threshold is met."""
        mock_settings = MagicMock()
        mock_settings.ingestion.price_change_threshold_abs = 10.0  # High abs threshold
        mock_settings.ingestion.price_change_threshold_pct = 2.0  # Low pct threshold

        mock_get_settings = MagicMock(return_value=mock_settings)
        monkeypatch.setattr("dealbrain_api.settings.get_settings", mock_get_settings)

        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.price_usd = 95.00
        listing.marketplace = "ebay"
        listing.vendor_item_id = None

        # Should emit: $100 → $95 = $5 change (<$10 abs) but 5% (>=2% pct) ✓
        emitted = service.check_and_emit_price_change(listing, Decimal("100.00"), Decimal("95.00"))

        assert emitted is True
        assert len(service.get_events()) == 1

    def test_check_and_emit_meets_absolute_threshold_only(self, monkeypatch):
        """Test emission when only absolute threshold is met."""
        mock_settings = MagicMock()
        mock_settings.ingestion.price_change_threshold_abs = 5.0  # Low abs threshold
        mock_settings.ingestion.price_change_threshold_pct = 10.0  # High pct threshold

        mock_get_settings = MagicMock(return_value=mock_settings)
        monkeypatch.setattr("dealbrain_api.settings.get_settings", mock_get_settings)

        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "Expensive PC"
        listing.price_usd = 1995.00
        listing.marketplace = "ebay"
        listing.vendor_item_id = None

        # Should emit: $2000 → $1995 = $5 change (>=$5 abs) ✓ but 0.25% (<10% pct)
        emitted = service.check_and_emit_price_change(
            listing, Decimal("2000.00"), Decimal("1995.00")
        )

        assert emitted is True
        assert len(service.get_events()) == 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_price_change_with_very_small_decimals(self):
        """Test price change with very small decimal amounts."""
        # Change: $100.00 → $100.01 = $0.01 change
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("100.01"),
            Decimal("0.01"),  # Exact match
            Decimal("0.01"),  # 0.01% change
        )
        assert result is True

    def test_price_change_calculation_with_decimals(self):
        """Test precise decimal calculations for price changes."""
        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.marketplace = "other"
        listing.vendor_item_id = None

        service.emit_price_changed(listing, Decimal("100.00"), Decimal("99.99"))

        event = service.get_events()[0]
        assert event.change_amount == Decimal("-0.01")
        # Percent: (-0.01 / 100) * 100 = -0.01%
        assert abs(event.change_percent - Decimal("-0.01")) < Decimal("0.001")

    def test_large_price_change(self):
        """Test large price change detection."""
        result = should_emit_price_change(
            Decimal("1000.00"),
            Decimal("100.00"),
            Decimal("1.00"),
            Decimal("1.0"),
        )
        assert result is True  # 90% change, $900 absolute

    def test_price_increase_event(self):
        """Test price increase emits positive change."""
        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.marketplace = "ebay"
        listing.vendor_item_id = "123"

        service.emit_price_changed(listing, Decimal("500.00"), Decimal("600.00"))

        event = service.get_events()[0]
        assert event.change_amount == Decimal("100.00")  # Positive
        assert event.change_percent == Decimal("20.00")  # 20% increase

    def test_same_price_no_emit(self):
        """Test that same price does not emit event."""
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("100.00"),
            Decimal("1.00"),
            Decimal("1.0"),
        )
        assert result is False  # No change

    def test_event_timestamp_accuracy(self):
        """Test that PriceChangedEvent timestamp is recent."""
        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.marketplace = "ebay"
        listing.vendor_item_id = None

        before = datetime.utcnow()
        service.emit_price_changed(listing, Decimal("100.00"), Decimal("90.00"))
        after = datetime.utcnow()

        event = service.get_events()[0]
        assert before <= event.changed_at <= after


class TestPriceThresholdEdgeCases:
    """Test price threshold edge cases as specified in ID-026."""

    def test_exactly_one_dollar_change_should_emit(self):
        """Test exactly $1 change should emit."""
        # $100 → $99 = exactly $1 change
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("99.00"),
            Decimal("1.00"),  # Threshold
            Decimal("5.0"),
        )
        assert result is True  # Exactly $1 meets threshold

    def test_ninety_nine_cents_change_should_not_emit(self):
        """Test $0.99 change should not emit."""
        # $100 → $99.01 = $0.99 change
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("99.01"),
            Decimal("1.00"),  # Threshold
            Decimal("5.0"),
        )
        assert result is False  # $0.99 < $1

    def test_exactly_two_percent_change_should_emit(self):
        """Test exactly 2% change should emit."""
        # $100 → $98 = exactly 2% change
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("98.00"),
            Decimal("10.00"),  # High absolute threshold (not met)
            Decimal("2.0"),  # Exactly 2%
        )
        assert result is True  # Exactly 2% meets threshold

    def test_one_point_nine_percent_change_should_not_emit(self):
        """Test 1.9% change should not emit."""
        # $100 → $98.10 = 1.9% change
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("98.10"),
            Decimal("10.00"),  # Not met
            Decimal("2.0"),  # Not met (1.9% < 2%)
        )
        assert result is False

    def test_small_absolute_large_percentage(self):
        """Test small absolute change with large percentage."""
        # $10 → $9 = $1 absolute, 10% change
        # Threshold: $5 abs, 8% pct
        result = should_emit_price_change(
            Decimal("10.00"),
            Decimal("9.00"),
            Decimal("5.00"),  # $1 < $5 (not met)
            Decimal("8.0"),  # 10% >= 8% (met)
        )
        assert result is True  # Percent threshold met

    def test_large_absolute_small_percentage(self):
        """Test large absolute change with small percentage."""
        # $1000 → $990 = $10 absolute, 1% change
        # Threshold: $5 abs, 5% pct
        result = should_emit_price_change(
            Decimal("1000.00"),
            Decimal("990.00"),
            Decimal("5.00"),  # $10 >= $5 (met)
            Decimal("5.0"),  # 1% < 5% (not met)
        )
        assert result is True  # Absolute threshold met

    def test_exactly_threshold_both_conditions(self):
        """Test when both thresholds are exactly met."""
        # $100 → $95 = $5 absolute, 5% change
        # Threshold: $5 abs, 5% pct
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("95.00"),
            Decimal("5.00"),  # Exactly met
            Decimal("5.0"),  # Exactly met
        )
        assert result is True

    def test_price_increase_meets_absolute_threshold(self):
        """Test price increase meeting absolute threshold."""
        # $100 → $105 = +$5 absolute, +5% change
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("105.00"),
            Decimal("5.00"),  # $5 >= $5 (met)
            Decimal("10.0"),  # 5% < 10% (not met)
        )
        assert result is True

    def test_price_increase_meets_percent_threshold(self):
        """Test price increase meeting percent threshold."""
        # $100 → $103 = +$3 absolute, +3% change
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("103.00"),
            Decimal("5.00"),  # $3 < $5 (not met)
            Decimal("2.0"),  # 3% >= 2% (met)
        )
        assert result is True

    def test_both_thresholds_not_met(self):
        """Test when neither threshold is met."""
        # $100 → $99.50 = $0.50 absolute, 0.5% change
        # Threshold: $1 abs, 1% pct
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("99.50"),
            Decimal("1.00"),  # $0.50 < $1 (not met)
            Decimal("1.0"),  # 0.5% < 1% (not met)
        )
        assert result is False

    def test_fractional_dollar_threshold(self):
        """Test with fractional dollar threshold."""
        # $100 → $99.50 = $0.50 change
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("99.50"),
            Decimal("0.50"),  # Exactly met
            Decimal("1.0"),
        )
        assert result is True

    def test_very_small_price_change(self):
        """Test with very small price change (pennies)."""
        # $100.00 → $100.02 = $0.02 change, 0.02% change
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("100.02"),
            Decimal("0.01"),  # $0.02 >= $0.01 (met)
            Decimal("0.01"),  # 0.02% >= 0.01% (met)
        )
        assert result is True

    def test_price_change_rounding_edge_case(self):
        """Test price change with rounding edge cases."""
        # $99.99 → $100.00 = $0.01 change, ~0.01% change
        result = should_emit_price_change(
            Decimal("99.99"),
            Decimal("100.00"),
            Decimal("0.01"),  # Exactly met
            Decimal("0.01"),  # Should be met
        )
        assert result is True

    def test_zero_price_thresholds(self):
        """Test with zero thresholds (always emit)."""
        # Any change should emit with zero thresholds
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("99.99"),
            Decimal("0.00"),  # Zero threshold
            Decimal("0.0"),  # Zero threshold
        )
        assert result is True  # $0.01 >= $0, 0.01% >= 0%

    def test_negative_price_change_abs_value(self):
        """Test that absolute value is used for comparison."""
        # $100 → $110 = +$10, +10%
        # Should use abs($10) and abs(10%) for threshold comparison
        result = should_emit_price_change(
            Decimal("100.00"),
            Decimal("110.00"),
            Decimal("10.00"),  # |+$10| >= $10 (met)
            Decimal("20.0"),  # |+10%| < 20% (not met)
        )
        assert result is True

    def test_high_precision_percentage_calculation(self):
        """Test high precision percentage calculation."""
        # $99.99 → $98.99 = $1.00, ~1.00010001%
        result = should_emit_price_change(
            Decimal("99.99"),
            Decimal("98.99"),
            Decimal("2.00"),  # Not met
            Decimal("1.0"),  # Should be met (1.00010001% >= 1.0%)
        )
        assert result is True

    def test_event_service_integration_exact_thresholds(self, monkeypatch):
        """Test IngestionEventService with exact threshold values."""
        # Mock settings with specific thresholds
        mock_settings = MagicMock()
        mock_settings.ingestion.price_change_threshold_abs = 1.0
        mock_settings.ingestion.price_change_threshold_pct = 2.0

        mock_get_settings = MagicMock(return_value=mock_settings)
        monkeypatch.setattr("dealbrain_api.settings.get_settings", mock_get_settings)

        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.marketplace = "ebay"
        listing.vendor_item_id = None

        # Test exactly $1 change
        emitted = service.check_and_emit_price_change(
            listing, Decimal("100.00"), Decimal("99.00")
        )
        assert emitted is True

        service.clear_events()

        # Test $0.99 change (should not emit)
        emitted = service.check_and_emit_price_change(
            listing, Decimal("100.00"), Decimal("99.01")
        )
        assert emitted is False

    def test_event_service_integration_percent_boundary(self, monkeypatch):
        """Test IngestionEventService with percent boundary cases."""
        mock_settings = MagicMock()
        mock_settings.ingestion.price_change_threshold_abs = 10.0
        mock_settings.ingestion.price_change_threshold_pct = 2.0

        mock_get_settings = MagicMock(return_value=mock_settings)
        monkeypatch.setattr("dealbrain_api.settings.get_settings", mock_get_settings)

        service = IngestionEventService()

        listing = MagicMock(spec=Listing)
        listing.id = 1
        listing.title = "PC"
        listing.marketplace = "ebay"
        listing.vendor_item_id = None

        # Test exactly 2% change ($100 → $98)
        emitted = service.check_and_emit_price_change(
            listing, Decimal("100.00"), Decimal("98.00")
        )
        assert emitted is True

        service.clear_events()

        # Test 1.9% change ($100 → $98.10) - should not emit
        emitted = service.check_and_emit_price_change(
            listing, Decimal("100.00"), Decimal("98.10")
        )
        assert emitted is False
