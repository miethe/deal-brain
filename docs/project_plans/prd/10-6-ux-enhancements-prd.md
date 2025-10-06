# Product Requirements Document: 10-6 UX Enhancements & Bug Fixes

**Version:** 1.0
**Date:** October 6, 2025
**Status:** Draft
**Author:** Lead Architect

---

## 1. Executive Summary

### 1.1 Overview

This PRD defines the requirements for a comprehensive set of UX enhancements and critical bug fixes to improve the Deal Brain application's usability, discoverability, and data integrity. The enhancements focus on making CPU information more accessible, streamlining data entry workflows, and fixing calculation and persistence bugs that affect core functionality.

### 1.2 Goals

**Primary Goals:**
1. **Enhanced CPU Discoverability:** Make CPU specifications immediately accessible within the Listings table without requiring navigation away from the current view
2. **Streamlined Data Entry:** Improve dropdown field consistency and introduce custom modals for inline option creation
3. **Improved Table UX:** Restore column resizing functionality and ensure dropdown field usability
4. **Consistent Modal Patterns:** Standardize the Add Entry experience across the application with expandable modal patterns
5. **Dashboard Interactivity:** Make dashboard listings clickable with overview modals
6. **Data Integrity:** Fix critical bugs affecting CPU Mark calculations, CPU persistence, and seed data generation

**Secondary Goals:**
- Maintain WCAG AA accessibility compliance across all new components
- Ensure consistent visual design language aligned with existing patterns
- Preserve performance optimizations (memoization, debouncing) in enhanced components

### 1.3 Success Metrics

**Quantitative Metrics:**
- CPU tooltip hover interaction rate > 60% for users viewing listings with CPUs
- CPU modal open rate > 30% from tooltip clicks
- Inline dropdown option creation usage > 20% when adding new listings
- Zero calculation errors for $/CPU Mark fields after fix deployment
- 100% success rate for CPU save operations after bug fix

**Qualitative Metrics:**
- Users can discover full CPU specs without leaving the Listings table
- Dropdown fields are consistently readable across all table views
- Modal experiences feel cohesive and follow established patterns
- Dashboard provides quick access to listing details without full page navigation

### 1.4 Scope

**In Scope:**
- CPU tooltip and full details modal for Listings table
- Secondary Storage dropdown matching Primary Storage pattern
- Custom modal for inline dropdown option creation (replacing browser dialog)
- Dropdown field width consistency fixes
- Column resizing restoration in all tables
- Enhanced Add Entry modal with expandable pattern for Listings
- Clickable dashboard listings with overview modals
- Bug fixes: CPU Mark calculations, CPU save error, seed script error

**Out of Scope:**
- GPU tooltip/modal (future enhancement)
- Bulk CPU data import UI (covered by existing import pipeline)
- Advanced CPU comparison features
- Custom field creation from dashboard modals
- Migration of existing listings (no users in production)

---

## 2. Feature Requirements

### 2.1 Listings Enhancements

#### 2.1.1 CPU Tooltip in Listings Table

**User Story:**
As a Deal Brain user, I want to see key CPU specifications when hovering over a CPU in the Listings table, so that I can quickly assess hardware capabilities without leaving my current view.

**Acceptance Criteria:**
1. **Visual Indicator:** When a listing has a CPU assigned, an info icon appears adjacent to the CPU name in the CPU column
2. **Tooltip Trigger:** Hovering over the info icon displays a tooltip popover containing:
   - CPU name (header)
   - PassMark Single-Thread Score (labeled, formatted number)
   - PassMark Multi-Thread Score (labeled, formatted number)
   - Integrated Graphics: Yes/No indicator
   - iGPU Model: Display model name if iGPU present, otherwise "N/A"
   - iGPU Mark: Display score if iGPU present and score available, otherwise "N/A"
   - TDP: Display wattage with "W" suffix if available, otherwise "N/A"
   - Release Year: Display year if available, otherwise "N/A"
3. **Accessibility:**
   - Info icon has ARIA label "View CPU details"
   - Tooltip content is accessible to screen readers
   - Keyboard accessible via Tab navigation + Enter to show tooltip
4. **Performance:** CPU data fetched with listing data (no separate API call per tooltip hover)
5. **Visual Design:**
   - Tooltip uses existing shadcn/ui Popover component
   - Info icon uses consistent sizing (h-4 w-4) and muted color
   - Tooltip content uses clear label/value pairs with proper spacing
   - "View Full CPU Details" button prominently placed at bottom of tooltip

**UI/UX Specifications:**
- **Tooltip Positioning:** Auto-positioned by Radix UI (prefer top/bottom based on viewport)
- **Tooltip Dimensions:** Min width 280px, max width 360px, auto height
- **Typography:**
  - Header (CPU name): text-sm font-semibold
  - Labels: text-xs font-medium text-muted-foreground
  - Values: text-sm
- **Spacing:** py-3 px-4 with 8px gap between rows
- **Z-index:** Layered above table content (z-50)

**Technical Considerations:**
- Extend `ListingRow` interface to include full CPU object with all fields
- Modify listings API response to include nested CPU data via `selectin` loading
- Create `CpuTooltip` component accepting CPU object as prop
- Use React.memo for tooltip component to prevent unnecessary re-renders
- Tooltip content should not cause table row height changes (absolutely positioned)

---

#### 2.1.2 Full CPU Details Modal

**User Story:**
As a Deal Brain user, I want to view complete CPU specifications in a dedicated modal, so that I can review all technical details without navigating away from my current workflow.

**Acceptance Criteria:**
1. **Modal Trigger:** Clicking "View Full CPU Details" button in CPU tooltip opens the modal
2. **Modal Content:** Displays all CPU table fields:
   - **Header Section:** CPU name (large, prominent)
   - **Core Specifications:** Manufacturer, Socket, Cores, Threads
   - **Performance Metrics:** CPU Mark (Multi), CPU Mark (Single), iGPU Mark
   - **Power & Thermal:** TDP (W), Release Year
   - **Graphics:** iGPU Model (if present)
   - **Additional:** Notes field (if present), Attributes JSON (if present, formatted)
   - **Metadata:** Created At, Updated At (formatted timestamps)
3. **Data Handling:**
   - All fields display "N/A" or "—" for null values
   - Numbers formatted with thousands separators where appropriate
   - TDP displays with "W" suffix
   - Dates formatted as "MMM DD, YYYY at HH:MM AM/PM"
4. **Modal Actions:**
   - "Close" button in header
   - "View All CPUs" button linking to /catalog/cpus (if catalog page exists)
   - ESC key closes modal
   - Click outside modal closes (with optional confirmation if future edit mode added)
5. **Accessibility:**
   - Focus trapped within modal when open
   - Focus returns to trigger button on close
   - All fields have clear labels for screen readers

**UI/UX Specifications:**
- **Modal Size:** max-w-2xl (768px)
- **Layout:** Two-column grid for specification pairs on desktop, single column on mobile
- **Visual Hierarchy:**
  - H2 for CPU name
  - H4 for section headers (Core Specs, Performance, etc.)
  - Grid layout with label/value pairs
- **Sections with Separators:** Use Separator component between major sections
- **Button Placement:** Footer with centered buttons, primary "Close" on right

**Technical Considerations:**
- Create `CpuDetailsModal` component in `apps/web/components/listings/`
- Use existing Dialog/Modal components from shadcn/ui
- Accept `cpu: CpuResponse | null` and `open: boolean` props
- Use existing `getCpu` API function from `apps/web/lib/api/listings.ts`
- If CPU data not already in listing response, fetch on modal open
- Component should handle loading and error states gracefully

---

#### 2.1.3 Secondary Storage Dropdown

**User Story:**
As a Deal Brain user, I want to select Secondary Storage capacity from a predefined dropdown (like Primary Storage), so that I can quickly enter common values without typing.

**Acceptance Criteria:**
1. **Field Conversion:** Secondary Storage (GB) field changes from freeform number input to dropdown
2. **Dropdown Options:** Matches Primary Storage dropdown exactly:
   - 128, 256, 512, 1024, 2048, 4096 (GB)
3. **Inline Creation:** Support "Create new option" for custom values via inline creation modal (see 2.1.4)
4. **Field Behavior:**
   - Stored as number in database (existing schema unchanged)
   - Display formatted with "GB" suffix in table cells
   - ComboBox component with search/filter
5. **Integration:** Works in both:
   - Listings table inline editing
   - Add Listing form
6. **Backward Compatibility:** Existing listings with custom values display correctly

**UI/UX Specifications:**
- **Dropdown Width:** Auto-sized to fit longest option + padding (not constrained by column width)
- **Option Display:** "128 GB", "256 GB", etc. (number + suffix)
- **Search:** User can type to filter options (e.g., "512" filters to 512 GB)
- **Empty State:** If no CPU selected, dropdown shows all options; if CPU selected, options remain same (no filtering)

**Technical Considerations:**
- Add `'secondary_storage_gb'` to `DROPDOWN_FIELD_CONFIGS` constant in `listings-table.tsx`
- Use existing ComboBox component infrastructure
- No database migration required (field already exists as number)
- Update `add-listing-form.tsx` to use dropdown instead of number input
- Ensure saved values trigger metric recalculation if applicable

---

#### 2.1.4 Custom Modal for Inline Dropdown Option Creation

**User Story:**
As a Deal Brain user, I want to add new dropdown options through a custom in-app modal instead of a browser dialog, so that I have a consistent, professional experience that matches the rest of the application.

**Acceptance Criteria:**
1. **Modal Trigger:** Clicking "Create new option" (or similar CTA) in any dropdown field opens the custom modal
2. **Modal Content:**
   - **Title:** "Add New [Field Name] Option" (dynamically set)
   - **Input Field:** Single text input for new option value
   - **Validation:** Client-side validation for:
     - Required field (non-empty)
     - No duplicate options (check against existing options)
     - Appropriate format based on field type (e.g., number-only for numeric fields)
   - **Confirmation Message:** "This will add the option globally for all listings"
3. **Modal Actions:**
   - **Cancel Button:** Closes modal without action
   - **Add Option Button:** Saves new option and closes modal
   - Submit on Enter key press when focused on input
4. **Post-Save Behavior:**
   - New option immediately available in dropdown without page refresh
   - New option auto-selected in the field that triggered creation
   - Success toast notification: "Option added successfully"
   - Listing refetch triggered to show updated options
5. **Error Handling:**
   - API errors displayed in modal (below input field)
   - Network errors show toast notification
   - Modal remains open on error for user to retry

**UI/UX Specifications:**
- **Modal Size:** max-w-md (448px)
- **Layout:**
  - Header with title and close button
  - Content area with label, input, helper text
  - Footer with Cancel (left) and Add (right, primary) buttons
- **Helper Text:** "This option will be available for all listings in the [Field Name] field"
- **Focus Management:** Auto-focus input field on modal open
- **Loading State:** Add button shows spinner and disables during save

**Technical Considerations:**
- Create `InlineOptionCreationModal` component in `apps/web/components/forms/`
- Props: `open`, `onOpenChange`, `fieldId`, `fieldName`, `fieldType`, `onSuccess`
- Use existing `POST /v1/reference/custom-fields/{field_id}/options` endpoint
- Integrate with ComboBox component's inline creation flow
- Replace browser `prompt()` calls with modal
- Use React Hook Form for input validation
- Trigger `useQueryClient.invalidateQueries` for field options on success

---

### 2.2 Table UX Improvements

#### 2.2.1 Dropdown Width Consistency

**User Story:**
As a Deal Brain user, I want dropdown fields to be readable without clicking them, so that I can quickly scan and compare values across rows.

**Acceptance Criteria:**
1. **Width Calculation:** Dropdown field width determined by:
   - Width of longest option in dropdown
   - Plus 40px padding (20px each side)
   - Plus 24px for dropdown chevron icon
   - Minimum width: 120px
2. **Affected Fields:** All dropdown/enum fields in all tables:
   - Listings: Condition, Status, Storage Type, RAM (GB), Primary Storage (GB), Secondary Storage (GB)
   - Global Fields: Data Type, Entity Type
   - Valuation Rules: Component Type, Metric Type
3. **Unconstrained by Column:** Dropdown should overflow column width if necessary (not truncate)
4. **Visual Consistency:** All dropdowns use same styling approach across application
5. **Responsive Behavior:** On mobile, dropdown max-width: 90vw to prevent overflow

**UI/UX Specifications:**
- **Dropdown Button:**
  - Width: auto (calculated as above)
  - Min-width: 120px
  - Max-width: 400px (prevent extremely wide dropdowns)
  - Padding: px-3 py-2
  - Font: text-sm
- **Popover Width:** Match button width or auto-size to content, whichever is wider
- **Z-index:** Ensure dropdown popover appears above table cells (z-50)

**Technical Considerations:**
- Update ComboBox component to calculate width based on options prop
- Create utility function `calculateDropdownWidth(options: string[]): number`
- Apply width via inline style or dynamic className
- Ensure width calculation happens after options load (handle async options)
- For numeric fields (RAM, Storage), format display values for width calculation ("128 GB" not "128")

---

#### 2.2.2 Column Resizing Restoration

**User Story:**
As a Deal Brain user, I want to resize table columns to customize my view, so that I can focus on the information most relevant to me.

**Acceptance Criteria:**
1. **Functionality Restored:** All columns in all tables can be resized by dragging column borders
2. **Affected Tables:**
   - Listings table (primary)
   - Global Fields table
   - Valuation Rules table
   - CPUs/GPUs catalog tables (if applicable)
3. **Resize Behavior:**
   - Drag handle visible on hover between column headers
   - Cursor changes to col-resize on hover
   - Minimum column width: 60px (prevent collapse)
   - Maximum column width: 600px (prevent extreme widening)
   - Specific fields with enforced minimums:
     - Title/Name columns: 200px minimum
     - Price/Valuation columns: 120px minimum
     - Short enum fields: 100px minimum
4. **Persistence:** Column widths saved to localStorage per table
   - Key format: `dealbrain_table_columns_[tableName]_v1`
   - Persists across sessions
   - Reset option available (future enhancement)
5. **Visual Feedback:**
   - Column border highlights on hover (subtle color change)
   - Cursor indicates draggable area
   - Column width updates smoothly during drag (debounced render)

**UI/UX Specifications:**
- **Resize Handle:**
  - Width: 4px clickable area (visual width 2px)
  - Position: Absolutely positioned on right edge of header cell
  - Color: border-border (default), border-primary (hover)
  - Cursor: col-resize
- **Debouncing:** 150ms debounce on resize event to prevent excessive renders
- **Constraints:**
  - Text wrapping enabled for cells when column narrower than content
  - Horizontal scroll enabled when total width exceeds viewport

**Technical Considerations:**
- Verify TanStack Table's column resizing API is enabled in DataGrid component
- Check if `columnSizing` state is managed in useReactTable hook
- Ensure `columnResizeMode` is set to "onChange" for smooth resizing
- Add `enableColumnResizing: true` to table options
- Verify column resize handlers are not being blocked by other event listeners
- Update `data-grid.tsx` to include resize handle rendering
- Add localStorage persistence via useEffect hook watching columnSizing state
- Load persisted widths on component mount via `initialState` option

---

### 2.3 Global Fields Integration

#### 2.3.1 Add Entry Modal Expandable Behavior

**User Story:**
As a Deal Brain user, I want to add new listings through a consistent modal experience that can expand to full screen when needed, so that I have flexibility in how I interact with forms based on context.

**Acceptance Criteria:**
1. **Modal Behavior Changes:**
   - **From Data Tab (Global Fields page):** "Add entry" button opens Add Listing form in modal mode by default
   - **From /listings Page:** "Add Listing" button opens Add Listing form in modal mode by default
   - Both trigger the same underlying component with different initial states
2. **Modal Features:**
   - **Default State:** Modal overlay with Add Listing form (max-w-4xl)
   - **Expand Button:** Icon button in modal header (top-right, near close button)
   - **Expand Action:** Modal transitions to full-screen view (similar to page view)
   - **Collapse Button:** Available in full-screen mode to return to modal
3. **Form Consistency:** Same form fields, validation, and submission logic regardless of modal/expanded state
4. **Navigation Integration:**
   - After successful submission in modal mode, option to view listing (navigates to /listings with highlight)
   - In expanded mode, success can redirect or close (configurable)
5. **State Preservation:** Form data persists when toggling between modal and expanded states

**UI/UX Specifications:**
- **Modal Mode:**
  - max-w-4xl width
  - Standard modal overlay (backdrop with blur)
  - Scrollable content if form exceeds viewport
  - Close button and Expand button in header
- **Expanded Mode:**
  - Full viewport width and height
  - No backdrop (appears as page)
  - Collapse button in consistent position
  - Maintains form padding and spacing
- **Transition:** Smooth animation between modal and expanded (200ms ease-in-out)
- **Icons:**
  - Expand: Maximize icon (lucide-react)
  - Collapse: Minimize icon (lucide-react)

**Technical Considerations:**
- Create `AddListingModal` wrapper component accepting `mode: 'modal' | 'expanded'` prop
- Use existing `add-listing-form.tsx` as form content
- Implement expand/collapse via state management (useState)
- Update Data Tab "Add entry" button to trigger modal
- Update /listings "Add Listing" button to trigger modal
- Use conditional rendering for Dialog vs. full-screen container
- Ensure form submission callbacks close modal appropriately
- Consider using ModalContent component's `preventClose` prop during form submission

---

### 2.4 Dashboard Enhancements

#### 2.4.1 Clickable Dashboard Listings with Overview Modals

**User Story:**
As a Deal Brain user, I want to click on featured listings in the dashboard to see a quick overview, so that I can decide whether to investigate further without leaving the dashboard.

**Acceptance Criteria:**
1. **Clickable Listings:** All listings displayed on dashboard become clickable:
   - "Best $ / CPU Mark" listing
   - "Top Perf / Watt" listing
   - "Best Under Budget" listings (all items in list)
2. **Modal Trigger:** Clicking anywhere on a listing card/row opens overview modal
3. **Modal Content - Listing Overview:**
   - **Header:** Listing title + thumbnail (if available)
   - **Pricing Section:**
     - Base Price
     - Adjusted Price
     - Valuation badge (using existing ValuationCell styling)
   - **Performance Metrics:**
     - $/CPU Mark (Single)
     - $/CPU Mark (Multi)
     - Composite Score
   - **Hardware Summary:**
     - CPU name (clickable to CPU modal if desired, future enhancement)
     - RAM (GB)
     - Primary Storage (type + capacity)
     - Ports summary (if applicable)
   - **Metadata:**
     - Condition
     - Status
     - Manufacturer, Form Factor (if available)
4. **Modal Actions:**
   - **Primary CTA:** "View Full Listing" button navigating to `/listings?highlight={id}`
   - **Secondary CTA:** "View Valuation Breakdown" button (if valuation data exists)
   - **Close Button:** Standard modal close in header
5. **Loading State:** Show skeleton loader while fetching full listing details (if not already in dashboard data)

**UI/UX Specifications:**
- **Modal Size:** max-w-3xl (896px)
- **Layout:**
  - Left column: Thumbnail (if available, 200px width)
  - Right column: Content sections
  - Single column on mobile
- **Visual Hierarchy:**
  - H2 for listing title
  - H4 for section headers
  - Grid layout for spec pairs
- **Interactive States:**
  - Hover on dashboard listing: subtle background color change (bg-accent)
  - Cursor: pointer
  - Transition: 150ms ease-in-out
- **Thumbnail:**
  - Width: 200px, height: auto (maintain aspect ratio)
  - Rounded corners (rounded-lg)
  - Fallback: Placeholder image or icon if no thumbnail

**Technical Considerations:**
- Update `dashboard-summary.tsx` to make SummaryCard and ListingRow clickable
- Create `ListingOverviewModal` component in `apps/web/components/listings/`
- Props: `listingId: number`, `open: boolean`, `onOpenChange: (open: boolean) => void`
- Fetch full listing details via `GET /v1/listings/{id}` endpoint
- Reuse existing components where possible:
  - ValuationCell for pricing display
  - DualMetricCell for CPU Mark metrics
  - PortsDisplay for ports summary
- Pass success callback to navigate to /listings page on "View Full Listing" click
- Use React Query for data fetching with 5-minute cache

---

### 2.5 Critical Bug Fixes

#### 2.5.1 CPU Mark Metrics Calculation

**User Story:**
As a Deal Brain user, I expect the $/CPU Mark (Single) and $/CPU Mark (Multi) fields to display calculated values for all listings with CPUs and prices, so that I can accurately compare price efficiency.

**Bug Description:**
Currently, the new performance metric fields `dollar_per_cpu_mark_single` and `dollar_per_cpu_mark_multi` are empty for all listings, even those with valid CPU and price data.

**Root Cause Analysis Required:**
- Verify if metrics are calculated on listing create/update
- Check if calculation service is being called
- Verify database columns exist and are properly mapped
- Ensure listing API response includes these fields

**Acceptance Criteria:**
1. **Calculation Trigger:** Metrics automatically calculated when:
   - Listing is created with CPU and price
   - Listing CPU is updated
   - Listing price (base or adjusted) is updated
2. **Calculation Logic:**
   - `dollar_per_cpu_mark_single = adjusted_price / cpu.cpu_mark_single`
   - `dollar_per_cpu_mark_multi = adjusted_price / cpu.cpu_mark_multi`
   - If adjusted_price is null, use base_price_usd
   - If CPU marks are null, field should be null (not 0 or error)
3. **Database Persistence:** Calculated values stored in listing table
4. **API Response:** Fields included in listing list and detail responses
5. **Recalculation Script:** Ability to bulk recalculate for all existing listings

**Technical Investigation:**
- Check `apps/api/dealbrain_api/services/listings.py` for metric calculation logic
- Verify `recalculate_listing_metrics` function exists and is called
- Check if database columns are present (may need migration)
- Review `ListingResponse` schema to ensure fields are included
- Test calculation with sample data in development

**Testing Requirements:**
- Unit tests for calculation logic with various scenarios:
  - Valid CPU with both marks present
  - CPU with only single-thread mark
  - CPU with only multi-thread mark
  - Listing without CPU (should be null)
  - Listing without price (should be null)
- Integration test for automatic recalculation on update
- Regression test to ensure existing listings calculate correctly

---

#### 2.5.2 CPU Save Error Fix

**User Story:**
As a Deal Brain user, I expect to successfully save a CPU selection to a listing without encountering database errors.

**Bug Description:**
When attempting to save a CPU to a listing from the /listings page, the operation fails with a SQLAlchemy error indicating a type mismatch: string '13' cannot be interpreted as an integer for the cpu_id parameter.

**Error Log:**
```
sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error)
<class 'asyncpg.exceptions.DataError'>: invalid input for query argument $1:
'13' ('str' object cannot be interpreted as an integer)

[SQL: UPDATE listing SET cpu_id=$1::INTEGER, updated_at=now() WHERE listing.id = $2::INTEGER]
[parameters: ('13', 13)]
```

**Root Cause Analysis:**
- Frontend is sending cpu_id as string instead of number
- API endpoint is not casting/validating cpu_id type before database operation
- Pydantic schema may not be enforcing integer type

**Acceptance Criteria:**
1. **Type Safety:** cpu_id must be handled as integer throughout the stack:
   - Frontend: Send as number (not string)
   - API: Validate and cast to int in request schema
   - Service: Ensure type consistency before database operation
2. **Validation:** API should return 400 Bad Request if cpu_id is not a valid integer
3. **Error Handling:** Clear error messages if CPU ID doesn't exist (404) or is invalid (400)
4. **Backward Compatibility:** Fix should not break existing working update operations

**Technical Investigation:**
- Check `listings-table.tsx` or `add-listing-form.tsx` for CPU selection handling
- Review API endpoint handler for CPU update (likely `PATCH /v1/listings/{id}`)
- Check Pydantic schema for listing update request
- Verify database column type (should be Integer)
- Test with both direct API calls and UI interaction

**Fix Strategy:**
1. **Frontend:** Ensure ComboBox value for cpu_id is parsed to number before sending
2. **API Schema:** Add explicit `int` type validation in Pydantic model
3. **Service Layer:** Add defensive int casting in service method
4. **Testing:** Add test case for string-to-int edge case

---

#### 2.5.3 Seed Script Port Creation Error

**User Story:**
As a developer, I expect the seed_sample_listings.py script to execute successfully, so that I can populate the database with sample data for testing.

**Bug Description:**
The seed script fails when attempting to create Port objects with a TypeError indicating 'port_profile_id' is an invalid keyword argument.

**Error Log:**
```python
File "/mnt/containers/deal-brain/scripts/seed_sample_listings.py", line 169, in seed_sample_listings
  port = Port(
         ^^^^^
...
TypeError: 'port_profile_id' is an invalid keyword argument for Port
```

**Root Cause Analysis:**
- Script is using incorrect keyword argument name for Port model initialization
- Port model may have different field name or relationship structure
- Possible mismatch between script and database model definition

**Acceptance Criteria:**
1. **Script Execution:** seed_sample_listings.py runs to completion without errors
2. **Data Creation:** Script successfully creates:
   - 5 sample listings
   - Associated PortsProfile records
   - Associated Port records with correct relationships
3. **Data Integrity:** Created records have valid relationships and can be queried
4. **Documentation:** Script includes clear docstring with usage instructions

**Technical Investigation:**
- Review `apps/api/dealbrain_api/models/core.py` Port model definition
- Check if field is named `ports_profile_id` instead of `port_profile_id`
- Verify Port model's `__init__` method accepts keyword arguments
- Check if Port should be created via PortsProfile relationship instead
- Review working examples in codebase (e.g., test fixtures)

**Fix Strategy:**
1. **Identify Correct Field Name:** Match script to actual Port model definition
2. **Update Script:** Use correct keyword argument or relationship pattern
3. **Alternative Approach:** Consider creating Ports via PortsProfile.ports relationship
4. **Add Type Hints:** Improve script with proper type annotations for clarity
5. **Testing:** Run script in clean database to verify complete execution

---

## 3. Technical Architecture

### 3.1 Frontend Components

#### 3.1.1 New Components

| Component | Path | Purpose |
|-----------|------|---------|
| `CpuTooltip` | `apps/web/components/listings/` | CPU specification tooltip with hover trigger |
| `CpuDetailsModal` | `apps/web/components/listings/` | Full CPU details modal dialog |
| `InlineOptionCreationModal` | `apps/web/components/forms/` | Custom modal for adding dropdown options |
| `ListingOverviewModal` | `apps/web/components/listings/` | Quick listing overview from dashboard |
| `AddListingModal` | `apps/web/components/listings/` | Wrapper for add listing with expand/collapse |

#### 3.1.2 Modified Components

| Component | Path | Changes |
|-----------|------|---------|
| `listings-table.tsx` | `apps/web/components/listings/` | Add CPU tooltip integration, Secondary Storage dropdown, column resize restoration |
| `add-listing-form.tsx` | `apps/web/components/listings/` | Add Secondary Storage dropdown, integrate with modal wrapper |
| `combobox.tsx` | `apps/web/components/forms/` | Integrate inline creation modal, improve width calculation |
| `dashboard-summary.tsx` | `apps/web/components/dashboard/` | Make listings clickable, integrate overview modal |
| `data-grid.tsx` | `apps/web/components/ui/` | Enable column resizing, persist column widths |

### 3.2 Backend Endpoints

#### 3.2.1 Existing Endpoints (No Changes Required)

All necessary endpoints already exist:
- `GET /v1/listings` - Returns listing list with CPU data (verify includes full CPU object)
- `GET /v1/listings/{id}` - Returns single listing with full details
- `PATCH /v1/listings/{id}` - Updates listing (bug fix needed for cpu_id type handling)
- `POST /v1/reference/custom-fields/{field_id}/options` - Creates new dropdown option
- `GET /v1/catalog/cpus` - Lists all CPUs
- `GET /v1/catalog/cpus/{id}` - Returns CPU details

#### 3.2.2 Endpoint Modifications

**PATCH /v1/listings/{id}**
- **Change:** Add type validation/casting for cpu_id field
- **Schema Update:** Ensure `UpdateListingRequest` schema enforces `cpu_id: int | None`
- **Service Update:** Add defensive casting in `update_listing` service method
- **Testing:** Add test case for string cpu_id input (should cast or error gracefully)

### 3.3 Database Schema Changes

**No migrations required** - all necessary fields exist:
- `listing.cpu_id` (Integer, ForeignKey)
- `listing.secondary_storage_gb` (Integer, nullable)
- `listing.dollar_per_cpu_mark_single` (Float, nullable)
- `listing.dollar_per_cpu_mark_multi` (Float, nullable)
- `cpu.*` (All fields needed for tooltip/modal)
- `port.ports_profile_id` (Integer, ForeignKey - verify name)

**Verification Required:**
1. Confirm performance metric columns exist in listing table
2. Confirm Port model foreign key field name
3. Verify CPU fields are loaded with listing queries (selectin or joinedload)

### 3.4 Shared Logic

**No changes to `packages/core/`** - This feature set does not require new domain logic. All functionality is UI/API layer enhancements and bug fixes to existing logic.

### 3.5 Services Layer Updates

| Service | File | Changes |
|---------|------|---------|
| ListingsService | `apps/api/dealbrain_api/services/listings.py` | Fix metric calculation trigger, add cpu_id type handling |
| CustomFieldsService | `apps/api/dealbrain_api/services/custom_fields.py` | No changes (inline creation already works) |

---

## 4. User Experience Flows

### 4.1 CPU Discovery Flow

**Scenario:** User browsing listings wants to check CPU specifications

1. User lands on `/listings` page with populated listings table
2. User scans rows and notices info icon next to CPU names
3. User hovers over info icon for listing of interest
4. **Tooltip appears** with key CPU specs:
   - Single/Multi-thread scores
   - iGPU information
   - TDP and release year
5. User decides specs warrant deeper investigation
6. User clicks "View Full CPU Details" button in tooltip
7. **Modal opens** with complete CPU specifications organized by category
8. User reviews all fields, satisfied with comprehensive view
9. User clicks "Close" or ESC to dismiss modal
10. User returns to listings table at exact scroll position

**Alternative Flow:** Direct modal access (future enhancement)
- User right-clicks CPU name → "View CPU Details" context menu option

### 4.2 Dropdown Option Creation Flow

**Scenario:** User adding listing with non-standard RAM configuration

1. User clicks "Add Listing" button (opens modal)
2. User fills in basic fields (title, price, condition)
3. User reaches RAM (GB) dropdown, clicks to open
4. User types "48" to filter options
5. No existing option for 48 GB found
6. User sees "Create new option: 48" at bottom of dropdown
7. User clicks "Create new option: 48"
8. **Custom modal opens** with title "Add New RAM (GB) Option"
9. Modal shows input field pre-filled with "48"
10. Modal shows helper text: "This option will be available for all listings..."
11. User confirms value is correct
12. User clicks "Add Option" button
13. **Modal closes**, dropdown refreshes
14. 48 GB now appears in dropdown and is auto-selected
15. **Toast notification** appears: "Option added successfully"
16. User continues filling form with new option selected

**Error Flow:**
- Step 12: API error occurs (e.g., duplicate option)
- Error message appears below input: "Option already exists"
- Modal remains open, focus stays on input
- User can correct or cancel

### 4.3 Dashboard Interaction Flow

**Scenario:** User reviews dashboard and wants details on "Best Value" listing

1. User lands on dashboard (home page)
2. User sees "Best $ / CPU Mark" card with featured listing
3. Card displays: Title, Adjusted Price, $/CPU Mark, Composite Score
4. User wants more context before navigating to full listing
5. **User clicks anywhere on listing card** (entire card is clickable)
6. **Listing Overview Modal opens** showing:
   - Thumbnail and title
   - Pricing breakdown with valuation badge
   - Performance metrics (Single/Multi CPU Mark)
   - Hardware summary (CPU, RAM, Storage, Ports)
   - Condition and metadata
7. User reviews information quickly
8. User decides this listing is worth full investigation
9. User clicks "View Full Listing" button
10. **Modal closes**, navigation to `/listings?highlight={id}`
11. Listings table opens with target listing highlighted (scroll into view)

**Alternative Flow:** Valuation breakdown
- Step 8: User clicks "View Valuation Breakdown" instead
- Valuation modal stacks on top of overview modal (or replaces it)
- User reviews applied rules and adjustments
- User can return to overview or navigate to full listing

### 4.4 Column Resizing Flow

**Scenario:** User wants to widen Title column to see full listing names

1. User on `/listings` with default column widths
2. Title column shows truncated names with "..."
3. User hovers cursor between Title and next column header
4. **Cursor changes to col-resize** icon
5. **Column border highlights** (subtle color change)
6. User clicks and drags border to the right
7. **Title column widens smoothly**, text un-truncates
8. User releases mouse button
9. **New width persists** (saved to localStorage)
10. User refreshes page
11. **Title column maintains custom width**

**Mobile Behavior:**
- Column resizing disabled on touch devices (future: touch-optimized resize)
- Columns maintain responsive defaults on mobile
- Horizontal scroll enabled if total width exceeds viewport

---

## 5. Accessibility & Performance

### 5.1 WCAG AA Compliance Requirements

#### 5.1.1 Keyboard Navigation

**All New Interactive Elements:**
- CPU tooltip trigger: Tab-accessible, Enter/Space to show tooltip, ESC to close
- Modal dialogs: Tab-traps focus within modal, ESC to close, focus returns to trigger
- Clickable dashboard listings: Tab-accessible, Enter/Space to open modal
- Column resize handles: Tab-accessible, Arrow keys to resize (optional enhancement)
- Dropdown inline creation: Full keyboard workflow (Tab, Enter, ESC)

**Focus Management:**
- Visible focus indicators on all interactive elements (2px outline, high contrast)
- Focus trap in modals prevents tabbing to background content
- Focus restoration to trigger element on modal close
- Logical tab order follows visual hierarchy

#### 5.1.2 Screen Reader Support

**ARIA Labels:**
- CPU info icon: `aria-label="View CPU details"`
- Modal close buttons: `aria-label="Close dialog"`
- Expand/collapse buttons: `aria-label="Expand to full screen"` / `aria-label="Collapse to modal"`
- Column resize handles: `aria-label="Resize column"`

**ARIA Attributes:**
- Modals: `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to title
- Tooltips: `role="tooltip"`, `aria-describedby` linking trigger to content
- Clickable cards: `role="button"` if using div, prefer semantic button element
- Loading states: `aria-busy="true"` during data fetch

**Screen Reader Announcements:**
- Success actions: `aria-live="polite"` region for toast notifications
- Error states: `aria-live="assertive"` for critical errors
- Loading states: Loading text within `aria-live` region

#### 5.1.3 Color Contrast

**All Text:**
- Normal text (body, labels): Minimum 4.5:1 contrast ratio
- Large text (headings): Minimum 3:1 contrast ratio
- Interactive elements: Hover/focus states maintain contrast ratios

**Non-Text Elements:**
- Icons: Minimum 3:1 contrast against background
- Form borders: Minimum 3:1 contrast for inputs and dropdowns
- Focus indicators: Minimum 3:1 contrast against background

**Testing:**
- Run automated contrast checks with axe DevTools
- Manual verification with color blindness simulators
- Test with high contrast mode enabled (Windows/Mac)

### 5.2 Performance Considerations

#### 5.2.1 React Optimization

**Memoization:**
- `CpuTooltip`: Wrap with `React.memo`, compare by cpu.id
- `ListingOverviewModal`: Wrap with `React.memo`, compare by listingId and open state
- Table cells: Existing memoization maintained, extend to new cells
- Dropdown options: Memoize calculated widths with `useMemo`

**Debouncing:**
- Column resizing: 150ms debounce (already implemented)
- Dropdown search: 200ms debounce (already implemented)
- Form inputs: No debounce needed for controlled inputs with validation

**Code Splitting:**
- Modals: Use dynamic imports for modal components (`React.lazy`)
- Load CPU Details Modal only when tooltip "View Full Details" clicked
- Listing Overview Modal loaded on first dashboard listing click

#### 5.2.2 Data Fetching

**React Query Optimization:**
- CPU data: Include with listing fetch (no separate requests per tooltip)
- Listing details: 5-minute cache for overview modal
- Field options: 5-minute cache (already implemented)
- Dashboard data: 1-minute cache with automatic refetch

**Batch Requests:**
- Listings table: Single request fetches all listings with nested CPU data
- Avoid N+1 queries: Use `selectin` loading strategy for CPU/GPU relationships
- Pagination: Implement cursor-based pagination if listing count exceeds 100

**Prefetching:**
- Prefetch CPU details on tooltip hover (optional enhancement)
- Prefetch listing details on dashboard card hover (optional)

#### 5.2.3 Rendering Performance

**Virtualization:**
- Listings table: Maintain existing virtualization for 100+ rows
- Dropdown options: Virtualize if option count exceeds 50
- Modal content: Avoid virtualizing (content should fit in viewport with scroll)

**Bundle Size:**
- Monitor bundle impact of new components (should be < 5KB per component)
- Tree-shake unused Radix UI components
- Use named imports for Lucide icons (avoid full icon bundle)

**Render Metrics:**
- First Contentful Paint (FCP): < 1.5s
- Largest Contentful Paint (LCP): < 2.5s
- Cumulative Layout Shift (CLS): < 0.1
- First Input Delay (FID): < 100ms

---

## 6. Success Metrics

### 6.1 Feature Adoption Metrics

**CPU Tooltip & Modal:**
- **Tooltip Hover Rate:** % of users who hover over CPU info icon (target: >60%)
- **Modal Open Rate:** % of tooltip viewers who open full CPU modal (target: >30%)
- **Average Time in Modal:** Seconds spent viewing CPU details (target: 15-45s)

**Inline Dropdown Creation:**
- **Creation Usage Rate:** % of dropdown interactions that use inline creation (target: >20%)
- **Creation Success Rate:** % of inline creations that complete successfully (target: >95%)
- **Option Reuse Rate:** % of created options that are used on subsequent listings (target: >50%)

**Dashboard Interactivity:**
- **Modal Open Rate:** % of dashboard visits that open overview modal (target: >40%)
- **View Full Listing Rate:** % of modal viewers who navigate to full listing (target: >60%)
- **Dashboard Exit Rate:** % of users who complete tasks from dashboard without leaving (target: >25%)

**Column Resizing:**
- **Resize Adoption:** % of users who resize at least one column (target: >50%)
- **Resize Persistence:** % of resizes that are maintained across sessions (target: >90%)
- **Average Columns Resized:** Number of columns customized per user (target: 2-4)

### 6.2 Quality Metrics

**Bug Fix Validation:**
- **CPU Mark Calculation Accuracy:** 100% of listings with CPU+price show calculated metrics
- **CPU Save Success Rate:** 100% of CPU selection attempts persist correctly
- **Seed Script Reliability:** 100% success rate across 10+ executions in clean database

**Performance:**
- **Tooltip Render Time:** < 100ms from hover to display
- **Modal Open Time:** < 200ms from click to modal visible
- **Dropdown Width Calculation:** < 50ms per dropdown
- **Column Resize Responsiveness:** < 150ms debounced update

**Accessibility:**
- **Keyboard Navigation:** 100% of interactive elements accessible via keyboard
- **Screen Reader Compatibility:** Zero critical ARIA errors (axe audit)
- **Contrast Compliance:** 100% of text meets WCAG AA standards

### 6.3 User Satisfaction

**Qualitative Feedback (Post-Launch Surveys):**
- "I can quickly review CPU specs without leaving the table" (target: >80% agree)
- "Dropdowns are easy to read and use" (target: >85% agree)
- "Adding new options feels seamless" (target: >75% agree)
- "Dashboard listings provide useful quick information" (target: >70% agree)

**Error Rates:**
- Form submission errors: < 5%
- Modal interaction errors: < 2%
- Data display errors (null/undefined): < 1%

---

## 7. Dependencies & Risks

### 7.1 Dependencies

#### 7.1.1 Technical Dependencies

**Must Be Completed First:**
1. **Bug Fixes:** Must be completed before UI enhancements
   - Fix CPU Mark calculation (blocks metric display in modals)
   - Fix CPU save error (blocks testing of CPU tooltip/modal flow)
   - Fix seed script (blocks generation of test data)

2. **Column Resizing:** Must be restored before dropdown width fixes
   - Column resizing restoration enables testing of dropdown width behavior
   - Dropdown widths need resizeable columns to demonstrate unconstrained behavior

**Can Be Developed in Parallel:**
- CPU Tooltip & Modal (independent)
- Secondary Storage Dropdown (independent)
- Inline Option Creation Modal (independent)
- Dashboard Overview Modal (independent)
- Add Entry Modal Expandable (independent)

#### 7.1.2 External Dependencies

**No External Dependencies:**
- All required libraries already in package.json (Radix UI, TanStack, React Query)
- No new backend dependencies required
- No API rate limits or third-party services involved

### 7.2 Risks & Mitigation

#### 7.2.1 Technical Risks

**Risk 1: Performance Impact of Nested Modals**
- **Probability:** Medium
- **Impact:** High (modal stacking could cause z-index issues, focus trap conflicts)
- **Mitigation:**
  - Use Radix UI's modal prop to control layering
  - Test CPU modal from tooltip + listing overview modal stacking
  - Implement proper focus management for nested modals
  - Consider closing parent modal when child opens (alternative approach)

**Risk 2: Column Resizing Breaking Existing Table Layout**
- **Probability:** Medium
- **Impact:** Medium (could affect existing table features like sorting, filtering)
- **Mitigation:**
  - Test column resizing with all table features (sort, filter, grouping)
  - Add comprehensive regression tests for data-grid component
  - Implement feature flag for gradual rollout
  - Provide "Reset Layout" option for users to revert changes

**Risk 3: Dropdown Width Calculation Performance**
- **Probability:** Low
- **Impact:** Medium (calculating width for many dropdowns could slow initial render)
- **Mitigation:**
  - Memoize width calculations with useMemo
  - Perform calculations only once per unique option set
  - Cache calculated widths in component state
  - Measure render time with React DevTools Profiler

**Risk 4: CPU Data Not Included in Listing Response**
- **Probability:** Medium
- **Impact:** High (tooltip would require separate API call per listing, performance issue)
- **Mitigation:**
  - Verify listings endpoint includes CPU data via selectin loading
  - If not included, update backend to eager-load CPU relationship
  - Add API response schema validation in frontend
  - Implement fallback to fetch CPU data if missing (with loading state)

#### 7.2.2 UX Risks

**Risk 1: Modal Fatigue (Too Many Modals)**
- **Probability:** Medium
- **Impact:** Medium (users may feel overwhelmed by modal-heavy UI)
- **Mitigation:**
  - Use modals consistently (don't mix with full-page navigations)
  - Ensure ESC key and click-outside work reliably
  - Provide "Don't show again" option for repetitive modals (future)
  - Monitor modal abandonment rates (close without action)

**Risk 2: Inline Creation Modal Confusion**
- **Probability:** Low
- **Impact:** Medium (users may not understand option is global)
- **Mitigation:**
  - Clear helper text: "This option will be available for all listings"
  - Consider requiring confirmation: "Add [option] for all listings?"
  - Show success toast with context: "48 GB added to RAM options"
  - Add undo option in toast notification (future enhancement)

**Risk 3: Dashboard Modal Not Providing Enough Context**
- **Probability:** Low
- **Impact:** Low (users may still need to navigate to full listing)
- **Mitigation:**
  - Include most critical information in modal (pricing, metrics, hardware)
  - Ensure "View Full Listing" button is prominent
  - Track modal → full listing navigation rate as success metric
  - Iterate on modal content based on usage patterns

#### 7.2.3 Schedule Risks

**Risk 1: Bug Fixes Take Longer Than Expected**
- **Probability:** Medium
- **Impact:** High (blocks other features from testing)
- **Mitigation:**
  - Prioritize bug fixes as Phase 1 (completed before UI work)
  - Allocate buffer time for investigation and testing
  - Have fallback plan: UI features with mock data if bugs persist
  - Engage with backend team early for collaborative debugging

**Risk 2: Scope Creep (Additional Requests During Development)**
- **Probability:** High
- **Impact:** Medium (could delay core features)
- **Mitigation:**
  - Document out-of-scope items clearly (e.g., GPU tooltip, advanced filters)
  - Create backlog for future enhancements
  - Time-box investigation of edge cases
  - Require formal approval for scope additions

### 7.3 Rollback Plan

**If Critical Issues Arise Post-Deployment:**

1. **CPU Tooltip/Modal:** Hide info icon via feature flag
2. **Inline Creation Modal:** Revert to browser prompt() dialog
3. **Secondary Storage Dropdown:** Revert to number input field
4. **Dashboard Modals:** Remove click handlers, keep links
5. **Column Resizing:** Disable via table config flag
6. **Add Entry Modal:** Use existing full-page form

**Feature Flags (Recommended):**
- `ENABLE_CPU_TOOLTIP`: Boolean, default false (gradual rollout)
- `ENABLE_CUSTOM_CREATION_MODAL`: Boolean, default false
- `ENABLE_DASHBOARD_MODALS`: Boolean, default false
- `ENABLE_COLUMN_RESIZE`: Boolean, default true (disable on regression)

---

## 8. Appendices

### 8.1 Wireframes & Mockups

**To Be Created:**
- CPU tooltip layout (content hierarchy)
- CPU details modal layout (section organization)
- Inline option creation modal
- Listing overview modal (dashboard)
- Add entry modal (collapsed vs. expanded states)

### 8.2 API Response Examples

#### 8.2.1 Listing with Full CPU Data
```json
{
  "id": 13,
  "title": "Dell OptiPlex 7090 Micro",
  "base_price_usd": 499.99,
  "adjusted_price_usd": 449.99,
  "condition": "refurb",
  "status": "active",
  "cpu_id": 42,
  "cpu": {
    "id": 42,
    "name": "Intel Core i7-10700",
    "manufacturer": "Intel",
    "cores": 8,
    "threads": 16,
    "tdp_w": 65,
    "igpu_model": "Intel UHD Graphics 630",
    "cpu_mark_multi": 17500,
    "cpu_mark_single": 2850,
    "igpu_mark": 1200,
    "release_year": 2020
  },
  "dollar_per_cpu_mark_single": 0.158,
  "dollar_per_cpu_mark_multi": 0.026,
  "ram_gb": 16,
  "primary_storage_gb": 512,
  "storage_type": "NVMe",
  "secondary_storage_gb": null,
  "thumbnail_url": "/thumbnails/dell-optiplex-7090.jpg"
}
```

### 8.3 Database Schema Reference

#### 8.3.1 Relevant Tables
```sql
-- CPU table (existing)
CREATE TABLE cpu (
  id INTEGER PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  manufacturer VARCHAR(64) NOT NULL,
  cores INTEGER,
  threads INTEGER,
  tdp_w INTEGER,
  igpu_model VARCHAR(255),
  cpu_mark_multi INTEGER,
  cpu_mark_single INTEGER,
  igpu_mark INTEGER,
  release_year INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Listing table (existing, relevant fields)
CREATE TABLE listing (
  id INTEGER PRIMARY KEY,
  cpu_id INTEGER REFERENCES cpu(id),
  secondary_storage_gb INTEGER,
  dollar_per_cpu_mark_single FLOAT,
  dollar_per_cpu_mark_multi FLOAT,
  -- ... other fields
);

-- Port table (existing, verify field name)
CREATE TABLE port (
  id INTEGER PRIMARY KEY,
  ports_profile_id INTEGER REFERENCES ports_profile(id), -- Confirm name
  type VARCHAR(32) NOT NULL,
  count INTEGER NOT NULL DEFAULT 1,
  -- ... other fields
);
```

### 8.4 Component Props Interfaces

#### 8.4.1 CpuTooltip Component
```typescript
interface CpuTooltipProps {
  cpu: CpuData;
  onOpenDetails: () => void;
  triggerClassName?: string;
}

interface CpuData {
  id: number;
  name: string;
  cpu_mark_single: number | null;
  cpu_mark_multi: number | null;
  igpu_model: string | null;
  igpu_mark: number | null;
  tdp_w: number | null;
  release_year: number | null;
}
```

#### 8.4.2 CpuDetailsModal Component
```typescript
interface CpuDetailsModalProps {
  cpuId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}
```

#### 8.4.3 InlineOptionCreationModal Component
```typescript
interface InlineOptionCreationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  fieldId: number;
  fieldName: string;
  fieldType: "string" | "number" | "enum";
  initialValue?: string;
  onSuccess: (newOption: string) => void;
}
```

#### 8.4.4 ListingOverviewModal Component
```typescript
interface ListingOverviewModalProps {
  listingId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onViewFullListing?: () => void;
}
```

---

## 9. Implementation Checklist

### 9.1 Phase 1: Bug Fixes (Highest Priority)

- [ ] Investigate and fix CPU Mark calculation logic
- [ ] Add recalculation trigger on price/CPU update
- [ ] Add bulk recalculation script for existing listings
- [ ] Fix CPU save error (type casting)
- [ ] Update Pydantic schema for cpu_id validation
- [ ] Fix seed script Port creation error
- [ ] Verify Port model field name
- [ ] Run seed script successfully
- [ ] Add unit tests for all bug fixes
- [ ] Regression test suite execution

### 9.2 Phase 2: Foundation (Table & Dropdown UX)

- [ ] Restore column resizing in data-grid component
- [ ] Add localStorage persistence for column widths
- [ ] Implement dropdown width calculation utility
- [ ] Apply dropdown width fix to all affected fields
- [ ] Test dropdown overflow behavior
- [ ] Create InlineOptionCreationModal component
- [ ] Integrate modal with ComboBox component
- [ ] Add Secondary Storage dropdown configuration
- [ ] Update add-listing-form for Secondary Storage
- [ ] Regression test existing table features

### 9.3 Phase 3: CPU Discoverability

- [ ] Create CpuTooltip component
- [ ] Integrate tooltip into listings-table
- [ ] Verify CPU data included in listing API response
- [ ] Create CpuDetailsModal component
- [ ] Implement getCpu API client function
- [ ] Connect tooltip to modal trigger
- [ ] Add loading and error states
- [ ] Accessibility audit (keyboard, screen reader)
- [ ] Performance testing (tooltip render time)
- [ ] Cross-browser testing

### 9.4 Phase 4: Dashboard Enhancements

- [ ] Create ListingOverviewModal component
- [ ] Make dashboard SummaryCard clickable
- [ ] Make dashboard ListingRow clickable
- [ ] Implement listing detail fetch
- [ ] Integrate ValuationCell into modal
- [ ] Add "View Full Listing" navigation
- [ ] Test modal stacking scenarios
- [ ] Accessibility audit
- [ ] Mobile responsive testing

### 9.5 Phase 5: Add Entry Modal Enhancement

- [ ] Create AddListingModal wrapper component
- [ ] Implement expand/collapse state management
- [ ] Add expand/collapse button UI
- [ ] Integrate with Data Tab "Add entry" button
- [ ] Integrate with /listings "Add Listing" button
- [ ] Test state preservation during expand/collapse
- [ ] Test form submission in both modes
- [ ] Accessibility audit (focus management)
- [ ] Animation performance testing

### 9.6 Phase 6: Testing & Quality Assurance

- [ ] Unit tests for all new components
- [ ] Integration tests for modal flows
- [ ] E2E tests for critical user journeys
- [ ] Accessibility testing (axe, keyboard, screen reader)
- [ ] Performance testing (React Profiler)
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Mobile testing (iOS Safari, Chrome Android)
- [ ] Load testing (100+ listings in table)
- [ ] Error scenario testing (API failures, network issues)

### 9.7 Phase 7: Documentation & Deployment

- [ ] Update component documentation
- [ ] Create user guide for new features
- [ ] Update API documentation (if changed)
- [ ] Create deployment guide
- [ ] Add feature flags (if using gradual rollout)
- [ ] Create rollback procedures
- [ ] Prepare release notes
- [ ] Deploy to staging environment
- [ ] Stakeholder review and sign-off
- [ ] Deploy to production

---

## 10. Conclusion

This PRD defines a comprehensive set of enhancements to improve the Deal Brain user experience through better CPU information discoverability, streamlined data entry, consistent table interactions, and interactive dashboard elements. Combined with critical bug fixes, these features will significantly improve usability and data integrity.

**Next Steps:**
1. Review and approve this PRD with stakeholders
2. Create detailed implementation plan with task breakdown
3. Assign phases to development sprints
4. Begin Phase 1 (Bug Fixes) immediately
5. Iterate on component designs with user feedback

**Estimated Timeline:**
- Phase 1 (Bug Fixes): 2-3 days
- Phase 2 (Foundation): 3-4 days
- Phase 3 (CPU Features): 3-4 days
- Phase 4 (Dashboard): 2-3 days
- Phase 5 (Add Entry Modal): 2-3 days
- Phase 6 (Testing): 3-4 days
- Phase 7 (Documentation): 1-2 days

**Total Estimated Duration:** 16-23 days (3-4.5 weeks)

---

**Document History:**
- v1.0 (2025-10-06): Initial PRD created by Lead Architect
