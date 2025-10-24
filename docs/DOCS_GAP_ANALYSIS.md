# Documentation Gap Analysis Report
**Deal Brain Project**
**Analysis Date:** October 24, 2025

---

## Executive Summary

Deal Brain has a **solid foundation** of documentation with 70+ documents covering architecture, design systems, user features, and database schemas. However, significant gaps exist in areas critical for **public release and developer onboarding**. The project lacks comprehensive REST API endpoint documentation, complete backend development guides, production deployment procedures, and clear contribution guidelines.

**Overall Documentation Health: 65/100**
- Strengths: Architecture & design patterns well documented, user-facing features comprehensive
- Critical Gaps: API reference, backend patterns, deployment, contribution guidelines
- Impact: New developers struggle with local setup variations; public release blocked without API docs

**Recommended Immediate Actions:**
1. **Create REST API endpoint reference** (111 endpoints documented in code, zero in docs) — 12 hours
2. **Write CONTRIBUTING.md** (blocking open source release) — 4 hours
3. **Add Backend Development Guide** (no patterns/conventions documented) — 8 hours
4. **Production Deployment Guide** (Docker config exists but no guide) — 6 hours
5. **Troubleshooting & FAQ** (common setup issues not documented) — 4 hours

---

## Scoring Methodology

Documentation quality is scored on a **5-point scale**:

| Score | Level | Definition |
|-------|-------|-----------|
| **5/5** | Comprehensive | Complete, detailed, with examples; easy to follow; recently updated |
| **4/5** | Good | Covers main topics; minor gaps; mostly easy to use |
| **3/5** | Partial | Has basic content; missing details; could be better organized |
| **2/5** | Minimal | Very brief; lacks examples; missing key information |
| **1/5** | Critical Gap | Missing or completely inadequate; blocks progress; needs rewrite |

**Scoring considers:** completeness, code examples, clarity, recency, searchability, and practical utility.

---

## Critical Gaps (Highest Priority)

### 1. REST API Endpoint Reference (Score: 1/5)
**Status:** Severely Inadequate
**Impact:** Blocks public release; unclear for frontend devs; no client library possible

**What's Missing:**
- No documentation for 111+ REST endpoints across 11 API modules
- No request/response examples or schemas
- No authentication/authorization details
- No error handling reference
- No rate limiting documentation
- No deprecation/versioning strategy

**Current State:**
- Code has routes in `/apps/api/dealbrain_api/api/` (admin, baseline, catalog, custom_fields, dashboard, entities, field_data, fields, health, imports, ingestion, listings, metrics, rankings, rules, settings)
- FastAPI auto-generates OpenAPI at `/docs` but no static documentation
- Some service usage docs exist (normalizer, event service, ruleset) but no endpoint reference

**What Should Be Documented:**
- All endpoints organized by domain (Listings, Catalog, Rules, Custom Fields, etc.)
- Request/response schemas with TypeScript types
- Authentication requirements and examples
- Error codes and HTTP status handling
- Rate limiting and pagination
- Practical curl/fetch examples
- WebSocket endpoints (if any)

**Effort:** 12 hours (1.5 hours per module × 8 modules)

**Recommended Outline:**
```
docs/api/
├── README.md (overview, authentication, base URL)
├── listings.md (CRUD, search, metrics)
├── catalog.md (CPU/GPU catalog endpoints)
├── rules.md (valuation rules CRUD)
├── custom-fields.md (dynamic fields)
├── imports.md (import jobs, status)
├── ingestion.md (URL normalization)
├── settings.md (application configuration)
├── dashboard.md (KPI endpoints)
├── entities.md (entity lookup)
└── admin.md (admin operations)
```

---

### 2. CONTRIBUTING.md (Score: 1/5)
**Status:** Missing
**Impact:** Blocks open source release; unclear contribution process

**What's Missing:**
- No contribution guidelines
- No code of conduct
- No pull request process
- No commit message conventions
- No testing requirements
- No branch naming conventions

**Current State:**
- README.md references CONTRIBUTING.md and CODE_OF_CONDUCT.md but files don't exist
- No issue templates
- No PR template
- CLAUDE.md exists but is internal (Claude AI agent instructions)

**What Should Be Documented:**
1. **Getting Started for Contributors**
   - Fork and clone instructions
   - Local environment setup
   - Running tests before submitting PR

2. **Code Standards**
   - Python: Black, isort, ruff (referenced in Makefile)
   - TypeScript: ESLint, Prettier (referenced in Makefile)
   - Run `make format && make lint` before commits
   - No console.log/print statements in production code

3. **Pull Request Process**
   - Create feature branch from main
   - Write tests for changes
   - Update documentation
   - Ensure CI passes
   - Provide PR description with context

4. **Commit Message Convention**
   - feat: New feature
   - fix: Bug fix
   - docs: Documentation updates
   - refactor: Code refactoring
   - test: Tests only
   - chore: Build, CI, etc.

5. **Testing Requirements**
   - Backend: pytest coverage > 70%
   - Frontend: Jest for logic, Playwright for E2E
   - Run `make test` before submitting

6. **Issue Reporting**
   - Bug template
   - Feature request template
   - Expected vs actual behavior

**Effort:** 4 hours

**Related Files to Create:**
- CONTRIBUTING.md (3 hours)
- CODE_OF_CONDUCT.md (0.5 hours)
- .github/ISSUE_TEMPLATE/bug.yml (0.3 hours)
- .github/ISSUE_TEMPLATE/feature.yml (0.2 hours)

---

### 3. Backend Development Guide (Score: 1/5)
**Status:** Missing
**Impact:** High friction for backend contributors; duplicated code patterns

**What's Missing:**
- No async/await patterns guide
- No SQLAlchemy/database patterns
- No validation/error handling patterns
- No logging best practices
- No database migration guide
- No service layer conventions
- No API endpoint development checklist

**Current State:**
- CLAUDE.md has high-level architecture but not development patterns
- Services layer exists (apps/api/dealbrain_api/services/) but no documentation
- Database models documented separately but not patterns
- Some API examples in codebase (technical/api/*.md) but not systematic

**What Should Be Documented:**
1. **Async Patterns**
   - When to use async vs sync
   - async context managers (session_scope)
   - Celery task patterns

2. **Database Operations**
   - Creating services for data access
   - Async SQLAlchemy session management
   - Pagination and filtering
   - Relationships and lazy loading

3. **API Development**
   - Creating FastAPI routers
   - Request validation with Pydantic
   - Response models
   - Dependency injection
   - Exception handling

4. **Domain Logic**
   - Placing logic in packages/core
   - Schema validation
   - Enum usage

5. **Testing**
   - Test fixtures and factories
   - Database test setup
   - API endpoint testing
   - Mocking external services

6. **Error Handling**
   - Custom exceptions
   - Error responses
   - Logging errors
   - Status codes

**Effort:** 8 hours

**Recommended Structure:**
```
docs/development/backend/
├── overview.md (architecture refresher)
├── async-patterns.md
├── database-guide.md
├── api-development.md
├── domain-logic.md
├── testing-guide.md
├── error-handling.md
└── migrations.md
```

---

### 4. Production Deployment Guide (Score: 1/5)
**Status:** Missing
**Impact:** No clear path to production; unclear environment configuration

**What's Missing:**
- No cloud deployment instructions (AWS, GCP, Azure, etc.)
- No SSL/TLS setup guide
- No database backup strategy
- No monitoring setup beyond local Prometheus
- No environment variable security guide
- No scaling considerations
- No zero-downtime deployment procedures
- No disaster recovery plan

**Current State:**
- Docker Compose exists for local development
- Infrastructure documentation sparse (only observability/logging-design.md)
- .env.example shows available variables but no deployment context
- No Dockerfile for production builds
- No Kubernetes manifests or helm charts

**What Should Be Documented:**
1. **Pre-Deployment Checklist**
   - Environment variables required
   - Database migration strategy
   - SSL certificate setup
   - Secrets management
   - Monitoring endpoints

2. **Cloud Deployment (pick 1-2)**
   - Docker Compose on VPS
   - AWS (ECS/RDS)
   - Railway or similar PaaS
   - Self-hosted with systemd

3. **Database & Backup**
   - PostgreSQL configuration
   - Backup frequency
   - Restore procedures
   - Monitoring disk space

4. **Observability**
   - Prometheus setup
   - Grafana dashboards
   - Log aggregation
   - Alert configuration

5. **Security**
   - API rate limiting
   - CORS configuration
   - Authentication tokens
   - Database encryption

6. **Maintenance**
   - Rolling deployments
   - Database migrations in production
   - Health checks
   - Log rotation

**Effort:** 6 hours

**Recommended Structure:**
```
docs/deployment/
├── README.md (overview)
├── prerequisites.md
├── docker-compose-vps.md
├── aws-ecs.md
├── environment-variables.md
├── database-backup.md
├── monitoring-setup.md
├── ssl-setup.md
└── troubleshooting.md
```

---

### 5. Frontend Development Guide (Score: 2/5)
**Status:** Minimal
**Impact:** Unclear component patterns; inconsistent implementations

**What's Missing:**
- No Next.js App Router patterns guide
- No React Query usage patterns
- No component composition patterns
- No state management guide
- No testing guide (Jest/React Testing Library)
- No styling/Tailwind conventions
- No performance optimization guide

**Current State:**
- Design System documentation exists (design/design-guidance.md)
- Architecture report mentions patterns (reports/codebase_analysis/04-frontend-architecture.md)
- Some component-specific ADRs exist (ADR-007, ADR-008, ADR-010)
- No centralized frontend development guide

**What Should Be Documented:**
1. **Project Structure**
   - app/ (pages and routes)
   - components/ (organized by domain)
   - hooks/ (custom hooks)
   - lib/ (utilities and API clients)
   - types/ (TypeScript interfaces)

2. **Component Patterns**
   - Functional components with TypeScript
   - Props interfaces
   - Composition over inheritance
   - Memoization usage (React.memo, useMemo)

3. **Data Fetching**
   - React Query hooks usage
   - Caching strategy
   - Error handling
   - Loading states
   - Pagination

4. **Forms & Validation**
   - Zod for validation
   - Form state management
   - Error display
   - Submission handling

5. **Testing**
   - Jest setup
   - React Testing Library
   - Playwright E2E tests
   - Mocking API calls

6. **Performance**
   - Code splitting
   - Image optimization
   - Debouncing (mentioned as 200ms search)
   - Virtual scrolling patterns

**Effort:** 6 hours

**Recommended Structure:**
```
docs/development/frontend/
├── setup.md
├── project-structure.md
├── component-patterns.md
├── data-fetching.md
├── forms.md
├── styling.md
├── testing.md
└── performance.md
```

---

## Important Gaps (Medium Priority)

### 6. CLI Tool Reference (Score: 2/5)
**Current State:** Brief mention in README, minimal detail
**Issue:** Users/developers don't know all CLI capabilities

**What Exists:**
```bash
poetry run dealbrain-cli --help     # Show all commands
poetry run dealbrain-cli add        # Add listing interactively
poetry run dealbrain-cli top        # Show top listings
poetry run dealbrain-cli explain    # Show valuation breakdown
poetry run dealbrain-cli export     # Export JSON
```

**What's Missing:**
- No detailed command reference
- No examples for each command
- No advanced usage scenarios
- No environment variable configuration
- No output format documentation

**Recommended Document:** `docs/cli-reference.md` (2-3 hours)

---

### 7. Troubleshooting & FAQ (Score: 1/5)
**Status:** Missing
**Impact:** New developers stuck on common problems; wasted time

**Common Issues Not Documented:**
- Database connection errors
- API URL configuration (localhost vs Docker IP)
- Port conflicts
- Poetry/pnpm version issues
- Migration failures
- Permission issues in Docker
- Environment variable mistakes
- Celery worker issues

**Recommended Document:** `docs/troubleshooting.md` (4 hours)

**Should Include:**
- Docker-specific issues
- Local development issues
- Database setup problems
- API connection issues
- Performance debugging
- Common code mistakes

---

### 8. Database Schema Reference (Score: 3/5)
**Current State:** Detailed in codebase analysis; could be more accessible
**Issue:** No quick ER diagram; schema changes scattered

**What Exists:**
- Detailed in `/docs/reports/codebase_analysis/05-database-schema.md`
- Model definitions in code
- Alembic migrations document changes

**What's Missing:**
- ER diagram (visual)
- Quick reference table
- Relationship documentation
- Migration guide (how to add new fields)
- Data type reference

**Recommended Document:** `docs/database-schema-reference.md` with ER diagram (3 hours)

---

### 9. Testing Strategy & Patterns (Score: 2/5)
**Current State:** Some test docs; no unified strategy
**Issue:** Unclear what to test; duplicated test code

**What Exists:**
- E2E test scenarios: `/docs/technical/testing/e2e-test-scenarios-baseline-hydration.md`
- Deferred tests: `/docs/technical/testing/baseline-deferred-tests.md`
- Some pytest fixtures in tests/conftest.py

**What's Missing:**
- Unit testing patterns
- Integration testing strategy
- Mock/fixture best practices
- Test coverage targets
- Running specific test suites
- Debugging failing tests

**Recommended Document:** `docs/development/testing-strategy.md` (4 hours)

---

### 10. Environment Variables Reference (Score: 2/5)
**Current State:** .env.example exists; no documentation
**Issue:** Unclear what each variable does; why it matters

**What Exists:**
- `.env.example` with variables
- Some mentioned in setup.md

**What's Missing:**
- Description of each variable
- Production vs development values
- Security implications
- Performance tuning variables
- Logging configuration

**Recommended Document:** `docs/environment-variables.md` (2 hours)

---

## Enhancement Opportunities (Lower Priority)

### 11. Glossary & Terminology (Score: 1/5)
**Issue:** Project uses domain-specific terms without definition
- "Valuation rules", "baseline", "rulesets", "action multipliers", "entity tooltips"
- New developers confused by terminology

**Recommended:** `docs/glossary.md` (2 hours)

---

### 12. Security Guide (Score: 1/5)
**What's Missing:**
- No authentication/authorization documentation
- No input validation guide
- No API security best practices
- No data sensitivity classification
- No incident response procedure

**Recommended:** `docs/security-guide.md` (3 hours)

---

### 13. Performance Optimization Guide (Score: 2/5)
**Current State:** Some ADRs mention optimization (virtual scrolling, memoization)
**What's Missing:**
- No unified performance guide
- No database query optimization
- No API response time targets
- No caching strategy
- No load testing procedures

**Recommended:** `docs/performance-guide.md` (3 hours)

---

### 14. Migration Guide (Score: 1/5)
**What's Missing:**
- No "upgrading to new version" guide
- No breaking change documentation
- No database schema upgrade procedures
- No API version migration guide

**Recommended:** `docs/migrations.md` (2 hours)

---

## Documentation Inventory Table

| File Path | Score | Type | Assessment | Priority |
|-----------|-------|------|------------|----------|
| README.md | 5/5 | Overview | Excellent overview, great quick start | ✅ |
| CLAUDE.md | 4/5 | Development | Good for Claude; new devs need more | ✅ |
| docs/README.md | 4/5 | Index | Great navigation; comprehensive | ✅ |
| docs/technical/setup.md | 2/5 | Setup | Very brief; needs expansion | ❌ |
| docs/technical/INSTALL_DEPS.md | 3/5 | Setup | Better; still missing some issues | ⚠️ |
| docs/technical/api/*.md | 3/5 | API | Service examples; missing endpoints | ⚠️ |
| docs/technical/testing/*.md | 2/5 | Testing | Deferred tests; missing patterns | ⚠️ |
| docs/architecture/*.md | 5/5 | Architecture | Excellent; comprehensive ADRs | ✅ |
| docs/design/*.md | 5/5 | Design | Complete system; thorough | ✅ |
| docs/user-guide/*.md | 4/5 | Features | Good; missing some edge cases | ✅ |
| docs/reports/*.md | 5/5 | Analysis | Deep dive; very complete | ✅ |
| docs/configuration/*.md | 3/5 | Config | URL ingestion covered; more needed | ⚠️ |
| CONTRIBUTING.md | 1/5 | Governance | **Missing** | ❌ CRITICAL |
| CODE_OF_CONDUCT.md | 1/5 | Governance | **Missing** | ❌ CRITICAL |
| docs/api/*.md | 1/5 | Reference | **Missing** | ❌ CRITICAL |
| docs/deployment/*.md | 1/5 | Operations | **Missing** | ❌ CRITICAL |
| docs/development/backend/*.md | 1/5 | Development | **Missing** | ❌ CRITICAL |
| docs/development/frontend/*.md | 2/5 | Development | Minimal; needs expansion | ⚠️ IMPORTANT |
| docs/troubleshooting.md | 1/5 | Support | **Missing** | ❌ CRITICAL |
| docs/cli-reference.md | 1/5 | Reference | **Missing** | ⚠️ IMPORTANT |
| docs/environment-variables.md | 1/5 | Reference | **Missing** | ⚠️ IMPORTANT |
| docs/testing-strategy.md | 1/5 | Development | **Missing** | ⚠️ IMPORTANT |
| docs/glossary.md | 1/5 | Reference | **Missing** | ⚠️ IMPORTANT |
| docs/security-guide.md | 1/5 | Security | **Missing** | ⚠️ IMPORTANT |
| docs/performance-guide.md | 1/5 | Performance | **Missing** | ⚠️ IMPORTANT |

---

## Refactoring Recommendations

### 1. Consolidate Setup Documentation
**Current:** Technical setup scattered (setup.md, INSTALL_DEPS.md, README references, CLAUDE.md)
**Recommendation:** Create unified `docs/development/getting-started.md` that references specific detailed docs

### 2. Organize Development Guides
**Current:** Mixed between CLAUDE.md, various ADRs, architecture reports
**Recommendation:** Create `docs/development/` with clear subsections:
- getting-started.md
- backend/
- frontend/
- testing/
- contributing.md

### 3. API Documentation Structure
**Current:** No API docs; users must read code
**Recommendation:** Create `/docs/api/` with:
- OpenAPI spec generation (already auto-generated in FastAPI)
- Static markdown reference
- Examples for common workflows

### 4. Cross-Reference Links
**Issue:** Many documents reference others but links are hard to find
**Recommendation:** Audit all relative links; ensure consistency from /docs/ directory

### 5. Add "Related Documents" Sections
**Issue:** Users don't know what else they should read
**Recommendation:** Add "Related Documents" or "Next Steps" sections to guides

---

## Public Release Checklist

**Documentation must be complete before public release:**

### Critical (Blocking Release)
- [ ] CONTRIBUTING.md exists and complete
- [ ] CODE_OF_CONDUCT.md exists
- [ ] REST API endpoint reference (all 111+ endpoints documented)
- [ ] Deployment guide for at least one platform
- [ ] README.md validated (all links working, accurate info)
- [ ] LICENSE file present and clear
- [ ] SECURITY.md for vulnerability reporting

### Important (Should Have)
- [ ] Getting started guide for new developers
- [ ] Backend development guide
- [ ] Frontend development guide
- [ ] Troubleshooting guide
- [ ] CLI reference guide
- [ ] Database schema reference with ER diagram
- [ ] Environment variables documented
- [ ] Testing strategy explained

### Nice to Have
- [ ] Glossary of terms
- [ ] Performance optimization guide
- [ ] Migration/upgrade guide
- [ ] Security best practices
- [ ] Examples/tutorials section

---

## Implementation Roadmap

### Phase 1: Public Release Blockers (Week 1-2 | 30 hours)
**Goal:** Unblock open source release

1. **CONTRIBUTING.md** (4 hours)
   - PR process, code standards, testing requirements
   - Day 1

2. **CODE_OF_CONDUCT.md** (1 hour)
   - Standard CoC adapted for project
   - Day 1

3. **REST API Reference** (12 hours)
   - Document all 111+ endpoints
   - Organize by domain (listings, rules, catalog, etc.)
   - Include examples and error handling
   - Days 2-5

4. **Production Deployment Guide** (6 hours)
   - One primary deployment method documented
   - Environment setup, secrets, monitoring
   - Days 5-6

5. **Backend Development Guide** (6 hours)
   - Async patterns, database, API development
   - Error handling, logging
   - Day 6-7

6. **Troubleshooting Guide** (4 hours)
   - Common setup issues
   - Database, Docker, port conflicts
   - Day 7

### Phase 2: Developer Onboarding (Week 3-4 | 20 hours)
**Goal:** Smooth new developer experience

1. **Frontend Development Guide** (6 hours)
   - Component patterns, data fetching, forms
   - Testing, styling
   - Day 8-9

2. **Testing Strategy** (4 hours)
   - Unit, integration, E2E patterns
   - Fixtures, mocking
   - Day 9-10

3. **Environment Variables Reference** (2 hours)
   - Document each variable, security implications
   - Day 10

4. **CLI Reference Guide** (2 hours)
   - Command details, examples, advanced usage
   - Day 10

5. **Getting Started Unified Doc** (3 hours)
   - Single entry point for new developers
   - Links to detailed docs
   - Day 11

6. **Database Schema Visual** (3 hours)
   - ER diagram
   - Quick reference
   - Day 11

### Phase 3: Polish & Optimization (Week 5 | 10 hours)
**Goal:** Comprehensive documentation

1. **Glossary** (2 hours)
   - Domain-specific terms explained
   - Day 12

2. **Security Guide** (3 hours)
   - Auth/authz, input validation, secrets
   - Day 12-13

3. **Performance Guide** (3 hours)
   - Database queries, caching, frontend optimization
   - Day 13

4. **Documentation Audit** (2 hours)
   - Validate all links, examples working
   - Verify accuracy
   - Day 14

---

## Estimated Timeline & Effort

| Phase | Duration | Effort | Owner |
|-------|----------|--------|-------|
| Phase 1: Blockers | 2 weeks | 30 hours | Documentation Writer |
| Phase 2: Onboarding | 2 weeks | 20 hours | Documentation Writer |
| Phase 3: Polish | 1 week | 10 hours | Documentation Writer |
| **Total** | **5 weeks** | **60 hours** | **8 days FTE** |

**Parallel work:** While documenting, code review for accuracy can be async.

---

## Key Recommendations

### Immediate Actions (This Week)
1. **Create docs/api/ directory** with endpoint reference template
2. **Write CONTRIBUTING.md** using standard template
3. **Start REST API documentation** (start with 3 most-used modules)
4. **Set up documentation review process** (require API docs with new endpoints)

### Process Improvements
1. **Enforce documentation in PRs** - No endpoint changes without doc updates
2. **Link documentation to code** - Docstrings should reference user docs
3. **Add docs to CI/CD** - Validate markdown links in automated tests
4. **Create documentation templates** - For new guides, API docs, ADRs

### Documentation Quality
1. **Assign doc reviewer** - Someone ensures quality before merge
2. **Set 3-month review cycle** - Update docs as code evolves
3. **Track broken links** - Automated scanning in CI
4. **Collect user feedback** - "Was this helpful?" in docs

---

## Success Metrics

Documentation will be considered **complete for public release** when:

- ✅ All 111+ REST endpoints documented with examples
- ✅ CONTRIBUTING.md exists and clear
- ✅ New backend developers can contribute without Slack questions
- ✅ New frontend developers can build components independently
- ✅ Deployment guide allows production deployment on chosen platform
- ✅ Troubleshooting guide answers 80%+ of common issues
- ✅ Zero broken documentation links
- ✅ All code examples tested and working

**Target: Documentation Gap Score increased to 85/100 (from 65/100)**

---

## Appendix: Quick Reference

### Most Critical Missing Docs
1. REST API endpoint reference (blocks public release)
2. CONTRIBUTING.md (blocks open source)
3. Production deployment guide (blocks production)
4. Backend development patterns (blocks contributor productivity)
5. Troubleshooting guide (blocks developer onboarding)

### Highest Impact Quick Wins
1. CONTRIBUTING.md (4 hours → unblocks contributors)
2. REST API reference for 3 most-used modules (6 hours → 50% of API documented)
3. Troubleshooting guide (4 hours → eliminates ~80% of support questions)

### Files to Create (in order of priority)
```
/docs/api/README.md                          # API overview
/docs/api/listings.md                        # Listing endpoints
/docs/api/rules.md                           # Rules endpoints
/docs/api/authentication.md                  # Auth details
/CONTRIBUTING.md                             # Contribution guide
/docs/deployment/README.md                   # Deployment overview
/docs/development/backend/README.md          # Backend guide
/docs/troubleshooting.md                     # Common issues
/docs/development/frontend/README.md         # Frontend guide
/docs/development/testing-strategy.md        # Testing guide
/CODE_OF_CONDUCT.md                          # Code of conduct
/docs/environment-variables.md               # Env var reference
/docs/cli-reference.md                       # CLI guide
```

### Review Existing Docs to Improve
```
docs/technical/setup.md                      # Expand with more troubleshooting
docs/README.md                               # Add links to new docs above
docs/reports/codebase_analysis/03-backend-architecture.md  # Reference from dev guide
docs/reports/codebase_analysis/04-frontend-architecture.md # Reference from dev guide
```

---

**Report Generated:** October 24, 2025
**Analysis Scope:** User-facing documentation (excluding /docs/project_plans/)
**Next Review:** December 2025 or after Phase 1 completion
