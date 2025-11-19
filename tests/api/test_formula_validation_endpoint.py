"""
API endpoint tests for formula validation.

Tests the /api/v1/valuation-rules/validate-formula endpoint.
"""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models.core import Listing, Cpu, CustomFieldDefinition


@pytest.fixture
async def sample_cpu(db_session: AsyncSession) -> Cpu:
    """Create a sample CPU for testing"""
    cpu = Cpu(
        model="Intel Core i7-12700K",
        manufacturer="Intel",
        cores=12,
        threads=20,
        base_clock_ghz=Decimal("3.6"),
        turbo_clock_ghz=Decimal("5.0"),
        tdp_watts=125,
        cpu_mark_multi=Decimal("35228"),
        cpu_mark_single=Decimal("4116"),
        igpu_mark=Decimal("2500"),
    )
    db_session.add(cpu)
    await db_session.commit()
    await db_session.refresh(cpu)
    return cpu


@pytest.fixture
async def sample_listing(db_session: AsyncSession, sample_cpu: Cpu) -> Listing:
    """Create a sample listing for testing"""
    listing = Listing(
        title="Test Gaming PC",
        url="https://example.com/listing/1",
        price_usd=Decimal("800.00"),
        base_valuation_usd=Decimal("750.00"),
        adjusted_valuation_usd=Decimal("750.00"),
        condition="used",
        manufacturer="Dell",
        cpu_id=sample_cpu.id,
        ram_gb=Decimal("16.0"),
        storage_gb=Decimal("512.0"),
        cpu_mark_multi=Decimal("35228"),
        cpu_mark_single=Decimal("4116"),
        is_active=True,
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)
    return listing


@pytest.fixture
async def custom_field(db_session: AsyncSession) -> CustomFieldDefinition:
    """Create a custom field for testing"""
    field = CustomFieldDefinition(
        entity="listing",
        key="warranty_months",
        label="Warranty Months",
        data_type="number",
        is_active=True,
    )
    db_session.add(field)
    await db_session.commit()
    await db_session.refresh(field)
    return field


# --- Valid Formula Tests ---


@pytest.mark.asyncio
async def test_api_validate_simple_formula(
    async_client: AsyncClient,
    sample_listing: Listing,
):
    """Test API validation of simple formula"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "ram_gb * 2.5",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert len(data["errors"]) == 0
    assert data["preview"] is not None
    assert data["preview"] == 40.0  # 16 * 2.5
    assert "ram_gb" in data["used_fields"]
    assert "ram_gb" in data["available_fields"]


@pytest.mark.asyncio
async def test_api_validate_complex_formula(
    async_client: AsyncClient,
    sample_listing: Listing,
):
    """Test API validation of complex formula"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "ram_gb * 2.5 + cpu_mark_multi / 1000 * 5.0",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert data["preview"] is not None
    assert data["preview"] > 200.0
    assert "ram_gb" in data["used_fields"]
    assert "cpu_mark_multi" in data["used_fields"]


@pytest.mark.asyncio
async def test_api_validate_formula_with_functions(
    async_client: AsyncClient,
    sample_listing: Listing,
):
    """Test API validation with allowed functions"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "max(ram_gb * 2.5, 50)",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert data["preview"] == 50.0


@pytest.mark.asyncio
async def test_api_validate_formula_with_conditional(
    async_client: AsyncClient,
    sample_listing: Listing,
):
    """Test API validation with ternary conditional"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert data["preview"] == 40.0


@pytest.mark.asyncio
async def test_api_validate_formula_with_custom_context(
    async_client: AsyncClient,
):
    """Test API validation with custom context"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "ram_gb * 2.5 + storage_gb / 100",
            "entity_type": "Listing",
            "sample_context": {
                "ram_gb": 32.0,
                "storage_gb": 1000.0,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert data["preview"] is not None
    # 32 * 2.5 + 1000 / 100 = 80 + 10 = 90
    assert data["preview"] == 90.0


# --- Invalid Formula Tests ---


@pytest.mark.asyncio
async def test_api_validate_empty_formula(async_client: AsyncClient):
    """Test API validation of empty formula"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "",
            "entity_type": "Listing",
        },
    )

    # Empty formula should fail Pydantic validation
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_validate_syntax_error(async_client: AsyncClient):
    """Test API validation with syntax error"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "ram_gb * 2.5 +",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is False
    assert len(data["errors"]) > 0
    assert data["errors"][0]["severity"] == "error"
    assert data["errors"][0]["suggestion"] is not None


@pytest.mark.asyncio
async def test_api_validate_unmatched_parentheses(async_client: AsyncClient):
    """Test API validation with unmatched parentheses"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "max(ram_gb * 2.5",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is False
    assert len(data["errors"]) > 0
    assert "parenthesis" in data["errors"][0]["suggestion"].lower()


@pytest.mark.asyncio
async def test_api_validate_undefined_field(async_client: AsyncClient):
    """Test API validation with undefined field"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "nonexistent_field * 2.5",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is False
    assert len(data["errors"]) > 0
    assert "not available" in data["errors"][0]["message"].lower()


@pytest.mark.asyncio
async def test_api_validate_disallowed_function(async_client: AsyncClient):
    """Test API validation with disallowed function"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "eval('ram_gb * 2.5')",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is False
    assert len(data["errors"]) > 0


# --- Entity Type Tests ---


@pytest.mark.asyncio
async def test_api_validate_cpu_formula(async_client: AsyncClient, sample_cpu: Cpu):
    """Test API validation for CPU entity type"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "cores * 10 + threads * 5",
            "entity_type": "CPU",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert "cores" in data["used_fields"]
    assert "threads" in data["used_fields"]
    assert "cores" in data["available_fields"]


@pytest.mark.asyncio
async def test_api_validate_gpu_formula(async_client: AsyncClient):
    """Test API validation for GPU entity type"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "vram_gb * 25",
            "entity_type": "GPU",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert "vram_gb" in data["used_fields"]
    assert "vram_gb" in data["available_fields"]


# --- Custom Field Tests ---


@pytest.mark.asyncio
async def test_api_validate_with_custom_field(
    async_client: AsyncClient,
    custom_field: CustomFieldDefinition,
):
    """Test API validation with custom field"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "warranty_months * 5",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert "warranty_months" in data["used_fields"]
    assert "warranty_months" in data["available_fields"]


# --- Warning Tests ---


@pytest.mark.asyncio
async def test_api_validation_warnings(async_client: AsyncClient):
    """Test that warnings are returned for risky operations"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "100 / ram_gb",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Should be valid but have warnings
    assert data["valid"] is True
    warnings = [e for e in data["errors"] if e["severity"] == "warning"]
    assert len(warnings) > 0
    assert "division" in warnings[0]["message"].lower()


# --- Security Tests ---


@pytest.mark.asyncio
async def test_api_security_injection_attempts(async_client: AsyncClient):
    """Test that security injection attempts are blocked"""
    dangerous_formulas = [
        "__import__('os').system('ls')",
        "exec('print(1)')",
        "eval('1+1')",
    ]

    for formula in dangerous_formulas:
        response = await async_client.post(
            "/api/v1/valuation-rules/validate-formula",
            json={
                "formula": formula,
                "entity_type": "Listing",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0


# --- Error Handling Tests ---


@pytest.mark.asyncio
async def test_api_missing_required_fields(async_client: AsyncClient):
    """Test API validation with missing required fields"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            # Missing formula
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_api_default_entity_type(async_client: AsyncClient, sample_listing: Listing):
    """Test that entity_type defaults to Listing"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "ram_gb * 2.5",
            # entity_type omitted, should default to "Listing"
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert "ram_gb" in data["available_fields"]


# --- Response Structure Tests ---


@pytest.mark.asyncio
async def test_api_response_structure(async_client: AsyncClient, sample_listing: Listing):
    """Test that API response has correct structure"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "ram_gb * 2.5",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Check all required fields are present
    assert "valid" in data
    assert "errors" in data
    assert "preview" in data
    assert "used_fields" in data
    assert "available_fields" in data

    # Check types
    assert isinstance(data["valid"], bool)
    assert isinstance(data["errors"], list)
    assert isinstance(data["used_fields"], list)
    assert isinstance(data["available_fields"], list)


@pytest.mark.asyncio
async def test_api_error_structure(async_client: AsyncClient):
    """Test that error objects have correct structure"""
    response = await async_client.post(
        "/api/v1/valuation-rules/validate-formula",
        json={
            "formula": "ram_gb * 2.5 +",
            "entity_type": "Listing",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["errors"]) > 0
    error = data["errors"][0]

    # Check error structure
    assert "message" in error
    assert "severity" in error
    assert "position" in error
    assert "suggestion" in error

    # Check types
    assert isinstance(error["message"], str)
    assert isinstance(error["severity"], str)
    assert error["severity"] in ["error", "warning", "info"]
