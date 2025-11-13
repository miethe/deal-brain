---
title: "Deal Builder - PRD"
description: "Interactive PC build configuration with real-time valuation and deal quality indicators. Users create custom builds by selecting components (CPU, RAM, Storage, GPU) and receive instant pricing, adjusted valuations, and performance metrics using existing valuation rules and PassMark benchmarks."
audience: [ai-agents, developers, pm]
tags: [feature, deal-builder, valuation, performance-metrics, user-tools, interactive]
created: 2025-11-12
updated: 2025-11-12
category: "product-planning"
status: draft
related:
  - /home/user/deal-brain/docs/design/deal-builder-ux-specification.md
  - /home/user/deal-brain/docs/design/deal-builder-implementation-guide.md
  - /home/user/deal-brain/packages/core/dealbrain_core/valuation.py
  - /home/user/deal-brain/apps/api/dealbrain_api/services/listings.py
---

# Deal Builder - Product Requirements Document

## Executive Summary

Deal Builder is an interactive PC build configuration tool that enables users to create custom PC builds by selecting individual components and receive instant, data-driven pricing and performance valuations. The feature reuses the existing valuation system (component-based pricing rules, PassMark benchmarks, scoring profiles) to calculate adjusted values and deal quality indicators in real-time. Users can save builds for future reference and share them via URLs for community collaboration.

**Primary User Need**: Users cannot preview custom build economics before purchasing components individually. Deal Builder closes this gap by providing transparent, real-time valuation feedback as components are selected.

**Strategic Value**: Increases user engagement with deal evaluation, builds community content through sharing, and creates data for recommendation engines (future phases).

## Context & Background

### Existing Valuation System
- **Component Valuation**: Condition multipliers + component-specific adjustments in `packages/core/dealbrain_core/valuation.py`
- **Performance Metrics**: Dollar-per-CPU-Mark (single/multi-thread) calculated via `apply_listing_metrics()` in `apps/api/dealbrain_api/services/listings.py`
- **Deal Meter Thresholds**: From `ApplicationSettings` model - great_deal (25%), good_deal (15%), premium_warning (10%)
- **Color System**: Established CSS variables for deal indicators (green/red backgrounds with appropriate contrast)
- **UI Components**: ValuationCell, DeltaBadge, PerformanceMetricDisplay already exist and can be adapted

### User Behavior Insights
- Users browse listings to understand market pricing
- Users want to validate custom build decisions against market data
- Users hesitate to purchase without understanding component value contribution
- No current mechanism to explore "what-if" scenarios with different components

### Competitive Gap
- eBay/Amazon show total price but not valuation intelligence
- PC Builder sites (PCPartPicker, etc.) show compatibility but not market value
- Deal Brain has unique advantage: valuation rules + benchmark data

## Problem Statement

**Current State**: Users cannot preview or validate custom PC build economics. They see component prices individually but cannot understand:
1. Total adjusted value vs. market (is this a good deal overall?)
2. Performance efficiency ($/CPU Mark) impact of component choices
3. Deal quality relative to pre-built systems in database
4. Historical value of same configuration

**Impact**: Users make purchases based on incomplete information, reducing confidence in Deal Brain's pricing intelligence. Missed opportunity for user engagement and data collection.

## Goals & Success Metrics

### Primary Goals
1. **Enable transparent build valuation** - Users create builds and receive instant pricing/valuation feedback
2. **Increase feature adoption** - 30%+ of monthly active users create at least one build (measured via analytics)
3. **Drive engagement** - Average session time on builder page >5 minutes, 40%+ save rate for builds created
4. **Generate shareable content** - 25%+ of saved builds shared via URL (tracked via share_token access logs)

### Success Metrics
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Builds Created/DAU | 0.3+ | Analytics event tracking |
| Saved Builds | 40%+ of created | Database query on `saved_builds` table |
| Shares Generated | 25%+ of saved | Share token access logs |
| Avg Session Time | >5 minutes | Analytics page duration |
| Feature Adoption | 30% MAU | Analytics cohort analysis |
| API Response Time | <300ms | Backend performance monitoring |
| Error Rate | <1% | API error tracking |

## Requirements

### Functional Requirements

#### F1: Component Selection (Progressive Disclosure)
- **CPU Selection (Required)**: Users must select CPU first; enables performance metric calculations
- **Subsequent Components (Optional but Recommended)**: RAM, Primary Storage, GPU, Secondary Storage in that order
- **Advanced Components (Collapsible)**: PSU, Case, Cooling, Motherboard, Other
- **Selection Interface**: Modal with search (200ms debounce), filters (manufacturer, price range, performance tier), and "Recommended" section showing top components from existing deals
- **Component Information**: Display CPU Mark (multi/single), TDP, cores/threads, price range for all selection options
- **Edit/Remove**: Users can change or remove any component, triggering recalculation

#### F2: Real-Time Valuation Calculation
- **Price Calculation**: Sum of component base prices, apply valuation rules from `ApplicationSettings.valuation_rules`
- **Adjusted Value**: Apply condition multipliers and component adjustments via `dealbrain_core/valuation.py:apply_valuation_rules()`
- **Deal Meter Display**: Color-coded indicator (green/red) showing Great Deal (25%+ savings) → Good Deal (15-25%) → Fair (0-15%) → Premium (10%+ markup)
- **Performance Metrics**: Calculate `dollar_per_cpu_mark_multi` and `dollar_per_cpu_mark_single` if CPU selected (via `scoring.py`)
- **Debouncing**: API calls debounced at 300ms to avoid excessive requests during rapid selections
- **API Endpoint**: `POST /v1/builder/calculate` accepts component IDs, returns pricing + metrics + valuation breakdown

#### F3: Valuation Breakdown Display
- **Sticky Valuation Panel** (desktop >1024px): Right column, sticks to viewport during scroll
- **Floating Drawer** (mobile <768px): Button at bottom opens full-screen drawer with valuation details
- **Content**: Total price, adjusted value, delta amount + percentage, deal quality indicator, performance metrics with comparisons to database averages
- **Expandable Breakdown**: Detailed view shows base costs, applied rules, adjustments, final valuation with explanations

#### F4: Save Build Functionality
- **Save Modal**: Name (required), description (optional), tags, visibility (private/public/unlisted)
- **Persistence**: New `saved_builds` table in PostgreSQL with component references, pricing snapshot, metrics snapshot, valuation breakdown (JSONB)
- **Auto-generated Share Token**: UUID-based token for shareable URLs (`/builder/shared/{token}`)
- **API Endpoint**: `POST /v1/builder/builds` creates build, `PATCH /v1/builder/builds/{id}` updates

#### F5: Saved Builds Management
- **Display Section**: Below builder, shows user's saved builds in grid (3 cols desktop, 1 col mobile)
- **Card Information**: Build name, base→adjusted price with delta badge, deal quality indicator, creation date
- **Card Actions**: Load (populate builder), Edit (edit and update), Delete (with confirmation), Duplicate, Share
- **API Endpoints**: `GET /v1/builder/builds` (list user's), `GET /v1/builder/builds/{id}` (get one), `DELETE /v1/builder/builds/{id}`

#### F6: Share Functionality
- **Share Modal**: Copy URL button, quick share (Twitter/Reddit/Email), export options (PDF/Text/JSON)
- **Shared View Page**: `/builder/shared/[share_token]/page.tsx` - read-only display of build with all valuation data
- **Access Control**: Public builds visible to anyone, private builds show 404, unlisted accessible only via direct link
- **Price Update Banner**: Notify viewer if component prices changed since build was saved
- **API Endpoint**: `GET /v1/builder/builds/{id}/share` returns shareable data

#### F7: Real-Time Metrics & Recommendations
- **Comparison Metrics**: Show $/CPU Mark (multi/single) with percentile ranking vs. database (e.g., "23% better than average")
- **Composite Score**: 0-100 scale based on selected `Profile` (from `ApplicationSettings`)
- **Recommendations**: Show CPUs from top-performing listings, sorted by recommendation score
- **Empty State**: When no components selected, show onboarding with "Start Building!" message and CPU selection CTA

### Non-Functional Requirements

#### NF1: Performance
- **Page Load**: <2s initial render with skeleton loaders
- **Component Selection Modal**: <500ms to populate with filtered results
- **Valuation Calculation**: <300ms from component selection to UI update (debounced)
- **Saved Builds Load**: <1s to fetch and display user's builds
- **Database Query Optimization**: Use indexes on `(user_id, deleted_at)`, `share_token`, `visibility` for `saved_builds` table

#### NF2: Database Schema
- **New Table**: `saved_builds` with fields: id, user_id (nullable for future), name, description, tags, visibility, share_token, component references (cpu_id, gpu_id, ram_spec_id, etc.), pricing snapshot (JSONB), metrics snapshot (JSONB), valuation breakdown (JSONB), timestamps
- **Indexes**: `idx_user_builds (user_id, deleted_at)`, `idx_share_token (share_token)`, `idx_visibility (visibility, deleted_at)`
- **Soft Deletes**: `deleted_at` column for audit trail and recovery

#### NF3: API Architecture
- **Reuse Existing Patterns**: Use `ListingsService` as pattern for `BuilderService` (new file: `apps/api/dealbrain_api/services/builder.py`)
- **Core Logic Reuse**: Directly call `dealbrain_core/valuation.py:apply_valuation_rules()` and `scoring.py:calculate_metrics()`
- **Database Models**: Extend `apps/api/dealbrain_api/models/core.py` with `SavedBuild` SQLAlchemy model
- **API Router**: New file `apps/api/dealbrain_api/api/builder.py` with endpoints under `/v1/builder/`

#### NF4: Frontend Architecture
- **State Management**: React Context (`BuilderProvider`) for component selection state, calculations, editing mode
- **Data Fetching**: React Query for API calls with 5-minute cache on catalog data, no cache on calculations
- **Component Memoization**: `React.memo()` on ComponentCard, ValuationPanel to prevent unnecessary re-renders
- **Responsive Design**: CSS Grid for layout, Mobile-first approach with breakpoints at 768px and 1024px
- **Lazy Loading**: Code-split modals (ComponentSelectorModal, SaveBuildModal, ShareModal) for faster initial page load

#### NF5: Accessibility (WCAG AA)
- **Keyboard Navigation**: Tab through components, Enter to select, Escape to close modals, Arrow keys in lists
- **Screen Reader Support**: ARIA labels on all buttons, live regions for price updates (`aria-live="polite"`), semantic HTML
- **Color Contrast**: Text 4.5:1 minimum, UI elements 3:1 minimum, deal indicators distinguishable without color alone
- **Focus Indicators**: Visible focus rings on all interactive elements, 3px minimum outline

#### NF6: Security & Data Privacy
- **Input Validation**: All component IDs must exist in database before calculation
- **Share Token Security**: Generate cryptographically random tokens (uuid4), 64-char hex strings
- **Access Control**: Verify user_id on build access, private builds return 404 to non-owners
- **CORS**: Builder API endpoints same-origin only (Next.js to FastAPI via proxy or direct)

## User Stories & Use Cases

### Story 1: Browse & Build
**As a** budget-conscious PC buyer
**I want to** create a custom build with specific components
**So that** I can understand the total cost and value before purchasing

**Acceptance Criteria**:
- Select CPU from modal with search
- See available RAM/Storage options
- Real-time price updates as components added
- See deal quality indicator and $/CPU Mark metrics
- Save build with name for later reference

### Story 2: Share & Discuss
**As a** community member
**I want to** share my build with friends or online forums
**So that** I can get feedback and discuss specifications

**Acceptance Criteria**:
- Click "Share" button and copy shareable link
- Shared link displays read-only build view
- Others can click "Build Your Own" to load into their builder
- Can export build as PDF or text for Discord/Reddit

### Story 3: Track Multiple Builds
**As a** PC enthusiast
**I want to** save multiple build variations
**So that** I can compare different configurations over time

**Acceptance Criteria**:
- Create 3+ different builds and save each
- Saved builds section shows all builds
- Can load any saved build back into builder
- Can edit and update saved builds
- Can delete builds with confirmation

### Story 4: Compare to Market
**As a** data-driven buyer
**I want to** see how my custom build compares to pre-built systems in the database
**So that** I can ensure I'm getting market-competitive value

**Acceptance Criteria**:
- See "Compare to Listings" button in valuation panel
- Drawer shows 3-5 similar pre-builts with price comparisons
- Can click through to view full listing details
- Shows deal quality comparison (is my build better/worse value?)

## Scope

### In-Scope (MVP Phase 1-3)
- Component selection (CPU, RAM, Storage, GPU, PSU, Case, etc.)
- Real-time valuation calculation using existing rules
- Save and load builds
- Shareable URLs with read-only view
- Performance metrics display ($/CPU Mark, composite score)
- Saved builds gallery with management actions
- Mobile responsive design
- Basic accessibility (keyboard nav, ARIA labels)

### Out-of-Scope (Future Phases)
- Component compatibility validation (DDR5 vs DDR4, etc.)
- Price history tracking and alerts
- Build templates and presets
- AI-powered recommendations based on user behavior
- Community build gallery and voting
- Multi-user collaboration on builds
- Budget calculator and financing options
- Integration with retailers for direct purchase links

## Dependencies & Assumptions

### Dependencies
- **External**: PassMark CPU/GPU benchmark database (already integrated)
- **Internal**:
  - `packages/core/dealbrain_core/valuation.py` - valuation rule engine
  - `packages/core/dealbrain_core/scoring.py` - metrics calculation
  - `ApplicationSettings` model with valuation thresholds and profiles
  - Existing CPU/GPU/RAM catalogs in database
  - React Query for data fetching
  - shadcn/ui component library

### Assumptions
- User authentication is handled by existing auth system (future phases)
- Component pricing remains relatively stable during session
- Users understand PC component basics (no in-app education required)
- Database performance allows real-time metric calculations
- API response times acceptable for 300ms debounce interval

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Slow valuation calculations for edge cases (many components) | Medium | High | Implement caching, optimize SQL queries, add timeouts |
| Users confused by valuation logic differences vs. listings | Medium | Medium | Show clear breakdown with rule explanations, link to documentation |
| Mobile UX issues with component selection | Low | Medium | Extensive mobile testing, A/B test modal vs. native select |
| Share token collisions | Very Low | High | Use uuid4 with 64-char hex encoding, database unique constraint |
| Unused feature if adoption is low | Low | Medium | Marketing and in-app prompts, make easy to access from listings |
| Performance degradation as saved_builds table grows | Low | Medium | Implement pagination, add database indexes, archive old data |

## Target State (Post-Implementation)

### User Experience
- User navigates to `/builder` page
- Sees onboarding with "Start with CPU" message
- Selects CPU via search modal, sees recommendations
- Adds RAM, Storage, GPU (optional)
- Watches real-time price and valuation updates in sticky right panel
- Sees deal meter (Good Deal!), performance metrics ($/CPU Mark better than average)
- Expands breakdown to see valuation rules applied
- Clicks "Save Build" with name and description
- Saved builds appear in gallery below
- Shares build URL with friends, they see read-only view with "Build Your Own" CTA
- Later, loads saved build to make variations, saves new version

### Technical State
- New `SavedBuild` SQLAlchemy model in `apps/api/dealbrain_api/models/core.py`
- `BuilderService` in `apps/api/dealbrain_api/services/builder.py` with methods: `calculate_build_valuation()`, `save_build()`, `get_user_builds()`, `compare_build_to_listings()`
- New API router `apps/api/dealbrain_api/api/builder.py` with endpoints under `/v1/builder/`
- Alembic migration creating `saved_builds` table with indexes
- React components in `apps/web/components/builder/`: BuilderProvider, ComponentBuilder, ComponentCard, ComponentSelectorModal, ValuationPanel, SavedBuildsSection, ShareModal
- Next.js page routes: `/app/builder/page.tsx`, `/app/builder/shared/[token]/page.tsx`
- Database: ~10k saved builds per 100k MAU (estimated capacity)

## Acceptance Criteria

### Backend (Phase 1-2)
- [ ] SavedBuild model created with all fields and indexes
- [ ] Alembic migration runs successfully, creates table
- [ ] BuilderService.calculate_build_valuation() returns correct pricing (validated vs. manual calculation)
- [ ] BuilderService.apply_valuation_rules() produces same results as existing valuation system
- [ ] API POST /v1/builder/calculate accepts component IDs, returns pricing + metrics within 300ms
- [ ] API POST /v1/builder/builds saves build, generates share_token, stores snapshot
- [ ] API GET /v1/builder/builds/{id}/share returns correct data for shareable URL
- [ ] All endpoints secured (private builds only accessible to owner)
- [ ] 100% test coverage for builder service logic

### Frontend (Phase 2-3)
- [ ] Builder page loads with skeleton loaders in <2s
- [ ] Component selection modal loads CPUs in <500ms, filters work
- [ ] Real-time valuation updates when component selected (300ms debounce)
- [ ] Deal meter displays correct color/message for all threshold ranges
- [ ] Performance metrics calculated and displayed with correct formulas
- [ ] Save button opens modal, saves build, shows success toast
- [ ] Saved builds gallery loads and displays all user builds
- [ ] Share button copies correct URL and shows copy confirmation
- [ ] Shared URL loads read-only build view correctly
- [ ] Mobile layout stacks correctly, floating drawer works
- [ ] Keyboard navigation works (Tab through components, Enter to select)
- [ ] ARIA labels present, screen reader announces updates
- [ ] >95 Lighthouse accessibility score

### Integration
- [ ] End-to-end: Select CPU → Save Build → Share → View Shared URL works
- [ ] Component changes update valuation in real-time
- [ ] Saved builds load and repopulate builder correctly
- [ ] Saved valuation snapshot matches current calculation for same components
- [ ] API error states handled gracefully on frontend
- [ ] Analytics events tracked for feature adoption
- [ ] No N+1 queries in API endpoints
- [ ] Database response times <100ms for all builder queries

## Implementation Overview

### Phase 1: Backend Foundation (Days 1-5)
**Goal**: API and database ready for frontend integration

**Tasks**:
- D1-2: Create SavedBuild SQLAlchemy model, Alembic migration
- D3-4: Implement BuilderService with calculate_build_valuation(), save_build(), get_user_builds()
- D5: Implement API endpoints `/v1/builder/calculate`, `/v1/builder/builds` CRUD

**Deliverables**:
- `saved_builds` table exists with data
- API endpoints accessible and tested
- BuilderService unit tests (>80% coverage)

**Files Modified**:
- Create: `apps/api/dealbrain_api/services/builder.py`
- Create: `apps/api/alembic/versions/[timestamp]_add_saved_builds_table.py`
- Edit: `apps/api/dealbrain_api/models/core.py` (add SavedBuild model)
- Edit: `apps/api/dealbrain_api/api/builder.py` (new router file)

### Phase 2: Frontend Component Selection (Days 6-10)
**Goal**: Users can select components and see real-time calculations

**Tasks**:
- D6: Create BuilderProvider context, BuilderPage layout
- D7: Build ComponentCard, ComponentSelectorModal with search
- D8: Implement real-time valuation calculation via API
- D9: Build ValuationPanel with deal meter and metrics
- D10: Connect component selection to valuation updates

**Deliverables**:
- Builder page loads and renders
- Component selection working end-to-end
- Real-time calculations functional
- UI matches design specification

**Files Created**:
- `/apps/web/components/builder/builder-provider.tsx`
- `/apps/web/components/builder/component-builder.tsx`
- `/apps/web/components/builder/component-card.tsx`
- `/apps/web/components/builder/component-selector-modal.tsx`
- `/apps/web/components/builder/valuation-panel.tsx`
- `/apps/web/app/builder/page.tsx`

### Phase 3: Save & Share (Days 11-15)
**Goal**: Users can persist and share builds

**Tasks**:
- D11: Build SaveBuildModal and save functionality
- D12: Implement SavedBuildsSection gallery
- D13: Build ShareModal and shareable URL view
- D14: Handle shared build loading and read-only view
- D15: Add load/edit/delete actions on saved builds

**Deliverables**:
- Save build workflow end-to-end
- Saved builds gallery functional
- Share feature working with URLs
- Shared build page displays correctly

**Files Created**:
- `/apps/web/components/builder/save-build-modal.tsx`
- `/apps/web/components/builder/saved-builds-section.tsx`
- `/apps/web/components/builder/share-modal.tsx`
- `/apps/web/app/builder/shared/[token]/page.tsx`

### Phase 4: Mobile & Polish (Days 16-20)
**Goal**: Mobile-responsive, accessible, tested

**Tasks**:
- D16: Implement mobile layouts, floating drawer for valuation panel
- D17: Test keyboard navigation and screen reader support
- D18: Performance optimization (code splitting, memoization)
- D19: Cross-browser testing, bug fixes
- D20: Documentation, deployment prep

**Deliverables**:
- Mobile UX matches specification
- WCAG AA accessibility compliance verified
- Performance benchmarks met (<2s page load, <300ms calculations)
- Ready for production deployment

### Phase 5: Monitoring & Iteration (Days 21+)
**Goal**: Track adoption and gather user feedback

**Tasks**:
- Monitor analytics (builds created, saves rate, shares)
- Fix reported bugs and edge cases
- Gather feedback from users
- Plan Phase 2 features (compatibility validation, price history)

**Success**: 30%+ MAU adoption, <1% error rate, positive user feedback

## Technical Implementation Notes

### Component ID Validation
When calculating valuation, validate that component IDs exist and are active:
```python
# BuilderService.calculate_build_valuation()
cpu = session.query(CPU).filter_by(id=cpu_id).first()
if not cpu:
    raise ValueError(f"CPU {cpu_id} not found in catalog")
```

### Reuse Existing Valuation Logic
Call existing `apply_valuation_rules()` function directly:
```python
from dealbrain_core.valuation import apply_valuation_rules

adjusted_price = apply_valuation_rules(
    base_price=total_price,
    rules=settings.valuation_rules,
    component_conditions=conditions_dict
)
```

### Performance Metrics Calculation
Use `scoring.py` for metrics:
```python
from dealbrain_core.scoring import calculate_metrics

metrics = calculate_metrics(
    cpu_mark_multi=cpu.cpu_mark_multi,
    cpu_mark_single=cpu.cpu_mark_single,
    adjusted_price=adjusted_price
)
```

### Database Query Optimization
Use joins and eager loading to avoid N+1:
```python
# BuilderService.get_user_builds()
builds = session.query(SavedBuild)\
    .options(
        joinedload(SavedBuild.cpu),
        joinedload(SavedBuild.gpu)
    )\
    .filter_by(user_id=user_id, deleted_at=None)\
    .order_by(SavedBuild.created_at.desc())\
    .all()
```

### Frontend State Management
BuilderContext stores component IDs, calculations triggered on selection:
```typescript
// BuilderProvider reduces to:
{
  components: { cpu_id: 1, ram_spec_id: 5, ... },
  calculations: { base_price, adjusted_price, metrics, breakdown },
  isCalculating: boolean,
  lastCalculated: timestamp
}
```

### Debounce Implementation
Use React Query with debounce on component changes:
```typescript
const { data: valuation } = useQuery({
  queryKey: ['builder', components],
  queryFn: () => calculateBuildValuation(components),
  enabled: !!components.cpu_id,
  staleTime: 5 * 60 * 1000, // 5 minutes
  debounceTime: 300 // 300ms
});
```

## Testing Strategy

- **Unit Tests**: BuilderService methods (validation, calculations)
- **Integration Tests**: Full builder workflows (select → calculate → save → share)
- **Component Tests**: ComponentCard, ValuationPanel rendering with different states
- **API Tests**: Endpoint contracts, error handling
- **E2E Tests**: Complete user flows in Playwright/Cypress
- **Performance Tests**: <300ms calculation time, page load <2s

---

**Document Version**: 1.0
**Last Updated**: 2025-11-12
**Status**: Ready for Implementation
**Next Step**: Stakeholder review and approval before Phase 1 starts
