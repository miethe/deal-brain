# Accessibility Testing Quick Start

**Goal**: Verify WCAG 2.1 Level AA compliance for Phase 4 features

---

## 1. Start the Server (1 minute)

```bash
make web
# Wait for server to start at http://localhost:3020
```

---

## 2. Run Automated Tests (5 minutes)

```bash
pnpm test:e2e:a11y
```

**Expected Output**:
```
✓ Public Deal Page (3 tests)
✓ Collections List (3 tests)
✓ Collection Workspace (2 tests)
✓ Share Modal (3 tests)
✓ Collection Selector (2 tests)
✓ Color Contrast (1 test)
✓ Keyboard Navigation (2 tests)
✓ Mobile Touch Targets (1 test)
```

---

## 3. View Results (2 minutes)

```bash
pnpm test:e2e:report
```

Opens HTML report in browser.

---

## 4. Fix Any Violations (varies)

If tests fail, check console output:

```
❌ Accessibility violations found in Share Modal:

  SERIOUS: color-contrast
  Description: Elements must have insufficient color contrast
  Help: https://dequeuniversity.com/rules/axe/4.8/color-contrast
  Elements (1):
    1. <p class="text-gray-400">Share this listing</p>
```

**Fix**:
1. Click the "Help" URL
2. Find the element (use "Target" selector)
3. Apply recommended fix
4. Re-run tests

**Common Fixes**: See `docs/testing/accessibility-patterns.md`

---

## 5. Manual Testing (4-6 hours)

**Checklist**: `docs/testing/accessibility-checklist.md`

**Priority Tests**:
1. **Keyboard Navigation** (30 min)
   - Tab through all pages
   - Verify focus visible
   - Test Escape closes modals

2. **Screen Reader** (1-2 hours)
   - Download NVDA (Windows) or use VoiceOver (Mac)
   - Navigate public deal page
   - Test share modal
   - Test collections

3. **Color Contrast** (30 min)
   - Use Color Contrast Analyzer
   - Check all text: 4.5:1 minimum
   - Check buttons/icons: 3:1 minimum

4. **Touch Targets** (30 min)
   - Resize browser to 375px width (iPhone SE)
   - Measure button sizes (should be ≥ 44px)

5. **Zoom/Reflow** (30 min)
   - Zoom to 200% (Cmd/Ctrl + Plus)
   - Resize to 320px width
   - Verify no horizontal scroll

---

## 6. Update Audit Report (1 hour)

**File**: `docs/testing/accessibility-audit-report.md`

Fill in:
- Test results (pass/fail)
- Violations found
- Fixes applied
- Manual test results

---

## 7. Get Sign-Off

Share audit report with QA/stakeholders.

---

## Need Help?

- **Full Testing Guide**: `docs/testing/accessibility-testing-guide.md`
- **Manual Checklist**: `docs/testing/accessibility-checklist.md`
- **Component Patterns**: `docs/testing/accessibility-patterns.md`
- **Test Documentation**: `tests/e2e/README-ACCESSIBILITY.md`

---

## Tools Needed

**Automated**:
- ✅ Already installed: @axe-core/playwright

**Manual**:
- Screen Reader: [NVDA](https://www.nvaccess.org/) (Free) or VoiceOver (Mac built-in)
- Color Contrast: [Analyzer](https://www.tpgi.com/color-contrast-checker/) (Free)
- Browser: Chrome/Firefox/Safari DevTools

---

**Estimated Total Time**: 8-12 hours (including fixes)
