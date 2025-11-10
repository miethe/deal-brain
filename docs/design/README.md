# Deal Brain Design Documentation
**UI/UX Design Specifications**
**Last Updated**: 2025-10-19

---

## Overview

This directory contains comprehensive design documentation for Deal Brain's user interface components. All designs follow WCAG 2.1 AA accessibility standards, use the shadcn/ui component library, and maintain consistency with the existing Deal Brain design system.

---

## Current Design Projects

### Single URL Import Component (Task ID-022)
**Status**: Design Complete - Ready for Implementation
**Phase**: Phase 4 - Frontend & Testing
**Estimated Implementation**: 20 hours across 4 phases

Complete design package for the single URL import feature, enabling users to import PC listings from marketplace URLs (eBay, Amazon, retailers) with real-time status updates.

#### Design Documents

1. **Design Summary** (`single-url-import-summary.md`)
   - Executive overview of the design
   - Component architecture strategy
   - State management approach
   - Accessibility features
   - Integration points
   - Success metrics
   - **Start here for overview**

2. **Technical Specification** (`single-url-import-technical-spec.md`)
   - Complete TypeScript type definitions
   - Zod validation schemas
   - API client implementations
   - React Query polling hook
   - Full component code (3 components)
   - Testing requirements
   - Performance optimizations
   - **Use this for implementation**

3. **Visual Mockups** (`single-url-import-mockups.md`)
   - 10 detailed ASCII mockups (all states)
   - Mobile responsive layouts
   - Dark mode variants
   - Animation specifications
   - Typography and spacing scales
   - Color system and tokens
   - Micro-interaction details
   - **Use this for visual reference**

4. **Component Tree** (`single-url-import-component-tree.md`)
   - Component hierarchy diagrams
   - Data flow visualizations
   - Props flow diagrams
   - State management layers
   - Hook dependencies
   - Event handler mappings
   - Accessibility tree
   - **Use this to understand structure**

5. **Quick Reference** (`single-url-import-quickref.md`)
   - Quick start guide
   - Component cheat sheets
   - Styling reference
   - Testing checklist
   - Common gotchas
   - Code snippets
   - Implementation order
   - **Use this during development**

#### Key Features

- **6 Component States**: Idle, validating, submitting, polling, success, error
- **Real-time Status**: 2-second polling with progress indicator
- **Accessible**: WCAG 2.1 AA compliant, keyboard navigation, screen reader support
- **Responsive**: Mobile-first design with breakpoints
- **Error Handling**: User-friendly messages with retry options
- **Performance**: Memoized components, debounced validation, optimized polling

#### File Locations

All design documents:
```
/mnt/containers/deal-brain/docs/design/
├── single-url-import-summary.md          (Start here)
├── single-url-import-technical-spec.md   (Implementation guide)
├── single-url-import-mockups.md          (Visual reference)
├── single-url-import-component-tree.md   (Structure diagrams)
└── single-url-import-quickref.md         (Developer cheat sheet)
```

Implementation files (to be created):
```
/mnt/containers/deal-brain/apps/web/
├── components/ingestion/
│   ├── single-url-import-form.tsx
│   ├── ingestion-status-display.tsx
│   ├── import-success-result.tsx
│   ├── types.ts
│   ├── schemas.ts
│   ├── error-messages.ts
│   └── __tests__/
├── lib/api/
│   └── ingestion.ts
└── hooks/
    └── use-ingestion-job.ts
```

---

## Design System

### Core Principles

1. **Accessibility First**
   - WCAG 2.1 AA compliance minimum
   - Keyboard navigation on all interactive elements
   - Screen reader support with ARIA labels
   - Color contrast ratios meet standards

2. **Performance Conscious**
   - Component memoization for expensive renders
   - Debounced inputs (200-300ms)
   - Optimized polling intervals
   - Code splitting where beneficial

3. **Responsive Design**
   - Mobile-first approach
   - Breakpoints: 640px (mobile), 1024px (tablet), 1280px (desktop)
   - Flexible layouts with Tailwind utilities
   - Touch-friendly targets (44px minimum)

4. **Consistency**
   - shadcn/ui component library
   - 8px spacing grid system
   - Standardized color tokens
   - Predictable interaction patterns

### Component Library

**Base Components** (shadcn/ui):
- Button (variants: default, outline, ghost, secondary)
- Input (text, url, number)
- Select (with keyboard navigation)
- Label (semantic markup)
- Card (container with header/content/footer)
- Alert (status messages)
- Badge (metadata tags)
- Dialog/Modal (overlays)

**Custom Components**:
- ListingsTable (sortable, filterable)
- ValuationBreakdown (modal with rules display)
- CustomFieldEditor (dynamic field management)
- URL Import components (new in Phase 4)

### Design Tokens

**Colors** (CSS variables):
```css
--primary:           221 83% 53%    (Blue)
--success:           142 71% 45%    (Green)
--destructive:       0 84% 60%      (Red)
--muted:             240 4.8% 95.9% (Gray light)
--foreground:        240 10% 3.9%   (Text)
--background:        0 0% 100%      (White)
```

**Spacing** (8px grid):
```
0.5 = 4px   (gap-0.5)
1   = 8px   (gap-1, p-1)
2   = 16px  (gap-2, p-2)
3   = 24px  (gap-3, p-3)
4   = 32px  (space-y-4)
6   = 48px  (p-6, typical card padding)
8   = 64px  (large sections)
```

**Typography**:
```
text-xs:    12px / 1.4em
text-sm:    14px / 1.5em
text-base:  16px / 1.5em  (default)
text-lg:    18px / 1.75em
text-xl:    20px / 1.75em
text-2xl:   24px / 1.2em  (card titles)
text-3xl:   30px / 1.2em  (page titles)
```

**Border Radius**:
```
rounded-sm:   2px
rounded:      4px
rounded-md:   6px   (default)
rounded-lg:   8px   (cards)
rounded-full: 9999px (badges, pills)
```

---

## Accessibility Guidelines

### Keyboard Navigation

**Essential Shortcuts**:
- `Tab`: Move focus forward
- `Shift+Tab`: Move focus backward
- `Enter`: Activate button/submit form
- `Space`: Toggle checkbox/radio
- `Escape`: Close modal/clear form
- `Arrow keys`: Navigate select/radio groups

**Focus Indicators**:
```css
.focus-visible:outline-none
.focus-visible:ring-2
.focus-visible:ring-ring
.focus-visible:ring-offset-2
```

### Screen Reader Support

**ARIA Patterns**:
- `aria-label`: Label for interactive elements without visible text
- `aria-describedby`: Link to help text or error messages
- `aria-invalid`: Indicate form validation errors
- `aria-live="polite"`: Announce status changes
- `aria-live="assertive"`: Announce critical errors
- `role="status"`: Indicate status information
- `role="alert"`: Indicate error/warning messages

**Best Practices**:
- All form inputs have associated labels
- Error messages linked via `aria-describedby`
- Status updates announced to screen readers
- Hidden content uses `.sr-only` class
- Interactive elements have descriptive labels

### Color Contrast

**Minimum Ratios** (WCAG AA):
- Normal text (14-18px): 4.5:1
- Large text (18px+ or 14px+ bold): 3:1
- Interactive elements: 3:1

**Testing**:
- Use browser DevTools Accessibility panel
- Run axe accessibility audits
- Test with actual screen readers (NVDA, JAWS, VoiceOver)
- Validate color contrast with tools

---

## Design Workflow

### 1. Requirements Gathering
- Review user stories and acceptance criteria
- Identify accessibility requirements
- Determine responsive needs
- List integration points

### 2. Component Design
- Sketch component hierarchy
- Define state machine (if applicable)
- Plan data flow and props
- Choose appropriate UI components

### 3. Visual Design
- Create mockups (ASCII or Figma)
- Define color scheme
- Specify typography
- Detail spacing and layout

### 4. Technical Specification
- Write TypeScript type definitions
- Define validation schemas
- Plan API integration
- Document accessibility features

### 5. Implementation Handoff
- Provide all design documents
- Create quick reference guide
- Define success criteria
- Specify testing requirements

### 6. Review & Iterate
- Review implementation against specs
- Test accessibility compliance
- Gather user feedback
- Iterate as needed

---

## Testing Standards

### Unit Testing
- Render tests for all components
- Validation tests for forms
- State transition tests
- Event handler tests
- Target: 90%+ coverage

### Accessibility Testing
- Automated: axe-core via jest-axe
- Manual: NVDA/JAWS screen reader testing
- Keyboard navigation verification
- Color contrast validation
- Target: 0 violations

### Integration Testing
- Full user flows (happy path)
- Error scenarios
- Edge cases
- API integration
- Target: All critical paths covered

### Visual Regression
- Snapshot tests for stable components
- Cross-browser testing (Chrome, Firefox, Safari)
- Mobile device testing
- Dark mode verification

---

## Design Tools & Resources

### Tools
- **Figma**: For complex visual designs (when needed)
- **Excalidraw**: For quick diagrams and flows
- **ASCII Art**: For inline documentation mockups
- **Chrome DevTools**: Accessibility panel, contrast checker
- **axe DevTools**: Browser extension for a11y audits

### Resources
- shadcn/ui docs: https://ui.shadcn.com
- Radix UI docs: https://www.radix-ui.com
- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- MDN Accessibility: https://developer.mozilla.org/en-US/docs/Web/Accessibility
- React Hook Form: https://react-hook-form.com
- TanStack Query: https://tanstack.com/query/latest

### Code References
- Existing components: `/mnt/containers/deal-brain/apps/web/components/`
- UI components: `/mnt/containers/deal-brain/apps/web/components/ui/`
- Utilities: `/mnt/containers/deal-brain/apps/web/lib/utils.ts`
- Global styles: `/mnt/containers/deal-brain/apps/web/app/globals.css`

---

## Future Design Projects

### Upcoming (Phase 4 Continuation)
- **Bulk URL Import UI** (Task ID-023)
  - Multi-URL upload (CSV/JSON)
  - Progress tracking table
  - Per-URL status display
  - Download results

- **Provenance Badge** (Task ID-024)
  - Listing detail integration
  - Quality indicator tooltips
  - Last seen timestamp

- **Admin Adapter Settings** (Task ID-025)
  - Enable/disable adapters
  - Configure timeouts and retries
  - View health metrics
  - Test endpoints

### Potential Future Enhancements
- Advanced filtering UI
- Bulk edit components
- Data visualization (charts)
- Mobile app design
- Email notification templates

---

## Contributing to Design Docs

### Design Document Structure

Each design project should include:

````markdown
1. **Summary Document**
   - Overview and key decisions
   - Component architecture
   - State management approach
   - Accessibility features
   - Success metrics

2. **Technical Specification**
   - TypeScript types
   - Validation schemas
   - API integration
   - Full component code
   - Testing requirements

3. **Visual Mockups**
   - All component states
   - Responsive layouts
   - Animation specs
   - Typography/spacing
   - Color usage

4. **Quick Reference**
   - Cheat sheets
   - Code snippets
   - Testing checklist
   - Common gotchas

5. **Component Tree** (if complex)
   - Hierarchy diagrams
   - Data flow
   - Dependencies

### File Naming Convention

```
{component-name}-summary.md
{component-name}-technical-spec.md
{component-name}-mockups.md
{component-name}-quickref.md
{component-name}-component-tree.md
```

### Writing Style

- Use clear, concise language
- Include code examples
- Add visual diagrams (ASCII art)
- Specify absolute file paths
- Document accessibility considerations
- Provide implementation estimates
````

---

## Contact & Support

For design questions or clarifications:

1. Review existing design documents
2. Check component examples in codebase
3. Consult shadcn/ui documentation
4. Reference WCAG guidelines for accessibility

---

## Version History

### v1.0 (2025-10-19)
- Initial design documentation structure
- Single URL Import component design complete
- Design system guidelines documented
- Accessibility standards defined

---

**Design System Maintainer**: UI Design Team
**Last Review**: 2025-10-19
**Next Review**: After Phase 4 completion
