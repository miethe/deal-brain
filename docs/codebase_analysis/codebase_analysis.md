# Deal Brain: Comprehensive Codebase Analysis

**Generated:** 2025-10-14
**Version:** 0.1.0
**License:** MIT

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](./01-architecture-overview.md)
3. [Directory Structure](./02-directory-structure.md)
4. [Backend Architecture](./03-backend-architecture.md)
5. [Frontend Architecture](./04-frontend-architecture.md)
6. [Database Schema](./05-database-schema.md)
7. [API Documentation](./06-api-documentation.md)
8. [Shared Domain Logic](./07-shared-domain-logic.md)
9. [DevOps & Infrastructure](./08-devops-infrastructure.md)
10. [Technology Stack](./09-technology-stack.md)
11. [Key Insights & Recommendations](./10-insights-recommendations.md)

---

## 1. Project Overview

### Project Type
**Deal Brain** is a full-stack web application designed as a price-to-performance intelligence system for Small Form Factor (SFF) PCs. It combines:
- A data-driven valuation engine
- Component catalog management
- Excel workbook import capabilities
- Real-time performance metrics
- Rule-based pricing adjustments

### Purpose
The application helps users:
- Import PC listing data from Excel workbooks
- Normalize and enrich listings with CPU/GPU benchmark data
- Apply configurable valuation rules to compute adjusted prices
- Rank deals based on customizable scoring profiles
- Visualize pricing trends and performance metrics
- Make informed purchasing decisions

### Key Features

#### Core Functionality
- **Component Catalog**: Comprehensive database of CPUs, GPUs, RAM specs, and storage profiles
- **Valuation Engine**: Rule-based system for computing adjusted prices based on components and condition
- **Performance Metrics**: CPU Mark (single/multi-thread), GPU scores, price-per-performance ratios
- **Scoring Profiles**: Weighted metric system for ranking listings
- **Import Pipeline**: Excel workbook parsing and normalization
- **Custom Fields**: Dynamic field system for extending entities (listings, CPUs, GPUs)

#### Advanced Features
- **Baseline Valuation**: Packaged ruleset system for consistent pricing standards
- **Rule Groups**: Organized valuation rules by component type (CPU, RAM, storage, etc.)
- **Ports Management**: Detailed I/O connectivity tracking
- **Metadata Enrichment**: Manufacturer, series, model number, form factor
- **PassMark Integration**: Automated CPU benchmark data import
- **Real-time Preview**: Live valuation impact preview before applying rules

### Tech Stack Summary

**Backend:**
- Python 3.11+
- FastAPI (async web framework)
- SQLAlchemy 2.0 (async ORM)
- PostgreSQL (primary database)
- Redis (caching & Celery broker)
- Celery (async task processing)

**Frontend:**
- TypeScript
- Next.js 14 (App Router)
- React 18
- TanStack Query (data fetching)
- Radix UI (accessible components)
- Tailwind CSS (styling)
- Zustand (state management)

**Infrastructure:**
- Docker & Docker Compose
- Prometheus (metrics)
- Grafana (observability)
- OpenTelemetry (tracing)

### Architecture Pattern

**Monorepo Structure** with clear separation of concerns:

```
deal-brain/
├── apps/
│   ├── api/          # FastAPI backend
│   ├── cli/          # Typer CLI tools
│   └── web/          # Next.js frontend
├── packages/
│   └── core/         # Shared domain logic
└── infra/            # Docker configs
```

**Architectural Highlights:**
1. **Domain-Driven Design**: Core business logic in `packages/core`
2. **Service Layer Pattern**: Backend services orchestrate domain logic + persistence
3. **Async-First**: Async I/O throughout backend (SQLAlchemy, FastAPI)
4. **API-Driven**: Frontend communicates via REST API
5. **Component-Based UI**: Reusable React components with shadcn/ui
6. **Repository Pattern**: Database access abstracted through services

### Development Philosophy

1. **Shared Domain Logic**: Valuation, scoring, and business rules live in `packages/core` to ensure consistency across API and CLI
2. **Type Safety**: Pydantic for Python, TypeScript for frontend
3. **Testing**: Pytest for backend, Playwright for E2E
4. **Code Quality**: Black, Ruff, ESLint, pre-commit hooks
5. **Observability**: Structured logging, Prometheus metrics, OpenTelemetry tracing

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- pnpm
- Poetry
- Docker & Docker Compose

### Setup Commands

```bash
# Install dependencies
make setup

# Run full stack (Docker)
make up

# Run API locally
make api

# Run frontend locally
make web

# Apply database migrations
make migrate

# Run tests
make test
```

### Key Endpoints

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Web UI:** http://localhost:3000
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3021

---

## Documentation Organization

This analysis is split into focused documents for clarity and token efficiency:

### Technical Architecture
- **[Architecture Overview](./01-architecture-overview.md)**: System design, data flow, design patterns
- **[Backend Architecture](./03-backend-architecture.md)**: FastAPI, services, models
- **[Frontend Architecture](./04-frontend-architecture.md)**: Next.js, components, state management
- **[Database Schema](./05-database-schema.md)**: Models, relationships, migrations

### Reference Documentation
- **[Directory Structure](./02-directory-structure.md)**: Complete file organization
- **[API Documentation](./06-api-documentation.md)**: REST endpoints, request/response schemas
- **[Shared Domain Logic](./07-shared-domain-logic.md)**: Core business logic
- **[Technology Stack](./09-technology-stack.md)**: Dependencies, versions, tools

### Operations & Quality
- **[DevOps & Infrastructure](./08-devops-infrastructure.md)**: Docker, deployment, observability
- **[Insights & Recommendations](./10-insights-recommendations.md)**: Code quality, improvements, best practices

---

## Navigation Guide

### For New Developers
1. Start with [Architecture Overview](./01-architecture-overview.md)
2. Review [Directory Structure](./02-directory-structure.md)
3. Deep dive into [Backend](./03-backend-architecture.md) or [Frontend](./04-frontend-architecture.md)
4. Reference [API Documentation](./06-api-documentation.md) as needed

### For Feature Development
1. Review [Shared Domain Logic](./07-shared-domain-logic.md)
2. Check [Database Schema](./05-database-schema.md) for data models
3. Follow patterns in [Backend](./03-backend-architecture.md) or [Frontend](./04-frontend-architecture.md)
4. Test using [DevOps](./08-devops-infrastructure.md) guidelines

### For Architecture Decisions
1. Study [Architecture Overview](./01-architecture-overview.md)
2. Review [Technology Stack](./09-technology-stack.md)
3. Consider [Insights & Recommendations](./10-insights-recommendations.md)

---

## Project Status

### Maturity Level
**MVP+** - Core features complete, enhancements ongoing

### Recent Additions
- Baseline valuation system with packaged rulesets
- Performance metrics (CPU Mark, price efficiency)
- Product metadata (manufacturer, series, form factor)
- PassMark benchmark integration
- Ports management system
- Listing links and valuation overrides

### Active Development Areas
- UI editing flows (profiles, rules, listings)
- Automated test coverage expansion
- Observability dashboard refinement
- Celery task orchestration

---

## Contributing

### Code Style
- Python: Black (line length 100), isort, Ruff
- TypeScript: ESLint, Prettier
- Pre-commit hooks enforce standards

### Workflow
1. Create feature branch
2. Write tests
3. Implement feature
4. Run `make lint` and `make test`
5. Submit PR

### Key Conventions
- Async-first in backend
- Pydantic for data validation
- React Query for data fetching
- Component composition over inheritance
- Services orchestrate domain logic

---

## Support & Resources

- **CLAUDE.md**: AI assistant instructions
- **README.md**: Quick start guide
- **docs/**: User guides, architecture decisions
- **docs/project_plans/**: PRDs and implementation plans
- **.claude/**: Claude Code agent configurations

---

**End of Main Analysis Document**

For detailed information, navigate to the specific documentation files listed in the Table of Contents.
