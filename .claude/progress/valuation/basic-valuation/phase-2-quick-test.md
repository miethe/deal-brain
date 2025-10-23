# Phase 2 Quick Test Script

**Version**: 1.0
**Last Updated**: 2025-10-15
**Purpose**: Rapid manual testing checklist for Phase 2 UX improvements

## Pre-Test Setup

### Environment Check
```bash
# Ensure services running
make up

# Verify API accessible
curl http://localhost:8000/health

# Verify frontend accessible
curl http://localhost:3020
```

### Test Data Setup
```bash
# Ensure test data exists
poetry run python scripts/seed_sample_listings.py

# Verify field metadata available
curl http://localhost:8000/v1/entities/metadata | jq '.entities | length'
# Expected: > 3 entities
```

### URLs to Test
- Frontend: http://localhost:3020
- Valuation Rules: http://localhost:3020/valuation-rules
- API Health: http://localhost:8000/health
- API Docs: http://localhost:8000/docs

---

## 5-Minute Smoke Test

### Test Flow (5 minutes)

#### 1. Field Selector Performance (1 min)
**Objective**: Verify virtual scrolling and debouncing work

1. Navigate to: http://localhost:3020/valuation-rules
2. Click any rule's "Edit" button (or "Add Rule")
3. In rule modal, click "Add Condition"
4. Click field selector dropdown

**CHECK**: Dropdown opens instantly (< 100ms)
- [ ] Pass / [ ] Fail

5. Type "price" in search box
6. Observe filtering behavior

**CHECK**: Filters after 200ms debounce (not instant)
- [ ] Pass / [ ] Fail

7. Scroll through results with mouse wheel

**CHECK**: Smooth 60 FPS scrolling, no stuttering
- [ ] Pass / [ ] Fail

8. Open React DevTools → Components
9. Find VirtualizedCommandList component
10. Check rendered children count

**CHECK**: < 30 CommandItem components in DOM
- [ ] Pass / [ ] Fail

**Time Spent**: _____ min

---

#### 2. Field Value Autocomplete (2 min)
**Objective**: Verify autocomplete fetches and caches values

**Test 2A: Enum Field (30 sec)**
1. In condition row, select field: "listing.condition"
2. Click value dropdown

**CHECK**: Dropdown shows enum options (New, Like New, Good, Fair)
- [ ] Pass / [ ] Fail

3. Try typing "Custom Value"

**CHECK**: Cannot create custom value (enum restricted)
- [ ] Pass / [ ] Fail

**Test 2B: String Field with Autocomplete (60 sec)**
4. Change field to: "listing.manufacturer"
5. Open Network tab in DevTools
6. Click value dropdown
7. Observe network request

**CHECK**: API call to /v1/fields/listing.manufacturer/values
- [ ] Pass / [ ] Fail

8. Wait for values to load

**CHECK**: Dropdown shows existing manufacturers
- [ ] Pass / [ ] Fail

9. Type a custom value (e.g., "Custom Corp")
10. Look for "Create: Custom Corp" option

**CHECK**: Can create custom value for string field
- [ ] Pass / [ ] Fail

**Test 2C: Number Field (30 sec)**
11. Change field to: "listing.price_usd"

**CHECK**: Shows number input (not dropdown)
- [ ] Pass / [ ] Fail

12. Try typing letters

**CHECK**: Only accepts numbers
- [ ] Pass / [ ] Fail

**Time Spent**: _____ min

---

#### 3. Keyboard Navigation (1 min)
**Objective**: Verify accessibility and keyboard controls

1. Click in browser address bar
2. Press Tab repeatedly until field selector focused

**CHECK**: Field selector button receives focus with visible outline
- [ ] Pass / [ ] Fail

3. Press Enter to open dropdown

**CHECK**: Dropdown opens
- [ ] Pass / [ ] Fail

4. Press ArrowDown 3 times
5. Press ArrowUp 1 time

**CHECK**: Focus moves between items, scroll follows focus
- [ ] Pass / [ ] Fail

6. Press Enter to select focused item

**CHECK**: Item selected, dropdown closes
- [ ] Pass / [ ] Fail

7. Open dropdown again
8. Press Escape

**CHECK**: Dropdown closes, focus returns to button
- [ ] Pass / [ ] Fail

**Time Spent**: _____ min

---

#### 4. Caching Behavior (1 min)
**Objective**: Verify React Query caching works

1. Open React Query DevTools panel (bottom right icon)
2. Select field: "cpu.manufacturer"
3. Wait for values to load
4. Note API request in Network tab

**CHECK**: Network request made on first load
- [ ] Pass / [ ] Fail

5. Change to different field (e.g., "listing.condition")
6. Change back to "cpu.manufacturer"
7. Check Network tab

**CHECK**: No new API request (cache hit)
- [ ] Pass / [ ] Fail

8. In React Query DevTools, find query key "field-values"
9. Check "dataUpdatedAt" timestamp

**CHECK**: Cache entry exists with recent timestamp
- [ ] Pass / [ ] Fail

**Time Spent**: _____ min

---

### Smoke Test Results

**Total Time**: _____ minutes
**Tests Passed**: _____ / 16
**Tests Failed**: _____ / 16

**PASS THRESHOLD**: 14 / 16 (87.5%)

**Overall Result**: [ ] PASS / [ ] FAIL

---

## 10-Minute Extended Test

If smoke test passes, run extended tests for edge cases and performance.

### Test 5: Large Dataset Performance (2 min)

**Setup**:
```bash
# Create 200+ listings with varied data
poetry run python scripts/seed_large_dataset.py
```

**Test Steps**:
1. Open field selector
2. Open Performance Monitor: Cmd+Shift+P → "Show Performance Monitor"
3. Scroll rapidly through field list
4. Note FPS counter

**CHECK**: FPS stays > 55 during scroll
- [ ] Pass / [ ] Fail

5. Type search query: "listing"
6. Note CPU usage

**CHECK**: CPU usage < 50% during search
- [ ] Pass / [ ] Fail

---

### Test 6: Mobile Responsive (2 min)

1. Open DevTools → Device Mode (Cmd+Shift+M)
2. Select iPhone SE (375px width)
3. Open field selector

**CHECK**: Dropdown fits screen, no horizontal scroll
- [ ] Pass / [ ] Fail

4. Scroll field list with touch emulation

**CHECK**: Touch scrolling smooth
- [ ] Pass / [ ] Fail

5. Select a field with long name

**CHECK**: Text truncates with ellipsis
- [ ] Pass / [ ] Fail

---

### Test 7: Error Handling (2 min)

**Test 7A: Invalid Field API Call**
1. Open DevTools → Network tab
2. Block API requests: Right-click → Block request URL
3. Select field: "listing.manufacturer"

**CHECK**: Shows error state or loading indefinitely (graceful)
- [ ] Pass / [ ] Fail

4. Unblock request
5. Refresh page

**CHECK**: Autocomplete works after recovery
- [ ] Pass / [ ] Fail

**Test 7B: Empty Results**
6. Create field with no data (custom field, no values set)
7. Select that field

**CHECK**: Empty state message shown (not error)
- [ ] Pass / [ ] Fail

---

### Test 8: Screen Reader (2 min)

**Requirements**: VoiceOver (macOS) or NVDA (Windows)

**macOS Setup**:
```bash
# Enable VoiceOver
Cmd + F5
```

**Test Steps**:
1. Navigate to field selector with VoiceOver

**CHECK**: Announces "Select field, button"
- [ ] Pass / [ ] Fail

2. Press VO + Space to open dropdown

**CHECK**: Announces "Search fields, edit text"
- [ ] Pass / [ ] Fail

3. Navigate through field items with VO + Arrow

**CHECK**: Announces field label and metadata
- [ ] Pass / [ ] Fail

4. Select a field
5. Open dropdown again
6. Navigate to selected field

**CHECK**: Announces "selected" state
- [ ] Pass / [ ] Fail

---

### Test 9: Browser Compatibility (2 min)

**Test in 3 browsers**:

**Browser 1: Chrome**
- Version: _________________
- [ ] Field selector works
- [ ] Autocomplete works
- [ ] Performance good

**Browser 2: Firefox**
- Version: _________________
- [ ] Field selector works
- [ ] Autocomplete works
- [ ] Performance good

**Browser 3: Safari**
- Version: _________________
- [ ] Field selector works
- [ ] Autocomplete works
- [ ] Performance good

---

### Extended Test Results

**Total Time**: _____ minutes
**Tests Passed**: _____ / 12
**Tests Failed**: _____ / 12

**PASS THRESHOLD**: 10 / 12 (83%)

**Overall Result**: [ ] PASS / [ ] FAIL

---

## Debug Checklist

If tests fail, use this checklist to diagnose issues.

### Field Selector Not Working

**Symptom**: Dropdown doesn't open or shows no items

**Debug Steps**:
1. Open Console tab, check for errors
2. Check error message:

**Error: "VirtualizedCommandList is not defined"**
- [ ] Verify import: `import { VirtualizedCommandList } from '../ui/virtualized-command-list'`
- [ ] Check file exists: `apps/web/components/ui/virtualized-command-list.tsx`

**Error: "Cannot read property 'entities' of undefined"**
- [ ] Check API response: `curl http://localhost:8000/v1/entities/metadata`
- [ ] Verify backend running: `docker ps | grep api`

**Items not rendering**:
- [ ] Open React DevTools → Components
- [ ] Check VirtualizedCommandList props: `items` should be array
- [ ] Check `renderItem` prop is function

---

### Autocomplete Not Working

**Symptom**: Value dropdown empty or doesn't show suggestions

**Debug Steps**:
1. Open Network tab
2. Filter by "fields"
3. Select field to trigger autocomplete

**No API request**:
- [ ] Check `useFieldValues` hook enabled: `enabled: !!fieldName`
- [ ] Verify `fieldName` prop passed to ValueInput
- [ ] Check API_URL correct: `console.log(API_URL)`

**API returns 404**:
- [ ] Check field name format: Should be "entity.field" (e.g., "listing.condition")
- [ ] Verify backend route: `curl http://localhost:8000/v1/fields/listing.condition/values`
- [ ] Check backend logs: `docker logs dealbrain-api -f`

**API returns 500**:
- [ ] Check backend error: `docker logs dealbrain-api`
- [ ] Verify database connection: `make migrate`
- [ ] Check field exists in database

**Values not displayed**:
- [ ] Check response format: `{ field_name: string, values: string[], count: number }`
- [ ] Verify ComboBox options mapping: `options.map(v => ({ label: v, value: v }))`
- [ ] Check React Query cache: Open React Query DevTools

---

### Performance Issues

**Symptom**: Lag, stuttering, or low FPS

**Debug Steps**:
1. Open Performance Monitor
2. Record performance profile
3. Analyze long tasks

**Virtual scrolling not active**:
- [ ] Check DOM: Should have < 30 items rendered
- [ ] Verify `@tanstack/react-virtual` installed: `pnpm list @tanstack/react-virtual`
- [ ] Check virtualizer initialized: React DevTools → VirtualizedCommandList state

**Debounce not working**:
- [ ] Check `use-debounce` installed: `pnpm list use-debounce`
- [ ] Verify debounce delay: 200ms in `useDebounce(searchQuery, 200)`
- [ ] Test typing speed: Should filter after pause

**Slow API response**:
- [ ] Check Network tab timing
- [ ] Verify database query optimized: Check for DISTINCT, LIMIT
- [ ] Test with smaller limit: `?limit=10`

---

### Accessibility Issues

**Symptom**: Keyboard nav broken, screen reader issues

**Debug Steps**:
1. Tab through components
2. Check focus indicators

**No focus outline**:
- [ ] Verify CSS: `.focus-visible:focus` should have outline
- [ ] Check focus-visible polyfill loaded

**Screen reader not announcing**:
- [ ] Check aria-live region: `<div role="status" aria-live="polite">`
- [ ] Verify aria-label on button: `aria-label="Select field"`
- [ ] Check role="combobox" and aria-expanded

**Keyboard nav fails**:
- [ ] Verify onKeyDown handlers present
- [ ] Check CommandList handles arrow keys
- [ ] Test with keyboard only (no mouse)

---

## Performance Benchmarks

Use these benchmarks to evaluate performance quantitatively.

### Benchmark 1: Initial Render Time

**How to Measure**:
```javascript
// In EntityFieldSelector component
const startTime = performance.now();
// ... render logic ...
const endTime = performance.now();
console.log(`Render time: ${endTime - startTime}ms`);
```

**Targets**:
- 50 fields: < 50ms
- 200 fields: < 100ms
- 500 fields: < 150ms

**Your Results**:
- 50 fields: _____ ms
- 200 fields: _____ ms
- 500 fields: _____ ms

**Pass**: [ ] Yes / [ ] No

---

### Benchmark 2: Search Filter Time

**How to Measure**:
```javascript
// In filteredFields useMemo
const startTime = performance.now();
const filtered = allFields.filter(/* ... */);
const endTime = performance.now();
console.log(`Filter time: ${endTime - startTime}ms`);
```

**Targets**:
- 50 fields: < 10ms
- 200 fields: < 30ms
- 500 fields: < 50ms

**Your Results**:
- 50 fields: _____ ms
- 200 fields: _____ ms
- 500 fields: _____ ms

**Pass**: [ ] Yes / [ ] No

---

### Benchmark 3: API Response Time

**How to Measure**:
1. Open Network tab
2. Select field to trigger API call
3. Check "Timing" tab for selected request

**Targets**:
- Waiting (TTFB): < 100ms
- Content Download: < 50ms
- Total: < 200ms

**Your Results**:
- Field: ___________________
- Waiting: _____ ms
- Content Download: _____ ms
- Total: _____ ms

**Pass**: [ ] Yes / [ ] No

---

### Benchmark 4: Virtual Scrolling FPS

**How to Measure**:
1. Open Performance Monitor: Cmd+Shift+P → "Show Performance Monitor"
2. Open field selector with 500+ items
3. Scroll continuously for 10 seconds
4. Note minimum FPS

**Target**: > 55 FPS

**Your Results**:
- Average FPS: _____ fps
- Minimum FPS: _____ fps
- Frame drops: _____ %

**Pass**: [ ] Yes / [ ] No

---

## Test Data Scenarios

Use these scenarios to test edge cases.

### Scenario 1: Empty Database

**Setup**:
```bash
# Clear all listings
poetry run python scripts/clear_test_data.py
```

**Expected Behavior**:
- Field selector works
- Value autocomplete returns empty array
- No errors in console

**Test**:
- [ ] Field selector opens
- [ ] Select field: "listing.manufacturer"
- [ ] Value dropdown shows "No options"
- [ ] No console errors

---

### Scenario 2: Single Entity

**Setup**:
```bash
# Create only listing data, no CPU/GPU
poetry run python scripts/seed_listings_only.py
```

**Expected Behavior**:
- Only listing fields available
- CPU/GPU fields not shown

**Test**:
- [ ] Field selector shows listing fields
- [ ] Search "cpu" returns no results
- [ ] Selecting listing field works

---

### Scenario 3: Large Values List

**Setup**:
```bash
# Create 500+ unique manufacturers
poetry run python scripts/seed_many_manufacturers.py
```

**Expected Behavior**:
- API respects limit parameter
- Virtual scrolling works in value dropdown
- Search filters large list

**Test**:
- [ ] Select field: "listing.manufacturer"
- [ ] Value dropdown shows limit (e.g., 100 values)
- [ ] Scroll smooth in value dropdown
- [ ] Search filters correctly

---

## Quick Reference Commands

### Start/Stop Services
```bash
make up          # Start all services
make down        # Stop all services
make logs        # View all logs
make api-logs    # View API logs only
```

### Data Management
```bash
make seed        # Seed database
make migrate     # Run migrations
make psql        # Connect to database
```

### Testing
```bash
pnpm test        # Frontend unit tests
pytest           # Backend unit tests
pnpm lint        # Lint frontend
make format      # Format all code
```

### Debugging
```bash
# Check API health
curl http://localhost:8000/health

# Test field values endpoint
curl http://localhost:8000/v1/fields/listing.condition/values | jq

# Check entities metadata
curl http://localhost:8000/v1/entities/metadata | jq '.entities[0]'

# View React Query cache
# Open React Query DevTools in browser (icon in bottom-right)

# Clear browser cache
# Chrome: Cmd+Shift+Delete → Clear cached images and files
```

---

## Sign-Off Checklist

Before marking Phase 2 complete, verify:

### Functionality
- [ ] Field selector opens and closes
- [ ] Search filters fields correctly
- [ ] Virtual scrolling works with 200+ fields
- [ ] Enum autocomplete works
- [ ] String autocomplete works
- [ ] Number input works
- [ ] Boolean checkbox works
- [ ] Cache prevents duplicate API calls

### Performance
- [ ] Field selector renders < 100ms
- [ ] Search filters < 50ms
- [ ] Virtual scrolling 60 FPS
- [ ] API responses < 200ms
- [ ] No memory leaks (check DevTools Memory profiler)

### Accessibility
- [ ] Keyboard navigation works (Tab, Arrow, Enter, Escape)
- [ ] Focus indicators visible
- [ ] Screen reader announces correctly
- [ ] ARIA attributes present

### Browser Compatibility
- [ ] Chrome: Works
- [ ] Firefox: Works
- [ ] Safari: Works

### Code Quality
- [ ] No console errors
- [ ] No React warnings
- [ ] TypeScript compiles without errors
- [ ] ESLint passes

### Documentation
- [ ] Code comments added for complex logic
- [ ] Testing plan completed
- [ ] Known issues documented

---

## Tester Sign-Off

**Tester Name**: _______________________
**Date**: _______________________
**Time Spent**: _______ minutes

**5-Minute Smoke Test**: [ ] PASS / [ ] FAIL
**10-Minute Extended Test**: [ ] PASS / [ ] FAIL / [ ] SKIPPED

**Overall Assessment**: [ ] Ready for Production / [ ] Needs Work

**Issues Found**: _______________________________________________
______________________________________________________________
______________________________________________________________

**Next Steps**: ________________________________________________
______________________________________________________________
______________________________________________________________

---

**Document Version**: 1.0
**Last Updated**: 2025-10-15
**For**: Phase 2 UX Improvements
