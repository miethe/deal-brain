# Deal Brain Documentation

Welcome to the Deal Brain documentation hub. This is your master index for all project documentation, guides, and references. Deal Brain is a full-stack price-to-performance intelligence system for Small Form Factor PCs that imports listings, normalizes data, applies configurable valuation rules, and ranks deals with explainable scoring.

---

## Quick Navigation

### I'm brand new - where do I start?

1. Read the [project overview](/mnt/containers/deal-brain/README.md) for feature overview
2. Follow [Installation & Setup](technical/setup.md) to get dependencies running
3. Try [Quick Start Guide](technical/INSTALL_DEPS.md) for local development
4. Explore the [Dashboard](#dashboard-overview) in your browser

### I want to understand how this works

- **System Architecture**: See [Architecture Overview](architecture/architecture.md)
- **Data Flow**: Read [URL Ingestion Architecture](architecture/URL_INGESTION_ARCHITECTURE.md)
- **Valuation Engine**: Study [Valuation Rules Documentation](architecture/valuation-rules.md)
- **Database Schema**: Check [Codebase Analysis - Database](reports/codebase_analysis/05-database-schema.md)

### I want to build a new feature

1. Review [Feature Development Guidelines](architecture/adr/ADR-007-catalog-state-management.md)
2. Check [Backend Architecture](reports/codebase_analysis/03-backend-architecture.md)
3. Review [Frontend Architecture](reports/codebase_analysis/04-frontend-architecture.md)
4. Look at [Design System & Guidelines](design/design-guidance.md)

### I want to import/export data

- **Excel Workbooks**: See [Import Guide](user-guide/guides/import-guide.md)
- **Marketplace URLs**: See [URL Ingestion Setup](configuration/url-ingestion.md)
- **Bulk Imports**: Read [Importer Usage Guide](user-guide/guides/importer-usage-guide.md)
- **Export Listings & Collections**: See [Export/Import User Guide](guides/export-import-user-guide.md)
- **Export/Import API**: See [Export/Import API Reference](api/export-import-api.md)
- **Export Format Details**: See [Export Format Reference](schemas/export-format-reference.md)
- **Troubleshooting**: See [Export/Import Troubleshooting](guides/export-import-troubleshooting.md)

### I want to understand valuation rules

- **Quick Intro**: [Basic Valuation Mode](user-guide/valuation-rules/basic-valuation-mode.md)
- **Complete Reference**: [Valuation Rules Guide](user-guide/guides/valuation-rules.md)
- **Formula Reference**: [Formula Builder & Reference](user-guide/valuation-rules/FORMULA_REFERENCE.md)
- **Quick Formula Guide**: [Formula Quick Reference](user-guide/valuation-rules/FORMULA_QUICK_REFERENCE.md)

### I want to contribute code

1. Read [CLAUDE.md](/mnt/containers/deal-brain/CLAUDE.md) for development guidelines
2. Check relevant architecture docs above
3. Review [Testing Guides](technical/testing/) for test patterns
4. Check [API Documentation](technical/api/) for endpoint specs

### I'm deploying to production

- Check [Docker Compose Setup](#docker-compose-stack) (see infrastructure section)
- Review environment configuration in root `.env.example`
- See [Observability & Logging](observability/logging-design.md)
- Check [Infrastructure Documentation](reports/codebase_analysis/08-devops-infrastructure.md)

---

## Documentation Directory

### Getting Started

| Document | Purpose | Status |
|----------|---------|--------|
| [Setup & Installation](technical/setup.md) | Initial project setup, dependency installation | ✅ Complete |
| [Install Dependencies](technical/INSTALL_DEPS.md) | Detailed dependency installation guide | ✅ Complete |
| [Data Directory Guide](/mnt/containers/deal-brain/data/README.md) | Reference files, seed data, import templates | ✅ Complete |

### Core Concepts & Architecture

| Document | Purpose | Status |
|----------|---------|--------|
| [Architecture Overview](architecture/architecture.md) | Monorepo structure, services, data model | ✅ Complete |
| [URL Ingestion Architecture](architecture/URL_INGESTION_ARCHITECTURE.md) | Complete URL ingestion pipeline design | ✅ Complete |
| [Valuation Rules Architecture](architecture/valuation-rules.md) | Comprehensive valuation system documentation | ✅ Complete |
| [Codebase Analysis](reports/codebase_analysis/codebase_analysis.md) | 10-part deep dive into system architecture | ✅ Complete |

### Features & Usage

#### Catalogs & Views
| Document | Purpose | Status |
|----------|---------|--------|
| [Catalog Views Guide](user-guide/catalog-views.md) | CPU/GPU catalog views, filtering, search | ✅ Complete |
| [Performance Metrics](user-guide/performance-metrics.md) | CPU Mark, PassMark benchmarks, metric calculations | ✅ Complete |

#### Valuation Rules System
| Document | Purpose | Status |
|----------|---------|--------|
| [Valuation Rules Guide](user-guide/guides/valuation-rules.md) | Complete valuation rules overview | ✅ Complete |
| [Basic Valuation Mode](user-guide/valuation-rules/basic-valuation-mode.md) | Basic mode concepts and usage | ✅ Complete |
| [Formula Builder Guide](user-guide/valuation-rules/formula-builder.md) | How to create custom formulas | ✅ Complete |
| [Formula Reference](user-guide/valuation-rules/FORMULA_REFERENCE.md) | Complete formula field & function reference | ✅ Complete |
| [Formula Quick Reference](user-guide/valuation-rules/FORMULA_QUICK_REFERENCE.md) | Quick lookup for formulas | ✅ Complete |
| [Mode Switching](user-guide/valuation-rules/valuation-rules-mode-switching.md) | Switch between basic and advanced modes | ✅ Complete |
| [Baseline JSON Format](user-guide/valuation-rules/baseline-json-format.md) | JSON import/export format specification | ✅ Complete |

#### Custom Fields & Data Management
| Document | Purpose | Status |
|----------|---------|--------|
| [Global Fields Backend Guide](user-guide/guides/global-fields-backend.md) | Backend implementation for custom fields | ✅ Complete |
| [RAM/Storage Catalog](user-guide/guides/ram-storage-catalog.md) | RAM and storage component management | ✅ Complete |

#### Imports & Data Ingestion
| Document | Purpose | Status |
|----------|---------|--------|
| [Import Guide](user-guide/guides/import-guide.md) | How to import listings from Excel | ✅ Complete |
| [Importer Usage Guide](user-guide/guides/importer-usage-guide.md) | CLI importer and web import workflow | ✅ Complete |

### API & Integration Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| [Export/Import API Reference](api/export-import-api.md) | Complete REST API for export/import operations | ✅ Complete |
| [Export Format Reference](schemas/export-format-reference.md) | v1.0.0 schema details, field specifications, validation | ✅ Complete |
| [Export/Import Troubleshooting](guides/export-import-troubleshooting.md) | Common issues, error messages, debugging tips | ✅ Complete |
| [URL Ingestion Configuration](configuration/url-ingestion.md) | Configure URL ingestion settings | ✅ Complete |
| [Event Service Usage](technical/api/event-service-usage-examples.md) | Event service API examples | ✅ Complete |
| [Normalizer Service Usage](technical/api/normalizer_service_usage.md) | Data normalization API guide | ✅ Complete |
| [Ruleset Packaging](technical/api/ruleset-packaging-baseline.md) | Rule packaging and distribution | ✅ Complete |
| [URL Adapters](/mnt/containers/deal-brain/apps/api/dealbrain_api/adapters/README.md) | eBay, JSON-LD, generic adapters | ✅ Complete |
| [Core Fields Mapping](technical/dto/core-fields-mapping.md) | Data transfer object field mapping | ✅ Complete |

### Frontend Development

| Document | Purpose | Status |
|----------|---------|--------|
| [Design System & Guidance](design/design-guidance.md) | UI/UX design principles, component library, accessibility | ✅ Complete |
| [Design README](design/README.md) | Design documentation index with project status | ✅ Complete |
| [Import Page Specification](design/import-page-specification.md) | Import page UI/UX specification | ✅ Complete |
| [Import Page Summary](design/import-page-summary.md) | Executive summary of import page design | ✅ Complete |
| [Single URL Import Design](design/single-url-import-design.md) | Complete single URL import feature design | ✅ Complete |
| [Single URL Import Mockups](design/single-url-import-mockups.md) | Visual mockups with 10+ state variations | ✅ Complete |
| [Single URL Import Technical Spec](design/single-url-import-technical-spec.md) | TypeScript types, API integration, testing | ✅ Complete |
| [Single URL Component Tree](design/single-url-import-component-tree.md) | Component hierarchy and data flow diagrams | ✅ Complete |
| [Single URL Quick Reference](design/single-url-import-quickref.md) | Developer cheat sheet and implementation guide | ✅ Complete |
| [Import Page Validation Checklist](design/import-page-validation-checklist.md) | QA and acceptance criteria | ✅ Complete |

### Backend Development

| Document | Purpose | Status |
|----------|---------|--------|
| [API Documentation Index](technical/api) | API endpoint references and specifications | ⚠️ Partial |
| [Testing Documentation](technical/testing) | E2E tests, baseline test deferred cases | ⚠️ Partial |

### Operations & Deployment

| Document | Purpose | Status |
|----------|---------|--------|
| [Observability & Logging](observability/logging-design.md) | Logging strategy, Prometheus instrumentation | ✅ Complete |

### Architecture Decision Records (ADRs)

| Document | Purpose | Status |
|----------|---------|--------|
| [ADR-003: Baseline Rule Hydration](architecture/adr/0003-baseline-rule-hydration-strategy.md) | Hydration strategy for baseline rules | ✅ Complete |
| [ADR-004: URL Ingestion API Prefix](architecture/adr/ADR-004-url-ingestion-api-prefix.md) | API versioning and endpoint structure | ✅ Complete |
| [ADR-007: Catalog State Management](architecture/adr/ADR-007-catalog-state-management.md) | Frontend state management patterns | ✅ Complete |
| [ADR-007: Enhanced Breakdown Modal](architecture/adr/ADR-007-enhanced-breakdown-modal-architecture.md) | Modal architecture for valuation breakdown | ✅ Complete |
| [ADR-008: Virtual Scrolling Strategy](architecture/adr/ADR-008-virtual-scrolling-strategy.md) | Performance optimization via virtualization | ✅ Complete |
| [ADR-010: Detail Page Architecture](architecture/adr/ADR-010-detail-page-architecture.md) | Listing detail page design | ✅ Complete |
| [ADR: Basic Valuation](architecture/adr/ADR-basic-valuation.md) | Basic valuation system design | ✅ Complete |

### Analysis & Reports

| Document | Purpose | Status |
|----------|---------|--------|
| [Architecture Overview Report](reports/codebase_analysis/01-architecture-overview.md) | High-level system architecture | ✅ Complete |
| [Directory Structure Report](reports/codebase_analysis/02-directory-structure.md) | Complete file/directory organization | ✅ Complete |
| [Backend Architecture Report](reports/codebase_analysis/03-backend-architecture.md) | FastAPI, SQLAlchemy, services deep dive | ✅ Complete |
| [Frontend Architecture Report](reports/codebase_analysis/04-frontend-architecture.md) | Next.js, React Query, component patterns | ✅ Complete |
| [Database Schema Report](reports/codebase_analysis/05-database-schema.md) | Complete database model documentation | ✅ Complete |
| [API Documentation Report](reports/codebase_analysis/06-api-documentation.md) | All endpoints documented | ✅ Complete |
| [Shared Domain Logic Report](reports/codebase_analysis/07-shared-domain-logic.md) | Valuation, scoring, shared schemas | ✅ Complete |
| [DevOps & Infrastructure Report](reports/codebase_analysis/08-devops-infrastructure.md) | Docker, deployment, observability | ✅ Complete |
| [Technology Stack Report](reports/codebase_analysis/09-technology-stack.md) | All dependencies, versions, purposes | ✅ Complete |
| [Insights & Recommendations](reports/codebase_analysis/10-insights-recommendations.md) | Best practices, performance tips | ✅ Complete |
| [Theme Implementation Analysis](reports/theme-implementation-analysis.md) | Dark/light theme system analysis | ✅ Complete |

### Design Specifications

| Document | Purpose | Status |
|----------|---------|--------|
| [Component Tree](design/single-url-import-component-tree.md) | Hierarchical component structure | ✅ Complete |
| [Specs Directory](design/specs) | Detailed specification documents | ⚠️ Partial |
| [Theme Documentation](design/theme) | Theming and styling system | ✅ Complete |

---

## Documentation Status Overview

### Comprehensive (✅)
Documentation that is complete, current, and ready for active use:
- Architecture and ADR documents
- Design specifications and UI/UX guides
- User guides for all features
- API integration documentation
- Full codebase analysis reports
- Observability and logging design

### Partial (⚠️)
Documentation with existing content but may need expansion:
- Backend API documentation (endpoint reference)
- Testing documentation (could expand scenarios)
- Design specs subdirectories (some deeper specs needed)

### Needs Work (❌)
Areas where documentation should be expanded or created:
- (Currently all major areas have documentation)

---

## Finding What You Need

### By Task

| Task | Primary Docs | Secondary Docs |
|------|-------------|----------------|
| Set up local environment | [Setup](technical/setup.md), [Install Deps](technical/INSTALL_DEPS.md) | [CLAUDE.md](/mnt/containers/deal-brain/CLAUDE.md) |
| Export listing or collection | [Export/Import API](api/export-import-api.md) | [Export Format Ref](schemas/export-format-reference.md) |
| Import exported data | [Export/Import API](api/export-import-api.md) | [Troubleshooting](guides/export-import-troubleshooting.md) |
| Import Excel workbook | [Import Guide](user-guide/guides/import-guide.md) | [Importer Usage](user-guide/guides/importer-usage-guide.md) |
| Import from marketplace URL | [URL Config](configuration/url-ingestion.md) | [URL Ingestion Architecture](architecture/URL_INGESTION_ARCHITECTURE.md) |
| Create valuation rules | [Valuation Rules Guide](user-guide/guides/valuation-rules.md), [Formula Reference](user-guide/valuation-rules/FORMULA_REFERENCE.md) | [ADR-Basic Valuation](architecture/adr/ADR-basic-valuation.md) |
| Understand catalog/metrics | [Catalog Views](user-guide/catalog-views.md), [Performance Metrics](user-guide/performance-metrics.md) | [Valuation Architecture](architecture/valuation-rules.md) |
| Add custom field | [Global Fields Guide](user-guide/guides/global-fields-backend.md) | [Data Model Report](reports/codebase_analysis/05-database-schema.md) |
| Add API endpoint | [Backend Architecture](reports/codebase_analysis/03-backend-architecture.md) | [API Documentation](technical/api/) |
| Create new component | [Design Guidance](design/design-guidance.md) | [Frontend Architecture](reports/codebase_analysis/04-frontend-architecture.md) |
| Deploy to production | [Architecture Overview](architecture/architecture.md), [Infrastructure](reports/codebase_analysis/08-devops-infrastructure.md) | [Observability](observability/logging-design.md) |
| Optimize performance | [ADR-Virtual Scrolling](architecture/adr/ADR-008-virtual-scrolling-strategy.md) | [Frontend Architecture](reports/codebase_analysis/04-frontend-architecture.md) |
| Understand data flow | [URL Ingestion Arch](architecture/URL_INGESTION_ARCHITECTURE.md) | [Architecture Overview](architecture/architecture.md) |

---

## Key Documentation Sections

### Dashboard Overview

Deal Brain's web dashboard provides:

- **KPI Analytics**: Overview metrics and statistics
- **Listings Table**: Sortable, filterable listing view with valuation breakdown
- **Detailed Views**: Per-listing detail pages with component breakdown
- **Import Workflow**: URL and file-based import interfaces
- **Settings**: Valuation rules, scoring profiles, custom fields
- **Accessibility**: Full WCAG 2.1 AA compliance, keyboard navigation, screen reader support

See [Catalog Views Guide](user-guide/catalog-views.md) for UI overview.

### Docker Compose Stack

The full development stack includes:

- **db** (Postgres) - Port 5432
- **redis** - Port 6379
- **api** (FastAPI) - Port 8000
- **web** (Next.js) - Port 3000
- **worker** (Celery) - Background tasks
- **prometheus** - Metrics collection (Port 9090)
- **grafana** - Monitoring dashboard (Port 3000)
- **otel-collector** - OpenTelemetry tracing

See `docker-compose.yml` in project root for full details.

### Core Concepts

**Listings**: Individual PC configurations with components (CPU, GPU, RAM, storage, ports) and calculated metrics.

**Valuation Rules**: Component-based pricing adjustments that determine if a deal is "good", "great", or "premium" based on configured thresholds.

**Scoring Profiles**: Weighted combinations of performance metrics (CPU Mark, GPU Score, etc.) that rank deals intelligently.

**Performance Metrics**: Real-time calculations of price-per-metric (e.g., $/CPU Mark single-thread).

**Custom Fields**: Dynamic fields that can be added to listings, rules, or profiles without code changes.

**Adapters**: Service integrations (eBay, JSON-LD, generic scraper) that extract listing data from marketplace URLs.

See [Architecture Overview](architecture/architecture.md) for more details.

---

## Contributing to Documentation

### Adding New Documentation

1. **Determine category**: Does it belong in design/, user-guide/, architecture/, technical/, or reports/?
2. **Use existing style**: Follow patterns in similar documents (headings, code examples, formatting)
3. **Include status**: Mark if documentation is comprehensive (✅), partial (⚠️), or needs work (❌)
4. **Update this index**: Add entry to relevant section in `/docs/README.md`
5. **Link properly**: Use relative paths that work from `/docs/` directory

### Documentation Style Guide

- **Headings**: Use `#` for main (rarely), `##` for major sections, `###` for subsections
- **Code blocks**: Always specify language: \`\`\`typescript, \`\`\`python, \`\`\`bash
- **Paths**: Use absolute paths starting with `/mnt/containers/deal-brain/`
- **Links**: Use relative paths from `/docs/` directory where possible
- **Examples**: Include working, tested examples with realistic data
- **Lists**: Use bullets for unordered, numbers for sequential steps
- **Tables**: Use for structured information comparisons
- **Notes**: Use blockquotes for important information (> Note:)

### Documentation Status Indicators

- ✅ **Comprehensive**: Complete, current, ready for active use
- ⚠️ **Partial**: Has content but could use expansion
- ❌ **Needs Work**: Minimal content or significantly out of date

---

## Quick Reference

### Common Commands

```bash
# Setup
make setup                           # Install all dependencies
make migrate                         # Apply database migrations

# Running Services
make up                              # Start full Docker stack
make down                            # Stop all services
make api                             # Run API locally
make web                             # Run web locally

# Development
make test                            # Run test suite
make lint                            # Lint code
make format                          # Format code

# CLI Commands
poetry run dealbrain-cli --help      # Show all commands
poetry run dealbrain-cli import path/to/file.xlsx  # Import workbook
poetry run dealbrain-cli top         # Show top deals
poetry run dealbrain-cli explain <id> # Show valuation breakdown

# Data Management
poetry run python scripts/generate_formula_reference.py   # Regenerate formula docs
poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv  # Import CPU data
poetry run python scripts/recalculate_all_metrics.py      # Recalculate metrics
```

See [CLAUDE.md](/mnt/containers/deal-brain/CLAUDE.md) for complete command reference.

### File Organization

```
/mnt/containers/deal-brain/
├── apps/
│   ├── api/                    # FastAPI backend
│   ├── web/                    # Next.js frontend
│   └── cli/                    # Typer CLI commands
├── packages/
│   └── core/                   # Shared domain logic
├── docs/                       # This documentation
│   ├── architecture/           # System design & ADRs
│   ├── design/                 # UI/UX specifications
│   ├── user-guide/             # Feature guides
│   ├── technical/              # API & testing docs
│   ├── configuration/          # Setup guides
│   ├── observability/          # Logging & monitoring
│   └── reports/                # Analysis documents
├── data/                       # Reference files & seeds
├── infra/                      # Docker, observability config
└── tests/                      # Backend test suite
```

### Key Files

- `/mnt/containers/deal-brain/CLAUDE.md` - Development guidelines for Claude
- `/mnt/containers/deal-brain/README.md` - Project overview and quick start
- `/mnt/containers/deal-brain/.env.example` - Environment variables template
- `/mnt/containers/deal-brain/docker-compose.yml` - Full stack configuration
- `/mnt/containers/deal-brain/pyproject.toml` - Python dependencies and tools
- `/mnt/containers/deal-brain/package.json` - JavaScript workspace root

---

## Documentation Roadmap

### Currently Documented (v1.0)

- Complete system architecture
- URL ingestion and marketplace integration
- Valuation rules and scoring
- All user-facing features
- API integrations and adapters
- Full design system
- Database and data models
- DevOps and infrastructure
- Testing strategies
- Performance optimization patterns

### Future Documentation Needs

- [x] Create troubleshooting guide (common issues and solutions) - ✅ Export/Import Troubleshooting added
- [ ] Expand backend API endpoint reference (detailed request/response examples)
- [ ] Add more integration examples (marketplace-specific workflows)
- [ ] Add migration guides (upgrading, schema changes)
- [ ] Expand testing section (test patterns, coverage reports)
- [ ] Add performance profiling guide
- [ ] Create compliance documentation (accessibility, security)

---

## Support & Questions

### Finding Help

1. **Search existing documentation** - Most questions are answered in guides above
2. **Check reports** - Codebase analysis documents have deep technical details
3. **Review code comments** - Inline documentation in source code
4. **Check CLAUDE.md** - Development and coding guidelines
5. **Review ADRs** - Architecture decisions with rationale

### Documentation Gaps

If you find missing or incomplete documentation:

1. Check if there's a partial document in relevant section
2. Look for related documents that might cover the topic
3. Create an issue with documentation improvements
4. Submit documentation PR with updates

---

## Document Index by File Count

- **Design Documentation**: 16 comprehensive design documents
- **User Guides**: 12 feature and workflow guides (added export/import)
- **Architecture & ADRs**: 8 architectural decision records and overviews
- **API Documentation**: 13 API, integration, and schema documents (added export/import API + schema reference + troubleshooting)
- **Technical Documentation**: 10 backend, API, and testing documents
- **Analysis Reports**: 11 in-depth codebase analysis documents
- **Total**: ~230 documentation files across all project documentation

---

**Documentation Last Updated**: October 24, 2025

**Maintained By**: Development Team

**Contributing**: See sections above for adding new documentation
