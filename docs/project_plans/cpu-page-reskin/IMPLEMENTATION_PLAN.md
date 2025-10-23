# CPU Catalog Page Reskin - Implementation Plan

**Version:** 1.0
**Date:** 2025-10-15
**Status:** Ready for Sprint Planning
**Project:** Deal Brain CPU Catalog Enhancement

---

## 1. Overview

### 1.1 Project Scope Summary

Transform the current basic CPU table into a comprehensive, interactive catalog experience mirroring the Listings page architecture. The enhancement introduces:

- **Dual-tab interface** (Catalog + Data views)
- **Performance-based pricing metrics** ($/PassMark calculations with visual indicators)
- **Statistical target pricing** from actual listing data
- **Multiple view modes** (Grid, List, Master-Detail)
- **Interactive CPU detail modal** with comprehensive analytics
- **Enhanced filtering and sorting** capabilities

### 1.2 Timeline Estimate

**Total Duration:** 3-4 weeks (3 sprints)

| Phase | Duration | Sprint |
|-------|----------|--------|
| Phase 1: Backend Foundation | 1 week | Sprint 1 |
| Phase 2: Frontend Core | 1 week | Sprint 2 |
| Phase 3: Performance Metrics & Analytics | 1 week | Sprint 2-3 |
| Phase 4: Polish, Testing & Documentation | 3-5 days | Sprint 3 |

**Key Milestones:**
- Week 1 End: Database migrated, API endpoints functional, analytics service operational
- Week 2 End: All view modes implemented, basic CPU catalog functional
- Week 3 End: Performance metrics integrated, full feature complete, QA passed

### 1.3 Team Roles and Responsibilities

| Role | Responsibilities | Estimated Effort |
|------|------------------|------------------|
| **Backend Developer** | Database migrations, service layer, API endpoints, analytics calculations | 60 hours |
| **Frontend Developer** | React components, state management, UI implementation, React Query integration | 70 hours |
| **Full-Stack Developer** | Integration work, end-to-end feature coordination, performance optimization | 40 hours |
| **QA Engineer** | Test planning, manual testing, accessibility audit, performance validation | 20 hours |
| **Tech Writer** | API documentation, user guide updates, inline help text | 10 hours |

**Total Estimated Effort:** 200 hours (5 weeks @ 40 hours/week)

---

## 2. Development Phases

### Phase 1: Backend Foundation (Week 1)

**Objectives:**
- Extend database schema with analytics fields
- Implement CPU analytics service layer
- Create API endpoints for CPU data with analytics
- Set up nightly recalculation task

**Deliverables:**
- Migration scripts executed successfully
- `CPUAnalyticsService` with calculation methods
- API endpoints returning analytics data
- Celery task for nightly metric refresh

**Time Estimate:** 5 days (40 hours)

**Dependencies:**
- None (foundational work)

**Success Criteria:**
- [ ] Migration runs without errors on staging
- [ ] `/v1/cpus` endpoint returns CPUs with price targets and performance values
- [ ] Analytics calculations match manual verification
- [ ] Nightly task completes in < 5 minutes for 500 CPUs
- [ ] All endpoints meet < 500ms P95 latency requirement

---

### Phase 2: Frontend Core (Week 2)

**Objectives:**
- Create CPU catalog page structure with dual tabs
- Implement all three view modes (Grid, List, Master-Detail)
- Build CPU catalog store with Zustand
- Implement client-side filtering and URL synchronization

**Deliverables:**
- `/cpus` page with tab switching
- Grid, List, and Master-Detail view components
- `cpu-catalog-store.ts` for state management
- Filter components adapted from Listings page

**Time Estimate:** 5 days (40 hours)

**Dependencies:**
- Phase 1 API endpoints must be functional

**Success Criteria:**
- [ ] All three view modes render correctly
- [ ] Tab switching works smoothly
- [ ] Filters apply client-side without lag
- [ ] URL parameters sync with store state
- [ ] View preferences persist across sessions
- [ ] Mobile responsive (tested on 320px-1920px viewports)

---

### Phase 3: Performance Metrics & Analytics (Week 2-3)

**Objectives:**
- Integrate performance value badges and price target displays
- Implement CPU detail modal with comprehensive analytics
- Add performance metrics to Listings page/table
- Build interactive charts and visualizations

**Deliverables:**
- `PerformanceBadge` component with color-coded ratings
- `PriceTargets` component showing Great/Good/Fair prices
- `CPUDetailModal` with all sections
- Updated Listings table with CPU performance columns

**Time Estimate:** 5 days (40 hours)

**Dependencies:**
- Phase 1 analytics data must be available
- Phase 2 page structure must be complete

**Success Criteria:**
- [ ] Performance badges display correct ratings
- [ ] Price targets show confidence levels accurately
- [ ] Detail modal loads in < 300ms
- [ ] All tooltips provide helpful context
- [ ] Charts render without performance issues
- [ ] Listings integration doesn't break existing functionality

---

### Phase 4: Polish, Testing & Documentation (Week 3)

**Objectives:**
- Comprehensive accessibility audit and fixes
- Performance optimization (memoization, caching, indexes)
- Cross-browser testing and bug fixes
- User documentation and API docs

**Deliverables:**
- Zero critical accessibility violations
- All performance benchmarks met
- Comprehensive test coverage (unit, integration, E2E)
- Updated user guide and API documentation

**Time Estimate:** 3-5 days (25-40 hours)

**Dependencies:**
- Phases 1-3 complete

**Success Criteria:**
- [ ] WCAG AA compliance verified (axe, WAVE)
- [ ] Lighthouse scores > 90 (Performance, Accessibility, Best Practices)
- [ ] All critical and high-priority bugs resolved
- [ ] Test coverage > 80% for new code
- [ ] Documentation published and reviewed

---

## 3. Detailed Task Breakdown

### 3.1 Database & Migrations

#### DB-001: Create Database Migration Script (P0)
**Description:** Generate Alembic migration to add analytics fields to CPU table

**Estimated Effort:** 4 hours

**Dependencies:** None

**Acceptance Criteria:**
- Migration script adds all 10 new columns (price targets, performance metrics)
- All indexes created (manufacturer, socket, cores, price targets, performance value)
- Upgrade and downgrade functions both work correctly
- Migration tested on staging with production data snapshot

**Implementation Notes:**
```python
# Migration: apps/api/alembic/versions/xxx_add_cpu_analytics_fields.py

def upgrade():
    # Price target fields
    op.add_column('cpu', sa.Column('price_target_good', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('price_target_great', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('price_target_fair', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('price_target_sample_size', sa.Integer, server_default='0'))
    op.add_column('cpu', sa.Column('price_target_confidence', sa.String(16), nullable=True))
    op.add_column('cpu', sa.Column('price_target_stddev', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('price_target_updated_at', sa.DateTime, nullable=True))

    # Performance value fields
    op.add_column('cpu', sa.Column('dollar_per_mark_single', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('dollar_per_mark_multi', sa.Numeric(10,2), nullable=True))
    op.add_column('cpu', sa.Column('performance_value_percentile', sa.Numeric(5,2), nullable=True))
    op.add_column('cpu', sa.Column('performance_value_rating', sa.String(16), nullable=True))
    op.add_column('cpu', sa.Column('performance_metrics_updated_at', sa.DateTime, nullable=True))

    # Indexes for query performance
    op.create_index('idx_cpu_price_targets', 'cpu',
                    ['price_target_good', 'price_target_confidence'])
    op.create_index('idx_cpu_performance_value', 'cpu',
                    ['dollar_per_mark_single', 'dollar_per_mark_multi'])
    op.create_index('idx_cpu_manufacturer', 'cpu', ['manufacturer'])
    op.create_index('idx_cpu_socket', 'cpu', ['socket'])
    op.create_index('idx_cpu_cores', 'cpu', ['cores'])
```

---

#### DB-002: Update CPU SQLAlchemy Model (P0)
**Description:** Add new fields and properties to CPU model class

**Estimated Effort:** 2 hours

**Dependencies:** DB-001

**Acceptance Criteria:**
- All 12 new fields added with correct types
- Properties `has_sufficient_pricing_data` and `price_targets_fresh` implemented
- Model validates correctly with existing data
- Relationships to Listing maintained

**File:** `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`

**Implementation Notes:**
```python
class Cpu(Base, TimestampMixin):
    # ... existing fields ...

    # Price Target Fields
    price_target_good: Mapped[float | None]
    price_target_great: Mapped[float | None]
    price_target_fair: Mapped[float | None]
    price_target_sample_size: Mapped[int] = mapped_column(default=0)
    price_target_confidence: Mapped[str | None] = mapped_column(String(16))
    price_target_stddev: Mapped[float | None]
    price_target_updated_at: Mapped[datetime | None]

    # Performance Value Fields
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

---

### 3.2 Backend API Development

#### BE-001: Create Pydantic Schemas for CPU Analytics (P0)
**Description:** Define request/response schemas for CPU analytics data

**Estimated Effort:** 3 hours

**Dependencies:** DB-002

**Acceptance Criteria:**
- `PriceTarget`, `PerformanceValue`, `CPUAnalytics` schemas defined
- `CPUWithAnalytics`, `CPUDetail`, `CPUStatistics` schemas created
- All schemas validate correctly with test data
- Schema documentation includes field descriptions

**File:** `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/cpu.py`

**Implementation Notes:**
```python
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class PriceTarget(BaseModel):
    """CPU price target ranges from listing data"""
    good: float | None = Field(description="Average adjusted price")
    great: float | None = Field(description="One std dev below average")
    fair: float | None = Field(description="One std dev above average")
    sample_size: int = Field(description="Number of listings used")
    confidence: Literal['high', 'medium', 'low', 'insufficient']
    stddev: float | None = Field(description="Standard deviation of prices")
    updated_at: datetime | None

class PerformanceValue(BaseModel):
    """CPU performance value metrics"""
    dollar_per_mark_single: float | None
    dollar_per_mark_multi: float | None
    percentile: float | None = Field(ge=0, le=100)
    rating: Literal['excellent', 'good', 'fair', 'poor'] | None
    updated_at: datetime | None

class CPUWithAnalytics(CpuRead):
    """CPU with embedded analytics"""
    price_targets: PriceTarget
    performance_value: PerformanceValue
    listings_count: int

class CPUStatistics(BaseModel):
    """Global CPU statistics for filters"""
    manufacturers: list[str]
    sockets: list[str]
    core_range: tuple[int, int]
    tdp_range: tuple[int, int]
    year_range: tuple[int, int]
    total_count: int
```

---

#### BE-002: Implement CPU Analytics Service (P0)
**Description:** Create service layer with price target and performance value calculation methods

**Estimated Effort:** 12 hours

**Dependencies:** BE-001

**Acceptance Criteria:**
- `calculate_price_targets()` correctly computes mean ± std dev
- `calculate_performance_value()` calculates $/mark and percentile rank
- `update_cpu_analytics()` persists all fields to database
- `recalculate_all_cpu_metrics()` processes all CPUs efficiently
- Edge cases handled (insufficient data, missing benchmarks, outliers)
- Calculations verified manually with sample data

**File:** `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/cpu_analytics.py`

**Implementation Notes:**
- Use Python `statistics` module for mean/stdev calculations
- Query only active listings for current market data
- Implement percentile calculation using database query for efficiency
- Add comprehensive logging for debugging
- Handle division by zero gracefully
- Refer to PRD Section 8.3 for detailed algorithm pseudocode

---

#### BE-003: Create GET /v1/cpus Endpoint (P0)
**Description:** List all CPUs with optional analytics data

**Estimated Effort:** 4 hours

**Dependencies:** BE-002

**Acceptance Criteria:**
- Endpoint returns `List[CPUWithAnalytics]` format
- Analytics fields populated from pre-computed CPU table columns
- Response includes listings count for each CPU
- Query optimized (single DB query with joins)
- Response time < 500ms P95 with 100+ CPUs
- Supports `include_analytics` query parameter

**File:** `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`

**Implementation Notes:**
```python
@router.get("/cpus", response_model=list[CPUWithAnalytics])
async def list_cpus(
    session: AsyncSession = Depends(session_dependency),
    include_analytics: bool = Query(default=True)
) -> Sequence[CPUWithAnalytics]:
    """List all CPUs with optional analytics data"""

    stmt = select(Cpu).order_by(Cpu.name)
    result = await session.execute(stmt)
    cpus = result.scalars().all()

    response = []
    for cpu in cpus:
        cpu_dict = CpuRead.model_validate(cpu).model_dump()

        if include_analytics:
            # Build analytics from stored fields
            cpu_dict['price_targets'] = PriceTarget(...)
            cpu_dict['performance_value'] = PerformanceValue(...)

            # Count listings
            stmt = select(func.count(Listing.id)).where(
                Listing.cpu_id == cpu.id,
                Listing.status == ListingStatus.ACTIVE
            )
            cpu_dict['listings_count'] = await session.scalar(stmt) or 0

        response.append(CPUWithAnalytics(**cpu_dict))

    return response
```

---

#### BE-004: Create GET /v1/cpus/{id} Endpoint (P1)
**Description:** Get detailed CPU information with analytics and market data

**Estimated Effort:** 3 hours

**Dependencies:** BE-002

**Acceptance Criteria:**
- Returns `CPUDetail` schema with full specifications
- Includes top 10 associated listings by adjusted price
- Includes price distribution for histogram
- 404 error for non-existent CPU ID
- Response time < 300ms P95

**File:** `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`

---

#### BE-005: Create GET /v1/cpus/statistics Endpoint (P1)
**Description:** Global CPU statistics for filter dropdown options

**Estimated Effort:** 2 hours

**Dependencies:** None

**Acceptance Criteria:**
- Returns unique manufacturers, sockets lists
- Returns min/max ranges for cores, TDP, years
- Returns total CPU count
- Results cached (5 min TTL)
- Response time < 200ms

**File:** `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`

---

#### BE-006: Create POST /v1/cpus/recalculate-metrics Endpoint (P2)
**Description:** Admin endpoint to trigger metric recalculation background task

**Estimated Effort:** 2 hours

**Dependencies:** BE-002

**Acceptance Criteria:**
- Returns 202 Accepted immediately
- Triggers background task via Celery or BackgroundTasks
- Admin-only access (authentication check)
- Returns task ID for status tracking

**File:** `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`

---

#### BE-007: Implement Nightly Recalculation Task (P1)
**Description:** Celery task to refresh all CPU analytics nightly

**Estimated Effort:** 4 hours

**Dependencies:** BE-002

**Acceptance Criteria:**
- Task scheduled for 2:00 AM UTC (cron expression)
- Processes all CPUs in batches (50 at a time)
- Logs summary (total processed, success count, error count)
- Completes in < 10 minutes for 500 CPUs
- Handles failures gracefully (continue processing remaining CPUs)
- Sends alert if > 10% of CPUs fail

**File:** `/mnt/containers/deal-brain/apps/api/dealbrain_api/tasks/cpu_metrics.py`

**Implementation Notes:**
```python
from celery import shared_task
from celery.schedules import crontab

@shared_task
def recalculate_all_cpu_metrics():
    """Nightly task to refresh CPU analytics"""
    async with session_scope() as session:
        result = await CPUAnalyticsService.recalculate_all_cpu_metrics(session)

        logger.info(
            "CPU metrics recalculation complete",
            extra={
                "total": result['total'],
                "success": result['success'],
                "errors": result['errors']
            }
        )

        if result['errors'] > result['total'] * 0.1:
            # Alert if >10% failed
            send_alert("CPU metrics recalculation had high error rate")

        return result

# Celery beat schedule
app.conf.beat_schedule = {
    'recalculate-cpu-metrics': {
        'task': 'recalculate_all_cpu_metrics',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM UTC
    }
}
```

---

### 3.3 Frontend Components

#### FE-001: Create CPU Catalog Store (P0)
**Description:** Zustand store for CPU catalog state management

**Estimated Effort:** 3 hours

**Dependencies:** None

**Acceptance Criteria:**
- Store includes activeTab, activeView, filters, selectedCPUId states
- Actions for setActiveTab, setActiveView, setFilters, clearFilters
- Dialog states for CPU detail modal and compare modal
- Persistence configured for view preferences only
- URL sync hooks available

**File:** `/mnt/containers/deal-brain/apps/web/stores/cpu-catalog-store.ts`

**Implementation Notes:**
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type CPUViewMode = 'grid' | 'list' | 'master-detail';
export type CPUTabMode = 'catalog' | 'data';

export interface CPUFilterState {
  searchQuery: string;
  manufacturer: string[];
  socket: string[];
  coreRange: [number, number];
  tdpRange: [number, number];
  hasIGPU: boolean | null;
  minPassMark: number | null;
}

export interface CPUCatalogState {
  activeView: CPUViewMode;
  setActiveView: (view: CPUViewMode) => void;

  activeTab: CPUTabMode;
  setActiveTab: (tab: CPUTabMode) => void;

  filters: CPUFilterState;
  setFilters: (filters: Partial<CPUFilterState>) => void;
  clearFilters: () => void;

  selectedCPUId: number | null;
  setSelectedCPU: (id: number | null) => void;

  detailModalOpen: boolean;
  detailModalCPUId: number | null;
  openDetailModal: (id: number) => void;
  closeDetailModal: () => void;

  compareCPUs: number[];
  toggleCompare: (cpuId: number) => void;
  clearCompare: () => void;
}

const DEFAULT_FILTERS: CPUFilterState = {
  searchQuery: '',
  manufacturer: [],
  socket: [],
  coreRange: [2, 64],
  tdpRange: [15, 280],
  hasIGPU: null,
  minPassMark: null,
};

export const useCPUCatalogStore = create<CPUCatalogState>()(
  persist(
    (set) => ({
      activeView: 'grid',
      setActiveView: (view) => set({ activeView: view }),

      activeTab: 'catalog',
      setActiveTab: (tab) => set({ activeTab: tab }),

      filters: DEFAULT_FILTERS,
      setFilters: (partialFilters) =>
        set((state) => ({
          filters: { ...state.filters, ...partialFilters },
        })),
      clearFilters: () => set({ filters: DEFAULT_FILTERS }),

      selectedCPUId: null,
      setSelectedCPU: (id) => set({ selectedCPUId: id }),

      detailModalOpen: false,
      detailModalCPUId: null,
      openDetailModal: (id) =>
        set({ detailModalOpen: true, detailModalCPUId: id }),
      closeDetailModal: () =>
        set({ detailModalOpen: false, detailModalCPUId: null }),

      compareCPUs: [],
      toggleCompare: (cpuId) =>
        set((state) => ({
          compareCPUs: state.compareCPUs.includes(cpuId)
            ? state.compareCPUs.filter((id) => id !== cpuId)
            : [...state.compareCPUs, cpuId],
        })),
      clearCompare: () => set({ compareCPUs: [] }),
    }),
    {
      name: 'cpu-catalog-store',
      partialize: (state) => ({
        activeView: state.activeView,
        activeTab: state.activeTab,
        filters: state.filters,
      }),
    }
  )
);
```

---

#### FE-002: Create CPU Catalog Main Page (P0)
**Description:** Main page component with tab structure

**Estimated Effort:** 4 hours

**Dependencies:** FE-001

**Acceptance Criteria:**
- Page renders at `/cpus` route
- Dual tabs (Catalog, Data) with smooth switching
- Header with title, description, "Add CPU" button (admin only)
- URL synchronization working
- Loading states handled
- Error boundaries in place

**File:** `/mnt/containers/deal-brain/apps/web/app/cpus/page.tsx`

**Implementation Notes:**
```typescript
"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { useCPUCatalogStore } from "@/stores/cpu-catalog-store";
import { useUrlSync } from "@/hooks/use-url-sync-cpu";
import { CatalogTab } from "./_components/catalog-tab";
import { DataTab } from "./_components/data-tab";
import { CPUDetailModal } from "./_components/cpu-detail-modal";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/utils";
import { CPUWithAnalytics } from "@/types/cpu";

export default function CPUsPage() {
  const [addModalOpen, setAddModalOpen] = useState(false);

  // Fetch CPUs with analytics
  const { data: cpus, isLoading } = useQuery({
    queryKey: ["cpus", "analytics"],
    queryFn: () => apiFetch<CPUWithAnalytics[]>("/v1/cpus"),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Sync URL with store
  useUrlSync();

  // Get tab state from store
  const activeTab = useCPUCatalogStore((state) => state.activeTab);
  const setActiveTab = useCPUCatalogStore((state) => state.setActiveTab);

  return (
    <div className="w-full space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">CPUs</h1>
          <p className="text-sm text-muted-foreground">
            Browse CPU catalog with performance metrics and pricing analytics.
          </p>
        </div>
        <Button onClick={() => setAddModalOpen(true)}>
          Add CPU
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as CPUTabMode)}>
        <TabsList>
          <TabsTrigger value="catalog">Catalog</TabsTrigger>
          <TabsTrigger value="data">Data</TabsTrigger>
        </TabsList>

        <TabsContent value="catalog" className="space-y-4">
          <CatalogTab cpus={cpus || []} isLoading={isLoading} />
        </TabsContent>

        <TabsContent value="data" className="space-y-4">
          <DataTab cpus={cpus || []} isLoading={isLoading} />
        </TabsContent>
      </Tabs>

      <CPUDetailModal />
    </div>
  );
}
```

---

#### FE-003: Create Catalog Tab Component (P0)
**Description:** Container for filter controls and view switcher

**Estimated Effort:** 3 hours

**Dependencies:** FE-001, FE-002

**Acceptance Criteria:**
- Filters and view switcher positioned correctly
- Client-side filtering applied to CPU list
- Filtered results passed to active view component
- Memoization prevents unnecessary re-renders
- Empty state shown when no results

**File:** `/mnt/containers/deal-brain/apps/web/app/cpus/_components/catalog-tab.tsx`

**Implementation Notes:**
- Follow pattern from `/apps/web/app/listings/_components/catalog-tab.tsx`
- Use `useMemo` for filtered CPU list
- Implement debounced search (200ms)
- Render GridView, ListView, or MasterDetailView based on activeView

---

#### FE-004: Create CPU Filters Component (P1)
**Description:** Filter panel with search, dropdowns, and range sliders

**Estimated Effort:** 6 hours

**Dependencies:** FE-001

**Acceptance Criteria:**
- Search input with debouncing (200ms)
- Manufacturer multi-select dropdown
- Socket multi-select dropdown
- Core count range slider (2-64)
- TDP range slider (15-280W)
- iGPU presence checkbox (Yes/No/Any)
- Minimum PassMark input
- "Clear all filters" button
- Filter count badge
- Collapsible on desktop, drawer on mobile

**File:** `/mnt/containers/deal-brain/apps/web/app/cpus/_components/cpu-filters.tsx`

**Implementation Notes:**
```typescript
import { useCPUCatalogStore } from "@/stores/cpu-catalog-store";
import { Input } from "@/components/ui/input";
import { MultiSelect } from "@/components/ui/multi-select";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { useDebounce } from "@/hooks/use-debounce";

export function CPUFilters() {
  const filters = useCPUCatalogStore((state) => state.filters);
  const setFilters = useCPUCatalogStore((state) => state.setFilters);
  const clearFilters = useCPUCatalogStore((state) => state.clearFilters);

  const debouncedSearch = useDebounce((value: string) => {
    setFilters({ searchQuery: value });
  }, 200);

  return (
    <div className="space-y-4">
      {/* Search */}
      <Input
        placeholder="Search CPUs..."
        defaultValue={filters.searchQuery}
        onChange={(e) => debouncedSearch(e.target.value)}
      />

      {/* Manufacturer */}
      <MultiSelect
        label="Manufacturer"
        options={['Intel', 'AMD', 'Apple']}
        value={filters.manufacturer}
        onChange={(value) => setFilters({ manufacturer: value })}
      />

      {/* Socket */}
      <MultiSelect
        label="Socket"
        options={['LGA1700', 'AM5', 'AM4', 'LGA1200']}
        value={filters.socket}
        onChange={(value) => setFilters({ socket: value })}
      />

      {/* Core Count Range */}
      <div>
        <label>Core Count: {filters.coreRange[0]}-{filters.coreRange[1]}</label>
        <Slider
          min={2}
          max={64}
          step={2}
          value={filters.coreRange}
          onValueChange={(value) => setFilters({ coreRange: value as [number, number] })}
        />
      </div>

      {/* TDP Range */}
      <div>
        <label>TDP: {filters.tdpRange[0]}W-{filters.tdpRange[1]}W</label>
        <Slider
          min={15}
          max={280}
          step={5}
          value={filters.tdpRange}
          onValueChange={(value) => setFilters({ tdpRange: value as [number, number] })}
        />
      </div>

      {/* Clear Filters */}
      <Button variant="outline" onClick={clearFilters}>
        Clear All Filters
      </Button>
    </div>
  );
}
```

---

#### FE-005: Create CPU Grid View Component (P0)
**Description:** Responsive grid layout with CPU cards

**Estimated Effort:** 8 hours

**Dependencies:** FE-006, FE-007, FE-008

**Acceptance Criteria:**
- Responsive grid (1-4 columns based on viewport)
- CPU cards display all key information
- Click to open detail modal
- Loading skeleton cards during fetch
- Empty state when no CPUs match filters
- Smooth hover animations
- Keyboard navigation support

**File:** `/mnt/containers/deal-brain/apps/web/app/cpus/_components/grid-view.tsx`

**Implementation Notes:**
```typescript
import React from "react";
import { CPUCard } from "./cpu-card";
import { CPUWithAnalytics } from "@/types/cpu";
import { Skeleton } from "@/components/ui/skeleton";

interface GridViewProps {
  cpus: CPUWithAnalytics[];
  isLoading?: boolean;
}

export const GridView = React.memo(function GridView({ cpus, isLoading }: GridViewProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-96" />
        ))}
      </div>
    );
  }

  if (cpus.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No CPUs found matching filters</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {cpus.map((cpu) => (
        <CPUCard key={cpu.id} cpu={cpu} />
      ))}
    </div>
  );
});
```

---

#### FE-006: Create CPU Card Component (P0)
**Description:** Individual CPU card for grid view

**Estimated Effort:** 6 hours

**Dependencies:** FE-007, FE-008

**Acceptance Criteria:**
- Displays CPU name, manufacturer badge
- Shows cores/threads, TDP, socket
- PassMark score bars (single/multi-thread)
- Performance badge component
- Price targets component
- "View Details" button
- Hover effects (elevation, scale)
- Click handler opens detail modal

**File:** `/mnt/containers/deal-brain/apps/web/app/cpus/_components/cpu-card.tsx`

**Implementation Notes:**
- Follow design from PRD Section 9.2
- Use shadcn/ui Card components
- Implement Progress bars for PassMark visualization
- Make entire card clickable (not just button)

---

#### FE-007: Create Performance Badge Component (P0)
**Description:** Color-coded badge showing $/PassMark rating

**Estimated Effort:** 4 hours

**Dependencies:** None

**Acceptance Criteria:**
- Four rating variants (excellent, good, fair, poor)
- Color coding matches design system (green/yellow/red)
- Arrow icons indicate performance direction
- Tooltip shows percentile rank and explanation
- Handles null/missing data gracefully
- Accessible (ARIA labels, keyboard support)

**File:** `/mnt/containers/deal-brain/apps/web/app/cpus/_components/performance-badge.tsx`

**Implementation Notes:**
```typescript
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ArrowDownIcon, ArrowUpIcon, MinusIcon } from "lucide-react";

interface PerformanceBadgeProps {
  rating: 'excellent' | 'good' | 'fair' | 'poor' | null;
  dollarPerMark: number | null;
  percentile?: number | null;
}

export function PerformanceBadge({
  rating,
  dollarPerMark,
  percentile
}: PerformanceBadgeProps) {
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
      color: 'bg-green-600 text-white hover:bg-green-700',
      icon: <ArrowDownIcon className="mr-1 h-3 w-3" />,
      label: 'Excellent Value',
      description: 'Top 25% for performance per dollar'
    },
    good: {
      color: 'bg-green-500 text-white hover:bg-green-600',
      icon: <ArrowDownIcon className="mr-1 h-3 w-3" />,
      label: 'Good Value',
      description: '25-50th percentile'
    },
    fair: {
      color: 'bg-yellow-500 text-black hover:bg-yellow-600',
      icon: <MinusIcon className="mr-1 h-3 w-3" />,
      label: 'Fair Value',
      description: '50-75th percentile'
    },
    poor: {
      color: 'bg-red-500 text-white hover:bg-red-600',
      icon: <ArrowUpIcon className="mr-1 h-3 w-3" />,
      label: 'Poor Value',
      description: 'Bottom 25%'
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
        <p className="text-sm">{config.description}</p>
        {percentile && (
          <p className="text-xs">Better than {(100 - percentile).toFixed(0)}% of CPUs</p>
        )}
      </TooltipContent>
    </Tooltip>
  );
}
```

---

#### FE-008: Create Price Targets Component (P0)
**Description:** Display Great/Good/Fair price ranges with confidence indicator

**Estimated Effort:** 4 hours

**Dependencies:** None

**Acceptance Criteria:**
- Shows all three price points (Great, Good, Fair)
- Confidence badge (high/medium/low) with tooltip
- Sample size display ("Based on N listings")
- Last updated timestamp
- Handles insufficient data case
- Color coding for price levels

**File:** `/mnt/containers/deal-brain/apps/web/app/cpus/_components/price-targets.tsx`

**Implementation Notes:**
- Refer to PRD Section 9.2 for component structure
- Use `formatDistanceToNow` from `date-fns` for timestamp
- Show alert for insufficient data (< 2 listings)

---

#### FE-009: Create CPU Detail Modal (P1)
**Description:** Comprehensive modal with all CPU details and analytics

**Estimated Effort:** 10 hours

**Dependencies:** BE-004, FE-007, FE-008

**Acceptance Criteria:**
- Modal opens from any view mode
- Five sections: Performance, Specs, Pricing, Market Data, Additional Info
- Lazy loads analytics data on open
- Charts render correctly (PassMark bars, price distribution)
- "View Listings" button navigates to filtered Listings page
- "Edit CPU" button (admin only)
- Keyboard accessible (ESC to close, Tab navigation)
- Focus trap while open
- Scroll lock on body

**File:** `/mnt/containers/deal-brain/apps/web/app/cpus/_components/cpu-detail-modal.tsx`

**Implementation Notes:**
```typescript
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useCPUCatalogStore } from "@/stores/cpu-catalog-store";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/utils";
import { CPUDetail } from "@/types/cpu";
import { PerformanceBadge } from "./performance-badge";
import { PriceTargets } from "./price-targets";

export function CPUDetailModal() {
  const detailModalOpen = useCPUCatalogStore((state) => state.detailModalOpen);
  const detailModalCPUId = useCPUCatalogStore((state) => state.detailModalCPUId);
  const closeDetailModal = useCPUCatalogStore((state) => state.closeDetailModal);

  const { data: cpu, isLoading } = useQuery({
    queryKey: ["cpu", detailModalCPUId, "detail"],
    queryFn: () => apiFetch<CPUDetail>(`/v1/cpus/${detailModalCPUId}`),
    enabled: detailModalOpen && !!detailModalCPUId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  return (
    <Dialog open={detailModalOpen} onOpenChange={(open) => !open && closeDetailModal()}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{cpu?.name || "Loading..."}</DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div>Loading...</div>
        ) : cpu ? (
          <div className="space-y-6">
            {/* Performance Overview Section */}
            <section>
              <h3 className="font-semibold mb-2">Performance Overview</h3>
              {/* PassMark bars, iGPU score */}
            </section>

            {/* Performance Value Section */}
            <section>
              <h3 className="font-semibold mb-2">Performance Value</h3>
              <PerformanceBadge
                rating={cpu.performance_value.rating}
                dollarPerMark={cpu.performance_value.dollar_per_mark_single}
                percentile={cpu.performance_value.percentile}
              />
            </section>

            {/* Specifications Section */}
            <section>
              <h3 className="font-semibold mb-2">Specifications</h3>
              {/* Grid of specs */}
            </section>

            {/* Target Pricing Section */}
            <section>
              <h3 className="font-semibold mb-2">Target Pricing</h3>
              <PriceTargets targets={cpu.price_targets} />
            </section>

            {/* Market Data Section */}
            <section>
              <h3 className="font-semibold mb-2">Market Data</h3>
              <p>{cpu.listings_count} active listings</p>
              {/* Price distribution chart */}
            </section>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
```

---

#### FE-010: Create Dense List View Component (P1)
**Description:** Compact list layout for CPUs

**Estimated Effort:** 5 hours

**Dependencies:** FE-007, FE-008

**Acceptance Criteria:**
- Compact rows with essential info inline
- Hover effects highlight row
- Click row to open detail modal
- Scrollable with sticky header
- Virtualized if > 100 CPUs

**File:** `/mnt/containers/deal-brain/apps/web/app/cpus/_components/list-view.tsx`

---

#### FE-011: Create Master-Detail View Component (P2)
**Description:** Split-screen layout with list and detail panel

**Estimated Effort:** 8 hours

**Dependencies:** FE-009

**Acceptance Criteria:**
- 30% list / 70% detail split
- Selected CPU highlights in list
- Detail panel scrollable independently
- Responsive (switches to grid on mobile)
- Keyboard navigation (arrow keys)

**File:** `/mnt/containers/deal-brain/apps/web/app/cpus/_components/master-detail-view.tsx`

---

#### FE-012: Create Data Tab Component (P1)
**Description:** Full-featured data table with sorting, filtering, pagination

**Estimated Effort:** 10 hours

**Dependencies:** None

**Acceptance Criteria:**
- All columns from PRD Section 5.7 table
- Sortable columns with direction indicator
- Column visibility toggle
- Pagination (25, 50, 100, 200 per page)
- Export to CSV button
- Row click opens detail modal
- Virtualized scrolling for 500+ rows

**File:** `/mnt/containers/deal-brain/apps/web/app/cpus/_components/data-tab.tsx`

**Implementation Notes:**
- Use `@tanstack/react-table` for table logic
- Use `react-window` for virtualization
- Implement CSV export using `papaparse`

---

### 3.4 State Management

#### SM-001: Implement URL Synchronization Hook (P1)
**Description:** Custom hook to sync store state with URL query parameters

**Estimated Effort:** 3 hours

**Dependencies:** FE-001

**Acceptance Criteria:**
- Active tab synced to URL (`?tab=catalog`)
- Active view synced to URL (`?view=grid`)
- Filters synced to URL (search, manufacturer, etc.)
- Detail modal ID synced (`?detail=123`)
- URL changes update store
- Store changes update URL (debounced)
- Browser back/forward buttons work correctly

**File:** `/mnt/containers/deal-brain/apps/web/hooks/use-url-sync-cpu.ts`

**Implementation Notes:**
```typescript
import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useCPUCatalogStore } from '@/stores/cpu-catalog-store';

export function useUrlSync() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const activeTab = useCPUCatalogStore((state) => state.activeTab);
  const activeView = useCPUCatalogStore((state) => state.activeView);
  const filters = useCPUCatalogStore((state) => state.filters);
  const detailModalCPUId = useCPUCatalogStore((state) => state.detailModalCPUId);

  const setActiveTab = useCPUCatalogStore((state) => state.setActiveTab);
  const setActiveView = useCPUCatalogStore((state) => state.setActiveView);
  const setFilters = useCPUCatalogStore((state) => state.setFilters);
  const openDetailModal = useCPUCatalogStore((state) => state.openDetailModal);

  // Read from URL on mount
  useEffect(() => {
    const tab = searchParams.get('tab');
    const view = searchParams.get('view');
    const search = searchParams.get('search');
    const detailId = searchParams.get('detail');

    if (tab && (tab === 'catalog' || tab === 'data')) {
      setActiveTab(tab);
    }
    if (view && ['grid', 'list', 'master-detail'].includes(view)) {
      setActiveView(view as CPUViewMode);
    }
    if (search) {
      setFilters({ searchQuery: search });
    }
    if (detailId) {
      openDetailModal(parseInt(detailId));
    }
  }, []);

  // Write to URL on state change (debounced)
  useEffect(() => {
    const params = new URLSearchParams();
    if (activeTab !== 'catalog') params.set('tab', activeTab);
    if (activeView !== 'grid') params.set('view', activeView);
    if (filters.searchQuery) params.set('search', filters.searchQuery);
    if (detailModalCPUId) params.set('detail', detailModalCPUId.toString());

    const newUrl = params.toString() ? `?${params.toString()}` : '';
    router.replace(`/cpus${newUrl}`, { scroll: false });
  }, [activeTab, activeView, filters.searchQuery, detailModalCPUId]);
}
```

---

### 3.5 Performance Calculations

#### PC-001: Add CPU Performance Metrics to Listings Integration (P1)
**Description:** Display CPU performance data in Listings table and detail modal

**Estimated Effort:** 6 hours

**Dependencies:** BE-003, FE-007

**Acceptance Criteria:**
- New "CPU Value" column in Listings table
- Column shows PerformanceBadge component
- New "CPU Target Price" column with delta from target
- Listing detail modal includes CPU performance section
- Data fetched via updated `/v1/listings` endpoint
- No performance degradation on Listings page

**Files:**
- `/mnt/containers/deal-brain/apps/web/components/listings/listings-table.tsx`
- `/mnt/containers/deal-brain/apps/web/components/listings/listing-details-dialog.tsx`

**Implementation Notes:**
```typescript
// Add columns to Listings table
{
  accessorKey: 'cpu.performance_value.rating',
  header: 'CPU Value',
  cell: ({ row }) => (
    <PerformanceBadge
      rating={row.original.cpu?.performance_value?.rating}
      dollarPerMark={row.original.cpu?.performance_value?.dollar_per_mark_single}
    />
  )
},
{
  accessorKey: 'cpu.price_targets.good',
  header: 'CPU Target Price',
  cell: ({ row }) => {
    const target = row.original.cpu?.price_targets?.good;
    const listingPrice = row.original.adjusted_price_usd;

    if (!target || !listingPrice) return '-';

    const delta = listingPrice - target;
    const deltaPercent = (delta / target) * 100;

    return (
      <div className="flex items-center gap-2">
        <span>${target.toFixed(2)}</span>
        <Badge variant={deltaPercent < 0 ? 'success' : 'warning'}>
          {deltaPercent > 0 ? '+' : ''}{deltaPercent.toFixed(1)}%
        </Badge>
      </div>
    );
  }
}
```

---

### 3.6 Testing

#### TEST-001: Backend Unit Tests (P0)
**Description:** Unit tests for CPU analytics service calculations

**Estimated Effort:** 8 hours

**Dependencies:** BE-002

**Acceptance Criteria:**
- Test `calculate_price_targets()` with various sample sizes
- Test edge cases (0 listings, 1 listing, outliers)
- Test `calculate_performance_value()` percentile logic
- Test `update_cpu_analytics()` persistence
- Test `recalculate_all_cpu_metrics()` batch processing
- Coverage > 80% for cpu_analytics.py

**File:** `/mnt/containers/deal-brain/tests/test_cpu_analytics_service.py`

**Implementation Notes:**
```python
import pytest
from dealbrain_api.services.cpu_analytics import CPUAnalyticsService

@pytest.mark.asyncio
async def test_calculate_price_targets_sufficient_data(session):
    """Test price targets with 10+ listings"""
    cpu_id = 1
    # Create 10 test listings with known prices
    # ...

    result = await CPUAnalyticsService.calculate_price_targets(session, cpu_id)

    assert result.sample_size == 10
    assert result.confidence == 'high'
    assert result.good == pytest.approx(350.0, rel=0.01)
    assert result.great < result.good
    assert result.fair > result.good

@pytest.mark.asyncio
async def test_calculate_price_targets_insufficient_data(session):
    """Test with < 2 listings"""
    cpu_id = 2
    # Create 1 listing
    # ...

    result = await CPUAnalyticsService.calculate_price_targets(session, cpu_id)

    assert result.sample_size == 1
    assert result.confidence == 'insufficient'
    assert result.good is None

# Add 10-15 more test cases covering edge cases
```

---

#### TEST-002: API Integration Tests (P1)
**Description:** Integration tests for CPU catalog endpoints

**Estimated Effort:** 6 hours

**Dependencies:** BE-003, BE-004, BE-005

**Acceptance Criteria:**
- Test GET /v1/cpus returns correct schema
- Test GET /v1/cpus/{id} returns full detail
- Test GET /v1/cpus/statistics returns valid ranges
- Test 404 handling for non-existent CPU
- Test analytics data populated correctly
- Coverage > 75% for catalog.py

**File:** `/mnt/containers/deal-brain/tests/test_api_catalog_cpus.py`

---

#### TEST-003: Frontend Component Tests (P1)
**Description:** React Testing Library tests for key components

**Estimated Effort:** 8 hours

**Dependencies:** FE-006, FE-007, FE-008, FE-009

**Acceptance Criteria:**
- Test CPUCard renders with valid data
- Test PerformanceBadge color coding
- Test PriceTargets insufficient data state
- Test CPUDetailModal opens/closes correctly
- Test filter interactions
- Test view switching
- Coverage > 70% for new components

**File:** `/mnt/containers/deal-brain/apps/web/__tests__/cpus/components.test.tsx`

**Implementation Notes:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { PerformanceBadge } from '@/app/cpus/_components/performance-badge';

describe('PerformanceBadge', () => {
  it('renders excellent rating with correct color', () => {
    render(
      <PerformanceBadge
        rating="excellent"
        dollarPerMark={0.05}
        percentile={15}
      />
    );

    const badge = screen.getByText(/0.05\/mark/);
    expect(badge).toHaveClass('bg-green-600');
  });

  it('shows no data state when rating is null', () => {
    render(<PerformanceBadge rating={null} dollarPerMark={null} />);

    expect(screen.getByText('No data')).toBeInTheDocument();
  });

  // Add 5-10 more test cases
});
```

---

#### TEST-004: E2E Scenarios (P2)
**Description:** End-to-end tests for critical user flows

**Estimated Effort:** 6 hours

**Dependencies:** All frontend and backend tasks

**Acceptance Criteria:**
- Test: Browse CPUs, filter, open detail modal
- Test: Switch between view modes
- Test: Navigate from CPU to Listings page
- Test: CPU metrics update after new listing added
- Tests run in CI pipeline

**Tool:** Playwright or Cypress

**File:** `/mnt/containers/deal-brain/e2e/cpu-catalog.spec.ts`

---

### 3.7 Documentation

#### DOC-001: API Documentation (P1)
**Description:** OpenAPI/Swagger documentation for new CPU endpoints

**Estimated Effort:** 3 hours

**Dependencies:** BE-003, BE-004, BE-005

**Acceptance Criteria:**
- All endpoints documented with request/response schemas
- Example responses provided
- Error codes documented
- Available at `/docs` endpoint

**File:** FastAPI auto-generates from route decorators

---

#### DOC-002: User Guide Updates (P2)
**Description:** Update user-facing documentation with CPU catalog features

**Estimated Effort:** 4 hours

**Dependencies:** All features complete

**Acceptance Criteria:**
- "CPU Catalog" section added to user guide
- Screenshots of all view modes
- Explanation of performance metrics and price targets
- Filter usage guide
- Published on docs site

**File:** `/mnt/containers/deal-brain/docs/user-guide/cpu-catalog.md`

---

#### DOC-003: Inline Help Text (P2)
**Description:** Tooltips and help text throughout UI

**Estimated Effort:** 2 hours

**Dependencies:** Frontend components

**Acceptance Criteria:**
- All metrics have tooltip explanations
- Filter controls have help icons
- Empty states have helpful guidance
- Error messages are actionable

**Implementation:** Add to component files during development

---

## 4. File Structure

### 4.1 New Files to Create

#### Backend Files

```
apps/api/
├── alembic/versions/
│   └── xxx_add_cpu_analytics_fields.py          # DB migration
├── dealbrain_api/
│   ├── services/
│   │   └── cpu_analytics.py                     # Analytics service (NEW)
│   ├── tasks/
│   │   └── cpu_metrics.py                       # Celery task (NEW)
│   └── api/
│       └── (catalog.py updated)                 # Extended with CPU endpoints

packages/core/
└── dealbrain_core/schemas/
    └── (cpu.py updated)                         # New analytics schemas
```

#### Frontend Files

```
apps/web/
├── app/cpus/
│   ├── page.tsx                                 # Main CPU page (NEW)
│   └── _components/
│       ├── catalog-tab.tsx                      # Catalog container (NEW)
│       ├── data-tab.tsx                         # Data table container (NEW)
│       ├── view-switcher.tsx                    # View mode toggle (NEW)
│       ├── cpu-filters.tsx                      # Filter panel (NEW)
│       ├── grid-view.tsx                        # Grid layout (NEW)
│       ├── list-view.tsx                        # List layout (NEW)
│       ├── master-detail-view.tsx               # Split view (NEW)
│       ├── cpu-card.tsx                         # Individual card (NEW)
│       ├── cpu-detail-modal.tsx                 # Detail modal (NEW)
│       ├── performance-badge.tsx                # Value badge (NEW)
│       ├── price-targets.tsx                    # Price ranges (NEW)
│       └── cpu-specifications.tsx               # Specs table (NEW)
├── stores/
│   └── cpu-catalog-store.ts                     # Zustand store (NEW)
├── hooks/
│   ├── use-url-sync-cpu.ts                      # URL sync (NEW)
│   ├── use-cpu-analytics.ts                     # Analytics hook (NEW)
│   └── use-cpu-filters.ts                       # Filter hook (NEW)
├── types/
│   └── cpu.ts                                   # TypeScript types (NEW)
└── lib/
    └── cpu-utils.ts                             # Utility functions (NEW)
```

#### Test Files

```
tests/
├── test_cpu_analytics_service.py                # Backend unit tests (NEW)
├── test_api_catalog_cpus.py                     # API integration tests (NEW)
└── (existing test files)

apps/web/
└── __tests__/cpus/
    ├── components.test.tsx                      # Component tests (NEW)
    └── store.test.ts                            # Store tests (NEW)

e2e/
└── cpu-catalog.spec.ts                          # E2E tests (NEW)
```

### 4.2 Existing Files to Modify

#### Backend Modifications

```
apps/api/dealbrain_api/
├── models/core.py                               # Add CPU analytics fields
├── api/catalog.py                               # Extend with CPU endpoints
└── api/listings.py                              # Add CPU analytics to response

packages/core/dealbrain_core/
└── schemas/cpu.py                               # Add analytics schemas
```

#### Frontend Modifications

```
apps/web/
├── components/listings/
│   ├── listings-table.tsx                       # Add CPU value columns
│   └── listing-details-dialog.tsx               # Add CPU performance section
└── app/
    └── layout.tsx                               # Add /cpus to navigation (if not present)
```

---

## 5. Technical Implementation Details

### 5.1 Database Migration Strategy

**Pre-Migration Checklist:**
- [ ] Backup production database
- [ ] Test migration on staging with production data snapshot (anonymized)
- [ ] Verify migration rollback script works
- [ ] Schedule deployment during low-traffic window (Sunday 2-4 AM UTC)

**Migration Execution Steps:**
1. Deploy backend code with migration (no traffic yet)
2. Run migration: `poetry run alembic upgrade head`
3. Verify all columns added: `\d cpu` in psql
4. Run data validation script (check for nulls, types)
5. Enable traffic to new endpoints
6. Monitor error rates for 15 minutes
7. If errors > 1%, rollback immediately

**Rollback Plan:**
```bash
# If migration fails or causes issues
poetry run alembic downgrade -1

# If data corruption detected
pg_restore --clean --if-exists -d dealbrain production_backup.dump
```

**Post-Migration:**
- Run `recalculate_all_cpu_metrics` task immediately
- Monitor database query performance (check slow query log)
- Verify indexes created correctly: `\d cpu` → check idx_ entries

---

### 5.2 API Endpoint Specifications

#### GET /v1/cpus

**Purpose:** List all CPUs with analytics data

**Query Parameters:**
```typescript
{
  include_analytics?: boolean;  // default: true
}
```

**Response Schema:**
```typescript
Array<{
  // Base CPU fields
  id: number;
  name: string;
  manufacturer: string;
  socket: string | null;
  cores: number | null;
  threads: number | null;
  tdp_w: number | null;
  igpu_model: string | null;
  cpu_mark_multi: number | null;
  cpu_mark_single: number | null;
  igpu_mark: number | null;
  release_year: number | null;

  // Analytics (if include_analytics=true)
  price_targets: {
    good: number | null;
    great: number | null;
    fair: number | null;
    sample_size: number;
    confidence: 'high' | 'medium' | 'low' | 'insufficient';
    stddev: number | null;
    updated_at: string | null;  // ISO 8601
  };
  performance_value: {
    dollar_per_mark_single: number | null;
    dollar_per_mark_multi: number | null;
    percentile: number | null;
    rating: 'excellent' | 'good' | 'fair' | 'poor' | null;
    updated_at: string | null;
  };
  listings_count: number;
}>
```

**Performance Target:** < 500ms P95 (100+ CPUs)

**Caching Strategy:**
- React Query: 5 min stale time, 10 min cache time
- Backend: No caching needed (data pre-computed in DB)

**Error Handling:**
- 500: Database connection error → Retry with exponential backoff
- Empty array: No CPUs in database → Show setup guide

---

#### GET /v1/cpus/{id}

**Purpose:** Get detailed CPU information with analytics and market data

**Path Parameters:**
- `id` (integer, required): CPU ID

**Response Schema:**
```typescript
{
  // All fields from GET /v1/cpus
  ...

  // Additional detail fields
  associated_listings: Array<{
    id: number;
    title: string;
    adjusted_price_usd: number | null;
    status: string;
    cpu_id: number;
  }>;
  market_data: {
    price_distribution: number[];  // All listing prices for histogram
    listings_total: number;
  };
}
```

**Performance Target:** < 300ms P95

**Caching Strategy:**
- React Query: 2 min stale time (modal content)
- Backend: No caching (real-time data preferred)

**Error Handling:**
- 404: CPU not found → Show error modal with "Go Back" button
- 500: Server error → Show retry button

---

#### GET /v1/cpus/statistics

**Purpose:** Global CPU statistics for filter dropdown populations

**Response Schema:**
```typescript
{
  manufacturers: string[];     // Unique manufacturers (sorted)
  sockets: string[];           // Unique sockets (sorted)
  core_range: [number, number]; // [min, max]
  tdp_range: [number, number];  // [min, max]
  year_range: [number, number]; // [min, max]
  total_count: number;
}
```

**Performance Target:** < 200ms P95

**Caching Strategy:**
- React Query: 10 min stale time (rarely changes)
- Backend: Redis cache 5 min TTL (optional optimization)

---

### 5.3 Service Layer Architecture

**CPUAnalyticsService Responsibilities:**
1. Calculate price targets from listing data
2. Calculate performance value metrics and percentile ranks
3. Update CPU table with computed analytics
4. Batch process all CPUs for nightly refresh

**Service Design Principles:**
- Pure functions for calculations (testable)
- Async/await for all database operations
- Explicit error handling with logging
- Transaction boundaries clearly defined

**Example Service Method:**
```python
class CPUAnalyticsService:
    @staticmethod
    async def calculate_price_targets(
        session: AsyncSession,
        cpu_id: int
    ) -> PriceTarget:
        """
        Calculate price targets from active listing adjusted prices.

        Algorithm:
        1. Fetch all active listings with this CPU
        2. Extract adjusted_price_usd values (exclude nulls, zeros)
        3. Calculate mean and standard deviation
        4. Set targets: good=mean, great=mean-stddev, fair=mean+stddev
        5. Determine confidence based on sample size

        Args:
            session: Database session
            cpu_id: ID of CPU to calculate targets for

        Returns:
            PriceTarget with calculated values

        Raises:
            ValueError: If cpu_id invalid
        """
        # Implementation (see BE-002 for full code)
```

**Error Handling Strategy:**
- Invalid CPU ID → Raise ValueError with descriptive message
- No listings → Return PriceTarget with confidence='insufficient'
- Database error → Log exception, re-raise for caller to handle
- Outlier detection → Flag but include in calculation (transparency)

---

### 5.4 Component Hierarchy

**CPU Catalog Page Component Tree:**
```
CPUsPage (page.tsx)
├── Header
│   ├── Title & Description
│   └── Add CPU Button (admin only)
├── Tabs
│   ├── CatalogTab
│   │   ├── CPUFilters
│   │   │   ├── SearchInput (debounced)
│   │   │   ├── ManufacturerSelect
│   │   │   ├── SocketSelect
│   │   │   ├── CoreRangeSlider
│   │   │   ├── TDPRangeSlider
│   │   │   ├── iGPUCheckbox
│   │   │   └── ClearFiltersButton
│   │   ├── ViewSwitcher (Grid | List | Master-Detail)
│   │   └── ActiveView
│   │       ├── GridView
│   │       │   └── CPUCard[]
│   │       │       ├── CPUHeader (name, manufacturer badge)
│   │       │       ├── CPUSpecs (cores, TDP, socket)
│   │       │       ├── PassMarkBars (single, multi, iGPU)
│   │       │       ├── PerformanceBadge
│   │       │       ├── PriceTargets
│   │       │       └── ViewDetailsButton
│   │       ├── ListView
│   │       │   └── CPUListItem[]
│   │       └── MasterDetailView
│   │           ├── CPUList (left panel)
│   │           └── CPUDetailPanel (right panel)
│   └── DataTab
│       ├── CPUsTable
│       │   ├── TableHeader (sortable columns)
│       │   ├── TableBody (virtualized rows)
│       │   └── TableFooter (pagination)
│       └── ExportButton
└── Modals
    ├── CPUDetailModal
    │   ├── PerformanceOverview
    │   ├── PerformanceValue
    │   ├── Specifications
    │   ├── TargetPricing
    │   ├── MarketData
    │   └── AdditionalInfo
    └── AddCPUModal (admin)
```

**Memoization Strategy:**
- All view components: `React.memo()`
- Filtered CPU list: `useMemo([cpus, filters])`
- Event handlers: `useCallback()`
- Expensive calculations: `useMemo()`

---

### 5.5 State Management Flow

**Zustand Store State Machine:**
```
Initial State
  ↓
User Action (filter change, view switch, etc.)
  ↓
Store Update (setFilters, setActiveView)
  ↓
URL Update (via useUrlSync hook)
  ↓
Component Re-render (subscribers notified)
  ↓
Client-side Filter Application (useMemo)
  ↓
View Re-render (memoized)
```

**State Persistence Strategy:**
- **Persisted:** activeView, activeTab, filters (localStorage)
- **Session-only:** selectedCPUId, detailModalOpen, compareCPUs
- **Never persisted:** isLoading, error states

**URL Synchronization:**
```
Store State          URL Parameter
───────────────      ─────────────
activeTab            ?tab=catalog
activeView           ?view=grid
searchQuery          ?search=i7
manufacturer         ?mfr=Intel,AMD
detailModalCPUId     ?detail=123
```

---

### 5.6 React Query Cache Strategy

**Query Keys:**
```typescript
// List all CPUs with analytics
["cpus", "analytics"]

// Single CPU detail
["cpu", cpuId, "detail"]

// CPU statistics (for filters)
["cpus", "statistics"]

// Associated listings for a CPU
["cpu", cpuId, "listings"]
```

**Cache Configuration:**
```typescript
// Global defaults (already configured)
{
  staleTime: 5 * 60 * 1000,  // 5 minutes
  cacheTime: 10 * 60 * 1000, // 10 minutes
}

// CPU-specific overrides
{
  queryKey: ["cpus", "analytics"],
  staleTime: 5 * 60 * 1000,   // 5 minutes (moderate freshness)
}

{
  queryKey: ["cpu", cpuId, "detail"],
  staleTime: 2 * 60 * 1000,   // 2 minutes (fresher for modal)
}

{
  queryKey: ["cpus", "statistics"],
  staleTime: 10 * 60 * 1000,  // 10 minutes (rarely changes)
}
```

**Cache Invalidation Strategy:**
- After CPU created/updated: Invalidate `["cpus"]` queries
- After listing created/updated: Invalidate `["cpus", "analytics"]` (price targets affected)
- After metric recalculation: Invalidate all CPU queries

**Optimistic Updates:**
- Not needed (read-only views, no user edits in catalog)

---

## 6. Testing Strategy

### 6.1 Unit Tests (Backend)

**Scope:** Service layer calculations, utility functions

**Coverage Target:** > 80%

**Key Test Cases:**
1. **Price Target Calculation:**
   - 10+ listings (high confidence)
   - 5-9 listings (medium confidence)
   - 2-4 listings (low confidence)
   - 0-1 listings (insufficient)
   - Outliers present (high std dev)

2. **Performance Value Calculation:**
   - Valid benchmark scores and prices
   - Missing benchmark scores
   - Missing listing prices
   - Percentile edge cases (0%, 25%, 50%, 75%, 100%)

3. **Update CPU Analytics:**
   - Successful update with all fields
   - Partial data (some nulls)
   - Database constraint violations

4. **Recalculate All Metrics:**
   - Batch processing efficiency
   - Error handling (continue on failure)
   - Summary statistics accuracy

**Example Test:**
```python
@pytest.mark.asyncio
async def test_calculate_price_targets_with_outliers(session):
    """Test price targets with one extreme outlier"""
    cpu_id = 1
    # Create 9 listings at $300-320
    # Create 1 outlier at $1000

    result = await CPUAnalyticsService.calculate_price_targets(session, cpu_id)

    # Outlier should increase std dev significantly
    assert result.stddev > 100  # High variance
    assert result.confidence == 'high'  # Sample size still 10
    # Mean should be pulled up by outlier
    assert result.good > 350
```

---

### 6.2 API Integration Tests

**Scope:** Endpoint request/response validation

**Coverage Target:** > 75%

**Key Test Cases:**
1. **GET /v1/cpus:**
   - Returns all CPUs
   - Analytics fields populated
   - Listings count accurate
   - Query parameter `include_analytics=false` works

2. **GET /v1/cpus/{id}:**
   - Returns full CPU detail
   - Associated listings included
   - Market data populated
   - 404 for invalid ID

3. **GET /v1/cpus/statistics:**
   - Returns all unique values
   - Ranges correct
   - Total count matches database

4. **POST /v1/cpus/recalculate-metrics:**
   - Returns 202 Accepted
   - Background task triggered
   - Admin-only (401 for non-admin)

**Example Test:**
```python
@pytest.mark.asyncio
async def test_get_cpu_detail_success(client, session):
    """Test GET /v1/cpus/{id} returns full detail"""
    # Create test CPU with listings
    cpu = await create_test_cpu(session, name="Intel i7-13700K")
    await create_test_listings(session, cpu_id=cpu.id, count=5)

    response = await client.get(f"/v1/cpus/{cpu.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == cpu.id
    assert data["name"] == "Intel i7-13700K"
    assert "price_targets" in data
    assert "performance_value" in data
    assert "associated_listings" in data
    assert len(data["associated_listings"]) == 5
```

---

### 6.3 Component Tests (Frontend)

**Scope:** React components in isolation

**Coverage Target:** > 70%

**Key Test Cases:**
1. **PerformanceBadge:**
   - Renders all rating variants
   - Color coding correct
   - Tooltip shows percentile
   - Null data shows "No data"

2. **PriceTargets:**
   - Shows all three prices
   - Confidence badge correct
   - Insufficient data alert
   - Updated timestamp formats correctly

3. **CPUCard:**
   - Renders CPU data
   - Click opens detail modal
   - PassMark bars scale correctly
   - Missing data handled gracefully

4. **CPUDetailModal:**
   - Opens/closes correctly
   - Loads data on open
   - All sections render
   - ESC key closes modal

5. **CPUFilters:**
   - Search input debounces
   - Multi-select updates store
   - Sliders update ranges
   - Clear button resets all

**Example Test:**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CPUCard } from '@/app/cpus/_components/cpu-card';
import { useCPUCatalogStore } from '@/stores/cpu-catalog-store';

const mockCPU = {
  id: 1,
  name: 'Intel Core i7-13700K',
  manufacturer: 'Intel',
  cores: 16,
  threads: 24,
  tdp_w: 125,
  socket: 'LGA1700',
  cpu_mark_single: 4231,
  cpu_mark_multi: 41678,
  price_targets: {
    good: 350,
    great: 320,
    fair: 380,
    sample_size: 10,
    confidence: 'high',
  },
  performance_value: {
    dollar_per_mark_single: 0.0623,
    rating: 'excellent',
    percentile: 22.5,
  },
  listings_count: 12,
};

describe('CPUCard', () => {
  it('renders CPU information correctly', () => {
    render(<CPUCard cpu={mockCPU} />);

    expect(screen.getByText('Intel Core i7-13700K')).toBeInTheDocument();
    expect(screen.getByText('Intel')).toBeInTheDocument();
    expect(screen.getByText('16/24')).toBeInTheDocument();
    expect(screen.getByText('125W')).toBeInTheDocument();
  });

  it('opens detail modal on click', () => {
    const openDetailModal = jest.fn();
    useCPUCatalogStore.setState({ openDetailModal });

    render(<CPUCard cpu={mockCPU} />);

    fireEvent.click(screen.getByText('View Details'));

    expect(openDetailModal).toHaveBeenCalledWith(1);
  });

  it('displays performance badge with correct rating', () => {
    render(<CPUCard cpu={mockCPU} />);

    const badge = screen.getByText(/0.06/);  // $0.0623/mark
    expect(badge).toHaveClass('bg-green-600');  // Excellent rating
  });
});
```

---

### 6.4 E2E Scenarios

**Tool:** Playwright

**Scope:** Critical user journeys end-to-end

**Coverage Target:** 5-10 key scenarios

**Key Scenarios:**
1. **Browse and Filter CPUs:**
   - Navigate to /cpus
   - Enter search query
   - Select manufacturer filter
   - Verify filtered results

2. **View Mode Switching:**
   - Switch to List view
   - Switch to Master-Detail view
   - Switch back to Grid view
   - Verify URL updates

3. **CPU Detail Modal:**
   - Click CPU card
   - Modal opens with details
   - Close with ESC key
   - Modal state cleared

4. **Navigate to Listings:**
   - Open CPU detail modal
   - Click "View Listings" button
   - Verify redirect to /listings?cpu=123
   - Listings filtered by CPU

5. **Performance Metrics Display:**
   - Verify PerformanceBadge colors
   - Verify price targets show
   - Verify tooltips appear on hover

**Example E2E Test:**
```typescript
// cpu-catalog.spec.ts
import { test, expect } from '@playwright/test';

test('browse CPUs and open detail modal', async ({ page }) => {
  // Navigate to CPU catalog
  await page.goto('/cpus');

  // Verify page loaded
  await expect(page.locator('h1')).toContainText('CPUs');

  // Search for specific CPU
  await page.fill('input[placeholder="Search CPUs..."]', 'i7-13700K');

  // Wait for debounce
  await page.waitForTimeout(300);

  // Verify filtered results
  const cpuCards = page.locator('[data-testid="cpu-card"]');
  await expect(cpuCards).toHaveCount(1);

  // Click CPU card to open modal
  await cpuCards.first().click();

  // Verify modal opened
  const modal = page.locator('[role="dialog"]');
  await expect(modal).toBeVisible();
  await expect(modal).toContainText('Intel Core i7-13700K');

  // Verify performance section visible
  await expect(modal.locator('text=Performance Overview')).toBeVisible();
  await expect(modal.locator('text=Target Pricing')).toBeVisible();

  // Close modal with ESC
  await page.keyboard.press('Escape');
  await expect(modal).not.toBeVisible();
});

test('filter CPUs by manufacturer', async ({ page }) => {
  await page.goto('/cpus');

  // Open manufacturer filter
  await page.click('button:has-text("Manufacturer")');

  // Select Intel
  await page.click('text=Intel');

  // Verify URL updated
  await expect(page).toHaveURL(/mfr=Intel/);

  // Verify all visible CPUs are Intel
  const manufacturerBadges = page.locator('[data-testid="manufacturer-badge"]');
  const count = await manufacturerBadges.count();
  for (let i = 0; i < count; i++) {
    await expect(manufacturerBadges.nth(i)).toHaveText('Intel');
  }
});
```

---

## 7. Performance Optimization Checklist

### 7.1 Backend Optimization

- [ ] **Database Indexes Created**
  - `idx_cpu_price_targets` on (price_target_good, price_target_confidence)
  - `idx_cpu_performance_value` on (dollar_per_mark_single, dollar_per_mark_multi)
  - `idx_cpu_manufacturer` on (manufacturer)
  - `idx_cpu_socket` on (socket)
  - `idx_cpu_cores` on (cores)

- [ ] **Query Optimization**
  - Use `selectinload` for eager loading relationships
  - Avoid N+1 queries (single query for CPU list with analytics)
  - Use `func.count()` instead of loading all listings for counts
  - Batch operations in nightly recalculation (50 CPUs at a time)

- [ ] **Response Caching**
  - React Query client-side caching (5 min stale time)
  - Optional: Redis caching for `/v1/cpus/statistics` (5 min TTL)

- [ ] **Analytics Pre-computation**
  - Store all analytics in CPU table (not computed per request)
  - Nightly task refreshes stale data
  - On-demand recalculation for new listings

### 7.2 Frontend Optimization

- [ ] **Component Memoization**
  - `React.memo()` on GridView, ListView, MasterDetailView
  - `React.memo()` on CPUCard, CPUListItem
  - `useMemo()` for filtered CPU list
  - `useCallback()` for all event handlers

- [ ] **Debouncing/Throttling**
  - Search input debounced (200ms)
  - Filter changes debounced
  - URL updates debounced (300ms)
  - Scroll event handlers throttled

- [ ] **Code Splitting**
  - Lazy load CPUDetailModal (only when opened)
  - Lazy load chart components (if using recharts)
  - Dynamic imports for heavy dependencies

- [ ] **Virtualization**
  - Data table virtualized with `react-window` (500+ rows)
  - Grid view uses native CSS grid (no virtualization needed < 100 items)

- [ ] **Image/Asset Optimization**
  - Use Next.js Image component for any images
  - SVG icons optimized (lucide-react already optimized)
  - No unnecessary bundle size increases

### 7.3 Performance Benchmarks

**Target Metrics:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (GET /v1/cpus) | < 500ms P95 | Backend logs, APM |
| API Response Time (GET /v1/cpus/{id}) | < 300ms P95 | Backend logs, APM |
| Page Load Time (TTI) | < 1.5s | Lighthouse |
| Modal Open Time | < 300ms | Chrome DevTools Performance |
| Filter Application | < 200ms | Chrome DevTools Performance |
| Data Table Render (100 rows) | < 500ms | Chrome DevTools Performance |
| Lighthouse Performance Score | > 90 | Lighthouse CI |
| First Contentful Paint | < 1.2s | Lighthouse |
| Total Blocking Time | < 300ms | Lighthouse |

**Monitoring Setup:**
- Enable Prometheus metrics for new endpoints
- Add custom timing metrics for analytics calculations
- Set up Grafana dashboard for CPU catalog performance
- Configure alerts for P95 latency > target

---

## 8. Accessibility Checklist

### 8.1 Keyboard Navigation

- [ ] **Tab Navigation**
  - All interactive elements focusable
  - Logical tab order (top-to-bottom, left-to-right)
  - Skip links for main content
  - No keyboard traps

- [ ] **Keyboard Shortcuts**
  - Enter/Space: Activate buttons, open modals
  - Escape: Close modals, clear search
  - Arrow keys: Navigate table rows, filter options
  - Home/End: Jump to first/last item
  - Tab: Move to next focusable element
  - Shift+Tab: Move to previous focusable element

- [ ] **Focus Management**
  - Visible focus indicators (2px outline)
  - Focus trapped in modal when open
  - Focus restored to trigger element on modal close
  - Focus moves to first input in filters when opened

### 8.2 Screen Reader Support

- [ ] **ARIA Labels**
  - All icons have `aria-label`
  - Buttons have descriptive labels
  - Form inputs have associated labels
  - Complex widgets have `aria-labelledby`

- [ ] **ARIA Roles**
  - Dialog role on modals
  - Tablist, tab, tabpanel for tabs
  - Searchbox role on search input
  - Grid role on data table (if applicable)

- [ ] **Live Regions**
  - Filter application announces result count
  - Sort changes announced
  - Modal open/close announced
  - Error messages in live region

- [ ] **Screen Reader Testing**
  - Test with NVDA (Windows)
  - Test with JAWS (Windows)
  - Test with VoiceOver (macOS, iOS)
  - All content announced correctly
  - Navigation logical and understandable

### 8.3 Visual Accessibility

- [ ] **Color Contrast**
  - Text: 4.5:1 minimum (WCAG AA)
  - Large text: 3:1 minimum
  - UI components: 3:1 minimum
  - Performance badges meet contrast requirements
  - Price target colors meet contrast

- [ ] **Color Independence**
  - Information not conveyed by color alone
  - Icons supplement color coding
  - Text labels for all color-coded elements

- [ ] **Text Sizing**
  - All text resizable up to 200% without breaking layout
  - No horizontal scrolling at 200% zoom
  - Touch targets minimum 44x44px (mobile)

- [ ] **Motion/Animation**
  - Respect `prefers-reduced-motion`
  - Disable animations for users with motion sensitivity
  - No auto-playing animations > 5 seconds

### 8.4 Accessibility Audit Tools

- [ ] **Automated Testing**
  - axe DevTools: 0 critical violations
  - WAVE: 0 errors
  - Lighthouse Accessibility: Score > 95

- [ ] **Manual Testing**
  - Keyboard-only navigation test
  - Screen reader walkthrough
  - Color contrast verification
  - Zoom/resize testing (200%, 400%)

---

## 9. Risk Mitigation

### 9.1 Identified Risks with Mitigation Tasks

#### Risk 1: Insufficient Listing Data for Price Targets

**Probability:** High
**Impact:** High
**Description:** Many CPUs may have < 2 listings, resulting in "Insufficient data" messages throughout UI

**Mitigation Tasks:**
1. **Pre-Launch Audit (DB-003):**
   - Write script to count listings per CPU
   - Generate report showing data coverage
   - Identify CPUs with 0-1 listings
   - **Acceptance:** Report generated before frontend development starts

2. **Alternative Messaging (FE-013):**
   - Create "Insufficient data" component with helpful CTA
   - Add "View similar CPUs" suggestion
   - Include "Add listing" button for admin users
   - **Acceptance:** Empty state tested and approved by PM

3. **Aggregate Similar CPUs (BE-008):**
   - (Future enhancement) Group CPUs by tier (e.g., all i7-13xxx)
   - Calculate aggregate price targets
   - **Acceptance:** Out of scope for MVP, added to backlog

**Monitoring:**
- Daily job reports % of CPUs with sufficient data
- Alert if < 60% have 5+ listings

---

#### Risk 2: Performance Degradation on CPU List Endpoint

**Probability:** Medium
**Impact:** High
**Description:** GET /v1/cpus endpoint may be slow with 500+ CPUs and analytics joins

**Mitigation Tasks:**
1. **Query Optimization (BE-009):**
   - Use `EXPLAIN ANALYZE` to profile query
   - Ensure indexes utilized correctly
   - Eagerly load only necessary relationships
   - **Acceptance:** Query plan shows index scans, not sequential scans

2. **Load Testing (TEST-005):**
   - Test endpoint with 500 CPUs
   - Measure P95, P99 latencies
   - Simulate concurrent requests (50 req/s)
   - **Acceptance:** P95 < 500ms under load

3. **Response Caching (BE-010):**
   - Implement Redis cache layer (optional)
   - 5 min TTL for /v1/cpus response
   - Invalidate on CPU create/update
   - **Acceptance:** Cache hit ratio > 80%

4. **Pagination (BE-011):**
   - Add `limit` and `offset` query params
   - Default limit: 100 CPUs per page
   - **Acceptance:** Frontend pagination working

**Monitoring:**
- APM tracks endpoint latency
- Alert if P95 > 600ms

---

#### Risk 3: User Confusion About Percentile-Based Ratings

**Probability:** Medium
**Impact:** Medium
**Description:** Users may not understand how $/PassMark percentile ratings work

**Mitigation Tasks:**
1. **Comprehensive Tooltips (FE-014):**
   - Add detailed tooltip to PerformanceBadge
   - Explain percentile rank with example
   - Include "Learn More" link to docs
   - **Acceptance:** Tooltip includes visual example

2. **User Guide Section (DOC-004):**
   - Write "Understanding Performance Metrics" guide
   - Include visual diagrams
   - Provide example calculations
   - **Acceptance:** Guide reviewed and approved

3. **Onboarding Tour (FE-015):**
   - (Optional) Add first-visit walkthrough
   - Highlight key features
   - Explain metrics interactively
   - **Acceptance:** Out of scope for MVP

**Monitoring:**
- User feedback survey after 2 weeks
- Track clicks on "Learn More" links

---

#### Risk 4: Mobile UX Complexity

**Probability:** Medium
**Impact:** Medium
**Description:** Complex data visualizations and multi-column grids may not work well on mobile

**Mitigation Tasks:**
1. **Simplified Mobile Views (FE-016):**
   - Auto-switch to Grid view on mobile (< 768px)
   - Disable Master-Detail view on small screens
   - Reduce CPU card content density
   - **Acceptance:** Mobile layout tested on real devices (iPhone, Android)

2. **Touch Optimization (FE-017):**
   - Ensure tap targets > 44x44px
   - Add touch-friendly controls (larger sliders)
   - Test swipe gestures for filter drawer
   - **Acceptance:** Touch testing passed on 3 devices

3. **Performance Testing (TEST-006):**
   - Test on lower-end Android devices
   - Measure FID, CLS on mobile
   - Optimize bundle size for mobile
   - **Acceptance:** Lighthouse mobile score > 85

**Monitoring:**
- Track mobile bounce rate
- Monitor mobile page load times

---

#### Risk 5: Database Migration Breaks Existing Listings Functionality

**Probability:** Low
**Impact:** Critical
**Description:** Migration adds columns to CPU table; if errors occur, entire app could be down

**Mitigation Tasks:**
1. **Staging Migration Test (DB-004):**
   - Copy production data to staging (anonymized)
   - Run migration on staging
   - Verify Listings page still works
   - **Acceptance:** All existing tests pass post-migration

2. **Rollback Script Prepared (DB-005):**
   - Write and test downgrade migration
   - Document rollback procedure
   - Practice rollback on staging
   - **Acceptance:** Rollback completes in < 5 minutes

3. **Deployment Window (OPS-001):**
   - Schedule deployment during low-traffic period
   - Notify users of maintenance window
   - Have DBA on standby
   - **Acceptance:** Deployment plan approved

4. **Monitoring During Deployment (OPS-002):**
   - Watch error rates in real-time
   - Monitor database CPU/memory
   - Check slow query log
   - **Acceptance:** Runbook created for on-call engineer

**Rollback Criteria:**
- Error rate > 1% after migration
- P95 latency > 2x baseline
- Any database constraint violations

---

## 10. Quality Gates

### 10.1 Code Review Requirements

**Before Merge:**
- [ ] All code changes reviewed by at least 1 senior engineer
- [ ] Backend changes reviewed by backend lead
- [ ] Frontend changes reviewed by frontend lead
- [ ] No unresolved comments in PR
- [ ] All CI checks passing (linters, tests, build)

**Code Review Checklist:**
- [ ] Code follows project style guide (Black, ESLint)
- [ ] No hardcoded values (use constants, environment variables)
- [ ] Error handling comprehensive
- [ ] Logging adequate for debugging
- [ ] No performance anti-patterns (N+1 queries, unnecessary renders)
- [ ] Accessibility requirements met
- [ ] Security concerns addressed (input validation, SQL injection prevention)

---

### 10.2 Testing Requirements Before Merge

**Backend:**
- [ ] All new service methods have unit tests
- [ ] API endpoints have integration tests
- [ ] Test coverage > 80% for new code
- [ ] All tests passing (pytest)
- [ ] No skipped tests without justification

**Frontend:**
- [ ] All new components have tests
- [ ] Critical user flows have E2E tests
- [ ] Test coverage > 70% for new components
- [ ] All tests passing (Jest, Playwright)
- [ ] Visual regression tests passed (if applicable)

**Manual Testing:**
- [ ] Feature tested in Chrome, Firefox, Safari
- [ ] Mobile tested on iOS and Android
- [ ] Keyboard navigation tested
- [ ] Screen reader tested (NVDA or VoiceOver)

---

### 10.3 Performance Benchmarks

**Must Pass Before Production:**
- [ ] GET /v1/cpus: P95 < 500ms (100+ CPUs)
- [ ] GET /v1/cpus/{id}: P95 < 300ms
- [ ] CPU page TTI < 1.5s
- [ ] Modal open < 300ms
- [ ] Filter application < 200ms
- [ ] Lighthouse Performance > 90
- [ ] Lighthouse Accessibility > 95
- [ ] No bundle size increase > 100KB

**Load Testing:**
- [ ] API handles 50 req/s without degradation
- [ ] Database queries optimized (index usage verified)
- [ ] No memory leaks (frontend or backend)

---

### 10.4 Accessibility Audit

**Must Pass Before Production:**
- [ ] axe DevTools: 0 critical violations, < 5 moderate
- [ ] WAVE: 0 errors, < 10 warnings
- [ ] Lighthouse Accessibility: > 95
- [ ] Manual keyboard navigation: All features accessible
- [ ] Manual screen reader test: All content understandable
- [ ] Color contrast: All text/UI elements meet WCAG AA
- [ ] Focus indicators: Visible on all interactive elements

---

## 11. Deployment Plan

### 11.1 Pre-Deployment Checklist

**Code Readiness:**
- [ ] All PRs merged to `main` branch
- [ ] CI/CD pipeline passing (tests, linters, build)
- [ ] Version tagged (e.g., `v1.5.0-cpu-catalog`)
- [ ] CHANGELOG.md updated

**Infrastructure Readiness:**
- [ ] Database backup completed
- [ ] Migration script reviewed and approved
- [ ] Rollback plan documented and tested
- [ ] Monitoring dashboards created
- [ ] Alerts configured (latency, error rate)

**Communication:**
- [ ] Deployment scheduled (Sunday 2-4 AM UTC)
- [ ] Stakeholders notified (PM, team leads)
- [ ] User-facing announcement drafted (if applicable)
- [ ] Support team briefed on new features

---

### 11.2 Migration Execution Steps

**Step 1: Pre-Deployment (30 min before)**
1. Verify staging migration successful
2. Create production database backup
3. Put application in maintenance mode (optional)
4. Verify rollback script ready

**Step 2: Deploy Backend (T+0)**
1. Deploy API code to production (no traffic yet)
   ```bash
   git checkout v1.5.0-cpu-catalog
   docker build -t dealbrain-api:v1.5.0 apps/api
   docker push dealbrain-api:v1.5.0
   ```
2. Update Kubernetes/Docker deployment
3. Wait for health checks to pass

**Step 3: Run Migration (T+5)**
1. SSH into production database server
2. Run migration:
   ```bash
   cd /app
   poetry run alembic upgrade head
   ```
3. Verify columns added:
   ```sql
   \d cpu
   -- Check for 12 new columns
   ```
4. Check migration logs for errors

**Step 4: Initial Data Population (T+10)**
1. Trigger metric recalculation:
   ```bash
   curl -X POST https://api.dealbrain.com/v1/cpus/recalculate-metrics \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```
2. Monitor background task completion
3. Verify sample CPUs have analytics populated

**Step 5: Deploy Frontend (T+20)**
1. Build and deploy Next.js app:
   ```bash
   cd apps/web
   pnpm build
   docker build -t dealbrain-web:v1.5.0 .
   docker push dealbrain-web:v1.5.0
   ```
2. Update deployment
3. Wait for health checks

**Step 6: Enable Traffic (T+25)**
1. Remove maintenance mode
2. Route 10% traffic to new version (canary)
3. Monitor error rates for 5 minutes
4. If stable, route 100% traffic

**Step 7: Post-Deployment Verification (T+30)**
1. Smoke test critical paths:
   - Visit /cpus page
   - Open CPU detail modal
   - Check Listings integration
2. Verify metrics dashboards
3. Check error logs
4. Test rollback procedure (staging only)

---

### 11.3 Rollout Phases

**Phase 1: Internal Beta (Week 1)**
- Deploy to staging environment
- Internal team testing (5-10 users)
- Bug triage and fixes
- Performance validation

**Criteria to Proceed:**
- [ ] No P0 bugs
- [ ] < 3 P1 bugs
- [ ] All performance benchmarks met
- [ ] Positive feedback from team

---

**Phase 2: Limited Rollout (Week 2)**
- Deploy to production with feature flag
- Enable for 10% of users (random selection)
- Monitor metrics:
  - Error rate < 0.5%
  - P95 latency < targets
  - User engagement > baseline
- Gather user feedback (in-app survey)

**Criteria to Proceed:**
- [ ] Error rate stable
- [ ] No critical bugs reported
- [ ] Positive user sentiment (> 3.5/5 stars)

---

**Phase 3: Full Rollout (Week 3)**
- Increase to 50% of users
- Monitor for 2 days
- Address any P1/P2 bugs
- Optimize based on feedback

**Criteria to Proceed:**
- [ ] All P1 bugs resolved
- [ ] Performance stable at scale
- [ ] No rollback incidents

---

**Phase 4: General Availability (Week 4)**
- Enable for 100% of users
- Publish announcement (blog post, email)
- Update user documentation
- Train support team
- Remove feature flag

**Success Metrics (30 days post-GA):**
- CPU page views: 200+ unique users/day
- Detail modal opens: 50+ interactions/day
- Average time on page: > 2 minutes
- User satisfaction: > 4/5 stars

---

### 11.4 Feature Flag Strategy

**Flag Configuration:**
```typescript
// Environment variable
FEATURE_CPU_CATALOG_ENABLED=true

// LaunchDarkly or similar
{
  "cpu-catalog": {
    "enabled": true,
    "rollout": {
      "percentage": 100,
      "targetUsers": ["admin", "beta-testers"]
    }
  }
}
```

**Frontend Usage:**
```typescript
import { useFeatureFlag } from '@/hooks/use-feature-flag';

export default function Navigation() {
  const cpuCatalogEnabled = useFeatureFlag('cpu-catalog');

  return (
    <nav>
      <Link href="/listings">Listings</Link>
      {cpuCatalogEnabled && (
        <Link href="/cpus">CPUs</Link>
      )}
    </nav>
  );
}
```

**Rollback:**
- Set `FEATURE_CPU_CATALOG_ENABLED=false`
- Or reduce rollout percentage to 0%
- No code deployment needed

---

### 11.5 Monitoring and Alerts

**Metrics to Monitor:**
1. **Error Rate**
   - Alert if > 1% of requests fail
   - Dashboard: Grafana panel showing 5xx errors

2. **Latency**
   - Alert if P95 > 600ms for /v1/cpus
   - Alert if P95 > 400ms for /v1/cpus/{id}

3. **Database Performance**
   - Alert if CPU > 80%
   - Alert if slow queries > 1s

4. **User Engagement**
   - Track page views, bounce rate
   - Track modal open rate
   - Track filter usage

**Alert Configuration (Prometheus):**
```yaml
groups:
  - name: cpu-catalog
    rules:
      - alert: CPUCatalogHighErrorRate
        expr: rate(http_requests_total{path="/v1/cpus", status=~"5.."}[5m]) > 0.01
        annotations:
          summary: "CPU catalog error rate > 1%"

      - alert: CPUCatalogSlowResponse
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{path="/v1/cpus"}[5m])) > 0.6
        annotations:
          summary: "CPU catalog P95 latency > 600ms"
```

---

## 12. Post-Launch

### 12.1 User Feedback Collection Plan

**In-App Survey (Week 1-2):**
- Trigger after 3 interactions with CPU catalog
- 3 questions:
  1. "How useful is the CPU catalog?" (1-5 stars)
  2. "Which feature do you find most valuable?" (checkboxes)
  3. "What would you improve?" (free text)
- Store responses in database for analysis

**User Interviews (Week 3-4):**
- Recruit 5-10 active users
- 30-min video call
- Ask about workflow, pain points, feature requests
- Document insights in product backlog

**Analytics Tracking:**
- Track page views, time on page
- Track filter usage (which filters most popular)
- Track view mode preferences (grid vs list vs master-detail)
- Track modal open rate, "View Listings" click rate

---

### 12.2 Metrics to Monitor

**Engagement Metrics:**
- Daily active users on /cpus page
- Average time on page
- Bounce rate
- Detail modal open rate
- Listings navigation from CPU page (conversion)

**Performance Metrics:**
- API response times (P50, P95, P99)
- Page load times (FCP, LCP, TTI)
- Error rates (4xx, 5xx)
- Cache hit rates

**Business Metrics:**
- Does CPU catalog increase Listing detail views?
- Does it reduce time-to-decision for users?
- Correlation between CPU catalog usage and user retention

**Target KPIs (30 days):**
- CPU page views: 1000+ unique users
- Avg time on page: > 2 minutes
- Detail modal opens: 200+ interactions
- Listings navigation: 20% of CPU detail modal views
- User satisfaction: > 4/5 stars

---

### 12.3 Iteration Priorities

**Phase 2 Enhancements (Backlog):**
1. **CPU Comparison Modal (P1)**
   - Side-by-side comparison of 2-4 CPUs
   - Highlight differences
   - Share comparison URL

2. **Price History Charts (P2)**
   - Time-series chart showing price trends
   - Requires historical data collection

3. **Advanced Filtering (P2)**
   - Boolean filter logic (AND/OR)
   - Saved filter presets
   - Filter templates (e.g., "Gaming CPUs", "Budget CPUs")

4. **Similar CPUs Suggestions (P2)**
   - "CPUs you might also like" section
   - Based on specs, price range, performance tier

5. **Export/Share Features (P3)**
   - Export CPU comparison to PDF
   - Share CPU detail link with preview
   - Email CPU alerts (price drops)

**Bug Fixes and Polish:**
- Address all P1/P2 bugs from user feedback
- Optimize slow queries identified in production
- Improve mobile UX based on heatmap data
- Enhance tooltips/help text based on support tickets

---

### 12.4 Technical Debt Tracking

**Known Debt Items:**
1. **Percentile Calculation Optimization**
   - Current: Database query per CPU
   - Future: Batch calculation, cache in Redis
   - Impact: Nightly task performance

2. **Client-Side Filtering Limits**
   - Current: Filter 500 CPUs client-side
   - Future: Server-side filtering with pagination
   - Impact: Scalability for 1000+ CPUs

3. **Mock Data Dependencies**
   - Some tests use hardcoded mock data
   - Future: Factory functions, Faker library
   - Impact: Test maintainability

4. **Accessibility Gaps**
   - Some minor ARIA improvements needed
   - Future: Full WCAG AAA compliance
   - Impact: Broader user accessibility

**Debt Prioritization:**
- High: Items blocking new features
- Medium: Items causing maintenance burden
- Low: Nice-to-haves for future refactor

**Tracking:**
- Create GitHub issues with `tech-debt` label
- Estimate effort for each item
- Allocate 20% of sprint capacity to debt paydown

---

## 13. Appendix

### 13.1 Glossary

**CPU Analytics:** Computed metrics for a CPU including price targets and performance value.

**Price Targets:** Statistical price ranges (Great/Good/Fair) derived from listing data using mean ± standard deviation.

**Performance Value:** Efficiency metric calculated as $/PassMark (lower is better), with percentile ranking.

**Confidence Level:** Indicator of price target reliability based on sample size (high: 10+ listings, medium: 5-9, low: 2-4, insufficient: <2).

**PassMark Scores:** Benchmark scores from PassMark Software for CPU performance (single-thread and multi-thread).

**Percentile Rank:** Position of a CPU's $/PassMark value relative to all CPUs (0-100, lower percentile = better value).

**Adjusted Price:** Listing price after deductions for components (RAM, storage, OS) using valuation rules.

**Catalog View:** Interactive view mode (Grid, List, or Master-Detail) for browsing CPUs.

**Data View:** Tabular view with sortable columns and pagination for CPUs.

---

### 13.2 Reference Links

**Internal Documentation:**
- [CLAUDE.md](/mnt/containers/deal-brain/CLAUDE.md) - Project overview and commands
- [PRD](/mnt/containers/deal-brain/docs/project_plans/cpu-page-reskin/PRD.md) - CPU Catalog PRD

**External Resources:**
- [React Query Docs](https://tanstack.com/query/latest/docs/react/overview)
- [Zustand Docs](https://zustand-demo.pmnd.rs/)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

**Design References:**
- Listings page: `/apps/web/app/listings/page.tsx`
- Catalog store pattern: `/apps/web/stores/catalog-store.ts`
- API catalog pattern: `/apps/api/dealbrain_api/api/catalog.py`

---

### 13.3 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-15 | Claude (Documentation Agent) | Initial implementation plan created from PRD |

---

**END OF IMPLEMENTATION PLAN**

---

## Quick Start for Developers

**Sprint 1 (Backend):**
1. Start with DB-001: Create migration script
2. Run migration on staging: `poetry run alembic upgrade head`
3. Implement BE-002: CPU analytics service
4. Implement BE-003, BE-004, BE-005: API endpoints
5. Test with Postman/curl, verify response schemas

**Sprint 2 (Frontend):**
1. Create FE-001: CPU catalog store
2. Create FE-002: Main page component
3. Implement FE-006: CPU card component
4. Implement FE-007, FE-008: Badge and price components
5. Implement FE-005: Grid view (bringing it all together)

**Sprint 3 (Polish):**
1. Implement remaining view modes (list, master-detail)
2. Add tests (TEST-001, TEST-002, TEST-003)
3. Accessibility audit and fixes
4. Performance optimization
5. Documentation updates

**Questions?** Refer to PRD Section 12.1 or reach out to project lead.
