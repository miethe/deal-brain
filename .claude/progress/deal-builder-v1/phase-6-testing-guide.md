# Phase 6 Testing Guide: Valuation Display & Real-time Calculations

## Quick Start

```bash
# Start development server
cd /home/user/deal-brain
make web

# OR directly
cd apps/web && pnpm dev

# Navigate to: http://localhost:3000/builder
```

## Test Scenarios

### 1. Empty State (No CPU Selected)
**Steps**:
1. Navigate to `/builder`
2. Observe right panel (Valuation Panel)

**Expected**:
- Card with title "Build Valuation"
- Message: "Select a CPU to begin calculating pricing and performance metrics"
- No pricing or metrics displayed
- Performance Metrics card shows: "Select CPU to see performance metrics"

### 2. Basic CPU Selection
**Steps**:
1. Click "Select Component" on CPU card
2. Choose any CPU from modal
3. Observe right panel updates

**Expected**:
- Loading indicator appears briefly ("Calculating...")
- Valuation panel populates within 500ms:
  - Base Price displayed
  - Adjusted Value displayed
  - Savings amount shown (green if positive, red if negative)
- DealMeter appears with color-coded quality
- Performance Metrics populate with:
  - $/CPU Mark (Multi)
  - $/CPU Mark (Single)
  - Composite Score with progress bar

### 3. Deal Quality Color Coding
**Test different CPUs to verify color coding**:

**Great Deal (Green)**: 25%+ savings
- DealMeter shows green background
- Label: "Great Deal!"
- Description: "Excellent value for money"

**Good Deal (Light Green)**: 15-25% savings
- DealMeter shows green background
- Label: "Good Deal"
- Description: "Above average value"

**Fair Value (Yellow)**: 0-15% savings
- DealMeter shows yellow background
- Label: "Fair Value"
- Description: "Market rate pricing"

**Premium Price (Red)**: Negative savings
- DealMeter shows red background
- Label: "Premium Price"
- Description: "Paying more than estimated value"

### 4. Adding Multiple Components
**Steps**:
1. Select CPU (wait for valuation)
2. Add GPU (observe update)
3. Add RAM (observe update)
4. Add Storage (observe update)

**Expected**:
- Each addition triggers recalculation
- Loading indicator shows during calculation
- Valuation updates within 500ms (300ms debounce + API time)
- No multiple API calls during rapid selection (debouncing works)

### 5. Valuation Breakdown Expansion
**Steps**:
1. Select CPU and additional components
2. Scroll to "Valuation Breakdown" card
3. Click chevron icon to expand

**Expected (Expanded)**:
- "Base Configuration" section:
  - Component Total: $X.XX
- "Valuation Adjustments" section (if rules applied):
  - Rule name with component type
  - Adjustment amount (red for deductions, green for premiums)
- "Adjusted Value" section:
  - Final adjusted value
  - Total adjustment amount

**Expected (Collapsed)**:
- Only header with "Valuation Breakdown" title and chevron icon

### 6. Performance Metrics Display
**Steps**:
1. Select CPU with benchmark data
2. Observe Performance Metrics card

**Expected**:
- $/CPU Mark (Multi): Shows efficiency ratio (lower is better)
- $/CPU Mark (Single): Shows single-thread efficiency
- Composite Score:
  - Large blue number out of 100
  - Visual progress bar (blue fill)
  - Interpretation text:
    - 80+: "Excellent overall value"
    - 60-79: "Good overall value"
    - 40-59: "Average overall value"
    - <40: "Below average overall value"

### 7. Real-time Updates & Debouncing
**Steps**:
1. Open browser DevTools → Network tab
2. Filter for `/v1/builder/calculate`
3. Rapidly select and deselect components

**Expected**:
- API calls are debounced (not called on every keystroke)
- Only one API call after 300ms of inactivity
- Loading state shows during calculation
- UI updates smoothly

### 8. Removing Components
**Steps**:
1. Build with CPU + GPU + RAM
2. Click "Remove" on GPU card
3. Observe valuation update

**Expected**:
- Valuation recalculates immediately
- Adjusted value changes
- DealMeter color may change
- Breakdown shows fewer components

### 9. Error Handling
**Steps**:
1. Stop API server: `make down`
2. Try selecting components in builder

**Expected**:
- Error card displays:
  - Red alert icon
  - Error message describing issue
- No crash or blank screen
- Can recover when API restarts

### 10. Responsive Design - Desktop
**Steps**:
1. View builder on desktop (>1024px width)
2. Scroll down the page

**Expected**:
- Valuation panel sticks to top (lg:sticky lg:top-6)
- Left panel (components) scrolls normally
- Right panel (valuation) stays visible
- 60/40 split maintained (2 cols vs 1 col)

### 11. Responsive Design - Mobile
**Steps**:
1. Resize browser to mobile width (<1024px)
2. Scroll through builder page

**Expected**:
- Single column layout
- Component selection section on top
- Valuation panel below (not sticky)
- Both sections scroll normally
- No horizontal overflow

### 12. Loading States
**Steps**:
1. Select CPU (observe initial load)
2. Add components quickly (observe recalculation)

**Expected**:
- Loading indicator appears in valuation card:
  - Spinning loader icon
  - Text: "Calculating..."
- Positioned near title
- Loading clears when data arrives

### 13. Empty Metrics (CPU without benchmark data)
**Steps**:
1. Select CPU that lacks benchmark data

**Expected**:
- Valuation still calculates (base + adjusted price)
- Performance Metrics shows:
  - "Select CPU to see performance metrics" OR
  - Empty fields for missing metrics
- No error thrown

## Visual Verification Checklist

### Layout
- [ ] Sticky panel on desktop (doesn't scroll away)
- [ ] Full-width on mobile (no overflow)
- [ ] Proper spacing between cards (gap-4)
- [ ] Cards aligned properly

### Typography
- [ ] Tabular numbers aligned in tables
- [ ] Font sizes consistent (text-sm, text-lg, text-3xl)
- [ ] Font weights appropriate (font-semibold, font-bold)
- [ ] Text colors readable (proper contrast)

### Colors
- [ ] DealMeter green (great/good deals)
- [ ] DealMeter yellow (fair value)
- [ ] DealMeter red (premium price)
- [ ] Composite score blue accent
- [ ] Adjustments: red (deductions), green (premiums)

### Interactivity
- [ ] Chevron icon toggles expansion
- [ ] Hover states on clickable elements
- [ ] Loading spinner animates
- [ ] Progress bar fills correctly

### Accessibility
- [ ] Keyboard navigation works (Tab through elements)
- [ ] Focus indicators visible
- [ ] Color not sole indicator (text labels present)
- [ ] Semantic HTML (card, button, etc.)

## Performance Benchmarks

### Target Metrics
- Initial load: < 2 seconds
- Debounce delay: 300ms
- API response: < 200ms
- UI update: < 100ms
- Total time to valuation: < 500ms

### Monitoring Points
1. Component selection click
2. Debounce timer start
3. API request sent
4. API response received
5. State update dispatched
6. UI re-render complete

## Common Issues & Solutions

### Issue: Valuation panel blank after CPU selection
**Possible Causes**:
- API server not running
- API endpoint changed
- Authentication issue

**Solution**:
```bash
# Check API is running
make api

# Check endpoint in browser
curl http://localhost:8000/v1/builder/calculate
```

### Issue: Loading state never clears
**Possible Causes**:
- API timeout
- Network error
- State update not dispatched

**Solution**:
- Check browser console for errors
- Verify React Query is configured
- Check BuilderProvider reducer

### Issue: Debouncing not working (too many API calls)
**Possible Causes**:
- useEffect dependency array issue
- Cleanup not running

**Solution**:
- Verify useEffect has proper cleanup
- Check debounce timer state

### Issue: Colors not updating correctly
**Possible Causes**:
- CSS class not applied
- Tailwind not compiling
- Color thresholds wrong

**Solution**:
- Inspect element to verify classes
- Check getDealQuality function
- Verify Tailwind config

## Browser Testing

### Desktop Browsers
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Mobile Browsers
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)
- [ ] Firefox Mobile

## Regression Testing

**Ensure previous phases still work**:
- [ ] Component selection modal opens
- [ ] Component cards display correctly
- [ ] Remove button works
- [ ] BuilderProvider state updates
- [ ] Page navigation works

## Sign-off Checklist

Before marking Phase 6 complete:
- [ ] All test scenarios pass
- [ ] Visual verification complete
- [ ] Performance benchmarks met
- [ ] Accessibility tested
- [ ] Responsive design verified
- [ ] Error handling tested
- [ ] Browser compatibility checked
- [ ] No console errors
- [ ] No TypeScript errors
- [ ] No ESLint warnings

## Next Phase Preparation

**For Phase 7 (Save & Share)**:
1. Verify current state is accessible via useBuilder()
2. Test that valuation persists during navigation
3. Ensure all component IDs are captured
4. Verify share token generation works
5. Test public/private build visibility

---

**Status**: Phase 6 implementation complete and ready for testing
**Date**: 2025-11-14
