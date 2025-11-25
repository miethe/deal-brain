---
title: "Implementation Plan: Partial Data Extraction & Manual Field Population"
description: "Phased implementation overview with phase-specific documentation and agent assignments"
audience: [ai-agents, developers]
tags:
  - implementation
  - planning
  - agent-assignments
  - partial-imports
created: 2025-11-08
updated: 2025-11-08
category: product-planning
status: accepted
related:
  - /docs/project_plans/import-partial-data-manual-population/PRD.md
  - /docs/project_plans/import-partial-data-manual-population/ADR-001-nullable-price-strategy.md
---

# Implementation Plan: Partial Data Extraction & Manual Field Population

## Executive Summary

This document provides a high-level implementation overview for enabling partial data extraction and manual field population in the Deal Brain URL import system. The feature allows users to import listings with incomplete data (e.g., missing price), and then complete the import later through a modal interface.

**Total Estimated Duration**: 6-8 days (development only, no phased rollout)

**Architecture**: Immediate feature deployment upon completion (no rollout gates)

---

## Quick Links to Phase Documentation

Each phase has detailed task breakdowns, acceptance criteria, and testing requirements:

1. **[Phase 1: Backend Schema & Database](/docs/project_plans/import-partial-data-manual-population/phase-1-backend-schema-database.md)** (2-3 days)
   - Update NormalizedListingSchema to accept nullable prices
   - Apply database migrations for quality tracking
   - Update adapters to gracefully handle extraction failures

2. **[Phase 2: Backend API & Services](/docs/project_plans/import-partial-data-manual-population/phase-2-backend-api-services.md)** (2-3 days)
   - Update ListingsService to support partial listings
   - Create completion API endpoint
   - Create bulk import status polling endpoint

3. **[Phase 3: Frontend - Manual Population Modal](/docs/project_plans/import-partial-data-manual-population/phase-3-frontend-manual-population.md)** (2-3 days)
   - Build accessible PartialImportModal component
   - Integrate modal into import flow
   - Handle completion and error states

4. **[Phase 4: Frontend - Real-Time UI Updates](/docs/project_plans/import-partial-data-manual-population/phase-4-frontend-realtime-updates.md)** (2-3 days)
   - Create useImportPolling hook for real-time status
   - Build BulkImportProgress component
   - Implement toast notifications

5. **[Phase 5: Integration & Testing](/docs/project_plans/import-partial-data-manual-population/phase-5-integration-testing.md)** (1-2 days)
   - End-to-end testing across all phases
   - Database migration validation
   - Monitoring setup and performance verification

---

## Feature Overview

### What It Does

Users can now import listings from URLs even when data extraction is incomplete:

1. **Partial Import**: System extracts available data (title, specs, condition)
2. **Quality Tracking**: Listing marked as "partial" with missing fields list
3. **Manual Completion**: Modal prompts user to provide missing data (e.g., price)
4. **Metrics Calculation**: Once complete, system calculates valuation and scoring
5. **Real-Time Status**: Bulk import dashboard shows live progress for multiple URLs

### Key Flows

**Single URL Import (Partial)**
```
User → Adapter extracts data → No price extracted
→ Listing created with quality="partial"
→ Modal shows: "Please enter price"
→ User enters price → API completes listing
→ Metrics calculated → Listing ready
```

**Bulk URL Import (Multiple Partial)**
```
User uploads 50 URLs → Status polls every 2s
→ Per-URL progress shown: queued → running → complete
→ 20 extracted fully, 30 are partial
→ Modal appears for 1st partial → User completes
→ Modal appears for 2nd partial → User completes
→ ... repeat for all partial imports
```

---

## Dependencies & Critical Path

### Sequencing

```
Phase 1 (Schema & DB)
        ↓
Phase 2 (API & Services)
        ↓
Phase 3 & 4 (Frontend)  ← Can run in parallel
        ↓
Phase 5 (Testing & Validation)
```

### Key Dependencies

- **Phase 2 depends on Phase 1**: API needs database changes applied
- **Phase 3 depends on Phase 2**: Modal needs completion API endpoint
- **Phase 4 depends on Phase 2**: Polling hook needs status endpoint
- **Phase 3 & 4 parallel**: Modal and polling independent (both use Phase 2 APIs)
- **Phase 5 independent**: Can validate earlier phases incrementally

---

## Agent Assignments

| Agent | Responsibilities | Phases |
|-------|------------------|--------|
| **python-backend-engineer** | Schema updates, adapters, services, API endpoints, metrics | 1, 2, 5 |
| **data-layer-expert** | Database migrations, model updates, schema validation | 1, 5 |
| **ui-engineer** | React components, hooks, modal, polling, notifications | 3, 4, 5 |

**Lead Coordinator**: python-backend-engineer (overall implementation)

---

## Success Criteria by Phase

### Phase 1: Backend Schema & Database
- Schema accepts `price=None` with title required
- Migrations applied cleanly, no data loss
- Adapters gracefully handle missing prices
- All tests pass (unit + integration)

### Phase 2: Backend API & Services
- ListingsService creates and completes partial listings
- Completion API endpoint functional and validated
- Bulk status endpoint returns correct aggregations
- All tests pass (unit + integration + API)

### Phase 3: Frontend - Manual Population Modal
- Modal renders extracted data and allows price entry
- API integration works end-to-end
- Keyboard accessible, WCAG AA compliant
- All tests pass (unit + integration)

### Phase 4: Frontend - Real-Time UI Updates
- Polling hook tracks bulk import status correctly
- Progress component updates in real-time
- Notifications appear for key events
- All tests pass (unit + integration)

### Phase 5: Integration & Testing
- All E2E tests pass
- Migrations validated in staging environment
- Performance benchmarks acceptable
- Monitoring setup complete and working

---

## Technical Decisions

See [ADR-001: Nullable Price Strategy](/docs/project_plans/import-partial-data-manual-population/ADR-001-nullable-price-strategy.md) for detailed architectural decisions including:

- Why nullable price in database (vs. other approaches)
- Quality tracking strategy
- Data extraction metadata design
- Migration rollback strategy

---

## Risk Mitigation

### Database Migration Risk
- **Risk**: Making price_usd nullable could break existing queries
- **Mitigation**: Add NULL checks to all price-dependent queries, test extensively in staging
- **Rollback**: Feature flag allows disabling without migration downgrade

### Data Quality Risk
- **Risk**: Users enter invalid prices or incomplete data
- **Mitigation**: Frontend validation (positive number), backend validation (Pydantic), manual review dashboard (future)

### Performance Risk
- **Risk**: Polling every 2s could create load
- **Mitigation**: Use connection pooling, consider WebSocket for high-volume (future)

### Integration Risk
- **Risk**: Modal and polling not properly synchronized
- **Mitigation**: Use custom window events for loose coupling, comprehensive E2E tests

---

## Rollback Plan

If issues discovered after deployment:

1. **Application Level**: Return 400 error if price=None (disable feature at code level)
2. **Data Level**: Keep migrations applied (data remains, feature disabled)
3. **Communication**: Notify users that partial imports temporarily disabled

**Note**: We are NOT implementing feature flags or phased rollout. This is a complete feature deployment immediately upon Phase 5 completion.

---

## Monitoring & Observability

Post-deployment monitoring:

**Prometheus Metrics**:
- `import_attempts_total` - Count by marketplace and quality
- `import_results_total` - Success/failure rates
- `partial_import_completions_total` - User completions
- `import_duration_seconds` - Performance tracking

**Grafana Dashboard**:
- Import success rate (full + partial)
- Partial completion rate
- Average import duration by marketplace
- Pending partial imports count

**Alerts**:
- High failure rate (>10% failures)
- Many pending partial imports (>100)
- Slow processing (95th percentile >30s)

---

## Post-Implementation Tasks

**Not in this plan (future enhancements)**:
- Feature flags for gradual rollout
- Phased user rollout (5% → 25% → 50% → 100%)
- Beta testing phase
- WebSocket support for real-time polling
- Partial import review dashboard (admin tool)
- Bulk completion API (complete multiple at once)
- Auto-fill suggestions based on market data

---

## Implementation Checklist

### Before Starting
- [ ] Read PRD and ADR documents
- [ ] Review existing import system
- [ ] Understand current adapter architecture
- [ ] Coordinate with team on schedule

### During Development
- [ ] Create feature branch from main
- [ ] Complete each phase in order (can run 3 & 4 in parallel)
- [ ] Review and merge each phase when complete
- [ ] Document any deviations from plan

### Before Production Deployment
- [ ] All tests passing
- [ ] Migrations validated in staging
- [ ] Performance benchmarks acceptable
- [ ] Monitoring configured and alerting
- [ ] Rollback plan documented and tested
- [ ] Code review complete

---

## File Structure

```
docs/project_plans/import-partial-data-manual-population/
├── implementation-plan.md                    # This file (overview & links)
├── phase-1-backend-schema-database.md        # Task breakdowns
├── phase-2-backend-api-services.md           # Task breakdowns
├── phase-3-frontend-manual-population.md     # Task breakdowns
├── phase-4-frontend-realtime-updates.md      # Task breakdowns
├── phase-5-integration-testing.md            # Task breakdowns
├── PRD.md                                    # Product requirements
└── ADR-001-nullable-price-strategy.md        # Architecture decisions
```

Each phase document contains:
- Overview and objectives
- Detailed tasks with code examples
- Acceptance criteria
- Unit and integration tests
- Testing strategy

---

## Key Contacts & Resources

**Questions?**
- Schema/Database: Ask data-layer-expert
- Backend API: Ask python-backend-engineer
- Frontend: Ask ui-engineer

**Documentation**:
- Product Requirements: [PRD.md](/docs/project_plans/import-partial-data-manual-population/PRD.md)
- Architecture Decisions: [ADR-001.md](/docs/project_plans/import-partial-data-manual-population/ADR-001-nullable-price-strategy.md)
- Phase Details: See links above

---

## Glossary

- **Partial Import**: Listing created with missing fields (typically price=None)
- **Full Import**: Complete listing with all required fields and metrics calculated
- **Quality**: "full" or "partial" indicator on listing
- **Extraction Metadata**: Dict tracking which fields were extracted vs. manual
- **Bulk Job**: Multiple URL imports in single operation
- **Completion**: User provides missing data, triggering metrics recalculation
