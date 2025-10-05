# Performance Metrics & Data Enrichment - Phases 5-8 Tracking

**Started:** October 5, 2025
**PRD:** docs/project_plans/requests/prd-10-5-performance-metrics.md
**Implementation Plan:** docs/project_plans/requests/implementation-plan-10-5.md
**Previous Phases:** 1-4 Complete (93%)

---

## Phase 5: Form Enhancements

**Duration:** 2 days
**Dependencies:** Phase 4 complete

### Tasks

#### 5.1 Update Listing Form with New Fields
- [x] Add manufacturer dropdown (9 options: Dell, HP, Lenovo, Apple, ASUS, Acer, MSI, Custom Build, Other)
- [x] Add series text input (placeholder: OptiPlex, ThinkCentre, Mac Studio)
- [x] Add model number text input (placeholder: 7090, M75q, A2615)
- [x] Add form_factor dropdown (6 options: Desktop, Laptop, Server, Mini-PC, All-in-One, Other)
- [x] Integrate CPU Info Panel below CPU selector
- [x] Integrate Ports Builder component
- [x] Update submit handler to save all new fields
- [x] Trigger metric calculation after save
- [x] Add form validation for new fields (built-in HTML5 validation)

#### 5.2 Create API Client Methods
- [x] Create getCpu(cpuId) method
- [x] Create recalculateListingMetrics(listingId) method
- [x] Create updateListingPorts(listingId, ports) method
- [x] Add TypeScript interfaces for API responses
- [x] Implement error handling
- [x] Test API client methods (TypeScript compilation passing)

**Status:** ✅ Complete

---

## Phase 6: Data Population & Migration

**Duration:** 2-3 days
**Dependencies:** Phase 5 complete

### Tasks

#### 6.1 Import PassMark Benchmark Data
- [ ] Source PassMark CSV data (web scrape or purchase)
- [ ] Create import_passmark_data.py script
- [ ] Implement CSV parsing with name matching
- [ ] Handle unmatched CPUs (logging)
- [ ] Run import and verify 95%+ coverage
- [ ] Document data source and update frequency

#### 6.2 Bulk Recalculate Listing Metrics
- [ ] Create recalculate_all_metrics.py script
- [ ] Implement progress logging (every 100 listings)
- [ ] Test with large dataset (1000+ listings)
- [ ] Handle errors gracefully
- [ ] Log completion summary
- [ ] Optional: Create Celery task for background processing

#### 6.3 Seed Sample Data
- [ ] Update seeds.py with metadata fields
- [ ] Add sample listings with all form factors
- [ ] Include multiple manufacturers
- [ ] Add ports data to samples
- [ ] Trigger metric recalculation on seed
- [ ] Test seed script execution

**Status:** 🔄 Not Started

---

## Phase 7: Testing & Quality Assurance

**Duration:** 2-3 days
**Dependencies:** Phase 6 complete

### Tasks

#### 7.1 Unit Tests
- [ ] Backend: test_listing_metrics.py (calculation service)
- [ ] Backend: test_ports_service.py (ports CRUD)
- [ ] Backend: test_listings_api.py (API endpoints)
- [ ] Frontend: dual-metric-cell.test.tsx
- [ ] Frontend: cpu-info-panel.test.tsx
- [ ] Frontend: ports-builder.test.tsx
- [ ] Achieve >90% backend coverage
- [ ] Test edge cases (null CPU, missing data)

#### 7.2 Integration Tests
- [ ] Test: Create listing with full metadata
- [ ] Test: Update valuation → metrics recalculate
- [ ] Test: Toggle valuation mode
- [ ] Test: Ports CRUD workflow
- [ ] Verify data persistence
- [ ] Check UI state transitions
- [ ] Ensure no console errors

#### 7.3 Performance Testing
- [ ] Bulk recalculation: <10s for 1000 listings
- [ ] Table render: <2s for 500 rows
- [ ] Scroll FPS: >30 FPS with 500+ rows
- [ ] Identify bottlenecks
- [ ] Implement optimizations if needed
- [ ] Document performance metrics

#### 7.4 Accessibility Audit
- [ ] Run Lighthouse (score ≥90)
- [ ] Run axe DevTools (0 critical violations)
- [ ] Test keyboard navigation
- [ ] Verify screen reader compatibility
- [ ] Check color contrast (WCAG AA)
- [ ] Ensure focus indicators visible

**Status:** 🔄 Not Started

---

## Phase 8: Documentation & Rollout

**Duration:** 1-2 days
**Dependencies:** Phase 7 complete

### Tasks

#### 8.1 Update Documentation
- [ ] Update CLAUDE.md with new features
- [ ] Update docs/architecture.md (data model section)
- [ ] Create docs/user-guide/listings.md
- [ ] Generate API docs (OpenAPI)
- [ ] Document migration strategy
- [ ] Add PassMark data import guide

#### 8.2 Staged Rollout
- [ ] Deploy to staging environment
- [ ] Internal testing (1 week)
- [ ] Beta release (10% users)
- [ ] Collect user feedback (>20 responses)
- [ ] Full rollout (100%)
- [ ] Publish changelog

#### 8.3 Monitoring & Alerts
- [ ] Create Grafana dashboards
- [ ] Configure Prometheus alerts
- [ ] Integrate error tracking (Sentry/Rollbar)
- [ ] Set up on-call rotation
- [ ] Document monitoring metrics
- [ ] Test alert triggers

**Status:** 🔄 Not Started

---

## Overall Progress

- **Phase 5:** 0/15 tasks (0%)
- **Phase 6:** 0/14 tasks (0%)
- **Phase 7:** 0/17 tasks (0%)
- **Phase 8:** 0/15 tasks (0%)
- **Total Phases 5-8:** 0/61 tasks (0%)

---

## Notes

- Phases 1-4 completed with 50/54 tasks (93%)
- All database schemas and core components ready
- Backend services and API endpoints functional
- Frontend components created and integrated
- Ready to proceed with form enhancements

---

## Key Decisions

- **PassMark Data Source:** TBD (web scrape vs purchase)
- **Valuation Mode Persistence:** localStorage (not user-level DB)
- **Performance Strategy:** React.memo + indexes + optional virtual scrolling
- **Testing Priority:** Backend unit tests first, then integration, then frontend

---

## Risks & Mitigations

1. **PassMark Data Availability**
   - Risk: Data source unavailable
   - Mitigation: Multiple sources, manual entry fallback

2. **Performance at Scale**
   - Risk: Slow metric calculations
   - Mitigation: Background jobs, caching, indexing

3. **User Adoption**
   - Risk: Low usage of new fields
   - Mitigation: Clear UI, tooltips, onboarding

---

## Success Criteria

- All 61 tasks completed or explicitly deferred
- TypeScript compilation passing
- All tests passing (>90% coverage)
- Documentation complete
- Staged rollout successful
- Performance targets met
