# Listings Detail Page & Modal Enhancement - Progress Tracker

**Project**: Listings Facelift Enhancement
**PRD**: `docs/project_plans/listings-facelift-enhancement/PRD.md`
**Implementation Plan**: `docs/project_plans/listings-facelift-enhancement/IMPLEMENTATION_PLAN.md`
**Status**: Planning Complete - Ready for Implementation
**Start Date**: TBD
**Target Completion**: 6-7 weeks from start

---

## Overview

Comprehensive enhancement to Deal Brain's listings display system with four key improvements:
1. **Auto-Close Creation Modal** - Seamless UX after listing creation
2. **Smart Rule Display** - Show only top 4 contributing rules in modal
3. **Enhanced Valuation Breakdown** - Organized, clickable, labeled breakdown screen
4. **Complete Detail Page Redesign** - Rich, comprehensive listing detail view

---

## Phase Status

| Phase | Description | Status | Start | End | Progress |
|-------|-------------|--------|-------|-----|----------|
| Phase 1 | Auto-Close Creation Modal | ⏸️ Not Started | - | - | 0/5 tasks |
| Phase 2 | Smart Rule Display | ⏸️ Not Started | - | - | 0/4 tasks |
| Phase 3 | Enhanced Valuation Breakdown | ⏸️ Not Started | - | - | 0/8 tasks |
| Phase 4 | Detail Page Foundation | ⏸️ Not Started | - | - | 0/10 tasks |
| Phase 5 | Entity Links & Tooltips | ⏸️ Not Started | - | - | 0/9 tasks |
| Phase 6 | Specifications & Valuation Tabs | ⏸️ Not Started | - | - | 0/11 tasks |
| Phase 7 | Polish & Testing | ⏸️ Not Started | - | - | 0/11 tasks |

**Overall Progress**: 0/57 tasks completed (0%)

---

## Phase 1: Auto-Close Creation Modal (Week 1)

**Objectives**: Implement auto-close behavior for listing creation modal with list refresh and highlighting.

**Status**: ⏸️ Not Started
**Progress**: 0/5 tasks

### Tasks

- [ ] **TASK-101**: Update create listing mutation with onSuccess callback
  - File: `apps/web/hooks/use-listings.ts`
  - Acceptance: Modal closes on successful creation

- [ ] **TASK-102**: Implement list invalidation and refetch logic
  - File: `apps/web/hooks/use-listings.ts`
  - Acceptance: List refreshes automatically after creation

- [ ] **TASK-103**: Add highlighting for newly created listing
  - Files: `apps/web/components/listings/listing-card.tsx`, `apps/web/app/listings/page.tsx`
  - Acceptance: New listing highlighted for 3 seconds

- [ ] **TASK-104**: Add success toast notification
  - File: Component using create modal
  - Acceptance: Toast appears with "Listing created successfully"

- [ ] **TASK-105**: Implement error handling and user feedback
  - File: `apps/web/hooks/use-listings.ts`
  - Acceptance: Errors show toast, modal stays open for retry

---

## Phase 2: Smart Rule Display (Week 1-2)

**Objectives**: Filter valuation rules to show only top 4 contributors, hide inactive rules.

**Status**: ⏸️ Not Started
**Progress**: 0/4 tasks

### Tasks

- [ ] **TASK-201**: Add sorting logic for rules by absolute adjustment value
  - File: `apps/web/components/listings/listing-valuation-tab.tsx`
  - Acceptance: Rules sorted by |adjustment|, top 4 shown

- [ ] **TASK-202**: Implement "Show All Rules" toggle in valuation tab
  - File: `apps/web/components/listings/listing-valuation-tab.tsx`
  - Acceptance: Toggle reveals all rules with smooth transition

- [ ] **TASK-203**: Update rule card styling for better visual hierarchy
  - File: `apps/web/components/listings/listing-valuation-tab.tsx`
  - Acceptance: Color-coded cards with clear deductions/additions

- [ ] **TASK-204**: Add unit tests for rule filtering logic
  - File: `apps/web/components/listings/__tests__/listing-valuation-tab.test.tsx`
  - Acceptance: Tests cover sorting, filtering, toggle behavior

---

## Phase 3: Enhanced Valuation Breakdown (Week 2-3)

**Objectives**: Reorganize breakdown modal with sorted sections, clickable rules, RuleGroup labels.

**Status**: ⏸️ Not Started
**Progress**: 0/8 tasks

### Tasks

- [ ] **TASK-301**: Enhance backend API with rulesets and rule_groups data
  - File: `apps/api/dealbrain_api/api/listings.py`
  - Acceptance: API returns ruleset_name, rule_group_name per rule

- [ ] **TASK-302**: Update ValuationBreakdownResponse schema
  - File: `apps/api/dealbrain_api/schemas/listings.py`
  - Acceptance: Schema includes new fields

- [ ] **TASK-303**: Create section headers for "Top Contributors" and "All Rules"
  - File: `apps/web/components/listings/valuation-breakdown-modal.tsx`
  - Acceptance: Visual separation between sections

- [ ] **TASK-304**: Implement sorting logic (contributors at top, rest alphabetical)
  - File: `apps/web/components/listings/valuation-breakdown-modal.tsx`
  - Acceptance: Rules sorted correctly in both sections

- [ ] **TASK-305**: Add RuleGroup/Ruleset badges to rule cards
  - File: `apps/web/components/listings/valuation-breakdown-modal.tsx`
  - Acceptance: Badges show on each rule card

- [ ] **TASK-306**: Make rule names clickable (link to rule detail)
  - File: `apps/web/components/listings/valuation-breakdown-modal.tsx`
  - Acceptance: Click opens rule detail (future: modal/page)

- [ ] **TASK-307**: Add hover states and improved visual hierarchy
  - File: `apps/web/components/listings/valuation-breakdown-modal.tsx`
  - Acceptance: Clear hover states, accessible interactions

- [ ] **TASK-308**: Write integration tests for enhanced breakdown
  - File: `apps/web/components/listings/__tests__/valuation-breakdown-modal.test.tsx`
  - Acceptance: Tests cover sorting, badges, interactions

---

## Phase 4: Detail Page Foundation (Week 3-4)

**Objectives**: Build core detail page structure with hero, tabs, and responsive layout.

**Status**: ⏸️ Not Started
**Progress**: 0/10 tasks

### Tasks

- [ ] **TASK-401**: Create detail page route and server component
  - File: `apps/web/app/listings/[id]/page.tsx`
  - Acceptance: Route renders with basic layout

- [ ] **TASK-402**: Implement breadcrumb navigation
  - File: `apps/web/components/listings/listing-breadcrumbs.tsx`
  - Acceptance: Home > Listings > [Title] breadcrumb trail

- [ ] **TASK-403**: Build hero section with title, pricing, and image
  - File: `apps/web/components/listings/listing-hero.tsx`
  - Acceptance: Responsive hero with all key elements

- [ ] **TASK-404**: Create tab navigation component
  - File: `apps/web/components/listings/listing-tabs.tsx`
  - Acceptance: Tabs for Overview, Specs, Valuation, History

- [ ] **TASK-405**: Implement tab content routing with URL params
  - File: `apps/web/app/listings/[id]/page.tsx`
  - Acceptance: ?tab=specs changes active tab

- [ ] **TASK-406**: Add fallback image logic (manufacturer/form factor icons)
  - File: `apps/web/components/listings/listing-image.tsx`
  - Acceptance: Shows image or appropriate fallback icon

- [ ] **TASK-407**: Create responsive grid layout for detail sections
  - File: `apps/web/app/listings/[id]/page.tsx`
  - Acceptance: Desktop 2-col, mobile stacked layout

- [ ] **TASK-408**: Add loading states and skeleton screens
  - File: `apps/web/app/listings/[id]/loading.tsx`
  - Acceptance: Smooth loading experience

- [ ] **TASK-409**: Implement error boundary and 404 handling
  - File: `apps/web/app/listings/[id]/error.tsx`
  - Acceptance: Graceful error handling

- [ ] **TASK-410**: Style detail page with Deal Brain design system
  - Files: Multiple component files
  - Acceptance: Consistent with existing design patterns

---

## Phase 5: Entity Links & Tooltips (Week 4-5)

**Objectives**: Make CPU/GPU/RAM/Storage clickable with hover tooltips showing details.

**Status**: ⏸️ Not Started
**Progress**: 0/9 tasks

### Tasks

- [ ] **TASK-501**: Create entity link component with hover tooltip
  - File: `apps/web/components/listings/entity-link.tsx`
  - Acceptance: Reusable component for all entities

- [ ] **TASK-502**: Enhance CPU tooltip with full details
  - File: `apps/web/components/listings/cpu-tooltip.tsx`
  - Acceptance: Shows all CPU fields (cores, threads, TDP, etc.)

- [ ] **TASK-503**: Create GPU tooltip component
  - File: `apps/web/components/listings/gpu-tooltip.tsx`
  - Acceptance: Shows GPU specs on hover

- [ ] **TASK-504**: Create RAM spec tooltip component
  - File: `apps/web/components/listings/ram-tooltip.tsx`
  - Acceptance: Shows module count, capacity, speed, generation

- [ ] **TASK-505**: Create storage profile tooltip component
  - File: `apps/web/components/listings/storage-tooltip.tsx`
  - Acceptance: Shows interface, form factor, performance tier

- [ ] **TASK-506**: Integrate entity links in specifications tab
  - File: `apps/web/components/listings/listing-specifications-tab.tsx`
  - Acceptance: All entities are clickable with tooltips

- [ ] **TASK-507**: Implement click navigation to entity detail pages
  - File: `apps/web/components/listings/entity-link.tsx`
  - Acceptance: Click goes to /cpus/[id], /gpus/[id], etc.

- [ ] **TASK-508**: Add keyboard navigation for tooltips
  - File: `apps/web/components/listings/entity-link.tsx`
  - Acceptance: Tab navigation, Escape to close

- [ ] **TASK-509**: Write accessibility tests for entity interactions
  - File: `apps/web/components/listings/__tests__/entity-link.test.tsx`
  - Acceptance: WCAG AA compliant, screen reader friendly

---

## Phase 6: Specifications & Valuation Tabs (Week 5-6)

**Objectives**: Build complete specifications and valuation tabs on detail page.

**Status**: ⏸️ Not Started
**Progress**: 0/11 tasks

### Tasks

- [ ] **TASK-601**: Create specifications tab component
  - File: `apps/web/components/listings/listing-specifications-tab.tsx`
  - Acceptance: Organized sections for all specs

- [ ] **TASK-602**: Organize specs into logical sections (Hardware, Storage, Metadata, etc.)
  - File: `apps/web/components/listings/listing-specifications-tab.tsx`
  - Acceptance: Clear visual grouping

- [ ] **TASK-603**: Add ports profile display with icons
  - File: `apps/web/components/listings/ports-display.tsx`
  - Acceptance: USB-A, USB-C, HDMI, DP counts with icons

- [ ] **TASK-604**: Display custom field values from attributes
  - File: `apps/web/components/listings/listing-specifications-tab.tsx`
  - Acceptance: All custom fields shown in appropriate section

- [ ] **TASK-605**: Create valuation tab on detail page
  - File: `apps/web/components/listings/listing-detail-valuation-tab.tsx`
  - Acceptance: Same functionality as modal valuation tab

- [ ] **TASK-606**: Integrate existing ListingValuationTab logic
  - File: `apps/web/components/listings/listing-detail-valuation-tab.tsx`
  - Acceptance: Override controls, breakdown button work

- [ ] **TASK-607**: Add history tab for provenance tracking
  - File: `apps/web/components/listings/listing-history-tab.tsx`
  - Acceptance: Shows created_at, updated_at, import source

- [ ] **TASK-608**: Display listing status and seller info
  - File: `apps/web/components/listings/listing-specifications-tab.tsx`
  - Acceptance: Status badge, seller name if available

- [ ] **TASK-609**: Add "Edit Listing" action button on detail page
  - File: `apps/web/app/listings/[id]/page.tsx`
  - Acceptance: Button opens edit modal

- [ ] **TASK-610**: Implement responsive layout for all tabs
  - Files: All tab components
  - Acceptance: Desktop/tablet/mobile layouts work

- [ ] **TASK-611**: Write integration tests for tab functionality
  - File: `apps/web/app/listings/[id]/__tests__/page.test.tsx`
  - Acceptance: Tab switching, data display, interactions tested

---

## Phase 7: Polish & Testing (Week 6-7)

**Objectives**: Accessibility audit, performance optimization, comprehensive testing, documentation.

**Status**: ⏸️ Not Started
**Progress**: 0/11 tasks

### Tasks

- [ ] **TASK-701**: Run accessibility audit with axe-core
  - Acceptance: No WCAG AA violations

- [ ] **TASK-702**: Test with screen readers (NVDA, JAWS, VoiceOver)
  - Acceptance: All content accessible via screen reader

- [ ] **TASK-703**: Optimize component rendering with React.memo
  - Files: All listing components
  - Acceptance: No unnecessary re-renders

- [ ] **TASK-704**: Implement image lazy loading and optimization
  - File: `apps/web/components/listings/listing-image.tsx`
  - Acceptance: Images load efficiently

- [ ] **TASK-705**: Run Lighthouse performance audit
  - Acceptance: Performance score >90, LCP <2.5s

- [ ] **TASK-706**: Cross-browser testing (Chrome, Firefox, Safari, Edge)
  - Acceptance: Consistent behavior across browsers

- [ ] **TASK-707**: Mobile device testing (iOS, Android)
  - Acceptance: Touch interactions work smoothly

- [ ] **TASK-708**: Write end-to-end tests with Playwright
  - File: `apps/web/e2e/listings-detail.spec.ts`
  - Acceptance: Complete user flows tested

- [ ] **TASK-709**: Update component documentation and Storybook
  - Files: All new components
  - Acceptance: Stories for all components

- [ ] **TASK-710**: Update user guide with new features
  - File: `docs/user-guide.md`
  - Acceptance: Screenshots and instructions for new features

- [ ] **TASK-711**: Conduct final review and sign-off
  - Acceptance: All acceptance criteria met, stakeholder approval

---

## Metrics & Success Criteria

### Functional Completeness
- [ ] All 57 tasks completed
- [ ] All acceptance criteria met
- [ ] All phases deployed to production

### Quality Standards
- [ ] Unit test coverage >80%
- [ ] Zero accessibility violations (WCAG AA)
- [ ] Lighthouse performance score >90
- [ ] No critical bugs in production

### User Adoption
- [ ] Detail page views increase by >50%
- [ ] Average session time on detail page >2 minutes
- [ ] Modal interaction time reduced by >30%
- [ ] User feedback score >4.5/5

---

## Notes

- Update this tracker as tasks are completed
- Mark phases as "In Progress" when work begins
- Add actual dates when phases start/end
- Document any blockers or risks in this section
- Link to related PRs and commits

---

**Last Updated**: 2025-10-22
**Updated By**: Claude Code (Initial Planning)
