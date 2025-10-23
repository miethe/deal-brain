"""
Integration tests for FormulaValidationService.

Tests formula validation, field availability checking, and preview calculations.
"""

import pytest
import pytest_asyncio
import time
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from dealbrain_api.models.core import Listing, Cpu, Gpu, CustomFieldDefinition
from dealbrain_api.services.formula_validation import FormulaValidationService
from dealbrain_api.db import Base

# Try to import aiosqlite
try:
    import aiosqlite
    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide an isolated in-memory database session for tests"""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping formula validation tests")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest_asyncio.fixture
async def validation_service():
    """Create FormulaValidationService instance"""
    return FormulaValidationService()


@pytest_asyncio.fixture
async def sample_cpu(db_session: AsyncSession) -> Cpu:
    """Create a sample CPU for testing"""
    cpu = Cpu(
        name="Intel Core i7-12700K",
        manufacturer="Intel",
        cores=12,
        threads=20,
        tdp_w=125,
        cpu_mark_multi=35228,
        cpu_mark_single=4116,
        igpu_mark=2500,
        release_year=2021,
    )
    db_session.add(cpu)
    await db_session.commit()
    await db_session.refresh(cpu)
    return cpu


@pytest_asyncio.fixture
async def sample_gpu(db_session: AsyncSession) -> Gpu:
    """Create a sample GPU for testing"""
    gpu = Gpu(
        name="NVIDIA RTX 3060",
        manufacturer="NVIDIA",
        gpu_mark=15000,
    )
    db_session.add(gpu)
    await db_session.commit()
    await db_session.refresh(gpu)
    return gpu


@pytest_asyncio.fixture
async def sample_listing(
    db_session: AsyncSession,
    sample_cpu: Cpu,
    sample_gpu: Gpu
) -> Listing:
    """Create a sample listing for testing"""
    listing = Listing(
        title="Test Gaming PC",
        listing_url="https://example.com/listing/1",
        price_usd=800.00,
        adjusted_price_usd=750.00,
        condition="used",
        manufacturer="Dell",
        series="OptiPlex",
        model_number="7090",
        form_factor="mini",
        cpu_id=sample_cpu.id,
        gpu_id=sample_gpu.id,
        ram_gb=16,
        primary_storage_gb=512,
        status="active",
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)
    return listing


@pytest_asyncio.fixture
async def custom_field(db_session: AsyncSession) -> CustomFieldDefinition:
    """Create a custom field for testing"""
    field = CustomFieldDefinition(
        entity="listing",
        key="custom_discount_pct",
        label="Custom Discount %",
        data_type="number",
        description="Custom discount percentage",
        is_active=True,
        display_order=100,
    )
    db_session.add(field)
    await db_session.commit()
    await db_session.refresh(field)
    return field


# --- Valid Formula Tests ---

@pytest.mark.asyncio
async def test_validate_simple_formula(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
    sample_listing: Listing,
):
    """Test validation of simple formula"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="ram_gb * 2.5",
        entity_type="Listing",
    )

    assert result["valid"] is True
    assert len(result["errors"]) == 0
    assert result["preview"] is not None
    assert result["preview"] == 40.0  # 16 * 2.5
    assert "ram_gb" in result["used_fields"]


@pytest.mark.asyncio
async def test_validate_complex_formula(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
    sample_listing: Listing,
):
    """Test validation of complex formula with multiple operations"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="ram_gb * 2.5 + cpu_mark_multi / 1000 * 5.0",
        entity_type="Listing",
    )

    assert result["valid"] is True
    assert len(result["errors"]) == 0
    assert result["preview"] is not None
    # 16 * 2.5 + 35228 / 1000 * 5.0 = 40.0 + 176.14
    assert result["preview"] > 200.0
    assert "ram_gb" in result["used_fields"]
    assert "cpu_mark_multi" in result["used_fields"]


@pytest.mark.asyncio
async def test_validate_formula_with_functions(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
    sample_listing: Listing,
):
    """Test validation of formula with allowed functions"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="max(ram_gb * 2.5, 50)",
        entity_type="Listing",
    )

    assert result["valid"] is True
    assert len(result["errors"]) == 0
    assert result["preview"] == 50.0  # max(40, 50) = 50
    assert "ram_gb" in result["used_fields"]


@pytest.mark.asyncio
async def test_validate_formula_with_conditional(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
    sample_listing: Listing,
):
    """Test validation of formula with ternary conditional"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0",
        entity_type="Listing",
    )

    assert result["valid"] is True
    assert len(result["errors"]) == 0
    assert result["preview"] == 40.0  # 16 >= 16, so 16 * 2.5
    assert "ram_gb" in result["used_fields"]


# --- Invalid Formula Tests ---

@pytest.mark.asyncio
async def test_validate_empty_formula(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test validation of empty formula"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="",
        entity_type="Listing",
    )

    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert result["errors"][0]["severity"] == "error"
    assert "empty" in result["errors"][0]["message"].lower()


@pytest.mark.asyncio
async def test_validate_formula_syntax_error(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test validation of formula with syntax error"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="ram_gb * 2.5 +",  # Incomplete expression
        entity_type="Listing",
    )

    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert result["errors"][0]["severity"] == "error"
    assert result["errors"][0]["suggestion"] is not None


@pytest.mark.asyncio
async def test_validate_formula_unmatched_parentheses(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test validation of formula with unmatched parentheses"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="max(ram_gb * 2.5",  # Missing closing parenthesis
        entity_type="Listing",
    )

    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert result["errors"][0]["severity"] == "error"
    assert "parenthesis" in result["errors"][0]["suggestion"].lower()


@pytest.mark.asyncio
async def test_validate_formula_undefined_field(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test validation of formula with undefined field"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="nonexistent_field * 2.5",
        entity_type="Listing",
    )

    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert "not available" in result["errors"][0]["message"].lower()


@pytest.mark.asyncio
async def test_validate_formula_disallowed_function(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test validation of formula with disallowed function"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="eval('ram_gb * 2.5')",  # eval is not allowed
        entity_type="Listing",
    )

    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert result["errors"][0]["severity"] == "error"


# --- Field Availability Tests ---

@pytest.mark.asyncio
async def test_get_available_fields_listing(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
    custom_field: CustomFieldDefinition,
):
    """Test getting available fields for Listing entity"""
    fields = await validation_service.get_available_fields(
        session=db_session,
        entity_type="Listing",
    )

    # Check standard fields
    assert "price_usd" in fields
    assert "ram_gb" in fields
    assert "cpu_mark_multi" in fields
    assert "condition" in fields

    # Check custom field
    assert "custom_discount_pct" in fields

    # Check nested CPU fields
    assert "cpu.cores" in fields
    assert "cpu.cpu_mark_multi" in fields


@pytest.mark.asyncio
async def test_get_available_fields_cpu(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test getting available fields for CPU entity"""
    fields = await validation_service.get_available_fields(
        session=db_session,
        entity_type="CPU",
    )

    assert "model" in fields
    assert "cores" in fields
    assert "threads" in fields
    assert "cpu_mark_multi" in fields
    assert "tdp_watts" in fields


@pytest.mark.asyncio
async def test_get_available_fields_gpu(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test getting available fields for GPU entity"""
    fields = await validation_service.get_available_fields(
        session=db_session,
        entity_type="GPU",
    )

    assert "model" in fields
    assert "vram_gb" in fields
    assert "tdp_watts" in fields


# --- Sample Context Tests ---

@pytest.mark.asyncio
async def test_get_sample_context_from_database(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
    sample_listing: Listing,
):
    """Test getting sample context from database"""
    context = await validation_service.get_sample_context(
        session=db_session,
        entity_type="Listing",
    )

    assert context["ram_gb"] == 16.0
    assert context["price_usd"] == 800.0
    assert context["cpu_mark_multi"] == 35228.0
    assert context["condition"] == "used"


@pytest.mark.asyncio
async def test_get_sample_context_with_provided_values(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test getting sample context with user-provided values"""
    provided = {
        "ram_gb": 32.0,
        "storage_gb": 1024.0,
    }

    context = await validation_service.get_sample_context(
        session=db_session,
        entity_type="Listing",
        provided_context=provided,
    )

    # Provided values should override defaults
    assert context["ram_gb"] == 32.0
    assert context["storage_gb"] == 1024.0


@pytest.mark.asyncio
async def test_get_sample_context_default_values(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test getting sample context with default values when no data exists"""
    context = await validation_service.get_sample_context(
        session=db_session,
        entity_type="Listing",
    )

    # Should have some default values
    assert "ram_gb" in context
    assert "cpu_mark_multi" in context
    assert context["ram_gb"] > 0


# --- Preview Calculation Tests ---

@pytest.mark.asyncio
async def test_preview_with_custom_context(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test preview calculation with custom context"""
    custom_context = {
        "ram_gb": 64.0,
        "cpu_mark_multi": 50000.0,
    }

    result = await validation_service.validate_formula(
        session=db_session,
        formula="ram_gb * 2.5 + cpu_mark_multi / 1000",
        entity_type="Listing",
        sample_context=custom_context,
    )

    assert result["valid"] is True
    assert result["preview"] is not None
    # 64 * 2.5 + 50000 / 1000 = 160 + 50 = 210
    assert result["preview"] == 210.0


@pytest.mark.asyncio
async def test_preview_with_nested_fields(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
    sample_listing: Listing,
):
    """Test preview calculation with nested CPU fields"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="cpu.cores * 10 + cpu.threads * 5",
        entity_type="Listing",
    )

    assert result["valid"] is True
    assert result["preview"] is not None
    # 12 * 10 + 20 * 5 = 120 + 100 = 220
    assert result["preview"] == 220.0


# --- Warning Tests ---

@pytest.mark.asyncio
async def test_validation_warnings_division(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test that division operations produce warnings"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="ram_gb / 2",
        entity_type="Listing",
    )

    # Formula should be valid but have warnings
    assert result["valid"] is True
    warnings = [e for e in result["errors"] if e["severity"] == "warning"]
    assert len(warnings) > 0
    assert "division" in warnings[0]["message"].lower()


@pytest.mark.asyncio
async def test_validation_warnings_deep_nesting(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test that deeply nested formulas produce warnings"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="((((((ram_gb * 2) + 1) * 3) + 2) * 4) + 3)",
        entity_type="Listing",
    )

    # Formula should be valid but have warnings
    assert result["valid"] is True
    warnings = [e for e in result["errors"] if e["severity"] == "warning"]
    assert len(warnings) > 0


# --- Performance Tests ---

@pytest.mark.asyncio
async def test_validation_performance(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
    sample_listing: Listing,
):
    """Test that validation completes within performance target (<200ms)"""
    formula = "ram_gb * 2.5 + score_cpu_multi / 1000 * 5.0"

    start_time = time.time()
    result = await validation_service.validate_formula(
        session=db_session,
        formula=formula,
        entity_type="Listing",
    )
    elapsed_ms = (time.time() - start_time) * 1000

    assert result["valid"] is True
    assert elapsed_ms < 200, f"Validation took {elapsed_ms:.2f}ms, expected <200ms"


# --- Security Tests ---

@pytest.mark.asyncio
async def test_security_injection_attempt(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test that injection attempts are blocked"""
    dangerous_formulas = [
        "__import__('os').system('ls')",
        "exec('print(1)')",
        "eval('1+1')",
        "open('/etc/passwd').read()",
    ]

    for formula in dangerous_formulas:
        result = await validation_service.validate_formula(
            session=db_session,
            formula=formula,
            entity_type="Listing",
        )

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert result["errors"][0]["severity"] == "error"


# --- Edge Cases ---

@pytest.mark.asyncio
async def test_validate_formula_with_zero_division_risk(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test formula with potential zero division"""
    result = await validation_service.validate_formula(
        session=db_session,
        formula="100 / ram_gb",
        entity_type="Listing",
    )

    # Should be valid but have warning about division
    assert result["valid"] is True
    warnings = [e for e in result["errors"] if e["severity"] == "warning"]
    assert len(warnings) > 0


@pytest.mark.asyncio
async def test_validate_formula_case_insensitive_entity(
    validation_service: FormulaValidationService,
    db_session: AsyncSession,
):
    """Test that entity type is case-insensitive"""
    result1 = await validation_service.validate_formula(
        session=db_session,
        formula="ram_gb * 2.5",
        entity_type="Listing",
    )

    result2 = await validation_service.validate_formula(
        session=db_session,
        formula="ram_gb * 2.5",
        entity_type="listing",
    )

    assert result1["valid"] is True
    assert result2["valid"] is True
    assert result1["available_fields"] == result2["available_fields"]
