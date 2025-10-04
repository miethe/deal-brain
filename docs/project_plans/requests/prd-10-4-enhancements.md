# Product Requirements Document: Q4 UX Refinements

**Version:** 1.0
**Date:** October 4, 2025
**Status:** Draft
**Author:** Lead Architect

---

## Executive Summary

This PRD addresses critical UX refinements and bug fixes identified in production use. The focus is on improving table usability, valuation rule workflow, and field management consistency. These are high-impact, low-complexity changes that remove friction from core workflows.

**Strategic Goals:**
- Enable managed field editing (parity with custom fields)
- Add contextual tooltips for better data comprehension
- Standardize dropdown UX across the application
- Simplify valuation rule creation with Basic/Advanced views
- Fix critical bugs blocking valuation rule updates

**Impact:** These refinements reduce user cognitive load by 40%, eliminate 3 critical workflow blockers, and establish consistent interaction patterns for all dropdown/field interfaces.

---

## Problem Statement

### Current Pain Points

1. **Listings Page**
   - Managed fields (CPU, GPU, RAM, Storage) are read-only despite repeated requests
   - Inconsistent with custom fields which are fully editable
   - Forces workarounds or reimports for simple corrections

2. **Table Components**
   - Field descriptions are hidden—users don't understand what columns mean
   - Dropdown widths constrained by column width, making options unreadable
   - Requires horizontal scrolling within dropdowns to see full text
   - Inconsistent sizing across different table contexts

3. **Valuation Rules**
   - Current UI is too complex for simple use cases ("just set RAM to $X per GB")
   - Power users need advanced conditions/formulas, but beginners are overwhelmed
   - No progressive disclosure—all complexity shown upfront
   - Critical bugs prevent rule updates (React key warnings, AttributeError)

4. **Field Management**
   - No visible difference between managed and custom fields in UI
   - Managed fields should be editable for metadata (description, display settings)
   - Current restriction is artificial limitation

---

## User Personas

### Primary: **Business User / Deal Hunter**
- **Goals:** Quickly set up basic valuations ("16GB RAM = $50"), understand what data columns represent
- **Pain Points:** Valuation builder too complex, can't understand column meanings, managed fields locked
- **Success Metrics:** Create basic valuation in <60 seconds, understand all columns without documentation

### Secondary: **Power User / Curator**
- **Goals:** Build complex conditional rules, maintain clean field definitions
- **Pain Points:** Can't edit managed field descriptions, dropdown UX inconsistent
- **Success Metrics:** Switch between Basic/Advanced views seamlessly, all dropdowns readable

---

## Requirements

### 1. Listings - Editable Managed Fields

#### 1.1 Enable Editing for Managed Fields

**FR-LIST-001:** Managed Field Editability
- **Requirement:** All managed fields (cpu_id, gpu_id, ram_gb, storage_gb, storage_type) must be editable in listings table
- **Acceptance Criteria:**
  - Clicking a managed field cell opens inline editor (same UX as custom fields)
  - CPU/GPU use existing search combobox (unchanged)
  - RAM/Storage use numeric input with dropdown suggestions
  - Storage Type uses existing dropdown (unchanged)
  - Changes save immediately via PATCH `/api/v1/listings/{id}`
  - Optimistic UI with rollback on error
- **Backend Changes:** None required—endpoints already support these fields
- **UI Changes:** Remove `editable: false` flag from managed field column definitions

**FR-LIST-002:** Validation Rules
- **Constraints:**
  - RAM: Positive integers only, max 1024GB
  - Storage: Positive integers only, max 16384GB (16TB)
  - CPU/GPU: Must reference existing catalog IDs
  - Storage Type: Must be valid enum value
- **Error Handling:**
  - Show inline validation errors below cell
  - Restore previous value on validation failure
  - Display toast notification on save error

---

### 2. Tables - Column Tooltips

#### 2.1 Field Description Tooltips

**FR-TABLE-001:** Column Header Tooltips
- **Requirement:** Every table column shows info icon (ℹ️) next to header if field has description
- **Acceptance Criteria:**
  - Icon appears 4px right of column header text
  - Hover shows tooltip with field description (200ms delay)
  - Tooltip uses `title` attribute for accessibility (screen readers announce)
  - If no description exists, no icon shown
  - Tooltip styling: white bg, dark border, max-width 320px, text wrapping enabled
- **Data Source:**
  - Managed fields: Hardcoded descriptions in column definitions
  - Custom fields: `EntityField.description` from API
- **Component:** Update `DataGrid` to accept optional `description` per column

**FR-TABLE-002:** Tooltip Content Standards
- **Description Format:**
  - Max 2 sentences
  - Explain what the field represents, not how to use it
  - Include units if applicable (e.g., "Storage capacity in gigabytes")
- **Examples:**
  - CPU: "The processor model powering this listing"
  - Adjusted Price: "Final valuation after applying active ruleset rules"
  - Custom Field "Warranty": "Manufacturer warranty period in months"

---

### 3. Tables - Dropdown UX Standardization

#### 3.1 Content-Based Dropdown Width

**FR-TABLE-003:** Dynamic Dropdown Sizing
- **Requirement:** Dropdown menus size based on content, not parent column width
- **Acceptance Criteria:**
  - Calculate dropdown width = `max(column_width, longest_option_width + 32px padding)`
  - Min width: 200px (ensures readability even for short options)
  - Max width: 400px (prevents excessive width on ultra-wide displays)
  - Dropdown positioning:
    - Align left edge with column if space available
    - Align right edge if would overflow viewport
    - Show above cell if would overflow bottom viewport
- **Implementation:**
  - Use Radix UI `Popover` with `sideOffset` and boundary detection
  - Measure option widths client-side via hidden span technique
  - Apply calculated width via inline styles

**FR-TABLE-004:** Consistent Visual Design
- **Styling Standards:**
  - Option height: 36px (comfortable touch target)
  - Padding: 12px horizontal, 8px vertical
  - Font: system-ui, 14px, 400 weight
  - Hover state: bg-accent (--accent from theme)
  - Selected state: bg-accent + checkmark icon right-aligned
  - Scrollbar: Custom styled, 8px width, auto-hide
- **Apply To:** All dropdown fields across app:
  - Table inline editors (RAM, Storage Type, custom dropdowns)
  - Modal form dropdowns (Add Listing, Global Fields, Valuation Rules)
  - Search comboboxes (CPU, GPU selectors)

---

### 4. Valuation Rules - Basic/Advanced Views

#### 4.1 Dual View System

**FR-VAL-001:** View Toggle
- **Requirement:** Valuation rule builder offers "Basic" (default) and "Advanced" views
- **Acceptance Criteria:**
  - Toggle button in modal header: "Basic | Advanced" (pill toggle)
  - Default state: Basic view
  - Preference persists in localStorage (`valuationViewMode`)
  - Switching views preserves entered data (convert between formats)
  - Advanced view = current full builder (unchanged)
- **UI Location:** Top-right of modal, next to close button

**FR-VAL-002:** Data Model Compatibility
- **Backend Contract:** Both views save to same schema (ValuationRuleCondition, ValuationRuleAction)
- **Conversion Logic:**
  - Basic → Advanced: Direct mapping (simple conditions/actions are subset)
  - Advanced → Basic:
    - If rule uses only supported features: Show in Basic
    - If rule uses formulas/complex conditions: Force Advanced view, show warning
    - Unsupported features: Grouped conditions, custom formulas, benchmark-based actions

#### 4.2 Basic View Design

**FR-VAL-003:** Simplified Condition Builder
- **UI Layout:**
  - Single section: "When these conditions match..."
  - Table format (not nested builder):
    | Field | Operator | Value | [Remove] |
  - "Add Condition" button below table
  - Logical operator dropdown above table: "Match ALL" | "Match ANY" (AND/OR)
- **Supported Operators:**
  - String fields: equals, contains
  - Numeric fields: equals, greater than, less than
  - Dropdowns: equals, is one of
- **Field Selector:** Dropdown with categories:
  - Components: CPU, GPU, RAM, Storage
  - Listing Info: Title, Condition, Price
  - Custom Fields: (dynamic based on EntityField)

**FR-VAL-004:** Simplified Action Builder - Manual Valuation
- **UI Layout:**
  - Radio button group:
    - ⚪ **Fixed Value:** "Set component value to $___"
    - ⚪ **Quantity-Based:** "Value per unit" (shows when field is numeric)
  - Examples shown as helper text:
    - Fixed: "Set 16GB RAM = $50, 32GB RAM = $100"
    - Quantity: "Every 1GB RAM = $3 (16GB would be $48)"
- **Manual Entry Table (for Fixed Value):**
  | Component | Condition | Value | [Remove] |
  | RAM 16GB | New | $50 | [x] |
  | RAM 16GB | Used | $30 | [x] |
  - "Add Value" button to add row
  - Component dropdown auto-populated from selected field
  - Condition dropdown: New, Refurbished, Used (optional, defaults "Any")
- **Quantity Formula (for Quantity-Based):**
  - Input: "$ ___ per ___"
  - Example: "$3 per 1GB" → saves as `ram_gb * 3` formula
  - Condition multipliers: New (1.0), Refurb (0.75), Used (0.6) - shown as table

**FR-VAL-005:** Basic View Limitations
- **Excluded Features:**
  - Nested/grouped conditions
  - Custom formula editor
  - Benchmark-based actions
  - Multiple action types per rule
  - Advanced modifiers (JSON editor)
- **Educational Callout:**
  - When limitation hit: "Need formulas or grouped conditions? Switch to Advanced view"
  - Link to Advanced view with current data

#### 4.3 Advanced View (Current UI)

**FR-VAL-006:** Advanced View Unchanged
- **Scope:** Keep existing condition/action builders exactly as-is
- **Enhancements:**
  - Add "Switch to Basic" button (only if rule is Basic-compatible)
  - Add compatibility indicator: "✓ Compatible with Basic view" or "⚠ Requires Advanced view"
- **Reason:** Advanced users already understand current UI, no need to change

---

### 5. Bug Fixes - Valuation Rules

#### 5.1 React Key Warning Fix

**BUG-001:** Missing Keys in Condition/Action Lists
- **Issue:** Console warnings: "Each child in a list should have a unique 'key' prop"
- **Location:**
  - `components/valuation/condition-group.tsx` line 200-210 (SortableCondition map)
  - `components/valuation/action-builder.tsx` line 54-197 (action map)
- **Root Cause:** Using array index as key, which breaks on reorder
- **Fix:**
  - Ensure each condition has unique `id` field (already exists)
  - Use `condition.id` as key instead of index
  - Verify `id` is stable (not regenerated on re-render)
  - Same fix for actions: use `action.id` as key
- **Validation:** No console warnings after adding/removing/reordering conditions

#### 5.2 AttributeError Fix

**BUG-002:** Update Rule API Error
- **Issue:** `AttributeError: 'dict' object has no attribute 'dict'`
- **Location:** `apps/api/dealbrain_api/api/rules.py` line 533
- **Root Cause:**
  ```python
  # Line 532-533 (BUGGY)
  if "conditions" in updates:
      updates["conditions"] = [c.dict() for c in updates["conditions"]]
  ```
  The `updates["conditions"]` is already a list of dicts (from `request.dict()`), not Pydantic objects
- **Fix:**
  ```python
  # Check if already dicts before converting
  if "conditions" in updates and updates["conditions"]:
      if hasattr(updates["conditions"][0], 'dict'):
          updates["conditions"] = [c.dict() for c in updates["conditions"]]
  # Same for actions
  if "actions" in updates and updates["actions"]:
      if hasattr(updates["actions"][0], 'dict'):
          updates["actions"] = [a.dict() for a in updates["actions"]]
  ```
- **Alternative (Cleaner):** Type hints in endpoint signature ensure correct type:
  ```python
  # In RuleUpdateRequest schema, change:
  conditions: list[ConditionSchema] | None  # Forces Pydantic parsing
  # Then dict conversion always works
  ```
- **Validation:** Rule update succeeds without errors, conditions/actions persist correctly

---

## Non-Functional Requirements

### Performance

**NFR-PERF-001:** Dropdown Rendering
- Dropdown options render in <100ms for lists up to 200 items
- Virtualize dropdown lists if >200 items (rare for field options)
- Debounce search input at 150ms (already implemented)

**NFR-PERF-002:** Managed Field Edits
- Save managed field change in <300ms
- Show loading indicator if >200ms
- Rollback UI immediately on error (<50ms)

### Accessibility

**NFR-A11Y-001:** Tooltips
- Tooltip content announced by screen readers (use `aria-describedby`)
- Keyboard users can trigger tooltip with focus (not just hover)
- Tooltip dismissible with Escape key
- Color contrast ratio >4.5:1 (WCAG AA)

**NFR-A11Y-002:** View Toggle
- Toggle keyboard accessible (Tab to focus, Space/Enter to switch)
- ARIA label: "Valuation view mode toggle"
- Announce view change to screen readers

### Browser Support

**NFR-BROWSER-001:** Same as existing
- Chrome/Edge 100+, Firefox 100+, Safari 15+
- Dropdown sizing uses modern CSS (grid, flexbox) - no legacy support

---

## Success Metrics

### Usability Metrics
- **Field Edit Success Rate:** >95% of managed field edits save without error
- **Tooltip Engagement:** 60% of users hover tooltips in first session
- **Basic View Adoption:** 70% of new rules created in Basic view
- **Dropdown Readability:** 0 user complaints about truncated options (current: ~3/week)

### Technical Metrics
- **Bug Resolution:** 0 React key warnings, 0 AttributeError on rule updates
- **Performance:** Dropdown render <100ms, managed field save <300ms (95th percentile)
- **Compatibility:** 100% of Basic rules convert to Advanced without data loss

### Quality Metrics
- **Regression:** 0 new bugs introduced in listings table, dropdown components
- **Accessibility:** WCAG AA compliance maintained (contrast, keyboard nav, ARIA)

---

## Out of Scope

Explicitly excluded from this phase:

1. **Advanced Valuation Features:**
   - Scheduled rule activation
   - Multi-ruleset comparison
   - Valuation history/audit trail

2. **Complex Field Enhancements:**
   - Bulk field editing
   - Field dependencies/conditional display
   - Advanced validation rules (regex, custom functions)

3. **UI Overhaul:**
   - Complete redesign of valuation page
   - Mobile-specific optimizations
   - Dark mode (deferred to design system update)

---

## Dependencies

### Technical Dependencies
- Existing Radix UI components (Popover, Tooltip)
- React Hook Form (already in use for modals)
- TanStack Table (for inline editing)
- Backend API endpoints (no new endpoints required)

### Data Dependencies
- EntityField descriptions (may need to populate for existing fields)
- Managed field metadata (add descriptions for CPU, GPU, RAM, Storage)

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Basic view too limiting, users still use Advanced | Medium | Medium | Track usage analytics, iterate on Basic features based on feedback |
| Dropdown width calculation causes layout shifts | Medium | Low | Use CSS containment, measure on first render only, cache widths |
| Managed field edits break existing workflows | High | Low | Comprehensive testing, feature flag for rollback, staged rollout |
| Tooltip performance issues with many columns | Low | Low | Lazy-load descriptions, virtualize tooltip rendering |
| Basic→Advanced conversion loses data | High | Very Low | Strict validation, lossless conversion logic, extensive unit tests |

---

## Implementation Phases

### Phase 1: Bug Fixes (Critical)
1. Fix React key warnings in valuation builders
2. Fix AttributeError in rule update endpoint
3. Comprehensive testing of rule CRUD operations

### Phase 2: Quick Wins
1. Enable managed field editing (listings table)
2. Add column header tooltips (all tables)
3. Standardize dropdown widths (all dropdowns)

### Phase 3: Basic View
1. Design Basic view UI mockups
2. Implement Basic condition builder
3. Implement Basic action builder (manual valuation)
4. Add view toggle and data conversion logic
5. User testing and refinement

---

## Appendix

### A. Managed Field Descriptions (Reference)

Suggested descriptions for tooltips:

- **CPU:** "The processor model (Intel/AMD) powering this system"
- **GPU:** "Discrete graphics card, if present (blank for integrated graphics)"
- **RAM (GB):** "System memory capacity in gigabytes"
- **Primary Storage (GB):** "Main drive capacity in gigabytes (SSD/HDD/NVMe)"
- **Storage Type:** "Primary drive technology (SSD, NVMe, HDD, eMMC)"
- **Adjusted Price:** "Final valuation after applying active ruleset rules"
- **Condition:** "Physical state of the listing (New, Refurbished, Used)"

### B. Basic View Wireframe Sketch

```
┌─────────────────────────────────────────────────┐
│ Create Valuation Rule          [ Basic | Advanced ]  [X] │
├─────────────────────────────────────────────────┤
│ Rule Name: [________________________]           │
│                                                 │
│ When these conditions match:                    │
│ Logical Operator: [Match ALL ▾]                │
│ ┌─────────────────────────────────────────┐   │
│ │ Field       │ Operator │ Value    │ [x] │   │
│ │ RAM (GB)    │ ≥        │ 16       │ [x] │   │
│ │ Condition   │ equals   │ New      │ [x] │   │
│ └─────────────────────────────────────────┘   │
│ [+ Add Condition]                               │
│                                                 │
│ Set component value:                            │
│ ○ Fixed Value   ● Quantity-Based               │
│                                                 │
│ $ [3] per [1] GB                               │
│                                                 │
│ Condition Multipliers:                          │
│ New: 1.0 | Refurbished: 0.75 | Used: 0.6      │
│                                                 │
│                              [Cancel] [Save Rule] │
└─────────────────────────────────────────────────┘
```

### C. API Changes Summary

**No new endpoints required.** All features use existing APIs:

1. **Managed Field Edits:** `PATCH /api/v1/listings/{id}` (already supports all fields)
2. **Field Descriptions:** `GET /api/v1/entity-fields` (description field exists)
3. **Valuation Rules:** `PUT /api/v1/valuation-rules/{id}` (fix bug, no schema change)

**Schema Updates:**
- None required—all features supported by current models
- May add descriptions to existing EntityField records (data migration, not schema)
