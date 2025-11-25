---
title: "Community & Social Features Phase 3.1-3.2 - Foundation & Reputation"
description: "Detailed task breakdown for Phase 3.1 (Foundation: Database, catalog API, voting) and Phase 3.2 (Reputation: Curator badges, notifications, following). Includes acceptance criteria, file modifications, and quality gates."
audience: [ai-agents, developers]
tags: [implementation, planning, community, phase-3.1, phase-3.2, voting, reputation, notifications]
created: 2025-11-14
updated: 2025-11-14
category: "product-planning"
status: draft
related:
  - community-social-features-v1.md
  - ../community-social-features-v1.md
---

# Phase 3.1-3.2: Foundation & Reputation Implementation

**Duration**: Weeks 1-7 (7 weeks total)
**Effort**: 45 story points (25 Phase 3.1 + 20 Phase 3.2)
**Key Deliverables**: Catalog API, voting system, reputation calculation, notifications

---

## Phase 3.1: Foundation (Weeks 1-4)

**Objective**: Build core catalog infrastructure and voting system

### Phase 3.1 Overview

| Task ID | Task Name | Effort | Duration | Assignee | Dependencies |
|---------|-----------|--------|----------|----------|--------------|
| DB-001 | Create CommunityDeal, Vote, UserProfile tables | 3 pts | 2 days | data-layer-expert | None |
| DB-002 | Create Alembic migration for Phase 3.1 schema | 2 pts | 1 day | data-layer-expert | DB-001 |
| DB-003 | Add RLS policies for community tables | 2 pts | 1 day | backend-architect | DB-002 |
| REPO-001 | Implement CommunityDealRepository | 2 pts | 2 days | python-backend-engineer | DB-002 |
| REPO-002 | Implement VoteRepository | 2 pts | 1 day | python-backend-engineer | DB-002 |
| REPO-003 | Implement UserProfileRepository | 1.5 pts | 1 day | python-backend-engineer | DB-002 |
| SVC-001 | Implement CommunityDealService | 3 pts | 2 days | service-engineer | REPO-001, REPO-003 |
| SVC-002 | Implement VotingService with deduplication | 3 pts | 2 days | service-engineer | REPO-002, SVC-001 |
| SVC-003 | Implement anti-abuse: Rate limiting service | 2 pts | 1 day | moderation-specialist | SVC-002 |
| API-001 | Implement community-deals router (GET list, POST publish) | 2 pts | 2 days | python-backend-engineer | SVC-001 |
| API-002 | Implement voting router (POST vote, DELETE vote) | 1.5 pts | 1 day | python-backend-engineer | SVC-002 |
| API-003 | Implement curator router (GET profile) | 1 pt | 1 day | python-backend-engineer | SVC-001 |
| SCHEMA-001 | Create Pydantic schemas for community features | 2 pts | 1 day | python-backend-engineer | API-001, API-002 |
| UI-001 | Implement CatalogBrowserPage component | 2 pts | 2 days | ui-engineer | API-001 |
| UI-002 | Implement DealCard component (with votes display) | 2 pts | 1 day | frontend-developer | UI-001 |
| UI-003 | Implement VotingUI component | 2 pts | 1 day | frontend-developer | UI-002, API-002 |
| UI-004 | Implement CuratorBadge component (placeholder for Phase 3.2) | 1 pt | 1 day | frontend-developer | UI-001 |
| UI-005 | Implement CuratorProfilePage component | 2 pts | 2 days | ui-engineer | API-003 |
| TEST-001 | Write CommunityDealRepository tests | 1.5 pts | 1 day | test-automator | REPO-001 |
| TEST-002 | Write VotingService tests | 2 pts | 1 day | test-automator | SVC-002 |
| TEST-003 | Write API integration tests (catalog, voting) | 2 pts | 2 days | test-automator | API-001, API-002 |
| TEST-004 | Write E2E tests (publish → vote) | 2 pts | 2 days | test-automator | TEST-003, UI-001 |
| OBS-001 | Add OpenTelemetry spans for community operations | 1 pt | 1 day | backend-architect | API-001, API-002, API-003 |

**Critical Path**: DB-001 → DB-002 → REPO-001/REPO-002 → SVC-001/SVC-002 → API-001/API-002 → TEST-003

---

## Phase 3.1 Detailed Tasks

### Database Layer (DB-001, DB-002, DB-003)

#### DB-001: Create CommunityDeal, Vote, UserProfile Tables

**Objective**: Design and implement initial schema for Phase 3.1

**Duration**: 2 days
**Effort**: 3 story points
**Assignee**: data-layer-expert

**Files to Create**:
- `/apps/api/alembic/versions/2025_11_14_community_foundation.py` (migration)

**Acceptance Criteria**:
- [ ] CommunityDeal table created with columns:
  - id (UUID, PK)
  - deal_id (UUID, FK to Listing)
  - curator_id (UUID, FK to User, indexed)
  - title, description (indexed for search)
  - category_tags (JSONB, indexed)
  - published_at, updated_at (indexed)
  - view_count, vote_count (denormalized, updated async)
  - vote_score (calculated, denormalized)
  - affiliate_link_flag, affiliate_url (optional)
  - is_published (boolean, default true)
  - snapshot_data (JSONB - immutable deal data at publish)
  - Indexes: (curator_id), (published_at), (vote_score), (view_count)
  - Constraints: UNIQUE(deal_id, curator_id) - one per deal per curator

- [ ] Vote table created with columns:
  - id (UUID, PK)
  - user_id (UUID, FK to User, indexed)
  - community_deal_id (UUID, FK to CommunityDeal, indexed)
  - vote_type (ENUM: UPVOTE, DOWNVOTE)
  - created_at (indexed)
  - Constraints: UNIQUE(user_id, community_deal_id) - one vote per user per deal
  - Index: (community_deal_id) for vote count queries

- [ ] UserProfile table created with columns:
  - id (UUID, PK)
  - user_id (UUID, FK to User, UNIQUE, indexed)
  - username (VARCHAR, UNIQUE, indexed)
  - bio (TEXT, optional)
  - avatar_url (VARCHAR, optional)
  - reputation_score (INTEGER, default 0, indexed)
  - deals_published_count (INTEGER, default 0, denormalized)
  - followers_count (INTEGER, default 0, denormalized)
  - created_at, updated_at

- [ ] All tables use async SQLAlchemy style with:
  - `from sqlalchemy.ext.asyncio import AsyncSession`
  - Proper type hints
  - Relationship definitions for ORM joins

- [ ] Migration is idempotent and can be rolled back
- [ ] Schema documentation includes FK relationships and indexes
- [ ] No N+1 queries possible with designed indexes

**Success Metrics**:
- Migration runs cleanly in dev/test
- Tables created with all columns and constraints
- Indexes created as specified
- RLS policies ready for DB-003

---

#### DB-002: Create Alembic Migration for Phase 3.1

**Objective**: Integrate community tables into migration framework

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: data-layer-expert

**Files to Modify**:
- `/apps/api/alembic/env.py` (if needed)
- `/apps/api/alembic/versions/2025_11_14_community_foundation.py` (created in DB-001)

**Acceptance Criteria**:
- [ ] Migration follows Alembic conventions:
  - Has up() and down() functions
  - Includes `from alembic import op`
  - Uses batch mode for SQLite compatibility (if needed)

- [ ] Can be applied: `alembic upgrade head`
- [ ] Can be rolled back: `alembic downgrade -1`
- [ ] No conflicts with existing migrations
- [ ] Migration timestamp correctly ordered after latest migration
- [ ] Generated migration auto-detects schema from models if using --autogenerate
- [ ] Tested in dev environment:
  - [ ] Migration runs without errors
  - [ ] Tables exist after running
  - [ ] Rollback succeeds and tables removed
  - [ ] Data is preserved on rollback (if supported)

**Success Metrics**:
- Migration integrates with existing framework
- No manual SQL needed (pure Alembic ops)
- Clear description in migration docstring

---

#### DB-003: Add RLS Policies for Community Tables

**Objective**: Implement row-level security for community features

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: backend-architect

**Files to Create**:
- `/apps/api/alembic/versions/2025_11_14_rls_community_policies.py` (migration)

**Acceptance Criteria**:
- [ ] RLS enabled on CommunityDeal table:
  - Community deals are visible to all authenticated users (SELECT)
  - Only curator can update their own deal (UPDATE)
  - Only curator can delete their own deal (DELETE)
  - Policy: `(SELECT * FROM community_deal WHERE auth.uid() = curator_id OR NOT auth.is_user())`

- [ ] RLS enabled on Vote table:
  - Users can see all votes (SELECT)
  - Users can only create votes for themselves (INSERT)
  - Users can only delete their own votes (DELETE)
  - Policy: `(SELECT * WHERE user_id = auth.uid() OR auth.is_user() IS NOT TRUE)`

- [ ] RLS enabled on UserProfile table:
  - Public profiles visible to all (SELECT)
  - Users can only update their own profile (UPDATE)
  - Policy: `(SELECT * FROM user_profile WHERE user_id = auth.uid() OR NOT auth.is_user())`

- [ ] RLS policies created via Alembic migration (not manual)
- [ ] Policies have meaningful names (e.g., `community_deal_public_read`)
- [ ] Tested that:
  - [ ] Anonymous users cannot see community deals
  - [ ] Authenticated users can see all deals
  - [ ] Users cannot modify others' deals/votes
  - [ ] Users can vote on the same deal once only

**Success Metrics**:
- All RLS policies defined and enforced
- No unauthorized access possible
- Audit trail of policy changes in migration

---

### Repository Layer (REPO-001, REPO-002, REPO-003)

#### REPO-001: Implement CommunityDealRepository

**Objective**: Create data access layer for community deals

**Duration**: 2 days
**Effort**: 2 story points
**Assignee**: python-backend-engineer

**Files to Create**:
- `/apps/api/dealbrain_api/repositories/community_deal_repository.py`

**Acceptance Criteria**:
- [ ] Methods implemented:
  - `async create(deal_id, curator_id, title, description, ...) -> CommunityDeal`
  - `async get_by_id(deal_id: UUID) -> CommunityDeal | None`
  - `async get_by_curator_id(curator_id: UUID, skip: int, limit: int) -> list[CommunityDeal]`
  - `async get_latest(skip: int, limit: int) -> list[CommunityDeal]` (sorted by published_at DESC)
  - `async get_trending(skip: int, limit: int, days: int = 7) -> list[CommunityDeal]` (sorted by vote_score DESC)
  - `async search(query: str, filters: dict, skip: int, limit: int) -> list[CommunityDeal]`
  - `async get_vote_count(deal_id: UUID) -> int`
  - `async update_vote_count(deal_id: UUID, delta: int) -> None`
  - `async update_view_count(deal_id: UUID) -> None`
  - `async delete(deal_id: UUID) -> bool`

- [ ] All queries use:
  - Async SQLAlchemy session
  - Proper cursor-based pagination (not offset/limit)
  - Efficient joins (no N+1 queries)
  - Indexed columns where possible

- [ ] Search implementation:
  - Full-text search on title, description (PostgreSQL tsvector if available)
  - Filter by category_tags using JSONB operators
  - Filter by date range
  - Sort by relevance, recency, votes

- [ ] Unit tests in `/tests/test_repositories/test_community_deal_repository.py`:
  - [ ] Test create, read, update, delete
  - [ ] Test trending query performance
  - [ ] Test search filters
  - [ ] Test pagination (cursor-based)

- [ ] No raw SQL (use SQLAlchemy ORM)
- [ ] Proper error handling (not found, invalid params)
- [ ] Type hints on all parameters and return values

**Success Metrics**:
- All methods implemented and tested
- Trending query <500ms for 10,000 deals
- Search supports filtering and sorting
- Zero N+1 queries

---

#### REPO-002: Implement VoteRepository

**Objective**: Create data access layer for voting

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: python-backend-engineer

**Files to Create**:
- `/apps/api/dealbrain_api/repositories/vote_repository.py`

**Acceptance Criteria**:
- [ ] Methods implemented:
  - `async create(user_id: UUID, deal_id: UUID, vote_type: VoteType) -> Vote`
  - `async get_by_user_and_deal(user_id: UUID, deal_id: UUID) -> Vote | None`
  - `async delete_by_user_and_deal(user_id: UUID, deal_id: UUID) -> bool`
  - `async get_votes_for_deal(deal_id: UUID) -> list[Vote]`
  - `async get_user_votes(user_id: UUID, skip: int, limit: int) -> list[Vote]`
  - `async count_upvotes(deal_id: UUID) -> int`
  - `async count_downvotes(deal_id: UUID) -> int`
  - `async has_voted(user_id: UUID, deal_id: UUID) -> bool`
  - `async get_vote_stats(deal_id: UUID) -> (upvotes: int, downvotes: int, net_score: int)`

- [ ] All queries use async SQLAlchemy
- [ ] Database enforces UNIQUE(user_id, deal_id) constraint
- [ ] Vote deletion is soft (keeps audit trail) or hard (configurable)
- [ ] Unit tests:
  - [ ] Test vote creation
  - [ ] Test deduplication (cannot vote twice on same deal)
  - [ ] Test vote deletion
  - [ ] Test vote counting
- [ ] No N+1 queries

**Success Metrics**:
- All methods working
- Deduplication enforced at database level
- Vote operations <100ms

---

#### REPO-003: Implement UserProfileRepository

**Objective**: Create data access layer for user profiles

**Duration**: 1 day
**Effort**: 1.5 story points
**Assignee**: python-backend-engineer

**Files to Create**:
- `/apps/api/dealbrain_api/repositories/user_profile_repository.py`

**Acceptance Criteria**:
- [ ] Methods implemented:
  - `async get_or_create(user_id: UUID) -> UserProfile`
  - `async get_by_user_id(user_id: UUID) -> UserProfile | None`
  - `async get_by_username(username: str) -> UserProfile | None`
  - `async update(user_id: UUID, bio: str | None, avatar_url: str | None) -> UserProfile`
  - `async update_deals_count(user_id: UUID, delta: int) -> None`
  - `async update_followers_count(user_id: UUID, delta: int) -> None`
  - `async get_top_curators(limit: int) -> list[UserProfile]` (sorted by reputation_score DESC)
  - `async set_reputation(user_id: UUID, score: int) -> UserProfile`

- [ ] Username validation (alphanumeric, 3-30 chars, unique)
- [ ] Profile is created automatically when user signs up (migration or trigger)
- [ ] Unit tests:
  - [ ] Test get_or_create
  - [ ] Test update bio/avatar
  - [ ] Test username uniqueness
  - [ ] Test reputation tracking

**Success Metrics**:
- Profile CRUD working
- Username lookup fast (<100ms)

---

### Service Layer (SVC-001, SVC-002, SVC-003)

#### SVC-001: Implement CommunityDealService

**Objective**: Business logic for community deal publishing and catalog browsing

**Duration**: 2 days
**Effort**: 3 story points
**Assignee**: service-engineer

**Files to Create**:
- `/apps/api/dealbrain_api/services/community_deal_service.py`

**Acceptance Criteria**:
- [ ] Methods implemented:
  - `async publish_deal(deal_id: UUID, curator_id: UUID, title: str, description: str, category_tags: list[str], affiliate_url: str | None) -> CommunityDealDTO`
    - Takes snapshot of deal data at publish time
    - Validates deal exists and is owned by curator or can be published
    - Stores snapshot_data as JSONB (immutable)
    - Checks: deal not already published as community deal
    - Increments curator's deals_published_count
    - Returns DTO (no ORM model exposed)

  - `async get_deal(deal_id: UUID) -> CommunityDealDTO | None`
    - Increments view_count
    - Includes vote count and curator info

  - `async browse_latest(skip: int, limit: int) -> list[CommunityDealDTO]`
    - Sorted by published_at DESC
    - Paginated (cursor-based)
    - Includes vote counts

  - `async browse_trending(skip: int, limit: int, days: int = 7) -> list[CommunityDealDTO]`
    - Sorted by vote_score DESC
    - Filters deals from last N days

  - `async search(query: str, category_filter: list[str], skip: int, limit: int) -> list[CommunityDealDTO]`
    - Full-text search on title + description
    - Filter by category tags

  - `async get_curator_deals(curator_id: UUID, skip: int, limit: int) -> list[CommunityDealDTO]`

- [ ] RLS checks: Only authenticated users can call these methods
- [ ] Snapshot data includes: original deal title, price, components, valuation
- [ ] View count updates are async (separate task or batch)
- [ ] All return DTOs (not ORM models)
- [ ] Unit tests:
  - [ ] Test publish_deal validation
  - [ ] Test snapshot creation
  - [ ] Test browse/search/trending queries
  - [ ] Test RLS enforcement
- [ ] No N+1 queries

**Success Metrics**:
- All methods working
- Browse/search <500ms for 10,000 deals
- Snapshots immutable and complete

---

#### SVC-002: Implement VotingService with Deduplication

**Objective**: Business logic for voting with anti-abuse measures

**Duration**: 2 days
**Effort**: 3 story points
**Assignee**: service-engineer

**Files to Create**:
- `/apps/api/dealbrain_api/services/voting_service.py`

**Acceptance Criteria**:
- [ ] Methods implemented:
  - `async vote(user_id: UUID, deal_id: UUID, vote_type: VoteType) -> VoteDTO`
    - Checks: user hasn't already voted on this deal
    - Creates or updates vote
    - Increments/decrements vote count on CommunityDeal
    - Returns DTO

  - `async unvote(user_id: UUID, deal_id: UUID) -> bool`
    - Removes user's vote
    - Updates vote count on CommunityDeal

  - `async get_user_vote(user_id: UUID, deal_id: UUID) -> VoteDTO | None`
    - Returns user's vote if exists

  - `async get_deal_vote_stats(deal_id: UUID) -> VoteStatsDTO`
    - upvote_count, downvote_count, net_score

- [ ] Deduplication enforced at DB level (UNIQUE constraint)
- [ ] Service validates:
  - Deal exists
  - User exists
  - User hasn't voted already (checked in DB)
- [ ] Vote count denormalization:
  - CommunityDeal.vote_count updated on insert/delete
  - CommunityDeal.vote_score calculated (upvotes - downvotes or weighted)
  - Updates are atomic
- [ ] Rate limiting integration (SVC-003):
  - Check rate limit before vote
  - Return 429 if exceeded
  - Includes: max 10 votes/hour per user, max 1 vote/minute per IP
- [ ] Audit logging:
  - All vote operations logged with user_id, deal_id, vote_type, timestamp
- [ ] Unit tests:
  - [ ] Test vote creation
  - [ ] Test deduplication (second vote fails)
  - [ ] Test unvote
  - [ ] Test vote count updates
  - [ ] Test rate limiting (SVC-003 integration)

**Success Metrics**:
- Vote operations <100ms
- Deduplication prevents vote rings
- Rate limiting enforced

---

#### SVC-003: Implement Anti-Abuse: Rate Limiting Service

**Objective**: Prevent vote/publish spam with rate limiting

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: moderation-specialist

**Files to Create**:
- `/apps/api/dealbrain_api/services/anti_abuse_service.py`

**Acceptance Criteria**:
- [ ] Methods implemented:
  - `async check_vote_rate_limit(user_id: UUID, ip_address: str) -> bool`
    - User limit: Max 10 votes/hour
    - IP limit: Max 1 vote/minute per IP
    - Returns True if allowed, False if exceeded

  - `async check_publish_rate_limit(user_id: UUID, ip_address: str) -> bool`
    - User limit: Max 5 deals/day
    - IP limit: Max 10 deals/day
    - Returns True if allowed, False if exceeded

  - `async get_rate_limit_status(user_id: UUID, ip_address: str) -> RateLimitStatusDTO`
    - Returns current counts and reset times

- [ ] Storage in RateLimitKey table:
  - key_type (VOTE or PUBLISH)
  - key_value (user_id or IP:user_id)
  - count (reset hourly/daily)
  - reset_at (timestamp)

- [ ] Atomic operations using database row locks or Redis
- [ ] Rate limit keys expire automatically (TTL)
- [ ] Logging:
  - Log rate limit violations with user_id, IP, action
  - Alert if >100 violations in 5 minutes (potential bot attack)
- [ ] Unit tests:
  - [ ] Test user vote rate limit
  - [ ] Test IP vote rate limit
  - [ ] Test publish rate limit
  - [ ] Test rate limit reset

**Success Metrics**:
- Rate limiting working for votes and publishes
- Prevents obvious bot spam
- <10ms overhead per request

---

### API Layer (API-001, API-002, API-003, SCHEMA-001)

#### API-001: Implement Community-Deals Router

**Objective**: HTTP endpoints for publishing and browsing community deals

**Duration**: 2 days
**Effort**: 2 story points
**Assignee**: python-backend-engineer

**Files to Create**:
- `/apps/api/dealbrain_api/api/community_deals.py`

**Endpoints**:

1. **GET /api/v1/community-deals** (Browse Catalog)
   - Query params: `skip=0, limit=50, sort_by=recent|trending, category_filter=CPU,GPU`
   - Response: `{ "items": [CommunityDealDTO], "total": int, "next_cursor": str | null }`
   - Response time SLA: <500ms
   - Rate limit: 1000 req/min per IP
   - RLS: Visible to authenticated users only

2. **GET /api/v1/community-deals/trending** (Trending Deals)
   - Query params: `skip=0, limit=50, days=7`
   - Response: `{ "items": [CommunityDealDTO], "total": int, "next_cursor": str | null }`
   - Sorted by vote_score DESC

3. **GET /api/v1/community-deals/:deal_id** (View Single Deal)
   - Response: `CommunityDealDTO` (includes snapshot data)
   - Also increments view_count
   - Rate limit: 1000 req/min per IP

4. **POST /api/v1/community-deals** (Publish Deal)
   - Request: `{ "deal_id": UUID, "title": str, "description": str, "category_tags": [str], "affiliate_url": str | null }`
   - Response: `CommunityDealDTO`
   - Requires auth (user_id from JWT)
   - Rate limiting: SVC-003 (max 5/day)
   - Returns 422 if deal already published as community deal
   - Returns 409 if rate limit exceeded

5. **GET /api/v1/community-deals/search** (Search Deals)
   - Query params: `q=string, category=str, skip=0, limit=50`
   - Response: `{ "items": [CommunityDealDTO], "total": int, "next_cursor": str | null }`

**Acceptance Criteria**:
- [ ] All 5 endpoints implemented
- [ ] Request/response validation using Pydantic schemas
- [ ] Proper error responses (400, 401, 404, 409, 422, 429)
- [ ] OpenTelemetry spans created for each endpoint
- [ ] Structured logging (request_id, user_id, response_time)
- [ ] Rate limiting enforced
- [ ] Cursor-based pagination (not offset/limit)
- [ ] CORS headers configured
- [ ] Unit tests:
  - [ ] Test successful publish
  - [ ] Test duplicate publish (409)
  - [ ] Test rate limiting (429)
  - [ ] Test browse pagination
  - [ ] Test search filtering
  - [ ] Test trending query
  - [ ] Test view count increment

**Success Metrics**:
- All endpoints working and tested
- Response times <500ms
- Rate limiting prevents abuse

---

#### API-002: Implement Voting Router

**Objective**: HTTP endpoints for upvoting/downvoting deals

**Duration**: 1 day
**Effort**: 1.5 story points
**Assignee**: python-backend-engineer

**Files to Create**:
- `/apps/api/dealbrain_api/api/votes.py`

**Endpoints**:

1. **POST /api/v1/votes** (Vote on Deal)
   - Request: `{ "deal_id": UUID, "vote_type": "UPVOTE" | "DOWNVOTE" }`
   - Response: `VoteDTO`
   - Requires auth
   - Rate limiting: SVC-003 (max 10 votes/hour)
   - Returns 409 if already voted (cannot change vote type, must delete first)
   - Returns 400 if invalid vote_type

2. **DELETE /api/v1/votes/:deal_id** (Remove Vote)
   - Response: `{ "success": bool }`
   - Requires auth (can only delete own votes)
   - Returns 404 if vote not found

3. **GET /api/v1/votes/:deal_id** (Get Deal Vote Stats)
   - Response: `VoteStatsDTO { upvotes: int, downvotes: int, net_score: int }`
   - Rate limit: 1000 req/min per IP

4. **GET /api/v1/votes/user/:user_id** (Get User's Votes - for profiles)
   - Query params: `skip=0, limit=50`
   - Response: `{ "items": [VoteDTO], "total": int, "next_cursor": str | null }`
   - Rate limit: 1000 req/min per IP
   - Optional: Hide individual votes (show only count/stats)

**Acceptance Criteria**:
- [ ] All 4 endpoints implemented
- [ ] Deduplication enforced (UNIQUE constraint in DB)
- [ ] Rate limiting enforced (SVC-003)
- [ ] Proper error responses (400, 401, 404, 409, 429)
- [ ] OpenTelemetry spans
- [ ] Vote count on CommunityDeal updated atomically
- [ ] Unit tests:
  - [ ] Test successful vote
  - [ ] Test vote deduplication (cannot vote twice)
  - [ ] Test delete vote
  - [ ] Test vote stats
  - [ ] Test rate limiting
  - [ ] Test 401 without auth

**Success Metrics**:
- Vote operations <100ms
- Deduplication prevents vote rings
- Rate limiting working

---

#### API-003: Implement Curator Router

**Objective**: HTTP endpoints for curator profiles

**Duration**: 1 day
**Effort**: 1 story point
**Assignee**: python-backend-engineer

**Files to Create**:
- `/apps/api/dealbrain_api/api/curator.py`

**Endpoints**:

1. **GET /api/v1/curator/:username** (Get Curator Profile)
   - Response: `CuratorProfileDTO { user: UserProfileDTO, deals_count: int, followers_count: int, deals: [CommunityDealDTO], reputation_score: int }`
   - Includes recent 10 deals published
   - Rate limit: 1000 req/min per IP

2. **PUT /api/v1/curator/profile** (Update Own Profile)
   - Request: `{ "username": str, "bio": str, "avatar_url": str }`
   - Response: `CuratorProfileDTO`
   - Requires auth
   - Returns 409 if username taken
   - Rate limit: 100 req/min per user

3. **GET /api/v1/curator/top** (Top Curators)
   - Query params: `skip=0, limit=10, sort_by=reputation|followers|recent_activity`
   - Response: `{ "items": [CuratorProfileDTO], "total": int, "next_cursor": str | null }`
   - Sorted by reputation_score DESC (default)
   - Rate limit: 1000 req/min per IP

**Acceptance Criteria**:
- [ ] All 3 endpoints implemented
- [ ] Profile includes curator stats (deals, followers, reputation)
- [ ] Top curators list working
- [ ] Update profile validates username uniqueness
- [ ] Proper error responses
- [ ] Unit tests:
  - [ ] Test get profile
  - [ ] Test update profile
  - [ ] Test top curators list
  - [ ] Test 404 for non-existent curator

**Success Metrics**:
- Profile endpoints working
- Top curators list <500ms

---

#### SCHEMA-001: Create Pydantic Schemas

**Objective**: Define request/response schemas for all API endpoints

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: python-backend-engineer

**Files to Create**:
- `/apps/api/dealbrain_api/schemas/community_deals.py`
- `/apps/api/dealbrain_api/schemas/votes.py`
- `/apps/api/dealbrain_api/schemas/curator.py`

**Schemas to Implement**:

```python
# community_deals.py
class CommunityDealCreate(BaseModel):
    deal_id: UUID
    title: str  # min 5, max 200
    description: str  # max 2000
    category_tags: list[str]  # min 1, max 5
    affiliate_url: str | None = None  # validated as URL

class CommunityDealDTO(BaseModel):
    id: UUID
    deal_id: UUID
    curator_id: UUID
    title: str
    description: str
    category_tags: list[str]
    published_at: datetime
    view_count: int
    vote_count: int
    vote_score: int
    affiliate_link_flag: bool
    curator: UserProfileDTO  # nested
    snapshot_data: dict  # original deal data

class CommunityDealListResponse(BaseModel):
    items: list[CommunityDealDTO]
    total: int
    next_cursor: str | None = None

# votes.py
class VoteCreate(BaseModel):
    deal_id: UUID
    vote_type: VoteType  # UPVOTE, DOWNVOTE

class VoteDTO(BaseModel):
    id: UUID
    user_id: UUID
    deal_id: UUID
    vote_type: VoteType
    created_at: datetime

class VoteStatsDTO(BaseModel):
    deal_id: UUID
    upvotes: int
    downvotes: int
    net_score: int

# curator.py
class UserProfileDTO(BaseModel):
    user_id: UUID
    username: str
    bio: str | None
    avatar_url: str | None
    reputation_score: int
    deals_published_count: int
    followers_count: int
    created_at: datetime

class CuratorProfileDTO(BaseModel):
    user: UserProfileDTO
    recent_deals: list[CommunityDealDTO]  # latest 10
    followers_count: int
    following: bool  # whether current user follows this curator

class CuratorListResponse(BaseModel):
    items: list[CuratorProfileDTO]
    total: int
    next_cursor: str | None = None
```

**Acceptance Criteria**:
- [ ] All schemas defined and validated
- [ ] Min/max validation on string fields
- [ ] URL validation for affiliate links
- [ ] Proper type hints
- [ ] Nested DTOs (e.g., CommunityDealDTO includes UserProfileDTO)
- [ ] Unit tests for validation:
  - [ ] Test valid inputs
  - [ ] Test invalid inputs (too short, wrong type, etc.)
  - [ ] Test URL validation
  - [ ] Test required/optional fields

**Success Metrics**:
- All schemas working and validated
- Clear error messages for validation failures

---

### Frontend Layer (UI-001 through UI-005)

#### UI-001: Implement CatalogBrowserPage Component

**Objective**: Main page for browsing community deals

**Duration**: 2 days
**Effort**: 2 story points
**Assignee**: ui-engineer

**Files to Create**:
- `/apps/web/app/dashboard/community/page.tsx`
- `/apps/web/components/community/CatalogBrowser.tsx`

**Features**:
- Header: "Community Deals" with filter/sort UI
- Main grid: Deal cards in responsive layout
- Filters:
  - Sort: Recent, Trending, Top Voted
  - Category: CPU, GPU, RAM, Storage, etc. (checkboxes)
  - Search box (debounced, 200ms)
- Pagination: "Load More" button or infinite scroll
- Empty state: "No deals found" message
- Loading states: Skeleton loaders while fetching

**Acceptance Criteria**:
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Filters work correctly (sort, category, search)
- [ ] Pagination working (infinite scroll or Load More)
- [ ] Search is debounced (200ms)
- [ ] API calls made to GET /api/v1/community-deals with correct params
- [ ] React Query used for data fetching
- [ ] Loading and error states displayed
- [ ] Accessibility:
  - [ ] WCAG 2.1 AA compliant
  - [ ] Keyboard navigation (Tab, Enter)
  - [ ] Screen reader support (aria labels, semantic HTML)
  - [ ] Focus management
- [ ] Performance:
  - [ ] Page loads in <2s (initial)
  - [ ] Search debounced
  - [ ] Lazy load images
- [ ] Unit tests:
  - [ ] Test rendering
  - [ ] Test filter interactions
  - [ ] Test pagination
  - [ ] Test API calls with React Query

**Success Metrics**:
- Page loads and displays deals
- Filters work correctly
- Accessible to screen readers and keyboard navigation

---

#### UI-002: Implement DealCard Component

**Objective**: Reusable card component for displaying deals

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: frontend-developer

**Files to Create**:
- `/apps/web/components/community/DealCard.tsx`

**Features**:
- Deal title and description (truncated)
- Component info (CPU, GPU, price, etc.)
- Vote count (upvote + downvote)
- Curator info (name, avatar, reputation badge)
- Affiliate flag (if applicable)
- Click to view full details
- Hover effects

**Acceptance Criteria**:
- [ ] Displays all deal info clearly
- [ ] Vote counts visible
- [ ] Curator name and avatar displayed
- [ ] Responsive (works on mobile/tablet/desktop)
- [ ] Accessibility:
  - [ ] Proper semantic HTML
  - [ ] Alt text on images
  - [ ] Keyboard navigable
  - [ ] Screen reader support
- [ ] Unit tests:
  - [ ] Test rendering with sample data
  - [ ] Test curator info display
  - [ ] Test vote count display

**Success Metrics**:
- Card displays all needed info
- Looks good on all screen sizes
- Accessible

---

#### UI-003: Implement VotingUI Component

**Objective**: Upvote/downvote UI component

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: frontend-developer

**Files to Create**:
- `/apps/web/components/community/VotingUI.tsx`
- `/apps/web/hooks/useVoting.ts` (custom hook for voting logic)

**Features**:
- Upvote button with count
- Downvote button with count
- Active state (user's vote highlighted)
- Loading state while voting
- Error message if vote fails
- Tooltip: "Login to vote"
- Rate limiting: Show "Too many votes, try again later" if 429

**Acceptance Criteria**:
- [ ] Vote buttons functional
- [ ] Active states show user's current vote
- [ ] Vote counts update after voting
- [ ] Loading states while voting
- [ ] Error handling (429 rate limit, 401 auth required)
- [ ] Accessibility:
  - [ ] Buttons are proper `<button>` elements
  - [ ] aria-labels on vote buttons
  - [ ] Focus indicators
  - [ ] Keyboard navigable
- [ ] API calls to POST /api/v1/votes and DELETE /api/v1/votes/:deal_id
- [ ] React Query mutation hooks for voting
- [ ] Unit tests:
  - [ ] Test vote submission
  - [ ] Test vote deletion
  - [ ] Test rate limit error (429)
  - [ ] Test auth error (401)
  - [ ] Test active state
- [ ] useVoting hook:
  - `const { vote, unvote, isVoting, userVote, error } = useVoting(dealId)`

**Success Metrics**:
- Voting UI works end-to-end
- Vote counts update
- Error handling working

---

#### UI-004: Implement CuratorBadge Component (Placeholder)

**Objective**: Visual component for curator reputation badge

**Duration**: 1 day
**Effort**: 1 story point
**Assignee**: frontend-developer

**Files to Create**:
- `/apps/web/components/community/CuratorBadge.tsx`

**Features** (Phase 3.1):
- Placeholder badge (shows rank, e.g., "★★★")
- Hover tooltip: "Reputation: 100"
- Hidden if reputation_score < 3 (Phase 3.2 will finalize thresholds)
- Styling prepared for final badge design (Phase 3.2)

**Features** (Phase 3.2 - Integration):
- Actual badge design and thresholds
- "Trusted Curator" for reputation >= 50
- "Rising Star" for reputation >= 20
- Dynamic styling based on badge level

**Acceptance Criteria**:
- [ ] Placeholder badge renders
- [ ] Accepts curator_id and reputation_score props
- [ ] Hidden if score < 3
- [ ] Hover tooltip shows score
- [ ] Styling prepared for final design
- [ ] Accessibility:
  - [ ] aria-label: "Reputation badge: Trusted Curator"
  - [ ] Icon + text (not color alone)
  - [ ] Sufficient contrast
- [ ] Unit tests:
  - [ ] Test rendering when score >= 3
  - [ ] Test hidden when score < 3
  - [ ] Test tooltip

**Success Metrics**:
- Badge component ready for Phase 3.2 integration
- Placeholder working

---

#### UI-005: Implement CuratorProfilePage Component

**Objective**: Curator profile page showing deals and stats

**Duration**: 2 days
**Effort**: 2 story points
**Assignee**: ui-engineer

**Files to Create**:
- `/apps/web/app/curator/[username]/page.tsx`
- `/apps/web/components/curator/CuratorProfile.tsx`

**Features**:
- Header: Curator name, avatar, bio
- Stats: Deals published, followers, reputation score
- "Follow" button (Phase 3.2 integration)
- Recent deals grid (10 most recent)
- View all deals link
- Empty state: "No deals published yet"

**Acceptance Criteria**:
- [ ] Profile page loads curator data from GET /api/v1/curator/:username
- [ ] All stats displayed (deals, followers, reputation)
- [ ] Recent deals listed in grid
- [ ] Responsive design
- [ ] Accessibility:
  - [ ] WCAG 2.1 AA
  - [ ] Semantic HTML
  - [ ] Screen reader support
- [ ] 404 handling (curator not found)
- [ ] React Query for data fetching
- [ ] Unit tests:
  - [ ] Test rendering with sample curator data
  - [ ] Test stats display
  - [ ] Test deals grid

**Success Metrics**:
- Profile page loads and displays curator info
- Deals listed correctly
- Responsive and accessible

---

### Testing Layer (TEST-001 through TEST-004)

#### TEST-001: Write CommunityDealRepository Tests

**Duration**: 1 day
**Effort**: 1.5 story points
**Assignee**: test-automator

**Files to Create**:
- `/tests/test_repositories/test_community_deal_repository.py`

**Test Cases**:
- [ ] test_create_community_deal
- [ ] test_get_by_id
- [ ] test_get_by_curator_id
- [ ] test_get_latest
- [ ] test_get_trending
- [ ] test_search (with filters)
- [ ] test_update_vote_count
- [ ] test_update_view_count
- [ ] test_pagination_cursor

**Coverage**: >90% of repository methods

---

#### TEST-002: Write VotingService Tests

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: test-automator

**Files to Create**:
- `/tests/test_services/test_voting_service.py`

**Test Cases**:
- [ ] test_vote_on_deal
- [ ] test_cannot_vote_twice_on_same_deal (deduplication)
- [ ] test_unvote
- [ ] test_vote_count_updates
- [ ] test_rate_limiting (SVC-003 integration)
- [ ] test_vote_type_validation

**Coverage**: >90% of service logic

---

#### TEST-003: Write API Integration Tests

**Duration**: 2 days
**Effort**: 2 story points
**Assignee**: test-automator

**Files to Create**:
- `/tests/test_api/test_community_deals_api.py`
- `/tests/test_api/test_votes_api.py`
- `/tests/test_api/test_curator_api.py`

**Test Cases** (community_deals_api):
- [ ] test_get_catalog_list
- [ ] test_get_trending
- [ ] test_publish_deal
- [ ] test_publish_deal_duplicate (409)
- [ ] test_publish_deal_rate_limit (429)
- [ ] test_search_deals
- [ ] test_view_single_deal (increments view_count)

**Test Cases** (votes_api):
- [ ] test_vote_on_deal
- [ ] test_vote_deduplication (409)
- [ ] test_unvote
- [ ] test_vote_stats
- [ ] test_vote_rate_limit (429)
- [ ] test_vote_without_auth (401)

**Test Cases** (curator_api):
- [ ] test_get_curator_profile
- [ ] test_get_curator_not_found (404)
- [ ] test_update_curator_profile
- [ ] test_top_curators

**Coverage**: >85% of API layer

---

#### TEST-004: Write E2E Tests

**Duration**: 2 days
**Effort**: 2 story points
**Assignee**: test-automator

**Files to Create**:
- `/tests/e2e/test_community_catalog.spec.ts` (Playwright or Cypress)

**Critical Journeys**:
- [ ] User publishes deal → Deal appears in catalog → Other user votes on it
- [ ] User browses catalog → Filters by category → Searches by keyword
- [ ] User votes on deal → Vote count updates in real-time
- [ ] Curator profile page loads → Shows published deals

**Coverage**: >80% of critical user flows

---

### Observability (OBS-001)

#### OBS-001: Add OpenTelemetry Spans

**Duration**: 1 day
**Effort**: 1 story point
**Assignee**: backend-architect

**Files to Modify**:
- All routers, services, and repositories

**Acceptance Criteria**:
- [ ] Spans created for all operations:
  - `publish_deal`, `browse_deals`, `vote_deal`, `unvote_deal`, `get_curator_profile`
- [ ] Span attributes:
  - `user_id`, `curator_id`, `deal_id`
  - `operation_name`, `status` (success/error)
  - `duration_ms`
- [ ] Structured logging with:
  - `trace_id`, `span_id`
  - `user_id`, `action`, `status`
- [ ] Dashboard in observability platform:
  - Latency metrics by operation
  - Error rate tracking
  - RPS (requests per second)

---

## Phase 3.2: Reputation & Notifications (Weeks 5-7)

**Objective**: Build curator recognition and engagement loops

### Phase 3.2 Overview

| Task ID | Task Name | Effort | Duration | Assignee | Dependencies |
|---------|-----------|--------|----------|----------|--------------|
| BATCH-001 | Implement reputation calculation batch job | 3 pts | 2 days | service-engineer | Phase 3.1 complete |
| BADGE-001 | Implement curator badge logic | 2 pts | 1 day | service-engineer | BATCH-001 |
| FOLLOW-001 | Create Follow table and FollowRepository | 2 pts | 1 day | data-layer-expert | Phase 3.1 complete |
| FOLLOW-002 | Implement FollowService | 1.5 pts | 1 day | service-engineer | FOLLOW-001 |
| NOTIF-001 | Create Notification table and NotificationRepository | 2 pts | 1 day | data-layer-expert | Phase 3.1 complete |
| NOTIF-002 | Implement NotificationService (async email) | 3 pts | 2 days | service-engineer | NOTIF-001, FOLLOW-002 |
| API-FOLLOW-001 | Implement follows router | 1.5 pts | 1 day | python-backend-engineer | FOLLOW-002 |
| API-NOTIF-001 | Implement notifications router | 2 pts | 1 day | python-backend-engineer | NOTIF-002 |
| UI-BADGE-001 | Integrate CuratorBadge component with real badges | 1 pt | 1 day | frontend-developer | BADGE-001 |
| UI-FOLLOW-001 | Implement FollowButton component | 1.5 pts | 1 day | frontend-developer | API-FOLLOW-001 |
| UI-NOTIF-001 | Implement NotificationPreferences UI | 2 pts | 1 day | ui-engineer | API-NOTIF-001 |
| TEST-BATCH-001 | Write reputation batch job tests | 1.5 pts | 1 day | test-automator | BATCH-001 |
| TEST-FOLLOW-001 | Write follow/unfollow tests | 1 pt | 1 day | test-automator | FOLLOW-002 |
| TEST-NOTIF-001 | Write notification delivery tests | 2 pts | 1 day | test-automator | NOTIF-002 |

**Critical Path**: Phase 3.1 → BATCH-001 → BADGE-001 → (FOLLOW-001/FOLLOW-002 parallel with NOTIF-001/NOTIF-002) → API-FOLLOW-001 & API-NOTIF-001 → UI integration

### Key Tasks (Summary)

**Database & Services:**
- Reputation batch job: Hourly calculation of curator scores (weighted votes + follows)
- Following mechanism: Track which users follow which curators
- Notification system: Async email delivery when curators publish deals

**API & Frontend:**
- Follows endpoints: POST /follows, DELETE /follows/:id
- Notification endpoints: GET /notifications, PUT /notifications/:id
- UI: Follow button, notification preferences, badge integration

**Quality Gates:**
- Reputation calculation complete in <5 min for 10,000 deals
- Notifications delivered 95%+ within 5 minutes
- Follow mechanism tested with >80% coverage
- All new endpoints documented

---

## Phase 3.1-3.2 Quality Gates Summary

### Before Phase 3.1 Ends
- [ ] Database schema created and migrations tested
- [ ] Community deal catalog API functional (browse, search, publish)
- [ ] Voting system preventing vote rings (deduplication at DB level)
- [ ] Rate limiting preventing spam
- [ ] All Phase 3.1 tests passing with >85% coverage
- [ ] Catalog pages <500ms response time
- [ ] Vote operations <100ms
- [ ] User profiles showing curator stats

### Before Phase 3.2 Ends
- [ ] Reputation batch job running hourly (5min for 10,000 deals)
- [ ] Curator badges display correctly (based on reputation thresholds)
- [ ] Following mechanism integrated
- [ ] Notifications delivered 95%+ within 5 minutes
- [ ] Notification preferences UI fully functional
- [ ] All Phase 3.2 tests passing with >85% coverage
- [ ] E2E tests: Publish → Vote → Follow → Notify working

### Before Proceeding to Phase 3.3
- [ ] Phase 1 & 2 integration verified (no breaking changes)
- [ ] All community features behind feature flags
- [ ] Observability dashboards active (latency, errors, RPS)
- [ ] Security review passed (RLS, rate limiting, vote integrity)
- [ ] Performance benchmarks met
- [ ] Team trained on new systems

---

**Total Phase 3.1-3.2 Effort**: 45 story points (approximately 2-3 weeks development + testing)
**Expected Completion**: End of Week 7

For Phase 3.3-3.4 details, see: `community-social-features-phase-3.3-3.4.md`
