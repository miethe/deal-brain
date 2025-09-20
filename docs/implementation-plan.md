# Deal Brain MVP Implementation Plan

## 1. Objectives
Deliver a production-ready MVP of Deal Brain aligned with the PRD: a full-stack application that ingests listings, normalizes component value, provides dashboards/rankings, exposes API/CLI, and ships with Docker-based infrastructure plus setup documentation.

## 2. Architectural Overview
- **Monorepo layout**
  - `apps/api`: FastAPI service (REST + background workers), Alembic migrations, valuation engine, importers.
  - `apps/web`: Next.js 14 App Router frontend with Tailwind, shadcn/ui, TanStack Table, Tremor charts.
  - `apps/cli`: Python Typer CLI packaged with the backend domain layer.
  - `packages/core`: Shared Python domain logic (valuation engine, scoring, schemas) used by API & CLI.
  - `packages/js-ui`: Shared UI primitives (design tokens, hooks) consumed by the web app.
  - `infra`: Docker Compose, environment samples, deployment scripts, observability configs.
  - `data`: Seed CSV/JSON derived from the spreadsheet, fixtures for tests, snapshot baselines.
  - `tests`: Integration/system test harness (pytest for API, Playwright for E2E, smoke scripts).
- **Runtime stack**
  - Postgres 15 for persistence with SQLAlchemy ORM models + Alembic migrations.
  - Redis 7 for caching and Celery task queue (async valuation recompute, imports, analytics).
  - FastAPI with Pydantic v2 schemas for request/response validation.
  - Celery workers co-located with API container in dev; dedicated worker image for production.
  - Next.js frontend served separately (Node runtime) communicating with API via REST.
  - Observability: Prometheus metrics via `prometheus-fastapi-instrumentator`, structured logging with Loguru, OpenTelemetry traces (export to OTLP collector in infra).

## 3. Domain Model & Storage
- **Core tables**
  - `cpu`, `gpu`, `valuation_rule`, `profile`, `ports_profile`, `port`, `listing`, `listing_component` (normalized components), `listing_score_snapshot` (history), `import_job`, `task_run`, `user` (placeholder for future auth).
- **Schema management**: Alembic migrations; migration autogeneration with offline + online scripts; seeding pipeline invoked after migrations.
- **Data ingestion**
  - CLI/API importer parsing Excel → canonical CSV (pandas), stored in `data/imports`. Idempotent upsert by natural keys. Async variant via Celery for large imports.

## 4. Backend Services
- **Modules**
  - `config`: settings management via Pydantic BaseSettings, environment overlays.
  - `db`: SQLAlchemy session management, base classes, repository helpers.
  - `models`: ORM definitions for all entities.
  - `schemas`: Pydantic DTOs for API/CLI.
  - `valuation`: rule application, condition multipliers, GPU blending, scoring engine.
  - `services`: listing CRUD, catalog maintenance, profile application, dashboard aggregations.
  - `api`: FastAPI routers for listings, catalogs, profiles, valuation rules, rankings, dashboard, imports, health, tasks.
  - `workers`: Celery app, tasks for import, recompute scores, scheduled refreshes.
- **Validation & explainability**
  - Valuation engine returns detailed breakdown JSON; persisted per listing.
  - API endpoints expose explain payload and scoreboard metrics.

## 5. Frontend (Next.js)
- **Design system**: Tailwind + shadcn; theme tokens stored in `packages/js-ui` with CSS variables.
- **Pages/Routes**
  - `/` Dashboard with KPI cards, charts, top listings table.
  - `/listings` dynamic table with filters, bulk actions, add/edit dialogs.
  - `/listings/[id]` detail view with explain panel, history timeline.
  - `/profiles` management for scoring profiles (sliders, default selection).
  - `/valuation-rules` table with edit sheets, preview recalculation.
  - `/import` wizard for Excel/CSV ingestion + progress.
- **State/Data layer**
  - TanStack Query for API data fetching/caching.
  - Zod-based client schemas mirroring API contracts.
  - Charting with Tremor for distribution and share visuals.
  - Command palette (cmdk) for quick navigation/add listing.

## 6. CLI
- Python Typer app sharing domain services via `packages/core`.
- Commands: `import`, `add`, `list`, `explain`, `profiles switch`, `export` (JSON/CSV) aligning with PRD.
- Uses same settings (env var config) to connect to API DB or call API endpoints.

## 7. Infrastructure & DevEx
- Docker Compose services: `db` (postgres), `redis`, `api`, `worker`, `web`, `ingest` (optional), `otlp-collector`, `prometheus`, `grafana` (lightweight dashboards), `pgadmin` (optional).
- Makefile or Taskfile for common dev commands (`make up`, `make migrate`, `make seed`, etc.).
- Pre-commit hooks: formatting (ruff/black, isort), mypy, eslint, prettier, stylelint.
- CI pipeline (GitHub Actions) with matrix for backend/frontend tests, lint, type checking.
- `.env.example` plus docs for environment configuration.

## 8. Testing Strategy
- **Backend**: pytest with async test client, factory Boy fixtures, snapshot tests for valuation outputs vs spreadsheet baselines, API contract tests, importer tests.
- **Frontend**: Vitest/React Testing Library for components, Playwright for E2E core flows (add listing, adjust valuation rule, profile ordering change).
- **CLI**: golden file tests using pytest invoking Typer CLI runner.
- **Data**: seeding verification tests ensuring row counts & sample metrics align with Excel.

## 9. Delivery Phases
1. **Foundation**: repo scaffolding, tooling, Docker, base settings, dependency management.
2. **Data Layer**: SQLAlchemy models, Alembic migrations, seeds, importer pipeline.
3. **Domain Logic**: valuation engine, scoring, explain breakdown, composite profile calculations.
4. **API Delivery**: FastAPI routers for catalogs, listings, rankings, dashboard, tasks; background jobs integration.
5. **Frontend**: Next.js app with core pages, forms, tables, dashboards, explain UI.
6. **CLI & Automation**: Typer commands, export utilities, integration with API.
7. **Testing & Observability**: automated tests, lint, metrics/instrumentation, docs, final polish.

## 10. Documentation & Handoff
- `docs/setup.md`: dev env setup, docker usage, commands.
- `docs/architecture.md`: high-level architecture, module map, data flow diagrams.
- `docs/valuation-rules.md`: describing valuation config and extension.
- API reference generated via FastAPI OpenAPI + Redoc.
- Changelog seeded (`CHANGELOG.md`) using Keep a Changelog.

---

# Deal Brain Task Tracker
Status legend: ☐ Todo · ◐ In Progress · ☐● Blocked · ✔ Done

## Phase 1 — Foundation
- ✔ Repo scaffold with Poetry + pnpm workspaces
- ✔ Base Docker Compose, Makefile, `.env.example`
- ✔ Pre-commit, linting, formatting config

## Phase 2 — Data Layer
- ✔ Define SQLAlchemy models + Pydantic schemas
- ✔ Alembic initial migration + env setup
- ✔ Seed ingestion pipeline from Excel/CSV

## Phase 3 — Domain Logic
- ✔ Valuation engine (RAM/Storage/OS deductions)
- ✔ GPU normalization blending
- ✔ Composite scoring profiles application
- ✔ Explain JSON persistence & schema

## Phase 4 — API Delivery
- ☐ FastAPI app bootstrap (routing, DI, auth stub)
- ☐ Listings CRUD + valuation recompute
- ☐ Catalog endpoints (CPU/GPU/Rules/Profiles)
- ☐ Rankings & dashboard aggregation endpoints
- ☐ Import job orchestration + Celery tasks

## Phase 5 — Frontend
- ✔ Next.js App Router scaffold with Tailwind & shadcn
- ✔ Dashboard page + KPI cards
- ◐ Listings table + add/edit dialogs + explain view (edit flow pending)
- ◐ Profiles management UI (read-only, editing to follow)
- ☐ Valuation rules editor + preview
- ◐ Import experience revamp (multi-entity mapping, conflict resolution, Apple-tier UX)

## Phase 6 — CLI & Automation
- ✔ Typer CLI scaffold sharing domain layer
- ✔ Commands: import/add/top/explain/export
- ☐ Packaging config + distribution docs

## Phase 7 — Testing & Observability
- ◐ Backend pytest suite with fixtures & snapshots (initial valuation test)
- ☐ Frontend Vitest/RTL + Playwright E2E
- ☐ CLI tests
- ✔ Observability stack (metrics/logging/traces)
- ✔ Documentation (setup, architecture, valuation)

