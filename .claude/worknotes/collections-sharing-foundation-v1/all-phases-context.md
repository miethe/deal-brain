# Collections & Sharing Foundation v1 - Working Context

**Purpose:** Token-efficient context for resuming work across AI turns for all phases

---

## Current State

**Branch:** claude/collections-sharing-foundation-01DM8Wo2RYeHrniBjRgP2CpL
**Current Phase:** Phase 3 Complete, Ready for Phase 4 (UI Layer & Integration)
**Last Commit:** 831dee1 - Phase 3 API Layer complete
**Status:** ✅ 74% Complete (66/89 SP)

---

## Key Architectural Decisions

### Database Architecture
- **3 new tables:** ListingShare (public shares), UserShare (user-to-user shares), Collection + CollectionItem
- **Share tokens:** Secure random 64-char tokens (secrets.token_urlsafe(48))
- **Expiry strategy:** Public shares 180 days, user-to-user shares 30 days
- **Cascade deletes:** Collection deletion removes all CollectionItems
- **Position column:** Integer field for user-defined ordering (drag-and-drop support)

### Backend Patterns (Deal Brain Conventions)
- **Layered architecture:** API Routes → Services → Domain Logic (packages/core) → Database
- **Async-first:** All database operations use async SQLAlchemy
- **Repository pattern:** Data access layer separates queries from business logic
- **Pydantic validation:** All API requests/responses use Pydantic schemas
- **Domain logic in packages/core:** Shared logic between API and CLI lives in core package

### API Design
- **Authentication:** JWT tokens via session_dependency() for protected routes
- **Rate limiting:** 10 shares/hour/user to prevent abuse
- **Pagination:** limit/offset for list endpoints, default 20 items
- **Error handling:** Standard HTTP status codes (400, 401, 403, 404, 409, 500)
- **OpenAPI docs:** Auto-generated via FastAPI Swagger UI

### Frontend Patterns
- **Radix UI:** All base components use Radix primitives (headless, accessible)
- **React Query:** Server state management with aggressive caching
- **Zustand:** Global client state (if needed for UI preferences)
- **Component memoization:** React.memo for performance optimization
- **Mobile-first:** Card view on mobile, table view on desktop

### Security Considerations
- **Token enumeration prevention:** Use 64-char random tokens, not sequential IDs
- **Authorization checks:** Verify ownership before all mutations
- **SQL injection prevention:** SQLAlchemy parameterized queries only
- **XSS prevention:** Pydantic validation + frontend sanitization
- **Rate limiting:** Applied to share creation endpoints

---

## Important Learnings

*This section will be populated as development progresses with gotchas, patterns, and best practices discovered.*

---

## Quick Reference

### Environment Setup

```bash
# Backend API
export PYTHONPATH="$PWD/apps/api"
poetry install
poetry run uvicorn dealbrain_api.app:app --reload

# Frontend Web
cd apps/web
pnpm install
pnpm dev

# Database
make migrate  # Apply Alembic migrations
poetry run alembic revision --autogenerate -m "description"  # Create migration

# Full stack
make up  # Docker Compose with Postgres, Redis, API, web, worker

# Testing
poetry run pytest apps/api/tests/  # Backend tests
pnpm --filter "./apps/web" test  # Frontend tests
```

### Key Files

**Database:**
- Models: `apps/api/dealbrain_api/models/core.py`
- Migrations: `apps/api/alembic/versions/`
- DB config: `apps/api/dealbrain_api/db.py`

**Backend Services:**
- Sharing: `apps/api/dealbrain_api/services/sharing_service.py` (to be created)
- Collections: `apps/api/dealbrain_api/services/collections_service.py` (to be created)
- Repositories: `apps/api/dealbrain_api/repositories/` (to be created)

**Backend API:**
- Share endpoints: `apps/api/dealbrain_api/api/shares.py` (to be created)
- User share endpoints: `apps/api/dealbrain_api/api/user_shares.py` (to be created)
- Collections endpoints: `apps/api/dealbrain_api/api/collections.py` (to be created)

**Schemas:**
- Shared schemas: `packages/core/dealbrain_core/schemas/` (to be created)
- API schemas: `apps/api/dealbrain_api/schemas/` (to be created)

**Frontend Pages:**
- Collections list: `apps/web/app/collections/page.tsx` (to be created)
- Collection workspace: `apps/web/app/collections/[id]/page.tsx` (to be created)
- Public deal page: `apps/web/app/deals/[id]/[token]/page.tsx` (to be created)

**Frontend Components:**
- Collections: `apps/web/components/collections/` (to be created)
- Share button: `apps/web/components/share/` (to be created)

**Frontend Hooks:**
- `apps/web/hooks/useCollections.ts` (to be created)
- `apps/web/hooks/useCollection.ts` (to be created)
- `apps/web/hooks/useShare.ts` (to be created)

---

## Phase Scope Summary

### Phase 1: Database Schema & Repository Layer (21 SP, Week 1)
Create migrations for ListingShare, UserShare, Collection, CollectionItem tables. Implement SQLAlchemy models and repository pattern for data access.

### Phase 2: Service & Business Logic Layer (21 SP, Week 1-2)
Implement SharingService, CollectionsService, and integration logic. Handle token generation, validation, authorization, and business rules.

### Phase 3: API Layer (20 SP, Week 2)
Create REST endpoints for shares, user-shares, collections, and collection items. Implement request/response handling, validation, and error handling.

### Phase 4: UI Layer & Integration (20 SP, Week 2-3)
Build React components for public deal pages, share modals, collections list, and workspace view. Integrate with API using React Query.

### Phase 5: Integration, Polish & Performance (17 SP, Week 3-4)
Connect all pieces end-to-end. Add notifications, exports, mobile optimization, and performance tuning.

### Phase 6: Testing & Launch (10 SP, Week 4-5)
Comprehensive E2E testing, accessibility audit, security review, performance testing, documentation, and staged rollout.

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Shareable pages created/month | 200 by month 3 |
| Share-to-visit conversion | >5% |
| New user signups from shares | 50/month by month 3 |
| Collections created | 100 by month 2 |
| Avg items per active collection | ≥3 items |
| Collections with notes | >70% |
| User-to-user shares | 200/month by month 3 |
| Share-to-import conversion | >40% |

---

## Critical Path & Dependencies

```
Phase 1 (Database) → Phase 2 (Services) → Phase 3 (API) → Phase 4 (UI) → Phase 5 (Integration) → Phase 6 (Testing)
```

- Phases 1-3 are sequential (backend critical path)
- Phase 4 can begin once Phase 3 endpoints are available (with mocks)
- Phases 5-6 require all previous phases complete
- Total timeline: 5 weeks (35 days)

---

## Subagent Coordination

### Primary Subagents
- **data-layer-expert:** Phase 1 migrations and models
- **python-backend-engineer:** Phases 2-3 (services, API), Phase 5 (backend polish)
- **ui-engineer-enhanced:** Phases 4-5 (UI components, mobile optimization)
- **test-automator:** Phase 6 (E2E testing, QA)
- **documentation-writer:** Phase 6 (API docs, user guides)

### Cross-Phase Collaboration
- Backend and frontend can work in parallel starting Phase 4 (with API mocks)
- Testing can begin incrementally during Phase 4-5 (unit tests ongoing)
- Documentation should be drafted during Phase 5, finalized in Phase 6

---

## Notes for Future Sessions

*This section will be updated at the end of each turn with:*
- Current blockers or issues
- Next immediate tasks
- Context needed for continuation
- Any deviations from the original plan
