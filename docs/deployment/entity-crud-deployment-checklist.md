---
title: "Entity CRUD Deployment Checklist"
description: "Comprehensive checklist for deploying entity CRUD functionality to production"
audience: [devops, developers]
tags: [deployment, checklist, entity-crud, production]
created: 2025-11-14
updated: 2025-11-14
category: "configuration-deployment"
status: published
related:
  - /docs/deployment/entity-crud-migration-plan.md
  - /docs/deployment/frontend-smoke-tests.md
  - /scripts/deployment/smoke-tests.sh
---

# Entity CRUD Deployment Checklist

## Overview

This checklist covers all steps required to deploy the Entity CRUD functionality (Phases 1-7) to production. Follow each section in order and check off items as completed.

**Deployment Type**: Zero-downtime, backwards-compatible deployment
**Estimated Duration**: 30-45 minutes (including verification)
**Required Downtime**: None

---

## Pre-Deployment Checklist

### Code & Tests

- [ ] All Phase 8 tests passing locally
  ```bash
  poetry run pytest tests/test_catalog_api.py -v
  ```
- [ ] Code reviewed and approved (PR merged)
- [ ] Branch up-to-date with main/master
- [ ] No merge conflicts
- [ ] All CI/CD checks passing (if applicable)

### Database

- [ ] Verify current migration status on staging
  ```bash
  poetry run alembic current
  # Expected: 0026 (head)
  ```
- [ ] Verify no pending migrations
  ```bash
  poetry run alembic check
  # Expected: "No new migrations found"
  ```
- [ ] Database backup completed (automated backup verified)
- [ ] Backup retention confirmed (can restore if needed)

### Testing & Quality

- [ ] Smoke tests passing on staging
  ```bash
  API_URL=https://staging-api.yourdomain.com ./scripts/deployment/smoke-tests.sh
  ```
- [ ] Frontend smoke tests completed on staging
  - See `/docs/deployment/frontend-smoke-tests.md`
- [ ] Performance benchmarks meet targets
  - Update endpoints: < 200ms p95 latency
  - Delete endpoints: < 500ms p95 latency
  - List endpoints: < 100ms p95 latency
- [ ] Accessibility audit passed (WCAG AA compliance)
- [ ] Browser compatibility verified (Chrome, Firefox, Safari, Edge)

### Monitoring & Observability

- [ ] OpenTelemetry collector running and healthy
- [ ] Prometheus scraping API metrics
  - Check: `http://prometheus:9090/targets`
- [ ] Grafana dashboards accessible
  - Check: `http://grafana:3000/dashboards`
- [ ] Alert rules configured for:
  - API error rate > 5%
  - API latency p95 > 1000ms
  - Database connection pool exhaustion
  - High CPU/memory usage
- [ ] Log aggregation working (if applicable)
- [ ] On-call engineer notified and available

### Communication

- [ ] Stakeholders notified of deployment window
  - Sent: [Date/Time]
  - Recipients: [List or link to notification]
- [ ] Deployment scheduled in team calendar
- [ ] Rollback plan reviewed and understood
- [ ] Post-deployment communication drafted

---

## Deployment Steps

### 1. Backend Deployment (API)

#### 1.1 Pre-Deploy Verification

- [ ] SSH into production API server (or access deployment system)
- [ ] Verify current version running
  ```bash
  git rev-parse HEAD
  curl http://localhost:8000/health
  ```
- [ ] Check current resource usage (CPU, memory, disk)
  ```bash
  top
  df -h
  ```

#### 1.2 Pull Latest Code

- [ ] Navigate to application directory
  ```bash
  cd /path/to/deal-brain
  ```
- [ ] Backup current version (tag or note commit hash)
  ```bash
  git rev-parse HEAD > /tmp/pre-deployment-commit.txt
  ```
- [ ] Pull latest code from deployment branch
  ```bash
  git fetch origin
  git checkout <deployment-branch>
  git pull origin <deployment-branch>
  ```
- [ ] Verify correct commit deployed
  ```bash
  git log -1 --oneline
  ```

#### 1.3 Install Dependencies

- [ ] Install Python dependencies
  ```bash
  poetry install --no-dev --sync
  ```
- [ ] Verify virtual environment activated
  ```bash
  which python
  # Should show: .venv/bin/python or poetry venv path
  ```

#### 1.4 Database Migrations

- [ ] Run database migrations (should be no-op for this deployment)
  ```bash
  poetry run alembic upgrade head
  # Expected: "No changes detected" or already at head
  ```
- [ ] Verify migration status
  ```bash
  poetry run alembic current
  # Expected: 0026 (head)
  ```

#### 1.5 Restart API Service

- [ ] Restart API service gracefully

  **For systemd:**
  ```bash
  sudo systemctl restart dealbrain-api
  sudo systemctl status dealbrain-api
  ```

  **For Docker Compose:**
  ```bash
  docker-compose restart api
  docker-compose logs -f api --tail=50
  ```

  **For Docker (standalone):**
  ```bash
  docker restart dealbrain-api
  docker logs -f dealbrain-api --tail=50
  ```

- [ ] Wait for service to be healthy (30-60 seconds)

#### 1.6 Verify API Health

- [ ] Check health endpoint
  ```bash
  curl -f http://localhost:8000/health
  # Expected: HTTP 200 OK
  ```
- [ ] Check metrics endpoint (if exposed)
  ```bash
  curl http://localhost:8000/metrics
  ```
- [ ] Verify API logs show no errors
  ```bash
  # For systemd
  journalctl -u dealbrain-api -n 50 --no-pager

  # For Docker
  docker logs dealbrain-api --tail=50
  ```
- [ ] Test a critical endpoint
  ```bash
  curl http://localhost:8000/v1/catalog/cpus?limit=1
  # Expected: HTTP 200 with CPU data
  ```

---

### 2. Frontend Deployment (Web)

#### 2.1 Pre-Deploy Verification

- [ ] SSH into production web server (or access deployment system)
- [ ] Verify current version running
  ```bash
  git rev-parse HEAD
  curl http://localhost:3000/
  ```

#### 2.2 Pull Latest Code

- [ ] Navigate to application directory
  ```bash
  cd /path/to/deal-brain
  ```
- [ ] Backup current version
  ```bash
  git rev-parse HEAD > /tmp/pre-deployment-web-commit.txt
  ```
- [ ] Pull latest code
  ```bash
  git fetch origin
  git checkout <deployment-branch>
  git pull origin <deployment-branch>
  ```

#### 2.3 Install Dependencies & Build

- [ ] Install JavaScript dependencies
  ```bash
  pnpm install --frozen-lockfile
  ```
- [ ] Build production bundle
  ```bash
  cd apps/web
  pnpm build
  ```
- [ ] Verify build succeeded (no errors)
  ```bash
  ls -la .next/
  # Should see build artifacts
  ```

#### 2.4 Deploy Static Assets

- [ ] Copy static assets to CDN (if applicable)
  ```bash
  # Example for S3/CloudFront
  # aws s3 sync .next/static s3://your-bucket/_next/static --cache-control max-age=31536000
  ```
- [ ] Verify assets uploaded successfully

#### 2.5 Restart Web Service

- [ ] Restart web service gracefully

  **For systemd:**
  ```bash
  sudo systemctl restart dealbrain-web
  sudo systemctl status dealbrain-web
  ```

  **For Docker Compose:**
  ```bash
  docker-compose restart web
  docker-compose logs -f web --tail=50
  ```

  **For Docker (standalone):**
  ```bash
  docker restart dealbrain-web
  docker logs -f dealbrain-web --tail=50
  ```

- [ ] Wait for service to be healthy (15-30 seconds)

#### 2.6 Verify Web Health

- [ ] Check homepage loads
  ```bash
  curl -I http://localhost:3000/
  # Expected: HTTP 200 OK
  ```
- [ ] Check Next.js health (if available)
  ```bash
  curl http://localhost:3000/api/health
  ```
- [ ] Verify web logs show no errors
  ```bash
  # For systemd
  journalctl -u dealbrain-web -n 50 --no-pager

  # For Docker
  docker logs dealbrain-web --tail=50
  ```

---

## Post-Deployment Verification

### Automated Smoke Tests

- [ ] Run automated smoke test script
  ```bash
  cd /home/user/deal-brain
  API_URL=https://api.yourdomain.com ./scripts/deployment/smoke-tests.sh
  ```
- [ ] All smoke tests passed
- [ ] Review smoke test output for warnings

### Manual Frontend Smoke Tests

Complete all tests in `/docs/deployment/frontend-smoke-tests.md`:

- [ ] Homepage loads without errors
- [ ] Navigate to `/catalog/cpus`
- [ ] CPU detail page loads
- [ ] Edit CPU modal opens and saves successfully
- [ ] Delete CPU dialog opens and cancels correctly
- [ ] Navigate to `/global-fields`
- [ ] "View Details" links work
- [ ] All entity types tested (CPU, GPU, Profile, PortsProfile, RamSpec, StorageProfile)

### Critical User Paths

- [ ] **Create Entity**: Can create new CPU via API
  ```bash
  curl -X POST http://localhost:8000/v1/catalog/cpus \
    -H "Content-Type: application/json" \
    -d '{"name":"Test CPU","manufacturer":"TestCo"}'
  ```
- [ ] **Read Entity**: Can fetch CPU detail via API
- [ ] **Update Entity**: Can update CPU via PATCH
  ```bash
  curl -X PATCH http://localhost:8000/v1/catalog/cpus/1 \
    -H "Content-Type: application/json" \
    -d '{"notes":"Updated via smoke test"}'
  ```
- [ ] **Delete Entity**: Delete attempt on in-use entity returns 409 Conflict
- [ ] **List Entities**: Can list all CPUs
- [ ] **Usage Check**: Can fetch listings using CPU

### Performance Verification

- [ ] Check API response times in Grafana
  - p50 < 100ms for list endpoints
  - p95 < 200ms for update endpoints
  - p95 < 500ms for delete endpoints
- [ ] Check database query performance
  - No slow queries (> 1s)
  - Connection pool utilization < 80%
- [ ] Check frontend load times
  - First contentful paint < 1.5s
  - Time to interactive < 3s

### Monitoring & Alerts

- [ ] No critical alerts firing
- [ ] API error rate < 1%
  - Check Grafana: API Error Rate dashboard
  - Check Prometheus: `rate(http_requests_total{status=~"5.."}[5m])`
- [ ] No database connection errors
- [ ] CPU/memory usage within normal ranges
  - API container: < 80% CPU, < 2GB RAM
  - Web container: < 60% CPU, < 1GB RAM

### Data Integrity

- [ ] Verify no data loss
  - Check entity counts match pre-deployment
  ```bash
  # Count CPUs
  curl http://localhost:8000/v1/catalog/cpus | jq '. | length'
  ```
- [ ] Verify foreign key constraints intact
  - Update entity and verify listings still reference it
- [ ] Verify unique constraints working
  - Attempt to create duplicate entity (should fail with 422)

---

## Rollback Procedure (If Issues Detected)

### Decision Criteria for Rollback

Initiate rollback if:
- ❌ Critical smoke tests failing
- ❌ API error rate > 10%
- ❌ Data integrity issues detected
- ❌ Monitoring shows service degradation
- ❌ User-facing critical bugs reported

### Rollback Steps

#### 1. Rollback API

- [ ] SSH into API server
- [ ] Checkout previous commit
  ```bash
  cd /path/to/deal-brain
  git checkout $(cat /tmp/pre-deployment-commit.txt)
  ```
- [ ] Restart API service
  ```bash
  sudo systemctl restart dealbrain-api
  # or
  docker-compose restart api
  ```
- [ ] Verify API health
  ```bash
  curl http://localhost:8000/health
  ```

#### 2. Rollback Web

- [ ] SSH into web server
- [ ] Checkout previous commit
  ```bash
  cd /path/to/deal-brain
  git checkout $(cat /tmp/pre-deployment-web-commit.txt)
  ```
- [ ] Rebuild frontend (if needed)
  ```bash
  cd apps/web && pnpm build
  ```
- [ ] Restart web service
  ```bash
  sudo systemctl restart dealbrain-web
  # or
  docker-compose restart web
  ```
- [ ] Verify web health
  ```bash
  curl -I http://localhost:3000/
  ```

#### 3. Database Rollback

- [ ] **Not needed** - No migrations to rollback for this deployment

#### 4. Verify Rollback

- [ ] Run smoke tests on rolled-back version
- [ ] Verify all services healthy
- [ ] Check monitoring dashboards
- [ ] Notify stakeholders of rollback

---

## Post-Deployment Tasks

### Communication

- [ ] Send deployment success notification
  - To: [Stakeholders, team members]
  - Subject: "Entity CRUD Features Deployed to Production"
  - Include: Deployment time, features added, any known issues
- [ ] Update deployment log/wiki with:
  - Deployment timestamp
  - Commit hash deployed
  - Any issues encountered
  - Resolution steps taken

### Monitoring (First 24 Hours)

- [ ] Monitor error rates closely (every 2 hours for first 8 hours)
- [ ] Watch for unusual patterns in logs
- [ ] Track user feedback/support tickets
- [ ] Review performance metrics

### Documentation

- [ ] Update production environment documentation (if needed)
- [ ] Document any deployment issues and resolutions
- [ ] Update runbook with lessons learned

### Cleanup

- [ ] Remove temporary files
  ```bash
  rm /tmp/pre-deployment-commit.txt
  rm /tmp/pre-deployment-web-commit.txt
  ```
- [ ] Archive deployment artifacts (if applicable)

---

## Success Criteria Summary

Deployment is successful when ALL of these criteria are met:

- ✅ All smoke tests passing (automated + manual)
- ✅ API error rate < 1%
- ✅ No critical alerts firing
- ✅ Performance metrics within acceptable ranges
- ✅ No data integrity issues
- ✅ All critical user paths functional
- ✅ Frontend loads without errors in all major browsers
- ✅ Edit functionality works for all entity types
- ✅ Delete functionality correctly prevents deletion of in-use entities
- ✅ Monitoring dashboards show healthy state

---

## Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| Deployment Lead | [Name/Email] | [Hours] |
| Backend Engineer | [Name/Email] | [Hours] |
| Frontend Engineer | [Name/Email] | [Hours] |
| DevOps On-Call | [Name/Email/Phone] | 24/7 |
| Product Owner | [Name/Email] | [Hours] |

---

## References

- [Migration Plan](/docs/deployment/entity-crud-migration-plan.md)
- [Smoke Test Script](/scripts/deployment/smoke-tests.sh)
- [Frontend Smoke Tests](/docs/deployment/frontend-smoke-tests.md)
- [Rollback Runbook](/docs/deployment/rollback-runbook.md) (if exists)
- [Incident Response](/docs/deployment/incident-response.md) (if exists)

---

## Deployment Log

**Date**: _______________
**Time Started**: _______________
**Time Completed**: _______________
**Deployed By**: _______________
**Commit Hash**: _______________
**Issues Encountered**: _______________
**Resolution**: _______________
**Rollback Required**: [ ] Yes [ ] No
**Notes**: _______________
