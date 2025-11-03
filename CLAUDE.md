# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Deal Brain is a full-stack price-to-performance assistant for small form factor PCs. The system imports Excel workbooks containing PC listings, normalizes them, computes adjusted pricing based on component valuation rules, applies scoring profiles, and ranks deals with explainable breakdowns.

### Key Features

**Valuation System:**
- Color-coded pricing display with configurable thresholds (good deal, great deal, premium)
- Interactive valuation breakdown modals showing applied rules and adjustments
- Settings-based threshold configuration (ApplicationSettings model)

**Data Management:**
- Dynamic custom fields system with Global Fields UI
- Inline dropdown option creation without context switching
- Default value configuration for all field types
- CPU enrichment with benchmark scores (CPU Mark, Single-Thread, iGPU Mark)

**Performance Metrics:**
- Dual CPU Mark metrics (single-thread and multi-thread price efficiency)
- Base and adjusted valuations with automatic calculations
- Product metadata (manufacturer, series, model number, form factor)
- Structured ports management (USB-A, USB-C, HDMI, DisplayPort, etc.)
- Automatic metric recalculation on price or CPU changes
- PassMark benchmark data import from CSV

**UI/UX:**
- Memoized components for performance optimization
- Debounced search inputs (200ms)
- Accessible design (WCAG AA compliant, keyboard navigation, screen reader support)
- Responsive tables with column resizing, sorting, filtering


<!-- BEGIN SYMBOLS SECTION -->
# Agent Delegation Strategy

## Before Implementing: Explore First

**Always explore the codebase before building new features:**

```markdown
Task("codebase-explorer", "Find all existing [pattern] implementations to understand current conventions")
```

### Symbols vs Explore: Decision Framework

Based on validation testing (see `docs/testing/symbols_vs_explore_validation_report.md`):

**Use codebase-explorer (80% of tasks - 0.1s):**

- Quick "what and where" discovery (symbols-based)
- Finding specific functions/classes/components
- Getting file:line references
- Cost/speed critical tasks
- **Performance**: ~100+ symbols from multiple files in 0.1 seconds
- **Cost**: ~$0.001 per query

**Use explore subagent (20% of tasks - 2-3 min):**

- Understanding "how and why" with full context
- Generating implementation plans or ADRs
- Complex architectural analysis
- Test coverage and pattern analysis
- **Performance**: 300+ files analyzed in 2-3 minutes
- **Cost**: ~$0.01-0.02 per query

**Optimal Workflow (Phase 1 → Phase 2):**

```markdown
# Phase 1: Quick Discovery (0.1s) - ALWAYS START HERE
Task("codebase-explorer", "Find all [pattern] implementations")
→ Get instant symbol inventory
→ Identify key files

# Phase 2: Deep Analysis (2-3 min) - ONLY IF NEEDED
Task("explore", "Analyze [pattern] in [specific files from Phase 1]")
→ Get full context and patterns
```

### Symbol System for Token Efficiency

The codebase-explorer uses the {{PROJECT_NAME}} symbols system for **95-99% token reduction**:

- **Symbols**: Pre-generated metadata about all functions, classes, components, and types
- **Domain Chunking**: Separated by domain for targeted loading
- **Precise References**: Get exact file:line locations for navigation
- **Architectural Awareness**: Symbols tagged by layer for intelligent filtering
- **Test Separation**: Load test context only when debugging

**Performance Comparison:**

| Metric | Symbols (codebase-explorer) | Explore Subagent |
|--------|----------------------------|------------------|
| Duration | 0.1 seconds | 2-3 minutes |
| Best For | "What and where" | "How and why" |
| Token Efficiency | 95-99% reduction | Full context |
| Cost | ~$0.001 | ~$0.01-0.02 |

**Token Efficiency Example:**

```text
Traditional Approach:
- Read 5-10 similar files: ~200KB context
- Load related utilities: ~50KB context
Total: ~250KB

Symbol-Based Approach (via codebase-explorer):
- Query 20 relevant symbols: ~5KB context (0.1s)
- Load supporting context (15 symbols): ~3KB context
- On-demand lookups (10 symbols): ~2KB context
Total: ~10KB context (96% reduction)

Deep Analysis Approach (via explore):
- Analyze 300+ files: ~10,000+ LOC (2-3 min)
- Full patterns with code snippets: Complete context
```

**How it works:**

1. You delegate to codebase-explorer: `Task("codebase-explorer", "Find Button patterns")`
2. Codebase-explorer queries symbol files (token-efficient metadata)
3. You receive curated results with file:line references
4. You read only the specific files you need
5. If you need deeper understanding, delegate to explore with specific targets

**Key Insight**: Use symbols for 80% of quick lookups, reserve explore for 20% requiring deep understanding.

### Symbol Files

**Domain-Specific Files (Recommended):**
- `{{SYMBOLS_DIR}}/symbols-ui.json` - UI components library - Reusable React components, hooks, utilities. Customize directories to match your component library location. - 0 symbols
- `{{SYMBOLS_DIR}}/symbols-ui-tests.json` - UI test helpers (on-demand) - 0 symbols
- `{{SYMBOLS_DIR}}/symbols-web.json` - Next.js web application - App router pages, layouts, client/server components. Adjust directories for your Next.js structure. - 0 symbols
- `{{SYMBOLS_DIR}}/symbols-api.json` - Backend API layer - FastAPI routers, services, repositories, schemas. Use apiLayers for granular access by architectural layer. - 0 symbols
- `{{SYMBOLS_DIR}}/symbols-api-tests.json` - API test helpers (on-demand) - 0 symbols
- `{{SYMBOLS_DIR}}/symbols-cli.json` - Command-line interface utilities - CLI commands, argument parsing, user interaction. - 0 symbols

**API Layer Files (Granular Access):**
- `{{SYMBOLS_DIR}}/symbols-api-routers.json` - API route handlers - FastAPI routers, endpoints, request/response handling - 0 symbols
- `{{SYMBOLS_DIR}}/symbols-api-services.json` - Business logic services - Orchestration, validation, domain operations - 0 symbols
- `{{SYMBOLS_DIR}}/symbols-api-repositories.json` - Data access layer - Database queries, ORM operations, RLS enforcement - 0 symbols
- `{{SYMBOLS_DIR}}/symbols-api-schemas.json` - Data Transfer Objects - Pydantic models for API serialization and validation - 0 symbols
- `{{SYMBOLS_DIR}}/symbols-api-cores.json` - Core utilities - Auth, observability, middleware, error handling - 0 symbols

**All symbols include architectural layer tags** for intelligent filtering:
- API layers: `router`, `service`, `repository`, `schema`, `model`, `core`, `auth`, `middleware`, `observability`
- Frontend layers: `component`, `hook`, `page`, `util`
- Test layer: `test`

**See**: `/docs/development/symbols-best-practices.md` for comprehensive guidance.

<!-- END SYMBOLS SECTION -->

## Documentation Policy

### Core Principle: Document Only When Explicitly Needed

Documentation should **ONLY** be created when:
1. Explicitly tasked in an implementation plan, PRD, or user request
2. Absolutely necessary to provide essential information to users or developers
3. Part of a defined allowed documentation bucket (see below)

**More documentation ≠ better.** Unnecessary documentation creates debt, becomes outdated, and misleads future developers. When in doubt, ask: "Is this in an allowed bucket?" If not, don't create it.

### Strictly Prohibited Documentation

**DO NOT Create:**
- **Debugging Summaries**: Never document encountered bugs, errors, or debugging sessions as standalone docs
- **Unstructured Progress Docs**: Never create MULTIPLE scattered progress docs per phase (one per phase is allowed, see "Allowed Tracking Documentation")
- **Unorganized Context Files**: Never create context files outside the structured directories (see "Directory Structure")
- **Ad-Hoc Observation Logs**: Never create observation logs outside the monthly structure (use `.claude/worknotes/observations/observation-log-MM-YY.md`)
- **Session Notes as Docs**: Never publish personal notes, exploration logs, or investigation results as permanent documentation
- **Temporary Context as Docs**: Don't convert worknotes into permanent documentation without explicit need
- **Daily/Weekly Status Reports**: Don't create status update documents (use git commits and phase progress docs)

**Examples of What NOT to Create:**
```
❌ "2025-11-03-celery-event-loop-fix-context.md" - debugging summary (use git commit)
❌ "phase-1-3-progress.md" - consolidated multi-phase progress (use one per phase)
❌ "observations-week-1.md" - weekly observations (use monthly observation log)
❌ "issues-encountered-during-refactor.md" - debugging notes (use worknotes or commits)
❌ "why-we-changed-the-architecture.md" - exploration summary (use ADR or phase context)
❌ "random-context-notes.md" - unstructured notes (use organized structure)
```

**What IS Allowed (See "Allowed Tracking Documentation"):**
```
✅ ".claude/progress/listings-enhancements-v3/phase-2-progress.md" - ONE per phase
✅ ".claude/worknotes/listings-enhancements-v3/phase-2-context.md" - ONE per phase
✅ ".claude/worknotes/observations/observation-log-11-25.md" - monthly observations
✅ ".claude/worknotes/fixes/bug-fixes-tracking-11-25.md" - monthly bug fix tracking
```

**The Key Difference:**
- ❌ Multiple scattered files per phase → Creates documentation sprawl
- ✅ ONE structured file per phase → Organized, maintainable tracking
- ❌ Ad-hoc debugging summaries → Should be in git commits
- ✅ Structured monthly logs → Brief, organized, time-bounded

### Allowed Tracking Documentation

While permanent documentation should be minimized, **structured tracking documentation** is allowed when following these strict patterns:

**Progress Tracking (One Per Phase):**
- **Purpose**: Track implementation progress, completed tasks, blockers, and next steps for a specific phase of work
- **Location**: `.claude/progress/[prd-name]/phase-[N]-progress.md`
- **Limit**: ONE progress document per phase, not multiple scattered files
- **Required**: Only when working on multi-phase implementations from a PRD
- **Audience**: AI agents continuing work across sessions
- **Example**: `.claude/progress/listings-enhancements-v3/phase-2-progress.md`

**Context/Notes Documentation (One Per Phase):**
- **Purpose**: Document implementation decisions, technical notes, architecture considerations discovered during a phase
- **Location**: `.claude/worknotes/[prd-name]/phase-[N]-context.md`
- **Limit**: ONE context document per phase, organized by PRD name
- **Content**: Technical decisions, integration patterns, gotchas, architectural notes
- **Audience**: AI agents and developers who need to understand implementation choices
- **Example**: `.claude/worknotes/listings-enhancements-v3/phase-2-context.md`

**Monthly Observation Logs (Limited Exception):**
- **Purpose**: Track observations, learnings, patterns, and insights discovered during development
- **Location**: `.claude/worknotes/observations/observation-log-MM-YY.md`
- **Format**: Brief bullet points (1-2 lines per observation), one file per month
- **Content**: Pattern discoveries, performance insights, architectural learnings
- **Similar to**: Bug-fix tracking structure (monthly, concise, organized)
- **Example**: `.claude/worknotes/observations/observation-log-11-25.md`

**Other Changelog-Type Documents:**
- **When Allowed**: Only if explicitly called out in PRD, implementation plan, or user request
- **Examples**: CHANGELOG.md updates, release notes, version history
- **Requirement**: Must be part of the planned work, not created ad-hoc
- **Location**: Project root or `/docs/` as specified in the plan

**Key Principles for Tracking Docs:**
1. **One Per Phase**: Don't create multiple progress or context docs for the same phase
2. **Organized Structure**: Use consistent directory structure (see below)
3. **Explicit Need**: Only create when working on multi-phase implementations
4. **Concise Content**: Keep notes brief and actionable, not verbose essays
5. **Temporary Nature**: These are working documents, not permanent documentation

**When to Create Tracking Docs:**
- ✅ Working on multi-phase PRD implementation and need to track progress across sessions
- ✅ Documenting architectural decisions made during implementation (context notes)
- ✅ Recording monthly observations to improve future development patterns
- ❌ NOT for debugging sessions (use git commits instead)
- ❌ NOT for bug fix summaries (use monthly bug-fix tracking)
- ❌ NOT for exploration or investigation notes (keep in temporary worknotes)

### Directory Structure for Tracking Docs

When creating allowed tracking documentation, follow this **exact structure**:

```
.claude/
├── progress/                                    # Phase progress tracking
│   └── [prd-name]/                             # Organized by PRD
│       ├── phase-1-progress.md                 # ONE per phase
│       ├── phase-2-progress.md
│       └── phase-3-progress.md
│
├── worknotes/                                   # Implementation context & notes
│   ├── [prd-name]/                             # Organized by PRD
│   │   ├── phase-1-context.md                  # ONE per phase
│   │   ├── phase-2-context.md
│   │   └── phase-3-context.md
│   │
│   ├── fixes/                                   # Bug fix tracking
│   │   └── bug-fixes-tracking-MM-YY.md         # ONE per month
│   │
│   └── observations/                            # Development observations
│       └── observation-log-MM-YY.md            # ONE per month
│
└── agents/                                      # Agent-specific configurations
    └── [agent-name]/                           # Agent prompts and configs
```

**Example for Multi-Phase PRD Implementation:**

```
.claude/
├── progress/
│   └── listings-enhancements-v3/
│       ├── phase-1-progress.md          # ✅ Tracks Phase 1 tasks
│       ├── phase-2-progress.md          # ✅ Tracks Phase 2 tasks
│       └── phase-3-progress.md          # ✅ Tracks Phase 3 tasks
│
└── worknotes/
    ├── listings-enhancements-v3/
    │   ├── phase-1-context.md           # ✅ Phase 1 decisions/notes
    │   ├── phase-2-context.md           # ✅ Phase 2 decisions/notes
    │   └── phase-3-context.md           # ✅ Phase 3 decisions/notes
    │
    ├── fixes/
    │   └── bug-fixes-tracking-11-25.md  # ✅ November 2025 fixes
    │
    └── observations/
        └── observation-log-11-25.md     # ✅ November 2025 observations
```

**Naming Conventions:**

| Document Type | Naming Pattern | Example |
|--------------|----------------|---------|
| Phase Progress | `phase-[N]-progress.md` | `phase-2-progress.md` |
| Phase Context | `phase-[N]-context.md` | `phase-2-context.md` |
| Bug Fix Tracking | `bug-fixes-tracking-MM-YY.md` | `bug-fixes-tracking-11-25.md` |
| Observation Log | `observation-log-MM-YY.md` | `observation-log-11-25.md` |

**Directory Organization Rules:**

1. **By PRD Name**: Group all progress and context docs by the PRD they implement
2. **By Month**: Group bug fixes and observations by month (MM-YY format)
3. **One Per Phase**: Never create multiple progress or context docs for the same phase
4. **Consistent Naming**: Follow the exact naming patterns above
5. **No Nesting**: Don't create subdirectories within PRD folders (flat structure)

**Anti-Patterns to Avoid:**

```
❌ .claude/worknotes/2025-11-02-celery-event-loop-fix-context.md
   → Should be: git commit message or bug-fixes-tracking-11-25.md entry

❌ .claude/progress/listings-enhancements-v3/phase-1-progress-updated.md
   → Should be: Update existing phase-1-progress.md, not create new file

❌ .claude/worknotes/listings-enhancements-v3/phase-2-context-notes.md
   → Should be: phase-2-context.md (follow naming convention)

❌ .claude/worknotes/observations/nov-3-observations.md
   → Should be: observation-log-11-25.md (monthly, not daily)
```

**When Uncertain:**
- Ask: "Does this fit the allowed tracking structure?"
- If yes: Use the exact structure and naming above
- If no: It probably belongs in a git commit message or shouldn't be created

### Allowed Documentation Buckets

Only create documentation that falls into one of these categories:

**1. User Documentation**
- **Purpose**: Help end users accomplish tasks
- **Examples**: Setup guides, tutorials, how-to guides, troubleshooting, user walkthroughs
- **Location**: `/docs/guides/`, `/docs/user-guides/`

**2. Developer Documentation**
- **Purpose**: Help developers understand code and integrate with systems
- **Examples**: API documentation, SDK usage guides, integration guides, development setup
- **Location**: `/docs/api/`, `/docs/development/`, `/docs/integrations/`

**3. Architecture & Design Specifications**
- **Purpose**: Explain system design decisions and architecture
- **Examples**: Architecture Decision Records (ADRs), system diagrams, component specifications, design system docs
- **Location**: `/docs/architecture/`, `/docs/design/`

**4. README Files**
- **Purpose**: Document projects, packages, modules, and directories
- **Examples**: Project READMEs, package READMEs, feature READMEs
- **Location**: Root of project/package/module directory

**5. Configuration Documentation**
- **Purpose**: Explain how to configure and deploy systems
- **Examples**: Environment setup, deployment guides, configuration file documentation
- **Location**: `/docs/configuration/`, `/docs/deployment/`

**6. Test Documentation**
- **Purpose**: Document testing strategies and approaches
- **Examples**: Test plans, testing strategies, coverage goals, test data setup
- **Location**: `/docs/testing/`

**7. Product Documentation**
- **Purpose**: Define product requirements and implementation plans
- **Examples**: PRDs, implementation plans, feature specifications
- **Location**: `/docs/project_plans/`, `/docs/product/`

**8. Monthly Bug-Fix Context (LIMITED EXCEPTION)**
- **Purpose**: Brief reference of bug fixes completed in a month
- **Location**: `.claude/worknotes/fixes/` (single file per month: `bug-fixes-tracking-MM-YY.md`)
- **Format**: Very brief bullet points (1-2 lines per fix), no lengthy explanations
- **Content example**:
  ```markdown
  ---
  title: "Bug Fixes - November 2025"
  description: "Brief tracking of significant bug fixes completed"
  audience: [ai-agents]
  category: worknotes
  status: draft
  ---

  - Fixed Celery event loop conflicts in async tasks (commit: 8f93897)
  - Corrected DELETE endpoint path for listings (commit: 5b3f538)
  ```

### Frontmatter Requirements

**ALL new markdown documentation MUST include YAML frontmatter:**

```yaml
---
title: "Clear, Descriptive Title"
description: "Brief summary of what this documentation covers (1-2 sentences)"
audience: [ai-agents, developers, users, design, pm, qa]
tags: [relevant, tags, for, searchability]
created: 2025-11-03
updated: 2025-11-03
category: "documentation-category"
status: draft|review|published|deprecated
related:
  - /docs/path/to/related/doc.md
  - /docs/another/related/doc.md
---
```

**Frontmatter Fields:**

| Field | Purpose | Example |
|-------|---------|---------|
| `title` | Clear, searchable title | "Authentication API Documentation" |
| `description` | 1-2 sentence summary | "Comprehensive guide to auth endpoints and flows" |
| `audience` | Who should read this | `[developers, ai-agents]` or `[users, design]` |
| `tags` | Keywords for search | `[api, authentication, security, endpoints]` |
| `created` | Creation date | `2025-11-03` |
| `updated` | Last modification date | `2025-11-03` |
| `category` | Documentation bucket | `developer-documentation`, `user-guides`, `architecture` |
| `status` | Current state | `draft`, `review`, `published`, `deprecated` |
| `related` | Links to related docs | Array of relative file paths |

**Category Options**: `user-documentation`, `developer-documentation`, `architecture-design`, `api-documentation`, `configuration-deployment`, `test-documentation`, `product-planning`, `worknotes`

**Audience Options**: `users`, `developers`, `ai-agents`, `design`, `pm`, `qa`, `devops`

### Documentation vs. Worknotes

**Use `.claude/worknotes/` For:**
- Exploration and investigation logs
- Debugging sessions and findings
- Temporary implementation context
- Notes on things to remember
- Status updates and progress tracking

**Use `/docs/` For:**
- Permanent, published documentation in allowed buckets
- Content meant to be read by users or future developers
- Stable information unlikely to become outdated
- Officially supported guides and references

### When to Ask Before Documenting

1. **Is this in an allowed bucket?** If not, don't create it.
2. **Is this explicitly tasked?** If it wasn't requested, is it absolutely necessary?
3. **Will this become outdated?** If it documents a temporary state or debugging, it doesn't belong.
4. **Is there already documentation?** Update existing docs instead of creating new ones.
5. **Is this a worknote instead?** If it's exploration or debugging, it belongs in `.claude/worknotes/`.

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

# Performance metrics data population
poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv  # Import CPU benchmarks
poetry run python scripts/recalculate_all_metrics.py  # Recalculate performance metrics for all listings
poetry run python scripts/seed_sample_listings.py     # Create sample listings with metadata and ports

# Formula reference generation
poetry run python scripts/generate_formula_reference.py  # Generate comprehensive formula reference JSON
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
- `listings.py` - Listing CRUD, component sync, metrics application, performance calculations
- `ports.py` - Ports profile and port management for connectivity data
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
The system supports two import methods via a unified interface at `/dashboard/import`:

**URL-Based Import:**
1. Single URL form or bulk URL upload (CSV/JSON)
2. Adapters extract data from marketplace listings (eBay, Amazon, etc.)
3. Normalizer standardizes extracted data
4. Deduplication checks for existing listings
5. ListingsService upserts to database with provenance tracking

**File-Based Import:**
1. CLI command `poetry run dealbrain-cli import path/to/workbook.xlsx` or web upload
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

### Backend
- `apps/api/dealbrain_api/models/core.py` - SQLAlchemy models (CPU, GPU, Listing, ApplicationSettings, etc.)
- `apps/api/dealbrain_api/services/` - Business logic layer (listings, custom_fields, settings)
- `apps/api/dealbrain_api/api/` - FastAPI endpoints (organized by domain)
- `apps/api/alembic/versions/` - Database migrations
- `apps/api/dealbrain_api/settings.py` - FastAPI configuration via pydantic-settings

### Frontend
- `apps/web/app/` - Next.js 14 App Router pages
- `apps/web/components/` - React components (organized by domain: listings, valuation, forms, ui)
- `apps/web/lib/` - Utilities (valuation-utils, cpu-options, api clients)
- `apps/web/hooks/` - Custom React hooks (useValuationThresholds, useFieldOptions, etc.)
- `apps/web/components/ui/` - Reusable UI components (shadcn/ui based)

### Configuration
- `pyproject.toml` - Python dependencies, Poetry scripts, tool configs (black, ruff, mypy)
- `package.json` - Monorepo root, defines pnpm workspace
- `apps/web/package.json` - Next.js dependencies
- `Makefile` - Common development tasks
