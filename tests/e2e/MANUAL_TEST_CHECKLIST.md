# Manual Test Checklist for Entity CRUD Operations

Use this checklist to manually verify entity CRUD functionality if automated E2E tests cannot run.

---

## Prerequisites

- [ ] Backend API running on `http://localhost:8000`
- [ ] Frontend web server running on `http://localhost:3020`
- [ ] Database migrated and seeded with sample data
- [ ] Browser DevTools open (Console tab)

---

## US-1: Edit Entity Specification

### Test Case 1.1: Edit CPU Successfully

**Setup**:
1. [ ] Navigate to `/catalog/cpus`
2. [ ] Click on any CPU to view its detail page

**Test Steps**:
1. [ ] Verify CPU name and details are displayed in the header
2. [ ] Click the "Edit" button in the top-right corner
3. [ ] Verify the "Edit CPU" modal opens with current data pre-filled
4. [ ] Change the CPU name (add " - UPDATED" to the name)
5. [ ] Change the cores value (e.g., from 8 to 10)
6. [ ] Click "Save Changes" button

**Expected Results**:
- [ ] Modal closes after submission
- [ ] Success toast appears (e.g., "CPU updated successfully")
- [ ] Page header shows the new CPU name
- [ ] Specifications section shows the updated cores value
- [ ] No console errors

**Result**: ⬜ Pass | ⬜ Fail

**Notes**: _______________________________________

---

### Test Case 1.2: Validation Error Handling

**Setup**:
1. [ ] Navigate to any CPU detail page
2. [ ] Click "Edit" button

**Test Steps**:
1. [ ] Clear the CPU name field completely
2. [ ] Observe the form state

**Expected Results**:
- [ ] Error message appears below the name field (e.g., "This field is required")
- [ ] "Save Changes" button is disabled
- [ ] Field has red border or error styling

**Test Steps (continued)**:
3. [ ] Enter a valid CPU name
4. [ ] Observe the form state

**Expected Results**:
- [ ] Error message disappears
- [ ] "Save Changes" button is enabled
- [ ] Field returns to normal styling

**Result**: ⬜ Pass | ⬜ Fail

**Notes**: _______________________________________

---

### Test Case 1.3: Cancel Edit Without Saving

**Setup**:
1. [ ] Navigate to any CPU detail page
2. [ ] Note the current CPU name

**Test Steps**:
1. [ ] Click "Edit" button
2. [ ] Change the CPU name to something different
3. [ ] Click "Cancel" button

**Expected Results**:
- [ ] Modal closes
- [ ] Original CPU name is still displayed (no changes saved)
- [ ] No toast messages appear
- [ ] No console errors

**Result**: ⬜ Pass | ⬜ Fail

**Notes**: _______________________________________

---

## US-2: Delete Unused Entity

### Test Case 2.1: Delete CPU With No Listings

**Setup**:
1. [ ] Create a new CPU via `/global-fields` (Data tab > Add entry)
   - Name: "Test CPU for Deletion"
   - Manufacturer: "Test"
2. [ ] Navigate to its detail page

**Test Steps**:
1. [ ] Verify there is NO "Used in X listings" badge
2. [ ] Click the "Delete" button
3. [ ] Verify "Delete CPU" confirmation dialog appears
4. [ ] Verify dialog message mentions "Test CPU for Deletion"
5. [ ] Verify dialog warns "This action cannot be undone"
6. [ ] Verify NO confirmation input field is present (entity is unused)
7. [ ] Click the "Delete" button in the dialog

**Expected Results**:
- [ ] Dialog closes
- [ ] Redirect to `/catalog/cpus` (CPU list page)
- [ ] Success toast appears (e.g., "CPU deleted successfully")
- [ ] Deleted CPU no longer appears in the list
- [ ] No console errors

**Result**: ⬜ Pass | ⬜ Fail

**Notes**: _______________________________________

---

## US-3: Attempt Delete In-Use Entity

### Test Case 3.1: Show Usage Badge and Require Confirmation

**Setup**:
1. [ ] Navigate to any CPU detail page that has associated listings
   - OR create a listing via `/listings/new` with a specific CPU

**Test Steps**:
1. [ ] Verify "Used in X listing(s)" badge is visible near the CPU name
2. [ ] Note the number of listings (X)
3. [ ] Click the "Delete" button
4. [ ] Verify "Delete CPU" confirmation dialog appears

**Expected Results**:
- [ ] Dialog shows "Used in X Listing(s)" badge (with destructive/red styling)
- [ ] Dialog warns "currently used in X listing(s)"
- [ ] Dialog contains a confirmation input field
- [ ] Input field placeholder shows the exact CPU name
- [ ] "Delete" button in dialog is DISABLED

**Test Steps (continued)**:
5. [ ] Type incorrect text in the confirmation field (e.g., "wrong name")

**Expected Results**:
- [ ] "Delete" button remains DISABLED
- [ ] Input field may show error styling

**Test Steps (continued)**:
6. [ ] Clear the field and type the EXACT CPU name

**Expected Results**:
- [ ] "Delete" button becomes ENABLED
- [ ] Input field shows success styling

**Result**: ⬜ Pass | ⬜ Fail

**Notes**: _______________________________________

---

### Test Case 3.2: Prevent or Allow Deletion of In-Use Entity

**Setup**:
1. [ ] Use the same CPU from Test Case 3.1 (with listings)

**Test Steps**:
1. [ ] Click "Delete" button
2. [ ] Enter the exact CPU name in the confirmation field
3. [ ] Click the "Delete" button in the dialog
4. [ ] Observe the outcome

**Expected Results (if backend prevents deletion)**:
- [ ] Error toast appears (e.g., "Cannot delete: entity is used in X listings")
- [ ] Dialog closes OR remains open with error message
- [ ] CPU still exists (can navigate back to detail page)
- [ ] Listings still reference the CPU

**Expected Results (if backend allows cascade deletion)**:
- [ ] Success toast appears (e.g., "CPU deleted successfully")
- [ ] Redirect to CPU list page
- [ ] CPU no longer appears in list
- [ ] Associated listings no longer reference this CPU

**Result**: ⬜ Pass | ⬜ Fail

**Backend Behavior**: ⬜ Prevents deletion | ⬜ Allows cascade

**Notes**: _______________________________________

---

## US-4: Manage Entities from Global Fields

### Test Case 4.1: Navigate from Global Fields to Detail Page

**Setup**:
1. [ ] Navigate to `/global-fields`
2. [ ] Click "Data" tab

**Test Steps**:
1. [ ] Wait for the data grid to load
2. [ ] Locate any CPU row in the table
3. [ ] Note the CPU name and manufacturer shown in the row
4. [ ] Click the "View Details" link in the Actions column

**Expected Results**:
- [ ] Navigation to `/catalog/cpus/{id}`
- [ ] CPU detail page loads
- [ ] Page header shows the same CPU name
- [ ] Manufacturer matches the grid data
- [ ] All specifications are displayed
- [ ] No console errors

**Result**: ⬜ Pass | ⬜ Fail

**Notes**: _______________________________________

---

### Test Case 4.2: Create New CPU from Global Fields

**Setup**:
1. [ ] Navigate to `/global-fields`
2. [ ] Click "Data" tab

**Test Steps**:
1. [ ] Click "Add entry" button
2. [ ] Verify create modal/dialog opens
3. [ ] Fill in the form:
   - Name: "Global Fields Test CPU"
   - Manufacturer: "Test Mfg"
   - Cores: 8
   - Threads: 16
4. [ ] Click "Save" or "Create" button

**Expected Results**:
- [ ] Modal closes
- [ ] Success toast appears (e.g., "CPU created successfully")
- [ ] New CPU appears in the data grid
- [ ] CPU row shows "Global Fields Test CPU" and "Test Mfg"
- [ ] No console errors

**Test Steps (continued)**:
5. [ ] Click "View Details" on the newly created CPU

**Expected Results**:
- [ ] Navigation to detail page
- [ ] All entered data is displayed correctly
- [ ] CPU is fully functional (can edit, delete)

**Cleanup**:
- [ ] Delete the test CPU using the "Delete" button

**Result**: ⬜ Pass | ⬜ Fail

**Notes**: _______________________________________

---

### Test Case 4.3: Data Consistency Between Views

**Setup**:
1. [ ] Navigate to `/global-fields`
2. [ ] Click "Data" tab

**Test Steps**:
1. [ ] Locate any CPU row
2. [ ] Note the following data:
   - CPU Name: _________________
   - Manufacturer: _________________
   - Cores: _________________
3. [ ] Click "View Details"
4. [ ] Compare detail page data with noted values

**Expected Results**:
- [ ] CPU name on detail page matches grid
- [ ] Manufacturer matches
- [ ] Cores value matches
- [ ] All visible fields are consistent

**Test Steps (continued)**:
5. [ ] Click browser back button or navigate to `/global-fields`
6. [ ] Click "Data" tab
7. [ ] Verify the same CPU row still shows the same data

**Expected Results**:
- [ ] Data in grid is unchanged
- [ ] No data loss or corruption
- [ ] Grid state is preserved

**Result**: ⬜ Pass | ⬜ Fail

**Notes**: _______________________________________

---

## Accessibility Tests

### Test Case A1: Keyboard Navigation

**Setup**:
1. [ ] Navigate to any CPU detail page

**Test Steps**:
1. [ ] Press Tab key repeatedly
2. [ ] Observe focus indicator moving through elements
3. [ ] Tab until "Edit" button is focused
4. [ ] Press Enter key

**Expected Results**:
- [ ] Focus is visible on each element
- [ ] Tab order is logical (left-to-right, top-to-bottom)
- [ ] "Edit" button receives focus
- [ ] Pressing Enter opens the edit modal

**Test Steps (continued)**:
5. [ ] Press Tab to move through modal form fields
6. [ ] Press Escape key

**Expected Results**:
- [ ] Focus moves through form fields
- [ ] Each field is keyboard accessible
- [ ] Pressing Escape closes the modal
- [ ] Focus returns to the page (ideally to the Edit button)

**Result**: ⬜ Pass | ⬜ Fail

**Notes**: _______________________________________

---

### Test Case A2: Mobile Responsive Design

**Setup**:
1. [ ] Open browser DevTools (F12)
2. [ ] Toggle device emulation (Ctrl+Shift+M / Cmd+Shift+M)
3. [ ] Select "iPhone SE" or similar mobile device
4. [ ] Navigate to any CPU detail page

**Test Steps**:
1. [ ] Observe page layout
2. [ ] Scroll down the page
3. [ ] Click "Edit" button
4. [ ] Observe modal layout

**Expected Results**:
- [ ] Page content is readable (no horizontal scrolling)
- [ ] Header and title are visible
- [ ] "Edit" and "Delete" buttons are accessible
- [ ] Scrolling works smoothly
- [ ] Modal fits within viewport (or is scrollable)
- [ ] Modal form fields are accessible
- [ ] Buttons are touch-friendly (not too small)

**Test Steps (continued)**:
5. [ ] Rotate device to landscape (if possible in DevTools)

**Expected Results**:
- [ ] Layout adapts to landscape orientation
- [ ] No layout breaking or overflow

**Result**: ⬜ Pass | ⬜ Fail

**Notes**: _______________________________________

---

### Test Case A3: ARIA Labels and Screen Reader Support

**Setup**:
1. [ ] Navigate to any CPU detail page
2. [ ] Open browser DevTools > Elements tab

**Test Steps**:
1. [ ] Inspect the "Edit" button
2. [ ] Check for `aria-label` attribute
3. [ ] Inspect the "Delete" button
4. [ ] Check for `aria-label` attribute

**Expected Results**:
- [ ] Edit button has `aria-label="Edit [CPU Name]"` or similar
- [ ] Delete button has `aria-label="Delete [CPU Name]"` or similar
- [ ] Labels include the entity name for context
- [ ] Labels are descriptive for screen reader users

**Optional (if screen reader available)**:
5. [ ] Enable screen reader (NVDA, JAWS, VoiceOver)
6. [ ] Navigate to Edit button
7. [ ] Listen to announcement

**Expected Results**:
- [ ] Screen reader announces button purpose clearly
- [ ] Entity name is included in announcement

**Result**: ⬜ Pass | ⬜ Fail

**Notes**: _______________________________________

---

## Summary

| Test Case | Result | Notes |
|-----------|--------|-------|
| US-1.1: Edit CPU Successfully | ⬜ Pass / ⬜ Fail | |
| US-1.2: Validation Errors | ⬜ Pass / ⬜ Fail | |
| US-1.3: Cancel Edit | ⬜ Pass / ⬜ Fail | |
| US-2.1: Delete Unused Entity | ⬜ Pass / ⬜ Fail | |
| US-3.1: Show Usage Badge | ⬜ Pass / ⬜ Fail | |
| US-3.2: Prevent/Allow Delete | ⬜ Pass / ⬜ Fail | |
| US-4.1: Navigate from Global Fields | ⬜ Pass / ⬜ Fail | |
| US-4.2: Create from Global Fields | ⬜ Pass / ⬜ Fail | |
| US-4.3: Data Consistency | ⬜ Pass / ⬜ Fail | |
| A1: Keyboard Navigation | ⬜ Pass / ⬜ Fail | |
| A2: Mobile Responsive | ⬜ Pass / ⬜ Fail | |
| A3: ARIA Labels | ⬜ Pass / ⬜ Fail | |

**Total**: ___ / 12 Passed

---

## Issues Found

List any bugs or issues discovered during manual testing:

1. ___________________________________________
2. ___________________________________________
3. ___________________________________________
4. ___________________________________________
5. ___________________________________________

---

## Tester Information

- **Tester Name**: _______________________
- **Date**: _______________________
- **Browser**: _______________________ (version: _______)
- **OS**: _______________________
- **Screen Size**: _______________________
- **Notes**: _______________________________________

---

## Recommendations

After completing manual testing:

1. [ ] Review automated E2E tests in `/home/user/deal-brain/tests/e2e/entity-crud.spec.ts`
2. [ ] Compare manual results with test assertions
3. [ ] Update tests if new edge cases discovered
4. [ ] File bug reports for any failures
5. [ ] Consider additional test scenarios not covered

---

## Next Steps

- [ ] Run automated E2E tests when environment is ready
- [ ] Test other entity types (GPU, RAM Spec, Storage Profile, etc.)
- [ ] Test edge cases and error scenarios
- [ ] Perform load testing with many entities
- [ ] Test concurrent operations (multiple users)
