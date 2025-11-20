---
title: "CI/CD Implementation Guide"
description: "Step-by-step implementation guide for setting up CI/CD pipelines and deploying Deal Brain"
audience: [developers, devops]
tags: [implementation, setup, github-actions, deployment, render]
created: 2025-11-20
updated: 2025-11-20
category: "configuration-deployment"
status: published
related:
  - /docs/deployment/DEPLOYMENT_STRATEGY.md
  - /docs/deployment/environment-configuration.md
---

# CI/CD Implementation Guide

This guide walks through implementing the CI/CD pipeline and deploying Deal Brain step-by-step.

---

## Phase 1: Foundation (Week 1-2)

### Step 1: Set Up GitHub Container Registry

#### 1.1 Create GitHub Token

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Click "Generate new token (classic)"
3. Configure token:
   - Name: `GHCR_TOKEN`
   - Expiration: 90 days
   - Scopes: `read:packages`, `write:packages`, `delete:packages`
4. Copy token (you won't see it again)

#### 1.2 Add Token to GitHub Secrets

1. Go to Repository Settings → Secrets and Variables → Actions
2. Click "New repository secret"
3. Name: `GHCR_TOKEN`
4. Value: (paste the token)
5. Click "Add secret"

#### 1.3 Test Registry Access Locally

```bash
# Log in to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Alternatively, use personal access token
echo GHCR_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build a test image
docker build -f infra/api/Dockerfile \
  --target production \
  -t ghcr.io/USERNAME/deal-brain-api:test .

# Push test image
docker push ghcr.io/USERNAME/deal-brain-api:test

# Verify
curl -H "Authorization: token GITHUB_TOKEN" \
  https://api.github.com/user/packages
```

### Step 2: Configure GitHub Actions Workflows

#### 2.1 Add CI/CD Workflow

The main workflow is already provided as `/github/workflows/ci-cd.yml`. Update it with your details:

```bash
# Review the workflow
cat .github/workflows/ci-cd.yml | head -50

# Update placeholders:
# - Replace REGISTRY with ghcr.io
# - Replace IMAGE_NAME with your-username/deal-brain
# - Replace secrets references with your actual secret names
```

#### 2.2 Test Workflow Trigger

```bash
# Push to main to trigger workflow
git add .github/workflows/ci-cd.yml
git commit -m "ci: add GitHub Actions CI/CD pipeline"
git push origin main

# Watch workflow run
# Go to: Repository → Actions → CI/CD Pipeline
```

### Step 3: Set Up Local Development Environment

#### 3.1 Install Required Tools

```bash
# Docker & Docker Compose
docker --version  # Should be 20.10+
docker-compose --version  # Should be 2.0+

# Git
git --version  # Should be 2.30+

# Python
python3 --version  # Should be 3.11+

# Node.js
node --version  # Should be 18+
corepack enable pnpm
pnpm --version  # Should be 8+
```

#### 3.2 Configure Local Environment

```bash
# Clone repository
git clone https://github.com/USERNAME/deal-brain.git
cd deal-brain

# Copy environment file
cp .env.example .env

# Edit for your local setup (optional - defaults work for Docker)
vim .env

# Make sure .env is in .gitignore
echo ".env" >> .gitignore
git add .gitignore
git commit -m "chore: ensure .env not tracked"
```

#### 3.3 Verify Local Setup

```bash
# Install dependencies
make setup

# Start services
make up

# Run tests
make test

# Verify services running
docker-compose ps

# Check API health
curl http://localhost:8020/health

# Stop services
make down
```

### Step 4: Implement Health Check Endpoint

#### 4.1 Verify Health Endpoint Exists

```bash
# Check if endpoint is implemented
grep -r "def health" apps/api/

# If not found, create it:
# File: apps/api/dealbrain_api/api/health.py

cat > apps/api/dealbrain_api/api/health.py << 'EOF'
from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dealbrain_api.db import get_db
import redis
import time

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint for deployment verification."""

    # Get start time for response
    start_time = time.time()

    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - app.start_time) if hasattr(app, 'start_time') else 0,
    }

    # Check database
    try:
        await db.execute("SELECT 1")
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        checks["status"] = "degraded"

    # Check Redis
    try:
        redis_client.ping()
        checks["redis"] = "connected"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        checks["status"] = "degraded"

    checks["response_time_ms"] = int((time.time() - start_time) * 1000)

    if checks["status"] != "healthy":
        raise HTTPException(status_code=503, detail=checks)

    return checks
EOF
```

#### 4.2 Register Health Endpoint

```bash
# Update main FastAPI app
# File: apps/api/dealbrain_api/main.py

# Add to app initialization:
from dealbrain_api.api import health
app.include_router(health.router)
```

#### 4.3 Test Health Endpoint

```bash
# Local test
curl -s http://localhost:8020/health | jq

# Output should be:
# {
#   "status": "healthy",
#   "timestamp": "2025-11-20T12:00:00.000000",
#   "database": "connected",
#   "redis": "connected",
#   "response_time_ms": 45
# }
```

### Step 5: Set Up Render Account

#### 5.1 Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub account
3. Authorize Render to access repositories
4. Create new project

#### 5.2 Configure Staging Service

```bash
# In Render dashboard:
# 1. Create Web Service
# 2. Connect GitHub repository
# 3. Configure:
#    Name: dealbrain-api-staging
#    Environment: Docker
#    Branch: main
#    Dockerfile path: infra/api/Dockerfile
#    Build command: (leave empty - use Dockerfile)
#    Start command: dealbrain-api
# 4. Set environment variables:
#    ENVIRONMENT=staging
#    LOG_LEVEL=INFO
#    DATABASE_URL=postgresql+asyncpg://user:pass@host/db
#    REDIS_URL=redis://host:port
#    SECRET_KEY=<generate-secure-key>
#    NEXT_PUBLIC_API_URL=https://staging-api.dealbrain.render.com
```

#### 5.3 Create Deployment Webhook

```bash
# In Render dashboard:
# 1. Select service (dealbrain-api-staging)
# 2. Go to Settings → Deploy Webhook
# 3. Copy webhook URL
# 4. Add to GitHub Secrets:
#    Name: RENDER_DEPLOY_HOOK_STAGING
#    Value: <webhook-url>
```

#### 5.4 Set Up PostgreSQL

```bash
# In Render dashboard:
# 1. Create PostgreSQL Database
# 2. Configure:
#    Name: dealbrain-staging-db
#    Database: dealbrain_staging
# 3. Copy connection string
# 4. Add to environment variables:
#    DATABASE_URL=<connection-string-with-asyncpg>
#    SYNC_DATABASE_URL=<connection-string-with-psycopg>
```

#### 5.5 Set Up Redis

```bash
# In Render dashboard:
# 1. Create Redis Instance
# 2. Configure:
#    Name: dealbrain-staging-redis
# 3. Copy connection URL
# 4. Add to environment:
#    REDIS_URL=<redis-connection-url>
```

### Step 6: Test Staging Deployment

#### 6.1 Trigger Deployment

```bash
# Make a test commit
echo "test" >> .gitignore
git add .gitignore
git commit -m "test: trigger CI/CD pipeline"
git push origin main

# Watch GitHub Actions
# Go to: Actions → CI/CD Pipeline → Watch progress

# Simultaneously watch Render deploy
# Go to Render → dealbrain-api-staging → Deployments
```

#### 6.2 Verify Deployment

```bash
# After deployment completes:

# Check health endpoint
curl -s https://staging-api.dealbrain.render.com/health | jq

# Check logs
# Render dashboard → Logs tab
```

#### 6.3 Run Staging Tests

```bash
# Test API endpoints
curl -s https://staging-api.dealbrain.render.com/api/listings | jq

# Test web frontend
curl -s https://staging-web.dealbrain.render.com/ | grep -i "dealbrain"

# Monitor for 10+ minutes
# Check error rates, response times, CPU usage
```

---

## Phase 2: Production Ready (Week 3-4)

### Step 7: Implement Database Migrations

#### 7.1 Create Migration Script

```bash
# File: scripts/run_migrations.sh

#!/bin/bash
set -e

echo "Running database migrations..."
poetry run alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Migrations completed successfully"
    exit 0
else
    echo "Migration failed"
    exit 1
fi
```

#### 7.2 Test Migration

```bash
# Test locally
docker-compose down -v  # Clean database
docker-compose up -d db
sleep 5
poetry run alembic upgrade head
poetry run alembic current  # Verify version
```

#### 7.3 Configure Migration in Render

```bash
# In Render dashboard:
# 1. Select dealbrain-api-staging service
# 2. Settings → Build Command
# 3. Set command:
#    pip install poetry && \
#    poetry install && \
#    poetry run alembic upgrade head
```

### Step 8: Set Up Monitoring

#### 8.1 Configure Grafana

```bash
# Access Grafana
# Local: http://localhost:3021 (admin/admin)
# Production: Configure dashboard in deployment platform

# Create dashboard:
# 1. Add Prometheus datasource
# 2. Create panels:
#    - Request Rate (5m)
#    - Error Rate (%)
#    - Response Time (p95)
#    - CPU Usage
#    - Memory Usage
#    - Database Connections
```

#### 8.2 Configure Prometheus Alerts

```bash
# File: infra/prometheus/alerts.yml

groups:
  - name: dealbrain
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        annotations:
          summary: "High error rate detected"
```

#### 8.3 Set Up Slack Integration

```bash
# Create Slack Incoming Webhook
# 1. Go to Slack workspace
# 2. Apps → Custom Integrations → Incoming Webhooks
# 3. Create new webhook for #deployments channel
# 4. Copy webhook URL
# 5. Add to GitHub Secrets:
#    Name: SLACK_WEBHOOK_URL
#    Value: <webhook-url>
```

### Step 9: Configure Production Environment

#### 9.1 Create Production Service in Render

```bash
# Follow similar steps as staging:
# Name: dealbrain-api-production
# Branch: main (with tag filtering for v* tags)
# Environment variables:
#   ENVIRONMENT=production
#   LOG_LEVEL=WARNING
#   DATABASE_URL=<production-db-url>
#   REDIS_URL=<production-redis-url>
#   SECRET_KEY=<new-production-key>
#   NEXT_PUBLIC_API_URL=https://api.dealbrain.com
```

#### 9.2 Create Production Database

```bash
# Follow similar steps as staging:
# Ensure:
# - Daily automated backups
# - Point-in-time recovery enabled
# - Read replicas if needed
# - Enhanced monitoring
```

#### 9.3 Create Deployment Webhook for Production

```bash
# In Render dashboard:
# 1. Select production service
# 2. Get webhook URL
# 3. Add to GitHub Secrets:
#    Name: RENDER_DEPLOY_HOOK_PRODUCTION
#    Value: <webhook-url>
```

### Step 10: Manual Approval Gate

#### 10.1 Configure Environment Protection

```bash
# In GitHub (if using branch protection):
# 1. Go to Settings → Branches → main
# 2. Add branch protection rule
# 3. Under "Require status checks to pass":
#    Check all required jobs (lint, test, build)
# 4. Under environment-specific rules:
#    Require approval for production deployment
```

#### 10.2 Document Approval Process

```bash
# File: docs/APPROVAL_PROCESS.md

# Production deployments require:
# 1. Tech Lead approval
# 2. QA Lead approval
# 3. At least 24-hour staging soak time
# 4. No critical alerts in last 1 hour
# 5. Backup verification
```

---

## Phase 3: Advanced Features (Week 5+)

### Step 11: Implement Blue/Green Deployment

#### 11.1 Create Blue/Green Service Strategy

```bash
# Strategy for Render:
# 1. Deploy to "green" service (dealbrain-api-blue/green)
# 2. Run health checks
# 3. Update load balancer to route to green
# 4. Keep blue running for 30+ minutes
# 5. Monitor for issues
# 6. Either promote green or rollback to blue

# For Kubernetes:
# Use Deployment with RevisionHistoryLimit: 2
# Enable automatic rollback on failure
```

#### 11.2 Implement Traffic Shifting

```bash
# For Render:
# - Cannot do automatic traffic split
# - Manual traffic shift via DNS/load balancer

# For Kubernetes:
# Use Istio VirtualService with weight-based routing
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: dealbrain-api
spec:
  hosts:
  - dealbrain.example.com
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: dealbrain-api-blue
      weight: 90
    - destination:
        host: dealbrain-api-green
      weight: 10
```

### Step 12: Implement Canary Deployments

#### 12.1 Set Up Canary Release Strategy

```bash
# Using Argo Rollouts (for Kubernetes):
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: dealbrain-api
spec:
  replicas: 3
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {duration: 5m}
      - setWeight: 25
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 5m}
      - setWeight: 100
```

#### 12.2 Automated Metric Analysis

```bash
# Using Flagger (for progressive delivery):
# Monitor key metrics during rollout
# Auto-rollback if:
# - Error rate > 5%
# - Latency p95 > 3000ms
# - CPU spike > 80%
```

### Step 13: Implement Auto-Rollback

#### 13.1 Create Rollback Workflow

```bash
# File: .github/workflows/rollback.yml

name: Rollback Deployment

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to rollback to'
        required: true
      environment:
        description: 'Environment (staging or production)'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest
    steps:
      - name: Rollback via Render
        run: |
          # Get deployment history
          # Find version to rollback to
          # Trigger deployment of that version
          # Monitor for success
          # Send notification
```

#### 13.2 Create Automated Rollback Triggers

```bash
# Monitor these metrics:
# - Error rate spike > 5% from baseline
# - Response time p95 > 3x baseline
# - CPU > 90% for 5+ minutes
# - Memory > 90% for 5+ minutes
# - Database connection errors

# Automatically trigger rollback via:
# - Custom monitoring webhook
# - Datadog/New Relic integration
# - CloudWatch alarms (for AWS)
```

---

## Phase 4: GitOps (Week 6+)

### Step 14: Implement GitOps with ArgoCD

#### 14.1 Install ArgoCD

```bash
# For Kubernetes deployments:
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Visit https://localhost:8080 (username: admin, get password via):
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

#### 14.2 Create Application

```bash
# File: infra/argocd/dealbrain-api.yml

apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: dealbrain-api
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/USERNAME/deal-brain
    targetRevision: main
    path: infra/k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: dealbrain-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

#### 14.3 Push Infrastructure as Code

```bash
# Create K8s manifests
mkdir -p infra/k8s
cat > infra/k8s/deployment.yml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dealbrain-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: ghcr.io/USERNAME/deal-brain-api:latest
        ports:
        - containerPort: 8000
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
EOF

# Push to git
git add infra/k8s/
git commit -m "infra: add Kubernetes manifests for GitOps"
git push origin main
```

---

## Troubleshooting

### Build Failures

**Issue: Docker build fails with "permission denied"**
```bash
# Solution: Ensure user has Docker permissions
sudo usermod -aG docker $USER
newgrp docker
```

**Issue: GitHub Actions workflow not triggering**
```bash
# Solution: Check workflow syntax
act -j validate -v  # Test locally with act

# Check GitHub Actions logs
# Go to: Actions tab → View detailed logs
```

### Deployment Failures

**Issue: Health check failing after deployment**
```bash
# Check logs
docker-compose logs api

# Verify environment variables
echo $DATABASE_URL
echo $REDIS_URL

# Test service connectivity
curl http://api:8000/health
```

**Issue: Database migration fails**
```bash
# Rollback migration
poetry run alembic downgrade -1

# Check migration history
poetry run alembic history --verbose

# Fix migration file and retry
poetry run alembic upgrade head
```

### Performance Issues

**Issue: High memory usage after deployment**
```bash
# Check memory limits
docker stats

# Check for memory leaks
# Monitor over 10+ minutes
watch 'docker stats --no-stream'

# If spike, check logs for errors
docker-compose logs -f api | grep -i error
```

---

## Verification Checklist

After implementation, verify:

- [ ] GitHub Actions workflow runs on push
- [ ] Docker images build successfully
- [ ] Images push to GHCR
- [ ] Staging deployment automatic
- [ ] Health endpoints respond
- [ ] Database migrations run
- [ ] Monitoring dashboards show data
- [ ] Slack notifications working
- [ ] Manual approval gate working
- [ ] Production deployment manual
- [ ] Rollback procedure tested
- [ ] Team trained on process

---

## Next Steps

1. **Week 1-2**: Complete Phase 1 (Foundation)
2. **Week 3-4**: Complete Phase 2 (Production Ready)
3. **Week 5+**: Implement Phase 3 (Advanced features)
4. **Month 2+**: Implement Phase 4 (GitOps)

---

## Related Documentation

- [Deployment Strategy](/docs/deployment/DEPLOYMENT_STRATEGY.md)
- [Environment Configuration](/docs/deployment/environment-configuration.md)
- [Pre-Deployment Checklist](/docs/deployment/pre-deployment-checklist.md)
