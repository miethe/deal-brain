---
title: "Phase 2 Test Suite Summary"
description: "Comprehensive testing coverage for Phase 2a (Sharing), 2b (Card Generation), and 2c (Export/Import)"
audience: [developers, qa, ai-agents]
tags: [testing, phase-2, coverage, pytest]
created: 2025-11-19
updated: 2025-11-19
category: "test-documentation"
status: published
related:
  - /home/user/deal-brain/PHASE_2A_IMPLEMENTATION_SUMMARY.md
  - /home/user/deal-brain/tests/services/test_image_generation.py
  - /home/user/deal-brain/tests/test_export_import_schemas.py
---

# Phase 2 Comprehensive Test Suite

This document summarizes the comprehensive test suites created for all Phase 2 features.

## Test Coverage Overview

### Phase 2a: Collections Sharing
**Target Coverage:** >85%

**Test Files:**
1. `/home/user/deal-brain/tests/repositories/test_collection_share_token_repository.py` (NEW)
   - Token generation with secure random values
   - Token validation with expiry checks
   - View count tracking (atomic updates)
   - Token expiration (soft-delete)
   - Eager loading of collections and items
   - Pagination and query optimization
   - **Tests:** 15+ test methods

2. `/home/user/deal-brain/tests/services/test_collections_sharing.py` (NEW)
   - Visibility updates with telemetry
   - Public collection access (no auth)
   - Access control checks (RLS)
   - Collection copying with items
   - Public collection listing with pagination
   - Search with filters (name, description)
   - Share token generation and validation
   - **Tests:** 25+ test methods

**Existing Tests (Already Created):**
- `/home/user/deal-brain/tests/repositories/test_collection_repository.py`
- `/home/user/deal-brain/tests/services/test_collections_service.py`

### Phase 2b: Card Generation
**Target Coverage:** >85%

**Test Files:**
1. `/home/user/deal-brain/tests/services/test_image_generation.py` (EXISTING)
   - Browser pool management
   - Card rendering with Playwright
   - Cache management (S3)
   - Valuation tier calculation
   - Placeholder generation
   - Template rendering
   - **Tests:** 15+ test methods

2. `/home/user/deal-brain/tests/api/test_card_generation_api.py` (NEW)
   - GET /listings/{id}/card-image endpoint
   - Parameter validation (style, size, format)
   - Caching headers (Cache-Control, ETag)
   - Content-Type headers
   - Error responses (404, 400, 500)
   - Cache invalidation on listing updates
   - **Tests:** 15+ test methods

### Phase 2c: Export/Import
**Target Coverage:** >85%

**Test Files:**
1. `/home/user/deal-brain/tests/test_export_import_schemas.py` (EXISTING)
   - Schema validation for v1.0.0
   - Component schema validation
   - Deal export validation
   - Collection export validation
   - Sample file validation
   - Edge cases and backward compatibility
   - **Tests:** 25+ test methods

2. `/home/user/deal-brain/tests/services/test_export_import_service.py` (NEW)
   - Deal export with all relationships
   - Deal import with validation
   - Duplicate detection (listings, collections)
   - Collection export with items
   - Collection import with merge strategies
   - Schema version validation
   - Preview system with TTL
   - **Tests:** 20+ test methods

3. `/home/user/deal-brain/tests/e2e/test_export_import_e2e.py` (NEW)
   - Export → Import → Verify round-trip
   - Collection export/import with items
   - Share → Copy → Export workflow
   - Import validation and error handling
   - Performance tests (large collections)
   - **Tests:** 12+ test methods

## Test Organization

### Repository Tests
**Location:** `/home/user/deal-brain/tests/repositories/`

**Purpose:** Test data access layer in isolation
- Database operations (CRUD)
- Query optimization and eager loading
- Pagination and filtering
- Access control at DB level

**Pattern:**
```python
@pytest.mark.asyncio
class TestRepositoryMethod:
    async def test_success_case(self, repository, session):
        # Arrange
        # Act
        # Assert
        pass

    async def test_error_case(self, repository, session):
        # Arrange
        # Act
        # Assert
        pass
```

### Service Tests
**Location:** `/home/user/deal-brain/tests/services/`

**Purpose:** Test business logic layer
- Service orchestration
- Validation and authorization
- Telemetry and logging
- Integration with repositories

**Pattern:**
```python
@pytest.mark.asyncio
class TestServiceMethod:
    async def test_success_with_mocks(self, service, session):
        with patch.object(service, "_emit_event") as mock_emit:
            # Arrange
            # Act
            result = await service.method()
            # Assert
            mock_emit.assert_called_once()
```

### API Tests
**Location:** `/home/user/deal-brain/tests/api/`

**Purpose:** Test REST API endpoints
- Request/response validation
- HTTP status codes
- Authentication/authorization
- Error handling
- Headers (caching, content-type)

**Pattern:**
```python
@pytest.mark.asyncio
async def test_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/endpoint")
        assert response.status_code == 200
```

### E2E Tests
**Location:** `/home/user/deal-brain/tests/e2e/`

**Purpose:** Test complete workflows
- Multi-service interactions
- Data integrity across operations
- Critical user paths
- Performance under load

**Pattern:**
```python
@pytest.mark.asyncio
async def test_complete_workflow(services, session, users):
    # Step 1: Create resource
    # Step 2: Share resource
    # Step 3: Copy resource
    # Step 4: Export resource
    # Step 5: Verify fidelity
```

## Test Fixtures

### Common Fixtures

**Database Session:**
```python
@pytest_asyncio.fixture
async def session():
    """Create in-memory async SQLite session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
```

**Sample Data:**
```python
@pytest_asyncio.fixture
async def sample_user(session):
    user = User(username="testuser", email="test@example.com")
    session.add(user)
    await session.flush()
    return user

@pytest_asyncio.fixture
async def sample_listing(session, sample_cpu):
    listing = Listing(title="Test PC", price_usd=100.0, cpu_id=sample_cpu.id)
    session.add(listing)
    await session.flush()
    return listing
```

## Running Tests

### Run All Phase 2 Tests
```bash
# Run all new Phase 2 tests
pytest tests/repositories/test_collection_share_token_repository.py -v
pytest tests/services/test_collections_sharing.py -v
pytest tests/services/test_export_import_service.py -v
pytest tests/api/test_card_generation_api.py -v
pytest tests/e2e/test_export_import_e2e.py -v

# Run all existing Phase 2 tests
pytest tests/services/test_image_generation.py -v
pytest tests/test_export_import_schemas.py -v
```

### Run with Coverage
```bash
# Generate coverage report for Phase 2 features
pytest \
  tests/repositories/test_collection_share_token_repository.py \
  tests/services/test_collections_sharing.py \
  tests/services/test_export_import_service.py \
  tests/api/test_card_generation_api.py \
  tests/e2e/test_export_import_e2e.py \
  --cov=apps/api/dealbrain_api/repositories/collection_share_token_repository \
  --cov=apps/api/dealbrain_api/services/collections_service \
  --cov=apps/api/dealbrain_api/services/export_import \
  --cov=apps/api/dealbrain_api/services/image_generation \
  --cov-report=html \
  --cov-report=term-missing
```

### Run Specific Test Classes
```bash
# Run only visibility tests
pytest tests/services/test_collections_sharing.py::TestUpdateVisibility -v

# Run only export tests
pytest tests/services/test_export_import_service.py::TestExportListing -v

# Run only E2E tests
pytest tests/e2e/test_export_import_e2e.py -v
```

### Run Tests in Parallel
```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/ -n 4
```

## Test Metrics

### Coverage Targets

| Component | Target | Files |
|-----------|--------|-------|
| CollectionShareTokenRepository | >85% | 1 file |
| CollectionsService (sharing features) | >85% | 1 file |
| ExportImportService | >85% | 1 file |
| ImageGenerationService | >85% | 1 file (existing) |
| Export/Import Schemas | >90% | 1 file (existing) |

### Test Count Summary

| Category | Test Files | Test Methods | Status |
|----------|-----------|--------------|--------|
| Repository Tests | 2 | 30+ | ✅ Complete |
| Service Tests | 3 | 60+ | ✅ Complete |
| API Tests | 1 | 15+ | ✅ Complete |
| E2E Tests | 1 | 12+ | ✅ Complete |
| Schema Tests | 1 | 25+ | ✅ Existing |
| **TOTAL** | **8** | **140+** | ✅ Complete |

## Test Patterns and Best Practices

### 1. Arrange-Act-Assert (AAA) Pattern
```python
async def test_method():
    # Arrange: Set up test data and mocks
    user = await create_user(session)
    collection = await create_collection(session, user.id)

    # Act: Execute the method under test
    result = await service.update_visibility(
        collection_id=collection.id,
        new_visibility="public",
        user_id=user.id,
    )

    # Assert: Verify the result
    assert result is not None
    assert result.visibility == "public"
```

### 2. Test Isolation
- Each test creates its own data
- In-memory SQLite database per test
- No shared state between tests
- Clean up in fixtures

### 3. Mocking External Dependencies
```python
with patch("apps.api.dealbrain_api.services.image_generation.boto3.client") as mock_s3:
    mock_s3.return_value.put_object = AsyncMock()
    # Test code here
```

### 4. Async Testing
```python
@pytest.mark.asyncio
async def test_async_method():
    result = await async_method()
    assert result is not None
```

### 5. Parametrized Tests
```python
@pytest.mark.parametrize("visibility,expected", [
    ("private", False),
    ("unlisted", True),
    ("public", True),
])
async def test_access(visibility, expected):
    can_access = await service.check_access(collection_id, None)
    assert can_access == expected
```

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Phase 2 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run Phase 2 tests
        run: |
          poetry run pytest tests/repositories/test_collection_share_token_repository.py -v
          poetry run pytest tests/services/test_collections_sharing.py -v
          poetry run pytest tests/services/test_export_import_service.py -v
          poetry run pytest tests/api/test_card_generation_api.py -v
          poetry run pytest tests/e2e/test_export_import_e2e.py -v

      - name: Generate coverage report
        run: |
          poetry run pytest --cov --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

## Known Issues and Limitations

### 1. In-Memory SQLite Limitations
- Some advanced PostgreSQL features not available
- Foreign key constraints may behave differently
- Performance characteristics different from production

### 2. Mocked Dependencies
- Playwright browser rendering is mocked (no real screenshots)
- S3 client is mocked (no real uploads)
- Telemetry events are mocked (no real logging)

### 3. Test Data
- Sample data is minimal (not representative of production scale)
- Large dataset tests are limited by in-memory constraints

## Future Improvements

### 1. Integration Tests with Real Dependencies
- PostgreSQL test database (via Docker)
- Real S3 bucket (LocalStack or MinIO)
- Real Playwright browser (headless)

### 2. Performance Testing
- Load testing for export/import of large collections
- Stress testing for concurrent card generation
- Benchmark tests for duplicate detection

### 3. Contract Testing
- API contract tests (OpenAPI validation)
- Schema evolution tests (v1.0.0 → v1.1.0)
- Backward compatibility tests

### 4. Visual Regression Testing
- Screenshot comparison for card images
- Diff detection for UI changes
- Automated visual QA

## References

### Test Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

### Project Documentation
- [Phase 2a Implementation Summary](/home/user/deal-brain/PHASE_2A_IMPLEMENTATION_SUMMARY.md)
- [Export/Import Schema v1.0.0](/home/user/deal-brain/docs/schemas/deal-brain-export-schema-v1.0.0.json)
- [Collections API Documentation](/home/user/deal-brain/apps/api/dealbrain_api/api/collections.py)

---

**Last Updated:** 2025-11-19
**Coverage Target:** >85% for all Phase 2 features
**Total Tests:** 140+ test methods across 8 test files
