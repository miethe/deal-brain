# Deal Brain Collections Enhancement & Export – Phase 2 PRD

**Version:** 1.0
**Created:** 2025-11-14
**Updated:** 2025-11-14
**Status:** Planning
**Owner:** Product & Engineering
**Target Timeline:** Post-Black Friday (Medium Priority)

---

## Executive Summary

This PRD defines Phase 2 of Deal Brain's community and sharing evolution: extending private collections (Phase 1) into public/shareable entities, enabling static card image export for social sharing, and providing portable deal artifact formats for external tools and workflows.

### Phase 2 Scope (Post-Black Friday)

1. **Shareable Collections (FR-B3)** – Public/unlisted read-only collection links with discovery and copying capabilities
2. **Shareable Deal Card Images (FR-A2)** – Static visual card generation for social media and forums
3. **Export/Import Portable Artifacts (FR-A4)** – Standardized deal and collection formats for backup, external tools, and agent workflows

### Business Impact

- **Community Engagement:** Enable users to become curators, extending reach beyond individual deals
- **Content Portability:** Support power users, external workflows, and AI agent integrations
- **Visual Sharing:** Unblock sharing in environments with poor link preview support (forums, chat apps)
- **User Retention:** Encourage collection creation, curation, and ongoing engagement

### Success Metrics (Target)

- **Adoption:** 25%+ of active users share ≥1 collection or export a deal within first month
- **Engagement:** Shared collection views generate measurable traffic; 15%+ copy rate
- **Quality:** Exported deals remain valid and reusable across versions (zero breaking changes in v1.0)
- **Performance:** Card image generation < 3 seconds; export JSON < 500KB for typical collection

---

## Dependencies & Phase 1 Reference

**This phase requires Phase 1 completion:**

- Private collections created, stored, and queryable (FR-B1)
- Collection workspace view with item list and per-item notes (FR-B2)
- Shareable individual deal pages / links (FR-A1) [required for card context]
- User-to-user deal import flows (FR-A3, FR-A5) [required for portable format alignment]

**Phase 1 Assumptions for Phase 2 Design:**

- Collections have `id`, `name`, `description`, `user_id`, `created_at`, `updated_at`, `visibility: 'private'`
- Listings (deals) are queryable with full valuation breakdown, components, and metadata
- Deal pages exist at `/deals/{listing_id}` with shareable link
- User shares include notion of snapshot vs. current state

---

## Problem Statement

### Gap 1: Collections Are Private-Only

**Current State:** Phase 1 collections are private; users cannot share curation or influence others.

**User Pain:**
- "I found 5 great Plex boxes; I want to send this list to my Discord community, not individually."
- "I want to publish my 'Top Budget Gaming Boxes 2025' and see if others agree."

**Business Gap:** No content network effect or community feedback loop.

---

### Gap 2: Sharing Requires Links (No Previews in Weak Environments)

**Current State:** Individual deal sharing relies on link previews; forums and some chat apps strip metadata.

**User Pain:**
- "Screenshots are clearer than links on Reddit; I have to export manually."
- "I want a clean image I can drop into Slack when a screenshot won't render."

**Business Gap:** Reduced sharing in key communities where deals are discovered.

---

### Gap 3: No Deal Portability or Backup

**Current State:** Collections and deals exist only in Deal Brain; no way to export for external use.

**User Pain:**
- "I want to back up my evaluations in case the service goes down."
- "I want to attach deal data to Jira tickets or project docs."
- "Can I send a deal to an external analysis tool?"

**Business Gap:** Vendor lock-in perception; missed integration opportunities.

---

## Goals & Non-Goals

### Goals

- **G1:** Enable users to share curated collections via public/unlisted links with discoverable, read-only views
- **G2:** Provide static card image generation for deals, suitable for social media and forums
- **G3:** Export deals and collections as portable, versioned artifacts (JSON) for backup, external tools, and workflows
- **G4:** Maintain clarity between **snapshot time** (when shared) and **current state** (live prices/availability)
- **G5:** Implement visibility model (private → unlisted → public) with minimal moderation burden for v1.0

### Non-Goals

- Community discovery catalog (FR-C1; Phase 3)
- Collaborative/multi-user collection editing (FR-B4; Phase 3)
- Voting, reputation, or advanced ranking (FR-C2, FR-C3; Phase 3)
- Affiliate link tracking or monetization
- Watermark or branding on card images (keep neutral for user trust)
- Complex access control (share with specific users); public or unlisted only for v1.0

---

## Detailed Feature Specifications

### Feature 1: Shareable Collections (FR-B3)

#### 1.1 Visibility Model

**Visibility Attribute:** Add `visibility: enum('private', 'unlisted', 'public')` to `Collection` table (default: 'private').

| Visibility | Access | Discovery | Link Shareable | Authentication |
|-----------|--------|-----------|-----------------|-----------------|
| `private` | Owner only | No | No (403) | Required |
| `unlisted` | Anyone with link | No (not in catalog) | Yes | Optional |
| `public` | Anyone | Yes (discoverable) | Yes | Optional |

#### 1.2 Public Collection View

**Endpoint:** `GET /collections/{id}?visibility=public` (or `unlisted`)

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Top 5 SFF Plex Boxes for 2025",
  "description": "Curated list of compact, power-efficient NAS/media boxes",
  "visibility": "public",
  "owner": {
    "id": "uuid",
    "username": "curator_name",
    "profile_url": "/users/{id}"
  },
  "created_at": "2025-11-01T00:00:00Z",
  "updated_at": "2025-11-14T12:00:00Z",
  "item_count": 5,
  "items": [
    {
      "id": "listing_id",
      "name": "Dell PowerEdge R6515",
      "price": 1299.99,
      "score": 8.5,
      "components": {...},
      "valuation_breakdown": {...}
    }
  ],
  "actions": {
    "copy_to_my_collections": "/api/collections/{id}/copy",
    "view_owner_profile": "/users/{owner_id}"
  }
}
```

#### 1.3 Copy Collection to Own Workspace

**Endpoint:** `POST /collections/{id}/copy`

**Behavior:**
- Creates a new private collection owned by requesting user
- Imports all listings with snapshot metadata (price, score, timestamp)
- Preserves item notes from original collection (user can edit)
- Does **not** create a link back to original (user decides what to do with shared collection)

**Response:** `201 Created` with new collection details.

---

### Feature 2: Shareable Deal Card Images (FR-A2)

#### 2.1 Card Generation Endpoint

**Endpoint:** `GET /listings/{id}/card-image?format=png&style=light` (or `dark`)

**Parameters:**
- `format`: `png` (v1.0) or `jpeg` (future)
- `style`: `light` (white bg) or `dark` (dark theme)
- `include_score_detail`: boolean (default: false) – show full breakdown or just summary

**Response:** HTTP 200 with `Content-Type: image/png`

#### 2.2 Card Content & Layout

**Visual Elements (Required):**
- Deal Brain logo (top-left corner, transparent)
- Product name, price, key specs (CPU, RAM, storage)
- Deal Brain score (large, color-coded: green/good, yellow/fair, red/poor)
- "As of [ISO date/time]" timestamp (required; prices change)
- Brief valuation verdict text (e.g., "Great value for productivity builds")
- Link text: "View on Deal Brain: deal-brain.app/deals/{id}"

**Card Dimensions:**
- Default: 1200x630px (standard social preview)
- Mobile: 1080x1080px (Instagram, Discord)

**Design Constraints:**
- Must be legible at 200px width (smallest social preview)
- Neutral, non-salesy tone (avoid hype language)
- High contrast for accessibility

#### 2.3 Backend Implementation

**Approach:** Use headless browser (Puppeteer or Playwright) to render React component → PNG on-demand or cache.

**Caching Strategy:**
- Cache PNG files by listing ID + style for 24 hours
- Invalidate on listing price update or valuation change
- Store in S3 or similar with 30-day TTL

**Performance Target:** <3 seconds for generation (including cache miss).

---

### Feature 3: Export / Import Portable Artifacts (FR-A4)

#### 3.1 Portable Format Specification (v1.0)

**Format:** JSON (human-readable, versionable, schema-validated)

```json
{
  "deal_brain_export": {
    "version": "1.0.0",
    "exported_at": "2025-11-14T12:00:00Z",
    "exported_by": "user_id or anonymous",
    "type": "deal|collection",
    "data": { ... }
  }
}
```

**Deal Export (Individual Listing):**
```json
{
  "deal_brain_export": {
    "version": "1.0.0",
    "exported_at": "2025-11-14T12:00:00Z",
    "type": "deal",
    "data": {
      "listing": {
        "id": "uuid",
        "name": "Dell PowerEdge R6515",
        "price": 1299.99,
        "condition": "used",
        "seller": "eBay Refurbished",
        "url": "https://ebay.com/itm/...",
        "components": {
          "cpu": { "name": "AMD EPYC 7742", "mark": 45000, ... },
          "ram_gb": 16,
          "storage_gb": 500
        }
      },
      "valuation": {
        "base_price": 1299.99,
        "adjusted_price": 1150.00,
        "score": 8.5,
        "score_breakdown": {
          "price_efficiency": 8.2,
          "performance_value": 8.8,
          "condition_factor": 0.95
        },
        "rules_applied": [
          { "name": "Refurbished deduction", "adjustment": -150 },
          { "name": "High RAM value", "adjustment": +100 }
        ]
      },
      "metadata": {
        "imported_at": "2025-11-01T00:00:00Z",
        "last_updated": "2025-11-14T10:00:00Z",
        "snapshot_notes": "Price checked 2025-11-14 08:00 UTC. May change."
      }
    }
  }
}
```

**Collection Export:**
```json
{
  "deal_brain_export": {
    "version": "1.0.0",
    "exported_at": "2025-11-14T12:00:00Z",
    "type": "collection",
    "data": {
      "collection": {
        "name": "Top 5 SFF Plex Boxes",
        "description": "...",
        "created_at": "2025-11-01T00:00:00Z"
      },
      "items": [
        { "listing": {...}, "valuation": {...} },
        { "listing": {...}, "valuation": {...} }
      ]
    }
  }
}
```

#### 3.2 Export Endpoints

**Deal Export:**
- `GET /listings/{id}/export?format=json` → JSON file download
- `GET /listings/{id}/export?format=yaml` → YAML (future)

**Collection Export:**
- `GET /collections/{id}/export?format=json` → JSON with all items

**Behavior:**
- Generates file on-demand (no caching)
- Filename: `deal_brain_[type]_[id]_[YYYYMMDD].json`
- Include `Content-Disposition: attachment` header

#### 3.3 Import Endpoints

**Deal Import:**
- `POST /listings/import` with JSON payload or file upload
- Validates schema version, data presence
- Returns `201 Created` with new listing or matches to existing (fuzzy on name + price)
- User can review import preview, select duplicates, then commit

**Collection Import:**
- `POST /collections/import` with JSON file
- Creates new collection + imports all deals
- Returns preview of items to be added, user confirms

**Validation Rules:**
- Reject if `version` > current app version (might have newer schema)
- Warn if `version` < current (may be missing fields)
- Require: `listing.name`, `listing.price`, `listing.components`
- Optional: `valuation` (recalculated on import if missing)

---

## User Experience & Interaction Flow

### Share Collection Flow

1. User navigates to collection detail page
2. Clicks "Share" button (top-right)
3. Modal appears with three options:
   - **Share Link:** Display `unlisted` link, copy to clipboard
   - **Make Public:** Toggle visibility to public (modal warning: "Anyone can find this via search")
   - **Export as File:** Generate JSON, download

4. If "Make Public," link changes; user can browse `/collections/discover` to verify it appears
5. Copy link, share on Discord/Reddit/email

### Card Image Download Flow

1. User on listing detail page or in collection
2. Clicks "Share" or "Download Card" button
3. Small menu:
   - "Copy Link" (existing)
   - "Download Card Image" → Opens style picker (light/dark)
   - "Export as JSON" (new)
4. Card image downloads or appears in new tab (lazy-loaded, cached)

### Export / Import Flow

1. **Export:**
   - From listing detail or collection detail: "⋮" menu → "Export as JSON"
   - Downloads file named `deal_brain_deal_[id]_[date].json`

2. **Import:**
   - Dashboard or `/import` page: "Import Deal" button
   - Upload JSON file or paste URL (if file is hosted)
   - Preview modal shows parsed data, allows edits
   - Confirm: creates listing or merges with existing
   - On success: "Deal imported to Collections" with link to view

---

## Data Model & API Changes

### Database Schema Changes

#### Collections Table (ALTER)
```sql
ALTER TABLE collection ADD COLUMN visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('private', 'unlisted', 'public'));
ALTER TABLE collection ADD COLUMN public_slug VARCHAR(255) UNIQUE NULLABLE; -- vanity URL option
CREATE INDEX idx_collection_visibility ON collection(visibility);
CREATE INDEX idx_collection_user_visibility ON collection(user_id, visibility);
```

#### New Tables
```sql
CREATE TABLE collection_share_token (
  id UUID PRIMARY KEY,
  collection_id UUID REFERENCES collection(id) ON DELETE CASCADE,
  token VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NULLABLE,
  view_count INT DEFAULT 0
);

CREATE TABLE deal_export_cache (
  id UUID PRIMARY KEY,
  listing_id UUID REFERENCES listing(id) ON DELETE CASCADE,
  format VARCHAR(10), -- 'json', 'yaml'
  data JSONB,
  generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP,
  UNIQUE (listing_id, format)
);
```

### Pydantic Schema Changes

#### CollectionRead (add field)
```python
class CollectionRead(BaseModel):
    id: UUID
    name: str
    description: str
    visibility: Literal['private', 'unlisted', 'public'] = 'private'
    public_slug: Optional[str] = None
    owner_id: UUID
    owner: Optional[UserRead] = None  # populated only for public/unlisted
    item_count: int
    created_at: datetime
    updated_at: datetime
```

#### PortableDealExport (new)
```python
class PortableDealExport(BaseModel):
    deal_brain_export: dict = {
        "version": "1.0.0",
        "exported_at": datetime,
        "type": "deal",
        "data": {
            "listing": ListingRead,
            "valuation": ValuationRead,
            "metadata": dict
        }
    }
```

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `PATCH` | `/collections/{id}` | Update visibility, name, description |
| `GET` | `/collections/{id}?public=true` | Fetch public/unlisted collection |
| `POST` | `/collections/{id}/copy` | Copy collection to own workspace |
| `GET` | `/collections/discover` | Browse public collections (pagination, search, sort) |
| `GET` | `/listings/{id}/export` | Export deal as JSON |
| `POST` | `/listings/import` | Import deal from JSON file or URL |
| `GET` | `/listings/{id}/card-image` | Generate or fetch card image |
| `GET` | `/collections/{id}/export` | Export collection as JSON |
| `POST` | `/collections/import` | Import collection from JSON |

---

## Non-Functional Requirements

| Requirement | Target | Notes |
|------------|--------|-------|
| **Card Image Generation** | <3 sec @ p95 | Cache aggressively; use CDN |
| **Export JSON Size** | <500 KB per collection | Limit to 100 items; paginate if larger |
| **Public Collection View** | <200 ms @ p95 | Cache read; optimize query |
| **Import Validation** | <1 sec | Run async if >10 items |
| **Backward Compatibility** | 100% | New fields optional; old exports must parse |
| **Data Integrity** | ACID | Transactions for export/import operations |
| **Security** | OWASP | Validate uploaded JSON, sanitize user input, rate-limit imports |

---

## Success Metrics & Acceptance Criteria

### Phase 2 Acceptance Criteria

#### FR-B3: Shareable Collections

- [ ] Collection visibility toggle (`private`, `unlisted`, `public`) implemented and persisted
- [ ] Public collection view accessible at `/collections/{id}` with read-only rendering
- [ ] Copy collection to own workspace works; creates new private collection with all items
- [ ] Public collections appear in `/collections/discover` page with search and filter
- [ ] User can toggle visibility; link changes; warning shown when making public
- [ ] No regression in Phase 1 private collection features

#### FR-A2: Card Images

- [ ] Endpoint `GET /listings/{id}/card-image` generates PNG (light & dark styles)
- [ ] Card includes: product name, price, score, timestamp, "As of [date]" text
- [ ] Card is legible at 200px width and renders correctly on social platforms
- [ ] Image generation completes <3 sec; caching works (24-hr TTL)
- [ ] Download flow integrated into listing detail and collection items

#### FR-A4: Portable Artifacts

- [ ] Deal export (`/listings/{id}/export`) generates valid v1.0.0 JSON
- [ ] Deal import (`POST /listings/import`) accepts JSON, validates, returns preview
- [ ] Collection export/import works; all items included
- [ ] Exported deals can be re-imported without loss of data (round-trip test)
- [ ] Exported JSONs remain valid across minor API version changes (backward compatibility)
- [ ] Import handles duplicates gracefully (merge or skip); user has choice

### Quantitative Success Metrics (Target)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Collection share rate | 25% of active users share ≥1 collection | GA event tracking |
| Public collection discovery | 15%+ copy rate | Collection copy counts |
| Card image usage | 10%+ of shared deals use card image | Link in POST requests |
| Export/import adoption | 5% of users export a deal | API call tracking |
| Shared collection views | 100+ views per shared collection (avg) | Page view tracking |
| Card image performance | <3 sec @ p95 | APM metrics |

---

## Implementation Phases

### Phase 2a: Shareable Collections & Public Discovery (Weeks 1–3)

**Tasks:**
1. Add `visibility` column to collections table
2. Implement public collection view endpoint + UI template
3. Build "Make Public" / visibility toggle UI
4. Implement collection copy endpoint
5. Build `/collections/discover` page (list, search, filter by name/owner)
6. Update collection detail sidebar with visibility indicator
7. Add telemetry events (visibility changed, collection copied, viewed)
8. Integration testing + E2E tests

**Deliverable:** Users can share and copy collections; public collections discoverable.

---

### Phase 2b: Card Image Generation (Weeks 2–4, can overlap with 2a)

**Tasks:**
1. Evaluate headless browser (Puppeteer/Playwright) and S3 setup
2. Implement card image template (React component or static design)
3. Implement image generation endpoint (`GET /listings/{id}/card-image`)
4. Add caching layer (Redis for metadata, S3 for images)
5. Implement download UI button in listing detail + collection items
6. Test rendering on multiple styles (light/dark)
7. Performance optimization (cache hit, CDN delivery)

**Deliverable:** Users can download card images; images render correctly on social platforms.

---

### Phase 2c: Export / Import Artifacts (Weeks 3–5)

**Tasks:**
1. Define v1.0.0 portable format JSON schema
2. Implement deal export endpoint + validation
3. Implement deal import endpoint + validation + preview UI
4. Implement collection export/import endpoints
5. Handle duplicates (fuzzy matching on name+price)
6. Build import preview modal (show what will be imported)
7. Add merge/skip options for duplicates
8. Round-trip testing (export → import → export should be identical)
9. Backward compatibility testing (old exports should still parse)

**Deliverable:** Users can export and re-import deals/collections; formats are stable v1.0.0.

---

## Testing Strategy

### Automated Tests

**Unit:**
- Visibility toggle logic (private → public → unlisted)
- Card image URL generation and caching
- JSON export schema validation
- Import validation (required fields, data types)

**Integration:**
- Collection visibility toggle → DB update + cache invalidate
- Export endpoint → valid JSON with correct structure
- Import endpoint → creates listing with correct metadata
- Copy collection → new collection with same items (different IDs)

**E2E:**
- Share collection flow (UI → endpoint → public URL accessible)
- Download card image (UI → endpoint → file download)
- Export → import round-trip (data fidelity)

**Performance:**
- Card image generation: <3 sec @ p95
- Export JSON generation: <1 sec for 100-item collection
- Public collection view: <200 ms @ p95

### Manual Testing Checklist

- [ ] Share private collection; verify link returns 404 (or login wall)
- [ ] Share unlisted collection; verify link works; not in discover
- [ ] Make collection public; verify appears in discover; can be searched
- [ ] Copy public collection; verify new collection is private; all items present
- [ ] Download card image in light and dark mode; verify legibility on mobile
- [ ] Export deal; download JSON; inspect schema and data completeness
- [ ] Import exported deal; verify all fields preserved
- [ ] Import collection with 10 items; verify all present; preview shown before confirm
- [ ] Test import with duplicate (same name/price); verify merge option works
- [ ] Test card image rendering on Discord, Slack, Twitter; verify appears correctly
- [ ] Test export file naming (should include date, ID)

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| **Public collections attract spam/inappropriate content** | Medium | High | Require login to create; flag/report option; monitor early; consider moderation in Phase 3 |
| **Card image generation slow / resource-intensive** | Medium | Medium | Cache aggressively; use lazy loading; defer to background job if >3 sec |
| **Portable format breaks with schema changes** | Low | High | Strict versioning; versioned endpoints; migration guide for major versions |
| **Import causes duplicate listings** | Medium | Low | Fuzzy matching on name+price+seller; user preview before commit |
| **Social platform previews fail on card images** | Low | Medium | Test on major platforms (Discord, Twitter, Slack); use standard dimensions (1200x630) |
| **Export files become outdated quickly** | Medium | Low | Always show "As of" timestamp; recommend re-export periodically |

---

## Assumptions & Open Questions

### Assumptions

1. Phase 1 collections are fully functional and tested
2. Deal pages (FR-A1) are public and shareable with good social previews
3. Headless browser (Puppeteer or Playwright) is acceptable for image generation
4. S3 or similar object storage is available for image caching
5. Users expect public collections to be **fully indexed** for search/discovery
6. No affiliate tracking or monetization in v1.0

### Open Questions (for PM/Design Review)

1. **Collection Thumbnails:** Should public collections show a composite image (first N items) or just text?
2. **Card Image Customization:** Should users be able to customize card design (colors, layout) or keep it standardized?
3. **Expiry & Versioning:** Should exported deals include an expiry hint (e.g., "expires 2026-02-14") or always be fresh?
4. **Rate Limiting:** Should there be limits on card image generation or export/import per user?
5. **User Profile Pages:** Should there be a `/users/{id}` profile showing their public collections and top deals?
6. **Notifications:** Should collection owner be notified when someone copies their collection?

---

## References & Related Documentation

- **Feature Request:** `/docs/project_plans/requests/needs-designed/collections-community/feature-request-collections-more.md`
- **Phase 1 PRD:** (reference when available)
- **Design System:** (colors, typography, component library)
- **API Documentation:** `/docs/api/` (base URL, auth, response formats)

---

## Appendix A: Example User Scenarios

### Scenario 1: Community Curator Shares Collection

1. **Alex** curates "Best Budget Plex Boxes 2025" (Phase 1 private collection)
2. She clicks "Share" → Selects "Make Public"
3. Link: `deal-brain.app/collections/plex-boxes-2025`
4. She posts on Reddit's `/r/homelab` and Discord
5. **30 days later:** 400 views, 60 copies, 10 people message her asking for updates

### Scenario 2: Power User Exports Deals for Documentation

1. **Bob** has 5 candidate systems in a collection
2. He exports collection → `deal_brain_collection_[uuid]_20251114.json`
3. Embeds JSON in GitHub issue for his homelabbing group
4. Each team member can import → compare in their own Deal Brain
5. Team works async without vendor lock-in

### Scenario 3: Social Sharing via Card Image

1. **Charlie** finds a killer deal in Deal Brain
2. Clicks "Share" → "Download Card Image" → Light theme
3. Gets PNG image: `deal_brain_card_dell_r6515_20251114.png`
4. Pastes directly into Discord (no link preview needed)
5. 5 friends see the image, scores, and "View on Deal Brain" link

---

## Appendix B: JSON Schema (v1.0.0)

See separate file: `deal-brain-export-schema-v1.0.0.json`

Key validations:
- `version` must match `1.0.0` for Phase 2a
- `type` must be `deal` or `collection`
- Required fields: `listing.name`, `listing.price`, `listing.components`
- Optional fields: `valuation`, `metadata`, notes

---

## Appendix C: Card Image Design Spec

**Figma Mockup:** (link to design when available)

**Fonts & Colors:**
- Primary font: System sans-serif (Roboto or equivalent)
- Score color: Green (#10b981) for 7.5+, Yellow (#f59e0b) for 5–7.5, Red (#ef4444) for <5
- Background: Light mode: #ffffff, Dark mode: #1f2937
- Accent: Deal Brain brand blue (#3b82f6)

**Layout Grid:**
- 1200x630px @ 2x DPI = 2400x1260px internal
- Padding: 40px all sides
- Logo (top-left): 120x40px
- Score (center-right): 120x120px, large number + "/ 10" suffix

---

**End of PRD**
