---
title: "Clerk Authentication Integration - PRD v2"
description: "Comprehensive user authentication and authorization system using Clerk for Deal Brain SaaS platform, including RLS, user profiles, and admin controls."
audience: [ai-agents, developers]
tags: [authentication, clerk, rls, security, saas, oauth, multi-tenant]
created: 2025-11-25
updated: 2025-11-25
category: "product-planning"
status: draft
related:
  - /docs/project_plans/clerk_user_integration/product_requirements_document.md
  - /docs/project_plans/clerk_user_integration/implementation_plan.md
---

# Clerk Authentication Integration - PRD v2

**Feature Name**: Clerk-Backed User Authentication & Authorization
**Version**: 2.0 (Enhanced from Codex v1)
**Date**: 2025-11-25
**Author**: Claude Code
**Status**: Draft

## 1. Executive Summary

Deal Brain requires a comprehensive authentication and authorization system to evolve from a single-user tool into a multi-tenant SaaS platform. This PRD defines the implementation of Clerk-based authentication with OAuth support (Google, GitHub), row-level security (RLS) for data isolation, user profiles with preferences, and admin controls for user management.

**Key Deliverables**:
- OAuth login (Google, GitHub) and email/password authentication via Clerk
- Session management with JWT token validation on FastAPI backend
- User profiles with application preferences
- Row-level security (RLS) for per-user data isolation
- Collection ownership and sharing permissions
- Admin vs. regular user role separation
- Protected routes and auth-aware UI components

## 2. Context & Background

### Current State

Deal Brain currently operates without authenticated users:

- **Database**: `User` model exists (`apps/api/dealbrain_api/models/sharing.py:28`) with `username`, `email`, `display_name` fields but no auth integration
- **Backend**: Placeholder `get_current_user()` returns hardcoded `user_id=1` (`apps/api/dealbrain_api/api/collections.py:64-83`)
- **Frontend**: No ClerkProvider, no middleware, no auth token injection (`apps/web/components/providers.tsx`, `apps/web/lib/utils.ts`)
- **Data Isolation**: Collections have `user_id` foreign key; Listings, Profiles, ValuationRulesets do not

### Technical Foundation

**Existing Patterns to Leverage**:
- `CurrentUserDep` dependency pattern already established for collections API
- AsyncSession dependency injection pattern (`session_dependency()`)
- User model with relationships to Collections, Shares

**Clerk SDK Versions** (as of Nov 2025):
- `@clerk/nextjs@6.35.4` - Next.js integration
- `@clerk/backend@2.23.2` - Backend JWT validation
- Breaking: `auth()` is async in v6 (must await)
- API Version: 2025-11-10

## 3. Problem Statement

Without authentication:
1. All users share the same data - no privacy or personalization
2. Cannot support multi-tenant SaaS deployment
3. No audit trail for user actions
4. Cannot implement premium features or usage limits
5. No foundation for social features (sharing, collaboration)

## 4. Goals & Success Metrics

### Goals

| Goal | Description |
|------|-------------|
| G1 | Secure authentication via Clerk (OAuth + email/password) |
| G2 | Per-user data isolation with PostgreSQL RLS |
| G3 | User profiles with application preferences |
| G4 | Role-based access control (admin vs. user) |
| G5 | Protected routes with graceful auth state handling |

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| M1 | 100% API endpoints require authentication | Automated test coverage |
| M2 | RLS policy tests pass for 2+ seeded users | Integration tests |
| M3 | Auth latency < 300ms p95 | Token verification benchmark |
| M4 | Settings CRUD works with Clerk sync | E2E tests |
| M5 | Zero data leakage across users | Security audit |

## 5. Requirements

### 5.1 Functional Requirements

#### FR-1: Authentication System

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | Users can sign up via Google OAuth | P0 |
| FR-1.2 | Users can sign up via GitHub OAuth | P0 |
| FR-1.3 | Users can sign up via email/password | P1 |
| FR-1.4 | Users can sign out from all sessions | P0 |
| FR-1.5 | Users can manage active sessions | P2 |
| FR-1.6 | Failed auth attempts are logged | P1 |

#### FR-2: User Domain Model

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | User record created on first sign-in (JIT provisioning) | P0 |
| FR-2.2 | User synced via Clerk webhooks (create, update, delete) | P0 |
| FR-2.3 | User has role field (admin, user) | P0 |
| FR-2.4 | User has preferences JSONB field | P1 |
| FR-2.5 | User avatar_url synced from Clerk | P1 |

#### FR-3: Row-Level Security

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Listing table has user_id foreign key | P0 |
| FR-3.2 | Profile table has user_id foreign key | P0 |
| FR-3.3 | ValuationRuleset table has user_id foreign key | P1 |
| FR-3.4 | RLS policies enforce user_id = current_user | P0 |
| FR-3.5 | Session sets `app.current_user_id` on each request | P0 |

#### FR-4: Authorization

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Admin can view all users | P1 |
| FR-4.2 | Admin can modify user roles | P1 |
| FR-4.3 | Users can only access their own data | P0 |
| FR-4.4 | Collections support private/public/shared visibility | P1 |
| FR-4.5 | Listings can be shared via Collections | P2 |

#### FR-5: UI Auth Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | Login page with Google/GitHub/email options | P0 |
| FR-5.2 | Sign-up page with same options | P0 |
| FR-5.3 | User menu in AppShell header | P0 |
| FR-5.4 | Profile/settings page | P1 |
| FR-5.5 | Protected routes redirect to login | P0 |
| FR-5.6 | Auth state persists across page refreshes | P0 |

### 5.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Token verification latency | < 300ms p95 |
| NFR-2 | JWKS cache duration | 1 hour (Clerk SDK default) |
| NFR-3 | Webhook idempotency | 100% (handle retries) |
| NFR-4 | Auth state hydration | SSR + CSR compatible |
| NFR-5 | Accessibility | WCAG AA for auth flows |

### 5.3 Security Requirements

| ID | Requirement |
|----|-------------|
| SEC-1 | All APIs require authentication unless explicitly public |
| SEC-2 | Tokens validated using Clerk JWKS with automatic rotation |
| SEC-3 | Minimal PII stored locally (Clerk is system of record) |
| SEC-4 | Webhook signatures validated with Clerk secret |
| SEC-5 | Audit logs for auth events (login, logout, role change) |
| SEC-6 | CSRF protection via authorizedParties in token verification |

## 6. Scope

### In Scope

- Clerk integration (OAuth providers, email/password)
- User model with Clerk ID linking
- RLS implementation for Listing, Profile, ValuationRuleset
- Basic admin UI for user management
- Settings page with profile management
- Protected route middleware
- Webhook handlers for user lifecycle

### Out of Scope

- Mobile app authentication (CLI tokens only)
- Social features (public profiles, feeds) - future work
- Organization/team multi-tenancy - future work
- Data migration for existing listings - no production data
- Legacy auth providers - Clerk only

## 7. Dependencies & Assumptions

### Dependencies

| Dependency | Impact |
|------------|--------|
| Clerk account setup | Required for API keys |
| Clerk SDK (@clerk/nextjs@6.35.x) | Required for frontend |
| Clerk JWKS endpoint | Required for backend token validation |
| PostgreSQL RLS support | Required for data isolation |

### Assumptions

1. No existing production data requiring migration
2. Single-tenant deployment initially (no organizations)
3. Clerk sandbox available for development
4. Existing `User` model can be extended (not replaced)

## 8. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Token verification latency | Medium | Medium | Cache JWKS, use Clerk SDK caching |
| RLS misconfiguration | Low | High | Comprehensive tests, security review |
| Webhook delivery failures | Low | Medium | Idempotent handlers, retry logic |
| JWT size limit (1.2KB) | Low | Low | Minimal custom claims, store in DB |
| Clerk API version changes | Medium | Medium | Pin SDK versions, monitor changelog |

## 9. Target State

### Architecture After Implementation

```
┌─────────────────────────────────────────────────────────────────┐
│                         Next.js Frontend                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ <ClerkProvider>                                              ││
│  │   ├── middleware.ts (route protection)                       ││
│  │   ├── <SignedIn>/<SignedOut> components                     ││
│  │   ├── useAuth() hook for token injection                    ││
│  │   └── User menu, profile page                               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ Authorization: Bearer <clerk_jwt>
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Auth Middleware                                              ││
│  │   ├── verify_clerk_jwt() dependency                         ││
│  │   ├── get_current_user() → User model                       ││
│  │   └── CurrentUserDep annotation                             ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ Webhook Handler (/api/webhooks/clerk)                       ││
│  │   ├── user.created → upsert User                            ││
│  │   ├── user.updated → update User                            ││
│  │   └── user.deleted → soft delete User                       ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ SET LOCAL app.current_user_id
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PostgreSQL with RLS                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Tables with user_id + RLS Policies                          ││
│  │   ├── listing (user_id FK, RLS policy)                      ││
│  │   ├── profile (user_id FK, RLS policy)                      ││
│  │   ├── valuation_ruleset (user_id FK, RLS policy)            ││
│  │   ├── collection (user_id FK, existing RLS)                 ││
│  │   └── user (clerk_id unique, role, preferences)             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 10. Acceptance Criteria

### AC-1: Authentication Flow

- [ ] User can sign in via Google OAuth
- [ ] User can sign in via GitHub OAuth
- [ ] User can sign in via email/password
- [ ] User can sign out
- [ ] Session persists across page refreshes
- [ ] Invalid token returns 401 Unauthorized

### AC-2: User Provisioning

- [ ] First sign-in creates User record
- [ ] Clerk webhook creates User if not exists
- [ ] Clerk webhook updates User on profile change
- [ ] Clerk webhook soft-deletes User on deletion

### AC-3: Data Isolation

- [ ] User A cannot see User B's listings
- [ ] User A cannot see User B's profiles
- [ ] RLS policy tests pass for all protected tables
- [ ] Admin can bypass RLS for management queries

### AC-4: UI Integration

- [ ] Login page renders with all auth options
- [ ] User menu shows avatar and name
- [ ] Protected routes redirect unauthenticated users
- [ ] Settings page updates profile successfully

### AC-5: Security

- [ ] No API endpoints accessible without auth (except webhooks)
- [ ] Webhook signature validation passes
- [ ] JWKS caching reduces verification latency
- [ ] Audit log captures auth events

## 11. Implementation

See implementation plan: `./clerk-auth-integration-implementation-plan-v2.md`

See progress tracking: `.claude/progress/clerk-auth-integration-v2/all-phases-progress.md`

## 12. Appendix

### A. Database Schema Changes

**User Model Updates**:
```python
class User(Base, TimestampMixin):
    id: int  # Internal primary key
    clerk_id: str  # Clerk user_id (unique, indexed)
    email: str
    username: str
    display_name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    avatar_url: Optional[str]
    role: str  # 'admin' | 'user'
    preferences: dict  # JSONB
    is_active: bool  # Soft delete flag
```

**Tables Requiring user_id**:
- `listing` - requires new `user_id` FK
- `profile` - requires new `user_id` FK
- `valuation_ruleset` - requires new `user_id` FK
- `saved_build` - requires new `user_id` FK

### B. Environment Variables

```bash
# Frontend (.env.local)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard

# Backend (.env)
CLERK_SECRET_KEY=sk_test_...
CLERK_WEBHOOK_SECRET=whsec_...
CLERK_JWKS_URL=https://api.clerk.com/.well-known/jwks.json
```

### C. API Endpoints

**New Endpoints**:
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/webhooks/clerk | Clerk webhook handler |
| GET | /api/v1/users/me | Get current user profile |
| PATCH | /api/v1/users/me | Update current user preferences |
| GET | /api/v1/admin/users | List all users (admin) |
| PATCH | /api/v1/admin/users/{id}/role | Update user role (admin) |

**Protected Endpoints** (all existing endpoints):
- All `/api/v1/listings/*`
- All `/api/v1/profiles/*`
- All `/api/v1/collections/*`
- All `/api/v1/valuation-rules/*`

### D. Related Documents

- Original Codex PRD: `./product_requirements_document.md`
- Original Codex Implementation Plan: `./implementation_plan.md`
- Clerk v6 Migration Guide: https://clerk.com/changelog/2024-10-22-clerk-nextjs-v6
- Clerk API 2025-11-10 Breaking Changes: https://clerk.com/docs/guides/development/upgrading/upgrade-guides/2025-11-10
