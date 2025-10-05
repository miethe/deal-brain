# Performance Metrics & Data Enrichment - Implementation Tracking

**Started:** October 5, 2025
**PRD:** docs/project_plans/requests/prd-10-5-performance-metrics.md
**Implementation Plan:** docs/project_plans/requests/implementation-plan-10-5.md

## Phase 1: Database Schema & Migrations

### Tasks
- [x] 1.1 Create migration for listing performance metrics (0012)
  - [x] Add dollar_per_cpu_mark_single column
  - [x] Add dollar_per_cpu_mark_single_adjusted column
  - [x] Add dollar_per_cpu_mark_multi column
  - [x] Add dollar_per_cpu_mark_multi_adjusted column
  - [x] Create indexes for filtering/sorting
  - [x] Test migration up/down (upgrade successful, confirmed at 0013)
- [x] 1.2 Create migration for listing metadata fields (0013)
  - [x] Add manufacturer column
  - [x] Add series column
  - [x] Add model_number column
  - [x] Add form_factor column
  - [x] Create indexes for filtering
  - [x] Test migration up/down (upgrade successful)
- [x] 1.3 Update SQLAlchemy Models
  - [x] Add performance metric fields to Listing model
  - [x] Add metadata fields to Listing model
  - [x] Verify model/migration alignment (models match migrations)
  - [x] Run alembic check (alembic current shows 0013 head)

**Status:** ✅ Complete

**Notes:**
- Created migrations manually (0012 and 0013) following existing pattern
- All 4 performance metric fields added with indexes
- All 4 metadata fields added with indexes on manufacturer and form_factor
- Migrations applied successfully
- SQLAlchemy models updated to match database schema

---

## Phase 2: Backend Calculation Services

### Tasks
- [ ] 2.1 Implement CPU Performance Calculation Service
  - [ ] Create calculate_cpu_performance_metrics function
  - [ ] Create update_listing_metrics function
  - [ ] Create bulk_update_listing_metrics function
  - [ ] Add unit tests
  - [ ] Test edge cases (null CPU, zero marks, null adjusted price)
- [ ] 2.2 Implement Ports Management Service
  - [ ] Create get_or_create_ports_profile function
  - [ ] Create update_listing_ports function
  - [ ] Create get_listing_ports function
  - [ ] Add unit tests
  - [ ] Test cascade delete
- [ ] 2.3 Create API Endpoints
  - [ ] POST /v1/listings/{id}/recalculate-metrics
  - [ ] POST /v1/listings/bulk-recalculate-metrics
  - [ ] POST /v1/listings/{id}/ports
  - [ ] GET /v1/listings/{id}/ports
  - [ ] Update ListingResponse schema
  - [ ] Update CpuResponse schema
  - [ ] Add integration tests

**Status:** Not Started

---

## Phase 3: Frontend Core Components

### Tasks
- [ ] 3.1 Create DualMetricCell Component
  - [ ] Implement component with raw/adjusted display
  - [ ] Add percentage improvement indicator
  - [ ] Add color coding (green/red/gray)
  - [ ] Add memoization
  - [ ] Handle null/undefined gracefully
- [ ] 3.2 Create CPUInfoPanel Component
  - [ ] Display CPU name and benchmarks
  - [ ] Show TDP and release year
  - [ ] Display iGPU info
  - [ ] Responsive grid layout
  - [ ] Handle null values
- [ ] 3.3 Create PortsBuilder Component
  - [ ] Implement add/remove port entries
  - [ ] Port type dropdown (9 options)
  - [ ] Quantity input with validation
  - [ ] Create PortsDisplay for table view
  - [ ] Add popover for full details
- [ ] 3.4 Create ValuationModeToggle Component
  - [ ] Base/Adjusted mode toggle
  - [ ] Icons and ARIA labels
  - [ ] localStorage persistence
  - [ ] Smooth animations

**Status:** Not Started

---

## Phase 4: Listings Table Integration

### Tasks
- [ ] 4.1 Add Dual CPU Mark Columns
  - [ ] Add dollar_per_cpu_mark_single column
  - [ ] Add dollar_per_cpu_mark_multi column
  - [ ] Integrate DualMetricCell
  - [ ] Add column tooltips
  - [ ] Enable sorting and filtering
  - [ ] Update ListingRow interface
- [ ] 4.2 Add Product Metadata Columns
  - [ ] Add manufacturer column with multi-select filter
  - [ ] Add form_factor column with multi-select filter
  - [ ] Add ports column with compact display
  - [ ] Handle null values
  - [ ] Enable inline editing
- [ ] 4.3 Integrate Valuation Mode Toggle
  - [ ] Add toggle to table header
  - [ ] Wire to table state
  - [ ] Update Valuation column behavior
  - [ ] Update description based on mode
  - [ ] Performance metrics use correct price

**Status:** Not Started

---

## Progress Summary

- **Phase 1:** 0/13 tasks complete
- **Phase 2:** 0/16 tasks complete
- **Phase 3:** 0/14 tasks complete
- **Phase 4:** 0/11 tasks complete
- **Overall:** 0/54 tasks complete (0%)

---

## Notes

- CPU model already has required fields (cpu_mark_single, cpu_mark_multi, igpu_mark, tdp_w, release_year, igpu_model)
- No CPU migration needed
- Ports infrastructure already exists (PortsProfile, Port tables)
- Valuation rules system already functional
