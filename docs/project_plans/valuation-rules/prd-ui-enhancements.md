# Product Requirements Document: UI/UX Enhancements

**Version:** 1.0
**Date:** October 2, 2025
**Status:** Draft
**Author:** Lead Architect

---

## Executive Summary

This PRD defines critical UI/UX enhancements across three primary domains: Valuation Rules management, Table Components optimization, and Global Fields functionality. These improvements will transform Deal Brain from a data-heavy catalog tool into a polished, production-grade valuation platform with Apple-tier user experience.

**Strategic Goals:**
- Enable full CRUD operations for valuation rule hierarchies (Rulesets → Groups → Rules)
- Establish a consistent, reusable modal/dialog design system
- Optimize table performance and UX for large datasets
- Streamline dropdown field management with inline creation
- Add real-time valuation visibility in listings

**Impact:** These enhancements eliminate current workflow blockers, reduce cognitive load, and establish scalable UI patterns for future features.

---

## Problem Statement

### Current Pain Points

1. **Valuation Rules Page**
   - Read-only interface prevents rule management workflows
   - No visibility into rule conditions/actions without backend access
   - Missing hierarchical CRUD: Users cannot add/edit Rule Groups or individual Rules
   - Inconsistent with other pages (Listings, Global Fields have full CRUD)

2. **Table Components**
   - Performance degrades with moderate datasets during column resizing
   - No dropdown support for RAM/Storage fields (only Storage Type has it)
   - No inline dropdown option creation—requires context switching to Global Fields
   - Missing column locking for horizontal scroll scenarios
   - Text truncation without visual feedback
   - Poor multi-pane layouts on pages with multiple tables
   - Fixed sidebar/navbar scroll with content (should remain static)

3. **Global Fields**
   - Confusing "Multi-select" as separate field type instead of checkbox option
   - Cannot define dropdown options during field creation
   - Core fields not editable (limits metadata improvements)

4. **Listings Table**
   - No Valuation column showing calculated adjusted prices
   - Users must manually track which listings offer best value

---

## User Personas

### Primary: **Power User / Deal Hunter**
- **Goals:** Quickly identify best price-to-performance deals, customize valuation rules
- **Pain Points:** Cannot modify rules without reimporting data, slow table interactions
- **Success Metrics:** Can create custom rule groups in <2 minutes, sort by valuation instantly

### Secondary: **Admin / Curator**
- **Goals:** Maintain clean field definitions, ensure consistent data structure
- **Pain Points:** Cannot edit core fields, must leave current context to add dropdown options
- **Success Metrics:** Inline dropdown creation saves 80% of time, core field metadata editable

---

## Requirements

### 1. Valuation Rules Page Enhancements

#### 1.1 Hierarchical CRUD Interface

**FR-VR-001:** Three-level nested UI
- **Requirement:** Display Rulesets → Rule Groups → Rules in expandable/collapsible sections
- **Acceptance Criteria:**
  - Clicking a Ruleset expands to show its Rule Groups
  - Clicking a Rule Group shows its Rules
  - Each level shows summary count (e.g., "3 groups • 12 rules")
  - Default state: first ruleset expanded, others collapsed

**FR-VR-002:** Ruleset Management
- **Add:** "New Ruleset" button opens modal with fields:
  - Name (required, unique)
  - Description (optional, textarea)
  - Version (default "1.0.0")
  - Is Active (checkbox, default true)
- **Edit:** Pencil icon next to ruleset name opens same modal pre-filled
- **Delete:** Trash icon with confirmation dialog: "Delete '{name}'? This will remove all {count} rule groups and {count} rules."

**FR-VR-003:** Rule Group Management
- **Add:** "Add Group" button appears when ruleset expanded, modal fields:
  - Name (required, unique within ruleset)
  - Category (dropdown: "component", "condition", "market", "custom")
  - Description (optional)
  - Display Order (number, default 100)
  - Weight (number, default 1.0)
- **Edit/Delete:** Same pattern as rulesets

**FR-VR-004:** Rule Management
- **Add:** "Add Rule" button when group expanded, modal with tabs:
  - **Tab 1 - Details:**
    - Name (required)
    - Description
    - Priority (number)
    - Is Active (checkbox)
  - **Tab 2 - Conditions:**
    - Dynamic condition builder (see 1.2)
  - **Tab 3 - Actions:**
    - Dynamic action builder (see 1.3)
- **View:** Clicking rule name expands inline section showing:
  - Conditions as readable logic (e.g., "IF RAM ≥ 16GB AND Condition = New")
  - Actions as readable operations (e.g., "Deduct $8 per GB over 16GB")
- **Edit/Delete:** Inline edit/trash icons

#### 1.2 Condition Builder UI

**FR-VR-005:** Condition Form
- **Fields:**
  - Field Name (dropdown: listing attributes)
  - Field Type (auto-detected, read-only)
  - Operator (dropdown based on type):
    - String: equals, contains, starts_with, ends_with
    - Number: eq, gt, gte, lt, lte, between
    - Boolean: is_true, is_false
    - Enum: in_list, not_in_list
  - Value (input type matches field type)
  - Logical Operator (AND/OR for multiple conditions)
- **Multi-Condition Support:**
  - "Add Condition" button for AND/OR chains
  - Grouped conditions with visual indentation

#### 1.3 Action Builder UI

**FR-VR-006:** Action Form
- **Fields:**
  - Action Type (dropdown: "adjust_price", "set_score", "add_tag", "custom")
  - Metric (conditional: shows for score actions)
  - Value USD (number, for price adjustments)
  - Unit Type (dropdown: "fixed", "per_unit", "percentage")
  - Formula (advanced: code editor for custom formulas)
  - Modifiers JSON (advanced: collapsible JSON editor)
- **Multi-Action Support:**
  - "Add Action" button
  - Display order via drag handles

#### 1.4 Validation & Error Handling

**FR-VR-007:** Input Validation
- Unique name constraints at each level
- Required field enforcement
- Numeric range validation (weights 0.0-10.0, priorities 0-1000)
- Condition/action schema validation before save

**FR-VR-008:** Error States
- Inline error messages below invalid fields
- Modal-level error summary at top
- API error display with retry option
- Optimistic UI with rollback on failure

---

### 2. Modal Design System

#### 2.1 Unified Modal Component

**FR-MODAL-001:** Standardized Modal Shell
- **Component:** Enhanced `ModalShell` with variants:
  - Small (400px): Confirmations, simple forms
  - Medium (640px): Standard forms
  - Large (800px): Complex forms with tabs
  - Full (90vw): Data tables, complex workflows
- **Consistent Elements:**
  - Header: Title (text-xl font-semibold) + Description (text-sm text-muted-foreground)
  - Body: max-h-[70vh] with overflow-y-auto
  - Footer: Sticky with border-top, flex justify-between
  - Close: X button top-right + ESC key + click outside
- **Styling:** Inherits from existing `modal-shell.tsx` but adds variants

**FR-MODAL-002:** Modal Inheritance Strategy
- Base modal component handles:
  - Accessibility (ARIA labels, focus trap, keyboard nav)
  - Animation (fade-in 150ms, scale from 95% to 100%)
  - Responsive behavior (full-screen on mobile)
- Specialized modals extend base:
  - `ValuationRuleModal`: Tabs, condition/action builders
  - `GlobalFieldModal`: Dynamic field type options
  - `ListingFormModal`: Entity-specific validations

**FR-MODAL-003:** Form State Management
- Unsaved changes warning on close
- Field-level validation on blur
- Form-level validation on submit
- Loading states during async operations
- Success/error toast notifications post-submit

---

### 3. Table Component Enhancements

#### 3.1 Performance Optimization

**FR-TABLE-001:** Pagination Implementation
- **Default:** 50 rows per page
- **Options:** 25, 50, 100, 200, All
- **Behavior:**
  - Paginate when data exceeds 50 rows
  - Virtualization for "All" view with >100 rows
  - Preserve page on filter/sort changes

**FR-TABLE-002:** Column Resizing Optimization
- **Mechanism:** Debounced resize events (150ms)
- **Constraints:**
  - Min width: 80px (prevents text truncation)
  - Max width: 600px
  - Text wrapping enabled when min width reached
  - Visual indicator (dashed border) when at min width
- **Performance:** Resize only updates affected column, not entire table

**FR-TABLE-003:** Virtualization for Large Datasets
- **Trigger:** Auto-enable when >100 rows visible
- **Library:** Continue using `@tanstack/react-table` with virtual scrolling
- **Behavior:** Render visible rows + 10 overscan, recycle on scroll

#### 3.2 Dropdown Field Enhancements

**FR-TABLE-004:** Dropdown Fields for RAM/Storage
- **Fields:** RAM (GB), Primary Storage (GB)
- **Common Values:**
  - RAM: 4, 8, 16, 24, 32, 48, 64, 96, 128
  - Storage: 128, 256, 512, 1024, 2048, 4096
- **Behavior:** Editable dropdown (combobox) allows typing custom value

**FR-TABLE-005:** Inline Dropdown Option Creation
- **Trigger:** Type non-existent value in dropdown, press Enter
- **Modal:** "Add '{value}' to {field_name}?" with:
  - Value (pre-filled, editable)
  - "Add to Global Fields" checkbox (default true)
  - Cancel / Confirm buttons
- **Result:** Option immediately available, synced to backend
- **Scope:** Applies to ALL dropdown fields in app (tables, modals, forms)

#### 3.3 Column Locking

**FR-TABLE-006:** Sticky Columns
- **Default Locked:** First 2 columns (usually ID/Title) + Actions column
- **User Control:** Settings dropdown with "Lock Column" checkbox per column
- **Behavior:**
  - Locked columns use `position: sticky` with z-index layering
  - Left-locked: sticky left, Right-locked (Actions): sticky right
  - Visual separator (border-right) on locked columns
- **Persistence:** Save locked state to localStorage per table

#### 3.4 Multi-Pane Layout

**FR-TABLE-007:** Dynamic Pane Sizing
- **Algorithm:**
  - Detect all panes on page (data attribute `data-pane`)
  - Calculate min-height per pane: max(300px, content height up to 400px)
  - Distribute remaining viewport height proportionally
  - If total > viewport, allow page scroll (not pane scroll)
- **User Control:** Drag divider between panes to resize (persist to localStorage)

**FR-TABLE-008:** Static Sidebar/Navbar
- **Implementation:** `position: sticky; top: 0` for navbar, `position: fixed` for sidebar
- **Z-index:** navbar = 100, sidebar = 90, modals = 200
- **Responsive:** Sidebar collapses to hamburger on <1024px

---

### 4. Global Fields Enhancements

#### 4.1 Field Type Improvements

**FR-GF-001:** Multi-Select as Checkbox Option
- **Change:** Remove "Multi-select" from Type dropdown
- **Add:** "Allow Multiple Selections" checkbox below Type field
- **Behavior:**
  - When Type = "Dropdown" and checkbox enabled → saves as `multi_select`
  - Existing multi-select fields migrate to dropdown + checkbox
- **Validation:** Checkbox only enabled when Type = "Dropdown"

**FR-GF-002:** Dropdown Options Builder
- **UI:** When Type = "Dropdown", show "Options" section:
  - List of current options (draggable for reordering)
  - "Add Option" input with "+" button
  - Delete icon per option
  - "Import from CSV" button (paste comma-separated values)
- **Validation:** At least 1 option required for Dropdown type

#### 4.2 Core Field Editability

**FR-GF-003:** Editable Core Field Metadata
- **Locked Properties:** Entity, Key, Type (prevents breaking changes)
- **Editable Properties:**
  - Label
  - Description
  - Required status (with dependency check warning)
  - Validation rules
  - Options (for dropdown fields)
- **UI Indicator:** Lock icon next to disabled fields with tooltip explaining why

---

### 5. Listings Table Valuation Column

#### 5.1 Real-Time Valuation Display

**FR-LISTING-001:** Valuation Column
- **Position:** Insert after "Title" column, before "CPU"
- **Header:** "Valuation" with info tooltip: "Adjusted price based on active ruleset"
- **Cell Content:**
  - Primary: `adjusted_price_usd` formatted as currency
  - Secondary: Delta badge if different from `list_price_usd`:
    - Green badge: "-$50 (savings)" if adjusted < list
    - Red badge: "+$30 (premium)" if adjusted > list
- **Sorting:** Enabled, numeric sort
- **Filtering:** Numeric range filter (min/max inputs)

**FR-LISTING-002:** Valuation Breakdown Modal
- **Trigger:** Click on valuation cell value
- **Content:**
  - Listing title + thumbnail
  - Base price
  - Applied rules as expandable list:
    - Rule group → Rule name → Adjustment amount
  - Final adjusted price
  - "View Full Breakdown" link to dedicated breakdown page
- **Size:** Medium modal (640px)

**FR-LISTING-003:** Real-Time Updates
- **Behavior:**
  - Valuations recalculate when:
    - Listing data changes
    - Active ruleset changes
    - Rule within active ruleset modified
  - Use React Query invalidation to trigger refetch
  - Optimistic UI: Show loading spinner during recalc (if >500ms)

---

## Non-Functional Requirements

### Performance

**NFR-PERF-001:** Table Operations
- Column resize: <100ms response time
- Sort/filter: <200ms for datasets up to 1,000 rows
- Pagination load: <150ms per page

**NFR-PERF-002:** Modal Interactions
- Open/close animation: 150ms
- Form submit: <500ms for simple forms, <2s for complex (rules with many conditions)
- Validation: <50ms inline, <200ms on submit

### Accessibility

**NFR-A11Y-001:** WCAG 2.1 AA Compliance
- Keyboard navigation for all modals, tables, dropdowns
- ARIA labels on all interactive elements
- Focus management (trap in modals, restore on close)
- Screen reader announcements for dynamic content

### Usability

**NFR-UX-001:** Consistency
- All modals use `ModalShell` component
- All tables use `DataGrid` component
- Identical button styling across app
- Error messages follow toast pattern

**NFR-UX-002:** Feedback
- Loading states for all async operations
- Success toast on save (auto-dismiss 3s)
- Error toast on failure (persistent until dismissed)
- Optimistic UI with rollback on error

### Browser Support

**NFR-BROWSER-001:** Target Browsers
- Chrome/Edge 100+
- Firefox 100+
- Safari 15+
- No IE11 support required

---

## Success Metrics

### Adoption Metrics
- **Valuation Rule Creation:** 80% of users create custom rule within first week
- **Table Interaction:** Column resize usage >50% of sessions
- **Inline Dropdown Creation:** 60% reduction in Global Fields page visits

### Performance Metrics
- **Page Load:** Listings page <2s on 4G connection
- **Interaction:** Table operations <200ms at 95th percentile
- **Valuation Calculation:** <1s for listings with 10+ rules applied

### Quality Metrics
- **Errors:** <1% failed saves due to validation
- **Accessibility:** 0 critical WAVE errors
- **Consistency:** 100% modal/table components use shared system

---

## Out of Scope

The following are explicitly excluded from this phase:

1. **Advanced Rule Engine Features:**
   - Scheduled rule activation
   - A/B testing between rulesets
   - Machine learning-based rule suggestions

2. **Table Features:**
   - Bulk import/export from table context
   - Advanced pivoting/grouping (beyond single-column grouping)
   - Inline chart visualizations

3. **Mobile Optimization:**
   - This phase focuses on desktop (1024px+)
   - Mobile responsive design deferred to Phase 5

4. **Collaboration Features:**
   - Real-time collaborative editing
   - User-level permissions for rule editing
   - Change approval workflows

---

## Dependencies

### Technical Dependencies
- `@tanstack/react-table` v8.x (already in use)
- `@tanstack/react-query` v5.x (already in use)
- `shadcn/ui` components (dialog, dropdown-menu, etc.)
- Backend API endpoints (see Implementation Plan)

### External Dependencies
- No external services required
- Design system components extend existing patterns

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Performance degradation with large rulesets (100+ rules) | High | Medium | Implement pagination at group level, lazy-load conditions/actions |
| Rule validation complexity causes UX slowdown | Medium | High | Move complex validation to backend, show lightweight inline checks only |
| Inline dropdown creation conflicts with Global Fields | Medium | Low | Use optimistic UI, sync immediately via API, handle duplicates gracefully |
| Column locking breaks on table re-renders | High | Medium | Use React refs for DOM manipulation, test with React strict mode |
| Valuation recalculation triggers infinite loops | High | Low | Implement query deduplication, use stable query keys, add rate limiting |

---

## Appendix

### A. Wireframe References

*(Wireframes to be created in Figma/Excalidraw and linked here)*

- Valuation Rules page: 3-level hierarchy
- Rule creation modal: Tabbed interface
- Listings table: Valuation column + breakdown modal
- Global Fields: Multi-select checkbox + options builder

### B. API Endpoint Requirements

See [Implementation Plan](./implementation-plan-ui-enhancements.md) Section 3.2 for detailed API contracts.

### C. Component Hierarchy

```
ValuationRulesPage
├── RulesetList
│   ├── RulesetCard
│   │   ├── RuleGroupList
│   │   │   ├── RuleGroupCard
│   │   │   │   ├── RuleList
│   │   │   │   │   └── RuleCard
│   │   │   │   └── AddRuleButton → RuleFormModal
│   │   │   └── AddGroupButton → RuleGroupFormModal
│   │   └── RulesetActions
│   └── AddRulesetButton → RulesetFormModal
```

### D. Database Schema Changes

Minimal changes required—existing models support all features:
- `ValuationRuleset`, `ValuationRuleGroup`, `ValuationRuleV2` already exist
- `ValuationRuleCondition`, `ValuationRuleAction` already support complex structures
- `EntityField.options` column already stores dropdown options as JSON array

---

**Approval Signatures:**

- **Product Owner:** ___________________________ Date: ___________
- **Lead Architect:** ___________________________ Date: ___________
- **Tech Lead:** ___________________________ Date: ___________
