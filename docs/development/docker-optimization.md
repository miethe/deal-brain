---
title: "Docker Build Optimization Guide"
description: "Multi-stage Docker builds for faster development iteration with minimal image bloat"
audience: [developers, ai-agents, devops]
tags: [docker, optimization, playwright, build-performance, development]
created: 2025-11-20
updated: 2025-11-20
category: "developer-documentation"
status: published
related:
  - /docs/project_plans/playwright-infrastructure/playwright-infrastructure-v1.md
  - /docs/architecture/playwright-optimization-analysis.md
---

# Docker Build Optimization

## Overview

This document describes the multi-stage Docker build strategy that eliminates Playwright dependencies from development workflows while maintaining full functionality in production.

## Problem Statement

Playwright adds significant overhead to Docker images:
- **Image size**: 1.71GB per image (API + Worker = 3.4GB total)
- **Build time**: 5-6 minutes per build
- **System dependencies**: 33 packages for Chromium browser
- **Use case**: Only needed for social media card generation (optional feature)

This overhead impacts:
- Development iteration speed (builds block testing)
- CI/CD pipeline costs (40+ minutes overhead per day)
- Local disk usage (multiple GB for dev environments)

## Solution: Multi-Stage Builds

We use multi-stage Docker builds with two targets:

### Development Target
- **Purpose**: Fast local development
- **Size**: <600MB (65% reduction)
- **Build time**: 2-3 minutes (50% reduction)
- **Dependencies**: Minimal (build-essential, libpq-dev, ca-certificates)
- **Playwright**: NOT included
- **Use case**: Local development, integration tests, CI builds

### Production Target
- **Purpose**: Full-featured production deployment
- **Size**: ~1.71GB (unchanged from current)
- **Build time**: 5-6 minutes (unchanged)
- **Dependencies**: All current dependencies including Playwright
- **Playwright**: Included with Chromium browser
- **Use case**: Production deployments, card generation tasks

## Build Commands

### Building Images Manually

**Development build (fast):**
```bash
docker build --target=development -t dealbrain-api:dev -f infra/api/Dockerfile .
docker build --target=development -t dealbrain-worker:dev -f infra/worker/Dockerfile .
```

**Production build (full features):**
```bash
docker build --target=production -t dealbrain-api:prod -f infra/api/Dockerfile .
docker build --target=production -t dealbrain-worker:prod -f infra/worker/Dockerfile .
```

**Note**: If `--target` is omitted, the build defaults to the last stage (production).

### Using Docker Compose

**Development (default):**
```bash
# Uses development target automatically
docker compose up
```

**Production:**
```bash
# Uses production profile with production target
docker compose --profile production up
```

## Docker Compose Profiles

The `docker-compose.yml` defines two sets of services:

### Default Services (Development)
- `api` - Uses `target: development`
- `worker` - Uses `target: development`
- All other services (db, redis, web, etc.)

### Production Profile Services
- `api-prod` - Uses `target: production` (profiles: ["production"])
- `worker-prod` - Uses `target: production` (profiles: ["production"])

**Key behavior:**
- Running `docker compose up` starts development services
- Running `docker compose --profile production up` starts production services
- Profiles ensure dev and prod services don't conflict (both expose same ports)

## Makefile Integration

Existing Makefile commands work without changes:

```bash
make up          # Starts development stack (uses development target)
make down        # Stops all services
make api         # Runs API locally (not Docker)
make web         # Runs web locally (not Docker)
```

## CI/CD Integration

### Development Builds (Pull Requests, Tests)

Update CI workflows to use development target:

```yaml
# .github/workflows/test.yml
- name: Build development image
  run: |
    docker build --target=development -t dealbrain-api:dev -f infra/api/Dockerfile .
```

**Benefits:**
- Faster CI builds (2-3 min instead of 5-6 min)
- Smaller images cached by CI
- Tests run against same environment as local development

### Production Builds (Deployments)

Use production target for deployment builds:

```yaml
# .github/workflows/deploy.yml
- name: Build production image
  run: |
    docker build --target=production -t dealbrain-api:prod -f infra/api/Dockerfile .
```

**Note**: Can also omit `--target` since production is the default (last stage).

## Dockerfile Structure

Both API and Worker Dockerfiles follow the same pattern:

```dockerfile
# Stage 1: Development (minimal)
FROM python:3.11-slim AS development

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy application code and install Python dependencies
COPY pyproject.toml README.md ./
COPY apps ./apps
COPY packages ./packages
COPY data ./data

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8000
CMD ["dealbrain-api"]

# ===================================

# Stage 2: Production (full features)
FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install ALL dependencies including Playwright system packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        # Playwright system dependencies for Chromium
        libnss3 libxss1 libasound2 libatk-bridge2.0-0 \
        libgtk-3-0 libdrm2 libgbm1 libxkbcommon0 \
        # ... (33 total packages)
    && rm -rf /var/lib/apt/lists/*

# Copy application code and install Python dependencies
COPY pyproject.toml README.md ./
COPY apps ./apps
COPY packages ./packages
COPY data ./data

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Install Playwright browsers (Chromium only)
RUN playwright install chromium

EXPOSE 8000
CMD ["dealbrain-api"]
```

## Key Design Decisions

### Why Two Separate Stages?

**Alternative considered**: Build args with conditional installation
```dockerfile
ARG INSTALL_PLAYWRIGHT=false
RUN if [ "$INSTALL_PLAYWRIGHT" = "true" ]; then ...
```

**Why multi-stage is better:**
- Clearer separation of concerns (dev vs prod)
- Better layer caching (stages cached independently)
- Easier to understand and maintain
- No runtime conditionals needed

### Why Production is Default?

Production is the last stage in the Dockerfile, making it the default when `--target` is omitted. This ensures:
- Production builds "just work" without special flags
- Developers must explicitly choose development (forces awareness)
- Backward compatibility with existing build scripts

### Why Separate Production Services in Docker Compose?

**Alternative considered**: Single service with profile-based target
```yaml
api:
  build:
    target: ${BUILD_TARGET:-development}
```

**Why separate services is better:**
- No environment variable needed
- Explicit profile selection (`docker compose --profile production up`)
- Services can have different configurations (resources, replicas, etc.)
- No accidental production deployment with dev image

## Testing & Validation

### Image Size Verification

```bash
# Build both targets
docker build --target=development -t dealbrain-api:dev -f infra/api/Dockerfile .
docker build --target=production -t dealbrain-api:prod -f infra/api/Dockerfile .

# Check sizes
docker images | grep dealbrain-api
# Expected:
# dealbrain-api:dev   <600MB
# dealbrain-api:prod  ~1.71GB
```

### Build Time Measurement

```bash
# Development build (expect 2-3 minutes)
time docker build --no-cache --target=development -t dealbrain-api:dev -f infra/api/Dockerfile .

# Production build (expect 5-6 minutes)
time docker build --no-cache --target=production -t dealbrain-api:prod -f infra/api/Dockerfile .
```

### Playwright Presence Check

```bash
# Development: Playwright should NOT exist
docker run --rm dealbrain-api:dev which playwright
# Expected: command not found

# Production: Playwright should exist
docker run --rm dealbrain-api:prod which playwright
# Expected: /usr/local/bin/playwright (or similar path)
```

### Functional Testing

**Development stack:**
```bash
docker compose up
# Verify:
# - API starts and responds to health checks
# - Worker connects to Redis
# - Database migrations run successfully
# - Web app connects to API
```

**Production stack:**
```bash
docker compose --profile production up
# Verify:
# - Same as development
# - Card generation tasks work (Playwright available)
```

## Troubleshooting

### Issue: Build fails with "target not found"

**Cause**: Docker version too old to support multi-stage builds
**Solution**: Upgrade to Docker 17.05 or later

### Issue: Production profile doesn't start

**Cause**: Conflicting port bindings (both dev and prod services try to use 8020)
**Solution**: Stop dev services first: `docker compose down`

### Issue: Playwright not found in production

**Cause**: Built wrong target or target not specified
**Solution**: Verify build command includes `--target=production` or omits `--target` entirely

### Issue: Development build too large (>600MB)

**Cause**: Playwright dependencies leaked into development stage
**Solution**: Verify Dockerfile separation - development stage should NOT have Playwright system packages

## Rollback Procedure

If multi-stage builds cause issues, rollback to single-stage:

```bash
# Restore backup
cp infra/api/Dockerfile.backup infra/api/Dockerfile
cp infra/worker/Dockerfile.backup infra/worker/Dockerfile

# Restore docker-compose.yml (remove target: development and profiles)
git checkout docker-compose.yml

# Rebuild
docker compose build
docker compose up
```

## Success Metrics

| Metric | Baseline | Target | Actual |
|--------|----------|--------|--------|
| Dev image size | 1.71GB | <600MB | _Measure after build_ |
| Dev build time | 5-6 min | 2-3 min | _Measure after build_ |
| Prod image size | 1.71GB | 1.71GB (unchanged) | _Measure after build_ |
| Build disk savings | 3.4GB | 1.2GB | _Measure after build_ |

## Future Optimizations

### Phase 2: Base Image Reuse

**Opportunity**: Both stages currently duplicate the same Python dependency installation.

**Optimization**:
```dockerfile
FROM python:3.11-slim AS base
# Install Python deps (shared)

FROM base AS development
# Minimal system deps

FROM base AS production
# Full system deps + Playwright
```

**Benefits**:
- Reduce duplicate layer caching
- Potentially faster builds when Python deps change

### Phase 3: Layer Caching Strategy

**Opportunity**: Copy operations happen before dependency installation, causing cache invalidation on code changes.

**Optimization**: Separate dependency installation from code copy
```dockerfile
COPY pyproject.toml README.md ./
RUN pip install .
# ^ Cached unless dependencies change

COPY apps ./apps
COPY packages ./packages
# ^ Invalidates cache but no reinstall needed
```

## Related Documentation

- **PRD**: `/docs/project_plans/playwright-infrastructure/playwright-infrastructure-v1.md`
- **Architecture Analysis**: `/docs/architecture/playwright-optimization-analysis.md`
- **Dockerfiles**: `infra/api/Dockerfile`, `infra/worker/Dockerfile`
- **Compose Config**: `docker-compose.yml`

## Change History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-20 | 1.0 | Initial multi-stage implementation |
