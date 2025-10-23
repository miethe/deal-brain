# Technical Architecture & Design

**Status:** Draft
**Last Updated:** October 22, 2025

---

## Component Architecture

### Client-Server Data Flow

```
┌─────────────────────────────────────────────┐
│ Server Component: /listings/[id]/page.tsx   │
│                                             │
│ 1. Fetch listing (all relationships)        │
│ 2. Call notFound() if not found             │
│ 3. Generate metadata for SEO                │
│ 4. Render DetailPageLayout                  │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ DetailPageLayout (Client Component)         │
│                                             │
│ ├─ Breadcrumb                               │
│ ├─ DetailPageHero                           │
│ │  ├─ ProductImage                          │
│ │  └─ SummaryCardsGrid                      │
│ └─ DetailPageTabs                           │
│    ├─ SpecificationsTab                     │
│    │  ├─ EntityLink (with tooltip)          │
│    │  └─ EntityTooltip (HoverCard)          │
│    ├─ ValuationTab                          │
│    │  ├─ RuleCards (max 4)                  │
│    │  └─ ValuationBreakdownModal            │
│    │     ├─ Contributors section             │
│    │     └─ Inactive section (collapsible)   │
│    ├─ HistoryTab                            │
│    └─ NotesTab (placeholder)                │
└─────────────────────────────────────────────┘
```

### Data Flow Diagram

```
User navigates to /listings/[id]
         ↓
Server fetches listing with relationships:
  - Eager load CPU, GPU, RAM, Storage, Ports
  - Generate valuation breakdown
         ↓
Server renders page with initial data
         ↓
Client hydrates components
         ↓
On entity hover:
  - Tooltip trigger (200ms delay)
  - Client queries entity details
  - React Query caches result
  - HoverCard displays data
         ↓
User clicks "View Full Breakdown":
  - Open ValuationBreakdownModal
  - Fetch breakdown (cached if recent)
  - Sort rules into contributors/inactive
  - Render with section headers
         ↓
User clicks rule name:
  - Navigate to /valuation/rules/[id]
  - Modal remains open (user navigates in new tab)
```

---

## State Management

### React Query Strategy

**Listing Data Cache:**

```typescript
// Primary cache for detail page
queryKey: ['listing', 'detail', listingId]
staleTime: 5 * 60 * 1000     // 5 minutes
cacheTime: 10 * 60 * 1000    // 10 minutes
refetchOnWindowFocus: false  // Already fresh from SSR

// Use case: Detail page, avoid refetch on focus
```

**Valuation Breakdown Cache:**

```typescript
queryKey: ['listing', 'valuation', listingId]
staleTime: 5 * 60 * 1000     // 5 minutes
cacheTime: 10 * 60 * 1000    // 10 minutes

// Use case: Valuation modal, separate cache from listing
```

**Entity Data Cache (Tooltips):**

```typescript
queryKey: ['cpu', cpuId]
staleTime: 30 * 60 * 1000    // 30 minutes (entity data stable)
cacheTime: 60 * 60 * 1000    // 1 hour
enabled: isHovered && !!cpuId // Only fetch on hover

// Similar for: gpu, ram-spec, storage-profile
```

### Invalidation Strategy

**On Listing Edit/Save:**

```typescript
// Invalidate all listing-related queries
queryClient.invalidateQueries({
  queryKey: ['listing']        // Matches all listing* keys
})

// Also invalidate related caches
queryClient.invalidateQueries({
  queryKey: ['listings', 'records']
})
queryClient.invalidateQueries({
  queryKey: ['listings', 'count']
})
```

---

## Performance Optimization

### Code Splitting

**Tab Content Lazy Loading:**

```typescript
const SpecificationsTab = lazy(() =>
  import('./specifications-tab')
)
const ValuationTab = lazy(() =>
  import('./valuation-tab-page')
)
const HistoryTab = lazy(() =>
  import('./history-tab')
)

// Suspense boundary with loading skeleton
<Suspense fallback={<TabSkeleton />}>
  <TabContent />
</Suspense>
```

### Image Optimization

**Next.js Image Component:**

```typescript
<Image
  src={thumbnail_url || fallbackIcon}
  alt={listing.title}
  width={400}
  height={400}
  priority={true}              // Above fold
  placeholder="blur"            // LQIP blur
  blurDataURL={dataUrl}        // Base64 placeholder
  sizes="(max-width: 768px) 100vw,
         (max-width: 1024px) 400px,
         400px"
  quality={85}                 // Optimize file size
/>
```

### Memoization Strategy

**Expensive Computations:**

```typescript
// Memoize rule sorting/filtering
const filteredRules = useMemo(() => {
  return sortRulesByImpact(rules);
}, [rules])

// Memoize component with React.memo
const RuleCard = React.memo(({ rule }) => (
  <div>{rule.name}</div>
))

// Memoize callbacks
const handleRuleClick = useCallback((ruleId) => {
  navigate(`/valuation/rules/${ruleId}`);
}, [navigate])
```

---

## Accessibility Implementation

### Keyboard Navigation

**Modal Focus Management:**

```typescript
// In ValuationBreakdownModal
useEffect(() => {
  // Focus first focusable element when modal opens
  const firstFocusable = modalRef.current?.querySelector(
    'button, a, input'
  )
  firstFocusable?.focus()

  // Focus trap: prevent Tab from leaving modal
  return handleKeyboardTrap(modalRef.current)
}, [isOpen])
```

**Tab Navigation with Arrow Keys:**

```typescript
// Tab bar handles left/right arrows
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'ArrowRight') {
    focusNextTab()
  } else if (e.key === 'ArrowLeft') {
    focusPreviousTab()
  }
}
```

### ARIA Attributes

**Rule Section Headers:**

```tsx
<h2
  id="contributors-section"
  className="text-sm font-semibold..."
>
  ACTIVE CONTRIBUTORS ({count})
</h2>
<div aria-labelledby="contributors-section">
  {/* Rules in this section */}
</div>
```

**Icon Buttons:**

```tsx
<button aria-label="Edit listing">
  <EditIcon />
</button>

<button aria-label="Delete listing">
  <TrashIcon />
</button>
```

**Badge Annotations:**

```tsx
<Badge
  variant="outline"
  aria-label={`Belongs to ${ruleGroup}`}
>
  {ruleGroup}
</Badge>
```

---

## Caching Strategy

### Multi-Layer Cache

```
┌──────────────────────────────────────┐
│ Browser HTTP Cache (Static assets)   │
│ TTL: 1 year for versioned files      │
└──────────────────────────────────────┘
         ↓
┌──────────────────────────────────────┐
│ Next.js ISR (Incremental Static)     │
│ TTL: 60 seconds for detail pages     │
└──────────────────────────────────────┘
         ↓
┌──────────────────────────────────────┐
│ React Query Client Cache             │
│ TTL: 5 minutes (stale time)          │
│ Network: Fetches when stale          │
└──────────────────────────────────────┘
         ↓
┌──────────────────────────────────────┐
│ API Server (Database)                │
│ Response: JSON with full data        │
└──────────────────────────────────────┘
```

### Cache Invalidation Events

**User Actions:**
- Create listing → Invalidate `['listings', 'records']`, `['listings', 'count']`
- Edit listing → Invalidate `['listing', 'detail', id]`, `['listing', 'valuation', id]`
- Change settings → Invalidate all affected caches

**Time-Based:**
- Listing detail: 5 minutes (stale time)
- Entity data: 30 minutes (stable reference data)

---

## Error Handling

### API Error Strategy

```typescript
// On listing detail fetch failure
const { isError, error } = useQuery({
  queryKey: ['listing', 'detail', id],
  queryFn: () => apiFetch(`/v1/listings/${id}`),
  retry: 3,
  retryDelay: (attemptIndex) =>
    Math.min(1000 * 2 ** attemptIndex, 30000),
  onError: (error) => {
    if (error.status === 404) {
      notFound()  // Trigger 404 page
    } else {
      showErrorToast('Unable to load listing')
    }
  }
})
```

### Graceful Degradation

```typescript
// Missing entity relationships
{cpu ? (
  <EntityLink type="cpu" id={cpu.id} name={cpu.name} />
) : (
  <span className="text-muted-foreground">Not specified</span>
)}

// Missing image
{image ? (
  <Image src={image} alt={title} />
) : (
  <FallbackIcon />
)}
```

---

## Testing Strategy

### Unit Test Examples

**RuleCard Component:**

```typescript
test('renders rule card with name and amount', () => {
  const rule = { id: 1, name: 'Test Rule', adjustment_amount: -50 }
  const { getByText } = render(<RuleCard rule={rule} />)

  expect(getByText('Test Rule')).toBeInTheDocument()
  expect(getByText('-$50.00')).toBeInTheDocument()
})

test('applies correct color for savings', () => {
  const rule = { adjustment_amount: -50 }
  const { getByText } = render(<RuleCard rule={rule} />)

  expect(getByText('-$50.00')).toHaveClass('text-emerald-600')
})
```

**Rule Filtering Logic:**

```typescript
test('filters rules to max 4 contributors', () => {
  const rules = generateTestRules(10)  // 10 rules
  const filtered = filterTopRules(rules)

  expect(filtered).toHaveLength(4)
  expect(filtered.every(r => r.adjustment_amount !== 0)).toBe(true)
})
```

### Integration Test Examples

**Detail Page Navigation:**

```typescript
test('navigates from detail page to CPU detail', async () => {
  const { getByText } = render(<ListingDetailPage listing={listing} />)

  const cpuLink = getByText('Intel Core i7-1165G7')
  fireEvent.click(cpuLink)

  expect(router.pathname).toBe('/catalog/cpus/45')
})
```

---

## Deployment Considerations

### Backend Deployment

1. **Database Migrations** (if schema changes)
   ```bash
   poetry run alembic upgrade head
   ```

2. **API Deployment**
   - Enhanced endpoints ready before frontend
   - Maintain backward compatibility during rollout
   - Feature flags for new API fields (optional)

3. **Verification**
   ```bash
   curl http://api/v1/listings/123 \
     -H "Authorization: Bearer $TOKEN" | jq .rule_group_name
   ```

### Frontend Deployment

1. **Build**
   ```bash
   cd apps/web
   pnpm build
   ```

2. **Deploy**
   - Vercel automatic deployment from git
   - Environment variables: NEXT_PUBLIC_API_URL
   - Preload critical chunks

3. **Verification**
   - Detail page loads: `/listings/123`
   - Tooltips appear on hover
   - Responsive on mobile

---

## Monitoring & Observability

### Key Metrics to Monitor

**Frontend:**
- LCP (Largest Contentful Paint): target < 2.5s
- FID (First Input Delay): target < 100ms
- CLS (Cumulative Layout Shift): target < 0.1
- Error rate: target < 1%

**Backend:**
- API response time (p95): target < 500ms
- Database query time: target < 200ms
- Error rate: target < 0.1%

### Logging Strategy

```typescript
// Log important user actions
logger.info('listing_detail_viewed', { listingId, userId })
logger.info('entity_tooltip_shown', { entityType, entityId })
logger.info('valuation_breakdown_opened', { listingId })

// Log errors with context
logger.error('listing_fetch_failed', {
  listingId,
  status: error.status,
  message: error.message
})
```

---

## Security Considerations

### API Security

- Listing detail endpoint: Verify user has access to listing
- Input validation: ID parameter must be positive integer
- Rate limiting: 100 requests/minute per user
- Authentication: Clerk JWT token required

### XSS Prevention

```typescript
// React escapes HTML by default
<div>{listing.title}</div>  // Safe - automatically escaped

// Custom fields: validate schema
validateJSONSchema(listing.attributes)

// URLs: use URL constructor for validation
const url = new URL(listing.listing_url)
<a href={url.href} target="_blank">{url.hostname}</a>
```

---

## Related Documentation

- **[UI/UX Design](./ui-ux.md)** - Visual specifications
- **[Accessibility Guidelines](./accessibility.md)** - WCAG AA compliance
- **[Performance Optimization](./performance.md)** - Detailed performance strategy
- **[Technical Requirements](../requirements/technical.md)** - General technical needs
