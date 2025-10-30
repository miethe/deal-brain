# Clerk-Backed User Accounts Implementation Plan

## 1. Authentication Integration Across Stack
### Objectives
- Validate Clerk tokens on all API requests and expose authenticated user context.
- Replace existing or placeholder auth flows in the Next.js frontend with Clerk components and helpers.

### Key Tasks
1. Add Clerk environment variables to infrastructure artifacts (Docker Compose, deployment manifests, local `.env` files).
2. Install `@clerk/nextjs` in `apps/web` and wrap the root layout with `<ClerkProvider>`; guard protected routes with `<SignedIn>` or server helpers.
3. Introduce a FastAPI dependency in `apps/api/dealbrain_api/dependencies` that validates Clerk JWTs (using `clerk-backend` or JWKS fetch) and attaches user context.
4. Update all protected routers in `apps/api/dealbrain_api/routes` to require the new dependency; ensure OpenAPI docs reflect auth requirements.
5. Provide integration tests in `tests/api` covering auth success and failure scenarios.

## 2. User Domain Model and Persistence
### Objectives
- Store application-specific user data linked to Clerk identities.
- Ensure services and routes can retrieve or create user records on demand.

### Key Tasks
1. Create a SQLAlchemy model `User` in `apps/api/dealbrain_api/models/user.py` with Clerk `user_id`, email, role, preferences JSONB, and timestamps.
2. Generate an Alembic migration under `apps/api/alembic/versions` creating the `users` table and necessary indexes.
3. Update database initialization to provision default roles and permissions; ensure tests seed demo users.
4. Implement a service in `apps/api/dealbrain_api/services/user_service.py` for user creation and synchronization, and expose a dependency for accessing the current user record.
5. Cover the service with unit tests in `tests/api/services` and ensure factories or fixtures are updated.

## 3. Clerk Webhooks and Synchronization
### Objectives
- Keep local user data synchronized with Clerk lifecycle events.
- Ensure webhook handling is secure and observable.

### Key Tasks
1. Add a webhook endpoint in `apps/api/dealbrain_api/routes/webhooks.py` using Clerk signature validation.
2. Update configuration in `apps/api/dealbrain_api/core/config.py` to load the webhook secret.
3. Implement handlers to upsert or delete local `User` records on relevant Clerk events.
4. Write tests simulating webhook payloads to ensure data consistency and signature enforcement.

## 4. Row Level Security (RLS)
### Objectives
- Enforce per-user data isolation at the database level.
- Ensure backend sessions communicate the current user identity to PostgreSQL.

### Key Tasks
1. Enable RLS in an Alembic migration for each relevant table (for example, `deals`, `documents`, `workspaces`) and define policies tied to `user_id` or tenant ID.
2. Modify database session management in `apps/api/dealbrain_api/db/session.py` to execute `SET LOCAL app.current_user_id = :id` per request.
3. Update repositories to include `user_id` columns in new records.
4. Add regression tests (possibly using pytest with async DB fixtures) to ensure cross-user access is denied.

## 5. Frontend User Settings Experience
### Objectives
- Provide an authenticated settings area for profile management and app preferences.
- Synchronize settings changes between Clerk and Deal Brain.

### Key Tasks
1. Add a Next.js route `apps/web/app/(authenticated)/settings/page.tsx` with Clerk components for profile picture, name, and email.
2. Implement forms for application preferences using existing UI primitives in `apps/web/components`.
3. Connect the UI to backend settings endpoints located in `apps/api/dealbrain_api/routes/settings.py`.
4. Write frontend tests under `apps/web/__tests__/settings.test.tsx` and end-to-end coverage if Playwright is configured.
5. Update documentation in `docs/` to describe the settings experience and available options.

## 6. Backend Settings and API Token Management
### Objectives
- Allow users to configure application-level preferences and manage API tokens securely.

### Key Tasks
1. Define new tables or models `user_preferences` and `api_tokens` in `apps/api/dealbrain_api/models`.
2. Create CRUD endpoints in `apps/api/dealbrain_api/routes/settings.py` protected by the auth dependency.
3. Implement token generation utilities in `apps/api/dealbrain_api/utils/security.py` with hashing and prefix display.
4. Add tests in `tests/api/routes/test_settings.py` ensuring RBAC and RLS compliance.

## 7. Admin and Observability Enhancements
### Objectives
- Provide operators with insight and control over user accounts.
- Improve visibility into authentication flows.

### Key Tasks
1. Add admin-only API routes (`apps/api/dealbrain_api/routes/admin_users.py`) checking the user role.
2. Build a simple admin UI or CLI command (`apps/cli`) to list users and modify roles.
3. Integrate structured logging for auth events in `apps/api/dealbrain_api/core/logging.py` and pipe events to monitoring.
4. Write role-based access tests in `tests/api/routes/test_admin_users.py`.

## 8. Documentation and Developer Experience
### Objectives
- Streamline local setup and onboarding for developers working with Clerk.

### Key Tasks
1. Revise `docs/development.md` (or create a new document) detailing environment setup, Clerk dashboard configuration, and local webhook testing.
2. Update `.env.example` files across `apps/web` and `apps/api`.
3. Modify CI workflows (GitHub Actions under `.github/workflows` if present) to supply mock Clerk secrets for tests.
4. Ensure onboarding scripts in `scripts/` or the Makefile include Clerk setup steps.
