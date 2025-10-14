# E2E Test Scenarios: Baseline Rule Hydration

**Status:** Deferred - To be implemented in future testing sprint
**Date:** 2025-10-14
**Related:** [Implementation Plan](../project_plans/valuation-rules/basic-to-advanced-transition/basic-to-advanced-implementation-plan.md), [PRD](../project_plans/valuation-rules/basic-to-advanced-transition/basic-to-advanced-transition-prd.md), [ADR-0003](../architecture/adr/0003-baseline-rule-hydration-strategy.md)

## Overview

This document outlines the end-to-end (E2E) test scenarios for the baseline rule hydration feature. These tests should be implemented when the project adopts an E2E testing framework (Playwright or Cypress).

**Purpose:** Ensure the complete user journey for hydrating baseline rules when switching from Basic to Advanced mode works correctly across the entire stack (frontend, API, database).

## Prerequisites

### Testing Framework Requirements
- E2E testing framework installed (Playwright recommended, Cypress alternative)
- Test database with seed data
- Authenticated test user session
- Sample ruleset with baseline placeholder rules

### Test Data Setup
Before running these tests, ensure:
1. At least one active ruleset with baseline placeholder rules exists
2. Placeholder rules have `baseline_placeholder: true` in metadata
3. Placeholder rules include various field types:
   - Enum multiplier (e.g., DDR Generation)
   - Formula (e.g., RAM Capacity calculation)
   - Fixed value (e.g., Base depreciation)
4. Test listings exist to verify valuation impact

---

## Test Scenarios

### Scenario 1: Hydration Banner Display

**Test ID:** E2E-HYDRATE-001
**Priority:** High
**User Story:** US-1 (View Baseline Rules in Advanced Mode)

**Test Steps:**
1. Navigate to `/valuation-rules` page
2. Select a ruleset with non-hydrated baseline rules
3. Verify Basic mode is active (default)
4. Click "Advanced" mode toggle

**Expected Results:**
- Hydration banner appears at top of page with:
  - Info icon
  - Title: "Baseline Rules Need Preparation"
  - Description explaining need for hydration
  - Button: "Prepare Baseline Rules for Editing"
  - Button is enabled (not disabled)
- Rules table shows placeholder rules with:
  - 0 conditions
  - Actions with blank/zero values
  - Correct priority and names

**Acceptance Criteria:**
- [ ] Banner is visible in Advanced mode
- [ ] Banner is NOT visible in Basic mode
- [ ] Button text is clear and actionable
- [ ] Banner styling matches design system (Alert component)

**Screenshot Points:**
- Advanced mode with hydration banner visible
- Placeholder rules in collapsed state

---

### Scenario 2: Hydration Process - Loading State

**Test ID:** E2E-HYDRATE-002
**Priority:** High
**User Story:** US-2 (Edit Baseline Rules in Advanced Mode)

**Test Steps:**
1. Complete Scenario 1 (navigate to Advanced mode with banner)
2. Click "Prepare Baseline Rules for Editing" button
3. Observe UI during hydration process

**Expected Results:**
- Button immediately enters loading state:
  - Spinner icon appears
  - Button text changes to "Preparing Rules..."
  - Button becomes disabled
- Banner remains visible during process
- No error messages appear
- Page does not navigate away

**Acceptance Criteria:**
- [ ] Loading state activates within 100ms of click
- [ ] Button is disabled during loading
- [ ] Spinner animation is smooth
- [ ] User cannot double-click to trigger multiple hydrations

**Screenshot Points:**
- Button in loading state with spinner

---

### Scenario 3: Successful Hydration - Banner Dismissal

**Test ID:** E2E-HYDRATE-003
**Priority:** High
**User Story:** US-2 (Edit Baseline Rules in Advanced Mode)

**Test Steps:**
1. Complete Scenario 2 (trigger hydration)
2. Wait for hydration to complete (typically <2 seconds)
3. Observe UI changes post-hydration

**Expected Results:**
- Success toast notification appears with:
  - Title: "Baseline Rules Prepared"
  - Message showing counts (e.g., "Created 18 rules from 12 baseline fields")
- Hydration banner disappears
- Rules table refreshes and shows expanded rules:
  - Rules now have conditions (for enum types)
  - Actions have non-zero values
  - Multiple rules created for enum fields (e.g., DDR3, DDR4, DDR5)
- Page remains in Advanced mode

**Acceptance Criteria:**
- [ ] Toast appears within 500ms of completion
- [ ] Banner is removed from DOM
- [ ] Rules list updates automatically (no manual refresh needed)
- [ ] Rule count increases as expected

**Screenshot Points:**
- Success toast notification
- Advanced mode without banner showing expanded rules

---

### Scenario 4: Expanded Rules Display

**Test ID:** E2E-HYDRATE-004
**Priority:** High
**User Story:** US-1 (View Baseline Rules in Advanced Mode)

**Test Steps:**
1. Complete Scenario 3 (successful hydration)
2. Locate a previously placeholder enum rule (e.g., "DDR Generation")
3. Verify expanded rules structure

**Expected Results:**
For enum multiplier fields:
- Original placeholder rule is NOT visible (marked inactive)
- Multiple new rules appear with pattern: "{Field Name}: {Enum Value}"
  - Example: "DDR Generation: DDR3", "DDR Generation: DDR4", "DDR Generation: DDR5"
- Each expanded rule shows:
  - 1 condition: `field = enum_value`
  - 1 action: Multiplier with converted value (e.g., 0.7 → 70.0)
- Rules are grouped visually in same Rule Group

For formula fields:
- Single rule with formula action
- No conditions (always applies)

For fixed value fields:
- Single rule with fixed_value action
- Value populated from metadata

**Acceptance Criteria:**
- [ ] Enum fields expand to correct number of rules
- [ ] Condition field paths are correct
- [ ] Action values match original multipliers
- [ ] Rule names are descriptive

**Screenshot Points:**
- Expanded enum rules (all variants visible)
- Formula rule with formula displayed
- Fixed value rule

---

### Scenario 5: Edit Hydrated Rule

**Test ID:** E2E-HYDRATE-005
**Priority:** High
**User Story:** US-2 (Edit Baseline Rules in Advanced Mode)

**Test Steps:**
1. Complete Scenario 4 (view expanded rules)
2. Click "Edit" button on one of the hydrated rules
3. Make changes:
   - Modify condition value
   - Update action value
   - Change rule name
4. Save changes
5. Verify updates persist

**Expected Results:**
- Rule builder modal opens with pre-filled values
- All fields are editable (not read-only)
- Changes save successfully
- Updated rule displays new values in rules table
- No error messages or warnings about editing hydrated rules

**Acceptance Criteria:**
- [ ] Modal opens correctly
- [ ] Fields are pre-populated with current values
- [ ] Save button is enabled
- [ ] Changes persist after page refresh
- [ ] Audit trail records the edit

**Screenshot Points:**
- Rule builder modal with hydrated rule loaded
- Updated rule in table after save

---

### Scenario 6: Verify Foreign Key Rules Hidden

**Test ID:** E2E-HYDRATE-006
**Priority:** Medium
**User Story:** US-1 (View Baseline Rules in Advanced Mode)

**Test Steps:**
1. Complete Scenario 3 (successful hydration)
2. Check for foreign key rules (RAM Spec, GPU rules)
3. Verify they are not displayed in Advanced mode

**Expected Results:**
- Rules with `is_foreign_key_rule: true` in metadata do NOT appear in rules table
- Rule counts exclude foreign key rules
- No visual clutter from system-managed rules

**Optional Enhancement:**
- If "Show System Rules" toggle exists, verify:
  - Toggle is off by default
  - Turning it on reveals foreign key rules
  - Foreign key rules are marked with a badge/icon

**Acceptance Criteria:**
- [ ] Foreign key rules not visible by default
- [ ] Rule count reflects only user-editable rules
- [ ] (Optional) Toggle reveals system rules when enabled

**Screenshot Points:**
- Advanced mode without foreign key rules
- (Optional) Advanced mode with "Show System Rules" enabled

---

### Scenario 7: Switch Back to Basic Mode

**Test ID:** E2E-HYDRATE-007
**Priority:** High
**User Story:** US-3 (Sync Basic Mode After Advanced Edits)

**Test Steps:**
1. Complete Scenario 5 (edit hydrated rule in Advanced mode)
2. Click "Basic" mode toggle
3. Observe Basic mode display

**Expected Results:**
- Mode switches to Basic successfully
- Hydrated baseline fields show one of:
  - **Option A (Read-only):** Display current values with "Managed in Advanced Mode" badge/label
  - **Option B (Warning):** Show warning message: "This ruleset has been edited in Advanced mode. Some features may not be available in Basic mode."
- Override inputs may be disabled for hydrated fields
- Non-hydrated fields (if any) remain editable

**Acceptance Criteria:**
- [ ] No errors when switching modes
- [ ] Clear indication that rules are managed in Advanced mode
- [ ] User understands they need to use Advanced mode for editing
- [ ] No data loss or corruption

**Screenshot Points:**
- Basic mode showing "Managed in Advanced Mode" indicator
- Warning banner (if applicable)

---

### Scenario 8: Idempotency - Re-hydrate Attempt

**Test ID:** E2E-HYDRATE-008
**Priority:** Medium
**Functional Requirement:** Hydration should be idempotent

**Test Steps:**
1. Complete Scenario 3 (successful hydration)
2. Manually trigger hydration again via API (if endpoint accessible in UI)
   - OR: Reset data and repeat Scenario 1-3 with same ruleset
3. Verify behavior

**Expected Results:**
- Hydration service detects already-hydrated rules (via `hydrated: true` metadata)
- No duplicate rules are created
- Response indicates "0 rules hydrated" or "Already hydrated"
- No errors occur

**Acceptance Criteria:**
- [ ] No duplicate rules after second hydration
- [ ] Database record count unchanged
- [ ] Appropriate message returned (if exposed in UI)

**Screenshot Points:**
- (If applicable) Response message for already-hydrated ruleset

---

### Scenario 9: Error Handling - Hydration Failure

**Test ID:** E2E-HYDRATE-009
**Priority:** Medium
**User Story:** Error recovery

**Test Steps:**
1. Navigate to Advanced mode with placeholder rules
2. Simulate error condition (e.g., disconnect network, invalid data)
3. Click "Prepare Baseline Rules for Editing"
4. Observe error handling

**Expected Results:**
- Error toast appears with:
  - Title: "Hydration Failed"
  - Error message (user-friendly, not raw stack trace)
  - Variant: Destructive (red styling)
- Hydration banner remains visible
- Button returns to enabled state (can retry)
- Rules table shows original placeholder rules (no partial hydration)

**Acceptance Criteria:**
- [ ] Error is caught and displayed gracefully
- [ ] No partial hydration (transaction rollback)
- [ ] User can retry hydration
- [ ] Error is logged for debugging

**Screenshot Points:**
- Error toast notification
- Banner still visible after error

---

### Scenario 10: Valuation Impact - Before and After Hydration

**Test ID:** E2E-HYDRATE-010
**Priority:** Medium
**Functional Requirement:** Hydration should NOT change valuation results

**Test Steps:**
1. Navigate to Listings page
2. Select a test listing with known base price
3. Note the adjusted price and valuation breakdown (before hydration)
4. Navigate to Valuation Rules page
5. Complete Scenario 3 (hydrate baseline rules)
6. Return to Listings page
7. Re-evaluate the same test listing
8. Compare adjusted price and breakdown

**Expected Results:**
- Adjusted price remains EXACTLY the same
- Valuation breakdown shows:
  - Same total adjustment amount
  - Possibly different rule names (expanded rules instead of placeholders)
  - Same individual adjustment amounts per field
- No valuation calculation changes introduced by hydration

**Acceptance Criteria:**
- [ ] Adjusted price identical (to 2 decimal places)
- [ ] Total adjustment identical
- [ ] Individual field adjustments match
- [ ] Breakdown structure is valid

**Screenshot Points:**
- Valuation breakdown before hydration
- Valuation breakdown after hydration (side-by-side comparison)

---

## Additional Test Considerations

### Performance Tests
- **Hydration Speed:** Measure time for hydration of various ruleset sizes
  - Small ruleset (10 rules): <1 second
  - Medium ruleset (50 rules): <3 seconds
  - Large ruleset (100+ rules): <5 seconds
- **UI Responsiveness:** Ensure UI remains responsive during hydration

### Accessibility Tests
- **Keyboard Navigation:** All hydration flow accessible via keyboard
- **Screen Reader:** Banner and button properly announced
- **Focus Management:** Focus moves appropriately after hydration

### Cross-Browser Tests
- Test on Chrome, Firefox, Safari, Edge
- Verify consistent behavior across browsers

### Mobile Responsiveness
- Test on mobile viewport sizes
- Verify banner displays correctly
- Ensure button is tappable

---

## Test Data Fixtures

### Sample Ruleset Structure
```json
{
  "id": 1,
  "name": "Test Baseline Ruleset",
  "priority": 10,
  "is_active": true,
  "rule_groups": [
    {
      "id": 10,
      "name": "RAM Adjustments",
      "category": "ram",
      "rules": [
        {
          "id": 101,
          "name": "DDR Generation",
          "conditions": [],
          "actions": [{
            "action_type": "multiplier",
            "value_usd": 0.0
          }],
          "metadata_json": {
            "baseline_placeholder": true,
            "field_type": "enum_multiplier",
            "valuation_buckets": {
              "ddr3": 0.7,
              "ddr4": 1.0,
              "ddr5": 1.3
            }
          }
        }
      ]
    }
  ]
}
```

### Expected Hydration Result
```json
{
  "status": "success",
  "ruleset_id": 1,
  "hydrated_rule_count": 1,
  "created_rule_count": 3,
  "hydration_summary": [
    {
      "original_rule_id": 101,
      "field_name": "DDR Generation",
      "field_type": "enum_multiplier",
      "expanded_rule_ids": [102, 103, 104]
    }
  ]
}
```

---

## Test Execution Checklist

When implementing these E2E tests:

- [ ] Set up test database with seed data
- [ ] Create fixture for baseline ruleset
- [ ] Implement Scenario 1-3 (critical path)
- [ ] Implement Scenario 4-6 (expanded rules validation)
- [ ] Implement Scenario 7 (mode switching)
- [ ] Implement Scenario 8-9 (edge cases and errors)
- [ ] Implement Scenario 10 (valuation verification)
- [ ] Add performance benchmarks
- [ ] Document test data setup in README
- [ ] Configure CI/CD pipeline to run E2E tests
- [ ] Create test report dashboard

---

## Maintenance Notes

### When to Update These Tests
- When hydration UI changes (banner text, button labels)
- When new field types are added
- When hydration logic changes
- After any breaking API changes

### Known Limitations
- Tests assume synchronous hydration (no background jobs)
- Tests do not cover dehydration (Phase 5 feature)
- Tests assume single-user environment (no concurrent hydration)

---

## References

- [Implementation Plan](../project_plans/valuation-rules/basic-to-advanced-transition/basic-to-advanced-implementation-plan.md) - Lines 693-708
- [PRD](../project_plans/valuation-rules/basic-to-advanced-transition/basic-to-advanced-transition-prd.md) - User Stories US-1, US-2, US-3
- [ADR-0003](../architecture/adr/0003-baseline-rule-hydration-strategy.md) - Hydration strategy decisions
- [Architecture Doc](../architecture/valuation-rules.md) - System overview

---

**Last Updated:** 2025-10-14
**Status:** Ready for E2E framework implementation
