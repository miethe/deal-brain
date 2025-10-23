# Design Guidance & Principles

**Project:** Deal Brain
**Version:** 1.0
**Last Updated:** 2025-10-04
**Authority:** Frontend Architecture Team

---

## Purpose

This document serves as the **source of truth** for design decisions in Deal Brain. All frontend development should align with these principles to ensure consistency, accessibility, and maintainability.

---

## Design Philosophy

### Core Principles

1. **User-First**: Every design decision prioritizes user needs and cognitive load
2. **Accessible by Default**: WCAG 2.1 AA compliance is mandatory, not optional
3. **Performance Matters**: Fast, responsive interfaces are part of good UX
4. **Consistent & Predictable**: Users should never be surprised by UI behavior
5. **Data-Dense Clarity**: Present complex information clearly without overwhelming

### Design Values

- **Clarity over cleverness** - Simple, obvious designs win
- **Consistency over novelty** - Familiar patterns reduce cognitive load
- **Function over form** - Beauty serves purpose, not ego
- **Accessibility over aesthetics** - Everyone uses the product

---

## Color System

### Semantic Color Architecture

Deal Brain uses a **semantic color system** where colors represent meaning, not appearance. This enables:
- Theme switching without code changes
- Consistent meaning across contexts
- Accessible contrast management
- Brand flexibility

### Color Meanings

| Color | Meaning | Usage |
|-------|---------|-------|
| **Primary** | Primary actions, brand identity | CTAs, active states, navigation |
| **Secondary** | Secondary actions, supporting elements | Alternative buttons, less prominent actions |
| **Destructive** | Dangerous/irreversible actions | Delete, remove, error states |
| **Success** | Positive outcomes, confirmations | Success messages, completed states |
| **Muted** | Low-priority information | Placeholders, disabled states, subtle backgrounds |
| **Accent** | Highlights, callouts | Important but non-actionable info |

### Valuation Color Language

**Special system for price-to-performance indicators:**

| Color | Meaning | Threshold | Usage |
|-------|---------|-----------|-------|
| **Dark Green** | Great deal | 25%+ savings | High-value opportunities |
| **Medium Green** | Good deal | 15-25% savings | Solid value |
| **Light Green** | Light savings | 1-15% savings | Slight advantage |
| **Light Red** | Light premium | 0-10% markup | Slight overpay |
| **Dark Red** | Premium warning | 10%+ markup | Significant overpay |
| **Gray** | Neutral | No delta | Market price |

**Design Rule:** Valuation colors MUST maintain distinctiveness in all themes.

### Color Usage Guidelines

#### DO:
✅ Use semantic colors for UI elements
✅ Maintain 4.5:1 contrast ratio for text
✅ Maintain 3:1 contrast ratio for UI components
✅ Test colors in all supported themes
✅ Use color + icon/text for information (not color alone)

#### DON'T:
❌ Hardcode hex/RGB colors in components
❌ Use color as the only indicator of meaning
❌ Override semantic colors without theme variants
❌ Create new color variables without design review
❌ Use low-contrast text for aesthetics

---

## Typography

### Font Stack

```css
/* System font stack - Fast, native, accessible */
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
             Roboto, "Helvetica Neue", Arial, sans-serif;
```

**Rationale:**
- Zero network requests (instant load)
- Native OS rendering (better performance)
- Familiar to users (reduced cognitive load)
- Excellent Unicode support

### Type Scale

| Size | Usage | CSS Class | Line Height |
|------|-------|-----------|-------------|
| 2xl | Page titles | `text-2xl` | 1.2 |
| xl | Section headings | `text-xl` | 1.3 |
| lg | Subsection headings | `text-lg` | 1.4 |
| base | Body text | `text-base` | 1.5 |
| sm | Secondary text | `text-sm` | 1.4 |
| xs | Metadata, labels | `text-xs` | 1.3 |

### Typography Guidelines

#### DO:
✅ Use consistent type scale
✅ Maintain 1.5 line height for body text
✅ Use `font-semibold` for emphasis (not `font-bold`)
✅ Use `text-muted-foreground` for secondary text
✅ Left-align text (never center for readability)

#### DON'T:
❌ Use multiple font families
❌ Create custom font sizes outside the scale
❌ Use all-caps for long text
❌ Use line heights < 1.3 for readability
❌ Use justified text (causes rivers)

---

## Spacing & Layout

### Spacing Scale

Based on Tailwind's 4px base unit:

| Size | Pixels | Usage |
|------|--------|-------|
| 1 | 4px | Tight internal spacing |
| 2 | 8px | Small gaps, icon padding |
| 3 | 12px | Default gap between items |
| 4 | 16px | Default padding, comfortable spacing |
| 6 | 24px | Section spacing |
| 8 | 32px | Large section spacing |
| 12 | 48px | Major section breaks |

### Layout Principles

1. **Consistent Padding**: Use `p-6` (24px) for card padding
2. **Consistent Gaps**: Use `gap-4` (16px) for flex/grid items
3. **Breathing Room**: Don't cram - whitespace is free
4. **Visual Hierarchy**: Larger spacing = greater separation
5. **Responsive Scaling**: Reduce spacing on mobile

### Grid System

```tsx
// Standard content layout
<div className="space-y-6 p-6">
  {/* Content sections with 24px vertical spacing */}
</div>

// Card grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* Responsive grid with 24px gaps */}
</div>
```

---

## Component Design Patterns

### Buttons

**Hierarchy:**

1. **Primary** - One per screen section
   ```tsx
   <Button variant="default">Save Changes</Button>
   ```

2. **Secondary** - Supporting actions
   ```tsx
   <Button variant="secondary">Cancel</Button>
   ```

3. **Ghost** - Tertiary actions, low emphasis
   ```tsx
   <Button variant="ghost">Learn More</Button>
   ```

4. **Outline** - Alternative emphasis
   ```tsx
   <Button variant="outline">Options</Button>
   ```

**Button Guidelines:**

- ✅ Use clear, action-oriented labels ("Save", not "OK")
- ✅ Place primary action on the right
- ✅ Maintain minimum 44x44px touch target (mobile)
- ❌ Don't use more than one primary button per context
- ❌ Don't use "Click here" - describe the action

### Cards

**Standard Card Structure:**

```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Supporting text</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Main content */}
  </CardContent>
  <CardFooter>
    {/* Actions */}
  </CardFooter>
</Card>
```

**Card Guidelines:**

- ✅ Use consistent padding (24px)
- ✅ Include clear visual hierarchy
- ✅ Limit card width for readability (max 800px)
- ❌ Don't nest cards deeply (max 2 levels)
- ❌ Don't overload with information

### Forms

**Form Layout Pattern:**

```tsx
<form className="space-y-4">
  <div className="space-y-2">
    <Label htmlFor="field">Field Label</Label>
    <Input id="field" type="text" />
    <p className="text-sm text-muted-foreground">
      Helper text explaining the field
    </p>
  </div>
  {/* More fields... */}
  <div className="flex justify-end gap-2">
    <Button variant="secondary">Cancel</Button>
    <Button type="submit">Save</Button>
  </div>
</form>
```

**Form Guidelines:**

- ✅ Always include labels (never placeholder-only)
- ✅ Provide clear helper text
- ✅ Show validation errors inline
- ✅ Disable submit while loading
- ✅ Use appropriate input types
- ❌ Don't hide labels (accessibility)
- ❌ Don't use placeholder as label
- ❌ Don't validate on input (validate on blur)

### Tables

**Data Table Pattern:**

```tsx
<div className="rounded-md border">
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Column</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <TableRow>
        <TableCell>Data</TableCell>
      </TableRow>
    </TableBody>
  </Table>
</div>
```

**Table Guidelines:**

- ✅ Use fixed header for scrolling tables
- ✅ Alternate row backgrounds for readability
- ✅ Right-align numeric data
- ✅ Include sorting indicators
- ✅ Provide pagination for > 50 rows
- ❌ Don't use tables for layout
- ❌ Don't cram too many columns
- ❌ Don't hide important data on mobile

---

## Accessibility Standards

### WCAG 2.1 AA Compliance

**Mandatory Requirements:**

1. **Contrast Ratios**
   - Normal text: ≥ 4.5:1
   - Large text (18pt+): ≥ 3:1
   - UI components: ≥ 3:1

2. **Keyboard Navigation**
   - All interactive elements must be keyboard accessible
   - Visible focus indicators required
   - Logical tab order maintained

3. **Screen Reader Support**
   - Semantic HTML elements
   - ARIA labels where needed
   - Alt text for images

4. **Motion & Animation**
   - Respect `prefers-reduced-motion`
   - No auto-playing videos
   - Provide pause controls

### Accessibility Checklist

Before shipping any UI:

- [ ] All text meets contrast requirements
- [ ] Keyboard navigation works correctly
- [ ] Focus indicators are visible
- [ ] Screen reader announces correctly
- [ ] Form labels are associated properly
- [ ] Error messages are clear and actionable
- [ ] Color is not the only indicator
- [ ] Touch targets are ≥ 44x44px
- [ ] Motion respects user preferences
- [ ] Page structure uses semantic HTML

### Accessibility Patterns

**Skip Links:**
```tsx
<a href="#main-content" className="sr-only focus:not-sr-only">
  Skip to main content
</a>
```

**ARIA Labels:**
```tsx
<Button aria-label="Close dialog" onClick={onClose}>
  <X className="h-4 w-4" />
</Button>
```

**Live Regions:**
```tsx
<div aria-live="polite" aria-atomic="true">
  {statusMessage}
</div>
```

---

## Interaction Design

### Feedback Patterns

**All user actions require feedback:**

1. **Immediate** (< 100ms) - Visual state change
   - Button press states
   - Input focus
   - Hover effects

2. **Quick** (100ms - 1s) - Loading indicators
   - Spinner for short waits
   - Skeleton screens for loading data
   - Progress bars for known duration

3. **Delayed** (> 1s) - Persistent feedback
   - Toast notifications
   - Success/error messages
   - Status updates

### Loading States

**Pattern Selection:**

| Duration | Pattern | Example |
|----------|---------|---------|
| < 300ms | Disable only | Button states |
| 300ms - 3s | Spinner | Form submission |
| 3s - 10s | Progress bar | File upload |
| > 10s | Background task | Data import |

**Loading State Examples:**

```tsx
// Button loading
<Button disabled={loading}>
  {loading ? <Loader className="mr-2 h-4 w-4 animate-spin" /> : null}
  Save
</Button>

// Skeleton screen
<div className="space-y-4">
  <Skeleton className="h-12 w-full" />
  <Skeleton className="h-12 w-full" />
</div>
```

### Error Handling

**Error Display Hierarchy:**

1. **Inline errors** - Field-level validation
   ```tsx
   <p className="text-sm text-destructive">Email is required</p>
   ```

2. **Alert banners** - Form-level errors
   ```tsx
   <Alert variant="destructive">
     <AlertTitle>Error</AlertTitle>
     <AlertDescription>Please fix the errors below</AlertDescription>
   </Alert>
   ```

3. **Toast notifications** - System-level errors
   ```tsx
   toast({
     title: "Error",
     description: "Failed to save changes",
     variant: "destructive"
   });
   ```

**Error Message Guidelines:**

- ✅ Be specific ("Email is required" not "Error")
- ✅ Explain what went wrong
- ✅ Suggest how to fix it
- ✅ Use plain language
- ❌ Don't show technical errors to users
- ❌ Don't blame the user
- ❌ Don't use jargon

---

## Performance Guidelines

### Performance Budgets

**Hard Limits:**

- First Contentful Paint: < 1.5s
- Largest Contentful Paint: < 2.5s
- Time to Interactive: < 3.5s
- Cumulative Layout Shift: < 0.1
- First Input Delay: < 100ms

### Optimization Patterns

**Component Memoization:**

```tsx
import { memo } from 'react';

// Memoize expensive list items
const ListItem = memo(({ data }) => {
  return <div>{/* Expensive render */}</div>;
});
```

**Debounced Inputs:**

```tsx
import { useDeb ounce } from 'use-debounce';

// Debounce search by 200ms
const [searchTerm] = useDebounce(inputValue, 200);
```

**Virtual Scrolling:**

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

// For lists > 100 items
const virtualizer = useVirtualizer({
  count: items.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 60
});
```

### Image Optimization

**Guidelines:**

- ✅ Use Next.js Image component
- ✅ Provide width/height to prevent CLS
- ✅ Use WebP format
- ✅ Lazy load below-fold images
- ❌ Don't load images larger than display size
- ❌ Don't use unoptimized formats (BMP, TIFF)

```tsx
import Image from 'next/image';

<Image
  src="/image.jpg"
  alt="Description"
  width={800}
  height={600}
  loading="lazy"
  placeholder="blur"
/>
```

---

## Responsive Design

### Breakpoint Strategy

```typescript
// Tailwind breakpoints
sm: 640px   // Phone landscape
md: 768px   // Tablet portrait
lg: 1024px  // Tablet landscape / Small desktop
xl: 1280px  // Desktop
2xl: 1536px // Large desktop
```

### Mobile-First Approach

**Always design for mobile first, then enhance:**

```tsx
// ✅ Mobile-first (default is mobile)
<div className="flex flex-col lg:flex-row">

// ❌ Desktop-first (requires overrides)
<div className="flex flex-row lg:flex-col">
```

### Responsive Patterns

**Navigation:**
- Mobile: Hamburger menu
- Desktop: Horizontal nav or sidebar

**Tables:**
- Mobile: Card-based layout
- Desktop: Full table view

**Forms:**
- Mobile: Single column
- Desktop: Multi-column for related fields

**Images:**
- Mobile: Full-width
- Desktop: Constrained width with margins

### Touch Targets

**Minimum Sizes:**
- Buttons: 44x44px (mobile)
- Links: 44px height with padding
- Form inputs: 44px height
- Checkboxes/radios: 24x24px with 44x44px target

---

## Animation & Motion

### Animation Principles

1. **Purposeful** - Animations serve a function
2. **Subtle** - Motion enhances, doesn't distract
3. **Performant** - Use transforms, avoid layout changes
4. **Respectful** - Honor prefers-reduced-motion

### Standard Timings

```typescript
// Animation durations
duration-75   // 75ms  - Quick interactions
duration-150  // 150ms - Dropdowns, tooltips
duration-300  // 300ms - Modals, page transitions
duration-500  // 500ms - Complex transitions
```

### Easing Functions

```typescript
ease-linear   // Constant speed
ease-in       // Slow start
ease-out      // Slow end (preferred for most)
ease-in-out   // Slow start and end
```

### Animation Examples

**Button Hover:**
```tsx
<Button className="transition-colors duration-150">
  Click Me
</Button>
```

**Modal Entrance:**
```tsx
<Dialog className="animate-in fade-in-0 zoom-in-95 duration-300">
  {content}
</Dialog>
```

**Skeleton Loading:**
```tsx
<div className="animate-pulse bg-muted" />
```

**Respect User Preferences:**
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Decision-Making Framework

### When Making Design Decisions

Ask these questions in order:

1. **Is it accessible?**
   - If no, redesign
   - If yes, continue

2. **Is it performant?**
   - Measure impact
   - If slow, optimize or reconsider
   - If fast, continue

3. **Is it consistent?**
   - Check existing patterns
   - If pattern exists, use it
   - If new pattern, document it

4. **Does it serve the user?**
   - Validate with user needs
   - If unclear, research
   - If yes, implement

5. **Can it be maintained?**
   - Consider future changes
   - Document complexity
   - Train team if needed

### Design Review Checklist

Before submitting for review:

- [ ] Matches design system patterns
- [ ] Meets accessibility standards
- [ ] Tested in all supported themes
- [ ] Tested on mobile and desktop
- [ ] Performance impact measured
- [ ] Documentation updated
- [ ] Edge cases handled
- [ ] Error states designed
- [ ] Loading states implemented
- [ ] Empty states considered

---

## Governance

### Design System Updates

**Process for Changes:**

1. **Proposal** - Document change with rationale
2. **Review** - Frontend team reviews
3. **Approval** - Tech lead approves
4. **Implementation** - Make changes
5. **Documentation** - Update this guide
6. **Communication** - Announce to team

### When to Deviate

**Deviations allowed when:**
- User research supports it
- Accessibility requires it
- Technical constraints demand it
- Business needs justify it

**Deviations require:**
- Written justification
- Tech lead approval
- Documentation update
- Team communication

### Versioning

This document follows semantic versioning:
- **Major** - Breaking changes to patterns
- **Minor** - New patterns added
- **Patch** - Clarifications, fixes

Current version: **1.0.0**

---

## Related Documentation

- [Theming Developer Guide](./theming-developer-guide.md)
- [Theme Implementation Analysis](./theme-implementation-analysis.md)
- [Component Library](../apps/web/components/ui/README.md) (if exists)

---

## Changelog

### Version 1.0.0 (2025-10-04)
- Initial design guidance document
- Established core principles
- Documented color system
- Defined typography standards
- Created spacing guidelines
- Established component patterns
- Set accessibility standards
- Defined interaction patterns
- Created decision framework

---

**Maintained by:** Frontend Architecture Team
**Questions?** Reach out in #frontend-dev
**Last Review:** 2025-10-04
**Next Review:** 2025-11-04
