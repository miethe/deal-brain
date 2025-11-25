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

        # Assert modified_at timestamp updated (or at least not before original)
        assert data["updated_at"] >= original_created_at

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
        gpu_b = await client.post("/v1/catalog/gpus", json={"name": "GPU B", "manufacturer": "AMD"})

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
            "medium": StorageMedium.SATA_SSD.value,
            "interface": "NVMe",
            "form_factor": "M.2",
            "capacity_gb": 512,
            "performance_tier": "high",
        }
        create_response = await client.post("/v1/catalog/storage-profiles", json=create_payload)
        assert create_response.status_code == 201
        storage_profile_id = create_response.json()["id"]

        # Full update
        update_payload = {
            "label": "1TB NVMe SSD",
            "medium": StorageMedium.SATA_SSD.value,
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
                "medium": StorageMedium.SATA_SSD.value,
                "interface": "NVMe",
                "form_factor": "M.2",
                "capacity_gb": 512,
                "performance_tier": "high",
            },
        )
        profile_b = await client.post(
            "/v1/catalog/storage-profiles",
            json={
                "medium": StorageMedium.SATA_SSD.value,
                "interface": "NVMe",
                "form_factor": "M.2",
                "capacity_gb": 1024,
                "performance_tier": "high",
            },
        )

        profile_b_id = profile_b.json()["id"]

        # Try to change profile B to match profile A
        update_payload = {
            "medium": StorageMedium.SATA_SSD.value,
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
                "medium": StorageMedium.SATA_SSD.value,
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
        create_response = await client.post("/v1/catalog/storage-profiles", json=create_payload)
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


# --- CPU DELETE Tests ---


class TestCpuDelete:
    """Tests for DELETE /v1/catalog/cpus/{cpu_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_cpu_unused_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully delete unused CPU entity."""
        # Create CPU via POST
        create_payload = {"name": "Test CPU for Deletion", "manufacturer": "Intel"}
        create_response = await client.post("/v1/catalog/cpus", json=create_payload)
        assert create_response.status_code == 201
        cpu_id = create_response.json()["id"]

        # Delete via DELETE
        delete_response = await client.delete(f"/v1/catalog/cpus/{cpu_id}")

        # Assert response is 204 No Content
        assert delete_response.status_code == 204

        # Verify entity no longer exists
        get_response = await client.get(f"/v1/catalog/cpus/{cpu_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_cpu_in_use_conflict(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 409 Conflict when CPU is used in listings."""
        # Create CPU
        cpu_payload = {"name": "CPU In Use", "manufacturer": "Intel"}
        cpu_response = await client.post("/v1/catalog/cpus", json=cpu_payload)
        assert cpu_response.status_code == 201
        cpu_id = cpu_response.json()["id"]

        # Create listing that uses this CPU
        listing_payload = {
            "title": "Test Listing",
            "url": "https://example.com/test-cpu-listing",
            "price_usd": 500.0,
            "cpu_id": cpu_id,
        }
        listing_response = await client.post("/v1/listings/", json=listing_payload)
        assert listing_response.status_code == 201

        # Attempt DELETE
        delete_response = await client.delete(f"/v1/catalog/cpus/{cpu_id}")

        # Assert response is 409 Conflict
        assert delete_response.status_code == 409

        # Assert error message includes usage count
        error_detail = delete_response.json()["detail"]
        assert "used in 1 listing(s)" in error_detail

        # Verify entity still exists
        get_response = await client.get(f"/v1/catalog/cpus/{cpu_id}")
        assert get_response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_cpu_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent CPU."""
        non_existent_id = 99999
        delete_response = await client.delete(f"/v1/catalog/cpus/{non_existent_id}")

        assert delete_response.status_code == 404
        error_detail = delete_response.json()["detail"]
        assert "not found" in error_detail

    @pytest.mark.asyncio
    async def test_delete_cpu_multiple_listings_usage_count(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should report correct usage count when CPU used in multiple listings."""
        # Create CPU
        cpu_payload = {"name": "Popular CPU", "manufacturer": "AMD"}
        cpu_response = await client.post("/v1/catalog/cpus", json=cpu_payload)
        cpu_id = cpu_response.json()["id"]

        # Create multiple listings using this CPU
        for i in range(3):
            listing_payload = {
                "title": f"Test Listing {i}",
                "url": f"https://example.com/listing-{i}",
                "price_usd": 500.0 + i * 100,
                "cpu_id": cpu_id,
            }
            await client.post("/v1/listings/", json=listing_payload)

        # Attempt DELETE
        delete_response = await client.delete(f"/v1/catalog/cpus/{cpu_id}")

        # Assert 409 with exact count
        assert delete_response.status_code == 409
        error_detail = delete_response.json()["detail"]
        assert "used in 3 listing(s)" in error_detail


# --- GPU DELETE Tests ---


class TestGpuDelete:
    """Tests for DELETE /v1/catalog/gpus/{gpu_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_gpu_unused_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully delete unused GPU entity."""
        # Create GPU via POST
        create_payload = {"name": "Test GPU for Deletion", "manufacturer": "NVIDIA"}
        create_response = await client.post("/v1/catalog/gpus", json=create_payload)
        assert create_response.status_code == 201
        gpu_id = create_response.json()["id"]

        # Delete via DELETE
        delete_response = await client.delete(f"/v1/catalog/gpus/{gpu_id}")

        # Assert response is 204 No Content
        assert delete_response.status_code == 204

        # Verify entity no longer exists
        get_response = await client.get(f"/v1/catalog/gpus/{gpu_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_gpu_in_use_conflict(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 409 Conflict when GPU is used in listings."""
        # Create GPU
        gpu_payload = {"name": "GPU In Use", "manufacturer": "AMD"}
        gpu_response = await client.post("/v1/catalog/gpus", json=gpu_payload)
        assert gpu_response.status_code == 201
        gpu_id = gpu_response.json()["id"]

        # Create listing that uses this GPU
        listing_payload = {
            "title": "Test GPU Listing",
            "url": "https://example.com/test-gpu-listing",
            "price_usd": 800.0,
            "gpu_id": gpu_id,
        }
        listing_response = await client.post("/v1/listings/", json=listing_payload)
        assert listing_response.status_code == 201

        # Attempt DELETE
        delete_response = await client.delete(f"/v1/catalog/gpus/{gpu_id}")

        # Assert response is 409 Conflict
        assert delete_response.status_code == 409

        # Assert error message includes usage count
        error_detail = delete_response.json()["detail"]
        assert "used in 1 listing(s)" in error_detail

        # Verify entity still exists
        get_response = await client.get(f"/v1/catalog/gpus/{gpu_id}")
        assert get_response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_gpu_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent GPU."""
        non_existent_id = 99999
        delete_response = await client.delete(f"/v1/catalog/gpus/{non_existent_id}")

        assert delete_response.status_code == 404
        error_detail = delete_response.json()["detail"]
        assert "not found" in error_detail

    @pytest.mark.asyncio
    async def test_delete_gpu_multiple_listings_usage_count(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should report correct usage count when GPU used in multiple listings."""
        # Create GPU
        gpu_payload = {"name": "Popular GPU", "manufacturer": "NVIDIA"}
        gpu_response = await client.post("/v1/catalog/gpus", json=gpu_payload)
        gpu_id = gpu_response.json()["id"]

        # Create multiple listings using this GPU
        for i in range(5):
            listing_payload = {
                "title": f"GPU Listing {i}",
                "url": f"https://example.com/gpu-listing-{i}",
                "price_usd": 1000.0 + i * 50,
                "gpu_id": gpu_id,
            }
            await client.post("/v1/listings/", json=listing_payload)

        # Attempt DELETE
        delete_response = await client.delete(f"/v1/catalog/gpus/{gpu_id}")

        # Assert 409 with exact count
        assert delete_response.status_code == 409
        error_detail = delete_response.json()["detail"]
        assert "used in 5 listing(s)" in error_detail


# --- Profile DELETE Tests ---


class TestProfileDelete:
    """Tests for DELETE /v1/catalog/profiles/{profile_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_profile_unused_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully delete unused non-default profile."""
        # Create profile via POST
        create_payload = {
            "name": "Test Profile for Deletion",
            "weights_json": {"cpu_score": 1.0},
            "is_default": False,
        }
        create_response = await client.post("/v1/catalog/profiles", json=create_payload)
        assert create_response.status_code == 201
        profile_id = create_response.json()["id"]

        # Delete via DELETE
        delete_response = await client.delete(f"/v1/catalog/profiles/{profile_id}")

        # Assert response is 204 No Content
        assert delete_response.status_code == 204

        # Verify entity no longer exists in list
        list_response = await client.get("/v1/catalog/profiles")
        profile_ids = [p["id"] for p in list_response.json()]
        assert profile_id not in profile_ids

    @pytest.mark.asyncio
    async def test_delete_profile_in_use_conflict(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 409 Conflict when Profile is used in listings."""
        # Create profile
        profile_payload = {
            "name": "Profile In Use",
            "weights_json": {"cpu_score": 1.0},
            "is_default": False,
        }
        profile_response = await client.post("/v1/catalog/profiles", json=profile_payload)
        assert profile_response.status_code == 201
        profile_id = profile_response.json()["id"]

        # Create listing that uses this profile
        listing_payload = {
            "title": "Test Profile Listing",
            "url": "https://example.com/test-profile-listing",
            "price_usd": 600.0,
            "active_profile_id": profile_id,
        }
        listing_response = await client.post("/v1/listings/", json=listing_payload)
        assert listing_response.status_code == 201

        # Attempt DELETE
        delete_response = await client.delete(f"/v1/catalog/profiles/{profile_id}")

        # Assert response is 409 Conflict
        assert delete_response.status_code == 409

        # Assert error message includes usage count
        error_detail = delete_response.json()["detail"]
        assert "used in 1 listing(s)" in error_detail

        # Verify entity still exists
        list_response = await client.get("/v1/catalog/profiles")
        profile_ids = [p["id"] for p in list_response.json()]
        assert profile_id in profile_ids

    @pytest.mark.asyncio
    async def test_delete_profile_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent profile."""
        non_existent_id = 99999
        delete_response = await client.delete(f"/v1/catalog/profiles/{non_existent_id}")

        assert delete_response.status_code == 404
        error_detail = delete_response.json()["detail"]
        assert "not found" in error_detail

    @pytest.mark.asyncio
    async def test_delete_profile_only_default_conflict(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should prevent deletion of only default profile."""
        # Create single default profile
        profile_payload = {
            "name": "Only Default Profile",
            "weights_json": {"cpu_score": 1.0},
            "is_default": True,
        }
        profile_response = await client.post("/v1/catalog/profiles", json=profile_payload)
        assert profile_response.status_code == 201
        profile_id = profile_response.json()["id"]

        # Attempt DELETE
        delete_response = await client.delete(f"/v1/catalog/profiles/{profile_id}")

        # Assert response is 409 Conflict
        assert delete_response.status_code == 409

        # Assert error message about default profile
        error_detail = delete_response.json()["detail"]
        assert "only default profile" in error_detail

        # Verify entity still exists
        list_response = await client.get("/v1/catalog/profiles")
        profile_ids = [p["id"] for p in list_response.json()]
        assert profile_id in profile_ids

    @pytest.mark.asyncio
    async def test_delete_profile_non_default_with_other_defaults_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should allow deletion of non-default profile when other profiles exist."""
        # Create default profile
        default_profile = await client.post(
            "/v1/catalog/profiles",
            json={
                "name": "Default Profile",
                "weights_json": {"cpu_score": 1.0},
                "is_default": True,
            },
        )
        assert default_profile.status_code == 201

        # Create non-default profile
        non_default_profile = await client.post(
            "/v1/catalog/profiles",
            json={
                "name": "Non-Default Profile",
                "weights_json": {"cpu_score": 1.0},
                "is_default": False,
            },
        )
        assert non_default_profile.status_code == 201
        non_default_id = non_default_profile.json()["id"]

        # Delete non-default profile should succeed
        delete_response = await client.delete(f"/v1/catalog/profiles/{non_default_id}")
        assert delete_response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_profile_default_with_other_defaults_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should allow deletion of default profile when other default exists."""
        # Create first default profile
        profile1 = await client.post(
            "/v1/catalog/profiles",
            json={"name": "Profile 1", "weights_json": {"cpu_score": 1.0}, "is_default": True},
        )
        profile1_id = profile1.json()["id"]

        # Create second default profile (will unset first one)
        profile2 = await client.post(
            "/v1/catalog/profiles",
            json={"name": "Profile 2", "weights_json": {"cpu_score": 1.0}, "is_default": True},
        )
        assert profile2.status_code == 201

        # Delete first profile should succeed (no longer default)
        delete_response = await client.delete(f"/v1/catalog/profiles/{profile1_id}")
        assert delete_response.status_code == 204


# --- PortsProfile DELETE Tests ---


class TestPortsProfileDelete:
    """Tests for DELETE /v1/catalog/ports-profiles/{profile_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_ports_profile_unused_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully delete unused PortsProfile entity."""
        # Create PortsProfile via POST with nested ports
        create_payload = {
            "name": "Test Ports Profile for Deletion",
            "ports": [
                {"type": "USB-A", "count": 4},
                {"type": "HDMI", "count": 1},
            ],
        }
        create_response = await client.post("/v1/catalog/ports-profiles", json=create_payload)
        assert create_response.status_code == 201
        profile_id = create_response.json()["id"]

        # Delete via DELETE
        delete_response = await client.delete(f"/v1/catalog/ports-profiles/{profile_id}")

        # Assert response is 204 No Content
        assert delete_response.status_code == 204

        # Verify entity no longer exists
        list_response = await client.get("/v1/catalog/ports-profiles")
        profile_ids = [p["id"] for p in list_response.json()]
        assert profile_id not in profile_ids

    @pytest.mark.asyncio
    async def test_delete_ports_profile_cascade_ports(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should cascade delete related Port entities."""
        # Create PortsProfile with multiple ports
        create_payload = {
            "name": "Profile with Many Ports",
            "ports": [
                {"type": "USB-A", "count": 6},
                {"type": "USB-C", "count": 2},
                {"type": "HDMI", "count": 2},
                {"type": "DisplayPort", "count": 1},
            ],
        }
        create_response = await client.post("/v1/catalog/ports-profiles", json=create_payload)
        assert create_response.status_code == 201
        profile_id = create_response.json()["id"]
        created_ports = create_response.json()["ports"]
        assert len(created_ports) == 4

        # Delete PortsProfile
        delete_response = await client.delete(f"/v1/catalog/ports-profiles/{profile_id}")
        assert delete_response.status_code == 204

        # Verify Port entities are also deleted (cascade)
        # We can't query Port entities directly, but we can verify by checking
        # that the profile is gone and the database enforces cascade delete
        list_response = await client.get("/v1/catalog/ports-profiles")
        profile_ids = [p["id"] for p in list_response.json()]
        assert profile_id not in profile_ids

    @pytest.mark.asyncio
    async def test_delete_ports_profile_in_use_conflict(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 409 Conflict when PortsProfile is used in listings."""
        # Create PortsProfile
        profile_payload = {
            "name": "Ports Profile In Use",
            "ports": [{"type": "USB-A", "count": 4}],
        }
        profile_response = await client.post("/v1/catalog/ports-profiles", json=profile_payload)
        assert profile_response.status_code == 201
        profile_id = profile_response.json()["id"]

        # Create listing that uses this ports profile
        listing_payload = {
            "title": "Test Ports Listing",
            "url": "https://example.com/test-ports-listing",
            "price_usd": 700.0,
            "ports_profile_id": profile_id,
        }
        listing_response = await client.post("/v1/listings/", json=listing_payload)
        assert listing_response.status_code == 201

        # Attempt DELETE
        delete_response = await client.delete(f"/v1/catalog/ports-profiles/{profile_id}")

        # Assert response is 409 Conflict
        assert delete_response.status_code == 409

        # Assert error message includes usage count
        error_detail = delete_response.json()["detail"]
        assert "used in 1 listing(s)" in error_detail

        # Verify entity still exists
        list_response = await client.get("/v1/catalog/ports-profiles")
        profile_ids = [p["id"] for p in list_response.json()]
        assert profile_id in profile_ids

    @pytest.mark.asyncio
    async def test_delete_ports_profile_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent ports profile."""
        non_existent_id = 99999
        delete_response = await client.delete(f"/v1/catalog/ports-profiles/{non_existent_id}")

        assert delete_response.status_code == 404
        error_detail = delete_response.json()["detail"]
        assert "not found" in error_detail


# --- RamSpec DELETE Tests ---


class TestRamSpecDelete:
    """Tests for DELETE /v1/catalog/ram-specs/{ram_spec_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_ram_spec_unused_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully delete unused RamSpec entity."""
        # Create RamSpec via POST
        create_payload = {
            "ddr_generation": RamGeneration.DDR4.value,
            "speed_mhz": 3200,
            "total_capacity_gb": 16,
        }
        create_response = await client.post("/v1/catalog/ram-specs", json=create_payload)
        assert create_response.status_code == 201
        ram_spec_id = create_response.json()["id"]

        # Delete via DELETE
        delete_response = await client.delete(f"/v1/catalog/ram-specs/{ram_spec_id}")

        # Assert response is 204 No Content
        assert delete_response.status_code == 204

        # Verify entity no longer exists
        get_response = await client.get(f"/v1/catalog/ram-specs/{ram_spec_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_ram_spec_in_use_conflict(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 409 Conflict when RamSpec is used in listings."""
        # Create RamSpec
        ram_spec_payload = {
            "ddr_generation": RamGeneration.DDR5.value,
            "speed_mhz": 5600,
            "total_capacity_gb": 32,
        }
        ram_spec_response = await client.post("/v1/catalog/ram-specs", json=ram_spec_payload)
        assert ram_spec_response.status_code == 201
        ram_spec_id = ram_spec_response.json()["id"]

        # Create listing that uses this RAM spec
        listing_payload = {
            "title": "Test RAM Listing",
            "url": "https://example.com/test-ram-listing",
            "price_usd": 900.0,
            "ram_spec_id": ram_spec_id,
        }
        listing_response = await client.post("/v1/listings/", json=listing_payload)
        assert listing_response.status_code == 201

        # Attempt DELETE
        delete_response = await client.delete(f"/v1/catalog/ram-specs/{ram_spec_id}")

        # Assert response is 409 Conflict
        assert delete_response.status_code == 409

        # Assert error message includes usage count
        error_detail = delete_response.json()["detail"]
        assert "used in 1 listing(s)" in error_detail

        # Verify entity still exists
        get_response = await client.get(f"/v1/catalog/ram-specs/{ram_spec_id}")
        assert get_response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_ram_spec_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent RAM spec."""
        non_existent_id = 99999
        delete_response = await client.delete(f"/v1/catalog/ram-specs/{non_existent_id}")

        assert delete_response.status_code == 404
        error_detail = delete_response.json()["detail"]
        assert "not found" in error_detail


# --- StorageProfile DELETE Tests ---


class TestStorageProfileDelete:
    """Tests for DELETE /v1/catalog/storage-profiles/{storage_profile_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_storage_profile_unused_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully delete unused StorageProfile entity."""
        # Create StorageProfile via POST
        create_payload = {
            "medium": StorageMedium.SATA_SSD.value,
            "interface": "NVMe",
            "capacity_gb": 512,
        }
        create_response = await client.post("/v1/catalog/storage-profiles", json=create_payload)
        assert create_response.status_code == 201
        storage_profile_id = create_response.json()["id"]

        # Delete via DELETE
        delete_response = await client.delete(f"/v1/catalog/storage-profiles/{storage_profile_id}")

        # Assert response is 204 No Content
        assert delete_response.status_code == 204

        # Verify entity no longer exists
        get_response = await client.get(f"/v1/catalog/storage-profiles/{storage_profile_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_storage_profile_in_use_primary_conflict(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 409 Conflict when StorageProfile used as primary storage."""
        # Create StorageProfile
        storage_payload = {
            "medium": StorageMedium.SATA_SSD.value,
            "interface": "NVMe",
            "capacity_gb": 1024,
        }
        storage_response = await client.post("/v1/catalog/storage-profiles", json=storage_payload)
        assert storage_response.status_code == 201
        storage_profile_id = storage_response.json()["id"]

        # Create listing that uses this storage profile as primary
        listing_payload = {
            "title": "Test Primary Storage Listing",
            "url": "https://example.com/test-primary-storage-listing",
            "price_usd": 1000.0,
            "primary_storage_profile_id": storage_profile_id,
        }
        listing_response = await client.post("/v1/listings/", json=listing_payload)
        assert listing_response.status_code == 201

        # Attempt DELETE
        delete_response = await client.delete(f"/v1/catalog/storage-profiles/{storage_profile_id}")

        # Assert response is 409 Conflict
        assert delete_response.status_code == 409

        # Assert error message includes usage count
        error_detail = delete_response.json()["detail"]
        assert "used in 1 listing(s)" in error_detail

        # Verify entity still exists
        get_response = await client.get(f"/v1/catalog/storage-profiles/{storage_profile_id}")
        assert get_response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_storage_profile_in_use_secondary_conflict(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 409 Conflict when StorageProfile used as secondary storage."""
        # Create StorageProfile
        storage_payload = {
            "medium": StorageMedium.HDD.value,
            "interface": "SATA",
            "capacity_gb": 2000,
        }
        storage_response = await client.post("/v1/catalog/storage-profiles", json=storage_payload)
        assert storage_response.status_code == 201
        storage_profile_id = storage_response.json()["id"]

        # Create listing that uses this storage profile as secondary
        listing_payload = {
            "title": "Test Secondary Storage Listing",
            "url": "https://example.com/test-secondary-storage-listing",
            "price_usd": 1200.0,
            "secondary_storage_profile_id": storage_profile_id,
        }
        listing_response = await client.post("/v1/listings/", json=listing_payload)
        assert listing_response.status_code == 201

        # Attempt DELETE
        delete_response = await client.delete(f"/v1/catalog/storage-profiles/{storage_profile_id}")

        # Assert response is 409 Conflict
        assert delete_response.status_code == 409

        # Assert error message includes usage count
        error_detail = delete_response.json()["detail"]
        assert "used in 1 listing(s)" in error_detail

        # Verify entity still exists
        get_response = await client.get(f"/v1/catalog/storage-profiles/{storage_profile_id}")
        assert get_response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_storage_profile_in_use_both_fields_conflict(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should count usage in both primary and secondary storage fields."""
        # Create StorageProfile
        storage_payload = {
            "medium": StorageMedium.SATA_SSD.value,
            "interface": "SATA",
            "capacity_gb": 500,
        }
        storage_response = await client.post("/v1/catalog/storage-profiles", json=storage_payload)
        assert storage_response.status_code == 201
        storage_profile_id = storage_response.json()["id"]

        # Create listing using as primary storage
        listing1_payload = {
            "title": "Primary Storage Listing",
            "url": "https://example.com/primary-storage-listing",
            "price_usd": 800.0,
            "primary_storage_profile_id": storage_profile_id,
        }
        await client.post("/v1/listings/", json=listing1_payload)

        # Create listing using as secondary storage
        listing2_payload = {
            "title": "Secondary Storage Listing",
            "url": "https://example.com/secondary-storage-listing",
            "price_usd": 900.0,
            "secondary_storage_profile_id": storage_profile_id,
        }
        await client.post("/v1/listings/", json=listing2_payload)

        # Attempt DELETE
        delete_response = await client.delete(f"/v1/catalog/storage-profiles/{storage_profile_id}")

        # Assert 409 with count from both fields
        assert delete_response.status_code == 409
        error_detail = delete_response.json()["detail"]
        assert "used in 2 listing(s)" in error_detail

    @pytest.mark.asyncio
    async def test_delete_storage_profile_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent storage profile."""
        non_existent_id = 99999
        delete_response = await client.delete(f"/v1/catalog/storage-profiles/{non_existent_id}")

        assert delete_response.status_code == 404
        error_detail = delete_response.json()["detail"]
        assert "not found" in error_detail


# --- CPU CREATE Tests ---


class TestCpuCreate:
    """Tests for POST /v1/catalog/cpus endpoint."""

    @pytest.mark.asyncio
    async def test_create_cpu_success(self, client: AsyncClient, async_session: AsyncSession):
        """Should successfully create a new CPU."""
        payload = {
            "name": "Intel Core i7-12700K",
            "manufacturer": "Intel",
            "socket": "LGA1700",
            "cores": 12,
            "threads": 20,
            "tdp_w": 125,
            "cpu_mark_multi": 35000,
            "cpu_mark_single": 4000,
            "attributes": {"generation": "12th"},
        }
        response = await client.post("/v1/catalog/cpus", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Intel Core i7-12700K"
        assert data["manufacturer"] == "Intel"
        assert data["cores"] == 12
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_cpu_duplicate_name(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 400 for duplicate CPU name."""
        payload = {"name": "Duplicate CPU", "manufacturer": "Intel"}

        # Create first
        response1 = await client.post("/v1/catalog/cpus", json=payload)
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = await client.post("/v1/catalog/cpus", json=payload)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]


# --- GPU CREATE Tests ---


class TestGpuCreate:
    """Tests for POST /v1/catalog/gpus endpoint."""

    @pytest.mark.asyncio
    async def test_create_gpu_success(self, client: AsyncClient, async_session: AsyncSession):
        """Should successfully create a new GPU."""
        payload = {
            "name": "NVIDIA GeForce RTX 4090",
            "manufacturer": "NVIDIA",
            "gpu_mark": 35000,
            "metal_score": 300000,
            "attributes": {"vram": "24GB"},
        }
        response = await client.post("/v1/catalog/gpus", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "NVIDIA GeForce RTX 4090"
        assert data["gpu_mark"] == 35000
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_gpu_duplicate_name(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 400 for duplicate GPU name."""
        payload = {"name": "Duplicate GPU", "manufacturer": "NVIDIA"}

        response1 = await client.post("/v1/catalog/gpus", json=payload)
        assert response1.status_code == 201

        response2 = await client.post("/v1/catalog/gpus", json=payload)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]


# --- Profile CREATE Tests ---


class TestProfileCreate:
    """Tests for POST /v1/catalog/profiles endpoint."""

    @pytest.mark.asyncio
    async def test_create_profile_success(self, client: AsyncClient, async_session: AsyncSession):
        """Should successfully create a new profile."""
        payload = {
            "name": "Gaming Profile",
            "description": "Optimized for gaming",
            "weights_json": {"cpu_score": 0.4, "gpu_score": 0.6},
            "is_default": False,
        }
        response = await client.post("/v1/catalog/profiles", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Gaming Profile"
        assert data["weights_json"]["gpu_score"] == 0.6
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_profile_duplicate_name(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 400 for duplicate profile name."""
        payload = {"name": "Duplicate Profile", "weights_json": {"cpu_score": 1.0}}

        response1 = await client.post("/v1/catalog/profiles", json=payload)
        assert response1.status_code == 201

        response2 = await client.post("/v1/catalog/profiles", json=payload)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_profile_as_default_unsets_others(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should unset other default profiles when creating new default."""
        # Create first default profile
        payload1 = {"name": "Default 1", "weights_json": {"cpu_score": 1.0}, "is_default": True}
        response1 = await client.post("/v1/catalog/profiles", json=payload1)
        assert response1.status_code == 201
        profile1_id = response1.json()["id"]

        # Create second default profile
        payload2 = {"name": "Default 2", "weights_json": {"cpu_score": 1.0}, "is_default": True}
        response2 = await client.post("/v1/catalog/profiles", json=payload2)
        assert response2.status_code == 201

        # Verify first profile is no longer default
        list_response = await client.get("/v1/catalog/profiles")
        profiles = list_response.json()
        profile1 = next(p for p in profiles if p["id"] == profile1_id)
        assert profile1["is_default"] is False


# --- PortsProfile CREATE Tests ---


class TestPortsProfileCreate:
    """Tests for POST /v1/catalog/ports-profiles endpoint."""

    @pytest.mark.asyncio
    async def test_create_ports_profile_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully create a new ports profile."""
        payload = {
            "name": "Standard Desktop",
            "description": "Standard desktop connectivity",
            "ports": [
                {"type": "USB-A", "count": 6},
                {"type": "USB-C", "count": 2},
                {"type": "HDMI", "count": 1},
            ],
            "attributes": {"category": "desktop"},
        }
        response = await client.post("/v1/catalog/ports-profiles", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Standard Desktop"
        assert len(data["ports"]) == 3
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_ports_profile_duplicate_name(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return 400 for duplicate ports profile name."""
        payload = {"name": "Duplicate Ports", "ports": []}

        response1 = await client.post("/v1/catalog/ports-profiles", json=payload)
        assert response1.status_code == 201

        response2 = await client.post("/v1/catalog/ports-profiles", json=payload)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]


# --- RamSpec CREATE Tests ---


class TestRamSpecCreate:
    """Tests for POST /v1/catalog/ram-specs endpoint."""

    @pytest.mark.asyncio
    async def test_create_ram_spec_success(self, client: AsyncClient, async_session: AsyncSession):
        """Should successfully create a new RAM spec."""
        payload = {
            "label": "32GB DDR5 6000MHz",
            "ddr_generation": RamGeneration.DDR5.value,
            "speed_mhz": 6000,
            "module_count": 2,
            "capacity_per_module_gb": 16,
            "total_capacity_gb": 32,
            "attributes": {"cl": "36"},
        }
        response = await client.post("/v1/catalog/ram-specs", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["total_capacity_gb"] == 32
        assert data["speed_mhz"] == 6000
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_ram_spec_get_or_create_behavior(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return existing RAM spec if duplicate specifications."""
        payload = {
            "ddr_generation": RamGeneration.DDR4.value,
            "speed_mhz": 3200,
            "module_count": 2,
            "capacity_per_module_gb": 8,
            "total_capacity_gb": 16,
        }

        # Create first
        response1 = await client.post("/v1/catalog/ram-specs", json=payload)
        assert response1.status_code == 201
        id1 = response1.json()["id"]

        # Create duplicate should return same entity
        response2 = await client.post("/v1/catalog/ram-specs", json=payload)
        assert response2.status_code == 201
        id2 = response2.json()["id"]

        # Should be the same ID (get_or_create behavior)
        assert id1 == id2


# --- StorageProfile CREATE Tests ---


class TestStorageProfileCreate:
    """Tests for POST /v1/catalog/storage-profiles endpoint."""

    @pytest.mark.asyncio
    async def test_create_storage_profile_success(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should successfully create a new storage profile."""
        payload = {
            "label": "2TB NVMe Gen4",
            "medium": StorageMedium.SATA_SSD.value,
            "interface": "NVMe",
            "form_factor": "M.2",
            "capacity_gb": 2000,
            "performance_tier": "premium",
            "attributes": {"gen": "4"},
        }
        response = await client.post("/v1/catalog/storage-profiles", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["capacity_gb"] == 2000
        assert data["interface"] == "NVMe"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_storage_profile_get_or_create_behavior(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return existing storage profile if duplicate specifications."""
        payload = {
            "medium": StorageMedium.HDD.value,
            "interface": "SATA",
            "form_factor": "3.5-inch",
            "capacity_gb": 4000,
            "performance_tier": "standard",
        }

        response1 = await client.post("/v1/catalog/storage-profiles", json=payload)
        assert response1.status_code == 201
        id1 = response1.json()["id"]

        response2 = await client.post("/v1/catalog/storage-profiles", json=payload)
        assert response2.status_code == 201
        id2 = response2.json()["id"]

        # Should be the same ID (get_or_create behavior)
        assert id1 == id2


# --- CPU READ Tests ---


class TestCpuRead:
    """Tests for GET /v1/catalog/cpus and GET /v1/catalog/cpus/{cpu_id} endpoints."""

    @pytest.mark.asyncio
    async def test_list_cpus(self, client: AsyncClient, async_session: AsyncSession):
        """Should return list of all CPUs."""
        # Create test CPUs
        await client.post("/v1/catalog/cpus", json={"name": "CPU 1", "manufacturer": "Intel"})
        await client.post("/v1/catalog/cpus", json={"name": "CPU 2", "manufacturer": "AMD"})

        # List all CPUs
        response = await client.get("/v1/catalog/cpus")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert all("id" in cpu and "name" in cpu for cpu in data)

    @pytest.mark.asyncio
    async def test_get_cpu_by_id(self, client: AsyncClient, async_session: AsyncSession):
        """Should return specific CPU by ID."""
        create_response = await client.post(
            "/v1/catalog/cpus", json={"name": "Test CPU", "manufacturer": "Intel"}
        )
        cpu_id = create_response.json()["id"]

        response = await client.get(f"/v1/catalog/cpus/{cpu_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == cpu_id
        assert data["name"] == "Test CPU"


# --- GPU READ Tests ---


class TestGpuRead:
    """Tests for GET /v1/catalog/gpus and GET /v1/catalog/gpus/{gpu_id} endpoints."""

    @pytest.mark.asyncio
    async def test_list_gpus(self, client: AsyncClient, async_session: AsyncSession):
        """Should return list of all GPUs."""
        await client.post("/v1/catalog/gpus", json={"name": "GPU 1", "manufacturer": "NVIDIA"})
        await client.post("/v1/catalog/gpus", json={"name": "GPU 2", "manufacturer": "AMD"})

        response = await client.get("/v1/catalog/gpus")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_get_gpu_by_id(self, client: AsyncClient, async_session: AsyncSession):
        """Should return specific GPU by ID."""
        create_response = await client.post(
            "/v1/catalog/gpus", json={"name": "Test GPU", "manufacturer": "NVIDIA"}
        )
        gpu_id = create_response.json()["id"]

        response = await client.get(f"/v1/catalog/gpus/{gpu_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == gpu_id


# --- Profile READ Tests ---


class TestProfileRead:
    """Tests for GET /v1/catalog/profiles endpoints."""

    @pytest.mark.asyncio
    async def test_list_profiles(self, client: AsyncClient, async_session: AsyncSession):
        """Should return list of all profiles."""
        await client.post(
            "/v1/catalog/profiles",
            json={"name": "Profile 1", "weights_json": {"cpu_score": 1.0}},
        )

        response = await client.get("/v1/catalog/profiles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_profile_by_id(self, client: AsyncClient, async_session: AsyncSession):
        """Should return specific profile by ID."""
        create_response = await client.post(
            "/v1/catalog/profiles",
            json={"name": "Test Profile", "weights_json": {"cpu_score": 1.0}},
        )
        profile_id = create_response.json()["id"]

        response = await client.get(f"/v1/catalog/profiles/{profile_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == profile_id
        assert data["name"] == "Test Profile"

    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent profile."""
        response = await client.get("/v1/catalog/profiles/99999")
        assert response.status_code == 404


# --- PortsProfile READ Tests ---


class TestPortsProfileRead:
    """Tests for GET /v1/catalog/ports-profiles endpoints."""

    @pytest.mark.asyncio
    async def test_list_ports_profiles(self, client: AsyncClient, async_session: AsyncSession):
        """Should return list of all ports profiles."""
        await client.post("/v1/catalog/ports-profiles", json={"name": "Ports 1", "ports": []})

        response = await client.get("/v1/catalog/ports-profiles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_ports_profile_by_id(self, client: AsyncClient, async_session: AsyncSession):
        """Should return specific ports profile by ID."""
        create_response = await client.post(
            "/v1/catalog/ports-profiles",
            json={"name": "Test Ports Profile", "ports": [{"type": "USB-A", "count": 4}]},
        )
        profile_id = create_response.json()["id"]

        response = await client.get(f"/v1/catalog/ports-profiles/{profile_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == profile_id
        assert data["name"] == "Test Ports Profile"

    @pytest.mark.asyncio
    async def test_get_ports_profile_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent ports profile."""
        response = await client.get("/v1/catalog/ports-profiles/99999")
        assert response.status_code == 404


# --- RamSpec READ Tests ---


class TestRamSpecRead:
    """Tests for GET /v1/catalog/ram-specs endpoints."""

    @pytest.mark.asyncio
    async def test_list_ram_specs(self, client: AsyncClient, async_session: AsyncSession):
        """Should return list of all RAM specs."""
        await client.post(
            "/v1/catalog/ram-specs",
            json={
                "ddr_generation": RamGeneration.DDR4.value,
                "speed_mhz": 3200,
                "total_capacity_gb": 16,
            },
        )

        response = await client.get("/v1/catalog/ram-specs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_ram_spec_by_id(self, client: AsyncClient, async_session: AsyncSession):
        """Should return specific RAM spec by ID."""
        create_response = await client.post(
            "/v1/catalog/ram-specs",
            json={
                "ddr_generation": RamGeneration.DDR5.value,
                "speed_mhz": 5600,
                "total_capacity_gb": 32,
            },
        )
        ram_spec_id = create_response.json()["id"]

        response = await client.get(f"/v1/catalog/ram-specs/{ram_spec_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ram_spec_id
        assert data["total_capacity_gb"] == 32

    @pytest.mark.asyncio
    async def test_get_ram_spec_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent RAM spec."""
        response = await client.get("/v1/catalog/ram-specs/99999")
        assert response.status_code == 404


# --- StorageProfile READ Tests ---


class TestStorageProfileRead:
    """Tests for GET /v1/catalog/storage-profiles endpoints."""

    @pytest.mark.asyncio
    async def test_list_storage_profiles(self, client: AsyncClient, async_session: AsyncSession):
        """Should return list of all storage profiles."""
        await client.post(
            "/v1/catalog/storage-profiles",
            json={"medium": StorageMedium.SATA_SSD.value, "interface": "SATA", "capacity_gb": 512},
        )

        response = await client.get("/v1/catalog/storage-profiles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_storage_profile_by_id(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return specific storage profile by ID."""
        create_response = await client.post(
            "/v1/catalog/storage-profiles",
            json={
                "medium": StorageMedium.SATA_SSD.value,
                "interface": "NVMe",
                "capacity_gb": 1024,
            },
        )
        storage_profile_id = create_response.json()["id"]

        response = await client.get(f"/v1/catalog/storage-profiles/{storage_profile_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == storage_profile_id
        assert data["capacity_gb"] == 1024

    @pytest.mark.asyncio
    async def test_get_storage_profile_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent storage profile."""
        response = await client.get("/v1/catalog/storage-profiles/99999")
        assert response.status_code == 404


# --- "Used In" Endpoint Tests ---


class TestCpuListings:
    """Tests for GET /v1/catalog/cpus/{cpu_id}/listings endpoint."""

    @pytest.mark.asyncio
    async def test_get_cpu_listings(self, client: AsyncClient, async_session: AsyncSession):
        """Should return all listings that use this CPU."""
        # Create CPU
        cpu_response = await client.post(
            "/v1/catalog/cpus", json={"name": "Test CPU for Listings", "manufacturer": "Intel"}
        )
        cpu_id = cpu_response.json()["id"]

        # Create listings using this CPU
        for i in range(3):
            await client.post(
                "/v1/listings/",
                json={
                    "title": f"Listing {i}",
                    "url": f"https://example.com/listing-{i}",
                    "price_usd": 500.0 + i * 100,
                    "cpu_id": cpu_id,
                },
            )

        # Get listings
        response = await client.get(f"/v1/catalog/cpus/{cpu_id}/listings")
        assert response.status_code == 200
        listings = response.json()
        assert len(listings) == 3

    @pytest.mark.asyncio
    async def test_get_cpu_listings_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent CPU."""
        response = await client.get("/v1/catalog/cpus/99999/listings")
        assert response.status_code == 404


class TestGpuListings:
    """Tests for GET /v1/catalog/gpus/{gpu_id}/listings endpoint."""

    @pytest.mark.asyncio
    async def test_get_gpu_listings(self, client: AsyncClient, async_session: AsyncSession):
        """Should return all listings that use this GPU."""
        # Create GPU
        gpu_response = await client.post(
            "/v1/catalog/gpus", json={"name": "Test GPU for Listings", "manufacturer": "NVIDIA"}
        )
        gpu_id = gpu_response.json()["id"]

        # Create listings using this GPU
        for i in range(2):
            await client.post(
                "/v1/listings/",
                json={
                    "title": f"GPU Listing {i}",
                    "url": f"https://example.com/gpu-listing-{i}",
                    "price_usd": 800.0 + i * 100,
                    "gpu_id": gpu_id,
                },
            )

        # Get listings
        response = await client.get(f"/v1/catalog/gpus/{gpu_id}/listings")
        assert response.status_code == 200
        listings = response.json()
        assert len(listings) == 2

    @pytest.mark.asyncio
    async def test_get_gpu_listings_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent GPU."""
        response = await client.get("/v1/catalog/gpus/99999/listings")
        assert response.status_code == 404


class TestRamSpecListings:
    """Tests for GET /v1/catalog/ram-specs/{ram_spec_id}/listings endpoint."""

    @pytest.mark.asyncio
    async def test_get_ram_spec_listings(self, client: AsyncClient, async_session: AsyncSession):
        """Should return all listings that use this RAM spec."""
        # Create RAM spec
        ram_spec_response = await client.post(
            "/v1/catalog/ram-specs",
            json={
                "ddr_generation": RamGeneration.DDR4.value,
                "speed_mhz": 3200,
                "total_capacity_gb": 16,
            },
        )
        ram_spec_id = ram_spec_response.json()["id"]

        # Create listings using this RAM spec
        for i in range(2):
            await client.post(
                "/v1/listings/",
                json={
                    "title": f"RAM Listing {i}",
                    "url": f"https://example.com/ram-listing-{i}",
                    "price_usd": 600.0 + i * 100,
                    "ram_spec_id": ram_spec_id,
                },
            )

        # Get listings
        response = await client.get(f"/v1/catalog/ram-specs/{ram_spec_id}/listings")
        assert response.status_code == 200
        listings = response.json()
        assert len(listings) == 2

    @pytest.mark.asyncio
    async def test_get_ram_spec_listings_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent RAM spec."""
        response = await client.get("/v1/catalog/ram-specs/99999/listings")
        assert response.status_code == 404


class TestStorageProfileListings:
    """Tests for GET /v1/catalog/storage-profiles/{storage_profile_id}/listings endpoint."""

    @pytest.mark.asyncio
    async def test_get_storage_profile_listings_primary(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return listings that use this storage profile as primary."""
        # Create storage profile
        storage_response = await client.post(
            "/v1/catalog/storage-profiles",
            json={"medium": StorageMedium.SATA_SSD.value, "interface": "NVMe", "capacity_gb": 512},
        )
        storage_profile_id = storage_response.json()["id"]

        # Create listings using this as primary storage
        await client.post(
            "/v1/listings/",
            json={
                "title": "Primary Storage Listing",
                "url": "https://example.com/primary-storage-listing",
                "price_usd": 900.0,
                "primary_storage_profile_id": storage_profile_id,
            },
        )

        # Get listings
        response = await client.get(f"/v1/catalog/storage-profiles/{storage_profile_id}/listings")
        assert response.status_code == 200
        listings = response.json()
        assert len(listings) >= 1

    @pytest.mark.asyncio
    async def test_get_storage_profile_listings_secondary(
        self, client: AsyncClient, async_session: AsyncSession
    ):
        """Should return listings that use this storage profile as secondary."""
        # Create storage profile
        storage_response = await client.post(
            "/v1/catalog/storage-profiles",
            json={"medium": StorageMedium.HDD.value, "interface": "SATA", "capacity_gb": 2000},
        )
        storage_profile_id = storage_response.json()["id"]

        # Create listings using this as secondary storage
        await client.post(
            "/v1/listings/",
            json={
                "title": "Secondary Storage Listing",
                "url": "https://example.com/secondary-storage-listing",
                "price_usd": 1000.0,
                "secondary_storage_profile_id": storage_profile_id,
            },
        )

        # Get listings
        response = await client.get(f"/v1/catalog/storage-profiles/{storage_profile_id}/listings")
        assert response.status_code == 200
        listings = response.json()
        assert len(listings) >= 1

    @pytest.mark.asyncio
    async def test_get_storage_profile_listings_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent storage profile."""
        response = await client.get("/v1/catalog/storage-profiles/99999/listings")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
