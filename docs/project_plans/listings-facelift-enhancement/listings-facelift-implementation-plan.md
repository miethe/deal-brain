# Implementation Plan: Listings Enhancement

**Project:** Listings Detail Page & Modal Enhancement
**Version:** 1.0 (Modular Structure)
**Date:** 2025-10-22
**Status:** Ready for Implementation
**Estimated Duration:** 7 weeks

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Documentation Structure](#documentation-structure)
3. [Technical Architecture](#technical-architecture)
4. [File Manifest](#file-manifest)
5. [Implementation Phases](#implementation-phases)
6. [Testing Strategy](#testing-strategy)
7. [Deployment Plan](#deployment-plan)
8. [Success Criteria](#success-criteria)

---

## Project Overview

### Goals

Transform the listings experience with four key improvements:

1. **Auto-close creation modal** - Streamline workflow by automatically closing modal after successful listing creation
2. **Smart rule display** - Show only top 4 contributing valuation rules in modal for clarity
3. **Enhanced breakdown modal** - Organize rules into contributors/inactive sections with navigation
4. **Rich detail page** - Complete redesign with product images, entity links, and tabbed layout

### Key Deliverables

- Auto-closing creation modal with list refresh and highlighting
- Filtered valuation tab showing max 4 contributing rules
- Enhanced valuation breakdown modal with sorting and clickable rules
- Complete detail page (`/listings/[id]`) with hero section and tabs
- Reusable entity link and tooltip components
- Comprehensive test coverage (unit, integration, accessibility)

### Dependencies

**Frontend:**
- Next.js 14 App Router
- React Query v5
- Radix UI primitives (Dialog, Tabs, HoverCard, Collapsible)
- shadcn/ui components
- Tailwind CSS 3+

**Backend:**
- FastAPI with async SQLAlchemy
- Existing `/v1/listings/{id}` endpoint
- Enhanced `/v1/listings/{id}/valuation-breakdown` endpoint
- Entity detail endpoints (`/v1/cpus/{id}`, `/v1/gpus/{id}`, etc.)

---

## Documentation Structure

### Modular Organization

This implementation plan is broken into multiple focused documents for better maintainability:

**Main Documents:**
- **[PRD.md](./PRD.md)** - Executive summary, goals, overview, and documentation index
- **[listings-facelift-implementation-plan.md](./listings-facelift-implementation-plan.md)** - This document (phases, tasks, timeline)
- **[SUCCESS_METRICS.md](./success-metrics.md)** - Metrics, measurement, and success criteria

**Requirements Documents** (in `requirements/` folder):
- **[auto-close-modal.md](./requirements/auto-close-modal.md)** - Feature 1: Auto-close behavior
- **[smart-rule-display.md](./requirements/smart-rule-display.md)** - Feature 2: Filter to top 4 rules
- **[enhanced-breakdown.md](./requirements/enhanced-breakdown.md)** - Feature 3: Organized modal
- **[detail-page.md](./requirements/detail-page.md)** - Feature 4: Rich detail page
- **[data-model.md](./requirements/data-model.md)** - API schemas, TypeScript interfaces
- **[technical.md](./requirements/technical.md)** - Component architecture, state management
- **[risks.md](./requirements/risks.md)** - Risk analysis and mitigation strategies

**Design Documents** (in `design/` folder):
- **[ui-ux.md](./design/ui-ux.md)** - Color palette, typography, spacing, component specs
- **[technical-design.md](./design/technical-design.md)** - Component hierarchy, data flow, error handling
- **[accessibility.md](./design/accessibility.md)** - WCAG AA compliance, keyboard navigation, screen readers
- **[performance.md](./design/performance.md)** - Caching strategy, optimization, Core Web Vitals

### How to Navigate

- **Planning:** Start with [PRD.md](./PRD.md) for overview
- **Requirements:** Deep-dive specific features in `requirements/` folder
- **Design:** Review `design/` folder for implementation details
- **Implementation:** Follow phases below with reference to detailed feature docs
- **Success:** Track against [success-metrics.md](./success-metrics.md)

---

## Technical Architecture

### Component Architecture

```
/listings/[id]/
├── page.tsx (Server Component)
│   ├── DetailPageLayout
│   │   ├── DetailPageHero
│   │   │   ├── ProductImage (with fallbacks)
│   │   │   └── SummaryCardsGrid
│   │   │       ├── PriceSummaryCard
│   │   │       ├── PerformanceSummaryCard
│   │   │       ├── HardwareSummaryCard
│   │   │       └── MetadataSummaryCard
│   │   └── DetailPageTabs
│   │       ├── SpecificationsTab
│   │       │   ├── HardwareSection (with EntityLinks)
│   │       │   ├── ProductDetailsSection
│   │       │   ├── PerformanceMetricsSection
│   │       │   └── CustomFieldsSection
│   │       ├── ValuationTab (reuses ListingValuationTab)
│   │       ├── HistoryTab
│   │       └── NotesTab (placeholder)
│   └── EntityTooltip (HoverCard wrapper)

Modal Components:
├── AddListingModal (enhanced with auto-close)
├── ListingValuationTab (enhanced with filtering)
└── ValuationBreakdownModal (enhanced with sections + navigation)

Reusable Components:
├── EntityLink (clickable link with optional tooltip)
├── EntityTooltip (hover card for CPU, GPU, RAM, Storage)
├── ProductImage (image with manufacturer-based fallbacks)
└── SummaryCard (reusable metric card)
```

**See [Technical Architecture](./design/technical-design.md) for detailed component data flow.**

### Data Flow

```
Creation Flow:
User submits form → API POST /v1/listings → Success (201)
  → React Query onSuccess callback
    → Close modal (200ms fade)
    → Invalidate queries: ['listings', 'records'], ['listings', 'count']
    → Refetch listings
    → Scroll to new item
    → Apply highlight animation (2s pulse)
    → Move focus to new item row
    → Show success toast

Detail Page Load:
Server Component → apiFetch(`/v1/listings/${id}`)
  → Eager load: CPU, GPU, RAM, Storage, Ports, Valuation Breakdown
  → Render hero + tabs
  → Client-side: Prefetch entity tooltips on hover

Valuation Breakdown:
Click "View Full Breakdown" → Open ValuationBreakdownModal
  → React Query fetch: `/v1/listings/${id}/valuation-breakdown`
  → Sort adjustments: contributors (by amount desc) + inactive (alphabetical)
  → Render sections with RuleGroup badges
  → Click rule name → Next.js navigate to `/valuation/rules/${ruleId}`
```

### API Enhancements

See [Data Model](./requirements/data-model.md) for complete schemas.

**Required Backend Changes:**

1. **Enhanced `/v1/listings/{id}` endpoint:**
   - Eager-load all relationships (CPU, GPU, RAM, Storage, Ports)
   - Include full entity data for tooltips (cores, TDP, marks, etc.)
   - Return 404 if listing not found

2. **Enhanced `/v1/listings/{id}/valuation-breakdown` endpoint:**
   - Add `rule_description` to each adjustment
   - Add `rule_group_id` and `rule_group_name` to each adjustment
   - Include ALL rules (active + inactive with zero adjustments)
   - Return parent ruleset information

---

## File Manifest

### New Files

**Frontend Components** (see [Technical Requirements](./requirements/technical.md#new-files)):

```
apps/web/components/listings/
├── detail-page-layout.tsx                      # Layout wrapper with hero and tabs
├── detail-page-hero.tsx                        # Hero section with image and summary cards
├── specifications-tab.tsx                      # Specifications tab content
├── valuation-tab-page.tsx                      # Valuation tab wrapper (reuses ListingValuationTab)
├── history-tab.tsx                             # History/audit log tab
├── notes-tab.tsx                               # Notes tab (placeholder)
├── entity-link.tsx                             # Reusable clickable entity link
├── entity-tooltip.tsx                          # Reusable entity hover tooltip (HoverCard)
├── product-image.tsx                           # Image with fallback handling
└── summary-card.tsx                            # Reusable summary card component
```

**App Router Pages:**

```
apps/web/app/listings/[id]/
├── page.tsx                                    # Enhanced detail page (server component)
├── loading.tsx                                 # Loading skeleton
└── not-found.tsx                               # 404 page
```

**Tests:**

```
apps/web/components/listings/__tests__/
├── entity-link.test.tsx                        # Entity link component tests
├── entity-tooltip.test.tsx                     # Entity tooltip tests
├── valuation-tab.test.tsx                      # Enhanced valuation tab tests
├── breakdown-modal.test.tsx                    # Enhanced breakdown modal tests
└── detail-page.test.tsx                        # Detail page integration tests
```

### Modified Files

**Frontend:**

```
apps/web/components/listings/
├── add-listing-modal.tsx                       # Add auto-close on success
├── add-listing-form.tsx                        # Call onSuccess callback with new listing ID
├── listing-valuation-tab.tsx                   # Add rule filtering logic (max 4)
└── valuation-breakdown-modal.tsx               # Add sections, sorting, clickable rules
```

**Backend:**

```
apps/api/dealbrain_api/
├── api/listings.py                             # Enhanced endpoints
└── services/listings.py                        # Eager-load relationships
```

---

## Implementation Phases

### Phase 1: Auto-Close Modal (Week 1)

**Objective:** Streamline creation workflow by auto-closing modal after successful listing creation.

**Key Tasks:**
- TASK-101: Modify AddListingForm to accept onSuccess callback
- TASK-102: Enhance AddListingModal auto-close logic
- TASK-103: Implement list refresh and highlight in listings page
- TASK-104: Focus management after modal close
- TASK-105: Add success toast notification

**Time Estimate:** 3 days

**See:** [Auto-Close Modal Feature](./requirements/auto-close-modal.md) for detailed requirements.

---

### Phase 2: Smart Rule Display (Week 1-2)

**Objective:** Filter valuation tab to show only top 4 contributing rules with clear hierarchy.

**Key Tasks:**
- TASK-201: Implement rule filtering logic in ListingValuationTab
- TASK-202: Update rule cards display with count indicator
- TASK-203: Add empty state for zero contributors
- TASK-204: Color-code adjustments (green/red)

**Time Estimate:** 2 days

**See:** [Smart Rule Display Feature](./requirements/smart-rule-display.md) for detailed requirements.

---

### Phase 3: Enhanced Breakdown Modal (Week 2-3)

**Objective:** Reorganize breakdown modal with contributors/inactive sections, clickable rules, and RuleGroup badges.

**Key Tasks:**
- TASK-301: Backend - Enhance valuation breakdown endpoint
- TASK-302: Backend - Eager-load rule metadata
- TASK-303: Frontend - Implement sorting logic
- TASK-304: Frontend - Add section headers and separators
- TASK-305: Frontend - Add RuleGroup badges
- TASK-306: Frontend - Make rule names clickable
- TASK-307: Frontend - Implement collapsible section
- TASK-308: Frontend - Add hover tooltips

**Time Estimate:** 5 days

**See:** [Enhanced Valuation Breakdown Feature](./requirements/enhanced-breakdown.md) for detailed requirements.

---

### Phase 4: Detail Page Foundation (Week 3-4)

**Objective:** Create basic detail page structure with hero section, breadcrumbs, and tab navigation.

**Key Tasks:**
- TASK-401: Backend - Enhance /v1/listings/{id} endpoint with eager loading
- TASK-402: Create detail page route
- TASK-403: Create loading skeleton
- TASK-404: Create 404 not-found page
- TASK-405: Create DetailPageLayout component
- TASK-406: Create breadcrumb navigation
- TASK-407: Create DetailPageHero component
- TASK-408: Create ProductImage component
- TASK-409: Create tab navigation component
- TASK-410: Implement responsive design

**Time Estimate:** 5 days

**See:** [Detail Page Feature](./requirements/detail-page.md) for detailed requirements.

---

### Phase 5: Entity Links & Tooltips (Week 4-5)

**Objective:** Implement clickable entity relationships with hover tooltips for rich contextual information.

**Key Tasks:**
- TASK-501: Create SummaryCard component
- TASK-502: Create summary cards grid in hero
- TASK-503: Create EntityLink component
- TASK-504: Create EntityTooltip component
- TASK-505: Implement CPU tooltip
- TASK-506: Implement GPU tooltip
- TASK-507: Implement RAM Spec tooltip
- TASK-508: Implement Storage Profile tooltip
- TASK-509: Backend - Verify entity detail endpoints

**Time Estimate:** 5 days

---

### Phase 6: Specifications & Valuation Tabs (Week 5-6)

**Objective:** Build specifications tab with entity links and integrate valuation tab into detail page.

**Key Tasks:**
- TASK-601: Create SpecificationsTab component
- TASK-602: Implement Hardware section
- TASK-603: Implement Product Details section
- TASK-604: Implement Listing Info section
- TASK-605: Implement Performance Metrics section
- TASK-606: Implement Metadata section
- TASK-607: Implement Custom Fields section
- TASK-608: Handle null/missing values
- TASK-609: Create ValuationTabPage component
- TASK-610: Create HistoryTab component
- TASK-611: Create NotesTab component (placeholder)

**Time Estimate:** 5 days

---

### Phase 7: Polish & Testing (Week 6-7)

**Objective:** Accessibility audit, performance optimization, cross-browser testing, and comprehensive test coverage.

**Key Tasks:**
- TASK-701: Accessibility audit with axe-core
- TASK-702: Keyboard navigation testing
- TASK-703: Performance optimization
- TASK-704: Cross-browser testing
- TASK-705: Responsive testing on real devices
- TASK-706: Write unit tests for new components
- TASK-707: Write integration tests for flows
- TASK-708: Visual regression testing
- TASK-709: Performance benchmarking
- TASK-710: User acceptance testing
- TASK-711: Update documentation

**Time Estimate:** 7 days

**See:** [Testing Strategy](#testing-strategy) for detailed testing approach.

---

## Testing Strategy

### Unit Tests

**Target Coverage:** >80% for new components

**Test Framework:** Jest + React Testing Library

See [Testing Strategy - Unit Tests](./requirements/technical.md#testing-strategy) for detailed test cases.

### Integration Tests

**Test Scenarios:**

1. **Creation Flow** - Form submit → modal close → list refresh → highlight
2. **Detail Page Navigation** - Click listing → navigate → page render
3. **Tab Switching** - Click tab → URL update → content change
4. **Entity Link Navigation** - Click entity link → navigate to detail page
5. **Entity Tooltip Display** - Hover link → tooltip appears → data displays
6. **Valuation Breakdown Flow** - Click button → modal opens → sections display → rule click navigates

### Accessibility Tests

- Automated: axe-core in CI
- Manual keyboard navigation (Tab, Enter, Space, Arrow keys)
- Screen reader testing (NVDA, JAWS, VoiceOver)
- Color contrast verification
- Touch target validation

See [Accessibility Guidelines](./design/accessibility.md) for detailed requirements.

### Performance Tests

**Metrics:**
- LCP: < 2.5s (75th percentile)
- FID: < 100ms (75th percentile)
- CLS: < 0.1 (75th percentile)
- API p95: < 500ms

See [Performance Optimization](./design/performance.md) for detailed strategy.

---

## Deployment Plan

### Pre-Deployment Checklist

- [ ] All tests passing (unit, integration, accessibility)
- [ ] Performance benchmarks met (LCP < 2.5s, API < 500ms)
- [ ] Cross-browser testing completed
- [ ] Responsive testing on real devices completed
- [ ] User acceptance testing completed
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Database migrations prepared (if any)
- [ ] Feature flags configured (if applicable)

### Deployment Steps

**Backend Deployment:**

1. Deploy API changes (if any schema changes, apply migrations first)
2. Verify endpoints return enhanced data
3. Test valuation breakdown endpoint with rule metadata

**Frontend Deployment:**

1. Build Next.js app: `pnpm build`
2. Deploy to production (e.g., Vercel)
3. Verify detail page loads
4. Test end-to-end flows

See [Deployment Plan](./requirements/technical.md#deployment-considerations) for detailed steps.

---

## Success Criteria

### Functional Completeness

- [x] Creation modal auto-closes on success with visual confirmation
- [x] Valuation tab shows max 4 contributing rules with clear hierarchy
- [x] Breakdown modal organizes rules into contributors and inactive sections
- [x] Rule names are clickable and navigate to rule detail pages
- [x] Detail page displays comprehensive listing information with tabs
- [x] Product images load with appropriate fallbacks
- [x] Entity relationships are clickable with hover tooltips
- [x] All tabs (Specifications, Valuation, History) are functional
- [x] Responsive design works across all breakpoints

### Quality Standards

- [x] Accessibility requirements met (WCAG AA, keyboard navigation, screen reader)
- [x] Performance targets achieved (LCP < 2.5s, API < 500ms p95)
- [x] All automated tests passing (unit, integration, accessibility)
- [x] Cross-browser testing completed (Chrome, Firefox, Safari)
- [x] User acceptance testing completed with no critical issues

See [Success Metrics](./success-metrics.md) for detailed measurement and post-launch tracking.

---

**End of Implementation Plan**

**Version History:**
- v1.0 (2025-10-22): Initial implementation plan
- v1.1 (2025-10-23): Refactored into modular structure with linked documentation

**Review & Approval:**
- Technical Lead: [Pending]
- Product Owner: [Pending]
- Backend Engineer: [Pending]
- Frontend Engineer: [Pending]
