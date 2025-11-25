# PRD: Listing Valuation & Management Enhancements

## Executive Summary

This PRD addresses three critical gaps in the Deal Brain listings experience:

1. **Valuation Calculation Fix** – Adjusted performance metrics are computed incorrectly using adjusted prices instead of adjusted deltas, making CPU-specific valuations inaccurate.
2. **Delete Functionality** – No way to remove listings from the system permanently.
3. **Import Accessibility** – Import functionality only accessible from dedicated `/import` page, not integrated into catalog view.

These enhancements improve data accuracy, user control, and workflow efficiency.

## Problem Statements

### PS1: Incorrect Adjusted Performance Metrics

**Current Behavior:**
Adjusted metrics (`dollar_per_cpu_mark_single_adjusted`, `dollar_per_cpu_mark_multi_adjusted`) incorrectly divide the adjusted listing price by CPU marks. This inflates CPU valuations when other components are downgraded.

**Example:**
- PC with $500 base price, $100 RAM deduction = $400 adjusted price
- Current calculation: $400 / CPU mark (wrong – assumes entire $400 is CPU value)
- Correct calculation: ($500 - $100) / CPU mark = $400 / CPU mark (CPU-specific delta only)

**Impact:**
- Users cannot accurately compare CPU value across listings
- Valuation breakdowns mislead users about CPU contribution to deal quality
- Metrics API returns unreliable data for analysis

### PS2: No Listing Deletion

**Current Behavior:**
Listings are immutable; once imported or created, they cannot be removed. Users must contact admin or manually truncate database.

**Impact:**
- Duplicate imports pollute catalog
- Accidental listings cannot be cleaned up
- No self-service data governance

### PS3: Import Located Outside Catalog View

**Current Behavior:**
Import functionality only accessible via `/import` page separate from `/listings` catalog. Users must navigate away from catalog to import new listings.

**Impact:**
- Workflow friction – users cannot import while browsing catalog
- Discovery issue – new users may not find import feature
- Catalog view feels incomplete without data entry affordance

## Goals & Success Metrics

### Goals
- Deliver accurate CPU-specific adjusted valuations reflecting delta-based calculations
- Empower users with self-service listing deletion capability
- Streamline import workflow by integrating into catalog view

### Success Metrics
- All adjusted metrics calculations pass test suite validating delta-based formulas (100%)
- Delete functionality handles referential integrity cleanly (100% deletion success)
- Import button present and functional in `/listings` catalog view
- No support escalations regarding valuation metric accuracy within 30 days of launch

## User Stories

### US1: Accurate Valuation Comparison
**As a** deal hunter
**I want to** compare CPU value across listings without component downgrades inflating metrics
**So that** I identify best-value processors regardless of RAM or storage condition

### US2: Self-Service Data Cleanup
**As a** catalog manager
**I want to** delete duplicate or unwanted listings from the UI
**So that** I maintain data quality without admin intervention

### US3: Seamless Import Workflow
**As a** power user
**I want to** import listings without leaving the catalog view
**So that** I can browse existing deals and add new ones in one workflow

## Functional Requirements

### FR1 – Adjusted Delta Metrics Calculation
1. Calculate `dollar_per_cpu_mark_single_adjusted` using: `(base_price - adjustment_delta) / cpu_mark_single`
2. Calculate `dollar_per_cpu_mark_multi_adjusted` using: `(base_price - adjustment_delta) / cpu_mark_multi`
3. Adjustment delta = total of all component downward adjustments from valuation rules (RAM condition, storage, etc.)
4. Recalculate metrics whenever base price, CPU benchmarks, or active valuation rules change
5. Audit all code referencing adjusted metrics to ensure each use case applies correct formula (delta vs. price)

### FR2 – Listing Deletion
1. Add "Delete" button in listing detail modal (bottom action bar, near "View Full Page")
2. Add "Delete" button in listing detail page (top right near metadata)
3. Show confirmation dialog: "Permanently delete this listing? This action cannot be undone."
4. On confirmation, delete from database completely, including related components, scores, and field values
5. Cascade deletion respects referential integrity; handles edge cases gracefully
6. Return to catalog after successful deletion

### FR3 – Import Button in Catalog
1. Add "Import" button next to "Add Listing" button in `/listings` top right corner
2. Clicking opens modal with import interface (URL form and file upload – same as `/import` page)
3. Supports URL-based imports (single/bulk) and file-based imports (.xlsx)
4. After successful import, close modal and refresh catalog view to show new listings
5. Maintain import history and status feedback (success/errors)

## Technical Approach (High-Level)

### Valuation Calculation Fix
- Modify `calculate_cpu_performance_metrics()` in `apps/api/dealbrain_api/services/listings.py` to compute adjustment delta
- Track which adjustments are "component downgrades" vs. "component upgrades" in valuation breakdown JSON
- Add unit tests validating delta-based formulas for all metric types
- Audit all dependent code (dashboards, exports, API responses) to confirm correct application

### Delete Functionality
- Add `DELETE /api/v1/listings/{id}` endpoint with proper auth checks
- Create `delete_listing()` service method handling cascade deletions
- Add delete handlers to listing detail modal and page components
- Implement confirmation dialog with proper accessibility (focus trap, keyboard support)
- Add audit logging for deleted listings

### Import in Catalog
- Extract import form logic from `/import` page into reusable modal component
- Add import modal to listings page layout
- Add "Import" button triggering modal open
- Reuse existing import service and validation logic
- Add refresh logic to reload catalog after successful import

## Out of Scope

- Soft delete (archival) vs. hard delete semantics – out of scope for V1
- Bulk deletion operations
- Import scheduling or automation
- Undo functionality for deleted listings
- Advanced valuation rule semantics beyond delta calculation

## Open Questions

1. Should adjustment deltas include upward adjustments or only downward? (Assumption: downward only)
2. Should deleted listings be archived for audit purposes, or completely removed? (Assumption: completely removed)
3. Should import modal restrict file types or allow any format? (Assumption: follow existing `/import` restrictions)
4. Does delete require admin approval or is user-initiated sufficient? (Assumption: user-initiated, with confirmation)
5. Should listing deletion emit events for analytics or logging? (Assumption: yes, audit log)

## Launch Checklist

- [ ] Valuation delta calculation implemented and unit tested
- [ ] All code using adjusted metrics reviewed and corrected
- [ ] Delete endpoint implemented with cascade logic
- [ ] Delete UI added to detail modal and page
- [ ] Confirmation dialog accessibility tested
- [ ] Import modal extracted and integrated into catalog
- [ ] E2E tests cover all three features
- [ ] Database migration (if needed) tested in staging
- [ ] User documentation updated
