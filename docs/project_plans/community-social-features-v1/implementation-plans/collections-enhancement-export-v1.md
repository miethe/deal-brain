---
title: "Implementation Plan: Collections Enhancement & Export – Phase 2"
description: "Comprehensive implementation plan for Deal Brain's Phase 2 collections enhancement, including shareable collections, card image generation, and portable artifact export/import functionality."
audience: [developers, ai-agents]
tags: [collections, sharing, image-generation, export-import, phase-2, implementation]
created: 2025-11-14
updated: 2025-11-14
category: "product-planning"
status: published
related:
  - ../PRDs/collections-enhancement-export-v1.md
---

# Implementation Plan: Collections Enhancement & Export – Phase 2

**Project:** Deal Brain Collections Enhancement & Export
**Phase:** Phase 2 (Post-Black Friday)
**Complexity:** Large (L)
**Track:** Full (Comprehensive with architecture validation)
**Estimated Effort:** 85 story points
**Estimated Timeline:** 4-5 weeks (overlapping subphases)
**Owner:** Engineering & Product
**Status:** Ready for Implementation Planning

---

## Executive Summary

This implementation plan translates the Collections Enhancement & Export PRD into a detailed, actionable roadmap with task breakdowns, dependencies, and quality gates. Phase 2 extends Deal Brain's Phase 1 private collections into shareable, discoverable entities; adds static card image generation for social sharing; and introduces portable deal/collection artifacts for backup, external integration, and AI workflows.

### Key Outcomes

1. **Shareable Collections (FR-B3):** Users can make collections public/unlisted, discover others' curations, and copy them to their workspace
2. **Card Image Generation (FR-A2):** Listings can be downloaded as PNG/JPEG cards suitable for social media and forums
3. **Portable Artifacts (FR-A4):** Deals and collections export as versioned JSON; import validates and integrates seamlessly

### Complexity Drivers

- **Image Generation Infrastructure:** Headless browser integration (Playwright), S3 caching, performance optimization
- **Schema Versioning:** Portable formats must remain backward-compatible; v1.0 schema locked
- **Cross-Layer Changes:** Database → Repository → Service → API → UI; 8-layer implementation
- **Quality Gates:** Round-trip export/import testing, social platform image validation, backward compatibility

### Success Criteria

- 25%+ of active users share ≥1 collection within first month post-launch
- Card image generation <3 sec @ p95; 24-hr cache hit rate >80%
- Export JSON validates against v1.0 schema; 100% round-trip fidelity
- Zero breaking changes to portable format; old exports still parse
- All 3 features fully tested with E2E, integration, and performance coverage

---

## Dependencies & Blockers

### Phase 1 Completion Requirements

**CRITICAL:** This phase depends on Phase 1 full completion. Phase 1 deliverables required:

- [ ] Collections table exists with `id`, `name`, `description`, `user_id`, `created_at`, `updated_at`
- [ ] Collection CRUD endpoints functional (`GET`, `POST`, `PATCH`, `DELETE` `/collections/`)
- [ ] Collections UI pages implemented (create, list, detail, edit)
- [ ] Listing detail pages exist at `/deals/{listing_id}` with shareable links
- [ ] User authentication and authorization functional
- [ ] Valuation breakdown computed and accessible via API
- [ ] User profiles with basic info (id, username, avatar)

### External Dependencies

- [ ] S3 or equivalent object storage configured and accessible from API
- [ ] Playwright/Puppeteer libraries available in deployment environment
- [ ] Design system and card component design finalized (Figma mockup)
- [ ] PostgreSQL supports JSONB and composite indexes (existing)

### Known Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| **Image generation slow/OOM** | Implement timeout (5s), fallback to cached version, defer to background job if needed |
| **S3 costs spike** | Implement 30-day TTL on cached images; monitor storage usage weekly |
| **Import duplicates flood DB** | Implement fuzzy matching on name+price+seller; show preview before commit |
| **Public collections attract spam** | Require user account to create; add flag/report option; review reports weekly in Phase 2 |
| **Schema versioning breaks** | Lock v1.0.0 format; create migration guide before v1.1; test backward compatibility in Phase 2c |

---

## Layered Architecture Mapping

Deal Brain implementation follows 8-layer architecture:

```
Layer 1: Database           (Schema changes, migrations)
Layer 2: Repository         (Data access, queries, tokens)
Layer 3: Service            (Business logic, validation, orchestration)
Layer 4: API                (Endpoints, request/response contracts)
Layer 5: Image Generation   (Playwright, rendering, caching)
Layer 6: Frontend/UI        (React components, pages, modals)
Layer 7: Testing            (Unit, integration, E2E, performance)
Layer 8: Documentation      (API docs, schema reference, ADR)
```

### Phase Sequencing Strategy

Phases **overlap** to maximize parallelization:

- **Phase A (Weeks 1-3):** Shareable Collections (Layers 1-4, 6-7)
- **Phase B (Weeks 2-4, overlaps A):** Card Image Generation (Layers 3-6, special Layer 5)
- **Phase C (Weeks 3-5, overlaps A&B):** Export/Import Artifacts (Layers 1-4, 6-8)

Each phase can proceed independently once Phase 1 is complete; teams can parallelize across 3-4 engineers.

---

## Phase 2a: Shareable Collections & Public Discovery

**Timeline:** Weeks 1–3
**Lead:** Backend + Full-Stack Engineer
**Story Points:** 28
**Dependency:** Phase 1 complete

### Phase 2a Objectives

1. Add visibility column to collections table; support `private`, `unlisted`, `public` states
2. Implement public collection view endpoint + read-only template
3. Build visibility toggle UI; warn users when making public
4. Implement collection copy endpoint; copy to own workspace
5. Build `/collections/discover` page with search, filter, pagination
6. Add instrumentation for telemetry (share, copy, view events)
7. Comprehensive testing (unit, integration, E2E)

### Phase 2a Task Breakdown

#### Layer 1: Database Schema Changes (3 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2a-db-1** | Add `visibility` column to `collection` table | 2 pts | Phase 1 | Alembic migration runs cleanly; column has CHECK constraint; default value is 'private'; index on visibility and (user_id, visibility) created |
| **2a-db-2** | Create `collection_share_token` table | 2 pts | 2a-db-1 | Token generation; unique constraint on token; FK to collection(id); expires_at nullable; view_count tracks shares |
| **2a-db-3** | Create database indexes for public discovery | 1 pt | 2a-db-1 | Indexes on (visibility, created_at) for recent public; (visibility, updated_at) for trending |

**Migration Scripts Location:** `/home/user/deal-brain/apps/api/alembic/versions/`

---

#### Layer 2: Repository Layer (4 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2a-repo-1** | Add visibility query methods to `CollectionRepository` | 3 pts | 2a-db-1 | Methods: `get_by_id_and_visibility()`, `list_public()`, `list_by_visibility()`, `count_public_collections()` |
| **2a-repo-2** | Implement token management in `CollectionShareTokenRepository` | 2 pts | 2a-db-2 | Generate token, validate token, track view_count increment, soft-delete (set expires_at) |
| **2a-repo-3** | Add discovery queries (pagination, filtering) | 3 pts | 2a-db-1 | Filter by visibility=public; sort by created_at, view_count; full-text search on name+description |
| **2a-repo-4** | Add RLS (Row Level Security) validation for visibility | 2 pts | 2a-db-1, Phase 1 | Enforce: owner can see private; anyone can see unlisted/public; queries return 403 if unauthorized |

**Location:** `/home/user/deal-brain/apps/api/dealbrain_api/services/repositories/`

---

#### Layer 3: Service Layer (5 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2a-svc-1** | Implement collection visibility service | 3 pts | 2a-repo-1 | Service: `update_visibility()`, `get_public_collection()`, `check_access()` with proper auth checks |
| **2a-svc-2** | Implement collection copy service | 4 pts | Phase 1 (collections service), 2a-svc-1 | Copy method: create new collection, copy all items, preserve notes, create valuation snapshots |
| **2a-svc-3** | Implement collection discovery service | 3 pts | 2a-repo-3 | Service: `list_public_collections()`, `search_collections()`, `filter_by_owner()`, pagination support |
| **2a-svc-4** | Add token generation & validation | 2 pts | 2a-repo-2 | Generate unique tokens, validate on GET requests, increment view_count |
| **2a-svc-5** | Add telemetry event emission | 2 pts | 2a-svc-1, 2a-svc-2, 2a-svc-3 | Emit events: `collection.visibility_changed`, `collection.copied`, `collection.discovered` with user + collection context |

**Location:** `/home/user/deal-brain/apps/api/dealbrain_api/services/`

---

#### Layer 4: API Endpoints (4 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2a-api-1** | Implement PATCH `/collections/{id}` (visibility update) | 2 pts | 2a-svc-1 | Update visibility, validate state transitions, return 403 if not owner, cache invalidation |
| **2a-api-2** | Implement GET `/collections/{id}?visibility=public` (public view) | 2 pts | 2a-svc-1, 2a-repo-1 | Return read-only collection + owner info, populate item_count, return 404 if private and not owner |
| **2a-api-3** | Implement POST `/collections/{id}/copy` (copy to workspace) | 3 pts | 2a-svc-2 | Create new private collection, import items, return new collection with link |
| **2a-api-4** | Implement GET `/collections/discover` (public discovery) | 3 pts | 2a-svc-3 | Pagination (limit, offset), filter (owner, visibility), sort (recent, popular), full-text search |

**Location:** `/home/user/deal-brain/apps/api/dealbrain_api/api/routers/collections.py`

---

#### Layer 6: Frontend/UI (5 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2a-ui-1** | Create visibility toggle component | 2 pts | Design system | Dropdown: private → unlisted → public; warning modal when toggling to public; shows "Shareable Link" option |
| **2a-ui-2** | Implement share modal on collection detail | 3 pts | 2a-api-1, 2a-ui-1 | Display copy-to-clipboard link, visibility selector, export option, share preview |
| **2a-ui-3** | Build `/collections/discover` page | 4 pts | 2a-api-4, 2a-ui-1 | List public collections, search bar, filter by owner, pagination, "Copy to My Collections" button on each |
| **2a-ui-4** | Add visibility indicator to collection detail sidebar | 1 pt | 2a-api-2 | Badge showing current visibility (private=gray, unlisted=blue, public=green) |
| **2a-ui-5** | Update collection list to show share count | 2 pts | 2a-svc-5 (telemetry) | Show view_count badge on public collections, sort option by popularity |

**Location:** `/home/user/deal-brain/apps/web/components/collections/` and `/home/user/deal-brain/apps/web/app/collections/`

---

#### Layer 7: Testing (2 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2a-test-1** | Unit + integration tests (database, service, API layer) | 4 pts | All 2a-* tasks | Test coverage: visibility toggle, token validation, copy logic, discovery queries; >85% coverage |
| **2a-test-2** | E2E tests (UI flows) | 3 pts | 2a-ui-*, 2a-api-* | Test: share collection → verify link → copy collection → verify in my collections; discover page works |

**Location:** `/home/user/deal-brain/tests/` and `/home/user/deal-brain/apps/web/__tests__/`

---

### Phase 2a Quality Gates

- [ ] All Alembic migrations run cleanly on fresh DB
- [ ] API tests pass; visibility enforcement verified (RLS)
- [ ] E2E test: make collection public → verify link works → copy collection → verify in workspace
- [ ] E2E test: search discover page; find collection by name/owner
- [ ] Performance: `/collections/discover` <200ms with 100+ public collections
- [ ] Security: Unauthenticated user cannot view private collections (403)
- [ ] Telemetry: Events emit correctly; can trace share → view → copy pipeline

---

## Phase 2b: Card Image Generation

**Timeline:** Weeks 2–4 (overlaps Phase 2a)
**Lead:** Backend Engineer + Frontend Engineer
**Story Points:** 32
**Dependency:** Phase 1 complete; design system finalized

### Phase 2b Objectives

1. Evaluate and integrate Playwright for headless browser rendering
2. Design card template as React component or static HTML
3. Implement `/listings/{id}/card-image` endpoint with generation logic
4. Set up caching layer (Redis metadata, S3 for images)
5. Implement image download UI in listing detail and collections
6. Test rendering on Discord, Twitter, Slack, mobile
7. Performance optimization and CDN delivery strategy

### Phase 2b Task Breakdown

#### Layer 3: Service Layer – Image Generation (4 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2b-svc-1** | Design card template (React component) | 3 pts | Design mockup (Figma) | Component accepts listing, style (light/dark), format (png/jpeg); renders at 1200x630 and 1080x1080px |
| **2b-svc-2** | Implement Playwright integration service | 4 pts | 2b-svc-1 | Service: `render_card()`, takes React component → PNG; handles timeouts, OOM, cleanup |
| **2b-svc-3** | Implement S3 caching service | 3 pts | Infra (S3 configured) | Service: `upload_to_s3()`, `get_from_cache()`, `invalidate_cache()`; 30-day TTL |
| **2b-svc-4** | Implement cache invalidation logic | 2 pts | 2b-svc-3 | Invalidate on listing price/component/valuation change; hook into ListingService.update() |

**Location:** `/home/user/deal-brain/apps/api/dealbrain_api/services/image_generation.py`

---

#### Layer 4: API Endpoints (2 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2b-api-1** | Implement GET `/listings/{id}/card-image` endpoint | 3 pts | 2b-svc-2, 2b-svc-3 | Query params: format (png/jpeg), style (light/dark); return image with correct MIME type; cache headers (Cache-Control: 86400) |
| **2b-api-2** | Add cache metadata endpoints (optional) | 1 pt | 2b-svc-3 | GET `/listings/{id}/card-image/metadata` returns cache status, generation time, expiry |

**Location:** `/home/user/deal-brain/apps/api/dealbrain_api/api/routers/listings.py`

---

#### Layer 5: Image Generation Infrastructure (3 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2b-infra-1** | Set up Playwright in API container | 2 pts | Docker/deployment setup | Playwright installed; headless browser pool configured (max 2 concurrent); startup test runs |
| **2b-infra-2** | Configure S3 bucket + lifecycle policies | 2 pts | AWS/infrastructure | Bucket created; CORS rules for cross-origin image loading; 30-day TTL lifecycle rule; access logging |
| **2b-infra-3** | Implement background job for cache warm-up (optional) | 1 pt | Celery/worker setup | Background job: pre-generate card images for top 100 listings daily; reduces p95 latency |

**Location:** Infrastructure config files (docker-compose, alembic, environment scripts)

---

#### Layer 6: Frontend/UI (3 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2b-ui-1** | Create card image download button + style picker modal | 3 pts | 2b-api-1 | Button on listing detail page; modal to select light/dark theme; download or preview; shows "Generating..." with spinner |
| **2b-ui-2** | Add card image preview to collection items | 2 pts | 2b-ui-1 | Thumbnail of card image next to listing in collection view; download option in item menu |
| **2b-ui-3** | Implement image sharing UI on deal cards | 2 pts | 2b-ui-1 | "Share as Image" button in deal card; integrates with share modal from Phase 2a |

**Location:** `/home/user/deal-brain/apps/web/components/listings/` and `/home/user/deal-brain/apps/web/components/cards/`

---

#### Layer 7: Testing (2 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2b-test-1** | Unit + integration tests (image generation, caching) | 4 pts | 2b-svc-*, 2b-api-* | Test: generate card, verify PNG valid, cache hit/miss, invalidation logic, timeout handling |
| **2b-test-2** | Social platform rendering tests | 3 pts | 2b-ui-*, 2b-api-* | Manual test: Discord, Twitter, Slack, mobile; verify image appears, legible at 200px, correct dimensions |

**Location:** `/home/user/deal-brain/tests/test_image_generation.py`

---

### Phase 2b Performance Requirements & Optimization

**Performance Targets:**

- Card generation: <3 sec @ p95 (including cache miss)
- Cache hit rate: >80% (measure in APM)
- S3 latency: <100ms for cached images
- Image size: <500 KB per image

**Optimization Strategy:**

1. **Playwright pool:** Reuse browser instances; max 2 concurrent to avoid OOM
2. **S3 caching:** 24-hr TTL for cache hit; lazy expiry with background refresh
3. **CDN:** CloudFront or similar in front of S3; geo-distributed delivery
4. **Monitoring:** APM metrics on generation time, cache hit rate, S3 errors
5. **Fallback:** If generation >5 sec, serve cached/default image; log error for analysis

---

### Phase 2b Quality Gates

- [ ] Playwright integration test passes; headless browser starts/stops cleanly
- [ ] Card image renders correctly in light and dark modes at all dimensions
- [ ] S3 bucket configured with correct permissions and lifecycle policies
- [ ] Cache invalidation tested: update listing price → old image invalidated
- [ ] Performance: Card generation <3 sec @ p95; verified with load test
- [ ] Social platform test: Image renders correctly on Discord, Twitter, Slack
- [ ] Security: S3 bucket not publicly readable; signed URLs for download if needed
- [ ] Cost estimation: S3 storage and Playwright usage monitored; no runaway costs

---

## Phase 2c: Export/Import Portable Artifacts

**Timeline:** Weeks 3–5 (overlaps Phases 2a & 2b)
**Lead:** Backend Engineer + Full-Stack Engineer
**Story Points:** 25
**Dependency:** Phase 1 complete; schema finalized

### Phase 2c Objectives

1. Finalize v1.0.0 JSON schema for deals and collections
2. Implement deal export endpoint with validation
3. Implement deal import endpoint with preview and duplicate detection
4. Implement collection export/import endpoints
5. Build import preview modal and merge/skip UI
6. Add round-trip testing (export → import → export = identical)
7. Backward compatibility testing with mock old exports

### Phase 2c Task Breakdown

#### Layer 1: Database Schema (1 task)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2c-db-1** | Create `deal_export_cache` table (optional, for performance) | 1 pt | Phase 1 | Table stores cached JSON exports; UNIQUE (listing_id, format); expires_at for cleanup |

**Note:** Export can be generated on-demand; cache table is optional for performance.

---

#### Layer 2: Repository Layer (2 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2c-repo-1** | Add query methods for duplicate detection | 2 pts | Phase 1 (listings) | Fuzzy match on name+price+seller; Levenshtein distance or similar; return potential matches |
| **2c-repo-2** | Add export cache repository (if 2c-db-1 used) | 1 pt | 2c-db-1 | Store/retrieve cached JSON; invalidation on listing update |

**Location:** `/home/user/deal-brain/apps/api/dealbrain_api/services/repositories/`

---

#### Layer 3: Service Layer (6 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2c-svc-1** | Implement PortableDealExport schema & validator | 3 pts | PRD spec (Appendix B) | Pydantic model for v1.0.0 format; validates listing, valuation, metadata; test with sample exports |
| **2c-svc-2** | Implement deal export service | 2 pts | 2c-svc-1 | Service: `export_listing_as_json()`, includes valuation breakdown, metadata, timestamp |
| **2c-svc-3** | Implement deal import service | 3 pts | 2c-svc-1, 2c-repo-1 | Service: `import_listing_from_json()`, validates schema, detects duplicates, returns preview |
| **2c-svc-4** | Implement collection export service | 2 pts | 2c-svc-2 | Service: `export_collection_as_json()`, includes all items with valuations |
| **2c-svc-5** | Implement collection import service | 3 pts | 2c-svc-3, Phase 1 (collections) | Service: `import_collection_from_json()`, creates collection + imports items, handles bulk import |
| **2c-svc-6** | Implement schema versioning & backward compatibility | 2 pts | 2c-svc-1 | Version checking; migration helpers for v0.9 → v1.0; warn on version mismatch |

**Location:** `/home/user/deal-brain/apps/api/dealbrain_api/services/export_import.py`

---

#### Layer 4: API Endpoints (5 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2c-api-1** | Implement GET `/listings/{id}/export` (deal export) | 2 pts | 2c-svc-2 | Query param: format (json/yaml, v1.0 supports json); return file download with correct filename/headers |
| **2c-api-2** | Implement POST `/listings/import` (deal import) | 3 pts | 2c-svc-3 | Accept JSON file or URL; return preview with parsed data + duplicate matches; user confirms to create |
| **2c-api-3** | Implement GET `/collections/{id}/export` (collection export) | 2 pts | 2c-svc-4 | Return JSON file with all items; filename includes collection name, date, ID |
| **2c-api-4** | Implement POST `/collections/import` (collection import) | 3 pts | 2c-svc-5 | Accept JSON file; return preview (show items to be imported); user confirms; create collection + items |
| **2c-api-5** | Add schema validation middleware/decorator | 1 pt | 2c-svc-1, 2c-api-2, 2c-api-4 | Validates incoming JSON against v1.0.0 schema; returns 400 with schema errors if invalid |

**Location:** `/home/user/deal-brain/apps/api/dealbrain_api/api/routers/listings.py` and `collections.py`

---

#### Layer 6: Frontend/UI (3 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2c-ui-1** | Add export option to listing/collection detail menus | 2 pts | 2c-api-1, 2c-api-3 | "⋮" menu → "Export as JSON"; download file with correct naming |
| **2c-ui-2** | Build import preview modal | 3 pts | 2c-api-2, 2c-api-4 | Modal shows parsed data, duplicate matches, merge/skip options; user can edit before confirming |
| **2c-ui-3** | Implement import flow on dashboard/collections | 2 pts | 2c-ui-2, 2c-api-2, 2c-api-4 | Upload JSON file; trigger preview modal; confirm to create/merge |

**Location:** `/home/user/deal-brain/apps/web/components/import-export/` and `/home/user/deal-brain/apps/web/app/dashboard/`

---

#### Layer 8: Documentation (2 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2c-doc-1** | Create JSON schema reference document | 2 pts | 2c-svc-1, PRD Appendix B | Document v1.0.0 schema, required/optional fields, example exports, validation rules |
| **2c-doc-2** | Create import/export API documentation | 2 pts | 2c-api-* | Document endpoints, request/response examples, error codes, rate limits |

**Location:** `/home/user/deal-brain/docs/api/` and `/home/user/deal-brain/docs/schemas/`

---

#### Layer 7: Testing (4 tasks)

| ID | Task | Effort | Dependencies | Acceptance Criteria |
|-----|------|--------|---|---|
| **2c-test-1** | Unit tests (schema validation, export generation) | 3 pts | 2c-svc-* | Test: valid export JSON, schema validation, version checking, backward compatibility with v0.9 mock |
| **2c-test-2** | Integration tests (export → import → export round-trip) | 4 pts | 2c-svc-*, 2c-api-* | Test: export deal → import → re-export should be identical (except timestamp); valuation preserved |
| **2c-test-3** | Duplicate detection tests | 2 pts | 2c-repo-1, 2c-svc-3 | Test: fuzzy match on name+price+seller; verify merges detected |
| **2c-test-4** | E2E tests (UI import/export flows) | 3 pts | 2c-ui-*, 2c-api-* | Test: export deal → download JSON → import → verify in collection; collection export/import flow |

**Location:** `/home/user/deal-brain/tests/test_export_import.py`

---

### Phase 2c JSON Schema & Versioning

**Schema File Location:** `/home/user/deal-brain/docs/schemas/deal-brain-export-schema-v1.0.0.json`

**Key Schema Elements:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Deal Brain Export Format v1.0.0",
  "type": "object",
  "required": ["deal_brain_export"],
  "properties": {
    "deal_brain_export": {
      "type": "object",
      "required": ["version", "exported_at", "type", "data"],
      "properties": {
        "version": {"type": "string", "enum": ["1.0.0"]},
        "exported_at": {"type": "string", "format": "date-time"},
        "exported_by": {"type": "string", "format": "uuid"},
        "type": {"type": "string", "enum": ["deal", "collection"]},
        "data": {"type": "object"}
      }
    }
  }
}
```

**Versioning Strategy:**

1. Lock v1.0.0 for Phase 2c; no breaking changes
2. Add migration helpers for v0.9 → v1.0 (if older exports exist)
3. Test backward compatibility: old exports must parse in new importer
4. Before v1.1: Create migration guide; plan for any schema additions (optional fields only)

---

### Phase 2c Quality Gates

- [ ] JSON schema file created and validates against JSON Schema draft-07
- [ ] Export API returns valid v1.0.0 JSON for deals and collections
- [ ] Import API rejects invalid schema; returns helpful error messages
- [ ] Round-trip test passes: export deal → import → re-export = identical (except timestamp)
- [ ] Duplicate detection tested: fuzzy match on name+price+seller works correctly
- [ ] Backward compatibility: mock v0.9 export parsed without error
- [ ] E2E test: export from listing detail → download → import on dashboard → verify in collection
- [ ] Performance: Export <1 sec for single deal, <2 sec for 100-item collection
- [ ] Security: Uploaded JSON validated; no code injection via import

---

## Cross-Phase Integration & Sequencing

### Critical Path Analysis

**Dependency Graph:**

```
Phase 1 (complete)
├── Phase 2a (Weeks 1-3)
│   ├── DB schema (2a-db-*)
│   ├── Repository (2a-repo-*)
│   ├── Service (2a-svc-*)
│   ├── API (2a-api-*)
│   └── UI (2a-ui-*) [DEPENDENT on API]
│
├── Phase 2b (Weeks 2-4, overlaps 2a)
│   ├── Service: Image gen (2b-svc-1..4) [CAN START after 2a-svc-1]
│   ├── Infrastructure (2b-infra-*) [PARALLEL with 2b-svc-1]
│   ├── API (2b-api-*) [DEPENDENT on 2b-svc-2]
│   └── UI (2b-ui-*) [DEPENDENT on 2b-api-1]
│
└── Phase 2c (Weeks 3-5, overlaps 2a & 2b)
    ├── Service: Export/import (2c-svc-*) [CAN START immediately]
    ├── API (2c-api-*) [DEPENDENT on 2c-svc-*]
    ├── Documentation (2c-doc-*) [PARALLEL with 2c-svc-1]
    └── UI (2c-ui-*) [DEPENDENT on 2c-api-*]
```

### Suggested Team Allocation (4 Engineers)

**Engineer A – Backend Lead (Collections & Discovery)**
- Owns: Phase 2a (all database, repository, service, API)
- Weeks: 1-3
- Handoff: API contracts to Engineer B for UI integration

**Engineer B – Full-Stack (Collections UI + Export/Import UI)**
- Owns: Phase 2a UI, Phase 2c UI + API
- Weeks: 1-3 (UI), 3-5 (Export/Import)
- Dependencies: Waits for Engineer A API contracts (week 1)

**Engineer C – Backend (Image Generation Infrastructure)**
- Owns: Phase 2b infrastructure, service, API
- Weeks: 2-4
- Parallel: Can start after Engineer A completes 2a-svc-1 (week 1.5)
- Dependencies: S3, Playwright setup (infra prerequisites)

**Engineer D – QA + Documentation Lead**
- Owns: All testing (unit, integration, E2E, performance), documentation, schema
- Weeks: 1-5 (continuous, starts after developers)
- Dependencies: Code from A, B, C to test against

---

## Risk Assessment & Mitigation

### High-Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **Image generation OOM / timeout** | Medium (30%) | High (blocks 2b) | Implement timeout (5s), fallback to SVG/text card, background job for high-traffic deals |
| **S3 costs spike unexpectedly** | Medium (30%) | Medium (budget impact) | Set up billing alerts, implement 30-day TTL, monitor daily, archive old images quarterly |
| **Duplicate detection fails; import floods DB** | Medium (25%) | Medium (data quality) | Fuzzy match algorithm tested with sample data, preview UI prevents accidental bulk import |
| **Public collections attract spam** | Medium (40%) | Low (Phase 3 handles moderation) | Require user account, flag/report option, rate limit collection creation, manual review weekly |
| **Schema versioning breaks on v1.1** | Low (15%) | High (backward compatibility) | Lock v1.0.0 now, document migration path before v1.1, test v0.9 → v1.0 compatibility |
| **Social platform image rendering fails** | Low (20%) | Medium (feature reduced) | Test on major platforms early (week 2), adjust dimensions/format as needed, provide PNG + JPEG options |

### Medium-Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **Playwright version conflicts with API env** | Low (20%) | Medium (CI/CD blocker) | Pin Playwright version in requirements, test in Docker early, document troubleshooting |
| **Collection discovery query slow (>200ms)** | Low (20%) | Low (UX, not feature-blocking) | Index (visibility, created_at), pagination (limit 20), caching discover results (5 min TTL) |
| **Export file format doesn't match design spec** | Low (15%) | Low (cosmetic fix) | Finalize schema early, get design review by week 1, prepare update plan |
| **Phase 1 not fully complete when 2a starts** | Medium (35%) | High (blocks 2a start) | Lock Phase 1 completion date; plan Phase 2a kickoff only after Phase 1 sign-off |

### Low-Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **Telemetry events fail to emit** | Low (10%) | Low (metrics data gap) | Add observability tests, verify event payload, retry logic in event handler |
| **UI components conflict with design system** | Low (10%) | Low (polish) | Get design review at component mockup stage, test accessibility (WCAG AA) |

---

## Architecture Validation Checklist

Ensure Phase 2 design complies with Deal Brain's layered architecture:

### Database Layer

- [ ] All schema changes use Alembic migrations
- [ ] Migrations are reversible (down() implemented)
- [ ] Indexes created for all new foreign keys and query filters
- [ ] UNIQUE constraints enforced (e.g., share tokens)
- [ ] CHECK constraints enforce enum values (visibility)
- [ ] Timestamps use CURRENT_TIMESTAMP, managed by DB

### Repository Layer

- [ ] All queries use async SQLAlchemy session
- [ ] RLS (Row Level Security) enforced: users see only data they should
- [ ] Query methods abstract database details (no raw SQL in services)
- [ ] Pagination implemented for discovery queries
- [ ] Index usage verified; no sequential scans on large tables

### Service Layer

- [ ] Services handle business logic; repos handle data access
- [ ] All services emit telemetry events for monitoring
- [ ] Error handling: specific exceptions raised, logged, handled gracefully
- [ ] Validation logic in services before database operations
- [ ] No direct database calls; always via repository layer

### API Layer

- [ ] All endpoints follow REST conventions
- [ ] Request/response models use Pydantic with validation
- [ ] Authentication/authorization checked before business logic
- [ ] Error responses include helpful messages (400, 403, 404, 500)
- [ ] Rate limiting considered for resource-intensive endpoints (image generation, import)
- [ ] CORS headers correct for cross-origin requests (image CDN access)

### Frontend Layer

- [ ] Components use React hooks (no class components)
- [ ] Data fetching via React Query; pagination, caching, refetching managed
- [ ] Forms use controlled components with validation feedback
- [ ] Accessibility: keyboard navigation, screen reader support (WCAG AA)
- [ ] Performance: memoized components, debounced inputs, lazy loading images

### Infrastructure & DevOps

- [ ] Environment variables documented (.env.example)
- [ ] Secrets (S3 credentials) not in code; use IAM roles or .env
- [ ] Docker image includes Playwright dependencies
- [ ] Database migrations run on deployment before app starts
- [ ] Monitoring/observability: metrics, logs, traces for new features

### Testing

- [ ] Unit tests: service logic, validators, utilities (>85% coverage)
- [ ] Integration tests: database transactions, service orchestration, API contract testing
- [ ] E2E tests: critical user flows (share → copy, export → import, card download)
- [ ] Performance tests: p95 latencies measured, alerts configured
- [ ] Security tests: auth enforcement, SQL injection prevention, XSS on user input

### Documentation

- [ ] API documentation: all endpoints, request/response examples, error codes
- [ ] Schema documentation: JSON schema reference, example exports
- [ ] Architecture Decision Records (ADR) for major design choices
- [ ] README for key services (image generation, export/import)
- [ ] Deployment guide: environment setup, migration steps, rollback plan

---

## Quality Gates & Sign-Off Criteria

### Pre-Launch Quality Gates (All Must Pass)

#### Phase 2a: Shareable Collections

- **Database:**
  - [ ] Alembic migrations run cleanly on fresh/staging DB
  - [ ] Visibility column has DEFAULT 'private' and CHECK constraint
  - [ ] Indexes created and query plans verified

- **API:**
  - [ ] PATCH `/collections/{id}` updates visibility; returns 403 if not owner
  - [ ] GET `/collections/{id}` returns 403 for private if not owner
  - [ ] GET `/collections/discover` returns public collections only, paginated
  - [ ] POST `/collections/{id}/copy` creates new private collection with all items

- **UI:**
  - [ ] Visibility toggle works; warning shown when toggling to public
  - [ ] Discover page loads within 2 sec; search/filter functional
  - [ ] E2E test passes: make collection public → copy → verify in my collections

- **Testing:**
  - [ ] Unit tests: >85% coverage of visibility logic
  - [ ] Integration tests: database, service, API layer tested
  - [ ] Performance: discover page <200ms with 100+ collections

#### Phase 2b: Card Image Generation

- **Infrastructure:**
  - [ ] Playwright installed and tested in Docker container
  - [ ] S3 bucket configured with correct CORS, lifecycle, permissions

- **API:**
  - [ ] GET `/listings/{id}/card-image` returns valid PNG/JPEG within 3 sec
  - [ ] Cache hit rate >80% for repeated requests (24-hr TTL)
  - [ ] Cache invalidation works: update listing → old image cleared

- **UI:**
  - [ ] Card download button appears on listing detail and collection items
  - [ ] Style picker (light/dark) works correctly
  - [ ] Downloaded image is legible at 200px width (mobile preview)

- **Testing:**
  - [ ] Unit tests: image generation, caching logic
  - [ ] Social platform tests: Discord, Twitter, Slack render correctly
  - [ ] Performance: p95 generation time <3 sec (load test with 100 concurrent requests)
  - [ ] No OOM or resource exhaustion in 1-hour soak test

#### Phase 2c: Export/Import Portable Artifacts

- **Schema:**
  - [ ] JSON schema file created and validates against JSON Schema draft-07
  - [ ] Example exports provided and validated against schema

- **API:**
  - [ ] GET `/listings/{id}/export` returns valid v1.0.0 JSON
  - [ ] POST `/listings/import` validates schema; rejects invalid exports
  - [ ] POST `/collections/import` creates collection and all items
  - [ ] Round-trip test: export → import → re-export = identical (except timestamp)

- **UI:**
  - [ ] Export option appears in listing/collection menus; download works
  - [ ] Import preview modal shows parsed data, duplicates, merge/skip options
  - [ ] E2E test: export → import → verify in collection

- **Testing:**
  - [ ] Unit tests: schema validation, export generation, backward compatibility
  - [ ] Round-trip testing: all field types (CPU, RAM, storage, valuation, notes) preserved
  - [ ] Duplicate detection tested: fuzzy match on name+price+seller
  - [ ] Performance: export <1 sec for single deal, <2 sec for 100-item collection

### Launch Checklist (Final Validation)

- [ ] All phase quality gates passed (2a, 2b, 2c)
- [ ] Performance benchmarks met: discovery <200ms, card <3s, export <1s
- [ ] Security: no SQL injection, XSS, or auth bypass; OWASP compliance verified
- [ ] Monitoring: dashboards for card generation, cache hit rate, import success rate, errors
- [ ] Telemetry: collection share, copy, view events tracked; image downloads logged
- [ ] Documentation: API docs, schema reference, deployment guide published
- [ ] Rollback plan: feature flags for new endpoints; data migration reversible
- [ ] Phase 1 sign-off: no regressions in collections, listing detail, sharing flows
- [ ] PM/Design sign-off: UI matches design spec, feature acceptance criteria met
- [ ] Engineering sign-off: all tests pass, code review complete, coverage >85%

---

## Linear Import Data & Task Structure

### Linear Setup Instructions

1. **Create Epic:** "Deal Brain Collections Enhancement – Phase 2"
2. **Create Cycles:**
   - Cycle 2a: "Phase 2a: Shareable Collections" (Weeks 1-3)
   - Cycle 2b: "Phase 2b: Card Image Generation" (Weeks 2-4)
   - Cycle 2c: "Phase 2c: Export/Import Artifacts" (Weeks 3-5)

3. **Import Tasks:** Use the CSV format below for Linear bulk import

### Phase 2a Tasks (CSV for Linear)

```csv
Title,Description,Estimate,Priority,Status,Cycle,Assignee,Labels
"Add visibility column to collection table","Alembic migration: add visibility enum column (private/unlisted/public)",2,High,Backlog,Cycle 2a,Engineer-A,database
"Create collection_share_token table","New table for sharing tokens; tracks view_count",2,High,Backlog,Cycle 2a,Engineer-A,database
"Create discovery indexes","Indexes on (visibility, created_at) for efficient queries",1,Medium,Backlog,Cycle 2a,Engineer-A,database
"Add visibility query methods","Repository: get_by_visibility, list_public, count_public",3,High,Backlog,Cycle 2a,Engineer-A,backend
"Implement token management","Repository: generate, validate, track tokens",2,Medium,Backlog,Cycle 2a,Engineer-A,backend
"Add discovery queries","Repository: pagination, filtering, full-text search",3,High,Backlog,Cycle 2a,Engineer-A,backend
"Implement RLS for visibility","Repository: enforce visibility rules per user",2,High,Backlog,Cycle 2a,Engineer-A,security
"Implement visibility service","Service: update_visibility, check_access, get_public_collection",3,High,Backlog,Cycle 2a,Engineer-A,backend
"Implement collection copy service","Service: copy collection to own workspace; preserve items",4,High,Backlog,Cycle 2a,Engineer-A,backend
"Implement discovery service","Service: list_public, search, filter, pagination",3,Medium,Backlog,Cycle 2a,Engineer-A,backend
"Implement token service","Service: generate, validate, view_count tracking",2,Medium,Backlog,Cycle 2a,Engineer-A,backend
"Add telemetry events","Emit collection.visibility_changed, copied, discovered events",2,Low,Backlog,Cycle 2a,Engineer-A,observability
"Implement PATCH /collections/{id} visibility","API: update visibility with auth checks and cache invalidation",2,High,Backlog,Cycle 2a,Engineer-A,api
"Implement GET /collections/{id} public view","API: read-only public collection view with owner info",2,High,Backlog,Cycle 2a,Engineer-A,api
"Implement POST /collections/{id}/copy","API: copy collection to own workspace",3,High,Backlog,Cycle 2a,Engineer-A,api
"Implement GET /collections/discover","API: list public collections with search, filter, pagination",3,High,Backlog,Cycle 2a,Engineer-A,api
"Create visibility toggle component","UI: dropdown for private/unlisted/public with warning modal",2,High,Backlog,Cycle 2a,Engineer-B,frontend
"Implement share modal","UI: copy link, visibility selector, export option",3,High,Backlog,Cycle 2a,Engineer-B,frontend
"Build /collections/discover page","UI: list public collections, search, filter, copy button",4,High,Backlog,Cycle 2a,Engineer-B,frontend
"Add visibility indicator badge","UI: badge on collection detail showing current visibility",1,Low,Backlog,Cycle 2a,Engineer-B,frontend
"Update collection list view","UI: show share count, sort by popularity",2,Medium,Backlog,Cycle 2a,Engineer-B,frontend
"Unit & integration tests (Phase 2a)","Tests for database, service, API; >85% coverage",4,High,Backlog,Cycle 2a,Engineer-D,testing
"E2E tests (Phase 2a)","Test share, copy, discover flows",3,High,Backlog,Cycle 2a,Engineer-D,testing
```

### Phase 2b Tasks (CSV for Linear)

```csv
Title,Description,Estimate,Priority,Status,Cycle,Assignee,Labels
"Design card template React component","React component for 1200x630px card; light/dark styles",3,High,Backlog,Cycle 2b,Engineer-C,frontend
"Implement Playwright integration service","Service: render_card() → PNG; handle timeouts, cleanup",4,High,Backlog,Cycle 2b,Engineer-C,backend
"Implement S3 caching service","Service: upload, retrieve, invalidate cached images",3,High,Backlog,Cycle 2b,Engineer-C,backend
"Implement cache invalidation logic","Hook into listing updates; invalidate on price/component change",2,High,Backlog,Cycle 2b,Engineer-C,backend
"Set up Playwright in Docker","Install Playwright, configure headless browser pool (max 2)",2,High,Backlog,Cycle 2b,Engineer-C,infra
"Configure S3 bucket & lifecycle policies","Create bucket, set CORS, lifecycle (30-day TTL), logging",2,High,Backlog,Cycle 2b,Engineer-C,infra
"Background job for cache warm-up (optional)","Celery job: pre-generate cards for top 100 listings daily",1,Low,Backlog,Cycle 2b,Engineer-C,infrastructure
"Implement GET /listings/{id}/card-image","API: return PNG/JPEG with cache headers (86400s)",3,High,Backlog,Cycle 2b,Engineer-C,api
"Add cache metadata endpoints (optional)","API: /listings/{id}/card-image/metadata for cache status",1,Low,Backlog,Cycle 2b,Engineer-C,api
"Create download button + style picker","UI: button on listing detail, modal for light/dark selection",3,High,Backlog,Cycle 2b,Engineer-B,frontend
"Add card preview to collection items","UI: thumbnail + download option in collection view",2,Medium,Backlog,Cycle 2b,Engineer-B,frontend
"Implement image sharing UI","UI: 'Share as Image' button in deal cards",2,Medium,Backlog,Cycle 2b,Engineer-B,frontend
"Unit & integration tests (Phase 2b)","Tests for image generation, caching, invalidation; >85% coverage",4,High,Backlog,Cycle 2b,Engineer-D,testing
"Social platform rendering tests","Manual test on Discord, Twitter, Slack, mobile",3,High,Backlog,Cycle 2b,Engineer-D,testing-manual
"Performance tests (image generation)","Load test: card generation <3s p95; cache hit rate >80%",3,High,Backlog,Cycle 2b,Engineer-D,performance
```

### Phase 2c Tasks (CSV for Linear)

```csv
Title,Description,Estimate,Priority,Status,Cycle,Assignee,Labels
"Create deal_export_cache table (optional)","Migration: optional table for cached JSON exports",1,Low,Backlog,Cycle 2c,Engineer-A,database
"Add duplicate detection query methods","Repository: fuzzy match on name+price+seller",2,High,Backlog,Cycle 2c,Engineer-A,backend
"Add export cache repository (optional)","Repository for optional deal_export_cache table",1,Low,Backlog,Cycle 2c,Engineer-A,backend
"Implement PortableDealExport schema","Pydantic model for v1.0.0 format; validator",3,High,Backlog,Cycle 2c,Engineer-A,backend
"Implement deal export service","Service: export_listing_as_json() with valuation",2,High,Backlog,Cycle 2c,Engineer-A,backend
"Implement deal import service","Service: import_listing_from_json(); detect duplicates",3,High,Backlog,Cycle 2c,Engineer-A,backend
"Implement collection export service","Service: export_collection_as_json() with all items",2,High,Backlog,Cycle 2c,Engineer-A,backend
"Implement collection import service","Service: import_collection_from_json(); bulk import",3,High,Backlog,Cycle 2c,Engineer-A,backend
"Implement schema versioning & compatibility","Version checking; v0.9 → v1.0 migration helpers",2,Medium,Backlog,Cycle 2c,Engineer-A,backend
"Implement GET /listings/{id}/export","API: deal export endpoint; download JSON file",2,High,Backlog,Cycle 2c,Engineer-A,api
"Implement POST /listings/import","API: deal import with preview and duplicate detection",3,High,Backlog,Cycle 2c,Engineer-A,api
"Implement GET /collections/{id}/export","API: collection export with all items",2,High,Backlog,Cycle 2c,Engineer-A,api
"Implement POST /collections/import","API: collection import with preview",3,High,Backlog,Cycle 2c,Engineer-A,api
"Add schema validation middleware","Decorator for validating incoming JSON against v1.0.0",1,Medium,Backlog,Cycle 2c,Engineer-A,api
"Add export option to menus","UI: listing/collection detail 'Export as JSON' option",2,Medium,Backlog,Cycle 2c,Engineer-B,frontend
"Build import preview modal","UI: show parsed data, duplicates, merge/skip options",3,High,Backlog,Cycle 2c,Engineer-B,frontend
"Implement import flow on dashboard","UI: upload JSON, trigger preview, confirm create/merge",2,High,Backlog,Cycle 2c,Engineer-B,frontend
"Create JSON schema reference document","Documentation: v1.0.0 schema, examples, validation rules",2,Medium,Backlog,Cycle 2c,Engineer-D,documentation
"Create import/export API documentation","Documentation: endpoints, examples, error codes",2,Medium,Backlog,Cycle 2c,Engineer-D,documentation
"Unit tests (export/import validation)","Tests for schema validation, export generation, backward compat",3,High,Backlog,Cycle 2c,Engineer-D,testing
"Integration tests (round-trip)","Test export → import → export = identical; field preservation",4,High,Backlog,Cycle 2c,Engineer-D,testing
"Duplicate detection tests","Test fuzzy match on name+price+seller; verify merges",2,Medium,Backlog,Cycle 2c,Engineer-D,testing
"E2E tests (import/export flows)","Test export deal → import → verify in collection; collection flow",3,High,Backlog,Cycle 2c,Engineer-D,testing
```

---

## Success Metrics & Monitoring

### Key Performance Indicators (KPIs)

**Adoption Metrics:**
- Collection share rate: 25%+ of active users share ≥1 collection (week 2 post-launch)
- Copy rate: 15%+ of public collections copied to other users' workspaces (week 4)
- Card image usage: 10%+ of shared deals use card image (tracked via link in posts)
- Export/import adoption: 5%+ of users export or import a deal (week 3)

**Quality Metrics:**
- Shared collection views: 100+ average views per public collection (baseline)
- Card image generation: <3 sec @ p95; cache hit rate >80%
- Export JSON validity: 100% of exported files validate against v1.0 schema
- Round-trip fidelity: 100% of exported deals can be re-imported without loss
- Social platform rendering: 100% of card images render correctly on Discord, Twitter, Slack

**Operational Metrics:**
- Image generation errors: <0.5% (monitor Sentry)
- S3 storage usage: <100GB (monthly budget estimate)
- API error rate: <0.1% for export/import endpoints
- Database query performance: discovery queries <200ms p95

### Monitoring & Alerts

**Dashboards to Create:**

1. **Image Generation Dashboard:**
   - Generation time (p50, p95)
   - Cache hit/miss ratio
   - Error count + types
   - S3 storage usage

2. **Collection Sharing Dashboard:**
   - Public collections created (daily)
   - Collections copied (daily)
   - Discover page views
   - Average collection views

3. **Export/Import Dashboard:**
   - Export count (daily)
   - Import count (daily)
   - Duplicate detection hit rate
   - Schema validation errors

4. **Infrastructure Dashboard:**
   - Playwright browser pool usage
   - S3 request latency
   - Database query performance
   - Memory/CPU usage for image generation

**Alerts to Configure:**

- Card image generation >5 sec (p95 SLA breach)
- S3 storage >80GB (budget warning)
- Import schema validation errors >1% (data quality issue)
- Collection discovery query >300ms (performance degradation)
- Image generation process crashes (restart needed)

---

## Deployment & Rollout Strategy

### Pre-Launch Deployment

1. **Week 4:** Deploy Phase 2a (collections) to staging; run full regression suite
2. **Week 4:** Deploy Phase 2b (image generation) to staging; test on social platforms
3. **Week 5:** Deploy Phase 2c (export/import) to staging; round-trip testing
4. **Week 5:** Feature flag all 3 features as OFF in production
5. **Week 5:** Soft-launch to 5% of users (feature flag); monitor errors, performance
6. **Week 6:** Expand to 50% of users if soft-launch metrics pass
7. **Week 6:** Full rollout to all users

### Feature Flags

```python
# In FastAPI startup config
FEATURES_ENABLED = {
    'collection_visibility': os.getenv('FEATURE_COLLECTION_VISIBILITY', 'false'),
    'card_image_generation': os.getenv('FEATURE_CARD_IMAGE_GENERATION', 'false'),
    'export_import': os.getenv('FEATURE_EXPORT_IMPORT', 'false'),
}

# In endpoint handlers
@router.patch('/collections/{id}', feature_flag('collection_visibility'))
async def update_collection_visibility(...):
    ...
```

### Rollback Plan

**If Phase 2a breaks:**
- Feature flag: `FEATURE_COLLECTION_VISIBILITY=false`
- Database: Alembic downgrade to remove visibility column (fully reversible)
- UI: Revert to previous deployment
- Timeline: <15 min to rollback

**If Phase 2b causes OOM:**
- Feature flag: `FEATURE_CARD_IMAGE_GENERATION=false`
- Scale down Playwright pool to 1 instance
- Clear S3 cache; restart image generation service
- Timeline: <10 min

**If Phase 2c corrupts data on import:**
- Feature flag: `FEATURE_EXPORT_IMPORT=false`
- Restore affected listings from database backup
- Investigate import validation bug
- Timeline: <30 min for rollback; investigate separately

### Monitoring During Rollout

- **Real-time alerts:** PagerDuty for error rate >1%, latency >3s
- **Hourly reporting:** Dashboard checks for adoption metrics, error rates
- **User feedback:** Slack channel for user-reported issues
- **Daily review:** Team syncs on metrics; decision to expand rollout percentage

---

## Documentation Plan (Layer 8)

### Required Documentation Files

#### API Documentation

**File:** `/home/user/deal-brain/docs/api/collections-sharing.md`

- Endpoint descriptions: PATCH `/collections/{id}`, GET `/collections/{id}`, POST `/collections/{id}/copy`, GET `/collections/discover`
- Request/response examples
- Error codes and meanings
- Rate limiting notes
- Authentication requirements

**File:** `/home/user/deal-brain/docs/api/image-generation.md`

- Endpoint: GET `/listings/{id}/card-image`
- Query parameters: format, style
- Response types and headers
- Caching behavior
- Error handling
- Performance targets

**File:** `/home/user/deal-brain/docs/api/export-import.md`

- Endpoints: GET/POST `/listings/{id}/export`, POST `/listings/import`, GET/POST `/collections/{id}/export`, POST `/collections/import`
- Request/response schema
- Duplicate detection behavior
- Error codes (400 for invalid schema, 409 for duplicates)
- File format and naming

#### Schema Documentation

**File:** `/home/user/deal-brain/docs/schemas/deal-brain-export-schema-v1.0.0.json`

- Full JSON schema (JSON Schema draft-07 format)
- Property descriptions and types
- Required vs. optional fields
- Examples for deal and collection exports

**File:** `/home/user/deal-brain/docs/schemas/export-format-reference.md`

- Human-readable schema reference
- Field descriptions and types
- Example exports for deal and collection
- Validation rules
- Version history and migration notes

#### Architecture Decision Records (ADRs)

**File:** `/home/user/deal-brain/docs/architecture/adr-card-image-caching.md`

- Decision: Use Playwright + S3 for card image generation and caching
- Rationale: Performance, scalability, cost vs. alternatives (serverless functions, etc.)
- Consequences: Requires Playwright in container, S3 API calls, 30-day TTL management

**File:** `/home/user/deal-brain/docs/architecture/adr-portable-format-versioning.md`

- Decision: Lock v1.0.0 schema; plan migration path before v1.1
- Rationale: Ensure backward compatibility, simplify testing
- Consequences: Must document migration helpers for future versions

#### Deployment Guide

**File:** `/home/user/deal-brain/docs/deployment/phase-2-deployment.md`

- Environment variables: `FEATURE_COLLECTION_VISIBILITY`, `FEATURE_CARD_IMAGE_GENERATION`, `FEATURE_EXPORT_IMPORT`, S3 credentials
- Database migrations: step-by-step Alembic commands
- Service dependencies: Playwright, S3
- Rollback procedures for each phase
- Monitoring setup and alerts

---

## Appendix: Testing Examples

### Unit Test Example (Phase 2a – Visibility Toggle)

```python
# tests/test_collection_visibility.py
import pytest
from dealbrain_api.services import CollectionService

@pytest.mark.asyncio
async def test_update_visibility_private_to_public():
    # Setup
    collection = await fixture_create_collection(visibility='private')
    service = CollectionService()

    # Execute
    updated = await service.update_visibility(collection.id, 'public', user_id=collection.owner_id)

    # Assert
    assert updated.visibility == 'public'
    assert updated.updated_at > collection.updated_at

@pytest.mark.asyncio
async def test_update_visibility_not_owner_returns_403():
    # Setup
    collection = await fixture_create_collection(visibility='private', owner_id='user-1')
    service = CollectionService()

    # Execute & Assert
    with pytest.raises(PermissionError):
        await service.update_visibility(collection.id, 'public', user_id='user-2')
```

### Integration Test Example (Phase 2c – Round-Trip)

```python
# tests/test_export_import_roundtrip.py
import pytest
from dealbrain_api.services import ExportImportService

@pytest.mark.asyncio
async def test_export_deal_import_deal_roundtrip():
    # Setup: Create a listing with components and valuation
    listing = await fixture_create_listing_with_valuation(
        name="Dell PowerEdge R6515",
        price=1299.99,
        cpu="AMD EPYC 7742",
        ram_gb=16,
    )
    service = ExportImportService()

    # Export
    export_json = await service.export_listing_as_json(listing.id)
    assert export_json['deal_brain_export']['version'] == '1.0.0'

    # Import
    imported_listing = await service.import_listing_from_json(export_json, user_id='test-user')

    # Assert: all fields preserved
    assert imported_listing.name == listing.name
    assert imported_listing.price == listing.price
    assert imported_listing.components.cpu.name == listing.components.cpu.name
    assert imported_listing.valuation_breakdown == listing.valuation_breakdown

    # Re-export: should be identical (except timestamp)
    export_json_2 = await service.export_listing_as_json(imported_listing.id)
    assert export_json_2['deal_brain_export']['data'] == export_json['deal_brain_export']['data']
```

### E2E Test Example (Phase 2a – Share & Copy Flow)

```javascript
// apps/web/__tests__/e2e/collections-share.spec.ts
import { test, expect } from '@playwright/test';

test('Share collection and copy to own workspace', async ({ page, context }) => {
    const authorizedPage = await context.newPage();
    await authorizedPage.goto('/collections');

    // Create a collection (Phase 1)
    const collectionName = 'Test Collection ' + Date.now();
    await authorizedPage.click('[data-testid="new-collection"]');
    await authorizedPage.fill('[data-testid="collection-name"]', collectionName);
    await authorizedPage.click('[data-testid="create"]');

    // Make public
    await authorizedPage.click('[data-testid="share"]');
    await authorizedPage.click('[data-testid="visibility-public"]');
    await authorizedPage.click('[data-testid="confirm-public"]');

    // Get shareable link
    const link = await authorizedPage.locator('[data-testid="share-link"]').inputValue();
    expect(link).toContain('/collections/');

    // Open in new context (simulate different user)
    const otherUserPage = await context.newPage();
    await otherUserPage.goto(link);

    // Verify public view
    expect(await otherUserPage.locator('h1').textContent()).toContain(collectionName);

    // Copy to own workspace
    await otherUserPage.click('[data-testid="copy-collection"]');
    expect(await otherUserPage.locator('[data-testid="copy-success"]')).toBeVisible();

    // Verify in own collections
    await otherUserPage.goto('/collections');
    expect(await otherUserPage.locator(`text=${collectionName}`)).toBeVisible();
});
```

---

## Timeline & Milestones

### Sprint Planning (4-week timeline with 1-week buffer)

**Week 1 (Nov 18-22):**
- Phase 2a: Database schema, repository layer
- Phase 2b: Design card template, evaluate Playwright
- Phase 2c: Define v1.0.0 schema, start service implementation
- Milestone: Database migrations merged; API contracts finalized

**Week 2 (Nov 25-29):**
- Phase 2a: Complete API endpoints, start UI implementation
- Phase 2b: Playwright integration, S3 setup, image generation service
- Phase 2c: Complete export/import services
- Milestone: All API endpoints implemented; image generation MVP

**Week 3 (Dec 2-6):**
- Phase 2a: Complete UI, E2E testing, staging deployment
- Phase 2b: Card download UI, performance optimization, testing
- Phase 2c: Complete API endpoints, import preview UI, schema validation
- Milestone: All features functional on staging; quality gate review

**Week 4 (Dec 9-13):**
- All phases: Integration testing, performance validation, documentation
- Feature flag setup, soft-launch planning
- Rollout to 5% of users
- Milestone: Feature flags enabled in production (soft-launch)

**Week 5 (Dec 16-20):**
- Monitor soft-launch metrics
- Address bugs, performance issues
- Expand to 50% → 100% based on metrics
- Post-launch: monitoring, telemetry, user feedback
- Milestone: Full rollout complete; Phase 2 live to all users

---

## Summary & Next Steps

### What's Included in This Plan

✓ Detailed task breakdown across 8 layers of architecture
✓ Effort estimates (story points) and timeline
✓ Quality gates and acceptance criteria
✓ Risk assessment and mitigation strategies
✓ Linear import-ready CSV task data
✓ Testing strategy with examples
✓ Deployment and rollback procedures
✓ Monitoring and metrics
✓ Documentation plan

### Immediate Next Steps

1. **Confirm Phase 1 completion:** Lock Phase 1 sign-off date; ensure all Phase 1 features functional
2. **Design review:** Finalize card template mockup (Figma) with design system compliance
3. **Infrastructure setup:** Provision S3 bucket, configure Playwright in Docker, test environment
4. **Team assignment:** Assign 4 engineers to phases based on skills
5. **Linear setup:** Create epic, cycles, import tasks from CSV above
6. **Kickoff:** Engineering kickoff meeting; review timeline, dependencies, risks
7. **Week 1 start:** Parallel work on Phase 2a (collections) and infrastructure (2b/2c prep)

### Success Criteria for Phase 2 Completion

- All 3 features (shareable collections, card images, export/import) fully implemented and tested
- Quality gates passed: database, API, UI, performance, security
- Soft-launch metrics: >10% of users active on new features
- Production stability: error rate <0.5%, no OOM, no data corruption
- Documentation complete: API docs, schema reference, ADRs, deployment guide
- PM/Design sign-off: feature acceptance, design compliance verified

---

**Document Version:** 1.0
**Last Updated:** 2025-11-14
**Owner:** Engineering Team
**Status:** Ready for Implementation Sprint Kickoff
