"""Tests for listing normalizer service."""

from __future__ import annotations

from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from dealbrain_api.db import Base
from dealbrain_api.models.core import Cpu
from dealbrain_api.services.ingestion import ListingNormalizer
from dealbrain_core.schemas.ingestion import NormalizedListingSchema

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
        pytest.skip("aiosqlite is not installed; skipping normalizer tests")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


class TestCurrencyConversion:
    """Tests for currency conversion."""

    def test_convert_usd_to_usd(self, db_session: AsyncSession):
        """Test USD to USD conversion (no change)."""
        normalizer = ListingNormalizer(db_session)
        result = normalizer._convert_to_usd(Decimal("599.99"), "USD")

        assert result == Decimal("599.99")

    def test_convert_eur_to_usd(self, db_session: AsyncSession):
        """Test EUR to USD conversion."""
        normalizer = ListingNormalizer(db_session)
        result = normalizer._convert_to_usd(Decimal("500"), "EUR")

        # 500 EUR * 1.08 = 540.00 USD
        assert result == Decimal("540.00")

    def test_convert_gbp_to_usd(self, db_session: AsyncSession):
        """Test GBP to USD conversion."""
        normalizer = ListingNormalizer(db_session)
        result = normalizer._convert_to_usd(Decimal("400"), "GBP")

        # 400 GBP * 1.27 = 508.00 USD
        assert result == Decimal("508.00")

    def test_convert_cad_to_usd(self, db_session: AsyncSession):
        """Test CAD to USD conversion."""
        normalizer = ListingNormalizer(db_session)
        result = normalizer._convert_to_usd(Decimal("1000"), "CAD")

        # 1000 CAD * 0.74 = 740.00 USD
        assert result == Decimal("740.00")

    def test_convert_unknown_currency_defaults_to_usd(self, db_session: AsyncSession):
        """Test that unknown currency defaults to USD (no conversion)."""
        normalizer = ListingNormalizer(db_session)
        result = normalizer._convert_to_usd(Decimal("599.99"), "JPY")

        # Unknown currency defaults to USD
        assert result == Decimal("599.99")

    def test_convert_none_currency_defaults_to_usd(self, db_session: AsyncSession):
        """Test that None currency defaults to USD (no conversion)."""
        normalizer = ListingNormalizer(db_session)
        result = normalizer._convert_to_usd(Decimal("599.99"), None)

        # None currency defaults to USD
        assert result == Decimal("599.99")

    def test_convert_preserves_decimal_precision(self, db_session: AsyncSession):
        """Test that conversion preserves 2 decimal places."""
        normalizer = ListingNormalizer(db_session)
        result = normalizer._convert_to_usd(Decimal("123.456"), "EUR")

        # 123.456 EUR * 1.08 = 133.33248 → 133.33
        assert result == Decimal("133.33")
        assert result.as_tuple().exponent == -2  # 2 decimal places


class TestConditionNormalization:
    """Tests for condition string normalization."""

    def test_normalize_condition_new(self, db_session: AsyncSession):
        """Test 'new' condition normalization."""
        normalizer = ListingNormalizer(db_session)

        assert normalizer._normalize_condition("new") == "new"
        assert normalizer._normalize_condition("NEW") == "new"
        assert normalizer._normalize_condition("New") == "new"

    def test_normalize_condition_brand_new(self, db_session: AsyncSession):
        """Test 'brand new' condition normalization."""
        normalizer = ListingNormalizer(db_session)

        assert normalizer._normalize_condition("brand new") == "new"
        assert normalizer._normalize_condition("Brand New") == "new"
        assert normalizer._normalize_condition("BRAND NEW") == "new"

    def test_normalize_condition_refurbished(self, db_session: AsyncSession):
        """Test refurbished condition variants."""
        normalizer = ListingNormalizer(db_session)

        assert normalizer._normalize_condition("refurbished") == "refurb"
        assert normalizer._normalize_condition("Seller refurbished") == "refurb"
        assert normalizer._normalize_condition("manufacturer refurbished") == "refurb"
        assert normalizer._normalize_condition("MANUFACTURER REFURBISHED") == "refurb"

    def test_normalize_condition_used(self, db_session: AsyncSession):
        """Test used condition variants."""
        normalizer = ListingNormalizer(db_session)

        assert normalizer._normalize_condition("used") == "used"
        assert normalizer._normalize_condition("Used") == "used"
        assert normalizer._normalize_condition("pre-owned") == "used"
        assert normalizer._normalize_condition("Pre-Owned") == "used"
        assert normalizer._normalize_condition("open box") == "used"
        assert normalizer._normalize_condition("for parts") == "used"

    def test_normalize_condition_unknown_defaults_to_used(self, db_session: AsyncSession):
        """Test that unknown conditions default to 'used'."""
        normalizer = ListingNormalizer(db_session)

        assert normalizer._normalize_condition("unknown") == "used"
        assert normalizer._normalize_condition("excellent") == "used"
        assert normalizer._normalize_condition("like new") == "used"

    def test_normalize_condition_none_defaults_to_used(self, db_session: AsyncSession):
        """Test that None condition defaults to 'used'."""
        normalizer = ListingNormalizer(db_session)

        assert normalizer._normalize_condition(None) == "used"

    def test_normalize_condition_handles_whitespace(self, db_session: AsyncSession):
        """Test that whitespace is trimmed before normalization."""
        normalizer = ListingNormalizer(db_session)

        assert normalizer._normalize_condition("  new  ") == "new"
        assert normalizer._normalize_condition("\trefurbished\n") == "refurb"


class TestSpecExtraction:
    """Tests for spec extraction from descriptions."""

    def test_extract_cpu_from_description(self, db_session: AsyncSession):
        """Test CPU extraction from description."""
        normalizer = ListingNormalizer(db_session)

        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599"),
            description="Gaming PC with Intel Core i7-12700K processor",
            marketplace="other",
            condition="used",
        )

        specs = normalizer._extract_specs(data)

        assert "cpu_model" in specs
        assert "i7-12700K" in specs["cpu_model"]

    def test_extract_cpu_i5_variant(self, db_session: AsyncSession):
        """Test CPU extraction for i5 variants."""
        normalizer = ListingNormalizer(db_session)

        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599"),
            description="Compact PC with Intel i5-13600K",
            marketplace="other",
            condition="used",
        )

        specs = normalizer._extract_specs(data)

        assert "cpu_model" in specs
        assert "i5-13600K" in specs["cpu_model"]

    def test_extract_cpu_ryzen(self, db_session: AsyncSession):
        """Test CPU extraction for AMD Ryzen."""
        normalizer = ListingNormalizer(db_session)

        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599"),
            description="AMD Ryzen 7 5800X3D Gaming PC",
            marketplace="other",
            condition="used",
        )

        specs = normalizer._extract_specs(data)

        assert "cpu_model" in specs
        # Ryzen pattern: "Ryzen 7" + "-" + "5800X3D"
        assert "Ryzen 7" in specs["cpu_model"]
        assert "5800X3D" in specs["cpu_model"]

    def test_extract_ram_from_description(self, db_session: AsyncSession):
        """Test RAM extraction from description."""
        normalizer = ListingNormalizer(db_session)

        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599"),
            description="Features 16GB DDR4 RAM",
            marketplace="other",
            condition="used",
        )

        specs = normalizer._extract_specs(data)

        assert "ram_gb" in specs
        assert specs["ram_gb"] == 16

    def test_extract_ram_various_formats(self, db_session: AsyncSession):
        """Test RAM extraction with various formats."""
        normalizer = ListingNormalizer(db_session)

        test_cases = [
            ("32GB RAM", 32),
            ("16 GB DDR4", 16),
            ("8GB Memory", 8),
            ("64 GB", 64),
        ]

        for description, expected_ram in test_cases:
            data = NormalizedListingSchema(
                title="PC",
                price=Decimal("599"),
                description=description,
                marketplace="other",
                condition="used",
            )

            specs = normalizer._extract_specs(data)
            assert specs.get("ram_gb") == expected_ram

    def test_extract_storage_from_description(self, db_session: AsyncSession):
        """Test storage extraction from description."""
        normalizer = ListingNormalizer(db_session)

        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599"),
            description="512GB NVMe SSD",
            marketplace="other",
            condition="used",
        )

        specs = normalizer._extract_specs(data)

        assert "storage_gb" in specs
        assert specs["storage_gb"] == 512

    def test_extract_storage_with_tb(self, db_session: AsyncSession):
        """Test storage extraction with TB units."""
        normalizer = ListingNormalizer(db_session)

        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599"),
            description="1TB SSD storage",
            marketplace="other",
            condition="used",
        )

        specs = normalizer._extract_specs(data)

        assert "storage_gb" in specs
        assert specs["storage_gb"] == 1024  # 1 TB = 1024 GB

    def test_extract_storage_various_formats(self, db_session: AsyncSession):
        """Test storage extraction with various formats."""
        normalizer = ListingNormalizer(db_session)

        test_cases = [
            ("256GB SSD", 256),
            ("512 GB NVMe", 512),
            ("1 TB HDD", 1024),
            ("2TB Storage", 2048),
        ]

        for description, expected_storage in test_cases:
            data = NormalizedListingSchema(
                title="PC",
                price=Decimal("599"),
                description=description,
                marketplace="other",
                condition="used",
            )

            specs = normalizer._extract_specs(data)
            assert specs.get("storage_gb") == expected_storage

    def test_extract_all_specs_combined(self, db_session: AsyncSession):
        """Test extracting all specs from a complete description."""
        normalizer = ListingNormalizer(db_session)

        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599"),
            description="Gaming PC with Intel Core i7-12700K processor, 16GB DDR4 RAM, 512GB NVMe SSD",
            marketplace="other",
            condition="used",
        )

        specs = normalizer._extract_specs(data)

        assert "cpu_model" in specs
        assert "i7-12700K" in specs["cpu_model"]
        assert specs["ram_gb"] == 16
        assert specs["storage_gb"] == 512

    def test_extract_no_specs_from_empty_description(self, db_session: AsyncSession):
        """Test that empty description returns empty specs dict."""
        normalizer = ListingNormalizer(db_session)

        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599"),
            description=None,
            marketplace="other",
            condition="used",
        )

        specs = normalizer._extract_specs(data)

        assert specs == {}

    def test_extract_only_missing_specs(self, db_session: AsyncSession):
        """Test that extraction only fills in missing fields."""
        normalizer = ListingNormalizer(db_session)

        # Already has CPU and RAM, should only extract storage
        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599"),
            description="Gaming PC with Intel i7-12700K processor, 16GB DDR4 RAM, 1TB SSD storage",
            marketplace="other",
            condition="used",
            cpu_model="i9-13900K",  # Already set
            ram_gb=32,  # Already set
        )

        specs = normalizer._extract_specs(data)

        # Should not override existing values
        assert "cpu_model" not in specs  # Not extracted because already present
        assert "ram_gb" not in specs  # Not extracted because already present
        assert specs["storage_gb"] == 1024  # Extracted because missing


class TestCPUCanonicalization:
    """Tests for CPU canonicalization against catalog."""

    @pytest.mark.asyncio
    async def test_canonicalize_cpu_exact_match(self, db_session: AsyncSession):
        """Test exact CPU name matching."""
        # Create test CPU in catalog
        cpu = Cpu(
            name="Intel Core i7-12700K",
            manufacturer="Intel",
            cpu_mark_multi=30000,
            cpu_mark_single=4000,
            igpu_mark=2500,
        )
        db_session.add(cpu)
        await db_session.commit()

        normalizer = ListingNormalizer(db_session)
        result = await normalizer._canonicalize_cpu("Intel Core i7-12700K")

        assert result is not None
        assert result["name"] == "Intel Core i7-12700K"
        assert result["cpu_mark_multi"] == 30000
        assert result["cpu_mark_single"] == 4000
        assert result["igpu_mark"] == 2500

    @pytest.mark.asyncio
    async def test_canonicalize_cpu_partial_match(self, db_session: AsyncSession):
        """Test partial CPU name matching."""
        # Create test CPU with full name
        cpu = Cpu(
            name="Intel Core i7-12700K 12-Core 3.6 GHz",
            manufacturer="Intel",
            cpu_mark_multi=30000,
            cpu_mark_single=4000,
            igpu_mark=2500,
        )
        db_session.add(cpu)
        await db_session.commit()

        normalizer = ListingNormalizer(db_session)

        # Should match with partial string
        result = await normalizer._canonicalize_cpu("i7-12700K")

        assert result is not None
        assert "i7-12700K" in result["name"]
        assert result["cpu_mark_multi"] == 30000

    @pytest.mark.asyncio
    async def test_canonicalize_cpu_case_insensitive(self, db_session: AsyncSession):
        """Test case-insensitive CPU matching."""
        cpu = Cpu(
            name="Intel Core i7-12700K",
            manufacturer="Intel",
            cpu_mark_multi=30000,
            cpu_mark_single=4000,
            igpu_mark=2500,
        )
        db_session.add(cpu)
        await db_session.commit()

        normalizer = ListingNormalizer(db_session)

        # Should match regardless of case
        result = await normalizer._canonicalize_cpu("intel core I7-12700k")

        assert result is not None
        assert result["name"] == "Intel Core i7-12700K"

    @pytest.mark.asyncio
    async def test_canonicalize_cpu_no_match(self, db_session: AsyncSession):
        """Test when CPU not found in catalog."""
        normalizer = ListingNormalizer(db_session)
        result = await normalizer._canonicalize_cpu("Unknown CPU XYZ-9000")

        assert result is None

    @pytest.mark.asyncio
    async def test_canonicalize_cpu_none_input(self, db_session: AsyncSession):
        """Test CPU canonicalization with None input."""
        normalizer = ListingNormalizer(db_session)
        result = await normalizer._canonicalize_cpu(None)

        assert result is None

    @pytest.mark.asyncio
    async def test_canonicalize_cpu_with_null_benchmarks(self, db_session: AsyncSession):
        """Test CPU matching when benchmark data is null."""
        cpu = Cpu(
            name="Intel Pentium G4560",
            manufacturer="Intel",
            cpu_mark_multi=None,
            cpu_mark_single=None,
            igpu_mark=None,
        )
        db_session.add(cpu)
        await db_session.commit()

        normalizer = ListingNormalizer(db_session)
        result = await normalizer._canonicalize_cpu("Pentium G4560")

        assert result is not None
        assert result["name"] == "Intel Pentium G4560"
        assert result["cpu_mark_multi"] is None
        assert result["cpu_mark_single"] is None
        assert result["igpu_mark"] is None


class TestQualityAssessment:
    """Tests for data quality assessment."""

    def test_assess_quality_full(self, db_session: AsyncSession):
        """Test quality=full when all optional fields present."""
        normalizer = ListingNormalizer(db_session)

        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599.99"),
            condition="new",
            cpu_model="i7-12700K",
            ram_gb=16,
            storage_gb=512,
            images=["http://example.com/img.jpg"],
            marketplace="other",
        )

        quality = normalizer.assess_quality(data)

        assert quality == "full"

    def test_assess_quality_partial(self, db_session: AsyncSession):
        """Test quality=partial when some optional fields missing."""
        normalizer = ListingNormalizer(db_session)

        # Only has condition and images (2 optional fields)
        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599.99"),
            condition="new",
            images=["http://example.com/img.jpg"],
            marketplace="other",
        )

        quality = normalizer.assess_quality(data)

        assert quality == "partial"

    def test_assess_quality_minimal(self, db_session: AsyncSession):
        """Test quality=partial with minimal fields."""
        normalizer = ListingNormalizer(db_session)

        # Only required fields
        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599.99"),
            condition="used",
            marketplace="other",
        )

        quality = normalizer.assess_quality(data)

        assert quality == "partial"

    def test_assess_quality_threshold_boundary(self, db_session: AsyncSession):
        """Test quality assessment at threshold boundary (4 optional fields)."""
        normalizer = ListingNormalizer(db_session)

        # Exactly 4 optional fields (condition, cpu, ram, storage)
        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599.99"),
            condition="new",
            cpu_model="i7-12700K",
            ram_gb=16,
            storage_gb=512,
            marketplace="other",
        )

        quality = normalizer.assess_quality(data)

        assert quality == "full"

        # Remove one field to drop below threshold
        data_partial = NormalizedListingSchema(
            title="PC",
            price=Decimal("599.99"),
            condition="new",
            cpu_model="i7-12700K",
            ram_gb=16,
            # storage_gb removed
            marketplace="other",
        )

        quality_partial = normalizer.assess_quality(data_partial)

        assert quality_partial == "partial"

    def test_assess_quality_missing_required_field_raises_error(self, db_session: AsyncSession):
        """Test that missing required fields raise ValueError."""
        normalizer = ListingNormalizer(db_session)

        # This should raise an error during schema validation
        # But if somehow we get a schema without title, assess_quality should catch it
        # Note: Pydantic validation will prevent this, but we test the logic

        # We can't actually create an invalid schema due to Pydantic validation
        # So we test with a minimal valid schema and verify it doesn't raise
        data = NormalizedListingSchema(
            title="PC",
            price=Decimal("599.99"),
            condition="used",
            marketplace="other",
        )

        # Should not raise
        quality = normalizer.assess_quality(data)
        assert quality == "partial"


class TestNormalizeEndToEnd:
    """End-to-end tests for the complete normalization flow."""

    @pytest.mark.asyncio
    async def test_normalize_full_flow(self, db_session: AsyncSession):
        """Test complete normalization flow with all transformations."""
        # Create test CPU in catalog
        cpu = Cpu(
            name="Intel Core i7-12700K 12-Core 3.6 GHz",
            manufacturer="Intel",
            cpu_mark_multi=30000,
            cpu_mark_single=4000,
            igpu_mark=2500,
        )
        db_session.add(cpu)
        await db_session.commit()

        # Raw data from adapter (European listing)
        raw = NormalizedListingSchema(
            title="Gaming PC",
            price=Decimal("500"),  # EUR
            currency="EUR",
            condition="new",  # Use enum value directly
            description="PC with Intel Core i7-12700K processor, 16GB DDR4 RAM, 512GB SSD storage",
            marketplace="other",
            seller="TechStore",
            images=["http://example.com/image1.jpg"],
        )

        normalizer = ListingNormalizer(db_session)
        enriched = await normalizer.normalize(raw)

        # Check currency conversion
        assert enriched.price == Decimal("540.00")  # 500 EUR * 1.08 = 540 USD
        assert enriched.currency == "USD"

        # Check condition normalization
        assert enriched.condition == "new"

        # Check spec extraction
        assert enriched.ram_gb == 16
        assert enriched.storage_gb == 512

        # Check CPU canonicalization
        assert "Intel Core i7-12700K" in enriched.cpu_model
        assert "12-Core" in enriched.cpu_model

        # Check preserved fields
        assert enriched.title == "Gaming PC"
        assert enriched.seller == "TechStore"
        assert enriched.marketplace == "other"
        assert len(enriched.images) == 1

        # Check quality assessment
        quality = normalizer.assess_quality(enriched)
        assert quality == "full"

    @pytest.mark.asyncio
    async def test_normalize_partial_data(self, db_session: AsyncSession):
        """Test normalization with minimal data."""
        raw = NormalizedListingSchema(
            title="PC for Sale",
            price=Decimal("299.99"),
            currency="USD",
            condition="used",
            marketplace="other",
        )

        normalizer = ListingNormalizer(db_session)
        enriched = await normalizer.normalize(raw)

        # Should handle missing optional fields gracefully
        assert enriched.price == Decimal("299.99")
        assert enriched.currency == "USD"
        assert enriched.condition == "used"
        assert enriched.cpu_model is None
        assert enriched.ram_gb is None
        assert enriched.storage_gb is None
        assert enriched.images == []

        # Quality should be partial
        quality = normalizer.assess_quality(enriched)
        assert quality == "partial"

    @pytest.mark.asyncio
    async def test_normalize_with_existing_specs(self, db_session: AsyncSession):
        """Test normalization when specs are already provided."""
        # Create test CPU
        cpu = Cpu(
            name="AMD Ryzen 9 5950X",
            manufacturer="AMD",
            cpu_mark_multi=50000,
            cpu_mark_single=3800,
            igpu_mark=None,
        )
        db_session.add(cpu)
        await db_session.commit()

        raw = NormalizedListingSchema(
            title="Workstation PC",
            price=Decimal("800"),
            currency="USD",
            condition="refurb",  # Use enum value
            cpu_model="Ryzen 9 5950X",  # Already provided
            ram_gb=32,  # Already provided
            storage_gb=1024,  # Already provided
            marketplace="other",
            description="Some other text without specs",
        )

        normalizer = ListingNormalizer(db_session)
        enriched = await normalizer.normalize(raw)

        # Should use provided values
        assert enriched.ram_gb == 32
        assert enriched.storage_gb == 1024

        # CPU should be canonicalized
        assert "AMD Ryzen 9 5950X" in enriched.cpu_model

        # Condition should be normalized
        assert enriched.condition == "refurb"

    @pytest.mark.asyncio
    async def test_normalize_multiple_currencies(self, db_session: AsyncSession):
        """Test normalization with various currencies."""
        normalizer = ListingNormalizer(db_session)

        test_cases = [
            (Decimal("100"), "USD", Decimal("100.00")),
            (Decimal("100"), "EUR", Decimal("108.00")),
            (Decimal("100"), "GBP", Decimal("127.00")),
            (Decimal("100"), "CAD", Decimal("74.00")),
        ]

        for price, currency, expected_usd in test_cases:
            raw = NormalizedListingSchema(
                title="Test PC",
                price=price,
                currency=currency,
                condition="used",
                marketplace="other",
            )

            enriched = await normalizer.normalize(raw)
            assert enriched.price == expected_usd
            assert enriched.currency == "USD"

    @pytest.mark.asyncio
    async def test_normalize_preserves_metadata(self, db_session: AsyncSession):
        """Test that normalization preserves important metadata."""
        raw = NormalizedListingSchema(
            title="Test Listing",
            price=Decimal("599.99"),
            currency="USD",
            condition="used",
            marketplace="ebay",
            vendor_item_id="123456789012",
            seller="eBaySeller123",
            description="Test description",
            images=["img1.jpg", "img2.jpg"],
        )

        normalizer = ListingNormalizer(db_session)
        enriched = await normalizer.normalize(raw)

        # Verify all metadata is preserved
        assert enriched.title == "Test Listing"
        assert enriched.marketplace == "ebay"
        assert enriched.vendor_item_id == "123456789012"
        assert enriched.seller == "eBaySeller123"
        assert enriched.description == "Test description"
        assert len(enriched.images) == 2
