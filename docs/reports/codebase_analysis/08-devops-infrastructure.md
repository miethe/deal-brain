# DevOps & Infrastructure

**Location**: `/mnt/containers/deal-brain/`

**Purpose**: Comprehensive guide to Deal Brain's containerized architecture, deployment, observability, and operational workflows.

---

## Table of Contents

1. [Docker Architecture](#docker-architecture)
2. [Individual Service Dockerfiles](#individual-service-dockerfiles)
3. [Environment Configuration](#environment-configuration)
4. [Database Management](#database-management)
5. [Caching & Queue](#caching--queue)
6. [Observability Stack](#observability-stack)
7. [Development Workflow](#development-workflow)
8. [Production Considerations](#production-considerations)
9. [CI/CD](#cicd)

---

## 1. Docker Architecture

### Overview

Deal Brain uses Docker Compose to orchestrate a multi-service stack with comprehensive observability. The architecture separates concerns across 8 services with proper health checks, volume management, and network isolation.

### docker-compose.yml Structure

**Location**: `/mnt/containers/deal-brain/docker-compose.yml`

```yaml
version: "3.9"

services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: dealbrain
      POSTGRES_PASSWORD: dealbrain
      POSTGRES_DB: dealbrain
    ports:
      - "5442:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dealbrain"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6399:6379"
    volumes:
      - redis_data:/data

  api:
    build:
      context: .
      dockerfile: infra/api/Dockerfile
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    env_file: .env.example
    environment:
      DATABASE_URL: postgresql+asyncpg://dealbrain:dealbrain@db:5432/dealbrain
      SYNC_DATABASE_URL: postgresql+psycopg://dealbrain:dealbrain@db:5432/dealbrain
    ports:
      - "8020:8000"
    command: ["dealbrain-api"]

  worker:
    build:
      context: .
      dockerfile: infra/worker/Dockerfile
    depends_on:
      api:
        condition: service_started
      redis:
        condition: service_started
    env_file: .env.example
    command: ["celery", "-A", "dealbrain_api.worker", "worker", "-l", "info"]

  web:
    build:
      context: .
      dockerfile: infra/web/Dockerfile
    depends_on:
      api:
        condition: service_started
    environment:
      # Update this to your remote host's IP if running remotely
      NEXT_PUBLIC_API_URL: http://10.42.9.11:8020
    ports:
      - "3020:3000"
    command: ["pnpm", "--filter", "web", "dev", "--", "-H", "0.0.0.0"]

  otel-collector:
    image: otel/opentelemetry-collector:0.89.0
    restart: unless-stopped
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./infra/otel/config.yaml:/etc/otel-collector-config.yaml:ro

  prometheus:
    image: prom/prometheus:v2.50.0
    restart: unless-stopped
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:10.3.1
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin
    ports:
      - "3021:3000"
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  db_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### Service Breakdown

| Service | Image/Build | Port Mapping | Purpose |
|---------|------------|--------------|---------|
| **db** | postgres:15-alpine | 5442:5432 | Primary PostgreSQL database with health checks |
| **redis** | redis:7-alpine | 6399:6379 | Cache and Celery message broker |
| **api** | infra/api/Dockerfile | 8020:8000 | FastAPI backend with async SQLAlchemy |
| **worker** | infra/worker/Dockerfile | - | Celery worker for background tasks |
| **web** | infra/web/Dockerfile | 3020:3000 | Next.js 14 frontend with App Router |
| **otel-collector** | otel/opentelemetry-collector:0.89.0 | - | OpenTelemetry metrics aggregation |
| **prometheus** | prom/prometheus:v2.50.0 | 9090:9090 | Time-series metrics database |
| **grafana** | grafana/grafana:10.3.1 | 3021:3000 | Metrics visualization dashboards |

### Port Mappings

Development ports are offset from standard ports to avoid conflicts:

```
Standard    Deal Brain    Service
5432   -->  5442          PostgreSQL
6379   -->  6399          Redis
8000   -->  8020          FastAPI API
3000   -->  3020          Next.js Web
9090   -->  9090          Prometheus
3000   -->  3021          Grafana
```

### Volume Management

Four named volumes provide data persistence:

- **db_data**: PostgreSQL data directory (`/var/lib/postgresql/data`)
- **redis_data**: Redis persistence (`/data`)
- **prometheus_data**: Time-series metrics storage (`/prometheus`)
- **grafana_data**: Dashboard configurations and state (`/var/lib/grafana`)

**Volume Operations**:

```bash
# List volumes
docker volume ls | grep deal-brain

# Inspect volume
docker volume inspect deal-brain_db_data

# Remove all volumes (destructive!)
docker-compose down -v

# Backup database volume
docker run --rm -v deal-brain_db_data:/data -v $(pwd):/backup alpine tar czf /backup/db_backup.tar.gz /data
```

### Health Checks

Only the database service implements health checks in the compose file:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U dealbrain"]
  interval: 10s
  timeout: 5s
  retries: 5
```

The API service waits for database health before starting via dependency conditions:

```yaml
depends_on:
  db:
    condition: service_healthy
```

### Networking

All services communicate via Docker's default bridge network with automatic service discovery. Services reference each other by service name:

- API connects to database: `postgresql+asyncpg://dealbrain:dealbrain@db:5432/dealbrain`
- Worker connects to Redis: `redis://redis:6379/0`
- Prometheus scrapes API: `api:8000/metrics`

---

## 2. Individual Service Dockerfiles

### API Dockerfile

**Location**: `/mnt/containers/deal-brain/infra/api/Dockerfile`

```dockerfile
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY apps ./apps
COPY packages ./packages
COPY data ./data

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8000

CMD ["dealbrain-api"]
```

**Key Features**:
- Single-stage build for simplicity (not optimized for production)
- Python 3.11 slim base for smaller image size
- Installs PostgreSQL client libraries (libpq-dev)
- Copies entire monorepo structure (apps, packages, data)
- Uses Poetry-generated `pyproject.toml` for pip installation
- Exposes port 8000 internally
- Runs FastAPI via Poetry script `dealbrain-api`

**Optimization Opportunities**:
- Multi-stage build to exclude build dependencies from runtime
- Use `poetry export` to create requirements.txt
- Copy only necessary files (avoid data directory)
- Use Docker layer caching for dependencies

### Web Dockerfile

**Location**: `/mnt/containers/deal-brain/infra/web/Dockerfile`

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* .npmrc* ./
COPY pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/js-ui/package.json ./packages/js-ui/package.json
RUN corepack enable pnpm \
    && pnpm install --frozen-lockfile=false

FROM node:20-alpine AS runtime
ENV NODE_ENV=development
WORKDIR /app
RUN corepack enable pnpm
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/pnpm-lock.yaml* ./
COPY pnpm-workspace.yaml ./
COPY package.json ./
COPY apps ./apps
COPY packages ./packages
EXPOSE 3000
CMD ["pnpm", "--filter", "web", "dev", "--", "-H", "0.0.0.0"]
```

**Key Features**:
- Multi-stage build separating dependency installation from runtime
- Uses Node 20 Alpine for minimal footprint
- Enables pnpm via corepack (built into Node 20+)
- Workspace-aware installation for monorepo
- Development mode with hot reload enabled
- Listens on 0.0.0.0 for external access

**Development vs Production**:
```dockerfile
# Production would use:
# - NODE_ENV=production
# - pnpm build step
# - Static file serving via nginx
# - No source code copying
```

### Worker Dockerfile

**Location**: `/mnt/containers/deal-brain/infra/worker/Dockerfile`

```dockerfile
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY apps ./apps
COPY packages ./packages
COPY data ./data

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

CMD ["celery", "-A", "dealbrain_api.worker", "worker", "-l", "info"]
```

**Key Features**:
- Identical to API Dockerfile except for CMD
- Shares same dependencies (FastAPI, SQLAlchemy, Celery)
- Runs Celery worker process
- Log level set to INFO

**Optimization**:
- Could share base image with API service
- Consider using Docker BuildKit cache mounts

---

## 3. Environment Configuration

### .env.example Structure

**Location**: `/mnt/containers/deal-brain/.env.example`

```env
# Deal Brain environment variables
DATABASE_URL=postgresql+asyncpg://dealbrain:dealbrain@db:5432/dealbrain
SYNC_DATABASE_URL=postgresql+psycopg://dealbrain:dealbrain@db:5432/dealbrain
REDIS_URL=redis://redis:6379/0
SECRET_KEY=changeme
LOG_LEVEL=INFO
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
WEB_URL=http://localhost:3000

# Data import paths
IMPORT_ROOT=./data/imports
EXPORT_ROOT=./data/exports

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
PROMETHEUS_ENABLED=true
```

### Environment Variables by Service

#### API Service

| Variable | Purpose | Example |
|----------|---------|---------|
| DATABASE_URL | Async SQLAlchemy connection | `postgresql+asyncpg://user:pass@db:5432/dealbrain` |
| SYNC_DATABASE_URL | Synchronous connection (Alembic) | `postgresql+psycopg://user:pass@db:5432/dealbrain` |
| REDIS_URL | Celery broker and cache | `redis://redis:6379/0` |
| SECRET_KEY | JWT/session signing | Generate with `openssl rand -hex 32` |
| LOG_LEVEL | Logging verbosity | INFO, DEBUG, WARNING |
| ENVIRONMENT | Deployment environment | development, staging, production |
| API_HOST | Uvicorn bind address | 0.0.0.0 for Docker, 127.0.0.1 local |
| API_PORT | Uvicorn port | 8000 |
| PROMETHEUS_ENABLED | Enable /metrics endpoint | true/false |
| OTEL_EXPORTER_OTLP_ENDPOINT | OpenTelemetry collector | http://otel-collector:4317 |

**Settings Implementation**:

```python
# apps/api/dealbrain_api/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    environment: str = "development"
    log_level: str = "INFO"
    database_url: str
    sync_database_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "changeme"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    prometheus_enabled: bool = True
    otel_exporter_otlp_endpoint: str | None = None
```

#### Web Service

| Variable | Purpose | Example |
|----------|---------|---------|
| NEXT_PUBLIC_API_URL | API endpoint for browser | `http://10.42.9.11:8020` |
| NODE_ENV | Next.js environment | development, production |

**Important**: The `NEXT_PUBLIC_` prefix exposes variables to browser code. Set to Docker host IP for remote access.

#### Worker Service

Inherits same environment as API service (DATABASE_URL, REDIS_URL, etc.)

### Secrets Management

**Current State**: Plaintext in .env files (development only)

**Production Recommendations**:

```bash
# Use Docker secrets
echo "super_secret_key" | docker secret create db_password -
```

```yaml
# docker-compose.yml
services:
  api:
    secrets:
      - db_password
    environment:
      DATABASE_URL: postgresql+asyncpg://dealbrain:@db:5432/dealbrain
      DATABASE_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    external: true
```

**Alternative Approaches**:
- AWS Secrets Manager with ECS task roles
- Kubernetes Secrets mounted as volumes
- HashiCorp Vault integration
- Environment variable injection via CI/CD

---

## 4. Database Management

### PostgreSQL 15 Setup

**Container Configuration**:
- Image: `postgres:15-alpine`
- Volume: `db_data:/var/lib/postgresql/data`
- Port: 5442 (external) -> 5432 (internal)
- User/Password: dealbrain/dealbrain
- Database: dealbrain

**Health Check**: `pg_isready -U dealbrain` every 10 seconds

### Connection Pooling

**Async Engine (API)**:

```python
# apps/api/dealbrain_api/db.py
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

_engine: AsyncEngine | None = None

def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            future=True,
            pool_size=5,           # Default connection pool
            max_overflow=10,       # Additional connections under load
            pool_pre_ping=True,    # Test connections before use
        )
    return _engine
```

**Session Management**:

```python
@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope for async operations."""
    session = get_session_factory()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

### Alembic Migration Workflow

**Configuration**: `/mnt/containers/deal-brain/alembic.ini`

```ini
[alembic]
script_location = apps/api/alembic
sqlalchemy.url = sqlite:///./dealbrain.db  # Overridden by env var
```

**Migration Directory**: `/mnt/containers/deal-brain/apps/api/alembic/versions/`

**Current Migrations** (18 total):
1. 0001_initial.py - Core schema (CPU, GPU, Listing, ValuationRule)
2. 0002_import_sessions.py - Import job tracking
3. 0003_enum_to_string.py - Enum to string migration
4. 0004_importer_custom_fields.py - Dynamic custom fields
5. 0005_custom_field_enhancements.py - Field metadata
6. 0006_custom_field_audit.py - Audit columns
7. 0007_custom_field_locking.py - Field locking
8. 0008_replace_valuation_rules_v2.py - Rule system v2
9. 0009_add_profile_rule_group_weights.py - Profile weighting
10. 0010_add_application_settings_table.py - App settings
11. 0011_add_cpu_igpu_mark.py - Integrated GPU benchmarks
12. 0012_add_listing_performance_metrics.py - Performance metrics
13. 0013_add_listing_metadata_fields.py - Product metadata
14. 0014_add_cpu_passmark_fields.py - PassMark benchmark data
15. 0015_listing_links_and_ruleset_priority.py - External links
16. 0016_add_rule_group_is_active.py - Rule group activation
17. 0017_ram_and_storage_profiles.py - Component profiles

**Common Commands**:

```bash
# Apply all pending migrations
make migrate
# or
poetry run alembic upgrade head

# Generate new migration
poetry run alembic revision --autogenerate -m "add_new_column"

# View migration history
poetry run alembic history

# Rollback one migration
poetry run alembic downgrade -1

# View current revision
poetry run alembic current
```

**Environment Override**:

```python
# apps/api/alembic/env.py
from dealbrain_api.settings import get_settings

config.set_main_option(
    "sqlalchemy.url",
    get_settings().sync_database_url or get_settings().database_url
)
```

### Backup Considerations

**Manual Backup**:

```bash
# Using docker exec
docker exec deal-brain-db-1 pg_dump -U dealbrain dealbrain > backup.sql

# Using docker volume
docker run --rm -v deal-brain_db_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/db_backup_$(date +%Y%m%d).tar.gz /data

# Restore
docker exec -i deal-brain-db-1 psql -U dealbrain dealbrain < backup.sql
```

**Production Recommendations**:
- Automated daily backups to S3/GCS
- Point-in-time recovery (PITR) via WAL archiving
- Managed database service (RDS, Cloud SQL)
- Backup retention policy (7 days daily, 4 weeks weekly)

**PostgreSQL Configuration** (for production):

```bash
# postgresql.conf tuning
shared_buffers = 256MB           # 25% of RAM
effective_cache_size = 1GB       # 50% of RAM
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 100
```

---

## 5. Caching & Queue

### Redis Configuration

**Container**:
- Image: `redis:7-alpine`
- Volume: `redis_data:/data`
- Port: 6399 (external) -> 6379 (internal)

**Persistence**: Enabled via volume mount (RDB snapshots)

**Connection String**: `redis://redis:6379/0`

### Celery Worker Setup

**Worker Configuration**:

```python
# apps/api/dealbrain_api/worker.py
from celery import Celery

celery_app = Celery("dealbrain")
celery_app.config_from_object({
    "broker_url": "redis://redis:6379/0",
    "result_backend": "redis://redis:6379/0",
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
})
```

**Container Command**: `celery -A dealbrain_api.worker worker -l info`

### Task Types

**Valuation Recalculation Task**:

```python
# apps/api/dealbrain_api/tasks/valuation.py
@celery_app.task(name="valuation.recalculate_listings", bind=True)
def recalculate_listings_task(
    self,
    *,
    listing_ids: Iterable[int | str | None] | None = None,
    ruleset_id: int | None = None,
    batch_size: int = 100,
    include_inactive: bool = False,
    reason: str | None = None,
) -> dict[str, int]:
    """Celery task entry-point for listing recalculation."""
    # Async execution wrapper
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(
        _recalculate_listings_async(
            listing_ids=listing_ids,
            ruleset_id=ruleset_id,
            batch_size=batch_size,
            include_inactive=include_inactive,
        )
    )
```

**Task Features**:
- Asynchronous database operations via SQLAlchemy
- Batch processing (100 listings per batch)
- Progress tracking via counters
- Error handling with fallback to synchronous execution

### Task Scheduling

**Manual Enqueue**:

```python
from dealbrain_api.tasks.valuation import recalculate_listings_task

# Queue task
recalculate_listings_task.delay(
    listing_ids=[1, 2, 3],
    reason="ruleset_updated"
)
```

**API Trigger**:

```python
# apps/api/dealbrain_api/services/listings.py
from dealbrain_api.tasks.valuation import enqueue_listing_recalculation

def update_ruleset(session, ruleset_id):
    # ... update logic ...

    # Trigger recalculation
    enqueue_listing_recalculation(
        ruleset_id=ruleset_id,
        reason="ruleset_updated"
    )
```

**Monitoring Tasks**:

```bash
# View active tasks
docker exec deal-brain-worker-1 celery -A dealbrain_api.worker inspect active

# View registered tasks
docker exec deal-brain-worker-1 celery -A dealbrain_api.worker inspect registered

# Purge queue
docker exec deal-brain-worker-1 celery -A dealbrain_api.worker purge
```

### Future Task Types

**Potential Background Jobs**:
- **Import processing**: Excel workbook parsing
- **Data enrichment**: CPU benchmark fetching
- **Report generation**: Export to PDF/Excel
- **Email notifications**: Price alerts
- **Scheduled cleanups**: Old import data deletion

---

## 6. Observability Stack

### Architecture Overview

```
FastAPI App --> OpenTelemetry Instrumentation --> OTLP Exporter
                                                      |
                                                      v
                                              OTEL Collector
                                                      |
                                            +----------+---------+
                                            |                    |
                                            v                    v
                                       Prometheus            Logging
                                            |
                                            v
                                        Grafana
```

### OpenTelemetry Configuration

**Location**: `/mnt/containers/deal-brain/infra/otel/config.yaml`

```yaml
receivers:
  otlp:
    protocols:
      grpc:
      http:

exporters:
  logging:
    loglevel: info
  prometheus:
    endpoint: 0.0.0.0:9464

service:
  pipelines:
    metrics:
      receivers: [otlp]
      exporters: [prometheus, logging]
    traces:
      receivers: [otlp]
      exporters: [logging]
```

**Key Features**:
- Receives metrics via OTLP (gRPC and HTTP)
- Exports metrics to Prometheus on port 9464
- Logs all traces and metrics to stdout
- No trace export to external service (could add Jaeger/Tempo)

### Prometheus Configuration

**Location**: `/mnt/containers/deal-brain/infra/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "dealbrain-api"
    metrics_path: /metrics
    static_configs:
      - targets: ["api:8000"]

  - job_name: "otel-collector"
    static_configs:
      - targets: ["otel-collector:9464"]
```

**Scrape Targets**:
1. **dealbrain-api** - FastAPI `/metrics` endpoint (15s interval)
2. **otel-collector** - OTEL Collector internal metrics

**Access**: http://localhost:9090

### FastAPI Instrumentation

**Implementation**:

```python
# apps/api/dealbrain_api/app.py
from prometheus_fastapi_instrumentator import Instrumentator

def create_app() -> FastAPI:
    app = FastAPI(title="Deal Brain API", version="0.1.0")

    # Instrument the app for Prometheus metrics
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app)

    return app
```

**Exposed Metrics** (via prometheus-fastapi-instrumentator):

```
# HTTP request count
http_requests_total{method="GET",path="/api/v1/listings",status="200"} 42

# HTTP request duration
http_request_duration_seconds_bucket{le="0.1",method="GET",path="/api/v1/listings"} 38
http_request_duration_seconds_sum{method="GET",path="/api/v1/listings"} 3.2
http_request_duration_seconds_count{method="GET",path="/api/v1/listings"} 42

# HTTP requests in progress
http_requests_in_progress{method="GET",path="/api/v1/listings"} 2
```

**Custom Metrics Example**:

```python
from prometheus_client import Counter, Histogram

# Define custom metrics
listing_valuations_total = Counter(
    "listing_valuations_total",
    "Total number of listing valuations performed",
    ["status"]
)

valuation_duration_seconds = Histogram(
    "valuation_duration_seconds",
    "Time spent calculating listing valuations"
)

# Instrument code
with valuation_duration_seconds.time():
    result = calculate_valuation(listing)
listing_valuations_total.labels(status="success").inc()
```

### Grafana Dashboards

**Access**:
- URL: http://localhost:3021
- Username: `admin`
- Password: `admin`

**Data Source Configuration**:

```yaml
# Automatically configure Prometheus datasource
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

**Recommended Dashboards**:

1. **API Overview**:
   - Request rate (req/sec)
   - Error rate (%)
   - P50/P95/P99 latency
   - Requests in progress

2. **Database Performance**:
   - Connection pool utilization
   - Query duration
   - Active transactions

3. **Celery Workers**:
   - Task queue length
   - Task success/failure rate
   - Task execution time

4. **System Resources**:
   - Container CPU usage
   - Memory utilization
   - Disk I/O

**Sample PromQL Queries**:

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Slow endpoints
topk(5, avg(rate(http_request_duration_seconds_sum[5m])) by (path))
```

### Logging Strategy

**Current State**:
- Stdout/stderr logging to Docker daemon
- Log level controlled by `LOG_LEVEL` environment variable

**View Logs**:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# Since timestamp
docker-compose logs --since 2024-10-14T10:00:00 api
```

**Production Recommendations**:

1. **Structured Logging**:
```python
# Use structlog for JSON output
import structlog

logger = structlog.get_logger()
logger.info("listing_valued", listing_id=123, adjusted_price=599.99)
```

2. **Log Aggregation**:
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Loki + Grafana
   - CloudWatch Logs / Stackdriver
   - Fluentd/Fluent Bit collectors

3. **Log Retention**:
   - Docker log rotation: `max-size: "10m", max-file: "3"`
   - Centralized storage with retention policies

4. **Sensitive Data Redaction**:
```python
# Filter secrets from logs
import re

def sanitize_log(message: str) -> str:
    return re.sub(r'password=\S+', 'password=***', message)
```

### Alerting (Future)

**Prometheus Alertmanager Integration**:

```yaml
# prometheus.yml
rule_files:
  - /etc/prometheus/alerts.yml

alerting:
  alertmanagers:
    - static_configs:
      - targets: ["alertmanager:9093"]
```

**Sample Alert Rules**:

```yaml
# alerts.yml
groups:
  - name: dealbrain
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m]) /
          rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: APIDown
        expr: up{job="dealbrain-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API is down"
```

---

## 7. Development Workflow

### Local Development Setup

**Initial Setup** (without Docker):

```bash
# Clone repository
git clone <repo-url> deal-brain
cd deal-brain

# Install dependencies
make setup
# Equivalent to:
#   poetry install
#   pnpm install --frozen-lockfile=false

# Start external dependencies (Postgres + Redis)
docker-compose up -d db redis

# Run database migrations
make migrate

# Seed sample data
make seed
```

**Run Services Locally**:

```bash
# Terminal 1: API server
make api
# Runs: poetry run dealbrain-api
# Access: http://localhost:8000/docs

# Terminal 2: Web server
make web
# Runs: pnpm --filter web dev
# Access: http://localhost:3000

# Terminal 3: Celery worker (optional)
poetry run celery -A dealbrain_api.worker worker -l info
```

### Running Full Stack

**Start All Services**:

```bash
# Build and start all containers
make up
# Equivalent to: docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop all services
make down
# Equivalent to: docker-compose down
```

**Service Health Checks**:

```bash
# API health
curl http://localhost:8020/health

# Web access
open http://localhost:3020

# Prometheus targets
open http://localhost:9090/targets

# Grafana
open http://localhost:3021
```

### Hot Reload Capabilities

**API (FastAPI)**:
- Uvicorn runs with `reload=True` flag
- Watches Python files for changes
- Auto-restarts on file modification
- Reload excludes: `.git`, `__pycache__`, `*.pyc`

```python
# apps/api/dealbrain_api/main.py
uvicorn.run(
    "dealbrain_api.main:get_app",
    host="0.0.0.0",
    port=8000,
    reload=True,  # Hot reload enabled
    factory=True,
)
```

**Web (Next.js)**:
- Fast Refresh enabled by default
- Instant browser updates on save
- Preserves component state
- Error overlay for debugging

**Worker (Celery)**:
- No hot reload in production
- Development: Use watchdog or restart manually
- Future: `celery -A dealbrain_api.worker worker --autoreload`

### Debugging Strategies

**API Debugging**:

1. **VS Code Launch Configuration**:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "dealbrain_api.main:get_app",
        "--factory",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

2. **Interactive Debugging**:
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use ipdb
import ipdb; ipdb.set_trace()
```

3. **Database Query Logging**:
```python
# Enable SQLAlchemy echo
_engine = create_async_engine(
    settings.database_url,
    echo=True,  # Log all SQL queries
    future=True
)
```

**Web Debugging**:

1. **Browser DevTools**: React DevTools, Network tab
2. **Next.js Error Overlay**: Auto-displays runtime errors
3. **Console Logging**:
```typescript
console.log('[DEBUG]', { listings, filters });
```

**Worker Debugging**:

```bash
# Run worker in foreground with debug logging
poetry run celery -A dealbrain_api.worker worker -l debug

# Inspect task state
poetry run python
>>> from dealbrain_api.worker import celery_app
>>> celery_app.control.inspect().active()
```

### Code Quality Checks

**Linting**:

```bash
# Run all linters
make lint

# Python (ruff)
poetry run ruff check .

# TypeScript (eslint)
pnpm --filter web lint
```

**Formatting**:

```bash
# Format all code
make format

# Python (black + isort)
poetry run black .
poetry run isort .

# TypeScript (prettier via eslint)
pnpm --filter web lint --fix
```

**Type Checking**:

```bash
# Python (mypy)
poetry run mypy apps/api apps/cli packages/core

# TypeScript (built into Next.js build)
pnpm --filter web build
```

### Testing

**Run Full Test Suite**:

```bash
make test
# Equivalent to: poetry run pytest
```

**Test with Coverage**:

```bash
poetry run pytest --cov=dealbrain_api --cov=dealbrain_core --cov-report=html
```

**Run Specific Tests**:

```bash
# Single test file
poetry run pytest tests/test_custom_fields_service.py -v

# Single test function
poetry run pytest tests/test_custom_fields_service.py::test_create_field -v

# Tests matching pattern
poetry run pytest -k "test_valuation" -v
```

**Watch Mode** (requires pytest-watch):

```bash
poetry run ptw tests/ --clear
```

---

## 8. Production Considerations

### Build Optimization

**Multi-Stage Dockerfiles**:

```dockerfile
# Optimized API Dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir poetry && \
    poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.11-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps ./apps
COPY packages ./packages
EXPOSE 8000
CMD ["gunicorn", "dealbrain_api.main:get_app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

**Next.js Production Build**:

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/
RUN corepack enable pnpm && pnpm install --frozen-lockfile

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED 1
RUN pnpm --filter web build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
```

**Image Size Comparison**:

| Build Type | API Size | Web Size |
|------------|----------|----------|
| Current (dev) | ~800MB | ~1.2GB |
| Optimized (prod) | ~250MB | ~180MB |

### Security Best Practices

**Environment Variables**:
- Never commit .env files
- Use secrets management (AWS Secrets Manager, Vault)
- Rotate credentials regularly
- Principle of least privilege

**Docker Security**:

```dockerfile
# Run as non-root user
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 app
USER app

# Drop capabilities
RUN apt-get purge -y build-essential && \
    rm -rf /var/lib/apt/lists/*
```

**Database Security**:
- Use connection pooling
- Enable SSL/TLS for connections
- Restrict network access (VPC, security groups)
- Regular security patches

**API Security**:
- Rate limiting (not currently implemented)
- CORS configuration (currently allows all origins)
- Input validation (Pydantic models)
- SQL injection prevention (SQLAlchemy ORM)

**Production CORS**:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dealbrain.com",
        "https://app.dealbrain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Scaling Strategies

**Horizontal Scaling**:

```yaml
# docker-compose.yml
services:
  api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: "1.0"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 512M
```

**Load Balancing**:

```nginx
# nginx.conf
upstream api {
    least_conn;
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Worker Scaling**:

```bash
# Scale Celery workers
docker-compose up -d --scale worker=5
```

**Database Scaling**:
- Read replicas for query load
- Connection pooling (PgBouncer)
- Caching layer (Redis, Memcached)
- Database partitioning

**CDN Integration**:
- Cloudflare / CloudFront for static assets
- Edge caching for API responses
- Image optimization

### Monitoring and Alerting

**SLOs (Service Level Objectives)**:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Availability | 99.5% uptime | Uptime monitors |
| API Latency | P95 < 500ms | Request duration histogram |
| Error Rate | < 1% | HTTP 5xx / total requests |
| Database | Query P95 < 100ms | SQLAlchemy instrumentation |

**Health Checks**:

```python
@app.get("/health")
async def health():
    # Check database connectivity
    async with session_scope() as session:
        await session.execute(text("SELECT 1"))

    # Check Redis connectivity
    redis_client.ping()

    return {
        "status": "healthy",
        "database": "ok",
        "redis": "ok"
    }
```

**Kubernetes Probes** (future):

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Deployment Architecture

**Kubernetes Deployment** (example):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dealbrain-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dealbrain-api
  template:
    metadata:
      labels:
        app: dealbrain-api
    spec:
      containers:
      - name: api
        image: dealbrain/api:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: dealbrain-api
spec:
  selector:
    app: dealbrain-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## 9. CI/CD

### Pre-Commit Hooks

**Configuration**: `/mnt/containers/deal-brain/.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.2
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/psf/black
    rev: 24.2.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-merge-conflict
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

**Install Pre-Commit**:

```bash
# Install hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files

# Update hooks
poetry run pre-commit autoupdate
```

**Hook Stages**:
1. **ruff**: Fast Python linter (replaces flake8, pylint)
2. **ruff-format**: Fast Python formatter
3. **black**: Python code formatter
4. **isort**: Import statement organizer
5. **check-merge-conflict**: Detect merge conflict markers
6. **end-of-file-fixer**: Ensure files end with newline
7. **trailing-whitespace**: Remove trailing whitespace

### Testing Strategy

**Test Pyramid**:

```
           /\
          /  \
         /E2E \         10% - End-to-end tests (Playwright)
        /------\
       /        \
      /Integration\     30% - Integration tests (API + DB)
     /------------\
    /              \
   /  Unit Tests    \   60% - Unit tests (services, domain logic)
  /------------------\
```

**Unit Tests**:
- Domain logic (`packages/core/`)
- Service layer (`apps/api/dealbrain_api/services/`)
- Utilities and helpers

**Integration Tests**:
- API endpoint tests with real database
- Database model tests
- Celery task tests

**E2E Tests** (future):
- User workflows (create listing, view deals)
- Import Excel file flow
- Valuation breakdown modal

**Test Configuration**:

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from dealbrain_api.db import Base

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()
```

### Deployment Pipeline (Proposed)

**GitHub Actions Workflow**:

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install Poetry
        run: pip install poetry

      - name: Install dependencies
        run: poetry install

      - name: Run linters
        run: |
          poetry run ruff check .
          poetry run black --check .

      - name: Run tests
        run: poetry run pytest --cov --cov-report=xml
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/postgres

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push API
        uses: docker/build-push-action@v4
        with:
          context: .
          file: infra/api/Dockerfile
          push: true
          tags: dealbrain/api:${{ github.sha }},dealbrain/api:latest
          cache-from: type=registry,ref=dealbrain/api:latest
          cache-to: type=inline

      - name: Build and push Web
        uses: docker/build-push-action@v4
        with:
          context: .
          file: infra/web/Dockerfile
          push: true
          tags: dealbrain/web:${{ github.sha }},dealbrain/web:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to production
        run: |
          # SSH to production server
          # Pull latest images
          # Run database migrations
          # Restart services with zero-downtime
          echo "Deploy to production"
```

**Deployment Steps**:

1. **Test** - Run linters, unit tests, integration tests
2. **Build** - Build Docker images and push to registry
3. **Deploy** - Update production environment

**Zero-Downtime Deployment**:

```bash
# Rolling update with Docker Compose
docker-compose pull api web
docker-compose up -d --no-deps --scale api=2 api
sleep 10
docker-compose up -d --no-deps --scale api=1 api

# Or with Kubernetes
kubectl set image deployment/dealbrain-api api=dealbrain/api:v1.1.0
kubectl rollout status deployment/dealbrain-api
```

**Rollback Strategy**:

```bash
# Docker Compose
docker-compose up -d api:v1.0.0

# Kubernetes
kubectl rollout undo deployment/dealbrain-api

# Database migration rollback
poetry run alembic downgrade -1
```

---

## Summary

### Key Strengths

1. **Comprehensive Observability**: OpenTelemetry + Prometheus + Grafana stack ready
2. **Clean Architecture**: Service isolation with Docker Compose
3. **Developer Experience**: Hot reload, pre-commit hooks, Makefile shortcuts
4. **Async-First**: SQLAlchemy async, FastAPI async endpoints
5. **Type Safety**: Pydantic models, TypeScript frontend

### Areas for Improvement

1. **Production Readiness**:
   - Optimize Dockerfiles (multi-stage builds)
   - Add health check endpoints
   - Implement secrets management
   - Configure CORS properly

2. **Scalability**:
   - Add load balancing
   - Implement caching strategies
   - Database read replicas
   - Rate limiting

3. **Observability**:
   - Add distributed tracing (Jaeger)
   - Implement structured logging
   - Create Grafana dashboards
   - Set up alerting rules

4. **CI/CD**:
   - Automated testing pipeline
   - Container image scanning
   - Automated deployments
   - E2E test suite

5. **Documentation**:
   - Runbooks for common operations
   - Disaster recovery procedures
   - Architecture decision records

### Quick Reference

**Essential Commands**:

```bash
# Development
make setup              # Install dependencies
make up                 # Start full stack
make down               # Stop services
make api                # Run API locally
make web                # Run web locally
make migrate            # Apply migrations
make test               # Run tests

# Operations
docker-compose logs -f api          # View API logs
docker-compose restart worker       # Restart worker
docker exec -it deal-brain-db-1 psql -U dealbrain  # Access database
poetry run alembic current          # Check migration status

# Monitoring
open http://localhost:9090          # Prometheus
open http://localhost:3021          # Grafana
curl http://localhost:8020/metrics  # API metrics
```

**Port Reference**:

- 5442: PostgreSQL
- 6399: Redis
- 8020: FastAPI API
- 3020: Next.js Web
- 9090: Prometheus
- 3021: Grafana

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Related Documentation**:
- [03-backend-architecture.md](./03-backend-architecture.md) - Backend services detail
- [04-frontend-architecture.md](./04-frontend-architecture.md) - Frontend implementation
- [05-data-layer.md](./05-data-layer.md) - Database models and migrations
