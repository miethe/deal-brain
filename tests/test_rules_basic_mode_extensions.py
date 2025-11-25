"""Tests for Rules API extensions supporting Basic mode metadata"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from dealbrain_api.db import Base, get_engine, get_session_factory
from dealbrain_api.main import app
from dealbrain_api.models.core import ValuationRuleset, ValuationRuleGroup, ValuationRuleV2
from dealbrain_api.validation.rules_validation import VALID_ENTITY_KEYS


# --- Fixtures ---


@pytest.fixture
async def db_session():
    """Create async database session for tests"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with get_session_factory()() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Create async HTTP client for API tests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestRuleGroupBasicModeExtensions:
    """Test rule group extensions for Basic mode support"""

    async def test_create_group_with_basic_managed_metadata(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test creating a rule group with basic_managed and entity_key"""
        # Create a ruleset first
        ruleset_resp = await client.post(
            "/api/v1/rulesets",
            json={
                "name": "Test Ruleset",
                "description": "Test ruleset for basic mode",
            },
        )
        assert ruleset_resp.status_code == 200
        ruleset_id = ruleset_resp.json()["id"]

        # Create a basic-managed group
        group_data = {
            "ruleset_id": ruleset_id,
            "name": "Basic CPU Rules",
            "category": "cpu",
            "description": "CPU rules managed by Basic mode",
            "basic_managed": True,
            "entity_key": "CPU",
        }

        response = await client.post("/api/v1/rule-groups", json=group_data)
        assert response.status_code == 200

        result = response.json()
        assert result["name"] == "Basic CPU Rules"
        assert result["basic_managed"] is True
        assert result["entity_key"] == "CPU"
        assert "basic_managed" in result["metadata"]
        assert result["metadata"]["basic_managed"] is True
        assert result["metadata"]["entity_key"] == "CPU"

    async def test_create_group_requires_entity_key_when_basic_managed(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that basic_managed groups require entity_key"""
        # Create a ruleset first
        ruleset_resp = await client.post(
            "/api/v1/rulesets",
            json={
                "name": "Test Ruleset",
                "description": "Test ruleset",
            },
        )
        assert ruleset_resp.status_code == 200
        ruleset_id = ruleset_resp.json()["id"]

        # Try to create a basic-managed group without entity_key
        group_data = {
            "ruleset_id": ruleset_id,
            "name": "Invalid Group",
            "category": "test",
            "basic_managed": True,
            # Missing entity_key
        }

        response = await client.post("/api/v1/rule-groups", json=group_data)
        assert response.status_code == 422  # Validation error
        assert "entity_key is required" in response.json()["detail"][0]["msg"]

    async def test_invalid_entity_key_rejected(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that invalid entity keys are rejected"""
        # Create a ruleset first
        ruleset_resp = await client.post(
            "/api/v1/rulesets",
            json={
                "name": "Test Ruleset",
                "description": "Test ruleset",
            },
        )
        assert ruleset_resp.status_code == 200
        ruleset_id = ruleset_resp.json()["id"]

        # Try to create a group with invalid entity_key
        group_data = {
            "ruleset_id": ruleset_id,
            "name": "Invalid Entity Group",
            "category": "test",
            "basic_managed": True,
            "entity_key": "InvalidEntity",
        }

        response = await client.post("/api/v1/rule-groups", json=group_data)
        assert response.status_code == 400
        assert "Invalid entity_key" in response.json()["detail"]

    async def test_update_basic_managed_group_forbidden(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that basic-managed groups cannot be manually updated"""
        # Create a ruleset first
        ruleset_resp = await client.post(
            "/api/v1/rulesets",
            json={
                "name": "Test Ruleset",
                "description": "Test ruleset",
            },
        )
        assert ruleset_resp.status_code == 200
        ruleset_id = ruleset_resp.json()["id"]

        # Create a basic-managed group
        group_data = {
            "ruleset_id": ruleset_id,
            "name": "Protected Group",
            "category": "protected",
            "basic_managed": True,
            "entity_key": "Listing",
        }

        group_resp = await client.post("/api/v1/rule-groups", json=group_data)
        assert group_resp.status_code == 200
        group_id = group_resp.json()["id"]

        # Try to update the group
        update_data = {
            "name": "Modified Name",
        }

        response = await client.put(f"/api/v1/rule-groups/{group_id}", json=update_data)
        assert response.status_code == 403
        assert "Cannot update basic-managed rule groups" in response.json()["detail"]

    async def test_list_groups_includes_basic_metadata(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that listing groups includes basic_managed and entity_key"""
        # Create a ruleset
        ruleset_resp = await client.post(
            "/api/v1/rulesets",
            json={
                "name": "Test Ruleset",
                "description": "Test ruleset",
            },
        )
        assert ruleset_resp.status_code == 200
        ruleset_id = ruleset_resp.json()["id"]

        # Create both basic-managed and standard groups
        groups = [
            {
                "ruleset_id": ruleset_id,
                "name": "Basic Group",
                "category": "basic",
                "basic_managed": True,
                "entity_key": "GPU",
            },
            {
                "ruleset_id": ruleset_id,
                "name": "Standard Group",
                "category": "standard",
                # No basic_managed or entity_key
            },
        ]

        for group_data in groups:
            await client.post("/api/v1/rule-groups", json=group_data)

        # List groups
        response = await client.get(f"/api/v1/rule-groups?ruleset_id={ruleset_id}")
        assert response.status_code == 200

        results = response.json()
        assert len(results) == 2

        # Check basic-managed group
        basic_group = next(g for g in results if g["name"] == "Basic Group")
        assert basic_group["basic_managed"] is True
        assert basic_group["entity_key"] == "GPU"

        # Check standard group
        standard_group = next(g for g in results if g["name"] == "Standard Group")
        assert standard_group["basic_managed"] is None
        assert standard_group["entity_key"] is None


@pytest.mark.asyncio
class TestRuleModifiersExtensions:
    """Test rule action modifiers extensions"""

    async def test_create_rule_with_modifiers(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test creating a rule with modifiers_json"""
        # Setup: Create ruleset and group
        ruleset_resp = await client.post(
            "/api/v1/rulesets",
            json={"name": "Test Ruleset"},
        )
        ruleset_id = ruleset_resp.json()["id"]

        group_resp = await client.post(
            "/api/v1/rule-groups",
            json={
                "ruleset_id": ruleset_id,
                "name": "Test Group",
                "category": "test",
            },
        )
        group_id = group_resp.json()["id"]

        # Create rule with modifiers
        rule_data = {
            "group_id": group_id,
            "name": "Rule with Modifiers",
            "description": "Test rule with clamping",
            "conditions": [],
            "actions": [
                {
                    "action_type": "per_unit",
                    "metric": "cpu_mark",
                    "value_usd": 10.0,
                    "modifiers": {
                        "clamp": True,
                        "min_usd": 50.0,
                        "max_usd": 200.0,
                        "explanation": "CPU benchmark adjustment",
                        "formula_notes": "$10 per 1000 CPU Mark points",
                        "unit": "multiplier",
                    },
                }
            ],
        }

        response = await client.post("/api/v1/valuation-rules", json=rule_data)
        assert response.status_code == 200

        result = response.json()
        assert result["actions"][0]["modifiers"]["clamp"] is True
        assert result["actions"][0]["modifiers"]["min_usd"] == 50.0
        assert result["actions"][0]["modifiers"]["max_usd"] == 200.0

    async def test_validate_clamp_requires_min_or_max(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that clamp=true requires min_usd or max_usd"""
        # Setup
        ruleset_resp = await client.post(
            "/api/v1/rulesets",
            json={"name": "Test Ruleset"},
        )
        ruleset_id = ruleset_resp.json()["id"]

        group_resp = await client.post(
            "/api/v1/rule-groups",
            json={
                "ruleset_id": ruleset_id,
                "name": "Test Group",
                "category": "test",
            },
        )
        group_id = group_resp.json()["id"]

        # Try to create rule with clamp but no min/max
        rule_data = {
            "group_id": group_id,
            "name": "Invalid Clamp Rule",
            "conditions": [],
            "actions": [
                {
                    "action_type": "fixed_value",
                    "value_usd": 100.0,
                    "modifiers": {
                        "clamp": True,
                        # Missing min_usd and max_usd
                    },
                }
            ],
        }

        response = await client.post("/api/v1/valuation-rules", json=rule_data)
        assert response.status_code == 400
        assert "at least one of 'min_usd' or 'max_usd'" in response.json()["detail"]

    async def test_validate_min_max_ordering(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that min_usd cannot be greater than max_usd"""
        # Setup
        ruleset_resp = await client.post(
            "/api/v1/rulesets",
            json={"name": "Test Ruleset"},
        )
        ruleset_id = ruleset_resp.json()["id"]

        group_resp = await client.post(
            "/api/v1/rule-groups",
            json={
                "ruleset_id": ruleset_id,
                "name": "Test Group",
                "category": "test",
            },
        )
        group_id = group_resp.json()["id"]

        # Try to create rule with invalid min/max
        rule_data = {
            "group_id": group_id,
            "name": "Invalid Min/Max Rule",
            "conditions": [],
            "actions": [
                {
                    "action_type": "fixed_value",
                    "value_usd": 100.0,
                    "modifiers": {
                        "clamp": True,
                        "min_usd": 200.0,  # Greater than max
                        "max_usd": 100.0,
                    },
                }
            ],
        }

        response = await client.post("/api/v1/valuation-rules", json=rule_data)
        assert response.status_code == 400
        assert (
            "'min_usd' (200.0) cannot be greater than 'max_usd' (100.0)"
            in response.json()["detail"]
        )

    async def test_cannot_modify_rules_in_basic_managed_group(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that rules in basic-managed groups cannot be manually modified"""
        # Setup: Create a basic-managed group
        ruleset_resp = await client.post(
            "/api/v1/rulesets",
            json={"name": "Test Ruleset"},
        )
        ruleset_id = ruleset_resp.json()["id"]

        group_resp = await client.post(
            "/api/v1/rule-groups",
            json={
                "ruleset_id": ruleset_id,
                "name": "Basic Group",
                "category": "basic",
                "basic_managed": True,
                "entity_key": "RamSpec",
            },
        )
        group_id = group_resp.json()["id"]

        # Create a rule in the basic-managed group (this simulates what the Basic UI would do)
        rule_data = {
            "group_id": group_id,
            "name": "Basic Rule",
            "conditions": [],
            "actions": [
                {
                    "action_type": "fixed_value",
                    "value_usd": 100.0,
                }
            ],
        }

        rule_resp = await client.post("/api/v1/valuation-rules", json=rule_data)
        assert rule_resp.status_code == 200
        rule_id = rule_resp.json()["id"]

        # Try to update the rule
        update_data = {
            "name": "Modified Rule",
        }

        response = await client.put(f"/api/v1/valuation-rules/{rule_id}", json=update_data)
        assert response.status_code == 403
        assert "Cannot update rule in basic-managed rule groups" in response.json()["detail"]

        # Try to delete the rule
        response = await client.delete(f"/api/v1/valuation-rules/{rule_id}")
        assert response.status_code == 403
        assert "Cannot delete rule from basic-managed rule groups" in response.json()["detail"]


@pytest.mark.asyncio
class TestEntityKeyValidation:
    """Test entity key validation"""

    async def test_all_valid_entity_keys(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that all valid entity keys are accepted"""
        # Create a ruleset
        ruleset_resp = await client.post(
            "/api/v1/rulesets",
            json={"name": "Test Ruleset"},
        )
        ruleset_id = ruleset_resp.json()["id"]

        # Test each valid entity key
        for idx, entity_key in enumerate(VALID_ENTITY_KEYS):
            group_data = {
                "ruleset_id": ruleset_id,
                "name": f"Group for {entity_key}",
                "category": f"cat_{idx}",
                "basic_managed": True,
                "entity_key": entity_key,
            }

            response = await client.post("/api/v1/rule-groups", json=group_data)
            assert response.status_code == 200
            assert response.json()["entity_key"] == entity_key


@pytest.mark.asyncio
class TestRulesetWithBasicManagedGroups:
    """Test ruleset endpoints with basic-managed groups"""

    async def test_get_ruleset_includes_basic_metadata(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that getting a ruleset includes basic_managed and entity_key for groups"""
        # Create ruleset
        ruleset_resp = await client.post(
            "/api/v1/rulesets",
            json={"name": "Test Ruleset with Basic Groups"},
        )
        ruleset_id = ruleset_resp.json()["id"]

        # Create a basic-managed group
        group_resp = await client.post(
            "/api/v1/rule-groups",
            json={
                "ruleset_id": ruleset_id,
                "name": "Basic Storage Rules",
                "category": "storage",
                "basic_managed": True,
                "entity_key": "StorageProfile",
            },
        )
        group_id = group_resp.json()["id"]

        # Create a rule in the group
        await client.post(
            "/api/v1/valuation-rules",
            json={
                "group_id": group_id,
                "name": "Storage Rule",
                "conditions": [],
                "actions": [
                    {
                        "action_type": "per_unit",
                        "metric": "storage_gb",
                        "value_usd": 0.5,
                        "modifiers": {
                            "clamp": True,
                            "min_usd": 10.0,
                            "unit": "usd",
                        },
                    }
                ],
            },
        )

        # Get the full ruleset
        response = await client.get(f"/api/v1/rulesets/{ruleset_id}")
        assert response.status_code == 200

        result = response.json()
        assert len(result["rule_groups"]) == 1

        group = result["rule_groups"][0]
        assert group["basic_managed"] is True
        assert group["entity_key"] == "StorageProfile"
        assert len(group["rules"]) == 1
        assert group["rules"][0]["actions"][0]["modifiers"]["clamp"] is True
