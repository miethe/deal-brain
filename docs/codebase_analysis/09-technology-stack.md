# Technology Stack

## Table of Contents
1. [Language Versions](#language-versions)
2. [Backend Stack](#backend-stack)
3. [Frontend Stack](#frontend-stack)
4. [Database & Infrastructure](#database--infrastructure)
5. [Observability](#observability)
6. [Development Tools](#development-tools)
7. [Testing](#testing)
8. [Technology Decisions](#technology-decisions)

---

## Language Versions

### Python
- **Version:** 3.11+
- **Specified in:** `pyproject.toml` (`python = "^3.11"`)
- **Docker Image:** `python:3.11-slim`
- **Features Used:**
  - Type hints with modern syntax (PEP 604 union types)
  - Async/await for concurrent operations
  - Pattern matching (structural pattern matching)
  - Enhanced error messages

### TypeScript
- **Version:** 5.3.3
- **Specified in:** `apps/web/package.json`
- **Compilation Target:** ES2020
- **Features Used:**
  - Strict mode enabled
  - Path aliases (`@/*`)
  - Type inference
  - JSX/TSX support

### Node.js
- **Version:** 20 LTS (Alpine-based)
- **Specified in:** `infra/web/Dockerfile` (`node:20-alpine`)
- **Package Manager:** pnpm 8.15.4 (via Corepack)
- **Runtime:** Used for Next.js and build tools

---

## Backend Stack

### Web Framework
**FastAPI ^0.110.0**
- Modern async Python web framework
- Automatic OpenAPI documentation
- Built-in validation via Pydantic
- High performance (comparable to Node.js)
- Native async/await support

### Database & ORM
**SQLAlchemy ^2.0.25**
- Async ORM with `AsyncSession`
- Declarative models in `apps/api/dealbrain_api/models/core.py`
- Relationship management and eager loading
- Query optimization with selectinload/joinedload

**Database Drivers:**
- `asyncpg ^0.29.0` - High-performance async PostgreSQL driver (primary)
- `psycopg ^3.1.18` - Sync driver for migrations and scripts
- `psycopg-binary ^3.1.18` - Binary distribution for performance

**Alembic ^1.13.1**
- Database migration management
- Auto-generation from model changes
- Version control for schema evolution
- Located in `apps/api/alembic/`

### Data Validation
**Pydantic ^2.6.2**
- Request/response schema validation
- Automatic JSON serialization
- Type coercion and validation
- Used across API, CLI, and domain packages

**pydantic-settings ^2.2.1**
- Environment-based configuration
- Type-safe settings management
- Automatic `.env` file loading

### Task Queue
**Celery ^5.3.6**
- Distributed task queue
- Background job processing
- Scheduled tasks (beat)
- Used for:
  - Bulk listing recalculations
  - Import processing
  - Metric updates

**Redis ^5.0.1**
- Celery broker and result backend
- Session caching
- Query result caching
- Rate limiting

### Server & Runtime
**Uvicorn ^0.27.1**
- ASGI server for FastAPI
- Hot reload in development
- Production-ready with `--workers` flag
- HTTP/1.1 and WebSocket support

### Data Processing
**Pandas ^2.2.1**
- Excel workbook parsing
- Data normalization and transformation
- Used in import pipeline

**openpyxl ^3.1.2**
- Excel file reading/writing
- Workbook manipulation
- Integration with Pandas

**NumPy ^1.26.4**
- Numerical computations
- Array operations
- Dependency for Pandas

### CLI Framework
**Typer ^0.9.0**
- Type-safe CLI commands
- Automatic help generation
- Rich formatting support
- Commands in `apps/cli/dealbrain_cli/main.py`

### Utilities
**Loguru ^0.7.2**
- Structured logging
- Colored output
- Automatic exception catching

**structlog ^24.1.0**
- Structured logging for production
- JSON output for log aggregation

**httpx ^0.26.0**
- Async HTTP client
- Used for external API calls

**tenacity ^8.2.3**
- Retry logic with exponential backoff
- Fault tolerance

**rapidfuzz ^3.6.1**
- Fast fuzzy string matching
- Component catalog search

**python-multipart ^0.0.9**
- File upload handling
- Form data parsing

**itsdangerous ^2.1.2**
- Secure token generation
- Session management

**passlib[bcrypt] ^1.7.4**
- Password hashing
- User authentication

**python-dateutil ^2.8.2**
- Date parsing and manipulation

**pyyaml ^6.0.1**
- YAML configuration files
- Data serialization

### Observability
**prometheus-fastapi-instrumentator ^6.1.0**
- Automatic Prometheus metrics
- Request/response timing
- Error rate tracking

---

## Frontend Stack

### Framework
**Next.js 14.1.0**
- React meta-framework with App Router
- Server-side rendering (SSR)
- Static site generation (SSG)
- API routes (not used - separate backend)
- File-based routing
- Nested layouts for consistent UI

**React 18.2.0**
- Component-based UI library
- Concurrent rendering
- Automatic batching
- Server components (Next.js 14)

### TypeScript
**TypeScript 5.3.3**
- Type safety across frontend
- Path aliases for imports
- Strict mode enabled

### Data Fetching
**TanStack Query ^5.24.3** (formerly React Query)
- Server state management
- Automatic caching and invalidation
- Optimistic updates
- Background refetching
- DevTools for debugging
- Located in `apps/web/hooks/` and query clients

### Tables & Virtualization
**TanStack Table ^8.10.8**
- Headless table library
- Column sorting, filtering, resizing
- Pagination and selection
- Used in listings table

**TanStack Virtual ^3.13.12**
- Virtual scrolling for large lists
- Performance optimization
- Row virtualization strategy (see ADR-008)

### UI Components
**Radix UI** (Multiple Packages)
- Unstyled, accessible component primitives
- Keyboard navigation built-in
- WCAG AA compliant
- Components used:
  - `@radix-ui/react-dialog ^1.0.5` - Modals
  - `@radix-ui/react-dropdown-menu ^2.0.6` - Dropdowns
  - `@radix-ui/react-select ^2.0.0` - Select inputs
  - `@radix-ui/react-tooltip ^1.0.7` - Tooltips
  - `@radix-ui/react-popover ^1.0.7` - Popovers
  - `@radix-ui/react-tabs ^1.1.13` - Tab navigation
  - `@radix-ui/react-checkbox ^1.0.4` - Checkboxes
  - `@radix-ui/react-alert-dialog ^1.0.5` - Confirmation dialogs
  - `@radix-ui/react-hover-card ^1.0.7` - Hover cards
  - `@radix-ui/react-scroll-area ^1.0.5` - Custom scrollbars
  - `@radix-ui/react-slider ^1.1.2` - Range sliders
  - `@radix-ui/react-slot ^1.0.2` - Component composition
  - `@radix-ui/react-toast ^1.1.4` - Toast notifications

**Lucide React ^0.319.0**
- Icon library
- Tree-shakeable icons
- Consistent design system

### Styling
**Tailwind CSS ^3.4.1**
- Utility-first CSS framework
- JIT (Just-In-Time) compilation
- Custom design tokens
- Dark mode support

**tailwindcss-animate ^1.0.7**
- Pre-built animation utilities
- Smooth transitions

**tailwind-merge ^2.2.1**
- Merge conflicting Tailwind classes
- Used in `cn()` utility

**class-variance-authority ^0.7.0**
- Type-safe component variants
- Used for button styles, badges, etc.

**next-themes ^0.2.1**
- Theme switching (light/dark mode)
- System preference detection

**Framer Motion ^11.0.3**
- Animation library
- Page transitions
- Gesture-based interactions
- Component animations

### Forms & Validation
**React Hook Form ^7.50.1**
- Performant form management
- Uncontrolled components
- Built-in validation
- Used in listing forms, rule builder

**@hookform/resolvers ^3.3.4**
- Integration adapters for validation libraries
- Zod resolver for schema validation

**Zod ^3.22.4**
- TypeScript-first schema validation
- Type inference
- Runtime validation
- Shared schemas with backend (via code generation or manual sync)

### State Management
**Zustand ^5.0.8**
- Lightweight state management
- No boilerplate
- Used for:
  - UI state (modals, drawers)
  - User preferences
  - Temporary form state

### Drag & Drop
**dnd-kit** (Multiple Packages)
- Modern drag-and-drop toolkit
- Accessible by default
- Touch support
- Components:
  - `@dnd-kit/core ^6.1.0` - Core functionality
  - `@dnd-kit/sortable ^8.0.0` - Sortable lists
  - `@dnd-kit/utilities ^3.2.2` - Utility functions
- Used in rule builder, field ordering

### Charts
**Recharts ^2.12.0**
- Composable charting library
- Built on D3
- Responsive charts
- Used for performance metrics visualization

### Utilities
**use-debounce ^10.0.0**
- Debounced values and callbacks
- Used for search inputs (200ms delay)

**clsx ^2.1.0**
- Conditional class name construction
- Used with `cn()` utility

**cmdk ^0.2.1**
- Command menu component
- Keyboard-first navigation

---

## Database & Infrastructure

### Database
**PostgreSQL 15**
- Primary data store
- JSON/JSONB support for flexible schemas
- Full-text search capabilities
- Docker image: `postgres:15-alpine`
- Port: 5442 (external), 5432 (internal)

### Cache & Message Broker
**Redis 7**
- Celery task queue broker
- Session caching
- Query result caching
- Docker image: `redis:7-alpine`
- Port: 6399 (external), 6379 (internal)

### Containerization
**Docker & Docker Compose**
- Container orchestration
- Service isolation
- Development environment parity
- Compose version: 3.9

**Dockerfiles:**
- `infra/api/Dockerfile` - Python 3.11 backend
- `infra/web/Dockerfile` - Node 20 frontend
- `infra/worker/Dockerfile` - Celery worker

**Docker Services:**
- `db` - PostgreSQL database
- `redis` - Redis cache/queue
- `api` - FastAPI backend (port 8020)
- `web` - Next.js frontend (port 3020)
- `worker` - Celery background worker
- `otel-collector` - OpenTelemetry collector
- `prometheus` - Metrics storage (port 9090)
- `grafana` - Metrics visualization (port 3021)

---

## Observability

### Metrics
**Prometheus v2.50.0**
- Time-series metrics database
- Pull-based metrics collection
- PromQL query language
- Configuration: `infra/prometheus/prometheus.yml`
- Port: 9090

**Grafana 10.3.1**
- Metrics visualization dashboards
- Alerting
- Multiple data source support
- Default credentials: admin/admin
- Port: 3021

### Tracing
**OpenTelemetry Collector 0.89.0**
- Distributed tracing collection
- Trace aggregation and export
- Configuration: `infra/otel/config.yaml`
- Integration with FastAPI via instrumentation

### Application Instrumentation
**prometheus-fastapi-instrumentator ^6.1.0**
- Automatic FastAPI metrics
- Request duration histograms
- Error rate counters
- In-flight request gauge

---

## Development Tools

### Python Package Management
**Poetry** (via `pyproject.toml`)
- Dependency resolution
- Virtual environment management
- Lock file for reproducibility
- Build system: poetry-core >= 1.6.1

### JavaScript Package Management
**pnpm 8.15.4**
- Fast, efficient package manager
- Monorepo workspace support
- Content-addressable storage
- Configured via Corepack

### Code Formatting
**Black ^24.2.0**
- Opinionated Python code formatter
- Line length: 100 characters
- No configuration needed

**isort ^5.13.2**
- Python import sorting
- Black-compatible profile
- Line length: 100

### Linting
**Ruff ^0.2.2**
- Fast Python linter (Rust-based)
- Replaces flake8, pylint, etc.
- Rules enabled: E, F, I, UP, B, C4, SIM, N, S
- Ignores: S101 (assert statements in tests)

**ESLint ^8.56.0**
- JavaScript/TypeScript linting
- Next.js config extends: `eslint-config-next`
- Integrated with Prettier

### Type Checking
**mypy ^1.8.0**
- Static type checking for Python
- Python version: 3.11
- SQLAlchemy plugin enabled
- Strict optional checking

**TypeScript 5.3.3**
- Built-in type checking
- `tsc --noEmit` for validation

### Git Hooks
**pre-commit ^3.6.2**
- Git hook framework
- Runs formatters and linters before commit
- Configuration: `.pre-commit-config.yaml`

### Build Tools
**autoprefixer ^10.4.17**
- Automatic CSS vendor prefixes

**postcss ^8.4.33**
- CSS transformation pipeline

**Tailwind CSS ^3.4.1**
- PostCSS plugin for utility generation

---

## Testing

### Backend Testing
**pytest ^8.0.2**
- Python testing framework
- Fixtures and parametrization
- Test discovery and execution
- Configuration in `pyproject.toml`

**pytest-asyncio ^0.23.5**
- Async test support
- AsyncSession fixtures
- Async event loop management

**pytest-cov ^4.1.0**
- Code coverage reporting
- Coverage reports
- Integration with pytest

**pytest-mock ^3.12.0**
- Mocking utilities
- MockFixture plugin

### Test Utilities
**factory-boy ^3.3.0**
- Test data generation
- Model factories
- Faker integration

**freezegun ^1.4.0**
- Time mocking
- Datetime freezing for deterministic tests

### End-to-End Testing
**Playwright ^1.41.2**
- Cross-browser E2E testing
- Auto-wait mechanisms
- Screenshot and video recording
- Configuration: `playwright.config.ts`

**@playwright/test ^1.40.0**
- Playwright test runner
- Monorepo root dependency

**pytest-playwright ^0.4.2**
- Playwright integration for pytest
- Python E2E tests

---

## Technology Decisions

### 1. Python 3.11+ for Backend
**Decision:** Use Python 3.11 or higher

**Rationale:**
- Modern async/await syntax and performance improvements
- Native async support in SQLAlchemy 2.0
- Enhanced type hinting (PEP 604, 612)
- Improved error messages for faster debugging
- Active LTS support and security updates

**Alternatives Considered:**
- Python 3.10: Lacks some performance optimizations
- Python 3.12: Too new, less stable ecosystem support at project start
- Node.js: Less mature data science ecosystem (Pandas equivalent)

**Benefits:**
- Strong data processing libraries (Pandas, NumPy)
- Excellent async frameworks (FastAPI, SQLAlchemy)
- Rich type system with Pydantic
- Mature ORM and migration tools

---

### 2. FastAPI over Django/Flask
**Decision:** Use FastAPI as the web framework

**Rationale:**
- Native async/await support (required for async SQLAlchemy)
- Automatic OpenAPI documentation generation
- Built-in request/response validation via Pydantic
- High performance (comparable to Node.js)
- Modern Python best practices

**Alternatives Considered:**
- **Django:** Heavier framework, ORM not async-native, more opinionated
- **Flask:** Mature but lacks async support, no built-in validation
- **Sanic:** Async but smaller ecosystem, less documentation

**Benefits:**
- Fast development with automatic docs
- Type safety end-to-end
- Performance suitable for high-traffic APIs
- Clean dependency injection system

---

### 3. SQLAlchemy 2.0 Async ORM
**Decision:** Use SQLAlchemy 2.0 with async session

**Rationale:**
- Async queries for high concurrency
- Mature ORM with excellent relationship management
- Alembic integration for migrations
- Type hints support for better IDE experience

**Alternatives Considered:**
- **Django ORM:** Tied to Django framework
- **Tortoise ORM:** Async but less mature, smaller community
- **Raw SQL:** Too low-level, loses type safety

**Benefits:**
- Efficient connection pooling
- Query optimization (selectinload, joinedload)
- Schema migrations with Alembic
- SQL Alchemy plugin for mypy

---

### 4. PostgreSQL over MySQL/MongoDB
**Decision:** Use PostgreSQL 15 as primary database

**Rationale:**
- JSONB support for flexible schemas (valuation_breakdown, custom fields)
- Advanced indexing (GIN, BRIN for JSON queries)
- Full ACID compliance
- Excellent performance for complex queries
- Strong Python ecosystem support (asyncpg)

**Alternatives Considered:**
- **MySQL:** Less advanced JSON support, weaker full-text search
- **MongoDB:** NoSQL flexibility but loses relational integrity
- **SQLite:** Not production-ready for concurrent writes

**Benefits:**
- Best-in-class JSON/JSONB handling
- Full-text search capabilities
- Mature replication and backup tools
- Active development and community

---

### 5. Next.js 14 App Router
**Decision:** Use Next.js 14 with App Router (not Pages Router)

**Rationale:**
- Server components for better initial load performance
- Nested layouts for consistent UI (AppShell pattern)
- Improved data fetching with async server components
- Better code splitting and lazy loading
- Future-proof architecture (Pages Router being phased out)

**Alternatives Considered:**
- **Create React App:** No SSR, deprecated
- **Vite + React Router:** More setup, no server components
- **Remix:** Newer, smaller ecosystem
- **Next.js Pages Router:** Legacy approach, less performant

**Benefits:**
- Automatic code splitting
- Server-side rendering for better SEO
- API routes (not used but available)
- Image optimization out of the box
- Production-ready with minimal config

---

### 6. TanStack Query over SWR/Redux
**Decision:** Use TanStack Query (React Query) for data fetching

**Rationale:**
- Powerful caching with automatic invalidation
- Optimistic updates for instant UI feedback
- Background refetching for stale data
- DevTools for debugging queries
- Excellent TypeScript support

**Alternatives Considered:**
- **SWR:** Simpler but less feature-rich, no optimistic updates
- **Redux Toolkit Query:** Tightly coupled with Redux state
- **Apollo Client:** GraphQL-focused, overkill for REST API

**Benefits:**
- Eliminates boilerplate for data fetching
- Automatic retry and error handling
- Query deduplication and request batching
- Window focus refetching

---

### 7. Radix UI over Material-UI/Chakra
**Decision:** Use Radix UI primitives with custom styling

**Rationale:**
- Unstyled components for complete design control
- Built-in accessibility (WCAG AA compliant)
- Keyboard navigation out of the box
- Small bundle size (tree-shakeable)
- Composable primitive components

**Alternatives Considered:**
- **Material-UI (MUI):** Heavy, opinionated design, larger bundle
- **Chakra UI:** Good but less flexible styling
- **Headless UI:** Smaller ecosystem, less comprehensive

**Benefits:**
- Full control over visual design
- Accessibility by default
- Modern React patterns (compound components)
- Excellent TypeScript definitions

---

### 8. Tailwind CSS over CSS-in-JS
**Decision:** Use Tailwind CSS for styling

**Rationale:**
- Utility-first approach for rapid prototyping
- JIT compilation for minimal bundle size
- Consistent design tokens (spacing, colors)
- No runtime overhead (unlike CSS-in-JS)
- Great DX with IntelliSense

**Alternatives Considered:**
- **Styled Components:** Runtime overhead, larger bundles
- **Emotion:** Similar runtime issues
- **CSS Modules:** More boilerplate, less consistent

**Benefits:**
- Fast iteration speed
- Predictable class names
- Dark mode built-in
- PurgeCSS for production optimization

---

### 9. Zustand over Redux/Context
**Decision:** Use Zustand for client state management

**Rationale:**
- Minimal boilerplate compared to Redux
- No provider wrapping required
- Simple API with hooks
- Excellent TypeScript support
- Small bundle size (1KB)

**Alternatives Considered:**
- **Redux Toolkit:** More boilerplate, overkill for UI state
- **Context API:** Performance issues with frequent updates
- **Jotai/Recoil:** Atomic state, more complex for simple cases

**Benefits:**
- Easy to learn and use
- Works alongside TanStack Query (server state separate)
- Middleware support (persist, devtools)
- No re-render issues

---

### 10. Pydantic Everywhere
**Decision:** Use Pydantic for all data validation (API, domain, CLI)

**Rationale:**
- Type safety at runtime and compile time
- Automatic JSON serialization/deserialization
- Clear API contracts with automatic docs
- Validation errors with helpful messages
- Integration with FastAPI

**Alternatives Considered:**
- **Dataclasses:** No validation logic
- **Marshmallow:** More boilerplate, less type-safe
- **Cerberus:** Dict-based, loses type information

**Benefits:**
- Single source of truth for schemas
- FastAPI automatic OpenAPI generation
- SQLAlchemy model integration (model_validate)
- Easy migration from dict to typed models

---

### 11. Monorepo with Poetry + pnpm
**Decision:** Monorepo structure with Poetry (Python) and pnpm (JavaScript)

**Rationale:**
- Shared domain logic in `packages/core/`
- Atomic changes across backend, frontend, CLI
- Simplified dependency management
- Single source of truth for configurations

**Alternatives Considered:**
- **Multi-repo:** Coordination overhead, versioning issues
- **Turborepo/Nx:** Added complexity for current scale
- **npm/yarn workspaces:** pnpm more efficient for disk space

**Benefits:**
- Code reuse across API and CLI
- Consistent versioning
- Single CI/CD pipeline
- Easier refactoring

---

### 12. Docker Compose for Local Development
**Decision:** Docker Compose for full-stack local environment

**Rationale:**
- Environment parity (dev/staging/prod)
- One-command setup (`make up`)
- Isolated services (DB, Redis, API, worker)
- Consistent across team members

**Alternatives Considered:**
- **Local installs:** Configuration drift, inconsistent versions
- **Kubernetes:** Too complex for local dev
- **Vagrant:** Heavier, slower

**Benefits:**
- No "works on my machine" issues
- Easy to add new services (Prometheus, Grafana)
- Volume mounts for hot reload
- Network isolation for security

---

### 13. Celery for Background Tasks
**Decision:** Use Celery with Redis broker

**Rationale:**
- Mature distributed task queue
- Robust retry and error handling
- Scheduled tasks (beat) for cron jobs
- Monitoring tools (Flower)

**Alternatives Considered:**
- **RQ (Redis Queue):** Simpler but less feature-rich
- **Dramatiq:** Good but smaller ecosystem
- **FastAPI BackgroundTasks:** Not suitable for long-running jobs

**Benefits:**
- Proven at scale
- Excellent monitoring and debugging
- Chain/group task primitives
- Multi-worker support

---

### 14. Prometheus + Grafana for Observability
**Decision:** Prometheus for metrics, Grafana for visualization

**Rationale:**
- Industry-standard observability stack
- Pull-based metrics for reliability
- Powerful PromQL query language
- Rich dashboard ecosystem

**Alternatives Considered:**
- **Datadog/New Relic:** Expensive for small teams
- **ELK Stack:** Heavy, more logging-focused
- **InfluxDB:** Time-series but less ecosystem

**Benefits:**
- Open-source and self-hosted
- Pre-built Grafana dashboards
- Easy integration with FastAPI
- Alerting capabilities

---

### 15. Playwright for E2E Testing
**Decision:** Playwright for end-to-end tests

**Rationale:**
- Cross-browser testing (Chromium, Firefox, WebKit)
- Auto-wait eliminates flaky tests
- Modern async API
- Built-in screenshot/video recording

**Alternatives Considered:**
- **Cypress:** Browser-only, not true E2E
- **Selenium:** Older, more flaky tests
- **Puppeteer:** Chromium-only

**Benefits:**
- Reliable tests without explicit waits
- Trace viewer for debugging
- Mobile device emulation
- Parallel test execution

---

## Version Management

### Dependency Updates
- **Automated:** Dependabot not currently configured
- **Manual:** Check for updates quarterly
- **Lock Files:**
  - Python: `poetry.lock`
  - JavaScript: `pnpm-lock.yaml`

### Breaking Changes
- Major version bumps require team review
- Test suite must pass before upgrading
- Document migration steps in changelog

---

## Related Documentation
- [Architecture Overview](./01-architecture-overview.md) - System design and patterns
- [Directory Structure](./02-directory-structure.md) - Project organization
- [API Structure](./04-api-structure.md) - Backend API details
- [Frontend Components](./05-frontend-components.md) - Frontend architecture

---

**Next:** [Performance Optimization →](./10-performance-optimization.md)
