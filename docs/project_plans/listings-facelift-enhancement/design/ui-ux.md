# UI/UX Design Specifications

**Status:** Draft
**Last Updated:** October 22, 2025

---

## Visual Design System

### Color Palette

#### Valuation Color Coding

- **Great Deal (savings ≥ threshold):** `text-emerald-600` (green) - #059669
- **Good Deal (savings < threshold):** `text-blue-600` (blue) - #2563eb
- **Premium (price increase):** `text-red-600` (red) - #dc2626
- **Neutral (no change):** `text-muted-foreground` (gray) - #6b7280

#### Status Badges

- **Available:** `bg-green-100 text-green-800` - Active, ready for sale
- **Sold:** `bg-gray-100 text-gray-800` - No longer available
- **Archived:** `bg-yellow-100 text-yellow-800` - Hidden from main view
- **Draft:** `bg-blue-100 text-blue-800` - Not yet published

#### Interactive Elements

- **Links:** `text-primary hover:underline` - Standard text link
- **Hover Cards:** `bg-accent/5 border-accent` - Subtle highlight
- **Focus:** `ring-2 ring-offset-2 ring-ring` - WCAG AA compliant

---

## Typography

### Headings

**Page title (h1):**
- Size: `text-3xl`
- Weight: `font-bold`
- Spacing: `tracking-tight`
- Usage: Listing title, page main heading

**Section headers (h2):**
- Size: `text-2xl`
- Weight: `font-semibold`
- Usage: Major section breaks

**Subsection headers (h3):**
- Size: `text-lg`
- Weight: `font-semibold`
- Usage: Tab content sections, group titles

**Card titles (h4):**
- Size: `text-base`
- Weight: `font-semibold`
- Usage: Summary card titles, modal headers

### Body Text

**Default:**
- Size: `text-sm` or `text-base`
- Weight: `font-normal`
- Line height: `leading-relaxed`

**Muted:**
- Size: `text-sm`
- Color: `text-muted-foreground`
- Usage: Secondary information, hints

**Emphasized:**
- Weight: `font-medium` or `font-semibold`
- Usage: Important values, labels

### Data Display

**Labels:**
- Size: `text-xs`
- Case: `uppercase`
- Spacing: `tracking-wide`
- Color: `text-muted-foreground`
- Usage: Specification labels, field names

**Values:**
- Size: `text-sm font-medium` or `text-base`
- Usage: Actual specification data

**Metrics:**
- Size: `text-lg font-semibold` or `text-2xl font-bold`
- Usage: Large numbers, prices, composite scores

---

## Spacing & Layout

### Container Widths

- **Max width:** `max-w-7xl` (1280px) - Main content area
- **Modal max width:** `max-w-3xl` (768px) - Dialog modals
- **Narrow column:** `max-w-2xl` (672px) - Single column layouts

### Padding & Margin

**Section spacing:**
- Between major sections: `space-y-6` or `space-y-8`
- Between cards: `space-y-4`
- Reduced mobile: `space-y-3` or `space-y-4`

**Card padding:**
- Standard: `p-4` or `p-6`
- Compact: `p-3`
- Mobile reduced: `p-3` or `p-4`

**Content padding:**
- Desktop: `px-4 sm:px-6 lg:px-8`
- Allows responsive padding for mobile/tablet/desktop

### Grid Layouts

**Summary cards grid:**
```
Desktop:  grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4
Tablet:   grid-cols-1 md:grid-cols-2 gap-4
Mobile:   grid-cols-1 gap-3
```

**Specifications grid:**
```
Desktop:  grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3
Tablet:   grid-cols-1 md:grid-cols-2 gap-3
Mobile:   grid-cols-1 gap-2
```

---

## Component Specifications

### Summary Card

**Structure:**
```tsx
<Card>
  <CardHeader>
    <div className="flex items-center gap-2">
      <Icon className="h-5 w-5 text-muted-foreground" />
      <CardTitle className="text-sm font-medium">Label</CardTitle>
    </div>
  </CardHeader>
  <CardContent>
    <div className="text-2xl font-bold">Value</div>
    <p className="text-xs text-muted-foreground mt-1">Subtitle</p>
  </CardContent>
</Card>
```

**Variants:**
- **Price Card:** Currency icon, color-coded values (green/red/gray)
- **Performance Card:** Lightning bolt icon, numeric scores
- **Hardware Card:** CPU icon, component list (CPU, GPU, RAM, Storage)
- **Metadata Card:** Info icon, status/condition information

**Styling:**
- Border: `border rounded-lg`
- Shadow: `shadow-sm`
- Hover: Optional subtle scale/shadow on hover

### Entity Link

**Structure:**
```tsx
<Link href={entityPath}>
  {name}
</Link>
```

**Styling:**
- Color: `text-primary`
- Hover: `hover:underline cursor-pointer`
- Underline offset: `underline-offset-4`
- Focus: `ring-2 ring-offset-2 ring-ring`

**Interactive States:**
- Normal: Primary color text
- Hover: Underline appears
- Focus: Ring indicator visible
- Keyboard: Enter/Space triggers navigation

### Entity Tooltip

**Structure (HoverCard):**
```tsx
<HoverCard>
  <HoverCardTrigger asChild>
    <EntityLink />
  </HoverCardTrigger>
  <HoverCardContent className="w-80">
    <div className="space-y-2">
      <h4 className="text-sm font-semibold">{entityName}</h4>
      <dl className="grid grid-cols-2 gap-2 text-xs">
        <dt className="text-muted-foreground">Label:</dt>
        <dd className="font-medium">Value</dd>
      </dl>
    </div>
  </HoverCardContent>
</HoverCard>
```

**Styling:**
- Max width: `w-80` (320px)
- Padding: `p-3`
- Background: `popover` theme color
- Border: Standard border with subtle shadow
- Z-index: Floats above content

**Trigger Behavior:**
- Hover trigger: 200ms delay before showing
- Click trigger: Opens on click, closes on outside click
- Keyboard: Tab focuses trigger, Enter/Space opens

### Rule Card (Valuation)

**Contributor Card:**
- Border: `border-2` (thicker for importance)
- Background: `hover:bg-accent/5`
- Padding: `p-3` or `p-4`
- Title: `text-sm font-medium`
- Amount: `font-semibold` with color coding

**Inactive Card:**
- Border: `border` (standard)
- Color: `text-muted-foreground`
- Background: Slightly muted
- Title: `text-sm font-medium`
- Amount: `font-medium` in gray

**RuleGroup Badge:**
- Component: shadcn/ui Badge `variant="outline"`
- Size: `text-xs`
- Spacing: Adjacent to rule name or on separate line

### Tabs

**Navigation:**
- Component: shadcn/ui Tabs
- Style: Underline (default) or Pills (optional)
- Spacing below: `mb-6`
- Active indicator: Underline or pill background
- Focus: Ring indicator on tab button

**Tab Content:**
- Padding: Consistent with page padding
- Spacing: `space-y-6` between sections
- Responsive: Full-width on mobile, constrained on desktop

---

## Responsive Design Breakpoints

### Mobile (<768px)

**Hero Section:**
- Single column layout
- Image: Full width
- Summary cards: Single column grid, full width
- Cards stacked vertically

**Specifications:**
- Single column grid
- Reduced padding (`p-3`)
- Smaller font sizes on some elements
- Expandable sections for less critical data

**Touch Targets:**
- Minimum 44×44px for all interactive elements
- Buttons: `h-10 px-4` or larger
- Links: Add padding/hit area if < 44px

### Tablet (768px - 1023px)

**Hero Section:**
- Two column: Image top, summary cards bottom
- Image: 300px width, centered
- Cards: Two column grid
- Good readable text sizes

**Specifications:**
- Two column grid
- Standard padding (`p-4`)
- Good spacing between sections
- Most labels visible without scrolling

### Desktop (≥1024px)

**Hero Section:**
- Two column: Image left (400px), cards right
- Image: 400px width maximum
- Cards: Three column grid with good spacing
- Ample white space

**Specifications:**
- Three column grid for optimal scanning
- Standard padding (`p-4` or `p-6`)
- Generous spacing
- Good scrolling experience

### Ultra-Wide (≥1920px)

**Additional:**
- Max-width constraint: `max-w-7xl`
- Centered content with equal margins
- Ample white space on sides
- No layout changes needed (max-width handles)

---

## Visual Hierarchy

### Information Priority

1. **Critical:** Listing title, price, condition (h1, large, prominent)
2. **Important:** Summary cards, main specs (h3, bold, prominent color)
3. **Secondary:** Detailed specs, additional fields (text-sm, normal weight)
4. **Tertiary:** Metadata, timestamps (text-xs, muted color)

### Visual Emphasis

**Use font weight:**
- Bold: `font-bold` or `font-semibold` for primary info
- Normal: `font-normal` for body content
- Medium: `font-medium` for labels and values

**Use size:**
- Larger fonts for more important content
- Consistent scaling: 12px → 14px → 16px → 18px → 20px → 24px → 30px

**Use color:**
- Primary colors for interactive elements
- Muted colors for secondary information
- Color-coded for status/metrics (green/red/blue)

---

## Animation & Motion

**Modal Close:**
- Duration: 200ms
- Animation: Fade out
- Easing: ease-out
- Effect: Smooth exit

**List Highlight:**
- Duration: 2 seconds total
- Animation: Subtle pulse (background color pulse)
- Easing: ease-in-out
- Effect: `bg-accent/10` → transparent

**Tooltip Appearance:**
- Trigger delay: 200ms on hover
- Entrance animation: Fade in (100ms)
- Exit animation: Fade out (100ms)

**Collapsible Section:**
- Duration: 300ms
- Animation: Height transition
- Easing: ease-in-out
- Starting state: Collapsed if >10 items

---

## Accessibility in Design

### Color Contrast

- Text on background: ≥ 4.5:1 (WCAG AA)
- Large text (18pt+): ≥ 3:1
- Verify with: WebAIM Contrast Checker

### Focus Indicators

- Ring: `ring-2 ring-offset-2 ring-ring`
- Minimum 2px thick, minimum 2px offset
- Visible on all keyboard-navigable elements
- High contrast against background

### Touch Targets

- Minimum: 44×44px (WCAG AA)
- Buttons: `h-10 px-4` (40px height, padding provides width)
- Links: Add padding if text is narrow

### Text Sizing

- Base: 16px minimum for comfortable reading
- Avoid: Very small text for primary content
- Allow: 200% zoom without horizontal scroll

---

## Design System References

- **Component Library:** shadcn/ui (based on Radix UI + Tailwind CSS)
- **Icons:** Lucide React (`lucide-react` package)
- **Styling:** Tailwind CSS 3+
- **Colors:** CSS custom properties defined in theme

---

## Related Documentation

- **[Technical Architecture](./technical-design.md)** - Component structure
- **[Accessibility Guidelines](./accessibility.md)** - Detailed a11y specs
- **[Performance Optimization](./performance.md)** - Image optimization, code splitting
