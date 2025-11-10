---
title: "Partial Data Extraction & Manual Field Population - Project Overview"
description: "Complete planning artifacts for enabling partial imports with manual completion in Deal Brain"
audience: [developers, ai-agents, pm]
tags:
  - project-overview
  - partial-imports
  - planning
created: 2025-11-08
updated: 2025-11-08
category: product-planning
status: ready-for-implementation
---

# Partial Data Extraction & Manual Field Population - Project Overview

## Project Summary

Enable partial data extraction from URL imports, allowing users to manually complete missing fields (primarily price) via a real-time modal UI. This eliminates the current all-or-nothing import behavior that results in ~30% success rate, increasing it to 80%+ while maintaining data quality.

**Expected Impact**:
- Import success rate: 30% → 80%+
- Time to import: 5-10 min → 30-60 sec
- User experience: No data loss, immediate feedback
- Marketplace support: Amazon success 20% → 70%+

---

## Planning Artifacts

This directory contains all planning artifacts for the project:

### 1. Product Requirements Document (PRD)
**File**: `PRD.md`

Complete product specification including:
- Problem statement with current pain points
- User stories and acceptance criteria
- Detailed technical requirements by phase
- Success metrics and monitoring strategy
- Edge cases and error handling
- Testing strategy
- Rollout plan with phased deployment

**Key Sections**:
- Executive Summary
- Goals & Success Metrics
- Technical Requirements (4 phases)
- Design Specifications
- Testing Strategy
- Rollout Plan

### 2. Implementation Plan
**File**: `implementation-plan.md`

Detailed phase-by-phase implementation plan with:
- 6 phases: Schema/DB, API/Services, Modal UI, Real-time Updates, Testing, Rollout
- Specific task breakdown with agent assignments
- Duration estimates and dependencies
- Acceptance criteria for each task
- Testing requirements
- Risk mitigation strategies

**Total Duration**: 8-11 days (excluding 2-week rollout)

**Agent Assignments**:
- `python-backend-engineer`: Backend implementation (Phases 1-2, 5-6)
- `data-layer-expert`: Database migrations (Phases 1, 5)
- `ui-engineer`: Frontend components (Phases 3-4, 5)

### 3. Architectural Decision Record
**File**: `ADR-001-nullable-price-strategy.md`

Documents key architectural decisions:
- **Decision 1**: Make `listings.price_usd` nullable
- **Decision 2**: Only `title` required for import
- **Decision 3**: `quality` enum for tracking completeness
- **Decision 4**: `extraction_metadata` JSON for provenance
- **Decision 5**: Defer metrics until price provided
- **Decision 6**: PATCH endpoint for completion
- **Decision 7**: HTTP polling for real-time updates
- **Decision 8**: Auto-open modal on partial import

**Includes**: Rationale, trade-offs, alternatives considered, consequences, monitoring strategy

---

## Quick Start Guide

### For Project Managers

1. **Read**: `PRD.md` - Understand business goals, success metrics, user stories
2. **Review**: Implementation Plan phases and timeline
3. **Monitor**: Track rollout phases and success metrics (Grafana dashboard)

### For Backend Engineers

1. **Read**: Implementation Plan - Phase 1 and Phase 2 tasks
2. **Assignments**:
   - `python-backend-engineer`: Tasks 1.1, 1.3, 2.1, 2.2, 2.3
   - `data-layer-expert`: Tasks 1.2, 1.4
3. **Start**: Task 1.1 (Schema updates) - no dependencies
4. **Reference**: ADR for architectural context

### For Frontend Engineers

1. **Read**: Implementation Plan - Phase 3 and Phase 4 tasks
2. **Assignment**: `ui-engineer` - All tasks in Phases 3-4
3. **Dependencies**: Wait for Phase 2 completion (API endpoints ready)
4. **Start**: Task 3.1 (PartialImportModal component)

### For QA Engineers

1. **Read**: PRD Testing Strategy section
2. **Review**: Implementation Plan - Phase 5 (Integration & Testing)
3. **Test Scenarios**: See PRD Edge Cases section
4. **E2E Tests**: Implementation Plan Task 5.1

---

## Architecture Overview

### Database Changes

**Migration 0022** - Partial Import Support:
```sql
-- Make price nullable
ALTER TABLE listing ALTER COLUMN price_usd DROP NOT NULL;

-- Add quality tracking
ALTER TABLE listing ADD COLUMN quality VARCHAR(20) NOT NULL DEFAULT 'full';

-- Add metadata
ALTER TABLE listing ADD COLUMN extraction_metadata JSON NOT NULL DEFAULT '{}';
ALTER TABLE listing ADD COLUMN missing_fields JSON NOT NULL DEFAULT '[]';
```

**Migration 0023** - Bulk Job Tracking:
```sql
ALTER TABLE import_session ADD COLUMN bulk_job_id VARCHAR(36);
ALTER TABLE import_session ADD COLUMN quality VARCHAR(20);
ALTER TABLE import_session ADD COLUMN listing_id INTEGER REFERENCES listing(id);
ALTER TABLE import_session ADD COLUMN completed_at TIMESTAMP WITH TIME ZONE;
```

### API Changes

**New Endpoints**:
1. `PATCH /api/v1/listings/{listing_id}/complete` - Complete partial import
2. `GET /api/v1/ingest/bulk/{bulk_job_id}/status` - Poll import status

**Updated Endpoints**:
- `POST /api/v1/ingest` - Returns `quality` field in response
- `POST /api/v1/ingest/bulk` - Creates bulk_job_id for tracking

### Frontend Components

**New Components**:
1. `PartialImportModal` - Manual field completion UI
2. `BulkImportProgress` - Real-time progress indicator
3. `ImportToasts` - Toast notifications for import results

**New Hooks**:
1. `useImportStatus` - HTTP polling for bulk import status
2. `usePartialImportCompletion` - Modal state management

---

## Implementation Phases

### Phase 1: Backend - Schema & Database (2-3 days)
- Update `NormalizedListingSchema` to support partial imports
- Database migration: nullable price, quality tracking
- Update adapter validation to allow missing price
- Add bulk job tracking to ImportSession

### Phase 2: Backend - API & Services (2-3 days)
- Update `ListingsService` to handle partial imports
- Create PATCH endpoint for completion
- Create GET endpoint for bulk status polling
- Update ingestion service to track quality

### Phase 3: Frontend - Manual Population Modal (2-3 days)
- Build `PartialImportModal` component
- Integrate modal with import flow
- Auto-open on partial import completion
- Form validation and submission

### Phase 4: Frontend - Real-Time UI Updates (2-3 days)
- Create polling hook for import status
- Build progress indicator component
- Implement toast notifications
- Real-time grid updates

### Phase 5: Integration & Testing (1-2 days)
- End-to-end testing across all flows
- Migration validation in staging
- Performance testing (100+ URL bulk import)
- Accessibility audit

### Phase 6: Rollout & Monitoring (2 weeks)
- Feature flag implementation
- Internal testing (dev/staging)
- Beta rollout (10% users)
- Gradual rollout (25% → 50% → 100%)
- Monitoring dashboard and alerts

---

## Success Criteria

### Quantitative Metrics

| Metric | Current | Target | Measurement Period |
|--------|---------|--------|-------------------|
| Import Success Rate | ~30% | 80%+ | 7-day rolling |
| Partial Import Rate | 0% | 15-25% | Of successful imports |
| Manual Completion Rate | N/A | 70%+ | Of partial imports |
| Time to Import | 5-10 min | 30-60 sec | Average per listing |
| Amazon Success Rate | ~20% | 70%+ | 7-day rolling |
| Data Quality Score | ~85% | 90%+ | Validation pass rate |

### Qualitative Goals

- Users report improved import experience (survey score >4/5)
- Support tickets for import failures reduced by 50%
- Feature adoption: 80%+ of users successfully use partial imports
- Code quality: All tests passing, <5% bug rate in first 2 weeks

---

## Risk Assessment

### High Risk
- **Database Migration Irreversibility**: Cannot downgrade if partial imports exist
  - **Mitigation**: Feature flag allows disabling without downgrade, test in staging first

### Medium Risk
- **User Abandonment**: Users may close modal without completing
  - **Mitigation**: Auto-open modal, clear UX, "Complete later" option visible

### Low Risk
- **Polling Performance**: 2-second polling may create load
  - **Mitigation**: Connection pooling, stop polling when done, future WebSocket upgrade

---

## Monitoring & Observability

### Prometheus Metrics (to be added)

```python
import_attempts_total{marketplace, quality}  # Counter
import_success_rate{marketplace}             # Gauge
partial_import_completion_rate               # Gauge
import_duration_seconds{marketplace, quality} # Histogram
```

### Grafana Dashboard (to be created)

**Panels**:
1. Import success rate trend (7-day rolling average)
2. Partial import rate by marketplace
3. Manual completion funnel (partial → completed → abandoned)
4. Time to completion distribution (P50, P95, P99)

### Alerts

- **Critical**: Import success rate drops below 60%
- **Warning**: Partial completion rate below 50%
- **Info**: Partial import rate exceeds 30% (adapter issues)

---

## Future Enhancements

### Post-MVP Features (Phase 5+)

**Bulk Manual Population**:
- Complete multiple partial imports at once
- Table view with inline editing
- Bulk submit

**ML-Based Price Estimation**:
- Suggest prices based on similar listings
- Pre-fill price input with median
- Learn from user corrections

**Marketplace Native APIs**:
- Amazon Product Advertising API
- Etsy Open API
- 100% extraction success for supported sources

**Advanced Quality Tracking**:
- Quality score (0-100) based on field completeness
- "Verify extracted data" workflow
- Data quality trending dashboard

---

## Related Documentation

- **Current Ingestion System**: Architecture already supports optional price in schema
- **Adapter Implementation**: `apps/api/dealbrain_api/adapters/`
- **Database Models**: `apps/api/dealbrain_api/models/core.py`
- **Frontend Components**: `apps/web/components/imports/`
- **API Schemas**: `packages/core/dealbrain_core/schemas/ingestion.py`

---

## Questions & Clarifications

**Q: What happens to partial imports if user never completes them?**
A: Listings persist in database with `quality="partial"`. Dashboard shows "Incomplete Imports" section (future enhancement). Admin can clean up abandoned partials after 30 days.

**Q: Can users edit price later even for complete imports?**
A: Yes - existing listing edit flow allows price updates. This feature specifically handles *initial* import completion.

**Q: What if adapter extracts invalid price (e.g., "£299.99")?**
A: Adapter attempts to parse and convert to USD Decimal. If parsing fails, sets `price=None` and creates partial import. User manually enters USD price.

**Q: How do we prevent duplicate partial imports?**
A: Existing deduplication logic runs on `dedup_hash` (title + vendor_item_id). Partial imports deduplicate same as complete imports.

**Q: Can we support other missing fields (not just price)?**
A: Yes - architecture designed for extensibility. `missing_fields` is a list, `extraction_metadata` tracks any field. Future enhancement: support missing manufacturer, condition, etc.

---

## Contact & Support

**Lead Architect**: Review ADR and implementation plan
**Project Manager**: Track phases and success metrics
**Backend Team**: See Phase 1-2 tasks in implementation plan
**Frontend Team**: See Phase 3-4 tasks in implementation plan
**QA Team**: See Phase 5 testing requirements

**Start Date**: TBD (awaiting approval)
**Target Completion**: 8-11 days + 2-week rollout
**Status**: Ready for implementation
