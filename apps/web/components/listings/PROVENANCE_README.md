# Provenance Badge Components

Provenance badge components for displaying listing data source, quality level, and freshness indicators in Deal Brain.

## Overview

The provenance badge system provides visual indicators for:
- **Data Source**: Where the listing data came from (eBay API, JSON-LD, Web Scraper, Excel)
- **Data Quality**: Whether all required fields are present (Full/Partial)
- **Data Freshness**: When the listing was last seen/updated

## Components

### 1. ProvenanceBadge

Displays the data source with color-coded badge and icon.

```tsx
import { ProvenanceBadge } from '@/components/listings';

<ProvenanceBadge provenance="ebay_api" />
<ProvenanceBadge provenance="jsonld" />
<ProvenanceBadge provenance="scraper" />
<ProvenanceBadge provenance="excel" />
```

**Props:**
- `provenance`: `'ebay_api' | 'jsonld' | 'scraper' | 'excel'` (required)
- `className?`: Additional CSS classes
- `showLabel?`: Show text label (default: `true`)

**Color Scheme:**
- **eBay API**: Blue badge with shopping cart icon
- **JSON-LD**: Green badge with code icon
- **Web Scraper**: Yellow badge with globe icon
- **Excel**: Gray badge with spreadsheet icon

### 2. QualityIndicator

Displays data quality level with tooltip for missing fields.

```tsx
import { QualityIndicator } from '@/components/listings';

// Full quality
<QualityIndicator quality="full" />

// Partial quality with missing fields
<QualityIndicator
  quality="partial"
  missingFields={['RAM Size', 'Storage Type']}
/>
```

**Props:**
- `quality`: `'full' | 'partial'` (required)
- `missingFields?`: Array of missing field names (shown in tooltip)
- `className?`: Additional CSS classes
- `showLabel?`: Show text label (default: `true`)

**Color Scheme:**
- **Full**: Green badge with checkmark icon
- **Partial**: Orange badge with alert icon + tooltip

### 3. LastSeenTimestamp

Displays when the listing was last updated with relative time formatting.

```tsx
import { LastSeenTimestamp } from '@/components/listings';

<LastSeenTimestamp lastSeenAt="2025-04-27T10:30:00Z" />
```

**Props:**
- `lastSeenAt`: ISO datetime string (required)
- `className?`: Additional CSS classes
- `showIcon?`: Show clock icon (default: `true`)
- `showLabel?`: Show label text (default: `true`)

**Features:**
- Displays relative time (e.g., "2 days ago")
- Tooltip shows exact date/time on hover
- Uses semantic `<time>` element with `datetime` attribute

### 4. ListingProvenanceDisplay (Composite)

Combines all three components into a single, flexible display.

```tsx
import { ListingProvenanceDisplay } from '@/components/listings';

<ListingProvenanceDisplay
  provenance="ebay_api"
  quality="full"
  lastSeenAt="2025-04-27T10:30:00Z"
/>

// Partial quality with missing fields
<ListingProvenanceDisplay
  provenance="jsonld"
  quality="partial"
  lastSeenAt="2025-04-27T10:30:00Z"
  missingFields={['GPU Model', 'RAM Size']}
/>

// Vertical layout
<ListingProvenanceDisplay
  provenance="scraper"
  quality="full"
  lastSeenAt="2025-04-27T10:30:00Z"
  layout="vertical"
/>

// Compact mode (icons only)
<ListingProvenanceDisplay
  provenance="ebay_api"
  quality="full"
  lastSeenAt="2025-04-27T10:30:00Z"
  compact
/>

// Selective display
<ListingProvenanceDisplay
  provenance="excel"
  lastSeenAt="2025-04-27T10:30:00Z"
  showQuality={false}  // Hide quality indicator
/>
```

**Props:**
- `provenance`: `'ebay_api' | 'jsonld' | 'scraper' | 'excel'` (required)
- `quality?`: `'full' | 'partial'`
- `lastSeenAt?`: ISO datetime string
- `missingFields?`: Array of missing field names
- `className?`: Additional CSS classes
- `layout?`: `'horizontal' | 'vertical'` (default: `'horizontal'`)
- `showSource?`: Show provenance badge (default: `true`)
- `showQuality?`: Show quality indicator (default: `true`)
- `showTimestamp?`: Show timestamp (default: `true`)
- `compact?`: Hide labels, show only icons (default: `false`)

## Type Definitions

```tsx
import type {
  ProvenanceSource,
  QualityLevel,
  ListingProvenance,
  ListingWithProvenance,
  ProvenanceStats,
} from '@/components/listings';

// Type guards and helpers
import {
  hasProvenance,
  isPartialQuality,
  isStaleProvenance,
} from '@/components/listings';
```

**Core Types:**

```typescript
type ProvenanceSource = 'ebay_api' | 'jsonld' | 'scraper' | 'excel';
type QualityLevel = 'full' | 'partial';

interface ListingProvenance {
  source: ProvenanceSource;
  quality: QualityLevel;
  lastSeenAt: string;
  missingFields?: string[];
  sourceUrl?: string;
  ebayListingId?: string;
  confidenceScore?: number;
}
```

**Helper Functions:**

```typescript
// Check if listing has provenance data
if (hasProvenance(listing)) {
  console.log(listing.provenance.source);
}

// Check if quality is partial
if (isPartialQuality(listing.provenance)) {
  console.log('Some fields are missing');
}

// Check if data is stale (default: 7 days)
if (isStaleProvenance(listing.provenance.lastSeenAt, 7)) {
  console.log('Data needs refresh');
}
```

## Usage Examples

### In Listing Cards

```tsx
import { ListingProvenanceDisplay } from '@/components/listings';

function ListingCard({ listing }) {
  return (
    <div className="border rounded-lg p-4">
      <h3>{listing.title}</h3>
      <p className="text-2xl font-bold">${listing.price}</p>

      {listing.provenance && (
        <ListingProvenanceDisplay
          provenance={listing.provenance.source}
          quality={listing.provenance.quality}
          lastSeenAt={listing.provenance.lastSeenAt}
          missingFields={listing.provenance.missingFields}
        />
      )}
    </div>
  );
}
```

### In Table Cells (Compact)

```tsx
import { ListingProvenanceDisplay } from '@/components/listings';

function ListingsTable({ listings }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Title</th>
          <th>Price</th>
          <th>Source</th>
        </tr>
      </thead>
      <tbody>
        {listings.map(listing => (
          <tr key={listing.id}>
            <td>{listing.title}</td>
            <td>${listing.price}</td>
            <td>
              {listing.provenance && (
                <ListingProvenanceDisplay
                  provenance={listing.provenance.source}
                  quality={listing.provenance.quality}
                  compact
                  showTimestamp={false}
                />
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### In Detail Pages

```tsx
import {
  ProvenanceBadge,
  QualityIndicator,
  LastSeenTimestamp
} from '@/components/listings';

function ListingDetailPage({ listing }) {
  if (!listing.provenance) return null;

  return (
    <div>
      <h1>{listing.title}</h1>

      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <span className="font-medium">Data Source:</span>
        <ProvenanceBadge provenance={listing.provenance.source} />
        <QualityIndicator
          quality={listing.provenance.quality}
          missingFields={listing.provenance.missingFields}
        />
        <LastSeenTimestamp lastSeenAt={listing.provenance.lastSeenAt} />
      </div>
    </div>
  );
}
```

### Conditional Rendering

```tsx
import { hasProvenance, isPartialQuality } from '@/components/listings';

function ListingMetadata({ listing }) {
  if (!hasProvenance(listing)) {
    return <span className="text-muted-foreground">No provenance data</span>;
  }

  const needsAttention = isPartialQuality(listing.provenance) ||
                         isStaleProvenance(listing.provenance.lastSeenAt);

  return (
    <div>
      <ListingProvenanceDisplay {...listing.provenance} />
      {needsAttention && (
        <p className="text-sm text-orange-600 mt-2">
          This listing may need data refresh
        </p>
      )}
    </div>
  );
}
```

## Accessibility Features

All components are built with WCAG 2.1 AA compliance:

- **Screen Readers**: Proper ARIA labels on all badges
- **Keyboard Navigation**: Tooltips accessible via Tab key focus
- **Color Independence**: Icons accompany all color indicators
- **Contrast**: Compliant color contrast in light and dark modes
- **Semantic HTML**: Uses proper `<time>` elements with `datetime` attributes
- **Focus Indicators**: Clear focus states for keyboard navigation

**Screen Reader Announcements:**

```
"Data source: eBay API, Quality: Full, Last seen 2 days ago"
"Data from JSON-LD structured data, Quality: Partial - 3 fields missing"
```

## Dark Mode Support

All components automatically adapt to dark mode using Tailwind's `dark:` variants:

- Badge backgrounds and text colors adjust automatically
- Tooltips maintain proper contrast in both modes
- Icons remain visible and accessible in all themes

## Performance

All components are memoized using `React.memo()` to prevent unnecessary re-renders:

```tsx
export const ProvenanceBadge = memo(ProvenanceBadgeComponent);
export const QualityIndicator = memo(QualityIndicatorComponent);
export const LastSeenTimestamp = memo(LastSeenTimestampComponent);
export const ListingProvenanceDisplay = memo(ListingProvenanceDisplayComponent);
```

## Testing

### Component Tests

```tsx
import { render, screen } from '@testing-library/react';
import { ProvenanceBadge } from '@/components/listings';

test('renders eBay API badge', () => {
  render(<ProvenanceBadge provenance="ebay_api" />);
  expect(screen.getByLabelText(/Data from eBay API/i)).toBeInTheDocument();
});

test('renders partial quality with tooltip', async () => {
  const { user } = render(
    <QualityIndicator
      quality="partial"
      missingFields={['RAM Size']}
    />
  );

  const badge = screen.getByLabelText(/Partial/i);
  await user.hover(badge);

  expect(screen.getByText('Missing Fields:')).toBeInTheDocument();
  expect(screen.getByText('RAM Size')).toBeInTheDocument();
});
```

## Backend Integration

Expected API response structure:

```json
{
  "id": 123,
  "title": "Dell OptiPlex 7090",
  "price": 459.00,
  "provenance": {
    "source": "ebay_api",
    "quality": "full",
    "lastSeenAt": "2025-04-27T10:30:00Z",
    "sourceUrl": "https://www.ebay.com/itm/...",
    "ebayListingId": "295813456789"
  }
}
```

## File Structure

```
apps/web/components/listings/
├── provenance-badge.tsx          # Source badge component
├── quality-indicator.tsx         # Quality indicator component
├── last-seen-timestamp.tsx       # Timestamp component
├── listing-provenance-display.tsx # Composite component
├── provenance-types.ts           # TypeScript types
├── provenance-examples.tsx       # Usage examples/demos
├── PROVENANCE_README.md          # This documentation
└── index.ts                      # Export barrel
```

## Future Enhancements

Potential improvements for future iterations:

1. **Auto-refresh**: Automatically update relative timestamps
2. **Staleness warnings**: Visual indicators for stale data
3. **Source priority**: Display reliability scores by source
4. **Bulk operations**: Refresh multiple listings at once
5. **History tracking**: Show provenance change history
6. **Quality metrics**: Display data completeness percentage
7. **Source filtering**: Filter listings by provenance source
8. **Export metadata**: Include provenance in exports

## Support

For questions or issues with provenance components:

1. Check this documentation
2. Review `provenance-examples.tsx` for usage patterns
3. Consult the implementation plan at `/docs/project_plans/url-ingest/`
4. Check Deal Brain's CLAUDE.md for architecture guidance
