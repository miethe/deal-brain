---
title: "Deal Brain Deployment Strategy"
description: "Comprehensive CI/CD pipeline design, deployment automation, and zero-downtime deployment strategy for the Deal Brain monorepo"
audience: [developers, devops, ai-agents]
tags: [deployment, ci-cd, github-actions, docker, kubernetes, automation, zero-downtime]
created: 2025-11-20
updated: 2025-11-20
category: "configuration-deployment"
status: published
related:
  - /docs/deployment/github-actions-workflows.md
  - /docs/deployment/pre-deployment-checklist.md
  - /docs/deployment/environment-configuration.md
---

# Deal Brain Deployment Strategy

## Executive Summary

This document outlines a production-grade CI/CD pipeline and deployment automation strategy for Deal Brain, a Python/TypeScript monorepo with FastAPI backend, Next.js frontend, Celery workers, and PostgreSQL/Redis infrastructure.

**Key Principles:**
- Automated everything: No manual deployment steps
- Build once, deploy anywhere: Container-based immutability
- Zero-downtime deployments: Health checks and graceful shutdowns
- Fail fast: Early detection with comprehensive testing
- Security-first: Supply chain security and secrets management
- Observability: Deployment metrics and application health tracking

**Deployment Target Options:**
1. **Render** - Recommended for initial deployment (Platform-as-a-Service)
2. **Railway** - Alternative PaaS option
3. **AWS ECS** - Container orchestration at scale
4. **Kubernetes** - Enterprise-grade orchestration

---

## Current State Analysis

### Existing CI/CD
- **E2E Test Workflow**: GitHub Actions workflow for critical and mobile flows
- **Test Coverage**: Playwright tests, API health checks, database migrations
- **Stages**: Code → Install Dependencies → Build → Test → Upload Artifacts

### Existing Infrastructure
- **Docker Compose Stack**: 7+ services (PostgreSQL, Redis, API, Worker, Web, OTEL, Prometheus, Grafana)
- **Dockerfiles**: Multi-stage builds for development/production (API, Worker, Web)
- **Database**: Alembic migrations with async SQLAlchemy
- **Observability**: OpenTelemetry, Prometheus metrics, Grafana dashboards

### Gaps to Address
1. **No automated build and push of Docker images**
2. **No automated deployment to staging/production**
3. **No database migration coordination in deployment**
4. **No secret management strategy**
5. **No rollback automation**
6. **Limited pre-deployment security checks**
7. **No deployment health monitoring**
8. **No multi-environment environment variable management**

---

## Proposed CI/CD Pipeline Architecture

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Push (PR or Merge to main)                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
          ┌───────────▼───────────┐
          │  Trigger & Validate   │
          │  - Lint Python/JS     │
          │  - Security Scan      │
          └─────────┬─────────────┘
                    │
          ┌─────────▼──────────┐
          │  Unit & Integration │
          │  - Pytest (Python) │
          │  - Jest (TypeScript)│
          └─────────┬──────────┘
                    │
          ┌─────────▼──────────┐
          │  Build Containers  │
          │  - API image       │
          │  - Web image       │
          │  - Worker image    │
          └─────────┬──────────┘
                    │
          ┌─────────▼──────────┐
          │  E2E Tests         │
          │  - Critical flows  │
          │  - Mobile flows    │
          └─────────┬──────────┘
                    │
          ┌─────────▼──────────┐
    ┌─────│  Push to Registry  │──────┐
    │     │  - Docker Hub/GHCR │      │
    │     └────────────────────┘      │
    │                                 │
    │  ┌─────────────────────────┐   │
    │  │  Deploy to Staging      │   │
    │  │  - Run migrations       │   │
    │  │  - Deploy new images    │   │
    │  │  - Health checks        │   │
    │  │  - Smoke tests          │   │
    │  └─────────┬───────────────┘   │
    │            │                   │
    │  ┌─────────▼───────────────┐   │
    │  │  Await Manual Approval  │   │
    │  │  - Review staging       │   │
    │  │  - Approve production   │   │
    │  └─────────┬───────────────┘   │
    │            │                   │
    └───────────→├──────────────────-┘
                │
    ┌───────────▼──────────────┐
    │  Deploy to Production    │
    │  - Run migrations        │
    │  - Blue/green deploy     │
    │  - Health checks         │
    │  - Monitor metrics       │
    │  - Rollback on failure   │
    └──────────────────────────┘
```

### Pipeline Configuration Layers

#### 1. **Build Layer**
- **Lint & Format Check**: Ruff, Black, isort, ESLint
- **Security Scanning**: Bandit, safety, Snyk (dependencies)
- **Unit Tests**: pytest (Python), jest (TypeScript)
- **Integration Tests**: Database migrations, API endpoints
- **E2E Tests**: Playwright critical and mobile flows

#### 2. **Artifact Layer**
- **Docker Image Build**: Multi-stage for size optimization
- **Image Tagging**: Semantic versioning (v1.2.3) + git SHA
- **Image Scanning**: Trivy for vulnerabilities
- **Registry Push**: Docker Hub, GitHub Container Registry (GHCR), or ECR

#### 3. **Deployment Layer - Staging**
- **Prerequisites**:
  - Secrets from GitHub secrets manager
  - Environment configuration validation
  - Infrastructure health checks
- **Deployment Steps**:
  - Database migrations (Alembic)
  - Pull latest images
  - Health checks (API /health endpoint)
  - Smoke tests
  - Metrics baseline capture
- **Failure Handling**:
  - Auto-rollback on migration failure
  - Notify on deployment failure
  - Store artifacts for investigation

#### 4. **Approval Gate**
- **Manual Review**:
  - Check staging metrics
  - Review new features
  - Verify deployment logs
- **Automatic Approval** (optional):
  - Production branch deployment
  - Hot-fix deployments

#### 5. **Deployment Layer - Production**
- **Blue/Green Deployment**:
  - Deploy new version (green) alongside running version (blue)
  - Health checks on green
  - Gradual traffic shift
  - Quick rollback if issues
- **Zero-Downtime Strategy**:
  - Readiness probes ensure traffic only to healthy instances
  - Graceful shutdown with request draining
  - Connection pooling with proper cleanup
  - Database migrations backward compatible
- **Monitoring**:
  - Real-time metrics (request rate, error rate, latency)
  - Application logs aggregation
  - Alert triggers for critical metrics
  - Automatic rollback on SLA breach

---

## Detailed Implementation Strategy

### 1. Docker Build & Registry Strategy

#### Image Architecture

**API Service:**
```dockerfile
# Multi-stage: reduces final image size by 60%+
# Development: includes Playwright for card generation
# Production: includes only essential runtime dependencies
```

**Web Service:**
```dockerfile
# Build stage: Node.js with pnpm for npm package management
# Runtime stage: Alpine Node for minimal footprint
```

**Worker Service:**
```dockerfile
# Celery worker with Playwright for async image tasks
# Matches API service dependencies
```

#### Image Tagging Strategy

```
# Semantic versioning
ghcr.io/username/deal-brain-api:v1.2.3
ghcr.io/username/deal-brain-web:v1.2.3

# Git SHA for traceability
ghcr.io/username/deal-brain-api:v1.2.3-abc123def

# Latest tag for development
ghcr.io/username/deal-brain-api:latest

# Environment tags for staging
ghcr.io/username/deal-brain-api:staging-latest
ghcr.io/username/deal-brain-api:staging-v1.2.3
```

#### Registry Selection

| Registry | Pros | Cons | Best For |
|----------|------|------|----------|
| **GitHub Container Registry (GHCR)** | Free, integrated with GitHub, private by default | Less documentation than Docker Hub | Production, private repositories |
| **Docker Hub** | Largest community, most docs, free public repos | Rate limits, less GitHub integration | Public images, open source |
| **AWS ECR** | Integration with ECS/Fargate, private by default | AWS-only, costs involved | AWS deployments |

**Recommendation**: Use **GHCR** for this project (integrated with GitHub, free private storage)

### 2. Environment Configuration Strategy

#### Environment-Specific Variables

**Development** (`.env.example`, committed to repo)
```
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true
DATABASE_URL=postgresql+asyncpg://dealbrain:dealbrain@db:5432/dealbrain
REDIS_URL=redis://redis:6379/0
SECRET_KEY=dev-only-key-change-in-production
NEXT_PUBLIC_API_URL=http://localhost:8020
```

**Staging** (GitHub Secrets + deployment-time configuration)
```
ENVIRONMENT=staging
LOG_LEVEL=INFO
DATABASE_URL=<postgres-staging-url>
REDIS_URL=<redis-staging-url>
SECRET_KEY=<secure-random-key>
NEXT_PUBLIC_API_URL=<staging-domain-url>
API_HOST=0.0.0.0
API_PORT=8000
```

**Production** (GitHub Secrets + deployment-time configuration)
```
ENVIRONMENT=production
LOG_LEVEL=WARNING
DATABASE_URL=<postgres-production-url>
REDIS_URL=<redis-production-url>
SECRET_KEY=<secure-random-key>
NEXT_PUBLIC_API_URL=<production-domain-url>
API_HOST=0.0.0.0
API_PORT=8000
```

#### Secrets Management

**GitHub Secrets for CI/CD**
- `GHCR_TOKEN` - GitHub Container Registry authentication
- `DOCKER_HUB_USERNAME` / `DOCKER_HUB_TOKEN` - Docker Hub credentials
- `RENDER_DEPLOY_HOOK_STAGING` - Render deployment webhook
- `RENDER_DEPLOY_HOOK_PRODUCTION` - Render deployment webhook
- `SLACK_WEBHOOK_URL` - Notifications

**Environment Secrets (stored in deployment platform)**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - FastAPI secret key
- `API_KEYS` - Third-party API keys (eBay, etc.)
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` - S3 credentials

**No Secrets in Code:**
- .env files never committed (except .env.example with placeholders)
- Sensitive data loaded from environment at runtime
- Secrets rotated regularly (3-6 months)

### 3. Database Migration Strategy

#### Migration Workflow

```
PR → Test Migrations Locally → Review SQL → Merge
  ↓
Deploy to Staging → Run Migrations → Smoke Tests
  ↓
Staging Approval → Deploy to Production → Run Migrations → Verify
```

#### Zero-Downtime Migration Pattern

**Add Column with Default**
```sql
-- Safe: default allows writes during migration
ALTER TABLE listings ADD COLUMN new_field VARCHAR(255) DEFAULT 'value';
```

**Remove Column (After Deployment)**
```sql
-- Step 1 (first deploy): Stop using column in code
-- Step 2 (verify stable): Remove column in next deploy
ALTER TABLE listings DROP COLUMN old_field;
```

**Create Index Concurrently**
```sql
-- Non-blocking index creation
CREATE INDEX CONCURRENTLY idx_listings_status ON listings(status);
```

#### Migration Coordination

1. **Pre-Deployment**
   - Test migrations against staging database clone
   - Verify backward compatibility
   - Estimate duration for large tables

2. **During Staging Deployment**
   ```bash
   alembic upgrade head
   ```

3. **During Production Deployment**
   ```bash
   alembic upgrade head
   # Verify migration success before continuing
   ```

4. **Rollback Procedure**
   ```bash
   alembic downgrade -1  # Revert last migration
   ```

### 4. Health Check & Readiness Probe Strategy

#### API Health Endpoint

```python
# GET /health
{
  "status": "healthy",
  "version": "1.2.3",
  "database": "connected",
  "redis": "connected",
  "uptime_seconds": 3600
}
```

#### Readiness Probes (for load balancers)

**Before accepting traffic:**
1. API responds to health check
2. Database connectivity verified
3. All critical dependencies available
4. No ongoing migrations

#### Deployment Health Checks

```bash
# After deployment, verify:
curl -f http://localhost:8020/health || exit 1

# Check API endpoints
curl -f http://localhost:8020/api/listings || exit 1

# Verify web frontend loads
curl -f http://localhost:3000 || exit 1
```

### 5. Zero-Downtime Deployment Pattern

#### Blue/Green Deployment

```
┌─────────────────────────────────────────────────────────┐
│  Current (Blue) - Running in Production                 │
│  ├─ API v1.0.0 instances: 3                            │
│  ├─ Web v1.0.0 instances: 2                            │
│  └─ Worker instances: 2                                 │
└─────────────────────────────────────────────────────────┘

                    ↓ Deploy new version

┌─────────────────────────────────────────────────────────┐
│  New (Green) - Deployed but not receiving traffic       │
│  ├─ API v1.1.0 instances: 3                            │
│  ├─ Web v1.1.0 instances: 2                            │
│  └─ Worker instances: 2                                 │
│                                                          │
│  Health Checks:                                         │
│  ✓ API responding                                       │
│  ✓ Database migrations successful                       │
│  ✓ No critical errors in logs                          │
│  ✓ Memory/CPU within acceptable range                  │
└─────────────────────────────────────────────────────────┘

                    ↓ Gradual traffic shift

┌─────────────────────────────────────────────────────────┐
│  Traffic Distribution                                    │
│  ├─ Blue (v1.0.0): 50%  Green (v1.1.0): 50%            │
│  ├─ Monitor error rates, latency, resource usage       │
│  ├─ Canary period: 5-15 minutes                         │
└─────────────────────────────────────────────────────────┘

                    ↓ Switch all traffic

┌─────────────────────────────────────────────────────────┐
│  Updated (Green becomes Blue)                           │
│  ├─ API v1.1.0 instances: 3                            │
│  ├─ Web v1.1.0 instances: 2                            │
│  ├─ Blue (v1.0.0) retained for quick rollback          │
│  └─ Traffic: 100% → Green                              │
└─────────────────────────────────────────────────────────┘

        ↓ Verify (5-30 minutes) ↓ Keep or Rollback

    ┌─ All metrics OK ──→ Remove Blue v1.0.0
    │
    └─ Critical issue ──→ Switch back to Blue v1.0.0
```

#### Graceful Shutdown

**API Shutdown Sequence:**
```python
# 1. Stop accepting new connections
# 2. Drain existing requests (30-60s timeout)
# 3. Close database connections properly
# 4. Exit cleanly

@app.on_event("shutdown")
async def shutdown_event():
    # Connection cleanup
    await db.close()
    await redis.close()
```

**Worker Shutdown Sequence:**
```python
# Celery SIGTERM handling
# 1. Stop accepting new tasks
# 2. Complete in-flight tasks (timeout: 30s)
# 3. Close connections
# 4. Exit
```

### 6. Rollback Strategy

#### Automatic Rollback Triggers

```yaml
# Trigger rollback if any of these conditions met:
- Error rate > 5% for 2+ minutes
- Response time p95 > 3000ms for 3+ minutes
- CPU usage > 90% for 5+ minutes
- Memory usage > 85% for 5+ minutes
- Database connectivity failures
- Critical error pattern in logs (e.g., panic, fatal)
```

#### Manual Rollback Procedure

```bash
# 1. Identify deployment to rollback
git log --oneline | head -5

# 2. Trigger rollback in CI/CD
# Option A: GitHub Actions manual run
gh workflow run rollback.yml -f version=v1.0.0 -f environment=production

# Option B: Deploy previous version
git revert <commit-hash>
git push origin main
```

#### Rollback Considerations

- **Database Migrations**: Only rollback schema if safe (see migration strategy)
- **Data Integrity**: Verify no data loss during rollback
- **Cache Invalidation**: Clear caches if schema changed
- **Monitoring**: Keep monitoring active during rollback

### 7. Multi-Environment Deployment Flow

#### Development
- Local docker-compose stack
- Hot reload enabled
- Debug mode on
- All services run locally

#### Staging
- Full production-like setup
- Real database (not production data)
- Real secrets
- Run load tests and security scans
- Approval gate before production

#### Production
- Multi-instance setup
- Load balancing
- Database backups and replication
- Monitoring and alerting
- Manual approval gate
- Gradual rollout (canary)

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] GitHub Actions workflow for building and pushing images
- [ ] Secrets configuration in GitHub
- [ ] Registry setup (GHCR)
- [ ] Staging deployment automation
- [ ] Database migration testing

### Phase 2: Production Ready (Week 3-4)
- [ ] Production deployment workflow
- [ ] Manual approval gates
- [ ] Health check implementation
- [ ] Monitoring and alerting
- [ ] Rollback automation

### Phase 3: Advanced (Week 5+)
- [ ] Blue/green deployments
- [ ] Canary deployments with traffic split
- [ ] Auto-rollback on metrics breach
- [ ] GitOps integration (ArgoCD/Flux)
- [ ] Multi-region deployment

---

## Security Considerations

### Supply Chain Security (SLSA Framework)

#### Build Provenance
- [ ] Attestation of build environment
- [ ] Link artifacts to source commits
- [ ] Sign images with Sigstore

#### Dependency Security
- [ ] Dependency scanning (Snyk, Dependabot)
- [ ] SBOM generation (syft)
- [ ] License compliance checking

#### Image Security
- [ ] Vulnerability scanning (Trivy)
- [ ] Non-root container user
- [ ] Read-only filesystem
- [ ] No privileged mode

### Secrets Management

#### Pre-Deployment Scanning
- Scan commits for secrets (GitGuardian, TruffleHog)
- Block commits with exposed secrets

#### Rotation Strategy
- Rotate secrets every 90 days
- Implement secret versioning
- Update GitHub secrets and deployment config

#### Access Control
- GitHub secrets require branch protection
- Production deployments require approval
- Audit log all secret access

### Network Security

#### For Render/Railway (PaaS)
- Use HTTPS/TLS for all traffic
- Environment isolation
- VPC for internal services

#### For Kubernetes (Enterprise)
- Network policies for pod communication
- Service mesh (Istio/Linkerd) for security
- mTLS for inter-service communication

---

## Monitoring & Observability

### Deployment Metrics

```
Key Metrics to Track:
- Deployment frequency (target: daily)
- Lead time for changes (target: < 4 hours)
- Change failure rate (target: < 15%)
- Mean time to recovery (target: < 1 hour)
```

### Application Health

```
Real-time monitoring:
- Request rate (requests/second)
- Error rate (5xx, 4xx errors)
- Response time (p50, p95, p99 latency)
- Database pool utilization
- Redis connection count
- Task queue depth (Celery)
```

### Log Aggregation

```
Centralized logging:
- API request/response logs
- Worker task execution logs
- Migration logs
- Deployment logs
```

### Alerting

```
Critical alerts trigger immediate response:
- Deployment failure
- Health check failure
- Error rate spike
- Performance degradation
- Database connectivity loss
```

---

## Cost Optimization

### Compute
- Auto-scaling based on metrics
- Right-size instances
- Use spot instances (non-production)

### Storage
- Database backups retention policy
- Log retention limits
- Image cleanup (keep last 10 versions)

### Network
- CDN for static assets
- Cache headers optimization

### Recommendations
- Start on Render/Railway for simplicity
- Cost: $15-50/month for basic setup
- Scale to Kubernetes if needed (higher complexity)

---

## Checklist: Before First Deployment

- [ ] Docker images build successfully locally
- [ ] All tests pass locally
- [ ] Environment configuration reviewed
- [ ] Secrets configured in deployment platform
- [ ] Database migrations tested
- [ ] Health checks implemented and verified
- [ ] Monitoring and alerting configured
- [ ] Backup strategy in place
- [ ] Rollback plan documented
- [ ] Team trained on deployment process
- [ ] Runbook for common issues created
- [ ] Security scan clean (no high vulnerabilities)
- [ ] Performance baseline established

---

## Related Documents

See the accompanying guides for detailed implementation:
- [GitHub Actions Workflows Guide](/docs/deployment/github-actions-workflows.md)
- [Pre-Deployment Checklist](/docs/deployment/pre-deployment-checklist.md)
- [Environment Configuration Guide](/docs/deployment/environment-configuration.md)
- [Troubleshooting Guide](/docs/deployment/troubleshooting.md)
