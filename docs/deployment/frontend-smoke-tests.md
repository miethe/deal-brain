---
title: "Frontend Smoke Tests"
description: "Manual frontend smoke test checklist for entity CRUD functionality"
audience: [qa, developers, devops]
tags: [testing, frontend, smoke-tests, deployment, manual-testing]
created: 2025-11-14
updated: 2025-11-14
category: "test-documentation"
status: published
related:
  - /docs/deployment/entity-crud-deployment-checklist.md
  - /scripts/deployment/smoke-tests.sh
  - /docs/testing/accessibility-testing-guide.md
---

# Frontend Smoke Tests

## Overview

This document provides manual smoke test steps for verifying the Entity CRUD frontend functionality after deployment. These tests cover critical user paths and should be executed in production (or staging) after deployment.

**Estimated Time**: 15-20 minutes
**Environment**: Production (or Staging)
**Prerequisites**: Browser with access to deployed web application

---

## Pre-Test Setup

### Environment Access

- [ ] Web application URL: _______________
- [ ] Login credentials (if required): _______________
- [ ] Browser: _______________
- [ ] Browser version: _______________

### Test Data Requirements

Ensure the following test data exists in the environment:
- [ ] At least 1 CPU in the catalog
- [ ] At least 1 GPU in the catalog
- [ ] At least 1 Profile in the catalog
- [ ] At least 1 PortsProfile in the catalog
- [ ] At least 1 RamSpec in the catalog
- [ ] At least 1 StorageProfile in the catalog
- [ ] At least 1 Listing using a CPU (for testing in-use validation)

---

## Critical User Paths

### Test 1: Homepage & Navigation

**Objective**: Verify basic application functionality and navigation

1. [ ] Navigate to homepage: `https://yourdomain.com/`
2. [ ] Verify page loads without errors
   - Check browser console (F12) for errors
   - Check network tab for failed requests
3. [ ] Verify navigation menu is accessible
4. [ ] Click "Catalog" or "Global Fields" link
5. [ ] Verify navigation works

**Expected Result**: Homepage loads successfully, navigation works, no console errors.

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

### Test 2: CPU Catalog List View

**Objective**: Verify CPU catalog list page loads correctly

1. [ ] Navigate to `/catalog/cpus`
2. [ ] Verify CPU list displays
3. [ ] Verify at least one CPU is shown
4. [ ] Verify CPU data is correct (name, manufacturer, etc.)
5. [ ] Check for any visual glitches or layout issues

**Expected Result**: CPU catalog page loads with list of CPUs, no errors.

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

### Test 3: CPU Detail Page

**Objective**: Verify CPU detail page loads and displays entity information

1. [ ] From CPU list, click on a CPU name or "View Details" link
2. [ ] Verify detail page loads: `/catalog/cpus/{id}`
3. [ ] Verify CPU details are displayed:
   - Name
   - Manufacturer
   - CPU Mark (if available)
   - Single-Thread Rating (if available)
   - Attributes (if any)
4. [ ] Verify "Edit" button is visible
5. [ ] Verify "Delete" button is visible

**Expected Result**: Detail page loads with complete CPU information, action buttons visible.

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

### Test 4: Edit CPU (Happy Path)

**Objective**: Verify edit functionality works correctly

1. [ ] On CPU detail page, click "Edit" button
2. [ ] Verify edit modal/form opens
3. [ ] Verify form is pre-populated with current CPU data
4. [ ] Modify a non-critical field (e.g., "Notes")
   - Original value: _______________
   - New value: _______________
5. [ ] Click "Save" button
6. [ ] Verify success toast notification appears
7. [ ] Verify modal closes automatically
8. [ ] Verify page shows updated data (optimistic update)
9. [ ] Refresh page (F5)
10. [ ] Verify updated data persists after refresh

**Expected Result**: Edit saves successfully, optimistic update works, data persists.

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

### Test 5: Edit CPU (Validation Error)

**Objective**: Verify validation errors are handled correctly

1. [ ] On CPU detail page, click "Edit" button
2. [ ] Clear the "Name" field (required field)
3. [ ] Click "Save" button
4. [ ] Verify validation error message appears
5. [ ] Verify form does NOT close
6. [ ] Verify error message is clear and actionable
7. [ ] Click "Cancel" button
8. [ ] Verify modal closes
9. [ ] Verify no changes were saved

**Expected Result**: Validation prevents save, clear error shown, cancel works.

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

### Test 6: Edit CPU (Cancel)

**Objective**: Verify cancel functionality works correctly

1. [ ] On CPU detail page, click "Edit" button
2. [ ] Modify a field (e.g., "Notes")
3. [ ] Click "Cancel" button
4. [ ] Verify modal closes
5. [ ] Verify no changes were saved (page shows original data)
6. [ ] Verify no error or success messages appear

**Expected Result**: Cancel discards changes without saving.

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

### Test 7: Delete CPU (In-Use Prevention)

**Objective**: Verify delete protection for in-use entities

1. [ ] Navigate to a CPU that is used in at least one listing
   - Hint: Check CPU with listings in database or use test data
2. [ ] Click "Delete" button
3. [ ] Verify confirmation dialog appears
4. [ ] Verify dialog shows usage warning:
   - "This CPU is used in X listing(s)"
   - "Cannot delete CPU that is in use"
5. [ ] Verify delete action is disabled or shows clear error
6. [ ] Click "Close" or "Cancel"
7. [ ] Verify dialog closes
8. [ ] Verify CPU still exists (not deleted)

**Expected Result**: Cannot delete in-use CPU, clear warning shown.

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

### Test 8: Delete CPU (Unused - Success)

**Objective**: Verify delete functionality for unused entities

**Prerequisites**: Create a test CPU that is NOT used in any listings

1. [ ] Navigate to unused CPU detail page
2. [ ] Click "Delete" button
3. [ ] Verify confirmation dialog appears
4. [ ] Verify dialog shows:
   - CPU name and confirmation message
   - "Are you sure you want to delete?"
   - No usage warnings
5. [ ] Type confirmation (if required): _______________
6. [ ] Click "Delete" or "Confirm" button
7. [ ] Verify success toast notification appears
8. [ ] Verify redirect to CPU list page
9. [ ] Verify deleted CPU no longer appears in list

**Expected Result**: Unused CPU deleted successfully, redirects to list.

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

### Test 9: Global Fields - Entity List

**Objective**: Verify Global Fields UI shows all entity types

1. [ ] Navigate to `/global-fields`
2. [ ] Verify page loads
3. [ ] Verify entity type selector/tabs visible
4. [ ] Select "CPU" entity type
5. [ ] Verify CPU list displays
6. [ ] Select "GPU" entity type
7. [ ] Verify GPU list displays
8. [ ] Verify all entity types available:
   - [ ] CPU
   - [ ] GPU
   - [ ] Profile
   - [ ] PortsProfile
   - [ ] RamSpec
   - [ ] StorageProfile

**Expected Result**: Global Fields page shows all entity types, switching works.

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

### Test 10: Global Fields - View Details Link

**Objective**: Verify "View Details" links navigate correctly

1. [ ] On Global Fields page, select "CPU" entity type
2. [ ] Verify "View Details" link/button visible for each CPU row
3. [ ] Click "View Details" on a CPU
4. [ ] Verify navigation to `/catalog/cpus/{id}` detail page
5. [ ] Verify detail page loads correctly
6. [ ] Navigate back to Global Fields
7. [ ] Repeat for at least 2 other entity types (e.g., GPU, Profile)

**Expected Result**: "View Details" links navigate to correct detail pages.

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

### Test 11: Other Entity Types (Spot Check)

**Objective**: Verify CRUD functionality for other entity types

**Repeat Tests 3-8 for at least 2 other entity types:**

#### Entity Type: GPU

- [ ] Detail page loads (Test 3)
- [ ] Edit works (Test 4)
- [ ] Cancel works (Test 6)
- [ ] Delete protection works if in-use (Test 7)

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

#### Entity Type: Profile

- [ ] Detail page loads (Test 3)
- [ ] Edit works (Test 4)
- [ ] Cancel works (Test 6)
- [ ] Delete protection works if in-use (Test 7)

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

## Browser Compatibility Tests

**Objective**: Verify functionality across major browsers

### Chrome (Latest)

- [ ] Homepage loads
- [ ] Edit CPU works
- [ ] Delete dialog works
- [ ] No console errors

**Browser Version**: _______________
**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

### Firefox (Latest)

- [ ] Homepage loads
- [ ] Edit CPU works
- [ ] Delete dialog works
- [ ] No console errors

**Browser Version**: _______________
**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

### Safari (Latest)

- [ ] Homepage loads
- [ ] Edit CPU works
- [ ] Delete dialog works
- [ ] No console errors

**Browser Version**: _______________
**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

### Edge (Latest)

- [ ] Homepage loads
- [ ] Edit CPU works
- [ ] Delete dialog works
- [ ] No console errors

**Browser Version**: _______________
**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

## Responsive Design Tests

**Objective**: Verify UI works on different screen sizes

### Desktop (1920x1080)

- [ ] Layout renders correctly
- [ ] All buttons accessible
- [ ] Modals centered and sized appropriately
- [ ] No horizontal scrolling

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

### Tablet (768x1024)

- [ ] Layout adapts to smaller screen
- [ ] Navigation menu accessible
- [ ] Edit modal fits screen
- [ ] Touch targets appropriately sized

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

### Mobile (375x667)

- [ ] Mobile layout renders
- [ ] Navigation hamburger menu works (if applicable)
- [ ] Edit form usable on small screen
- [ ] Delete dialog readable
- [ ] No overlapping elements

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

## Accessibility Tests (Quick Check)

**Objective**: Verify basic accessibility compliance

### Keyboard Navigation

1. [ ] Navigate to CPU detail page
2. [ ] Use Tab key to navigate to "Edit" button
3. [ ] Press Enter to open edit modal
4. [ ] Use Tab to navigate through form fields
5. [ ] Use Shift+Tab to navigate backwards
6. [ ] Use Escape key to close modal
7. [ ] Verify focus indicators visible throughout

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

### Screen Reader (Optional)

If screen reader available (NVDA, JAWS, VoiceOver):

1. [ ] Navigate to edit button
2. [ ] Verify button announced as "Edit CPU" or similar
3. [ ] Open edit modal
4. [ ] Verify form labels read correctly
5. [ ] Verify validation errors announced

**Status**: [ ] Pass [ ] Fail [ ] Not Tested
**Notes**: _______________

---

## Performance Tests (Quick Check)

**Objective**: Verify acceptable performance

### Page Load Times

1. [ ] Open browser DevTools (F12)
2. [ ] Navigate to Network tab
3. [ ] Disable cache
4. [ ] Load `/catalog/cpus`
5. [ ] Record "DOMContentLoaded" time: _______________
6. [ ] Record "Load" time: _______________
7. [ ] Verify load time < 3 seconds

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

### Edit Modal Responsiveness

1. [ ] Click "Edit" button
2. [ ] Verify modal opens in < 500ms
3. [ ] Type in form field
4. [ ] Verify no input lag
5. [ ] Click "Save"
6. [ ] Verify success toast appears in < 1 second

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

## Error Handling Tests

### Network Error Simulation

**Prerequisites**: Browser DevTools with network throttling

1. [ ] Open DevTools → Network tab
2. [ ] Set throttling to "Offline"
3. [ ] Click "Edit" on a CPU
4. [ ] Modify a field
5. [ ] Click "Save"
6. [ ] Verify error message appears:
   - "Network error" or similar
   - Clear, actionable message
7. [ ] Verify form does NOT close
8. [ ] Verify data NOT corrupted
9. [ ] Re-enable network
10. [ ] Click "Save" again
11. [ ] Verify save succeeds

**Status**: [ ] Pass [ ] Fail
**Notes**: _______________

---

## Summary

### Overall Results

- **Total Tests**: _______________
- **Passed**: _______________
- **Failed**: _______________
- **Not Tested**: _______________

### Critical Issues Found

List any critical issues that should block deployment:

1. _______________
2. _______________
3. _______________

### Non-Critical Issues Found

List any minor issues that can be addressed post-deployment:

1. _______________
2. _______________
3. _______________

### Sign-Off

**Tested By**: _______________
**Date**: _______________
**Environment**: _______________
**Deployment Approved**: [ ] Yes [ ] No (specify blockers above)

---

## Appendix: Common Issues & Resolutions

### Issue: Edit modal not opening

**Symptoms**: Clicking "Edit" does nothing
**Check**:
- Browser console for JavaScript errors
- Network tab for failed API requests
- Verify API is running and accessible

**Resolution**:
- Clear browser cache and reload
- Verify API URL environment variable correct
- Check CORS configuration

### Issue: Delete confirmation not showing usage count

**Symptoms**: Dialog shows "0 listings" when entity is in use
**Check**:
- Verify `/v1/catalog/cpus/{id}/listings` endpoint returns data
- Check browser console for errors

**Resolution**:
- Verify backend usage check service is working
- Check database for foreign key relationships

### Issue: Optimistic update shows old data

**Symptoms**: Edit saves but UI shows old values
**Check**:
- Browser console for cache errors
- Network tab for API response

**Resolution**:
- Clear browser cache
- Verify React Query cache invalidation working
- Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

### Issue: Toast notifications not appearing

**Symptoms**: Success/error messages not shown
**Check**:
- Browser console for errors
- Verify toast library loaded

**Resolution**:
- Check that toast provider is correctly configured
- Verify CSS for toast library loaded
- Check z-index conflicts with other UI elements
