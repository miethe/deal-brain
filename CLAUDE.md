# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Deal Brain is a full-stack price-to-performance assistant for small form factor PCs. The system imports Excel workbooks containing PC listings, normalizes them, computes adjusted pricing based on component valuation rules, applies scoring profiles, and ranks deals with explainable breakdowns.

## Monorepo Structure

This is a Python/TypeScript monorepo managed with Poetry (Python) and pnpm (JavaScript):

- `apps/api/` - FastAPI backend with async SQLAlchemy, Alembic migrations
- `apps/cli/` - Typer-based CLI commands
- `apps/web/` - Next.js 14 App Router frontend
- `packages/core/` - Shared domain logic (valuation, scoring, schemas) used by both API and CLI
- `infra/` - Dockerfiles and observability configuration
- `tests/` - Backend test suite

## Essential Commands

### Setup & Installation
```bash
make setup              # Install Python and JavaScript dependencies
poetry install          # Python dependencies only
pnpm install --frozen-lockfile=false  # JavaScript dependencies only
```

### Running Services
```bash
make up                 # Start full Docker Compose stack (Postgres, Redis, API, web, worker, Prometheus, Grafana)
make down               # Stop all services
make api                # Run FastAPI dev server locally (without Docker)
make web                # Run Next.js dev server locally (without Docker)
```

### Database Migrations
```bash
make migrate            # Apply all pending Alembic migrations (alembic upgrade head)
poetry run alembic revision --autogenerate -m "description"  # Generate new migration
```

### Testing & Code Quality
```bash
make test               # Run pytest suite
poetry run pytest path/to/test_file.py::test_function_name  # Run single test
make lint               # Lint Python (ruff) and TypeScript (eslint)
make format             # Format code (black, isort, prettier)
```

### Data Seeding
```bash
make seed               # Run seed script (apps/api/dealbrain_api/seeds.py)
poetry run dealbrain-cli import path/to/workbook.xlsx  # Import Excel workbook
```

### CLI Commands
```bash
poetry run dealbrain-cli --help     # Show all CLI commands
poetry run dealbrain-cli add        # Add a new listing interactively
poetry run dealbrain-cli top        # Show top listings by metric
poetry run dealbrain-cli explain <listing_id>  # Show valuation breakdown
poetry run dealbrain-cli export     # Export top listings to JSON
```

## Architecture Principles

### Shared Domain Logic
The `packages/core/` directory contains the **core domain logic** shared across API and CLI:
- `valuation.py` - Component-based pricing adjustments (e.g., RAM deductions based on condition multipliers)
- `scoring.py` - Composite score calculations with weighted metrics
- `schemas/` - Pydantic models for request/response contracts
- `enums.py` - Shared enums (ComponentType, ComponentMetric, Condition, etc.)

**Key principle**: Domain logic lives in `packages/core`, not duplicated in `apps/api` or `apps/cli`.

### Backend Services Layer
`apps/api/dealbrain_api/services/` orchestrates persistence + domain logic:
- `listings.py` - Listing CRUD, component sync, metrics application
- `custom_fields.py` - Dynamic custom field management per entity
- `field_registry.py` - Field metadata registration and validation
- `imports/` - Excel workbook parsing and import pipeline

Services call domain functions from `packages/core` and handle database interactions.

### Database Models
`apps/api/dealbrain_api/models/core.py` contains all SQLAlchemy models:
- Core tables: `CPU`, `GPU`, `ValuationRule`, `Profile`, `PortsProfile`, `Listing`, `ListingComponent`, `ListingScoreSnapshot`
- Supporting tables: `ImportJob`, `TaskRun`, `EntityField`, `EntityFieldValue`
- Listings store `valuation_breakdown` JSON for explainability

### Frontend Data Fetching
Next.js app uses React Query (`@tanstack/react-query`) to fetch from the API:
- API base URL controlled by `NEXT_PUBLIC_API_URL` environment variable
- Default: `http://localhost:8000`, Docker: set to host machine's IP (e.g., `http://10.42.9.11:8020`)
- Utility: `apps/web/lib/utils.ts` exports `API_URL` constant

### Import Pipeline
The Excel import workflow:
1. CLI command `poetry run dealbrain-cli import path/to/workbook.xlsx`
2. Parses workbook with pandas (`apps/api/dealbrain_api/importers/`)
3. Generates `SpreadsheetSeed` schema
4. Upserts via services layer (CPU/GPU catalog, valuation rules, profiles, listings)
5. Computes adjusted prices and scores using shared domain logic

## Development Workflow

### When Adding Features
1. If adding domain logic (valuation rules, scoring algorithms), add to `packages/core/`
2. If adding API endpoints, add to `apps/api/dealbrain_api/api/`
3. If adding CLI commands, add to `apps/cli/dealbrain_cli/main.py`
4. If modifying database schema, create Alembic migration
5. Update frontend components in `apps/web/app/` or `apps/web/components/`

### Working with Database
- **Always** use async SQLAlchemy sessions for API code
- Use `session_scope()` context manager from `apps/api/dealbrain_api/db.py`
- Run migrations before testing schema changes: `make migrate`
- Alembic config: `alembic.ini` points to `apps/api/alembic/`

### Testing
- Backend tests in `tests/` use pytest with async support
- Test fixtures in `tests/conftest.py`
- Run focused tests: `poetry run pytest tests/test_custom_fields_service.py -v`

### Code Style
- Python: Black (line length 100), isort, ruff
- Pre-commit hooks configured in `.pre-commit-config.yaml`
- Run `make format` before committing

## Docker Compose Stack

Full stack includes:
- **db** (Postgres) - Port 5442
- **redis** - Port 6399
- **api** (FastAPI) - Port 8020
- **worker** (Celery) - Background task processing
- **web** (Next.js) - Port 3020
- **otel-collector** - OpenTelemetry collector
- **prometheus** - Port 9090
- **grafana** - Port 3021 (admin/admin)

Environment variables: `.env` for local development, `.env.example` for Docker.

## Key Files & Locations

- `pyproject.toml` - Python dependencies, Poetry scripts, tool configs (black, ruff, mypy)
- `package.json` - Monorepo root, defines pnpm workspace
- `apps/web/package.json` - Next.js dependencies
- `apps/api/dealbrain_api/settings.py` - FastAPI configuration via pydantic-settings
- `Makefile` - Common development tasks
