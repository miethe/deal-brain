# Technical Requirements

**Status:** Draft
**Last Updated:** October 22, 2025

---

## Component Architecture

### Frontend Component Hierarchy

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

### New Files

**Frontend Components:**

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

## State Management

### React Query Cache Keys

```typescript
// Listings data
['listings', 'records', { page, filters }]          // Listings table data
['listings', 'count', { filters }]                  // Total count
['listings', 'single', listingId]                   // Single listing (modal)
['listing', 'detail', listingId]                    // Detail page (server prefetch)
['listing', 'valuation', listingId]                 // Valuation breakdown

// Entity data (for tooltips)
['cpu', cpuId]                                      // CPU tooltip data
['gpu', gpuId]                                      // GPU tooltip data
['ram-spec', ramSpecId]                             // RAM tooltip data
['storage-profile', storageProfileId]               // Storage tooltip data

// Other
['rulesets', 'active']                              // Active rulesets
```

### URL State

```typescript
/listings/[id]?tab=valuation                        // Active tab
/listings?highlight=123                             // Highlight new listing (optional)
```

### Zustand Store (Optional)

```typescript
interface ListingsStore {
  recentListingId: number | null;                   // Last created listing
  setRecentListingId: (id: number | null) => void;
}
```

---

## API Requirements

### Enhanced Endpoints

**1. Enhanced `/v1/listings/{id}` endpoint:**
   - Eager-load all relationships (CPU, GPU, RAM, Storage, Ports)
   - Include full entity data for tooltips (cores, TDP, marks, etc.)
   - Return 404 if listing not found
   - Response time target: <500ms (p95)

**2. Enhanced `/v1/listings/{id}/valuation-breakdown` endpoint:**
   - Add `rule_description` to each adjustment
   - Add `rule_group_id` and `rule_group_name` to each adjustment
   - Include ALL rules (active + inactive with zero adjustments)
   - Return parent ruleset information
   - Response time target: <500ms (p95)

**3. Entity Detail Endpoints (Verify Existing):**
   - `/v1/cpus/{id}` - For tooltip data
   - `/v1/gpus/{id}` - For tooltip data
   - `/v1/ram-specs/{id}` - For tooltip data
   - `/v1/storage-profiles/{id}` - For tooltip data

### Schema Enhancements

**ValuationAdjustment Schema (Backend):**

```python
class ValuationAdjustmentSchema(BaseModel):
    rule_id: int | None = None
    rule_name: str
    rule_description: str | None = None          # NEW
    rule_group_id: int | None = None             # NEW
    rule_group_name: str | None = None           # NEW
    adjustment_amount: Decimal
    actions: list[ValuationAdjustmentActionSchema]
```

---

## Dependencies

### Frontend Stack

**Required:**
- Next.js 14+ (App Router)
- React Query v5+
- Radix UI primitives (Dialog, Tabs, HoverCard, Collapsible)
- Tailwind CSS 3+
- shadcn/ui component library
- lucide-react (for icons)

**Optional:**
- Vercel Analytics (for performance monitoring)
- Sentry (for error tracking)
- Posthog (for user analytics)

### Backend Stack

- FastAPI with async SQLAlchemy
- Existing `/v1/listings` endpoints
- Enhanced `/v1/listings/{id}/valuation-breakdown` endpoint
- Entity detail endpoints (CPU, GPU, etc.)

---

## Performance Considerations

### Optimization Strategies

1. **Server-side render detail page** (Next.js App Router)
2. **Prefetch related entities** during initial load
3. **Memoize expensive computations** (rule sorting, filtering)
4. **React Query caching** with 5-minute stale time
5. **Image optimization** with Next.js Image component
6. **Code splitting for tabs** (lazy load content)

### Caching Strategy

- Detail page listing: cache for 5 minutes, invalidate on edit
- Entity data (CPU, GPU, etc.): cache for 30 minutes
- Tooltip data: fetch on hover, cache in React Query
- Valuation breakdown: cache for 5 minutes, invalidate on setting changes

### Image Optimization

- Use Next.js `<Image>` component for optimization
- Blur placeholder while loading (LQIP)
- Responsive sizing with srcset
- Lazy loading for below-fold images
- CDN hosting for thumbnails

---

## Accessibility (WCAG AA)

### Keyboard Navigation

- All interactive elements accessible via Tab
- Modal dialogs trap focus appropriately
- Links have visible focus indicators (ring: 2px with offset)
- Skip links for main content
- Arrow keys for tab navigation (optional)

### Screen Reader Support

- Semantic HTML (nav, main, article, section)
- ARIA labels for icon buttons (`aria-label`)
- ARIA live regions for dynamic content (toasts, loading states)
- Alt text for all images (from listing title)
- Section headers announced (`<h2>`, `<h3>`)
- Badge annotations with `aria-label`

### Visual Accessibility

- Color contrast ratio ≥ 4.5:1 for text
- Color not sole indicator of information (use icons + color)
- Resizable text up to 200% without loss of functionality
- Touch targets ≥ 44×44 pixels (critical on mobile)
- Focus indicators clearly visible (2px ring with offset)

### Testing Requirements

- Automated testing with axe-core
- Manual keyboard navigation testing
- Screen reader testing (NVDA, JAWS, VoiceOver)
- Color contrast verification with tools
- Mobile touch target verification

---

## Browser Support

**Desktop:**
- Chrome (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Edge (last 2 versions)

**Mobile:**
- iOS Safari 14+
- Android Chrome 10+
- Samsung Internet 14+

---

## Screen Size Support

- **Mobile:** 375px - 767px
- **Tablet:** 768px - 1023px
- **Desktop:** 1024px - 1920px
- **Ultra-wide:** 1920px+

---

## Scalability Requirements

- **Data Volume:** Support listings with 50+ valuation rules without performance degradation
- **Image Sizes:** Handle images up to 5MB with optimization
- **Custom Fields:** Support 20+ custom fields per listing
- **Concurrent Users:** Handle 100+ concurrent users viewing detail pages

---

## Security Requirements

### Authorization

- Verify user has permission to view listing (if multi-tenant)
- Row-level security (RLS) at database level
- API authentication via Clerk JWT tokens

### Input Validation

- Sanitize listing ID parameter to prevent injection
- Validate API responses before rendering
- Type validation with TypeScript

### XSS Prevention

- Escape all user-generated content (notes, custom fields)
- Use React's built-in XSS protection
- Content Security Policy (CSP) headers on responses

### CORS Configuration

- API endpoints properly configured for Next.js frontend
- Whitelist frontend origins in CORS headers
- Secure credential handling (tokens in httpOnly cookies)

---

## Testing Strategy

### Unit Tests

- Test component props and rendering
- Test filtering/sorting logic
- Test data transformations
- Target coverage: >80% for new components

**Testing Framework:** Jest + React Testing Library

### Integration Tests

- Test creation flow end-to-end
- Test detail page navigation
- Test tab switching and state persistence
- Test entity link navigation
- Test valuation breakdown modal
- Use React Testing Library for DOM interactions

### Accessibility Tests

- Automated with axe-core
- Manual keyboard navigation testing
- Screen reader testing (NVDA, VoiceOver)
- Color contrast verification

### Performance Tests

- Core Web Vitals: LCP < 2.5s, FID < 100ms, CLS < 0.1
- API response times: p95 < 500ms
- Use Lighthouse CI or Vercel Analytics
- Test on 3G connection simulation

---

## Related Documentation

- **[Data Model & Schema](./data-model.md)** - API contracts, TypeScript interfaces
- **[Detail Page Requirements](./detail-page.md)** - UI/UX specifications
- **[Design - Technical Architecture](../design/technical-design.md)** - Component data flow
- **[Design - Accessibility Guidelines](../design/accessibility.md)** - Detailed A11y specs
- **[Implementation Plan](../../IMPLEMENTATION_PLAN.md)** - Phased approach, tasks, timeline
