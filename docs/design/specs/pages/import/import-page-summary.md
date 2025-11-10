# Import Page Design - Quick Reference

## Overview

User-friendly interface for TWO import methods with clear visual separation and contextual guidance.

**Location:** `/mnt/containers/deal-brain/apps/web/app/(dashboard)/import/page.tsx`

---

## Design Approach: Tab-Based Navigation

### Why Tabs?
- Clear separation without overwhelming users
- Maintains focus on one workflow at a time
- Accessible by default (keyboard navigation)
- Familiar pattern for related but distinct tasks
- Saves vertical space

### Alternatives Rejected
- **Cards:** Too much vertical scrolling
- **Accordion:** Implies hierarchy (these are equal)
- **Separate Pages:** Unnecessary navigation overhead

---

## Page Structure

```
Import Data Page
│
├─ Header
│  ├─ "Import Data" (H1)
│  └─ "Add individual listings from marketplace URLs..."
│
├─ Tabs (URL Import | File Import)
│
└─ Tab Content
   ├─ URL Import Tab
   │  ├─ Method Description Card
   │  ├─ Single URL Form
   │  └─ Bulk Import CTA
   │
   └─ File Import Tab
      ├─ Method Description Card
      └─ Importer Workspace
```

---

## Method 1: URL Import

### Purpose
Import individual PC listings from online marketplaces

### Components
1. **Method Description Card**
   - Icon: Link icon in primary/10% background circle
   - Title: "Import from Marketplace URLs"
   - Description: Auto extraction explanation
   - Best For: Individual imports, monitoring, quick entry
   - Supports: eBay, Amazon, Mercari, retailers

2. **Single URL Import Form** (existing component)
   - URL input field
   - Priority selector (High/Normal)
   - Status display with polling
   - Success/error handling

3. **Bulk Import CTA Card**
   - Dashed border (vs solid)
   - Heading: "Need to import multiple URLs?"
   - Button: Opens BulkImportDialog
   - Supports: Up to 1000 URLs via CSV or paste

---

## Method 2: File Import

### Purpose
Batch import from Excel/CSV workbooks with multiple entities

### Components
1. **Method Description Card**
   - Icon: Upload icon in primary/10% background circle
   - Title: "Import from Spreadsheet Files"
   - Description: Batch processing explanation
   - Best For: Large datasets, catalogs, rules, setup
   - Supports: .xlsx, .xls, .csv files
   - **How It Works:** 4-step workflow
     1. Upload your spreadsheet file
     2. Review and adjust column mappings
     3. Resolve any data conflicts
     4. Commit the import

2. **Importer Workspace** (existing component)
   - Upload dropzone
   - Field mapping editor
   - Preview tables
   - Conflict resolution
   - Commit workflow

---

## Key Design Elements

### Tab Navigation
- 2-column grid, max-width 400px
- Icons (16px) + labels
- Active state: white background with shadow
- Keyboard: Arrow keys to switch, Enter/Space to activate

### Method Description Cards
- **Border:** 2px solid (prominent)
- **Icon Container:** 40px circle, primary/10% background
- **Grid:** 2 columns on desktop, 1 on mobile
- **Typography:**
  - Title: 20px semibold
  - Description: 16px, relaxed line-height
  - Section Headers: 14px uppercase
  - Body: 14px

### Visual Markers
- **Bullets:** 6px primary circles
- **Numbers:** 20px muted circles with centered text

---

## Copy Highlights

### URL Import
- **Title:** "Import from Marketplace URLs"
- **Description:** "Extract listing data from eBay, Amazon, Mercari, and other online marketplaces. Our parser automatically identifies PC components, pricing, and specifications."
- **CTA:** "Bulk Import URLs"

### File Import
- **Title:** "Import from Spreadsheet Files"
- **Description:** "Upload Excel or CSV workbooks containing multiple listings, component catalogs, valuation rules, and scoring profiles. Review field mappings, resolve conflicts, and commit in one batch."

---

## Accessibility Features

### Keyboard Navigation
- Tab order: Header → Tabs → Content → Actions
- Arrow Left/Right: Switch tabs
- Enter/Space: Activate tab
- All forms: Native browser Tab support

### Screen Reader
- Proper heading hierarchy (H1 → H2 → H3)
- ARIA labels via Radix UI
- Live regions for status updates
- Descriptive link text

### Visual
- WCAG AA contrast ratios
- 2px focus rings
- 44x44px touch targets (mobile)
- No color-only meaning

---

## Responsive Behavior

### Mobile (< 768px)
- Single column layouts
- Stacked bulk CTA
- Full-width tabs
- 16px horizontal padding

### Tablet (768px - 1024px)
- 2-column method card grids
- Horizontal tabs
- Optimized touch targets

### Desktop (> 1024px)
- Max-width 1280px
- Full 2-column grids
- Generous whitespace

---

## Colors & Spacing

### Colors
- **Primary:** Brand blue for active states
- **Muted:** Secondary text and backgrounds
- **Border:** Light gray (2px for prominence)

### Spacing (8px grid)
- Page sections: 24px
- Card padding: 24px
- List items: 6px
- Icon gaps: 8px

---

## Component Dependencies

### shadcn/ui Components
- `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`
- `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`
- `Button`
- `Dialog` (via BulkImportDialog)

### Lucide Icons
- `Globe` (URL tab)
- `FileSpreadsheet` (File tab)
- `Link` (URL method)
- `Upload` (File method)

### Existing Components
- `SingleUrlImportForm`
- `BulkImportDialog`
- `ImporterWorkspace`

---

## Implementation Stats

- **File:** `/mnt/containers/deal-brain/apps/web/app/(dashboard)/import/page.tsx`
- **Lines:** 202
- **Components:** 3 new (ImportMethodCard + page structure)
- **Dependencies:** 8 imports
- **State:** 2 useState hooks (activeTab, bulkDialogOpen)

---

## Future Enhancements

### Near-Term
- Tab badges showing active import counts
- Recent imports list (last 5)
- Contextual help tooltips

### Mid-Term
- Saved URL templates
- Import scheduler
- Dedicated history page

### Long-Term
- Direct API integrations (eBay, Amazon)
- AI-assisted field mapping
- Real-time collaboration

---

## Testing Priorities

### Critical
- [ ] Tab switching works correctly
- [ ] Both forms submit and handle responses
- [ ] Keyboard navigation functions
- [ ] Screen reader announces content
- [ ] Mobile responsive layout

### Important
- [ ] Dark mode compatibility (if enabled)
- [ ] Focus indicators visible
- [ ] Touch targets meet 44px
- [ ] Cross-browser compatibility

### Nice-to-Have
- [ ] Animation smoothness
- [ ] Print styles
- [ ] High contrast mode

---

## Design System Alignment

All design decisions align with existing shadcn/ui patterns:
- Consistent card styling
- Standard button variants
- Familiar tab navigation
- Reusable component patterns
- Tailwind utility classes throughout

---

## Success Metrics

### User Experience
- **Clarity:** Users understand which method to use
- **Discoverability:** Both methods immediately visible
- **Efficiency:** Minimal clicks to start import
- **Confidence:** Clear feedback and guidance

### Technical
- **Performance:** Instant tab switching
- **Accessibility:** WCAG AA compliant
- **Maintainability:** Follows established patterns
- **Extensibility:** Easy to add new import methods

---

## Quick Links

- **Full Specification:** `/mnt/containers/deal-brain/docs/design/import-page-specification.md`
- **Visual Spec:** `/mnt/containers/deal-brain/docs/design/import-page-visual-spec.md`
- **Implementation:** `/mnt/containers/deal-brain/apps/web/app/(dashboard)/import/page.tsx`

---

## Changelog

**2025-10-21:** Initial design and implementation
- Tab-based navigation
- Method description cards
- Integration with existing components
- Full accessibility compliance
- Responsive design
- Performance optimizations
