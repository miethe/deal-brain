---
title: "Deployment Documentation Index"
description: "Index of all deployment-related documentation and scripts"
audience: [devops, developers]
tags: [deployment, documentation, index]
created: 2025-11-14
updated: 2025-11-14
category: "configuration-deployment"
status: published
---

# Deployment Documentation

This directory contains deployment plans, checklists, and scripts for production deployments.

## Quick Links

### Entity CRUD Deployment (Phase 9)

**Primary Documents**:
- [Migration Plan](./entity-crud-migration-plan.md) - Database migration strategy and rollback plan
- [Deployment Checklist](./entity-crud-deployment-checklist.md) - Complete step-by-step deployment guide
- [Frontend Smoke Tests](./frontend-smoke-tests.md) - Manual UI testing checklist
- [Communication Plan](./communication-plan.md) - Stakeholder communication templates

**Scripts**:
- [Automated Smoke Tests](../../scripts/deployment/smoke-tests.sh) - Automated API smoke tests

---

## Entity CRUD Deployment Overview

**Deployment Type**: Zero-downtime, backwards-compatible
**Database Changes**: None (no new migrations)
**Estimated Duration**: 30-45 minutes

### What's Being Deployed

Entity CRUD functionality (Phases 1-7):
- Edit capabilities for all catalog entities (CPU, GPU, Profile, PortsProfile, RamSpec, StorageProfile)
- Delete functionality with safety checks for in-use entities
- Enhanced detail views with usage information
- Improved user experience with optimistic updates

### Key Features

**API Endpoints Added**:
- `PUT /v1/catalog/{entity}/{id}` - Full update
- `PATCH /v1/catalog/{entity}/{id}` - Partial update
- `DELETE /v1/catalog/{entity}/{id}` - Delete with validation
- `GET /v1/catalog/{entity}/{id}/listings` - Usage information

**Frontend Components Added**:
- Entity detail pages with edit/delete UI
- Edit modals with form validation
- Delete confirmation dialogs with usage warnings
- Toast notifications for success/error states
- "View Details" links in Global Fields UI

### Pre-Deployment Requirements

1. **Code Ready**:
   - ✅ All Phase 8 tests passing
   - ✅ Code reviewed and merged
   - ✅ No database migrations needed

2. **Environment Ready**:
   - ✅ Staging environment tested
   - ✅ Database backup completed
   - ✅ Monitoring dashboards accessible

3. **Team Ready**:
   - ✅ Deployment checklist reviewed
   - ✅ Rollback plan understood
   - ✅ Support team trained
   - ✅ Stakeholders notified

---

## Deployment Process

### Step 1: Pre-Deployment

1. Review [Migration Plan](./entity-crud-migration-plan.md)
2. Complete pre-deployment checklist items
3. Verify staging environment healthy
4. Send stakeholder notifications (see [Communication Plan](./communication-plan.md))

### Step 2: Deployment

Follow the complete [Deployment Checklist](./entity-crud-deployment-checklist.md):

1. **Backend Deployment**:
   - Pull latest code
   - Install dependencies
   - Run migrations (no-op for this deployment)
   - Restart API service
   - Verify health

2. **Frontend Deployment**:
   - Pull latest code
   - Install dependencies
   - Build production bundle
   - Deploy static assets
   - Restart web service
   - Verify health

### Step 3: Post-Deployment Verification

1. **Automated Tests**:
   ```bash
   cd /home/user/deal-brain
   API_URL=https://api.yourdomain.com ./scripts/deployment/smoke-tests.sh
   ```

2. **Manual Tests**:
   - Complete [Frontend Smoke Tests](./frontend-smoke-tests.md)
   - Verify critical user paths
   - Check browser compatibility

3. **Monitoring**:
   - Check API error rates (< 1%)
   - Check performance metrics (< 200ms p95)
   - Verify no alerts firing

### Step 4: Post-Deployment Communication

Follow [Communication Plan](./communication-plan.md):
- Send deployment success notification (internal)
- Send user announcement (external)
- Monitor user feedback for 48 hours
- Send follow-up feedback request

---

## Rollback Procedure

If critical issues are detected:

1. **Initiate Rollback** (see [Deployment Checklist](./entity-crud-deployment-checklist.md#rollback-procedure))
2. **Rollback API**: Checkout previous commit, restart service
3. **Rollback Web**: Checkout previous commit, rebuild, restart service
4. **Database**: No rollback needed (no migrations)
5. **Verify**: Run smoke tests on rolled-back version
6. **Communicate**: Notify stakeholders (see [Communication Plan](./communication-plan.md#rollback-communication))

**Rollback Criteria**:
- API error rate > 10%
- Critical smoke tests failing
- Data integrity issues
- Service degradation detected

---

## Smoke Tests

### Automated API Tests

**Location**: `/scripts/deployment/smoke-tests.sh`

**Usage**:
```bash
# Local testing
./scripts/deployment/smoke-tests.sh

# Production testing
API_URL=https://api.yourdomain.com ./scripts/deployment/smoke-tests.sh

# Verbose output
VERBOSE=1 API_URL=https://api.yourdomain.com ./scripts/deployment/smoke-tests.sh

# Skip cleanup (for debugging)
CLEANUP=0 ./scripts/deployment/smoke-tests.sh
```

**Test Coverage**:
- API health check
- CPU CRUD operations
- GPU CRUD operations
- Profile CRUD operations
- PortsProfile CRUD operations
- RamSpec CRUD operations
- StorageProfile CRUD operations
- Fields Data API

**Expected Duration**: ~30 seconds

### Manual Frontend Tests

**Location**: [Frontend Smoke Tests](./frontend-smoke-tests.md)

**Test Categories**:
- Critical user paths (11 tests)
- Browser compatibility (4 browsers)
- Responsive design (3 screen sizes)
- Accessibility (keyboard, screen reader)
- Performance (page load, modal responsiveness)
- Error handling (network errors)

**Expected Duration**: 15-20 minutes

---

## Monitoring & Alerts

### Key Metrics to Watch

**API Performance**:
- Error rate: < 1% (alert if > 5%)
- Latency p95: < 200ms (alert if > 1000ms)
- Request rate: Monitor for anomalies

**Database**:
- Query performance: No slow queries (> 1s)
- Connection pool: < 80% utilization
- Lock contention: Monitor for deadlocks

**Frontend**:
- First contentful paint: < 1.5s
- Time to interactive: < 3s
- JavaScript errors: < 0.1% of page loads

### Dashboards

**Grafana**:
- API Overview Dashboard
- Database Performance Dashboard
- Frontend Performance Dashboard
- Entity CRUD Specific Dashboard (if created)

**Prometheus**:
- HTTP request rates: `rate(http_requests_total[5m])`
- Error rates: `rate(http_requests_total{status=~"5.."}[5m])`
- Latency: `histogram_quantile(0.95, http_request_duration_seconds_bucket)`

---

## Support Resources

### User Documentation

- [Entity Management User Guide](../guides/entity-management-user-guide.md) (if exists)
- [API Documentation](../api/catalog-api-reference.md)
- [FAQ](../user-guide/faq.md) (if exists)

### Troubleshooting

**Common Issues**:

1. **Edit not saving**:
   - Check validation errors in form
   - Verify API connectivity
   - Check browser console for errors

2. **Delete blocked**:
   - Entity is in use by listings
   - Check "Used In" section on detail page
   - Verify foreign key relationships

3. **Performance degradation**:
   - Check database query performance
   - Verify indexes are being used
   - Check connection pool utilization

### Contact Information

| Role | Contact | Method |
|------|---------|--------|
| Deployment Lead | [Name] | [Email/Slack] |
| DevOps On-Call | [Name] | [Phone/PagerDuty] |
| Engineering Lead | [Name] | [Email/Slack] |
| Support Team | [Email] | [support@domain.com] |

---

## Success Criteria

Deployment is successful when:

- ✅ All automated smoke tests passing
- ✅ All manual smoke tests passing
- ✅ API error rate < 1%
- ✅ No critical alerts firing
- ✅ Performance metrics within acceptable ranges
- ✅ No data integrity issues
- ✅ All critical user paths functional
- ✅ Positive user feedback (> 4/5 stars)

---

## Related Documentation

- [Implementation Plan](../project_plans/entity-detail-views/entity-detail-views-plan.md)
- [Architecture Documentation](../architecture/)
- [API Reference](../api/)
- [Testing Documentation](../testing/)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-14 | Claude | Initial deployment documentation for Entity CRUD Phase 9 |

---

## Feedback & Improvements

Have suggestions for improving this deployment process? Please:
- Open an issue: [LINK]
- Submit a PR: [LINK]
- Contact the DevOps team: [EMAIL]

We continuously improve our deployment practices based on lessons learned.
