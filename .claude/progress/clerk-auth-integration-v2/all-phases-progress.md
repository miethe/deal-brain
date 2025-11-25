---
type: progress
prd: "clerk-auth-integration-v2"
status: not_started
progress: 0
total_effort: 38
completed_effort: 0
in_progress_effort: 0
blocked_effort: 0
total_tasks: 29
completed_tasks: 0
in_progress_tasks: 0
blocked_tasks: 0
created: 2025-11-25
updated: 2025-11-25
owners: ["python-backend-engineer", "ui-engineer-enhanced"]
contributors: ["data-layer-expert", "documentation-writer", "backend-architect", "frontend-developer"]
next_phase: 1
current_phase: null
blockers: []
---

# Clerk Authentication Integration v2 - All Phases Progress

**Project**: Deal Brain Clerk-Backed User Authentication & Authorization
**Status**: NOT STARTED (0% complete, 0/38 story points)
**Last Updated**: 2025-11-25
**Primary Owners**: python-backend-engineer, ui-engineer-enhanced
**Supporting Subagents**: data-layer-expert, documentation-writer, backend-architect, frontend-developer

## Quick Links

- **PRD**: `/docs/project_plans/clerk_user_integration/clerk-auth-integration-prd-v2.md`
- **Implementation Plan**: `/docs/project_plans/clerk_user_integration/clerk-auth-integration-implementation-plan-v2.md`

---

## Overview

Comprehensive phased implementation of Clerk authentication with OAuth (Google, GitHub), email/password auth, row-level security (RLS), user profiles, and admin controls. 6 phases, 29 tasks, 38 story points total effort.

### Phase Summary

| Phase | Title | Effort | Status | Tasks | Primary Owner | Secondary |
|-------|-------|--------|--------|-------|---------------|-----------|
| 1 | Database & User Model | 6 pts | 🕐 NOT STARTED | 5 | data-layer-expert | — |
| 2 | Backend Auth Dependencies | 8 pts | 🕐 NOT STARTED | 6 | python-backend-engineer | backend-architect |
| 3 | Clerk Webhooks & Sync | 5 pts | 🕐 NOT STARTED | 5 | python-backend-engineer | — |
| 4 | Row-Level Security | 8 pts | 🕐 NOT STARTED | 4 | data-layer-expert | python-backend-engineer |
| 5 | Frontend Integration | 7 pts | 🕐 NOT STARTED | 7 | ui-engineer-enhanced | frontend-developer |
| 6 | Admin, Testing & Docs | 4 pts | 🕐 NOT STARTED | 5 | documentation-writer | python-backend-engineer |

**Progress**: 0% (0 of 38 story points) | **Next**: Phase 1

---

## Phase 1: Database & User Model

**Duration**: Estimated 2-3 days
**Assigned Subagent(s)**: data-layer-expert
**Status**: NOT STARTED
**Effort**: 6 story points

### Task Breakdown

| ID | Task | Effort | Status | Subagent(s) | Notes | Key Files |
|----|------|--------|--------|------------|-------|-----------|
| TASK-1.1 | Extend User Model | 2 pts | 🕐 Pending | data-layer-expert | Add clerk_id (unique), role, preferences (JSONB), avatar_url, first_name, last_name, is_active | `apps/api/dealbrain_api/models/sharing.py` |
| TASK-1.2 | Create User Migration | 1 pt | 🕐 Pending | data-layer-expert | Alembic migration 0031_extend_user_model_clerk_auth | `apps/api/alembic/versions/0031_*.py` |
| TASK-1.3 | Add user_id to Listing | 1 pt | 🕐 Pending | data-layer-expert | Add nullable user_id FK, update model | `apps/api/dealbrain_api/models/listings.py` |
| TASK-1.4 | Add user_id to Profile | 1 pt | 🕐 Pending | data-layer-expert | Add nullable user_id FK to profile table | `apps/api/dealbrain_api/models/listings.py` |
| TASK-1.5 | Add user_id to ValuationRuleset | 1 pt | 🕐 Pending | data-layer-expert | Add nullable user_id FK to valuation_ruleset table | `apps/api/alembic/versions/0032_*.py` |

### Success Criteria

- [ ] All migrations run successfully (forward and rollback)
- [ ] User model has clerk_id unique constraint and index
- [ ] Foreign keys cascade properly on user deletion
- [ ] Existing data remains accessible (nullable FKs)

---

## Phase 2: Backend Auth Dependencies

**Duration**: Estimated 3-4 days
**Assigned Subagent(s)**: python-backend-engineer (primary), backend-architect (support)
**Status**: NOT STARTED
**Effort**: 8 story points

### Task Breakdown

| ID | Task | Effort | Status | Subagent(s) | Notes | Key Files |
|----|------|--------|--------|------------|-------|-----------|
| TASK-2.1 | Create Auth Module | 2 pts | 🕐 Pending | python-backend-engineer, backend-architect | JWT verification, JWKS caching, CSRF via authorizedParties | `apps/api/dealbrain_api/core/auth.py` |
| TASK-2.2 | Auth Dependencies | 2 pts | 🕐 Pending | python-backend-engineer | get_current_user() and require_admin() | `apps/api/dealbrain_api/dependencies/auth.py` |
| TASK-2.3 | Update Collections API | 1 pt | 🕐 Pending | python-backend-engineer | Replace placeholder, use real auth | `apps/api/dealbrain_api/api/collections.py:64` |
| TASK-2.4 | Update Shares API | 1 pt | 🕐 Pending | python-backend-engineer | Replace placeholder in shares/user_shares | `apps/api/dealbrain_api/api/shares.py`, `user_shares.py` |
| TASK-2.5 | Protect All Routes | 1 pt | 🕐 Pending | python-backend-engineer | Add auth dependency to all routers | `apps/api/dealbrain_api/api/*.py` |
| TASK-2.6 | Auth Integration Tests | 1 pt | 🕐 Pending | python-backend-engineer | Test valid/invalid JWT, admin routes (90%+ coverage) | `tests/api/test_auth.py` |

### Success Criteria

- [ ] Valid Clerk JWT returns authenticated user context
- [ ] Invalid/expired JWT returns 401 Unauthorized
- [ ] Missing Authorization header returns 401
- [ ] Admin routes verify role and return 403 for non-admin
- [ ] JIT user provisioning works on first request
- [ ] Tests cover all auth scenarios (90%+ coverage)

---

## Phase 3: Clerk Webhooks & Sync

**Duration**: Estimated 2-3 days
**Assigned Subagent(s)**: python-backend-engineer
**Status**: NOT STARTED
**Effort**: 5 story points

### Task Breakdown

| ID | Task | Effort | Status | Subagent(s) | Notes | Key Files |
|----|------|--------|--------|------------|-------|-----------|
| TASK-3.1 | Webhook Endpoint | 1 pt | 🕐 Pending | python-backend-engineer | Create POST /api/webhooks/clerk | `apps/api/dealbrain_api/api/webhooks.py` |
| TASK-3.2 | Signature Validation | 1 pt | 🕐 Pending | python-backend-engineer | Verify signatures using svix.webhooks | `apps/api/dealbrain_api/api/webhooks.py` |
| TASK-3.3 | User Created Handler | 1 pt | 🕐 Pending | python-backend-engineer | Handle user.created event | `apps/api/dealbrain_api/services/user_sync_service.py` |
| TASK-3.4 | User Updated Handler | 1 pt | 🕐 Pending | python-backend-engineer | Handle user.updated event | `apps/api/dealbrain_api/services/user_sync_service.py` |
| TASK-3.5 | User Deleted Handler | 1 pt | 🕐 Pending | python-backend-engineer | Handle user.deleted event (soft delete) | `apps/api/dealbrain_api/services/user_sync_service.py` |

### Success Criteria

- [ ] Webhook signature validation works with CLERK_WEBHOOK_SECRET
- [ ] Duplicate events handled idempotently
- [ ] User sync data matches Clerk after processing
- [ ] Audit log captures user lifecycle events
- [ ] Tests simulate all webhook payloads with proper signatures

---

## Phase 4: Row-Level Security

**Duration**: Estimated 3-4 days
**Assigned Subagent(s)**: data-layer-expert (primary), python-backend-engineer (support)
**Status**: NOT STARTED
**Effort**: 8 story points

### Task Breakdown

| ID | Task | Effort | Status | Subagent(s) | Notes | Key Files |
|----|------|--------|--------|------------|-------|-----------|
| TASK-4.1 | Enable RLS Migration | 2 pts | 🕐 Pending | data-layer-expert | Enable RLS on listing, profile, valuation_ruleset | `apps/api/alembic/versions/0033_*.py` |
| TASK-4.2 | Create RLS Policies | 2 pts | 🕐 Pending | data-layer-expert | User owns rows, admin bypasses RLS | `apps/api/alembic/versions/0034_*.py` |
| TASK-4.3 | Session User Context | 2 pts | 🕐 Pending | python-backend-engineer | Set app.current_user_id and app.current_user_role | `apps/api/dealbrain_api/db.py` |
| TASK-4.4 | RLS Integration Tests | 2 pts | 🕐 Pending | python-backend-engineer | Cross-user isolation, admin query, performance <10ms | `tests/api/test_rls.py` |

### Success Criteria

- [ ] User A cannot query User B's listings via RLS
- [ ] Admin users can query all data (RLS bypass)
- [ ] RLS policies don't break existing queries
- [ ] Query performance impact < 10ms per request
- [ ] Tests confirm isolation across all protected tables

---

## Phase 5: Frontend Integration

**Duration**: Estimated 4-5 days
**Assigned Subagent(s)**: ui-engineer-enhanced (primary), frontend-developer (support)
**Status**: NOT STARTED
**Effort**: 7 story points

### Task Breakdown

| ID | Task | Effort | Status | Subagent(s) | Notes | Key Files |
|----|------|--------|--------|------------|-------|-----------|
| TASK-5.1 | Install Clerk SDK | 1 pt | 🕐 Pending | frontend-developer | Add @clerk/nextjs@6.35.4, @clerk/testing | `apps/web/package.json`, `.env.local` |
| TASK-5.2 | Add ClerkProvider | 1 pt | 🕐 Pending | frontend-developer | Wrap root layout with ClerkProvider | `apps/web/app/layout.tsx` |
| TASK-5.3 | Create Middleware | 1 pt | 🕐 Pending | frontend-developer | Route protection via authMiddleware() | `apps/web/middleware.ts` |
| TASK-5.4 | Update API Client | 1 pt | 🕐 Pending | frontend-developer | Inject auth token via useAuth hook | `apps/web/lib/utils.ts`, `lib/api-client.ts` |
| TASK-5.5 | Login/Signup Pages | 1 pt | 🕐 Pending | ui-engineer-enhanced | /sign-in and /sign-up routes with OAuth | `apps/web/app/(auth)/sign-in/`, `sign-up/` |
| TASK-5.6 | User Menu | 1 pt | 🕐 Pending | ui-engineer-enhanced | Header menu with avatar, name, sign-out | `apps/web/components/user-menu.tsx` |
| TASK-5.7 | Settings Page | 1 pt | 🕐 Pending | ui-engineer-enhanced | Profile & preferences UI | `apps/web/app/(authenticated)/settings/page.tsx` |

### Success Criteria

- [ ] ClerkProvider wraps entire app tree
- [ ] Unauthenticated users redirected to /sign-in
- [ ] API calls include valid JWT token
- [ ] User menu displays correct avatar and name
- [ ] Sign-out clears session and redirects to login
- [ ] Auth state persists across page refreshes

---

## Phase 6: Admin, Testing & Documentation

**Duration**: Estimated 2-3 days
**Assigned Subagent(s)**: documentation-writer (primary), python-backend-engineer (support)
**Status**: NOT STARTED
**Effort**: 4 story points

### Task Breakdown

| ID | Task | Effort | Status | Subagent(s) | Notes | Key Files |
|----|------|--------|--------|------------|-------|-----------|
| TASK-6.1 | Admin API Routes | 1 pt | 🕐 Pending | python-backend-engineer | GET /admin/users, PATCH /admin/users/:id/role | `apps/api/dealbrain_api/api/admin.py` |
| TASK-6.2 | E2E Auth Tests | 1 pt | 🕐 Pending | frontend-developer | Playwright tests (sign-in, sign-up, sign-out) | `apps/web/e2e/auth.spec.ts` |
| TASK-6.3 | Developer Setup Guide | 1 pt | 🕐 Pending | documentation-writer | Clerk sandbox setup, env vars, webhook testing | `docs/development/clerk-setup.md` |
| TASK-6.4 | Update .env.example | 0.5 pt | 🕐 Pending | documentation-writer | Add all CLERK_* and NEXT_PUBLIC_CLERK_* vars | `apps/api/.env.example`, `apps/web/.env.example` |
| TASK-6.5 | Auth Architecture ADR | 0.5 pt | 🕐 Pending | documentation-writer | Document auth flow, RLS, token handling | `docs/architecture/ADRs/adr-clerk-authentication.md` |

### Success Criteria

- [ ] Admin can view all users in system
- [ ] Admin can modify user roles and changes persist
- [ ] E2E tests pass for all auth flows
- [ ] Developer guide covers Clerk sandbox setup
- [ ] CI pipeline has Clerk test secrets configured

---

## Architecture Context

### Authentication Flow

1. **Frontend**: User signs in via Clerk UI (Google/GitHub/email)
2. **Clerk**: Issues JWT token with user claims (sub=clerk_id, email, name, etc)
3. **Frontend**: Injects JWT in Authorization header via useAuth() hook
4. **Backend**: Validates JWT using Clerk JWKS endpoint (cached)
5. **Backend**: Creates/updates User record (JIT provisioning)
6. **Backend**: Sets session context (current_user_id) for RLS
7. **Database**: RLS policies enforce user_id ownership

### RLS Architecture

- **Policy Type**: USING clause checks `user_id = NULLIF(current_setting('app.current_user_id')::int)`
- **Admin Bypass**: Separate policy checks `current_setting('app.current_user_role') = 'admin'`
- **Session Context**: FastAPI dependency sets LOCAL variables before query
- **Legacy Data**: Nullable user_id allows existing data accessible during transition

### Token Verification

- **JWKS Caching**: PyJWKClient caches for 1 hour (Clerk SDK default)
- **CSRF Protection**: Verify azp claim matches authorized frontend domain
- **Token Expiry**: Clerk tokens expire, frontend handles refresh automatically
- **Custom Claims**: Keep under 1.2KB to avoid cookie size limits

---

## Dependencies & Blockers

### Hard Dependencies

| Dependency | Phase | Impact | Resolution |
|------------|-------|--------|-----------|
| Clerk account setup | Phase 2 | Cannot test JWT validation | Request sandbox early |
| Clerk webhook secret | Phase 3 | Cannot test webhooks | Available after setup |
| NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY | Phase 5 | Cannot configure ClerkProvider | From Clerk dashboard |

### Phase Dependencies

- Phase 1 → Phase 2 (User model required for auth)
- Phase 2 → Phase 4 (Auth context required for RLS)
- Phases 2-3 ∥ Phase 5 (Can work in parallel)

### Current Blockers

_None - ready to start Phase 1_

---

## Quality Gates & Metrics

### Per-Phase Gates

| Phase | Quality Gate | Validation |
|-------|-------------|-----------|
| 1 | All migrations run forward/backward | Test suite passes |
| 2 | 90%+ auth code coverage | pytest coverage report |
| 3 | Webhook signature validation enforced | Reject invalid signatures |
| 4 | RLS isolation verified for 2+ users | No cross-user data access |
| 5 | Middleware protects routes, token injection works | E2E tests pass |
| 6 | E2E tests pass, docs accurate | CI pipeline green |

### Success Metrics

**Delivery**: 29/29 tasks, 38/38 story points
**Functional**: 100% auth on APIs, OAuth works, Settings CRUD works
**Technical**: <300ms p95 token verification, <10ms RLS overhead, 90%+ test coverage
**Business**: Ready for SaaS deployment, audit trail available

---

## Changelog

| Date | Milestone | Status |
|------|-----------|--------|
| 2025-11-25 | Initial all-phases tracking created | ✓ Complete |
| TBD | Phase 1 Complete | Pending |
| TBD | Phase 2 Complete | Pending |
| TBD | Phase 3 Complete | Pending |
| TBD | Phase 4 Complete | Pending |
| TBD | Phase 5 Complete | Pending |
| TBD | Phase 6 Complete | Pending |
