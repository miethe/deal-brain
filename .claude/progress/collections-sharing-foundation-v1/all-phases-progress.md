# Collections & Sharing Foundation v1 - All Phases Progress Tracker

**Plan:** docs/project_plans/implementation_plans/features/collections-sharing-foundation-v1.md
**PRD:** docs/project_plans/PRDs/features/collections-sharing-foundation-v1.md
**Started:** 2025-11-17
**Last Updated:** 2025-11-17
**Status:** ⏳ In Progress - Phase 1.1 Complete
**Branch:** claude/execute-collections-sharing-017bUmtPQ4LNP5iX3v62JeUe

---

## Completion Status

### Overall Progress
- **Total Story Points:** 89 SP
- **Completed:** 11 SP
- **Remaining:** 78 SP
- **Completion:** 12%

### Phase Summary
- [ ] Phase 1: Database Schema & Repository Layer (21 SP) — Week 1
- [ ] Phase 2: Service & Business Logic Layer (21 SP) — Week 1-2
- [ ] Phase 3: API Layer (20 SP) — Week 2
- [ ] Phase 4: UI Layer & Integration (20 SP) — Week 2-3
- [ ] Phase 5: Integration, Polish & Performance (17 SP) — Week 3-4
- [ ] Phase 6: Testing & Launch (10 SP) — Week 4-5

### Success Criteria (Pre-Launch)
- [ ] Shareable links work with previews on Slack, Discord, X
- [ ] User-to-user sharing sends notifications and imports deals
- [ ] Collections support full CRUD, filtering, sorting, notes, status tracking
- [ ] Workspace comparison view renders 100+ items without performance issues
- [ ] E2E tests cover all critical user flows
- [ ] Mobile views tested and optimized
- [ ] WCAG AA accessibility standards met

---

## Development Checklist

### PHASE 1: Database Schema & Repository Layer (21 SP)
**Duration:** 5 days | **Focus:** Database migrations, models, repositories

#### 1.1 Database Migrations (11 SP) ✅ COMPLETE

- [x] **1.1.1** Create ListingShare table (3 SP) ✅
  - **Subagent:** data-layer-expert
  - **Description:** Alembic migration for public deal shares
  - **Acceptance:** Table created with share_token, expires_at, view_count; Indexes on token and listing_id; Migration reversible
  - **Status:** Migration file created in 0028_add_collections_and_sharing_tables.py
  - **Notes:** Adapted to use Integer IDs instead of UUIDs to match existing codebase patterns

- [x] **1.1.2** Create UserShare table (3 SP) ✅
  - **Subagent:** data-layer-expert
  - **Description:** Alembic migration for user-to-user shares
  - **Acceptance:** Table with sender, recipient, share_token, expires_at; Indexes on recipient and token; Unique constraint on token; Relationships to users table
  - **Status:** Migration file created in 0028_add_collections_and_sharing_tables.py
  - **Notes:** Includes expires_at default of 30 days; viewed_at and imported_at tracking fields added

- [x] **1.1.3** Create Collection tables (3 SP) ✅
  - **Subagent:** data-layer-expert
  - **Description:** Alembic migrations for Collection and CollectionItem
  - **Acceptance:** Collections table with user_id, name, description, visibility, timestamps; CollectionItem table with collection_id, listing_id, status enum, notes, position; Cascade delete on collection removal; Unique constraint on (collection_id, listing_id)
  - **Status:** Migration file created in 0028_add_collections_and_sharing_tables.py
  - **Notes:** Check constraints added for visibility and status enums; position column nullable for flexible ordering

- [x] **1.1.4** Create indexes & constraints (2 SP) ✅
  - **Subagent:** data-layer-expert
  - **Description:** Optimize query performance for collections
  - **Acceptance:** Indexes on (user_id) for collections; Indexes on (collection_id) for items; Check constraint on item status enum; Position column supports drag-and-drop ordering
  - **Status:** All indexes created in migration file
  - **Notes:** Includes composite index on user_share(recipient_id, expires_at) for efficient inbox queries

#### 1.2 SQLAlchemy Models (6 SP)

- [ ] **1.2.1** ListingShare model (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** SQLAlchemy ORM model for public shares
  - **Acceptance:** Model in apps/api/dealbrain_api/models/core.py; Async-compatible; Relationships to Listing; Token generation utility; Expiry validation

- [ ] **1.2.2** UserShare model (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** SQLAlchemy ORM model for user-to-user shares
  - **Acceptance:** Model with sender/recipient relationships; Async-compatible; viewed_at, imported_at fields; __repr__ for debugging

- [ ] **1.2.3** Collection models (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** SQLAlchemy models for Collection and CollectionItem
  - **Acceptance:** Async-compatible; Collection: relationships to user and items; CollectionItem: relationships to collection and listing; Position property for ordering

#### 1.3 Repository Layer (6 SP)

- [ ] **1.3.1** ShareRepository (3 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Data access layer for shares
  - **Acceptance:** create_listing_share(listing_id, created_by, expires_at); get_by_token(token) with expiry validation; increment_view_count(); find_expired_shares(); Unit tests >90% coverage

- [ ] **1.3.2** CollectionRepository (3 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Data access layer for collections
  - **Acceptance:** CRUD methods (create, get, update, delete); find_by_user(user_id) with eager loading; add_item(collection_id, listing_id, status); update_item(item_id, status, notes, position); remove_item(item_id); Unit tests >90% coverage

#### 1.4 Schema & Validation (2 SP)

- [ ] **1.4.1** Pydantic schemas (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Define request/response schemas in packages/core/schemas/
  - **Acceptance:** ListingShareSchema; UserShareSchema; CollectionSchema; CollectionItemSchema; All with proper validation rules; Serialization tests

**Phase 1 Quality Gate:** ✅ All migrations apply cleanly | ✅ Repositories tested in isolation | ✅ No N+1 query issues

---

### PHASE 2: Service & Business Logic Layer (21 SP)
**Duration:** 5-6 days | **Focus:** Business logic, validation, token generation, authorization

#### 2.1 Sharing Service (8 SP)

- [ ] **2.1.1** SharingService class (3 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Core sharing business logic
  - **Acceptance:** generate_listing_share_token(listing_id, user_id, ttl_days=180); validate_listing_share_token(token); create_user_share(sender_id, recipient_id, listing_id, message); mark_user_share_viewed(share_id); check_share_access() with proper auth

- [ ] **2.1.2** Token generation & security (3 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Secure token generation with rate limiting
  - **Acceptance:** tokens.py utility using secrets.token_urlsafe(48); Prevents enumeration attacks; Rate limiter: max 10 shares/user/hour; Token uniqueness guarantee; Logging of token generation

- [ ] **2.1.3** Share validation & expiry (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Validate tokens, handle expiration
  - **Acceptance:** check_token_expired() utility; Auto-cleanup of expired shares (query optimization); User authorization checks (sender/recipient); Prevents accessing others' shares

#### 2.2 Collections Service (8 SP)

- [ ] **2.2.1** CollectionsService class (3 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Core collections business logic
  - **Acceptance:** create_collection(user_id, name, description); update_collection(collection_id, user_id, name, description, visibility); delete_collection(collection_id, user_id); list_user_collections(user_id); get_collection_with_items(collection_id, user_id)

- [ ] **2.2.2** Item management (3 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Add, update, remove items from collections
  - **Acceptance:** add_item(collection_id, listing_id, user_id) with deduplication; update_item(item_id, status, notes, position, user_id); remove_item(item_id, user_id); Reorder items (position management); Auth checks prevent cross-user access

- [ ] **2.2.3** Collection queries (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Optimized queries for collections
  - **Acceptance:** get_collection_with_eager_load() prevents N+1; filter_items(collection_id, filters) with price range, CPU, form factor; sort_items(collection_id, sort_key) maintains user sort preference; Query performance <200ms

#### 2.3 Integration Service (4 SP)

- [ ] **2.3.1** Send-to-collection logic (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Integrate sharing with collections
  - **Acceptance:** import_shared_deal(share_token, collection_id, user_id); Auto-populate default collection if none provided; Prevents duplicate adds; Preserves original metadata; Triggers imported_at timestamp

- [ ] **2.3.2** Deduplication & validation (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Check for duplicate deals, validate before adding
  - **Acceptance:** check_deal_already_in_collection(listing_id, collection_id) → bool; Returns helpful message if duplicate; Validates collection ownership; Validates listing exists

#### 2.4 Testing (3 SP)

- [ ] **2.4.1** Unit tests for services (3 SP)
  - **Subagent:** python-backend-engineer (with test-automator support)
  - **Description:** Comprehensive unit tests for all services
  - **Acceptance:** SharingService: token generation, validation, expiry (>90% coverage); CollectionsService: CRUD, item management (>90% coverage); All tests async-compatible; Mock databases; Edge case coverage

**Phase 2 Quality Gate:** ✅ All service methods tested | ✅ Authorization enforced | ✅ No SQL injection vulnerabilities | ✅ Token generation secure

---

### PHASE 3: API Layer (20 SP)
**Duration:** 5 days | **Focus:** REST endpoints, request/response handling, error handling

#### 3.1 Shares Endpoints (Public) (5 SP)

- [ ] **3.1.1** GET /deals/{id}/{token} endpoint (3 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Public deal preview endpoint
  - **Acceptance:** Route: GET /deals/{listing_id}/{share_token}; No auth required; Returns ListingShare + Listing data (read-only); Validates token expiry; Increments view count; 404 if token invalid/expired; Includes OG meta tags in response headers

- [ ] **3.1.2** Public deal page caching (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Optimize caching for link preview crawlers
  - **Acceptance:** Cache OG snapshot for 24 hours; Cache key: listing_id + share_token; Redis integration; Invalidate on listing update

#### 3.2 User Shares Endpoints (9 SP)

- [ ] **3.2.1** POST /user-shares (create share) (3 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Send deal to specific user
  - **Acceptance:** Route: POST /user-shares with {recipient_id, listing_id, message?}; Auth required (sender is current user); Validates recipient exists; Validates listing exists; Creates UserShare record; Triggers share notification; Rate limit: 10/hour/user

- [ ] **3.2.2** GET /user-shares (list received) (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** List shares received by current user
  - **Acceptance:** Route: GET /user-shares; Auth required; Pagination with limit/offset; Filter: unviewed, expired; Eager load sender and listing data

- [ ] **3.2.3** GET /user-shares/{token} (preview) (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Preview received share without import
  - **Acceptance:** Route: GET /user-shares/{share_token}; No auth required (but identifies sender); Returns UserShare + Listing + sender info; Marks viewed_at timestamp; 404 if token invalid/expired

- [ ] **3.2.4** POST /user-shares/{token}/import (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Import shared deal to user's workspace
  - **Acceptance:** Route: POST /user-shares/{token}/import; Auth required (recipient is current user); Creates CollectionItem in user's default collection (or specified); Marks imported_at timestamp; Returns collection_id; Deduplication check

#### 3.3 Collections Endpoints (9 SP)

- [ ] **3.3.1** POST /collections (create) (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Create new collection
  - **Acceptance:** Route: POST /collections with {name, description?, visibility}; Auth required (user_id from token); Validates name length (1-100 chars); Returns CollectionSchema with id; Timestamps set automatically

- [ ] **3.3.2** GET /collections (list user's) (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** List all user's collections
  - **Acceptance:** Route: GET /collections; Auth required; Pagination with limit/offset; Eager load item count, recent items; Sort by created_at (newest first)

- [ ] **3.3.3** GET /collections/{id} (detail) (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Get collection with all items
  - **Acceptance:** Route: GET /collections/{id}; Auth required (verify ownership); Eager load all items with listings; Includes filtering/sorting preferences; 403 if not owner

- [ ] **3.3.4** PATCH /collections/{id} (update) (1 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Update collection metadata
  - **Acceptance:** Route: PATCH /collections/{id} with {name?, description?, visibility?}; Auth required; Validates name length; 403 if not owner; Updates updated_at timestamp

- [ ] **3.3.5** DELETE /collections/{id} (1 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Delete collection (cascade delete items)
  - **Acceptance:** Route: DELETE /collections/{id}; Auth required; 403 if not owner; Soft delete or cascade hard delete; Returns 204 No Content

#### 3.4 Collection Items Endpoints (7 SP)

- [ ] **3.4.1** POST /collections/{id}/items (add) (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Add item to collection
  - **Acceptance:** Route: POST /collections/{id}/items with {listing_id, status?, notes?}; Auth required; 403 if not collection owner; Deduplication check; Validates listing exists; Auto-generates position

- [ ] **3.4.2** PATCH /collections/{id}/items/{item_id} (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Update item status, notes, position
  - **Acceptance:** Route: PATCH /collections/{id}/items/{item_id} with {status?, notes?, position?}; Auth required; Validates status enum; Auto-save notes (no explicit save needed); Auto-updates updated_at

- [ ] **3.4.3** DELETE /collections/{id}/items/{item_id} (1 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Remove item from collection
  - **Acceptance:** Route: DELETE /collections/{id}/items/{item_id}; Auth required; 403 if not owner; Returns 204 No Content

- [ ] **3.4.4** GET /collections/{id}/export (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Export collection as CSV/JSON
  - **Acceptance:** Route: GET /collections/{id}/export?format=csv|json; Auth required; Includes: listing name, price, CPU, GPU, $/CPU Mark, score, notes; Returns file download; CSV format with proper escaping

#### 3.5 API Testing (3 SP)

- [ ] **3.5.1** Integration tests for all endpoints (3 SP)
  - **Subagent:** python-backend-engineer (with test-automator support)
  - **Description:** Test all endpoints with real database
  - **Acceptance:** Happy path tests for each endpoint; Auth failure tests (403, 401); Validation failure tests (400); Not found tests (404); Deduplication tests; Rate limit tests

**Phase 3 Quality Gate:** ✅ All endpoints documented (OpenAPI) | ✅ All endpoints tested >90% coverage | ✅ Auth enforced on all protected routes | ✅ Rate limiting working | ✅ Proper HTTP status codes

---

### PHASE 4: UI Layer & Integration (20 SP)
**Duration:** 8 days | **Focus:** React components, API integration, user flows

#### 4.1 Public Deal Page (5 SP)

- [ ] **4.1.1** PublicDealPage component (3 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Shareable deal page at /deals/[id]/[token]
  - **Acceptance:** Route: /deals/[id]/[token]; Fetches listing via share token; Renders: image, specs, price, score, valuation breakdown; OpenGraph meta tags for link previews; "Add to Collection" CTA visible; No auth required to view; Sign-up prompt if not logged in

- [ ] **4.1.2** OG meta tags integration (2 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Generate proper OG tags for Slack/Discord/X
  - **Acceptance:** og:title with listing name; og:image with listing image; og:description with price + score; og:url with full share link; twitter:card support

#### 4.2 Share Button & Modals (5 SP)

- [ ] **4.2.1** ShareButton component (2 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Button to share deal (public + user-to-user)
  - **Acceptance:** Appears on listing detail, search results; Click opens modal (no nav away); Tabs for "Copy Link" and "Share with User"; Copy-to-clipboard functionality; Visual feedback on copy

- [ ] **4.2.2** Share Modal component (3 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Modal for user-to-user sharing
  - **Acceptance:** User search input (autocomplete, debounced 200ms); Search by username; Display matched users; Optional message field; Send button with loading state; Success toast on completion

#### 4.3 Collections List Page (5 SP)

- [ ] **4.3.1** CollectionsList page (3 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** List all user's collections at /collections
  - **Acceptance:** Route: /collections; Card grid layout; Each card shows: name, description, item count, created date; "New Collection" button; Pagination (load more); Mobile responsive

- [ ] **4.3.2** New Collection form (2 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Inline form to create collection
  - **Acceptance:** Modal or inline form; Name field (required, 1-100 chars); Description field (optional, markdown preview); Visibility selector (private default); Submit creates collection; Redirects to workspace

#### 4.4 Collections Workspace (10 SP)

- [ ] **4.4.1** CollectionWorkspace page (3 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Main comparison view at /collections/[id]
  - **Acceptance:** Route: /collections/[id]; Header: collection name, edit button, export button; Filters: price range, CPU family, form factor; Sort controls; View toggle: table/card view

- [ ] **4.4.2** Workspace table view (3 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Sortable, filterable table of items
  - **Acceptance:** Columns: name, price, CPU, GPU, $/CPU Mark, form factor, score, status; Click column headers to sort; Checkboxes for bulk selection; Inline status badge (color-coded); "Expand" action for notes panel

- [ ] **4.4.3** Workspace card view (2 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Mobile-friendly card layout
  - **Acceptance:** Card per item with essential info; Status badge visible; Notes accessible via expand; Stack vertically on mobile

- [ ] **4.4.4** Item details panel (2 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Side panel for editing notes and status
  - **Acceptance:** Click item → expand side panel; Notes field (markdown support); Status dropdown (undecided, shortlisted, rejected, bought); Auto-save to backend; Close button

#### 4.5 Collection Selector Modal (2 SP)

- [ ] **4.5.1** CollectionSelector modal (2 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Modal to add item to collection
  - **Acceptance:** Shows recent 5 collections; "Create New Collection" option; Create form inline (no modal cascade); Select and add item; Returns to workspace; Success toast

#### 4.6 React Query & Hooks (3 SP)

- [ ] **4.6.1** useCollections hook (1 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Fetch and manage user collections
  - **Acceptance:** Queries GET /collections; Caches with React Query; Returns {collections, isLoading, error}; Refetch on mutation

- [ ] **4.6.2** useCollection hook (1 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Fetch single collection with items
  - **Acceptance:** Queries GET /collections/{id}; Eager load items; Caches with React Query; Refetch on item changes

- [ ] **4.6.3** useShare hook (1 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Generate and share deals
  - **Acceptance:** POST /user-shares; Handles loading/error states; Success callback

**Phase 4 Quality Gate:** ✅ All pages render without errors | ✅ API integration works end-to-end | ✅ Mobile views tested on real devices | ✅ Accessibility audit passed (WCAG AA)

---

### PHASE 5: Integration, Polish & Performance (17 SP)
**Duration:** 8 days | **Focus:** Connect all pieces, optimize performance, handle edge cases, add notifications

#### 5.1 Send-to-Collection Flow (3 SP)

- [ ] **5.1.1** Integration: Share → Import → Collect (2 SP)
  - **Subagent:** python-backend-engineer + ui-engineer-enhanced
  - **Description:** Complete flow from share link to collection
  - **Acceptance:** Share link → Public page → "Add to Collection" → Collection selector → Workspace; All steps work end-to-end; User data preserved through flow; <2s page load time

- [ ] **5.1.2** Shared deal preview in collection (1 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Show shared deal origin in collection
  - **Acceptance:** Item metadata includes share_from (sender name); Optional: badge or indicator; Click to view original share

#### 5.2 Notifications System (4 SP)

- [ ] **5.2.1** Share notifications (in-app) (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** In-app notification when deal shared
  - **Acceptance:** Toast/banner when receiving share; Link to preview page; Notification history available

- [ ] **5.2.2** Email notifications (async) (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Async email when deal shared
  - **Acceptance:** Celery task to send email; Includes deal summary + link; Respects user notification preferences

#### 5.3 Collection Export (3 SP)

- [ ] **5.3.1** CSV export (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Export collection as CSV
  - **Acceptance:** Endpoint: GET /collections/{id}/export?format=csv; Columns: name, price, CPU, GPU, $/mark, score, status, notes; Proper CSV escaping; Browser download

- [ ] **5.3.2** JSON export (1 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Export collection as JSON
  - **Acceptance:** Endpoint: GET /collections/{id}/export?format=json; Structured JSON with metadata; Includes timestamps, status enums; Browser download

#### 5.4 Mobile Optimization (3 SP)

- [ ] **5.4.1** Mobile workspace view (2 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Optimize collections workspace for mobile
  - **Acceptance:** Card view on mobile (table on desktop); Touch-friendly controls; Horizontal scroll on wide tables; Tested on iOS 14+, Android 11+

- [ ] **5.4.2** Mobile share flow (1 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Optimize sharing UX on mobile
  - **Acceptance:** Share button easily tappable; Copy-to-clipboard works on all browsers; QR code option (optional)

#### 5.5 Performance Optimization (6 SP)

- [ ] **5.5.1** Database query optimization (2 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Optimize N+1 queries in collections
  - **Acceptance:** Eager load collection items with listings; Query time <200ms for 100 items; Pagination if >100 items; Profiling with django-silk or similar

- [ ] **5.5.2** Frontend caching & memoization (2 SP)
  - **Subagent:** ui-engineer-enhanced
  - **Description:** Optimize React rendering performance
  - **Acceptance:** Memoized components (React.memo); useCallback for stable function refs; React Query caching working properly; <100ms interaction latency

- [ ] **5.5.3** Link preview caching (1 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Cache OG snapshots efficiently
  - **Acceptance:** 24-hour cache on OG snapshot; Redis key strategy: listing_id:share_token; Invalidate on listing update

**Phase 5 Quality Gate:** ✅ Complete flow tested (share → public page → import → workspace) | ✅ Performance targets met (<2s page load, <100ms interactions) | ✅ Notifications working | ✅ Mobile tested on real devices

---

### PHASE 6: Testing & Launch (10 SP)
**Duration:** 10 days | **Focus:** Comprehensive testing, documentation, deployment preparation

#### 6.1 End-to-End Testing (7 SP)

- [ ] **6.1.1** E2E test: Share & public page (2 SP)
  - **Subagent:** test-automator (with python-backend-engineer support)
  - **Description:** Test complete share flow
  - **Acceptance:** Create share → Copy link → Open public page → Verify OG tags; Playwright/Cypress test

- [ ] **6.1.2** E2E test: User-to-user share (2 SP)
  - **Subagent:** test-automator (with python-backend-engineer support)
  - **Description:** Test sending deal to friend
  - **Acceptance:** User A shares deal with User B → User B receives notification → Views deal → Imports to collection; Playwright test

- [ ] **6.1.3** E2E test: Collections workflow (2 SP)
  - **Subagent:** test-automator (with python-backend-engineer support)
  - **Description:** Test complete collections workflow
  - **Acceptance:** Create collection → Add items → Edit notes/status → Filter/sort → Export; Playwright test

- [ ] **6.1.4** E2E test: Mobile flows (1 SP)
  - **Subagent:** test-automator (with ui-engineer-enhanced support)
  - **Description:** Test mobile-specific flows
  - **Acceptance:** Mobile share flow; Mobile workspace view; Mobile item editing; Real device testing (iOS, Android)

#### 6.2 Quality Assurance (3 SP)

- [ ] **6.2.1** Accessibility audit (1 SP)
  - **Subagent:** ui-engineer-enhanced (or a11y-sheriff if available)
  - **Description:** WCAG AA compliance verification
  - **Acceptance:** Run axe/WAVE accessibility checker; Keyboard navigation works; Screen reader compatible; Color contrast verified; Fix any critical issues

- [ ] **6.2.2** Security review (1 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Security & auth verification
  - **Acceptance:** Token enumeration prevention; SQL injection tests; XSS prevention; CSRF protection; Rate limiting working

- [ ] **6.2.3** Performance load testing (1 SP)
  - **Subagent:** python-backend-engineer
  - **Description:** Load test collections with 100+ items
  - **Acceptance:** Collections endpoint handles 100+ items <200ms; Public share page <1s load time; K6 or similar load testing tool

#### 6.3 Documentation (0 SP - handled by documentation-writer)

- [ ] **6.3.1** API documentation
  - **Subagent:** documentation-writer
  - **Description:** Auto-generated OpenAPI docs
  - **Acceptance:** FastAPI Swagger UI enabled; All endpoints documented; Request/response examples; Error codes documented

- [ ] **6.3.2** User guide
  - **Subagent:** documentation-writer
  - **Description:** User-facing documentation
  - **Acceptance:** How to share a deal; How to create a collection; How to use workspace; Tips & tricks

- [ ] **6.3.3** Developer guide
  - **Subagent:** documentation-writer
  - **Description:** Developer implementation reference
  - **Acceptance:** Architecture overview; Database schema diagram; API endpoint reference; Code examples

#### 6.4 Deployment Preparation (Handled by devops tasks - not tracked here)

- [ ] **6.4.1** Migration preparation
- [ ] **6.4.2** Feature flag setup
- [ ] **6.4.3** Analytics & monitoring

#### 6.5 Launch & Validation (Handled by devops - not tracked here)

- [ ] **6.5.1** Staged rollout execution

**Phase 6 Quality Gate:** ✅ All tests passing | ✅ Accessibility audit passed | ✅ Documentation complete | ✅ Monitoring configured | ✅ Launch readiness checklist signed off

---

## Work Log

### 2025-11-17 - Phase 1.1 Database Migrations Complete (11 SP)

**Completed by:** data-layer-expert

**Tasks Completed:**
- ✅ 1.1.1: ListingShare table migration (3 SP)
- ✅ 1.1.2: UserShare table migration (3 SP)
- ✅ 1.1.3: Collection and CollectionItem tables migration (3 SP)
- ✅ 1.1.4: Indexes and constraints (2 SP)

**Files Created:**
- `apps/api/alembic/versions/0028_add_collections_and_sharing_tables.py` (335 lines)

**Key Implementation Details:**

1. **User Table Created:**
   - Added minimal user table (id, username, email, display_name) to support foreign keys
   - Note: Full authentication system (passwords, OAuth) will be added in later phase
   - Unique indexes on username and email

2. **ListingShare Table:**
   - Public deal sharing via unique share_token (64 chars)
   - Optional expiry (expires_at) - NULL means never expires
   - View count tracking for analytics
   - Foreign keys to listing and user tables
   - Indexes: token (unique), listing_id, expires_at

3. **UserShare Table:**
   - User-to-user deal sharing with sender and recipient
   - Unique share_token for secure access
   - Message field for personal notes
   - Default expiry: 30 days from creation
   - Tracking: viewed_at, imported_at timestamps
   - Composite index on (recipient_id, expires_at) for inbox queries
   - Indexes: token (unique), sender_id

4. **Collection Table:**
   - Private deal collections per user
   - Name (max 100 chars), description, visibility
   - Visibility check constraint: 'private', 'unlisted', 'public'
   - Cascade delete when user is deleted
   - Index on user_id

5. **CollectionItem Table:**
   - Items within collections
   - Status tracking: 'undecided', 'shortlisted', 'rejected', 'bought'
   - Notes field for user annotations
   - Position field (nullable) for drag-and-drop ordering
   - Unique constraint: (collection_id, listing_id) - prevents duplicates
   - Cascade delete when collection or listing is deleted
   - Indexes: collection_id, listing_id

**Schema Adaptations:**
- Adapted spec from UUID to Integer IDs to match existing codebase
- Used singular table names (collection, not collections) per codebase convention
- Server default for timestamps: sa.func.now()
- Used check constraints instead of PostgreSQL ENUMs for better flexibility

**Migration Properties:**
- Revision: 0028
- Revises: 0bfccac265c8
- Fully reversible (downgrade implemented)
- No breaking changes to existing tables

**Testing Status:**
- ⚠️ Manual testing required (Docker not available in this environment)
- ✅ Python syntax validated
- ⏳ Pending: `alembic upgrade head` test
- ⏳ Pending: `alembic downgrade -1` test
- ⏳ Pending: Database schema verification

**Next Steps:**
- Run `alembic upgrade head` in development environment
- Verify all tables created correctly
- Test downgrade functionality
- Proceed to Phase 1.2: SQLAlchemy Models (python-backend-engineer)

---

## Decisions Log

### Decision 1: Use Integer IDs instead of UUIDs
**Date:** 2025-11-17
**Context:** PRD specification suggested UUID primary keys, but existing codebase uses Integer IDs
**Decision:** Adapted schema to use Integer IDs throughout to maintain consistency with existing models
**Rationale:**
- All existing tables (listing, cpu, gpu, etc.) use Integer IDs
- Changing to UUIDs would create inconsistency and require migrations for existing tables
- Integer IDs are performant and simpler for this use case
**Impact:** No impact on functionality; all features work identically with Integer IDs

### Decision 2: Create minimal User table now
**Date:** 2025-11-17
**Context:** Collections and sharing features require user authentication, but no User model exists
**Decision:** Created minimal user table with id, username, email, display_name fields only
**Rationale:**
- Enables foreign key relationships for collections and shares
- Provides foundation for future authentication implementation
- Minimal fields reduce risk of conflicts with future auth system design
**Impact:**
- Phase 1 can proceed with data model implementation
- Authentication implementation (passwords, OAuth, sessions) deferred to later phase
- No breaking changes expected when full auth is added

### Decision 3: Consolidate all migrations into single file
**Date:** 2025-11-17
**Context:** Tasks 1.1.1-1.1.4 could be 4 separate migrations or 1 consolidated migration
**Decision:** Created single migration file (0028) containing all tables
**Rationale:**
- All tables are tightly coupled (foreign keys between them)
- Easier to apply/revert as atomic unit
- Reduces number of migration files
- Matches existing codebase patterns (see migration 0021, 0027)
**Impact:** Cleaner migration history; easier rollback if issues found

### Decision 4: Use check constraints for enums instead of PostgreSQL ENUMs
**Date:** 2025-11-17
**Context:** Need to enforce valid values for visibility and status fields
**Decision:** Used check constraints (e.g., `visibility IN ('private', 'unlisted', 'public')`)
**Rationale:**
- Matches existing codebase pattern (migration 0003 converted ENUMs to strings)
- More flexible: can add new values without altering type
- Easier to work with in Python code
- Aligns with Deal Brain's preference for string-based enums
**Impact:** Simpler enum management; easier to extend in future

---

## Files Changed

### Created
- `apps/api/alembic/versions/0028_add_collections_and_sharing_tables.py` (335 lines)
  - Database migration for collections and sharing foundation
  - Creates 5 tables: user, listing_share, user_share, collection, collection_item
  - Includes all indexes and constraints per spec

### Modified
- `.claude/progress/collections-sharing-foundation-v1/all-phases-progress.md`
  - Updated completion status (11 SP completed)
  - Marked Phase 1.1 tasks as complete
  - Added work log entry
  - Documented architectural decisions

### Deleted
- None

---

## Notes

- This is a comprehensive tracker for ALL 6 phases of the Collections & Sharing Foundation v1 implementation
- Total effort: 89 story points over 5 weeks
- Each task includes the assigned subagent for orchestration
- Progress will be tracked incrementally as tasks are completed
- Phase quality gates must be met before proceeding to next phase
