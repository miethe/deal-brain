# Backend Architecture Overview

This guide provides a comprehensive overview of Deal Brain's backend architecture, including the monorepo structure, layering patterns, and key architectural principles.

## Architecture at a Glance

Deal Brain is a **full-stack price-to-performance assistant** with a carefully layered backend architecture:

```
┌─────────────────────────────────────────┐
│         FastAPI HTTP Layer              │
│  (apps/api/dealbrain_api/api/*.py)      │
└────────────────┬────────────────────────┘
                 │
┌─────────────────▼────────────────────────┐
│      Service/Orchestration Layer         │
│  (apps/api/dealbrain_api/services/*.py)  │
└────────────────┬────────────────────────┘
                 │
┌─────────────────▼────────────────────────┐
│        Domain Logic Layer                │
│ (packages/core/dealbrain_core/*.py)      │
└────────────────┬────────────────────────┘
                 │
┌─────────────────▼────────────────────────┐
│  Database Layer (SQLAlchemy + Alembic)   │
│  (apps/api/dealbrain_api/models/*.py)    │
└─────────────────────────────────────────┘
```

## Monorepo Structure

Deal Brain uses a **Python/TypeScript monorepo** managed with Poetry (Python) and pnpm (JavaScript).

### Backend Directories

```
apps/api/                                  # FastAPI backend application
├── dealbrain_api/
│   ├── api/                               # FastAPI route handlers
│   │   ├── listings.py                    # Listing CRUD endpoints
│   │   ├── catalog.py                     # CPU/GPU catalog endpoints
│   │   ├── rules.py                       # Valuation rules endpoints
│   │   ├── custom_fields.py               # Dynamic field management
│   │   ├── ingestion.py                   # URL ingestion endpoints
│   │   └── ... (other routes)
│   ├── services/                          # Business logic layer
│   │   ├── listings.py                    # Listing service (CRUD + valuation)
│   │   ├── custom_fields.py               # Custom field service
│   │   ├── rule_evaluation.py             # Rule engine
│   │   ├── imports/                       # Excel/file import pipeline
│   │   ├── ingestion.py                   # URL ingestion service
│   │   └── ... (other services)
│   ├── models/                            # SQLAlchemy ORM models
│   │   └── core.py                        # All data models
│   ├── tasks/                             # Celery background tasks
│   │   ├── valuation.py                   # Async valuation recalculation
│   │   └── ingestion.py                   # Async ingestion tasks
│   ├── db.py                              # Database configuration & session management
│   ├── app.py                             # FastAPI app factory
│   ├── main.py                            # Uvicorn entrypoint
│   ├── settings.py                        # Configuration (pydantic-settings)
│   └── worker.py                          # Celery app configuration
├── alembic/                               # Database migrations
│   ├── env.py                             # Alembic environment config
│   └── versions/                          # Migration files (0001_, 0002_, etc.)
└── tests/                                 # Backend test suite

packages/core/                             # Shared domain logic
├── dealbrain_core/
│   ├── valuation.py                       # Valuation computation engine
│   ├── scoring.py                         # Score calculation logic
│   ├── rule_evaluator.py                  # Rule evaluation engine
│   ├── enums.py                           # Shared enumerations
│   ├── schemas/                           # Pydantic models (requests/responses)
│   │   ├── listing.py                     # Listing schemas
│   │   ├── imports.py                     # Import schemas
│   │   ├── catalog.py                     # CPU/GPU/Port/RAM schemas
│   │   └── ... (other schemas)
│   └── rules/                             # Rule system logic
│       ├── evaluator.py                   # Rule evaluation
│       ├── conditions.py                  # Rule conditions
│       ├── actions.py                     # Rule actions
│       └── formula.py                     # Formula parsing/evaluation
```

### Key Directories

```
tests/                                     # Backend test suite
├── test_*.py                              # Pytest test files
├── api/                                   # API endpoint tests
├── services/                              # Service layer tests
├── core/                                  # Domain logic tests
└── conftest.py                            # Pytest configuration

apps/web/                                  # Next.js frontend (out of scope here)
apps/cli/                                  # Typer CLI commands (separate from API)
```

## Layering Patterns

### 1. FastAPI Layer (Presentation)

**Location:** `apps/api/dealbrain_api/api/*.py`

Responsibilities:
- HTTP request/response handling
- Request validation with Pydantic schemas
- Parameter extraction and normalization
- Error handling and HTTP status codes
- Dependency injection (session, auth, etc.)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import session_dependency

router = APIRouter(prefix="/v1/listings", tags=["listings"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: ListingCreate,
    session: AsyncSession = Depends(session_dependency)
) -> ListingRead:
    """Create a new listing."""
    try:
        listing = await create_listing_impl(session, payload)
        return listing
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
```

### 2. Service Layer (Business Logic Orchestration)

**Location:** `apps/api/dealbrain_api/services/*.py`

Responsibilities:
- Orchestrate database operations with services
- Coordinate calls to domain logic
- Handle transactions and data consistency
- Implement business workflows
- Caching and performance optimization

```python
# apps/api/dealbrain_api/services/listings.py
async def create_listing(
    session: AsyncSession,
    payload: NormalizedListingSchema,
) -> Listing:
    """Create listing and apply initial metrics."""
    # 1. Create listing record
    listing = Listing(
        title=payload.title,
        price_usd=payload.price_usd,
        condition=payload.condition.value,
    )
    session.add(listing)
    await session.flush()

    # 2. Call domain logic for valuation
    adjusted = compute_adjusted_price(
        listing_price_usd=listing.price_usd,
        condition=Condition(listing.condition),
        rules=rules_list,
        components=components_list,
    )
    listing.adjusted_price_usd = adjusted.adjusted_price_usd
    listing.valuation_breakdown = adjusted_breakdown_json

    # 3. Compute score using domain logic
    score = compute_composite_score(listing, metrics)
    listing.score = score

    await session.commit()
    return listing
```

### 3. Domain Logic Layer (Core Business Rules)

**Location:** `packages/core/dealbrain_core/*.py`

Responsibilities:
- Pure business logic (no I/O, no database)
- Valuation computation
- Score calculation
- Rule evaluation
- Data transformation and normalization

```python
# packages/core/dealbrain_core/valuation.py
def compute_adjusted_price(
    listing_price_usd: float,
    condition: Condition,
    rules: Iterable[ValuationRuleData],
    components: Iterable[ComponentValuationInput],
) -> ValuationResult:
    """Compute adjusted price based on valuation rules."""
    lookup = {rule.component_type: rule for rule in rules}
    lines: list[ValuationLine] = []

    for component in components:
        rule = lookup.get(component.component_type)
        if not rule:
            continue

        # Calculate deduction with condition multiplier
        deduction = (
            component.quantity *
            rule.unit_value_usd *
            rule.multiplier_for(condition)
        )

        lines.append(ValuationLine(
            label=component.label,
            component_type=component.component_type,
            quantity=component.quantity,
            unit_value=rule.unit_value_usd,
            condition_multiplier=rule.multiplier_for(condition),
            deduction_usd=deduction,
        ))

    adjusted = listing_price_usd - sum(l.deduction_usd for l in lines)
    return ValuationResult(
        listing_price_usd=listing_price_usd,
        adjusted_price_usd=adjusted,
        lines=lines,
    )
```

### 4. Database Layer (Persistence)

**Location:** `apps/api/dealbrain_api/models/core.py`

SQLAlchemy 2.0 async models with:
- Type hints for all columns
- Relationships with lazy loading strategies
- Timestamp mixins (created_at, updated_at)
- Indexes for common queries
- JSON columns for flexible data

```python
# apps/api/dealbrain_api/models/core.py
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Listing(Base, TimestampMixin):
    __tablename__ = "listing"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    adjusted_price_usd: Mapped[float | None] = mapped_column(Float)
    condition: Mapped[str] = mapped_column(String(32), nullable=False)

    cpu_id: Mapped[int | None] = mapped_column(ForeignKey("cpu.id"))
    cpu: Mapped[Cpu] = relationship(back_populates="listings", lazy="selectin")

    components: Mapped[list[ListingComponent]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    valuation_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=True,
        default=None
    )
```

## Key Architectural Principles

### 1. Shared Domain Logic in packages/core

**Core principle:** Business logic lives in `packages/core/`, not duplicated in `apps/api` or `apps/cli`.

Benefits:
- Single source of truth for calculations
- Shareable across API, CLI, and future services
- Testable in isolation without database
- Clear separation of concerns

### 2. Service Layer Orchestration

**Pattern:** Services coordinate persistence + domain logic

```python
# In services, you call domain functions and manage persistence
from dealbrain_core.valuation import compute_adjusted_price

async def update_listing_valuation(session, listing):
    # 1. Load data from database
    rule_records = await session.execute(select(ValuationRule))
    rules = rule_records.scalars().all()

    # 2. Transform to domain types
    domain_rules = [
        ValuationRuleData(
            component_type=ComponentType(r.component_type),
            metric=ComponentMetric(r.metric),
            unit_value_usd=r.unit_value_usd,
        )
        for r in rules
    ]

    # 3. Call domain logic (pure computation)
    result = compute_adjusted_price(
        listing_price_usd=listing.price_usd,
        condition=Condition(listing.condition),
        rules=domain_rules,
        components=listing_components,
    )

    # 4. Persist results
    listing.adjusted_price_usd = result.adjusted_price_usd
    await session.commit()
```

### 3. Async-First with SQLAlchemy 2.0

**Pattern:** All database operations are async

```python
# From db.py
@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope for async operations."""
    session = get_session_factory()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

# In services
async def list_listings(session: AsyncSession) -> list[Listing]:
    stmt = select(Listing).order_by(Listing.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())
```

### 4. Type Safety with Pydantic

**Request/Response contracts** use Pydantic schemas in `packages/core/dealbrain_core/schemas/`.

```python
# packages/core/dealbrain_core/schemas/listing.py
class ListingCreate(DealBrainModel):
    title: str
    price_usd: float
    condition: Condition = Condition.USED
    status: ListingStatus = ListingStatus.ACTIVE
    cpu_id: int | None = None

class ListingRead(ListingCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    adjusted_price_usd: float | None = None
    valuation_breakdown: dict[str, Any] | None = None
```

### 5. Enums for Type Safety

**Location:** `packages/core/dealbrain_core/enums.py`

Centralized enums prevent string-based errors:

```python
class Condition(str, Enum):
    NEW = "new"
    REFURB = "refurb"
    USED = "used"

class ComponentType(str, Enum):
    RAM = "ram"
    SSD = "ssd"
    HDD = "hdd"
    GPU = "gpu"
```

## Data Flow Examples

### Example 1: Creating a Listing

```
POST /v1/listings
  │
  ├─ FastAPI validates request (ListingCreate schema)
  │
  ├─ Service layer (create_listing):
  │   ├─ Insert Listing record
  │   ├─ Load valuation rules
  │   ├─ Call domain logic: compute_adjusted_price()
  │   ├─ Compute score: compute_composite_score()
  │   ├─ Update listing with adjusted price + score
  │   └─ Commit transaction
  │
  └─ Return ListingRead (JSON response)
```

### Example 2: Updating Valuation Rules

```
PUT /v1/rules/{rule_id}
  │
  ├─ FastAPI validates request
  │
  ├─ Service updates rule record
  │
  ├─ Enqueue background task: recalculate_listings_task()
  │   │
  │   └─ Celery (async):
  │       ├─ Stream all listings (batch processing)
  │       ├─ For each batch:
  │       │   ├─ Load rules from database
  │       │   ├─ Transform to domain types
  │       │   ├─ Call apply_listing_metrics (orchestrates valuation)
  │       │   └─ Persist adjusted prices + scores
  │       └─ Emit completion log
  │
  └─ Return immediately with task ID
```

## Configuration Management

**Location:** `apps/api/dealbrain_api/settings.py`

Uses `pydantic-settings` for environment-based configuration:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    database_url: str  # Required
    redis_url: str = "redis://localhost:6379/0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Nested settings for features
    telemetry: TelemetrySettings = Field(
        default_factory=TelemetrySettings
    )
    ingestion: IngestionSettings = Field(
        default_factory=IngestionSettings
    )

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

Load configuration:

```python
from dealbrain_api.settings import get_settings
settings = get_settings()
print(settings.database_url)
```

## HTTP Status Code Conventions

| Code | Scenario | Example |
|------|----------|---------|
| 200 OK | Successful GET/PATCH | Retrieve listing details |
| 201 Created | Successful POST | Create new listing |
| 204 No Content | Successful DELETE | Delete valuation rule |
| 400 Bad Request | Invalid request body | Missing required field |
| 404 Not Found | Resource not found | Listing ID doesn't exist |
| 422 Unprocessable Entity | Validation error | Invalid enum value |
| 500 Internal Server Error | Unexpected error | Database connection failure |

## Next Steps

Dive deeper into specific areas:

- **[Async Patterns](async-patterns.md)** - Master async/await, context managers, and Celery tasks
- **[Database Guide](database-guide.md)** - SQLAlchemy operations, relationships, and optimization
- **[API Development](api-development.md)** - Creating FastAPI routes and handling requests
- **[Domain Logic](domain-logic.md)** - Implementing business rules in packages/core
- **[Testing Guide](testing-guide.md)** - Writing tests with async support
- **[Error Handling](error-handling.md)** - Exception strategies and HTTP responses
- **[Migrations](migrations.md)** - Managing database schema changes
