---
title: "Clerk Authentication Integration - Implementation Plan v2"
description: "Phased implementation plan for Clerk authentication with RLS, user profiles, and admin controls in Deal Brain."
audience: [ai-agents, developers]
tags: [implementation, clerk, authentication, rls, fastapi, nextjs]
created: 2025-11-25
updated: 2025-11-25
category: "product-planning"
status: draft
related:
  - /docs/project_plans/clerk_user_integration/clerk-auth-integration-prd-v2.md
  - /docs/project_plans/clerk_user_integration/product_requirements_document.md
---

# Clerk Authentication Integration - Implementation Plan v2

**Feature**: Clerk-Backed User Authentication & Authorization
**Version**: 2.0
**Date**: 2025-11-25
**Estimated Effort**: 38 story points across 6 phases

## Executive Summary

This implementation plan details the phased approach to integrating Clerk authentication into Deal Brain. The plan follows the MP layered architecture (routers → services → repositories → DB) and assigns tasks to appropriate subagents.

### Milestones

| Milestone | Phase | Key Deliverable |
|-----------|-------|-----------------|
| M1 | Phase 1 | User model with Clerk ID, database schema |
| M2 | Phase 2 | Backend JWT validation, auth dependencies |
| M3 | Phase 3 | Clerk webhooks, user sync |
| M4 | Phase 4 | RLS implementation for all tables |
| M5 | Phase 5 | Frontend auth integration |
| M6 | Phase 6 | Admin UI, testing, documentation |

### Phase Overview

| Phase | Title | Effort | Subagents |
|-------|-------|--------|-----------|
| 1 | Database & User Model | 6 pts | data-layer-expert |
| 2 | Backend Auth Dependencies | 8 pts | python-backend-engineer, backend-architect |
| 3 | Clerk Webhooks & Sync | 5 pts | python-backend-engineer |
| 4 | Row-Level Security | 8 pts | data-layer-expert, python-backend-engineer |
| 5 | Frontend Integration | 7 pts | ui-engineer-enhanced, frontend-developer |
| 6 | Admin, Testing & Docs | 4 pts | documentation-writer, python-backend-engineer |

---

## Phase 1: Database & User Model

**Effort**: 6 story points
**Assigned Subagent(s)**: data-layer-expert

### Objectives

- Extend existing User model with Clerk integration fields
- Create database migration for schema changes
- Establish foundation for user-owned data

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate |
|----|------|-------------|---------------------|----------|
| DB-001 | Extend User Model | Add clerk_id, role, preferences, avatar_url, is_active to User model | Model compiles, relationships intact | 2 pts |
| DB-002 | Create Migration | Alembic migration for User model changes | Migration runs forward/backward | 1 pt |
| DB-003 | Add user_id to Listing | Add nullable user_id FK to listing table | FK constraint created | 1 pt |
| DB-004 | Add user_id to Profile | Add nullable user_id FK to profile table | FK constraint created | 1 pt |
| DB-005 | Add user_id to ValuationRuleset | Add nullable user_id FK to valuation_ruleset table | FK constraint created | 1 pt |

### Quality Gates

- [ ] All migrations run successfully (forward and rollback)
- [ ] User model has clerk_id unique constraint
- [ ] Foreign keys cascade properly on user deletion
- [ ] Existing data remains accessible (nullable FKs)

### Key Files

**Modify**:
- `apps/api/dealbrain_api/models/sharing.py` - User model
- `apps/api/dealbrain_api/models/listings.py` - Listing model

**Create**:
- `apps/api/alembic/versions/0031_extend_user_model_clerk_auth.py`
- `apps/api/alembic/versions/0032_add_user_id_to_listings.py`

### Implementation Notes

**User Model Extension**:
```python
# apps/api/dealbrain_api/models/sharing.py

class User(Base, TimestampMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clerk_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True, nullable=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Existing relationships...
```

---

## Phase 2: Backend Auth Dependencies

**Effort**: 8 story points
**Assigned Subagent(s)**: python-backend-engineer, backend-architect

### Objectives

- Implement Clerk JWT verification
- Create auth dependency for route protection
- Replace placeholder `get_current_user()`

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate |
|----|------|-------------|---------------------|----------|
| AUTH-001 | Create Auth Module | Create `apps/api/dealbrain_api/core/auth.py` with Clerk JWT verification | JWT validation works with test token | 2 pts |
| AUTH-002 | Auth Dependencies | Create `get_current_user()` and `require_admin()` dependencies | Dependencies inject user context | 2 pts |
| AUTH-003 | Update Collections API | Replace placeholder auth in collections.py | Collections protected by real auth | 1 pt |
| AUTH-004 | Update Shares API | Replace placeholder auth in shares.py, user_shares.py | Shares protected by real auth | 1 pt |
| AUTH-005 | Protect All Routes | Add auth dependency to all API routers | All routes require auth | 1 pt |
| AUTH-006 | Auth Tests | Integration tests for auth success/failure | 90%+ coverage on auth code | 1 pt |

### Quality Gates

- [ ] Valid Clerk JWT returns user context
- [ ] Invalid/expired JWT returns 401
- [ ] Missing token returns 401
- [ ] Admin routes check role
- [ ] Tests cover all auth scenarios

### Key Files

**Create**:
- `apps/api/dealbrain_api/core/auth.py` - Clerk JWT verification
- `apps/api/dealbrain_api/dependencies/auth.py` - Auth dependencies
- `tests/api/test_auth.py` - Auth integration tests

**Modify**:
- `apps/api/dealbrain_api/api/collections.py` - Replace placeholder
- `apps/api/dealbrain_api/api/shares.py` - Replace placeholder
- `apps/api/dealbrain_api/api/user_shares.py` - Replace placeholder
- `apps/api/dealbrain_api/api/listings.py` - Add auth dependency
- `apps/api/dealbrain_api/api/profiles.py` - Add auth dependency

### Implementation Notes

**Clerk JWT Verification**:
```python
# apps/api/dealbrain_api/core/auth.py

from functools import lru_cache
import httpx
import jwt
from jwt import PyJWKClient

class ClerkAuth:
    def __init__(self, jwks_url: str, authorized_parties: list[str]):
        self.jwk_client = PyJWKClient(jwks_url, cache_jwk_set=True)
        self.authorized_parties = authorized_parties

    def verify_token(self, token: str) -> dict:
        """Verify Clerk JWT and return claims."""
        signing_key = self.jwk_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk doesn't use aud
        )
        # Verify azp (authorized party) for CSRF protection
        if claims.get("azp") not in self.authorized_parties:
            raise jwt.InvalidTokenError("Invalid authorized party")
        return claims

@lru_cache()
def get_clerk_auth() -> ClerkAuth:
    return ClerkAuth(
        jwks_url=settings.CLERK_JWKS_URL,
        authorized_parties=[settings.FRONTEND_URL]
    )
```

**Auth Dependency**:
```python
# apps/api/dealbrain_api/dependencies/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(session_dependency),
) -> User:
    """Get authenticated user from Clerk JWT."""
    clerk_auth = get_clerk_auth()
    try:
        claims = clerk_auth.verify_token(credentials.credentials)
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))

    clerk_id = claims["sub"]
    user = await session.scalar(
        select(User).where(User.clerk_id == clerk_id)
    )

    if not user:
        # JIT provisioning - create user on first request
        user = User(
            clerk_id=clerk_id,
            email=claims.get("email"),
            username=claims.get("username", clerk_id[:8]),
            first_name=claims.get("first_name"),
            last_name=claims.get("last_name"),
            avatar_url=claims.get("image_url"),
        )
        session.add(user)
        await session.flush()

    return user

CurrentUserDep = Annotated[User, Depends(get_current_user)]
```

---

## Phase 3: Clerk Webhooks & Sync

**Effort**: 5 story points
**Assigned Subagent(s)**: python-backend-engineer

### Objectives

- Implement webhook endpoint for Clerk events
- Handle user lifecycle (create, update, delete)
- Ensure idempotent webhook processing

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate |
|----|------|-------------|---------------------|----------|
| WH-001 | Webhook Endpoint | Create POST /api/webhooks/clerk endpoint | Endpoint receives events | 1 pt |
| WH-002 | Signature Validation | Verify Clerk webhook signatures | Invalid signatures rejected | 1 pt |
| WH-003 | User Created Handler | Handle user.created event | User upserted in database | 1 pt |
| WH-004 | User Updated Handler | Handle user.updated event | User fields updated | 1 pt |
| WH-005 | User Deleted Handler | Handle user.deleted event | User soft-deleted | 1 pt |

### Quality Gates

- [ ] Webhook signature validation works
- [ ] Duplicate events handled idempotently
- [ ] User sync matches Clerk data
- [ ] Audit log captures webhook events
- [ ] Tests simulate all webhook payloads

### Key Files

**Create**:
- `apps/api/dealbrain_api/api/webhooks.py` - Webhook router
- `apps/api/dealbrain_api/services/user_sync_service.py` - User sync logic
- `tests/api/test_webhooks.py` - Webhook tests

**Modify**:
- `apps/api/dealbrain_api/app.py` - Register webhook router
- `apps/api/dealbrain_api/core/config.py` - Add CLERK_WEBHOOK_SECRET

### Implementation Notes

**Webhook Handler**:
```python
# apps/api/dealbrain_api/api/webhooks.py

from svix.webhooks import Webhook, WebhookVerificationError

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    session: AsyncSession = Depends(session_dependency),
):
    """Handle Clerk webhook events."""
    payload = await request.body()
    headers = dict(request.headers)

    # Verify webhook signature
    wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
    try:
        event = wh.verify(payload, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event["type"]
    user_data = event["data"]

    service = UserSyncService(session)

    if event_type == "user.created":
        await service.upsert_user(user_data)
    elif event_type == "user.updated":
        await service.upsert_user(user_data)
    elif event_type == "user.deleted":
        await service.soft_delete_user(user_data["id"])

    return {"status": "ok"}
```

---

## Phase 4: Row-Level Security

**Effort**: 8 story points
**Assigned Subagent(s)**: data-layer-expert, python-backend-engineer

### Objectives

- Enable RLS on user-owned tables
- Set session user ID on each request
- Create RLS policies for data isolation

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate |
|----|------|-------------|---------------------|----------|
| RLS-001 | Enable RLS Migration | Create migration enabling RLS on listing, profile, valuation_ruleset | RLS enabled on tables | 2 pts |
| RLS-002 | Create RLS Policies | Define policies: user owns rows, admin bypasses | Policies created | 2 pts |
| RLS-003 | Session User Context | Set `app.current_user_id` on session start | Variable set per request | 2 pts |
| RLS-004 | RLS Integration Tests | Test cross-user data isolation | Tests pass for 2+ users | 2 pts |

### Quality Gates

- [ ] User A cannot query User B's listings
- [ ] Admin can query all data
- [ ] RLS policies don't break existing queries
- [ ] Performance impact < 10ms per query
- [ ] Tests confirm isolation for all protected tables

### Key Files

**Create**:
- `apps/api/alembic/versions/0033_enable_rls_listing.py`
- `apps/api/alembic/versions/0034_enable_rls_profile_ruleset.py`
- `tests/api/test_rls.py` - RLS isolation tests

**Modify**:
- `apps/api/dealbrain_api/db.py` - Add session user context setter

### Implementation Notes

**RLS Migration**:
```python
# Migration: Enable RLS on listing table

def upgrade():
    # Enable RLS
    op.execute("ALTER TABLE listing ENABLE ROW LEVEL SECURITY")

    # Create policy for users (user_id matches session user)
    op.execute("""
        CREATE POLICY listing_user_isolation ON listing
        FOR ALL
        USING (
            user_id IS NULL  -- Legacy data accessible to all
            OR user_id = NULLIF(current_setting('app.current_user_id', true), '')::int
        )
        WITH CHECK (
            user_id = NULLIF(current_setting('app.current_user_id', true), '')::int
        )
    """)

    # Create policy for admin bypass
    op.execute("""
        CREATE POLICY listing_admin_bypass ON listing
        FOR ALL
        USING (
            current_setting('app.current_user_role', true) = 'admin'
        )
    """)

def downgrade():
    op.execute("DROP POLICY IF EXISTS listing_admin_bypass ON listing")
    op.execute("DROP POLICY IF EXISTS listing_user_isolation ON listing")
    op.execute("ALTER TABLE listing DISABLE ROW LEVEL SECURITY")
```

**Session Context**:
```python
# apps/api/dealbrain_api/db.py

async def session_with_user_context(
    user: User,
    session: AsyncSession,
) -> AsyncSession:
    """Set session-level user context for RLS."""
    await session.execute(
        text(f"SET LOCAL app.current_user_id = '{user.id}'")
    )
    await session.execute(
        text(f"SET LOCAL app.current_user_role = '{user.role}'")
    )
    return session
```

---

## Phase 5: Frontend Integration

**Effort**: 7 story points
**Assigned Subagent(s)**: ui-engineer-enhanced, frontend-developer

### Objectives

- Add ClerkProvider to Next.js app
- Create middleware for route protection
- Implement auth UI components

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate |
|----|------|-------------|---------------------|----------|
| FE-001 | Install Clerk SDK | Add @clerk/nextjs, configure environment | SDK installed, env vars set | 1 pt |
| FE-002 | Add ClerkProvider | Wrap app in ClerkProvider | Provider renders without errors | 1 pt |
| FE-003 | Create Middleware | Route protection in middleware.ts | Protected routes redirect | 1 pt |
| FE-004 | Update API Client | Inject auth token in apiFetch | API calls include Bearer token | 1 pt |
| FE-005 | Login/Signup Pages | Create /sign-in and /sign-up routes | Auth pages render correctly | 1 pt |
| FE-006 | User Menu | Add user menu to AppShell header | Avatar, name, sign-out shown | 1 pt |
| FE-007 | Settings Page | User profile and preferences | Settings CRUD works | 1 pt |

### Quality Gates

- [ ] ClerkProvider wraps entire app
- [ ] Unauthenticated users redirected to /sign-in
- [ ] API calls include valid JWT
- [ ] User menu shows correct user info
- [ ] Sign-out clears session

### Key Files

**Create**:
- `apps/web/middleware.ts` - Route protection
- `apps/web/app/(auth)/sign-in/[[...sign-in]]/page.tsx`
- `apps/web/app/(auth)/sign-up/[[...sign-up]]/page.tsx`
- `apps/web/app/(authenticated)/settings/page.tsx`
- `apps/web/components/user-menu.tsx`

**Modify**:
- `apps/web/app/layout.tsx` - Add ClerkProvider
- `apps/web/components/providers.tsx` - Wrap with Clerk
- `apps/web/components/app-shell.tsx` - Add UserMenu
- `apps/web/lib/utils.ts` - Add auth token injection

### Implementation Notes

**ClerkProvider Setup**:
```tsx
// apps/web/app/layout.tsx

import { ClerkProvider } from '@clerk/nextjs'

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <body>
          <Providers>
            <AppShell>{children}</AppShell>
          </Providers>
        </body>
      </html>
    </ClerkProvider>
  )
}
```

**Middleware**:
```tsx
// apps/web/middleware.ts

import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/',  // Landing page public
])

export default clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) {
    await auth.protect()
  }
})

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
}
```

**API Client with Auth**:
```tsx
// apps/web/lib/api-client.ts

import { useAuth } from '@clerk/nextjs'

export function useApiClient() {
  const { getToken } = useAuth()

  async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const token = await getToken()
    const headers = new Headers(init?.headers)

    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
    headers.set('Content-Type', 'application/json')

    const response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers,
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    return response.json()
  }

  return { apiFetch }
}
```

---

## Phase 6: Admin, Testing & Documentation

**Effort**: 4 story points
**Assigned Subagent(s)**: documentation-writer, python-backend-engineer

### Objectives

- Implement admin user management
- Complete test coverage
- Document setup and usage

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate |
|----|------|-------------|---------------------|----------|
| ADMIN-001 | Admin API Routes | GET /admin/users, PATCH /admin/users/:id/role | Admin can list/modify users | 1 pt |
| TEST-001 | E2E Auth Tests | Playwright tests for auth flows | Tests pass in CI | 1 pt |
| DOC-001 | Developer Setup Guide | Document Clerk setup, env vars, local dev | Guide complete and accurate | 1 pt |
| DOC-002 | Update .env.example | Add all Clerk environment variables | Example file updated | 0.5 pt |
| DOC-003 | Auth Architecture Doc | Document auth flow and RLS | ADR created | 0.5 pt |

### Quality Gates

- [ ] Admin can view all users
- [ ] Admin can change user roles
- [ ] E2E tests pass for sign-in, sign-up, sign-out
- [ ] Documentation covers all setup steps
- [ ] CI pipeline supports auth testing

### Key Files

**Create**:
- `apps/api/dealbrain_api/api/admin.py` - Admin routes
- `apps/web/e2e/auth.spec.ts` - E2E auth tests
- `docs/development/clerk-setup.md` - Developer guide
- `docs/architecture/ADRs/adr-clerk-authentication.md`

**Modify**:
- `apps/api/.env.example` - Add Clerk vars
- `apps/web/.env.example` - Add Clerk vars
- `.github/workflows/test.yml` - Add Clerk test secrets

---

## Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|------------|
| Token verification latency | Use JWKS caching (Clerk SDK default: 1 hour) |
| RLS breaks existing queries | Test extensively, keep user_id nullable initially |
| Webhook delivery failures | Implement idempotent handlers, log failures |

### Schedule Risks

| Risk | Mitigation |
|------|------------|
| Clerk account setup delays | Request Clerk sandbox access early |
| RLS complexity | Allocate extra time for testing |
| Frontend hydration issues | SSR-compatible patterns, incremental rollout |

---

## Resource Requirements

### Dependencies

```json
// apps/web/package.json
{
  "@clerk/nextjs": "^6.35.4",
  "@clerk/testing": "^1.13.18"
}

// apps/api/pyproject.toml
[tool.poetry.dependencies]
pyjwt = "^2.8.0"
cryptography = "^41.0.0"
svix = "^1.4.0"  # Webhook signature verification
```

### Environment Variables

| Variable | Location | Description |
|----------|----------|-------------|
| NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY | Frontend | Clerk publishable key |
| CLERK_SECRET_KEY | Backend | Clerk secret key |
| CLERK_WEBHOOK_SECRET | Backend | Webhook signing secret |
| CLERK_JWKS_URL | Backend | JWKS endpoint URL |

---

## Success Metrics

### Delivery Metrics

- [ ] All 6 phases completed
- [ ] 100% API endpoints protected
- [ ] E2E tests passing in CI

### Business Metrics

- [ ] User sign-up conversion rate tracked
- [ ] Auth error rate < 0.1%
- [ ] Session duration metrics captured

### Technical Metrics

- [ ] Token verification p95 < 300ms
- [ ] RLS query overhead < 10ms
- [ ] Zero data leakage incidents

---

## Implementation Progress

See progress tracking: `.claude/progress/clerk-auth-integration-v2/all-phases-progress.md`

---

## Related Documents

- PRD: `./clerk-auth-integration-prd-v2.md`
- Original Codex PRD: `./product_requirements_document.md`
- Original Codex Plan: `./implementation_plan.md`
