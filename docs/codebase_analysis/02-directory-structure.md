# Directory Structure

## Table of Contents
1. [Root Level Structure](#root-level-structure)
2. [apps/ Directory](#apps-directory)
3. [packages/ Directory](#packages-directory)
4. [Key Directories by Category](#key-directories-by-category)
5. [Configuration Files](#configuration-files)
6. [Quick Reference](#quick-reference)

---

## Root Level Structure

The Deal Brain codebase is organized as a monorepo with clear separation of concerns:

```
deal-brain/
├── apps/                   # Application code (API, CLI, Web)
├── packages/               # Shared libraries and domain logic
├── tests/                  # Test suites
├── docs/                   # Documentation
├── scripts/                # Utility scripts for data import and maintenance
├── infra/                  # Infrastructure configuration (Docker, observability)
├── data/                   # Sample data and baseline configurations
├── .claude/                # Claude AI assistant configuration
├── .github/                # GitHub configuration and workflows
├── pyproject.toml          # Python dependencies and project configuration
├── package.json            # JavaScript workspace configuration
├── Makefile                # Common development tasks
└── alembic.ini             # Database migration configuration
```

### Monorepo Organization

Deal Brain uses a hybrid monorepo structure:
- **Python**: Managed by Poetry, with dependencies in `pyproject.toml`
- **JavaScript**: Managed by pnpm workspaces, with workspace config in root `package.json`
- **Shared Code**: Domain logic in `packages/core/` used by both API and CLI

---

## apps/ Directory

The `apps/` directory contains all runnable applications. Each app is self-contained with its own dependencies and configuration.

### apps/api/ - FastAPI Backend

```
apps/api/
├── dealbrain_api/
│   ├── api/                    # API endpoints (FastAPI routes)
│   │   ├── __init__.py         # Router registration
│   │   ├── baseline.py         # Baseline valuation endpoints
│   │   ├── catalog.py          # Component catalog endpoints (CPUs, GPUs)
│   │   ├── custom_fields.py    # Dynamic field management
│   │   ├── listings.py         # Listing CRUD and valuation
│   │   ├── rules.py            # Valuation rules management
│   │   ├── imports.py          # Excel import endpoints
│   │   ├── health.py           # Health check endpoint
│   │   ├── metrics.py          # Prometheus metrics
│   │   ├── dashboard.py        # Dashboard statistics
│   │   ├── rankings.py         # Listing rankings
│   │   ├── admin.py            # Admin operations
│   │   ├── settings.py         # Application settings
│   │   └── schemas/            # API-specific request/response schemas
│   │       ├── listings.py
│   │       ├── custom_fields.py
│   │       ├── fields.py
│   │       └── imports.py
│   │
│   ├── services/               # Business logic layer
│   │   ├── listings.py         # Listing operations, metric calculations
│   │   ├── rules.py            # Valuation rule management
│   │   ├── rule_evaluation.py  # Rule evaluation engine
│   │   ├── rule_preview.py     # Preview rule impact before applying
│   │   ├── ruleset_packaging.py # Export/import rulesets
│   │   ├── baseline_loader.py  # Load baseline rulesets from JSON
│   │   ├── baseline_audit.py   # Audit trail for baseline changes
│   │   ├── baseline_metrics.py # Metrics for baseline valuations
│   │   ├── component_catalog.py # CPU/GPU catalog management
│   │   ├── custom_fields.py    # Dynamic field operations
│   │   ├── field_registry.py   # Field metadata registration
│   │   ├── field_metadata.py   # Field metadata queries
│   │   ├── ports.py            # Ports profile management
│   │   ├── passmark.py         # PassMark benchmark data integration
│   │   ├── settings.py         # Application settings service
│   │   ├── admin_tasks.py      # Background task management
│   │   ├── custom_fields_backfill.py # Data migration utilities
│   │   └── imports/            # Excel import pipeline
│   │       ├── service.py      # Main import orchestration
│   │       ├── specs.py        # Component spec parsing
│   │       └── utils.py        # Import utilities
│   │
│   ├── models/                 # SQLAlchemy database models
│   │   ├── core.py             # All database tables (CPU, GPU, Listing, etc.)
│   │   └── baseline_audit.py   # Baseline audit log model
│   │
│   ├── schemas/                # Pydantic schemas (API-level)
│   │   └── rules.py            # Rule-specific schemas
│   │
│   ├── validation/             # Validation logic
│   │   └── rules_validation.py # Validate rule structures
│   │
│   ├── tasks/                  # Celery background tasks
│   │   ├── __init__.py         # Task registration
│   │   └── baseline.py         # Baseline-related tasks
│   │
│   ├── cli/                    # CLI commands for API operations
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   └── baselines.py        # Baseline import CLI
│   │
│   ├── importers/              # Data importers
│   │   └── universal.py        # Universal Excel importer
│   │
│   ├── seeds/                  # Database seeding
│   │   ├── __init__.py
│   │   └── component_catalog.py # Seed component catalog
│   │
│   ├── db.py                   # Database session management
│   ├── settings.py             # FastAPI configuration
│   └── main.py                 # Application entry point
│
└── alembic/                    # Database migrations
    ├── versions/               # Migration files
    │   ├── 0019_add_baseline_audit_log.py
    │   ├── 0018_add_rule_group_metadata.py
    │   ├── 0017_ram_and_storage_profiles.py
    │   └── ... (older migrations)
    └── env.py                  # Alembic configuration
```

**Key Files:**
- `dealbrain_api/main.py` - FastAPI app initialization and router registration
- `dealbrain_api/db.py` - Database session factory and context managers
- `dealbrain_api/models/core.py` - All database tables in one file
- `dealbrain_api/services/` - Business logic layer, orchestrates domain logic and database

**When to Work Here:**
- Adding new API endpoints
- Implementing business logic (services layer)
- Creating database migrations
- Adding background tasks

---

### apps/cli/ - Command Line Interface

```
apps/cli/
└── dealbrain_cli/
    ├── __init__.py
    ├── main.py                 # Typer CLI entry point
    └── commands/               # CLI command groups
        ├── __init__.py
        └── rules.py            # Rule management commands
```

**Key Files:**
- `main.py` - CLI entry point with Typer commands (add, top, explain, export, import)

**When to Work Here:**
- Adding new CLI commands
- Building interactive terminal tools
- Batch operations on data

**Note:** The CLI shares domain logic with the API through `packages/core/`.

---

### apps/web/ - Next.js Frontend

```
apps/web/
├── app/                        # Next.js 14 App Router pages
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Home page (redirects to /listings)
│   ├── globals.css             # Global styles
│   │
│   ├── listings/               # Listings feature
│   │   ├── page.tsx            # Main listings page
│   │   ├── new/page.tsx        # Create new listing
│   │   ├── [id]/page.tsx       # Listing detail page
│   │   └── _components/        # Listings page components
│   │       ├── catalog-tab.tsx
│   │       ├── view-switcher.tsx
│   │       ├── listings-filters.tsx
│   │       ├── master-detail-view/ # Master-detail layout
│   │       │   ├── index.tsx
│   │       │   ├── master-list.tsx
│   │       │   ├── detail-panel.tsx
│   │       │   ├── compare-drawer.tsx
│   │       │   ├── key-value.tsx
│   │       │   └── kpi-metric.tsx
│   │       ├── dense-list-view/    # Compact table layout
│   │       │   ├── index.tsx
│   │       │   └── dense-table.tsx
│   │       └── grid-view/          # Card grid layout
│   │           ├── index.tsx
│   │           ├── listing-card.tsx
│   │           └── performance-badges.tsx
│   │
│   ├── valuation-rules/        # Valuation rules feature
│   │   ├── page.tsx            # Rules management page
│   │   └── _components/
│   │       └── basic-mode-tabs.tsx
│   │
│   ├── global-fields/          # Custom fields management
│   │   └── page.tsx
│   │
│   ├── import/                 # Import wizard
│   │   └── page.tsx
│   │
│   ├── admin/                  # Admin panel
│   │   └── page.tsx
│   │
│   └── profiles/               # Scoring profiles
│       └── page.tsx
│
├── components/                 # Reusable React components
│   ├── listings/               # Listing-related components
│   │   ├── listings-table.tsx  # Main listings table
│   │   ├── add-listing-form.tsx
│   │   ├── add-listing-modal.tsx
│   │   ├── listing-details-dialog.tsx
│   │   ├── listing-overview-modal.tsx
│   │   ├── listing-valuation-tab.tsx
│   │   ├── valuation-breakdown-modal.tsx
│   │   ├── valuation-mode-toggle.tsx
│   │   ├── quick-edit-dialog.tsx
│   │   ├── cpu-details-modal.tsx
│   │   ├── cpu-tooltip.tsx
│   │   ├── cpu-info-panel.tsx
│   │   ├── ports-display.tsx
│   │   ├── ports-builder.tsx
│   │   ├── dual-metric-cell.tsx
│   │   └── listing-formatters.ts
│   │
│   ├── valuation/              # Valuation rules components
│   │   ├── valuation-rules-table.tsx
│   │   ├── rule-builder-modal.tsx
│   │   ├── ruleset-builder-modal.tsx
│   │   ├── ruleset-card.tsx
│   │   ├── rule-group-form-modal.tsx
│   │   ├── basic-valuation-form.tsx
│   │   ├── baseline-field-card.tsx
│   │   ├── diff-adopt-wizard.tsx
│   │   ├── preview-impact-panel.tsx
│   │   ├── condition-row.tsx
│   │   ├── condition-group.tsx
│   │   └── action-builder.tsx
│   │
│   ├── forms/                  # Form components
│   │   ├── combobox.tsx        # Searchable select
│   │   ├── ram-spec-selector.tsx
│   │   └── storage-profile-selector.tsx
│   │
│   ├── custom-fields/          # Custom fields components
│   │   ├── global-fields-table.tsx
│   │   └── global-fields-data-tab.tsx
│   │
│   ├── dashboard/              # Dashboard components
│   │   └── dashboard-summary.tsx
│   │
│   ├── ui/                     # Base UI components (shadcn/ui)
│   │   ├── badge.tsx
│   │   ├── dialog.tsx
│   │   ├── sheet.tsx
│   │   ├── tabs.tsx
│   │   ├── tooltip.tsx
│   │   ├── toast.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── scroll-area.tsx
│   │   ├── data-grid.tsx       # Advanced data table
│   │   ├── empty-state.tsx
│   │   ├── modal-shell.tsx
│   │   ├── info-tooltip.tsx
│   │   ├── smart-dropdown.tsx
│   │   └── theme-toggle.tsx
│   │
│   ├── app-shell.tsx           # Main layout with navigation
│   └── error-boundary.tsx      # Error handling
│
├── hooks/                      # Custom React hooks
│   ├── use-baseline-overrides.ts # Manage baseline field overrides
│   ├── use-url-sync.ts         # Sync state with URL query params
│   ├── use-valuation-thresholds.ts # Color thresholds for pricing
│   ├── use-field-options.ts    # Dynamic field options
│   ├── use-unsaved-changes.ts  # Warn before leaving unsaved forms
│   └── use-toast.ts            # Toast notifications
│
├── lib/                        # Utility functions and API clients
│   ├── utils.ts                # General utilities (cn, API_URL)
│   ├── analytics.ts            # Analytics utilities
│   ├── component-catalog.ts    # Component catalog utilities
│   ├── valuation-utils.ts      # Valuation calculation helpers
│   ├── valuation-metrics.ts    # Metrics computation
│   ├── cpu-options.ts          # CPU dropdown options
│   ├── dropdown-utils.ts       # Dropdown utilities
│   └── api/                    # API client functions
│       ├── listings.ts         # Listings API calls
│       ├── rules.ts            # Rules API calls
│       ├── baseline.ts         # Baseline API calls
│       ├── entities.ts         # Entity API calls
│       └── admin.ts            # Admin API calls
│
├── stores/                     # Zustand state management
│   └── catalog-store.ts        # Catalog state (view mode, filters)
│
├── types/                      # TypeScript type definitions
│   └── baseline.ts             # Baseline-specific types
│
├── __tests__/                  # Frontend tests
│   └── listing-valuation-tab.test.tsx
│
├── public/                     # Static assets
├── middleware.ts               # Next.js middleware
├── next.config.js              # Next.js configuration
├── tailwind.config.ts          # Tailwind CSS configuration
├── tsconfig.json               # TypeScript configuration
└── package.json                # Frontend dependencies
```

**Key Files:**
- `app/layout.tsx` - Root layout with React Query provider, theme provider
- `components/app-shell.tsx` - Navigation shell used across pages
- `lib/utils.ts` - Utility functions, exports `API_URL` for backend calls
- `stores/catalog-store.ts` - Zustand store for catalog state management

**When to Work Here:**
- Adding new pages or routes
- Creating reusable components
- Implementing UI features
- Building forms and data tables
- Adding API integrations

---

## packages/ Directory

Shared code that can be used by multiple applications.

### packages/core/ - Shared Domain Logic

```
packages/core/
└── dealbrain_core/
    ├── __init__.py
    ├── enums.py                # Shared enums (ComponentType, Condition, etc.)
    ├── valuation.py            # Core valuation logic
    ├── scoring.py              # Scoring calculations
    ├── rule_evaluator.py       # Rule evaluation engine (legacy)
    ├── gpu.py                  # GPU utilities
    │
    ├── rules/                  # Modern rule system
    │   ├── __init__.py
    │   ├── evaluator.py        # Rule evaluation engine
    │   ├── conditions.py       # Condition matching logic
    │   ├── actions.py          # Action application logic
    │   ├── formula.py          # Formula evaluation
    │   └── packaging.py        # Ruleset packaging/export
    │
    └── schemas/                # Pydantic schemas (domain-level)
        ├── __init__.py
        ├── base.py             # Base schemas
        ├── baseline.py         # Baseline valuation schemas
        ├── catalog.py          # Component catalog schemas
        ├── custom_field.py     # Custom field schemas
        ├── imports.py          # Import schemas
        └── listing.py          # Listing schemas
```

**Key Principles:**
- **No Framework Dependencies**: Code here should not import FastAPI, SQLAlchemy, or Next.js
- **Pure Functions**: Domain logic should be testable without database or HTTP
- **Shared by API and CLI**: Both apps import from this package

**When to Work Here:**
- Adding new valuation rules logic
- Implementing scoring algorithms
- Creating domain-level schemas
- Building reusable business logic

---

### packages/js-ui/ - Shared UI Components (Experimental)

```
packages/js-ui/
├── src/
│   └── index.ts
├── package.json
└── tsconfig.json
```

**Note:** This package is currently experimental and not widely used.

---

## Key Directories by Category

### Backend Core

**Database Models**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`
- All SQLAlchemy models in one file
- Tables: CPU, GPU, Listing, ValuationRule, Profile, ApplicationSettings, etc.

**API Endpoints**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/`
- FastAPI route handlers
- Organized by domain (listings, rules, catalog)

**Services Layer**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/`
- Business logic orchestration
- Coordinates domain logic, database, and external systems
- Key services: `listings.py`, `rules.py`, `rule_evaluation.py`, `baseline_loader.py`

**Migrations**: `/mnt/containers/deal-brain/apps/api/alembic/versions/`
- Alembic database migrations
- Named with sequential numbers: `0019_add_baseline_audit_log.py`

---

### Frontend Core

**Pages**: `/mnt/containers/deal-brain/apps/web/app/`
- Next.js 14 App Router pages
- File-based routing (e.g., `listings/page.tsx` -> `/listings`)

**Components**: `/mnt/containers/deal-brain/apps/web/components/`
- Organized by feature (listings, valuation, forms)
- Base UI components in `ui/` subdirectory

**Hooks**: `/mnt/containers/deal-brain/apps/web/hooks/`
- Custom React hooks for state management and side effects

**API Clients**: `/mnt/containers/deal-brain/apps/web/lib/api/`
- Functions that call backend API endpoints
- Used by React Query hooks

**State Management**: `/mnt/containers/deal-brain/apps/web/stores/`
- Zustand stores for global state

---

### Domain Logic

**Core Package**: `/mnt/containers/deal-brain/packages/core/dealbrain_core/`
- Framework-agnostic business logic
- Shared by API and CLI
- Key files: `valuation.py`, `scoring.py`, `rules/evaluator.py`

---

### Infrastructure

**Docker Configurations**: `/mnt/containers/deal-brain/infra/`
- `api/Dockerfile` - FastAPI backend image
- `web/Dockerfile` - Next.js frontend image
- `worker/Dockerfile` - Celery worker image
- `otel/config.yaml` - OpenTelemetry collector configuration
- `prometheus/prometheus.yml` - Prometheus metrics configuration

**When to Work Here:**
- Modifying Docker builds
- Updating observability configuration
- Changing Prometheus scrape targets

---

### Documentation

**Structure**: `/mnt/containers/deal-brain/docs/`
```
docs/
├── codebase_analysis/          # Codebase documentation
│   ├── 01-architecture-overview.md
│   └── 02-directory-structure.md (this file)
│
├── architecture/               # Architecture decisions
│   ├── valuation-rules.md
│   └── decisions/              # ADRs (Architecture Decision Records)
│       ├── ADR-007-catalog-state-management.md
│       └── ADR-008-virtual-scrolling-strategy.md
│
├── project_plans/              # Feature planning documents
│   ├── valuation-rules/
│   ├── enhancements/
│   └── requests/
│
├── user-guide/                 # User-facing documentation
│   ├── basic-valuation-mode.md
│   ├── catalog-views.md
│   └── performance-metrics.md
│
├── developer/                  # Developer guides
│   └── baseline-json-format.md
│
├── api/                        # API documentation
│   └── ruleset-packaging-baseline.md
│
├── testing/                    # Testing documentation
│   └── baseline-deferred-tests.md
│
├── technical/                  # Technical specifications
│   └── core-fields-mapping.md
│
└── guides/                     # How-to guides
    └── ram-storage-catalog.md
```

**When to Work Here:**
- Adding feature documentation
- Writing user guides
- Creating architecture decision records (ADRs)

---

### Testing

**Structure**: `/mnt/containers/deal-brain/tests/`
```
tests/
├── conftest.py                 # Pytest fixtures and configuration
│
├── api/                        # API endpoint tests
│   └── test_rules_api.py
│
├── services/                   # Service layer tests
│   ├── test_rules_service.py
│   ├── test_rule_evaluation.py
│   ├── test_baseline_loader.py
│   └── test_ruleset_packaging.py
│
├── core/                       # Domain logic tests
│   └── test_rule_conditions.py
│
├── tasks/                      # Background task tests
│   └── test_enqueue_recalculation.py
│
├── e2e/                        # End-to-end tests (Playwright)
│   ├── listings.spec.ts
│   ├── data-grid.spec.ts
│   └── global-fields.spec.ts
│
├── test_valuation.py           # Valuation logic tests
├── test_listing_metrics.py     # Metrics calculation tests
├── test_custom_fields_service.py
└── test_custom_fields_integration.py
```

**Key Files:**
- `conftest.py` - Shared test fixtures (database session, test data)

**When to Work Here:**
- Adding test coverage for new features
- Writing integration tests
- Creating end-to-end test scenarios

---

### Scripts

**Structure**: `/mnt/containers/deal-brain/scripts/`
```
scripts/
├── import_passmark_data.py     # Import CPU benchmark data from CSV
├── recalculate_all_metrics.py # Recalculate performance metrics
├── recalculate_cpu_marks.py    # Update CPU mark scores
├── update_cpus_from_passmark.py
├── seed_sample_listings.py     # Create sample data
├── fix_baseline_field_types.py # Data migration script
├── import_entities.py          # Import entities from CSV/JSON
├── import_libraries.py
│
└── templates/                  # CSV/JSON templates
    ├── README.md
    ├── cpu.csv / cpu.json
    ├── gpu.csv / gpu.json
    ├── listing.csv / listing.json
    ├── profile.csv / profile.json
    └── ports_profile.csv / ports_profile.json
```

**When to Work Here:**
- Creating data migration scripts
- Building import utilities
- Writing maintenance scripts

**Usage:**
```bash
poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv
poetry run python scripts/recalculate_all_metrics.py
```

---

### Data

**Structure**: `/mnt/containers/deal-brain/data/`
```
data/
├── baselines/
│   └── baseline-v1.0.json      # Baseline valuation ruleset
├── deal_brain_valuation_rules.json
├── passmark_sample.csv         # Sample PassMark data
└── jsonformatter.json
```

**When to Work Here:**
- Adding baseline rulesets
- Storing sample data for testing
- Maintaining reference data files

---

### Claude Configuration

**Structure**: `/mnt/containers/deal-brain/.claude/`
```
.claude/
├── commands/                   # Custom Claude commands
│   ├── analyze/
│   │   ├── analyze-codebase.md
│   │   ├── check-file.md
│   │   └── architecture-review.md
│   ├── plan/
│   │   ├── plan_requests.md
│   │   └── plan_artifacts.md
│   └── ai/
│       ├── lyra.md
│       ├── session-learning-capture.md
│       └── memory-spring-cleaning.md
│
├── agents/                     # Agent personas
│   ├── architects/             # Architecture specialists
│   ├── dev-team/               # Development specialists
│   ├── ui-ux/                  # UI/UX specialists
│   ├── tech-writers/           # Documentation specialists
│   ├── ai/                     # AI/ML specialists
│   └── web-optimize-team/      # Performance specialists
│
├── progress/                   # Implementation tracking
│   ├── basic-valuation-enhance-progress.md
│   ├── baseline-field-type-fix.md
│   └── ui-enhancements-context.md
│
└── worknotes/                  # Work notes and context
    └── listing-link-valuation.md
```

**Purpose**: Configuration for Claude Code assistant interactions

---

## Configuration Files

### Root Configuration

**pyproject.toml** - Python project configuration
- Poetry dependencies
- Tool configurations (black, ruff, pytest, mypy)
- Poetry scripts (CLI entry points)

**package.json** - JavaScript workspace configuration
- pnpm workspace definition
- Root-level scripts

**Makefile** - Development task automation
- Common commands: `make setup`, `make up`, `make test`, `make migrate`

**alembic.ini** - Database migration configuration
- Points to `apps/api/alembic/` for migrations

**docker-compose.yml** - Local development stack
- Services: db, redis, api, worker, web, prometheus, grafana

**.env.example** - Environment variable template

---

### Application Configuration

**Backend (FastAPI)**
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/settings.py` - FastAPI configuration via pydantic-settings
- `/mnt/containers/deal-brain/apps/api/alembic/env.py` - Alembic migration environment

**Frontend (Next.js)**
- `/mnt/containers/deal-brain/apps/web/next.config.js` - Next.js configuration
- `/mnt/containers/deal-brain/apps/web/tailwind.config.ts` - Tailwind CSS configuration
- `/mnt/containers/deal-brain/apps/web/tsconfig.json` - TypeScript configuration

**Core Package**
- `/mnt/containers/deal-brain/packages/core/pyproject.toml` - Core package dependencies

---

## Quick Reference

### Where to Find Things

**Adding a new API endpoint?**
- Create route handler in `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/`
- Add business logic in `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/`
- Register router in `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/__init__.py`

**Adding a new page to the frontend?**
- Create `page.tsx` in `/mnt/containers/deal-brain/apps/web/app/[route-name]/`
- Add components in `/mnt/containers/deal-brain/apps/web/components/`
- Create API client functions in `/mnt/containers/deal-brain/apps/web/lib/api/`

**Adding domain logic?**
- Put pure business logic in `/mnt/containers/deal-brain/packages/core/dealbrain_core/`
- Add schemas in `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/`
- Create tests in `/mnt/containers/deal-brain/tests/core/`

**Adding a database table?**
- Add model to `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`
- Generate migration: `poetry run alembic revision --autogenerate -m "description"`
- Apply migration: `make migrate`

**Adding a CLI command?**
- Add command to `/mnt/containers/deal-brain/apps/cli/dealbrain_cli/main.py` or create in `commands/`

**Adding tests?**
- Backend: `/mnt/containers/deal-brain/tests/`
- Frontend: `/mnt/containers/deal-brain/apps/web/__tests__/`
- E2E: `/mnt/containers/deal-brain/tests/e2e/`

**Adding documentation?**
- User guide: `/mnt/containers/deal-brain/docs/user-guide/`
- Developer guide: `/mnt/containers/deal-brain/docs/developer/`
- Architecture: `/mnt/containers/deal-brain/docs/architecture/`

---

## Navigation Tips

### Finding Related Files

When working on a feature, you'll typically touch:
1. **Backend**: `api/` endpoint + `services/` logic + `models/core.py` (if schema changes)
2. **Frontend**: `app/` page + `components/` + `lib/api/` client
3. **Domain**: `packages/core/` for shared business logic
4. **Tests**: `tests/` for backend, `__tests__/` for frontend

### Common Workflows

**Adding a new listing field:**
1. Update `Listing` model in `apps/api/dealbrain_api/models/core.py`
2. Generate migration: `poetry run alembic revision --autogenerate -m "add field"`
3. Update service in `apps/api/dealbrain_api/services/listings.py`
4. Update API schema in `apps/api/dealbrain_api/api/schemas/listings.py`
5. Update frontend type in `apps/web/components/listings/`
6. Add to form/table in `apps/web/components/listings/`

**Adding a valuation rule:**
1. Add domain logic in `packages/core/dealbrain_core/rules/`
2. Update service in `apps/api/dealbrain_api/services/rule_evaluation.py`
3. Add tests in `tests/core/`
4. Update frontend in `apps/web/components/valuation/`

---

**Previous:** [Architecture Overview](./01-architecture-overview.md)

**Next:** API Documentation (coming soon)
