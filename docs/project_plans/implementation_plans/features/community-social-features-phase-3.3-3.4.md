---
title: "Community & Social Features Phase 3.3-3.4 - Collaboration & Hardening"
description: "Detailed task breakdown for Phase 3.3 (Collaboration & Moderation: Collections, moderation queue, anti-abuse) and Phase 3.4 (Polish & Hardening: Performance, security, testing, documentation, launch). Includes quality gates and pre-launch checklist."
audience: [ai-agents, developers]
tags: [implementation, planning, community, phase-3.3, phase-3.4, moderation, anti-abuse, performance, security]
created: 2025-11-14
updated: 2025-11-14
category: "product-planning"
status: draft
related:
  - /home/user/deal-brain/docs/project_plans/implementation_plans/features/community-social-features-v1.md
  - /home/user/deal-brain/docs/project_plans/PRDs/community-social-features-v1.md
---

# Phase 3.3-3.4: Collaboration & Hardening Implementation

**Duration**: Weeks 8-12 (5 weeks total)
**Effort**: 40 story points (25 Phase 3.3 + 15 Phase 3.4)
**Key Deliverables**: Collaborative collections, moderation framework, anti-abuse measures, performance optimization, security hardening, documentation

---

## Phase 3.3: Collaboration & Moderation (Weeks 8-10)

**Objective**: Enable team collaboration and build comprehensive moderation framework

### Phase 3.3 Overview

| Task ID | Task Name | Effort | Duration | Assignee | Dependencies |
|---------|-----------|--------|----------|----------|--------------|
| COLLAB-001 | Create CollaborativeCollection permission model | 2 pts | 1 day | backend-architect | Phase 3.2 complete |
| COLLAB-002 | Create CollaborativeCollection and Collaborator tables | 2 pts | 1 day | data-layer-expert | COLLAB-001 |
| COLLAB-003 | Create Alembic migration for collab schema | 1.5 pts | 1 day | data-layer-expert | COLLAB-002 |
| COLLAB-REPO-001 | Implement CollaborativeCollectionRepository | 2 pts | 1 day | python-backend-engineer | COLLAB-003 |
| COLLAB-SVC-001 | Implement CollaborativeCollectionService | 3 pts | 2 days | service-engineer | COLLAB-REPO-001 |
| COLLAB-API-001 | Implement collaborative collection routers | 2 pts | 1 day | python-backend-engineer | COLLAB-SVC-001 |
| COLLAB-UI-001 | Implement CollaborativeCollectionUI | 2 pts | 1 day | ui-engineer | COLLAB-API-001 |
| MOD-TABLE-001 | Create ModerationFlag and RateLimitKey tables | 2 pts | 1 day | data-layer-expert | Phase 3.2 complete |
| MOD-MIGRATE-001 | Create Alembic migration for moderation schema | 1.5 pts | 1 day | data-layer-expert | MOD-TABLE-001 |
| MOD-REPO-001 | Implement ModerationRepository | 1.5 pts | 1 day | python-backend-engineer | MOD-MIGRATE-001 |
| MOD-SVC-001 | Implement ModerationService | 2 pts | 1 day | moderation-specialist | MOD-REPO-001 |
| ABUSE-SVC-001 | Enhance anti-abuse: Anomaly detection batch job | 3 pts | 2 days | moderation-specialist | Phase 3.1 SVC-003 |
| ABUSE-SVC-002 | Implement affiliate link detection | 1.5 pts | 1 day | moderation-specialist | ABUSE-SVC-001 |
| MOD-API-001 | Implement moderation endpoints (admin only) | 2 pts | 1 day | python-backend-engineer | MOD-SVC-001 |
| REPORT-API-001 | Implement user report endpoint | 1 pt | 1 day | python-backend-engineer | MOD-SVC-001 |
| MOD-UI-001 | Implement ModerationQueue admin UI | 3 pts | 2 days | ui-engineer | MOD-API-001 |
| REPORT-UI-001 | Implement report button on deal cards | 1 pt | 1 day | frontend-developer | REPORT-API-001 |
| GUIDELINES-001 | Create content guidelines page | 1 pt | 1 day | technical-writer | None (parallel) |
| TEST-COLLAB-001 | Write collaborative collection tests | 1.5 pts | 1 day | test-automator | COLLAB-SVC-001 |
| TEST-MOD-001 | Write moderation service tests | 1.5 pts | 1 day | test-automator | MOD-SVC-001 |
| TEST-ABUSE-001 | Write anomaly detection tests | 1.5 pts | 1 day | test-automator | ABUSE-SVC-001 |
| LOAD-TEST-001 | Performance load testing (catalog, voting, collab) | 2 pts | 2 days | test-automator | COLLAB-API-001 |

**Critical Path**: COLLAB-001 → COLLAB-002 → COLLAB-003 → COLLAB-REPO-001 → COLLAB-SVC-001 → COLLAB-API-001

---

## Phase 3.3 Detailed Tasks

### Collaborative Collections (COLLAB-001 through COLLAB-UI-001)

#### COLLAB-001: Create Collaborative Collection Permission Model

**Objective**: Design permission system for multi-user collection editing

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: backend-architect

**Acceptance Criteria**:
- [ ] Define permission model:
  - **Owner**: Created collection; can invite, remove, delete, publish, edit settings
  - **Editor**: Invited by owner; can add/remove deals, see collaborators; cannot delete collection
  - **Viewer**: (Phase 4+) Read-only access; cannot edit

- [ ] Invite workflow documented:
  - Owner invites user by email/username
  - Invitation created with token/link
  - Invitee accepts or declines
  - Once accepted, becomes Editor on collection

- [ ] Permission checks:
  - Only owner can delete collection
  - Only owner/editors can modify deals in collection
  - Only owner can change collaborators
  - Viewers (future) cannot modify

- [ ] Edge cases:
  - Owner leaves collection (becomes archived or reassigns)
  - Last owner leaves (collection remains, editors cannot delete)
  - Remove collaborator (stop notifications, hide from collaborator list)
  - Invitations expire after 30 days if not accepted

**Success Criteria**:
- Permission model clear and documented
- Ready for implementation in COLLAB-002

---

#### COLLAB-002: Create CollaborativeCollection Tables

**Objective**: Design schema for multi-user collections

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: data-layer-expert

**Files to Create**:
- Migration: `/apps/api/alembic/versions/2025_11_XX_collaborative_collections.py`

**Tables**:

```sql
-- Extend existing Collection (or create new if not exists)
CollaborativeCollection(
  id (UUID, PK),
  owner_id (UUID, FK to User, indexed),
  name (VARCHAR),
  description (TEXT, optional),
  is_collaborative (BOOLEAN, default false),
  created_at, updated_at,
  ForeignKey(owner_id) -> User(id)
)

-- Permissions
Collaborator(
  id (UUID, PK),
  collection_id (UUID, FK, indexed),
  user_id (UUID, FK to User, indexed),
  role (ENUM: OWNER, EDITOR),
  invited_at, joined_at,
  created_at, updated_at,
  UNIQUE(collection_id, user_id),
  ForeignKey(collection_id) -> CollaborativeCollection(id),
  ForeignKey(user_id) -> User(id)
)

-- Invitation
CollaboratorInvitation(
  id (UUID, PK),
  collection_id (UUID, FK, indexed),
  invited_by (UUID, FK to User),
  invited_email (VARCHAR),
  token (VARCHAR, UNIQUE, indexed),
  status (ENUM: PENDING, ACCEPTED, DECLINED),
  expires_at (TIMESTAMP),
  created_at, updated_at,
  ForeignKey(collection_id) -> CollaborativeCollection(id),
  ForeignKey(invited_by) -> User(id)
)

-- Audit trail
CollaboratorAuditLog(
  id (UUID, PK),
  collection_id (UUID, FK, indexed),
  action (ENUM: ADDED, REMOVED, INVITED, JOINED, INVITATION_DECLINED),
  actor_id (UUID, FK to User),
  target_user_id (UUID, optional),
  details (JSONB),
  created_at,
  ForeignKey(collection_id) -> CollaborativeCollection(id),
  ForeignKey(actor_id) -> User(id)
)
```

**Acceptance Criteria**:
- [ ] Tables created with proper FKs and constraints
- [ ] Indexes on (owner_id), (collection_id, user_id), (token)
- [ ] UNIQUE constraint on (collection_id, user_id) prevents duplicate collaborators
- [ ] Invitation token is cryptographically secure (UUID or random string)
- [ ] Audit log tracks all changes for transparency

**Success Metrics**:
- Schema ready for Phase 3.3 implementation
- Supports 1000+ collaborators per collection (if needed)

---

#### COLLAB-003: Create Alembic Migration

**Objective**: Integrate collaborative collection schema into migration framework

**Duration**: 1 day
**Effort**: 1.5 story points
**Assignee**: data-layer-expert

**Acceptance Criteria**:
- [ ] Migration follows Alembic conventions
- [ ] Rollback supported
- [ ] Tested in dev environment

---

#### COLLAB-REPO-001: Implement CollaborativeCollectionRepository

**Objective**: Data access layer for collaborative collections

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: python-backend-engineer

**Files to Create**:
- `/apps/api/dealbrain_api/repositories/collaborative_collection_repository.py`

**Methods**:
- `async create(owner_id: UUID, name: str, description: str | None) -> CollaborativeCollection`
- `async get_by_id(collection_id: UUID) -> CollaborativeCollection | None`
- `async get_user_collections(user_id: UUID, skip: int, limit: int) -> list[CollaborativeCollection]`
- `async add_collaborator(collection_id: UUID, user_id: UUID, role: str) -> Collaborator`
- `async remove_collaborator(collection_id: UUID, user_id: UUID) -> bool`
- `async get_collaborators(collection_id: UUID) -> list[Collaborator]`
- `async get_collaborator_role(collection_id: UUID, user_id: UUID) -> str | None`
- `async is_owner(collection_id: UUID, user_id: UUID) -> bool`
- `async is_editor(collection_id: UUID, user_id: UUID) -> bool`
- `async create_invitation(collection_id: UUID, invited_by: UUID, invited_email: str) -> CollaboratorInvitation`
- `async accept_invitation(token: str, user_id: UUID) -> CollaborativeCollection | None`
- `async decline_invitation(token: str) -> bool`
- `async log_audit(collection_id: UUID, action: str, actor_id: UUID, details: dict) -> CollaboratorAuditLog`

**Acceptance Criteria**:
- [ ] All methods implemented and tested
- [ ] Permission checks (owner, editor) at DB level
- [ ] Invitation tokens secure and unique
- [ ] Audit log captures all changes
- [ ] No N+1 queries
- [ ] Unit tests >90% coverage

---

#### COLLAB-SVC-001: Implement CollaborativeCollectionService

**Objective**: Business logic for multi-user collection editing

**Duration**: 2 days
**Effort**: 3 story points
**Assignee**: service-engineer

**Files to Create**:
- `/apps/api/dealbrain_api/services/collaborative_collection_service.py`

**Methods**:
- `async create_collection(owner_id: UUID, name: str, description: str | None) -> CollaborativeCollectionDTO`
  - Creates collection with owner as sole collaborator
  - Returns DTO

- `async get_collection(collection_id: UUID, user_id: UUID) -> CollaborativeCollectionDTO`
  - Checks user has access (is collaborator or public)
  - Includes collaborators list

- `async invite_collaborator(collection_id: UUID, inviter_id: UUID, invited_email: str) -> InvitationDTO`
  - Checks inviter is owner
  - Creates invitation
  - Sends email with accept/decline links (Phase 3.3)
  - Logs audit entry

- `async accept_invitation(token: str, user_id: UUID) -> CollaborativeCollectionDTO`
  - Validates token exists and not expired
  - Adds user as Editor
  - Logs audit entry
  - Removes invitation

- `async remove_collaborator(collection_id: UUID, remover_id: UUID, target_user_id: UUID) -> bool`
  - Checks remover is owner
  - Removes collaborator
  - Logs audit entry
  - Prevents removing last owner (or handles gracefully)

- `async add_deal_to_collection(collection_id: UUID, user_id: UUID, deal_id: UUID) -> CollaborativeCollectionDTO`
  - Checks user is editor/owner
  - Adds deal
  - Logs modification

- `async remove_deal_from_collection(collection_id: UUID, user_id: UUID, deal_id: UUID) -> bool`
  - Checks user is editor/owner
  - Removes deal
  - Logs modification

- `async publish_collection_to_catalog(collection_id: UUID, user_id: UUID) -> CommunityDealDTO`
  - Checks user is owner
  - Creates collection as single deal in community catalog
  - Credits all collaborators
  - Logs audit entry

- `async get_audit_log(collection_id: UUID, user_id: UUID) -> list[AuditLogDTO]`
  - Checks user is collaborator
  - Returns audit entries

**Acceptance Criteria**:
- [ ] All methods implemented
- [ ] Permission checks (owner, editor) enforced
- [ ] Email invitations sent (integration with email service)
- [ ] Audit trail complete
- [ ] RLS enforcement
- [ ] Unit tests >80% coverage

---

#### COLLAB-API-001: Implement Collaborative Collection Routers

**Objective**: HTTP endpoints for collection collaboration

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: python-backend-engineer

**Endpoints**:

1. **POST /api/v1/collections** (Create Collection)
   - Request: `{ "name": str, "description": str | null }`
   - Response: `CollaborativeCollectionDTO`
   - Auth required

2. **GET /api/v1/collections/:id** (Get Collection)
   - Response: `CollaborativeCollectionDTO` (includes collaborators)
   - Auth required

3. **GET /api/v1/collections** (List User Collections)
   - Query: `skip=0, limit=50`
   - Response: `{ "items": [CollaborativeCollectionDTO], "total": int }`
   - Auth required

4. **POST /api/v1/collections/:id/invitations** (Invite Collaborator)
   - Request: `{ "invited_email": str }`
   - Response: `InvitationDTO`
   - Auth required (owner only)
   - Returns 403 if not owner

5. **POST /api/v1/collections/invitations/:token/accept** (Accept Invitation)
   - Response: `CollaborativeCollectionDTO`
   - Auth required

6. **POST /api/v1/collections/invitations/:token/decline** (Decline Invitation)
   - Response: `{ "success": bool }`

7. **DELETE /api/v1/collections/:id/collaborators/:user_id** (Remove Collaborator)
   - Response: `{ "success": bool }`
   - Auth required (owner only)

8. **GET /api/v1/collections/:id/audit-log** (Get Audit Log)
   - Response: `{ "items": [AuditLogDTO], "total": int }`
   - Auth required (collaborators only)

9. **POST /api/v1/collections/:id/deals/:deal_id** (Add Deal to Collection)
   - Response: `CollaborativeCollectionDTO`
   - Auth required (editor/owner)

10. **DELETE /api/v1/collections/:id/deals/:deal_id** (Remove Deal from Collection)
    - Response: `{ "success": bool }`
    - Auth required (editor/owner)

**Acceptance Criteria**:
- [ ] All endpoints implemented
- [ ] Permission checks (owner, editor) enforced
- [ ] Proper error responses (401, 403, 404, 409)
- [ ] OpenTelemetry spans
- [ ] Rate limiting (optional, Phase 3.3)
- [ ] Cursor-based pagination
- [ ] Unit tests >80% coverage

---

#### COLLAB-UI-001: Implement CollaborativeCollectionUI

**Objective**: Frontend for multi-user collection editing

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: ui-engineer

**Components**:
- `/apps/web/components/collections/CollaborativeCollectionEditor.tsx`
- `/apps/web/components/collections/CollaboratorsList.tsx`
- `/apps/web/components/collections/InviteCollaborator.tsx`
- `/apps/web/app/collections/:id/edit/page.tsx`

**Features**:
- Collection name/description editor
- Collaborators list (role, invite date)
- Invite collaborator button (email input)
- Remove collaborator button (owner only)
- Add/remove deals from collection
- Audit log viewer (optional)

**Acceptance Criteria**:
- [ ] Edit collection name/description
- [ ] Invite collaborators by email
- [ ] Accept/decline invitations
- [ ] Remove collaborators (owner only)
- [ ] Add/remove deals
- [ ] Responsive design
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] Unit tests >80% coverage

---

### Moderation Framework (MOD-TABLE-001 through MOD-UI-001)

#### MOD-TABLE-001: Create ModerationFlag and Related Tables

**Objective**: Database schema for moderation and anti-abuse

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: data-layer-expert

**Tables**:

```sql
ModerationFlag(
  id (UUID, PK),
  community_deal_id (UUID, FK, indexed),
  flagged_by (UUID, FK to User, nullable - allows admin flags),
  reason (ENUM: SPAM, ABUSE, AFFILIATE, MISLEADING, OTHER),
  user_comment (TEXT, optional),
  status (ENUM: OPEN, UNDER_REVIEW, APPROVED, REMOVED, APPEALED),
  admin_notes (TEXT, optional),
  appeal_notes (TEXT, optional),
  resolved_at (TIMESTAMP, nullable),
  resolver_id (UUID, FK to User, nullable),
  resolved_reason (TEXT, optional),
  created_at, updated_at,
  audit_log (JSONB),  -- history of all state changes
  ForeignKey(community_deal_id) -> CommunityDeal(id),
  ForeignKey(flagged_by) -> User(id),
  ForeignKey(resolver_id) -> User(id)
)

RateLimitKey(
  id (UUID, PK),
  key_type (ENUM: VOTE, PUBLISH),
  key_value (VARCHAR, indexed),  -- user_id or IP:user_id
  count (INTEGER),
  reset_at (TIMESTAMP, indexed),
  created_at, updated_at
)

AnomalyDetectionLog(
  id (UUID, PK),
  event_type (ENUM: RAPID_VOTING, VOTE_RING, SPAM_PUBLISHING, BOT_DETECTED, UNUSUAL_REPUTATION),
  target_id (UUID, indexed),  -- deal_id or user_id
  severity (ENUM: LOW, MEDIUM, HIGH),
  details (JSONB),  -- pattern details, IPs involved, etc.
  resolved (BOOLEAN, default false),
  action_taken (VARCHAR, nullable),  -- "flagged", "rate_limit_applied", "suspended"
  created_at, updated_at
)

AffiliateLink(
  id (UUID, PK),
  community_deal_id (UUID, FK, indexed),
  url (VARCHAR),
  detected_network (VARCHAR),  -- "amazon", "ebay", etc.
  flagged_for_review (BOOLEAN, default true),
  review_status (ENUM: PENDING, APPROVED, REJECTED),
  created_at, updated_at
)
```

**Acceptance Criteria**:
- [ ] Tables created with proper FKs and constraints
- [ ] Indexes on (community_deal_id), (status), (created_at)
- [ ] Audit log tracks all state changes
- [ ] RateLimitKey has automatic expiry (TTL)
- [ ] AnomalyDetectionLog indexed for quick queries

---

#### MOD-MIGRATE-001: Create Alembic Migration

**Objective**: Integrate moderation schema

**Duration**: 1 day
**Effort**: 1.5 story points
**Assignee**: data-layer-expert

**Acceptance Criteria**:
- [ ] Migration follows Alembic conventions
- [ ] Rollback supported
- [ ] Tested in dev

---

#### MOD-REPO-001: Implement ModerationRepository

**Objective**: Data access for moderation operations

**Duration**: 1 day
**Effort**: 1.5 story points
**Assignee**: python-backend-engineer

**Methods**:
- `async create_flag(deal_id: UUID, flagged_by: UUID, reason: str, comment: str | None) -> ModerationFlag`
- `async get_flag(flag_id: UUID) -> ModerationFlag | None`
- `async get_open_flags(skip: int, limit: int, sort_by: str = 'created_at') -> list[ModerationFlag]`
- `async get_flags_for_deal(deal_id: UUID) -> list[ModerationFlag]`
- `async update_flag_status(flag_id: UUID, status: str, admin_notes: str, resolver_id: UUID) -> ModerationFlag`
- `async add_audit_entry(flag_id: UUID, action: str, details: dict) -> None`
- `async get_audit_log(flag_id: UUID) -> list[dict]`

**For Rate Limiting:**
- `async get_rate_limit(key_type: str, key_value: str) -> RateLimitKey | None`
- `async increment_rate_limit(key_type: str, key_value: str, reset_at: datetime) -> int`
- `async reset_rate_limits() -> None` (batch job)

**For Anomaly Detection:**
- `async log_anomaly(event_type: str, target_id: UUID, severity: str, details: dict) -> AnomalyDetectionLog`
- `async get_high_severity_anomalies(skip: int, limit: int) -> list[AnomalyDetectionLog]`
- `async resolve_anomaly(anomaly_id: UUID, action_taken: str) -> None`

**Acceptance Criteria**:
- [ ] All methods implemented and tested
- [ ] Audit log captures all changes
- [ ] Rate limit queries efficient
- [ ] No N+1 queries

---

#### MOD-SVC-001: Implement ModerationService

**Objective**: Business logic for moderation workflow

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: moderation-specialist

**Methods**:
- `async flag_deal(deal_id: UUID, flagged_by: UUID, reason: str, comment: str | None) -> ModerationFlagDTO`
  - Creates flag with status=OPEN
  - Logs to audit trail
  - Sends alert to moderation team (optional)

- `async get_moderation_queue(skip: int, limit: int, sort_by: str = 'severity') -> list[ModerationFlagDTO]`
  - Returns open + under_review flags, sorted by severity

- `async approve_flag(flag_id: UUID, resolver_id: UUID, admin_notes: str) -> ModerationFlagDTO`
  - Sets status=APPROVED
  - Does NOT remove deal (flag is informational)
  - Logs audit entry

- `async reject_flag(flag_id: UUID, resolver_id: UUID, admin_notes: str) -> ModerationFlagDTO`
  - Sets status=REMOVED
  - Soft-deletes deal (hidden from catalog, kept in DB)
  - Notifies curator of removal (generic reason: "Did not meet content guidelines")
  - Logs audit entry

- `async appeal_flag(flag_id: UUID, curator_id: UUID, appeal_notes: str) -> ModerationFlagDTO`
  - Sets status=APPEALED
  - Adds appeal_notes
  - Escalates to review team
  - Logs audit entry

- `async get_flagged_deal_count() -> int`
  - Returns count of open + under_review flags (for dashboard)

- `async get_moderation_metrics() -> dict`
  - Returns: total_flags, open_count, resolved_count, avg_resolution_time, appeal_rate

**Acceptance Criteria**:
- [ ] Moderation workflow complete
- [ ] Audit trail immutable
- [ ] Notifications sent to curators
- [ ] Metrics for monitoring
- [ ] Unit tests >80% coverage

---

#### ABUSE-SVC-001: Enhance Anti-Abuse - Anomaly Detection Batch Job

**Objective**: Detect suspicious voting and publishing patterns

**Duration**: 2 days
**Effort**: 3 story points
**Assignee**: moderation-specialist

**Files to Modify/Create**:
- `/apps/api/dealbrain_api/services/anti_abuse_service.py` (extend from Phase 3.1)
- `/apps/api/dealbrain_api/celery_tasks/anomaly_detection.py` (new)

**Batch Job** (Runs hourly):

1. **Rapid Voting Detection:**
   - Query: Votes in last 60 minutes
   - Pattern: Same user voting on >20 deals in <60 min
   - Pattern: Same IP voting on >50 deals in <60 min
   - Action: Flag event, log to AnomalyDetectionLog with severity=HIGH

2. **Vote Ring Detection:**
   - Query: Deals with unusual vote patterns in last 24 hours
   - Pattern: Deal with >50 votes, all from new accounts (<7 days)
   - Pattern: Multiple deals, overlapping voter IPs
   - Action: Flag all deals, log anomalies with severity=HIGH

3. **Spam Publishing Detection:**
   - Query: Deals published in last 24 hours
   - Pattern: User publishing >10 deals/day
   - Pattern: User publishing from >5 different IPs/day
   - Pattern: All deals pointing to same affiliate domain
   - Action: Flag deals, rate-limit user, log anomalies with severity=MEDIUM/HIGH

4. **Bot Detection:**
   - Query: User profile activity
   - Pattern: Account created, published deals, voted on deals all within <1 hour
   - Pattern: Perfect vote distribution (balanced up/down votes)
   - Pattern: Non-human-like behavior patterns
   - Action: Flag account, rate-limit, log anomaly with severity=HIGH

5. **Curator Reputation Spike:**
   - Query: Reputation changes in last hour
   - Pattern: Reputation increase >100 points in <1 hour
   - Action: Review votes on deals, flag if anomalous

**Acceptance Criteria**:
- [ ] All patterns implemented
- [ ] Batch job completes in <5 minutes for 10,000 deals
- [ ] Severity scoring accurate
- [ ] Alerts sent to admin for HIGH severity
- [ ] No false positives on legitimate activity
- [ ] Unit tests >80% coverage
- [ ] Configurable thresholds (via settings)

---

#### ABUSE-SVC-002: Implement Affiliate Link Detection

**Objective**: Detect and flag affiliate links on community deals

**Duration**: 1 day
**Effort**: 1.5 story points
**Assignee**: moderation-specialist

**Files to Create**:
- `/apps/api/dealbrain_api/services/affiliate_detection_service.py`

**Implementation**:
- Regex patterns for common affiliate networks:
  - Amazon: `/gp/offer-listing/`, `amazon.com/?ref=`, `/tag/`
  - eBay: `ebay.com` + tracking params
  - Newegg: `shell_click.aspx`
  - Others: BestBuy, Micro Center, etc.

**Methods**:
- `detect_affiliate_link(url: str) -> (is_affiliate: bool, network: str | None, confidence: float)`
  - Returns True if URL matches known affiliate pattern
  - Includes network name (e.g., "amazon")
  - Confidence score (0.0-1.0)

- `flag_for_review(deal_id: UUID, url: str, network: str, confidence: float) -> AffiliateLink`
  - Creates AffiliateLink record
  - Sets flagged_for_review=True
  - Returns DTO

- `approve_affiliate_link(link_id: UUID, reviewer_id: UUID) -> AffiliateLink`
  - Sets review_status=APPROVED
  - Link remains visible, disclosure badge shown

- `reject_affiliate_link(link_id: UUID, reviewer_id: UUID) -> None`
  - Sets review_status=REJECTED
  - Can trigger deal removal if policy requires

**UI Integration**:
- POST /api/v1/community-deals endpoint includes optional `affiliate_url` parameter
- On publish, service calls detect_affiliate_link()
- If affiliate detected:
  - If confidence >0.9: Flag immediately, require admin approval before publish
  - If confidence 0.5-0.9: Flag, show warning to curator, allow publish with disclosure

**Acceptance Criteria**:
- [ ] Affiliate detection working
- [ ] Regex patterns accurate (high precision, low false positive)
- [ ] Reviewable in moderation queue
- [ ] Disclosure badge shown on deal cards
- [ ] Unit tests >80% coverage

---

#### MOD-API-001: Implement Moderation Endpoints (Admin Only)

**Objective**: HTTP endpoints for admin moderation

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: python-backend-engineer

**Endpoints** (All require `is_admin` role check):

1. **GET /api/v1/admin/moderation/queue** (Moderation Queue)
   - Query: `skip=0, limit=50, sort_by=severity|created_at, status=open|under_review|all`
   - Response: `{ "items": [ModerationFlagDTO], "total": int, "queue_stats": {...} }`
   - Returns open + under_review flags

2. **GET /api/v1/admin/moderation/flags/:flag_id** (Get Flag Details)
   - Response: `ModerationFlagDTO` (includes audit log)

3. **POST /api/v1/admin/moderation/flags/:flag_id/approve** (Approve Flag)
   - Request: `{ "admin_notes": str }`
   - Response: `ModerationFlagDTO`

4. **POST /api/v1/admin/moderation/flags/:flag_id/reject** (Reject Flag / Remove Deal)
   - Request: `{ "admin_notes": str, "removal_reason": str }`
   - Response: `ModerationFlagDTO`
   - Side effect: Soft-delete deal, notify curator

5. **POST /api/v1/admin/moderation/flags/:flag_id/appeal** (Start Appeal Review)
   - Request: `{ "status": "under_review_appeal" }`
   - Response: `ModerationFlagDTO`

6. **GET /api/v1/admin/moderation/metrics** (Moderation Metrics)
   - Response: `{ "total_flags": int, "open_count": int, "avg_resolution_time_hours": float, "appeal_rate": float }`

7. **GET /api/v1/admin/anomalies/high-severity** (High-Severity Anomalies)
   - Query: `skip=0, limit=50`
   - Response: `{ "items": [AnomalyDetectionLogDTO], "total": int }`

8. **POST /api/v1/admin/anomalies/:anomaly_id/resolve** (Resolve Anomaly)
   - Request: `{ "action_taken": str }`
   - Response: `AnomalyDetectionLogDTO`

**Acceptance Criteria**:
- [ ] All endpoints require admin authentication
- [ ] Proper error responses (401, 403)
- [ ] Audit logging of all moderation actions
- [ ] OpenTelemetry spans
- [ ] Unit tests >80% coverage

---

#### REPORT-API-001: Implement User Report Endpoint

**Objective**: Allow users to report problematic deals

**Duration**: 1 day
**Effort**: 1 story point
**Assignee**: python-backend-engineer

**Endpoint**:

**POST /api/v1/community-deals/:deal_id/report** (Report Deal)
- Request: `{ "reason": str, "comment": str | null }`
- Response: `{ "success": bool, "message": str }`
- Auth required
- Rate limiting: Max 5 reports/day per user
- Creates ModerationFlag with status=OPEN
- flagged_by = current user
- Returns success message: "Thank you for reporting. We'll review this deal shortly."

**Acceptance Criteria**:
- [ ] Endpoint implemented
- [ ] Rate limiting enforced
- [ ] Flag created with user context
- [ ] Confirmation message displayed
- [ ] Unit tests

---

#### MOD-UI-001: Implement Moderation Queue Admin UI

**Objective**: Admin dashboard for reviewing and resolving flags

**Duration**: 2 days
**Effort**: 3 story points
**Assignee**: ui-engineer

**Files to Create**:
- `/apps/web/app/admin/moderation/page.tsx`
- `/apps/web/components/admin/ModerationQueue.tsx`
- `/apps/web/components/admin/FlagReviewModal.tsx`
- `/apps/web/components/admin/AnomalyAlerts.tsx`

**Features**:
- **Moderation Queue Table:**
  - Flagged deal (title, curator, deal info)
  - Reason (SPAM, ABUSE, etc.)
  - Reporter (username or "Anonymous")
  - Status (OPEN, UNDER_REVIEW, RESOLVED)
  - Severity (HIGH, MEDIUM, LOW)
  - Created (timestamp)
  - Actions: "Review", "Approve", "Reject"

- **Flag Review Modal:**
  - Deal preview (image, title, description, price, components)
  - Curator info (name, reputation, # deals)
  - Flag reason and reporter comment
  - Audit log (previous flags on this curator?)
  - Admin notes text area
  - Approval/Rejection buttons
  - Appeal handling (if applicable)

- **Anomaly Alerts Section:**
  - List of high-severity anomalies
  - Event type, severity, target (deal/user)
  - Details (pattern description)
  - Action buttons: "Investigate", "Flag", "Resolve"

- **Queue Metrics Dashboard:**
  - Total flags, open count, resolved count
  - Avg resolution time
  - Flag distribution by reason
  - Most active reviewers

**Acceptance Criteria**:
- [ ] Queue loads correctly
- [ ] Review modal displays all info
- [ ] Approve/reject buttons functional
- [ ] Audit log visible
- [ ] Anomaly alerts visible
- [ ] Metrics dashboard working
- [ ] Responsive design
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] Unit tests >80% coverage

---

#### REPORT-UI-001: Implement Report Button on Deal Cards

**Objective**: User-facing report mechanism

**Duration**: 1 day
**Effort**: 1 story point
**Assignee**: frontend-developer

**Files to Modify**:
- `/apps/web/components/community/DealCard.tsx`
- `/apps/web/components/community/ReportDealModal.tsx` (new)

**Features**:
- "Report" button on deal card (or in menu)
- Clicking opens modal with form:
  - Reason dropdown: "Spam", "Abuse", "Affiliate link", "Misleading", "Other"
  - Comment text area (optional)
  - "Submit" button
- After submit: Success message
- Form validation (reason required)

**Acceptance Criteria**:
- [ ] Report button visible
- [ ] Modal displays with form
- [ ] POST /api/v1/community-deals/:deal_id/report called
- [ ] Success/error messages shown
- [ ] Rate limiting handled (429 response)
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] Unit tests

---

#### GUIDELINES-001: Create Content Guidelines Page

**Objective**: Document community standards

**Duration**: 1 day
**Effort**: 1 story point
**Assignee**: technical-writer

**Files to Create**:
- `/apps/web/app/community-guidelines/page.tsx`
- `/docs/community-guidelines.md` (source)

**Content**:
- Welcome & mission
- Acceptable content:
  - Objective deal evaluations
  - Performance metrics and comparisons
  - Component specifications and pricing
- Prohibited content:
  - Spam (repeated deals, off-topic)
  - Abuse (harassment, discrimination, hate speech)
  - Affiliate link abuse (undisclosed or excessive)
  - Misleading information (false specs, photoshopped prices)
  - Malware or security risks
- Enforcement & appeals:
  - How flags are reviewed
  - Appeal process
  - Community moderators (future)
- Contact support: Email/form

**Acceptance Criteria**:
- [ ] Guidelines published and visible
- [ ] Clear and understandable
- [ ] Linked from catalog page
- [ ] Mobile-friendly
- [ ] Accessibility (WCAG 2.1 AA)

---

### Phase 3.3 Testing & Load Testing

#### TEST-COLLAB-001: Write Collaborative Collection Tests

**Duration**: 1 day
**Effort**: 1.5 story points
**Assignee**: test-automator

**Test Cases**:
- [ ] Create collaborative collection
- [ ] Invite collaborator
- [ ] Accept/decline invitation
- [ ] Add/remove deals
- [ ] Remove collaborator
- [ ] Permission checks (owner only, editor only)
- [ ] Publish to community catalog
- [ ] Audit log tracking

**Coverage**: >85%

---

#### TEST-MOD-001: Write Moderation Service Tests

**Duration**: 1 day
**Effort**: 1.5 story points
**Assignee**: test-automator

**Test Cases**:
- [ ] Create flag
- [ ] Approve flag
- [ ] Reject flag (soft delete deal)
- [ ] Appeal flag
- [ ] Audit log updates
- [ ] Flag assignment to reviewers

**Coverage**: >85%

---

#### TEST-ABUSE-001: Write Anomaly Detection Tests

**Duration**: 1 day
**Effort**: 1.5 story points
**Assignee**: test-automator

**Test Cases**:
- [ ] Rapid voting detection
- [ ] Vote ring detection
- [ ] Spam publishing detection
- [ ] Bot detection
- [ ] Reputation spike detection
- [ ] Affiliate link detection

**Coverage**: >85%

---

#### LOAD-TEST-001: Performance Load Testing

**Duration**: 2 days
**Effort**: 2 story points
**Assignee**: test-automator

**Scenarios**:
- [ ] Catalog browse: 100+ concurrent users
- [ ] Voting: 10+ requests per second
- [ ] Collaborative collection edits: 50+ concurrent editors
- [ ] Moderation queue: Load with 1,000+ flags

**Acceptance Criteria**:
- [ ] Catalog browse: <500ms response time
- [ ] Vote submission: <100ms
- [ ] Collection edits: <200ms
- [ ] Database: <5% error rate under load
- [ ] No memory leaks detected

---

## Phase 3.4: Polish & Hardening (Weeks 11-12)

**Objective**: Performance, security, testing, documentation, launch readiness

### Phase 3.4 Overview

| Task ID | Task Name | Effort | Duration | Assignee | Dependencies |
|---------|-----------|--------|----------|----------|--------------|
| PERF-001 | Performance optimization (queries, caching) | 3 pts | 2 days | python-backend-engineer | Phase 3.3 complete |
| SECURITY-001 | Security audit and hardening | 2 pts | 1 day | security-specialist | Phase 3.3 complete |
| TEST-E2E-001 | Write E2E tests for critical journeys | 2 pts | 2 days | test-automator | Phase 3.3 complete |
| TEST-ACCESSIBILITY-001 | Accessibility audit (WCAG 2.1 AA) | 2 pts | 1 day | test-automator | Phase 3.3 UI complete |
| DOC-API-001 | API documentation (OpenAPI/Swagger) | 2 pts | 1 day | technical-writer | Phase 3.3 API complete |
| DOC-USER-001 | User guides (publish, vote, follow, notify) | 2 pts | 1 day | technical-writer | Phase 3.3 complete |
| DOC-MOD-001 | Moderation guide (for admins) | 1.5 pts | 1 day | technical-writer | Phase 3.3 complete |
| DOC-ADR-001 | Architecture Decision Records (reputation, voting, moderation, anti-abuse) | 2 pts | 1 day | technical-writer | Phase 3.3 complete |
| MONITORING-001 | Set up post-launch monitoring and alerting | 2 pts | 1 day | backend-architect | Phase 3.3 complete |
| MIGRATION-001 | Prepare database migration runbook | 1 pt | 1 day | data-layer-expert | All DB work |
| FEATURE-FLAGS-001 | Enable feature flags for gradual rollout | 1 pt | 1 day | backend-architect | Phase 3.3 complete |
| FINAL-REVIEW-001 | Final review and sign-off | 1 pt | 1 day | tech-lead | All tasks complete |

**Total Effort**: 15 story points

---

## Phase 3.4 Detailed Tasks

### Performance & Security (PERF-001, SECURITY-001)

#### PERF-001: Performance Optimization

**Objective**: Ensure all targets met and optimize hot paths

**Duration**: 2 days
**Effort**: 3 story points
**Assignee**: python-backend-engineer

**Tasks**:
- [ ] Query optimization:
  - Identify slow queries (>100ms) using APM
  - Add indexes where needed
  - Optimize N+1 queries
  - Use SELECT * efficiently (only needed columns)

- [ ] Caching strategy:
  - Cache curator profiles (5 min TTL)
  - Cache trending deals (1 min TTL)
  - Cache vote counts on deals (real-time via counter)
  - Use Redis for rate limiting (instead of DB queries)

- [ ] Batch operations:
  - Batch vote count updates (instead of 1-per-vote)
  - Batch reputation calculations (hourly)
  - Batch notification sends (via task queue)

- [ ] Database optimization:
  - Denormalize frequently-queried fields (vote_count, reputation_score)
  - Create read replicas for catalog queries (if at scale)
  - Tune connection pool size

- [ ] API optimization:
  - Implement compression (gzip)
  - Optimize payload sizes (DTO selection)
  - Cursor-based pagination (not offset/limit)

**Acceptance Criteria**:
- [ ] All endpoints meet response time targets:
  - Catalog browse: <500ms
  - Vote submission: <100ms
  - Profile load: <2s
  - Reputation batch: <5 min for 10,000 deals
  - Notification delivery: 95%+ within 5 min

- [ ] Load test passes:
  - 500+ concurrent catalog users
  - 50+ RPS voting
  - <1% error rate

- [ ] Database metrics:
  - Query P95 <100ms
  - Connection pool utilization <80%

---

#### SECURITY-001: Security Audit & Hardening

**Objective**: Identify and fix security vulnerabilities

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: security-specialist

**Audit Checklist**:
- [ ] Authentication:
  - JWT tokens validated
  - Sessions secure (secure cookie flags)
  - Rate limiting on auth endpoints

- [ ] Authorization:
  - RLS policies enforced on all data access
  - Admin endpoints require role check
  - No privilege escalation possible

- [ ] Vote Integrity:
  - UNIQUE constraint prevents double-voting
  - Vote counts immutable (no manual edits)
  - Vote deletion logged and audited

- [ ] Rate Limiting:
  - Voting: Max 10/hour per user, 1/min per IP
  - Publishing: Max 5/day per user, 10/day per IP
  - Limits enforced at API layer + middleware

- [ ] Data Protection:
  - PII (emails, IPs) encrypted at rest (if required)
  - Affiliate links sanitized (no malicious redirects)
  - SQL injection: Parameterized queries only (SQLAlchemy)
  - XSS: Output encoding in frontend (React)

- [ ] Moderation:
  - Admin actions logged and auditable
  - Moderators cannot access other moderators' data
  - No hardcoded credentials

- [ ] Third-party:
  - Email service integration secure (API keys from env)
  - Webhook signatures validated (if used)
  - Dependencies scanned for CVEs

**Acceptance Criteria**:
- [ ] Security audit report created
- [ ] No critical vulnerabilities found
- [ ] All medium vulnerabilities have mitigation plan
- [ ] Security checklist passed

---

### Testing (TEST-E2E-001, TEST-ACCESSIBILITY-001)

#### TEST-E2E-001: E2E Tests for Critical Journeys

**Objective**: Test complete user flows end-to-end

**Duration**: 2 days
**Effort**: 2 story points
**Assignee**: test-automator

**Tools**: Playwright or Cypress

**Critical Journeys**:
1. **Publish & Vote Journey:**
   - User 1 publishes deal to community catalog
   - User 2 browses catalog, finds deal
   - User 2 votes on deal
   - Vote count updates in real-time
   - Vote is visible on user profile

2. **Curator Profile Journey:**
   - User navigates to curator profile
   - Profile shows all published deals
   - Profile shows reputation score and badges
   - User can follow curator

3. **Notification Journey:**
   - User 1 follows User 2
   - User 2 publishes deal
   - User 1 receives notification
   - User 1 clicks notification link
   - Notification marked as read

4. **Collaborative Collection Journey:**
   - User 1 creates collaborative collection
   - User 1 invites User 2
   - User 2 accepts invitation
   - User 2 adds deal to collection
   - Both users see changes in real-time
   - Collection published to community catalog

5. **Moderation Journey:**
   - User reports deal
   - Admin sees flag in moderation queue
   - Admin reviews and removes deal
   - Deal disappears from catalog
   - Curator sees removal notification

**Acceptance Criteria**:
- [ ] All 5 journeys pass
- [ ] No console errors
- [ ] Performance acceptable (<5 sec per journey)
- [ ] Mobile and desktop tested

---

#### TEST-ACCESSIBILITY-001: Accessibility Audit

**Objective**: Ensure WCAG 2.1 AA compliance

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: test-automator

**Tools**: axe-core, WAVE, manual testing

**Areas**:
- [ ] All pages WCAG 2.1 AA compliant
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Screen reader support (ARIA labels, semantic HTML)
- [ ] Color contrast ratios (4.5:1 for text)
- [ ] Focus indicators visible
- [ ] Form labels associated with inputs
- [ ] Error messages clear and actionable
- [ ] Images have alt text
- [ ] Videos have captions (if applicable)

**Community Pages to Audit**:
- Catalog browse (/dashboard/community)
- Deal details
- Curator profiles (/curator/[username])
- Voting UI
- Notification preferences
- Moderation queue (admin)
- Report deal modal

**Acceptance Criteria**:
- [ ] No critical accessibility issues
- [ ] <5 medium issues (with mitigation plan)
- [ ] All interactive elements keyboard accessible
- [ ] Screen reader testing passes

---

### Documentation (DOC-API-001 through DOC-ADR-001)

#### DOC-API-001: API Documentation

**Objective**: Document all community API endpoints

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: technical-writer

**Deliverables**:
- OpenAPI/Swagger schema (generated from code or manual)
- Request/response examples for each endpoint
- Authentication requirements
- Rate limits and error codes
- Code samples (curl, JavaScript, Python)

**Coverage**:
- GET /api/v1/community-deals
- POST /api/v1/community-deals
- GET /api/v1/community-deals/:id
- POST /api/v1/votes
- DELETE /api/v1/votes/:deal_id
- GET /api/v1/curator/:username
- POST /api/v1/follows
- DELETE /api/v1/follows/:id
- GET /api/v1/notifications
- PUT /api/v1/notifications/:id
- (+ all moderation and collaborative collection endpoints)

---

#### DOC-USER-001: User Guides

**Objective**: Help users navigate community features

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: technical-writer

**Guides**:
- **How to Publish Deals to Community Catalog**
  - Step-by-step with screenshots
  - Guidelines for good titles/descriptions
  - Affiliate link disclosure

- **How to Vote & Discover Deals**
  - Browsing and filtering
  - Understanding vote counts
  - Sorting by trending/recent

- **How to Follow Curators**
  - Finding curators by reputation
  - Following and unfollowing
  - What notifications you'll receive

- **Managing Notification Preferences**
  - Enabling/disabling per curator
  - Email frequency options
  - Unsubscribing

- **Creating Collaborative Collections**
  - Inviting team members
  - Joint editing
  - Publishing as group

---

#### DOC-MOD-001: Moderation Guide

**Objective**: Train admins on moderation workflow

**Duration**: 1 day
**Effort**: 1.5 story points
**Assignee**: technical-writer

**Sections**:
- **Moderation Queue Overview**
  - Understanding flag reasons
  - Severity levels
  - SLA: <24 hour resolution

- **Reviewing Flags**
  - What to look for
  - Curator context (history of flags)
  - Deal context (related deals)

- **Taking Action**
  - Approving flags (informational)
  - Removing deals (soft delete)
  - Suspending curators (if needed)
  - Handling appeals

- **Escalation & Appeals**
  - When to escalate to team leads
  - Appeal process
  - Documentation requirements

- **Admin Tools**
  - Moderation dashboard navigation
  - Anomaly alerts
  - Metrics and reporting

---

#### DOC-ADR-001: Architecture Decision Records

**Objective**: Document key design decisions

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: technical-writer

**ADRs**:

1. **Reputation Algorithm**
   - Decision: Weight votes + follows, min 3 votes before badge
   - Rationale: Prevent gaming, early feedback
   - Alternatives considered: Weighted votes only, decay over time
   - Trade-offs: New curators harder to badge, but prevents spam

2. **Voting Mechanics**
   - Decision: UNIQUE(user_id, deal_id) constraint
   - Rationale: Simple, database-enforced deduplication
   - Alternatives: Application-level checking (slower)
   - Trade-offs: Cannot change vote type without delete+vote

3. **Moderation Workflow**
   - Decision: Soft delete (hide from catalog, keep in DB)
   - Rationale: Preserves audit trail, allows appeals
   - Alternatives: Hard delete (simpler, lose context)
   - Trade-offs: Database size grows, requires cleanup policy

4. **Anti-Abuse Approach**
   - Decision: Layered defense (rate limiting, deduplication, anomaly detection)
   - Rationale: Prevents most attacks without false positives
   - Alternatives: Single strong measure (CAPTCHA), ML-based (complex)
   - Trade-offs: Multiple components to maintain, thresholds need tuning

5. **Notification Delivery**
   - Decision: Real-time (async queue) with configurable frequency
   - Rationale: Engagement, but prevents fatigue
   - Alternatives: Batch emails only (simpler, less engagement)
   - Trade-offs: More infrastructure (task queue), need bounce handling

6. **Collaborative Collections**
   - Decision: Owner/Editor roles, invitations with tokens
   - Rationale: Simple permissions, secure invites
   - Alternatives: Granular roles (complex), open joining (spam risk)
   - Trade-offs: Future extensibility to Viewer role, Group ownership

---

### Monitoring & Deployment (MONITORING-001, MIGRATION-001, FEATURE-FLAGS-001)

#### MONITORING-001: Set Up Post-Launch Monitoring

**Objective**: Observability for community features

**Duration**: 1 day
**Effort**: 2 story points
**Assignee**: backend-architect

**Dashboards**:
- **Community Metrics:**
  - Deals published (daily, weekly)
  - Active curators (trailing 7-day count)
  - Votes per deal (avg, distribution)
  - Followers (growth curve)

- **Engagement:**
  - Catalog page views
  - Deal view distribution
  - Voting rate (% of viewers who vote)
  - Follow rate (% of profile viewers who follow)

- **Notifications:**
  - Emails sent, delivered, bounced
  - Notification open rate
  - Unsubscribe rate

- **Moderation:**
  - Flags submitted (daily)
  - Resolution time (SLA tracking)
  - Appeals (count, resolution)
  - Anomalies detected (by type, severity)

- **Performance:**
  - API latency (by endpoint)
  - Error rates
  - Rate limit hits (potential attacks)
  - Database query performance

**Alerts**:
- [ ] Rate limit hits >100 in 5 min (potential attack)
- [ ] Moderation queue backlog >50 (SLA risk)
- [ ] Notification delivery failure >5% (email service issue)
- [ ] High severity anomalies detected
- [ ] API error rate >1%
- [ ] Vote count inconsistency detected

**Logs**:
- All operations logged with trace_id, span_id, user_id
- Structured JSON logging
- Searchable in log aggregation platform

---

#### MIGRATION-001: Database Migration Runbook

**Objective**: Prepare for database schema deployment

**Duration**: 1 day
**Effort**: 1 story point
**Assignee**: data-layer-expert

**Runbook Contents**:
- Pre-migration checklist
  - Backup production database
  - Verify no long-running transactions
  - Alert timing (off-peak)
  - Rollback plan

- Migration steps
  - Run Alembic upgrade
  - Verify tables/indexes created
  - Seed initial data (if needed)
  - Verify RLS policies

- Post-migration
  - Run smoke tests
  - Verify backups taken
  - Monitor for issues

- Rollback procedure
  - Run Alembic downgrade
  - Restore from backup if needed
  - Verify data integrity

---

#### FEATURE-FLAGS-001: Enable Feature Flags

**Objective**: Gradual rollout of community features

**Duration**: 1 day
**Effort**: 1 story point
**Assignee**: backend-architect

**Feature Flags**:
```python
FEATURE_COMMUNITY_CATALOG = False  # Initially off
FEATURE_VOTING = False
FEATURE_COLLABORATIVE_COLLECTIONS = False
FEATURE_CURATOR_PROFILES = False
FEATURE_NOTIFICATIONS = False
FEATURE_MODERATION = True  # Always on (internal)
```

**Rollout Plan**:
- Week 1: Enable for 10% of users (beta testers)
- Week 2: Enable for 50% of users
- Week 3: Enable for 100% of users (full launch)

**Monitoring**:
- Track error rate by flag
- Monitor engagement metrics
- Collect user feedback

**Implementation**:
- Use feature flag service (e.g., LaunchDarkly, custom)
- Wrap all community code behind flag checks
- Cache flag values in-app

---

#### FINAL-REVIEW-001: Final Review & Sign-Off

**Objective**: Confirm readiness for launch

**Duration**: 1 day
**Effort**: 1 story point
**Assignee**: tech-lead

**Pre-Launch Checklist**:
- [ ] All Phase 3 tasks completed
- [ ] All tests passing (>80% coverage)
- [ ] Security audit passed
- [ ] Performance targets met
- [ ] Accessibility compliance verified
- [ ] Documentation complete
- [ ] Monitoring and alerts configured
- [ ] Database migrations tested
- [ ] Rollback procedures documented
- [ ] Team trained on operations
- [ ] Support team briefed
- [ ] Product/Marketing ready for announcement

**Sign-Off**:
- [ ] Engineering lead approval
- [ ] Product lead approval
- [ ] Security lead approval
- [ ] Operations lead approval

**Go/No-Go Decision**:
- If all checks pass: Proceed to launch
- If issues found: Schedule remediation, recheck

---

## Phase 3.3-3.4 Quality Gates Summary

### Before Phase 3.3 Ends
- [ ] Collaborative collections fully functional
- [ ] Moderation queue and admin UI complete
- [ ] User report mechanism working
- [ ] Affiliate link detection implemented
- [ ] Rate limiting enforced
- [ ] Anomaly detection batch job tested
- [ ] All Phase 3.3 tests passing with >85% coverage
- [ ] Load testing: 100+ concurrent users, 10+ RPS voting
- [ ] Moderation queue: <24h SLA achievable

### Before Phase 3.4 Ends (Pre-Launch)
- [ ] All performance targets met (<500ms catalog, <100ms vote)
- [ ] Security audit completed, critical issues resolved
- [ ] E2E tests passing for all 5 critical journeys
- [ ] Accessibility audit: WCAG 2.1 AA compliant
- [ ] API documentation complete with examples
- [ ] User guides, moderation guide, ADRs published
- [ ] Monitoring dashboards active
- [ ] Database migration runbook created and tested
- [ ] Feature flags working correctly
- [ ] Team trained and ready
- [ ] No blocking issues remaining

### Pre-Launch Security & Performance Requirements
- [ ] Vote count integrity: 100% accuracy under load
- [ ] Rate limiting: Blocks bots, allows legitimate users
- [ ] RLS policies: Enforced on all queries
- [ ] Affiliate detection: <2% false positive rate
- [ ] Notification delivery: 95%+ success rate, <5 min SLA
- [ ] Moderation response: <24h average
- [ ] Zero data loss scenarios

---

## Overall Implementation Summary

**Total Effort**: 85-95 story points over 12 weeks
**Team Size**: 10-12 people (roles distributed across phases)
**Key Milestones**:
- Week 4: Phase 3.1 complete (catalog + voting)
- Week 7: Phase 3.2 complete (reputation + notifications)
- Week 10: Phase 3.3 complete (collaboration + moderation)
- Week 12: Phase 3.4 complete (launch ready)

**Critical Success Factors**:
1. Phase 1 & 2 completion before Phase 3.1 starts
2. Strong moderation framework (anti-abuse, spam prevention)
3. Performance optimization throughout (not at end)
4. Security audit early (not just Week 11)
5. Team communication and code reviews weekly
6. Feature flags for safe rollout

**Expected Launch**: End of Week 12 (Mid-Q1 2026)

For master implementation plan and orchestration strategy, see: `/docs/project_plans/implementation_plans/features/community-social-features-v1.md`
