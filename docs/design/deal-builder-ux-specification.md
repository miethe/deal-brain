# Deal Builder UX/UI Specification

## Overview

The Deal Builder is an interactive tool that allows users to create custom PC builds by selecting components and seeing real-time valuation and performance calculations. This specification details the complete user experience, visual design, and interaction patterns.

## 1. Page Layout & Information Architecture

### 1.1 Navigation Integration

**Location in App**: New top-level navigation item
- Add to `NAV_ITEMS` between "Listings" and "Catalogs"
- Route: `/builder`
- Label: "Build & Price"

**Alternative Placement**: Could also go under a "Tools" dropdown if you want to keep the nav cleaner.

### 1.2 Page Structure

```
┌─────────────────────────────────────────────────────────────┐
│ Header: "Build & Price" + Actions (Save, Share, Compare)   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────────────┐│
│  │                      │  │                              ││
│  │  Component Builder   │  │  Live Valuation Panel       ││
│  │  (Left 60%)          │  │  (Right 40% - Sticky)       ││
│  │                      │  │                              ││
│  │  - Component Steps   │  │  - Running Total            ││
│  │  - Selection UI      │  │  - Deal Meter               ││
│  │  - Visual Cards      │  │  - Performance Metrics      ││
│  │                      │  │  - Breakdown Details        ││
│  │                      │  │                              ││
│  └──────────────────────┘  └──────────────────────────────┘│
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ Saved Builds Section (Optional - Collapsible)               │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Responsive Behavior

**Desktop (>1024px)**:
- Two-column layout with sticky valuation panel
- Component builder scrolls independently
- Valuation panel remains visible during scroll

**Tablet (768px - 1024px)**:
- Stack panels vertically
- Valuation panel sticks to top when scrolling past it
- Compact component cards (2-column grid)

**Mobile (<768px)**:
- Single column layout
- Floating "View Total" button that opens valuation drawer
- Component selection uses mobile-optimized selectors
- Compact cards stack vertically

## 2. Component Selection UI

### 2.1 Selection Flow & Hierarchy

**Ordered Component Steps** (Progressive disclosure):

1. **CPU** (Required) - Must select first
2. **RAM** (Optional but recommended)
3. **Primary Storage** (Optional but recommended)
4. **GPU** (Optional)
5. **Secondary Storage** (Optional)
6. **Other Components** (Collapsible section):
   - PSU
   - Case
   - Cooling
   - Motherboard
   - Other peripherals

### 2.2 Component Card Design

Each component type gets a card with the following states:

#### Empty State (Not Selected)
```
┌────────────────────────────────────────────────┐
│ 🔲 CPU                              [+ Select] │
│ Choose the processor for your build            │
│ 💡 Tip: Start here - affects performance calc  │
└────────────────────────────────────────────────┘
```

#### Selected State
```
┌────────────────────────────────────────────────┐
│ ✓ CPU                            [Edit] [×]    │
├────────────────────────────────────────────────┤
│  Intel Core i5-12400                           │
│  6 cores / 12 threads • 65W TDP                │
│  CPU Mark: 23,456 (Multi) | 3,234 (Single)    │
│                                                 │
│  Base Price: $189                              │
│  Adjusted: $165 (-$24 for used condition)      │
└────────────────────────────────────────────────┘
```

### 2.3 Component Selection Interface

**Selection Modal Design** (Preferred over inline dropdowns):

```
┌──────────────────────────────────────────────────────────┐
│ Select CPU                                        [×]     │
├──────────────────────────────────────────────────────────┤
│ 🔍 [Search CPUs...]                   Filter: ▼ All      │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Recommended (Based on current listings)                  │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ⭐ Intel Core i5-12400                     $189    │   │
│ │    6C/12T • 65W • CPU Mark: 23,456                │   │
│ │    💡 Great value - Popular in top deals          │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ Popular Options                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ○ AMD Ryzen 5 5600X                        $199    │   │
│ │    6C/12T • 65W • CPU Mark: 22,141                │   │
│ └───────────────────────────────────────────────────┘   │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ○ Intel Core i7-12700                      $329    │   │
│ │    12C/20T • 65W • CPU Mark: 35,657               │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ All CPUs (256)                                            │
│ [Load more...]                                            │
│                                                           │
├──────────────────────────────────────────────────────────┤
│                           [Cancel]  [Select Component]    │
└──────────────────────────────────────────────────────────┘
```

**Key Features**:
- Search with debounced filtering (200ms)
- "Recommended" section shows CPUs from top-performing listings
- Sort/filter options: Price, Performance, Efficiency, Popularity
- Visual hierarchy with performance metrics
- Hover shows additional details (release year, socket, etc.)
- Keyboard navigation support (arrow keys, Enter to select)

### 2.4 Component Information Display

**Required Information** (varies by component type):

**CPU**:
- Name
- Cores/Threads
- TDP
- CPU Mark (Multi & Single)
- iGPU Mark (if applicable)
- Estimated price range

**RAM**:
- Capacity (GB)
- Type (DDR4/DDR5)
- Speed (MHz)
- Module count
- Estimated price

**Storage**:
- Capacity (GB/TB)
- Type (NVMe/SSD/HDD)
- Interface (if relevant)
- Performance tier
- Estimated price

**GPU**:
- Model name
- VRAM
- Performance metrics
- TDP
- Estimated price

### 2.5 Filtering & Recommendations

**Smart Recommendations**:
1. **Based on Existing Listings**: Show components from highly-ranked deals
2. **Budget-Based**: Filter by price tiers (Budget, Mid-Range, High-End)
3. **Performance Tiers**: Group by PassMark score ranges
4. **Compatibility**: (Future enhancement - validate component compatibility)

**Filter Options**:
- Manufacturer (Intel, AMD, etc.)
- Performance tier
- Price range (slider)
- TDP/Power range
- Release year
- Form factor (for cases, motherboards)

## 3. Real-time Calculations Display

### 3.1 Live Valuation Panel (Sticky Right Panel)

```
┌──────────────────────────────────────────┐
│ Your Build                               │
├──────────────────────────────────────────┤
│                                          │
│ Total Price           $1,234             │
│ Adjusted Value        $987               │
│                                          │
│ ┌──────────────────────────────────────┐│
│ │ 💰 Great Deal!                       ││
│ │ -$247 (20.0% savings)                ││
│ │                                      ││
│ │ ████████████░░░░░░                   ││
│ │ Better than 78% of similar builds    ││
│ └──────────────────────────────────────┘│
│                                          │
│ Performance Metrics                      │
│ ├─ $/CPU Mark (Multi)    $0.042         │
│ ├─ $/CPU Mark (Single)   $0.305         │
│ └─ Composite Score       87.5           │
│                                          │
│ [View Breakdown ▼]                       │
│                                          │
│ ┌──────────────────────────────────────┐│
│ │ [Save Build]    [Share]    [Compare] ││
│ └──────────────────────────────────────┘│
└──────────────────────────────────────────┘
```

### 3.2 Deal Meter Visualization

**Progressive Color-Coded Meter**:

```
┌────────────────────────────────────────────┐
│                                            │
│  Premium      Fair      Good      Great    │
│  ├─────────────┼──────────┼────────┼─────┤ │
│  🔴           🟡        🟢       🟢🟢     │
│                            ▲               │
│                        Your Build          │
└────────────────────────────────────────────┘
```

**Indicator States** (matching existing valuation system):

1. **Great Deal** (25%+ savings):
   - Dark green background
   - "🔥 Great Deal!" header
   - Shows absolute and percentage savings
   - Animated badge pulse

2. **Good Deal** (15-25% savings):
   - Medium green background
   - "💰 Good Deal!" header
   - Shows savings breakdown

3. **Fair Deal** (0-15% savings):
   - Light green background
   - "✓ Fair Deal" header
   - Shows slight savings

4. **Premium** (markup >10%):
   - Red background
   - "⚠️ Premium Price" header
   - Shows markup amount
   - Warning text about above-market pricing

5. **Neutral** (0% delta):
   - Gray background
   - "Market Price" header

### 3.3 Valuation Breakdown Expandable Section

**Collapsed State**:
```
[View Breakdown ▼]
```

**Expanded State**:
```
┌──────────────────────────────────────────┐
│ Valuation Breakdown                  [▲] │
├──────────────────────────────────────────┤
│                                          │
│ Base Component Costs                     │
│ ├─ CPU (i5-12400)           $189         │
│ ├─ RAM (16GB DDR4)          $45          │
│ ├─ Storage (512GB NVMe)     $55          │
│ └─ GPU (GTX 1660 Super)     $220         │
│ ─────────────────────────────────────    │
│ Subtotal                    $509         │
│                                          │
│ Adjustments Applied                      │
│ ├─ Used CPU (-15%)          -$28         │
│ ├─ Older generation (-5%)   -$11         │
│ ├─ Bulk RAM discount        -$8          │
│ ─────────────────────────────────────    │
│ Total Adjustments           -$47         │
│                                          │
│ Final Adjusted Value        $462         │
│                                          │
│ 💡 Applied 3 valuation rules              │
│    [View Full Rule Details →]            │
└──────────────────────────────────────────┘
```

### 3.4 Performance Metrics Display

**Key Metrics** (calculated in real-time):

1. **$/CPU Mark (Multi-thread)**:
   - Formula: `adjusted_price / cpu_mark_multi`
   - Lower is better
   - Display with 3 decimal places

2. **$/CPU Mark (Single-thread)**:
   - Formula: `adjusted_price / cpu_mark_single`
   - Lower is better
   - Display with 3 decimal places

3. **Composite Score**:
   - Weighted score based on selected profile
   - 0-100 scale
   - Shows comparison to database average

**Display Format**:
```
Performance Metrics
┌──────────────────────────────────────┐
│ $/CPU Mark (Multi)        $0.042     │
│ 💡 23% better than average           │
│                                      │
│ $/CPU Mark (Single)       $0.305     │
│ 💡 15% better than average           │
│                                      │
│ Composite Score           87.5       │
│ ████████████████████░░               │
│ Better than 78% of listings          │
└──────────────────────────────────────┘
```

### 3.5 Empty State (No Components Selected)

```
┌──────────────────────────────────────────┐
│ Your Build                               │
├──────────────────────────────────────────┤
│                                          │
│        🔧                                │
│    Start Building!                       │
│                                          │
│  Select components to see real-time      │
│  pricing and value calculations          │
│                                          │
│  💡 Tip: Start with a CPU               │
│                                          │
└──────────────────────────────────────────┘
```

## 4. Build Management

### 4.1 Save Build Functionality

**Save Button** triggers modal:

```
┌──────────────────────────────────────────┐
│ Save Build                           [×] │
├──────────────────────────────────────────┤
│                                          │
│ Build Name *                             │
│ [Budget Gaming PC 2024...............]   │
│                                          │
│ Description (Optional)                   │
│ [Balanced build for 1080p gaming.....]  │
│ [...................................]    │
│                                          │
│ Tags (Optional)                          │
│ [gaming] [budget] [1080p]               │
│ + Add tag                                │
│                                          │
│ Privacy                                  │
│ ○ Private (Only you)                     │
│ ● Public (Anyone with link can view)     │
│ ○ Unlisted (Hidden from public gallery)  │
│                                          │
│ ☑ Include price snapshot                │
│ ☑ Track price changes                   │
│                                          │
├──────────────────────────────────────────┤
│               [Cancel]  [Save Build]     │
└──────────────────────────────────────────┘
```

**Saved Build Data Structure**:
```typescript
interface SavedBuild {
  id: string;
  name: string;
  description?: string;
  tags: string[];
  visibility: 'private' | 'public' | 'unlisted';
  components: {
    cpu_id?: number;
    gpu_id?: number;
    ram_spec_id?: number;
    primary_storage_profile_id?: number;
    secondary_storage_profile_id?: number;
    // ... other components
  };
  pricing_snapshot: {
    base_price: number;
    adjusted_price: number;
    component_prices: Record<string, number>;
    snapshot_date: string;
  };
  performance_metrics: {
    dollar_per_cpu_mark_multi: number;
    dollar_per_cpu_mark_single: number;
    composite_score: number;
  };
  valuation_breakdown: ValuationBreakdown;
  created_at: string;
  updated_at: string;
  user_id?: string; // For multi-user support
}
```

### 4.2 Saved Builds View

**Collapsible Section at Bottom of Page**:

```
┌─────────────────────────────────────────────────────────┐
│ Your Saved Builds (3)                            [+New] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─────────────────┐ ┌─────────────────┐ ┌────────────┐│
│ │ Gaming PC 2024  │ │ Budget Build    │ │ Workstation││
│ │                 │ │                 │ │            ││
│ │ $1,234 → $987   │ │ $650 → $520     │ │ $2.1k → ...││
│ │ 💰 Good Deal    │ │ 🔥 Great Deal   │ │ ⚠️ Premium ││
│ │                 │ │                 │ │            ││
│ │ Created: 2d ago │ │ Created: 1w ago │ │ Created: ..││
│ │                 │ │                 │ │            ││
│ │ [Load] [Share]  │ │ [Load] [Share]  │ │ [Load] [...││
│ │ [Edit] [Delete] │ │ [Edit] [Delete] │ │ [Edit] [De││
│ └─────────────────┘ └─────────────────┘ └────────────┘│
└─────────────────────────────────────────────────────────┘
```

**Card Hover Actions**:
- **Load**: Populate builder with saved components
- **Edit**: Open in builder and allow modifications
- **Share**: Copy link or open share modal
- **Duplicate**: Create a copy for variations
- **Delete**: Remove build (with confirmation)

**Grid Layout**:
- Desktop: 3 columns
- Tablet: 2 columns
- Mobile: 1 column (cards stack)

### 4.3 Edit vs. Load Behavior

**Load Build**:
- Clears current builder
- Populates all components from saved build
- Shows "Loaded from: [Build Name]" banner
- Unsaved changes prompt on navigation

**Edit Build**:
- Same as Load but sets "editing mode"
- Save button updates existing build instead of creating new
- Shows "Editing: [Build Name]" in header

## 5. Sharing Features

### 5.1 Share Modal

```
┌──────────────────────────────────────────┐
│ Share Build                          [×] │
├──────────────────────────────────────────┤
│                                          │
│ Share Link                               │
│ ┌──────────────────────────────────────┐│
│ │ dealbrain.app/build/a1b2c3d4         ││
│ │                          [Copy] 📋   ││
│ └──────────────────────────────────────┘│
│                                          │
│ Quick Share                              │
│ [Twitter] [Reddit] [Discord] [Email]    │
│                                          │
│ Export Options                           │
│ [📄 PDF]  [🔗 Link]  [📋 Text List]     │
│                                          │
│ ☑ Include pricing snapshot              │
│ ☑ Include performance metrics           │
│ ☐ Include component links               │
│                                          │
└──────────────────────────────────────────┘
```

### 5.2 Shareable Link Format

**URL Structure**: `/builder/shared/[build-id]`

**Shared View Page** (read-only):
- Displays full build with all components
- Shows pricing and valuation at time of share
- "Build Your Own" CTA button to copy to new build
- Price update banner if components have changed price
- Optional: "Track this build" to get price alerts

### 5.3 Export Formats

**PDF Export** (for sharing/printing):
- Build name and description
- Component list with images
- Pricing breakdown
- Performance metrics chart
- QR code with share link
- Deal Brain branding

**Text List** (for forums/Discord):
```
🖥️ Gaming PC Build - Deal Brain
────────────────────────────────
CPU: Intel Core i5-12400 ($189)
RAM: 16GB DDR4-3200 ($45)
Storage: 512GB NVMe ($55)
GPU: GTX 1660 Super ($220)
────────────────────────────────
Total: $509 → $462 (💰 Good Deal!)
$/CPU Mark: $0.042

Built with Deal Brain: https://dealbrain.app/build/abc123
```

**JSON Export** (for advanced users):
```json
{
  "build": {
    "name": "Gaming PC Build",
    "components": { ... },
    "pricing": { ... },
    "metrics": { ... }
  }
}
```

## 6. Visual Design

### 6.1 Color System (Matching Existing Valuation Colors)

**Deal Quality Indicators**:

```css
/* Great Deal (25%+ savings) */
--valuation-great-deal-bg: 142 76% 36%;
--valuation-great-deal-fg: 142 76% 96%;
--valuation-great-deal-border: 142 76% 46%;

/* Good Deal (15-25% savings) */
--valuation-good-deal-bg: 142 69% 58%;
--valuation-good-deal-fg: 142 10% 10%;
--valuation-good-deal-border: 142 69% 48%;

/* Light Savings (1-15%) */
--valuation-light-saving-bg: 142 76% 86%;
--valuation-light-saving-fg: 142 76% 16%;
--valuation-light-saving-border: 142 76% 76%;

/* Premium (10%+ markup) */
--valuation-premium-bg: 0 84% 60%;
--valuation-premium-fg: 0 0% 100%;
--valuation-premium-border: 0 84% 50%;

/* Light Premium */
--valuation-light-premium-bg: 0 84% 90%;
--valuation-light-premium-fg: 0 84% 20%;
--valuation-light-premium-border: 0 84% 80%;

/* Neutral */
--valuation-neutral-bg: 0 0% 85%;
--valuation-neutral-fg: 0 0% 25%;
--valuation-neutral-border: 0 0% 75%;
```

### 6.2 Component Card States

**Default (Unselected)**:
- Border: `border-border` (neutral gray)
- Background: `bg-card`
- Hover: `border-primary/50` with subtle shadow
- Icon: Muted color

**Selected**:
- Border: `border-primary` (2px)
- Background: `bg-card`
- Icon: Primary color
- Checkmark badge in top-right corner

**Required (Empty)**:
- Border: `border-amber-500/50` (dashed)
- Background: `bg-amber-50/50` (light amber tint)
- Helper text: Amber color

### 6.3 Typography Hierarchy

```css
/* Page Title */
h1: text-3xl font-bold tracking-tight

/* Section Headers */
h2: text-xl font-semibold

/* Component Card Titles */
h3: text-lg font-medium

/* Prices */
.price-primary: text-2xl font-bold tabular-nums
.price-adjusted: text-lg font-semibold tabular-nums text-green-600
.price-delta: text-sm tabular-nums text-muted-foreground

/* Metrics */
.metric-label: text-sm font-medium text-muted-foreground
.metric-value: text-base font-semibold tabular-nums

/* Helper Text */
.helper-text: text-sm text-muted-foreground
```

### 6.4 Spacing & Layout

**Card Spacing**:
- Gap between component cards: `gap-4` (16px)
- Card internal padding: `p-6` (24px)
- Card border radius: `rounded-lg` (8px)

**Panel Spacing**:
- Between sections: `space-y-6` (24px)
- Within sections: `space-y-4` (16px)
- Compact sections: `space-y-2` (8px)

**Responsive Breakpoints**:
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

### 6.5 Icons & Visual Elements

**Component Type Icons** (lucide-react):
- CPU: `Cpu`
- RAM: `MemoryStick`
- Storage: `HardDrive`
- GPU: `Monitor` or `Zap`
- PSU: `Zap`
- Case: `Box`
- Motherboard: `Boxes`

**Status Icons**:
- Selected: `CheckCircle2`
- Required: `AlertCircle`
- Optional: `Circle`
- Info: `Info`
- Edit: `Edit2` or `Pencil`
- Delete: `Trash2`
- Share: `Share2`
- Copy: `Copy`

### 6.6 Micro-interactions

**Hover States**:
- Component cards: Scale 1.02, shadow-md
- Buttons: Opacity 0.9
- Links: Underline

**Click Feedback**:
- Buttons: Scale 0.98 on active
- Cards: Brief border color flash on selection

**Loading States**:
- Component selection: Skeleton loader
- Price updates: Shimmer effect on price display
- Save/share: Spinner in button

**Success States**:
- Save: Green checkmark animation
- Copy link: "Copied!" toast notification
- Component selected: Slide-in from right

## 7. Edge Cases & User Feedback

### 7.1 Validation & Error States

**CPU Not Selected Warning**:
```
⚠️ Select a CPU to calculate performance metrics
```
- Appears in valuation panel
- Amber background
- Blocks performance calculations

**Incomplete Build**:
```
💡 Tip: Add RAM and Storage for complete valuation
```
- Informational (not blocking)
- Appears below component list
- Dismissible

**Component Compatibility Warning** (Future):
```
⚠️ Selected RAM may not be compatible with CPU
   → Check DDR4 vs DDR5 support
```

### 7.2 Loading States

**Initial Page Load**:
- Skeleton loaders for component cards
- Placeholder valuation panel
- Fade-in animation when loaded

**Component Selection Modal**:
- Skeleton rows while fetching catalog
- "Loading components..." spinner
- Disable search during initial load

**Calculation Updates**:
- Brief spinner overlay on valuation panel
- Smooth number transitions (animated count-up)
- Debounced to avoid flashing (200ms)

### 7.3 Empty States

**No Saved Builds**:
```
┌─────────────────────────────────────┐
│        📁                           │
│   No saved builds yet               │
│                                     │
│   Create your first build above     │
│   and save it for later!            │
│                                     │
│   [Start Building →]                │
└─────────────────────────────────────┘
```

**Component Not Available**:
```
⚠️ This component is no longer in our catalog
   → [Select Alternative]
```

### 7.4 Comparison with Existing Listings

**"Compare to Listings" Feature**:

Button in valuation panel that opens drawer:

```
┌──────────────────────────────────────────┐
│ Similar Listings                     [×] │
├──────────────────────────────────────────┤
│                                          │
│ Your Build: $987 (adjusted)              │
│                                          │
│ Similar Pre-Built Systems:               │
│ ┌──────────────────────────────────────┐│
│ │ Dell OptiPlex 7090 - $1,099          ││
│ │ Similar specs • 11% more expensive   ││
│ │ [View Details →]                     ││
│ └──────────────────────────────────────┘│
│                                          │
│ ┌──────────────────────────────────────┐│
│ │ HP EliteDesk 800 G8 - $950           ││
│ │ Similar specs • 4% less expensive    ││
│ │ 💰 Better deal!                      ││
│ │ [View Details →]                     ││
│ └──────────────────────────────────────┘│
│                                          │
│ [See All Similar Listings (12)]          │
└──────────────────────────────────────────┘
```

### 7.5 Data Validation

**Price Validation**:
- Warn if component price is outdated (>30 days)
- Show "Pricing may be stale" banner
- Offer "Refresh Prices" button

**Component Conflicts**:
- Detect and warn about impossible configurations
- Example: DDR5 RAM with DDR4-only CPU

**Missing Benchmark Data**:
- Show "Performance metrics unavailable" message
- Offer manual input option (advanced users)

## 8. Mobile Responsiveness

### 8.1 Mobile Layout Adjustments

**Single Column Layout**:
- Component cards stack vertically
- Full-width cards
- Compact card design (less padding)

**Floating Total Button**:
```
┌──────────────────────────────────────┐
│                                      │
│  (scrollable content)                │
│                                      │
└──────────────────────────────────────┘
        ┌────────────────┐
        │ $987           │
        │ 💰 Good Deal   │
        │ [View Details] │
        └────────────────┘
```
- Sticky to bottom of screen
- Tapping opens drawer with full valuation panel

**Mobile Component Selection**:
- Native mobile select for better UX
- Or full-screen modal with search
- Touch-friendly tap targets (44px minimum)

**Swipe Gestures**:
- Swipe left on component card: Edit/Delete actions
- Swipe down on valuation drawer: Close

### 8.2 Touch Interactions

**Tap Targets**:
- Minimum 44x44px for all interactive elements
- Increased padding around buttons on mobile
- Larger icons in mobile view

**Gesture Support**:
- Pull to refresh saved builds
- Swipe to dismiss modals
- Long-press for component details

## 9. Accessibility (WCAG AA Compliant)

### 9.1 Keyboard Navigation

**Tab Order**:
1. Header actions (Save, Share, Compare)
2. Component cards (in order)
3. Component action buttons (Select, Edit, Delete)
4. Valuation panel controls
5. Saved builds section

**Keyboard Shortcuts**:
- `/`: Focus search in component modal
- `Esc`: Close modal/drawer
- `Ctrl+S`: Save build
- `Ctrl+K`: Open command palette (future)

### 9.2 Screen Reader Support

**ARIA Labels**:
- All buttons have clear labels
- Component cards: `aria-label="CPU component, not selected"`
- Deal meter: `aria-label="Deal quality: Good deal, 20% savings"`

**Live Regions**:
- Price updates announce via `aria-live="polite"`
- Component selection announces: "CPU selected: Intel Core i5-12400"

**Semantic HTML**:
- Use `<main>`, `<section>`, `<article>` appropriately
- Form inputs have associated `<label>` elements
- Buttons vs links used semantically

### 9.3 Color Contrast

**Text Contrast**:
- All text meets 4.5:1 contrast ratio minimum
- Large text (18pt+) meets 3:1 ratio
- UI components meet 3:1 contrast with adjacent colors

**Dark Mode Support**:
- All colors have dark mode variants
- Deal indicators remain distinguishable
- Icons maintain contrast

## 10. Performance Considerations

### 10.1 Optimization Strategies

**Component Memoization**:
- Memoize component cards with React.memo
- Optimize valuation panel re-renders
- Debounce calculation updates (200ms)

**Data Fetching**:
- Prefetch component catalogs on page load
- Cache component data with React Query (5min stale time)
- Lazy load saved builds section

**Image Optimization**:
- Use Next.js Image component for component images
- Lazy load component thumbnails
- Placeholder blur while loading

### 10.2 Code Splitting

**Route-level Splitting**:
- Builder page loads independently
- Component selection modals loaded on-demand
- Share/export features loaded when needed

**Component Lazy Loading**:
```typescript
const ComponentModal = lazy(() => import('./component-modal'));
const SaveBuildModal = lazy(() => import('./save-build-modal'));
```

## 11. Technical Implementation Notes

### 11.1 Data Flow

```typescript
// Builder state management
interface BuilderState {
  selectedComponents: {
    cpu?: number;
    gpu?: number;
    ram_spec?: number;
    primary_storage_profile?: number;
    secondary_storage_profile?: number;
  };
  pricing: {
    base_price: number;
    adjusted_price: number;
    component_prices: Record<string, number>;
  };
  metrics: {
    dollar_per_cpu_mark_multi?: number;
    dollar_per_cpu_mark_single?: number;
    composite_score?: number;
  };
  valuation_breakdown?: ValuationBreakdown;
}
```

### 11.2 API Endpoints Needed

```typescript
// New endpoints to create:
POST   /v1/builder/calculate         // Calculate valuation for build
POST   /v1/builder/builds            // Save build
GET    /v1/builder/builds            // Get user's saved builds
GET    /v1/builder/builds/:id        // Get specific build
PATCH  /v1/builder/builds/:id        // Update build
DELETE /v1/builder/builds/:id        // Delete build
GET    /v1/builder/builds/:id/share  // Get shareable link data
GET    /v1/builder/compare           // Compare build to listings
GET    /v1/builder/recommendations   // Get recommended components
```

### 11.3 Reusable Components

**From Existing Codebase**:
- `ValuationCell` - Adapt for build total display
- `DeltaBadge` - Use for savings display
- `Button`, `Card`, `Badge` - UI primitives
- `ComboBox` - Component selection
- `Modal`/`Dialog` - Selection and save modals

**New Components to Create**:
- `ComponentCard` - Individual component display
- `ComponentSelector` - Modal for picking components
- `BuildValuationPanel` - Sticky right panel
- `DealMeter` - Visual deal quality indicator
- `SavedBuildCard` - Saved build thumbnail
- `ShareModal` - Sharing options
- `ComponentComparison` - Side-by-side component comparison

## 12. Future Enhancements

### 12.1 Phase 2 Features

1. **Component Compatibility Validation**
   - Check RAM type compatibility with CPU
   - Validate PSU wattage for build
   - Check case size for GPU length

2. **Price History Tracking**
   - Track component price changes over time
   - Alert users when saved build components drop in price
   - Show historical pricing charts

3. **Build Templates**
   - Pre-configured builds for common use cases
   - "Gaming", "Workstation", "Budget", "High-End"
   - Community-shared build templates

4. **AI-Powered Recommendations**
   - Suggest complementary components
   - Optimize for specific budgets
   - Balance bottlenecks

### 12.2 Phase 3 Features

1. **Social Features**
   - Public build gallery
   - Upvote/comment on builds
   - Follow users with great builds
   - Build of the week/month

2. **Advanced Analytics**
   - Performance per watt calculations
   - Upgrade path suggestions
   - Value retention predictions

3. **Integration with Listings**
   - "Find this build" button to search listings
   - Alert when similar pre-built appears
   - Convert listing to build for modification

## 13. Summary & Implementation Priority

### Priority 1 (MVP - Week 1-2)
- [x] Basic page structure and layout
- [x] Component selection for CPU, RAM, Storage
- [x] Real-time price calculation
- [x] Basic valuation display with deal meter
- [x] Save build functionality (local storage initially)

### Priority 2 (Enhanced - Week 3)
- [x] GPU selection
- [x] Full valuation breakdown
- [x] Performance metrics calculation
- [x] Share build via URL
- [x] Saved builds persistence (database)

### Priority 3 (Polish - Week 4)
- [x] Compare to listings feature
- [x] Component recommendations
- [x] Export to PDF/Text
- [x] Mobile optimization
- [x] Accessibility improvements

### Priority 4 (Future)
- [ ] Component compatibility checks
- [ ] Price history tracking
- [ ] Build templates
- [ ] Social features

---

## Design Tokens Reference

```typescript
// Spacing
const spacing = {
  cardGap: '1rem',           // 16px
  sectionGap: '1.5rem',      // 24px
  componentPadding: '1.5rem', // 24px
  panelPadding: '1.5rem',    // 24px
}

// Border Radius
const borderRadius = {
  card: '0.5rem',           // 8px
  button: '0.375rem',       // 6px
  badge: '9999px',          // pill shape
}

// Typography
const typography = {
  pageTitle: 'text-3xl font-bold',
  sectionTitle: 'text-xl font-semibold',
  cardTitle: 'text-lg font-medium',
  price: 'text-2xl font-bold tabular-nums',
  metric: 'text-base font-semibold tabular-nums',
}

// Breakpoints
const breakpoints = {
  mobile: '768px',
  tablet: '1024px',
  desktop: '1280px',
}
```

---

This specification provides a comprehensive blueprint for implementing the Deal Builder feature. It maintains consistency with your existing design system, leverages your current components and APIs, and provides a clear roadmap from MVP to full feature set.

The design prioritizes user experience, performance, and accessibility while staying true to Deal Brain's core value proposition: transparent, data-driven PC valuation.
