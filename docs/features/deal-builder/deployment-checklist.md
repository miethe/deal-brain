---
title: "Deal Builder - Deployment Checklist"
description: "Production deployment checklist for Deal Builder including pre-deployment validation, deployment steps, rollback plan, and monitoring"
audience: [developers, devops, pm]
tags: [deployment, production, deal-builder, checklist, monitoring]
created: 2025-11-14
updated: 2025-11-14
category: "configuration-deployment"
status: published
related:
  - /docs/features/deal-builder/testing-guide.md
  - /docs/features/deal-builder/accessibility.md
  - /docs/features/deal-builder/mobile-optimization.md
---

# Deal Builder - Deployment Checklist

## Pre-Deployment Validation

### Backend
- [ ] All migrations reviewed: `poetry run alembic check`
- [ ] Migration 0027 applied in staging: `poetry run alembic upgrade head`
- [ ] All backend tests passing: `poetry run pytest apps/api/tests/ -v`
- [ ] Coverage >85%: `poetry run pytest apps/api/tests/ --cov=dealbrain_api --cov-report=html`
- [ ] No type errors: `poetry run mypy apps/api/dealbrain_api`
- [ ] Linting clean: `poetry run ruff check apps/api`
- [ ] No security vulnerabilities: `poetry run safety check`

### Frontend
- [ ] TypeScript compilation: `pnpm --filter "./apps/web" run typecheck`
- [ ] Build successful: `pnpm --filter "./apps/web" run build`
- [ ] Linting clean: `pnpm --filter "./apps/web" run lint`
- [ ] No console errors in production build
- [ ] No dependency vulnerabilities: `pnpm audit`

### Environment Variables
- [ ] `NEXT_PUBLIC_API_URL` set correctly (production API URL)
- [ ] `DATABASE_URL` configured with production credentials
- [ ] `REDIS_URL` connection string set
- [ ] `OTEL_EXPORTER_OTLP_ENDPOINT` configured (observability)
- [ ] `SENTRY_DSN` set (if using Sentry)
- [ ] All secrets stored securely (not in code)

### Database
- [ ] Migration 0027 tested in staging environment
- [ ] `saved_builds` table created successfully
- [ ] Indexes created: `ix_saved_builds_user_id`, `ix_saved_builds_share_token`
- [ ] Unique constraint on `share_token` verified
- [ ] Database backup completed before migration

### Performance
- [ ] Lighthouse score >90 (performance)
- [ ] Lighthouse score >95 (accessibility)
- [ ] API response times validated:
  - [ ] `POST /builder/calculate` <300ms
  - [ ] `POST /builder/builds` <500ms
  - [ ] `GET /builder/builds/{id}` <200ms
  - [ ] `GET /builder/shared/{token}` <200ms
- [ ] Database indexes tested (query performance)
- [ ] Load testing completed (if applicable)

### Security
- [ ] SQL injection protection verified (Parameterized queries)
- [ ] XSS protection verified (React escapes by default)
- [ ] CSRF protection enabled (if using cookies)
- [ ] Rate limiting configured on API endpoints
- [ ] CORS configured correctly
- [ ] HTTPS enforced in production
- [ ] Sensitive data not logged (prices, user data)

## Deployment Steps

### 1. Pre-Deployment Communication
- [ ] Notify team of deployment window
- [ ] Create deployment ticket/issue
- [ ] Schedule deployment during low-traffic period
- [ ] Prepare rollback plan

### 2. Database Migration
```bash
# Connect to production database (via bastion/VPN if required)
# ALWAYS backup database first
pg_dump -h <prod-host> -U <user> -d dealbrain > backup_$(date +%Y%m%d_%H%M%S).sql

# Apply migration
poetry run alembic upgrade head

# Verify table created
psql -h <prod-host> -U <user> -d dealbrain -c "\d saved_builds"

# Verify indexes created
psql -h <prod-host> -U <user> -d dealbrain -c "\di saved_builds*"
```

- [ ] Database backup completed
- [ ] Migration applied successfully
- [ ] Table structure verified
- [ ] Indexes verified

### 3. Backend Deployment

**Docker Deployment**:
```bash
# Build Docker image
docker build -t deal-brain-api:v1.0.0 -f infra/Dockerfile.api .

# Tag for registry
docker tag deal-brain-api:v1.0.0 <registry>/deal-brain-api:v1.0.0
docker tag deal-brain-api:v1.0.0 <registry>/deal-brain-api:latest

# Push to registry
docker push <registry>/deal-brain-api:v1.0.0
docker push <registry>/deal-brain-api:latest

# Deploy to production (Kubernetes example)
kubectl set image deployment/deal-brain-api api=<registry>/deal-brain-api:v1.0.0
kubectl rollout status deployment/deal-brain-api

# Verify health
curl https://api.dealbrain.com/health
```

**Kubernetes Deployment** (if applicable):
```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deal-brain-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: <registry>/deal-brain-api:v1.0.0
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
```

- [ ] Docker image built
- [ ] Image pushed to registry
- [ ] Deployment updated
- [ ] Pods healthy
- [ ] Health check passing

### 4. Frontend Deployment

**Next.js Build**:
```bash
cd apps/web

# Set production environment variables
export NEXT_PUBLIC_API_URL=https://api.dealbrain.com

# Build production bundle
pnpm run build

# Output size check
ls -lh .next/static/chunks
# Target: Main bundle <500KB

# Preview build locally (optional)
pnpm start
```

**Vercel Deployment** (recommended):
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to production
vercel --prod

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL production
```

**Docker Deployment** (alternative):
```bash
# Build Docker image
docker build -t deal-brain-web:v1.0.0 -f infra/Dockerfile.web .

# Deploy similar to backend
```

- [ ] Production build completed
- [ ] Bundle size acceptable (<500KB)
- [ ] Environment variables set
- [ ] Deployment successful
- [ ] Site accessible

### 5. Post-Deployment Validation
- [ ] Navigate to `https://dealbrain.com/builder` - page loads
- [ ] Select CPU component - valuation appears
- [ ] Add GPU component - valuation updates
- [ ] Save build - success toast appears
- [ ] Load saved build - components repopulate
- [ ] Share build - shareable URL works
- [ ] Check browser console - no errors
- [ ] Check application logs - no errors
- [ ] Monitor API performance - response times acceptable
- [ ] Monitor error rates - <1% error rate

### 6. Smoke Tests (Production)
Run manual smoke tests on production:

**Test 1: Create and Calculate**:
1. Go to `/builder`
2. Click "Add CPU"
3. Select any CPU
4. Verify valuation appears
5. Verify no console errors

**Test 2: Save Build**:
1. Create build with CPU + GPU
2. Click "Save Build"
3. Enter name: "Production Test"
4. Save
5. Verify toast notification
6. Verify build appears in saved builds

**Test 3: Share Build**:
1. Click "Share" on saved build
2. Copy URL
3. Open in incognito window
4. Verify build displays
5. Click "Build Your Own"
6. Verify redirects to builder

**Test 4: Mobile**:
1. Open on mobile device (or DevTools mobile)
2. Navigate to `/builder`
3. Add component
4. Verify layout responsive
5. Save build
6. Verify modals full-screen

- [ ] All smoke tests passed
- [ ] Mobile experience validated

## Rollback Plan

If deployment fails or critical issues discovered:

### 1. Immediate Rollback (Application)
```bash
# Kubernetes rollback
kubectl rollout undo deployment/deal-brain-api
kubectl rollout undo deployment/deal-brain-web

# Docker rollback (manual)
docker pull <registry>/deal-brain-api:v0.9.0
docker pull <registry>/deal-brain-web:v0.9.0
# Restart containers with previous version

# Vercel rollback
vercel rollback
```

### 2. Database Rollback (If Required)
```bash
# Rollback migration (ONLY if absolutely necessary)
poetry run alembic downgrade -1

# Verify rollback
psql -c "SELECT version_num FROM alembic_version"
```

**WARNING**: Database rollback may cause data loss. Only rollback if:
- Migration caused critical errors
- No user data created in new table
- Team agrees to rollback

### 3. Verify Rollback
- [ ] Application running previous version
- [ ] Existing functionality working
- [ ] Error rates normalized
- [ ] No data loss occurred

### 4. Incident Report
If rollback required:
1. Document what went wrong
2. Root cause analysis
3. Create fix PR
4. Re-test in staging
5. Schedule new deployment

## Monitoring

### Metrics to Track

**Application Metrics**:
- Builder page views (`/builder` route)
- Builds created (POST /builder/builds count)
- Builds saved (save success rate)
- Shared builds accessed (GET /builder/shared/{token} count)
- Component selections (by type: CPU, GPU, RAM, Storage)

**Performance Metrics**:
- API response times:
  - `POST /builder/calculate` (p50, p95, p99)
  - `POST /builder/builds` (p50, p95, p99)
  - `GET /builder/builds` (p50, p95, p99)
  - `GET /builder/shared/{token}` (p50, p95, p99)
- Database query times
- Frontend page load times (Core Web Vitals)

**Error Metrics**:
- API error rate (overall and by endpoint)
- 4xx errors (client errors)
- 5xx errors (server errors)
- Database connection errors
- Frontend JavaScript errors

### Alerts to Configure

**Critical Alerts** (PagerDuty/Slack):
- API error rate >5% (5 minutes)
- Database connection failures
- Application down (health check failing)
- P99 response time >2s

**Warning Alerts** (Slack/Email):
- API error rate >1% (15 minutes)
- P95 response time >500ms (15 minutes)
- Build save failures >5% (30 minutes)
- Unusual traffic spike (>3x normal)

### Monitoring Tools

**Application Performance Monitoring (APM)**:
- Sentry (errors, performance)
- DataDog (metrics, traces, logs)
- New Relic (APM)
- Prometheus + Grafana (already configured)

**Log Aggregation**:
- CloudWatch Logs (AWS)
- Stackdriver (GCP)
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Grafana Loki (with Prometheus)

**Uptime Monitoring**:
- UptimeRobot
- Pingdom
- StatusPage.io (status page for users)

### Dashboards to Create

**Deal Builder Dashboard**:
- Builds created (time series)
- Save success rate
- Share link clicks
- Component selection breakdown (pie chart)
- Active users (DAU, MAU)

**Performance Dashboard**:
- API response times (p50, p95, p99)
- Error rate (%)
- Request volume (requests/sec)
- Database query performance

**Infrastructure Dashboard**:
- CPU usage
- Memory usage
- Database connections
- Redis cache hit rate

## Feature Flags (Future)

Consider implementing feature flags for gradual rollout:

```javascript
// Example: LaunchDarkly, Flagsmith, or custom
const isBuilderEnabled = featureFlags.get('deal-builder-v1')

if (isBuilderEnabled) {
  // Show builder feature
} else {
  // Show "Coming Soon" message
}
```

**Recommended Flags**:
- `deal-builder-v1` - Master toggle for entire feature
- `builder-share-enabled` - Share functionality toggle
- `builder-save-enabled` - Save functionality toggle
- `builder-real-time-calc` - Real-time calculation on/off

**Rollout Strategy**:
1. Deploy to 5% of users
2. Monitor metrics for 24 hours
3. Increase to 25% if stable
4. Increase to 50% after 48 hours
5. Full rollout after 1 week

## Documentation

- [ ] README updated with Deal Builder feature
- [ ] API documentation updated (`/docs` endpoint)
- [ ] User guide created (if needed)
- [ ] Internal team training completed
- [ ] Changelog updated with new features

## Success Criteria

### Technical Success
- [ ] All tests passing (backend >90%, frontend manual)
- [ ] No production errors >1% error rate
- [ ] Performance targets met (<300ms calculate, <500ms save)
- [ ] Accessibility validated (WCAG AA, Lighthouse >95)
- [ ] Mobile responsive (tested on iOS/Android)

### Product Success (Tracked Post-Launch)
- [ ] Feature adoption >30% MAU (monthly active users)
- [ ] Build save rate >60% (of users who build)
- [ ] Share link clicks >10% (of saved builds)
- [ ] No critical bugs reported (P0/P1)
- [ ] Positive user feedback (surveys, support tickets)

### Deployment Success
- [ ] Zero downtime deployment
- [ ] No rollback required
- [ ] All smoke tests passed
- [ ] Monitoring configured
- [ ] Team notified of successful deployment

## Post-Deployment Tasks

### Week 1
- [ ] Monitor error rates daily
- [ ] Review user feedback
- [ ] Check performance metrics
- [ ] Verify no data issues
- [ ] Address any minor bugs

### Week 2
- [ ] Analyze adoption metrics
- [ ] Review Sentry errors
- [ ] Optimize slow queries (if any)
- [ ] Plan Phase 2 features
- [ ] Gather user feedback

### Month 1
- [ ] Product metrics review
- [ ] Performance optimization
- [ ] User feedback session
- [ ] Plan improvements
- [ ] Update roadmap

## Contact Information

**Deployment Lead**: _____________________
**On-Call Engineer**: _____________________
**Product Owner**: _____________________
**Deployment Date**: _____________________
**Deployment Time**: _____________________ (UTC)

---

**Last Updated**: 2025-11-14
**Deployment Status**: Ready for Production
**Rollback Plan**: Tested and Documented
**Monitoring**: Configured

## Deployment Sign-Off

- [ ] Engineering Lead approved
- [ ] Product Manager approved
- [ ] QA validated
- [ ] DevOps reviewed
- [ ] Security reviewed (if required)
- [ ] All checklist items completed

**Deployed By**: _____________________
**Deployment Date**: _____________________
**Deployment Notes**: _____________________
