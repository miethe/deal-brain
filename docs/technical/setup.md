# Deal Brain — Setup Guide

Complete instructions for setting up Deal Brain for local development, testing, and deployment.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start (5 minutes)](#quick-start-5-minutes)
- [Detailed Setup](#detailed-setup)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Data Import](#data-import)
- [Running Services](#running-services)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Docker & Container Setup](#docker--container-setup)

---

## System Requirements

### Hardware
- **Disk Space**: 2GB minimum (5GB recommended for development)
- **RAM**: 4GB minimum (8GB+ recommended)
- **CPU**: Multi-core processor recommended for Docker services

### Software

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **Python** | 3.11 | 3.11+ (latest) | Required for backend |
| **Node.js** | 18.0 | 20.0+ | Required for frontend |
| **pnpm** | 8.15 | Latest | Install via Corepack: `corepack enable` |
| **Docker** | 20.10 | Latest | Required for services (postgres, redis, etc.) |
| **Docker Compose** | 2.0 | 2.17+ | Often included with Docker Desktop |
| **Git** | Any | Latest | For version control |

### Operating System Support
- **Linux** - Full support (Ubuntu 20.04+, Fedora 37+, Debian 11+)
- **macOS** - Full support (Intel and Apple Silicon)
- **Windows** - Supported via WSL2 (Windows Subsystem for Linux)

### Install Prerequisites

#### macOS (using Homebrew)
```bash
# Install Python 3.11
brew install python@3.11

# Install Node.js 20+
brew install node

# Enable pnpm via Corepack
corepack enable

# Install Docker Desktop
brew install --cask docker
```

#### Linux (Ubuntu/Debian)
```bash
# Install Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Install Node.js 20+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs

# Enable pnpm via Corepack
corepack enable

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Windows (using WSL2)
```bash
# Enable WSL2 first, then run Linux commands above
# Install Docker Desktop for Windows with WSL2 integration
# https://docs.docker.com/desktop/install/windows-install/
```

---

## Quick Start (5 minutes)

For a rapid setup without detailed explanation:

```bash
# 1. Clone the repository
git clone <repository-url>
cd deal-brain

# 2. Install dependencies (Python + Node.js)
make setup

# 3. Configure environment
cp .env.example .env

# 4. Apply database migrations
make migrate

# 5. Start the full stack
make up

# 6. Access the application
# Web UI:  http://localhost:3000
# API:     http://localhost:8000
# Grafana: http://localhost:3001 (admin / admin)
```

**Next steps:**
- Import sample data (see [Data Import](#data-import) section)
- Visit the dashboard at http://localhost:3000
- Check logs: `docker-compose logs -f`

---

## Detailed Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/deal-brain.git
cd deal-brain
```

### Step 2: Install Python Dependencies

**Using Poetry (recommended):**
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Ensure Poetry is in your PATH
export PATH="$HOME/.local/bin:$PATH"

# Install Python dependencies
poetry install

# Verify installation
poetry --version
poetry show | head -10
```

**Troubleshooting Poetry:**
- If `poetry` command not found, add to PATH: `export PATH="$HOME/.local/bin:$PATH"`
- To use system Python instead: `poetry env use /usr/bin/python3.11`

### Step 3: Install Node.js Dependencies

**Using pnpm:**
```bash
# Enable pnpm via Node's Corepack
corepack enable

# Install JavaScript dependencies (all workspaces)
pnpm install --frozen-lockfile=false

# Verify installation
pnpm --version
pnpm list --depth=0
```

**Using Makefile:**
```bash
# Install both Python and JavaScript dependencies
make setup
```

### Step 4: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the file to match your environment
nano .env  # or use your preferred editor
```

**Key environment variables:**

```bash
# Database (PostgreSQL)
DATABASE_URL="postgresql://postgres:postgres@localhost:5442/dealbrain"
SQLALCHEMY_ECHO=false

# Redis (Caching & Task Queue)
REDIS_URL="redis://redis:6379/0"

# Frontend API URL (for Next.js)
NEXT_PUBLIC_API_URL="http://localhost:8000"

# FastAPI Settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# Observability
OTEL_ENABLED=true
PROMETHEUS_PORT=9090
```

**For production**, change:
- `ENVIRONMENT=production`
- `DEBUG=false`
- `SECRET_KEY` to a secure random value
- Database credentials to production database
- `NEXT_PUBLIC_API_URL` to production URL

See `.env.example` for all available options.

### Step 5: Set Up the Database

**Using Docker (recommended):**
```bash
# Start PostgreSQL via Docker Compose
make up

# In another terminal, apply migrations
poetry run alembic upgrade head

# Verify database connection
poetry run psql $DATABASE_URL -c "SELECT version();"
```

**Using local PostgreSQL (if not using Docker):**
```bash
# Create database
createdb dealbrain

# Update DATABASE_URL in .env
DATABASE_URL="postgresql://username:password@localhost:5432/dealbrain"

# Apply migrations
poetry run alembic upgrade head
```

---

## Environment Configuration

### Configuration Files

| File | Purpose | Required |
|------|---------|----------|
| `.env` | Environment variables | Yes |
| `.env.example` | Example configuration | No (reference only) |
| `pyproject.toml` | Python project config | Yes (in repo) |
| `package.json` | JavaScript packages | Yes (in repo) |
| `docker-compose.yml` | Docker services | Yes (in repo) |
| `alembic.ini` | Database migrations | Yes (in repo) |

### Environment Categories

**Development:**
```bash
ENVIRONMENT=development
DEBUG=true
SQLALCHEMY_ECHO=true
LOG_LEVEL=debug
```

**Testing:**
```bash
ENVIRONMENT=testing
DATABASE_URL="sqlite:///./test.db"
DEBUG=true
```

**Production:**
```bash
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<long-random-string>
ALLOWED_HOSTS=yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

---

## Database Setup

### Initial Setup

```bash
# Apply all pending migrations
make migrate

# Or manually
poetry run alembic upgrade head
```

### Database Inspection

```bash
# Connect to database
psql $DATABASE_URL

# List tables
\dt

# Describe a table
\d listing

# View recent migrations
poetry run alembic history --rev-range=-5:
```

### Creating a New Migration

After modifying SQLAlchemy models:

```bash
# Auto-generate migration (recommended)
poetry run alembic revision --autogenerate -m "Add user_email column"

# Review the generated migration in alembic/versions/
# Then apply it
poetry run alembic upgrade head
```

### Reverting Migrations

```bash
# Revert to previous migration
poetry run alembic downgrade -1

# Revert multiple
poetry run alembic downgrade -2

# Revert to specific migration
poetry run alembic downgrade <revision_hash>
```

---

## Data Import

### Import Excel Workbooks

```bash
# Simple import
poetry run dealbrain-cli import ./data/imports/listings.xlsx

# Import with verbose output
poetry run dealbrain-cli import -v ./data/imports/listings.xlsx

# Validate without importing
poetry run dealbrain-cli import --validate-only ./data/imports/listings.xlsx
```

**Expected file structure:**
- Excel file with sheets for CPUs, GPUs, Valuation Rules, Profiles, Listings
- See `data/README.md` for detailed format specification

### Import Marketplace URLs

**Via Web UI:**
1. Navigate to `/dashboard/import`
2. Enter a single URL or upload CSV/JSON with multiple URLs
3. Monitor import progress in real-time

**Via CLI:**
```bash
poetry run dealbrain-cli import-url "https://www.ebay.com/itm/123456789"
```

### Seed Sample Data

```bash
# Load sample data (useful for development)
make seed

# This populates:
# - Sample CPUs and GPUs
# - Valuation rules
# - Scoring profiles
# - Example listings
```

---

## Running Services

### Full Stack with Docker (Recommended)

```bash
# Start all services
make up

# Services will be available at:
# - API:        http://localhost:8000
# - Web:        http://localhost:3000
# - Grafana:    http://localhost:3001
# - Prometheus: http://localhost:9090
# - PostgreSQL: localhost:5442
# - Redis:      localhost:6399

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f web
docker-compose logs -f worker

# Stop all services
make down

# Restart a specific service
docker-compose restart api
```

### Local Development (Without Docker)

```bash
# Terminal 1: FastAPI dev server
make api
# Available at http://localhost:8000
# Auto-reloads on file changes

# Terminal 2: Next.js dev server
make web
# Available at http://localhost:3000
# Auto-reloads on file changes

# Terminal 3 (optional): Celery worker for background tasks
poetry run celery -A dealbrain_api.worker worker --loglevel=info

# Terminal 4 (optional): Celery flower (task monitoring)
poetry run celery -A dealbrain_api.worker flower --port=5555
# Available at http://localhost:5555
```

**Requirements for local development:**
- PostgreSQL running (start with `make up` in separate terminal, then Ctrl+C after postgres starts)
- Redis running (included in Docker)

### Accessing Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Web UI** | http://localhost:3000 | Main application |
| **API Docs** | http://localhost:8000/docs | Swagger interactive API docs |
| **API ReDoc** | http://localhost:8000/redoc | Alternative API documentation |
| **Grafana** | http://localhost:3001 | Metrics dashboards (admin/admin) |
| **Prometheus** | http://localhost:9090 | Metrics data (queries) |
| **Flower** | http://localhost:5555 | Celery task monitoring |

---

## Development Workflow

### Code Quality Checks

```bash
# Format code (Black, isort, Prettier)
make format

# Lint code (ruff, ESLint)
make lint

# Run both format and lint
make format && make lint

# Commit hooks will also run these automatically
```

### Running Tests

```bash
# All tests
make test

# Specific test file
poetry run pytest tests/test_valuation_service.py -v

# With coverage report
poetry run pytest --cov=dealbrain_api tests/

# Run specific test function
poetry run pytest tests/test_valuation_service.py::test_apply_rules -v

# Run tests matching pattern
poetry run pytest -k "valuation" -v
```

### Database Migrations in Development

```bash
# After modifying models
poetry run alembic revision --autogenerate -m "Description"

# Review generated migration
cat alembic/versions/<hash>_description.py

# Apply
poetry run alembic upgrade head

# Verify
poetry run alembic current
```

---

## Troubleshooting

### Port Already in Use

**Problem**: Port 8000, 3000, or other port is already in use

**Solutions**:
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in .env
API_PORT=8001
NEXT_PORT=3001
```

### PostgreSQL Connection Refused

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Start PostgreSQL via Docker
make up

# Or verify DATABASE_URL in .env
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Poetry/pnpm Dependency Issues

**Problem**: `poetry install` fails with dependency conflicts

**Solutions**:
```bash
# Clear poetry cache
poetry cache clear . --all

# Remove lock file and reinstall
rm poetry.lock
poetry install

# Or update dependencies
poetry update
```

**Problem**: `pnpm install` fails

**Solutions**:
```bash
# Clear pnpm cache
pnpm store prune

# Reinstall with clean slate
rm -rf node_modules
pnpm install

# Update all packages
pnpm update
```

### Docker Container Crashes

**Problem**: `docker-compose up` fails, containers keep restarting

**Solutions**:
```bash
# Check logs
docker-compose logs api

# Rebuild images
docker-compose build --no-cache

# Clean up and restart
docker-compose down -v
docker-compose up
```

### Database Migrations Fail

**Problem**: `alembic upgrade head` fails

**Solutions**:
```bash
# Check migration history
poetry run alembic history

# See current state
poetry run alembic current

# Downgrade to safe point
poetry run alembic downgrade -1

# Then upgrade carefully
poetry run alembic upgrade +1
```

### API Returns 500 Errors

**Problem**: API requests return HTTP 500 errors

**Solutions**:
```bash
# Check API logs
docker-compose logs api

# Or if running locally
# Check terminal where `make api` is running

# Verify environment variables
env | grep DATABASE
env | grep REDIS

# Check database is accessible
psql $DATABASE_URL -c "SELECT 1"
```

### Frontend Blank/Not Loading

**Problem**: http://localhost:3000 shows blank page or console errors

**Solutions**:
```bash
# Clear Next.js cache
rm -rf apps/web/.next

# Reinstall node modules
pnpm -C apps/web install

# Check NEXT_PUBLIC_API_URL points to running API
grep NEXT_PUBLIC_API_URL .env

# Check API is actually running
curl http://localhost:8000/health
```

### Import Fails

**Problem**: Data import fails or hangs

**Solutions**:
```bash
# Check file format and location
ls -lh data/imports/

# Validate file (dry run)
poetry run dealbrain-cli import --validate-only ./data/imports/file.xlsx

# Check database schema
poetry run alembic current

# Check import logs
docker-compose logs -f api | grep import
```

### Tests Fail

**Problem**: `pytest` or test suite fails

**Solutions**:
```bash
# Ensure test database exists
ENVIRONMENT=testing poetry run alembic upgrade head

# Run with verbose output
poetry run pytest -vv

# Run specific failing test
poetry run pytest tests/test_file.py::test_function -vv

# Clear pytest cache
rm -rf .pytest_cache
pytest --cache-clear
```

### Memory Issues

**Problem**: Docker containers use too much memory, system slows down

**Solutions**:
```bash
# Check resource usage
docker stats

# Limit memory for containers in docker-compose.yml
# Add to services:
#   deploy:
#     resources:
#       limits:
#         memory: 512M

# Remove unused images/containers
docker system prune -a

# Restart with resource limits
docker-compose down
docker-compose up
```

---

## Docker & Container Setup

### Docker Compose Services

When running `make up`, these services start:

| Service | Port | Purpose | Image |
|---------|------|---------|-------|
| **postgres** | 5442 | Database | postgres:15 |
| **redis** | 6399 | Cache/Queue | redis:7 |
| **api** | 8000 | FastAPI server | Local build |
| **web** | 3000 | Next.js server | Local build |
| **worker** | – | Celery tasks | Local build |
| **prometheus** | 9090 | Metrics collection | prom/prometheus:latest |
| **grafana** | 3001 | Metrics dashboards | grafana/grafana:latest |
| **otel-collector** | 4317 | Distributed tracing | otel/opentelemetry-collector:latest |

### Building Docker Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build api

# Build without cache
docker-compose build --no-cache

# Build with custom Dockerfile
docker-compose -f docker-compose.prod.yml build
```

### Viewing Logs

```bash
# All service logs
docker-compose logs

# Follow logs (realtime)
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Show timestamps
docker-compose logs -t

# Last 100 lines
docker-compose logs --tail=100
```

### Container Inspection

```bash
# List running containers
docker-compose ps

# Shell access to container
docker-compose exec api bash
docker-compose exec web sh

# Inspect container
docker inspect deal-brain-api-1

# View resource usage
docker stats
```

### Cleaning Up Docker Resources

```bash
# Stop all services
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove images too
docker-compose down -v --rmi all

# Clean up unused Docker resources
docker system prune -a
```

---

## Production Setup

For deployment to production, see the [root README.md](../../README.md#installation--setup) which covers production considerations.

Key differences from development:
- Use production Docker image
- Set `ENVIRONMENT=production` and `DEBUG=false`
- Use strong `SECRET_KEY`
- Configure proper CORS and allowed hosts
- Set up HTTPS with SSL certificate
- Use production database and Redis
- Configure observability/monitoring
- Enable backup and recovery procedures

---

## Getting Help

### Documentation
- **[System Architecture](../architecture/architecture.md)** – Understand the system
- **[API Reference](../reports/codebase_analysis/06-api-documentation.md)** – API endpoints
- **[Troubleshooting](#troubleshooting)** – Common issues

### Debugging
- Check logs: `docker-compose logs -f`
- API Swagger docs: http://localhost:8000/docs
- Grafana dashboards: http://localhost:3001

### Asking for Help
1. Search existing GitHub issues
2. Check this guide's [Troubleshooting section](#troubleshooting)
3. Open a GitHub discussion with:
   - OS and Python/Node version
   - Error messages and logs
   - Steps to reproduce

---

**Last Updated**: October 24, 2025
**Setup Version**: 2.0
