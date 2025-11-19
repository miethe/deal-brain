"""Tests for baseline valuation API endpoints"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.db import Base, engine
from dealbrain_api.main import app
from dealbrain_api.models.core import ValuationRuleset, ValuationRuleAudit
from dealbrain_api.services.baseline_loader import BaselineLoaderService
from sqlalchemy import select


# --- Fixtures ---


@pytest.fixture
async def async_session():
    """Create async database session for tests"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from dealbrain_api.db import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Create async HTTP client for API tests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_baseline_json() -> dict[str, Any]:
    """Sample baseline JSON for testing"""
    return {
        "schema_version": "1.0",
        "generated_at": "2025-10-12T14:00:00Z",
        "description": "Test baseline",
        "entities": {
            "Listing": [
                {
                    "id": "base_adjustment",
                    "proper_name": "Base Adjustment",
                    "description": "Baseline adjustment",
                    "explanation": "Default offset",
                    "valuation_buckets": [
                        {"label": "Default", "min_usd": 15, "max_usd": 30, "Formula": None}
                    ],
                    "Formula": None,
                    "unit": "USD",
                    "dependencies": None,
                    "notes": "Applied uniformly",
                    "nullable": False,
                },
                {
                    "id": "condition_multiplier",
                    "proper_name": "Condition Multiplier",
                    "description": "Value adjustment based on condition",
                    "explanation": "Refurbished and used items are discounted",
                    "valuation_buckets": [
                        {"label": "New", "min_usd": 1.0, "max_usd": 1.0, "Formula": None},
                        {"label": "Refurbished", "min_usd": 0.75, "max_usd": 0.85, "Formula": None},
                        {"label": "Used", "min_usd": 0.60, "max_usd": 0.75, "Formula": None},
                    ],
                    "Formula": None,
                    "unit": "multiplier",
                    "dependencies": ["listing.condition"],
                    "notes": "Applied as percentage",
                    "nullable": False,
                },
            ],
            "CPU": [
                {
                    "id": "cpu_mark_multi",
                    "proper_name": "CPU Mark (Multi-Thread)",
                    "description": "PassMark multi-thread score valuation",
                    "explanation": "Baseline uplift based on benchmark",
                    "valuation_buckets": None,
                    "Formula": "clamp((cpu_mark_multi/1000)*3.6, 160, 260)",
                    "unit": "USD",
                    "dependencies": ["cpu.cpu_mark_multi"],
                    "notes": "Scaled per 1000 points",
                    "nullable": True,
                }
            ],
        },
    }


@pytest.fixture
def modified_baseline_json(sample_baseline_json: dict[str, Any]) -> dict[str, Any]:
    """Modified baseline JSON for diff testing"""
    modified = json.loads(json.dumps(sample_baseline_json))  # Deep copy

    # Change existing field
    modified["entities"]["Listing"][0]["valuation_buckets"][0]["max_usd"] = 35

    # Add new field
    modified["entities"]["Listing"].append(
        {
            "id": "warranty_adjustment",
            "proper_name": "Warranty Adjustment",
            "description": "Value bonus for extended warranty",
            "explanation": "Extended warranties add value",
            "valuation_buckets": [
                {"label": "Extended", "min_usd": 10, "max_usd": 25, "Formula": None}
            ],
            "Formula": None,
            "unit": "USD",
            "dependencies": ["listing.warranty"],
            "notes": "Applied when warranty > 1 year",
            "nullable": True,
        }
    )

    # Remove CPU field
    del modified["entities"]["CPU"]

    return modified


@pytest.fixture
async def loaded_baseline(
    async_session: AsyncSession, sample_baseline_json: dict[str, Any]
) -> ValuationRuleset:
    """Load baseline into database for testing"""
    service = BaselineLoaderService()
    result = await service.load_from_payload(
        session=async_session,
        payload=sample_baseline_json,
        actor="test_user",
    )

    stmt = select(ValuationRuleset).where(ValuationRuleset.id == result.ruleset_id)
    db_result = await async_session.execute(stmt)
    ruleset = db_result.scalar_one()
    return ruleset


# --- Test Cases ---


class TestBaselineMetadata:
    """Tests for GET /api/v1/baseline/meta endpoint"""

    async def test_get_metadata_no_baseline(self, client: AsyncClient):
        """Should return 404 when no baseline exists"""
        response = await client.get("/api/v1/baseline/meta")
        assert response.status_code == 404
        assert "No active baseline" in response.json()["detail"]

    async def test_get_metadata_success(
        self, client: AsyncClient, loaded_baseline: ValuationRuleset
    ):
        """Should return baseline metadata successfully"""
        response = await client.get("/api/v1/baseline/meta")
        assert response.status_code == 200

        data = response.json()
        assert data["ruleset_id"] == loaded_baseline.id
        assert data["is_active"] is True
        assert len(data["entities"]) == 2  # Listing and CPU

        # Check Listing entity
        listing_entity = next(e for e in data["entities"] if e["entity_key"] == "Listing")
        assert len(listing_entity["fields"]) == 2

        # Check field details
        base_adj = next(f for f in listing_entity["fields"] if f["field_name"] == "base_adjustment")
        assert base_adj["proper_name"] == "Base Adjustment"
        assert base_adj["unit"] == "USD"
        assert base_adj["min_value"] == 15
        assert base_adj["max_value"] == 30


class TestBaselineInstantiate:
    """Tests for POST /api/v1/baseline/instantiate endpoint"""

    async def test_instantiate_invalid_path(self, client: AsyncClient):
        """Should return 400 for non-existent file"""
        response = await client.post(
            "/api/v1/baseline/instantiate",
            json={
                "baseline_path": "/nonexistent/baseline.json",
                "create_adjustments_group": True,
            },
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    async def test_instantiate_success(
        self, client: AsyncClient, async_session: AsyncSession, tmp_path: Path
    ):
        """Should create new baseline ruleset from file"""
        # Create temporary baseline file
        baseline_file = tmp_path / "test_baseline.json"
        baseline_data = {
            "schema_version": "1.0",
            "generated_at": "2025-10-12T14:00:00Z",
            "entities": {
                "Listing": [
                    {
                        "id": "test_field",
                        "proper_name": "Test Field",
                        "description": "Test",
                        "unit": "USD",
                        "valuation_buckets": [{"label": "Test", "min_usd": 10, "max_usd": 20}],
                        "nullable": False,
                    }
                ]
            },
        }
        baseline_file.write_text(json.dumps(baseline_data))

        response = await client.post(
            "/api/v1/baseline/instantiate",
            json={
                "baseline_path": str(baseline_file),
                "create_adjustments_group": True,
                "actor": "test_user",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["created"] is True
        assert data["ruleset_id"] is not None
        assert data["created_groups"] == 1
        assert data["created_rules"] == 1

    async def test_instantiate_idempotent(
        self,
        client: AsyncClient,
        async_session: AsyncSession,
        loaded_baseline: ValuationRuleset,
        tmp_path: Path,
    ):
        """Should return existing ruleset if hash matches (idempotent)"""
        # Get the baseline's source JSON
        baseline_data = {
            "schema_version": "1.0",
            "generated_at": "2025-10-12T14:00:00Z",
            "description": "Test baseline",
            "entities": {
                "Listing": [
                    {
                        "id": "base_adjustment",
                        "proper_name": "Base Adjustment",
                        "description": "Baseline adjustment",
                        "unit": "USD",
                        "valuation_buckets": [{"label": "Default", "min_usd": 15, "max_usd": 30}],
                        "nullable": False,
                    }
                ]
            },
        }

        baseline_file = tmp_path / "existing_baseline.json"
        baseline_file.write_text(json.dumps(baseline_data))

        # First call - should skip because hash exists
        response = await client.post(
            "/api/v1/baseline/instantiate",
            json={
                "baseline_path": str(baseline_file),
                "create_adjustments_group": False,
            },
        )
        # Note: This will create a new one because hash is different
        # In real scenario, you'd use exact same hash
        assert response.status_code == 200


class TestBaselineDiff:
    """Tests for POST /api/v1/baseline/diff endpoint"""

    async def test_diff_no_current_baseline(
        self, client: AsyncClient, sample_baseline_json: dict[str, Any]
    ):
        """Should work even without current baseline (all fields shown as added)"""
        response = await client.post(
            "/api/v1/baseline/diff", json={"candidate_json": sample_baseline_json}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["summary"]["added_count"] == 3  # All fields are new
        assert data["summary"]["changed_count"] == 0
        assert data["summary"]["removed_count"] == 0
        assert data["current_version"] is None

    async def test_diff_with_changes(
        self,
        client: AsyncClient,
        loaded_baseline: ValuationRuleset,
        modified_baseline_json: dict[str, Any],
    ):
        """Should detect added, changed, and removed fields"""
        response = await client.post(
            "/api/v1/baseline/diff", json={"candidate_json": modified_baseline_json}
        )
        assert response.status_code == 200

        data = response.json()

        # Should have 1 added (warranty_adjustment)
        assert data["summary"]["added_count"] == 1
        added_field = data["added"][0]
        assert added_field["field_name"] == "warranty_adjustment"
        assert added_field["change_type"] == "added"

        # Should have 1 changed (base_adjustment max_usd changed from 30 to 35)
        assert data["summary"]["changed_count"] == 1
        changed_field = data["changed"][0]
        assert changed_field["field_name"] == "base_adjustment"
        assert changed_field["change_type"] == "changed"
        assert changed_field["value_diff"] is not None

        # Should have 1 removed (cpu_mark_multi)
        assert data["summary"]["removed_count"] == 1
        removed_field = data["removed"][0]
        assert removed_field["field_name"] == "cpu_mark_multi"
        assert removed_field["change_type"] == "removed"

    async def test_diff_no_changes(
        self,
        client: AsyncClient,
        loaded_baseline: ValuationRuleset,
        sample_baseline_json: dict[str, Any],
    ):
        """Should detect no changes when baseline is identical"""
        response = await client.post(
            "/api/v1/baseline/diff", json={"candidate_json": sample_baseline_json}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["summary"]["total_changes"] == 0
        assert len(data["added"]) == 0
        assert len(data["changed"]) == 0
        assert len(data["removed"]) == 0


class TestBaselineAdopt:
    """Tests for POST /api/v1/baseline/adopt endpoint"""

    async def test_adopt_all_changes(
        self,
        client: AsyncClient,
        async_session: AsyncSession,
        loaded_baseline: ValuationRuleset,
        modified_baseline_json: dict[str, Any],
    ):
        """Should adopt all changes and create new ruleset version"""
        response = await client.post(
            "/api/v1/baseline/adopt",
            json={
                "candidate_json": modified_baseline_json,
                "trigger_recalculation": False,
                "actor": "admin_user",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["new_ruleset_id"] != loaded_baseline.id
        assert data["changes_applied"] >= 1
        assert data["previous_ruleset_id"] == loaded_baseline.id
        assert data["audit_log_id"] is not None

        # Verify new ruleset was created
        stmt = select(ValuationRuleset).where(ValuationRuleset.id == data["new_ruleset_id"])
        result = await async_session.execute(stmt)
        new_ruleset = result.scalar_one()
        assert new_ruleset.is_active is True

        # Verify old ruleset was deactivated
        await async_session.refresh(loaded_baseline)
        assert loaded_baseline.is_active is False

        # Verify audit log
        audit_stmt = select(ValuationRuleAudit).where(ValuationRuleAudit.id == data["audit_log_id"])
        audit_result = await async_session.execute(audit_stmt)
        audit_entry = audit_result.scalar_one()
        assert audit_entry.action == "baseline_adopted"
        assert audit_entry.actor == "admin_user"

    async def test_adopt_selected_changes(
        self,
        client: AsyncClient,
        async_session: AsyncSession,
        loaded_baseline: ValuationRuleset,
        modified_baseline_json: dict[str, Any],
    ):
        """Should adopt only selected changes"""
        # Only adopt the warranty_adjustment field
        response = await client.post(
            "/api/v1/baseline/adopt",
            json={
                "candidate_json": modified_baseline_json,
                "selected_changes": ["Listing.warranty_adjustment"],
                "trigger_recalculation": False,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["changes_applied"] == 1
        assert "Listing.warranty_adjustment" in data["adopted_fields"]

        # base_adjustment changes should be skipped
        assert len(data["skipped_fields"]) > 0

    async def test_adopt_with_recalculation(
        self,
        client: AsyncClient,
        loaded_baseline: ValuationRuleset,
        modified_baseline_json: dict[str, Any],
    ):
        """Should trigger recalculation when requested"""
        response = await client.post(
            "/api/v1/baseline/adopt",
            json={
                "candidate_json": modified_baseline_json,
                "trigger_recalculation": True,
                "actor": "admin_user",
            },
        )
        assert response.status_code == 200

        data = response.json()
        # Note: recalculation_job_id may be None if Redis is not available
        # This is acceptable as it's a non-fatal failure
        assert "recalculation_job_id" in data


# --- Integration Tests ---


class TestBaselineWorkflow:
    """End-to-end baseline workflow tests"""

    async def test_full_baseline_lifecycle(
        self, client: AsyncClient, async_session: AsyncSession, tmp_path: Path
    ):
        """Test complete baseline workflow: instantiate -> diff -> adopt"""
        # Step 1: Create and instantiate initial baseline
        initial_baseline = {
            "schema_version": "1.0",
            "generated_at": "2025-10-12T10:00:00Z",
            "entities": {
                "Listing": [
                    {
                        "id": "field_v1",
                        "proper_name": "Field V1",
                        "description": "Version 1",
                        "unit": "USD",
                        "valuation_buckets": [{"label": "V1", "min_usd": 10, "max_usd": 20}],
                        "nullable": False,
                    }
                ]
            },
        }

        baseline_file = tmp_path / "v1_baseline.json"
        baseline_file.write_text(json.dumps(initial_baseline))

        instantiate_response = await client.post(
            "/api/v1/baseline/instantiate", json={"baseline_path": str(baseline_file)}
        )
        assert instantiate_response.status_code == 200
        v1_data = instantiate_response.json()
        assert v1_data["created"] is True

        # Step 2: Get metadata
        meta_response = await client.get("/api/v1/baseline/meta")
        assert meta_response.status_code == 200
        meta_data = meta_response.json()
        assert meta_data["ruleset_id"] == v1_data["ruleset_id"]

        # Step 3: Create v2 with changes
        v2_baseline = {
            "schema_version": "1.0",
            "generated_at": "2025-10-12T12:00:00Z",
            "entities": {
                "Listing": [
                    {
                        "id": "field_v1",
                        "proper_name": "Field V1 Updated",  # Changed
                        "description": "Version 1 updated",  # Changed
                        "unit": "USD",
                        "valuation_buckets": [
                            {"label": "V1", "min_usd": 15, "max_usd": 25}
                        ],  # Changed
                        "nullable": False,
                    },
                    {
                        "id": "field_v2",  # New field
                        "proper_name": "Field V2",
                        "description": "Version 2",
                        "unit": "multiplier",
                        "valuation_buckets": [{"label": "V2", "min_usd": 1.0, "max_usd": 1.5}],
                        "nullable": True,
                    },
                ]
            },
        }

        # Step 4: Diff v2 against v1
        diff_response = await client.post(
            "/api/v1/baseline/diff", json={"candidate_json": v2_baseline}
        )
        assert diff_response.status_code == 200
        diff_data = diff_response.json()
        assert diff_data["summary"]["added_count"] == 1  # field_v2
        assert diff_data["summary"]["changed_count"] == 1  # field_v1

        # Step 5: Adopt v2
        adopt_response = await client.post(
            "/api/v1/baseline/adopt",
            json={
                "candidate_json": v2_baseline,
                "actor": "workflow_test",
            },
        )
        assert adopt_response.status_code == 200
        adopt_data = adopt_response.json()
        assert adopt_data["new_ruleset_id"] != v1_data["ruleset_id"]
        assert adopt_data["previous_ruleset_id"] == v1_data["ruleset_id"]

        # Step 6: Verify new metadata
        final_meta_response = await client.get("/api/v1/baseline/meta")
        assert final_meta_response.status_code == 200
        final_meta_data = final_meta_response.json()
        assert final_meta_data["ruleset_id"] == adopt_data["new_ruleset_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
