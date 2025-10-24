# Deal Brain

**A full-stack price-to-performance intelligence system for Small Form Factor PCs.** Import listings from Excel workbooks or marketplace URLs, normalize and enrich the data, apply configurable valuation rules, and discover the best SFF PC deals ranked by intelligent scoring profiles.

---

## Features

- **Multi-Source Data Ingestion**: Import from Excel workbooks or marketplace URLs (eBay, Amazon, retailers) with automatic data extraction and normalization
- **Benchmark Integration**: PassMark CPU/GPU benchmark scores for accurate performance-per-dollar calculations
- **Configurable Valuation Engine**: Component-based pricing rules with color-coded deal quality indicators (good, great, premium)
- **Intelligent Scoring**: Customizable scoring profiles with weighted performance metrics (single/multi-thread CPU marks, GPU scores)
- **Performance Metrics**: Real-time calculations of adjusted pricing and scoring with automatic recalculation on updates
- **Connectivity Tracking**: Structured ports management (USB-A, USB-C, HDMI, DisplayPort, etc.) for complete system specifications
- **Explainable Scoring**: Interactive valuation breakdown modals showing exactly which rules and adjustments were applied to each listing
- **Responsive Dashboard**: KPI analytics, sortable/filterable listings table, and detailed listing views
- **CLI Tools**: Command-line interface for power users to import data, manage listings, and analyze deals
- **Production Infrastructure**: Docker Compose stack with Postgres, Redis, Celery async tasks, Prometheus/Grafana observability
- **Accessibility First**: WCAG 2.1 AA compliant interface with keyboard navigation and screen reader support
- **Shared Domain Logic**: Core valuation and scoring algorithms shared across API, CLI, and workers to eliminate duplication

---

## Quick Start

### Prerequisites

- **Python 3.11+** and **Poetry** for the backend
- **Node.js 18+** and **pnpm 8+** for the frontend
- **Docker** and **Docker Compose** (optional, for full stack)
- **Git** for version control

### Setup (5 minutes)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/deal-brain.git
   cd deal-brain
   ```

2. **Install dependencies**
   ```bash
   make setup
   ```
   This installs both Python and JavaScript dependencies via Poetry and pnpm.

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Update `.env` with your database and API settings.

4. **Run migrations**
   ```bash
   make migrate
   ```

5. **Start the stack**
   ```bash
   make up
   ```
   Or run services separately:
   ```bash
   make api          # FastAPI on http://localhost:8000
   make web          # Next.js on http://localhost:3000
   ```

6. **Access the application**
   - **Web UI**: http://localhost:3000
   - **API Docs**: http://localhost:8000/docs
   - **Grafana**: http://localhost:3021 (admin/admin)

---

## System Architecture

Deal Brain is a **Python/TypeScript monorepo** organized into layers:

```
deal-brain/
├── apps/
│   ├── api/              # FastAPI backend (async SQLAlchemy, Alembic migrations)
│   ├── cli/              # Typer CLI for power users
│   └── web/              # Next.js 14 App Router frontend
├── packages/
│   └── core/             # Shared domain logic (valuation, scoring, schemas)
├── infra/                # Docker configs, Prometheus/Grafana setup
├── tests/                # Backend test suite (pytest)
├── docs/                 # Documentation
└── scripts/              # Data import and utility scripts
```

### Key Architecture Decisions

**Shared Domain Logic** (`packages/core/`):
- Component-based valuation rules
- Composite scoring algorithms
- Pydantic schemas for contracts
- Shared enums for consistency
- Used by API, CLI, and Celery workers

**Layered Backend** (`apps/api/`):
- **Services Layer**: Business logic orchestration (listings, custom fields, imports)
- **API Layer**: RESTful endpoints with Pydantic request/response models
- **Database Layer**: Async SQLAlchemy ORM with Alembic migrations
- **Import Pipeline**: Multi-adapter support for URL/file ingestion

**Modern Frontend** (`apps/web/`):
- React Query for data fetching and caching
- TypeScript for type safety
- shadcn/ui components for consistency
- Memoized components for performance
- Accessible by default

---

## Technology Stack

### Backend
- **FastAPI** - Async Python web framework
- **SQLAlchemy** - Async ORM for database operations
- **Alembic** - Database migration management
- **Pydantic** - Data validation and serialization
- **Celery** - Distributed task queue
- **PostgreSQL** - Primary database
- **Redis** - Caching and task queue

### Frontend
- **Next.js 14** - React framework with App Router
- **React Query** - Server state management
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Accessible component library
- **Zod** - TypeScript-first schema validation

### Infrastructure & DevOps
- **Docker Compose** - Multi-container orchestration
- **Prometheus** - Metrics collection
- **Grafana** - Observability dashboards
- **OpenTelemetry** - Distributed tracing
- **Python Poetry** - Python dependency management
- **pnpm** - JavaScript monorepo package manager

---

## Installation & Setup

### Detailed Setup Guide

For a complete setup guide including Docker configuration, environment variables, database setup, and seeding with sample data, see [docs/setup.md](docs/setup.md).

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.11 | 3.11+ |
| Node.js | 18 | 18+ |
| Docker | 20.10 | 20.10+ |
| Docker Compose | 2.0 | 2.0+ |
| Disk Space | 2GB | 5GB+ |
| RAM | 4GB | 8GB+ |

### Development Environment Setup

```bash
# Clone and install
git clone https://github.com/yourusername/deal-brain.git
cd deal-brain
make setup

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Apply database migrations
make migrate

# Seed with sample data (optional)
make seed
```

---

## Running the Application

### Using Docker Compose (Recommended for Production)

```bash
# Start all services (Postgres, Redis, API, Web, Worker, Prometheus, Grafana)
make up

# View logs
docker-compose logs -f api    # API logs
docker-compose logs -f web    # Frontend logs

# Stop all services
make down
```

**Services & Ports:**
- **API**: http://localhost:8020
- **Web**: http://localhost:3020
- **Postgres**: localhost:5442
- **Redis**: localhost:6399
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3021

### Running Services Locally

For development without Docker:

```bash
# Terminal 1: FastAPI dev server
make api

# Terminal 2: Next.js dev server
make web

# Terminal 3 (optional): Celery worker
poetry run celery -A dealbrain_api.worker worker --loglevel=info
```

---

## Key Commands

### Development

```bash
# Install dependencies
make setup                    # Install Python and JS dependencies

# Running services
make up                       # Docker Compose stack
make down                     # Stop all services
make api                      # FastAPI dev server (reload on changes)
make web                      # Next.js dev server

# Database
make migrate                  # Apply pending Alembic migrations
make seed                     # Seed database with sample data

# Code quality
make format                   # Format code (black, isort, prettier)
make lint                     # Lint Python and TypeScript
make test                     # Run pytest suite
```

### Database

```bash
# Create a new migration after model changes
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# View migration history
poetry run alembic history
```

### Data Management

```bash
# Import data via CLI
poetry run dealbrain-cli import /path/to/listings.xlsx

# Import CPU benchmark data
poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv

# Recalculate all metrics
poetry run python scripts/recalculate_all_metrics.py

# Generate formula reference
poetry run python scripts/generate_formula_reference.py
```

### CLI Commands

```bash
# Show all available commands
poetry run dealbrain-cli --help

# Add a listing interactively
poetry run dealbrain-cli add

# Show top deals by metric
poetry run dealbrain-cli top

# Explain a listing's valuation
poetry run dealbrain-cli explain <listing_id>

# Export top listings to JSON
poetry run dealbrain-cli export
```

### Testing

```bash
# Run all tests
make test

# Run specific test file
poetry run pytest tests/test_valuation_service.py -v

# Run with coverage report
poetry run pytest --cov=dealbrain_api tests/
```

---

## Documentation

### Getting Started
- [Setup Guide](docs/setup.md) - Detailed installation and configuration
- [Quick Start](docs/quick-start.md) - Get running in 5 minutes

### Understanding the System
- [System Architecture](docs/architecture.md) - Component overview and data flow
- [Valuation Rules](docs/valuation-rules.md) - How pricing adjustments work
- [Scoring Profiles](docs/scoring-profiles.md) - Custom scoring configuration
- [Design System](docs/design/README.md) - UI components and accessibility

### Reference
- [API Reference](docs/api/README.md) - RESTful endpoint documentation
- [CLI Reference](docs/cli.md) - Command-line interface guide
- [Database Schema](docs/database-schema.md) - SQLAlchemy models
- [Custom Fields Guide](docs/custom-fields.md) - Dynamic field management

### Development
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Development Workflow](docs/development.md) - Development best practices
- [Testing Guide](docs/testing.md) - Testing strategies and patterns
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

---

## Development Workflow

### Adding Features

1. **Domain Logic** - Add business logic to `packages/core/`:
   ```bash
   # Add new valuation rule, scoring algorithm, etc.
   packages/core/valuation.py
   packages/core/scoring.py
   ```

2. **API Endpoints** - Add endpoints to `apps/api/dealbrain_api/api/`:
   ```bash
   # Create new router for feature
   apps/api/dealbrain_api/api/new_feature.py
   ```

3. **CLI Commands** - Add commands to `apps/cli/dealbrain_cli/main.py`

4. **Database Schema** - Create Alembic migration:
   ```bash
   poetry run alembic revision --autogenerate -m "Add feature"
   make migrate
   ```

5. **Frontend** - Add React components to `apps/web/`:
   ```bash
   # Components
   apps/web/components/feature/
   # Pages
   apps/web/app/feature/page.tsx
   ```

### Code Style

- **Python**: Black (100 char line), isort, ruff
- **TypeScript**: ESLint, Prettier (2 spaces)
- **Run before committing**: `make format && make lint`

### Testing

```bash
# Backend tests (pytest)
make test
poetry run pytest tests/test_feature.py -v

# Frontend tests (Jest + React Testing Library)
pnpm --filter web test

# E2E tests (Playwright)
pnpm test:e2e
```

---

## Project Roadmap

### Current Phase: Phase 3.5
- Entity tooltips in listing modals showing related data
- Enhanced metadata display for matched listings
- Performance optimizations for large datasets

### Upcoming Features
- **URL Bulk Import** - CSV/JSON upload for multiple marketplace URLs
- **Advanced Filtering** - Refine results by component specs and performance
- **Listing Edit UI** - Update listings directly in the interface
- **Automated Testing** - Expanded pytest and Playwright coverage
- **Enhanced Analytics** - More detailed KPI dashboards and reports

### Future Considerations
- Mobile app (React Native)
- Email notifications and alerts
- Integration with marketplace APIs (eBay, Amazon)
- Advanced data visualization
- Machine learning for deal prediction

---

## Support & Contributing

### Getting Help

1. **Check the Documentation** - Start with [docs/setup.md](docs/setup.md) or [docs/architecture.md](docs/architecture.md)
2. **Search Issues** - Look for existing GitHub issues
3. **Review Troubleshooting** - See [docs/troubleshooting.md](docs/troubleshooting.md) for common problems
4. **Ask Questions** - Open a GitHub discussion for general questions

### Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of conduct
- How to report bugs
- How to suggest features
- Pull request process
- Development setup
- Testing requirements

### Code of Conduct

This project is committed to providing a welcoming and inclusive environment. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## License

Deal Brain is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

### Attribution

Deal Brain uses:
- **PassMark Software** data for CPU/GPU benchmarks (used with permission)
- **shadcn/ui** component library (MIT licensed)
- **Radix UI** primitives (MIT licensed)
- **OpenTelemetry** (Apache 2.0 licensed)

---

## Acknowledgments

Deal Brain was created to help small form factor PC enthusiasts find the best value systems. Special thanks to:
- The FastAPI and Next.js communities
- PassMark Software for benchmark data
- Contributors and testers who provided feedback

---

## Contact

- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Email**: support@dealbrain.dev (if applicable)

---

**Last Updated**: October 24, 2025

For the latest version, visit [github.com/yourusername/deal-brain](https://github.com/yourusername/deal-brain)
