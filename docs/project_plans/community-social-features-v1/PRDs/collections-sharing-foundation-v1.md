---
title: "Collections & Sharing Foundation (Phase 1)"
description: "Pre-Black Friday MVP for Deal Brain's community features: shareable deal pages, user-to-user sharing, private collections, and workspace views."
audience: [ai-agents, developers, pm, design]
tags: [collections, sharing, community, social, deal-cards, mvp]
created: 2025-11-14
updated: 2025-11-14
category: "product-planning"
status: draft
related:
  - /docs/project_plans/requests/needs-designed/collections-community/feature-request-collections-more.md
---

# Deal Brain Collections & Sharing Foundation - Product Requirements Document

**Version:** 1.0
**Created:** November 14, 2025
**Updated:** November 14, 2025
**Status:** Draft (Planning)
**Owner:** Product & Engineering
**Target Launch:** Pre-Black Friday 2025

---

## Executive Summary

This PRD defines **Phase 1: Collections & Sharing Foundation**, Deal Brain's first community-centric release. The phase transforms Deal Brain from a **solo deal evaluator** into a **shared decision tool** by enabling users to share individual deals, organize them into collections, and collaborate on purchase decisions.

### Phase Scope

**In-Scope Features:**
- **FR-A1:** Shareable Deal Pages (public, read-only "deal cards" via link)
- **FR-A3:** User-to-User Deal Sharing (send deals to other users, receive & import)
- **FR-A5:** Send-to-Collection (add shared items directly to collections)
- **FR-B1:** Private Collections (user-defined groupings of deals)
- **FR-B2:** Collections Workspace View (comparison & notes interface)

**Out-of-Scope (Phase 2+):**
- Shareable collections (FR-B3), static card images (FR-A2), portable deal artifacts (FR-A4)
- Community catalog, voting, profiles (FR-C1–C3)
- Collaborative collections (FR-B4)

### Business Impact

- **Acquisition:** Shareable links introduce new users to Deal Brain organically
- **Engagement:** Collections transform browsing into active decision-making
- **Retention:** Users return to compare options and finalize purchases
- **Community:** Foundation for future public sharing and curation features

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Deal share click-through rate | >5% of shares generate visits | Link tracking analytics |
| Collection creation rate | >15% of active users create ≥1 collection | Event tracking |
| Collection engagement | >70% of collections have ≥3 items with notes | Usage analytics |
| User-to-user shares completed | >200 shares/month by month 3 | Share event tracking |
| Share-to-import conversion | >40% of shares result in import | Funnel analysis |

---

## Problem Statement

### Current State

Deal Brain is a **solo evaluator**: users browse listings, see scores, and make decisions in isolation. Sharing requires copying links from external marketplaces; Deal Brain's analysis doesn't follow. Organizing multiple candidate deals requires external tools (spreadsheets, notes, bookmarks).

### User Pain Points

1. **"I want my friend to see this deal *with* Deal Brain's verdict, not just the raw store link."**
   - Users resort to describing the deal verbally or copying metrics manually
   - Loss of Deal Brain's context and explainability

2. **"How do I compare 3–4 candidates side-by-side for my build?"**
   - No native workspace in Deal Brain for comparative analysis
   - Users fall back to spreadsheets, Google Docs, or other tools

3. **"Can I organize my candidates by use case (builds, budgets, timelines)?"**
   - No grouping mechanism; all deals exist in a flat list
   - Difficult to return to candidates later in the buying process

---

## Goals & Objectives

### Primary Goals

**G1: Enable Sharable Deal Context**
- Create shareable public pages for individual deals
- Ensure shared pages display Deal Brain's evaluation and explainability
- Support major platforms (Slack, Discord, Reddit, X) via link previews

**G2: Support User-to-User Sharing**
- Allow authenticated users to share deals directly (or via link)
- Enable recipients to preview and import deals without friction
- Establish the pattern for future collaborative workflows

**G3: Enable Collections as Decision Workspace**
- Allow users to create named, private collections of deals
- Provide a comparison view with notes and item status tracking
- Make collections the primary way users organize candidates

**G4: Measure Adoption & Refine**
- Establish clear metrics for each feature
- Identify high-value users and use cases
- Inform Phase 2 scope and prioritization

### Success Criteria

| Goal | Metric | Baseline | Target |
|------|--------|----------|--------|
| G1 | Shareable deal pages created | 0 | 200/month by month 3 |
| G1 | Share-generated new-user signups | 0 | 50/month by month 3 |
| G2 | User-to-user shares | 0 | 200/month by month 3 |
| G2 | Share-to-import conversion | N/A | >40% |
| G3 | Collections created per active user | 0 | 0.2 (20% penetration) |
| G3 | Items per collection (average) | 0 | ≥3 items |
| G3 | Collections with notes | 0 | >70% of active collections |

---

## User Stories & Use Cases

### Personas

**P1: Deal Hunter (Primary)**
- Actively researches 2–5 candidate PCs before purchasing
- Values transparency in pricing and scoring
- Wants to share discoveries with friends and communities

**P2: Collaborative Buyer (Secondary)**
- Plans purchases with others (co-buyers, team builds)
- Needs to compare options synchronously or asynchronously
- Prefers structured, shared workspace over back-and-forth messaging

**P3: Community Power User (Emerging)**
- Finds deals and wants to share curated lists with others
- Interested in becoming a trusted curator (future Phase 2)
- Values public recognition of good finds

### Use Cases

#### UC1: Share a Deal in Discord
**Actor:** P1 (Deal Hunter)
**Precondition:** User finds a great deal in Deal Brain
**Flow:**
1. User clicks "Share" button on listing
2. Clipboard copies shareable link (or QR code appears)
3. User pastes link in Discord channel
4. Friends see link preview with deal image, score, and price
5. Friends click to view full deal page (with or without login)

**Target Experience:** One click; frictionless sharing

#### UC2: Send Deal to Specific User
**Actor:** P1 (Deal Hunter)
**Precondition:** User has identified a deal relevant to a friend
**Flow:**
1. User clicks "Share with User" on listing (or search UI)
2. User selects or searches for friend by username
3. Friend receives notification: "Nick shared a deal: [Deal Name]"
4. Friend clicks notification → lands on shared deal preview page
5. Friend imports deal with one click
6. Deal appears in friend's workspace (or default collection)

**Acceptance Criteria:**
- [ ] Share modal appears without navigation away from listing
- [ ] Search finds users by username (exact match, no autocomplete initially)
- [ ] Shared deal preview loads in <1s
- [ ] Import button visible and functional without additional modals
- [ ] Imported deal retains all original metadata (price, score, valuation breakdown)

#### UC3: Build a Collection & Compare
**Actor:** P2 (Collaborative Buyer)
**Precondition:** User and friend are researching builds together
**Flow:**
1. User opens Deal Brain, clicks "New Collection"
2. User enters: "Black Friday 2025 SFF Gaming (<$800)"
3. User adds friend's shared deals + own finds
4. Collections workspace shows:
   - Listings in side panel (price, CPU, GPU, score)
   - Comparison table (price, CPU Mark, $/mark, power draw)
   - Notes area (pros/cons, status per item: shortlisted, rejected, bought)
5. User pins top 2 candidates for final decision
6. User exports selection (CSV, JSON) for final review

**Acceptance Criteria:**
- [ ] Collection creation completes in <1 interaction
- [ ] Add items via: search, share, import, recent browsing
- [ ] Comparison table supports 6+ columns (name, price, CPU, GPU, $/mark, form factor)
- [ ] Notes saved per item (rich text, optional)
- [ ] Item status tracking: shortlisted, rejected, bought, undecided
- [ ] Sort & filter by column (price range, CPU family, form factor)

#### UC4: Import & Organize Shared Deal
**Actor:** P1 (Deal Hunter)
**Precondition:** Friend sends a deal share link
**Flow:**
1. User receives share notification or link
2. User clicks → lands on shared deal preview
3. User sees: deal image, specs, price, Deal Brain score, valuation breakdown
4. User clicks "Add to Collection"
5. Modal shows: create new collection OR select from existing (max 5 suggestions)
6. User selects or creates collection
7. Deal added; user returns to collection view

**Acceptance Criteria:**
- [ ] Preview page loads without friction (1-2s max)
- [ ] Collection selector shows max 5 recent + recommended (not all)
- [ ] Create-new-collection form appears inline (no page reload)
- [ ] Deal imported with all original metadata

---

## Detailed Requirements

### FR-A1: Shareable Deal Pages

**Scope:** Public, read-only pages for individual deals (shareable via link).

**Public Deal Page Specifications:**

| Requirement | Specification |
|------------|---------------|
| URL Pattern | `/deals/{listing_id}/public/{share_token}` (unlisted, not indexed) |
| Authentication | None required (public link, no account needed) |
| Visibility | Not indexed by search engines; only accessible via shared link |
| Content | Listing image, specs, price, Deal Brain score, valuation breakdown, timestamp |
| Link Preview | Open Graph meta tags for Slack, Discord, X (title, image, description) |
| Call-to-Action | "View Full Details" (if logged in) or "Sign Up to Compare" (if logged out) |
| Expiration | Optional: admin-configurable expiry (default: 6 months) |

**Technical Architecture:**

- Backend: New endpoint `GET /listings/{id}/share/{token}` returns deal snapshot (read-only)
- Database: `ListingShare` table (listing_id, share_token, created_by, created_at, expires_at)
- Frontend: New page `/deals/[id]/[token].tsx` (static generation from listing)
- Caching: Cache OpenGraph snapshot for 24 hours (platform link crawler optimization)

---

### FR-A3: User-to-User Deal Sharing

**Scope:** Send deals to authenticated users; preview and import.

**Share Features:**

| Feature | Specification |
|---------|---------------|
| Share UI | Button on listing detail page, search results, data table |
| Recipient Selection | Search by username (exact or prefix match) |
| Notification | In-app notification + optional email |
| Recipient View | Shared deal preview (no auth required, but identifies sender) |
| Import Action | One-click import to user's workspace or default collection |
| Deduplication | System warns if deal already in user's workspace |
| Expiration | Share link valid for 30 days (configurable) |

**Technical Schema:**

```sql
-- New table for user-to-user shares
CREATE TABLE user_shares (
  id UUID PRIMARY KEY,
  sender_id UUID NOT NULL REFERENCES users(id),
  recipient_id UUID NOT NULL REFERENCES users(id),
  listing_id UUID NOT NULL REFERENCES listings(id),
  share_token VARCHAR(64) UNIQUE,
  message TEXT,  -- Optional personal message
  shared_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  viewed_at TIMESTAMP,
  imported_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_shares_recipient ON user_shares(recipient_id, expires_at);
CREATE INDEX idx_user_shares_token ON user_shares(share_token);
```

---

### FR-A5: Send-to-Collection

**Scope:** Allow users to add shared or imported deals directly to collections.

**UX Specifications:**

1. **From Shared Deal Preview:**
   - "Add to Collection" button visible in hero section
   - Modal shows: suggested collections (max 5 recent), create-new option
   - User selects and confirms

2. **From Search/Browse:**
   - Context menu or quick action on listing card
   - Modal similar to above
   - Collection selector appears inline

**Technical:**

- Reuse existing `collection_items` table (no new schema)
- Add service method: `add_to_collection(listing_id, collection_id, user_id)`
- Validate collection ownership before adding item

---

### FR-B1: Private Collections

**Scope:** User-created groupings of deals, fully private.

**Collection Features:**

| Feature | Specification |
|---------|---------------|
| Name | Required, ≤100 chars, user-defined |
| Description | Optional, markdown support |
| Visibility | Private by default (owner only) |
| Items | Ordered list of listings; supports up to 100 items per collection |
| Item Notes | Per-item rich text notes (max 500 chars) |
| Item Status | Enum: undecided, shortlisted, rejected, bought |
| Sorting | User-defined order (drag-and-drop) or by column (price, score) |
| Created/Updated | Timestamps |

**Database Schema:**

```sql
CREATE TABLE collections (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(100) NOT NULL,
  description TEXT,
  visibility ENUM('private', 'unlisted', 'public') DEFAULT 'private',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE collection_items (
  id UUID PRIMARY KEY,
  collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
  listing_id UUID NOT NULL REFERENCES listings(id),
  status ENUM('undecided', 'shortlisted', 'rejected', 'bought') DEFAULT 'undecided',
  notes TEXT,
  position INT,  -- For user-defined ordering
  added_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(collection_id, listing_id)
);

CREATE INDEX idx_collections_user ON collections(user_id);
CREATE INDEX idx_collection_items_collection ON collection_items(collection_id);
```

---

### FR-B2: Collections Workspace View

**Scope:** Dedicated view for viewing, comparing, and annotating collections.

**Workspace Layout:**

```
┌─────────────────────────────────────────────────────┐
│ [Collection Name]  [Edit]  [Export]  [More...]      │
├─────────────────────────────────────────────────────┤
│ [Filters: Price, CPU, Form Factor]  [Sort] [View]   │
├──────────────────────────────────────────────────────┤
│ Name        Price   CPU      GPU      $/Mark Status  │
├──────────────────────────────────────────────────────┤
│ [Item] [Checkbox] [Data columns...] [Status] [Notes] │
├──────────────────────────────────────────────────────┤
│ [Notes Area: Free-form comparison notes]            │
└─────────────────────────────────────────────────────┘
```

**Features:**

| Feature | Specification |
|---------|---------------|
| Item List | Table or card view (user preference) |
| Columns | Name, price, CPU, GPU, $/CPU Mark, form factor, score, condition |
| Sorting | Click column header to sort; maintain sort preference |
| Filtering | By price range, CPU family, form factor, score threshold |
| Selection | Checkboxes for bulk actions (compare, export, remove) |
| Per-Item Notes | Click item → expand side panel with notes editor |
| Status Badge | Color-coded badge per item (undecided, shortlisted, etc.) |
| Notes Editor | Markdown support; auto-save to backend |
| Comparison Export | CSV or JSON export of selected items |
| Mobile View | Stack items vertically; table becomes card view |

**API Endpoints:**

- `GET /collections/{id}` → Collection with all items and metadata
- `POST /collections` → Create new collection
- `PATCH /collections/{id}` → Update name, description, visibility
- `DELETE /collections/{id}` → Delete collection
- `POST /collections/{id}/items` → Add item to collection
- `PATCH /collections/{id}/items/{item_id}` → Update item status, notes, position
- `DELETE /collections/{id}/items/{item_id}` → Remove item from collection
- `GET /collections/{id}/export` → Export as CSV/JSON

---

## Technical Architecture

### Data Flow: Share → Import → Collect

```
Listing Detail Page
  ↓ [Share Button]
  ├─ Generate share_token (secure random 64 chars)
  ├─ Create ListingShare record
  ├─ Return shareable link: /deals/{id}/{token}
  │
  └─ User copies link → shares in chat
    ↓
    Public Deal Page (/deals/{id}/{token})
    ├─ Fetch ListingShare + Listing (via token)
    ├─ Render read-only deal preview
    ├─ Display Open Graph meta tags
    │
    └─ [Add to Collection] button
      ↓
      Collection Selector Modal
      ├─ List recent collections (max 5)
      ├─ Show "Create New Collection" option
      │
      └─ User selects/creates → add_to_collection()
        ↓
        Collections Workspace
        ├─ Item appears in table/card view
        ├─ User can add notes, change status
        ├─ Can compare with other items, export
```

### Backend Layer Structure

**Database** (PostgreSQL with async SQLAlchemy)
- `ListingShare` table (for FR-A1)
- `UserShare` table (for FR-A3)
- `Collection` and `CollectionItem` tables (for FR-B1/B2)

**Services** (`apps/api/dealbrain_api/services/`)
- `sharing_service.py` → generate share tokens, validate access
- `collections_service.py` → CRUD collections, manage items
- `shares_repository.py` → queries for shares (read-only from public link)

**API Routers** (`apps/api/dealbrain_api/api/`)
- `routers/listings.py` → add `POST /listings/{id}/share` endpoint
- `routers/shares.py` → public share endpoints (`GET /deals/{id}/{token}`)
- `routers/collections.py` → full collections CRUD
- `routers/user_shares.py` → user-to-user share endpoints

**Schemas** (Pydantic, `packages/core/schemas/`)
- `CollectionSchema`, `CollectionItemSchema`
- `ShareTokenSchema`, `ListingShareSchema`, `UserShareSchema`

### Frontend Architecture

**Pages** (`apps/web/app/`)
- `/collections` → list user's collections
- `/collections/[id]` → collection detail + workspace view
- `/deals/[id]/[token]` → public shareable deal page

**Components** (`apps/web/components/`)
- `CollectionsList.tsx` → card grid of user's collections
- `CollectionWorkspace.tsx` → main comparison view with table/cards
- `CollectionItemRow.tsx` → single item with inline notes, status
- `CollectionSelector.tsx` → modal for adding items to collections
- `PublicDealPage.tsx` → shareable deal page (no auth required)
- `ShareButton.tsx` → share modal/menu (for all listing contexts)

**Hooks** (`apps/web/hooks/`)
- `useCollection(id)` → fetch and manage collection
- `useCollections()` → list all user collections
- `useShare(listing_id)` → generate and manage share links

---

## Success Metrics & Monitoring

### Core Metrics

| Metric | Baseline | Target | Tool |
|--------|----------|--------|------|
| Shareable pages created/month | 0 | 200 by month 3 | Event tracking |
| Share-to-visit conversion | N/A | >5% | Link UTM tracking |
| New user signups from shares | 0 | 50/month | Analytics attribution |
| Collections created (cumulative) | 0 | 100 by month 2 | Event tracking |
| Avg items per active collection | 0 | ≥3 | Usage queries |
| Collections with notes (%) | N/A | >70% | Usage queries |
| User-to-user share completion | 0 | 200/month | Event tracking |
| Share-to-import conversion (%) | N/A | >40% | Funnel analysis |

### Telemetry Events

**Sharing:**
- `share_created` (listing_id, share_type: public/private)
- `share_accessed` (share_token, utm_source, viewer_logged_in)
- `share_imported` (share_token, import_to_collection_id)

**Collections:**
- `collection_created` (name, item_count_at_creation)
- `collection_item_added` (source: search/share/import, status_set)
- `collection_item_status_changed` (old_status, new_status)
- `collection_notes_edited` (length, save_count)
- `collection_exported` (format: csv/json, item_count)

---

## Timeline & Milestones

### High-Level Phases

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1: Backend Infrastructure** | Week 1 | Share token generation, ListingShare/UserShare/Collection schema, basic CRUD services |
| **Phase 2: Sharing UI & Public Pages** | Week 2 | Share buttons (listings detail, search), public deal pages, Open Graph meta tags |
| **Phase 3: Collections Core** | Week 2-3 | Collection CRUD, collection item management, workspace view (table/cards) |
| **Phase 4: Integration & Polish** | Week 3-4 | Send-to-collection flow, notes/status features, notifications, mobile optimization |
| **Phase 5: Testing & Launch** | Week 4-5 | E2E testing, performance optimization, documentation, staged rollout |

### Key Milestones

- **M1 (End Week 1):** Backend schemas created, migrations ready
- **M2 (End Week 2):** Shareable deal pages live, user-to-user shares functional
- **M3 (End Week 3):** Collections workspace live, basic comparison working
- **M4 (End Week 4):** Full integration tested, mobile-optimized
- **M5 (End Week 5):** Production launch (internal → beta → public)

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Link preview rendering fails on platforms | Medium | Medium | Pre-generate OG images, test on Slack/Discord/X |
| Collection item limit (100) too low | Low | Medium | Monitor usage; increase limit in Phase 1.5 if needed |
| Share token enumeration attack | Low | High | Use secure random 64-char tokens, rate-limit share creation |
| Notification spam (too many shares) | Medium | Medium | Batch notifications, user preferences (digest/real-time) |
| Mobile table UI becomes unreadable | Medium | Medium | Switch to card view on mobile, test on real devices |
| Performance (N+1 queries on collections) | Medium | Medium | Eager load collection items, cache collection metadata |

---

## Success Criteria (Acceptance)

All features must meet these criteria before Phase 1 launch:

### Sharing (FR-A1 & FR-A3)
- [ ] Shareable links generate working link previews on Slack, Discord, X
- [ ] Public deal page accessible without authentication
- [ ] Share token validation prevents unauthorized access
- [ ] User-to-user shares send notifications
- [ ] Shared deal import creates item in recipient's workspace

### Collections (FR-B1 & FR-B2)
- [ ] Collection creation, editing, deletion works end-to-end
- [ ] Items added to collections via: search, share, direct add
- [ ] Workspace table renders 100+ items without performance degradation
- [ ] Notes and status updates save automatically
- [ ] Filtering and sorting work without page reload
- [ ] Export (CSV/JSON) includes all relevant item data

### Integration (FR-A5)
- [ ] Shared deal preview includes "Add to Collection" button
- [ ] Collection selector modal appears without navigation
- [ ] Item added to collection with one click
- [ ] Imported item retains all original metadata

### Testing
- [ ] All new endpoints tested (unit + integration)
- [ ] E2E tests cover: share creation → public page view → import → collection view
- [ ] Mobile views tested on real devices (iOS 14+, Android 11+)
- [ ] Accessibility audit passed (WCAG AA)
- [ ] Performance targets met: page load <2s, interactions <100ms

---

## References

- Source Feature Request: `/docs/project_plans/requests/needs-designed/collections-community/feature-request-collections-more.md`
- Project Architecture: `/CLAUDE.md`
- Related Ticketed Work: Phase 2 (Shareable Collections), Phase 3 (Community Catalog)

---

**Document Status:** Ready for stakeholder review
**Next Steps:** Design approval → Implementation plan → Engineering kickoff
