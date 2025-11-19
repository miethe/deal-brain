---
title: "Accessibility Testing Checklist (WCAG 2.1 AA)"
description: "Manual accessibility testing checklist for Phase 4 collections and sharing features"
audience: [qa, developers, ai-agents]
tags: [accessibility, wcag, testing, a11y, phase-4]
created: 2025-11-18
updated: 2025-11-18
category: "test-documentation"
status: published
related:
  - /docs/testing/accessibility-audit-report.md
---

# Accessibility Testing Checklist

## Overview

This checklist ensures WCAG 2.1 Level AA compliance for all Phase 4 features (collections, sharing, public deal pages).

**Standard**: WCAG 2.1 Level AA
**Scope**: Collections list, collection workspace, public deal page, share modal, collection selector modal

---

## 1. Keyboard Navigation

### 1.1 Tab Navigation

**Collections List (`/collections`)**
- [ ] Can reach "New Collection" button via Tab
- [ ] Can reach all collection cards via Tab
- [ ] Tab order is logical (top to bottom, left to right)
- [ ] Can activate collection card with Enter/Space
- [ ] Can reach "Load More" button (if present)

**Collection Workspace (`/collections/[id]`)**
- [ ] Can reach view toggle buttons (Table/Cards) via Tab
- [ ] Can reach all filter/sort controls via Tab
- [ ] Can reach all items in table/grid via Tab
- [ ] Can reach action buttons (Remove, Share, etc.) via Tab
- [ ] Tab order follows visual layout

**Public Deal Page (`/deals/[id]/[token]`)**
- [ ] Can reach "Add to Collection" button via Tab
- [ ] Can reach "View Source" or external links via Tab
- [ ] Can reach all interactive summary cards via Tab
- [ ] Tab order is logical and predictable

**Share Modal**
- [ ] Can reach all tabs (Link, Email, etc.) via Tab
- [ ] Can reach "Copy Link" button via Tab
- [ ] Can reach "Generate QR Code" button (if present) via Tab
- [ ] Can reach "Close" button via Tab
- [ ] Focus traps within modal (doesn't escape to background)

**Collection Selector Modal**
- [ ] Can reach all collection checkboxes via Tab
- [ ] Can reach "New Collection" button via Tab
- [ ] Can reach "Save" and "Cancel" buttons via Tab
- [ ] Focus traps within modal

### 1.2 Keyboard Shortcuts

- [ ] **Escape** closes all modals (Share, Collection Selector)
- [ ] **Enter** activates focused buttons
- [ ] **Space** activates focused buttons and toggles checkboxes
- [ ] **Arrow keys** navigate within select dropdowns (if present)

### 1.3 Focus Management

- [ ] Opening modal moves focus to modal
- [ ] Closing modal returns focus to trigger element
- [ ] No keyboard traps (can always escape)
- [ ] Focus never gets lost (always on a visible element)

---

## 2. Focus Indicators

### 2.1 Visibility
- [ ] All interactive elements show visible focus indicator
- [ ] Focus indicator has sufficient contrast (≥ 3:1 against background)
- [ ] Focus indicator is at least 2px thick or clear outline
- [ ] Focus indicator works in both light and dark themes

### 2.2 Interactive Elements to Check
- [ ] Buttons (primary, secondary, outline, ghost)
- [ ] Links (inline, navigation)
- [ ] Form inputs (text, checkbox, select)
- [ ] Cards/tiles (clickable collection cards)
- [ ] Table rows (if clickable)
- [ ] Tabs (in Share modal)

---

## 3. Screen Reader Compatibility

### 3.1 Images
- [ ] All product images have meaningful `alt` text
- [ ] Decorative images have empty `alt=""` or `aria-hidden="true"`
- [ ] Fallback/placeholder images have descriptive alt text

### 3.2 Buttons and Links
- [ ] All buttons have accessible names (text or `aria-label`)
- [ ] Icon-only buttons have `aria-label` (e.g., "Share", "Close")
- [ ] External links indicate they open in new window (if applicable)
- [ ] "Add to Collection" button has clear label

### 3.3 Form Elements
- [ ] All inputs have associated `<label>` elements
- [ ] Required fields indicated (text + visual indicator)
- [ ] Error messages associated with inputs (`aria-describedby`)
- [ ] Placeholder text not used as sole label

### 3.4 ARIA Attributes
- [ ] Modals have `role="dialog"` and `aria-modal="true"`
- [ ] Modal titles have `aria-labelledby` or `aria-label`
- [ ] Live regions use `aria-live` for dynamic content (toasts, loading states)
- [ ] Buttons indicate state with `aria-pressed` (if toggle buttons)
- [ ] Expandable sections use `aria-expanded`

### 3.5 Headings
- [ ] Page has exactly one `<h1>` (main title)
- [ ] Heading hierarchy is logical (h1 → h2 → h3, no skips)
- [ ] Headings describe content accurately
- [ ] Section headings present for major sections

### 3.6 Landmarks
- [ ] Page has `<main>` landmark
- [ ] Navigation uses `<nav>` element
- [ ] Forms use `<form>` element
- [ ] Complementary content uses `<aside>` (if applicable)

---

## 4. Color Contrast

### 4.1 Text Contrast (WCAG AA: 4.5:1 for normal, 3:1 for large)

**Normal Text (< 18pt regular, < 14pt bold)**
- [ ] Body text meets 4.5:1 contrast
- [ ] Link text meets 4.5:1 contrast
- [ ] Button text meets 4.5:1 contrast
- [ ] Form labels meet 4.5:1 contrast
- [ ] Error messages meet 4.5:1 contrast

**Large Text (≥ 18pt regular, ≥ 14pt bold)**
- [ ] Headings meet 3:1 contrast
- [ ] Large button text meets 3:1 contrast

**UI Components (WCAG AA: 3:1)**
- [ ] Button borders meet 3:1 contrast
- [ ] Input borders meet 3:1 contrast
- [ ] Focus indicators meet 3:1 contrast
- [ ] Icons meet 3:1 contrast (if meaningful)

### 4.2 Color Alone
- [ ] Information not conveyed by color alone
- [ ] Validation errors use text + icon, not just red color
- [ ] "Good deal" badges use text + color
- [ ] Links distinguishable without color (underline, icon, etc.)

---

## 5. Touch Targets (Mobile)

**Viewport**: 375x667px (iPhone SE)

### 5.1 Minimum Size (WCAG 2.1 AA: 44x44px)
- [ ] "New Collection" button ≥ 44x44px
- [ ] Collection card links/buttons ≥ 44x44px
- [ ] "Add to Collection" button ≥ 44x44px
- [ ] Modal close buttons ≥ 44x44px
- [ ] Checkboxes with labels ≥ 44x44px (clickable area)
- [ ] Table action buttons ≥ 44x44px

### 5.2 Spacing
- [ ] Adequate spacing between touch targets (≥ 8px)
- [ ] No overlapping touch areas
- [ ] Targets don't accidentally trigger adjacent elements

---

## 6. Forms and Inputs

### 6.1 Labels and Instructions
- [ ] All inputs have visible labels
- [ ] Labels are associated with inputs (for/id or wrapping)
- [ ] Required fields clearly indicated
- [ ] Help text provided for complex inputs

### 6.2 Validation
- [ ] Error messages are clear and specific
- [ ] Errors announced to screen readers (`aria-describedby`, `aria-invalid`)
- [ ] Error summary at top of form (if multiple errors)
- [ ] Success messages announced to screen readers

### 6.3 Autocomplete
- [ ] Appropriate `autocomplete` attributes on inputs (name, email, etc.)
- [ ] Autocomplete works with browser autofill

---

## 7. Responsive Design

### 7.1 Reflow (WCAG 2.1 AA: No horizontal scroll at 320px width)
- [ ] Content reflows without horizontal scrolling at 320px width
- [ ] All functionality available on mobile
- [ ] No content loss at small viewports
- [ ] Cards stack vertically on mobile

### 7.2 Text Resizing
- [ ] Text can resize to 200% without loss of content or functionality
- [ ] No overlapping text at 200% zoom
- [ ] Buttons/controls remain usable at 200% zoom

### 7.3 Orientation
- [ ] Content works in both portrait and landscape
- [ ] No functionality restricted to specific orientation
- [ ] Layout adapts to orientation changes

---

## 8. Content Readability

### 8.1 Language
- [ ] Page has `lang` attribute (`<html lang="en">`)
- [ ] Language changes marked with `lang` attribute (if applicable)

### 8.2 Reading Order
- [ ] Visual order matches DOM order
- [ ] Content makes sense when linearized
- [ ] Tables linearize logically (row by row)

### 8.3 Link Purpose
- [ ] Link text describes destination
- [ ] "Click here" and "Read more" avoided (or clarified with context)
- [ ] External links indicated

---

## 9. Animations and Timing

### 9.1 Motion Reduction
- [ ] Respects `prefers-reduced-motion` setting
- [ ] Animations can be paused or disabled
- [ ] No auto-playing animations > 5 seconds

### 9.2 Timing
- [ ] No time limits on interactions
- [ ] If share link expires, expiration clearly communicated
- [ ] Users can extend time limits (if any)

---

## 10. Modals and Dialogs

### 10.1 Structure
- [ ] Modal has `role="dialog"`
- [ ] Modal has `aria-modal="true"`
- [ ] Modal has accessible title (`aria-labelledby` or `aria-label`)
- [ ] Modal description provided if needed (`aria-describedby`)

### 10.2 Behavior
- [ ] Opening modal moves focus to modal
- [ ] Focus trapped within modal
- [ ] Escape key closes modal
- [ ] Closing modal returns focus to trigger
- [ ] Background content inert (not focusable/clickable)

### 10.3 Close Mechanisms
- [ ] Close button visible and accessible
- [ ] Escape key works
- [ ] Click outside closes modal (or explicitly disabled)
- [ ] All close methods accessible via keyboard

---

## 11. Data Tables (if present in Collection Workspace)

### 11.1 Structure
- [ ] Table has `<caption>` or `aria-label`
- [ ] Header cells use `<th>` with `scope` attribute
- [ ] Data cells use `<td>`
- [ ] Complex tables have proper associations (`headers`, `id`)

### 11.2 Sorting
- [ ] Sort controls keyboard accessible
- [ ] Sort state communicated to screen readers (`aria-sort`)
- [ ] Visual indicator for sorted column

### 11.3 Selection
- [ ] Checkboxes for row selection keyboard accessible
- [ ] "Select All" checkbox has clear label
- [ ] Selected state communicated to screen readers

---

## 12. Error Handling

### 12.1 Error Identification
- [ ] Errors clearly identified
- [ ] Error messages specific and helpful
- [ ] Errors announced to screen readers

### 12.2 Error Suggestion
- [ ] Suggestions provided for correcting errors
- [ ] Examples given for complex inputs

### 12.3 Error Prevention
- [ ] Confirmation required for destructive actions (delete collection)
- [ ] User can review/edit before submission

---

## Testing Tools

### Automated Tools
- **axe DevTools**: Browser extension for automated scanning
- **WAVE**: Browser extension for visual feedback
- **Lighthouse**: Chrome DevTools accessibility audit
- **Playwright + axe-core**: Automated E2E accessibility testing

### Manual Testing Tools
- **Keyboard**: Test all interactions with Tab, Enter, Space, Escape
- **Screen Reader**: NVDA (Windows), JAWS (Windows), VoiceOver (macOS/iOS), TalkBack (Android)
- **Color Contrast Analyzer**: Standalone app or browser extension
- **Zoom**: Test at 200% browser zoom
- **Mobile Devices**: Test on actual devices (iPhone, Android)

---

## Quick Pass/Fail Criteria

### Must Pass (Critical)
- [ ] No critical or serious violations in automated axe scan
- [ ] All interactive elements keyboard accessible
- [ ] All images have alt text
- [ ] All form inputs have labels
- [ ] Text contrast meets 4.5:1 (normal) / 3:1 (large)
- [ ] Focus indicators visible on all elements
- [ ] Modals trap focus and close on Escape

### Should Pass (Important)
- [ ] Touch targets ≥ 44x44px on mobile
- [ ] Heading hierarchy logical
- [ ] No horizontal scroll at 320px width
- [ ] Content works at 200% zoom
- [ ] Animations respect `prefers-reduced-motion`

---

## Testing Checklist Status

- [ ] **Public Deal Page** - Fully tested
- [ ] **Collections List** - Fully tested
- [ ] **Collection Workspace** - Fully tested
- [ ] **Share Modal** - Fully tested
- [ ] **Collection Selector Modal** - Fully tested
- [ ] **Mobile Views** - Fully tested
- [ ] **Dark Theme** - Fully tested
- [ ] **Screen Reader Testing** - Completed (if available)

---

## Notes

Use this section to document any findings, exceptions, or follow-up items during manual testing:

```
Example:
- [2025-11-18] Share modal: Copy button focus indicator needs better contrast in dark mode
- [2025-11-18] Collection cards: Touch target is 42px, needs 2px increase for AA compliance
- [2025-11-18] Public deal page: External link icon needs aria-hidden="true" (decorative)
```

---

## Sign-Off

**Tested By**: _________________
**Date**: _________________
**Result**: ☐ Pass  ☐ Pass with minor issues  ☐ Fail (requires fixes)

**Summary**:
