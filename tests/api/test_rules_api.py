"""
API endpoint tests for valuation rules.

Tests all REST endpoints for rulesets, rule groups, and rules.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models.core import ValuationRulesetV2, ValuationRuleGroupV2, ValuationRuleV2


@pytest.fixture
async def sample_ruleset_data():
    """Sample ruleset data for testing."""
    return {
        "name": "Test Gaming Ruleset",
        "version": "1.0.0",
        "description": "Test ruleset for gaming PCs",
        "is_active": True,
        "metadata": {"author": "Test Suite", "tags": ["gaming", "test"]},
    }


@pytest.fixture
async def sample_rule_group_data():
    """Sample rule group data for testing."""
    return {
        "name": "CPU Valuation",
        "category": "cpu",
        "description": "CPU-based valuation rules",
        "weight": 0.30,
        "display_order": 1,
    }


@pytest.fixture
async def sample_rule_data():
    """Sample rule data for testing."""
    return {
        "name": "High-End CPU Premium",
        "description": "Premium for high-end CPUs",
        "category": "cpu",
        "evaluation_order": 100,
        "is_active": True,
        "conditions": {
            "field_name": "cpu.cpu_mark_multi",
            "field_type": "integer",
            "operator": "greater_than",
            "value": 30000,
        },
        "actions": [
            {
                "action_type": "fixed_value",
                "value_usd": 100.00,
                "description": "Add $100 for high-end CPU",
            }
        ],
    }


class TestRulesetEndpoints:
    """Test ruleset CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_ruleset(self, client: AsyncClient, sample_ruleset_data: dict):
        """Test POST /api/v1/rulesets - Create ruleset."""
        response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_ruleset_data["name"]
        assert data["version"] == sample_ruleset_data["version"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_ruleset_invalid_data(self, client: AsyncClient):
        """Test POST /api/v1/rulesets - Invalid data returns 422."""
        response = await client.post("/api/v1/rulesets", json={"name": "Missing required fields"})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_rulesets(self, client: AsyncClient, sample_ruleset_data: dict):
        """Test GET /api/v1/rulesets - List all rulesets."""
        # Create a ruleset first
        await client.post("/api/v1/rulesets", json=sample_ruleset_data)

        response = await client.get("/api/v1/rulesets")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_list_rulesets_active_only(self, client: AsyncClient, sample_ruleset_data: dict):
        """Test GET /api/v1/rulesets?active_only=true - Filter active rulesets."""
        # Create active ruleset
        await client.post("/api/v1/rulesets", json=sample_ruleset_data)

        # Create inactive ruleset
        inactive_data = sample_ruleset_data.copy()
        inactive_data["name"] = "Inactive Ruleset"
        inactive_data["is_active"] = False
        await client.post("/api/v1/rulesets", json=inactive_data)

        response = await client.get("/api/v1/rulesets?active_only=true")

        assert response.status_code == 200
        data = response.json()
        assert all(rs["is_active"] for rs in data)

    @pytest.mark.asyncio
    async def test_get_ruleset(self, client: AsyncClient, sample_ruleset_data: dict):
        """Test GET /api/v1/rulesets/{id} - Get single ruleset."""
        # Create ruleset
        create_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = create_response.json()["id"]

        # Get ruleset
        response = await client.get(f"/api/v1/rulesets/{ruleset_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ruleset_id
        assert data["name"] == sample_ruleset_data["name"]

    @pytest.mark.asyncio
    async def test_get_ruleset_not_found(self, client: AsyncClient):
        """Test GET /api/v1/rulesets/{id} - Non-existent ID returns 404."""
        response = await client.get("/api/v1/rulesets/99999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_ruleset(self, client: AsyncClient, sample_ruleset_data: dict):
        """Test PUT /api/v1/rulesets/{id} - Update ruleset."""
        # Create ruleset
        create_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = create_response.json()["id"]

        # Update ruleset
        update_data = {
            "name": "Updated Gaming Ruleset",
            "version": "1.1.0",
            "description": "Updated description",
        }

        response = await client.put(f"/api/v1/rulesets/{ruleset_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["version"] == update_data["version"]

    @pytest.mark.asyncio
    async def test_delete_ruleset(self, client: AsyncClient, sample_ruleset_data: dict):
        """Test DELETE /api/v1/rulesets/{id} - Delete ruleset."""
        # Create ruleset
        create_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = create_response.json()["id"]

        # Delete ruleset
        response = await client.delete(f"/api/v1/rulesets/{ruleset_id}")

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(f"/api/v1/rulesets/{ruleset_id}")
        assert get_response.status_code == 404


class TestRuleGroupEndpoints:
    """Test rule group endpoints."""

    @pytest.mark.asyncio
    async def test_create_rule_group(
        self,
        client: AsyncClient,
        sample_ruleset_data: dict,
        sample_rule_group_data: dict,
    ):
        """Test POST /api/v1/rulesets/{id}/groups - Create rule group."""
        # Create ruleset first
        ruleset_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = ruleset_response.json()["id"]

        # Create group
        response = await client.post(
            f"/api/v1/rulesets/{ruleset_id}/groups", json=sample_rule_group_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_rule_group_data["name"]
        assert data["ruleset_id"] == ruleset_id
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_rule_groups(
        self,
        client: AsyncClient,
        sample_ruleset_data: dict,
        sample_rule_group_data: dict,
    ):
        """Test GET /api/v1/rulesets/{id}/groups - List rule groups."""
        # Create ruleset and group
        ruleset_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = ruleset_response.json()["id"]

        await client.post(f"/api/v1/rulesets/{ruleset_id}/groups", json=sample_rule_group_data)

        # List groups
        response = await client.get(f"/api/v1/rulesets/{ruleset_id}/groups")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_delete_rule_group(
        self,
        client: AsyncClient,
        sample_ruleset_data: dict,
        sample_rule_group_data: dict,
    ):
        """Test DELETE /api/v1/rule-groups/{id} - Delete rule group."""
        # Create ruleset and group
        ruleset_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = ruleset_response.json()["id"]

        group_response = await client.post(
            f"/api/v1/rulesets/{ruleset_id}/groups", json=sample_rule_group_data
        )
        group_id = group_response.json()["id"]

        # Delete group
        response = await client.delete(f"/api/v1/rule-groups/{group_id}")

        assert response.status_code == 204


class TestRuleEndpoints:
    """Test rule endpoints."""

    @pytest.mark.asyncio
    async def test_create_rule(
        self,
        client: AsyncClient,
        sample_ruleset_data: dict,
        sample_rule_group_data: dict,
        sample_rule_data: dict,
    ):
        """Test POST /api/v1/rule-groups/{id}/rules - Create rule."""
        # Create ruleset and group
        ruleset_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = ruleset_response.json()["id"]

        group_response = await client.post(
            f"/api/v1/rulesets/{ruleset_id}/groups", json=sample_rule_group_data
        )
        group_id = group_response.json()["id"]

        # Create rule
        response = await client.post(f"/api/v1/rule-groups/{group_id}/rules", json=sample_rule_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_rule_data["name"]
        assert data["group_id"] == group_id
        assert "id" in data
        assert len(data["conditions"]) > 0
        assert len(data["actions"]) > 0

    @pytest.mark.asyncio
    async def test_list_rules(
        self,
        client: AsyncClient,
        sample_ruleset_data: dict,
        sample_rule_group_data: dict,
        sample_rule_data: dict,
    ):
        """Test GET /api/v1/rule-groups/{id}/rules - List rules."""
        # Create ruleset, group, and rule
        ruleset_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = ruleset_response.json()["id"]

        group_response = await client.post(
            f"/api/v1/rulesets/{ruleset_id}/groups", json=sample_rule_group_data
        )
        group_id = group_response.json()["id"]

        await client.post(f"/api/v1/rule-groups/{group_id}/rules", json=sample_rule_data)

        # List rules
        response = await client.get(f"/api/v1/rule-groups/{group_id}/rules")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_update_rule(
        self,
        client: AsyncClient,
        sample_ruleset_data: dict,
        sample_rule_group_data: dict,
        sample_rule_data: dict,
    ):
        """Test PUT /api/v1/rules/{id} - Update rule."""
        # Create ruleset, group, and rule
        ruleset_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = ruleset_response.json()["id"]

        group_response = await client.post(
            f"/api/v1/rulesets/{ruleset_id}/groups", json=sample_rule_group_data
        )
        group_id = group_response.json()["id"]

        rule_response = await client.post(
            f"/api/v1/rule-groups/{group_id}/rules", json=sample_rule_data
        )
        rule_id = rule_response.json()["id"]

        # Update rule
        update_data = {
            "name": "Updated High-End CPU Premium",
            "description": "Updated description",
            "is_active": False,
        }

        response = await client.put(f"/api/v1/rules/{rule_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["is_active"] == update_data["is_active"]

    @pytest.mark.asyncio
    async def test_delete_rule(
        self,
        client: AsyncClient,
        sample_ruleset_data: dict,
        sample_rule_group_data: dict,
        sample_rule_data: dict,
    ):
        """Test DELETE /api/v1/rules/{id} - Delete rule."""
        # Create ruleset, group, and rule
        ruleset_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = ruleset_response.json()["id"]

        group_response = await client.post(
            f"/api/v1/rulesets/{ruleset_id}/groups", json=sample_rule_group_data
        )
        group_id = group_response.json()["id"]

        rule_response = await client.post(
            f"/api/v1/rule-groups/{group_id}/rules", json=sample_rule_data
        )
        rule_id = rule_response.json()["id"]

        # Delete rule
        response = await client.delete(f"/api/v1/rules/{rule_id}")

        assert response.status_code == 204


class TestPreviewEndpoint:
    """Test rule preview endpoint."""

    @pytest.mark.asyncio
    async def test_preview_rule_impact(
        self,
        client: AsyncClient,
        sample_ruleset_data: dict,
        sample_rule_group_data: dict,
        sample_rule_data: dict,
    ):
        """Test POST /api/v1/rules/{id}/preview - Preview rule impact."""
        # Create ruleset, group, and rule
        ruleset_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = ruleset_response.json()["id"]

        group_response = await client.post(
            f"/api/v1/rulesets/{ruleset_id}/groups", json=sample_rule_group_data
        )
        group_id = group_response.json()["id"]

        rule_response = await client.post(
            f"/api/v1/rule-groups/{group_id}/rules", json=sample_rule_data
        )
        rule_id = rule_response.json()["id"]

        # Preview rule
        response = await client.post(f"/api/v1/rules/{rule_id}/preview")

        assert response.status_code == 200
        data = response.json()
        assert "total_listings_affected" in data
        assert "average_adjustment" in data
        assert "sample_listings" in data


class TestApplyEndpoint:
    """Test ruleset apply endpoint."""

    @pytest.mark.asyncio
    async def test_apply_ruleset(
        self,
        client: AsyncClient,
        sample_ruleset_data: dict,
        sample_rule_group_data: dict,
        sample_rule_data: dict,
    ):
        """Test POST /api/v1/rulesets/{id}/apply - Apply ruleset to listings."""
        # Create ruleset, group, and rule
        ruleset_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = ruleset_response.json()["id"]

        group_response = await client.post(
            f"/api/v1/rulesets/{ruleset_id}/groups", json=sample_rule_group_data
        )
        group_id = group_response.json()["id"]

        await client.post(f"/api/v1/rule-groups/{group_id}/rules", json=sample_rule_data)

        # Apply ruleset
        response = await client.post(f"/api/v1/rulesets/{ruleset_id}/apply")

        assert response.status_code == 200
        data = response.json()
        assert "listings_processed" in data
        assert "total_adjustments" in data


class TestPackageEndpoints:
    """Test package export/import endpoints."""

    @pytest.mark.asyncio
    async def test_export_package(
        self,
        client: AsyncClient,
        sample_ruleset_data: dict,
        sample_rule_group_data: dict,
        sample_rule_data: dict,
    ):
        """Test POST /api/v1/rulesets/{id}/export - Export package."""
        # Create complete ruleset
        ruleset_response = await client.post("/api/v1/rulesets", json=sample_ruleset_data)
        ruleset_id = ruleset_response.json()["id"]

        group_response = await client.post(
            f"/api/v1/rulesets/{ruleset_id}/groups", json=sample_rule_group_data
        )
        group_id = group_response.json()["id"]

        await client.post(f"/api/v1/rule-groups/{group_id}/rules", json=sample_rule_data)

        # Export package
        export_data = {
            "metadata": {
                "name": "test-package",
                "version": "1.0.0",
                "author": "Test",
                "description": "Test package",
            }
        }

        response = await client.post(f"/api/v1/rulesets/{ruleset_id}/export", json=export_data)

        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert "rulesets" in data
        assert "rule_groups" in data
        assert "rules" in data

    @pytest.mark.asyncio
    async def test_install_package(self, client: AsyncClient):
        """Test POST /api/v1/packages/install - Install package."""
        # Create a minimal package
        package_data = {
            "schema_version": "1.0",
            "metadata": {
                "name": "test-install",
                "version": "1.0.0",
                "author": "Test",
                "description": "Test installation",
            },
            "rulesets": [
                {
                    "name": "Imported Ruleset",
                    "version": "1.0.0",
                    "description": "Imported from package",
                    "is_active": True,
                    "metadata": {},
                }
            ],
            "rule_groups": [],
            "rules": [],
            "custom_field_definitions": [],
        }

        response = await client.post("/api/v1/packages/install", json=package_data)

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "rulesets_created" in data


class TestErrorHandling:
    """Test API error handling."""

    @pytest.mark.asyncio
    async def test_invalid_json(self, client: AsyncClient):
        """Test that invalid JSON returns 400."""
        response = await client.post(
            "/api/v1/rulesets",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_required_field(self, client: AsyncClient):
        """Test that missing required fields returns 422."""
        response = await client.post(
            "/api/v1/rulesets", json={"description": "Missing name and version"}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_invalid_id_type(self, client: AsyncClient):
        """Test that invalid ID type returns 422."""
        response = await client.get("/api/v1/rulesets/invalid-id")

        assert response.status_code == 422
