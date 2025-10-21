# Import Page Visual Design Specification

## Quick Reference

**Design System:** shadcn/ui (Radix UI + Tailwind CSS)
**Layout Pattern:** Tab-based navigation
**Color Mode:** Light mode (dark mode compatible)
**Breakpoints:** Mobile-first responsive (sm: 640px, md: 768px, lg: 1024px, xl: 1280px)

---

## Color Palette

### Primary Colors
```css
--primary: hsl(var(--primary))           /* Brand primary (blue) */
--primary-foreground: hsl(var(--primary-foreground))
```

### Semantic Colors
```css
--background: hsl(var(--background))     /* Page background (white) */
--foreground: hsl(var(--foreground))     /* Primary text (near-black) */
--muted: hsl(var(--muted))               /* Muted backgrounds (light gray) */
--muted-foreground: hsl(var(--muted-foreground))  /* Secondary text */
--card: hsl(var(--card))                 /* Card background */
--card-foreground: hsl(var(--card-foreground))
--border: hsl(var(--border))             /* Border color (light gray) */
```

### Usage Map
- **Page Background:** `--background`
- **Card Backgrounds:** `--card`
- **Primary Text:** `--foreground`
- **Secondary Text:** `--muted-foreground`
- **Active Tab:** `--primary`
- **Icon Containers:** `--primary` at 10% opacity
- **Borders:** `--border` (1px), 2px for prominent cards
- **Bullets/Numbers:** `--primary` for bullets, `--muted` for number backgrounds

---

## Typography Scale

### Page Header
```
Title: text-3xl (30px), font-bold, tracking-tight, --foreground
Description: text-base (16px), --muted-foreground, line-height: 1.5
```

### Card Headers
```
Title: text-xl (20px), font-semibold, --card-foreground
Description: text-base (16px), --muted-foreground, leading-relaxed (1.625)
```

### Section Headers
```
"Best For" / "Supports" / "How It Works":
  text-sm (14px), font-semibold, uppercase, tracking-wider, --muted-foreground
```

### Body Text
```
List Items: text-sm (14px), --foreground
Helper Text: text-sm (14px), --muted-foreground
Button Text: text-sm (14px), font-medium
```

### Tab Labels
```
text-sm (14px), font-medium, --muted-foreground (inactive)
Active: --foreground, with shadow
```

---

## Spacing System (4px/8px Grid)

### Vertical Rhythm
```
Page Sections:       24px (space-y-6)
Card Padding:        24px (p-6)
Section Headers:     8px bottom margin
List Items:          6px between items (space-y-1.5)
Tab Content:         24px top margin (mt-6)
```

### Horizontal Spacing
```
Icon + Text:         8px gap (gap-2)
Card Grid Columns:   24px gap (gap-6)
Bullet + Text:       8px gap
Number + Text:       8px gap
```

### Component Spacing
```
Container Padding:   32px vertical (py-8), auto horizontal
Card Inner Padding:  24px all sides (p-6)
Button Padding:      12px horizontal, 8px vertical (default)
                     16px horizontal, 10px vertical (size="lg")
```

---

## Layout Specifications

### Page Container
```css
max-width: 1280px (max-w-6xl)
margin: 0 auto
padding: 32px 0 (py-8)
display: flex
flex-direction: column
gap: 24px (space-y-6)
```

### Tab Navigation
```css
max-width: 400px (max-w-md)
display: grid
grid-template-columns: 1fr 1fr
background: hsl(var(--muted))
padding: 4px
border-radius: 6px (rounded-md)
```

### Tab Trigger (Single)
```css
display: inline-flex
align-items: center
justify-content: center
gap: 8px
padding: 6px 12px (py-1.5 px-3)
border-radius: 4px (rounded-sm)
font-size: 14px (text-sm)
font-weight: 500 (font-medium)

/* Active State */
background: white (bg-background)
box-shadow: 0 1px 2px rgba(0,0,0,0.05) (shadow-sm)
```

### Import Method Card
```css
border: 2px solid hsl(var(--border))
border-radius: 8px (rounded-lg)
box-shadow: 0 1px 2px rgba(0,0,0,0.05) (shadow-sm)
background: hsl(var(--card))
```

#### Card Header Section
```css
padding: 24px (p-6)
display: flex
flex-direction: column
gap: 6px (space-y-1.5)
```

#### Icon Container
```css
width: 40px (w-10)
height: 40px (h-10)
border-radius: 8px (rounded-lg)
background: hsl(var(--primary) / 0.1)
color: hsl(var(--primary))
display: flex
align-items: center
justify-content: center
flex-shrink: 0
```

#### Card Content Grid
```css
padding: 0 24px 24px (px-6 pb-6)
display: grid
grid-template-columns: 1fr 1fr (md:grid-cols-2)
gap: 24px (gap-6)

/* Mobile */
@media (max-width: 768px) {
  grid-template-columns: 1fr
}
```

### Bulk Import CTA Card
```css
border: 1px dashed hsl(var(--border))
border-radius: 8px (rounded-lg)
padding: 24px (p-6)
display: flex
flex-direction: column (md:flex-row)
align-items: stretch (md:items-center)
justify-content: space-between
gap: 16px (gap-4)
```

---

## Component States

### Tab States
```css
/* Default (Inactive) */
color: hsl(var(--muted-foreground))
background: transparent

/* Hover */
color: hsl(var(--foreground))

/* Active (data-[state=active]) */
background: hsl(var(--background))
color: hsl(var(--foreground))
box-shadow: 0 1px 2px rgba(0,0,0,0.05)

/* Focus */
outline: 2px solid hsl(var(--ring))
outline-offset: 2px
```

### Button States (Primary)
```css
/* Default */
background: hsl(var(--primary))
color: hsl(var(--primary-foreground))
border-radius: 6px (rounded-md)
padding: 8px 16px (default), 10px 20px (size="lg")

/* Hover */
background: hsl(var(--primary)) with 90% opacity

/* Active (pressed) */
transform: translateY(1px)

/* Disabled */
opacity: 0.5
cursor: not-allowed
```

### Card States
```css
/* Default */
border: 2px solid hsl(var(--border))
box-shadow: 0 1px 2px rgba(0,0,0,0.05)

/* Hover (interactive cards only) */
box-shadow: 0 4px 6px rgba(0,0,0,0.1)
transition: box-shadow 150ms ease

/* Dashed Border Variant (Bulk CTA) */
border-style: dashed
border-width: 1px
```

---

## Icon Specifications

### Icons Used
- **Globe** (URL Import tab)
- **FileSpreadsheet** (File Import tab)
- **Link** (URL method card)
- **Upload** (File method card)

### Icon Sizes
```css
Tab Icons:        16px × 16px (h-4 w-4)
Method Card Icon: 20px × 20px (h-5 w-5)
```

### Icon Colors
```css
Tab Icons:        Inherits from parent (muted → foreground)
Card Icons:       hsl(var(--primary))
```

---

## Visual Design Patterns

### Bullet Points (Unordered Lists)
```css
.bullet {
  width: 6px (w-1.5)
  height: 6px (h-1.5)
  border-radius: 50% (rounded-full)
  background: hsl(var(--primary))
  margin-top: 6px (mt-1.5)
  flex-shrink: 0
}

.list-item {
  display: flex
  align-items: flex-start
  gap: 8px
  font-size: 14px
  line-height: 1.5
}
```

### Numbered Steps (Ordered Lists)
```css
.number-circle {
  width: 20px (w-5)
  height: 20px (h-5)
  border-radius: 50% (rounded-full)
  background: hsl(var(--muted))
  color: hsl(var(--foreground))
  font-size: 12px (text-xs)
  font-weight: 500 (font-medium)
  display: flex
  align-items: center
  justify-content: center
  flex-shrink: 0
  margin-top: 2px (mt-0.5)
}

.step-item {
  display: flex
  align-items: flex-start
  gap: 8px
  font-size: 14px
  line-height: 1.5
}
```

---

## Responsive Breakpoints

### Mobile (< 640px)
```css
.container {
  padding-left: 16px
  padding-right: 16px
}

.method-card-content {
  grid-template-columns: 1fr
}

.bulk-cta {
  flex-direction: column
  align-items: stretch
}

.tab-list {
  width: 100%
}
```

### Tablet (640px - 768px)
```css
.container {
  padding-left: 24px
  padding-right: 24px
}

.method-card-content {
  grid-template-columns: 1fr
}
```

### Desktop (≥ 768px)
```css
.method-card-content {
  grid-template-columns: 1fr 1fr
}

.bulk-cta {
  flex-direction: row
  align-items: center
}
```

### Large Desktop (≥ 1280px)
```css
.container {
  max-width: 1280px
  margin: 0 auto
}
```

---

## Accessibility Visual Indicators

### Focus States
```css
/* All Interactive Elements */
:focus-visible {
  outline: 2px solid hsl(var(--ring))
  outline-offset: 2px
  border-radius: inherit
}

/* High Contrast Mode Support */
@media (prefers-contrast: high) {
  :focus-visible {
    outline-width: 3px
  }
}
```

### Touch Targets (Mobile)
```css
/* Minimum 44x44px */
button, .tab-trigger {
  min-height: 44px
  min-width: 44px (or auto for text buttons)
}

/* Padding adjustment for touch */
@media (max-width: 768px) {
  button {
    padding-top: 12px
    padding-bottom: 12px
  }
}
```

---

## Animation & Transitions

### Tab Switching
```css
.tab-content {
  animation: fadeIn 150ms ease-in
}

@keyframes fadeIn {
  from {
    opacity: 0
    transform: translateY(-4px)
  }
  to {
    opacity: 1
    transform: translateY(0)
  }
}
```

### Button Hover
```css
button {
  transition: background-color 150ms ease, transform 100ms ease
}

button:hover {
  background-color: hsl(var(--primary) / 0.9)
}

button:active {
  transform: translateY(1px)
}
```

### Card Hover (Future Enhancement)
```css
.method-card {
  transition: box-shadow 150ms ease
}

.method-card:hover {
  box-shadow: 0 4px 6px rgba(0,0,0,0.1)
}
```

---

## Dark Mode Considerations

All color values use CSS custom properties, automatically adapting to dark mode when implemented:

```css
/* Dark Mode Overrides (when implemented) */
@media (prefers-color-scheme: dark) {
  :root {
    --background: hsl(222.2 84% 4.9%)
    --foreground: hsl(210 40% 98%)
    --card: hsl(222.2 84% 4.9%)
    --card-foreground: hsl(210 40% 98%)
    --muted: hsl(217.2 32.6% 17.5%)
    --muted-foreground: hsl(215 20.2% 65.1%)
    --border: hsl(217.2 32.6% 17.5%)
  }
}
```

### Dark Mode Specific Adjustments
- Icon containers: `bg-primary/20` (increased opacity for visibility)
- Card borders: Lighter shade for definition
- Shadows: More subtle or removed
- Focus rings: Higher contrast color

---

## Print Styles (Future Enhancement)

```css
@media print {
  /* Hide interactive elements */
  .tab-list, button {
    display: none
  }

  /* Show all tab content */
  .tab-content {
    display: block !important
    page-break-after: always
  }

  /* Optimize cards */
  .method-card {
    border: 1px solid #000
    box-shadow: none
    page-break-inside: avoid
  }

  /* Flatten colors */
  body {
    background: white
    color: black
  }
}
```

---

## Component Composition Examples

### Tab Trigger with Icon
```tsx
<TabsTrigger value="url" className="gap-2">
  <Globe className="h-4 w-4" />
  URL Import
</TabsTrigger>
```
**Rendered Styles:**
- Display: `inline-flex items-center justify-center`
- Gap: `8px`
- Icon Size: `16px × 16px`
- Text Size: `14px`
- Padding: `6px 12px`

### Method Card Header
```tsx
<CardHeader>
  <div className="flex items-start gap-3">
    <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
      <Link className="h-5 w-5" />
    </div>
    <div className="space-y-1.5">
      <CardTitle className="text-xl">Import from Marketplace URLs</CardTitle>
      <CardDescription className="text-base leading-relaxed">
        Extract listing data...
      </CardDescription>
    </div>
  </div>
</CardHeader>
```
**Rendered Styles:**
- Container: `flex items-start gap-12px`
- Icon Box: `40px square, rounded-8px, primary-10% background`
- Title: `20px bold, primary foreground`
- Description: `16px, 1.625 line-height, muted foreground`

### Bullet List Item
```tsx
<li className="flex items-start gap-2 text-sm">
  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
  <span>Individual listing imports</span>
</li>
```
**Rendered Styles:**
- Container: `flex items-start gap-8px`
- Bullet: `6px circle, primary color, 6px top offset`
- Text: `14px, normal weight`

---

## Visual Hierarchy Summary

### Priority 1: Page Title
- Largest text (30px)
- Boldest weight
- Highest contrast (foreground color)

### Priority 2: Tab Navigation
- Prominent placement below header
- Active state clearly distinguished
- Icons enhance scannability

### Priority 3: Method Cards
- 2px border for prominence
- Icon containers draw attention
- Card titles (20px) establish hierarchy

### Priority 4: Section Headers
- Uppercase for distinction
- Muted color to support (not compete with) content
- Consistent throughout card

### Priority 5: Body Content
- Standard text size (14px)
- Sufficient line-height for readability
- Visual markers (bullets, numbers) aid scanning

### Priority 6: Helper Text
- Smallest prominence (muted color)
- Provides context without distraction
- Placed near relevant actions

---

## Measurement Reference

### Quick Conversion Chart
```
Spacing:
4px  = 0.25rem = Tailwind 1
8px  = 0.5rem  = Tailwind 2
12px = 0.75rem = Tailwind 3
16px = 1rem    = Tailwind 4
20px = 1.25rem = Tailwind 5
24px = 1.5rem  = Tailwind 6
32px = 2rem    = Tailwind 8
40px = 2.5rem  = Tailwind 10

Text Sizes:
12px = 0.75rem  = text-xs
14px = 0.875rem = text-sm
16px = 1rem     = text-base
20px = 1.25rem  = text-xl
30px = 1.875rem = text-3xl

Border Radius:
4px = 0.25rem = rounded-sm
6px = 0.375rem = rounded-md
8px = 0.5rem  = rounded-lg
```

---

## Design Review Checklist

### Visual Consistency
- [ ] All cards use consistent padding (24px)
- [ ] All icons are consistent sizes per context
- [ ] All section headers use uppercase + tracking
- [ ] All bullet points use 6px circles
- [ ] All numbered steps use 20px circles
- [ ] Tab icons are 16px, card icons are 20px

### Spacing Consistency
- [ ] 24px vertical rhythm throughout
- [ ] 8px gap for icon + text pairs
- [ ] 6px spacing between list items
- [ ] Consistent card grid gaps (24px)

### Typography Consistency
- [ ] Page title is text-3xl bold
- [ ] Card titles are text-xl semibold
- [ ] Section headers are text-sm semibold uppercase
- [ ] Body text is text-sm
- [ ] Muted text uses muted-foreground

### Color Usage
- [ ] Primary color only on active elements
- [ ] Muted-foreground for secondary text
- [ ] Border color consistent throughout
- [ ] Icon containers use 10% primary opacity

### Accessibility
- [ ] Focus rings on all interactive elements
- [ ] Touch targets meet 44px minimum
- [ ] Text contrast meets WCAG AA
- [ ] Heading hierarchy is logical

---

## Implementation Notes

This visual specification uses Tailwind CSS utility classes exclusively. All measurements, colors, and styles are derived from the project's design tokens defined in the Tailwind config.

**Key Files:**
- **Tailwind Config:** `/mnt/containers/deal-brain/apps/web/tailwind.config.ts`
- **Global Styles:** `/mnt/containers/deal-brain/apps/web/app/globals.css`
- **Component Implementation:** `/mnt/containers/deal-brain/apps/web/app/(dashboard)/import/page.tsx`

All components use the shadcn/ui design system, ensuring consistency with the rest of the application.
