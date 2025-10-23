# Accessibility Guidelines (WCAG AA)

**Status:** Draft
**Last Updated:** October 22, 2025
**Target Standard:** WCAG 2.1 Level AA

---

## Overview

This document provides detailed accessibility requirements for the Listings Enhancement project. All components and features must meet WCAG AA compliance for keyboard navigation, screen reader support, and visual accessibility.

---

## Keyboard Navigation

### Fundamental Principles

1. **All functionality keyboard accessible** - Every interactive element reachable via keyboard
2. **Logical tab order** - Tab order follows visual layout (typically left-to-right, top-to-bottom)
3. **Visible focus indicators** - 2px ring with 2px offset on all focusable elements
4. **Keyboard shortcuts** - Standard shortcuts (Enter, Space, Esc) work as expected

### Tab Order

```
1. Breadcrumb links
2. Page heading
3. Quick action buttons (Edit, Delete, Duplicate)
4. Product image (if link)
5. Summary cards (if clickable)
6. Tab navigation buttons
7. Tab content (varies by tab)
   - Entity links
   - Buttons within content
   - Form controls
8. Modal dialogs (when open)
```

### Key Handlers

**Focus Indicators:**

```typescript
// Apply to all interactive elements
const focusStyles = "focus:ring-2 focus:ring-offset-2 focus:ring-ring focus:outline-none"

<button className={focusStyles}>Action</button>
<a href="..." className={focusStyles}>Link</a>
<input className={focusStyles} />
```

**Modal Focus Trap:**

```typescript
// When modal opens, focus first element
// When Tab pressed in modal, cycle within modal
// Esc key closes modal (restore focus to trigger)

useEffect(() => {
  if (isOpen) {
    handleFocusTrap(modalRef.current)
  }
}, [isOpen])
```

**Tab Navigation:**

```typescript
// Allow arrow keys in tab bar
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'ArrowRight') {
    focusNextTab()
    e.preventDefault()
  } else if (e.key === 'ArrowLeft') {
    focusPreviousTab()
    e.preventDefault()
  }
}
```

---

## Screen Reader Support

### Semantic HTML

**Use Semantic Elements:**

```html
<!-- Good: Semantic -->
<nav aria-label="Breadcrumb">
  <ol>
    <li><a href="/dashboard">Dashboard</a></li>
    <li><a href="/listings">Listings</a></li>
    <li aria-current="page">Intel NUC i7</li>
  </ol>
</nav>

<!-- Avoid: Non-semantic -->
<div className="breadcrumb">
  <span onClick={goto}>/</span>
  ...
</div>
```

### ARIA Labels & Attributes

**Icon Buttons - Always Provide aria-label:**

```typescript
// Icon buttons NEED labels for screen readers
<button aria-label="Edit listing">
  <EditIcon />
</button>

<button aria-label="Delete listing" className="text-red-600">
  <TrashIcon />
</button>

<button aria-label="Duplicate listing">
  <CopyIcon />
</button>
```

**Form Labels - Link Inputs to Labels:**

```html
<label htmlFor="cpu-select">CPU:</label>
<select id="cpu-select">
  <option>Intel Core i7-1165G7</option>
  ...
</select>
```

**Sections - Label Regions:**

```tsx
<section aria-labelledby="hardware-heading">
  <h2 id="hardware-heading">Hardware</h2>
  {/* Hardware specs here */}
</section>
```

**Badges - Add aria-label:**

```tsx
<Badge
  variant="outline"
  aria-label={`Belongs to ${ruleGroup} rule group`}
>
  {ruleGroup}
</Badge>
```

### Live Regions

**For Dynamic Content Updates:**

```tsx
<div aria-live="polite" aria-atomic="true">
  {toastMessage}
</div>

<div aria-live="assertive" aria-atomic="true">
  {errorMessage}
</div>
```

**Modal Announcements:**

```tsx
<Dialog>
  <DialogContent role="alertdialog" aria-labelledby="dialog-title">
    <DialogHeader>
      <DialogTitle id="dialog-title">
        Confirm Delete
      </DialogTitle>
    </DialogHeader>
    ...
  </DialogContent>
</Dialog>
```

---

## Visual Accessibility

### Color Contrast

**Text Contrast Requirements:**

- **Normal text:** ≥ 4.5:1 (WCAG AA)
- **Large text (18pt+):** ≥ 3:1
- **UI components and graphics:** ≥ 3:1

**Verify With Tools:**

- WebAIM Contrast Checker
- Chrome DevTools Lighthouse
- Color Contrast Analyzer

**Examples - DO NOT rely on color alone:**

```
❌ WRONG:
Green text = savings, Red text = premium

✅ CORRECT:
✓ Green + checkmark = savings
⚠ Red + warning icon = premium
(also include text label)
```

### Focus Indicators

**Requirements:**

- Minimum 2px thick outline
- Minimum 2px offset from element
- Sufficient contrast with background (≥ 3:1)
- Must be visible at all zoom levels

**Implementation:**

```css
/* Tailwind default (excellent) */
focus:ring-2 focus:ring-offset-2 focus:ring-ring

/* Results in: 2px ring, 2px offset, theme color */
/* Adjust if needed for specific backgrounds */
```

### Text Sizing & Spacing

**Font Size Minimums:**

- Body text: 16px minimum
- Small text: 14px minimum
- Avoid < 12px for primary content
- Buttons and interactive: 16px minimum

**Line Height:**

- Body: `line-height: 1.5` (1.5x font size)
- Helps readability, especially for dyslexic users
- Tailwind: `leading-relaxed` or `leading-loose`

**Letter Spacing:**

- Tailwind: `tracking-normal` (default) or `tracking-wide`
- Especially important for all-caps text
- Example: `tracking-wide` for uppercase labels

### Resizable Text

**User Should Be Able To:**

- Increase text size up to 200%
- Without losing functionality
- Without horizontal scrolling

**Implementation:**

```css
/* Use relative units (rem, em) not fixed px */
font-size: 1rem;    /* Good */
font-size: 16px;    /* Less flexible */

/* Test with Chrome DevTools */
Cmd+Shift+P → "Rendering" → "Emulate CSS Media Feature prefers-reduced-motion"
```

---

## Touch Target Size

### Minimum Size

- Interactive elements: **44×44px minimum**
- Applies to: buttons, links, form controls
- Applies on all devices including desktop

**Implementation:**

```tsx
<button className="h-10 px-4">  {/* 40px height, adequate width */}
  Action
</button>

<a className="py-2 px-3">  {/* 16px padding = 48px interactive area */}
  Link
</a>
```

### Spacing Between Targets

- Minimum 8px between interactive elements
- Prevents accidental misclicks
- Especially important on mobile

```tsx
<div className="space-x-2">  {/* 8px gap between buttons */}
  <button>Save</button>
  <button>Cancel</button>
</div>
```

---

## Forms & Inputs

### Label Association

```html
<!-- REQUIRED: Every input must have associated label -->

<!-- Method 1: htmlFor/id -->
<label htmlFor="email">Email:</label>
<input id="email" type="email" />

<!-- Method 2: Wrapping -->
<label>
  Email:
  <input type="email" />
</label>

<!-- Method 3: aria-label (only when visual label impossible) -->
<input aria-label="Email" placeholder="Email" />
```

### Error Messages

```tsx
<div>
  <label htmlFor="cpu">CPU:
    <span aria-label="required">*</span>
  </label>
  <input
    id="cpu"
    aria-required="true"
    aria-invalid={hasError}
    aria-describedby={hasError ? "cpu-error" : undefined}
  />
  {hasError && (
    <span id="cpu-error" role="alert">
      CPU selection required
    </span>
  )}
</div>
```

---

## Images

### Alt Text Requirements

**Every image must have alt text:**

```tsx
<Image
  src={thumbnail}
  alt="Intel NUC i7-1165G7 - 16GB RAM, 512GB SSD mini PC"
  width={400}
  height={400}
/>
```

**Alt Text Best Practices:**

- Descriptive: Include key details about the product
- Concise: 100-150 characters
- Functional: Convey the image's purpose
- Don't repeat in caption/surrounding text
- Don't start with "image of..."

**Decorative Images:**

```tsx
// Decorative icon - empty alt text
<Icon aria-hidden="true" />

// Or explicitly hidden
<img src="decoration.svg" alt="" aria-hidden="true" />
```

---

## Modals & Dialogs

### Focus Management

```typescript
// When modal opens:
1. Move focus to first focusable element or close button
2. Trap focus within modal (Tab cycles within)
3. Esc key closes modal and restores focus

// When modal closes:
1. Focus returns to trigger button
2. Page content behind modal may be dimmed/disabled
```

### Announcement

```tsx
<Dialog>
  <DialogContent
    role="alertdialog"
    aria-labelledby="dialog-title"
    aria-describedby="dialog-description"
  >
    <DialogHeader>
      <DialogTitle id="dialog-title">Delete Listing?</DialogTitle>
    </DialogHeader>
    <p id="dialog-description">
      This action cannot be undone.
    </p>
  </DialogContent>
</Dialog>
```

---

## Testing & Verification

### Automated Testing (Continuous)

**Tools:**
- **axe-core** - In CI/CD pipeline
- **Lighthouse** - Build performance audits
- **WAVE** - Browser extension for manual checks

**In CI/CD:**

```yaml
# Example: GitHub Actions
- name: Accessibility Testing
  run: |
    npm run test:a11y
    npm run lint:a11y
```

### Manual Testing (Every Release)

**Screen Readers:**
- **Windows:** NVDA (free, open source)
- **macOS:** VoiceOver (built-in)
- **iOS:** VoiceOver (built-in)
- **Android:** TalkBack (built-in)

**Keyboard Navigation:**

```
1. Tab through entire page - reach all interactive elements?
2. Shift+Tab - reverse navigation works?
3. Enter/Space - activates buttons/links?
4. Esc - closes modals?
5. Arrow keys - work in tab bars/menus?
```

**Color & Contrast:**

```
1. Use WebAIM Contrast Checker on key elements
2. Zoom to 200% - still readable?
3. Test with color blindness simulator
4. Print in grayscale - still understandable?
```

### Test Scenarios

**Detail Page:**
- [ ] Navigate entire page with keyboard only
- [ ] All headings announced by screen reader
- [ ] All button labels clear and descriptive
- [ ] Entity links announce destination
- [ ] Tabs keyboard accessible and announced
- [ ] Modal focus trap working

**Valuation Breakdown Modal:**
- [ ] Modal title announced
- [ ] Section headers announced ("Active Contributors", "Inactive Rules")
- [ ] All rule cards navigable with Tab
- [ ] Rule names clickable with keyboard
- [ ] Collapse/expand buttons keyboard accessible
- [ ] Focus trap prevents focus from leaving modal
- [ ] Esc key closes modal

---

## Accessibility Checklist

### Design Phase

- [ ] Color not sole indicator of information
- [ ] 4.5:1 color contrast minimum for text
- [ ] 44×44px minimum touch targets
- [ ] Logical layout for tab order
- [ ] Focus indicators visible and clear
- [ ] No reliance on motion/animation alone

### Development Phase

- [ ] Semantic HTML elements used
- [ ] Form inputs have associated labels
- [ ] Icon buttons have aria-labels
- [ ] Section regions have labels
- [ ] Image alt text provided
- [ ] Modal focus trap implemented
- [ ] Live regions for dynamic content
- [ ] ARIA attributes where needed

### Testing Phase

- [ ] axe-core: Zero critical/serious violations
- [ ] Keyboard: Navigate all functionality
- [ ] Screen reader: NVDA or VoiceOver
- [ ] Mobile: Touch targets adequate
- [ ] Zoom: 200% without horizontal scroll
- [ ] Color: Contrast verified
- [ ] Motion: No required animations

### Post-Launch

- [ ] User feedback monitored
- [ ] Issue response time < 48 hours
- [ ] Accessibility bug priority: Critical
- [ ] Quarterly audit scheduled
- [ ] Team training on a11y best practices

---

## Resources

### Standards
- **WCAG 2.1:** https://www.w3.org/WAI/WCAG21/quickref/
- **WAI-ARIA:** https://www.w3.org/WAI/ARIA/apg/

### Tools
- **axe DevTools:** Browser extension for testing
- **WAVE:** Web accessibility evaluation tool
- **Lighthouse:** Built-in Chrome DevTools
- **NVDA:** Free screen reader for Windows
- **WebAIM:** Color contrast checker

### Learning
- **Web Accessibility by Google:** https://www.udacity.com/course/web-accessibility--ud891
- **A11ycasts:** YouTube series by Google Chrome
- **MDN Accessibility:** https://developer.mozilla.org/en-US/docs/Web/Accessibility

---

## Related Documentation

- **[UI/UX Design](./ui-ux.md)** - Visual accessibility details
- **[Technical Architecture](./technical-design.md)** - Implementation patterns
- **[Technical Requirements](../requirements/technical.md)** - General accessibility needs
