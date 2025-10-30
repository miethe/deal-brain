# Clerk-Backed User Accounts PRD

## Background
Deal Brain currently operates without authenticated users. To evolve the product into a SaaS platform and support eventual social features, the application must introduce full user accounts, secure authentication, and per-user data isolation. Clerk will be used as the identity platform because it offers hosted authentication, secure session handling, and SDK support for both the Next.js frontend and FastAPI backend.

## Goals
- Support secure login, signup, and session management with Clerk across the web and API surfaces.
- Introduce a persistent `User` domain model tied to Clerk identities.
- Protect all user-owned data with Row Level Security (RLS) so each tenant’s data is isolated by default.
- Deliver a user settings experience for account management and application preferences.
- Establish a foundation for future multi-tenant and social features (for example, shared dashboards).

## Non-Goals
- Public social features, shared dashboards, or community feeds (future work).
- Data migration or backfill considerations (no active production data).
- Support for non-web clients (mobile, CLI) beyond issuing API tokens.
- Legacy auth support; Clerk will be the sole identity provider.

## Target Users
- SaaS customers with private Deal Brain instances who require secure access control.
- Internal operators who need admin tooling for user management.

## Requirements

### Functional
1. Users can sign up, sign in, sign out, and manage sessions via Clerk on the Next.js frontend.
2. Backend APIs accept Clerk-issued tokens, verify them, and map requests to internal user records.
3. A `User` entity is persisted in the primary database with application-specific profile fields (role, preferences, metadata).
4. RLS ensures each user (and, later, organization) accesses only their data.
5. A settings page allows profile updates (name, avatar), notification preferences, and API key management.
6. Admin users can view user lists and toggle tenant-level settings (optional admin UI skeleton).
7. Audit logging captures key auth events (login, logout, failed auth, settings change).

### Non-Functional
- Authentication latency should remain under 300ms p95 for token verification.
- RLS policies must be thoroughly tested to prevent privilege escalation.
- Frontend should gracefully handle auth state hydration (SSR and CSR).
- Monitoring hooks log Clerk webhook processing and token validation errors.

### Security and Compliance
- All APIs require authentication unless explicitly marked public.
- Tokens validated using Clerk JWKS; rotate keys automatically.
- Store minimal PII and rely on Clerk as system of record for sensitive identity attributes.
- Implement least-privilege service roles for backend components.
- Maintain audit logs for security-relevant events.

### Dependencies
- Clerk SDK for Next.js and FastAPI (via `@clerk/nextjs` and `clerk-backend` or REST).
- Database (PostgreSQL) with RLS support.
- Existing infrastructure: Docker, Prisma/SQLModel/SQLAlchemy (confirm actual ORM in repo).

## Success Metrics
- 100% of API endpoints require and validate authentication.
- RLS policy tests confirm isolation across at least two seeded users.
- Settings page completes CRUD flows with Clerk profile synchronization.
- Integration tests achieve 90% or higher coverage for new auth-critical components.

## Risks and Mitigations
- **Token Verification Latency:** Cache Clerk JWKS and leverage Clerk SDK caching to avoid per-request network hits.
- **RLS Misconfiguration:** Implement thorough automated tests and manual verification to ensure no data leakage.
- **Webhook Reliability:** Use retry logic and idempotent handlers; log failures to the observability stack.
- **Local Developer Experience:** Provide comprehensive documentation and scripts to minimize friction with Clerk sandbox accounts.

## Estimated Effort
- Backend authentication and user model: 3–4 engineer-weeks.
- Frontend integration and settings UI: 2–3 engineer-weeks.
- RLS implementation and testing: 2 engineer-weeks.
- Admin and observability tooling: 1 engineer-week.
- Documentation and developer tooling: 0.5 engineer-week.

**Total estimated effort:** approximately 8–10 engineer-weeks, assuming one squad with backend and frontend collaboration plus dedicated QA.
