---
type: context
prd: "clerk-auth-integration-v2"
created: 2025-11-25
updated: 2025-11-25
author: "Claude Code"
---

# Clerk Authentication Integration v2 - Implementation Context

**Project**: Deal Brain Clerk-Backed User Authentication & Authorization
**Phase Coverage**: All phases (1-6)
**Purpose**: Document architectural decisions, integration patterns, and key gotchas

---

## Architectural Decisions

### 1. JWT Verification Strategy

**Decision**: Use PyJWKClient with JWKS caching + Clerk SDK v6.35.x

**Rationale**:
- Clerk SDK handles JWKS endpoint management automatically
- PyJWKClient caches for 1 hour by default
- Reduces per-request latency vs. fetching JWKS every time
- Automatic key rotation handled by Clerk

**Key Pattern**:
```python
from jwt import PyJWKClient

jwk_client = PyJWKClient(jwks_url, cache_jwk_set=True)
signing_key = jwk_client.get_signing_key_from_jwt(token)
claims = jwt.decode(token, signing_key.key, algorithms=["RS256"])
```

**Trade-offs**: ✓ Lower latency, fewer requests | ✗ 1-hour key rotation delay (acceptable)

**Gotchas**:
- Import from `jwt` library, not `cryptography`
- Must specify `algorithms=["RS256"]` (Clerk uses RS256)
- Don't verify `aud` claim (Clerk doesn't use it by default)

---

### 2. CSRF Protection via authorizedParties

**Decision**: Verify `azp` (authorized party) claim matches frontend domain

**Rationale**:
- Prevents token reuse from other domains
- Required for CloudFlare Workers, good practice everywhere
- Clerk SDK supports natively

**Key Pattern**:
```python
if claims.get("azp") not in settings.AUTHORIZED_PARTIES:
    raise jwt.InvalidTokenError("Invalid authorized party")
```

**Gotchas**:
- `azp` ≠ `aud` (different claims entirely)
- Must maintain AUTHORIZED_PARTIES config for each deployment
- For local development, add `localhost:3000` to AUTHORIZED_PARTIES

---

### 3. JIT (Just-In-Time) User Provisioning

**Decision**: Create User record on first API request if not exists

**Rationale**:
- No webhook delays for first-time users
- Fallback if webhooks fail
- Decouples webhook reliability from user experience

**Key Pattern**:
```python
user = await session.scalar(select(User).where(User.clerk_id == clerk_id))

if not user:
    user = User(
        clerk_id=clerk_id,
        email=claims.get("email"),
        username=claims.get("username", clerk_id[:8]),
        first_name=claims.get("first_name"),
        last_name=claims.get("last_name"),
        avatar_url=claims.get("image_url"),
    )
    session.add(user)
    await session.flush()  # Get user.id without commit
```

**Trade-offs**: ✓ Instant access, webhook-independent | ✗ Updates still need webhooks

**Gotchas**:
- Must flush (not commit) to get user.id for same-request usage
- Email/name changes from Clerk must be synced via webhook
- `user.id` != `clerk_id` (internal vs. external identifier)

---

### 4. RLS Session Context via SET LOCAL

**Decision**: Use PostgreSQL `SET LOCAL app.current_user_id` per request

**Rationale**:
- PostgreSQL standard approach for per-request security context
- Works with async SQLAlchemy (fires before each query)
- LOCAL scope ensures statement isolation
- Works in transactions without explicit reset

**Key Pattern**:
```python
async def session_with_user_context(session: AsyncSession, user_id: int):
    await session.execute(
        text(f"SET LOCAL app.current_user_id = '{user_id}'")
    )
    await session.execute(
        text(f"SET LOCAL app.current_user_role = '{user_role}'")
    )
    return session
```

**Trade-offs**: ✓ Clean separation, prevents leakage | ✗ Must set before each query

**Gotchas**:
- `SET LOCAL` is statement-scoped (resets after query) - that's good!
- Admin bypass needs separate policy, not NULL check
- Cannot use in transaction block before first query
- Nullable user_id allows legacy data visible to all (intentional during transition)

---

### 5. Nullable user_id for Backwards Compatibility

**Decision**: Make user_id nullable on listing, profile, valuation_ruleset

**Rationale**:
- Existing data has no owner - makes sense for backwards compat
- Can migrate data ownership gradually
- RLS policies allow `user_id IS NULL` for legacy data
- Easier rollback if auth system has issues

**RLS Policy**:
```sql
CREATE POLICY listing_user_isolation ON listing
FOR ALL
USING (
    user_id IS NULL  -- Legacy data accessible to all
    OR user_id = NULLIF(current_setting('app.current_user_id')::int, '')
);
```

**Trade-offs**: ✓ No migration needed, gradual ownership | ✗ Legacy data visible temporarily

**Gotchas**:
- RLS policies are OR conditions, so NULL check allows all access
- Consider adding post-launch task for data ownership cleanup
- Set clear expiration date for when NULL user_id support drops

---

### 6. Webhook Idempotency Strategy

**Decision**: Idempotent handlers that check for event_id duplicates

**Rationale**:
- Webhooks can be retried by Clerk (up to 5 times)
- Idempotency prevents duplicate user creation/updates
- Simple event_id tracking prevents issues

**Key Pattern**:
```python
@router.post("/webhooks/clerk")
async def clerk_webhook(request: Request, session: AsyncSession):
    event = wh.verify(payload, dict(request.headers))
    event_id = event["id"]

    # Check if already processed
    processed = await session.scalar(
        select(exists()).where(ClerkEvent.event_id == event_id)
    )
    if processed:
        return {"status": "already_processed"}

    # Process event...
    session.add(ClerkEvent(event_id=event_id, event_type=event["type"]))
    await session.commit()
    return {"status": "ok"}
```

**Trade-offs**: ✓ Handles retries without side effects | ✗ Requires ClerkEvent table

**Gotchas**:
- Don't assume webhooks arrive in order
- Use event timestamps, not arrival order
- Clean up old ClerkEvent records after 30 days

---

## Integration Patterns

### Pattern 1: Auth Dependency Chain

```python
# Minimal auth (get user info)
@dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    claims = clerk_auth.verify_token(credentials.credentials)
    # ... JIT provision ...
    return user

# Full auth with RLS (with DB access)
@dependency
async def get_db_with_auth(
    session: AsyncSession = Depends(session_dependency),
    user: User = Depends(get_current_user),
):
    await session.execute(
        text(f"SET LOCAL app.current_user_id = '{user.id}'")
    )
    return session

# Admin-only routes
@dependency
async def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return user
```

**When to use each**:
- `get_current_user`: Need user info but not DB access
- `get_db_with_auth`: Standard for all DB queries with RLS
- `require_admin`: Admin-only endpoints

---

### Pattern 2: Protected Route Middleware (Frontend)

```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/',  // Landing page
])

export default clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) {
    await auth.protect()  // Redirect to /sign-in if not authenticated
  }
})
```

**Key points**:
- `auth.protect()` is async (Clerk v6 breaking change)
- PUBLIC routes must be explicitly listed
- Fallback is to protect (secure by default)

---

### Pattern 3: API Token Injection

```typescript
// lib/api-client.ts
import { useAuth } from '@clerk/nextjs'

export function useApiClient() {
  const { getToken } = useAuth()

  async function apiFetch<T>(
    path: string,
    init?: RequestInit
  ): Promise<T> {
    const token = await getToken()
    const headers = new Headers(init?.headers)

    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }

    const response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers,
    })

    return response.json()
  }

  return { apiFetch }
}
```

**Key points**:
- `getToken()` is async (can be called in client components)
- Always inject for authenticated requests
- Token automatically refreshed by Clerk SDK

---

## Testing Strategies

### Strategy 1: Auth Testing

```python
@pytest.mark.asyncio
async def test_valid_clerk_jwt(client, clerk_token):
    response = await client.get(
        "/api/v1/listings",
        headers={"Authorization": f"Bearer {clerk_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_invalid_jwt(client):
    response = await client.get(
        "/api/v1/listings",
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_missing_auth(client):
    response = await client.get("/api/v1/listings")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_route_non_admin(client, user_token):
    response = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
```

### Strategy 2: RLS Testing

```python
@pytest.mark.asyncio
async def test_rls_user_isolation(session, user_a, user_b):
    # User A creates listing
    listing = Listing(user_id=user_a.id, ...)
    session.add(listing)
    await session.commit()

    # User B queries - should be empty (RLS blocks)
    await session.execute(
        text(f"SET LOCAL app.current_user_id = '{user_b.id}'")
    )
    results = await session.execute(select(Listing))
    assert len(results.scalars().all()) == 0  # RLS: Empty!

    # User A queries - should see it
    await session.execute(
        text(f"SET LOCAL app.current_user_id = '{user_a.id}'")
    )
    results = await session.execute(select(Listing))
    assert len(results.scalars().all()) == 1  # Visible

@pytest.mark.asyncio
async def test_rls_admin_bypass(session, admin_user):
    # Admin can see all data regardless of user_id
    await session.execute(
        text(f"SET LOCAL app.current_user_role = 'admin'")
    )
    results = await session.execute(select(Listing))
    # Should see all listings
```

### Strategy 3: E2E Testing (Playwright)

```typescript
// e2e/auth.spec.ts
import { setupClerkTestingToken } from '@clerk/testing/playwright'
import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await setupClerkTestingToken({ page })  // Auto-setup testing tokens
})

test('sign up with Google', async ({ page }) => {
  await page.goto('/sign-up')
  await page.click('button:has-text("Sign in with Google")')
  // ... Google OAuth flow
  await expect(page).toHaveURL('/dashboard')
})

test('sign out', async ({ page }) => {
  await page.goto('/dashboard')
  await page.click('[data-testid="user-menu"]')
  await page.click('button:has-text("Sign out")')
  await expect(page).toHaveURL('/sign-in')
})
```

---

## Deployment Considerations

### Pre-Deployment Checklist

- [ ] Clerk account created and configured
- [ ] OAuth apps (Google, GitHub) created with correct redirect URIs
- [ ] CLERK_SECRET_KEY and NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY in all environments
- [ ] Webhook secret configured in Clerk dashboard and backend (CLERK_WEBHOOK_SECRET)
- [ ] RLS admin bypass policy deployed BEFORE enabling RLS
- [ ] E2E tests passing in CI/CD pipeline
- [ ] Token verification latency verified (<300ms p95)
- [ ] Audit logging configured for security events
- [ ] Database backups in place
- [ ] Rollback plan documented and tested

### Rollback Plan

**If auth system breaks**:
1. Disable auth middleware temporarily (allow all requests)
2. Investigate root cause in logs
3. Fix and test locally first
4. Redeploy with middleware enabled

**If RLS data leakage occurs**:
1. Immediately disable RLS: `ALTER TABLE listing DISABLE ROW LEVEL SECURITY`
2. Investigate cause in audit logs
3. Fix policies
4. Reenable RLS with fixed policies

**If Clerk connectivity issues**:
1. Cache JWKS for longer period (increase cache TTL)
2. Fall back to previous valid tokens temporarily
3. Monitor Clerk status page
4. Coordinate with Clerk support

---

## Known Limitations

### Limitation 1: No Offline Support

**Impact**: Users must have internet connection to sign in
**Workaround**: Not applicable for SaaS (acceptable)

### Limitation 2: Token Expiry Handling

**Impact**: Tokens expire, frontend must handle refresh
**Workaround**: Clerk SDK handles automatically in useAuth()

### Limitation 3: RLS Blocks Admin Queries Initially

**Impact**: When RLS is first enabled, admin may get 403 errors
**Solution**: Deploy admin bypass policy BEFORE enabling RLS

```sql
-- Deploy this FIRST
CREATE POLICY admin_bypass ON listing
FOR ALL USING (current_setting('app.current_user_role') = 'admin');

-- THEN enable RLS
ALTER TABLE listing ENABLE ROW LEVEL SECURITY;
```

### Limitation 4: Webhook Retry Window

**Impact**: Clerk retries webhooks for ~24 hours before giving up
**Workaround**: Monitor webhook failures, implement alerting on failures

---

## Future Enhancements

### Post-Launch (v2.1):
- Clean up NULL user_id records
- Archive old ClerkEvent records
- Add webhook failure alerting

### Phase 2 (v3):
- Organization/team multi-tenancy (requires org_id on tables)
- API key management for non-web clients
- Advanced audit logging (log all data access)
- User invitation flows
- Role-based access control (RBAC) beyond admin/user

### Phase 3 (v4):
- Social features (share listings, collaborations)
- Premium tier support
- Usage-based billing

---

## Key Gotchas Summary

| Issue | Solution |
|-------|----------|
| Forgot to await auth() (v6) | Always `await auth()` in server components |
| JWT exceeds 1.2KB limit | Keep custom claims minimal, store data in DB |
| JWKS cache stale | PyJWKClient auto-refreshes if key not found |
| RLS blocks admin | Deploy admin bypass policy BEFORE enabling RLS |
| Webhook duplicates with JIT | Use idempotent upserts with event_id tracking |
| Timezone issues with claims | Parse timestamps carefully, use UTC |
| Session context not set | Dependency injection handles SET LOCAL |

---

## Related Documents

- **PRD v2**: `/docs/project_plans/clerk_user_integration/clerk-auth-integration-prd-v2.md`
- **Implementation Plan v2**: `/docs/project_plans/clerk_user_integration/clerk-auth-integration-implementation-plan-v2.md`
- **Progress Tracking**: `.claude/progress/clerk-auth-integration-v2/all-phases-progress.md`
- **Clerk Docs**: https://clerk.com/docs
- **Clerk v6 Changelog**: https://clerk.com/changelog/2024-10-22-clerk-nextjs-v6
- **Clerk API 2025-11-10 Breaking Changes**: https://clerk.com/docs/guides/development/upgrading/upgrade-guides/2025-11-10
- **PostgreSQL RLS**: https://www.postgresql.org/docs/current/sql-createrole.html
