---
title: "Deal Builder - Phase 4: API Layer Integration"
description: "FastAPI router design, endpoint contracts, request/response schemas, and integration with frontend. Covers all v1/builder/* endpoints with error handling and validation."
audience: [ai-agents, developers]
tags: [implementation, api, fastapi, endpoints, integration, phase-4]
created: 2025-11-12
updated: 2025-11-12
category: "product-planning"
status: draft
related:
  - /home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1.md
  - /home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1/phase-1-3-backend-database.md
---

# Phase 4: API Layer Integration

## Overview

Phase 4 implements the FastAPI router with all endpoints for frontend integration. This is the integration layer between backend services and frontend UI.

**Timeline**: Days 7-9 (approximately 1.5 weeks after Phase 3 starts)
**Effort**: 5 story points
**Agents**: backend-typescript-architect, python-backend-engineer

**Key Principle**: All endpoints must be tested to <300ms response time and provide consistent error handling.

---

## Task 4.1: Define API Request/Response Schemas

**Assigned to**: backend-typescript-architect

**Description**: Create Pydantic models for all request/response payloads.

**Technical Details**:

```python
# apps/api/dealbrain_api/schemas/builder.py (NEW FILE)

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum


class VisibilityEnum(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    UNLISTED = "unlisted"


# Request Schemas

class BuildComponentsRequest(BaseModel):
    """Components for build calculation."""
    cpu_id: Optional[int] = None
    gpu_id: Optional[int] = None
    ram_spec_id: Optional[int] = None
    primary_storage_profile_id: Optional[int] = None
    secondary_storage_profile_id: Optional[int] = None

    class Config:
        schema_extra = {
            "example": {
                "cpu_id": 1,
                "ram_spec_id": 5,
                "primary_storage_profile_id": 3,
            }
        }


class CalculateBuildRequest(BaseModel):
    """Request to calculate build valuation."""
    components: BuildComponentsRequest

    class Config:
        schema_extra = {
            "example": {
                "components": {
                    "cpu_id": 1,
                    "ram_spec_id": 5,
                }
            }
        }


class SaveBuildRequest(BaseModel):
    """Request to save a build."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = Field(default_factory=list)
    visibility: VisibilityEnum = VisibilityEnum.PRIVATE
    components: BuildComponentsRequest
    pricing: Dict[str, Any]
    metrics: Dict[str, Any]
    valuation_breakdown: Dict[str, Any]

    class Config:
        schema_extra = {
            "example": {
                "name": "Budget Gaming PC",
                "description": "1080p gaming build",
                "tags": ["gaming", "budget"],
                "visibility": "public",
                "components": {"cpu_id": 1},
                "pricing": {
                    "base_price": 500,
                    "adjusted_price": 450,
                    "component_prices": {"cpu": 189},
                },
                "metrics": {
                    "dollar_per_cpu_mark_multi": 0.042,
                },
                "valuation_breakdown": {},
            }
        }


class UpdateBuildRequest(BaseModel):
    """Request to update a build."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = None
    visibility: Optional[VisibilityEnum] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Gaming PC",
                "visibility": "public",
            }
        }


# Response Schemas

class PricingResponse(BaseModel):
    """Pricing snapshot."""
    base_price: float
    adjusted_price: float
    component_prices: Dict[str, float]


class MetricsResponse(BaseModel):
    """Performance metrics snapshot."""
    dollar_per_cpu_mark_multi: Optional[float] = None
    dollar_per_cpu_mark_single: Optional[float] = None
    composite_score: Optional[float] = None


class BuildCalculationResponse(BaseModel):
    """Response from build calculation."""
    pricing: PricingResponse
    metrics: MetricsResponse
    valuation_breakdown: Dict[str, Any]

    class Config:
        schema_extra = {
            "example": {
                "pricing": {
                    "base_price": 500,
                    "adjusted_price": 450,
                    "component_prices": {"cpu": 189},
                },
                "metrics": {
                    "dollar_per_cpu_mark_multi": 0.042,
                    "composite_score": 87.5,
                },
                "valuation_breakdown": {},
            }
        }


class SavedBuildResponse(BaseModel):
    """Response for a saved build."""
    id: int
    name: str
    description: Optional[str] = None
    tags: List[str]
    visibility: VisibilityEnum
    share_token: str
    components: BuildComponentsRequest
    pricing: PricingResponse
    metrics: MetricsResponse
    valuation_breakdown: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Budget Gaming PC",
                "tags": ["gaming", "budget"],
                "visibility": "public",
                "share_token": "abc123def456",
                "components": {"cpu_id": 1},
                "pricing": {
                    "base_price": 500,
                    "adjusted_price": 450,
                    "component_prices": {"cpu": 189},
                },
                "metrics": {
                    "dollar_per_cpu_mark_multi": 0.042,
                },
                "valuation_breakdown": {},
                "created_at": "2025-11-12T10:00:00Z",
                "updated_at": "2025-11-12T10:00:00Z",
            }
        }


class PaginatedBuildsResponse(BaseModel):
    """Paginated response for builds list."""
    items: List[SavedBuildResponse]
    total: int
    limit: int
    offset: int

    @property
    def page(self) -> int:
        return self.offset // self.limit + 1 if self.limit > 0 else 1


class ComparisonListingResponse(BaseModel):
    """Similar listing for comparison."""
    id: int
    title: str
    price_usd: float
    adjusted_price_usd: float
    cpu_name: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    difference_percent: float  # Difference from build


class BuildComparisonResponse(BaseModel):
    """Response for build comparison."""
    similar_listings: List[ComparisonListingResponse]
    insights: List[str]


class ErrorResponse(BaseModel):
    """Standard error response."""
    status: int
    detail: str
    type: str = "error"
```

**Acceptance Criteria**:
- All schemas have proper validation (min/max length, required fields)
- Examples provided for all request/response types
- from_attributes = True for ORM model conversion
- Schemas match API documentation expectations
- Enum types used for restricted values (visibility)
- Pydantic v2 compatible syntax

**Files Created**:
- `apps/api/dealbrain_api/schemas/builder.py`

**Effort**: 1 story point

---

## Task 4.2: Implement Builder Router Endpoints

**Assigned to**: python-backend-engineer

**Description**: Create FastAPI router with all endpoints under `/v1/builder/`.

**Technical Details**:

```python
# apps/api/dealbrain_api/api/builder.py (NEW FILE)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..db import get_db
from ..services.builder import BuilderService
from ..schemas.builder import (
    CalculateBuildRequest,
    BuildCalculationResponse,
    SaveBuildRequest,
    SavedBuildResponse,
    UpdateBuildRequest,
    PaginatedBuildsResponse,
    BuildComparisonResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/v1/builder", tags=["builder"])


@router.post("/calculate", response_model=BuildCalculationResponse)
async def calculate_build(
    request: CalculateBuildRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate valuation and metrics for a build configuration.

    - **cpu_id**: CPU component ID (optional)
    - **gpu_id**: GPU component ID (optional)
    - **ram_spec_id**: RAM specification ID (optional)

    Returns pricing, metrics, and valuation breakdown.
    """
    try:
        service = BuilderService(db)
        result = await service.calculate_build_valuation(
            components=request.components.dict(exclude_none=True)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Calculation failed")


@router.post("/builds", response_model=SavedBuildResponse, status_code=201)
async def save_build(
    request: SaveBuildRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Save a build configuration.

    Captures pricing, metrics, and valuation at save time.
    Returns the saved build with share_token for sharing.
    """
    try:
        service = BuilderService(db)
        build = await service.save_build(
            name=request.name,
            description=request.description,
            tags=request.tags,
            visibility=request.visibility.value,
            components=request.components.dict(exclude_none=True),
            pricing=request.pricing,
            metrics=request.metrics,
            valuation_breakdown=request.valuation_breakdown,
            user_id=None,  # TODO: Get from auth context
        )
        return build
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save build")


@router.get("/builds", response_model=PaginatedBuildsResponse)
async def list_user_builds(
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List builds for a user or public builds.

    - **user_id**: Filter by user (optional)
    - **limit**: Items per page (1-100, default 50)
    - **offset**: Pagination offset (default 0)
    """
    try:
        service = BuilderService(db)

        if user_id:
            items, total = await service.list_user_builds(user_id, limit, offset)
        else:
            items, total = await service.list_public_builds(limit, offset)

        return PaginatedBuildsResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch builds")


@router.get("/builds/{build_id}", response_model=SavedBuildResponse)
async def get_build(
    build_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific build by ID.

    Access control: User can access own builds and public builds.
    """
    try:
        service = BuilderService(db)
        build = await service.get_build(build_id)

        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        # TODO: Verify user has access (owner or public)

        return build
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch build")


@router.get("/builds/shared/{share_token}", response_model=SavedBuildResponse)
async def get_shared_build(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a build by share token.

    No authentication required - used for shareable URLs.
    """
    try:
        service = BuilderService(db)
        build = await service.get_build_by_share_token(share_token)

        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        return build
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch build")


@router.patch("/builds/{build_id}", response_model=SavedBuildResponse)
async def update_build(
    build_id: int,
    request: UpdateBuildRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a build's metadata.

    Can only update: name, description, tags, visibility.
    Component and pricing snapshots cannot be changed.
    """
    try:
        service = BuilderService(db)

        # Verify build exists
        build = await service.get_build(build_id)
        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        # TODO: Verify user owns build

        # Update fields
        updated = await service.update_build(
            build_id=build_id,
            name=request.name,
            description=request.description,
            tags=request.tags,
            visibility=request.visibility.value if request.visibility else None,
        )

        if not updated:
            raise HTTPException(status_code=404, detail="Build not found")

        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update build")


@router.delete("/builds/{build_id}", status_code=204)
async def delete_build(
    build_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a build (soft delete).

    Only the build owner can delete.
    """
    try:
        service = BuilderService(db)

        # Verify build exists
        build = await service.get_build(build_id)
        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        # TODO: Verify user owns build

        # Delete
        deleted = await service.delete_build(build_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Build not found")

        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete build")


@router.get("/compare", response_model=BuildComparisonResponse)
async def compare_build(
    cpu_id: int = Query(..., description="CPU component ID"),
    ram_gb: Optional[int] = Query(None, description="RAM in GB (±8GB variance)"),
    storage_gb: Optional[int] = Query(None, description="Storage in GB (±256GB variance)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare a build to similar listings in the database.

    Returns similar pre-built systems with price comparison.
    """
    try:
        service = BuilderService(db)
        comparison = await service.compare_build_to_listings(
            cpu_id=cpu_id,
            ram_gb=ram_gb,
            storage_gb=storage_gb,
        )
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch comparisons")
```

**Acceptance Criteria**:
- All endpoints return correct status codes (201 for POST, 204 for DELETE, etc.)
- Request validation working (required fields, type checking)
- Response schemas match specifications
- Error handling consistent (400 for bad input, 404 for not found, 500 for errors)
- Docstrings complete with parameter descriptions
- Response times <300ms measured (use timing middleware)
- CORS headers correct for frontend origin

**Files Created**:
- `apps/api/dealbrain_api/api/builder.py`

**Effort**: 2 story points

---

## Task 4.3: Register Router in FastAPI App

**Assigned to**: python-backend-engineer

**Description**: Register BuilderRouter in main FastAPI application.

**Technical Details**:

```python
# apps/api/dealbrain_api/main.py (MODIFY)

from fastapi import FastAPI
from .api import builder

app = FastAPI()

# ... existing routes ...

# Register builder router
app.include_router(builder.router)
```

**Acceptance Criteria**:
- Router registered in correct location in app initialization
- No import conflicts
- Endpoints accessible at `/v1/builder/*`
- All routes in OpenAPI docs

**Effort**: 0.5 story points

---

## Task 4.4: Implement API Tests

**Assigned to**: python-backend-engineer

**Description**: Comprehensive API endpoint tests using FastAPI TestClient.

**Technical Details**:

```python
# tests/test_builder_api.py

import pytest
from fastapi.testclient import TestClient
from dealbrain_api.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_calculate_build_endpoint(client):
    """Test POST /v1/builder/calculate endpoint."""
    response = client.post(
        "/v1/builder/calculate",
        json={
            "components": {
                "cpu_id": 1,
                "ram_spec_id": 1,
            }
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "pricing" in data
    assert "metrics" in data
    assert "valuation_breakdown" in data
    assert data["pricing"]["base_price"] > 0
    assert data["pricing"]["adjusted_price"] > 0


@pytest.mark.asyncio
async def test_save_build_endpoint(client):
    """Test POST /v1/builder/builds endpoint."""
    response = client.post(
        "/v1/builder/builds",
        json={
            "name": "Test Build",
            "description": "A test build",
            "tags": ["test", "gaming"],
            "visibility": "public",
            "components": {"cpu_id": 1},
            "pricing": {
                "base_price": 500,
                "adjusted_price": 450,
                "component_prices": {"cpu": 189},
            },
            "metrics": {
                "dollar_per_cpu_mark_multi": 0.042,
            },
            "valuation_breakdown": {},
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["name"] == "Test Build"
    assert data["share_token"] is not None
    assert len(data["share_token"]) > 20


@pytest.mark.asyncio
async def test_get_builds_endpoint(client):
    """Test GET /v1/builder/builds endpoint."""
    response = client.get("/v1/builder/builds?limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


@pytest.mark.asyncio
async def test_get_shared_build_endpoint(client):
    """Test GET /v1/builder/builds/shared/{token} endpoint."""
    # First create a build
    create_response = client.post(
        "/v1/builder/builds",
        json={
            "name": "Shared Build",
            "visibility": "public",
            "components": {"cpu_id": 1},
            "pricing": {
                "base_price": 500,
                "adjusted_price": 450,
                "component_prices": {"cpu": 189},
            },
            "metrics": {},
            "valuation_breakdown": {},
        },
    )

    build_data = create_response.json()
    share_token = build_data["share_token"]

    # Now get by share token
    response = client.get(f"/v1/builder/builds/shared/{share_token}")

    assert response.status_code == 200
    data = response.json()
    assert data["share_token"] == share_token


@pytest.mark.asyncio
async def test_error_handling(client):
    """Test error handling in endpoints."""
    # Missing required field
    response = client.post(
        "/v1/builder/builds",
        json={
            "description": "Missing name",
            "visibility": "public",
            "components": {},
            "pricing": {},
            "metrics": {},
            "valuation_breakdown": {},
        },
    )

    assert response.status_code == 422  # Validation error

    # Invalid component ID
    response = client.post(
        "/v1/builder/calculate",
        json={
            "components": {
                "cpu_id": 999999,  # Non-existent
            }
        },
    )

    # Should return 400 with error message
    assert response.status_code in [400, 500]
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_update_build_endpoint(client):
    """Test PATCH /v1/builder/builds/{id} endpoint."""
    # Create a build
    create_response = client.post(
        "/v1/builder/builds",
        json={
            "name": "Original Name",
            "visibility": "public",
            "components": {"cpu_id": 1},
            "pricing": {
                "base_price": 500,
                "adjusted_price": 450,
                "component_prices": {"cpu": 189},
            },
            "metrics": {},
            "valuation_breakdown": {},
        },
    )

    build_data = create_response.json()
    build_id = build_data["id"]

    # Update it
    response = client.patch(
        f"/v1/builder/builds/{build_id}",
        json={
            "name": "Updated Name",
            "visibility": "private",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["visibility"] == "private"


@pytest.mark.asyncio
async def test_delete_build_endpoint(client):
    """Test DELETE /v1/builder/builds/{id} endpoint."""
    # Create a build
    create_response = client.post(
        "/v1/builder/builds",
        json={
            "name": "To Delete",
            "visibility": "public",
            "components": {},
            "pricing": {
                "base_price": 500,
                "adjusted_price": 450,
                "component_prices": {},
            },
            "metrics": {},
            "valuation_breakdown": {},
        },
    )

    build_data = create_response.json()
    build_id = build_data["id"]

    # Delete it
    response = client.delete(f"/v1/builder/builds/{build_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/v1/builder/builds/{build_id}")
    assert response.status_code == 404
```

**Acceptance Criteria**:
- All endpoints tested (happy path + error cases)
- Status codes correct for all scenarios
- Response payloads match schemas
- Error handling tested (validation, not found, server errors)
- Test coverage >85% for router

**Files Created**:
- `tests/test_builder_api.py`

**Effort**: 1.5 story points

---

## Task 4.5: Performance Testing & Optimization

**Assigned to**: backend-typescript-architect

**Description**: Verify endpoint response times <300ms and optimize as needed.

**Technical Details**:

**Performance Test Script**:
```python
# scripts/test_builder_performance.py

import asyncio
import time
import httpx
from concurrent.futures import ThreadPoolExecutor

async def test_endpoint_performance():
    """Load test builder endpoints."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Test calculate endpoint
        times = []
        for i in range(100):
            start = time.perf_counter()
            response = await client.post(
                "/v1/builder/calculate",
                json={
                    "components": {
                        "cpu_id": 1,
                        "ram_spec_id": 1,
                    }
                },
            )
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # Convert to ms

        print(f"Calculate endpoint performance:")
        print(f"  Min: {min(times):.1f}ms")
        print(f"  Max: {max(times):.1f}ms")
        print(f"  Avg: {sum(times)/len(times):.1f}ms")
        print(f"  P95: {sorted(times)[int(len(times)*0.95)]:.1f}ms")
        print(f"  P99: {sorted(times)[int(len(times)*0.99)]:.1f}ms")

        # Verify all under 300ms
        slow_requests = [t for t in times if t > 300]
        if slow_requests:
            print(f"  ⚠️  {len(slow_requests)} requests exceeded 300ms!")
        else:
            print(f"  ✓ All requests under 300ms")
```

**Optimization Checklist**:
- [ ] Verify database queries are optimized (no N+1)
- [ ] Add database query caching if needed
- [ ] Profile calculate_build_valuation method
- [ ] Verify relationships use eager loading
- [ ] Test with 1000+ saved builds in database
- [ ] Verify pagination works correctly at scale
- [ ] Monitor memory usage during load test

**Acceptance Criteria**:
- All endpoints respond <300ms average
- P95 latency <400ms, P99 <500ms
- No database query timeouts
- Memory usage stable during load
- No connection leaks
- Database indexes effective

**Effort**: 1 story point

---

## Summary: Phase 4 Deliverables

| Artifact | File | Status |
|----------|------|--------|
| API Schemas | `apps/api/dealbrain_api/schemas/builder.py` | Ready |
| Router/Endpoints | `apps/api/dealbrain_api/api/builder.py` | Ready |
| Router Registration | `apps/api/dealbrain_api/main.py` | Update needed |
| API Tests | `tests/test_builder_api.py` | Ready |
| Performance Tests | `scripts/test_builder_performance.py` | Ready |

## API Endpoint Summary

| Method | Endpoint | Purpose | Response Time |
|--------|----------|---------|---|
| POST | `/v1/builder/calculate` | Calculate valuation | <300ms |
| POST | `/v1/builder/builds` | Save build | <500ms |
| GET | `/v1/builder/builds` | List builds | <500ms |
| GET | `/v1/builder/builds/{id}` | Get build | <100ms |
| GET | `/v1/builder/builds/shared/{token}` | Get shared build | <100ms |
| PATCH | `/v1/builder/builds/{id}` | Update build | <200ms |
| DELETE | `/v1/builder/builds/{id}` | Delete build | <200ms |
| GET | `/v1/builder/compare` | Compare to listings | <500ms |

## Quality Gates for Phase 4 Completion

Before proceeding to Phase 5 (Frontend):

- [ ] All endpoints implemented and accessible
- [ ] Request validation working (422 for bad input)
- [ ] Response schemas match specifications
- [ ] All tests passing (>85% coverage)
- [ ] Performance benchmarks met (<300ms for calculate)
- [ ] Error handling consistent and documented
- [ ] CORS headers correct for frontend
- [ ] OpenAPI documentation generated correctly
- [ ] Integration tests with Phase 1-3 backends passing

---

**Total Effort**: 5 story points
**Timeline**: Days 7-9 (~1.5 weeks after Phase 3 starts)
**Agents**: backend-typescript-architect (1.5pts), python-backend-engineer (3.5pts)

Next phase: [Phase 5-7: Frontend Components & Features](./phase-5-7-frontend.md)
