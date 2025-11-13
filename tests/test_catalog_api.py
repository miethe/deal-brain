"""Integration tests for catalog UPDATE endpoints (PUT and PATCH)."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from dealbrain_api.app import create_app
from dealbrain_api.db import Base
from dealbrain_core.enums import RamGeneration, StorageMedium


# --- Fixtures ---


@pytest_asyncio.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(test_engine):
    """Create async database session for tests."""
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_engine):
    """Create async HTTP client for API tests with test database."""
    app = create_app()

    # Override the session dependency to use test database
    from dealbrain_api.db import session_dependency

    async def override_session_dependency():
        session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[session_dependency] = override_session_dependency

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clean up override
    app.dependency_overrides.clear()


# --- CPU UPDATE Tests ---


class TestCpuUpdate:
    """Tests for PUT /v1/catalog/cpus/{cpu_id} endpoint."""

    @pytest.mark.asyncio
    
    async def test_update_cpu_full_success(self, client: AsyncClient, async_session: AsyncSession):
        """Should successfully perform full update (PUT) of CPU entity."""
        # Create CPU via POST
        create_payload = {
            "name": "Intel Core i5-10400",
            "manufacturer": "Intel",
            "socket": "LGA1200",
            "cores": 6,
            "threads": 12,
            "tdp_w": 65,
            "cpu_mark_multi": 12000,
            "attributes": {"test_key": "original_value"},
        }
        create_response = await client.post("/v1/catalog/cpus", json=create_payload)
        assert create_response.status_code == 201
        cpu_id = create_response.json()["id"]
        original_created_at = create_response.json()["created_at"]

        # Update via PUT with complete new data
        update_payload = {
            "name": "Intel Core i5-10400F",
            "manufacturer": "Intel",
            "socket": "LGA1200",
            "cores": 6,
            "threads": 12,
            "tdp_w": 65,
            "igpu_model": None,  # Changed - no iGPU in F variant
            "cpu_mark_multi": 12100,  # Changed
            "cpu_mark_single": 2800,  # New field
            "attributes": {"test_key": "updated_value"},  # Changed
        }
        update_response = await client.put(f"/v1/catalog/cpus/{cpu_id}", json=update_payload)

        # Assert response is 200 OK
        assert update_response.status_code == 200

        # Assert returned DTO matches update data
        data = update_response.json()
        assert data["name"] == "Intel Core i5-10400F"
        assert data["cpu_mark_multi"] == 12100
        assert data["cpu_mark_single"] == 2800
        assert data["attributes"]["test_key"] == "updated_value"

        # Assert modified_at timestamp updated
        assert data["updated_at"] != original_created_at

        # Verify database persistence
        verify_response = await client.get(f"/v1/catalog/cpus/{cpu_id}")
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["name"] == "Intel Core i5-10400F"
        assert verify_data["cpu_mark_multi"] == 12100

    @pytest.mark.asyncio
    async def test_update_cpu_unique_constraint_violation(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 422 when updating CPU with duplicate name."""
        # Create two CPUs
        cpu_a_payload = {"name": "CPU A", "manufacturer": "Intel"}
        cpu_b_payload = {"name": "CPU B", "manufacturer": "Intel"}

        cpu_a_response = await client.post("/v1/catalog/cpus", json=cpu_a_payload)
        cpu_b_response = await client.post("/v1/catalog/cpus", json=cpu_b_payload)

        assert cpu_a_response.status_code == 201
        assert cpu_b_response.status_code == 201

        cpu_b_id = cpu_b_response.json()["id"]

        # Try to update CPU B with CPU A's name
        update_payload = {"name": "CPU A", "manufacturer": "Intel"}
        update_response = await client.put(f"/v1/catalog/cpus/{cpu_b_id}", json=update_payload)

        # Assert response is 422 Unprocessable Entity
        assert update_response.status_code == 422

        # Assert error message describes constraint violation
        data = update_response.json()
        assert "already exists" in data["detail"]

    @pytest.mark.asyncio
    async def test_update_cpu_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent CPU."""
        non_existent_id = 99999
        update_payload = {"name": "Non-existent CPU", "manufacturer": "Intel"}
        response = await client.put(f"/v1/catalog/cpus/{non_existent_id}", json=update_payload)

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_update_cpu_invalid_input(self, client: AsyncClient):
        """Should return 422 for invalid input data."""
        # Create CPU first
        create_payload = {"name": "Test CPU", "manufacturer": "Intel"}
        create_response = await client.post("/v1/catalog/cpus", json=create_payload)
        assert create_response.status_code == 201
        cpu_id = create_response.json()["id"]

        # Try to update with invalid data (negative cores)
        invalid_payload = {"name": "Test CPU", "manufacturer": "Intel", "cores": -5}
        response = await client.put(f"/v1/catalog/cpus/{cpu_id}", json=invalid_payload)

        assert response.status_code == 422


class TestCpuPartialUpdate:
    """Tests for PATCH /v1/catalog/cpus/{cpu_id} endpoint."""

    @pytest.mark.asyncio
    async def test_partial_update_cpu_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully perform partial update (PATCH) of CPU entity."""
        # Create CPU via POST
        create_payload = {
            "name": "AMD Ryzen 5 5600X",
            "manufacturer": "AMD",
            "socket": "AM4",
            "cores": 6,
            "threads": 12,
            "cpu_mark_multi": 22000,
            "attributes": {"tier": "mid-range", "gen": "zen3"},
        }
        create_response = await client.post("/v1/catalog/cpus", json=create_payload)
        assert create_response.status_code == 201
        cpu_id = create_response.json()["id"]

        # Update via PATCH with partial data (only change cpu_mark_multi and add attribute)
        patch_payload = {
            "cpu_mark_multi": 22141,  # Updated
            "attributes": {"overclock": "yes"},  # New attribute
        }
        patch_response = await client.patch(f"/v1/catalog/cpus/{cpu_id}", json=patch_payload)

        # Assert response is 200 OK
        assert patch_response.status_code == 200

        # Assert patched fields updated
        data = patch_response.json()
        assert data["cpu_mark_multi"] == 22141

        # Assert non-patched fields unchanged
        assert data["name"] == "AMD Ryzen 5 5600X"
        assert data["socket"] == "AM4"
        assert data["cores"] == 6

        # Assert attributes_json merged correctly (not replaced)
        assert data["attributes"]["tier"] == "mid-range"  # Original preserved
        assert data["attributes"]["gen"] == "zen3"  # Original preserved
        assert data["attributes"]["overclock"] == "yes"  # New added

    @pytest.mark.asyncio
    async def test_partial_update_cpu_attributes_merge(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should merge attributes_json on PATCH, not replace completely."""
        # Create CPU with initial attributes
        create_payload = {
            "name": "Test CPU",
            "manufacturer": "Intel",
            "attributes": {"key1": "value1", "key2": "value2", "key3": "value3"},
        }
        create_response = await client.post("/v1/catalog/cpus", json=create_payload)
        assert create_response.status_code == 201
        cpu_id = create_response.json()["id"]

        # PATCH with partial attributes
        patch_payload = {"attributes": {"key2": "updated_value2", "key4": "value4"}}
        patch_response = await client.patch(f"/v1/catalog/cpus/{cpu_id}", json=patch_payload)

        assert patch_response.status_code == 200
        data = patch_response.json()

        # Verify merge behavior
        assert data["attributes"]["key1"] == "value1"  # Preserved
        assert data["attributes"]["key2"] == "updated_value2"  # Updated
        assert data["attributes"]["key3"] == "value3"  # Preserved
        assert data["attributes"]["key4"] == "value4"  # Added


# --- GPU UPDATE Tests ---


class TestGpuUpdate:
    """Tests for PUT /v1/catalog/gpus/{gpu_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_gpu_full_success(self, client: AsyncClient, async_session: AsyncSession):
        """Should successfully perform full update (PUT) of GPU entity."""
        # Create GPU via POST
        create_payload = {
            "name": "NVIDIA GeForce RTX 3060",
            "manufacturer": "NVIDIA",
            "gpu_mark": 17000,
            "attributes": {"vram": "12GB"},
        }
        create_response = await client.post("/v1/catalog/gpus", json=create_payload)
        assert create_response.status_code == 201
        gpu_id = create_response.json()["id"]

        # Update via PUT
        update_payload = {
            "name": "NVIDIA GeForce RTX 3060 Ti",
            "manufacturer": "NVIDIA",
            "gpu_mark": 20000,
            "metal_score": 95000,
            "attributes": {"vram": "8GB"},
        }
        update_response = await client.put(f"/v1/catalog/gpus/{gpu_id}", json=update_payload)

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "NVIDIA GeForce RTX 3060 Ti"
        assert data["gpu_mark"] == 20000
        assert data["metal_score"] == 95000
        assert data["attributes"]["vram"] == "8GB"

    @pytest.mark.asyncio
    async def test_update_gpu_unique_constraint_violation(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 422 when updating GPU with duplicate name."""
        gpu_a = await client.post(
            "/v1/catalog/gpus", json={"name": "GPU A", "manufacturer": "NVIDIA"}
        )
        gpu_b = await client.post(
            "/v1/catalog/gpus", json={"name": "GPU B", "manufacturer": "AMD"}
        )

        assert gpu_a.status_code == 201
        assert gpu_b.status_code == 201

        gpu_b_id = gpu_b.json()["id"]

        # Try to rename GPU B to GPU A's name
        update_payload = {"name": "GPU A", "manufacturer": "AMD"}
        response = await client.put(f"/v1/catalog/gpus/{gpu_b_id}", json=update_payload)

        assert response.status_code == 422
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_gpu_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent GPU."""
        response = await client.put(
            "/v1/catalog/gpus/99999", json={"name": "Non-existent", "manufacturer": "NVIDIA"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_gpu_invalid_input(self, client: AsyncClient):
        """Should return 422 for invalid input data."""
        create_response = await client.post(
            "/v1/catalog/gpus", json={"name": "Test GPU", "manufacturer": "NVIDIA"}
        )
        gpu_id = create_response.json()["id"]

        # Invalid gpu_mark (negative)
        invalid_payload = {"name": "Test GPU", "manufacturer": "NVIDIA", "gpu_mark": -1000}
        response = await client.put(f"/v1/catalog/gpus/{gpu_id}", json=invalid_payload)

        assert response.status_code == 422


class TestGpuPartialUpdate:
    """Tests for PATCH /v1/catalog/gpus/{gpu_id} endpoint."""

    @pytest.mark.asyncio
    async def test_partial_update_gpu_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully perform partial update (PATCH) of GPU entity."""
        create_payload = {
            "name": "AMD Radeon RX 6700 XT",
            "manufacturer": "AMD",
            "gpu_mark": 18000,
            "attributes": {"vram": "12GB", "architecture": "RDNA 2"},
        }
        create_response = await client.post("/v1/catalog/gpus", json=create_payload)
        gpu_id = create_response.json()["id"]

        # Partial update
        patch_payload = {"gpu_mark": 18500, "attributes": {"tdp": "230W"}}
        patch_response = await client.patch(f"/v1/catalog/gpus/{gpu_id}", json=patch_payload)

        assert patch_response.status_code == 200
        data = patch_response.json()
        assert data["gpu_mark"] == 18500  # Updated
        assert data["name"] == "AMD Radeon RX 6700 XT"  # Unchanged
        assert data["attributes"]["vram"] == "12GB"  # Preserved
        assert data["attributes"]["architecture"] == "RDNA 2"  # Preserved
        assert data["attributes"]["tdp"] == "230W"  # Added


# --- Profile UPDATE Tests ---


class TestProfileUpdate:
    """Tests for PUT /v1/catalog/profiles/{profile_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_profile_full_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully perform full update (PUT) of Profile entity."""
        create_payload = {
            "name": "Performance Profile",
            "description": "Optimized for performance",
            "weights_json": {"cpu_score": 0.5, "gpu_score": 0.3, "ram_score": 0.2},
            "is_default": False,
        }
        create_response = await client.post("/v1/catalog/profiles", json=create_payload)
        assert create_response.status_code == 201
        profile_id = create_response.json()["id"]

        # Full update
        update_payload = {
            "name": "High Performance Profile",
            "description": "Maximum performance",
            "weights_json": {"cpu_score": 0.6, "gpu_score": 0.4},
            "is_default": False,
        }
        update_response = await client.put(
            f"/v1/catalog/profiles/{profile_id}", json=update_payload
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "High Performance Profile"
        assert data["weights_json"]["cpu_score"] == 0.6
        assert "ram_score" not in data["weights_json"]  # Replaced, not merged

    @pytest.mark.asyncio
    async def test_update_profile_is_default_management(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should unset is_default from other profiles when setting new default."""
        # Create two profiles, first one default
        profile1 = await client.post(
            "/v1/catalog/profiles",
            json={
                "name": "Profile 1",
                "weights_json": {"cpu_score": 1.0},
                "is_default": True,
            },
        )
        profile2 = await client.post(
            "/v1/catalog/profiles",
            json={
                "name": "Profile 2",
                "weights_json": {"cpu_score": 1.0},
                "is_default": False,
            },
        )

        profile1_id = profile1.json()["id"]
        profile2_id = profile2.json()["id"]

        # Set profile 2 as default
        update_payload = {
            "name": "Profile 2",
            "weights_json": {"cpu_score": 1.0},
            "is_default": True,
        }
        update_response = await client.put(
            f"/v1/catalog/profiles/{profile2_id}", json=update_payload
        )

        assert update_response.status_code == 200
        assert update_response.json()["is_default"] is True

        # Verify profile 1 is no longer default
        profile1_check = await client.get(f"/v1/catalog/profiles")
        profiles = profile1_check.json()
        profile1_data = next(p for p in profiles if p["id"] == profile1_id)
        profile2_data = next(p for p in profiles if p["id"] == profile2_id)

        assert profile1_data["is_default"] is False
        assert profile2_data["is_default"] is True

    @pytest.mark.asyncio
    async def test_update_profile_prevent_unset_only_default(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should prevent unsetting is_default from only default profile."""
        # Create single default profile
        profile = await client.post(
            "/v1/catalog/profiles",
            json={
                "name": "Only Profile",
                "weights_json": {"cpu_score": 1.0},
                "is_default": True,
            },
        )
        profile_id = profile.json()["id"]

        # Try to unset is_default
        update_payload = {
            "name": "Only Profile",
            "weights_json": {"cpu_score": 1.0},
            "is_default": False,
        }
        update_response = await client.put(
            f"/v1/catalog/profiles/{profile_id}", json=update_payload
        )

        assert update_response.status_code == 422
        assert "only default profile" in update_response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_profile_unique_constraint_violation(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 422 when updating profile with duplicate name."""
        profile_a = await client.post(
            "/v1/catalog/profiles",
            json={"name": "Profile A", "weights_json": {"cpu_score": 1.0}},
        )
        profile_b = await client.post(
            "/v1/catalog/profiles",
            json={"name": "Profile B", "weights_json": {"cpu_score": 1.0}},
        )

        profile_b_id = profile_b.json()["id"]

        update_payload = {"name": "Profile A", "weights_json": {"cpu_score": 1.0}}
        response = await client.put(f"/v1/catalog/profiles/{profile_b_id}", json=update_payload)

        assert response.status_code == 422
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_profile_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent profile."""
        response = await client.put(
            "/v1/catalog/profiles/99999",
            json={"name": "Non-existent", "weights_json": {"cpu_score": 1.0}},
        )
        assert response.status_code == 404


class TestProfilePartialUpdate:
    """Tests for PATCH /v1/catalog/profiles/{profile_id} endpoint."""

    @pytest.mark.asyncio
    async def test_partial_update_profile_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully perform partial update (PATCH) with weights merging."""
        create_payload = {
            "name": "Balanced Profile",
            "weights_json": {"cpu_score": 0.33, "gpu_score": 0.33, "ram_score": 0.34},
        }
        create_response = await client.post("/v1/catalog/profiles", json=create_payload)
        profile_id = create_response.json()["id"]

        # Partial update - only change cpu_score weight
        patch_payload = {"weights_json": {"cpu_score": 0.5}}
        patch_response = await client.patch(
            f"/v1/catalog/profiles/{profile_id}", json=patch_payload
        )

        assert patch_response.status_code == 200
        data = patch_response.json()
        assert data["weights_json"]["cpu_score"] == 0.5  # Updated
        assert data["weights_json"]["gpu_score"] == 0.33  # Preserved
        assert data["weights_json"]["ram_score"] == 0.34  # Preserved


# --- PortsProfile UPDATE Tests ---


class TestPortsProfileUpdate:
    """Tests for PUT /v1/catalog/ports-profiles/{profile_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_ports_profile_full_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully perform full update (PUT) of PortsProfile with nested ports."""
        create_payload = {
            "name": "Mini PC Ports",
            "description": "Standard mini PC port configuration",
            "ports": [
                {"type": "USB-A", "count": 4},
                {"type": "USB-C", "count": 1},
                {"type": "HDMI", "count": 2},
            ],
        }
        create_response = await client.post("/v1/catalog/ports-profiles", json=create_payload)
        assert create_response.status_code == 201
        profile_id = create_response.json()["id"]

        # Full update with different ports
        update_payload = {
            "name": "Updated Mini PC Ports",
            "description": "Enhanced configuration",
            "ports": [
                {"type": "USB-A", "count": 2},  # Reduced
                {"type": "USB-C", "count": 2},  # Increased
                {"type": "DisplayPort", "count": 1},  # New
            ],
        }
        update_response = await client.put(
            f"/v1/catalog/ports-profiles/{profile_id}", json=update_payload
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated Mini PC Ports"
        assert len(data["ports"]) == 3

        # Verify old HDMI port is removed, DisplayPort added
        port_types = [p["type"] for p in data["ports"]]
        assert "DisplayPort" in port_types
        assert "HDMI" not in port_types

    @pytest.mark.asyncio
    async def test_update_ports_profile_unique_constraint_violation(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 422 when updating ports profile with duplicate name."""
        profile_a = await client.post(
            "/v1/catalog/ports-profiles",
            json={"name": "Ports Profile A", "ports": []},
        )
        profile_b = await client.post(
            "/v1/catalog/ports-profiles",
            json={"name": "Ports Profile B", "ports": []},
        )

        profile_b_id = profile_b.json()["id"]

        update_payload = {"name": "Ports Profile A"}
        response = await client.put(
            f"/v1/catalog/ports-profiles/{profile_b_id}", json=update_payload
        )

        assert response.status_code == 422
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_ports_profile_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent ports profile."""
        response = await client.put(
            "/v1/catalog/ports-profiles/99999",
            json={"name": "Non-existent", "ports": []},
        )
        assert response.status_code == 404


class TestPortsProfilePartialUpdate:
    """Tests for PATCH /v1/catalog/ports-profiles/{profile_id} endpoint."""

    @pytest.mark.asyncio
    async def test_partial_update_ports_profile_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully perform partial update (PATCH) with attributes merging."""
        create_payload = {
            "name": "Desktop Ports",
            "attributes": {"form_factor": "ATX", "generation": "gen4"},
            "ports": [{"type": "USB-A", "count": 6}],
        }
        create_response = await client.post("/v1/catalog/ports-profiles", json=create_payload)
        profile_id = create_response.json()["id"]

        # Partial update - only change attributes
        patch_payload = {"attributes": {"generation": "gen5", "pcie_lanes": 20}}
        patch_response = await client.patch(
            f"/v1/catalog/ports-profiles/{profile_id}", json=patch_payload
        )

        assert patch_response.status_code == 200
        data = patch_response.json()
        assert data["attributes"]["form_factor"] == "ATX"  # Preserved
        assert data["attributes"]["generation"] == "gen5"  # Updated
        assert data["attributes"]["pcie_lanes"] == 20  # Added

    @pytest.mark.asyncio
    async def test_partial_update_ports_profile_replace_ports(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should replace all ports when ports field provided in PATCH."""
        create_payload = {
            "name": "Test Ports Profile",
            "ports": [{"type": "USB-A", "count": 4}, {"type": "HDMI", "count": 1}],
        }
        create_response = await client.post("/v1/catalog/ports-profiles", json=create_payload)
        profile_id = create_response.json()["id"]

        # PATCH with new ports (replaces all)
        patch_payload = {"ports": [{"type": "USB-C", "count": 2}]}
        patch_response = await client.patch(
            f"/v1/catalog/ports-profiles/{profile_id}", json=patch_payload
        )

        assert patch_response.status_code == 200
        data = patch_response.json()
        assert len(data["ports"]) == 1
        assert data["ports"][0]["type"] == "USB-C"


# --- RamSpec UPDATE Tests ---


class TestRamSpecUpdate:
    """Tests for PUT /v1/catalog/ram-specs/{ram_spec_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_ram_spec_full_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully perform full update (PUT) of RamSpec entity."""
        create_payload = {
            "label": "16GB DDR4 3200MHz",
            "ddr_generation": RamGeneration.DDR4.value,
            "speed_mhz": 3200,
            "module_count": 2,
            "capacity_per_module_gb": 8,
            "total_capacity_gb": 16,
        }
        create_response = await client.post("/v1/catalog/ram-specs", json=create_payload)
        assert create_response.status_code == 201
        ram_spec_id = create_response.json()["id"]

        # Full update
        update_payload = {
            "label": "16GB DDR4 3600MHz",
            "ddr_generation": RamGeneration.DDR4.value,
            "speed_mhz": 3600,  # Changed
            "module_count": 2,
            "capacity_per_module_gb": 8,
            "total_capacity_gb": 16,
            "attributes": {"overclockable": True},
        }
        update_response = await client.put(
            f"/v1/catalog/ram-specs/{ram_spec_id}", json=update_payload
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["speed_mhz"] == 3600
        assert data["attributes"]["overclockable"] is True

    @pytest.mark.asyncio
    async def test_update_ram_spec_unique_constraint_violation(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 422 when updating RAM spec with duplicate specifications."""
        # Create two distinct RAM specs
        spec_a = await client.post(
            "/v1/catalog/ram-specs",
            json={
                "ddr_generation": RamGeneration.DDR4.value,
                "speed_mhz": 3200,
                "module_count": 2,
                "capacity_per_module_gb": 8,
                "total_capacity_gb": 16,
            },
        )
        spec_b = await client.post(
            "/v1/catalog/ram-specs",
            json={
                "ddr_generation": RamGeneration.DDR4.value,
                "speed_mhz": 3600,
                "module_count": 2,
                "capacity_per_module_gb": 8,
                "total_capacity_gb": 16,
            },
        )

        spec_b_id = spec_b.json()["id"]

        # Try to change spec B to match spec A's specifications
        update_payload = {
            "ddr_generation": RamGeneration.DDR4.value,
            "speed_mhz": 3200,  # Same as spec A
            "module_count": 2,
            "capacity_per_module_gb": 8,
            "total_capacity_gb": 16,
        }
        response = await client.put(f"/v1/catalog/ram-specs/{spec_b_id}", json=update_payload)

        assert response.status_code == 422
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_ram_spec_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent RAM spec."""
        response = await client.put(
            "/v1/catalog/ram-specs/99999",
            json={
                "ddr_generation": RamGeneration.DDR4.value,
                "speed_mhz": 3200,
                "total_capacity_gb": 16,
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_ram_spec_invalid_input(self, client: AsyncClient):
        """Should return 422 for invalid input data."""
        create_response = await client.post(
            "/v1/catalog/ram-specs",
            json={
                "ddr_generation": RamGeneration.DDR4.value,
                "speed_mhz": 3200,
                "total_capacity_gb": 16,
            },
        )
        ram_spec_id = create_response.json()["id"]

        # Invalid speed_mhz (out of range)
        invalid_payload = {
            "ddr_generation": RamGeneration.DDR4.value,
            "speed_mhz": 50000,  # Too high
            "total_capacity_gb": 16,
        }
        response = await client.put(f"/v1/catalog/ram-specs/{ram_spec_id}", json=invalid_payload)

        assert response.status_code == 422


class TestRamSpecPartialUpdate:
    """Tests for PATCH /v1/catalog/ram-specs/{ram_spec_id} endpoint."""

    @pytest.mark.asyncio
    async def test_partial_update_ram_spec_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully perform partial update (PATCH) of RamSpec entity."""
        create_payload = {
            "label": "32GB DDR5",
            "ddr_generation": RamGeneration.DDR5.value,
            "speed_mhz": 5200,
            "total_capacity_gb": 32,
            "attributes": {"ecc": False},
        }
        create_response = await client.post("/v1/catalog/ram-specs", json=create_payload)
        ram_spec_id = create_response.json()["id"]

        # Partial update
        patch_payload = {
            "speed_mhz": 5600,  # Updated
            "attributes": {"rgb": True},  # New attribute
        }
        patch_response = await client.patch(
            f"/v1/catalog/ram-specs/{ram_spec_id}", json=patch_payload
        )

        assert patch_response.status_code == 200
        data = patch_response.json()
        assert data["speed_mhz"] == 5600  # Updated
        assert data["total_capacity_gb"] == 32  # Unchanged
        assert data["attributes"]["ecc"] is False  # Preserved
        assert data["attributes"]["rgb"] is True  # Added


# --- StorageProfile UPDATE Tests ---


class TestStorageProfileUpdate:
    """Tests for PUT /v1/catalog/storage-profiles/{storage_profile_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_storage_profile_full_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully perform full update (PUT) of StorageProfile entity."""
        create_payload = {
            "label": "512GB NVMe SSD",
            "medium": StorageMedium.SSD.value,
            "interface": "NVMe",
            "form_factor": "M.2",
            "capacity_gb": 512,
            "performance_tier": "high",
        }
        create_response = await client.post(
            "/v1/catalog/storage-profiles", json=create_payload
        )
        assert create_response.status_code == 201
        storage_profile_id = create_response.json()["id"]

        # Full update
        update_payload = {
            "label": "1TB NVMe SSD",
            "medium": StorageMedium.SSD.value,
            "interface": "NVMe",
            "form_factor": "M.2",
            "capacity_gb": 1024,  # Changed
            "performance_tier": "premium",  # Changed
            "attributes": {"gen": "4"},
        }
        update_response = await client.put(
            f"/v1/catalog/storage-profiles/{storage_profile_id}", json=update_payload
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["capacity_gb"] == 1024
        assert data["performance_tier"] == "premium"
        assert data["attributes"]["gen"] == "4"

    @pytest.mark.asyncio
    async def test_update_storage_profile_unique_constraint_violation(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 422 when updating storage profile with duplicate specifications."""
        # Create two storage profiles
        profile_a = await client.post(
            "/v1/catalog/storage-profiles",
            json={
                "medium": StorageMedium.SSD.value,
                "interface": "NVMe",
                "form_factor": "M.2",
                "capacity_gb": 512,
                "performance_tier": "high",
            },
        )
        profile_b = await client.post(
            "/v1/catalog/storage-profiles",
            json={
                "medium": StorageMedium.SSD.value,
                "interface": "NVMe",
                "form_factor": "M.2",
                "capacity_gb": 1024,
                "performance_tier": "high",
            },
        )

        profile_b_id = profile_b.json()["id"]

        # Try to change profile B to match profile A
        update_payload = {
            "medium": StorageMedium.SSD.value,
            "interface": "NVMe",
            "form_factor": "M.2",
            "capacity_gb": 512,  # Same as profile A
            "performance_tier": "high",
        }
        response = await client.put(
            f"/v1/catalog/storage-profiles/{profile_b_id}", json=update_payload
        )

        assert response.status_code == 422
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_storage_profile_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent storage profile."""
        response = await client.put(
            "/v1/catalog/storage-profiles/99999",
            json={
                "medium": StorageMedium.SSD.value,
                "interface": "SATA",
                "capacity_gb": 256,
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_storage_profile_invalid_input(self, client: AsyncClient):
        """Should return 422 for invalid input data."""
        create_response = await client.post(
            "/v1/catalog/storage-profiles",
            json={
                "medium": StorageMedium.HDD.value,
                "interface": "SATA",
                "capacity_gb": 1000,
            },
        )
        storage_profile_id = create_response.json()["id"]

        # Invalid capacity_gb (out of range)
        invalid_payload = {
            "medium": StorageMedium.HDD.value,
            "interface": "SATA",
            "capacity_gb": 200000,  # Too large
        }
        response = await client.put(
            f"/v1/catalog/storage-profiles/{storage_profile_id}", json=invalid_payload
        )

        assert response.status_code == 422


class TestStorageProfilePartialUpdate:
    """Tests for PATCH /v1/catalog/storage-profiles/{storage_profile_id} endpoint."""

    @pytest.mark.asyncio
    async def test_partial_update_storage_profile_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully perform partial update (PATCH) of StorageProfile entity."""
        create_payload = {
            "label": "2TB HDD",
            "medium": StorageMedium.HDD.value,
            "interface": "SATA",
            "capacity_gb": 2000,
            "attributes": {"rpm": 7200},
        }
        create_response = await client.post(
            "/v1/catalog/storage-profiles", json=create_payload
        )
        storage_profile_id = create_response.json()["id"]

        # Partial update
        patch_payload = {
            "performance_tier": "standard",  # New field
            "attributes": {"cache_mb": 256},  # New attribute
        }
        patch_response = await client.patch(
            f"/v1/catalog/storage-profiles/{storage_profile_id}", json=patch_payload
        )

        assert patch_response.status_code == 200
        data = patch_response.json()
        assert data["performance_tier"] == "standard"  # Updated
        assert data["capacity_gb"] == 2000  # Unchanged
        assert data["attributes"]["rpm"] == 7200  # Preserved
        assert data["attributes"]["cache_mb"] == 256  # Added


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
