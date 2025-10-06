# Listings Catalog Views - User Guide

## Overview

The Listings Catalog View provides three specialized interfaces for browsing, comparing, and managing PC listings. Each view is optimized for different workflows, allowing you to choose the best interface for your current task.

### Available Views

1. **Grid View** - Visual discovery mode with cards showing key metrics at a glance
2. **Dense List View** - High-density table for bulk operations and quick scanning
3. **Master/Detail View** - Split layout for detailed comparison with context

All views share the same powerful filtering system and preserve your preferences across sessions.

---

## Getting Started

### Accessing Catalog Views

1. Navigate to the **Listings** page
2. Click the **Catalog** tab at the top of the page
3. The default view is Grid View - use the view switcher to change modes

### Understanding the Interface

All catalog views include:

- **Filter Bar** (sticky at top): Search, form factor, manufacturer, and price filters
- **View Switcher**: Toggle between Grid, List, and Master/Detail modes
- **Active Listings**: Filtered and sorted by best value (adjusted $/MT ascending)

---

## Grid View

### When to Use Grid View

Grid View is ideal for:
- **Visual browsing** - Quickly scanning multiple listings with prominent pricing
- **Deal discovery** - Color-coded indicators highlight value opportunities
- **Mobile browsing** - Responsive layout works great on tablets and phones
- **Initial exploration** - Get an overview before diving into details

### Layout

- **Mobile (< 640px)**: 1 column
- **Tablet (640-1024px)**: 2 columns
- **Desktop (1024-1280px)**: 3 columns
- **Large Desktop (> 1280px)**: 4 columns

### Card Structure

Each listing card displays:

**Header Section:**
- Title (bold, prominent)
- External link button (opens listing URL in new tab)

**Badges Row:**
- CPU name
- CPU benchmarks (ST and MT scores)
- Device type (e.g., Mini-PC, Laptop)
- Tags (max 2 shown)

**Price Section:**
- List price (large text)
- Adjusted price with color accent:
  - **Dark Emerald**: >15% savings (excellent deal)
  - **Light Emerald**: 5-15% savings (good deal)
  - **Amber**: >10% premium (caution)
  - **Gray**: Neutral valuation

**Performance Badges:**
Four metrics showing price efficiency:
- $/ST (raw): Dollar per single-thread CPU mark
- $/MT (raw): Dollar per multi-thread CPU mark
- $/ST (adj): Adjusted dollar per single-thread
- $/MT (adj): Adjusted dollar per multi-thread

Lower values indicate better performance-per-dollar. Hover for explanations.

**Metadata Row:**
- RAM (e.g., "16 GB")
- Storage (e.g., "512 GB SSD")
- Condition (e.g., "New", "Refurbished")

**Footer:**
- Vendor badge
- Quick Edit button (hover to reveal)

### Actions

**Click Card**: Opens detailed dialog with:
- KPI metrics (Price, Adjusted, $/ST, $/MT)
- Full performance badges
- Complete specifications
- Link to full listing page

**Quick Edit Button**: Opens inline editor for:
- Title
- Price
- Condition
- Status

**External Link Button**: Opens original listing URL in new tab

---

## Dense List View

### When to Use Dense List View

Dense List View is ideal for:
- **Bulk operations** - Select multiple listings for batch editing
- **Spreadsheet-like workflows** - Keyboard navigation and quick scanning
- **Detailed comparisons** - See all metrics side-by-side in table format
- **High information density** - Maximum data visibility on desktop

### Table Columns

| Column | Content | Notes |
|--------|---------|-------|
| Checkbox | Row selection | Shift+click for range selection |
| Title | Listing name, device type, RAM/storage | Bold title with metadata below |
| CPU | CPU name and benchmark scores | Name (main), scores (small text) |
| Price | List price in USD | Right-aligned, currency format |
| Adjusted | Adjusted price with color accent | Right-aligned, color-coded |
| $/ST | Single-thread price efficiency | 3 decimal places |
| $/MT | Multi-thread price efficiency | 3 decimal places |
| Actions | Details, Quick Edit, More | Hover to reveal |

### Features

**Virtual Scrolling:**
- Smooth 60fps scrolling with 1000+ rows
- Only visible rows rendered for performance
- 5-item overscan for seamless scrolling

**Keyboard Navigation:**
- **Arrow Keys**: Navigate rows (updates focus)
- **Enter**: Open details dialog for focused row
- **Escape**: Clear focus
- **Tab**: Cycle through action buttons

**Bulk Selection:**
- Click checkbox to select individual rows
- Header checkbox selects all visible rows
- **Shift+Click**: Select range between last selection and current row
- Bulk selection panel appears with:
  - **Clear** button: Deselect all
  - **Bulk Edit** button: Edit selected listings

**Hover Actions:**
Row hover reveals action cluster (opacity-70 → opacity-100 transition):
- **Details** button: Opens details dialog
- **Quick Edit** icon: Opens inline editor
- **More** icon: Dropdown menu (archive, duplicate)

---

## Master/Detail View

### When to Use Master/Detail View

Master/Detail View is ideal for:
- **Contextual comparison** - Keep list context while viewing details
- **Multi-listing evaluation** - Compare up to 6 listings side-by-side
- **Focused analysis** - Full specifications without losing your place
- **Keyboard-driven workflows** - j/k navigation like vim

### Layout

**Mobile (< 1024px):**
- Stacked vertically: Master list above, detail panel below

**Desktop (>= 1024px):**
- Split horizontally: Master list (40% width), detail panel (60% width)

### Master List (Left Panel)

Scrollable list with 70vh height showing:

**Each Item Displays:**
- Title (bold)
- Adjusted price (right-aligned)
- CPU name and benchmark scores
- Compare checkbox at bottom

**Item States:**
- **Default**: Gray background, subtle border
- **Hover**: Light background change
- **Selected**: Primary border, muted background

**Interactions:**
- **Click Item**: Updates detail panel instantly
- **Click Checkbox**: Toggles compare selection (max 6)

### Detail Panel (Right Panel)

Full specifications for selected listing:

**KPI Metrics Grid:**
Four tiles displaying:
- **Price**: List price in USD
- **Adjusted**: Adjusted price with color accent
- **$/ST**: Single-thread price efficiency
- **$/MT**: Multi-thread price efficiency

Each tile shows accent color for good/warn/neutral valuation.

**Performance Badges:**
Same four badges as Grid View with tooltips.

**Specifications Grid:**
Two-column layout with key-value pairs:
- **CPU**: Name and manufacturer
- **Scores**: ST and MT benchmarks
- **RAM**: Capacity in GB
- **Storage**: Capacity and type
- **Condition**: New, refurbished, or used
- **Vendor**: Store/seller name
- **Ports**: Connectivity (when available)

**Header Actions:**
- Device type badge
- External link button (opens in new tab)

### Compare Drawer

**Trigger:**
Floating **"Compare (N)"** button appears when items selected (bottom-right of screen)

**Sheet Layout:**
- Bottom sheet (60vh height)
- Grid layout: 1-3 columns responsive
- First 6 items visible, scroll message if more

**Each Comparison Card Shows:**
- Title
- Adjusted price
- $/MT (multi-thread efficiency)
- CPU name
- Benchmark scores (ST/MT)
- Performance badges
- Remove button (X icon)

**Actions:**
- **Remove**: Click X to remove from comparison
- **Clear All**: Button in sheet header clears all selections
- **Close**: Click overlay or Escape key

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `j` | Navigate down in master list |
| `k` | Navigate up in master list |
| `c` | Toggle compare for focused item |
| `Enter` | Open details dialog |
| `Escape` | Close drawer / clear focus |

**Navigation Note:**
- Shortcuts auto-scroll to keep focused item visible
- Focus indicated by keyboard focus ring
- Works seamlessly with mouse/touch input

---

## Shared Features

### Filtering System

All views use the same sticky filter bar with real-time updates:

**Search Input:**
- Searches: title, CPU name, manufacturer, series, model number
- 200ms debounce for smooth typing experience
- Case-insensitive partial matching

**Form Factor Dropdown:**
- Options: All, Mini-PC, Laptop, Desktop, etc.
- Filter by device type
- "All" shows every listing

**Manufacturer Dropdown:**
- Options: All, ASUS, Dell, HP, Lenovo, etc.
- Filter by PC manufacturer
- "All" shows every manufacturer

**Price Range Slider:**
- Range: $0 - $10,000 (default max)
- Filters by list price OR adjusted price (whichever is higher)
- Live updates as you drag

**Clear Filters Button:**
- Appears when any filter is active
- Resets all filters to defaults:
  - Search: empty
  - Form Factor: All
  - Manufacturer: All
  - Price: $10,000 max

### Sorting

All views automatically sort by **adjusted $/MT** (ascending):
- Lower $/MT = better value (more performance per dollar)
- Best deals appear first
- Ties broken by listing ID

### State Persistence

Your preferences are saved across sessions:

**Persisted (LocalStorage):**
- Active view mode (Grid / List / Master-Detail)
- Active tab (Catalog / Data)
- Filter state (search, form factor, manufacturer, price)

**Not Persisted (Session Only):**
- Selected listing in Master/Detail view
- Compare selections
- Dialog open/close states

**URL Synchronization:**
- View mode and filters sync to URL params
- Share filtered views by copying URL
- Browser back/forward navigation works

### Dialogs

**Details Dialog:**
- Accessible from all views (click card/row)
- Shows KPI metrics, performance badges, full specs
- Footer link to full listing page (`/listings/{id}`)
- Keyboard shortcut: Escape to close

**Quick Edit Dialog:**
- Accessible from Grid View footer or List View actions
- Editable fields: Title, Price, Condition, Status
- Save triggers optimistic update + API call
- Error handling with toast notifications

---

## Best Practices

### Choosing the Right View

**Use Grid View when:**
- Browsing new listings for the first time
- Visual scanning is more important than detailed metrics
- Working on mobile or tablet
- Color-coded value indicators are helpful

**Use Dense List View when:**
- Performing bulk operations (bulk edit)
- Comparing metrics across many listings
- Working with keyboard-heavy workflows
- Information density is paramount

**Use Master/Detail View when:**
- Evaluating multiple specific listings (comparison)
- Need detailed specs without losing context
- Using keyboard shortcuts (j/k/c navigation)
- Comparing up to 6 listings side-by-side

### Filtering Strategies

**Finding Great Deals:**
1. Set price range to your budget
2. Filter by desired form factor (e.g., Mini-PC)
3. Search for preferred CPU (e.g., "i7")
4. Sort automatically shows best value first
5. Look for dark emerald adjusted prices (>15% savings)

**Comparing Similar Devices:**
1. Use Master/Detail view
2. Filter to narrow results (manufacturer, form factor)
3. Select interesting listings with compare checkbox
4. Open compare drawer to see side-by-side
5. Evaluate $/MT and adjusted prices

**Bulk Editing:**
1. Switch to Dense List View
2. Apply filters to target specific listings
3. Use shift+click for range selection
4. Click "Bulk Edit" in selection panel
5. Update fields and save

---

## Troubleshooting

### No Listings Showing

**Possible Causes:**
- Filters too restrictive (especially price range)
- No listings in database yet
- Search query doesn't match any listing

**Solutions:**
- Click "Clear Filters" button
- Check price slider (drag to max)
- Clear search box
- Verify listings exist in Data tab

### Performance Issues

**Symptoms:**
- Slow scrolling in Dense List View
- Laggy filter updates
- Browser freezing

**Solutions:**
- Reduce visible listings with filters
- Dense List View uses virtual scrolling (automatic)
- Close other browser tabs
- Check browser DevTools console for errors

### State Not Persisting

**Symptoms:**
- View mode resets on refresh
- Filters don't persist

**Solutions:**
- Check browser allows localStorage
- Try incognito mode (localStorage disabled)
- Clear browser cache and retry
- Check browser console for errors

---

## Accessibility

### Keyboard Navigation

All interactive elements are keyboard accessible:
- **Tab**: Move through interactive elements
- **Shift+Tab**: Move backward
- **Enter**: Activate buttons, open dialogs
- **Escape**: Close dialogs, clear focus
- **Arrow Keys**: Navigate rows (Dense List, Master List)

### Screen Reader Support

- ARIA labels on all icon-only buttons
- Dynamic content announces changes
- Semantic HTML throughout (nav, main, header, etc.)
- Color never sole indicator (icons + text + color)

### Focus Indicators

- Visible focus rings on all interactive elements
- Radix UI components provide built-in focus management
- Dialogs trap focus until closed
- Focus restoration when dialogs close

### High Contrast Mode

- Color accents work in high contrast mode
- Border styles ensure visibility
- Text contrast ratios exceed WCAG AA (4.5:1)
- Icons provide non-color indicators

---

## Developer Notes

### Component Architecture

```
apps/web/app/listings/page.tsx (main page)
├── Tabs (Catalog | Data)
│   ├── CatalogTab
│   │   ├── ListingsFilters (shared)
│   │   ├── ViewSwitcher
│   │   ├── GridView
│   │   │   └── ListingCard[]
│   │   ├── DenseListView
│   │   │   └── DenseTable (virtual scrolling)
│   │   └── MasterDetailView
│   │       ├── MasterList
│   │       ├── DetailPanel
│   │       └── CompareDrawer
│   └── DataTab (existing ListingsTable)
└── Dialogs
    ├── ListingDetailsDialog
    └── QuickEditDialog
```

### State Management

**Zustand Store** (`stores/catalog-store.ts`):
- Client state for view mode, filters, selections
- Persist middleware (localStorage)
- Custom hooks: `useFilters()`, `useCompare()`

**React Query**:
- Server state for listings data
- Automatic caching and refetch
- Optimistic updates for mutations

### Performance Optimizations

**React.memo:**
- All card/row components memoized
- Prevents unnecessary re-renders

**Virtual Scrolling:**
- `@tanstack/react-virtual` in Dense List View
- Only renders visible rows + 5 overscan
- Smooth 60fps scrolling with 1000+ rows

**Debouncing:**
- 200ms debounce on search input (`use-debounce`)
- 300ms debounce on URL updates

**Client-Side Filtering:**
- `useMemo` for filtered/sorted listings
- O(n) filtering for <1000 listings
- Server-side filtering planned for larger datasets

---

## Changelog

### Version 1.0 (2025-10-06)

**Initial Release:**
- Grid View with responsive layout and color-coded pricing
- Dense List View with virtual scrolling and bulk operations
- Master/Detail View with comparison drawer and keyboard shortcuts
- Shared filtering system with URL synchronization
- Error boundaries and loading states
- Empty state handling
- State persistence via LocalStorage

**Performance:**
- React.memo on all components
- Virtual scrolling for 1000+ rows
- 200ms search debounce
- Optimistic updates

**Accessibility:**
- WCAG AA compliant color contrast
- Full keyboard navigation
- Screen reader support
- Semantic HTML

---

## Feedback & Support

For questions, feature requests, or bug reports:
- Open an issue in the GitHub repository
- Contact the development team
- Check the PRD for planned features

---

*Last Updated: 2025-10-06*
*Version: 1.0*
*Maintainer: Claude Code*
