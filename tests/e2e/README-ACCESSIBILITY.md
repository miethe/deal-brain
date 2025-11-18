# Accessibility Testing

## Overview

Automated accessibility tests for Phase 4 features using `@axe-core/playwright` to ensure WCAG 2.1 Level AA compliance.

## Quick Start

```bash
# Start web server
make web

# Run accessibility tests
pnpm test:e2e:a11y

# Run with UI (interactive)
pnpm test:e2e:a11y:ui

# View results
pnpm test:e2e:report
```

## Test File

**Location**: `tests/e2e/accessibility-audit.spec.ts`

**Coverage**:
- ✅ Public deal page (`/deals/[id]/[token]`)
- ✅ Collections list page (`/collections`)
- ✅ Collection workspace (`/collections/[id]`)
- ✅ Share modal
- ✅ Collection selector modal
- ✅ Color contrast checks
- ✅ Keyboard navigation
- ✅ Mobile touch targets (44x44px minimum)

## Test Suites

### 1. Public Deal Page
- Automated axe-core scan (zero critical/serious violations)
- ARIA labels verification
- Heading hierarchy check
- Focus management

### 2. Collections List
- Automated axe-core scan
- Keyboard accessible collection cards
- Accessible "New Collection" button

### 3. Collection Workspace
- Automated axe-core scan
- Accessible table/grid controls
- Keyboard navigation through items

### 4. Share Modal
- Automated axe-core scan
- Focus trapping verification
- Escape key closes modal
- Focus restoration on close

### 5. Collection Selector Modal
- Automated axe-core scan
- Accessible checkboxes with labels

### 6. Color Contrast
- All text meets 4.5:1 ratio (normal text)
- All large text meets 3:1 ratio
- UI components meet 3:1 ratio

### 7. Keyboard Navigation
- Tab order is logical
- All interactive elements reachable
- Focus indicators visible

### 8. Mobile Touch Targets
- All buttons/links ≥ 44x44 CSS pixels
- Adequate spacing between targets

## Running Specific Tests

```bash
# Test single component
pnpm test:e2e:a11y -g "Public Deal Page"
pnpm test:e2e:a11y -g "Collections List"
pnpm test:e2e:a11y -g "Share Modal"

# Test specific aspect
pnpm test:e2e:a11y -g "Keyboard Navigation"
pnpm test:e2e:a11y -g "Color Contrast"
pnpm test:e2e:a11y -g "Mobile Touch Targets"

# Test in specific browser
pnpm test:e2e:a11y --project=chromium
pnpm test:e2e:a11y --project=webkit
```

## Understanding Results

### Pass Criteria

Tests pass when:
- **Zero critical or serious violations** from axe-core
- All keyboard navigation works correctly
- All focus indicators are visible
- Color contrast meets WCAG AA minimums
- Touch targets meet 44x44px minimum on mobile

### Violation Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| **Critical** | Serious accessibility barrier | Must fix immediately |
| **Serious** | Significant barrier for some users | Must fix for WCAG AA compliance |
| **Moderate** | Noticeable issue | Should fix |
| **Minor** | Slight inconvenience | Nice to fix |

### Example Violation Output

```
❌ Accessibility violations found in Share Modal:

  CRITICAL: aria-required-children
  Description: Certain ARIA roles must contain particular children
  Help: https://dequeuniversity.com/rules/axe/4.8/aria-required-children
  Elements (1):
    1. <div role="radiogroup" class="...">
       Target: .share-modal div[role="radiogroup"]
```

**How to Fix**:
1. Click the "Help" URL for detailed guidance
2. Locate the element using the "Target" selector
3. Apply the recommended fix
4. Re-run tests to verify

## Manual Testing

Automated tests catch ~30-40% of accessibility issues. **Manual testing is required** for full compliance.

### Manual Test Checklist

See: `/docs/testing/accessibility-checklist.md`

**Key Areas**:
1. **Screen Reader Testing** - NVDA, JAWS, VoiceOver, TalkBack
2. **Zoom Testing** - 200% browser zoom, no content loss
3. **Reflow Testing** - 320px width, no horizontal scroll
4. **Reduced Motion** - Respect `prefers-reduced-motion`
5. **Actual Device Testing** - Touch targets on real phones/tablets

## Resources

### Documentation
- **Testing Guide**: `/docs/testing/accessibility-testing-guide.md`
- **Manual Checklist**: `/docs/testing/accessibility-checklist.md`
- **Audit Report**: `/docs/testing/accessibility-audit-report.md`
- **Patterns Reference**: `/docs/testing/accessibility-patterns.md`

### WCAG Guidelines
- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [Understanding WCAG 2.1](https://www.w3.org/WAI/WCAG21/Understanding/)

### Tools
- [axe DevTools](https://www.deque.com/axe/devtools/) - Browser extension
- [WAVE](https://wave.webaim.org/) - Web accessibility tool
- [Color Contrast Analyzer](https://www.tpgi.com/color-contrast-checker/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - Chrome DevTools

## Common Issues and Fixes

### Missing Accessible Names

```tsx
// ❌ Bad
<button><XIcon /></button>

// ✅ Good
<button aria-label="Close modal"><XIcon /></button>
```

### Insufficient Color Contrast

```tsx
// ❌ Bad (3.2:1 contrast)
<p className="text-gray-400">Price: $299</p>

// ✅ Good (4.5:1+ contrast)
<p className="text-gray-700 dark:text-gray-200">Price: $299</p>
```

### Missing Form Labels

```tsx
// ❌ Bad
<input type="text" placeholder="Collection name" />

// ✅ Good
<label htmlFor="name">Collection name</label>
<input type="text" id="name" />
```

### Touch Target Too Small

```tsx
// ❌ Bad (32px button)
<button className="p-1">Click me</button>

// ✅ Good (44px+ button)
<button className="p-3 min-h-[44px] min-w-[44px]">Click me</button>
```

## CI Integration

Add to GitHub Actions workflow:

```yaml
# .github/workflows/accessibility.yml
name: Accessibility Tests

on:
  pull_request:
    paths:
      - 'apps/web/**'

jobs:
  a11y:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: pnpm install
      - run: pnpm test:e2e:a11y
```

## Troubleshooting

### Web Server Not Running

**Error**: `Error: connect ECONNREFUSED 127.0.0.1:3020`

**Fix**:
```bash
make web
# or
pnpm --filter web dev
```

### Playwright Browsers Not Installed

**Error**: `Executable doesn't exist at /path/to/chromium`

**Fix**:
```bash
pnpm exec playwright install
```

### Tests Timeout

**Fix**: Increase timeout in test:
```typescript
await page.waitForSelector('h1', { timeout: 10000 });
```

## Next Steps

1. ✅ Run automated accessibility tests
2. ⏳ Review violations and prioritize fixes
3. ⏳ Fix critical and serious violations
4. ⏳ Conduct manual screen reader testing
5. ⏳ Test zoom and reflow at 200%
6. ⏳ Test on actual mobile devices
7. ⏳ Update audit report with results
8. ⏳ Get QA sign-off

---

**For detailed guidance**, see:
- `/docs/testing/accessibility-testing-guide.md` - Complete testing guide
- `/docs/testing/accessibility-checklist.md` - Manual testing checklist
- `/docs/testing/accessibility-patterns.md` - Component patterns reference
