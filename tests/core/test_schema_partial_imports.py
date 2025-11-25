"""Tests for partial import schema changes in NormalizedListingSchema."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from dealbrain_core.schemas.ingestion import NormalizedListingSchema


class TestNormalizedListingSchemaPartialImports:
    """Test suite for partial import functionality in NormalizedListingSchema."""

    def test_accepts_price_none_with_title(self):
        """Schema should accept price=None when title is provided."""
        data = {
            "title": "Test PC",
            "price": None,
            "condition": "new",
            "marketplace": "ebay",
        }
        schema = NormalizedListingSchema(**data)
        assert schema.title == "Test PC"
        assert schema.price is None

    def test_rejects_both_price_and_title_none(self):
        """Schema should reject when both price and title are None."""
        data = {
            "title": None,
            "price": None,
            "condition": "new",
            "marketplace": "ebay",
        }
        with pytest.raises(ValidationError) as exc_info:
            NormalizedListingSchema(**data)

        errors = exc_info.value.errors()
        # Should have validation errors for missing required fields
        assert len(errors) > 0

    def test_rejects_empty_title_with_price_none(self):
        """Schema should reject empty title when price is None."""
        data = {
            "title": "   ",  # Empty/whitespace-only title
            "price": None,
            "condition": "new",
            "marketplace": "ebay",
        }
        with pytest.raises(ValidationError) as exc_info:
            NormalizedListingSchema(**data)

        errors = exc_info.value.errors()
        # Should fail validation for minimum data requirement
        assert any(
            "At least title must be provided when price is missing" in str(error)
            for error in errors
        )

    def test_quality_defaults_to_full(self):
        """quality field should default to 'full'."""
        data = {
            "title": "Test PC",
            "price": Decimal("299.99"),
            "condition": "new",
            "marketplace": "ebay",
        }
        schema = NormalizedListingSchema(**data)
        assert schema.quality == "full"

    def test_extraction_metadata_defaults_to_empty_dict(self):
        """extraction_metadata field should default to {}."""
        data = {
            "title": "Test PC",
            "price": Decimal("299.99"),
            "condition": "new",
            "marketplace": "ebay",
        }
        schema = NormalizedListingSchema(**data)
        assert schema.extraction_metadata == {}

    def test_missing_fields_defaults_to_empty_list(self):
        """missing_fields field should default to []."""
        data = {
            "title": "Test PC",
            "price": Decimal("299.99"),
            "condition": "new",
            "marketplace": "ebay",
        }
        schema = NormalizedListingSchema(**data)
        assert schema.missing_fields == []

    def test_quality_accepts_full(self):
        """quality field should accept 'full'."""
        data = {
            "title": "Test PC",
            "price": Decimal("299.99"),
            "condition": "new",
            "marketplace": "ebay",
            "quality": "full",
        }
        schema = NormalizedListingSchema(**data)
        assert schema.quality == "full"

    def test_quality_accepts_partial(self):
        """quality field should accept 'partial'."""
        data = {
            "title": "Test PC",
            "price": None,
            "condition": "new",
            "marketplace": "ebay",
            "quality": "partial",
        }
        schema = NormalizedListingSchema(**data)
        assert schema.quality == "partial"

    def test_quality_rejects_invalid_value(self):
        """quality field should reject values other than 'full' or 'partial'."""
        data = {
            "title": "Test PC",
            "price": Decimal("299.99"),
            "condition": "new",
            "marketplace": "ebay",
            "quality": "invalid",
        }
        with pytest.raises(ValidationError) as exc_info:
            NormalizedListingSchema(**data)

        errors = exc_info.value.errors()
        # Should have validation error for invalid quality value
        assert any(error["loc"] == ("quality",) for error in errors)

    def test_extraction_metadata_with_custom_values(self):
        """extraction_metadata should accept custom provenance tracking."""
        data = {
            "title": "Test PC",
            "price": None,
            "condition": "new",
            "marketplace": "ebay",
            "extraction_metadata": {
                "title": "extracted",
                "condition": "extracted",
                "price": "extraction_failed",
                "cpu_model": "manual",
            },
        }
        schema = NormalizedListingSchema(**data)
        assert schema.extraction_metadata == {
            "title": "extracted",
            "condition": "extracted",
            "price": "extraction_failed",
            "cpu_model": "manual",
        }

    def test_missing_fields_with_custom_values(self):
        """missing_fields should accept list of field names."""
        data = {
            "title": "Test PC",
            "price": None,
            "condition": "new",
            "marketplace": "ebay",
            "missing_fields": ["price", "cpu_model", "ram_gb"],
        }
        schema = NormalizedListingSchema(**data)
        assert schema.missing_fields == ["price", "cpu_model", "ram_gb"]

    def test_partial_quality_with_metadata_and_missing_fields(self):
        """Test full partial import scenario with all tracking fields."""
        data = {
            "title": "Dell OptiPlex Mini PC",
            "price": None,
            "condition": "used",
            "marketplace": "ebay",
            "quality": "partial",
            "extraction_metadata": {
                "title": "extracted",
                "condition": "extracted",
                "marketplace": "extracted",
                "price": "extraction_failed",
            },
            "missing_fields": ["price"],
        }
        schema = NormalizedListingSchema(**data)
        assert schema.quality == "partial"
        assert schema.price is None
        assert schema.extraction_metadata["price"] == "extraction_failed"
        assert "price" in schema.missing_fields

    def test_full_quality_with_all_data(self):
        """Test full quality listing with complete data."""
        data = {
            "title": "HP EliteDesk 800 G3 Mini",
            "price": Decimal("349.99"),
            "condition": "refurb",
            "marketplace": "amazon",
            "cpu_model": "Intel Core i5-7500T",
            "ram_gb": 16,
            "storage_gb": 256,
            "quality": "full",
            "extraction_metadata": {
                "title": "extracted",
                "price": "extracted",
                "condition": "extracted",
                "cpu_model": "extracted",
                "ram_gb": "extracted",
                "storage_gb": "extracted",
            },
            "missing_fields": [],
        }
        schema = NormalizedListingSchema(**data)
        assert schema.quality == "full"
        assert schema.price == Decimal("349.99")
        assert schema.extraction_metadata["cpu_model"] == "extracted"
        assert schema.missing_fields == []
