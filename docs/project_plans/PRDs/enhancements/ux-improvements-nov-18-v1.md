---
title: "UX Improvements & Data Enhancement - November 18th - PRD"
description: "Comprehensive UX improvements including listing workflow enhancements, data presentation upgrades, import capabilities, and critical UI bug fixes"
audience: [ai-agents, developers, pm]
tags: [ux, import, data-presentation, workflow, bug-fixes, enhancements]
created: 2025-11-18
updated: 2025-11-18
category: "product-planning"
status: draft
related:
  - /docs/project_plans/requests/needs-designed/11-18.md
---

# UX Improvements & Data Enhancement - PRD

**Feature Name**: UX Improvements & Data Enhancement - November 18th
**Date**: 2025-11-18
**Author**: Claude (Sonnet 4.5)
**Status**: Draft
**Priority**: High
**Related**: Enhancement Request Doc (docs/project_plans/requests/needs-designed/11-18.md)

---

## 1. Executive Summary

This PRD addresses a comprehensive set of user experience improvements, data import enhancements, and critical UI bug fixes identified on November 18th. The enhancements span four key areas: (1) improved Amazon import data extraction, (2) streamlined listing management workflows, (3) enhanced data presentation and filtering capabilities, and (4) resolution of UI interaction bugs.

**Expected Impact**:
- **User Productivity**: 40-60% reduction in clicks/time for common listing edit workflows
- **Data Quality**: 50-70% improvement in auto-populated fields from Amazon imports
- **Discoverability**: Enhanced filtering and column customization improves data exploration
- **User Satisfaction**: Resolution of frustrating UI bugs (sliders, hidden rows) improves overall UX

**Scope**: 11 distinct enhancements grouped into 4 themes with 6 implementation phases

---

## 2. Context & Background

### Current State

**Import Functionality**:
- Amazon imports (without API key) populate minimal fields despite data availability on product pages
- Product titles/descriptions contain extractable data (CPU, RAM, manufacturer) not currently captured
- Manual field entry required for most Amazon imports, reducing efficiency

**Listing Management**:
- Quick edit modal exists but has limited field coverage
- Users must navigate away from view modal to quick edit modal (extra clicks)
- Full listing view page lacks direct edit button (non-intuitive)
- Adding/importing listings requires manual page refresh to see updates
- Valuation changes require manual recalculation task execution

**Data Presentation**:
- CPU catalog page (/cpus) lacks sorting capabilities
- No ability to filter CPUs by listing availability or popularity
- List views have fixed column sets - users cannot customize visible fields
- Column preferences not persisted across sessions

**UI Bugs**:
- Range sliders (e.g., CPU filters) show single handle; min/max selection unintuitive
- Table list views hide first row behind sticky header, requiring scroll for visibility

### Problem Statement

1. **Data Import Inefficiency**: Amazon imports require excessive manual data entry due to incomplete field population, despite data availability
2. **Workflow Friction**: Listing editing requires multiple navigation steps and lacks intuitive access points
3. **Limited Flexibility**: Users cannot customize data views or sort/filter by relevant criteria
4. **UX Frustrations**: Critical UI bugs impede usability and create confusion

---

## 3. Goals & Success Metrics

### Goals

**G1: Improve Import Data Quality**
- Increase auto-populated fields for Amazon imports from ~20% to 70%+
- Extract structured data from product titles/descriptions using NLP when needed

**G2: Streamline Listing Workflows**
- Reduce clicks to edit listing from view state: 3 clicks → 1 click
- Enable real-time UI updates on listing add/edit (eliminate manual refresh)
- Provide quick access to key field edits (CPU, RAM, Storage, GPU) from any context

**G3: Enhance Data Exploration**
- Enable comprehensive sorting on CPU catalog
- Support filtering by listing availability and popularity metrics
- Allow users to customize visible columns across all entity list views

**G4: Resolve Critical UI Bugs**
- Implement dual-handle range sliders for intuitive min/max selection
- Fix hidden table rows caused by sticky header overlap

### Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Amazon import fields populated | ~20% | 70%+ | % of fields with data post-import |
| Clicks to edit from listing view | 3 | 1 | User flow analysis |
| Time to see new listing in UI | Manual refresh | <2s auto | Performance monitoring |
| User-reported slider confusion | 8/10 users | 0/10 users | User testing feedback |
| Table visibility issues reported | 5+ reports | 0 reports | Support ticket tracking |

---

## 4. Requirements

### 4.1 Functional Requirements

#### FR1: Enhanced Amazon Import Data Extraction

**FR1.1**: Scrape additional structured data from Amazon product pages
- Extract: CPU model, RAM capacity/type, storage capacity/type, GPU model, manufacturer, form factor
- Parse product specifications table if available
- Handle variations in Amazon page structure across product categories

**FR1.2**: NLP-based title/description extraction
- Apply NLP patterns to extract component data from titles/descriptions
- Patterns for: "Intel Core i7-12700", "16GB DDR4", "512GB NVMe SSD", etc.
- Validate extracted data against known CPU/GPU catalogs
- Confidence scoring for extracted values (high/medium/low)

**FR1.3**: Import field population logic
- Prioritize structured data over NLP extraction
- Use NLP extraction as fallback when structured data unavailable
- Log extraction confidence for manual review/correction

#### FR2: Quick Edit Modal Enhancements

**FR2.1**: Expand quick edit modal fields
- Add fields: CPU (searchable dropdown), RAM (capacity + type), Storage (capacity + type), GPU (searchable dropdown)
- Reuse exact field components from full edit page (consistency)
- Include validation rules matching full edit page

**FR2.2**: Quick Edit button in view modal
- Add "Quick Edit" button to bottom toolbar of listing view modal
- Opens quick edit modal directly (no navigation away)
- Pre-populate quick edit modal with current listing data

#### FR3: Listing Management Workflow Improvements

**FR3.1**: Edit button on listing detail page
- Add "Edit" button in top-right corner next to "Delete"
- Opens full edit page for current listing
- Maintain consistent styling with other action buttons

**FR3.2**: Auto-refresh on listing add/import
- Implement Server-Sent Events (SSE) or WebSocket for real-time updates
- Push listing creation/update events to connected clients
- Update UI automatically without manual refresh
- Show toast notification on new listing appearance

**FR3.3**: Auto-recalculation on relevant changes
- Trigger valuation recalculation when:
  - Listing price/components change
  - Valuation rules change
  - CPU/GPU benchmark data updates
- Optimize to recalculate only affected listings (not full catalog)
- Smart dependency tracking: only recalculate when relevant fields change

#### FR4: CPU Catalog Enhancements

**FR4.1**: CPU sorting
- Enable sorting by: name, clock speed, core count, thread count, TDP, benchmark scores
- Support ascending/descending sort
- Persist sort preference in URL query params

**FR4.2**: CPU filtering by listings
- Filter: "CPUs with listings" (show only CPUs used in ≥1 listing)
- Sort by: "Listing count" (number of listings using each CPU)
- Display listing count badge on CPU cards

#### FR5: Column Selector for List Views

**FR5.1**: Column selector UI
- Add column selector dropdown/modal for all entity list views (listings, CPUs, etc.)
- Show all available fields for entity type
- Checkboxes for visible/hidden columns
- Drag-to-reorder visible columns

**FR5.2**: Column persistence
- Save column preferences to localStorage per entity type
- Restore preferences on page load
- Provide "Reset to Default" option

**FR5.3**: Entity coverage
- Implement for: Listings, CPUs, GPUs, Valuation Rules, Profiles
- Ensure all entity fields available in selector (including custom fields)

#### FR6: UI Bug Fixes

**FR6.1**: Dual-handle range sliders
- Replace single-handle sliders with dual-handle components
- Both min and max handles visible and draggable
- Show current range values (e.g., "1.5 GHz - 4.2 GHz")
- Apply to: CPU filters (clock speed, cores, threads), price ranges

**FR6.2**: Fix hidden table rows
- Adjust table layout to prevent first row hiding behind sticky header
- Ensure all rows fully visible without scrolling
- Test across entity list views (listings, CPUs, etc.)

### 4.2 Non-Functional Requirements

**NFR1: Performance**
- Amazon NLP extraction: <500ms per listing
- Auto-recalculation: <2s for affected listings (up to 100)
- Real-time updates: <2s from event to UI update
- Column selector load: <100ms

**NFR2: Scalability**
- SSE/WebSocket: Support 100+ concurrent connections
- Recalculation queue: Handle 1000+ listings without blocking

**NFR3: Reliability**
- Amazon scraping: Graceful degradation if page structure changes
- Real-time updates: Reconnect on connection loss
- Recalculation: Retry failed calculations with exponential backoff

**NFR4: Usability**
- Quick edit modal: Mobile-responsive
- Column selector: Accessible (keyboard navigation, screen reader support)
- Sliders: Touch-friendly on mobile devices

**NFR5: Maintainability**
- NLP extraction patterns: Externalized configuration (easy updates)
- Real-time event handlers: Centralized event bus pattern
- Recalculation logic: Reuse existing valuation core logic

---

## 5. User Stories

**US1: As a user, I want Amazon imports to auto-populate most fields so I spend less time on manual data entry**
- Acceptance: 70%+ of fields populated from Amazon product page
- Benefit: Reduce import time from 5 min → 1 min per listing

**US2: As a user, I want to quickly edit key listing fields without leaving the view modal so my workflow is uninterrupted**
- Acceptance: Click "Quick Edit" in view modal → Edit CPU/RAM/Storage/GPU → Save
- Benefit: Reduce edit workflow from 3 clicks to 1 click

**US3: As a user, I want newly added listings to appear automatically so I don't have to refresh the page**
- Acceptance: Add listing → See it in list view within 2s without manual refresh
- Benefit: Seamless workflow, confidence that changes are saved

**US4: As a user, I want to sort CPUs by specifications so I can find CPUs meeting my needs easily**
- Acceptance: Sort CPUs by clock speed, cores, TDP, etc.
- Benefit: Faster CPU research and comparison

**US5: As a user, I want to customize visible columns so I see only relevant fields for my workflow**
- Acceptance: Select columns via dropdown → Columns persist across sessions
- Benefit: Cleaner UI, faster scanning of relevant data

**US6: As a user, I want range sliders to have two handles so I can intuitively set min and max values**
- Acceptance: Drag left handle for min, right handle for max
- Benefit: No more confusion about how to set ranges

---

## 6. Scope

### In Scope

**Phase 1: Critical UI Bug Fixes**
- Dual-handle range sliders (FR6.1)
- Fix hidden table rows (FR6.2)

**Phase 2: Listing Workflow Enhancements**
- Quick edit modal field expansion (FR2.1)
- Quick Edit button in view modal (FR2.2)
- Edit button on listing detail page (FR3.1)

**Phase 3: Real-Time Updates Infrastructure**
- SSE/WebSocket implementation for listing events (FR3.2)
- Auto-recalculation triggers (FR3.3)

**Phase 4: Amazon Import Enhancement**
- Enhanced Amazon scraping (FR1.1)
- NLP-based extraction (FR1.2)
- Import field population logic (FR1.3)

**Phase 5: CPU Catalog Improvements**
- CPU sorting (FR4.1)
- CPU filtering by listings (FR4.2)

**Phase 6: Column Selector**
- Column selector UI (FR5.1)
- Column persistence (FR5.2)
- Entity coverage (FR5.3)

### Out of Scope

- API-based Amazon integration (requires API key/credentials)
- AI/ML-based component recognition (beyond rule-based NLP)
- Column-level permissions/access control
- Import from other marketplaces (eBay, Newegg, etc.) - separate PRD
- Bulk edit functionality - separate feature
- Advanced filtering UI (filter builder) - separate feature
- Saved filter sets - separate feature

---

## 7. Dependencies & Assumptions

### Dependencies

**D1: Backend Infrastructure**
- FastAPI backend must support SSE or WebSocket connections
- Celery worker for background recalculation tasks
- Redis for pub/sub messaging (real-time events)

**D2: Existing Components**
- Current quick edit modal exists and is functional
- Listing edit page components available for reuse
- Valuation recalculation logic exists (needs triggering mechanism)

**D3: External Services**
- Amazon product pages remain accessible (no rate limiting)
- No changes to Amazon page structure during implementation

### Assumptions

**A1: Data Availability**
- Amazon product pages contain extractable data in title/description
- CPU/GPU names in Amazon listings match catalog entries (with fuzzy matching)

**A2: User Behavior**
- Users prefer auto-refresh over manual refresh
- Column customization is valuable for power users (not overwhelming for casual users)
- Quick edit is sufficient for common edits (full edit page for complex changes)

**A3: Technical**
- SSE is sufficient for real-time updates (WebSocket if needed)
- localStorage acceptable for column preferences (no server-side storage)
- NLP extraction can achieve 70%+ field population rate

---

## 8. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Amazon page structure changes break scraping | High | Medium | Implement fallback to NLP extraction; add monitoring for extraction failures |
| Real-time updates increase server load | Medium | Medium | Implement connection throttling; use SSE (lighter than WebSocket) |
| NLP extraction accuracy <70% | Medium | Low | Manually tune extraction patterns; add user feedback mechanism for corrections |
| Column selector overwhelms casual users | Low | Medium | Default to essential columns; provide presets (Basic, Advanced, All) |
| Recalculation triggers cause performance issues | High | Low | Queue-based processing; only recalculate affected listings; add rate limiting |
| Dual-handle slider library introduces new bugs | Low | Low | Thorough testing; fallback to current slider if issues arise |

---

## 9. Target State

### Post-Implementation Experience

**Amazon Import Flow**:
1. User pastes Amazon URL into import form
2. System extracts 70%+ fields automatically (CPU, RAM, Storage, GPU, manufacturer, etc.)
3. User reviews/corrects low-confidence extractions
4. User saves listing → Listing appears in UI within 2s

**Listing Edit Flow**:
1. User views listing in modal or detail page
2. User clicks "Quick Edit" (from modal) or "Edit" (from detail page)
3. User edits CPU/RAM/Storage/GPU in quick edit modal
4. User saves → Valuation recalculates automatically → UI updates in <2s

**CPU Research Flow**:
1. User navigates to /cpus catalog
2. User filters: "CPUs with listings" + sort by "Listing count"
3. User sees popular CPUs with listing count badges
4. User sorts by clock speed to find high-performance options

**Data Exploration Flow**:
1. User opens column selector on listings page
2. User selects: Price, CPU, RAM, Storage, Valuation, CPU Mark
3. Preferences saved → Same columns appear on next visit
4. User drags columns to reorder as preferred

**UI Interaction**:
- Range sliders show two handles clearly indicating min/max
- All table rows fully visible (no hidden first row)
- Intuitive, frustration-free interactions

---

## 10. Acceptance Criteria

### AC1: Amazon Import Enhancement
- [ ] Amazon imports populate 70%+ of available fields
- [ ] NLP extraction correctly identifies CPU, RAM, Storage, GPU from titles/descriptions
- [ ] Low-confidence extractions flagged for user review
- [ ] Import time reduced from 5 min to <1 min per listing

### AC2: Quick Edit Enhancements
- [ ] Quick edit modal includes CPU, RAM, Storage, GPU fields
- [ ] Fields match full edit page (components, validation)
- [ ] "Quick Edit" button appears in listing view modal toolbar
- [ ] Quick edit opens pre-populated with current listing data

### AC3: Listing Management
- [ ] Edit button appears on listing detail page (top-right)
- [ ] New/edited listings appear in UI within 2s (no manual refresh)
- [ ] Valuation recalculates automatically when price/components change
- [ ] Recalculation completes in <2s for up to 100 affected listings

### AC4: CPU Catalog
- [ ] CPUs sortable by all specification fields (clock speed, cores, TDP, etc.)
- [ ] Filter "CPUs with listings" shows only CPUs in ≥1 listing
- [ ] Sort by "Listing count" shows most-used CPUs first
- [ ] Listing count badge displays on CPU cards

### AC5: Column Selector
- [ ] Column selector available on all entity list views
- [ ] All entity fields (including custom fields) available in selector
- [ ] Column preferences persist across sessions
- [ ] Drag-to-reorder columns works intuitively

### AC6: UI Bug Fixes
- [ ] All range sliders have two handles (min and max)
- [ ] Current range values displayed (e.g., "1.5 GHz - 4.2 GHz")
- [ ] First row in table list views fully visible (not hidden behind header)
- [ ] Bugs verified fixed across all affected pages

---

## 11. Implementation Approach

### Phased Rollout

**Phase 1: Critical UI Bug Fixes** (2 story points)
- **Priority**: Immediate (affects usability)
- **Deliverables**: Dual-handle sliders, fixed table headers
- **Risk**: Low
- **Timeline**: 2-3 days

**Phase 2: Listing Workflow Enhancements** (5 story points)
- **Priority**: High (high user value)
- **Deliverables**: Enhanced quick edit modal, quick edit button, edit button on detail page
- **Dependencies**: Existing edit components
- **Timeline**: 5-7 days

**Phase 3: Real-Time Updates Infrastructure** (8 story points)
- **Priority**: High (foundational for future features)
- **Deliverables**: SSE/WebSocket events, auto-recalculation triggers
- **Dependencies**: Backend infrastructure (FastAPI, Redis)
- **Timeline**: 7-10 days

**Phase 4: Amazon Import Enhancement** (8 story points)
- **Priority**: Medium (improves data quality)
- **Deliverables**: Enhanced scraping, NLP extraction, field population logic
- **Dependencies**: None
- **Timeline**: 7-10 days

**Phase 5: CPU Catalog Improvements** (3 story points)
- **Priority**: Medium (nice-to-have)
- **Deliverables**: CPU sorting, filtering by listings
- **Dependencies**: None
- **Timeline**: 3-5 days

**Phase 6: Column Selector** (8 story points)
- **Priority**: Low (power user feature)
- **Deliverables**: Column selector UI, persistence, entity coverage
- **Dependencies**: None
- **Timeline**: 7-10 days

**Total Effort**: 34 story points (~6-8 weeks with parallel work)

### Parallel Work Opportunities

- Phase 1 and Phase 2 can run in parallel (different components)
- Phase 4 and Phase 5 can run in parallel (independent features)
- Phase 3 blocks auto-recalculation but not other Phase 2 work

### Quality Gates

Each phase requires:
- [ ] Unit tests (80%+ coverage for new code)
- [ ] Integration tests (API + UI for workflows)
- [ ] Manual QA (cross-browser, mobile-responsive)
- [ ] Accessibility audit (keyboard navigation, screen readers)
- [ ] Performance testing (meets NFRs)

---

## 12. Open Questions

1. **Q1: Real-time updates implementation**
   - Should we use SSE or WebSocket? (Recommendation: SSE for simplicity)
   - How many concurrent connections do we expect? (Affects infrastructure)

2. **Q2: NLP extraction patterns**
   - Should patterns be hardcoded or configurable? (Recommendation: Configurable YAML)
   - How do we handle new component naming conventions? (Manual pattern updates vs. ML)

3. **Q3: Recalculation scope**
   - Should we recalculate dependent listings (e.g., all listings with same CPU)? (Yes, with queue)
   - Should recalculation be synchronous or asynchronous? (Async with progress indicator)

4. **Q4: Column selector defaults**
   - What columns should be visible by default for each entity? (Requires stakeholder input)
   - Should we provide preset column sets (Basic, Advanced, All)? (Recommendation: Yes)

5. **Q5: Amazon rate limiting**
   - Do we need to throttle Amazon scraping requests? (Likely yes)
   - Should we cache scraped data to avoid re-scraping? (Recommendation: Yes, 24hr TTL)

---

## 13. Success Criteria

**Implementation Success**:
- [ ] All 6 phases completed and deployed to production
- [ ] All acceptance criteria met
- [ ] No P0/P1 bugs introduced
- [ ] Performance NFRs achieved

**Business Success**:
- [ ] User-reported import time reduced by 80%+
- [ ] Edit workflow clicks reduced by 66%
- [ ] Slider confusion reports eliminated
- [ ] Table visibility issues eliminated
- [ ] Positive user feedback on auto-refresh and column customization

**Technical Success**:
- [ ] Real-time updates infrastructure supports 100+ concurrent users
- [ ] Recalculation queue handles 1000+ listings without blocking
- [ ] Amazon scraping achieves 70%+ field population rate
- [ ] Code coverage >80% for new code
- [ ] No performance regressions

---

## 14. Appendix

### A. Related Documents
- Enhancement Request: `/docs/project_plans/requests/needs-designed/11-18.md`
- Import Architecture: (TBD - may need ADR for real-time updates)

### B. Glossary
- **SSE (Server-Sent Events)**: HTTP-based protocol for server-to-client real-time updates
- **NLP (Natural Language Processing)**: Extraction of structured data from unstructured text
- **Quick Edit Modal**: Lightweight edit interface for common field changes
- **Column Selector**: UI component for customizing visible table columns

### C. Stakeholders
- **Product Owner**: (TBD)
- **Engineering Lead**: (TBD)
- **UX Designer**: (TBD)
- **QA Lead**: (TBD)

---

**Next Steps**:
1. Review and approve PRD
2. Create detailed implementation plan
3. Set up progress tracking
4. Begin Phase 1 (Critical UI Bug Fixes)
