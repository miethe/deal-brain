# All-Phases Progress: Clerk Authentication Integration v2

**Status**: NOT STARTED
**Last Updated**: 2025-11-25
**Completion**: 0% (0 of 38 story points)

## Phase Overview

| Phase | Title | Effort | Status | Completion |
|-------|-------|--------|--------|-----------|
| 1 | Database & User Model | 6 pts | NOT STARTED | 0% |
| 2 | Backend Auth Dependencies | 8 pts | NOT STARTED | 0% |
| 3 | Clerk Webhooks & Sync | 5 pts | NOT STARTED | 0% |
| 4 | Row-Level Security | 8 pts | NOT STARTED | 0% |
| 5 | Frontend Integration | 7 pts | NOT STARTED | 0% |
| 6 | Admin, Testing & Docs | 4 pts | NOT STARTED | 0% |

## Links

- **PRD**: `/docs/project_plans/clerk_user_integration/clerk-auth-integration-prd-v2.md`
- **Implementation Plan**: `/docs/project_plans/clerk_user_integration/clerk-auth-integration-implementation-plan-v2.md`

---

## Phase 1: Database & User Model

**Assigned Subagent(s)**: data-layer-expert
**Status**: NOT STARTED
**Effort**: 6 pts

### Completion Checklist

- [ ] DB-001: Extend User Model (2 pts)
      Add clerk_id, role, preferences, avatar_url, is_active to User model
      Assigned Subagent(s): data-layer-expert
      Files: `apps/api/dealbrain_api/models/sharing.py`

- [ ] DB-002: Create Migration for User Model (1 pt)
      Alembic migration for User model changes
      Assigned Subagent(s): data-layer-expert
      Files: `apps/api/alembic/versions/0031_extend_user_model_clerk_auth.py`

- [ ] DB-003: Add user_id to Listing (1 pt)
      Add nullable user_id FK to listing table
      Assigned Subagent(s): data-layer-expert
      Files: `apps/api/dealbrain_api/models/listings.py`, `apps/api/alembic/versions/0032_add_user_id_to_listings.py`

- [ ] DB-004: Add user_id to Profile (1 pt)
      Add nullable user_id FK to profile table
      Assigned Subagent(s): data-layer-expert
      Files: `apps/api/dealbrain_api/models/listings.py`

- [ ] DB-005: Add user_id to ValuationRuleset (1 pt)
      Add nullable user_id FK to valuation_ruleset table
      Assigned Subagent(s): data-layer-expert

### Success Criteria

- [ ] All migrations run successfully (forward and rollback)
- [ ] User model has clerk_id unique constraint
- [ ] Foreign keys cascade properly on user deletion
- [ ] Existing data remains accessible (nullable FKs)

---

## Phase 2: Backend Auth Dependencies

**Assigned Subagent(s)**: python-backend-engineer, backend-architect
**Status**: NOT STARTED
**Effort**: 8 pts

### Completion Checklist

- [ ] AUTH-001: Create Auth Module (2 pts)
      Create `apps/api/dealbrain_api/core/auth.py` with Clerk JWT verification
      Assigned Subagent(s): python-backend-engineer, backend-architect
      Files: `apps/api/dealbrain_api/core/auth.py`

- [ ] AUTH-002: Auth Dependencies (2 pts)
      Create `get_current_user()` and `require_admin()` dependencies
      Assigned Subagent(s): python-backend-engineer
      Files: `apps/api/dealbrain_api/dependencies/auth.py`

- [ ] AUTH-003: Update Collections API (1 pt)
      Replace placeholder auth in collections.py
      Assigned Subagent(s): python-backend-engineer
      Files: `apps/api/dealbrain_api/api/collections.py`

- [ ] AUTH-004: Update Shares API (1 pt)
      Replace placeholder auth in shares.py, user_shares.py
      Assigned Subagent(s): python-backend-engineer
      Files: `apps/api/dealbrain_api/api/shares.py`, `apps/api/dealbrain_api/api/user_shares.py`

- [ ] AUTH-005: Protect All Routes (1 pt)
      Add auth dependency to all API routers
      Assigned Subagent(s): python-backend-engineer
      Files: `apps/api/dealbrain_api/api/*.py`

- [ ] AUTH-006: Auth Tests (1 pt)
      Integration tests for auth success/failure
      Assigned Subagent(s): python-backend-engineer
      Files: `tests/api/test_auth.py`

### Success Criteria

- [ ] Valid Clerk JWT returns user context
- [ ] Invalid/expired JWT returns 401
- [ ] Missing token returns 401
- [ ] Admin routes check role
- [ ] Tests cover all auth scenarios

---

## Phase 3: Clerk Webhooks & Sync

**Assigned Subagent(s)**: python-backend-engineer
**Status**: NOT STARTED
**Effort**: 5 pts

### Completion Checklist

- [ ] WH-001: Webhook Endpoint (1 pt)
      Create POST /api/webhooks/clerk endpoint
      Assigned Subagent(s): python-backend-engineer
      Files: `apps/api/dealbrain_api/api/webhooks.py`

- [ ] WH-002: Signature Validation (1 pt)
      Verify Clerk webhook signatures
      Assigned Subagent(s): python-backend-engineer

- [ ] WH-003: User Created Handler (1 pt)
      Handle user.created event
      Assigned Subagent(s): python-backend-engineer
      Files: `apps/api/dealbrain_api/services/user_sync_service.py`

- [ ] WH-004: User Updated Handler (1 pt)
      Handle user.updated event
      Assigned Subagent(s): python-backend-engineer

- [ ] WH-005: User Deleted Handler (1 pt)
      Handle user.deleted event (soft delete)
      Assigned Subagent(s): python-backend-engineer

### Success Criteria

- [ ] Webhook signature validation works
- [ ] Duplicate events handled idempotently
- [ ] User sync matches Clerk data
- [ ] Audit log captures webhook events
- [ ] Tests simulate all webhook payloads

---

## Phase 4: Row-Level Security

**Assigned Subagent(s)**: data-layer-expert, python-backend-engineer
**Status**: NOT STARTED
**Effort**: 8 pts

### Completion Checklist

- [ ] RLS-001: Enable RLS Migration (2 pts)
      Create migration enabling RLS on listing, profile, valuation_ruleset
      Assigned Subagent(s): data-layer-expert
      Files: `apps/api/alembic/versions/0033_enable_rls_listing.py`

- [ ] RLS-002: Create RLS Policies (2 pts)
      Define policies: user owns rows, admin bypasses
      Assigned Subagent(s): data-layer-expert
      Files: `apps/api/alembic/versions/0034_enable_rls_profile_ruleset.py`

- [ ] RLS-003: Session User Context (2 pts)
      Set `app.current_user_id` on session start
      Assigned Subagent(s): python-backend-engineer
      Files: `apps/api/dealbrain_api/db.py`

- [ ] RLS-004: RLS Integration Tests (2 pts)
      Test cross-user data isolation
      Assigned Subagent(s): python-backend-engineer
      Files: `tests/api/test_rls.py`

### Success Criteria

- [ ] User A cannot query User B's listings
- [ ] Admin can query all data
- [ ] RLS policies don't break existing queries
- [ ] Performance impact < 10ms per query
- [ ] Tests confirm isolation for all protected tables

---

## Phase 5: Frontend Integration

**Assigned Subagent(s)**: ui-engineer-enhanced, frontend-developer
**Status**: NOT STARTED
**Effort**: 7 pts

### Completion Checklist

- [ ] FE-001: Install Clerk SDK (1 pt)
      Add @clerk/nextjs, configure environment
      Assigned Subagent(s): frontend-developer
      Files: `apps/web/package.json`, `apps/web/.env.local`

- [ ] FE-002: Add ClerkProvider (1 pt)
      Wrap app in ClerkProvider
      Assigned Subagent(s): frontend-developer
      Files: `apps/web/app/layout.tsx`

- [ ] FE-003: Create Middleware (1 pt)
      Route protection in middleware.ts
      Assigned Subagent(s): frontend-developer
      Files: `apps/web/middleware.ts`

- [ ] FE-004: Update API Client (1 pt)
      Inject auth token in apiFetch
      Assigned Subagent(s): frontend-developer
      Files: `apps/web/lib/utils.ts`, `apps/web/lib/api-client.ts`

- [ ] FE-005: Login/Signup Pages (1 pt)
      Create /sign-in and /sign-up routes
      Assigned Subagent(s): ui-engineer-enhanced
      Files: `apps/web/app/(auth)/sign-in/[[...sign-in]]/page.tsx`, `apps/web/app/(auth)/sign-up/[[...sign-up]]/page.tsx`

- [ ] FE-006: User Menu (1 pt)
      Add user menu to AppShell header
      Assigned Subagent(s): ui-engineer-enhanced
      Files: `apps/web/components/user-menu.tsx`, `apps/web/components/app-shell.tsx`

- [ ] FE-007: Settings Page (1 pt)
      User profile and preferences
      Assigned Subagent(s): ui-engineer-enhanced
      Files: `apps/web/app/(authenticated)/settings/page.tsx`

### Success Criteria

- [ ] ClerkProvider wraps entire app
- [ ] Unauthenticated users redirected to /sign-in
- [ ] API calls include valid JWT
- [ ] User menu shows correct user info
- [ ] Sign-out clears session

---

## Phase 6: Admin, Testing & Documentation

**Assigned Subagent(s)**: documentation-writer, python-backend-engineer
**Status**: NOT STARTED
**Effort**: 4 pts

### Completion Checklist

- [ ] ADMIN-001: Admin API Routes (1 pt)
      GET /admin/users, PATCH /admin/users/:id/role
      Assigned Subagent(s): python-backend-engineer
      Files: `apps/api/dealbrain_api/api/admin.py`

- [ ] TEST-001: E2E Auth Tests (1 pt)
      Playwright tests for auth flows
      Assigned Subagent(s): frontend-developer
      Files: `apps/web/e2e/auth.spec.ts`

- [ ] DOC-001: Developer Setup Guide (1 pt)
      Document Clerk setup, env vars, local dev
      Assigned Subagent(s): documentation-writer
      Files: `docs/development/clerk-setup.md`

- [ ] DOC-002: Update .env.example (0.5 pt)
      Add all Clerk environment variables
      Assigned Subagent(s): documentation-writer
      Files: `apps/api/.env.example`, `apps/web/.env.example`

- [ ] DOC-003: Auth Architecture Doc (0.5 pt)
      Document auth flow and RLS
      Assigned Subagent(s): documentation-writer
      Files: `docs/architecture/ADRs/adr-clerk-authentication.md`

### Success Criteria

- [ ] Admin can view all users
- [ ] Admin can change user roles
- [ ] E2E tests pass for sign-in, sign-up, sign-out
- [ ] Documentation covers all setup steps
- [ ] CI pipeline supports auth testing

---

## Notes & Blockers

### Notes

- Using Clerk SDK v6.35.x with async auth() pattern
- RLS uses PostgreSQL `SET LOCAL` for session user context
- JIT provisioning creates users on first API request
- Webhooks provide eventual consistency for user data

### Blockers

_None currently_

### Dependencies

- Clerk account setup required before Phase 2
- Clerk webhook secret required before Phase 3
- Frontend depends on backend auth (Phases 2-3) before Phase 5

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-25 | Initial progress tracking created | Claude Code |
