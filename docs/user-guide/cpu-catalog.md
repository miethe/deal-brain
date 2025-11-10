---
title: "CPU Catalog User Guide"
description: "Comprehensive guide to browsing, filtering, and analyzing CPUs in the Deal Brain catalog with performance metrics and market insights"
audience: [users, developers]
tags:
  - cpu-catalog
  - user-guide
  - features
  - analytics
  - price-targets
  - performance-metrics
created: 2025-11-06
updated: 2025-11-06
category: user-documentation
status: published
related:
  - /docs/user-guide/performance-metrics.md
  - /docs/user-guide/catalog-views.md
---

# CPU Catalog User Guide

**Version:** 1.0
**Last Updated:** 2025-11-06

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [View Modes](#view-modes)
4. [Understanding Performance Metrics](#understanding-performance-metrics)
5. [Price Targets](#price-targets)
6. [Filtering and Sorting](#filtering-and-sorting)
7. [CPU Detail Modal](#cpu-detail-modal)
8. [Common Workflows](#common-workflows)
9. [Tips and Best Practices](#tips-and-best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Glossary](#glossary)

---

## Overview

The CPU Catalog is a comprehensive browsing and analysis interface for exploring processors with real-time market insights, performance metrics, and pricing benchmarks. It provides data-driven guidance for evaluating CPU value propositions based on both historical pricing and performance benchmarks.

### Key Features

- **Three View Modes**: Grid, List, and Master-Detail views optimized for different workflows
- **Performance Metrics**: Dollar-per-PassMark value ratings showing price efficiency
- **Price Targets**: Market-derived pricing benchmarks (Great, Good, Fair) from real listings
- **Advanced Filtering**: Filter by manufacturer, socket, cores, TDP, price range, and more
- **Market Analytics**: Associated listings count, price distributions, and benchmark comparisons
- **Interactive Details**: Comprehensive CPU specifications with performance charts

### Who Should Use This Guide

This guide is designed for:
- Deal Brain users evaluating PC listings and CPU options
- Price analysts researching CPU market pricing
- PC builders comparing processor value propositions
- System integrators sourcing components

---

## Getting Started

### Accessing the CPU Catalog

Navigate to the CPU Catalog from the main navigation:

1. Click **"CPUs"** in the sidebar navigation menu (under "Catalogs" section)
2. The catalog opens in **Catalog** tab by default with Grid View active
3. All CPUs are displayed initially (filterable to show only CPUs with active listings)

### Interface Overview

The CPU Catalog page consists of two main tabs:

**Catalog Tab:**
- Visual browsing interface with three view modes
- Filter panel for narrowing results
- View switcher to toggle between Grid, List, and Master-Detail modes
- Quick access to CPU details via modal

**Data Tab:**
- Traditional data table with sortable columns
- Column visibility controls
- Pagination and export options
- Bulk selection capabilities

### Navigation Tips

- Use the **Tab switcher** to toggle between Catalog and Data views
- Use the **View switcher** (Grid, List, Master-Detail) in Catalog tab
- Filters persist across view mode changes
- Your preferred view mode is saved across sessions

[Screenshot placeholder: CPU Catalog page showing Catalog and Data tabs with Grid View active]

---

## View Modes

The CPU Catalog offers three distinct view modes, each optimized for different tasks and workflows.

### Grid View

**Best For:**
- Visual browsing and exploration
- Quick comparison of multiple CPUs
- Identifying value opportunities with color-coded indicators
- Mobile and tablet browsing

**Layout:**
- Responsive grid adjusting to screen size:
  - **Mobile (< 640px)**: 1 column
  - **Tablet (640-1024px)**: 2 columns
  - **Desktop (1024-1280px)**: 3 columns
  - **Large Desktop (> 1280px)**: 4 columns

**Card Components:**

Each CPU card displays:

1. **Header Section**
   - CPU name (bold, prominent)
   - Manufacturer badge (Intel, AMD)

2. **Specifications**
   - Cores/Threads (e.g., "8C/16T")
   - Socket (e.g., "LGA1700")
   - TDP (e.g., "125W")
   - Release Year (e.g., "2021")

3. **Performance Badges**
   - Single-Thread PassMark score
   - Multi-Thread PassMark score
   - iGPU Mark (if integrated graphics present)
   - Visual bars showing relative performance

4. **Performance Value Indicators**
   - $/Single-Thread Mark rating badge
   - $/Multi-Thread Mark rating badge
   - Color-coded: Excellent (green), Good (blue), Fair (yellow), Poor (red)

5. **Price Targets**
   - Good Price (median market price)
   - Great Price (25th percentile)
   - Fair Price (75th percentile)
   - Confidence badge (High, Medium, Low)

6. **Market Data**
   - Active listings count

**Interactions:**
- **Click Card**: Opens CPU detail modal
- **Hover**: Subtle highlight effect
- **Keyboard Navigation**: Tab through cards, Enter to open modal

[Screenshot placeholder: Grid View showing 6-8 CPU cards with all components visible]

---

### List View

**Best For:**
- Compact browsing with higher information density
- Quick scanning of many CPUs
- Comparing key metrics at a glance
- Desktop workflows

**Layout:**
- Vertical list of CPU entries
- Each row shows condensed information
- Hover effects reveal additional actions

**Row Components:**

Each list item displays:

1. **CPU Name and Manufacturer** (left-aligned, bold)
2. **Key Specs** (inline summary)
   - Cores/Threads/TDP
   - Socket type
3. **Performance Value Badge**
   - Single-thread $/PassMark rating
   - Color-coded indicator
4. **Price Target**
   - Good Price emphasized
   - Confidence indicator
5. **Actions**
   - Quick view button
   - Appears on hover

**Interactions:**
- **Click Row**: Opens CPU detail modal
- **Hover**: Highlights row and reveals actions
- **Keyboard Navigation**: Arrow keys to navigate, Enter to open modal

[Screenshot placeholder: List View showing 10-12 CPU rows in compact format]

---

### Master-Detail View

**Best For:**
- In-depth analysis of specific CPUs
- Side-by-side comparison workflow
- Detailed specification review
- Research and evaluation tasks

**Layout:**

**Desktop (>= 1024px):**
- Split horizontally into two panels
- **Left Panel (40% width)**: Master list of CPUs
- **Right Panel (60% width)**: Detail panel for selected CPU

**Mobile (< 1024px):**
- Stacked vertically
- Master list above, detail panel below

**Master List (Left Panel):**

Scrollable list (70vh height) displaying:
- CPU name (bold)
- Manufacturer badge
- Cores/Threads
- PassMark scores (single/multi)
- Price target (Good price)

**Item States:**
- Default: Gray background
- Hover: Light highlight
- Selected: Primary border with muted accent

**Detail Panel (Right Panel):**

Comprehensive CPU information organized into sections:

1. **KPI Metrics Grid**
   - Four tile layout showing:
     - Good Price (median)
     - Great Price (25th percentile)
     - $/Single-Thread Mark
     - $/Multi-Thread Mark
   - Each tile color-coded for value quality

2. **Performance Metrics**
   - PassMark Multi-Thread score with bar chart
   - PassMark Single-Thread score with bar chart
   - iGPU Mark (if applicable)
   - Performance value badges (Excellent/Good/Fair/Poor)

3. **Specifications Grid**
   - Two-column key-value layout:
     - CPU Model & Manufacturer
     - Cores & Threads
     - Socket & TDP
     - Base & Boost Clock (if available)
     - Release Year
     - iGPU Model

4. **Price Distribution Chart**
   - Histogram showing listing price ranges
   - Statistical markers (25th, 50th, 75th percentiles)
   - Sample size indicator

5. **Associated Listings**
   - Count of active listings with this CPU
   - Top 5 listings preview
   - "View All Listings" button

6. **External Resources**
   - PassMark benchmark page link
   - Comparison tool links (future)

**Interactions:**
- **Click Master List Item**: Updates detail panel instantly
- **Keyboard Shortcuts**:
  - `j`: Navigate down master list
  - `k`: Navigate up master list
  - `Enter`: Open full detail modal
  - `Escape`: Clear focus
- **Auto-scroll**: Focused item stays visible in scrollable list

[Screenshot placeholder: Master-Detail View showing left list and right detail panel with all sections]

---

## Understanding Performance Metrics

### Performance Value Ratings

Performance Value indicates **price efficiency** measured in **dollars per PassMark point**. This metric answers: "How much am I paying per unit of performance?"

**Lower is better** — you get more performance per dollar spent.

### Rating Tiers

| Badge | Color | Meaning | Typical Range | Percentile |
|-------|-------|---------|---------------|------------|
| **Excellent** | Dark Green | Top 25% value | < $0.08/mark | 0-25th |
| **Good** | Blue | Above average value | $0.08-$0.12/mark | 26-50th |
| **Fair** | Yellow | Average value | $0.12-$0.18/mark | 51-75th |
| **Poor** | Red | Below average value | > $0.18/mark | 76-100th |

### Dual Metrics: Single-Thread vs Multi-Thread

Performance value is calculated for **both** PassMark benchmarks:

#### $/Single-Thread Mark ($/ST Mark)

**Formula:**
```
$/ST Mark = Adjusted Price ÷ PassMark Single-Thread Rating
```

**Best For:**
- Gaming performance (most games favor single-thread)
- Everyday desktop responsiveness
- Web browsing and office applications
- General productivity tasks

**Example:**
```
CPU: Intel Core i5-12400
Adjusted Price: $600
Single-Thread Rating: 3,200
$/ST Mark: $0.19 per point (Fair value)
```

#### $/Multi-Thread Mark ($/MT Mark)

**Formula:**
```
$/MT Mark = Adjusted Price ÷ PassMark Multi-Thread Rating (CPU Mark)
```

**Best For:**
- Video editing and rendering
- 3D modeling and CAD
- Software compilation
- Virtualization and server workloads
- Scientific computing

**Example:**
```
CPU: AMD Ryzen 7 5800X
Adjusted Price: $700
Multi-Thread Rating: 28,000
$/MT Mark: $0.025 per point (Excellent value)
```

### Percentile Ranking

Each CPU's performance value is ranked against **all CPUs in the catalog**:

- **15th percentile** = Better than 85% of CPUs (Excellent)
- **35th percentile** = Better than 65% of CPUs (Good)
- **60th percentile** = Better than 40% of CPUs (Fair)
- **85th percentile** = Worse than 85% of CPUs (Poor)

**Lower percentile = Better value**

### How to Use Performance Metrics

**When Comparing CPUs:**

1. **Match Use Case to Metric**
   - Gaming build? Prioritize $/ST Mark
   - Workstation? Prioritize $/MT Mark
   - Balanced use? Consider both equally

2. **Look for Green Badges**
   - "Excellent" badges indicate top-tier value
   - Multiple "Good" or "Excellent" badges = strong all-around value

3. **Compare Within Price Brackets**
   - A $300 CPU with Fair $/MT may still outperform a $200 CPU with Excellent $/MT
   - Compare similar-priced CPUs for true value assessment

4. **Check Percentile Rank**
   - Lower percentile = better deal
   - 15th percentile is significantly better than 60th percentile

[Screenshot placeholder: Performance badge examples showing all 4 tiers with tooltips]

---

## Price Targets

Price Targets are **statistical benchmarks** derived from actual marketplace listings, showing what you should expect to pay based on recent market activity.

### Price Tiers Explained

Price targets use **percentile-based pricing** from adjusted listing prices:

#### Great Price (25th Percentile)

**Definition:** The price point below which **25% of listings** are sold.

**Meaning:** An excellent deal — you're paying less than 75% of similar listings.

**When to Target:**
- Actively hunting for best deals
- Willing to wait for the right listing
- Budget-conscious buyers

**Example:**
```
CPU: Intel Core i7-12700K
Great Price: $650
Meaning: Only 25% of listings are priced below $650
```

#### Good Price (50th Percentile / Median)

**Definition:** The **middle price point** — half of listings cost more, half cost less.

**Meaning:** A fair market price — reasonable and achievable.

**When to Target:**
- Standard purchase without extended search
- Confident it's not overpriced
- Need the CPU soon

**Example:**
```
CPU: Intel Core i7-12700K
Good Price: $750
Meaning: Median market price — 50% of listings are above/below this
```

#### Fair Price (75th Percentile)

**Definition:** The price point below which **75% of listings** are sold.

**Meaning:** Acceptable but not optimal — you're paying more than 75% of buyers.

**When to Target:**
- Urgent need for the CPU
- Limited availability in market
- Specific listing has desirable extras (better RAM, warranty, etc.)

**Example:**
```
CPU: Intel Core i7-12700K
Fair Price: $850
Meaning: 75% of listings are priced below $850
```

### Confidence Levels

Price targets include a **confidence indicator** based on sample size:

| Badge | Sample Size | Reliability | Meaning |
|-------|-------------|-------------|---------|
| **High** | 10+ listings | Highly reliable | Strong statistical basis |
| **Medium** | 5-9 listings | Moderately reliable | Adequate sample |
| **Low** | 2-4 listings | Less reliable | Limited sample |
| **Insufficient** | < 2 listings | Not valid | Not enough data |

### How Price Targets Are Calculated

**Statistical Method:**

```
Sample: All active listings with the CPU
Metric: Adjusted Price (base price after valuation rules applied)

Great Price = Mean - (1 × Standard Deviation)
Good Price = Mean (Average adjusted price)
Fair Price = Mean + (1 × Standard Deviation)

Confidence =
  Sample ≥ 10 → High
  Sample ≥ 5 → Medium
  Sample ≥ 2 → Low
  Sample < 2 → Insufficient
```

**Example Calculation:**

```
CPU: AMD Ryzen 5 5600X
Active Listings: 12
Adjusted Prices: $550, $580, $590, $600, $620, $630, $640, $650, $670, $680, $700, $720

Mean (Good Price): $619
Standard Deviation: $52

Great Price: $619 - $52 = $567
Good Price: $619
Fair Price: $619 + $52 = $671

Confidence: High (12 listings)
```

### Interpreting Price Targets

**Scenario: You found a listing at $700 for CPU with targets:**
- Great Price: $650
- Good Price: $750
- Fair Price: $850
- Confidence: High

**Analysis:**
- Your listing ($700) is **between Great and Good**
- You're paying **less than the median** (Good = $750)
- **Strong buy signal** — good value

**Scenario: You found a listing at $900 for CPU with targets:**
- Great Price: $650
- Good Price: $750
- Fair Price: $850
- Confidence: High

**Analysis:**
- Your listing ($900) is **above Fair Price**
- You're paying **more than 75% of buyers**
- **Caution** — consider waiting for better price or verifying extras justify premium

### When to Ignore Price Targets

**"Insufficient Data" Badge:**
- Fewer than 2 active listings
- Price targets not statistically valid
- Manually check Listings page for this CPU

**Niche or Rare CPUs:**
- Server-grade processors (e.g., Xeon, EPYC)
- Older generation CPUs with low market activity
- Newly released CPUs without price history

**High Price Variance Warning:**
- Standard deviation > 30% of mean
- Indicates wide pricing spread
- Review individual listings to understand variance

[Screenshot placeholder: Price Targets component showing all three tiers with High confidence badge and sample size]

---

## Filtering and Sorting

### Filter Panel

The left sidebar (desktop) or drawer (mobile) provides comprehensive filtering options.

### Available Filters

#### Search Input

**Functionality:**
- Searches CPU name field
- Case-insensitive
- Partial matching supported
- Debounced (200ms) for smooth typing

**Example:**
- Search "i7" → Returns all Intel Core i7 CPUs
- Search "ryzen 7" → Returns all AMD Ryzen 7 CPUs

#### Manufacturer Filter

**Options:**
- All (default)
- Intel
- AMD

**Use Case:**
- Filter by CPU brand preference
- Compare Intel vs AMD options

#### Socket Filter

**Options (Multi-Select):**
- LGA1700 (Intel 12th/13th/14th gen)
- LGA1200 (Intel 10th/11th gen)
- AM5 (AMD Ryzen 7000 series)
- AM4 (AMD Ryzen 1000-5000 series)
- And more...

**Use Case:**
- Filter by motherboard compatibility
- Ensure CPU fits existing board

#### Cores Filter

**Type:** Range slider

**Range:** 2 cores - 64 cores

**Use Case:**
- Set minimum cores for workload requirements
- Gaming: 4-8 cores
- Workstation: 8-16+ cores

#### Release Year Filter

**Type:** Range slider or multi-select

**Range:** 2015 - 2024

**Use Case:**
- Focus on recent architectures
- Find legacy CPUs for older builds

#### TDP Filter

**Type:** Range slider

**Range:** 15W - 280W

**Use Case:**
- Match thermal constraints
- Mini-PC: 15W-65W
- Desktop: 65W-125W
- High-performance: 125W+

#### Minimum PassMark Filter

**Type:** Number input

**Use Case:**
- Set performance floor
- Exclude low-performance CPUs

#### Has iGPU Filter

**Options:**
- Any (default)
- Yes (CPUs with integrated graphics)
- No (CPUs without integrated graphics)

**Use Case:**
- Find CPUs that don't require discrete GPU
- Exclude CPUs with unused iGPU for value

#### Active Listings Only Toggle

**Default:** Enabled

**Functionality:**
- Shows only CPUs with at least 1 active listing
- Reduces initial dataset for faster loading
- Disable to see all CPUs in catalog

**Use Case:**
- Focus on CPUs you can actually purchase
- Hide legacy CPUs with no market availability

### Applying Filters

1. **Open Filter Panel** (if collapsed)
2. **Select Desired Criteria** (filters apply instantly)
3. **View Filtered Results** (count updates in real-time)
4. **Clear Individual Filters** (click X on filter chip)
5. **Clear All Filters** (click "Clear All" button)

### Filter Persistence

- **URL Synchronization**: Filters saved in URL query parameters
- **Shareable Links**: Copy URL to share filtered view
- **Session Persistence**: Filters remain across view mode changes
- **Browser Navigation**: Back/forward buttons work with filters

### Sorting

#### Available Sort Options

**In Data Table View:**

Click column headers to sort:
- **CPU Name** (A-Z or Z-A)
- **Cores** (Low to High or High to Low)
- **TDP** (Low to High or High to Low)
- **CPU Mark (Multi)** (Low to High or High to Low)
- **CPU Mark (Single)** (Low to High or High to Low)
- **$/Mark (Single)** (Low to High or High to Low)
- **$/Mark (Multi)** (Low to High or High to Low)
- **Target Price (Good)** (Low to High or High to Low)
- **Listings Count** (Low to High or High to Low)
- **Release Year** (Oldest First or Newest First)

**Sort Direction:**
- Click once: Ascending (↑)
- Click twice: Descending (↓)
- Click third time: Clear sort

**Multi-Column Sort:**
- Hold `Shift` and click additional column headers
- Primary sort + secondary sort + tertiary sort

**In Catalog Views (Grid, List, Master-Detail):**

CPUs are automatically sorted by **performance value** ($/MT Mark ascending by default — best value first).

### Example Filtering Workflow

**Goal: Find best gaming CPU under $800**

1. **Set Price Filter**: Max "Good Price" to $800
2. **Set Core Filter**: 6-12 cores (gaming sweet spot)
3. **Set TDP Filter**: 65W-125W (adequate gaming performance)
4. **Sort by**: $/Single-Thread Mark (ascending)
5. **Review Results**: Top results are best gaming value under budget

[Screenshot placeholder: Filter panel with active filters and result count]

---

## CPU Detail Modal

### Opening the Modal

**From Any View Mode:**
- **Grid View**: Click CPU card
- **List View**: Click CPU row
- **Master-Detail View**: Click "Detail" button or press Enter
- **Data Table**: Click CPU row

**Keyboard Shortcut:**
- `Enter` when CPU is focused

**Deep Linking:**
- URL format: `/cpus?detail={cpu_id}`
- Shareable link opens catalog with modal

### Modal Structure

The CPU Detail Modal provides comprehensive information organized into sections:

#### 1. Header

- **CPU Name** (large heading)
- **Manufacturer Badge** (Intel/AMD)
- **Close Button** (X icon, top-right)

#### 2. Performance Overview Section

**PassMark Benchmarks:**
- Multi-Thread Score (CPU Mark) with horizontal bar chart
- Single-Thread Rating with horizontal bar chart
- iGPU Mark (if integrated graphics present)
- Visual bars show relative performance compared to catalog average

**Performance Value Badges:**
- $/Single-Thread Mark rating (Excellent/Good/Fair/Poor)
- $/Multi-Thread Mark rating
- Percentile rank displayed

#### 3. Specifications Section

**Key Specifications (Two-Column Grid):**

| Field | Example Value |
|-------|---------------|
| **Cores / Threads** | 8 Cores / 16 Threads |
| **Base Clock** | 3.6 GHz |
| **Boost Clock** | 5.0 GHz |
| **Socket** | LGA1700 |
| **TDP** | 125W |
| **Release Year** | 2021 |
| **iGPU Model** | Intel UHD 770 |
| **PassMark Category** | High End CPUs |

#### 4. Pricing Analytics Section

**Price Targets Display:**

```
┌─────────────────────────────────────┐
│ Great Deal: $650                    │ ← 25th percentile
│ Good Price: $750                    │ ← Median (emphasized)
│ Fair Price: $850                    │ ← 75th percentile
│                                     │
│ Confidence: High (12 listings)     │ ← Badge + sample size
│ Last Updated: 2025-11-05            │ ← Timestamp
└─────────────────────────────────────┘
```

**Confidence Badge:**
- Color-coded: High (green), Medium (yellow), Low (orange), Insufficient (gray)
- Tooltip explains sample size and reliability

**Price History Chart (Future Enhancement):**
- Line chart showing price trends over time
- Coming soon

#### 5. Market Data Section

**Associated Listings:**
- **Total Count**: Number of active listings with this CPU
- **Top 5 Listings Preview**:
  - Listing title
  - Price (list and adjusted)
  - Condition (New, Refurbished, Used)
  - Marketplace (eBay, Amazon, etc.)
  - Link to listing detail page
- **"View All Listings" Button**: Navigates to Listings page filtered by this CPU

**Price Distribution Chart:**
- Histogram showing spread of listing prices
- Vertical markers for 25th, 50th, 75th percentiles
- X-axis: Price range
- Y-axis: Number of listings

#### 6. Additional Information Section

**PassMark Category:**
- Classification (e.g., "High End CPUs", "Mid Range CPUs")

**Notes Field:**
- Admin-entered notes about CPU (if any)

**Custom Attributes:**
- JSON-stored additional metadata
- Displayed as key-value pairs

#### 7. Footer

**Action Buttons:**
- **"View Listings"**: Navigate to Listings page filtered by CPU
- **"Edit CPU"** (admin only): Open CPU edit form
- **"Close"**: Close modal (or press ESC)

**External Links:**
- PassMark CPU Benchmark page (official benchmark data)
- CPU comparison tools (future)

### Modal Behavior

**Interaction:**
- Scrollable content (if exceeds viewport height)
- Focus trap (Tab key cycles within modal)
- ESC key closes modal
- Click outside modal (overlay) closes modal
- Animations: Smooth fade-in (200ms)

**Data Loading:**
- Basic CPU data loads immediately
- Associated listings load asynchronously (lazy)
- Loading spinner for async sections

**Accessibility:**
- Keyboard navigable (Tab, Shift+Tab, ESC)
- Screen reader announcements
- ARIA labels on all controls
- Focus restoration on close

[Screenshot placeholder: CPU Detail Modal showing all sections fully populated]

---

## Common Workflows

### Workflow 1: Finding Best Value CPU for Budget

**Goal:** Find the best gaming CPU under $800.

**Steps:**

1. **Navigate to CPU Catalog** (`/cpus`)

2. **Enable "Active Listings Only"** (if not already enabled)
   - Ensures you only see CPUs you can buy

3. **Apply Filters:**
   - **Price Target**: Set max "Good Price" to $800
   - **Cores**: 6-12 cores (gaming sweet spot)
   - **TDP**: 65W-125W (adequate performance, manageable cooling)

4. **Switch to Grid View** (best for visual comparison)

5. **Sort by Performance Value:**
   - Look for CPUs with "Excellent" or "Good" $/Single-Thread Mark badges
   - Single-thread performance matters most for gaming

6. **Review Top Results:**
   - Check PassMark Single-Thread scores (higher is better)
   - Compare price targets (look for "Great" or "Good" prices)
   - Check confidence badges (prefer "High" confidence)

7. **Open Detail Modal for Finalists:**
   - Click top 2-3 CPUs to view full details
   - Review price distribution charts
   - Check number of active listings (more listings = competitive pricing)

8. **Navigate to Listings:**
   - Click "View Listings" in modal
   - See actual available listings with this CPU
   - Compare complete PC builds

**Expected Outcome:**
- Identified 2-3 CPUs offering best gaming value under budget
- Understand market pricing for each CPU
- Ready to evaluate complete PC listings

---

### Workflow 2: Researching a Specific CPU Model

**Goal:** Learn everything about Intel Core i7-12700K before purchasing.

**Steps:**

1. **Search for CPU:**
   - Use search input: "i7-12700k"
   - Press Enter or wait for debounced results

2. **Open CPU Detail Modal:**
   - Click the CPU card/row

3. **Review Performance Metrics:**
   - Check PassMark Multi-Thread score (28,000+)
   - Check PassMark Single-Thread score (3,800+)
   - Note iGPU Mark (Intel UHD 770: ~1,850)
   - **Interpretation**: Strong single-thread (gaming), excellent multi-thread (productivity)

4. **Analyze Price Targets:**
   - Great Price: $650
   - Good Price: $750
   - Fair Price: $850
   - Confidence: High (12 listings)
   - **Interpretation**: Don't pay more than $750 for good value

5. **Check Performance Value:**
   - $/Single-Thread Mark: $0.20 (Good)
   - $/Multi-Thread Mark: $0.027 (Excellent)
   - Percentile: 32nd (better than 68% of CPUs)
   - **Interpretation**: Excellent multi-thread value, good single-thread value

6. **Review Specifications:**
   - 12 cores (8 P-cores + 4 E-cores) / 20 threads
   - Base: 3.6 GHz, Boost: 5.0 GHz
   - TDP: 125W (requires adequate cooling)
   - Socket: LGA1700 (requires 600-series motherboard)
   - Release: 2021 (modern architecture, DDR5 support)

7. **Examine Price Distribution:**
   - Histogram shows most listings $700-$800
   - Few listings below $650 (Great Price)
   - Median is $750 (Good Price)
   - **Interpretation**: Target $700-$750 range

8. **View Associated Listings:**
   - Check "Top 5 Listings" preview
   - Note conditions: New ($850), Refurbished ($750), Used ($680)
   - Click "View All Listings" for complete list

9. **External Research:**
   - Click "PassMark Benchmark Page" for official benchmark data
   - Compare against competing CPUs (Ryzen 7 5800X)

**Expected Outcome:**
- Complete understanding of CPU performance profile
- Data-driven price targets ($650-$750 range)
- Confidence in purchase decision
- Ready to identify specific PC listings

---

### Workflow 3: Comparing Multiple CPUs Side-by-Side

**Goal:** Compare Intel Core i5-12400 vs AMD Ryzen 5 5600X for gaming build.

**Steps:**

1. **Filter to Candidates:**
   - Search "i5-12400"
   - Note key specs and price targets
   - Clear search

2. **Switch to Master-Detail View:**
   - Best for sequential comparison workflow

3. **Review First CPU (i5-12400):**
   - Click CPU in master list
   - Detail panel shows full specs
   - **Note Key Metrics:**
     - Single-Thread: 3,200
     - Multi-Thread: 17,500
     - Good Price: $550
     - $/ST Mark: $0.17 (Good)
     - TDP: 65W (lower heat, lower power)

4. **Review Second CPU (Ryzen 5 5600X):**
   - Click next CPU in master list
   - Detail panel updates
   - **Note Key Metrics:**
     - Single-Thread: 3,500
     - Multi-Thread: 21,000
     - Good Price: $600
     - $/ST Mark: $0.17 (Good)
     - TDP: 65W

5. **Compare Head-to-Head:**

| Metric | i5-12400 | Ryzen 5 5600X | Winner |
|--------|----------|---------------|--------|
| Single-Thread | 3,200 | 3,500 | AMD (+9%) |
| Multi-Thread | 17,500 | 21,000 | AMD (+20%) |
| Good Price | $550 | $600 | Intel (-8%) |
| $/ST Mark | $0.17 | $0.17 | Tie |
| $/MT Mark | $0.031 | $0.029 | AMD (-6%) |
| TDP | 65W | 65W | Tie |
| iGPU | Intel UHD 730 | None | Intel |
| Socket | LGA1700 | AM4 | Intel (newer) |

6. **Decision Framework:**
   - **Choose i5-12400 if**:
     - Budget is tight ($550 vs $600)
     - Need integrated graphics (no discrete GPU initially)
     - Want newer platform (DDR5 upgrade path)
   - **Choose Ryzen 5 5600X if**:
     - Performance is priority (+20% multi-thread)
     - Gaming performance matters (+9% single-thread)
     - Have discrete GPU (no iGPU needed)

7. **Check Listings Availability:**
   - Click "View Listings" for both CPUs
   - Verify sufficient listings available
   - Compare complete PC configurations

**Expected Outcome:**
- Clear understanding of performance differences
- Data-driven decision based on priorities
- Confidence in CPU selection

---

### Workflow 4: Filtering CPUs for Mini-PC Build

**Goal:** Find best value CPU for passively-cooled Mini-PC (TDP ≤ 65W).

**Steps:**

1. **Apply TDP Filter:**
   - Set max TDP to 65W
   - Excludes high-power desktop CPUs

2. **Apply Performance Filter:**
   - Set min CPU Mark (Multi) to 10,000
   - Ensures adequate performance
   - Excludes ultra-low-power CPUs

3. **Enable "Active Listings Only":**
   - Focus on purchasable CPUs

4. **Sort by $/Multi-Thread Mark:**
   - Best value for productivity workloads

5. **Switch to Grid View:**
   - Visual comparison of compact CPUs

6. **Review Results:**
   - Look for "Excellent" or "Good" badges
   - Check for integrated graphics (important for Mini-PC)
   - Common candidates:
     - Intel Core i5 (T-series, 35W)
     - AMD Ryzen 5 (65W)
     - Intel Core i7 (T-series, 35W)

7. **Open Detail Modal for Top 3:**
   - Verify iGPU present
   - Check associated Mini-PC listings
   - Confirm TDP within cooling constraints

8. **Select Winner:**
   - Balance performance, value, and availability
   - Verify compatible with target Mini-PC form factors

**Expected Outcome:**
- CPU options compatible with Mini-PC thermal constraints
- Best performance-per-dollar within TDP limit
- Integrated graphics for compact builds

---

## Tips and Best Practices

### Finding Deals

**1. Look for "Excellent" Performance Value Badges**
- Green badges indicate top 25% price efficiency
- Multiple "Excellent" badges = strong all-around value

**2. Target "Great" or "Good" Prices with "High" Confidence**
- "Great" prices are statistically excellent deals
- "High" confidence (10+ listings) ensures reliable data

**3. Monitor CPUs with 5+ Active Listings**
- More listings = competitive pricing
- More options to choose from

**4. Consider Slightly Older Generations**
- Previous-gen CPUs often offer better value
- Example: 11th gen Intel vs 12th gen (small performance gap, large price difference)

**5. Check Release Year for Feature Trade-offs**
- Newer CPUs: DDR5, PCIe 5.0, better efficiency
- Older CPUs: Mature platform, cheaper motherboards

### Performance Considerations

**For Gaming Builds:**
- **Prioritize Single-Thread Performance**
  - Look for Single-Thread Rating ≥ 3,000
  - Target $/ST Mark badges ("Excellent" or "Good")
- **Core Count Sweet Spot**: 6-12 cores
- **TDP Consideration**: 65W-125W for adequate performance

**For Workstation Builds:**
- **Prioritize Multi-Thread Performance**
  - Look for CPU Mark (Multi) ≥ 20,000
  - Target $/MT Mark badges ("Excellent" or "Good")
- **Core Count**: 8-16+ cores (depending on workload)
- **TDP Consideration**: 125W+ for maximum performance

**For Balanced Builds:**
- Look for CPUs with both Single-Thread and Multi-Thread "Good" or better ratings
- Core Count: 8-12 cores
- TDP: 65W-95W (efficient yet capable)

**Integrated Graphics (iGPU):**
- Essential if not using discrete GPU
- Intel UHD 770 or AMD Radeon Graphics recommended
- iGPU Mark ≥ 1,500 for basic tasks

### Filtering Strategies

**Start Broad, Then Narrow:**

1. **Initial Filter**: Manufacturer (Intel or AMD)
2. **Add Budget**: Price target max
3. **Add Performance**: Min PassMark score
4. **Add Platform**: Socket or release year
5. **Refine**: TDP, cores, iGPU

**Save Time with Presets:**
- Use "Active Listings Only" by default
- Filter out CPUs you can't purchase
- Faster initial load

**Use URL Sharing:**
- Copy URL after applying filters
- Share with colleagues or revisit later
- Browser bookmarks save filtered views

### Understanding Market Insights

**"Insufficient Data" Interpretation:**
- < 2 listings: Not enough market activity
- Could indicate:
  - Niche/specialized CPU (server, workstation)
  - Legacy CPU with low demand
  - Newly released CPU (wait for more data)
- **Action**: Manually check Listings page for this CPU

**Wide Price Ranges:**
- Large gap between Great and Fair prices
- Indicates high price variance
- Possible reasons:
  - Condition differences (New vs Used)
  - Listing extras (better RAM, storage, warranty)
  - Marketplace differences (eBay vs Amazon)
- **Action**: Review individual listings to understand variance

**Low Confidence Warnings:**
- < 5 listings: Limited statistical reliability
- Treat price targets as estimates, not guarantees
- Cross-reference with external sources (PCPartPicker, eBay sold listings)

### Cross-Referencing with Listings

**From CPU Catalog to Listings:**

1. Click "View Listings" in CPU detail modal
2. Listings page opens pre-filtered by CPU
3. See complete PC builds with this CPU
4. Compare:
   - RAM configurations
   - Storage options
   - Form factors (Desktop, Mini-PC, Laptop)
   - Conditions (New, Refurbished, Used)
   - Total system value

**From Listings to CPU Catalog:**

1. On Listings page, click CPU name in listing
2. Opens CPU detail modal (future enhancement)
3. View CPU performance metrics in context of listing
4. Decide if listing price justified by CPU value

---

## Troubleshooting

### Issue: No CPUs Showing

**Possible Causes:**
- Filters too restrictive
- "Active Listings Only" enabled with no matching CPUs
- No CPUs in database

**Solutions:**
1. Click **"Clear All Filters"** button
2. Disable **"Active Listings Only"** toggle
3. Check price target max slider (drag to maximum)
4. Clear search input
5. Verify CPUs exist in **Data Tab**

---

### Issue: Price Targets Show "Insufficient Data"

**Cause:**
- Fewer than 2 active listings with this CPU

**Solutions:**
1. **Manually Check Listings**: Click "View Listings" to see if any listings exist
2. **Check Data Tab**: Verify "Listings Count" column shows > 0
3. **Wait for Market Activity**: Newly added CPUs may not have listings yet
4. **Use External Sources**: Cross-reference with PCPartPicker or eBay sold listings

---

### Issue: Performance Value Shows "No Data"

**Cause:**
- CPU benchmarks not available
- Price targets insufficient

**Solutions:**
1. **Check PassMark Scores**: Open detail modal and verify Single-Thread and Multi-Thread scores exist
2. **Import Benchmark Data** (admin):
   ```bash
   poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv
   ```
3. **Recalculate Metrics** (admin):
   ```bash
   poetry run python scripts/recalculate_all_metrics.py
   ```

---

### Issue: Filters Not Working in List or Master-Detail Views

**Cause:**
- Bug in filter synchronization across view modes (known issue, being addressed)

**Solutions:**
1. **Switch to Grid View**: Filters work reliably in Grid View
2. **Apply Filters First**: Set all filters, then switch view modes
3. **Refresh Page**: Reload page and reapply filters
4. **Report Issue**: Contact development team if problem persists

---

### Issue: CPU Detail Modal Not Opening

**Possible Causes:**
- JavaScript error in browser console
- Slow network connection
- Missing CPU data

**Solutions:**
1. **Check Browser Console**: Open DevTools (F12) and check for errors
2. **Refresh Page**: Reload the CPU Catalog page
3. **Try Different CPU**: Click a different CPU to verify modal functionality
4. **Clear Browser Cache**: Clear cache and reload
5. **Try Different Browser**: Test in Chrome, Firefox, or Edge

---

### Issue: Performance is Slow (Grid View)

**Possible Causes:**
- Too many CPUs rendered (100+ cards)
- Old/slow device
- Other browser tabs consuming resources

**Solutions:**
1. **Apply Filters**: Reduce visible CPUs to < 50
2. **Enable "Active Listings Only"**: Reduces dataset significantly
3. **Switch to List View**: More performant than Grid View for large datasets
4. **Close Other Tabs**: Free up browser resources
5. **Use Data Tab**: Table view is fastest for large datasets

---

### Issue: Price Targets Not Updating After New Listings

**Cause:**
- Background task hasn't run yet
- Cache not invalidated

**Solutions:**
1. **Wait for Nightly Recalculation**: Price targets refresh automatically overnight
2. **Manual Recalculation** (admin):
   ```bash
   poetry run python scripts/recalculate_all_metrics.py
   ```
3. **Clear Cache**: Refresh page with hard reload (Ctrl+Shift+R)

---

### Issue: Keyboard Shortcuts Not Working (Master-Detail View)

**Cause:**
- Focus not on master list
- Conflicting browser extensions
- Keyboard shortcuts disabled

**Solutions:**
1. **Click Master List**: Click inside the master list to set focus
2. **Disable Browser Extensions**: Temporarily disable extensions (especially Vim-like extensions)
3. **Check Browser Settings**: Verify keyboard shortcuts not remapped
4. **Use Mouse**: Fallback to mouse/touch interaction

---

### Issue: Can't Find CPU I'm Looking For

**Possible Causes:**
- CPU not in database
- Search query typo
- CPU name variation

**Solutions:**
1. **Try Alternative Names**:
   - "i7-12700k" vs "i7 12700k" vs "Core i7-12700K"
   - "Ryzen 5 5600X" vs "5600X" vs "R5 5600X"
2. **Check Data Tab**: Browse full table without filters
3. **Disable Filters**: Clear all filters and search again
4. **Request Addition** (admin): Submit CPU to be added to catalog

---

## Glossary

### CPU Terms

**CPU (Central Processing Unit)**
- The main processor in a computer that executes instructions.

**Cores**
- Independent processing units within a CPU. More cores enable better multitasking and parallel workloads.

**Threads**
- Virtual cores created by hyperthreading/SMT. Allows one physical core to handle two instruction streams.

**TDP (Thermal Design Power)**
- Maximum heat output in watts. Higher TDP = more performance but requires better cooling.

**Socket**
- Physical interface between CPU and motherboard. Must match for compatibility (e.g., LGA1700, AM5).

**Base Clock**
- Guaranteed minimum frequency the CPU runs at under load.

**Boost Clock**
- Maximum frequency the CPU can reach under optimal conditions (adequate cooling, power).

**iGPU (Integrated Graphics Processing Unit)**
- Graphics processor built into the CPU. Enables video output without discrete GPU.

---

### Performance Terms

**PassMark**
- Industry-standard CPU benchmark suite measuring performance.

**CPU Mark (Multi-Thread)**
- PassMark overall performance score. Measures all cores working together.

**Single-Thread Rating**
- PassMark single-core performance score. Measures responsiveness and single-threaded tasks.

**iGPU Mark (G3D Score)**
- PassMark 3D graphics benchmark score for integrated graphics.

**Percentile Rank**
- Statistical ranking showing where a CPU falls relative to all CPUs (0-100). Lower percentile = better value.

---

### Pricing Terms

**List Price**
- Original asking price for a PC listing before adjustments.

**Adjusted Price**
- Price after valuation rules applied (deductions for RAM, storage, condition, etc.).

**Target Price**
- Statistical benchmark showing expected market price for a CPU.

**Great Price (25th Percentile)**
- Excellent deal — 75% of listings cost more.

**Good Price (Median / 50th Percentile)**
- Fair market price — half of listings cost more, half cost less.

**Fair Price (75th Percentile)**
- Acceptable price — 75% of listings cost less.

**Confidence Level**
- Reliability indicator for price targets based on sample size (High/Medium/Low/Insufficient).

---

### Performance Value Terms

**$/PassMark**
- Price efficiency metric: dollars paid per PassMark benchmark point.

**$/Single-Thread Mark ($/ST Mark)**
- Cost per single-thread PassMark point. Lower = better value for gaming/responsiveness.

**$/Multi-Thread Mark ($/MT Mark)**
- Cost per multi-thread PassMark point. Lower = better value for productivity/workstation.

**Performance Value Rating**
- Quality indicator: Excellent (top 25%), Good (26-50%), Fair (51-75%), Poor (76-100%).

---

### Statistical Terms

**Mean (Average)**
- Sum of all values divided by count. Used for "Good Price" calculation.

**Standard Deviation (StdDev)**
- Measure of data spread. Used to calculate "Great" and "Fair" prices.

**Sample Size**
- Number of listings used for statistical calculations.

**Median**
- Middle value when data sorted. 50% of values above, 50% below.

**Variance**
- Measure of data spread. High variance = wide price range.

---

## Related Resources

### Documentation

- **Performance Metrics Guide**: `/docs/user-guide/performance-metrics.md`
  - Deep dive into CPU Mark metrics and calculations
- **Catalog Views Guide**: `/docs/user-guide/catalog-views.md`
  - Detailed guide to Grid, List, and Master-Detail views
- **Listings User Guide**: `/docs/user-guide/guides/listings-workspace-notes.md`
  - How to browse and evaluate PC listings
- **API Documentation**: `/docs` (when server running)
  - Developer reference for CPU endpoints

### External Resources

- **PassMark CPU Benchmarks**: https://www.cpubenchmark.net/
  - Official CPU benchmark database and rankings
- **PCPartPicker**: https://pcpartpicker.com/
  - Community pricing data and system builds
- **CPU-World**: https://www.cpu-world.com/
  - Detailed CPU specifications and comparisons

### Project Plans

- **PRD**: `docs/project_plans/cpu-page-reskin/PRD.md`
  - Complete product requirements document
- **Implementation Plan**: `docs/project_plans/cpu-page-reskin/IMPLEMENTATION_PLAN.md`
  - Technical implementation details

---

## Feedback and Support

### Questions or Issues?

If you encounter problems or have questions about the CPU Catalog:

1. **Check This Guide First**: Search this document for your issue
2. **Review Troubleshooting Section**: Common problems and solutions
3. **Contact Development Team**: Submit feedback or bug reports
4. **File GitHub Issue**: For feature requests or bugs

### Feature Requests

Have ideas for improving the CPU Catalog?

- Submit feature requests via GitHub Issues
- Tag with `enhancement` and `cpu-catalog`
- Provide use case and expected behavior

---

**Version:** 1.0
**Last Updated:** 2025-11-06
**Phase:** CPU Page Reskin - Phase 4 Documentation
**Maintainer:** Deal Brain Development Team
