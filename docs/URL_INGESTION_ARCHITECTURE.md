# Deal Brain URL Ingestion Feature - Architecture Analysis

## Executive Summary

Deal Brain is a Python/TypeScript monorepo system for PC listings analysis with price-to-performance scoring. The codebase is well-architected for adding URL ingestion capabilities. This analysis identifies the existing patterns and infrastructure needed to implement web scraping and URL-based listing imports.

---

## 1. Current Import Architecture

### 1.1 Import Pipeline Overview

**Location:** `apps/api/dealbrain_api/importers/` and `apps/api/dealbrain_api/services/imports/`

The current import system supports **Excel/CSV files only**:

```
Excel/CSV File Upload
  → ImportSessionService.create_session()
  → File parsing (pandas)
  → Schema detection & mapping
  → Preview generation
  → Conflict detection
  → Commit → apply_seed()
  → Database persistence
```

**Key Components:**

1. **Excel Importer** (`excel.py`)
   - Reads Excel workbooks with pandas
   - Parses sheets for CPUs, GPUs, listings, valuation rules
   - Handles flexible column matching
   - Returns `SpreadsheetSeed` schema

2. **Import Session Service** (`services/imports/service.py`)
   - Manages multi-step import workflow (1235 lines)
   - Handles file upload, mapping, preview, conflict resolution
   - Async database operations with SQLAlchemy
   - Auto-creates missing CPUs, validates conflicts
   - Comprehensive audit logging

3. **Import Models** (`models/core.py`)
   - `ImportSession`: Tracks upload session state
   - `ImportSessionAudit`: Records all actions
   - `ImportJob`: Legacy import tracking (minimal usage)

### 1.2 Data Flow

```
Upload → Session Creation → Workbook Loading → Schema Inference
  → Field Mapping → Preview Generation → Conflict Detection
  → User Resolution → Seed Building → apply_seed()
  → ListingCreate → Listing (DB) → Metrics Calculation
```

### 1.3 Limitations for URL Ingestion

Current design assumes:
- **Structured data**: Pre-formatted columns/sheets
- **Synchronous source**: Complete file available upfront
- **No external fetching**: All data in the file
- **No real-time updates**: One-time import event

---

## 2. Database Schema for Listings

### 2.1 Listing Model

**Location:** `apps/api/dealbrain_api/models/core.py` (lines 340-426)

```python
class Listing(Base, TimestampMixin):
    __tablename__ = "listing"
    
    # Core fields (relevant for URL ingestion)
    id: int (PK)
    title: str (required, max 255)
    listing_url: str | None (Text field)
    seller: str | None (max 128)
    price_usd: float (required)
    price_date: datetime | None
    condition: str (Condition enum)
    status: str (ListingStatus enum: ACTIVE, ARCHIVED, DELISTED)
    notes: str | None (Text)
    raw_listing_json: dict | None (JSON - for scraped data)
    attributes_json: dict (JSON - flexible storage)
    other_urls: list[dict] (JSON - additional URLs)
    
    # Hardware specs
    cpu_id: int | None (FK → Cpu)
    gpu_id: int | None (FK → Gpu)
    ram_gb: int (default 0)
    primary_storage_gb: int (default 0)
    primary_storage_type: str | None
    secondary_storage_gb: int | None
    secondary_storage_type: str | None
    
    # Valuation/scoring
    adjusted_price_usd: float | None
    valuation_breakdown: dict | None (JSON)
    score_cpu_multi: float | None
    score_cpu_single: float | None
    score_gpu: float | None
    
    # Metadata
    manufacturer: str | None
    series: str | None
    model_number: str | None
    form_factor: str | None
```

**Key Observations:**
- `raw_listing_json` is designed to store scraped data
- `attributes_json` provides flexible extension point
- `other_urls` supports additional links
- Foreign keys to CPU/GPU for enrichment
- Relationships to components, scores, ports

### 2.2 Supporting Tables

- **Cpu, Gpu**: Component catalog (for enrichment)
- **RamSpec, StorageProfile**: Hardware specs
- **ListingComponent**: Additional components
- **ListingScoreSnapshot**: Historical scores
- **PortsProfile, Port**: Connectivity metadata

---

## 3. API Endpoint Patterns

### 3.1 Import Endpoints

**Location:** `apps/api/dealbrain_api/api/imports.py`

```
POST   /v1/imports/sessions                    → Create import session
GET    /v1/imports/sessions                    → List sessions
GET    /v1/imports/sessions/{id}               → Get session details
POST   /v1/imports/sessions/{id}/refresh       → Refresh preview
POST   /v1/imports/sessions/{id}/mappings      → Update field mappings
POST   /v1/imports/sessions/{id}/conflicts     → Compute conflicts
POST   /v1/imports/sessions/{id}/commit        → Commit import
```

### 3.2 Listing Endpoints

**Location:** `apps/api/dealbrain_api/api/listings.py`

```
POST   /v1/listings                  → Create listing
GET    /v1/listings                  → List listings
GET    /v1/listings/{id}             → Get listing
PATCH  /v1/listings/{id}             → Update listing
DELETE /v1/listings/{id}             → Delete listing
PATCH  /v1/listings/{id}/metrics     → Recalculate metrics
POST   /v1/listings/bulk/recalculate → Bulk recalculate
```

### 3.3 Router Structure

**Location:** `apps/api/dealbrain_api/api/__init__.py`

The app uses a modular router pattern. New URL ingestion routes would follow:

```python
# apps/api/dealbrain_api/api/url_ingestion.py
router = APIRouter(prefix="/v1/url-imports", tags=["url-imports"])

@router.post("/sessions", response_model=UrlImportSessionModel)
async def create_url_import_session(
    url: str,
    db: AsyncSession = Depends(session_dependency),
):
    """Create a URL-based import session"""
    
# Then include in api/__init__.py:
from . import url_ingestion
router.include_router(url_ingestion.router)
```

---

## 4. Background Job Infrastructure

### 4.1 Celery & Redis Setup

**Location:** 
- Worker config: `apps/api/dealbrain_api/worker.py`
- Tasks: `apps/api/dealbrain_api/tasks/`
- Docker: `docker-compose.yml`

**Configuration:**

```python
# worker.py
celery_app = Celery("dealbrain")
celery_app.config_from_object({
    "broker_url": "redis://redis:6379/0",
    "result_backend": "redis://redis:6379/0",
    "task_serializer": "json",
})
```

**Docker Services:**
- **Redis** on port 6379 (queue, result storage)
- **Worker**: Separate container running `celery worker`
- **API**: Separate container for FastAPI

### 4.2 Existing Task Pattern

**Location:** `apps/api/dealbrain_api/tasks/valuation.py`

```python
from dealbrain_api.worker import celery_app

@celery_app.task(name="valuation.recalculate_listings")
def recalculate_listings_task(listing_ids=None, batch_size=100):
    """Background task for metric recalculation"""
    return _recalculate_listings_async(
        listing_ids=listing_ids,
        batch_size=batch_size,
    )
```

**Pattern for URL scraping task would be:**

```python
@celery_app.task(name="url_ingestion.scrape_listing")
def scrape_listing_task(url: str, session_id: UUID):
    """Async task to scrape a single URL"""
    # Fetch content
    # Parse data
    # Create listing record
    # Update session progress
```

### 4.3 Async Database Access

**Location:** `apps/api/dealbrain_api/db.py`

Deal Brain uses **async SQLAlchemy** with connection pooling:

```python
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

async_engine = create_async_engine(
    "postgresql+asyncpg://...",
    pool_pre_ping=True,
    connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
    },
)

async with session_scope() as session:
    await session.execute(...)
    await session.commit()
```

**This supports:**
- Non-blocking I/O for HTTP requests
- Concurrent scraping with asyncio
- Connection pooling for database

---

## 5. Service Layer Organization

### 5.1 Services Pattern

**Location:** `apps/api/dealbrain_api/services/`

Deal Brain follows a **services layer** pattern that orchestrates persistence + domain logic:

```
Service (business logic) ↓
  ↓
Domain Logic (packages/core/)
  ↓
SQLAlchemy Models ↓
  ↓
Database
```

**Example: ListingsService** (`services/listings.py`)

```python
async def create_listing(
    db: AsyncSession,
    listing_create: ListingCreate,
) -> Listing:
    """Create listing, sync components, apply metrics"""
    listing = Listing(**listing_create.model_dump(exclude={"components"}))
    db.add(listing)
    await db.flush()
    
    # Sync components
    await sync_listing_components(db, listing, components)
    
    # Apply metrics
    await apply_listing_metrics(db, listing)
    
    await db.commit()
    return listing
```

### 5.2 URL Ingestion Service Would Fit As

```
apps/api/dealbrain_api/services/url_ingestion.py

class UrlIngestionService:
    """Manage URL-based import sessions and scraping"""
    
    async def create_session(
        db: AsyncSession,
        urls: list[str],
        source: str = "web",  # URL source
        config: dict | None = None,
    ) -> UrlIngestionSession:
        """Initialize import session for URLs"""
    
    async def fetch_and_parse(
        url: str,
        config: UrlScraperConfig,
    ) -> ScrapedListingData:
        """Fetch URL and extract listing data"""
    
    async def enrich_listing(
        db: AsyncSession,
        data: ScrapedListingData,
    ) -> Listing:
        """Match components, calculate metrics"""
```

---

## 6. HTTP Client Infrastructure

### 6.1 Available HTTP Client

**Dependency:** `httpx` (line 35 of `pyproject.toml`)

```toml
httpx = "^0.26.0"
```

Deal Brain has **httpx** available but **no existing HTTP client utilities**.

**Advantages of httpx:**
- Async/await support
- Connection pooling
- Timeout handling
- Streaming support

### 6.2 Recommended HTTP Client Pattern

```python
# apps/api/dealbrain_api/http_client.py
import httpx

class HttpClient:
    """Singleton HTTP client for external requests"""
    
    _client: httpx.AsyncClient | None = None
    
    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            cls._client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5,
                ),
            )
        return cls._client
    
    @classmethod
    async def close(cls) -> None:
        if cls._client:
            await cls._client.aclose()

# Usage in scraping task:
async def fetch_url(url: str) -> str:
    client = await HttpClient.get_client()
    response = await client.get(url, follow_redirects=True)
    response.raise_for_status()
    return response.text
```

---

## 7. Data Models & Schemas

### 7.1 Listing Schemas

**Location:** `packages/core/dealbrain_core/schemas/listing.py`

```python
class ListingBase(DealBrainModel):
    title: str
    listing_url: str | None  # Primary URL
    other_urls: list[ListingLink]  # Additional URLs
    price_usd: float
    condition: Condition
    # ... hardware specs

class ListingCreate(ListingBase):
    components: list[ListingComponentCreate] | None = None

class ListingRead(ListingBase):
    id: int
    adjusted_price_usd: float | None
    valuation_breakdown: dict[str, Any] | None
    # ... scores
```

### 7.2 URL Ingestion Schemas Would Add

```python
# packages/core/dealbrain_core/schemas/url_ingestion.py

class UrlSourceConfig(DealBrainModel):
    """Configuration for specific URL source"""
    name: str  # "ebay", "amazon", "hardwareforum"
    selectors: dict[str, str]  # CSS selectors for scraping
    headers: dict[str, str] | None = None
    auth: dict[str, str] | None = None

class ScrapedListingData(DealBrainModel):
    """Raw data extracted from URL"""
    title: str
    price_usd: float
    condition: Condition
    url: str
    raw_html: str | None  # Store original HTML
    extracted_fields: dict[str, Any]  # Parsed data
    cpu_name: str | None
    gpu_name: str | None
    ram_gb: int | None
    storage_specs: dict[str, Any]

class UrlImportSessionStatus(DealBrainModel):
    """Status of URL import job"""
    id: UUID
    urls: list[str]
    status: str  # pending, scraping, completed, failed
    progress: dict[str, int]  # {"total": 10, "completed": 5, "failed": 1}
    results: list[dict[str, Any]]  # Scraped listings
    errors: list[dict[str, str]]  # URL: error_message
```

---

## 8. Database Schema Extensions

### 8.1 New Tables Needed

```sql
-- Track URL import sessions (similar to ImportSession)
CREATE TABLE url_ingestion_session (
    id UUID PRIMARY KEY,
    source VARCHAR(64),  -- "ebay", "amazon", etc.
    status VARCHAR(32),  -- pending, scraping, completed
    urls_json JSON,  -- {"urls": ["http://...", ...]}
    config_json JSON,  -- Scraper configuration
    results_json JSON,  -- Scraped data
    error_summary_json JSON,  -- Failed URLs
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Track individual URL scrape jobs
CREATE TABLE url_scrape_job (
    id INT PRIMARY KEY,
    session_id UUID FOREIGN KEY,
    url TEXT,
    status VARCHAR(32),  -- pending, completed, failed
    scraped_data_json JSON,
    error_message TEXT,
    celery_task_id VARCHAR(255),  -- Celery task reference
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

**Alembic Migration Needed:**
```bash
poetry run alembic revision --autogenerate -m "add url ingestion tables"
```

---

## 9. Existing Patterns to Follow

### 9.1 Import Session Pattern

The current `ImportSession` model provides a good template:

```python
class ImportSession(Base, TimestampMixin):
    __tablename__ = "import_session"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    filename: str  # We'd use: source (ebay, amazon)
    status: str  # pending → mapping_required → completed
    preview_json: dict  # Preview of data
    conflicts_json: dict  # Conflicts needing resolution
    audit_events: relationship  # Full audit trail
```

### 9.2 Audit Logging Pattern

Import sessions include comprehensive audit:

```python
class ImportSessionAudit(Base):
    __tablename__ = "import_session_audit"
    
    session_id: UUID FOREIGN KEY
    event: str  # session_created, mappings_updated, commit_success
    message: str | None
    payload_json: dict | None
```

This pattern should be copied for URL ingestion.

### 9.3 Conflict Resolution Pattern

Import service detects and resolves CPU conflicts:

```python
async def compute_conflicts(db, session) -> dict[str, Any]:
    """Detect conflicts (e.g., existing CPUs with different specs)"""
    conflicts: dict[str, Any] = {}
    if cpu_conflicts := await self._detect_cpu_conflicts(...):
        conflicts["cpu"] = cpu_conflicts
    return conflicts

async def commit(db, session, conflict_resolutions) -> tuple[dict, list]:
    """User provides resolutions, then commit proceeds"""
    self._validate_conflicts(session.conflicts_json, resolutions)
    # Build seed and apply
```

---

## 10. External Integrations Status

### 10.1 What Exists

- **httpx**: Installed (async HTTP client)
- **Celery**: Configured (background tasks)
- **Redis**: Running in Docker
- **Async SQLAlchemy**: Fully configured
- **Audit logging**: Already implemented

### 10.2 What Doesn't Exist

- **Web scraping library**: Consider:
  - `beautifulsoup4` for HTML parsing
  - `playwright` (already in dev deps!) for JavaScript-heavy sites
  - `lxml` for fast parsing
  
- **URL validation**: Need to add:
  - Domain whitelist/blacklist
  - Rate limiting
  - User-Agent management

- **Data extraction**: Need to build:
  - CSS selector mapping
  - Schema inference for extracted data
  - Hardware spec parsing (CPU names, RAM GB, etc.)

- **Deduplication**: Need to implement:
  - Title + URL hash to prevent duplicates
  - Price change tracking

---

## 11. API Design Recommendations

### 11.1 URL Ingestion Endpoints

```
# Create URL import session
POST /v1/url-imports/sessions
{
    "urls": ["https://ebay.com/itm/123", "https://amazon.com/dp/ABC"],
    "source": "manual",
    "config": {
        "auto_parse_hardware": true,
        "deduplicate": true
    }
}
→ UrlImportSessionModel (id, status, progress)

# Get session status (with real-time progress)
GET /v1/url-imports/sessions/{session_id}
→ UrlImportSessionModel (updated status)

# Get scraped listings preview
GET /v1/url-imports/sessions/{session_id}/preview
→ { "listings": [...], "preview": [...], "errors": [...] }

# Commit scraped listings (like imports)
POST /v1/url-imports/sessions/{session_id}/commit
{
    "conflict_resolutions": {"cpu_name_1": "update"},
    "component_overrides": {0: {"cpu_match": "Intel Core i7"}}
}
→ { "created": 10, "errors": 2 }

# Stop active scraping job
POST /v1/url-imports/sessions/{session_id}/cancel
```

### 11.2 Webhook for Real-time Updates

For long-running scraping, consider WebSocket or polling:

```python
# WebSocket approach (advanced)
@router.websocket("/ws/url-imports/{session_id}")
async def websocket_url_import_status(
    websocket: WebSocket,
    session_id: UUID,
):
    """Stream real-time scraping progress"""
    await websocket.accept()
    while True:
        status = await get_session_progress(session_id)
        await websocket.send_json(status)
        await asyncio.sleep(1)

# OR simple polling (current approach)
GET /v1/url-imports/sessions/{session_id}/progress
→ { "total": 50, "completed": 23, "failed": 2 }
```

---

## 12. Implementation Roadmap

### Phase 1: Foundation (1-2 weeks)
1. [ ] Add database tables (Alembic migration)
2. [ ] Create schemas (`packages/core/schemas/url_ingestion.py`)
3. [ ] Implement HTTP client wrapper
4. [ ] Create `UrlIngestionService` skeleton
5. [ ] Add basic URL validation

### Phase 2: Scraping (2-3 weeks)
1. [ ] Implement HTML parser with CSS selectors
2. [ ] Build hardware spec extraction (CPU, GPU, RAM)
3. [ ] Create source-specific parsers (eBay, Amazon, etc.)
4. [ ] Add Celery tasks for async scraping
5. [ ] Implement error handling & retry logic

### Phase 3: Integration (1-2 weeks)
1. [ ] Add API endpoints (`/v1/url-imports/*`)
2. [ ] Implement conflict detection (like imports)
3. [ ] Add deduplication logic
4. [ ] Create progress tracking
5. [ ] Frontend UI for URL ingestion

### Phase 4: Polish (1 week)
1. [ ] Add comprehensive audit logging
2. [ ] Rate limiting & monitoring
3. [ ] Tests & documentation
4. [ ] Performance optimization

---

## 13. Key Files Reference

### Current Import System
- **Models**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py` (Listing, ImportSession)
- **Service**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/imports/service.py` (1235 lines)
- **API**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/imports.py`
- **Tasks**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/tasks/valuation.py`
- **Worker**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/worker.py`

### Core Schemas
- **Listing**: `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/listing.py`
- **Enums**: `/mnt/containers/deal-brain/packages/core/dealbrain_core/enums.py`

### Database
- **DB Setup**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/db.py`
- **Migrations**: `/mnt/containers/deal-brain/apps/api/alembic/versions/`

### Docker
- **Compose**: `/mnt/containers/deal-brain/docker-compose.yml`
- **Worker Dockerfile**: `/mnt/containers/deal-brain/infra/worker/Dockerfile`

---

## 14. Recommendations Summary

### What to Reuse
1. ✅ `ImportSession` pattern for `UrlIngestionSession`
2. ✅ `ImportSessionService` workflow for URL sessions
3. ✅ Async SQLAlchemy patterns
4. ✅ Celery task infrastructure
5. ✅ Audit logging architecture
6. ✅ Conflict detection/resolution pattern

### What to Build
1. 🆕 HTML parsing service (BeautifulSoup4)
2. 🆕 Source-specific scraper modules
3. 🆕 Hardware spec extraction logic
4. 🆕 HTTP client wrapper with rate limiting
5. 🆕 Deduplication logic
6. 🆕 URL validation & whitelisting

### Dependencies to Add
```toml
beautifulsoup4 = "^4.12.0"
lxml = "^4.9.0"  # For fast HTML parsing
# playwright already in dev deps
# httpx already present
```

### Architecture Decisions
- **Async**: Use async/await throughout (already pattern)
- **Background Jobs**: Celery tasks for scraping (already pattern)
- **Audit Trail**: Full logging (already pattern)
- **Preview-Then-Commit**: Same as imports (already pattern)
- **Deduplication**: Title + URL hash in database unique constraint

---

## Conclusion

The Deal Brain codebase is **well-structured and extensible** for adding URL ingestion. The existing patterns for:
- Import sessions and workflows
- Background job processing
- Async database operations
- Audit logging
- Conflict resolution

...provide a solid foundation. The main work involves:
1. Creating scraper infrastructure (HTML parsing, data extraction)
2. Extending the database schema minimally
3. Following existing patterns for consistency
4. Adding source-specific parsing logic

The async architecture, Celery infrastructure, and httpx library are all in place to support concurrent web scraping at scale.
