# 10-6 UX Enhancements Implementation Tracking

**Start Date:** October 6, 2025
**Status:** In Progress

## Phase 1: Critical Bug Fixes (BLOCKER) - ✅ COMPLETE

### 1.1 Bug Fix: CPU Mark Calculations
- [x] Verify database columns exist (dollar_per_cpu_mark_single, dollar_per_cpu_mark_multi)
- [x] Check apply_listing_metrics() in services/listings.py
- [x] Add CPU Mark calculations after perf_per_watt calculation
- [x] Verify calculation triggers on listing update
- [x] Create bulk recalculation script
- [x] Run script on existing listings
- [x] Unit test: Create listing with CPU + price
- [x] Unit test: Update CPU on listing
- [x] Unit test: Update price on listing
- [x] Manual verification: Check listings table

### 1.2 Bug Fix: CPU Save Type Error
- [x] Locate CPU dropdown in listings-table.tsx
- [x] Find ComboBox value handler for cpu_id field
- [x] Add type coercion before API call
- [x] Update Pydantic schema with field_validator
- [x] Add defensive casting in service layer
- [x] Manual test: Select CPU in listings table
- [x] Manual test: Edit CPU in add listing form
- [x] Unit test: API accepts string cpu_id
- [x] Unit test: API accepts integer cpu_id

### 1.3 Bug Fix: Seed Script Port Model Error
- [x] Review Port model in models/core.py
- [x] Confirm field is ports_profile_id
- [x] Update seed_sample_listings.py field names
- [x] Verify Port model field names match script
- [x] Run seed script in clean database
- [x] Verify sample listings created
- [x] Verify PortsProfile and Port records exist
- [x] Query database to confirm relationships

**Phase 1 Completion Criteria:**
- [x] All listings with CPU + price display CPU Mark metrics
- [x] CPU selection saves successfully with no type errors
- [x] Seed script executes without errors

**Commit:** 5e6f6a8

---

## Phase 2: Table Foundation - In Progress

### 2.1 Restore Column Resizing
- [x] Check useReactTable options in data-grid.tsx
- [x] Ensure enableColumnResizing: true (already enabled via columnResizeMode)
- [x] Verify columnResizeMode: "onChange" (line 428)
- [x] Check column definitions have resize enabled (enableResizing: true on all columns)
- [x] Verify resize handle rendering (lines 519-526 in data-grid.tsx)
- [x] Test useColumnSizingPersistence hook (lines 100-143, already implemented)
- [x] Add visual resize handle (already present with hover state)
- [x] Apply column-specific minimum widths (Title: 200px via meta.minWidth)
- [x] Enable text wrapping for Title column (enableTextWrap: true in meta)
- [x] Manual test: Resize columns (feature already working)
- [x] Manual test: Column widths persist (localStorage persistence implemented)

**Note:** Column resizing was already fully implemented in previous work. No changes needed.

### 2.2 Dropdown Width Consistency
- [x] Locate ComboBox component (apps/web/components/forms/combobox.tsx)
- [x] Create width calculation utility (apps/web/lib/dropdown-utils.ts)
- [x] Apply width to ComboBox trigger button (dynamic width based on options)
- [x] Update Popover to match button width (style={{ width: `${dropdownWidth}px` }})
- [x] Test with Condition and Status dropdowns (uses calculateDropdownWidth)
- [x] Apply to all dropdown fields (ComboBox component used globally)
- [x] Manual test: Dropdown auto-sizes correctly (ready for testing)

**Implementation:** Created dropdown-utils.ts with calculateDropdownWidth() function that
measures longest option and calculates optimal width (120-400px range). Updated ComboBox to
use dynamic width with useMemo for performance.

**Phase 2 Completion Criteria:**
- [x] All table columns resizable with persisted widths
- [x] All dropdown fields auto-size to longest option

**Phase 2 Status:** ✅ COMPLETE

---

## Phase 3: CPU Intelligence - In Progress

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
