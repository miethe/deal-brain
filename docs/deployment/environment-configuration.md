---
title: "Environment Configuration Guide"
description: "Comprehensive guide for managing environment variables and secrets across development, staging, and production environments"
audience: [developers, devops, ai-agents]
tags: [environment, configuration, secrets, github-secrets, deployment]
created: 2025-11-20
updated: 2025-11-20
category: "configuration-deployment"
status: published
related:
  - /docs/deployment/DEPLOYMENT_STRATEGY.md
  - /docs/deployment/pre-deployment-checklist.md
---

# Environment Configuration Guide

## Overview

Deal Brain requires careful management of environment variables across three deployment environments: **Development**, **Staging**, and **Production**. This guide covers best practices for configuration management, secrets handling, and environment-specific setup.

---

## Configuration Hierarchy

```
┌──────────────────────────────────────────────────────────────┐
│  Configuration Sources (priority order)                      │
├──────────────────────────────────────────────────────────────┤
│ 1. GitHub Secrets (highest - deployment-time)               │
│ 2. Environment Variables (GitHub Actions context)           │
│ 3. .env files (local development only)                      │
│ 4. Application defaults (lowest - fallback)                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Development Environment

### Local Setup

**File: `.env` (NOT committed to repo)**
```bash
# Core
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true
SECRET_KEY=dev-only-insecure-key

# Database
DATABASE_URL=postgresql+asyncpg://dealbrain:dealbrain@db:5432/dealbrain
SYNC_DATABASE_URL=postgresql://dealbrain:dealbrain@db:5432/dealbrain

# Cache
REDIS_URL=redis://redis:6379/0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8020
WEB_URL=http://localhost:3000
API_HOST=0.0.0.0
API_PORT=8000

# File Paths
IMPORT_ROOT=./data/imports
EXPORT_ROOT=./data/exports

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
PROMETHEUS_ENABLED=true

# Features
INGESTION_INGESTION_ENABLED=true
INGESTION_EBAY_ENABLED=true
INGESTION_JSONLD_ENABLED=true
INGESTION_AMAZON_ENABLED=false

# Playwright
PLAYWRIGHT__ENABLED=true
PLAYWRIGHT__MAX_CONCURRENT_BROWSERS=2
PLAYWRIGHT__BROWSER_TIMEOUT_MS=30000
PLAYWRIGHT__HEADLESS=true

# S3 (optional - not enabled in dev by default)
S3__ENABLED=false
AWS_S3_BUCKET_NAME=dealbrain-card-images
AWS_REGION=us-east-1
```

**File: `.env.example` (committed to repo)**
```bash
# This file serves as a template for environment variables
# Copy to .env and fill in your values

ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=false
SECRET_KEY=changeme

DATABASE_URL=postgresql+asyncpg://dealbrain:dealbrain@db:5432/dealbrain
SYNC_DATABASE_URL=postgresql://dealbrain:dealbrain@db:5432/dealbrain
REDIS_URL=redis://redis:6379/0

NEXT_PUBLIC_API_URL=http://localhost:8020
WEB_URL=http://localhost:3000

# ... rest of variables
```

### Docker Compose Usage

The `docker-compose.yml` loads environment variables from `.env`:

```yaml
services:
  api:
    env_file: .env.example  # Falls back to example
    environment:
      DATABASE_URL: postgresql+asyncpg://dealbrain:dealbrain@db:5432/dealbrain
      SYNC_DATABASE_URL: postgresql://dealbrain:dealbrain@db:5432/dealbrain
```

---

## Staging Environment

### Configuration in GitHub

**GitHub Secrets Setup**

Navigate to: Repository Settings → Secrets and variables → Actions

#### Required Secrets

```
Repository Secrets (available to all workflows):
├── GHCR_TOKEN
│   Value: GitHub Container Registry token
│   Access: public (safe for staging/prod)
│
├── RENDER_DEPLOY_HOOK_STAGING
│   Value: Render webhook URL for staging deployment
│   Format: https://api.render.com/deploy/srv-xxx?key=yyy
│   Access: Sensitive - restrict to main branch
│
├── SLACK_WEBHOOK_URL
│   Value: Slack incoming webhook for notifications
│   Access: Sensitive
│
└── (Other platform-specific secrets as needed)
```

#### Environment-Specific Secrets

Set these in Render dashboard or deployment platform:

**Staging Environment Variables (in Render/deployment platform):**
```
ENVIRONMENT=staging
LOG_LEVEL=INFO
DEBUG=false
SECRET_KEY=<secure-random-32-char-string>

DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/dealbrain_staging
SYNC_DATABASE_URL=postgresql://<user>:<password>@<host>:5432/dealbrain_staging
REDIS_URL=redis://<host>:<port>/0

NEXT_PUBLIC_API_URL=https://staging-api.dealbrain.example.com
WEB_URL=https://staging.dealbrain.example.com
API_HOST=0.0.0.0
API_PORT=8000

OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
PROMETHEUS_ENABLED=true

INGESTION_EBAY_API_KEY=<ebay-staging-key>
INGESTION_EBAY_ENABLED=true
INGESTION_EBAY_TIMEOUT_S=6
INGESTION_EBAY_RETRIES=2

INGESTION_JSONLD_ENABLED=true
INGESTION_AMAZON_ENABLED=false

PLAYWRIGHT__ENABLED=true
PLAYWRIGHT__MAX_CONCURRENT_BROWSERS=2
PLAYWRIGHT__HEADLESS=true

S3__ENABLED=true
S3__ENDPOINT_URL=https://s3-staging.example.com
AWS_S3_BUCKET_NAME=dealbrain-staging-images
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<staging-access-key>
AWS_SECRET_ACCESS_KEY=<staging-secret-key>
S3__CACHE_TTL_SECONDS=2592000
```

### Staging Deployment Flow

```
1. Push to main branch
   ↓
2. GitHub Actions validates & builds images
   ↓
3. Images pushed to GHCR with 'staging-latest' tag
   ↓
4. Render webhook triggered automatically
   ↓
5. Render pulls latest image
   ↓
6. Migrations run (alembic upgrade head)
   ↓
7. Services restart with new image
   ↓
8. Health checks verify deployment
   ↓
9. Slack notification sent
   ↓
10. Ready for manual testing & approval
```

---

## Production Environment

### Pre-Deployment Setup

**1. Provision Infrastructure**
```bash
# Render/Railway: Create production service
# AWS ECS: Create production cluster & task definitions
# Kubernetes: Create production namespace & ingress
```

**2. Set Up Databases**
```bash
# PostgreSQL:
- Create production database
- Configure backups (daily)
- Enable point-in-time recovery
- Set up read replicas if needed

# Redis:
- Create production instance
- Configure persistence
- Enable replication
```

**3. Configure Secrets Storage**
```bash
# GitHub Secrets:
RENDER_DEPLOY_HOOK_PRODUCTION
  - Separate from staging
  - Restrict to main branch only

# Deployment Platform:
All production environment variables
- Never use 'dev' or 'test' credentials
- Use production API keys
- Use production database URLs
```

### Production Environment Variables

**Set in Render/deployment platform (NEVER in GitHub Actions):**

```
ENVIRONMENT=production
LOG_LEVEL=WARNING
DEBUG=false
SECRET_KEY=<cryptographically-secure-random-64-char-string>

# Database - Use connection pooling
DATABASE_URL=postgresql+asyncpg://<prod-user>:<prod-pass>@<prod-host>:5432/dealbrain
SYNC_DATABASE_URL=postgresql://<prod-user>:<prod-pass>@<prod-host>:5432/dealbrain

# Redis with authentication
REDIS_URL=redis://<auth>:<password>@<prod-redis-host>:6379/0

# URLs
NEXT_PUBLIC_API_URL=https://api.dealbrain.com
WEB_URL=https://dealbrain.com
API_HOST=0.0.0.0
API_PORT=8000

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel.example.com:4317
PROMETHEUS_ENABLED=true
SENTRY_DSN=<sentry-production-dsn>

# eBay integration (production keys)
INGESTION_EBAY_API_KEY=<production-ebay-key>
INGESTION_EBAY_ENABLED=true
INGESTION_EBAY_TIMEOUT_S=6
INGESTION_EBAY_RETRIES=2

# JSON-LD adapter
INGESTION_JSONLD_ENABLED=true
INGESTION_JSONLD_TIMEOUT_S=8

# Amazon (when enabled)
INGESTION_AMAZON_ENABLED=false

# Price change detection
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=2.0
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=1.0
INGESTION_RAW_PAYLOAD_TTL_DAYS=30

# Playwright for card generation
PLAYWRIGHT__ENABLED=true
PLAYWRIGHT__MAX_CONCURRENT_BROWSERS=4
PLAYWRIGHT__BROWSER_TIMEOUT_MS=30000
PLAYWRIGHT__HEADLESS=true

# S3 for card image caching
S3__ENABLED=true
S3__ENDPOINT_URL=https://s3.amazonaws.com
AWS_S3_BUCKET_NAME=dealbrain-production-images
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<prod-iam-access-key>
AWS_SECRET_ACCESS_KEY=<prod-iam-secret-key>
S3__CACHE_TTL_SECONDS=2592000
```

### Production Deployment Flow

```
1. Tag release (git tag v1.2.3)
   ↓
2. Push tag to main branch
   ↓
3. GitHub Actions runs full CI/CD pipeline
   ↓
4. Builds production images with version tag
   ↓
5. Scans images for vulnerabilities
   ↓
6. Runs E2E tests
   ↓
7. Sends staging deployment
   ↓
8. MANUAL APPROVAL REQUIRED
   ↓
9. Verified staging images promoted to production
   ↓
10. Production deployment initiated
    ↓
11. Database migrations run
    ↓
12. Blue/green deployment setup
    ↓
13. Health checks verify green instance
    ↓
14. Gradual traffic shift from blue to green
    ↓
15. Monitoring for 30+ minutes
    ↓
16. Keep monitoring or rollback if issues
    ↓
17. Slack notification with deployment status
```

---

## Secrets Management Best Practices

### Generation

**Secret Key (FastAPI)**
```bash
# Generate secure random key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Output: 8-character minimum, 32+ recommended
```

**Database Password**
```bash
# Generate using password manager
# Requirements:
# - Minimum 32 characters
# - Mix of upper, lower, numbers, special chars
# - Avoid special chars that need escaping in URLs
```

### Storage

**GitHub Secrets (for CI/CD)**
```
✓ GHCR_TOKEN - registry push
✓ RENDER_DEPLOY_HOOK_STAGING - deployment
✓ RENDER_DEPLOY_HOOK_PRODUCTION - deployment
✓ SLACK_WEBHOOK_URL - notifications

✗ Database passwords (use deployment platform instead)
✗ API keys (use deployment platform instead)
✗ Secret keys (use deployment platform instead)
```

**Deployment Platform Secrets**
```
✓ DATABASE_URL - PostgreSQL connection
✓ REDIS_URL - Redis connection
✓ SECRET_KEY - FastAPI secret
✓ API_KEYS - Third-party integrations
✓ AWS credentials - S3 access
✓ SENTRY_DSN - Error tracking

✗ Never expose in GitHub Actions (use deployment platform)
✗ Never log or display in CI/CD output
```

### Rotation Schedule

| Secret Type | Rotation Frequency | Trigger |
|------------|-------------------|---------|
| API Keys | Every 3-6 months | Planned maintenance |
| Database Password | Every 6 months | Planned maintenance |
| Secret Key | Every 6 months | Planned maintenance |
| Temporary Keys | 7-30 days | Per policy |
| Compromised Keys | ASAP | Security incident |

### Rotation Process

```
1. Generate new secret
2. Add new secret to deployment platform
3. Restart services (they pick up new env var)
4. Verify new secret working
5. Remove old secret from storage
6. Document rotation in security log
7. Alert team of change
```

---

## Render Deployment Configuration

### Setting Environment Variables in Render

**Via Render Dashboard:**
1. Navigate to Service Settings
2. Environment
3. Add each variable:
   - Key: Variable name
   - Value: Variable value
   - Secret: Toggle for sensitive values

**Via render.yaml (Infrastructure as Code)**
```yaml
services:
  - type: web
    name: dealbrain-api
    env: docker
    repo: https://github.com/username/deal-brain
    branch: main
    buildCommand: |
      pip install poetry && poetry install
      poetry run alembic upgrade head
    startCommand: poetry run dealbrain-api
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: SECRET_KEY
        sync: false  # Don't sync from GitHub
      - key: DATABASE_URL
        fromDatabase:
          name: dealbrain-db
          property: connectionString
      - key: NEXT_PUBLIC_API_URL
        value: https://api.dealbrain.com

  - type: web
    name: dealbrain-web
    env: docker
    repo: https://github.com/username/deal-brain
    branch: main
    startCommand: pnpm --filter web start
    envVars:
      - key: NEXT_PUBLIC_API_URL
        value: https://api.dealbrain.com

  - type: background
    name: dealbrain-worker
    env: docker
    repo: https://github.com/username/deal-brain
    branch: main
    buildCommand: |
      pip install poetry && poetry install
      poetry run playwright install chromium
    startCommand: celery -A dealbrain_api.worker worker -l info

databases:
  - name: dealbrain-db
    ipAllowList: []  # Allow all IPs from services
  - name: dealbrain-redis
    plan: standard
```

---

## Railway Deployment Configuration

### Setting Environment Variables in Railway

**Via Railway Dashboard:**
1. Select Service
2. Variables
3. Add raw or individual variables

**Via railway.json (Infrastructure as Code)**
```json
{
  "services": {
    "dealbrain-api": {
      "source": {
        "repo": "https://github.com/username/deal-brain"
      },
      "startCommand": "poetry run dealbrain-api",
      "environmentVariables": {
        "ENVIRONMENT": "production",
        "LOG_LEVEL": "WARNING"
      }
    },
    "dealbrain-web": {
      "startCommand": "pnpm --filter web start",
      "environmentVariables": {
        "NEXT_PUBLIC_API_URL": "${{ Railway.API.URL }}"
      }
    },
    "postgres": {
      "image": "postgres:15-alpine"
    },
    "redis": {
      "image": "redis:7-alpine"
    }
  }
}
```

---

## AWS ECS Deployment Configuration

### Task Definition with Secrets

```json
{
  "family": "dealbrain-api",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "dealbrain-api",
      "image": "ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/deal-brain-api:latest",
      "essential": true,
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "LOG_LEVEL",
          "value": "WARNING"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:dealbrain-db-url"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:dealbrain-secret-key"
        },
        {
          "name": "REDIS_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:dealbrain-redis-url"
        }
      ]
    }
  ]
}
```

---

## Local Development Workflow

### First-Time Setup

```bash
# 1. Clone repository
git clone https://github.com/username/deal-brain.git
cd deal-brain

# 2. Copy example env file
cp .env.example .env

# 3. Edit .env with your local values
# (most defaults work for Docker Compose setup)
vim .env

# 4. Verify no actual secrets committed
git status  # Should NOT show .env

# 5. Run setup
make setup
make up
make migrate
make seed
```

### Daily Development

```bash
# Start services
make up

# Tail logs
docker-compose logs -f api web worker

# Stop services
make down

# Never commit .env
git status  # Always shows .env as untracked
```

### Before Committing

```bash
# Verify no secrets in staged files
git diff --cached | grep -i password  # Should be empty
git diff --cached | grep -i secret    # Should be empty
git diff --cached | grep -i token     # Should be empty

# Verify .env not staged
git status | grep .env  # Should show "untracked"

# Use .env.example for defaults
cp .env.example .env.example.backup
# ... update .env.example with any new variables
git add .env.example
```

---

## Troubleshooting Configuration Issues

### "Connection refused" errors

**Check:**
```bash
# Verify environment variable is set
echo $DATABASE_URL
echo $REDIS_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
redis-cli -u $REDIS_URL ping
```

### "Invalid SECRET_KEY" errors

**Check:**
```bash
# Verify SECRET_KEY is set
echo $SECRET_KEY

# Regenerate if needed
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### "S3 connection failed"

**Check:**
```bash
# Verify AWS credentials
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# Test S3 access
aws s3 ls s3://$AWS_S3_BUCKET_NAME
```

### Environment variables not picked up after update

**Solution:**
```bash
# Render/Railway: Services auto-restart on env var change
# Manual restart if not detected:
# 1. Go to deployment platform dashboard
# 2. Manual restart service
# 3. Verify new values applied
```

---

## Checklist: Environment Configuration

- [ ] `.env` never committed to repository
- [ ] `.env.example` has all required variables with safe defaults
- [ ] GitHub Secrets configured for CI/CD tokens only
- [ ] Deployment platform has all service-specific secrets
- [ ] SECRET_KEY is cryptographically random (32+ chars)
- [ ] DATABASE_URL uses async driver (asyncpg) for API
- [ ] REDIS_URL configured with proper port and database
- [ ] NEXT_PUBLIC_API_URL matches deployment domain
- [ ] API health endpoint responds with proper format
- [ ] Secrets rotated every 6 months
- [ ] No secrets in commit history (checked with TruffleHog)
- [ ] Environment variables documented per environment
- [ ] Staging and production use different credentials

---

## Related Documentation

- [Deployment Strategy](/docs/deployment/DEPLOYMENT_STRATEGY.md)
- [Pre-Deployment Checklist](/docs/deployment/pre-deployment-checklist.md)
