# Product Requirements Document: CPU Catalog Page Reskin

**Version:** 1.0
**Date:** 2025-10-15
**Status:** Draft
**Project:** Deal Brain CPU Catalog Enhancement

---

## 1. Executive Summary

This PRD defines requirements for creating a comprehensive CPU Catalog page that transforms the current simple CPU table into an interactive, analysis-rich catalog experience. The enhancement introduces performance-based pricing metrics, multiple viewing modes, and detailed CPU analytics to help users make informed decisions about CPU value propositions based on both historical pricing and performance benchmarks.

### Key Deliverables

1. **New CPU Catalog Page** with dual-tab interface (Catalog + Data views)
2. **Performance-Based Pricing** showing target price ranges derived from actual listing data
3. **Performance Value Metrics** ($/PassMark calculations) with visual indicators
4. **Interactive CPU Detail Modal** with comprehensive specifications and analytics
5. **Enhanced API Endpoints** for CPU analytics and performance metrics

### Business Value

- Enables users to quickly identify CPUs offering best performance-per-dollar
- Provides data-driven pricing targets based on actual market data
- Creates consistent UI/UX with existing Listings page
- Reduces friction in CPU selection and evaluation workflow

---

## 2. Problem Statement

### Current State

The existing CPU page (`/cpus`) provides a basic table view listing CPU specifications without:
- Performance-based value metrics or pricing guidance
- Multiple viewing modes (grid, list, master-detail)
- Visual indicators for deal quality
- Interactive details modal for comprehensive CPU information
- Statistical analysis of CPU pricing based on actual listings

### User Pain Points

1. **Limited CPU Evaluation Tools:** Users cannot quickly assess whether a CPU offers good performance value
2. **No Pricing Context:** No guidance on what constitutes a "good price" for a specific CPU model
3. **Inconsistent UX:** CPU page differs significantly from the polished Listings catalog experience
4. **Missing Analytics:** No aggregate statistics showing historical pricing patterns across listings
5. **Poor Discoverability:** Users must navigate to individual listings to understand CPU market pricing

### Impact

Without performance-based valuation tools, users:
- Struggle to compare CPU value propositions across different models
- Cannot identify underpriced or overpriced listings relative to CPU performance
- Lack data-driven guidance for setting target prices
- Experience inconsistent navigation patterns between Catalog and CPU pages

---

## 3. Goals & Success Metrics

### Primary Goals

1. **Create Comprehensive CPU Catalog:** Build catalog view matching Listings page UX patterns
2. **Enable Performance-Based Valuation:** Provide $/PassMark metrics with visual quality indicators
3. **Display Statistical Pricing:** Show target price ranges derived from actual listing data
4. **Improve CPU Discovery:** Enable filtering, sorting, and multiple view modes
5. **Maintain Performance:** Ensure page renders efficiently with memoization and optimization

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Page Load Time | < 1.5s | Time to interactive (TTI) |
| Data Table Render | < 500ms | For 100+ CPUs |
| CPU Detail Modal Open | < 300ms | Modal render time |
| Filter Response Time | < 200ms | Debounced search latency |
| API Response Time | < 500ms | P95 for /v1/cpus/analytics |
| User Engagement | 40%+ increase | CPU page views per session |

### Key Results

- Users can evaluate CPU performance value within 3 clicks
- 90% of CPU pricing targets calculated from 5+ listing samples
- Zero accessibility violations (WCAG AA compliant)
- 100% feature parity with Listings catalog view modes

---

## 4. User Stories & Use Cases

### Primary User Stories

**US-1: Browse CPU Catalog**
```
As a Deal Brain user,
I want to browse CPUs in multiple view modes (grid, list, master-detail),
So that I can explore CPU options in my preferred layout.

Acceptance Criteria:
- View switcher allows toggling between grid, list, master-detail
- All view modes display key CPU specifications
- View preference persists across sessions
- Keyboard navigation works in all views
```

**US-2: View Performance-Based Pricing**
```
As a user evaluating CPU deals,
I want to see target price ranges based on actual listing data,
So that I can determine if a listing's CPU is fairly priced.

Acceptance Criteria:
- Each CPU shows "Good", "Great", "Fair" price ranges
- Ranges calculated from listing adjusted prices (± 1 std dev)
- Price indicators update when new listings added
- Insufficient sample size shows appropriate message
```

**US-3: Compare Performance Value**
```
As a user comparing CPU options,
I want to see $/PassMark metrics for both single and multi-thread performance,
So that I can identify which CPUs offer best performance per dollar.

Acceptance Criteria:
- Both single-thread and multi-thread metrics displayed
- Color-coded indicators (green=good, yellow=fair, red=poor)
- Metrics sortable in data table view
- Calculations based on adjusted listing prices
```

**US-4: View Detailed CPU Information**
```
As a user researching a specific CPU,
I want to click on any CPU to open a detailed modal,
So that I can view all specifications and performance analytics.

Acceptance Criteria:
- Modal opens from any view mode
- Shows all CPU model fields (cores, threads, TDP, benchmarks, etc.)
- Displays associated listings count and pricing statistics
- Includes performance value metrics and historical data
- Accessible via keyboard (ESC to close)
```

**US-5: Filter and Search CPUs**
```
As a user with specific requirements,
I want to filter CPUs by manufacturer, core count, TDP, and search by name,
So that I can quickly find CPUs matching my criteria.

Acceptance Criteria:
- Search input filters by CPU name (debounced 200ms)
- Dropdown filters for manufacturer, socket, generation
- Slider filters for core count and TDP ranges
- Filter state persists in URL query parameters
- Clear filters button resets all criteria
```

**US-6: Sort CPUs by Performance Metrics**
```
As a user prioritizing specific attributes,
I want to sort CPUs by price, performance, efficiency,
So that I can identify top options for my use case.

Acceptance Criteria:
- Sortable columns: Name, Cores, TDP, PassMark scores, $/PassMark, Price ranges
- Click column header to toggle sort direction
- Sort direction indicated by arrow icons
- Multi-column sort support (Shift+Click)
```

### Secondary User Stories

**US-7: View Listings for CPU**
```
As a user interested in a specific CPU,
I want to see all listings containing that CPU,
So that I can find available deals.

Acceptance Criteria:
- CPU detail modal shows associated listings count
- "View Listings" button navigates to filtered Listings page
- Listings page pre-filters by selected CPU
```

**US-8: Compare Multiple CPUs**
```
As a user deciding between CPU options,
I want to select multiple CPUs for side-by-side comparison,
So that I can evaluate differences in specifications and value.

Acceptance Criteria:
- Checkbox selection in grid/list views
- Compare button appears when 2+ CPUs selected
- Comparison modal shows specs in aligned columns
- Clear selections button
```

---

## 5. Functional Requirements

### 5.1 CPU Catalog Page Structure

**FR-1.1: Page Layout**
- Implement dual-tab interface: "Catalog" and "Data" tabs
- Header section with page title, description, and "Add CPU" button (admin only)
- Persistent state management using Zustand store
- URL synchronization for active tab, view mode, and filters

**FR-1.2: Catalog Tab Components**
- ListingsFilters component adapted for CPU filtering
- ViewSwitcher toggle (Grid | List | Master-Detail)
- Active view component (GridView, DenseListView, MasterDetailView)
- ErrorBoundary wrapper for graceful error handling

**FR-1.3: Data Tab Components**
- CPUsTable component with sortable, filterable columns
- Pagination controls (25, 50, 100, 200 rows per page)
- Column visibility selector
- Export to CSV button

### 5.2 View Modes

**FR-2.1: Grid View**
```
Layout: Responsive grid (1-4 columns based on viewport)
Card Content:
  - CPU name (heading)
  - Manufacturer badge
  - Key specs: Cores/Threads, TDP, Socket
  - PassMark scores (single/multi) with bars
  - Performance value indicators
  - Target price ranges
  - Click to open detail modal
```

**FR-2.2: List View (Dense)**
```
Layout: Compact list items
Row Content:
  - CPU name + manufacturer inline
  - Cores/Threads/TDP summary
  - Single-thread $/PassMark badge
  - Target price range (Good price emphasized)
  - Hover effect with quick actions
```

**FR-2.3: Master-Detail View**
```
Layout: Split screen (30% list | 70% detail panel)
Left Panel: Scrollable list of CPUs
Right Panel: Selected CPU details
  - All specifications
  - Performance charts
  - Pricing statistics
  - Associated listings list
```

### 5.3 Performance-Based Pricing

**FR-3.1: Target Price Calculation**

Calculate three price points per CPU based on adjusted listing prices:

```typescript
// Calculation Logic
interface PriceTarget {
  great: number;      // mean - (1 * stdDev)
  good: number;       // mean (average adjusted price)
  fair: number;       // mean + (1 * stdDev)
  sampleSize: number; // count of listings
  confidence: 'high' | 'medium' | 'low';
}

// Confidence levels
confidence =
  sampleSize >= 10 ? 'high' :
  sampleSize >= 5 ? 'medium' :
  sampleSize >= 2 ? 'low' : 'insufficient'
```

**FR-3.2: Price Display Requirements**
- Show all three price points with labels: "Great Deal", "Good Price", "Fair Price"
- Display confidence indicator (icon + tooltip)
- Include sample size: "Based on N listings"
- Show last updated timestamp
- Handle edge cases:
  - < 2 listings: "Insufficient data - check Listings page"
  - No listings: "No market data available"
  - High variance (stdDev > 30% of mean): "Wide price range - review listings"

**FR-3.3: Price Update Triggers**
- Recalculate when new listing added with this CPU
- Recalculate when listing price updated
- Recalculate when listing marked inactive/deleted
- Background task runs nightly to refresh all CPU prices

### 5.4 Performance Value Metrics

**FR-4.1: $/PassMark Calculation**

Calculate performance efficiency metrics:

```typescript
interface PerformanceValue {
  // Single-thread metrics
  dollarPerSingleMark: number;        // adjusted_price / cpu_mark_single
  dollarPerSingleMarkPercentile: number; // Percentile rank (0-100)

  // Multi-thread metrics
  dollarPerMultiMark: number;         // adjusted_price / cpu_mark_multi
  dollarPerMultiMarkPercentile: number;

  // Quality indicator
  valueRating: 'excellent' | 'good' | 'fair' | 'poor';
}

// Rating thresholds (percentile-based)
valueRating =
  percentile <= 25 ? 'excellent' :  // Top quartile efficiency
  percentile <= 50 ? 'good' :
  percentile <= 75 ? 'fair' : 'poor'
```

**FR-4.2: Value Display Requirements**
- Show both single-thread and multi-thread metrics
- Color-coded badges:
  - Excellent: Dark green with ↓↓ icon
  - Good: Medium green with ↓ icon
  - Fair: Yellow/gray with → icon
  - Poor: Red with ↑ icon
- Tooltip shows percentile rank and explanation
- Include comparative text: "Better than X% of CPUs"

**FR-4.3: Integration Points**
- Display in CPU card (grid view)
- Display in CPU row (list view)
- Display in detail modal
- Display in Listings table (new column)
- Display in Listing detail modal when CPU selected

### 5.5 CPU Detail Modal

**FR-5.1: Modal Structure**

```
Header:
  - CPU name (large heading)
  - Manufacturer badge
  - Close button (X)

Body Sections:
  1. Performance Overview
     - PassMark Multi-Thread score + bar chart
     - PassMark Single-Thread score + bar chart
     - iGPU Mark (if applicable)
     - Performance value badges

  2. Specifications
     - Cores / Threads
     - Base / Boost Clock (if available)
     - Socket
     - TDP
     - Release Year
     - iGPU Model

  3. Pricing Analytics
     - Target price ranges (Great/Good/Fair)
     - Confidence indicator
     - Sample size
     - Price history chart (future enhancement)

  4. Market Data
     - Associated listings count
     - "View Listings" button
     - Price distribution chart

  5. Additional Information
     - PassMark category
     - Notes field
     - Custom attributes (attributes_json)

Footer:
  - "Edit CPU" button (admin only)
  - "View Listings" button
  - Close button
```

**FR-5.2: Modal Behavior**
- Opens on click from any view mode
- Keyboard accessible (Tab navigation, ESC to close)
- Focus trap within modal when open
- Scroll lock on body when modal open
- Lazy load associated listings data
- Supports deep linking (`/cpus?detail=123`)

### 5.6 Filtering & Search

**FR-6.1: Search Input**
- Debounced search (200ms delay)
- Searches CPU name field
- Case-insensitive matching
- Highlights matched text in results
- Clear button (X icon)

**FR-6.2: Filter Controls**

```typescript
interface CPUFilters {
  manufacturer: string[];      // Multi-select: Intel, AMD, etc.
  socket: string[];            // Multi-select: LGA1700, AM5, etc.
  coreRange: [number, number]; // Slider: 2-64 cores
  tdpRange: [number, number];  // Slider: 15-280W
  releaseYear: number[];       // Multi-select or range
  hasIGPU: boolean | null;     // Checkbox: Yes/No/Any
  minPassMark: number | null;  // Input: Minimum benchmark score
}
```

**FR-6.3: Filter UI**
- Collapsible filter panel (desktop) or drawer (mobile)
- Filter chips show active filters
- "Clear all filters" button
- Filter count badge on filter button
- Persist filters in URL query params

### 5.7 Data Table View

**FR-7.1: Table Columns**

| Column | Sortable | Filterable | Width | Default Visible |
|--------|----------|------------|-------|-----------------|
| Name | Yes | Yes (search) | 250px | Yes |
| Manufacturer | Yes | Yes (dropdown) | 120px | Yes |
| Cores/Threads | Yes | Yes (range) | 100px | Yes |
| TDP (W) | Yes | Yes (range) | 80px | Yes |
| Socket | Yes | Yes (dropdown) | 100px | Yes |
| CPU Mark (Multi) | Yes | Yes (range) | 120px | Yes |
| CPU Mark (Single) | Yes | Yes (range) | 120px | Yes |
| $/Mark (Single) | Yes | No | 100px | Yes |
| $/Mark (Multi) | Yes | No | 100px | Yes |
| Target Price (Good) | Yes | No | 100px | Yes |
| iGPU Model | Yes | Yes (search) | 150px | No |
| iGPU Mark | Yes | Yes (range) | 100px | No |
| Release Year | Yes | Yes (range) | 100px | No |
| Listings Count | Yes | No | 80px | Yes |
| Actions | No | No | 100px | Yes |

**FR-7.2: Table Features**
- Row selection with checkboxes
- Row hover highlights
- Click row to open detail modal
- Context menu (right-click) for actions
- Column resizing (drag header borders)
- Column reordering (drag headers)
- Sticky header on scroll
- Virtualized scrolling for 500+ rows

**FR-7.3: Pagination**
- Page size selector: 25, 50, 100, 200
- Page navigation controls
- Display "Showing X-Y of Z results"
- Keyboard shortcuts (← → for prev/next)

---

## 6. Non-Functional Requirements

### 6.1 Performance

**NFR-1.1: Load Time**
- Initial page load: < 1.5s (includes data fetch)
- Client-side rendering: < 500ms (data already cached)
- Modal open animation: < 300ms
- Filter application: < 200ms (debounced)

**NFR-1.2: Optimization Strategies**
- React.memo() for all view components
- useMemo() for filtered/sorted data
- useCallback() for event handlers
- React Query caching (5 min stale time)
- Virtualized table rendering (react-window)
- Lazy loading for CPU detail modal content

**NFR-1.3: API Performance**
- GET /v1/cpus endpoint: < 500ms (P95)
- GET /v1/cpus/{id} endpoint: < 300ms (P95)
- GET /v1/cpus/{id}/analytics endpoint: < 800ms (P95)
- Database query optimization with proper indexes
- Response caching (Redis) for analytics data

### 6.2 Accessibility

**NFR-2.1: WCAG AA Compliance**
- All interactive elements keyboard navigable
- Screen reader announcements for state changes
- ARIA labels for all icons and controls
- Focus indicators visible (2px outline)
- Color contrast ratios >= 4.5:1

**NFR-2.2: Keyboard Navigation**
- Tab: Navigate through interactive elements
- Enter/Space: Activate buttons, open modals
- Escape: Close modals, clear search
- Arrow keys: Navigate table rows, filter options
- Home/End: Jump to first/last item

**NFR-2.3: Screen Reader Support**
- Announce filter application: "Showing 42 CPUs"
- Announce sort changes: "Sorted by CPU Mark, descending"
- Announce modal open: "CPU detail modal for Intel Core i7-13700K"
- Live regions for dynamic content updates

### 6.3 Responsive Design

**NFR-3.1: Breakpoints**
- Mobile: 320-639px (1 column grid, drawer filters)
- Tablet: 640-1023px (2 column grid)
- Desktop: 1024-1439px (3 column grid)
- Large Desktop: 1440px+ (4 column grid)

**NFR-3.2: Mobile Optimizations**
- Filter panel becomes bottom drawer
- Table becomes horizontally scrollable cards
- Modal becomes full-screen
- Reduced animations for lower-end devices
- Touch-optimized controls (44px min tap target)

### 6.4 Browser Support

**NFR-4.1: Supported Browsers**
- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions
- Safari: Last 2 versions
- Mobile Safari: iOS 14+
- Chrome Android: Last 2 versions

**NFR-4.2: Graceful Degradation**
- Polyfills for missing APIs
- Fallback styles for unsupported CSS features
- Error boundaries catch and display render errors
- Offline indicator when API unavailable

### 6.5 Data Integrity

**NFR-5.1: Validation**
- CPU data validated against schema
- Performance metrics validated (non-negative, reasonable ranges)
- Price statistics validated (non-null sample size)
- Handle missing/null values gracefully

**NFR-5.2: Error Handling**
- Network errors show retry button
- Invalid data shows error message
- Fallback values for missing metrics
- Sentry error tracking for production issues

---

## 7. Technical Architecture Overview

### 7.1 Frontend Architecture

**Component Structure:**
```
apps/web/app/cpus/
├── page.tsx                       # Main CPU page with tabs
├── _components/
│   ├── catalog-tab.tsx            # Catalog view container
│   ├── data-tab.tsx               # Data table view
│   ├── view-switcher.tsx          # Grid/List/Master-Detail toggle
│   ├── cpu-filters.tsx            # Filter panel
│   ├── grid-view.tsx              # CPU grid cards
│   ├── list-view.tsx              # Dense CPU list
│   ├── master-detail-view.tsx     # Split screen view
│   ├── cpu-card.tsx               # Individual CPU card
│   ├── cpu-detail-modal.tsx       # Full CPU details
│   ├── performance-badge.tsx      # $/PassMark indicator
│   ├── price-targets.tsx          # Great/Good/Fair prices
│   └── cpu-specifications.tsx     # Specs table

apps/web/components/cpus/
├── cpu-table.tsx                  # Sortable data table
├── cpu-compare-modal.tsx          # Side-by-side comparison
└── cpu-form.tsx                   # Add/Edit CPU form (admin)

apps/web/stores/
└── cpu-catalog-store.ts           # Zustand state management

apps/web/hooks/
├── use-cpu-analytics.ts           # Fetch analytics data
├── use-cpu-filters.ts             # Filter state management
└── use-cpu-performance.ts         # Performance metrics hook

apps/web/lib/
└── cpu-utils.ts                   # Utility functions
```

**State Management:**
```typescript
// cpu-catalog-store.ts
interface CPUCatalogState {
  // View state
  activeTab: 'catalog' | 'data';
  activeView: 'grid' | 'list' | 'master-detail';

  // Filters
  filters: CPUFilters;

  // Selection
  selectedCPUId: number | null;
  compareCPUs: number[];

  // Modals
  detailModalOpen: boolean;
  detailModalCPUId: number | null;
  compareModalOpen: boolean;

  // Actions
  setActiveTab: (tab) => void;
  setActiveView: (view) => void;
  setFilters: (filters) => void;
  toggleCompare: (cpuId) => void;
  openDetailModal: (cpuId) => void;
  // ...
}
```

### 7.2 Backend Architecture

**Service Layer:**
```python
# apps/api/dealbrain_api/services/cpu_analytics.py

class CPUAnalyticsService:
    """Service for CPU performance analytics and pricing"""

    async def get_cpu_price_targets(
        self,
        session: AsyncSession,
        cpu_id: int
    ) -> PriceTargetResult:
        """Calculate Great/Good/Fair price targets from listings"""

    async def get_cpu_performance_value(
        self,
        session: AsyncSession,
        cpu_id: int
    ) -> PerformanceValueResult:
        """Calculate $/PassMark metrics and percentile rank"""

    async def get_cpu_market_data(
        self,
        session: AsyncSession,
        cpu_id: int
    ) -> CPUMarketData:
        """Get associated listings and pricing distribution"""

    async def recalculate_all_cpu_metrics(
        self,
        session: AsyncSession
    ) -> None:
        """Background task to refresh all CPU analytics"""
```

**Database Changes:**
```sql
-- Add computed columns to CPU table
ALTER TABLE cpu ADD COLUMN price_target_good NUMERIC(10,2);
ALTER TABLE cpu ADD COLUMN price_target_great NUMERIC(10,2);
ALTER TABLE cpu ADD COLUMN price_target_fair NUMERIC(10,2);
ALTER TABLE cpu ADD COLUMN price_target_sample_size INTEGER DEFAULT 0;
ALTER TABLE cpu ADD COLUMN price_target_confidence VARCHAR(16);
ALTER TABLE cpu ADD COLUMN price_target_updated_at TIMESTAMP;

ALTER TABLE cpu ADD COLUMN dollar_per_mark_single NUMERIC(10,2);
ALTER TABLE cpu ADD COLUMN dollar_per_mark_multi NUMERIC(10,2);
ALTER TABLE cpu ADD COLUMN performance_value_percentile NUMERIC(5,2);
ALTER TABLE cpu ADD COLUMN performance_value_rating VARCHAR(16);
ALTER TABLE cpu ADD COLUMN performance_metrics_updated_at TIMESTAMP;

-- Add indexes for performance
CREATE INDEX idx_cpu_price_targets ON cpu(price_target_good, price_target_confidence);
CREATE INDEX idx_cpu_performance_value ON cpu(dollar_per_mark_single, dollar_per_mark_multi);
CREATE INDEX idx_cpu_manufacturer ON cpu(manufacturer);
CREATE INDEX idx_cpu_socket ON cpu(socket);
CREATE INDEX idx_cpu_cores ON cpu(cores);
CREATE INDEX idx_cpu_marks ON cpu(cpu_mark_single, cpu_mark_multi);
```

### 7.3 API Endpoints

**New Endpoints:**

```python
# GET /v1/cpus
# Returns list of CPUs with basic info + analytics
Response: List[CPUWithAnalytics]
  - id, name, manufacturer, specs
  - price_targets (good, great, fair, confidence, sample_size)
  - performance_value ($/mark metrics, rating, percentile)
  - listings_count

# GET /v1/cpus/{id}
# Returns single CPU with full details
Response: CPUDetail
  - All CPU model fields
  - Computed analytics
  - Associated listings summary

# GET /v1/cpus/{id}/analytics
# Returns detailed analytics for a CPU
Response: CPUAnalytics
  - price_targets with distribution
  - performance_value with comparison
  - market_data (listings, price history)
  - benchmark_percentiles

# GET /v1/cpus/{id}/listings
# Returns all listings containing this CPU
Response: List[ListingSummary]
  - Filtered and sorted by adjusted price

# POST /v1/cpus/recalculate-metrics
# Admin endpoint to trigger metric recalculation
Response: TaskStatus

# GET /v1/cpus/statistics
# Global CPU statistics for filtering
Response: CPUStatistics
  - manufacturers: List[string]
  - sockets: List[string]
  - core_range: [min, max]
  - tdp_range: [min, max]
  - year_range: [min, max]
```

**Updated Endpoints:**

```python
# GET /v1/listings
# Add CPU performance value to listing response
Response: ListingRecord
  - ... existing fields ...
  - cpu.performance_value_rating
  - cpu.dollar_per_mark_single
  - cpu.dollar_per_mark_multi
```

### 7.4 Data Flow

**Page Load:**
```
1. User navigates to /cpus
2. Next.js renders page shell (SSR)
3. React Query fetches /v1/cpus (client-side)
4. Backend query joins CPU + analytics columns
5. Response cached (5 min)
6. Components render with data
7. Store syncs with URL params
```

**Filter Application:**
```
1. User changes filter control
2. Debounced update to store (200ms)
3. Store triggers useMemo recalculation
4. Filtered list re-renders
5. URL params updated
6. No additional API calls (client-side filtering)
```

**Detail Modal:**
```
1. User clicks CPU card
2. Store opens modal with CPU ID
3. React Query fetches /v1/cpus/{id}/analytics
4. Loading spinner shows immediately
5. Modal renders with data
6. Chart data fetched lazily
7. Focus trapped in modal
```

**Metric Recalculation:**
```
1. Celery task runs nightly (cron: 2:00 AM UTC)
2. Service loops through all CPUs
3. For each CPU:
   a. Fetch associated listings (active only)
   b. Calculate price statistics (mean, stddev)
   c. Calculate performance value ($/mark, percentile)
   d. Update CPU row with computed values
4. Cache invalidation for /v1/cpus
5. Log summary (CPUs processed, errors)
```

---

## 8. Data Model & API Requirements

### 8.1 Database Schema Updates

**CPU Table Additions:**
```python
# apps/api/dealbrain_api/models/core.py

class Cpu(Base, TimestampMixin):
    __tablename__ = "cpu"

    # ... existing fields ...

    # Price Target Fields (from listing analytics)
    price_target_good: Mapped[float | None]
    price_target_great: Mapped[float | None]
    price_target_fair: Mapped[float | None]
    price_target_sample_size: Mapped[int] = mapped_column(default=0)
    price_target_confidence: Mapped[str | None] = mapped_column(String(16))
    price_target_stddev: Mapped[float | None]
    price_target_updated_at: Mapped[datetime | None]

    # Performance Value Fields ($/PassMark metrics)
    dollar_per_mark_single: Mapped[float | None]
    dollar_per_mark_multi: Mapped[float | None]
    performance_value_percentile: Mapped[float | None]
    performance_value_rating: Mapped[str | None] = mapped_column(String(16))
    performance_metrics_updated_at: Mapped[datetime | None]

    @property
    def has_sufficient_pricing_data(self) -> bool:
        return self.price_target_sample_size >= 2

    @property
    def price_targets_fresh(self) -> bool:
        if not self.price_target_updated_at:
            return False
        age = datetime.utcnow() - self.price_target_updated_at
        return age.days < 7
```

**Migration Script:**
```python
# apps/api/alembic/versions/xxx_add_cpu_analytics_fields.py

def upgrade():
    # Add new columns
    op.add_column('cpu', sa.Column('price_target_good', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('price_target_great', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('price_target_fair', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('price_target_sample_size', sa.Integer, server_default='0'))
    op.add_column('cpu', sa.Column('price_target_confidence', sa.String(16), nullable=True))
    op.add_column('cpu', sa.Column('price_target_stddev', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('price_target_updated_at', sa.DateTime, nullable=True))

    op.add_column('cpu', sa.Column('dollar_per_mark_single', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('dollar_per_mark_multi', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('performance_value_percentile', sa.Numeric(5,2), nullable=True))
    op.add_column('cpu', sa.Column('performance_value_rating', sa.String(16), nullable=True))
    op.add_column('cpu', sa.Column('performance_metrics_updated_at', sa.DateTime, nullable=True))

    # Add indexes
    op.create_index('idx_cpu_price_targets', 'cpu', ['price_target_good', 'price_target_confidence'])
    op.create_index('idx_cpu_performance_value', 'cpu', ['dollar_per_mark_single', 'dollar_per_mark_multi'])
    op.create_index('idx_cpu_manufacturer', 'cpu', ['manufacturer'])
    op.create_index('idx_cpu_socket', 'cpu', ['socket'])
    op.create_index('idx_cpu_cores', 'cpu', ['cores'])

def downgrade():
    op.drop_index('idx_cpu_cores')
    op.drop_index('idx_cpu_socket')
    op.drop_index('idx_cpu_manufacturer')
    op.drop_index('idx_cpu_performance_value')
    op.drop_index('idx_cpu_price_targets')

    op.drop_column('cpu', 'performance_metrics_updated_at')
    op.drop_column('cpu', 'performance_value_rating')
    op.drop_column('cpu', 'performance_value_percentile')
    op.drop_column('cpu', 'dollar_per_mark_multi')
    op.drop_column('cpu', 'dollar_per_mark_single')

    op.drop_column('cpu', 'price_target_updated_at')
    op.drop_column('cpu', 'price_target_stddev')
    op.drop_column('cpu', 'price_target_confidence')
    op.drop_column('cpu', 'price_target_sample_size')
    op.drop_column('cpu', 'price_target_fair')
    op.drop_column('cpu', 'price_target_great')
    op.drop_column('cpu', 'price_target_good')
```

### 8.2 Pydantic Schemas

**Core Schemas:**
```python
# packages/core/dealbrain_core/schemas/cpu.py

class PriceTarget(BaseModel):
    """CPU price target ranges from listing data"""
    good: float | None
    great: float | None
    fair: float | None
    sample_size: int
    confidence: Literal['high', 'medium', 'low', 'insufficient']
    stddev: float | None
    updated_at: datetime | None

class PerformanceValue(BaseModel):
    """CPU performance value metrics"""
    dollar_per_mark_single: float | None
    dollar_per_mark_multi: float | None
    percentile: float | None  # 0-100
    rating: Literal['excellent', 'good', 'fair', 'poor'] | None
    updated_at: datetime | None

class CPUAnalytics(BaseModel):
    """Computed analytics for a CPU"""
    price_targets: PriceTarget
    performance_value: PerformanceValue
    listings_count: int
    price_distribution: list[float]  # For histogram

class CPUWithAnalytics(CpuRead):
    """CPU with embedded analytics"""
    price_targets: PriceTarget
    performance_value: PerformanceValue
    listings_count: int

class CPUDetail(CPUWithAnalytics):
    """Full CPU details with related data"""
    associated_listings: list[ListingSummary]
    market_data: dict[str, Any]  # Charts, trends

class CPUStatistics(BaseModel):
    """Global CPU statistics for filters"""
    manufacturers: list[str]
    sockets: list[str]
    core_range: tuple[int, int]
    tdp_range: tuple[int, int]
    year_range: tuple[int, int]
    total_count: int
```

### 8.3 Service Implementation

**CPU Analytics Service:**
```python
# apps/api/dealbrain_api/services/cpu_analytics.py

from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from statistics import mean, stdev
from datetime import datetime, timedelta

class CPUAnalyticsService:

    @staticmethod
    async def calculate_price_targets(
        session: AsyncSession,
        cpu_id: int
    ) -> PriceTarget:
        """
        Calculate price targets from listing adjusted prices.

        Algorithm:
        1. Fetch all active listings with this CPU
        2. Extract adjusted_price_usd values
        3. Calculate mean and standard deviation
        4. Set targets: good=mean, great=mean-stddev, fair=mean+stddev
        5. Determine confidence based on sample size
        """

        # Query active listings with adjusted prices
        stmt = select(Listing.adjusted_price_usd).where(
            Listing.cpu_id == cpu_id,
            Listing.status == ListingStatus.ACTIVE,
            Listing.adjusted_price_usd.isnot(None),
            Listing.adjusted_price_usd > 0
        )
        result = await session.execute(stmt)
        prices = [row[0] for row in result.all()]

        if len(prices) < 2:
            return PriceTarget(
                good=None,
                great=None,
                fair=None,
                sample_size=len(prices),
                confidence='insufficient',
                stddev=None,
                updated_at=datetime.utcnow()
            )

        # Calculate statistics
        price_mean = mean(prices)
        price_stddev = stdev(prices) if len(prices) > 1 else 0

        # Determine confidence
        if len(prices) >= 10:
            confidence = 'high'
        elif len(prices) >= 5:
            confidence = 'medium'
        else:
            confidence = 'low'

        return PriceTarget(
            good=round(price_mean, 2),
            great=round(max(price_mean - price_stddev, 0), 2),
            fair=round(price_mean + price_stddev, 2),
            sample_size=len(prices),
            confidence=confidence,
            stddev=round(price_stddev, 2),
            updated_at=datetime.utcnow()
        )

    @staticmethod
    async def calculate_performance_value(
        session: AsyncSession,
        cpu_id: int
    ) -> PerformanceValue:
        """
        Calculate $/PassMark metrics and percentile ranking.

        Algorithm:
        1. Get CPU benchmark scores
        2. Calculate average listing adjusted price
        3. Compute $/mark ratios
        4. Calculate percentile rank across all CPUs
        5. Assign rating based on quartiles
        """

        # Fetch CPU with benchmark scores
        cpu = await session.get(Cpu, cpu_id)
        if not cpu or not cpu.cpu_mark_single or not cpu.cpu_mark_multi:
            return PerformanceValue(
                dollar_per_mark_single=None,
                dollar_per_mark_multi=None,
                percentile=None,
                rating=None,
                updated_at=datetime.utcnow()
            )

        # Calculate average adjusted price from listings
        stmt = select(func.avg(Listing.adjusted_price_usd)).where(
            Listing.cpu_id == cpu_id,
            Listing.status == ListingStatus.ACTIVE,
            Listing.adjusted_price_usd.isnot(None)
        )
        avg_price = await session.scalar(stmt)

        if not avg_price:
            return PerformanceValue(
                dollar_per_mark_single=None,
                dollar_per_mark_multi=None,
                percentile=None,
                rating=None,
                updated_at=datetime.utcnow()
            )

        # Calculate $/mark ratios (lower is better)
        dollar_per_single = avg_price / cpu.cpu_mark_single
        dollar_per_multi = avg_price / cpu.cpu_mark_multi

        # Calculate percentile rank
        # Count CPUs with better (lower) $/mark ratios
        stmt = select(func.count(Cpu.id)).where(
            Cpu.dollar_per_mark_single < dollar_per_single,
            Cpu.dollar_per_mark_single.isnot(None)
        )
        better_count = await session.scalar(stmt) or 0

        stmt = select(func.count(Cpu.id)).where(
            Cpu.dollar_per_mark_single.isnot(None)
        )
        total_count = await session.scalar(stmt) or 1

        percentile = (better_count / total_count) * 100

        # Assign rating
        if percentile <= 25:
            rating = 'excellent'
        elif percentile <= 50:
            rating = 'good'
        elif percentile <= 75:
            rating = 'fair'
        else:
            rating = 'poor'

        return PerformanceValue(
            dollar_per_mark_single=round(dollar_per_single, 2),
            dollar_per_mark_multi=round(dollar_per_multi, 2),
            percentile=round(percentile, 1),
            rating=rating,
            updated_at=datetime.utcnow()
        )

    @staticmethod
    async def update_cpu_analytics(
        session: AsyncSession,
        cpu_id: int
    ) -> None:
        """Update all analytics fields for a CPU"""

        price_targets = await CPUAnalyticsService.calculate_price_targets(session, cpu_id)
        perf_value = await CPUAnalyticsService.calculate_performance_value(session, cpu_id)

        cpu = await session.get(Cpu, cpu_id)
        if not cpu:
            return

        # Update price target fields
        cpu.price_target_good = price_targets.good
        cpu.price_target_great = price_targets.great
        cpu.price_target_fair = price_targets.fair
        cpu.price_target_sample_size = price_targets.sample_size
        cpu.price_target_confidence = price_targets.confidence
        cpu.price_target_stddev = price_targets.stddev
        cpu.price_target_updated_at = price_targets.updated_at

        # Update performance value fields
        cpu.dollar_per_mark_single = perf_value.dollar_per_mark_single
        cpu.dollar_per_mark_multi = perf_value.dollar_per_mark_multi
        cpu.performance_value_percentile = perf_value.percentile
        cpu.performance_value_rating = perf_value.rating
        cpu.performance_metrics_updated_at = perf_value.updated_at

        await session.flush()

    @staticmethod
    async def recalculate_all_cpu_metrics(
        session: AsyncSession
    ) -> dict[str, int]:
        """Background task to refresh all CPU analytics"""

        stmt = select(Cpu.id)
        result = await session.execute(stmt)
        cpu_ids = [row[0] for row in result.all()]

        success_count = 0
        error_count = 0

        for cpu_id in cpu_ids:
            try:
                await CPUAnalyticsService.update_cpu_analytics(session, cpu_id)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to update CPU {cpu_id}: {e}")
                error_count += 1

        await session.commit()

        return {
            'total': len(cpu_ids),
            'success': success_count,
            'errors': error_count
        }
```

### 8.4 API Endpoint Implementation

**Catalog Endpoints:**
```python
# apps/api/dealbrain_api/api/catalog.py

@router.get("/cpus", response_model=list[CPUWithAnalytics])
async def list_cpus(
    session: AsyncSession = Depends(session_dependency),
    include_analytics: bool = Query(default=True)
) -> Sequence[CPUWithAnalytics]:
    """
    List all CPUs with optional analytics data.

    Analytics fields are pre-computed and stored in CPU table,
    so this query is fast even with analytics enabled.
    """

    stmt = select(Cpu).order_by(Cpu.name)
    result = await session.execute(stmt)
    cpus = result.scalars().all()

    # Transform to schema with analytics
    response = []
    for cpu in cpus:
        cpu_dict = CpuRead.model_validate(cpu).model_dump()

        if include_analytics:
            # Add embedded analytics from CPU table
            cpu_dict['price_targets'] = PriceTarget(
                good=cpu.price_target_good,
                great=cpu.price_target_great,
                fair=cpu.price_target_fair,
                sample_size=cpu.price_target_sample_size or 0,
                confidence=cpu.price_target_confidence or 'insufficient',
                stddev=cpu.price_target_stddev,
                updated_at=cpu.price_target_updated_at
            )

            cpu_dict['performance_value'] = PerformanceValue(
                dollar_per_mark_single=cpu.dollar_per_mark_single,
                dollar_per_mark_multi=cpu.dollar_per_mark_multi,
                percentile=cpu.performance_value_percentile,
                rating=cpu.performance_value_rating,
                updated_at=cpu.performance_metrics_updated_at
            )

            # Count associated listings
            stmt = select(func.count(Listing.id)).where(
                Listing.cpu_id == cpu.id,
                Listing.status == ListingStatus.ACTIVE
            )
            cpu_dict['listings_count'] = await session.scalar(stmt) or 0

        response.append(CPUWithAnalytics(**cpu_dict))

    return response


@router.get("/cpus/{cpu_id}", response_model=CPUDetail)
async def get_cpu_detail(
    cpu_id: int,
    session: AsyncSession = Depends(session_dependency)
) -> CPUDetail:
    """Get detailed CPU information with analytics and market data"""

    cpu = await session.get(Cpu, cpu_id)
    if not cpu:
        raise HTTPException(status_code=404, detail="CPU not found")

    # Build base response
    cpu_dict = CpuRead.model_validate(cpu).model_dump()

    # Add analytics
    cpu_dict['price_targets'] = PriceTarget(
        good=cpu.price_target_good,
        great=cpu.price_target_great,
        fair=cpu.price_target_fair,
        sample_size=cpu.price_target_sample_size or 0,
        confidence=cpu.price_target_confidence or 'insufficient',
        stddev=cpu.price_target_stddev,
        updated_at=cpu.price_target_updated_at
    )

    cpu_dict['performance_value'] = PerformanceValue(
        dollar_per_mark_single=cpu.dollar_per_mark_single,
        dollar_per_mark_multi=cpu.dollar_per_mark_multi,
        percentile=cpu.performance_value_percentile,
        rating=cpu.performance_value_rating,
        updated_at=cpu.performance_metrics_updated_at
    )

    # Fetch associated listings
    stmt = select(Listing).where(
        Listing.cpu_id == cpu_id,
        Listing.status == ListingStatus.ACTIVE
    ).order_by(Listing.adjusted_price_usd.asc().nulls_last()).limit(10)
    result = await session.execute(stmt)
    listings = result.scalars().all()

    cpu_dict['associated_listings'] = [
        ListingSummary.model_validate(listing) for listing in listings
    ]
    cpu_dict['listings_count'] = len(listings)

    # Add market data (price distribution for histogram)
    stmt = select(Listing.adjusted_price_usd).where(
        Listing.cpu_id == cpu_id,
        Listing.status == ListingStatus.ACTIVE,
        Listing.adjusted_price_usd.isnot(None)
    )
    result = await session.execute(stmt)
    prices = [row[0] for row in result.all()]

    cpu_dict['market_data'] = {
        'price_distribution': prices,
        'listings_total': len(prices)
    }

    return CPUDetail(**cpu_dict)


@router.get("/cpus/statistics", response_model=CPUStatistics)
async def get_cpu_statistics(
    session: AsyncSession = Depends(session_dependency)
) -> CPUStatistics:
    """Get global CPU statistics for filter options"""

    # Get unique manufacturers
    stmt = select(Cpu.manufacturer).distinct().where(Cpu.manufacturer.isnot(None))
    result = await session.execute(stmt)
    manufacturers = sorted([row[0] for row in result.all()])

    # Get unique sockets
    stmt = select(Cpu.socket).distinct().where(Cpu.socket.isnot(None))
    result = await session.execute(stmt)
    sockets = sorted([row[0] for row in result.all()])

    # Get core range
    stmt = select(func.min(Cpu.cores), func.max(Cpu.cores)).where(Cpu.cores.isnot(None))
    core_range = await session.execute(stmt)
    core_min, core_max = core_range.one()

    # Get TDP range
    stmt = select(func.min(Cpu.tdp_w), func.max(Cpu.tdp_w)).where(Cpu.tdp_w.isnot(None))
    tdp_range = await session.execute(stmt)
    tdp_min, tdp_max = tdp_range.one()

    # Get year range
    stmt = select(func.min(Cpu.release_year), func.max(Cpu.release_year)).where(Cpu.release_year.isnot(None))
    year_range = await session.execute(stmt)
    year_min, year_max = year_range.one()

    # Get total count
    stmt = select(func.count(Cpu.id))
    total_count = await session.scalar(stmt)

    return CPUStatistics(
        manufacturers=manufacturers,
        sockets=sockets,
        core_range=(core_min or 2, core_max or 64),
        tdp_range=(tdp_min or 15, tdp_max or 280),
        year_range=(year_min or 2015, year_max or 2025),
        total_count=total_count or 0
    )


@router.post("/cpus/recalculate-metrics", status_code=202)
async def trigger_metric_recalculation(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(session_dependency)
) -> dict[str, str]:
    """
    Trigger background recalculation of all CPU metrics.
    Admin-only endpoint.
    """

    background_tasks.add_task(
        CPUAnalyticsService.recalculate_all_cpu_metrics,
        session
    )

    return {
        "status": "accepted",
        "message": "Metric recalculation task started"
    }
```

---

## 9. UI/UX Requirements

### 9.1 Visual Design Patterns

**Design System Alignment:**
- Follow existing Deal Brain component library (shadcn/ui)
- Match Listings page aesthetic and spacing
- Use consistent color palette from CSS variables
- Maintain 8px grid system for spacing

**Color Coding:**
```css
/* Performance Value Badges */
--cpu-value-excellent: hsl(142, 76%, 36%);  /* Dark green */
--cpu-value-good: hsl(142, 71%, 45%);       /* Medium green */
--cpu-value-fair: hsl(47, 100%, 50%);       /* Yellow */
--cpu-value-poor: hsl(0, 84%, 60%);         /* Red */

/* Price Target Indicators */
--price-great: hsl(142, 76%, 36%);          /* Dark green */
--price-good: hsl(142, 71%, 45%);           /* Medium green */
--price-fair: hsl(47, 100%, 50%);           /* Yellow */

/* Confidence Indicators */
--confidence-high: hsl(142, 71%, 45%);
--confidence-medium: hsl(47, 100%, 50%);
--confidence-low: hsl(0, 84%, 60%);
```

### 9.2 Component Specifications

**CPU Card (Grid View):**
```tsx
<Card className="cpu-card hover:shadow-lg transition-shadow">
  <CardHeader>
    <CardTitle>{cpu.name}</CardTitle>
    <Badge variant="secondary">{cpu.manufacturer}</Badge>
  </CardHeader>

  <CardContent className="space-y-3">
    {/* Key Specs */}
    <div className="grid grid-cols-2 gap-2 text-sm">
      <div>
        <span className="text-muted-foreground">Cores:</span>
        <span className="font-medium">{cpu.cores}/{cpu.threads}</span>
      </div>
      <div>
        <span className="text-muted-foreground">TDP:</span>
        <span className="font-medium">{cpu.tdp_w}W</span>
      </div>
      <div>
        <span className="text-muted-foreground">Socket:</span>
        <span className="font-medium">{cpu.socket}</span>
      </div>
    </div>

    {/* PassMark Scores */}
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span>Single-Thread</span>
        <span className="font-medium">{cpu.cpu_mark_single}</span>
      </div>
      <Progress value={(cpu.cpu_mark_single / 5000) * 100} />

      <div className="flex justify-between text-xs">
        <span>Multi-Thread</span>
        <span className="font-medium">{cpu.cpu_mark_multi}</span>
      </div>
      <Progress value={(cpu.cpu_mark_multi / 50000) * 100} />
    </div>

    {/* Performance Value Badge */}
    <PerformanceBadge
      rating={cpu.performance_value.rating}
      dollarPerMark={cpu.performance_value.dollar_per_mark_single}
    />

    {/* Price Targets */}
    <PriceTargets targets={cpu.price_targets} />
  </CardContent>

  <CardFooter>
    <Button
      variant="outline"
      className="w-full"
      onClick={() => openDetailModal(cpu.id)}
    >
      View Details
    </Button>
  </CardFooter>
</Card>
```

**Performance Badge Component:**
```tsx
interface PerformanceBadgeProps {
  rating: 'excellent' | 'good' | 'fair' | 'poor' | null;
  dollarPerMark: number | null;
}

export function PerformanceBadge({ rating, dollarPerMark }: PerformanceBadgeProps) {
  if (!rating || !dollarPerMark) {
    return (
      <Badge variant="secondary" className="w-full justify-center">
        <MinusIcon className="mr-1 h-3 w-3" />
        No data
      </Badge>
    );
  }

  const config = {
    excellent: {
      color: 'bg-green-600 text-white',
      icon: <ArrowDownIcon className="mr-1 h-3 w-3" />,
      label: 'Excellent Value'
    },
    good: {
      color: 'bg-green-500 text-white',
      icon: <ArrowDownIcon className="mr-1 h-3 w-3" />,
      label: 'Good Value'
    },
    fair: {
      color: 'bg-yellow-500 text-black',
      icon: <MinusIcon className="mr-1 h-3 w-3" />,
      label: 'Fair Value'
    },
    poor: {
      color: 'bg-red-500 text-white',
      icon: <ArrowUpIcon className="mr-1 h-3 w-3" />,
      label: 'Poor Value'
    }
  }[rating];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge className={`w-full justify-center ${config.color}`}>
          {config.icon}
          ${dollarPerMark.toFixed(2)}/mark
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        <p className="font-semibold">{config.label}</p>
        <p className="text-sm">Performance per dollar (single-thread)</p>
      </TooltipContent>
    </Tooltip>
  );
}
```

**Price Targets Component:**
```tsx
interface PriceTargetsProps {
  targets: PriceTarget;
}

export function PriceTargets({ targets }: PriceTargetsProps) {
  if (targets.confidence === 'insufficient') {
    return (
      <Alert variant="secondary">
        <InfoIcon className="h-4 w-4" />
        <AlertDescription>
          Insufficient data ({targets.sample_size} listings)
        </AlertDescription>
      </Alert>
    );
  }

  const confidenceColor = {
    high: 'text-green-600',
    medium: 'text-yellow-600',
    low: 'text-orange-600'
  }[targets.confidence];

  return (
    <div className="space-y-2 text-sm">
      <div className="flex items-center justify-between">
        <span className="text-muted-foreground">Target Prices</span>
        <Tooltip>
          <TooltipTrigger>
            <Badge variant="outline" className={confidenceColor}>
              {targets.confidence}
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            Based on {targets.sample_size} active listings
          </TooltipContent>
        </Tooltip>
      </div>

      <div className="space-y-1">
        <div className="flex justify-between">
          <span className="text-green-600 font-medium">Great Deal:</span>
          <span className="font-semibold">${targets.great}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-green-500 font-medium">Good Price:</span>
          <span className="font-semibold">${targets.good}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-yellow-500 font-medium">Fair Price:</span>
          <span className="font-semibold">${targets.fair}</span>
        </div>
      </div>

      {targets.updated_at && (
        <p className="text-xs text-muted-foreground">
          Updated {formatDistanceToNow(targets.updated_at)} ago
        </p>
      )}
    </div>
  );
}
```

### 9.3 Interaction Patterns

**Hover States:**
- CPU cards: Elevation increase (shadow-lg), scale(1.02)
- Table rows: Background color change (bg-muted)
- Buttons: Opacity change (opacity-90)
- Badges: Brightness increase

**Loading States:**
- Initial page load: Skeleton cards (shimmer animation)
- Filter application: Fade out/in with 200ms transition
- Modal open: Spinner in modal body during data fetch
- Table sort: Loading spinner in column header

**Error States:**
- Network error: Alert banner with retry button
- No results: Empty state illustration with suggestions
- Missing data: "N/A" or "-" placeholder with muted color
- Invalid filter: Clear indication with reset option

**Empty States:**
```tsx
{filteredCPUs.length === 0 && (
  <Card className="col-span-full">
    <CardContent className="flex flex-col items-center justify-center py-12">
      <CpuIcon className="h-16 w-16 text-muted-foreground mb-4" />
      <h3 className="text-lg font-semibold mb-2">No CPUs found</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Try adjusting your filters or search criteria
      </p>
      <Button onClick={clearFilters} variant="outline">
        Clear Filters
      </Button>
    </CardContent>
  </Card>
)}
```

### 9.4 Responsive Behavior

**Mobile (< 640px):**
- Single column grid
- Filters in bottom drawer (swipe up)
- Table becomes stacked cards
- Modal becomes full-screen
- Reduced padding/margins
- Hide non-essential columns

**Tablet (640-1023px):**
- Two column grid
- Filters in side drawer (slide in)
- Table with horizontal scroll
- Modal covers 90% viewport
- Standard padding

**Desktop (1024px+):**
- Three/four column grid
- Filters in collapsible panel
- Full data table
- Modal max-width 800px, centered
- Generous padding

**Adaptive Features:**
```tsx
// View switcher adapts to screen size
const defaultView = useMediaQuery('(min-width: 1024px)')
  ? 'master-detail'
  : 'grid';

// Filter panel position
const filterPosition = useMediaQuery('(min-width: 768px)')
  ? 'side'
  : 'drawer';

// Card content density
const cardPadding = useMediaQuery('(min-width: 640px)')
  ? 'p-6'
  : 'p-4';
```

---

## 10. Performance Metrics Calculations

### 10.1 Price Target Algorithm

**Input:** List of active listings with adjusted prices for a given CPU

**Output:** PriceTarget object with good/great/fair prices

**Algorithm:**
```python
def calculate_price_targets(listings: list[Listing]) -> PriceTarget:
    """
    Calculate price targets using statistical methods.

    Approach: Mean ± Standard Deviation
    - Good Price: Mean (average adjusted price)
    - Great Price: Mean - 1 StdDev (one standard deviation below)
    - Fair Price: Mean + 1 StdDev (one standard deviation above)

    This creates a range where:
    - ~68% of listings fall between Great and Fair
    - ~16% are cheaper than Great (best deals)
    - ~16% are more expensive than Fair (premium pricing)
    """

    # Filter valid prices
    prices = [
        l.adjusted_price_usd
        for l in listings
        if l.status == 'active'
        and l.adjusted_price_usd
        and l.adjusted_price_usd > 0
    ]

    # Check sample size
    sample_size = len(prices)
    if sample_size < 2:
        return PriceTarget(
            good=None,
            great=None,
            fair=None,
            sample_size=sample_size,
            confidence='insufficient',
            stddev=None
        )

    # Calculate statistics
    mean_price = statistics.mean(prices)
    std_dev = statistics.stdev(prices)

    # Calculate targets
    good_price = mean_price
    great_price = max(mean_price - std_dev, 0)  # Floor at 0
    fair_price = mean_price + std_dev

    # Determine confidence level
    if sample_size >= 10:
        confidence = 'high'
    elif sample_size >= 5:
        confidence = 'medium'
    else:
        confidence = 'low'

    # Check for high variance (stddev > 30% of mean)
    if std_dev > (mean_price * 0.3):
        # Consider flagging this as "wide range"
        pass

    return PriceTarget(
        good=round(good_price, 2),
        great=round(great_price, 2),
        fair=round(fair_price, 2),
        sample_size=sample_size,
        confidence=confidence,
        stddev=round(std_dev, 2)
    )
```

**Edge Cases:**
1. **Insufficient Data (< 2 listings):** Display "Insufficient data" message
2. **High Variance:** Add warning tooltip: "Wide price range - review individual listings"
3. **Outliers:** Consider using median/IQR instead of mean/stddev for robustness
4. **Inactive Listings:** Exclude from calculation to reflect current market
5. **Null Adjusted Prices:** Exclude from calculation (fallback to list price if needed)

### 10.2 Performance Value Algorithm

**Input:** CPU benchmark scores + average listing adjusted price

**Output:** PerformanceValue object with $/mark metrics and rating

**Algorithm:**
```python
def calculate_performance_value(cpu: Cpu, avg_price: float) -> PerformanceValue:
    """
    Calculate $/PassMark metrics and assign value rating.

    Lower $/mark is better (more performance per dollar).

    Rating based on percentile rank:
    - Excellent: Top 25% (lowest $/mark)
    - Good: 25-50th percentile
    - Fair: 50-75th percentile
    - Poor: Bottom 25% (highest $/mark)
    """

    # Validate inputs
    if not cpu.cpu_mark_single or not cpu.cpu_mark_multi or not avg_price:
        return PerformanceValue(
            dollar_per_mark_single=None,
            dollar_per_mark_multi=None,
            percentile=None,
            rating=None
        )

    # Calculate $/mark ratios
    dollar_per_single = avg_price / cpu.cpu_mark_single
    dollar_per_multi = avg_price / cpu.cpu_mark_multi

    # Calculate percentile rank
    # Query: How many CPUs have better (lower) $/mark?
    better_count = db.query(Cpu).filter(
        Cpu.dollar_per_mark_single < dollar_per_single,
        Cpu.dollar_per_mark_single.isnot(None)
    ).count()

    total_count = db.query(Cpu).filter(
        Cpu.dollar_per_mark_single.isnot(None)
    ).count()

    percentile = (better_count / total_count) * 100

    # Assign rating based on quartiles
    if percentile <= 25:
        rating = 'excellent'   # Top quartile
    elif percentile <= 50:
        rating = 'good'        # Second quartile
    elif percentile <= 75:
        rating = 'fair'        # Third quartile
    else:
        rating = 'poor'        # Bottom quartile

    return PerformanceValue(
        dollar_per_mark_single=round(dollar_per_single, 4),
        dollar_per_mark_multi=round(dollar_per_multi, 4),
        percentile=round(percentile, 1),
        rating=rating
    )
```

**Percentile Calculation Notes:**
- Use single-thread metric as primary (more relevant for most workloads)
- Recalculate percentiles when new CPUs added or prices updated
- Cache percentile ranks in CPU table to avoid repeated calculation
- Update nightly via background task

**Alternative Approach (Absolute Thresholds):**
```python
# Instead of percentile-based, use fixed $/mark thresholds
def get_rating_by_threshold(dollar_per_mark: float) -> str:
    if dollar_per_mark < 0.05:    # < $0.05 per mark
        return 'excellent'
    elif dollar_per_mark < 0.10:  # $0.05-0.10 per mark
        return 'good'
    elif dollar_per_mark < 0.15:  # $0.10-0.15 per mark
        return 'fair'
    else:                          # > $0.15 per mark
        return 'poor'
```

**Recommendation:** Use percentile-based approach for dynamic adaptation to market changes. Fixed thresholds become outdated as CPU prices/performance evolve.

### 10.3 Display Integration

**Listings Table Integration:**
```tsx
// Add new columns to Listings table
const listingsColumns = [
  // ... existing columns ...
  {
    accessorKey: 'cpu.performance_value.rating',
    header: 'CPU Value',
    cell: ({ row }) => (
      <PerformanceBadge
        rating={row.original.cpu?.performance_value.rating}
        dollarPerMark={row.original.cpu?.performance_value.dollar_per_mark_single}
      />
    )
  },
  {
    accessorKey: 'cpu.price_targets.good',
    header: 'CPU Target Price',
    cell: ({ row }) => {
      const target = row.original.cpu?.price_targets.good;
      const listingPrice = row.original.adjusted_price_usd;

      if (!target || !listingPrice) return '-';

      const delta = listingPrice - target;
      const deltaPercent = (delta / target) * 100;

      return (
        <div className="flex items-center gap-2">
          <span>${target}</span>
          <Badge variant={deltaPercent < 0 ? 'success' : 'warning'}>
            {deltaPercent > 0 ? '+' : ''}{deltaPercent.toFixed(1)}%
          </Badge>
        </div>
      );
    }
  }
];
```

**Listing Detail Modal Enhancement:**
```tsx
// Add CPU performance section to Listing detail modal
<Section title="CPU Performance Analysis">
  <div className="grid grid-cols-2 gap-4">
    <div>
      <h4>Performance Value</h4>
      <PerformanceBadge
        rating={listing.cpu.performance_value.rating}
        dollarPerMark={listing.cpu.performance_value.dollar_per_mark_single}
      />
      <p className="text-sm text-muted-foreground">
        Better than {(100 - listing.cpu.performance_value.percentile).toFixed(0)}% of CPUs
      </p>
    </div>

    <div>
      <h4>Target Pricing</h4>
      <PriceTargets targets={listing.cpu.price_targets} />
      {listing.adjusted_price_usd <= listing.cpu.price_targets.good && (
        <Badge variant="success">
          Below target price!
        </Badge>
      )}
    </div>
  </div>
</Section>
```

---

## 11. Out of Scope

The following features are explicitly excluded from this PRD but may be considered for future phases:

### 11.1 Excluded Features

1. **CPU Price History Tracking**
   - Time-series charts showing price trends over time
   - Historical target price ranges
   - Reason: Requires additional data collection infrastructure
   - Future Phase: Phase 2 (Analytics Enhancement)

2. **CPU Benchmark Integration**
   - Direct integration with PassMark API for automatic score updates
   - Multi-source benchmark aggregation (Geekbench, Cinebench)
   - Reason: External API dependencies and licensing
   - Future Phase: Phase 3 (External Integrations)

3. **CPU Recommendation Engine**
   - AI-powered CPU suggestions based on use case
   - "Similar CPUs" recommendations
   - Reason: Requires ML model development
   - Future Phase: Phase 4 (Intelligence Layer)

4. **Advanced Comparison Features**
   - More than 2 CPUs side-by-side
   - Benchmark score visualization charts
   - Reason: Complex UI requirements
   - Future Phase: Phase 2 (Enhanced Comparison)

5. **User-Generated Content**
   - CPU reviews and ratings
   - Community-submitted pricing data
   - Reason: Moderation and validation requirements
   - Future Phase: Phase 5 (Community Features)

6. **Export/Sharing Features**
   - Export CPU comparison to PDF
   - Share CPU detail links
   - Reason: Low priority for MVP
   - Future Phase: Phase 3

7. **Admin Features**
   - Bulk CPU import from CSV
   - CPU merge/split tools
   - Manual price target overrides
   - Reason: Admin tools in separate initiative
   - Future Phase: Admin Console Enhancement

8. **Mobile App**
   - Native iOS/Android CPU catalog apps
   - Reason: Web-first approach
   - Future Phase: Phase 6 (Mobile)

### 11.2 Technical Debt Excluded

1. **Real-time Updates**
   - WebSocket connections for live price updates
   - Reason: Adds complexity, polling sufficient for MVP

2. **Advanced Caching**
   - Redis caching layer for all queries
   - CDN for static assets
   - Reason: Premature optimization

3. **Multi-tenancy**
   - Per-user CPU catalogs
   - Private price targets
   - Reason: Single-tenant application

### 11.3 Assumptions

These items are assumed to be handled separately or are existing capabilities:

1. **Authentication/Authorization:** Admin features use existing auth system
2. **Error Tracking:** Sentry already configured
3. **Analytics:** Existing analytics track page views
4. **API Rate Limiting:** Existing rate limiting applies
5. **Database Backups:** Existing backup strategy covers new fields
6. **Monitoring:** Existing Prometheus/Grafana dashboards extended

---

## 12. Open Questions & Assumptions

### 12.1 Open Questions

**Q1: Calculation Frequency**
- How often should price targets be recalculated?
- **Options:**
  - Real-time on every listing change (high load)
  - Hourly batch process (balanced)
  - Daily batch process (stale data)
- **Recommendation:** Nightly batch + on-demand recalc when listing added/updated for that CPU

**Q2: Outlier Handling**
- Should we filter outliers from price calculations?
- **Example:** If one listing is 5x the average, should it be excluded?
- **Recommendation:** Use IQR method to detect outliers, flag but don't exclude (maintain transparency)

**Q3: Historical vs. Current Pricing**
- Should price targets consider only current listings or include sold/expired?
- **Recommendation:** Active listings only (reflects current market), add historical view in Phase 2

**Q4: PassMark Score Updates**
- How do we handle PassMark score changes over time?
- **Recommendation:** Manual updates via admin tool, consider API integration in Phase 3

**Q5: Multi-Metric Performance Value**
- Should rating consider both single-thread and multi-thread, or just one?
- **Recommendation:** Primary rating from single-thread, display both metrics

**Q6: CPU Comparison Limits**
- How many CPUs can be compared simultaneously?
- **Recommendation:** Max 4 CPUs (UI constraint), show warning if more selected

**Q7: Mobile Master-Detail View**
- Is master-detail feasible on mobile?
- **Recommendation:** Auto-switch to grid view on mobile (< 768px)

**Q8: Filter Persistence**
- Should filters persist across sessions?
- **Recommendation:** Yes, store in Zustand persist middleware

### 12.2 Assumptions

**Technical Assumptions:**
1. PostgreSQL database can handle additional indexes without performance degradation
2. React Query caching sufficient for performance needs (no Redis required for MVP)
3. Existing API infrastructure supports new endpoints without architecture changes
4. Celery worker can handle nightly recalculation task (< 5 min for 500 CPUs)
5. Current PassMark data in database is accurate and complete

**Business Assumptions:**
1. Users understand statistical concepts (mean, standard deviation, percentile)
2. Adjusted prices are more relevant than list prices for valuation
3. Single-thread performance is primary metric for most users
4. Confidence levels (high/medium/low) are sufficient granularity
5. Target prices should be based on adjusted (not list) prices

**Data Assumptions:**
1. Sufficient listings exist for most CPUs (average 5+ per CPU)
2. Adjusted prices are calculated consistently across all listings
3. CPU benchmark scores are from PassMark and comparable
4. Listing status accurately reflects availability
5. Price dates are recent enough for current market analysis

**User Assumptions:**
1. Users want to compare CPUs before selecting for a listing
2. Performance-per-dollar is a primary decision factor
3. Users trust statistical price targets over gut feel
4. Grid/list/master-detail views cover all use cases
5. CPU catalog is secondary to Listings page (lower traffic)

### 12.3 Risk Mitigation

**Risk:** Insufficient data for many CPUs leads to "No data" messages
- **Mitigation:** Add alternative messaging: "View similar CPUs" or "Based on X similar models"
- **Fallback:** Show absolute price ranges from all listings if CPU-specific data insufficient

**Risk:** Performance metrics calculations too slow on nightly batch
- **Mitigation:** Optimize queries, add database indexes, parallelize calculations
- **Monitoring:** Track batch job duration, alert if > 10 minutes

**Risk:** Users confused by percentile-based ratings
- **Mitigation:** Add tooltip explanations, "Learn More" links, example comparisons
- **Alternative:** Provide toggle between percentile and absolute threshold ratings

**Risk:** Mobile UX degraded due to complex data visualization
- **Mitigation:** Simplify mobile cards, hide secondary metrics, test on real devices
- **Monitoring:** Track mobile bounce rates, heatmaps for interaction patterns

---

## 13. Dependencies & Risks

### 13.1 Technical Dependencies

**Internal Dependencies:**
1. **Listings Data Quality**
   - Dependency: Accurate adjusted_price_usd calculations
   - Impact: Critical (price targets invalid if adjusted prices wrong)
   - Mitigation: Validate valuation engine before this feature

2. **PassMark Benchmark Data**
   - Dependency: Complete and up-to-date CPU benchmark scores
   - Impact: High (performance metrics require valid benchmarks)
   - Mitigation: Audit CPU table, import missing scores

3. **Database Performance**
   - Dependency: Query optimization for analytics calculations
   - Impact: Medium (slow queries degrade UX)
   - Mitigation: Add indexes, load test with production data

4. **React Query Infrastructure**
   - Dependency: Existing React Query setup in web app
   - Impact: Low (already in use for Listings page)
   - Mitigation: None needed

**External Dependencies:**
1. **shadcn/ui Component Library**
   - Dependency: UI components for modals, tables, badges
   - Impact: Low (stable library, widely used)
   - Mitigation: None needed

2. **Next.js App Router**
   - Dependency: Routing and SSR capabilities
   - Impact: Low (core framework)
   - Mitigation: None needed

### 13.2 Project Dependencies

**Prerequisite Work:**
1. **Database Migration**
   - Must complete before any feature work
   - Timeline: 1 day
   - Owner: Backend team

2. **Schema Updates**
   - Pydantic schemas for new analytics types
   - Timeline: 1 day
   - Owner: Backend team

3. **Service Layer Implementation**
   - CPUAnalyticsService with calculation logic
   - Timeline: 3 days
   - Owner: Backend team

**Parallel Work:**
- Frontend components can be built with mock data
- Design system extensions (badges, color palette)
- Documentation updates

### 13.3 Risks & Mitigation Strategies

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Insufficient listing data for price targets | High | High | Add fallback messaging, aggregate similar CPUs, show "Coming soon" |
| Performance issues with nightly batch | Medium | Medium | Optimize queries, add indexes, parallelize, monitor duration |
| User confusion about metrics | Medium | High | Add comprehensive tooltips, help docs, onboarding tour |
| Mobile UX complexity | Medium | Medium | Simplify mobile views, hide secondary data, extensive testing |
| API response time degradation | Low | High | Cache analytics data, add Redis layer, optimize joins |
| Inaccurate price targets (outliers) | Medium | Medium | Implement outlier detection, show sample size, confidence levels |
| PassMark score staleness | Low | Medium | Add "Last updated" timestamps, manual refresh tool |
| Browser compatibility issues | Low | Low | Polyfills, graceful degradation, cross-browser testing |
| Accessibility violations | Medium | High | Audit with axe/WAVE, keyboard testing, screen reader testing |
| Database migration failures | Low | Critical | Test migration on staging, backup production, rollback plan |

**Critical Path Risks:**

**Risk: Database migration breaks existing Listings functionality**
- Impact: Critical (entire app down)
- Probability: Low
- Mitigation:
  - Thorough testing on staging with production data snapshot
  - Rollback script prepared before deployment
  - Deploy during low-traffic window
  - Monitor error rates post-deployment

**Risk: Performance degradation on CPU list endpoint**
- Impact: High (slow page loads)
- Probability: Medium
- Mitigation:
  - Load testing with 500+ CPUs
  - Database query explain analyze
  - Add appropriate indexes
  - Implement response caching (5 min TTL)
  - Monitor P95/P99 latency

**Risk: Insufficient listing data for most CPUs**
- Impact: High (feature doesn't provide value)
- Probability: Medium
- Mitigation:
  - Pre-launch audit: count listings per CPU
  - Identify CPUs with < 2 listings
  - Add "Similar CPUs" aggregation feature
  - Show "Listing needed" call-to-action
  - Phase rollout: start with well-populated CPUs

### 13.4 Launch Readiness Criteria

**Must Have (Blockers):**
- [ ] Database migration successful on staging
- [ ] All API endpoints return < 1s (P95)
- [ ] Zero critical accessibility violations
- [ ] Mobile responsive design verified on real devices
- [ ] Price target calculations validated with sample data
- [ ] Performance metrics match manual calculations
- [ ] Error handling covers all edge cases
- [ ] Admin can trigger manual metric recalculation

**Should Have (Launch with caveats):**
- [ ] 70% of CPUs have sufficient data (5+ listings)
- [ ] Comprehensive tooltips and help text
- [ ] Filter persistence working
- [ ] Master-detail view fully functional
- [ ] Export to CSV working

**Nice to Have (Post-launch):**
- [ ] CPU comparison modal
- [ ] Price history charts
- [ ] Advanced filtering (boolean logic)
- [ ] Saved filter presets

### 13.5 Rollout Strategy

**Phase 1: Internal Beta (Week 1)**
- Deploy to staging environment
- Internal team testing
- Fix critical bugs
- Validate data accuracy

**Phase 2: Limited Rollout (Week 2)**
- Deploy to production with feature flag
- Enable for 10% of users
- Monitor error rates, performance metrics
- Gather user feedback

**Phase 3: Full Rollout (Week 3)**
- Increase to 50% of users
- Address feedback, fix bugs
- Final QA pass

**Phase 4: General Availability (Week 4)**
- Enable for 100% of users
- Announcement to user base
- Documentation published
- Support team trained

**Rollback Plan:**
- Feature flag allows instant disable
- Database migration reversible (downgrade script)
- Previous CPU page remains available at /cpus/legacy

---

## 14. Success Criteria

### 14.1 Acceptance Criteria

**Feature Complete Checklist:**
- [ ] CPU catalog page accessible at /cpus route
- [ ] Dual-tab interface (Catalog + Data) functional
- [ ] All three view modes (Grid, List, Master-Detail) implemented
- [ ] CPU detail modal displays all specifications
- [ ] Price target calculation working for CPUs with 2+ listings
- [ ] Performance value metrics calculated and displayed
- [ ] Filters working: search, manufacturer, socket, core count, TDP
- [ ] Sorting working on all data table columns
- [ ] Mobile responsive design verified (320px+)
- [ ] Keyboard navigation works throughout
- [ ] Screen reader announcements correct
- [ ] Color contrast ratios meet WCAG AA
- [ ] API endpoints return < 500ms (P95)
- [ ] Nightly batch recalculation completes successfully
- [ ] Error states handled gracefully
- [ ] Loading states provide feedback

### 14.2 Launch Metrics

**Week 1 Post-Launch:**
- Page views: 200+ unique views
- Avg time on page: > 2 minutes
- Detail modal opens: 50+ interactions
- Filter usage: 30+ filter applications
- Error rate: < 1% of requests
- API P95 latency: < 800ms

**Month 1 Post-Launch:**
- Page views: 1000+ unique views
- CPU catalog drives 20% increase in Listing detail views
- 90% of CPUs have sufficient data (5+ listings)
- User satisfaction: 4+ stars (if feedback collected)

### 14.3 Quality Gates

**Performance:**
- Lighthouse score: > 90 (Performance, Accessibility, Best Practices)
- First Contentful Paint: < 1.2s
- Time to Interactive: < 2.5s
- Total Blocking Time: < 300ms

**Accessibility:**
- axe DevTools: 0 critical violations
- WAVE: 0 errors
- Keyboard navigation: 100% coverage
- Screen reader: All content announced correctly

**Code Quality:**
- TypeScript strict mode: 0 errors
- ESLint: 0 errors, 0 warnings
- Test coverage: > 80% for new code
- No console errors in production build

---

## Appendix A: Mockups & Wireframes

*(Note: Detailed mockups would be included in actual PRD. For this document, text descriptions provided.)*

**CPU Grid View:**
```
┌─────────────────────────────────────────────────────────────┐
│ CPUs                                              [Add CPU]  │
│ Browse CPU catalog in your preferred view                   │
├─────────────────────────────────────────────────────────────┤
│ [Catalog] [Data]                                            │
├─────────────────────────────────────────────────────────────┤
│ [Search CPUs...]  [Manufacturer▾] [Socket▾]  [Grid List MD]│
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│ │Intel    │ │AMD      │ │Intel    │ │AMD      │           │
│ │Core i7  │ │Ryzen 9  │ │Core i5  │ │Ryzen 7  │           │
│ │13700K   │ │7950X    │ │13600K   │ │7800X3D  │           │
│ │         │ │         │ │         │ │         │           │
│ │16C/24T  │ │16C/32T  │ │14C/20T  │ │8C/16T   │           │
│ │125W     │ │170W     │ │125W     │ │120W     │           │
│ │         │ │         │ │         │ │         │           │
│ │[======] │ │[=======]│ │[=====]  │ │[======] │           │
│ │Single   │ │Single   │ │Single   │ │Single   │           │
│ │[=======]│ │[========│ │[======] │ │[=======]│           │
│ │Multi    │ │Multi    │ │Multi    │ │Multi    │           │
│ │         │ │         │ │         │ │         │           │
│ │[Excelle-│ │[Good▼]  │ │[Good▼]  │ │[Excelle-│           │
│ │nt Value]│ │$0.08/mk │ │$0.09/mk │ │nt Value]│           │
│ │$0.06/mk │ │         │ │         │ │$0.05/mk │           │
│ │         │ │         │ │         │ │         │           │
│ │Great:   │ │Great:   │ │Great:   │ │Great:   │           │
│ │$320     │ │$490     │ │$250     │ │$360     │           │
│ │Good:    │ │Good:    │ │Good:    │ │Good:    │           │
│ │$350     │ │$530     │ │$280     │ │$390     │           │
│ │Fair:    │ │Fair:    │ │Fair:    │ │Fair:    │           │
│ │$380     │ │$570     │ │$310     │ │$420     │           │
│ │         │ │         │ │         │ │         │           │
│ │[Details]│ │[Details]│ │[Details]│ │[Details]│           │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```

**CPU Detail Modal:**
```
┌───────────────────────────────────────────────────────┐
│ Intel Core i7-13700K                            [X]   │
├───────────────────────────────────────────────────────┤
│                                                       │
│ Performance Overview                                  │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Single-Thread: 4,231  [=========         ] 85%  │ │
│ │ Multi-Thread:  41,678 [============      ] 83%  │ │
│ │ iGPU Mark:     4,523  [=======           ] 60%  │ │
│ └─────────────────────────────────────────────────┘ │
│                                                       │
│ Performance Value                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ [Excellent Value] $0.0623/mark                  │ │
│ │ Better than 78% of CPUs                         │ │
│ │ Top quartile for performance per dollar         │ │
│ └─────────────────────────────────────────────────┘ │
│                                                       │
│ Specifications                                        │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Cores/Threads: 16 / 24                          │ │
│ │ Socket:        LGA1700                          │ │
│ │ TDP:           125W                             │ │
│ │ Release Year:  2022                             │ │
│ │ iGPU:          Intel UHD Graphics 770           │ │
│ └─────────────────────────────────────────────────┘ │
│                                                       │
│ Target Pricing                [High Confidence ✓]    │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Great Deal:  $320 (One std dev below avg)       │ │
│ │ Good Price:  $350 (Average of 12 listings)      │ │
│ │ Fair Price:  $380 (One std dev above avg)       │ │
│ │                                                  │ │
│ │ Based on 12 active listings                     │ │
│ │ Updated 2 hours ago                             │ │
│ └─────────────────────────────────────────────────┘ │
│                                                       │
│ Market Data                                           │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Active Listings: 12                             │ │
│ │ Price Range:     $310 - $420                    │ │
│ │ [View All Listings →]                           │ │
│ └─────────────────────────────────────────────────┘ │
│                                                       │
├───────────────────────────────────────────────────────┤
│                        [Edit CPU] [Close]             │
└───────────────────────────────────────────────────────┘
```

---

## Appendix B: API Response Examples

**GET /v1/cpus Response:**
```json
[
  {
    "id": 1,
    "name": "Intel Core i7-13700K",
    "manufacturer": "Intel",
    "socket": "LGA1700",
    "cores": 16,
    "threads": 24,
    "tdp_w": 125,
    "igpu_model": "Intel UHD Graphics 770",
    "cpu_mark_multi": 41678,
    "cpu_mark_single": 4231,
    "igpu_mark": 4523,
    "release_year": 2022,
    "price_targets": {
      "good": 350.00,
      "great": 320.00,
      "fair": 380.00,
      "sample_size": 12,
      "confidence": "high",
      "stddev": 30.00,
      "updated_at": "2025-10-15T14:30:00Z"
    },
    "performance_value": {
      "dollar_per_mark_single": 0.0623,
      "dollar_per_mark_multi": 0.0084,
      "percentile": 22.5,
      "rating": "excellent",
      "updated_at": "2025-10-15T14:30:00Z"
    },
    "listings_count": 12
  }
]
```

**GET /v1/cpus/{id}/analytics Response:**
```json
{
  "cpu_id": 1,
  "price_targets": {
    "good": 350.00,
    "great": 320.00,
    "fair": 380.00,
    "sample_size": 12,
    "confidence": "high",
    "stddev": 30.00,
    "updated_at": "2025-10-15T14:30:00Z"
  },
  "performance_value": {
    "dollar_per_mark_single": 0.0623,
    "dollar_per_mark_multi": 0.0084,
    "percentile": 22.5,
    "rating": "excellent",
    "updated_at": "2025-10-15T14:30:00Z"
  },
  "market_data": {
    "price_distribution": [310, 325, 340, 345, 350, 355, 360, 365, 375, 380, 395, 420],
    "listings_total": 12,
    "price_min": 310,
    "price_max": 420,
    "price_median": 357.5
  },
  "associated_listings": [
    {
      "id": 101,
      "title": "Dell OptiPlex 7090 - i7-13700K, 32GB RAM",
      "adjusted_price_usd": 320.00,
      "status": "active"
    }
  ]
}
```

---

## Document Control

**Version History:**
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-15 | Claude (Documentation Agent) | Initial PRD draft |

**Approvals:**
- [ ] Product Owner
- [ ] Engineering Lead
- [ ] UX/Design Lead
- [ ] QA Lead

**Next Steps:**
1. Review PRD with stakeholders
2. Create implementation plan
3. Break down into user stories
4. Estimate effort and timeline
5. Prioritize in backlog

---

**End of Document**
