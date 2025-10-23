# Performance & Optimization Strategy

**Status:** Draft
**Last Updated:** October 22, 2025

---

## Core Web Vitals Targets

### Primary Metrics

**Largest Contentful Paint (LCP):**
- **Target:** < 2.5 seconds (75th percentile)
- **Measurement:** First significant paint (hero section)
- **Acceptable:** 2.5s - 4s (needs improvement)
- **Critical:** > 4s (poor)

**First Input Delay (FID):**
- **Target:** < 100ms (75th percentile)
- **Measurement:** Interactive element responsiveness
- **Acceptable:** 100ms - 300ms
- **Critical:** > 300ms

**Cumulative Layout Shift (CLS):**
- **Target:** < 0.1 (75th percentile)
- **Measurement:** Unexpected layout changes
- **Acceptable:** 0.1 - 0.25
- **Critical:** > 0.25

---

## Optimization Strategies

### Server-Side Rendering (SSR)

**Detail Page - Why SSR:**

```
1. HTML generated on server (not browser)
2. Listing data fetched server-side
3. Page delivered as complete HTML
4. JavaScript hydrates interactive elements
5. Faster First Contentful Paint (FCP)
```

**Implementation:**

```typescript
// apps/web/app/listings/[id]/page.tsx
export default async function ListingDetailPage({ params }) {
  const listing = await apiFetch(`/v1/listings/${params.id}`)

  if (!listing) {
    notFound()  // 404 page
  }

  return <DetailPageLayout listing={listing} />
}
```

**Benefits:**
- Faster FCP (HTML renders immediately)
- Better SEO (metadata in HTML)
- Reduced JavaScript bundle on client

---

### Image Optimization

**Next.js Image Component:**

```typescript
<Image
  src={thumbnail_url || fallbackIcon}
  alt={listing.title}
  width={400}
  height={400}

  // Optimization options
  priority={true}              // Above fold, load immediately
  placeholder="blur"           // Blur LQIP while loading
  blurDataURL={base64}        // Placeholder data
  quality={85}                // Reduce file size

  // Responsive sizes
  sizes="(max-width: 768px) 100vw,
         (max-width: 1024px) 400px,
         400px"

  // Lazy loading
  loading="lazy"              // Below fold images
/>
```

**Performance Impact:**

| Optimization | File Size | Load Time |
|-------------|-----------|-----------|
| Original JPEG | 150KB | 1.5s |
| Next.js Image (WebP, quality 85) | 45KB | 0.5s |
| LQIP Blur Placeholder | +2KB | Perceived speed |

**Image Hosting Strategy:**

```
CDN Priority:
1. Cloudinary/Imgix (if available) - Dynamic optimization
2. AWS CloudFront - Fast delivery
3. Next.js ISR Cache - Static resources
4. Fallback icons - No network needed
```

---

### Code Splitting & Lazy Loading

**Tab Content Splitting:**

```typescript
// Split each tab into separate JS bundle
const SpecificationsTab = lazy(() =>
  import('./specifications-tab').then(m => ({
    default: m.SpecificationsTab
  }))
)

const ValuationTab = lazy(() =>
  import('./valuation-tab-page')
)

const HistoryTab = lazy(() =>
  import('./history-tab')
)

// Suspense boundary with loading state
<Suspense fallback={<TabSkeleton />}>
  <TabContent />
</Suspense>
```

**Bundle Impact:**

```
Before: JavaScript bundle = 250KB (all tabs included)
After:  JavaScript bundle = 150KB
        + 35KB lazy-loaded per tab
        = Faster initial load
```

**Below-Fold Image Lazy Loading:**

```typescript
<Image
  src={secondary_storage_image}
  alt="Secondary storage"
  loading="lazy"              // Defer loading
  width={100}
  height={100}
/>
```

---

### React Query Caching

**Stale Time Configuration:**

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,           // 5 minutes
      cacheTime: 10 * 60 * 1000,          // 10 minutes
      refetchOnWindowFocus: false,        // SSR provides fresh data
      refetchOnMount: false,              // Trust cache
      retry: 2,                           // Retry failed requests
      retryDelay: exponentialBackoff,    // Exponential backoff
    },
  },
})
```

**Cache Keys & Stale Times:**

```typescript
// Listing detail - stable during session
['listing', 'detail', id]
staleTime: 5 * 60 * 1000  // 5 min

// Entity data - very stable
['cpu', id]
staleTime: 30 * 60 * 1000 // 30 min

// User settings - changes less frequently
['settings', userId]
staleTime: 60 * 60 * 1000 // 60 min
```

---

### Memoization

**Rule Sorting (Expensive):**

```typescript
const filteredAndSorted = useMemo(() => {
  // Without memo: recalculates every render
  // With memo: only recalculates when rules change

  const contributors = rules.filter(r => r.adjustment_amount !== 0)
  const sorted = contributors.sort((a, b) =>
    Math.abs(b.adjustment_amount) - Math.abs(a.adjustment_amount)
  )
  return sorted
}, [rules])  // Only runs when rules change
```

**Component Memoization:**

```typescript
// Prevent re-renders when props unchanged
const RuleCard = React.memo(({ rule, onNavigate }) => (
  <Card>{rule.name}</Card>
))

// With custom comparison
const DetailPageHero = React.memo(
  ({ listing, onImageLoad }) => (/* ... */),
  (prevProps, nextProps) => {
    // Custom comparison logic if needed
    return prevProps.listing.id === nextProps.listing.id
  }
)
```

**Callback Memoization:**

```typescript
const handleRuleClick = useCallback((ruleId) => {
  router.push(`/valuation/rules/${ruleId}`)
}, [router])

// Pass to child components without causing re-renders
<RuleCard rule={rule} onNavigate={handleRuleClick} />
```

---

### API Performance

**Endpoint Response Times (Targets):**

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| `GET /v1/listings/{id}` | 50ms | 200ms | 500ms |
| `GET /v1/listings/{id}/valuation-breakdown` | 100ms | 250ms | 500ms |
| `GET /v1/cpus/{id}` | 20ms | 50ms | 100ms |

**Optimization on Backend:**

```python
# Eager load relationships to avoid N+1 queries
stmt = (
    select(Listing)
    .where(Listing.id == id)
    .options(
        selectinload(Listing.cpu),
        selectinload(Listing.gpu),
        selectinload(Listing.ram_spec),
        selectinload(Listing.ports_profile).selectinload(PortsProfile.ports),
    )
)
```

**Pagination for Large Lists:**

```python
# Valuation rules: paginate if > 50 rules
rules = get_valuation_rules(id, limit=50, offset=0)

# Specifications: limit custom fields
custom_fields = get_custom_fields(listing, limit=20)
```

---

## Performance Monitoring

### Client-Side Metrics

**Web Vitals Tracking:**

```typescript
// apps/web/lib/vitals.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals'

export function reportWebVitals(metric: any) {
  // Send to analytics service
  fetch('/api/vitals', {
    method: 'POST',
    body: JSON.stringify(metric),
  })
}

// Hook in _app or root layout
useEffect(() => {
  getCLS(reportWebVitals)
  getFID(reportWebVitals)
  getFCP(reportWebVitals)
  getLCP(reportWebVitals)
  getTTFB(reportWebVitals)
}, [])
```

**Performance Marks:**

```typescript
// Mark important moments
performance.mark('detail-page-start')
// ... load data
performance.mark('detail-page-end')
performance.measure('detail-page-load', 'detail-page-start', 'detail-page-end')
```

### Server-Side Metrics

**API Response Time Monitoring:**

```python
# FastAPI middleware
import time

@app.middleware("http")
async def add_timing(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    # Log to monitoring service
    logger.info(
        'api_request',
        duration=duration,
        path=request.url.path,
        method=request.method
    )

    return response
```

### Monitoring Tools

**Vercel Analytics (Recommended):**
- Real User Monitoring (RUM)
- Core Web Vitals tracking
- Automatic deployment performance tracking

**Google Analytics 4:**
- Web Vitals measurement protocol
- Custom events for feature tracking

**Prometheus + Grafana:**
- Backend metrics
- API response times
- Database query durations

**Sentry:**
- Error rate tracking
- Performance monitoring
- Session replay integration

---

## Performance Testing

### Lighthouse CI

```yaml
# lighthouse-ci.json
{
  "ci": {
    "collect": {
      "url": ["http://localhost:3000/listings/123"],
      "numberOfRuns": 3
    },
    "assert": {
      "preset": "lighthouse:recommended",
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.8 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }]
      }
    }
  }
}
```

### Load Testing

```bash
# Simulate 100 concurrent users
artillery quick --count 100 --num 1000 http://api/v1/listings/123
```

### Device Testing

**Real Device Performance:**

- iPhone 12 (iOS 15+): LCP < 2.5s on 4G
- Samsung Galaxy A12 (Android 11): LCP < 3s on 4G
- iPad Air (WiFi): LCP < 2s

**Chrome DevTools Simulation:**

```
Device: iPhone 12
Network: Fast 4G
CPU Throttling: 4x slowdown
Results: Still meets targets
```

---

## Performance Budget

### JavaScript Budget

**Target:**
- Initial bundle: < 100KB (gzipped)
- Detail page: < 150KB after SSR
- Tab lazy loads: < 50KB each

**Monitoring:**

```json
{
  "bundles": [
    {
      "name": "main",
      "maxSize": "100kb"
    },
    {
      "name": "detail-page",
      "maxSize": "50kb"
    }
  ]
}
```

### Network Budget

**Listing Detail Page (LCP = 2.5s on Fast 4G):**

```
HTML delivery: 500ms
CSS parsing: 300ms
JavaScript execution: 400ms
Image load: 700ms
API calls: 200ms
Margin: 100ms
Total: 2.2s (within budget)
```

---

## Degradation Strategy

**If Performance Targets Not Met:**

1. **Reduce Image Quality** (quality: 75)
2. **Implement Pagination** for large datasets
3. **Defer Non-Critical Data** (lazy load entity data)
4. **Service Worker Caching** (offline support)
5. **Static Generation** (ISR for common listings)

---

## Performance Checklist

### Development

- [ ] Use Next.js Image component for all images
- [ ] Enable code splitting for lazy-loaded components
- [ ] Memoize expensive computations
- [ ] Configure React Query stale times
- [ ] Profile components with React DevTools
- [ ] Audit bundle with webpack-bundle-analyzer

### Pre-Launch

- [ ] Run Lighthouse audit (target: 80+ performance)
- [ ] Run Lighthouse CI (automated checks)
- [ ] Load test API endpoints
- [ ] Test on real mobile devices
- [ ] Monitor Core Web Vitals
- [ ] Review error rates

### Post-Launch

- [ ] Monitor Vercel Analytics daily
- [ ] Alert on Core Web Vitals regression
- [ ] Weekly performance review
- [ ] Monthly optimization cycle
- [ ] Quarterly deep-dive audit

---

## Related Documentation

- **[Technical Architecture](./technical-design.md)** - Caching strategy, code splitting
- **[Technical Requirements](../requirements/technical.md)** - Performance targets
- **[Accessibility Guidelines](./accessibility.md)** - WCAG AA compliance
