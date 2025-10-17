# URL Ingestion Feature - Session Notes

**Date**: 2025-10-17
**Session Type**: Planning & Architecture
**Duration**: ~1 hour
**Outcome**: ✅ Complete PRD and implementation plan

---

## Session Summary

Analyzed existing generic URL ingestion PRD and adapted it specifically for Deal Brain's architecture. Conducted deep codebase exploration to understand existing patterns and infrastructure. Created tailored PRD and detailed implementation plan leveraging Deal Brain's strengths.

---

## Key Findings

### Deal Brain Architecture Strengths
1. **Mature Import Pipeline**: ImportSession pattern with upload → mapping → preview → commit workflow
2. **Background Jobs**: Celery + Redis fully configured and operational
3. **Async Infrastructure**: SQLAlchemy async, httpx installed, connection pooling ready
4. **Listing Model**: Already has `listing_url`, `raw_listing_json`, `attributes_json` fields
5. **Enrichment Pipeline**: CPU/GPU catalog for component matching already exists
6. **Audit Logging**: Comprehensive audit tables and patterns established

### What Exists vs What Needs Building

**Already Built (70-80% of infrastructure):**
- ✅ Background job queue (Celery + Redis)
- ✅ Async HTTP client (httpx in dependencies)
- ✅ Database models with URL fields
- ✅ Import workflow patterns
- ✅ Conflict detection
- ✅ Preview-then-commit UX
- ✅ Audit logging

**Need to Build:**
- 🆕 HTML parsing service (BeautifulSoup4/lxml)
- 🆕 Marketplace adapters (eBay API, Amazon, schema.org)
- 🆕 Hardware spec extraction (regex for CPU/RAM/Storage/GPU)
- 🆕 URL validation and whitelisting
- 🆕 Rate limiting wrapper
- 🆕 Deduplication logic for URLs

---

## Decisions Made

### Architecture
- **Reuse ImportSession pattern**: Proven workflow, don't reinvent
- **API-first approach**: eBay Browse API → JSON-LD → scraping (last resort)
- **Extend Listing model**: Add marketplace, provenance, vendor_item_id fields
- **Celery for async**: Use existing worker, add scraping tasks
- **Raw payload storage**: New table for debugging/re-parsing (30-day TTL)

### Implementation Strategy
- **4 phases, 6 weeks total**: Foundation → Scraping → API → Frontend/Testing
- **P0 scope**: eBay + Generic JSON-LD only
- **P1 scope**: Amazon adapter, admin settings UI
- **Feature flags**: `ingestion.enabled`, `ingestion.adapters.{ebay|amazon}.enabled`

### Data Model
- Extend `Listing` table with:
  - `vendor_item_id` (e.g., eBay item ID)
  - `marketplace` (enum: ebay, amazon, other)
  - `provenance` (e.g., "ebay_api", "jsonld")
  - `last_seen_at` (for staleness detection)
- New `url_ingest_raw_payloads` table for debugging
- New `url_ingest_metrics` table for telemetry

---

## Files Created

1. **PRD**: `/mnt/containers/deal-brain/docs/project_plans/url-ingest/prd-url-ingest-dealbrain.md`
   - 489 lines, concise and actionable
   - Tailored to Deal Brain patterns
   - References existing ImportSession, Celery, Listing model

2. **Implementation Plan**: `/mnt/containers/deal-brain/docs/project_plans/url-ingest/implementation-plan.md`
   - 595 lines, 30 tasks across 4 phases
   - Absolute file paths for each task
   - Effort estimates (340 hours total)

3. **Tracking Doc**: `/mnt/containers/deal-brain/.claude/progress/url-ingestion-tracking.md`
   - Sprint tracking, task checklists
   - Risk register, success metrics
   - Decision log

4. **Session Notes**: `/mnt/containers/deal-brain/.claude/worknotes/url-ingestion-session.md` (this file)

---

## Key Insights

### Codebase Exploration Highlights

**Import Pipeline** (`apps/api/dealbrain_api/importers/`, `services/imports/`):
- ImportSessionService is 1235 lines - mature and well-tested
- Multi-step workflow: upload → schema detection → field mapping → preview → commit
- Conflict detection and resolution UI patterns
- Perfect foundation for URL ingestion sessions

**Listing Model** (`apps/api/dealbrain_api/models/core.py:340-426`):
- Already has `listing_url` (primary) and `other_urls` (JSON array)
- `raw_listing_json` field designed for scraped data
- `attributes_json` for flexible extensions
- Foreign keys to CPU/GPU for enrichment

**Background Jobs** (`apps/api/dealbrain_api/worker.py`, `tasks/`):
- Celery configured with Redis broker
- Worker container in Docker Compose
- Async task patterns established in `tasks/valuation.py`

**API Patterns** (`apps/api/dealbrain_api/api/*.py`):
- Clean router organization (`/api/v1/*`)
- RESTful conventions
- Dependency injection for DB sessions
- Easy to add `/api/v1/ingest/*` endpoints

---

## Technical Learnings

### Adapter Pattern Design
```python
class BaseAdapter(Protocol):
    def supports(self, url: str) -> bool: ...
    async def fetch(self, ctx: AdapterContext) -> AdapterResult: ...
```

**Registry Priority**: API adapters > JSON-LD > scrapers
**Fallback**: If eBay API fails, try JSON-LD from same URL

### Deduplication Strategy
1. **Primary key**: `(marketplace, vendor_item_id)` when available
2. **Fallback**: Hash of `normalize(title) + seller + price`
3. **Upsert behavior**: Update `last_seen_at`, emit `listing.updated` event

### Rate Limiting Approach
- Per-domain configuration in `ApplicationSettings`
- Default: API adapters per vendor quota, JSON-LD 6 req/min, scrapers 2 pages/min
- Use `httpx` with custom transport for rate limiting

---

## Next Steps

### Immediate (Next Session)
1. Start Phase 1: Foundation
2. Create Alembic migration for Listing model extensions
3. Implement base adapter protocol and registry
4. Build HTTP client wrapper with rate limiting

### Dependencies to Install
```bash
poetry add beautifulsoup4 lxml extruct url-normalize
# eBay SDK if using official client (or just httpx + Browse API)
```

### Questions for Product Owner
- eBay API credentials available? (App ID, OAuth tokens)
- Amazon PA-API credentials? (Access Key, Secret, Associate Tag)
- Priority: eBay first, or generic JSON-LD for broader coverage?
- Rate limit tolerances per domain?

---

## Risks Identified

1. **eBay API Gating**: May require business approval
   - *Mitigation*: Start with JSON-LD, add API incrementally

2. **Spec Extraction Accuracy**: Regex parsing is brittle
   - *Mitigation*: Show provenance, allow manual edits, iterate on patterns

3. **Anti-bot Defenses**: Retailers may block scraping
   - *Mitigation*: API-first, low concurrency, respect robots.txt, per-domain toggles

4. **Deduplication False Positives**: Different variants merged incorrectly
   - *Mitigation*: Conservative hash, include variant/seller, audit log

---

## Action Items

- [x] Create PRD tailored to Deal Brain
- [x] Create implementation plan with 4 phases
- [x] Create tracking document
- [x] Create session notes
- [ ] Commit all documents to git
- [ ] Schedule kick-off meeting for Phase 1

---

## Resources & References

- **Original Generic PRD**: `docs/project_plans/url-ingest/prd-url-ingest.md`
- **Deal Brain CLAUDE.md**: Architecture overview, commands, patterns
- **ImportSession Service**: `apps/api/dealbrain_api/services/imports/service.py`
- **Listing Model**: `apps/api/dealbrain_api/models/core.py:340-426`
- **Celery Worker**: `apps/api/dealbrain_api/worker.py`
- **Docker Compose**: `docker-compose.yml` (ports, services)

---

## Session Metrics

- **Codebase files explored**: ~25 files
- **Lines of code analyzed**: ~5,000 lines
- **Documentation created**: 4 files, ~1,600 lines total
- **Effort estimated**: 340 hours (6 weeks)
- **Tasks identified**: 30 implementation tasks
- **Phases planned**: 4 phases (Foundation, Scraping, API, Frontend)

---

*End of session notes*
