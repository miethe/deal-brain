---
title: "Accessibility Testing Guide"
description: "Complete guide to running accessibility audits for Deal Brain Phase 4 features"
audience: [developers, qa, ai-agents]
tags: [accessibility, testing, wcag, guide, phase-4]
created: 2025-11-18
updated: 2025-11-18
category: "test-documentation"
status: published
related:
  - /docs/testing/accessibility-checklist.md
  - /docs/testing/accessibility-audit-report.md
  - /tests/e2e/accessibility-audit.spec.ts
---

# Accessibility Testing Guide

## Overview

This guide explains how to run automated and manual accessibility tests for Phase 4 features (collections, sharing, public deal pages) to ensure WCAG 2.1 Level AA compliance.

---

## Quick Start

### 1. Prerequisites

```bash
# Install dependencies (if not already done)
pnpm install

# Ensure @axe-core/playwright is installed
pnpm list @axe-core/playwright
```

### 2. Start the Application

```bash
# Option 1: Start full Docker stack
make up

# Option 2: Start web server only
make web
# or
pnpm --filter web dev
```

The web server should be running at `http://localhost:3020`.

### 3. Run Accessibility Tests

```bash
# Run all accessibility tests
pnpm test:e2e tests/e2e/accessibility-audit.spec.ts

# Run with UI (interactive mode)
pnpm test:e2e:ui tests/e2e/accessibility-audit.spec.ts

# Run in headed mode (see browser)
pnpm test:e2e:headed tests/e2e/accessibility-audit.spec.ts

# Run using the convenience script
./scripts/run-accessibility-audit.sh
```

### 4. View Results

```bash
# View HTML report
pnpm test:e2e:report

# Report will open in your browser
# File location: playwright-report/index.html
```

---

## Test Structure

### Automated Tests (`tests/e2e/accessibility-audit.spec.ts`)

The accessibility test suite covers:

1. **Public Deal Page** (`/deals/[id]/[token]`)
   - No accessibility violations
   - Proper ARIA labels
   - Heading hierarchy

2. **Collections List Page** (`/collections`)
   - No accessibility violations
   - Accessible collection cards
   - Accessible "New Collection" button

3. **Collection Workspace** (`/collections/[id]`)
   - No accessibility violations
   - Accessible table/grid controls

4. **Share Modal**
   - No accessibility violations
   - Focus trapping
   - Escape key closes modal

5. **Collection Selector Modal**
   - No accessibility violations
   - Accessible checkboxes

6. **Color Contrast**
   - All text meets minimum contrast ratios

7. **Keyboard Navigation**
   - Tab navigation works throughout
   - Visible focus indicators

8. **Mobile Touch Targets**
   - All touch targets ≥ 44x44px

---

## Running Specific Test Suites

### Test Individual Components

```bash
# Public Deal Page only
pnpm test:e2e tests/e2e/accessibility-audit.spec.ts -g "Public Deal Page"

# Collections List only
pnpm test:e2e tests/e2e/accessibility-audit.spec.ts -g "Collections List"

# Share Modal only
pnpm test:e2e tests/e2e/accessibility-audit.spec.ts -g "Share Modal"

# Keyboard Navigation only
pnpm test:e2e tests/e2e/accessibility-audit.spec.ts -g "Keyboard Navigation"

# Mobile Touch Targets only
pnpm test:e2e tests/e2e/accessibility-audit.spec.ts -g "Mobile Touch Targets"
```

### Test Across Browsers

```bash
# Test in Chromium only
pnpm test:e2e tests/e2e/accessibility-audit.spec.ts --project=chromium

# Test in WebKit only
pnpm test:e2e tests/e2e/accessibility-audit.spec.ts --project=webkit

# Test in all configured browsers
pnpm test:e2e tests/e2e/accessibility-audit.spec.ts
```

---

## Understanding Test Results

### Pass Criteria

Tests pass when:
- **Zero critical or serious violations** from axe-core
- All keyboard navigation works
- All focus indicators visible
- Color contrast meets WCAG AA (4.5:1 for text, 3:1 for large text/UI)
- Touch targets meet 44x44px minimum on mobile

### Failure Analysis

When tests fail, check the console output for:

```
❌ Accessibility violations found in [Component]:

  CRITICAL: aria-required-children
  Description: Certain ARIA roles must contain particular children
  Help: https://dequeuniversity.com/rules/axe/4.8/aria-required-children
  Elements (1):
    1. <div role="radiogroup" class="...">
       Target: .collection-selector-modal div[role="radiogroup"]
```

**Key Information**:
- **Impact Level**: Critical, Serious, Moderate, Minor
- **Rule ID**: WCAG criterion violated
- **Description**: What's wrong
- **Help URL**: Detailed explanation and fix guidance
- **Elements**: Specific HTML elements with violations
- **Target**: CSS selector to locate element

---

## Manual Testing

Automated tests catch ~30-40% of accessibility issues. Manual testing is essential.

### 1. Keyboard Navigation Testing

**What to Test**:
- Tab through all interactive elements
- Shift+Tab to reverse
- Enter/Space to activate buttons
- Escape to close modals
- Arrow keys in select dropdowns

**Checklist**: See `docs/testing/accessibility-checklist.md` Section 1

### 2. Screen Reader Testing

**Tools**:
- **Windows**: [NVDA](https://www.nvaccess.org/) (Free) or JAWS (Paid)
- **macOS**: VoiceOver (Built-in: Cmd+F5)
- **iOS**: VoiceOver (Settings → Accessibility)
- **Android**: TalkBack (Settings → Accessibility)

**What to Test**:
- Navigate page with screen reader
- Verify all content announced
- Check button labels make sense
- Verify form inputs have labels
- Test modal announcements

**Checklist**: See `docs/testing/accessibility-checklist.md` Section 3

### 3. Color Contrast Testing

**Tools**:
- [Color Contrast Analyzer](https://www.tpgi.com/color-contrast-checker/) (Desktop app)
- [axe DevTools](https://www.deque.com/axe/devtools/) (Browser extension)
- [WAVE](https://wave.webaim.org/extension/) (Browser extension)

**Standards**:
- Normal text (< 18pt): **4.5:1** minimum
- Large text (≥ 18pt or ≥ 14pt bold): **3:1** minimum
- UI components (buttons, borders): **3:1** minimum

**Checklist**: See `docs/testing/accessibility-checklist.md` Section 4

### 4. Mobile Touch Target Testing

**Devices**:
- iPhone SE (375x667px) - Small screen baseline
- Android phone (360x640px) - Common Android size
- Tablet (768x1024px) - Larger touch targets

**Standards**:
- Minimum size: **44x44 CSS pixels**
- Adequate spacing: **≥ 8px** between targets

**Checklist**: See `docs/testing/accessibility-checklist.md` Section 5

### 5. Zoom and Reflow Testing

**What to Test**:
- Zoom to 200% in browser (Cmd/Ctrl + Plus)
- Resize window to 320px width
- Verify no horizontal scrolling
- Verify all content visible
- Verify all functionality works

**Checklist**: See `docs/testing/accessibility-checklist.md` Section 7

---

## Browser DevTools for Accessibility

### Chrome DevTools

1. Open DevTools (F12)
2. Go to "Lighthouse" tab
3. Select "Accessibility" category
4. Click "Analyze page load"
5. Review accessibility score and issues

### Firefox Accessibility Inspector

1. Open DevTools (F12)
2. Go to "Accessibility" tab
3. Enable accessibility features
4. Inspect elements for ARIA properties
5. Check contrast ratios

### Safari Web Inspector

1. Enable Developer menu (Safari → Preferences → Advanced)
2. Develop → Show Web Inspector
3. Go to "Audit" tab
4. Run "Accessibility" audit

---

## Common Issues and Fixes

### Issue: Missing Accessible Names on Icon Buttons

**Symptom**: `aria-command-name` violation
**Fix**: Add `aria-label` attribute

```tsx
// ❌ Bad
<button><XIcon /></button>

// ✅ Good
<button aria-label="Close modal"><XIcon /></button>
```

### Issue: Insufficient Color Contrast

**Symptom**: `color-contrast` violation
**Fix**: Darken text or lighten background

```tsx
// ❌ Bad (3.2:1 contrast)
<p className="text-gray-400">Price: $299</p>

// ✅ Good (4.5:1+ contrast)
<p className="text-gray-700 dark:text-gray-200">Price: $299</p>
```

### Issue: Missing Form Labels

**Symptom**: `label` violation
**Fix**: Associate label with input

```tsx
// ❌ Bad
<div>
  <input type="text" placeholder="Collection name" />
</div>

// ✅ Good
<div>
  <label htmlFor="collectionName">Collection name</label>
  <input type="text" id="collectionName" />
</div>
```

### Issue: Focus Not Trapped in Modal

**Symptom**: Tab key escapes modal to background
**Fix**: Use Radix UI Dialog (already handles focus trap)

```tsx
// ✅ Already implemented correctly
import { Dialog } from "@radix-ui/react-dialog";

<Dialog.Root open={open} onOpenChange={setOpen}>
  <Dialog.Content>
    {/* Focus is automatically trapped */}
  </Dialog.Content>
</Dialog.Root>
```

### Issue: Touch Target Too Small

**Symptom**: `target-size` violation on mobile
**Fix**: Increase button padding or min-height

```tsx
// ❌ Bad (32px button)
<button className="p-1">Click me</button>

// ✅ Good (44px+ button)
<button className="p-3 min-h-[44px] min-w-[44px]">Click me</button>
```

---

## Continuous Accessibility Testing

### Add to CI Pipeline

```yaml
# .github/workflows/accessibility.yml
name: Accessibility Tests

on:
  pull_request:
    paths:
      - 'apps/web/**'
      - 'tests/e2e/accessibility-audit.spec.ts'

jobs:
  a11y-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: pnpm install
      - run: pnpm test:e2e tests/e2e/accessibility-audit.spec.ts
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

### Pre-Commit Hook

```bash
# .husky/pre-commit
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Run accessibility tests on staged files
if git diff --cached --name-only | grep -q "apps/web/components/"; then
  echo "Running accessibility checks..."
  pnpm test:e2e tests/e2e/accessibility-audit.spec.ts --reporter=list
fi
```

---

## Resources

### WCAG Guidelines
- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [Understanding WCAG 2.1](https://www.w3.org/WAI/WCAG21/Understanding/)
- [How to Meet WCAG](https://www.w3.org/WAI/WCAG21/quickref/)

### Testing Tools
- [axe-core](https://github.com/dequelabs/axe-core) - Automated testing engine
- [axe DevTools](https://www.deque.com/axe/devtools/) - Browser extension
- [WAVE](https://wave.webaim.org/) - Web accessibility evaluation tool
- [Color Contrast Analyzer](https://www.tpgi.com/color-contrast-checker/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)

### Screen Readers
- [NVDA](https://www.nvaccess.org/) - Windows (Free)
- [JAWS](https://www.freedomscientific.com/products/software/jaws/) - Windows (Paid)
- [VoiceOver](https://www.apple.com/accessibility/voiceover/) - macOS/iOS
- [TalkBack](https://support.google.com/accessibility/android/answer/6283677) - Android

### Learning Resources
- [WebAIM](https://webaim.org/) - Web accessibility in mind
- [A11y Project](https://www.a11yproject.com/) - Community-driven accessibility resources
- [Deque University](https://dequeuniversity.com/) - Accessibility training

---

## Troubleshooting

### Tests Fail to Start

**Issue**: `Error: connect ECONNREFUSED 127.0.0.1:3020`
**Fix**: Ensure web server is running:
```bash
make web
# or
pnpm --filter web dev
```

### Tests Timeout

**Issue**: `Timeout 30000ms exceeded while waiting for selector`
**Fix**: Increase timeout in test or check if page is loading correctly:
```typescript
await page.waitForSelector('h1', { timeout: 10000 });
```

### Playwright Not Installed

**Issue**: `Executable doesn't exist at /path/to/chromium`
**Fix**: Install Playwright browsers:
```bash
pnpm exec playwright install
# or
npx playwright install chromium
```

### False Positives

**Issue**: Known third-party component violations (e.g., from libraries)
**Fix**: Exclude specific elements:
```typescript
const results = await new AxeBuilder({ page })
  .exclude('#third-party-widget')
  .analyze();
```

---

## Next Steps

1. ✅ Install @axe-core/playwright
2. ✅ Create accessibility test suite
3. ✅ Create manual testing checklist
4. ⏳ **Run automated tests** (requires web server)
5. ⏳ **Fix critical violations**
6. ⏳ **Conduct manual testing**
7. ⏳ **Update audit report** with results
8. ⏳ **Get sign-off** from QA/stakeholders

---

## Questions?

- **Automated testing**: See `tests/e2e/accessibility-audit.spec.ts`
- **Manual testing**: See `docs/testing/accessibility-checklist.md`
- **Audit results**: See `docs/testing/accessibility-audit-report.md`
- **WCAG guidelines**: https://www.w3.org/WAI/WCAG21/quickref/

For questions or issues, refer to the [Deal Brain documentation](/README.md) or consult the development team.
