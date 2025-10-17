# URL Ingestion Feature - Implementation Tracking

**Feature**: Universal URL Ingestion for Deal Brain
**PRD**: [prd-url-ingest-dealbrain.md](../../docs/project_plans/url-ingest/prd-url-ingest-dealbrain.md)
**Implementation Plan**: [implementation-plan.md](../../docs/project_plans/url-ingest/implementation-plan.md)
**Status**: Planning Complete
**Start Date**: 2025-10-17
**Target Completion**: 2025-12-01 (6 weeks)
**Effort Estimate**: 340 hours (2-3 engineers)

---

## Overview

Enable Deal Brain to ingest PC listings directly from retailer/marketplace URLs (eBay, Amazon, generic retailers). The system uses API-first approach when available, falls back to structured data (JSON-LD/schema.org), and leverages existing ImportSession patterns, Celery background jobs, and Listing enrichment pipeline.

**Key Integration Points:**
- Extends existing `Listing` model with marketplace/provenance fields
- Reuses `ImportSession` workflow pattern for async processing
- Leverages Celery + Redis for background scraping tasks
- Integrates with existing CPU/GPU enrichment pipeline
- Follows established API patterns (`/api/v1/ingest/*`)

---

## Phase Progress

### Phase 1: Foundation (Week 1) - 55 hours
**Status**: Not Started
**Target**: Week of 2025-10-17

- [ ] **ING-001**: Database schema migration (8h)
- [ ] **ING-002**: Pydantic schemas (6h)
- [ ] **ING-003**: Base adapter protocol (8h)
- [ ] **ING-004**: HTTP client wrapper (10h)
- [ ] **ING-005**: URL validation service (6h)
- [ ] **ING-006**: Settings management (8h)
- [ ] **ING-007**: Deduplication logic (5h)
- [ ] **ING-008**: Raw payload storage (4h)

**Blockers**: None
**Notes**: -

---

### Phase 2: Scraping Infrastructure (Weeks 2-3) - 115 hours
**Status**: Not Started
**Target**: Weeks of 2025-10-24 and 2025-10-31

- [ ] **ING-009**: eBay Browse API adapter (20h)
- [ ] **ING-010**: Generic JSON-LD extractor (16h)
- [ ] **ING-011**: Adapter router (12h)
- [ ] **ING-012**: Deduplication engine (14h)
- [ ] **ING-013**: Listing normalizer (18h)
- [ ] **ING-014**: Event emitter (12h)
- [ ] **ING-015**: Ingestion orchestrator (23h)

**Dependencies**: Phase 1 complete
**Blockers**: None
**Notes**: -

---

### Phase 3: API & Integration (Week 4) - 80 hours
**Status**: Not Started
**Target**: Week of 2025-11-07

- [ ] **ING-016**: Celery scraping task (12h)
- [ ] **ING-017**: Single URL endpoint (10h)
- [ ] **ING-018**: Bulk import endpoint (14h)
- [ ] **ING-019**: Status polling endpoints (8h)
- [ ] **ING-020**: ListingsService integration (20h)
- [ ] **ING-021**: Payload storage integration (8h)
- [ ] **ING-022**: Error handling & telemetry (8h)

**Dependencies**: Phase 2 complete
**Blockers**: None
**Notes**: -

---

### Phase 4: Frontend & Testing (Weeks 5-6) - 90 hours
**Status**: Not Started
**Target**: Weeks of 2025-11-14 and 2025-11-21

- [ ] **ING-023**: Single URL import form (12h)
- [ ] **ING-024**: Bulk uploader component (16h)
- [ ] **ING-025**: Status tracking UI (10h)
- [ ] **ING-026**: Provenance badges (8h)
- [ ] **ING-027**: Admin settings UI (12h)
- [ ] **ING-028**: Unit tests (16h)
- [ ] **ING-029**: Integration tests (16h)

**Dependencies**: Phase 3 complete
**Blockers**: None
**Notes**: -

---

## Current Sprint

**Sprint**: Planning
**Sprint Goal**: Complete PRD and implementation plan documentation
**Sprint Status**: ✅ Complete

**This Sprint Tasks:**
- [x] Analyze existing Deal Brain codebase architecture
- [x] Adapt generic URL ingestion PRD to Deal Brain patterns
- [x] Create Deal Brain-specific PRD
- [x] Create detailed implementation plan
- [x] Set up tracking documents

---

## Next Sprint

**Sprint**: Phase 1 - Foundation
**Sprint Goal**: Database schema, base adapters, HTTP infrastructure
**Sprint Duration**: 1 week
**Assigned**: TBD

**Sprint Tasks:**
1. Create Alembic migration for URL ingestion fields
2. Implement base adapter protocol and registry
3. Build HTTP client wrapper with rate limiting
4. Create URL validation service
5. Set up settings management for adapters
6. Implement deduplication logic
7. Create raw payload storage service

---

## Key Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Reuse ImportSession pattern | Proven async workflow, audit logging, conflict detection already built | 2025-10-17 |
| API-first adapter priority | Higher quality data, faster, respects ToS | 2025-10-17 |
| Store raw payloads | Debugging, re-parsing, audit trail | 2025-10-17 |
| Use existing Celery worker | No new infrastructure, proven reliability | 2025-10-17 |
| Extend Listing model vs new table | Simpler queries, unified schema, leverages existing enrichment | 2025-10-17 |

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API credential gating (eBay/Amazon) | Feature delay | Medium | Start with JSON-LD, add APIs incrementally |
| Anti-bot defenses | Scraping failures | High | API-first, low rate limits, respect robots.txt |
| Spec extraction accuracy | Poor data quality | Medium | Show provenance, allow manual edits, iterate on regex |
| Deduplication false positives | Lost variants | Low | Conservative matching, audit log merges |

---

## Success Metrics

**Performance:**
- Median eBay import: ≤5s
- Median JSON-LD import: ≤8s
- Bulk throughput: ≥120 URLs/min
- API availability: 99.5%

**Quality:**
- Field completeness: ≥85% for title/price/condition
- Dedupe accuracy: <2% false positives
- Error rate: <3% (excluding invalid URLs)

**Adoption:**
- 50+ URLs imported in first week (internal testing)
- 500+ URLs in first month (beta users)

---

## Notes & Learnings

*This section will be updated as implementation progresses*

### Week 1 (Planning)
- Deal Brain has excellent foundation: ImportSession, Celery, async SQLAlchemy all ready
- httpx already installed - no need for new HTTP library
- Listing model has `listing_url`, `raw_listing_json`, `attributes_json` - perfect for URL ingestion
- CPU/GPU enrichment pipeline can be reused for component matching

---

## Resources

- **PRD**: [docs/project_plans/url-ingest/prd-url-ingest-dealbrain.md](../../docs/project_plans/url-ingest/prd-url-ingest-dealbrain.md)
- **Implementation Plan**: [docs/project_plans/url-ingest/implementation-plan.md](../../docs/project_plans/url-ingest/implementation-plan.md)
- **Original Generic PRD**: [docs/project_plans/url-ingest/prd-url-ingest.md](../../docs/project_plans/url-ingest/prd-url-ingest.md)
- **Architecture Analysis**: TBD (created during exploration)
- **API Docs**: `/api/v1/ingest/*` (to be created)

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-10-17 | Created tracking document, PRD, and implementation plan | Claude |
