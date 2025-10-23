# Product Requirements Document: October 3 UX/Data Enhancements

**Version:** 1.0
**Date:** October 3, 2025
**Status:** Planning
**Author:** Lead Architect

---

## Executive Summary

This PRD addresses critical UX refinements and data quality enhancements across four primary domains: **Listings Valuation Display**, **Table Dropdown Workflows**, **Global Fields Management**, and **CPU Data Enrichment**. These improvements transform Deal Brain from a functional catalog tool into a polished, production-grade platform with intuitive workflows and comprehensive hardware data.

**Strategic Goals:**
- Provide clear, color-coded valuation insights directly in the listings table
- Eliminate context-switching friction when managing dropdown field options
- Modernize Global Fields terminology and workflows for non-technical users
- Enrich CPU catalog with standardized benchmark scores for accurate valuations

**Impact:** These enhancements eliminate current UX friction points, improve data quality for valuations, and establish user-friendly patterns that reduce training time and increase user confidence.

---

## Problem Statement

### Current Pain Points

1. **Listings Valuation Display**
   - Valuation column shows inconsistent formatting (some negative savings, some just prices, messy text)
   - No visual hierarchy to distinguish positive savings, negative savings (premiums), or neutral valuations
   - Users cannot quickly identify best deals without manual comparison
   - Missing configurable thresholds for highlighting exceptional value

2. **Table Dropdown Workflows**
   - Dropdown fields require leaving the current page to add new options via Global Fields
   - Search field within dropdowns has inconsistent styling and extra text
   - Creates friction in data entry workflows (especially during imports or bulk edits)

3. **Global Fields Management**
   - "Enum" terminology confuses non-technical users (should be "Dropdown")
   - Cannot define dropdown options during field creation—requires post-creation edit
   - No default value setting for any field type (requires manual entry for every new entity)
   - Core fields marked "Managed via schema" appear completely locked (can't edit labels, descriptions, options)
   - Confusing distinction between which properties are editable vs. locked

4. **CPU Data Quality**
   - Missing standardized benchmark scores (CPU Mark, Single Thread)
   - No integrated graphics benchmark data (iGPU Mark)
   - Cores, Threads, Series, Manufacturer stored as free text instead of controlled dropdowns
   - Prevents accurate performance-based valuations and comparisons

---

## User Personas

### Primary: **Deal Hunter / Power User**
- **Goals:** Quickly identify underpriced listings, understand savings at a glance
- **Pain Points:** Cannot visually scan for deals, unclear what "good" savings looks like
- **Success Metrics:** Identifies top 3 deals within 10 seconds of opening listings page

### Secondary: **Data Entry / Catalog Manager**
- **Goals:** Efficiently add listings and maintain clean dropdown options
- **Pain Points:** Must navigate away to add dropdown options, confusing field type names
- **Success Metrics:** Adds new dropdown option without leaving current form (saves 80% time)

### Tertiary: **System Administrator**
- **Goals:** Configure field defaults, maintain data quality standards
- **Pain Points:** Can't set sensible defaults, can't edit core field metadata
- **Success Metrics:** Sets default values for 10+ fields in <5 minutes, edits core field labels inline

---

## Requirements

### 1. Listings Valuation Column Enhancements

#### 1.1 Visual Formatting & Color Coding

**FR-VAL-001:** Standardized Display Format
- **Requirement:** Every valuation cell shows both adjusted price and savings delta in consistent format
- **Format Examples:**
  - Positive savings: `$450` with green badge `-$50` (13.9% off)
  - Neutral (no savings): `$500` with gray badge `$0` (List price)
  - Premium (negative savings): `$550` with red badge `+$50` (9.1% markup)
- **Acceptance Criteria:**
  - Primary value (adjusted_price_usd) displayed as large, bold currency
  - Delta badge positioned to the right with icon (↓ for savings, ↑ for premium)
  - Percentage calculation: `(list_price - adjusted_price) / list_price * 100`

**FR-VAL-002:** Color Coding System
- **Base Colors:**
  - Green (savings): adjusted_price < list_price
  - Red (premium): adjusted_price > list_price
  - Gray (neutral): adjusted_price == list_price
- **Intensity Thresholds (configurable):**
  - Light green: 1-10% savings
  - Medium green: 10-25% savings
  - Dark green: 25%+ savings
  - Light red: 1-10% markup
  - Dark red: 10%+ markup
- **Implementation:** Use Tailwind color variants (green-100/600/800, red-100/600/800)

**FR-VAL-003:** Configurable Threshold Settings
- **Location:** Settings page or profile configuration
- **Configurable Values:**
  - "Good Deal" threshold (default: 15% savings) → highlights in UI
  - "Great Deal" threshold (default: 25% savings) → additional visual indicator (star icon)
  - "Premium" warning threshold (default: 10% markup) → warning indicator
- **Acceptance Criteria:**
  - Thresholds stored per user or globally (TBD based on multi-user needs)
  - Changes reflect immediately in listings table
  - Tooltip on column header explains current thresholds

#### 1.2 Interactive Breakdown Modal

**FR-VAL-004:** Click-to-Expand Breakdown
- **Trigger:** Click on valuation cell or dedicated "Details" button
- **Modal Content:**
  - Listing title + thumbnail image
  - Base list price
  - Applied rules grouped by category:
    - Component Adjustments (RAM, Storage, GPU, etc.)
    - Condition Multipliers
    - Market Adjustments
  - Each rule shows: name, description, adjustment amount
  - Final adjusted price with total delta
  - Link to full breakdown page (existing `/listings/:id/breakdown` route)
- **Size:** Medium modal (640px)

**FR-VAL-005:** Sorting & Filtering
- **Sorting:** Enable numeric sort by adjusted_price_usd (already exists, verify)
- **Filtering:** Add range filter (min/max inputs) for adjusted_price_usd
- **Advanced Filter:** Filter by savings percentage (e.g., "Show only >20% savings")

---

### 2. Table Dropdown Enhancements

#### 2.1 Inline Option Creation

**FR-DROPDOWN-001:** Create New Option from Dropdown
- **Trigger:** User types value not in dropdown list, presses Enter or clicks "Create" button
- **Confirmation Dialog:**
  - Title: "Add '{value}' to {field_name}?"
  - Checkbox: "Add to Global Fields" (default: checked)
  - Actions: Cancel / Confirm
- **Behavior:**
  - If confirmed with checkbox: Add to field's options array in CustomFieldDefinition table
  - If confirmed without checkbox: Add to current entity only (transient value)
  - Option immediately available in current dropdown and future uses
  - API call: `POST /api/fields/{field_id}/options` with `{value: string}`
- **Scope:** All dropdown fields across app (listings table, CPU editor, custom entity forms)

**FR-DROPDOWN-002:** Consistent Search Field Styling
- **Requirement:** Search input within dropdown should have clean margins and no placeholder text
- **Styling:**
  - Match padding of dropdown options below it
  - No border (or subtle border matching option hover state)
  - Placeholder: empty or single icon (magnifying glass)
  - Consistent with existing ComboBox component design
- **Acceptance Criteria:**
  - Visual alignment with option list
  - No jarring spacing differences
  - Matches shadcn/ui Command component patterns

---

### 3. Global Fields Management Enhancements

#### 3.1 Field Type Clarity

**FR-FIELDS-001:** Rename "Enum" to "Dropdown"
- **Change:** In Type dropdown/selector, replace "enum" with "dropdown"
- **Database:** No migration needed—`data_type` can remain "enum" in DB
- **Display Layer:** Map "enum" → "Dropdown" in UI, "multi_select" → "Multi-Select Dropdown"
- **Acceptance Criteria:**
  - All UI references (form, table, tooltips) use "Dropdown"
  - Documentation/help text updated
  - No user-facing "enum" terminology

#### 3.2 Dropdown Options Builder (Create Flow)

**FR-FIELDS-002:** Options Builder in Create Form
- **Requirement:** When Type = "Dropdown", show "Field Options" section
- **UI Components:**
  - Section title: "Field Options" with description: "Define available options for this dropdown"
  - Initially: Single empty text input with "Add Option" button
  - Clicking "Add Option" adds another input below
  - Each option input has delete button (X icon) except when only one remains
  - "Import from CSV" button: paste comma-separated values to bulk add
- **Validation:**
  - At least 1 option required when Type = Dropdown
  - Duplicate options prevented (case-insensitive)
  - Empty options ignored
- **Data Storage:** Save as `options` array in CustomFieldDefinition table

**FR-FIELDS-003:** Options Builder in Edit Form
- **Requirement:** When editing Dropdown field, show existing options as editable list
- **UI Components:**
  - Each existing option as text input (inline editing)
  - Delete button per option (with confirmation if option is used in data)
  - "Add Option" button below list
  - Drag handles for reordering (save order to `options` array)
- **Behavior:**
  - Deleting used option shows warning: "'{option}' is used by {count} records. Delete anyway?"
  - Option edits update all existing records using that option (or prompt to migrate)

#### 3.3 Default Value Setting

**FR-FIELDS-004:** Default Value Configuration
- **Requirement:** All field types support optional "Default Value" setting
- **UI Implementation:**
  - Add "Default Value" field below Type selector
  - Input type adapts to field type:
    - Text/String: Text input
    - Number: Number input
    - Boolean: Checkbox
    - Dropdown: Dropdown showing available options
    - Multi-Select Dropdown: Multi-select showing available options
    - Date: Date picker
- **Behavior:**
  - When creating new entity (Listing, CPU, etc.), pre-fill field with default value
  - User can override during creation
  - Empty/null allowed if field not marked Required
- **Database:** Use existing `default_value` column in CustomFieldDefinition

#### 3.4 Core Field Editability

**FR-FIELDS-005:** Selective Locking of Core Fields
- **Locked Properties (non-editable):**
  - Entity (prevents reassigning field to different entity type)
  - Key (prevents breaking API contracts)
  - Type (prevents data type mismatches)
- **Editable Properties (even for core fields):**
  - Label (display name)
  - Description
  - Options (for dropdown fields)
  - Default Value
  - Required status (with dependency warning)
  - Validation rules (min/max, regex, etc.)
- **UI Treatment:**
  - Locked fields: Show lock icon with tooltip "This property cannot be changed to maintain data integrity"
  - Editable fields: Normal inputs, no special indicators
  - Banner at top: "Core field—some properties are locked to prevent breaking changes"
- **Acceptance Criteria:**
  - User can edit CPU.cores field options from text to dropdown
  - User can edit Listing.title label from "Title" to "Listing Name"
  - User cannot change CPU.cores key or entity

---

### 4. CPU Data Enrichment

#### 4.1 Benchmark Score Fields

**FR-CPU-001:** CPU Mark Score Field
- **Field:** `cpu_mark_multi` (already exists in DB schema)
- **Type:** Number (integer, nullable)
- **Source:** cpubenchmark.net PassMark scores
- **UI:** Add to CPU creation/edit form as "CPU Mark (Multi-Core)" with tooltip linking to PassMark
- **Validation:** Positive integer, typical range 1,000-50,000

**FR-CPU-002:** Single-Thread Score Field
- **Field:** `cpu_mark_single` (already exists in DB schema)
- **Type:** Number (integer, nullable)
- **Source:** cpubenchmark.net single-thread scores
- **UI:** Add as "CPU Mark (Single-Thread)" below multi-core field
- **Validation:** Positive integer, typical range 500-5,000

**FR-CPU-003:** Integrated Graphics Score
- **Field:** `igpu_mark` (add to CPU model if not present)
- **Type:** Number (integer, nullable)
- **Source:** cpubenchmark.net GPU scores for integrated graphics
- **UI:** Add as "iGPU Mark (Optional)" with description: "Benchmark score for integrated graphics (if applicable)"
- **Validation:** Positive integer, typical range 100-3,000

#### 4.2 Controlled Dropdown Fields

**FR-CPU-004:** Manufacturer Dropdown
- **Current:** Free text field
- **Change:** Convert to Dropdown field with common values
- **Options:** Intel, AMD, Apple, Qualcomm, MediaTek, Other
- **Migration:** Existing values migrate to closest match, manual review for "Other"
- **Allow Custom:** Yes (via inline creation flow)

**FR-CPU-005:** Series Dropdown
- **Current:** Free text field
- **Change:** Convert to Dropdown field with common values
- **Options (Intel):** Core i3, Core i5, Core i7, Core i9, Xeon, Pentium, Celeron
- **Options (AMD):** Ryzen 3, Ryzen 5, Ryzen 7, Ryzen 9, Threadripper, EPYC, Athlon
- **Behavior:** Options filter based on selected Manufacturer (dependent dropdown)
- **Allow Custom:** Yes

**FR-CPU-006:** Cores & Threads Dropdowns
- **Current:** Number fields (nullable)
- **Change:** Convert to Dropdown (but allow custom numeric entry)
- **Options:**
  - Cores: 1, 2, 4, 6, 8, 10, 12, 14, 16, 20, 24, 32, 64, 128
  - Threads: 2, 4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 64, 128, 256
- **Validation:** Threads >= Cores (logical constraint)
- **Allow Custom:** Yes (for exotic CPUs)

---

## Non-Functional Requirements

### Performance

**NFR-PERF-001:** Valuation Column Rendering
- Render time: <100ms for 100 rows (memoization required)
- Color calculation: Client-side, no API calls for color determination

**NFR-PERF-002:** Dropdown Option Creation
- API response: <300ms for adding new option
- Optimistic UI: Show new option immediately, rollback on error

### Accessibility

**NFR-A11Y-001:** Color Blindness Support
- Do not rely solely on color for savings/premium distinction
- Use icons (↓ ↑) and text labels in addition to color
- Support high-contrast mode with sufficient contrast ratios

**NFR-A11Y-002:** Keyboard Navigation
- All dropdown interactions keyboard-accessible (Tab, Enter, Escape)
- Valuation breakdown modal supports keyboard navigation and Escape to close

### Usability

**NFR-UX-001:** Consistency
- All dropdowns use unified ComboBox component
- All modals use ModalShell component
- Color scheme follows existing Tailwind config

**NFR-UX-002:** Feedback
- Toast notification on successful option creation: "'{option}' added to {field_name}"
- Error toast on failure with retry option
- Loading states for all async operations

---

## Success Metrics

### Adoption Metrics
- **Inline Dropdown Creation:** 70% of new options created inline (vs. navigating to Global Fields)
- **Default Values:** 80% of new fields configured with default values
- **Valuation Interaction:** 50% of users click breakdown modal within first session

### Performance Metrics
- **Deal Identification Speed:** Users identify top deal in <10 seconds (user testing)
- **Data Entry Speed:** 40% reduction in time to add listing with custom field values

### Quality Metrics
- **CPU Data Completeness:** 90% of CPUs have CPU Mark scores within 1 month
- **Field Clarity:** 0 support requests about "What is Enum?" after terminology change

---

## Out of Scope

The following are explicitly excluded from this phase:

1. **Advanced Valuation Features:**
   - Historical valuation trends over time
   - Comparative valuation across multiple rulesets
   - Market-based dynamic threshold adjustments

2. **Dropdown Features:**
   - Hierarchical/nested dropdowns (e.g., Manufacturer → Series → Model)
   - Conditional dropdowns beyond basic dependency (Series based on Manufacturer)
   - Bulk option import via file upload

3. **CPU Data:**
   - Automated benchmark score fetching from cpubenchmark.net API
   - Historical benchmark score tracking
   - Overclocking benchmark scores

4. **Multi-User Features:**
   - User-specific threshold preferences
   - Role-based field editing permissions
   - Collaborative option management

---

## Dependencies

### Technical Dependencies
- Existing components: ComboBox, ModalShell, DataGrid (already implemented)
- Backend API: CustomFieldDefinition model with `options` and `default_value` columns (already exists)
- React Query for optimistic updates and cache invalidation

### External Dependencies
- cpubenchmark.net (manual data entry, no API integration in this phase)

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Color-only distinction fails accessibility | High | Medium | Add icons and text labels, test with high-contrast mode |
| Option creation conflicts (race conditions) | Medium | Low | Use optimistic UI with server-side duplicate detection |
| CPU data migration complexity | Medium | Medium | Create migration script with manual review step, validate data |
| Threshold configuration UX unclear | Medium | Medium | Add inline help text, examples, and sensible defaults |
| Performance degradation with many options | Low | Low | Virtualize dropdown lists if >100 options (rare) |

---

## Appendix

### A. API Endpoint Requirements

**New Endpoints:**
1. `POST /api/fields/{field_id}/options` - Add new option to field
   - Request: `{value: string}`
   - Response: `{field: FieldResponse}`

2. `DELETE /api/fields/{field_id}/options/{option_value}` - Remove option
   - Query param: `force=true` to delete even if used
   - Response: `{success: boolean, affected_records: number}`

3. `GET /api/settings/valuation-thresholds` - Get threshold config
   - Response: `{good_deal: number, great_deal: number, premium_warning: number}`

4. `PUT /api/settings/valuation-thresholds` - Update thresholds
   - Request: `{good_deal?: number, great_deal?: number, premium_warning?: number}`

**Modified Endpoints:**
1. `GET /api/listings` - Ensure `adjusted_price_usd` and `list_price_usd` always returned

### B. Database Schema Changes

**Minimal migrations required:**

1. **CPU table** (if not present):
   - Add `igpu_mark` column (INTEGER NULL)
   - Verify `cpu_mark_multi` and `cpu_mark_single` exist

2. **Settings table** (if not present):
   - Create `application_settings` table:
     ```sql
     CREATE TABLE application_settings (
       key VARCHAR(64) PRIMARY KEY,
       value_json JSON NOT NULL,
       updated_at TIMESTAMP DEFAULT NOW()
     );
     ```
   - Seed with valuation thresholds

3. **CustomFieldDefinition table:**
   - Verify `options` (JSON array) and `default_value` (JSON) columns exist (already present)

### C. UI Component Hierarchy

```
ListingsTable
├── DataGrid
│   ├── ValuationCell (new component)
│   │   ├── AdjustedPrice (bold, large)
│   │   ├── DeltaBadge (colored, with icon)
│   │   └── OnClick → ValuationBreakdownModal
│   └── EditableCell (with ComboBox)
│       └── ComboBox (with inline create)
│           └── ConfirmationDialog

GlobalFieldsPage
├── FieldForm
│   ├── TypeSelector (Dropdown with "Dropdown" option)
│   ├── OptionsBuilder (conditional on Type=Dropdown)
│   │   ├── OptionInput[] (draggable list)
│   │   ├── AddOptionButton
│   │   └── ImportCSVButton
│   ├── DefaultValueInput (polymorphic based on Type)
│   └── LockedFieldBanner (for core fields)
```

### D. Migration Strategy

**Phase 1:** Backend changes (Week 1)
- Add `igpu_mark` to CPU model if needed
- Create settings table and seed thresholds
- Add API endpoints for option management

**Phase 2:** UI components (Week 1-2)
- Create ValuationCell component
- Enhance ComboBox with inline creation
- Build OptionsBuilder for field forms

**Phase 3:** Integration & Data (Week 2)
- Integrate ValuationCell into listings table
- Update Global Fields forms
- Migrate CPU data to dropdowns

**Phase 4:** Testing & Polish (Week 3)
- Accessibility testing (color blindness, keyboard nav)
- Performance testing (100+ row tables)
- User acceptance testing

**Phase 5:** Data Enrichment (Ongoing)
- Populate CPU benchmark scores from cpubenchmark.net
- Quality assurance on dropdown migrations
