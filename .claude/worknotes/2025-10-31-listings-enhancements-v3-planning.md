# Listings Enhancements v3 - Planning Session

**Date:** 2025-10-31
**Session Type:** Planning & Design
**Status:** Complete

## Summary

Completed comprehensive planning for Listings Enhancements v3 initiative. Created PRD and Implementation Plan for four major enhancement areas: performance optimization, UX improvements, CPU metrics layout, and image management system.

## Actions Taken

### 1. Codebase Analysis
- Explored current listings architecture using Explore agent
- Analyzed backend (models, services, API endpoints)
- Analyzed frontend (pages, components, state management)
- Identified performance optimizations already in place
- Documented image handling and valuation display systems

### 2. Document Creation

**PRD Created:** `/docs/project_plans/listings-enhancements-v3/PRD.md`
- Comprehensive product requirements for all 4 enhancement areas
- User stories with acceptance criteria
- Detailed UI/UX specifications
- Technical architecture considerations
- Success metrics and KPIs
- Risk analysis and mitigation strategies

**Implementation Plan Created:** `/docs/project_plans/listings-enhancements-v3/IMPLEMENTATION_PLAN.md`
- 20 detailed implementation tasks across 4 phases
- Effort estimates (196 total hours)
- Code examples for all major components
- Database migration specifications
- API endpoint specifications
- Testing strategy and benchmarks
- Deployment plan with rollback procedures

**Tracking Document:** `.claude/progress/listings-enhancements-v3.md`
- Task-level tracking structure
- Milestone definitions
- Success metrics tracking
- Risk monitoring

## Key Learnings

### Architecture Insights

1. **Existing Optimizations:**
   - ValuationCell and DualMetricCell already use React.memo
   - Search debounced at 200ms
   - Column resize debounced at 150ms
   - React Query caching (5-min stale time)

2. **Opportunities:**
   - No virtualization currently implemented (big win potential)
   - Hardcoded image fallback logic (maintenance burden)
   - No tooltips for adjusted value explanation
   - CPU metrics separated (usability issue)

3. **Data Flow:**
   - Valuation breakdown stored as JSON in database
   - Settings managed via ApplicationSettings model
   - Performance metrics calculated server-side
   - Image URLs extracted from raw_listing_json

### Design Decisions

1. **Virtualization:**
   - Use @tanstack/react-virtual (consistent with existing stack)
   - Auto-enable at 100+ rows
   - Maintain scroll position during operations

2. **Image Management:**
   - JSON config file (better TypeScript integration than YAML)
   - 7-level fallback hierarchy
   - Self-service workflow for non-technical users

3. **CPU Metrics:**
   - Reuse existing DualMetricCell pattern
   - Store thresholds in ApplicationSettings (consistent pattern)
   - CSS variables for color coding (theme support)

4. **Tooltips:**
   - Reusable ValuationTooltip component
   - 100ms delay before showing
   - Keyboard accessible (Tab, Enter, Escape)

## Technical Specifications

### Database Changes
- New setting: `cpu_mark_thresholds` in ApplicationSettings
- No schema changes to Listing model (reuse existing fields)

### API Changes
- New endpoint: `GET /v1/listings/paginated` (cursor-based)
- New endpoint: `GET /v1/settings/cpu_mark_thresholds`

### Frontend Changes
- New components: ValuationTooltip, PerformanceMetricDisplay
- Modified components: ListingsTable, DetailPageLayout, SpecificationsTab, ProductImageDisplay
- New utilities: image-resolver.ts, cpu-mark-utils.ts
- New hook: useCpuMarkThresholds

### Configuration
- New file: `apps/web/config/product-images.json`
- Directory restructure: `/public/images/{manufacturers,cpu-vendors,form-factors,fallbacks}`

## Effort Estimates

- **Phase 1 (Performance):** 72 hours (9 days)
- **Phase 2 (Adjusted Value):** 28 hours (3.5 days)
- **Phase 3 (CPU Metrics):** 44 hours (5.5 days)
- **Phase 4 (Image Management):** 52 hours (6.5 days)
- **Total:** 196 hours (24.5 days, ~6-8 weeks with testing)

## Success Metrics Targets

- Data tab interaction latency: <200ms (P95) for 1,000 listings
- Scroll FPS: 60fps with virtualization
- Tooltip engagement: >40% of users
- Support tickets (pricing questions): 15/month → <2/month
- Time to add manufacturer image: 30 min → <5 min

## Risks Identified

1. **Virtualization breaks row selection** (Medium/High)
   - Mitigation: Thorough testing, feature flag

2. **Performance degradation on mobile** (Medium/High)
   - Mitigation: Low-end device testing, RUM monitoring

3. **Image config file grows too large** (Low/Medium)
   - Mitigation: File size limits, lazy loading

## Next Steps

1. Team assignment (frontend lead, backend engineer, QA)
2. Kickoff meeting to review PRD and Implementation Plan
3. Sprint planning (break into 2-week sprints)
4. Set up feature branches and flags
5. Begin Phase 1 implementation

## Files Modified

### Created
- `/docs/project_plans/listings-enhancements-v3/PRD.md`
- `/docs/project_plans/listings-enhancements-v3/IMPLEMENTATION_PLAN.md`
- `/.claude/progress/listings-enhancements-v3.md`
- `/.claude/worknotes/2025-10-31-listings-enhancements-v3-planning.md`

### Deleted
- `/docs/project_plans/requests/needs-designed/10-24.md` (will be removed in commit)

## Context for Future Sessions

- All architecture analysis completed via Explore agent
- Existing performance optimizations documented
- Reusable patterns identified (DualMetricCell, ValuationCell, ApplicationSettings)
- Feature flags recommended for gradual rollout
- Critical path: PERF-002, UX-002, METRICS-002, IMG-003

---

**Session Duration:** ~2 hours
**Quality Check:** ✅ PRD comprehensive, Implementation Plan detailed with code examples, tracking structure in place
