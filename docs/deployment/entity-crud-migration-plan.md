---
title: "Entity CRUD Migration Plan"
description: "Database migration plan for entity CRUD functionality deployment"
audience: [developers, devops]
tags: [deployment, migrations, database, entity-crud]
created: 2025-11-14
updated: 2025-11-14
category: "configuration-deployment"
status: published
related:
  - /docs/deployment/entity-crud-deployment-checklist.md
  - /docs/api/catalog-api-reference.md
---

# Entity CRUD Migration Plan

## Overview

This document outlines the database migration strategy for deploying the Entity CRUD functionality (Phases 1-7). The entity CRUD features add comprehensive Create, Read, Update, and Delete capabilities for catalog entities (CPU, GPU, Profile, PortsProfile, RamSpec, StorageProfile).

**Key Point**: The entity CRUD features do NOT require new database migrations. All necessary database schema already exists from previous migrations. This deployment only involves API endpoint changes and frontend updates.

## Migration Status

### Required Migrations

**None** - All database schema required for entity CRUD already exists.

### Recently Applied Migrations (Reference)

For context, these are recent migrations in the system (not specific to entity CRUD):

| Revision | Description | Date | Related To |
|----------|-------------|------|------------|
| 0026 | Bulk job tracking for ImportSession | 2025-11-08 | Import pipeline |
| 0025 | Partial import support for Listing | 2025-11-08 | Import pipeline |
| 0024 | CPU analytics fields | 2025-11-07 | CPU enrichment |
| 0023 | Listing pagination indexes | 2025-11-06 | Performance |
| 0022 | Import session progress tracking | 2025-11-05 | Import pipeline |

## Pre-Deployment Verification

### 1. Check Current Migration Status

```bash
# Verify current migration head
poetry run alembic current

# Expected output: 0026 (head)
```

### 2. Verify No Pending Migrations

```bash
# Check for any unapplied migrations
poetry run alembic check

# Expected output: "No new migrations found"
```

### 3. Review Migration History

```bash
# List all applied migrations
poetry run alembic history --verbose
```

## Deployment Steps

### Database Changes

**No database migrations needed for this deployment.**

The entity CRUD functionality uses existing database schema:
- `cpu` table (existing)
- `gpu` table (existing)
- `profile` table (existing)
- `ports_profile` table (existing)
- `port` table (existing, cascade delete configured)
- `ram_spec` table (existing)
- `storage_profile` table (existing)
- `listing` table (existing, for usage checks)

All necessary columns, constraints, and indexes are already in place.

### API Changes

The following API endpoints have been added:

**CPU Endpoints:**
- `PUT /v1/catalog/cpus/{cpu_id}` - Full update
- `PATCH /v1/catalog/cpus/{cpu_id}` - Partial update
- `DELETE /v1/catalog/cpus/{cpu_id}` - Delete with usage check
- `GET /v1/catalog/cpus/{cpu_id}/listings` - Get listings using CPU

**GPU Endpoints:**
- `PUT /v1/catalog/gpus/{gpu_id}` - Full update
- `PATCH /v1/catalog/gpus/{gpu_id}` - Partial update
- `DELETE /v1/catalog/gpus/{gpu_id}` - Delete with usage check
- `GET /v1/catalog/gpus/{gpu_id}/listings` - Get listings using GPU

**Profile Endpoints:**
- `PUT /v1/catalog/profiles/{profile_id}` - Full update
- `PATCH /v1/catalog/profiles/{profile_id}` - Partial update
- `DELETE /v1/catalog/profiles/{profile_id}` - Delete with usage check
- `GET /v1/catalog/profiles/{profile_id}/listings` - Get listings using profile

**PortsProfile Endpoints:**
- `PUT /v1/catalog/ports-profiles/{profile_id}` - Full update
- `PATCH /v1/catalog/ports-profiles/{profile_id}` - Partial update
- `DELETE /v1/catalog/ports-profiles/{profile_id}` - Delete with usage check
- `GET /v1/catalog/ports-profiles/{profile_id}/listings` - Get listings using profile

**RamSpec Endpoints:**
- `PUT /v1/catalog/ram-specs/{ram_spec_id}` - Full update
- `PATCH /v1/catalog/ram-specs/{ram_spec_id}` - Partial update
- `DELETE /v1/catalog/ram-specs/{ram_spec_id}` - Delete with usage check
- `GET /v1/catalog/ram-specs/{ram_spec_id}/listings` - Get listings using spec

**StorageProfile Endpoints:**
- `PUT /v1/catalog/storage-profiles/{storage_profile_id}` - Full update
- `PATCH /v1/catalog/storage-profiles/{storage_profile_id}` - Partial update
- `DELETE /v1/catalog/storage-profiles/{storage_profile_id}` - Delete with usage check
- `GET /v1/catalog/storage-profiles/{storage_profile_id}/listings` - Get listings using profile

### Frontend Changes

New features added:
- Entity detail pages with edit/delete UI
- Edit modals with optimistic updates
- Delete confirmation dialogs with usage warnings
- "View Details" links in Global Fields UI
- Toast notifications for success/error states

## Rollback Plan

### If Issues Occur

Since this deployment has **no database migrations**, rollback is straightforward:

1. **Revert Code Changes:**
   ```bash
   git checkout <previous-stable-commit>
   ```

2. **Restart Services:**
   ```bash
   # Restart API
   systemctl restart dealbrain-api
   # or for Docker
   docker-compose restart api

   # Restart web
   systemctl restart dealbrain-web
   # or for Docker
   docker-compose restart web
   ```

3. **Verify Rollback:**
   ```bash
   # Check API health
   curl http://localhost:8000/health

   # Check that old endpoints still work
   curl http://localhost:8000/v1/catalog/cpus
   ```

### Database Rollback

**Not applicable** - No migrations to rollback.

## Testing Requirements

### Pre-Deployment Testing (Staging)

1. **API Endpoint Tests:**
   - Run full test suite: `poetry run pytest tests/test_catalog_api.py -v`
   - Verify all CRUD operations work
   - Test usage check validations

2. **Frontend Tests:**
   - Test edit functionality for all entity types
   - Test delete functionality with usage warnings
   - Verify optimistic updates work correctly
   - Test accessibility (keyboard navigation, screen readers)

3. **Integration Tests:**
   - End-to-end test: Create → Edit → Delete flow
   - Test concurrent updates (optimistic locking)
   - Test error handling and rollback

### Post-Deployment Verification (Production)

1. **Smoke Tests:**
   - Run automated smoke test script (see `scripts/deployment/smoke-tests.sh`)
   - Manual verification of critical paths (see `docs/deployment/frontend-smoke-tests.md`)

2. **Monitoring:**
   - Watch API error rates in Grafana
   - Monitor database query performance
   - Check OpenTelemetry traces for errors

## Downtime Estimate

**Zero downtime** - This is a backwards-compatible deployment:
- No database schema changes
- New endpoints added (existing endpoints unchanged)
- Frontend can be deployed independently

## Risk Assessment

### Low Risk Areas
- ✅ Read endpoints (already exist, unchanged)
- ✅ Create endpoints (already exist, unchanged)
- ✅ GET detail endpoints (already exist, enhanced)

### Medium Risk Areas
- ⚠️ Update endpoints (new functionality)
- ⚠️ Delete endpoints (new functionality, includes validation)
- ⚠️ Frontend optimistic updates (new UX pattern)

### Mitigation Strategies

1. **Usage Check Validation**: All delete operations check if entity is in use before deletion (prevents data integrity issues)
2. **Unique Constraint Checks**: All update operations validate unique constraints before applying changes
3. **Optimistic Updates**: Frontend uses optimistic updates with automatic rollback on errors
4. **Comprehensive Tests**: Full test suite covers all CRUD operations and edge cases

## Success Criteria

Deployment is successful when:

- ✅ All smoke tests pass (automated script)
- ✅ Frontend smoke tests pass (manual verification)
- ✅ API health endpoint returns 200 OK
- ✅ All entity types can be edited successfully
- ✅ All entity types can be deleted (when not in use)
- ✅ Delete operations correctly prevent deletion of in-use entities
- ✅ No increase in error rates (< 1% error rate)
- ✅ No performance degradation (< 200ms p95 latency)

## Contact Information

**Deployment Owner**: DevOps Team
**Technical Lead**: Backend Team
**On-Call**: [On-call rotation contact]

## References

- [Entity CRUD Deployment Checklist](/docs/deployment/entity-crud-deployment-checklist.md)
- [Smoke Test Script](/scripts/deployment/smoke-tests.sh)
- [Frontend Smoke Tests](/docs/deployment/frontend-smoke-tests.md)
- [API Documentation](/docs/api/catalog-api-reference.md)
- [Implementation Plan](/docs/project_plans/entity-detail-views/entity-detail-views-plan.md)
