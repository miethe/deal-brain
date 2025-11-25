# Phase 1: Data Tab Performance Optimization - Testing Guide

**Version:** 1.0
**Date:** 2025-10-31
**Phase:** Phase 1 - Performance Optimization
**Status:** Ready for Testing

---

## Overview

This guide provides comprehensive testing procedures for validating Phase 1 performance optimizations. All tests should be performed before staging and production deployment.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Performance Baseline Measurements](#performance-baseline-measurements)
3. [Virtualization Testing](#virtualization-testing)
4. [Pagination Endpoint Testing](#pagination-endpoint-testing)
5. [Rendering Optimization Testing](#rendering-optimization-testing)
6. [Performance Monitoring Testing](#performance-monitoring-testing)
7. [Regression Testing](#regression-testing)
8. [Automated Testing](#automated-testing)
9. [Success Criteria Checklist](#success-criteria-checklist)

---

## Prerequisites

### Environment Setup

1. **Development Environment:**
   ```bash
   # Ensure all dependencies are installed
   make setup

   # Apply database migration
   make migrate

   # Start full stack
   make up
   ```

2. **Seed Data:**
   ```bash
   # Create test data with 1,000+ listings for performance testing
   poetry run python scripts/seed_sample_listings.py --count 1000
   ```

3. **Browser Requirements:**
   - Chrome/Chromium (recommended for DevTools)
   - Firefox Developer Edition (optional, for cross-browser testing)
   - Disable browser extensions during testing

4. **Tools:**
   - Chrome DevTools (Performance tab)
   - React DevTools (Profiler)
   - Network throttling capability
   - Screen reader (NVDA/JAWS for accessibility testing)

---

## Performance Baseline Measurements

### Establish Baseline Metrics

Before testing, establish baseline measurements for comparison.

#### 1. Initial Page Load

**Procedure:**
1. Open Chrome DevTools > Performance tab
2. Click "Record"
3. Navigate to `http://localhost:3020/dashboard/data`
4. Wait for page to fully load
5. Click "Stop"

**Measure:**
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Time to Interactive (TTI)
- Total DOM nodes
- JavaScript heap size

**Target Values:**
- FCP: <1.8s
- LCP: <2.5s
- TTI: <3.8s
- DOM nodes (1,000 rows): ~30 (with virtualization)
- Heap size: <50MB

#### 2. Interaction Latency

**Procedure:**
1. Open Chrome DevTools > Performance tab
2. Enable "Screenshots" and "Web Vitals"
3. Record the following interactions:
   - Column sort
   - Column filter
   - Quick search input
   - Inline cell edit
   - Bulk edit submission

**Measure:**
- Interaction to Next Paint (INP)
- Total blocking time for each interaction

**Target Values:**
- Sort/filter: <200ms
- Quick search: <200ms (post-debounce)
- Inline edit: <200ms
- Bulk edit: <500ms (includes API call)

#### 3. Scroll Performance

**Procedure:**
1. Open Chrome DevTools > Performance tab
2. Record performance
3. Scroll rapidly through the table (top to bottom)
4. Stop recording

**Measure:**
- Frames Per Second (FPS) during scroll
- Long tasks (>50ms)
- Layout shifts (CLS)

**Target Values:**
- FPS: 60fps (consistent)
- Long tasks: 0 during scroll
- CLS: 0 (no layout shifts)

---

## Virtualization Testing

### Test 1: Threshold-Based Activation

**Objective:** Verify virtualization only activates with >100 rows.

**Procedure:**
1. Filter data to show <100 rows
2. Open Chrome DevTools > Elements
3. Inspect `<tbody>` element
4. Count rendered `<tr>` elements

**Expected Result:**
- All rows rendered (no virtualization)
- No padding rows

**Procedure (>100 rows):**
1. Clear filters to show >100 rows
2. Inspect `<tbody>` element
3. Count rendered `<tr>` elements

**Expected Result:**
- ~20-30 rows rendered (viewport + overscan)
- 2 padding rows (top and bottom)

### Test 2: Scroll Performance with 1,000+ Rows

**Objective:** Verify 60fps scroll performance with large datasets.

**Procedure:**
1. Ensure 1,000+ rows loaded
2. Open Chrome DevTools > Performance
3. Enable "Screenshots" and "FPS" meter
4. Record performance
5. Scroll rapidly from top to bottom and back
6. Stop recording

**Expected Result:**
- Consistent 60fps (green line in FPS meter)
- No dropped frames (red bars)
- No long tasks during scroll

### Test 3: Feature Preservation - Inline Editing

**Objective:** Verify inline editing works with virtualized rows.

**Procedure:**
1. Scroll to middle of table
2. Click on an editable cell (e.g., Price)
3. Modify value and press Enter
4. Scroll away and back
5. Verify value persisted

**Expected Result:**
- Cell becomes editable on click
- Value saves successfully
- Saved value visible after scrolling

### Test 4: Feature Preservation - Row Selection

**Objective:** Verify row selection persists across scroll.

**Procedure:**
1. Select 5 rows at top of table
2. Scroll to bottom
3. Select 5 more rows
4. Scroll back to top
5. Verify selection count (should be 10)
6. Open bulk edit panel

**Expected Result:**
- Selection count: 10
- All selected rows highlighted
- Bulk edit panel shows correct count

### Test 5: Feature Preservation - Grouping

**Objective:** Verify grouping works with virtualization.

**Procedure:**
1. Enable grouping by "Manufacturer" (if available)
2. Verify groups render correctly
3. Expand/collapse groups
4. Scroll through grouped data

**Expected Result:**
- Groups display correctly
- Expand/collapse works
- No rendering glitches during scroll

### Test 6: Highlight Navigation

**Objective:** Verify `?highlight=<id>` scrolls to correct row.

**Procedure:**
1. Note a listing ID from the middle of the dataset
2. Navigate to `/dashboard/data?highlight=<listing-id>`
3. Verify page scrolls to highlighted row
4. Verify row is highlighted (visual indication)

**Expected Result:**
- Page scrolls to correct row
- Row is highlighted
- Row is fully visible in viewport

---

## Pagination Endpoint Testing

### Test 7: API Response Time

**Objective:** Verify <100ms response time for paginated endpoint.

**Procedure:**
1. Open terminal
2. Use `curl` or `httpie` to test endpoint:
   ```bash
   # First page
   time curl -X GET "http://localhost:8000/v1/listings/paginated?limit=500" \
     -H "Content-Type: application/json"

   # Subsequent page (use next_cursor from response)
   time curl -X GET "http://localhost:8000/v1/listings/paginated?limit=500&cursor=<cursor>" \
     -H "Content-Type: application/json"
   ```

**Expected Result:**
- Response time: <100ms
- Returns 500 items (or less if fewer available)
- Includes `next_cursor` if more data available

### Test 8: Cursor-Based Pagination

**Objective:** Verify pagination consistency and correctness.

**Procedure:**
1. Fetch first page (`limit=50`)
2. Note the first and last item IDs
3. Fetch second page using `next_cursor` from first response
4. Verify no duplicate items between pages
5. Verify items are in correct sort order

**Expected Result:**
- No duplicate items
- Correct sort order maintained
- Total count accurate

### Test 9: Sorting and Filtering

**Objective:** Verify pagination works with all sort columns and filters.

**Test Cases:**
```bash
# Sort by updated_at DESC (default)
curl "http://localhost:8000/v1/listings/paginated?sort_by=updated_at&sort_order=desc&limit=50"

# Sort by price_usd ASC
curl "http://localhost:8000/v1/listings/paginated?sort_by=price_usd&sort_order=asc&limit=50"

# Filter by form_factor
curl "http://localhost:8000/v1/listings/paginated?form_factor=Mini PC&limit=50"

# Combine sort and filter
curl "http://localhost:8000/v1/listings/paginated?sort_by=price_usd&form_factor=Mini PC&limit=50"
```

**Expected Result:**
- All sort columns work correctly
- Filters apply correctly
- Response time <100ms for all queries

### Test 10: Database Index Usage

**Objective:** Verify database indexes are being used.

**Procedure:**
1. Connect to database:
   ```bash
   psql -h localhost -p 5442 -U dealbrain -d dealbrain
   ```

2. Check query plan:
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM listing
   WHERE updated_at < '2025-10-31T00:00:00'
   ORDER BY updated_at DESC, id DESC
   LIMIT 500;
   ```

**Expected Result:**
- Query plan shows index usage: "Index Scan using ix_listing_updated_at_id_desc"
- Execution time: <50ms
- No sequential scans

---

## Rendering Optimization Testing

### Test 11: React DevTools Profiler

**Objective:** Verify 50%+ render count reduction.

**Procedure:**
1. Install React DevTools extension
2. Open React DevTools > Profiler tab
3. Click "Record"
4. Perform interactions:
   - Sort a column
   - Filter a column
   - Edit a cell
   - Select rows
5. Stop recording
6. Review flamegraph and ranked chart

**Expected Result:**
- EditableCell components: No re-renders when other cells update
- DualMetricCell: No re-renders when values unchanged
- PortsDisplay: No re-renders when ports array reference changes
- Total render count significantly reduced compared to baseline

### Test 12: Memoization Verification

**Objective:** Verify React.memo is working for memoized components.

**Procedure:**
1. Open Chrome DevTools > Console
2. Add temporary console.log to memoized components:
   ```typescript
   // In DualMetricCell
   console.log('DualMetricCell render', raw, adjusted);
   ```
3. Edit a different cell in the same row
4. Check console

**Expected Result:**
- DualMetricCell should NOT log (no re-render)
- Only the edited cell should re-render

### Test 13: CSS Containment

**Objective:** Verify CSS containment is applied.

**Procedure:**
1. Open Chrome DevTools > Elements
2. Inspect a table row element
3. Check computed styles

**Expected Result:**
- `contain: layout style paint;`
- `content-visibility: auto;`
- `contain-intrinsic-size: auto 48px;`

---

## Performance Monitoring Testing

### Test 14: Dev-Mode Instrumentation

**Objective:** Verify performance monitoring works in development.

**Procedure:**
1. Ensure `NODE_ENV=development`
2. Start dev server: `make web`
3. Open browser console
4. Navigate to `/dashboard/data`
5. Perform interactions:
   - Sort a column
   - Filter a column
   - Type in quick search
   - Edit a cell
   - Bulk edit

**Expected Result:**
- Console warnings appear for operations >200ms
- No warnings for fast operations (<200ms)

**Example Warning:**
```
⚠️ Slow interaction: column_sort took 245.32ms (threshold: 200ms)
```

### Test 15: DevTools Performance Marks

**Objective:** Verify Performance API marks are created.

**Procedure:**
1. Open Chrome DevTools > Performance
2. Record performance
3. Sort a column
4. Stop recording
5. Look for "User Timing" track

**Expected Result:**
- User Timing marks visible:
  - `interaction_column_sort`
  - `interaction_column_filter`
  - `interaction_quick_search`

### Test 16: React Profiler Warnings

**Objective:** Verify React Profiler logs slow renders.

**Procedure:**
1. Open browser console
2. Trigger a slow render (e.g., load 1,000 rows initially)
3. Check console for render warnings

**Expected Result:**
- Warnings for renders >50ms:
  ```
  ⚠️ Slow render: ListingsTable (mount) took 67.45ms (threshold: 50ms)
  ```

### Test 17: Production Build Verification

**Objective:** Verify zero production overhead.

**Procedure:**
1. Build for production:
   ```bash
   cd apps/web
   pnpm build
   ```

2. Verify no performance code in bundle:
   ```bash
   grep -r "measureInteraction\|logRenderPerformance" .next/static/chunks/
   ```

**Expected Result:**
- No matches found (or only minified dead code)
- No performance monitoring in production bundle

---

## Regression Testing

### Test 18: Functionality Checklist

**Objective:** Verify all existing features still work.

**Checklist:**

- [ ] **Table Display**
  - [ ] Columns render correctly
  - [ ] Data loads and displays
  - [ ] Styling is correct (no visual regressions)

- [ ] **Sorting**
  - [ ] Single column sort works
  - [ ] Sort direction toggles correctly
  - [ ] Sort indicator displays

- [ ] **Filtering**
  - [ ] Column filters work
  - [ ] Multiple filters combine correctly
  - [ ] Clear filters works

- [ ] **Quick Search**
  - [ ] Search input works
  - [ ] Results filter correctly
  - [ ] Debounce works (200ms)

- [ ] **Inline Editing**
  - [ ] Click to edit works
  - [ ] Value saves on Enter
  - [ ] Value saves on blur
  - [ ] Validation works (if applicable)
  - [ ] Error handling works

- [ ] **Bulk Editing**
  - [ ] Row selection works
  - [ ] Bulk edit panel appears
  - [ ] Field selection works
  - [ ] Value update works
  - [ ] Submission works
  - [ ] Success message displays

- [ ] **Valuation Display**
  - [ ] Color coding correct
  - [ ] Delta calculation correct
  - [ ] Details modal opens
  - [ ] Breakdown displays correctly

- [ ] **CPU/GPU Metrics**
  - [ ] DualMetricCell displays correctly
  - [ ] Raw and adjusted values correct
  - [ ] Percentage improvement correct

- [ ] **Ports Display**
  - [ ] Ports summary displays
  - [ ] Popover opens on hover/click
  - [ ] Port details correct

- [ ] **Column Management**
  - [ ] Column visibility toggle works
  - [ ] Column reordering works
  - [ ] Column resizing works

### Test 19: Accessibility Testing

**Objective:** Verify WCAG 2.1 AA compliance maintained.

**Keyboard Navigation:**
- [ ] Tab through table rows
- [ ] Arrow keys navigate cells (if applicable)
- [ ] Enter activates inline edit
- [ ] Escape cancels inline edit
- [ ] Space toggles row selection

**Screen Reader:**
- [ ] NVDA/JAWS announces table structure
- [ ] Row count announced
- [ ] Column headers announced
- [ ] Cell values announced
- [ ] Editable state announced
- [ ] Selection state announced

**Visual:**
- [ ] Focus indicators visible
- [ ] Color contrast sufficient (4.5:1 for text)
- [ ] No keyboard traps
- [ ] Skip links work

### Test 20: Cross-Browser Testing

**Objective:** Verify functionality across browsers.

**Test in:**
- [ ] Chrome/Chromium (primary)
- [ ] Firefox
- [ ] Safari (if available)
- [ ] Edge

**Verify:**
- [ ] Virtualization works
- [ ] Performance acceptable
- [ ] No console errors
- [ ] Visual consistency

---

## Automated Testing

### Unit Tests

**Location:** `/apps/web/__tests__/`

**Run Tests:**
```bash
cd apps/web
pnpm test
```

**Required Tests:**
- [ ] Virtualization threshold logic
- [ ] Performance utility functions
- [ ] Cursor encoding/decoding
- [ ] Memoization comparison functions

### Integration Tests

**Location:** `/apps/api/tests/`

**Run Tests:**
```bash
poetry run pytest tests/api/test_listings.py -v
```

**Required Tests:**
- [ ] Paginated endpoint returns correct data
- [ ] Cursor pagination consistency
- [ ] Filtering works with pagination
- [ ] Sorting works with pagination

### E2E Tests

**Framework:** Playwright or Cypress (if available)

**Required Scenarios:**
- [ ] Load table with 1,000 rows
- [ ] Scroll performance (verify no dropped frames)
- [ ] Inline edit and save
- [ ] Bulk edit workflow
- [ ] Filter and sort combinations

---

## Success Criteria Checklist

### Performance Targets

- [ ] **Virtualization:**
  - [ ] Renders only visible rows + overscan (10 rows)
  - [ ] Scroll performance at 60fps with 1,000+ rows
  - [ ] Auto-enabled when row count > 100

- [ ] **Backend Pagination:**
  - [ ] API response time <100ms for 500-row page
  - [ ] Cursor-based pagination works correctly
  - [ ] Database indexes used (verified in query plan)

- [ ] **React Optimization:**
  - [ ] All heavy components use React.memo
  - [ ] Expensive calculations wrapped in useMemo
  - [ ] Event handlers wrapped in useCallback
  - [ ] CSS containment applied to table rows
  - [ ] Render count reduced by 50%+

- [ ] **Performance Monitoring:**
  - [ ] Interaction latency tracked
  - [ ] Render time tracked
  - [ ] Console warnings for slow operations
  - [ ] Zero production overhead verified

### Functionality Preservation

- [ ] All existing features work (see Test 18 checklist)
- [ ] No visual regressions
- [ ] No breaking changes
- [ ] Accessibility maintained (WCAG 2.1 AA)

### Quality Assurance

- [ ] TypeScript compilation successful
- [ ] ESLint passing
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] E2E tests passing (if available)
- [ ] Code review completed
- [ ] Documentation complete

---

## Test Results Template

Use this template to document test results:

```markdown
# Phase 1 Test Results

**Tester:** [Name]
**Date:** [YYYY-MM-DD]
**Environment:** [Development/Staging/Production]
**Browser:** [Chrome/Firefox/Safari/Edge + Version]

## Performance Measurements

| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| DOM Nodes (1,000 rows) | ~30 | | |
| Scroll FPS | 60fps | | |
| API Response Time | <100ms | | |
| Interaction Latency | <200ms | | |
| Render Count Reduction | 50%+ | | |

## Functional Tests

| Test | Pass/Fail | Notes |
|------|-----------|-------|
| Virtualization Threshold | | |
| Inline Editing | | |
| Row Selection | | |
| Sorting | | |
| Filtering | | |
| Quick Search | | |
| Bulk Editing | | |

## Regression Tests

| Feature | Pass/Fail | Notes |
|---------|-----------|-------|
| All features from Test 18 | | |

## Issues Found

1. [Issue description]
   - Severity: [Critical/High/Medium/Low]
   - Steps to reproduce:
   - Expected:
   - Actual:

## Conclusion

- [ ] All tests passing, ready for deployment
- [ ] Minor issues found, acceptable for deployment
- [ ] Major issues found, deployment blocked

**Overall Status:** [PASS/FAIL]
```

---

## Troubleshooting

### Issue: Virtualization Not Activating

**Symptoms:** All rows rendering even with >100 rows

**Check:**
1. Verify row count: `console.log(rows.length)`
2. Check virtualization threshold prop: `virtualizationThreshold={100}`
3. Inspect `enabled` flag in useVirtualization hook

**Solution:** Ensure threshold is configured correctly in DataGrid component.

### Issue: Scroll Performance Poor

**Symptoms:** Janky scrolling, dropped frames

**Check:**
1. Browser extensions disabled?
2. Chrome DevTools Performance tab: Look for long tasks
3. React DevTools Profiler: Look for unnecessary re-renders
4. CSS containment applied?

**Solution:** Review React DevTools Profiler for components re-rendering unnecessarily.

### Issue: Performance Warnings Not Appearing

**Symptoms:** No console warnings in dev mode

**Check:**
1. `NODE_ENV=development`?
2. Browser console filtering (show all levels)
3. Interactions actually slow (>200ms)?

**Solution:** Verify dev mode enabled and console not filtered.

### Issue: Pagination Endpoint Slow

**Symptoms:** Response time >100ms

**Check:**
1. Database indexes applied (`make migrate`)?
2. Query plan (use `EXPLAIN ANALYZE`)
3. Redis cache working?

**Solution:** Ensure migration 0023 applied, check database connection.

---

## Next Steps

After completing all tests:

1. **Document Results:** Fill out Test Results Template
2. **Report Issues:** Create GitHub issues for any bugs found
3. **Update Progress:** Mark testing complete in phase-1-progress.md
4. **Prepare Deployment:** Follow Migration Guide for staging deployment

---

## References

- [Phase 1 Summary](./phase-1-summary.md)
- [Phase 1 Migration Guide](./phase-1-migration-guide.md)
- [Performance Monitoring Guide](./performance-monitoring-guide.md)
- [PERF-002 Implementation Summary](./progress/PERF-002-implementation-summary.md)
- [PERF-004 Implementation Summary](./progress/PERF-004-implementation-summary.md)
