# Single URL Import Component - Visual Mockups
**Design Reference for Task ID-022**
**Created**: 2025-10-19

---

## State-by-State Visual Mockups

### 1. Idle State (Initial Load)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL                                        ┃
┃ Paste a listing URL from eBay, Amazon, or any retailer┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┃  Listing URL *                                         ┃
┃  ┌──────────────────────────────────────────────────┐ ┃
┃  │ https://www.ebay.com/itm/...                 [i]│ ┃
┃  └──────────────────────────────────────────────────┘ ┃
┃  ⓘ Supports eBay, Amazon, and most retail websites    ┃
┃                                                        ┃
┃  Priority (optional)                                   ┃
┃  ┌──────────────────────────────────────────────────┐ ┃
┃  │ Standard                                      ▼ │ ┃
┃  └──────────────────────────────────────────────────┘ ┃
┃                                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                  [Reset] [Import Listing]┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Colors:
- Card: white (#FFFFFF) with subtle shadow
- Border: gray-200 (#E5E7EB)
- Title: gray-900 (#111827), 24px, semibold
- Description: gray-500 (#6B7280), 14px
- Input border: gray-300 (#D1D5DB)
- Input focus: primary blue (#3B82F6) with 2px ring
- Button (Reset): outline, gray-700 text
- Button (Import): primary blue bg, white text
```

---

### 2. Validating State (After Blur)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL                                        ┃
┃ Paste a listing URL from eBay, Amazon, or any retailer┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┃  Listing URL *                                         ┃
┃  ┌──────────────────────────────────────────────────┐ ┃
┃  │ https://www.ebay.com/itm/12345678901        [✓]│ ┃
┃  └──────────────────────────────────────────────────┘ ┃
┃                                                        ┃
┃  ┌────────────────────────────────────────────────────┐┃
┃  │ ⚡ Validating URL...                              │┃
┃  └────────────────────────────────────────────────────┘┃
┃                                                        ┃
┃  Priority (optional)                                   ┃
┃  ┌──────────────────────────────────────────────────┐ ┃
┃  │ Standard                                      ▼ │ ┃
┃  └──────────────────────────────────────────────────┘ ┃
┃                                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                  [Reset] [Import Listing]┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Animation:
- Spinner icon rotates 360deg (0.75s duration, linear)
- Alert fades in from top (0.2s ease-out)
- Checkmark icon pulses once on validation success

Colors:
- Validation alert: blue-50 bg (#EFF6FF), blue-700 text (#1D4ED8)
- Checkmark: green-500 (#10B981)
```

---

### 3. Submitting State (Creating Job)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL                                        ┃
┃ Paste a listing URL from eBay, Amazon, or any retailer┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┃  Listing URL *                                         ┃
┃  ┌──────────────────────────────────────────────────┐ ┃
┃  │ https://www.ebay.com/itm/12345678901             │ ┃ (disabled)
┃  └──────────────────────────────────────────────────┘ ┃
┃                                                        ┃
┃  Priority (optional)                                   ┃
┃  ┌──────────────────────────────────────────────────┐ ┃
┃  │ Standard                                      ▼ │ ┃ (disabled)
┃  └──────────────────────────────────────────────────┘ ┃
┃                                                        ┃
┃  ┌────────────────────────────────────────────────────┐┃
┃  │ ⚡ Creating import job...                         │┃
┃  │                                                    │┃
┃  │ This usually takes a few seconds                  │┃
┃  └────────────────────────────────────────────────────┘┃
┃                                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                         (buttons hidden)┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

UI Changes:
- Form fields disabled (opacity 0.5)
- Submit button hidden
- Alert box takes visual focus
```

---

### 4. Polling State - Queued (Job Queued)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL                                        ┃
┃ Paste a listing URL from eBay, Amazon, or any retailer┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┃  ┌────────────────────────────────────────────────────┐┃
┃  │ ⚙  Importing listing...                  [3s] │┃
┃  │                                                    │┃
┃  │ ▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 15%   │┃
┃  │                                                    │┃
┃  │ Job queued, waiting for worker...                 │┃
┃  └────────────────────────────────────────────────────┘┃
┃                                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                            [Cancel Import]┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Colors:
- Alert: blue-50 bg, blue-700 text
- Progress bar bg: gray-200
- Progress bar fill: blue-500 with pulse animation
- Elapsed badge: gray-100 bg, gray-700 text
- Cancel button: destructive outline (red-600 text)

Progress Calculation:
- Queued: 15% (base)
- Running (0-5s): 15-50% (linear)
- Running (5-10s): 50-85% (slower)
- Running (>10s): 85-95% (very slow, asymptotic)
```

---

### 5. Polling State - Running (Extracting Data)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL                                        ┃
┃ Paste a listing URL from eBay, Amazon, or any retailer┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┃  ┌────────────────────────────────────────────────────┐┃
┃  │ ⚙  Importing listing...                  [7s] │┃
┃  │                                                    │┃
┃  │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░ 62%   │┃
┃  │                                                    │┃
┃  │ Extracting data from marketplace...               │┃
┃  └────────────────────────────────────────────────────┘┃
┃                                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                            [Cancel Import]┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Animation:
- Progress bar fill animates left-to-right (shimmer effect)
- Gear icon rotates continuously
- Status message fades between states (0.3s cross-fade)
```

---

### 6. Success State (Complete with Full Data)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL                                        ┃
┃ Paste a listing URL from eBay, Amazon, or any retailer┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┃  ┌────────────────────────────────────────────────────┐┃
┃  │ ✓  Listing imported successfully!                 │┃
┃  │                                                    │┃
┃  │  ┌──────────────────────────────────────────────┐ │┃
┃  │  │ Dell OptiPlex 7070 Micro i5-9500T 16GB     #42│ │┃
┃  │  │                                                │ │┃
┃  │  │ 🗄 EBAY API   ✓ Full data          Just now  │ │┃
┃  │  └──────────────────────────────────────────────┘ │┃
┃  │                                                    │┃
┃  │  [🔗 View Listing]  [Import Another]              │┃
┃  └────────────────────────────────────────────────────┘┃
┃                                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Colors:
- Alert: green-50 bg (#F0FDF4), green-700 text (#15803D)
- Alert border: green-200 (#BBF7D0)
- Checkmark icon: green-500 (#10B981)
- Preview card: white bg with gray-200 border
- Title: gray-900, 14px, medium weight
- Listing ID badge: gray-100 bg, gray-700 text
- Provenance badge: blue-100 bg, blue-700 text, blue-200 border
- Quality badge (full): green-100 bg, green-700 text, green-200 border
- Timestamp: gray-500, 12px
- View button: outline style
- Import Another: primary blue fill

Animation:
- Success alert slides in from top (0.4s ease-out)
- Checkmark icon scales in with bounce (0.5s spring)
- Preview card fades in (0.3s ease-in, 0.1s delay)
```

---

### 7. Success State (Partial Data Quality)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL                                        ┃
┃ Paste a listing URL from eBay, Amazon, or any retailer┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┃  ┌────────────────────────────────────────────────────┐┃
┃  │ ✓  Listing imported successfully!                 │┃
┃  │                                                    │┃
┃  │  ┌──────────────────────────────────────────────┐ │┃
┃  │  │ HP EliteDesk 800 G5 Mini PC              #43│ │┃
┃  │  │                                                │ │┃
┃  │  │ 🔍 JSON-LD   ⚠ Partial data       Just now  │ │┃
┃  │  └──────────────────────────────────────────────┘ │┃
┃  │                                                    │┃
┃  │  ⓘ Some details may be missing. You can edit the │┃
┃  │     listing to add CPU, RAM, or storage info.     │┃
┃  │                                                    │┃
┃  │  [🔗 View Listing]  [Import Another]              │┃
┃  └────────────────────────────────────────────────────┘┃
┃                                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Colors:
- Quality badge (partial): amber-100 bg, amber-700 text, amber-200 border
- Warning icon: amber-500
- Info message: blue-50 bg, blue-700 text, blue-200 border
- Provenance badge (JSON-LD): purple-100 bg, purple-700 text

Tooltip on hover over "Partial data":
┌────────────────────────────────────┐
│ Partial Quality Explanation        │
├────────────────────────────────────┤
│ We were able to extract:           │
│ ✓ Title, price, seller             │
│ ✗ CPU model                        │
│ ✗ RAM capacity                     │
│ ✗ Storage details                  │
│                                    │
│ Edit the listing to complete.     │
└────────────────────────────────────┘
```

---

### 8. Error State (Timeout)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL                                        ┃
┃ Paste a listing URL from eBay, Amazon, or any retailer┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┃  ┌────────────────────────────────────────────────────┐┃
┃  │ ✕  Import failed                                  │┃
┃  │                                                    │┃
┃  │ Import timed out. The marketplace may be slow to  │┃
┃  │ respond or temporarily unavailable.               │┃
┃  │                                                    │┃
┃  │ ▼ Show technical details                          │┃
┃  │                                                    │┃
┃  │ [🔄 Try Again]                                     │┃
┃  └────────────────────────────────────────────────────┘┃
┃                                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                  [Reset] [Import Listing]┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Colors:
- Alert: red-50 bg (#FEF2F2), red-700 text (#B91C1C)
- Alert border: red-200 (#FECACA)
- Error icon: red-500 (#EF4444)
- Details disclosure: red-700 text with underline on hover
- Retry button: outline style, red-600 border

Expanded error details:
┃  │ ▲ Hide technical details                          │┃
┃  │ ┌────────────────────────────────────────────────┐│┃
┃  │ │ {                                              ││┃
┃  │ │   "error_code": "TIMEOUT",                     ││┃
┃  │ │   "adapter": "ebay_api",                       ││┃
┃  │ │   "timeout_seconds": 6,                        ││┃
┃  │ │   "url": "https://ebay.com/itm/12345"          ││┃
┃  │ │ }                                              ││┃
┃  │ └────────────────────────────────────────────────┘│┃
```

---

### 9. Error State (Invalid Schema)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL                                        ┃
┃ Paste a listing URL from eBay, Amazon, or any retailer┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┃  ┌────────────────────────────────────────────────────┐┃
┃  │ ✕  Import failed                                  │┃
┃  │                                                    │┃
┃  │ Could not extract listing data. The page format   │┃
┃  │ may not be supported yet.                         │┃
┃  │                                                    │┃
┃  │ Supported marketplaces:                           │┃
┃  │ • eBay (fully supported)                          │┃
┃  │ • Amazon (coming soon)                            │┃
┃  │ • Most retailers with structured data             │┃
┃  │                                                    │┃
┃  │ [📧 Report This URL]  [Try Different URL]         │┃
┃  └────────────────────────────────────────────────────┘┃
┃                                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                  [Reset] [Import Listing]┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Additional UI:
- Report button opens pre-filled email/form
- Try Different URL resets form and focuses input
```

---

### 10. Error State (Item Not Found)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL                                        ┃
┃ Paste a listing URL from eBay, Amazon, or any retailer┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┃  ┌────────────────────────────────────────────────────┐┃
┃  │ ✕  Import failed                                  │┃
┃  │                                                    │┃
┃  │ Listing not found. The URL may be invalid or the  │┃
┃  │ item may have been removed from the marketplace.  │┃
┃  │                                                    │┃
┃  │ Please check:                                      │┃
┃  │ • URL is copied correctly                         │┃
┃  │ • Item is still available on marketplace          │┃
┃  │ • You have access to view the listing             │┃
┃  │                                                    │┃
┃  │ [🔄 Try Again]                                     │┃
┃  └────────────────────────────────────────────────────┘┃
┃                                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                  [Reset] [Import Listing]┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## Component Interactions

### Priority Select (Expanded)

```
┃  Priority (optional)                                   ┃
┃  ┌──────────────────────────────────────────────────┐ ┃
┃  │ Standard                                      ▲ │ ┃ [Open]
┃  └──────────────────────────────────────────────────┘ ┃
┃  ┌──────────────────────────────────────────────────┐ ┃
┃  │ ✓ High - Process immediately                     │ ┃ [Hover bg: blue-50]
┃  ├──────────────────────────────────────────────────┤ ┃
┃  │ ● Standard - Normal queue                        │ ┃ [Selected]
┃  ├──────────────────────────────────────────────────┤ ┃
┃  │   Low - Background processing                    │ ┃
┃  └──────────────────────────────────────────────────┘ ┃
```

### URL Input Validation (Real-time)

**Valid URL:**
```
┃  ┌──────────────────────────────────────────────────┐ ┃
┃  │ https://www.ebay.com/itm/12345              [✓]│ ┃ [Green checkmark]
┃  └──────────────────────────────────────────────────┘ ┃
```

**Invalid URL:**
```
┃  ┌──────────────────────────────────────────────────┐ ┃
┃  │ not-a-valid-url                              [✕]│ ┃ [Red X, red border]
┃  └──────────────────────────────────────────────────┘ ┃
┃  ⚠ Please enter a valid URL starting with http:// or https://
```

**Empty (after blur):**
```
┃  ┌──────────────────────────────────────────────────┐ ┃
┃  │                                              [!]│ ┃ [Red border]
┃  └──────────────────────────────────────────────────┘ ┃
┃  ⚠ Please enter a listing URL
```

---

## Mobile Responsive Layout (< 640px)

### Success State Mobile

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL             ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                             ┃
┃ ┌───────────────────────────┐┃
┃ │ ✓ Listing imported!      │┃
┃ │                           │┃
┃ │ ┌─────────────────────┐   │┃
┃ │ │ Dell OptiPlex       │   │┃
┃ │ │ 7070 Micro i5       │   │┃
┃ │ │                     │   │┃
┃ │ │ 🗄 EBAY  ✓ Full   │   │┃
┃ │ │                     │   │┃
┃ │ │ Just now       #42  │   │┃
┃ │ └─────────────────────┘   │┃
┃ │                           │┃
┃ │ [View Listing]            │┃ [Full width]
┃ │ [Import Another]          │┃ [Full width]
┃ └───────────────────────────┘┃
┃                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Changes for mobile:
- Single column layout
- Buttons stack vertically (full width)
- Reduced padding (12px instead of 24px)
- Smaller font sizes (title: 20px, body: 13px)
- Compact badges and icons
- Progress bar height: 4px (vs 6px desktop)
```

---

## Dark Mode Variant

### Success State (Dark Mode)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Import from URL                                        ┃ [gray-50 text]
┃ Paste a listing URL from eBay, Amazon, or any retailer┃ [gray-400 text]
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                        ┃
┃  ┌────────────────────────────────────────────────────┐┃ [green-900/20 bg]
┃  │ ✓  Listing imported successfully!                 │┃ [green-400 text]
┃  │                                                    │┃
┃  │  ┌──────────────────────────────────────────────┐ │┃ [gray-800 bg]
┃  │  │ Dell OptiPlex 7070 Micro i5-9500T 16GB     #42│ │┃ [gray-100 text]
┃  │  │                                                │ │┃
┃  │  │ 🗄 EBAY API   ✓ Full data          Just now  │ │┃ [gray-300 text]
┃  │  └──────────────────────────────────────────────┘ │┃
┃  │                                                    │┃
┃  │  [🔗 View Listing]  [Import Another]              │┃
┃  └────────────────────────────────────────────────────┘┃
┃                                                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Dark Mode Colors:
- Card bg: gray-900 (#111827)
- Border: gray-700 (#374151)
- Success alert: green-900/20 bg, green-400 text
- Preview card: gray-800 bg, gray-700 border
- Badges: darker backgrounds, lighter text
- Input bg: gray-800, border: gray-600
- Focus ring: blue-400 (more vibrant)
```

---

## Animation Specifications

### 1. Form Submission Flow

```
Frame 1 (0ms):     Idle state, button enabled
                   ↓
Frame 2 (100ms):   Button disabled, opacity 0.7
                   ↓
Frame 3 (200ms):   Status alert fades in from top (translateY: -10px → 0)
                   ↓
Frame 4 (500ms):   Spinner starts rotating
                   ↓
Frame 5 (2000ms):  Progress bar animates to 15%
                   ↓
Frame 6 (4000ms):  Progress bar at 45%, message changes
```

### 2. Success Animation

```
Frame 1 (0ms):     Polling state visible
                   ↓
Frame 2 (100ms):   Polling alert fades out (opacity: 1 → 0)
                   ↓
Frame 3 (200ms):   Success alert slides in from top
                   translateY: -20px → 0, opacity: 0 → 1
                   ↓
Frame 4 (300ms):   Checkmark icon scales in
                   scale: 0 → 1.2 → 1 (bounce easing)
                   ↓
Frame 5 (400ms):   Preview card fades in
                   opacity: 0 → 1
                   ↓
Frame 6 (500ms):   Buttons fade in
                   opacity: 0 → 1
```

### 3. Progress Bar Shimmer

```css
@keyframes shimmer {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
}

.progress-bar {
  background: linear-gradient(
    90deg,
    hsl(var(--primary)) 0%,
    hsl(var(--primary) / 0.8) 50%,
    hsl(var(--primary)) 100%
  );
  background-size: 200px 100%;
  animation: shimmer 2s infinite linear;
}
```

### 4. Spinner Rotation

```css
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.spinner {
  animation: spin 0.75s linear infinite;
}
```

---

## Micro-interactions

### Button Hover States

```
[Import Listing] - Default
bg: hsl(var(--primary))
text: white
shadow: sm

[Import Listing] - Hover
bg: hsl(var(--primary) / 0.9)
shadow: md
transform: translateY(-1px)
transition: all 0.2s ease

[Import Listing] - Active
bg: hsl(var(--primary) / 0.95)
shadow: sm
transform: translateY(0)
```

### Input Focus State

```
Input - Default
border: 1px solid hsl(var(--input))

Input - Focus
border: 1px solid hsl(var(--ring))
ring: 2px solid hsl(var(--ring) / 0.2)
ring-offset: 2px
transition: all 0.15s ease
```

### Badge Hover (Provenance/Quality)

```
Badge - Default
cursor: pointer

Badge - Hover
opacity: 0.8
transform: scale(1.05)
transition: all 0.15s ease

Badge - Tooltip appears after 500ms hover
```

---

## Typography Scale

```
Card Title:          24px / 1.2em / 600 weight / tracking-tight
Card Description:    14px / 1.5em / 400 weight / text-muted-foreground
Form Label:          14px / 1.4em / 500 weight / text-foreground
Input Text:          16px / 1.5em / 400 weight / text-foreground
Input Placeholder:   16px / 1.5em / 400 weight / text-muted-foreground
Error Message:       13px / 1.4em / 400 weight / text-destructive
Alert Title:         16px / 1.4em / 600 weight
Alert Description:   14px / 1.5em / 400 weight
Preview Title:       14px / 1.4em / 500 weight
Metadata Text:       12px / 1.4em / 400 weight / text-muted-foreground
Badge Text:          12px / 1.3em / 500 weight
Button Text:         14px / 1.4em / 500 weight
```

---

## Spacing System (8px Grid)

```
Card Padding:           24px (3 units)
Card Header Spacing:    24px (3 units)
Form Field Spacing:     16px (2 units)
Label-Input Gap:        8px (1 unit)
Alert Padding:          16px (2 units)
Alert Icon-Text Gap:    12px (1.5 units)
Preview Card Padding:   12px (1.5 units)
Button Gap:             8px (1 unit)
Badge Gap:              8px (1 unit)
Footer Padding:         16px (2 units)
```

---

## Accessibility Testing Checklist

- [ ] All interactive elements have visible focus indicators
- [ ] Color contrast meets WCAG AA (4.5:1 for normal text)
- [ ] Form errors announced to screen readers
- [ ] Status changes announced via aria-live regions
- [ ] All images/icons have alt text or aria-labels
- [ ] Keyboard navigation follows logical order
- [ ] No keyboard traps
- [ ] Skip links provided if in larger context
- [ ] Form labels properly associated with inputs
- [ ] Required fields marked with aria-required
- [ ] Error messages linked via aria-describedby

---

## File Locations (Absolute Paths)

- Design Document: `/mnt/containers/deal-brain/docs/design/single-url-import-design.md`
- Visual Mockups: `/mnt/containers/deal-brain/docs/design/single-url-import-mockups.md`
- Implementation: `/mnt/containers/deal-brain/apps/web/components/ingestion/single-url-import-form.tsx`

---

**Design Status**: Complete
**Ready for Implementation**: Yes
**Estimated Development Time**: 20 hours
