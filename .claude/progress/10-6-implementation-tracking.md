# 10-6 UX Enhancements Implementation Tracking

**Start Date:** October 6, 2025
**Status:** In Progress

## Phase 1: Critical Bug Fixes (BLOCKER) - In Progress

### 1.1 Bug Fix: CPU Mark Calculations
- [ ] Verify database columns exist (dollar_per_cpu_mark_single, dollar_per_cpu_mark_multi)
- [ ] Check apply_listing_metrics() in services/listings.py
- [ ] Add CPU Mark calculations after perf_per_watt calculation
- [ ] Verify calculation triggers on listing update
- [ ] Create bulk recalculation script
- [ ] Run script on existing listings
- [ ] Unit test: Create listing with CPU + price
- [ ] Unit test: Update CPU on listing
- [ ] Unit test: Update price on listing
- [ ] Manual verification: Check listings table

### 1.2 Bug Fix: CPU Save Type Error
- [ ] Locate CPU dropdown in listings-table.tsx
- [ ] Find ComboBox value handler for cpu_id field
- [ ] Add type coercion before API call
- [ ] Update Pydantic schema with field_validator
- [ ] Add defensive casting in service layer
- [ ] Manual test: Select CPU in listings table
- [ ] Manual test: Edit CPU in add listing form
- [ ] Unit test: API accepts string cpu_id
- [ ] Unit test: API accepts integer cpu_id

### 1.3 Bug Fix: Seed Script Port Model Error
- [ ] Review Port model in models/core.py
- [ ] Confirm field is ports_profile_id
- [ ] Update seed_sample_listings.py field names
- [ ] Verify Port model field names match script
- [ ] Run seed script in clean database
- [ ] Verify sample listings created
- [ ] Verify PortsProfile and Port records exist
- [ ] Query database to confirm relationships

**Phase 1 Completion Criteria:**
- [ ] All listings with CPU + price display CPU Mark metrics
- [ ] CPU selection saves successfully with no type errors
- [ ] Seed script executes without errors

---

## Phase 2: Table Foundation - Pending

### 2.1 Restore Column Resizing
- [ ] Check useReactTable options in data-grid.tsx
- [ ] Ensure enableColumnResizing: true
- [ ] Verify columnResizeMode: "onChange"
- [ ] Check column definitions have resize enabled
- [ ] Verify resize handle rendering
- [ ] Test useColumnSizingPersistence hook
- [ ] Add visual resize handle
- [ ] Apply column-specific minimum widths
- [ ] Enable text wrapping for Title column
- [ ] Manual test: Resize columns
- [ ] Manual test: Column widths persist

### 2.2 Dropdown Width Consistency
- [ ] Locate ComboBox component
- [ ] Create width calculation utility
- [ ] Apply width to ComboBox trigger button
- [ ] Update Popover to match button width
- [ ] Test with Condition and Status dropdowns
- [ ] Apply to all dropdown fields
- [ ] Manual test: Dropdown auto-sizes correctly

**Phase 2 Completion Criteria:**
- [ ] All table columns resizable with persisted widths
- [ ] All dropdown fields auto-size to longest option

---

## Phase 3: CPU Intelligence - Pending

### 3.1 CPU Data API Integration
- [ ] Verify listings API includes full CPU object
- [ ] Check GET /v1/listings endpoint
- [ ] Ensure CPU relationship uses selectin loading
- [ ] Update ListingRow interface
- [ ] Verify API response includes CPU data
- [ ] Add CPU to API response schema if missing

### 3.2 CPU Tooltip Component
- [ ] Create cpu-tooltip.tsx component
- [ ] Integrate into CPU column in listings-table.tsx
- [ ] Add React.memo for performance
- [ ] Manual test: Hover over Info icon
- [ ] Manual test: Click "View Full Details"
- [ ] Accessibility test: Tab to Info icon
- [ ] Accessibility test: Screen reader announces

### 3.3 CPU Details Modal
- [ ] Create cpu-details-modal.tsx component
- [ ] Integrate into listings-table.tsx
- [ ] Add state management for modal
- [ ] Manual test: Modal opens with CPU data
- [ ] Manual test: ESC key closes modal
- [ ] Manual test: Click outside modal
- [ ] Accessibility test: Focus trapped in modal
- [ ] Accessibility test: Focus returns to trigger

**Phase 3 Completion Criteria:**
- [ ] Listings API returns full CPU data
- [ ] CPU tooltip displays key specs
- [ ] CPU modal displays all specification fields

---

## Summary Statistics

**Total Tasks:** 48
**Completed:** 0
**In Progress:** 0
**Pending:** 48

**Current Phase:** Phase 1
**Overall Progress:** 0%
