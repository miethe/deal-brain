# Deal Brain — Architecture Overview

## Monorepo Structure
```
apps/
  api/              # FastAPI application, Alembic migrations, services
  cli/              # Typer-based command line tools
  web/              # Next.js 14 App Router frontend
packages/
  core/             # Shared domain logic (valuation, scoring, schemas)
infra/              # Dockerfiles, observability config
```

## Backend
- **FastAPI** with async SQLAlchemy sessions (`asyncpg`) and Alembic migrations.
- **Domain logic** lives in `packages/core` for reuse across API and CLI:
  - `valuation.py`: adjustable component rules → adjusted price breakdowns.
  - `scoring.py`: composite profile weighting, $/metric helpers.
  - `schemas/`: Pydantic contracts shared across transports.
- **Services** orchestrate persistence + domain logic (`apps/api/dealbrain_api/services`).
- **Import pipeline** parses the Excel workbook with pandas, generates `SpreadsheetSeed`, and upserts via shared services.
- **Observability**: Prometheus instrumentation via `prometheus-fastapi-instrumentator`; OTLP collector + Prometheus + Grafana shipped in Docker Compose.

## Frontend
- Next.js 14 App Router with Tailwind + lightweight shadcn-style primitives.
- React Query used for data fetching (`NEXT_PUBLIC_API_URL`), matching REST endpoints.
- Dashboard, listings table, valuation explain view, and import workflow already wired to the API.
- Component library (`packages/js-ui`) holds cross-app tokens and future shared primitives.

## CLI
- Typer commands share the same domain modules:
  - `import` seeds the database from Excel.
  - `add`, `top`, `explain`, `export` operate through SQLAlchemy sessions + valuation engine.

## Data Model Highlights
- Core tables: `cpu`, `gpu`, `valuation_rule`, `profile`, `ports_profile`, `listing`, `listing_component`, `listing_score_snapshot`, `import_job`, `task_run`.
- Enum types capture component categories, metrics, conditions, and listing statuses.
- Listings persist the explainable `valuation_breakdown` JSON for UI disclosure and CLI exports.

## Execution Modes
- **Local development**: `make up` runs API, web, worker, Postgres, Redis, observability stack.
- **Backend-only workflows**: CLI commands interact directly with the database using the shared services.
- **Future extensions**: Celery worker already scaffolded; add tasks for scheduled score refresh or import jobs.
