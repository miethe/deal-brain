---
title: "Phase 4 Validation Checklist - CPU Catalog"
description: "Comprehensive accessibility and performance validation checklist for CPU Catalog feature"
audience: [qa, developers]
tags: [validation, accessibility, performance, testing, wcag, lighthouse, cpu-catalog]
created: 2025-11-06
updated: 2025-11-06
category: "test-documentation"
status: "published"
related:
  - /docs/project_plans/cpu-page-reskin/IMPLEMENTATION_PLAN.md
  - /docs/user-guide/cpu-catalog.md
---

# Phase 4 Validation Checklist - CPU Catalog

**Project:** CPU Page Reskin
**Phase:** 4C - Quality Assurance (Accessibility & Performance Validation)
**Date:** 2025-11-06
**Status:** Ready for Validation

---

## Overview

This checklist provides comprehensive validation procedures for Phase 4C of the CPU Catalog feature. All tests must pass before proceeding to Phase 4D (Documentation).

**Validation Goals:**
- ✅ WCAG 2.1 AA compliance (zero critical violations)
- ✅ Lighthouse Performance score ≥ 90
- ✅ Cross-browser compatibility (Chrome, Firefox, Safari, Edge)
- ✅ Keyboard navigation fully functional
- ✅ Screen reader accessible

---

## Accessibility Validation (WCAG 2.1 AA)

### Tools Required

- **axe DevTools** - Browser extension for automated accessibility testing
  - Install: [Chrome Web Store](https://chrome.google.com/webstore) or [Firefox Add-ons](https://addons.mozilla.org)
- **WAVE** - Web Accessibility Evaluation Tool
  - Install: [WAVE Extension](https://wave.webaim.org/extension/)
- **Keyboard** - Manual keyboard navigation testing (no tools required)
- **Screen Reader** - NVDA (Windows) or VoiceOver (Mac) testing
  - NVDA: [Download](https://www.nvaccess.org/download/)
  - VoiceOver: Built into macOS (Cmd+F5)

### Automated Testing with axe DevTools

**Target URLs:**
- `/cpus` - Main CPU Catalog page (Grid View default)
- `/cpus?view=list` - List View
- `/cpus?view=master-detail` - Master-Detail View

**Test Steps:**
1. Install axe DevTools browser extension
2. Navigate to target URL in browser
3. Open axe DevTools panel (in browser DevTools)
4. Click "Scan all of my page" to run analysis
5. Wait for scan to complete (~10 seconds)
6. Review violations by severity:
   - **Critical** - Must fix (blocks accessibility)
   - **Serious** - Should fix (significant barrier)
   - **Moderate** - Should fix (minor barrier)
   - **Minor** - Nice to fix (best practice)
7. Document all Critical and Serious violations with:
   - Element selector
   - Issue description
   - Suggested remediation
8. Fix Critical violations immediately
9. Re-run scan to verify fixes

**Expected Results:**
- ✅ Zero Critical violations (required for Phase 4 completion)
- ✅ Zero Serious violations (required for Phase 4 completion)
- ⚠️ Moderate and Minor violations documented for future improvement

**Checklist:**

- [ ] axe scan on Grid View `/cpus`
  - [ ] Zero Critical violations
  - [ ] Zero Serious violations
  - [ ] Moderate/Minor violations documented
- [ ] axe scan on List View `/cpus?view=list`
  - [ ] Zero Critical violations
  - [ ] Zero Serious violations
  - [ ] Moderate/Minor violations documented
- [ ] axe scan on Master-Detail View `/cpus?view=master-detail`
  - [ ] Zero Critical violations
  - [ ] Zero Serious violations
  - [ ] Moderate/Minor violations documented
- [ ] axe scan on Detail Panel (open any CPU card)
  - [ ] Zero Critical violations
  - [ ] Zero Serious violations
  - [ ] Moderate/Minor violations documented
- [ ] All violations documented in `phase-4-validation-report.md`
- [ ] Screenshots of axe results saved

### WAVE Validation

**Test Steps:**
1. Install WAVE browser extension
2. Navigate to target URL
3. Click WAVE icon in browser toolbar
4. Review WAVE panel tabs:
   - **Errors** (red flags) - Must fix
   - **Alerts** (yellow flags) - Review carefully
   - **Features** (green flags) - Accessibility features detected
   - **Structure** - Page structure elements
   - **ARIA** - ARIA attributes used
5. Click on icons in page to see details
6. Document all Errors with:
   - Error type
   - Element location
   - Suggested fix

**Expected Results:**
- ✅ Zero Errors (red flags) - required for Phase 4 completion
- ✅ Structural elements present (headings, landmarks, lists)
- ✅ ARIA labels present on interactive elements
- ✅ No missing alt text on images

**Checklist:**

- [ ] WAVE scan on Grid View `/cpus`
  - [ ] Zero Errors
  - [ ] Headings properly structured (h1, h2, h3)
  - [ ] Landmarks present (main, nav, region)
  - [ ] ARIA labels on buttons/links
- [ ] WAVE scan on List View `/cpus?view=list`
  - [ ] Zero Errors
  - [ ] Table structure valid
  - [ ] Column headers present
- [ ] WAVE scan on Master-Detail View `/cpus?view=master-detail`
  - [ ] Zero Errors
  - [ ] Split panel accessible
- [ ] WAVE scan on Detail Panel (opened)
  - [ ] Zero Errors
  - [ ] Modal/dialog properly labeled
- [ ] All Errors documented in validation report
- [ ] Screenshots of WAVE results saved

### Keyboard Navigation Testing

**Test Method:** Use keyboard only (no mouse) to navigate entire interface.

**Test Scenarios:**

#### 1. Tab Navigation Through Grid View

**Steps:**
1. Navigate to `/cpus` in browser
2. Press Tab key repeatedly to move through page
3. Observe focus indicator on each element
4. Verify tab order is logical

**Expected Behavior:**
- [ ] Tab key moves focus through CPU cards sequentially
- [ ] Focus indicator visible on all interactive elements (border or outline)
- [ ] Tab order is logical:
  - [ ] Filter controls (manufacturer, socket, generation, etc.)
  - [ ] View switcher buttons (Grid/List/Master-Detail)
  - [ ] CPU cards (left-to-right, top-to-bottom)
  - [ ] Pagination controls (if present)
- [ ] Shift+Tab moves focus backward through elements
- [ ] Focus indicator meets WCAG contrast requirements (3:1 minimum)

#### 2. Opening Detail Panel with Keyboard

**Steps:**
1. Tab to a CPU card
2. Press Enter or Space key
3. Observe detail panel opens

**Expected Behavior:**
- [ ] Enter key on CPU card opens detail panel
- [ ] Space key on CPU card opens detail panel
- [ ] Focus moves to detail panel when opened (first focusable element)
- [ ] Escape key closes detail panel
- [ ] Focus returns to CPU card after closing (focus management)
- [ ] Panel announces to screen reader when opened

#### 3. Detail Panel Navigation

**Steps:**
1. Open detail panel with keyboard
2. Tab through all elements in panel
3. Verify all interactive elements accessible

**Expected Behavior:**
- [ ] Tab key moves through all interactive elements in panel:
  - [ ] Close button (X)
  - [ ] KPI metrics (if interactive)
  - [ ] Chart elements (if interactive, or properly marked as decorative)
  - [ ] Listings table rows
  - [ ] External links (PassMark, Compare)
- [ ] Charts are keyboard accessible OR properly marked as decorative with `aria-hidden="true"`
- [ ] Listings table rows are keyboard accessible (if clickable)
- [ ] Tab wraps within panel (doesn't escape to page behind)
- [ ] Shift+Tab moves backward within panel

#### 4. Filter Interactions

**Steps:**
1. Tab to filter controls
2. Interact with each filter using keyboard only

**Expected Behavior:**
- [ ] Tab moves to filter controls (Manufacturer, Socket, etc.)
- [ ] Enter or Space opens filter dropdown
- [ ] Arrow keys (↑↓) navigate dropdown options
- [ ] Enter or Space selects option
- [ ] Escape closes dropdown without selection
- [ ] Selected filter displayed correctly
- [ ] "Clear all filters" button keyboard accessible
- [ ] Filter changes announced to screen reader

#### 5. View Mode Switching

**Steps:**
1. Tab to view mode buttons (Grid/List/Master-Detail)
2. Press Enter or Space to switch views
3. Verify focus behavior

**Expected Behavior:**
- [ ] Tab moves to view mode button group
- [ ] Arrow keys (←→) navigate between view buttons (optional)
- [ ] Enter or Space activates selected view button
- [ ] View switches correctly
- [ ] Focus remains on active view button after switch
- [ ] Active view button has `aria-current="true"` or `aria-pressed="true"`
- [ ] View change announced to screen reader

#### 6. Keyboard Trap Testing

**Steps:**
1. Tab through entire page from start to end
2. Verify no elements trap focus

**Expected Behavior:**
- [ ] No keyboard traps (can Tab out of all sections)
- [ ] Can reach all interactive elements with Tab
- [ ] Can exit detail panel with Escape
- [ ] Can close dropdowns with Escape
- [ ] Focus never gets stuck in a loop

**Overall Keyboard Navigation Checklist:**

- [ ] All interactive elements reachable by keyboard
- [ ] Focus indicator visible on all elements (border, outline, background change)
- [ ] Focus indicator meets WCAG contrast requirements
- [ ] Tab order is logical and intuitive
- [ ] No keyboard traps (can Tab out of all sections)
- [ ] Enter/Space activates buttons and links
- [ ] Escape closes modals, dialogs, and dropdowns
- [ ] Arrow keys work in dropdowns and lists
- [ ] Focus management works correctly (returns to trigger element)

### Screen Reader Testing

**Tool:** NVDA (Windows) or VoiceOver (Mac)

**NVDA Setup:**
1. Download and install NVDA from [nvaccess.org](https://www.nvaccess.org/download/)
2. Launch NVDA (Ctrl+Alt+N)
3. Open browser and navigate to `/cpus`
4. Use arrow keys to navigate page content
5. Use Tab key to navigate interactive elements

**VoiceOver Setup (Mac):**
1. Press Cmd+F5 to enable VoiceOver
2. Open Safari or Chrome
3. Navigate to `/cpus`
4. Use VO+→ (Control+Option+Right Arrow) to navigate
5. Use Tab key to navigate interactive elements

**Test Scenarios:**

#### 1. CPU Card Announcement

**Steps:**
1. Navigate to a CPU card with screen reader
2. Listen to announcement

**Expected Announcement:**
- [ ] CPU name announced clearly (e.g., "AMD Ryzen 9 7950X")
- [ ] Manufacturer announced (e.g., "AMD")
- [ ] Key specifications announced:
  - [ ] Cores/threads (e.g., "16 cores, 32 threads")
  - [ ] TDP (e.g., "170W TDP")
  - [ ] Socket (e.g., "AM5 socket")
- [ ] Performance badges announced with ratings:
  - [ ] "Performance per dollar: Excellent, $0.05 per PassMark"
  - [ ] "Single-thread performance: Good, 95th percentile"
- [ ] Price targets announced:
  - [ ] "Great deal under $450"
  - [ ] "Good deal under $520"
  - [ ] "Fair price under $600"
- [ ] Element role announced (e.g., "button", "card", "clickable")
- [ ] Instructions provided (e.g., "Press Enter to open details")

#### 2. Filter Controls Announcement

**Steps:**
1. Navigate to filter controls with screen reader
2. Listen to announcements

**Expected Announcement:**
- [ ] Filter labels announced (e.g., "Manufacturer", "Socket", "Generation")
- [ ] Current filter values announced (e.g., "Manufacturer: All manufacturers")
- [ ] Dropdown role announced (e.g., "combo box", "button")
- [ ] When dropdown expanded:
  - [ ] "Expanded" state announced
  - [ ] Number of options announced (e.g., "10 items")
  - [ ] Each option announced when focused
- [ ] "Clear all filters" button announced with role

#### 3. Detail Panel Announcement

**Steps:**
1. Open detail panel with keyboard
2. Navigate through panel with screen reader

**Expected Announcement:**
- [ ] Panel opening announced (e.g., "Dialog opened", "Modal")
- [ ] Panel heading announced (CPU name, e.g., "AMD Ryzen 9 7950X Details")
- [ ] Section headings announced:
  - [ ] "Key Performance Indicators"
  - [ ] "Price Targets"
  - [ ] "Performance Charts"
  - [ ] "Available Listings"
- [ ] Key metrics announced with labels:
  - [ ] "CPU Mark score: 65,000"
  - [ ] "Single-thread score: 4,200"
  - [ ] "Performance per dollar: $0.05 per PassMark"
- [ ] Charts announced:
  - [ ] Chart title announced
  - [ ] Chart type announced (e.g., "Bar chart", "Histogram")
  - [ ] Alternative text provided OR marked as decorative with `aria-hidden="true"`
- [ ] Listings table announced:
  - [ ] "Table with 15 rows and 5 columns"
  - [ ] Column headers announced
  - [ ] Row content announced with structure

#### 4. Performance Badges

**Steps:**
1. Navigate to performance badges with screen reader
2. Listen to announcements

**Expected Announcement:**
- [ ] Badge label announced (e.g., "Performance per dollar")
- [ ] Rating announced (e.g., "Excellent", "Good", "Fair", "Poor")
- [ ] Metric value announced (e.g., "$0.05 per PassMark")
- [ ] Percentile announced if present (e.g., "95th percentile")
- [ ] Color information NOT relied upon alone (text provides meaning)

#### 5. Price Targets

**Steps:**
1. Navigate to price targets with screen reader
2. Listen to announcements

**Expected Announcement:**
- [ ] Price tier label announced (e.g., "Great deal", "Good deal", "Fair price")
- [ ] Prices announced with currency (e.g., "Under $450")
- [ ] Confidence badge announced:
  - [ ] "High confidence" (15+ listings)
  - [ ] "Medium confidence" (8-14 listings)
  - [ ] "Low confidence" (3-7 listings)
  - [ ] "Insufficient data" (<3 listings)
- [ ] Color information NOT relied upon alone

#### 6. View Mode Buttons

**Steps:**
1. Navigate to view mode buttons with screen reader
2. Listen to announcements

**Expected Announcement:**
- [ ] Button group announced (e.g., "View mode, button group")
- [ ] Each button announced with label:
  - [ ] "Grid view, button"
  - [ ] "List view, button"
  - [ ] "Master-detail view, button"
- [ ] Active button state announced (e.g., "Grid view, button, selected")
- [ ] Instructions provided (e.g., "Press Enter to switch view")

**Overall Screen Reader Checklist:**

- [ ] All meaningful content announced by screen reader
- [ ] ARIA labels present on interactive elements (`aria-label`, `aria-labelledby`)
- [ ] Images have alt text (or `alt=""` for decorative images)
- [ ] Form inputs have associated labels (`<label for="...">` or `aria-label`)
- [ ] Headings structured properly (h1, h2, h3 hierarchy)
- [ ] Landmarks used for page regions (`<nav>`, `<main>`, `<aside>`, `role="region"`)
- [ ] Dynamic content updates announced (`aria-live="polite"` or `aria-live="assertive"`)
- [ ] Buttons announced as "button", links as "link"
- [ ] State changes announced (expanded/collapsed, selected/unselected)

### Color Contrast Testing

**Test Method:** Use axe DevTools or WAVE contrast checker

**WCAG AA Requirements:**
- Normal text (< 18pt): 4.5:1 contrast ratio
- Large text (≥ 18pt or ≥ 14pt bold): 3:1 contrast ratio
- Interactive elements (focus indicators): 3:1 contrast ratio

**Elements to Check:**

#### Performance Badges
- [ ] "Excellent" badge - Foreground text on background color
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] "Good" badge - Foreground text on background color
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] "Fair" badge - Foreground text on background color
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] "Poor" badge - Foreground text on background color
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)

#### Price Target Badges
- [ ] "High confidence" badge - Foreground on background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] "Medium confidence" badge - Foreground on background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] "Low confidence" badge - Foreground on background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] "Insufficient data" badge - Foreground on background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)

#### Buttons and Links
- [ ] Primary button - Text on button background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] Secondary button - Text on button background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] Link text - Text on page background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] Focus indicators - Outline on background
  - [ ] Contrast ratio: ____:1 (≥ 3:1 required)

#### Filters and Forms
- [ ] Filter labels - Text on page background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] Filter values - Text on background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] Dropdown options - Text on dropdown background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)

#### Tables and Data
- [ ] Table headers - Text on header background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] Table cells - Text on cell background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] Alternating row colors - Text on row background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)

#### Charts
- [ ] Chart labels - Text on chart background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] Chart values - Text on chart background
  - [ ] Contrast ratio: ____:1 (≥ 4.5:1 required)
- [ ] Chart axes - Line color on background
  - [ ] Contrast ratio: ____:1 (≥ 3:1 required for graphics)

**Expected Results:**
- ✅ All text meets WCAG AA contrast ratio (4.5:1 for normal text, 3:1 for large text)
- ✅ All interactive elements have visible focus indicators with sufficient contrast (3:1)
- ✅ No reliance on color alone to convey information

### ARIA Validation

**Test Method:** Use browser DevTools to inspect ARIA attributes

**Elements to Verify:**

#### Page Structure
- [ ] `<main>` element or `role="main"` on main content area
- [ ] `<nav>` element or `role="navigation"` on navigation areas
- [ ] `<aside>` element or `role="complementary"` on sidebars
- [ ] `role="region"` on major page sections with `aria-labelledby`

#### Interactive Elements
- [ ] Icon-only buttons have `aria-label` (e.g., close button, filter toggle)
- [ ] Button groups have `role="group"` and `aria-label`
- [ ] Tooltips have `aria-describedby` on trigger element

#### Sections and Headings
- [ ] Sections have `aria-labelledby` pointing to heading ID
- [ ] Headings properly nested (h1 → h2 → h3, no skipping levels)

#### Dropdowns and Menus
- [ ] Dropdown buttons have `aria-expanded="true|false"`
- [ ] Dropdown menus have `role="menu"` or `role="listbox"`
- [ ] Dropdown items have `role="menuitem"` or `role="option"`
- [ ] Selected items have `aria-selected="true"`

#### Collapsible Sections
- [ ] Collapsible triggers have `aria-expanded="true|false"`
- [ ] Collapsible content has `aria-hidden="true|false"`

#### View Mode Buttons
- [ ] Active view button has `aria-current="true"` or `aria-pressed="true"`
- [ ] Button group has `role="group"` and `aria-label="View mode"`

#### Detail Panel (Modal/Dialog)
- [ ] Modal has `role="dialog"` or `role="alertdialog"`
- [ ] Modal has `aria-modal="true"`
- [ ] Modal has `aria-labelledby` pointing to heading ID
- [ ] Modal has `aria-describedby` pointing to description (if present)

#### Charts (If Interactive)
- [ ] Charts have `role="img"` if non-interactive (decorative)
- [ ] Charts have `aria-label` describing chart content
- [ ] Charts have `alt` text or `aria-describedby` with detailed description

#### Dynamic Content
- [ ] Loading states have `aria-busy="true"`
- [ ] Live regions have `aria-live="polite"` or `aria-live="assertive"`
- [ ] Status messages have `role="status"` or `role="alert"`

**Checklist:**

- [ ] All ARIA attributes used correctly (no syntax errors)
- [ ] No conflicting ARIA (e.g., `role="button"` on `<button>`)
- [ ] No redundant ARIA (e.g., `aria-label` on `<button>` with text content)
- [ ] ARIA enhances, not replaces, semantic HTML
- [ ] All `aria-labelledby` and `aria-describedby` IDs exist in DOM
- [ ] All required ARIA attributes present (e.g., `aria-expanded` on toggle buttons)

### Accessibility Summary Checklist

- [ ] **axe DevTools:** Zero Critical and Serious violations
- [ ] **WAVE:** Zero Errors
- [ ] **Keyboard Navigation:** All interactive elements accessible, logical tab order
- [ ] **Screen Reader:** All content announced correctly, ARIA labels present
- [ ] **Color Contrast:** All text meets WCAG AA (4.5:1 or 3:1)
- [ ] **ARIA:** All attributes used correctly, no conflicts or redundancy

**WCAG 2.1 AA Compliance:** ✅ PASSED / ❌ FAILED

---

## Performance Validation (Lighthouse)

### Tools Required

- **Chrome DevTools Lighthouse** - Built into Chrome browser (no installation needed)
- **Network Throttling** - Simulated 3G or 4G connection (built into Chrome DevTools)
- **CPU Throttling** - 4x slowdown to simulate slower devices (built into Chrome DevTools)

### Lighthouse Audit Setup

**Test Configuration:**
- **Device:** Desktop (primary), Mobile (bonus)
- **Categories:** Performance, Accessibility, Best Practices, SEO
- **Mode:** Navigation (default)
- **Throttling:** Applied (Simulated throttling)

**Target URLs:**
- `/cpus` - Main CPU Catalog page (Grid View)

**Test Steps:**
1. Open Chrome browser
2. Navigate to `/cpus` page
3. Open Chrome DevTools (F12 or right-click → Inspect)
4. Click **Lighthouse** tab in DevTools
5. Select **Desktop** device mode
6. Check all categories:
   - ☑ Performance
   - ☑ Accessibility
   - ☑ Best Practices
   - ☑ SEO
7. Click **Analyze page load** button
8. Wait for audit to complete (~30-60 seconds)
9. Review scores and metrics
10. Take screenshot of results (save to `validation/lighthouse-results/`)
11. Click **View Treemap** to analyze bundle size (optional)

**Repeat for Mobile:**
1. Select **Mobile** device mode in Lighthouse
2. Run audit again
3. Compare Desktop vs Mobile scores

### Performance Metrics

**Target Scores (Desktop):**
- **Performance:** ≥ 90 (target: 95+) - REQUIRED for Phase 4 completion
- **Accessibility:** ≥ 90 (target: 100) - REQUIRED for Phase 4 completion
- **Best Practices:** ≥ 90 - Recommended
- **SEO:** ≥ 85 - Recommended

**Core Web Vitals (Desktop):**

- **LCP (Largest Contentful Paint):** < 2.5s (Good)
  - Measures loading performance
  - Should be first CPU card or main content
- **FID (First Input Delay):** < 100ms (Good)
  - Measures interactivity (replaced by INP in newer Lighthouse)
- **CLS (Cumulative Layout Shift):** < 0.1 (Good)
  - Measures visual stability
  - No layout shifts during page load

**Additional Performance Metrics:**

- **FCP (First Contentful Paint):** < 1.8s
  - First text or image painted
- **TTI (Time to Interactive):** < 3.8s
  - Page fully interactive
- **Speed Index:** < 3.4s
  - How quickly content is visually displayed
- **Total Blocking Time (TBT):** < 200ms
  - Time page is blocked from responding to user input

**Checklist:**

- [ ] **Lighthouse Desktop Audit Completed**
  - [ ] Performance score: ____/100 (≥ 90 required)
  - [ ] Accessibility score: ____/100 (≥ 90 required)
  - [ ] Best Practices score: ____/100 (≥ 90 recommended)
  - [ ] SEO score: ____/100 (≥ 85 recommended)
- [ ] **Core Web Vitals (Desktop)**
  - [ ] LCP: ____s (< 2.5s required)
  - [ ] FID/INP: ____ms (< 100ms required)
  - [ ] CLS: ____ (< 0.1 required)
- [ ] **Additional Metrics (Desktop)**
  - [ ] FCP: ____s (< 1.8s target)
  - [ ] TTI: ____s (< 3.8s target)
  - [ ] Speed Index: ____s (< 3.4s target)
  - [ ] TBT: ____ms (< 200ms target)
- [ ] **Lighthouse Mobile Audit Completed (Bonus)**
  - [ ] Performance score: ____/100
  - [ ] Accessibility score: ____/100
- [ ] **Screenshot saved:** `validation/lighthouse-results/lighthouse-desktop-YYYY-MM-DD.png`
- [ ] **All metrics documented** in validation report

### Performance Optimization Verification

#### React Query Caching

**Test Method:** Verify caching reduces API calls on navigation

**Steps:**
1. Open Chrome DevTools → Network tab
2. Filter by "Fetch/XHR"
3. Navigate to `/cpus` (first visit)
4. Observe API calls (e.g., `GET /api/cpus`)
5. Navigate away from `/cpus` (e.g., to `/dashboard`)
6. Navigate back to `/cpus` (second visit)
7. Observe Network tab - should be NO or fewer API calls (cache hit)

**Expected Behavior:**
- [ ] First visit: API calls visible in Network tab (cache miss)
- [ ] Second visit: Fewer or no API calls (cache hit)
- [ ] Page loads instantly from cache (<100ms)
- [ ] Data displayed correctly from cache
- [ ] React Query DevTools shows "fresh" or "stale" cache status

**React Query Configuration to Verify:**
```typescript
// Expected in apps/web/hooks/useCPUs.ts or similar
const { data } = useQuery({
  queryKey: ['cpus'],
  queryFn: fetchCPUs,
  staleTime: 5 * 60 * 1000, // 5 minutes
  cacheTime: 10 * 60 * 1000, // 10 minutes
});
```

**Checklist:**
- [ ] React Query caching reduces API calls on repeated visits
- [ ] Network tab shows cache hits (fewer requests)
- [ ] Page loads instantly from cache (<100ms)

#### Memoization

**Test Method:** Use React DevTools Profiler to verify no unnecessary re-renders

**Steps:**
1. Install React DevTools extension
2. Open React DevTools → Profiler tab
3. Click "Record" button (🔴)
4. Interact with page:
   - Apply filter
   - Switch view mode
   - Scroll Grid View
   - Open/close Detail Panel
5. Stop recording
6. Review flame graph:
   - Green = memoized (did not re-render)
   - Yellow/Red = re-rendered
7. Verify CPU cards do NOT re-render when:
   - Scrolling page
   - Unrelated state changes
   - Detail panel opened/closed

**Expected Behavior:**
- [ ] CPU cards wrapped in `React.memo()` (check code)
- [ ] CPU cards do NOT re-render when scrolling (green in Profiler)
- [ ] Expensive calculations wrapped in `useMemo()` (check code)
- [ ] Callbacks wrapped in `useCallback()` (check code)
- [ ] Re-renders only happen when props/state change

**Code to Verify:**
```typescript
// Expected in apps/web/components/cpus/cpu-card.tsx
export const CPUCard = React.memo(({ cpu, onClick }) => {
  // Component implementation
});

// Expected in parent component
const sortedCPUs = useMemo(() => {
  return cpus.sort(/* ... */);
}, [cpus]);

const handleCardClick = useCallback((cpuId: string) => {
  // Handle click
}, [/* dependencies */]);
```

**Checklist:**
- [ ] React.memo used on CPU cards (check code)
- [ ] useMemo used on expensive calculations (sorting, filtering)
- [ ] useCallback used on event handlers
- [ ] React DevTools Profiler shows minimal re-renders

#### Image Optimization

**Test Method:** Verify images use Next.js Image component and lazy loading

**Steps:**
1. Open Chrome DevTools → Network tab
2. Filter by "Img"
3. Navigate to `/cpus` and scroll page
4. Observe image loading behavior

**Expected Behavior:**
- [ ] Images use Next.js `<Image>` component (check code)
- [ ] Images have `loading="lazy"` attribute (check Elements tab)
- [ ] Images only load when scrolled into viewport (Network tab)
- [ ] Images serve optimized formats (WebP, AVIF)
- [ ] Image sizes appropriate for viewport (no oversized images)

**Code to Verify:**
```typescript
// Expected in apps/web/components/cpus/cpu-card.tsx
import Image from 'next/image';

<Image
  src="/images/cpu-placeholder.png"
  alt="CPU placeholder"
  width={64}
  height={64}
  loading="lazy"
/>
```

**Network Tab Verification:**
- [ ] Check image format: Should be WebP or AVIF (modern formats)
- [ ] Check image size: Should be <100KB for thumbnails
- [ ] Check lazy loading: Images load only when scrolled into view

**Checklist:**
- [ ] Images use Next.js Image component (check code)
- [ ] Images lazy-loaded (Network tab shows progressive loading)
- [ ] Image sizes optimized (<100KB for thumbnails)

#### Bundle Size Analysis

**Test Method:** Analyze JavaScript bundle sizes

**Steps:**
1. Open terminal in `apps/web/` directory
2. Run production build:
   ```bash
   pnpm build
   ```
3. Review build output for bundle sizes:
   ```
   Route (app)                              Size     First Load JS
   ┌ ○ /                                    5.2 kB         120 kB
   └ ○ /cpus                                8.5 kB         123 kB
   ```
4. Check `.next/static/` directory for bundle files
5. Use Lighthouse → View Treemap to visualize bundle composition

**Expected Results:**
- [ ] Main bundle < 250KB gzipped
- [ ] First Load JS < 150KB for `/cpus` page
- [ ] No large third-party libraries added unnecessarily
- [ ] Code splitting used for large components (Detail Panel)
- [ ] Recharts (charts library) code-split or tree-shaken

**Bundle Size Targets:**
- **Main Bundle:** < 250KB gzipped
- **First Load JS:** < 150KB per page
- **Recharts (if used):** < 100KB (tree-shaken, only used components)

**Checklist:**
- [ ] Production build completed successfully
- [ ] Main bundle < 250KB gzipped
- [ ] First Load JS < 150KB for `/cpus` page
- [ ] Bundle sizes documented in validation report
- [ ] No unexpected large dependencies (review Treemap)

#### Performance Summary Checklist

- [ ] **React Query:** Caching works, reduces API calls
- [ ] **Memoization:** React.memo/useMemo/useCallback used, minimal re-renders
- [ ] **Images:** Lazy-loaded, optimized formats, appropriate sizes
- [ ] **Bundle Size:** Main bundle < 250KB, First Load JS < 150KB

---

## Cross-Browser Testing

### Browsers to Test

**Desktop (Required):**
- [ ] **Chrome (latest)** - Primary target browser
  - Version: ______
  - Download: [Google Chrome](https://www.google.com/chrome/)
- [ ] **Firefox (latest)** - Must work correctly
  - Version: ______
  - Download: [Mozilla Firefox](https://www.mozilla.org/firefox/)
- [ ] **Safari (latest)** - Must work correctly (macOS required)
  - Version: ______
  - Built into macOS
- [ ] **Edge (latest)** - Should work (Chromium-based)
  - Version: ______
  - Download: [Microsoft Edge](https://www.microsoft.com/edge)

**Mobile (Bonus):**
- [ ] **Chrome Mobile (Android)** - Should work
- [ ] **Safari Mobile (iOS)** - Should work

### Test Scenarios

**For Each Browser, Test All Scenarios:**

#### 1. Grid View Rendering

**Steps:**
1. Navigate to `/cpus` in browser
2. Verify Grid View renders correctly
3. Inspect visual layout and styling

**Expected Results:**
- [ ] CPU cards display in grid layout (3-4 columns on desktop)
- [ ] Cards have proper spacing and alignment
- [ ] Performance badges visible and styled correctly:
  - [ ] Colors render correctly (green, yellow, orange, red)
  - [ ] Text readable and styled
- [ ] Price targets visible and styled correctly:
  - [ ] Great/Good/Fair labels styled
  - [ ] Confidence badges styled
- [ ] Tooltips appear on hover (desktop) or tap (mobile)
  - [ ] Tooltip positioned correctly
  - [ ] Tooltip content readable
- [ ] No visual bugs (overlapping, misalignment, broken layout)

#### 2. List View Rendering

**Steps:**
1. Click "List View" button
2. Verify List View renders correctly
3. Inspect table layout

**Expected Results:**
- [ ] List rows display correctly in table layout
- [ ] Columns aligned properly (left, center, right as designed)
- [ ] Column headers visible and clickable
- [ ] Sorting works on column header click:
  - [ ] Sort indicator (▲▼) appears
  - [ ] Rows re-order correctly
  - [ ] Click again reverses sort order
- [ ] Alternating row colors visible (if designed)
- [ ] Responsive: Horizontal scroll appears on narrow viewports

#### 3. Master-Detail View

**Steps:**
1. Click "Master-Detail View" button
2. Verify split layout renders correctly
3. Click CPU in left list

**Expected Results:**
- [ ] Left list and right panel display side-by-side (50/50 or 40/60 split)
- [ ] Left list shows CPU names/basic info
- [ ] Right panel empty initially (or shows placeholder)
- [ ] Click CPU in left list:
  - [ ] Right panel updates to show CPU details
  - [ ] Selected CPU highlighted in left list
- [ ] Charts render correctly in right panel (Recharts):
  - [ ] Bar chart visible
  - [ ] Histogram visible
  - [ ] Axes and labels readable
  - [ ] Tooltips appear on hover
- [ ] Responsive: Split becomes stacked on mobile (list on top, panel below)

#### 4. Filters

**Steps:**
1. Click filter controls (Manufacturer, Socket, etc.)
2. Select options
3. Verify filtering works

**Expected Results:**
- [ ] Filter panel opens/closes correctly (if collapsible)
- [ ] Dropdown menus open when clicked:
  - [ ] Options display correctly
  - [ ] Scrollable if many options
  - [ ] Selected option highlighted
- [ ] Filters apply when selected:
  - [ ] CPU list updates to show only matching CPUs
  - [ ] "X results" count updates
- [ ] "Clear all filters" button works:
  - [ ] Removes all filters
  - [ ] CPU list resets to all CPUs
- [ ] Multiple filters work together (e.g., AMD + AM5 socket)

#### 5. Detail Panel

**Steps:**
1. Click a CPU card (Grid or List View)
2. Verify detail panel opens
3. Inspect all sections

**Expected Results:**
- [ ] Modal or panel opens correctly:
  - [ ] Overlay darkens background (if modal)
  - [ ] Panel positioned correctly (center or side)
  - [ ] Smooth animation (fade in)
- [ ] All sections render correctly:
  - [ ] KPIs (CPU Mark, Single-Thread, Price/Perf)
  - [ ] Price Targets (Great/Good/Fair with confidence)
  - [ ] Performance Charts (bar chart, histogram)
  - [ ] Available Listings table (columns, rows, data)
- [ ] Charts display correctly:
  - [ ] Recharts renders without errors
  - [ ] Axes and labels visible
  - [ ] Tooltips work on hover
  - [ ] Data renders correctly (bars, lines, etc.)
- [ ] Close button works:
  - [ ] Click X button closes panel
  - [ ] Click outside modal closes panel (if modal)
  - [ ] Escape key closes panel
- [ ] Listings table works:
  - [ ] Rows display correctly
  - [ ] Links clickable (external)
  - [ ] Sorting works (if implemented)

#### 6. Responsive Design (Mobile)

**Steps:**
1. Resize browser to 375px width (iPhone SE size)
2. Or use Chrome DevTools → Device Toolbar (Ctrl+Shift+M)
3. Test all features at mobile viewport

**Expected Results:**
- [ ] Layout adjusts for 320px viewport (smallest mobile)
- [ ] Layout adjusts for 375px viewport (common mobile)
- [ ] Filter panel becomes collapsible or drawer (if designed):
  - [ ] Opens from side or bottom
  - [ ] Closes with X button or overlay tap
- [ ] CPU cards stack vertically (1 column):
  - [ ] Full width
  - [ ] Readable text
  - [ ] Touchable buttons (44px minimum hit area)
- [ ] Detail panel becomes full-screen modal:
  - [ ] Covers entire viewport
  - [ ] Scrollable content
  - [ ] Close button accessible
- [ ] Tables scroll horizontally (if too wide):
  - [ ] Horizontal scroll indicator visible
  - [ ] All columns accessible
- [ ] Touch interactions work:
  - [ ] Tap to open detail panel
  - [ ] Swipe to scroll
  - [ ] Pinch to zoom (if allowed)

### Cross-Browser Compatibility Matrix

**Fill in after testing each browser:**

| Browser | Version | Grid View | List View | Master-Detail | Detail Panel | Filters | Overall |
|---------|---------|-----------|-----------|---------------|--------------|---------|---------|
| Chrome  |         | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Firefox |         | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Safari  |         | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Edge    |         | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

**Legend:**
- ✅ Pass (works correctly)
- ⚠️ Warning (minor issues, still usable)
- ❌ Fail (broken, unusable)

### Known Cross-Browser Issues

**Document any browser-specific issues found:**

| Browser | Issue Description | Severity | Workaround/Fix |
|---------|-------------------|----------|----------------|
| Example: Safari | Chart tooltips not appearing | Minor | Use native title attribute |
|         |                   |          |                |
|         |                   |          |                |

**Common CSS Issues to Watch For:**
- [ ] Flexbox/Grid layout differences
- [ ] CSS Grid not supported in older browsers
- [ ] CSS custom properties (variables) not working
- [ ] Backdrop filter not supported (blur effects)
- [ ] Position: sticky not working in older Safari
- [ ] Clamp() CSS function not supported in older browsers

**Common JavaScript Issues to Watch For:**
- [ ] Radix UI components not working (check console for errors)
- [ ] Recharts not rendering (SVG issues)
- [ ] React hooks errors (strict mode issues)
- [ ] Event handlers not firing (onClick, onChange)
- [ ] Fetch API not supported in older browsers (should use polyfill)

### Cross-Browser Testing Checklist

- [ ] All browsers tested (Chrome, Firefox, Safari, Edge)
- [ ] All test scenarios passed for each browser (Grid, List, Master-Detail, Filters, Detail Panel, Responsive)
- [ ] Compatibility matrix filled out
- [ ] Issues documented with severity and workarounds
- [ ] Screenshots saved for any browser-specific bugs

**Cross-Browser Compatibility:** ✅ PASSED / ❌ FAILED

---

## Validation Report Template

After completing all validation tasks, create a separate document:

**File:** `docs/project_plans/cpu-page-reskin/validation/phase-4-validation-report.md`

**Template:**

```markdown
# Phase 4 Validation Report - CPU Catalog

**Date:** 2025-11-06
**Validator:** [Your Name]
**Feature:** CPU Catalog (Phase 4 - Polish, Testing & Documentation)
**Phase:** 4C - Quality Assurance (Accessibility & Performance Validation)

---

## Executive Summary

**Validation Status:** ✅ PASSED / ❌ FAILED

**Overall Results:**
- Accessibility (WCAG 2.1 AA): ✅ PASSED / ❌ FAILED
- Performance (Lighthouse ≥ 90): ✅ PASSED / ❌ FAILED
- Cross-Browser Compatibility: ✅ PASSED / ❌ FAILED

**Key Findings:**
- [Summary of major findings, issues, or successes]
- [Any critical issues that blocked completion]
- [Any recommendations for future improvements]

---

## Accessibility Validation Results

### axe DevTools Results

**Grid View (`/cpus`):**
- Critical Violations: 0 ✅
- Serious Violations: 0 ✅
- Moderate Violations: [count]
- Minor Violations: [count]

**List View (`/cpus?view=list`):**
- Critical Violations: 0 ✅
- Serious Violations: 0 ✅
- Moderate Violations: [count]
- Minor Violations: [count]

**Master-Detail View (`/cpus?view=master-detail`):**
- Critical Violations: 0 ✅
- Serious Violations: 0 ✅
- Moderate Violations: [count]
- Minor Violations: [count]

**Detail Panel (opened):**
- Critical Violations: 0 ✅
- Serious Violations: 0 ✅
- Moderate Violations: [count]
- Minor Violations: [count]

**Issues Found:**
[List any Moderate or Minor violations for future improvement]

**Screenshots:** [Link to screenshots in `validation/axe-results/`]

### WAVE Results

**Grid View:**
- Errors: 0 ✅
- Alerts: [count]
- Features: [count]
- Structural Elements: [count]
- ARIA: [count]

**List View:**
- Errors: 0 ✅
- Alerts: [count]

**Master-Detail View:**
- Errors: 0 ✅
- Alerts: [count]

**Detail Panel:**
- Errors: 0 ✅
- Alerts: [count]

**Issues Found:**
[List any Alerts for review]

**Screenshots:** [Link to screenshots in `validation/wave-results/`]

### Keyboard Navigation Results

**Test Results:**
- All interactive elements reachable: ✅
- Focus indicators visible: ✅
- Tab order logical: ✅
- No keyboard traps: ✅
- Enter/Space activates buttons: ✅
- Escape closes modals: ✅

**Issues Found:**
[List any keyboard navigation issues]

### Screen Reader Results (NVDA)

**Test Results:**
- Meaningful content announced: ✅
- ARIA labels present: ✅
- Landmarks properly structured: ✅
- Headings properly nested: ✅
- Dynamic content announced: ✅

**Sample Announcements:**
- CPU Card: "AMD Ryzen 9 7950X, 16 cores 32 threads, 170W TDP, AM5 socket, Performance per dollar Excellent $0.05 per PassMark, button"
- Filter: "Manufacturer, combo box, All manufacturers, collapsed"
- Detail Panel: "AMD Ryzen 9 7950X Details, dialog"

**Issues Found:**
[List any screen reader issues]

### Color Contrast Results

**Test Method:** axe DevTools contrast checker

**Results:**
- All text meets WCAG AA (4.5:1): ✅
- Large text meets WCAG AA (3:1): ✅
- Interactive elements meet WCAG AA (3:1): ✅

**Contrast Ratios:**
| Element | Foreground | Background | Ratio | Pass |
|---------|------------|------------|-------|------|
| Performance Badge (Excellent) | #FFFFFF | #10B981 | 4.52:1 | ✅ |
| Performance Badge (Good) | #000000 | #FCD34D | 10.5:1 | ✅ |
| [Add more rows...] |  |  |  |  |

**Issues Found:**
[List any contrast issues]

### ARIA Validation Results

**Test Method:** Browser DevTools inspection

**Results:**
- All ARIA attributes used correctly: ✅
- No conflicting ARIA: ✅
- No redundant ARIA: ✅
- ARIA enhances semantic HTML: ✅

**ARIA Attributes Found:**
- `role="main"` on main content area
- `role="navigation"` on navigation areas
- `aria-label` on icon-only buttons
- `aria-expanded` on dropdowns
- `aria-modal="true"` on detail panel
- `aria-labelledby` on sections
- [Add more...]

**Issues Found:**
[List any ARIA issues]

### Accessibility Summary

**WCAG 2.1 AA Compliance:** ✅ PASSED / ❌ FAILED

**Criteria Met:**
- ✅ Zero Critical violations (axe)
- ✅ Zero Serious violations (axe)
- ✅ Zero Errors (WAVE)
- ✅ Keyboard navigation fully functional
- ✅ Screen reader accessible
- ✅ Color contrast meets WCAG AA
- ✅ ARIA used correctly

**Recommendations for Future Improvement:**
- [List Moderate/Minor issues to address later]
- [Any WCAG AAA enhancements to consider]

---

## Performance Validation Results

### Lighthouse Scores

**Desktop Audit:**
- **Performance:** [score]/100 (≥ 90 required) ✅ / ❌
- **Accessibility:** [score]/100 (≥ 90 required) ✅ / ❌
- **Best Practices:** [score]/100 (≥ 90 recommended) ✅ / ❌
- **SEO:** [score]/100 (≥ 85 recommended) ✅ / ❌

**Mobile Audit (Bonus):**
- **Performance:** [score]/100 ✅ / ❌
- **Accessibility:** [score]/100 ✅ / ❌

**Screenshot:** [Link to `validation/lighthouse-results/lighthouse-desktop-YYYY-MM-DD.png`]

### Core Web Vitals

**Desktop:**
- **LCP (Largest Contentful Paint):** [time]s (< 2.5s required) ✅ / ❌
- **FID/INP (First Input Delay):** [time]ms (< 100ms required) ✅ / ❌
- **CLS (Cumulative Layout Shift):** [score] (< 0.1 required) ✅ / ❌

**Mobile (Bonus):**
- **LCP:** [time]s
- **FID/INP:** [time]ms
- **CLS:** [score]

### Additional Performance Metrics

**Desktop:**
- **FCP (First Contentful Paint):** [time]s (< 1.8s target)
- **TTI (Time to Interactive):** [time]s (< 3.8s target)
- **Speed Index:** [time]s (< 3.4s target)
- **Total Blocking Time:** [time]ms (< 200ms target)

### Performance Optimizations Verified

**React Query Caching:**
- ✅ Caching reduces API calls on repeated visits
- ✅ Network tab shows cache hits
- ✅ Page loads instantly from cache (<100ms)

**Memoization:**
- ✅ React.memo used on CPU cards (code verified)
- ✅ useMemo used on expensive calculations (code verified)
- ✅ React DevTools Profiler shows minimal re-renders

**Image Optimization:**
- ✅ Images use Next.js Image component (code verified)
- ✅ Images lazy-loaded (Network tab verified)
- ✅ Image sizes optimized (<100KB)

**Bundle Size:**
- Main Bundle: [size]KB gzipped (< 250KB target) ✅ / ❌
- First Load JS: [size]KB (< 150KB target) ✅ / ❌
- Recharts: [size]KB (tree-shaken)

### Performance Summary

**Performance Targets:** ✅ PASSED / ❌ FAILED

**Criteria Met:**
- ✅ Lighthouse Performance ≥ 90
- ✅ Lighthouse Accessibility ≥ 90
- ✅ LCP < 2.5s
- ✅ FID/INP < 100ms
- ✅ CLS < 0.1
- ✅ React Query caching working
- ✅ Memoization implemented
- ✅ Images optimized
- ✅ Bundle size acceptable

**Recommendations for Future Improvement:**
- [Any optimizations to consider later]

---

## Cross-Browser Testing Results

**Browsers Tested:**

| Browser | Version | Date Tested |
|---------|---------|-------------|
| Chrome  | [version] | 2025-11-06 |
| Firefox | [version] | 2025-11-06 |
| Safari  | [version] | 2025-11-06 |
| Edge    | [version] | 2025-11-06 |

**Test Results Matrix:**

| Browser | Grid View | List View | Master-Detail | Detail Panel | Filters | Overall |
|---------|-----------|-----------|---------------|--------------|---------|---------|
| Chrome  | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Firefox | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Safari  | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edge    | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Issues Found:**

| Browser | Issue Description | Severity | Status | Workaround/Fix |
|---------|-------------------|----------|--------|----------------|
| [browser] | [issue] | Critical/Major/Minor | Fixed/Open | [fix description] |
|         |         |          |        |                |

**Screenshots:** [Link to screenshots of any browser-specific issues]

### Cross-Browser Summary

**Cross-Browser Compatibility:** ✅ PASSED / ❌ FAILED

**Criteria Met:**
- ✅ All browsers render correctly (Chrome, Firefox, Safari, Edge)
- ✅ All features work in all browsers
- ✅ No critical or major browser-specific bugs

**Recommendations:**
- [Any browser-specific enhancements to consider]

---

## Overall Validation Summary

**Phase 4C Validation Status:** ✅ COMPLETE / ❌ INCOMPLETE

**Criteria Met:**
- ✅ **Accessibility:** WCAG 2.1 AA compliant (zero critical violations)
- ✅ **Performance:** Lighthouse scores ≥ 90 (Performance & Accessibility)
- ✅ **Cross-Browser:** All tested browsers pass

**Blockers:**
- [List any issues blocking Phase 4 completion]

**Next Steps:**
1. ✅ Validation complete - Proceed to Phase 4D (DOC-003 and TEST-004)
2. [Any remaining tasks before documentation]

---

**Report Generated:** 2025-11-06
**Validated By:** [Your Name]
**Validation Checklist Version:** 1.0
```

---

## Validation Workflow

### Step-by-Step Process

**1. Preparation (5 minutes)**
- [ ] Install required tools (axe, WAVE, NVDA/VoiceOver)
- [ ] Open `/cpus` page in all browsers
- [ ] Open Chrome DevTools (F12)
- [ ] Create `validation/` directory structure:
  ```
  validation/
  ├── axe-results/
  ├── wave-results/
  ├── lighthouse-results/
  └── screenshots/
  ```

**2. Accessibility Testing (30-45 minutes)**
- [ ] Run axe DevTools on all views (5 min)
- [ ] Run WAVE on all views (5 min)
- [ ] Keyboard navigation testing (10 min)
- [ ] Screen reader testing (15 min)
- [ ] Color contrast testing (5 min)
- [ ] ARIA validation (5 min)

**3. Performance Testing (15-20 minutes)**
- [ ] Run Lighthouse Desktop audit (5 min)
- [ ] Run Lighthouse Mobile audit (5 min)
- [ ] Verify React Query caching (2 min)
- [ ] Verify memoization (React DevTools) (3 min)
- [ ] Verify image optimization (Network tab) (2 min)
- [ ] Analyze bundle size (pnpm build) (3 min)

**4. Cross-Browser Testing (20-30 minutes)**
- [ ] Test Chrome (5 min)
- [ ] Test Firefox (5 min)
- [ ] Test Safari (5 min)
- [ ] Test Edge (5 min)
- [ ] Test responsive design (5 min)
- [ ] Document issues (5 min)

**5. Documentation (20-30 minutes)**
- [ ] Create validation report (15 min)
- [ ] Take screenshots (5 min)
- [ ] Document issues with workarounds (5 min)
- [ ] Fill out compatibility matrix (5 min)

**Total Time Estimate:** 90-120 minutes (1.5-2 hours)

### Validation Pass Criteria

**Phase 4C is COMPLETE when:**
- ✅ All accessibility tests pass (zero critical/serious violations)
- ✅ All performance tests pass (Lighthouse ≥ 90)
- ✅ All cross-browser tests pass (no critical bugs)
- ✅ Validation report created and saved
- ✅ All issues documented with severity and status

**Phase 4C is INCOMPLETE when:**
- ❌ Any critical accessibility violations remain
- ❌ Lighthouse Performance or Accessibility < 90
- ❌ Critical browser-specific bugs exist
- ❌ Validation report not created

---

## Additional Resources

### Tools and Extensions

**Accessibility:**
- axe DevTools: https://www.deque.com/axe/devtools/
- WAVE Extension: https://wave.webaim.org/extension/
- NVDA Screen Reader: https://www.nvaccess.org/download/
- VoiceOver User Guide: https://support.apple.com/guide/voiceover/welcome/mac

**Performance:**
- Lighthouse: Built into Chrome DevTools
- React DevTools: https://react.dev/learn/react-developer-tools
- React Query DevTools: https://tanstack.com/query/latest/docs/devtools

**Testing:**
- Chrome DevTools: https://developer.chrome.com/docs/devtools/
- Firefox Developer Tools: https://firefox-source-docs.mozilla.org/devtools-user/

### Documentation

**Accessibility:**
- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- WAI-ARIA Practices: https://www.w3.org/WAI/ARIA/apg/
- MDN Accessibility: https://developer.mozilla.org/en-US/docs/Web/Accessibility

**Performance:**
- Web Vitals: https://web.dev/vitals/
- Lighthouse Scoring: https://developer.chrome.com/docs/lighthouse/performance/performance-scoring/
- React Performance: https://react.dev/learn/render-and-commit

**Testing:**
- Cross-Browser Testing: https://developer.mozilla.org/en-US/docs/Learn/Tools_and_testing/Cross_browser_testing

---

## Appendix: Common Issues and Solutions

### Accessibility Issues

**Issue:** Focus indicator not visible on buttons
**Solution:** Add CSS focus styles with sufficient contrast
```css
button:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}
```

**Issue:** Images missing alt text
**Solution:** Add descriptive alt text or `alt=""` for decorative images
```tsx
<Image src="/cpu.png" alt="AMD Ryzen 9 7950X processor" />
<Image src="/decoration.png" alt="" /> {/* Decorative */}
```

**Issue:** Dropdown not keyboard accessible
**Solution:** Use Radix UI DropdownMenu component (already accessible)

### Performance Issues

**Issue:** Large JavaScript bundle
**Solution:** Code split with dynamic imports
```tsx
const DetailPanel = dynamic(() => import('./detail-panel'), { ssr: false });
```

**Issue:** Slow API calls
**Solution:** Implement React Query caching
```tsx
const { data } = useQuery({
  queryKey: ['cpus'],
  queryFn: fetchCPUs,
  staleTime: 5 * 60 * 1000,
});
```

**Issue:** Layout shifts (CLS)
**Solution:** Reserve space for images and dynamic content
```tsx
<Image width={64} height={64} src="/cpu.png" alt="..." />
```

### Cross-Browser Issues

**Issue:** Flexbox/Grid not working in older browsers
**Solution:** Add fallback styles or use autoprefixer

**Issue:** Recharts not rendering in Safari
**Solution:** Check console for SVG errors, ensure polyfills loaded

---

**Checklist Version:** 1.0
**Last Updated:** 2025-11-06
**Phase:** CPU Page Reskin - Phase 4C (Accessibility & Performance Validation)
**Status:** Ready for Validation
