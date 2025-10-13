# Deal Brain - AI Agent Instructions

## Project Overview

Deal Brain is a full-stack price-to-performance valuation system for small form factor PCs. It's a **Python/TypeScript monorepo** with a FastAPI backend, Next.js 14 frontend, CLI tools, and shared domain logic.

**Core Capability**: Import Excel workbooks containing PC listings → normalize data → apply component-based valuation rules → compute adjusted prices → rank deals with explainable breakdowns.

## Monorepo Architecture

```
apps/
  api/         # FastAPI + SQLAlchemy 2.0 async, Alembic migrations
  cli/         # Typer CLI for imports, exports, valuation
  web/         # Next.js 14 App Router + React Query
packages/
  core/        # Shared domain logic (valuation, scoring, schemas)
infra/         # Dockerfiles, observability configs
```

**Critical principle**: Domain logic (valuation rules, scoring algorithms) lives in `packages/core`, NOT in `apps/api` or `apps/cli`. This enables code reuse across FastAPI endpoints and CLI commands.

## Essential Workflows

### Setup & Development
```bash
make setup              # Install Python (Poetry) + JS (pnpm) dependencies
make up                 # Start Docker Compose stack (Postgres:5442, Redis:6399, API:8020, Web:3020, Grafana:3021)
make api                # Run FastAPI locally with hot reload (port 8000)
make web                # Run Next.js dev server locally (port 3000)
make migrate            # Apply Alembic migrations (always run after schema changes)
```

### Database Migrations
- **Location**: `apps/api/alembic/versions/`
- **Generate**: `poetry run alembic revision --autogenerate -m "description"`
- **Apply**: `make migrate` (or `poetry run alembic upgrade head`)
- **Always** create migrations when modifying SQLAlchemy models in `apps/api/dealbrain_api/models/core.py`

### Testing
```bash
make test                                              # Run full pytest suite
poetry run pytest tests/test_custom_fields_service.py -v  # Focused test
poetry run pytest -k test_name                         # Run by name
```
- Test fixtures in `tests/conftest.py`
- Use `@pytest.mark.asyncio` for async tests
- Backend tests only; Playwright E2E tests planned

### Data Import
```bash
poetry run dealbrain-cli import ./data/imports/deal-brain.xlsx  # Import Excel workbook
poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv  # Import CPU benchmarks
poetry run python scripts/recalculate_all_metrics.py  # Recalculate all listing metrics
```

## Code Architecture Patterns

### 1. Shared Domain Logic (`packages/core`)
**Never duplicate valuation/scoring logic in API or CLI**. Always import from:
- `dealbrain_core.valuation` - Component-based price adjustments
- `dealbrain_core.scoring` - Composite score calculations
- `dealbrain_core.rules` - Rule evaluation engine (condition matching, actions)
- `dealbrain_core.schemas` - Pydantic models for request/response contracts

Example:
```python
from dealbrain_core.valuation import compute_adjusted_price, ValuationRuleData, ComponentValuationInput
from dealbrain_core.scoring import compute_composite_score, ListingMetrics
```

### 2. Backend Service Layer (`apps/api/dealbrain_api/services/`)
Services orchestrate persistence + domain logic. Key services:
- **`listings.py`** - Listing CRUD, component sync, metrics calculations (739 lines - large!)
- **`rule_evaluation.py`** - Rule matching engine with Prometheus metrics
- **`custom_fields.py`** - Dynamic field management per entity
- **`ports.py`** - Connectivity profile management

**Pattern**: Services call domain functions from `packages/core` + handle database interactions.

### 3. Database Sessions (CRITICAL)
**Always use async SQLAlchemy** in API code:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from dealbrain_api.db import session_scope

# In endpoints:
async def endpoint(session: AsyncSession = Depends(get_session)):
    # Use session here

# In standalone scripts:
async with session_scope() as session:
    # Your code
    await session.commit()  # Explicit commit if using session_scope
```

**Never** use sync database operations in FastAPI. CLI can use sync sessions.

### 4. Frontend Data Fetching
- **React Query** (`@tanstack/react-query`) for all API calls
- API base URL: `NEXT_PUBLIC_API_URL` env var (default: `http://localhost:8000`, Docker: host IP like `http://10.42.9.11:8020`)
- Pattern: Create custom hooks in `apps/web/hooks/` using `useQuery`/`useMutation`

Example:
```typescript
import { useQuery } from '@tanstack/react-query';
import { API_URL } from '@/lib/utils';

export function useListings() {
  return useQuery({
    queryKey: ['listings'],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/api/v1/listings`);
      return response.json();
    }
  });
}
```

### 5. Valuation System Architecture
Deal Brain has TWO valuation systems (legacy + new):

**Legacy (still active)**: Component-based deductions
- Code: `packages/core/dealbrain_core/valuation.py`
- Models: `ValuationRule` table
- Pattern: Deducts value per unit (e.g., $10/GB RAM) with condition multipliers

**New (Advanced Mode)**: Rule-based evaluation
- Code: `packages/core/dealbrain_core/rules/`, `apps/api/dealbrain_api/services/rule_evaluation.py`
- Models: `ValuationRuleset` → `ValuationRuleGroup` → `ValuationRuleV2` hierarchy
- Pattern: Condition matching (AND/OR logic) → Actions (fixed_value, per_unit, formula)
- UI: `/valuation-rules` page with Basic/Advanced tabs

**Key file**: `docs/architecture/valuation-rules.md` (643 lines) - comprehensive architecture guide.

## Project-Specific Conventions

### Import Paths
```python
# Correct - use explicit package names
from dealbrain_core.valuation import compute_adjusted_price
from dealbrain_api.models import Listing, Cpu
from dealbrain_api.services.listings import create_listing

# Incorrect - relative imports break in CLI context
from ..models import Listing  # ❌
```

### Field Naming
- **Database**: snake_case (`price_usd`, `cpu_mark_multi`)
- **API responses**: camelCase via Pydantic `alias_generator`
- **Frontend**: camelCase TypeScript interfaces

### Mutable Fields
`apps/api/dealbrain_api/services/listings.py` defines `MUTABLE_LISTING_FIELDS` set - only these fields can be updated via PATCH endpoints.

### URL Handling
Listings require validated URLs:
- `listing_url` - Primary URL (required, must be http/https with valid host)
- `other_urls` - Array of `{url, label}` objects
- Handled by `_sanitize_primary_url()` and `_normalize_other_urls()` in `listings.py`

## Key Files Reference

### Backend
- `apps/api/dealbrain_api/models/core.py` - All SQLAlchemy models (565 lines)
- `apps/api/dealbrain_api/services/listings.py` - Listing orchestration (739 lines)
- `apps/api/dealbrain_api/services/rule_evaluation.py` - Rule engine (603 lines)
- `apps/api/dealbrain_api/api/` - FastAPI routers (organized by domain)
- `apps/api/alembic/versions/` - Database migration history

### Frontend
- `apps/web/app/` - Next.js App Router pages
- `apps/web/components/listings/` - Listing UI components
- `apps/web/components/valuation/` - Valuation display components
- `apps/web/hooks/` - React Query hooks (useValuationThresholds, useFieldOptions, etc.)
- `apps/web/lib/utils.ts` - Exports `API_URL` constant

### Configuration
- `pyproject.toml` - Python deps, Poetry scripts, linting config (black line-length=100)
- `Makefile` - Common development commands
- `docker-compose.yml` - Full stack definition
- `.env` - Local development (`.env.example` for Docker)

## Observability

- **Metrics**: Prometheus exposed on API at `/metrics`, Grafana dashboards on port 3021
- **FastAPI instrumentation**: `prometheus-fastapi-instrumentator` tracks request latency, status codes
- **Custom metrics**: Rule evaluation service tracks valuation layer contributions, delta amounts
- **OTLP collector**: Ships traces to observability stack

## Testing Patterns

- Use `@pytest.mark.asyncio` for async test functions
- Fixtures in `tests/conftest.py` set up Python path for imports
- Mock React Query in frontend tests:
  ```typescript
  jest.mock('@tanstack/react-query', () => ({
    useQuery: jest.fn().mockReturnValue({ data: mockData, isLoading: false }),
    useMutation: jest.fn().mockImplementation((options) => ({ mutate: jest.fn() }))
  }));
  ```

## Common Gotchas

1. **Don't run migrations in Docker** - Database migrations must run after services start. Use `make migrate` locally or add init containers.
2. **Docker API URL** - In Docker, frontend can't use `localhost:8000`. Set `NEXT_PUBLIC_API_URL` to host IP.
3. **Async vs Sync** - API uses async SQLAlchemy, CLI can use sync. Never mix.
4. **Component imports** - UI components from `apps/web/components/ui/` are shadcn-based, don't modify directly.
5. **Legacy vs New valuation** - Check `ruleset_id` on listings to determine which system is active.

## Future Roadmap

- Celery worker scaffolded but not integrated (background task processing)
- Playwright E2E tests planned
- Advanced valuation rule formula support
- GraphQL API consideration
