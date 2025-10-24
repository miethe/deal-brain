# Provenance Badge Components

## Overview

The provenance badge system provides visual indicators for listing data origin, quality, and freshness in Deal Brain's URL ingestion feature (Phase 4, Task ID-024).

## Quick Start

```tsx
import {
  ProvenanceBadge,
  QualityIndicator,
  LastSeenTimestamp,
  ListingProvenanceDisplay
} from '@/components/listings';

// Simple usage
<ProvenanceBadge provenance="ebay_api" />

// Complete display
<ListingProvenanceDisplay
  provenance="ebay_api"
  quality="full"
  lastSeenAt="2025-04-27T10:30:00Z"
/>
```

## Components

### ProvenanceBadge

Displays the data source with color-coded visual indicators.

**Sources:**
- `ebay_api` - Blue badge with shopping cart icon
- `jsonld` - Green badge with structured data icon
- `scraper` - Yellow badge with web scraper icon
- `excel` - Gray badge with spreadsheet icon

### QualityIndicator

Shows data quality level with tooltips for missing fields.

**Levels:**
- `full` - Green checkmark (all fields present)
- `partial` - Orange warning (some fields missing)

### LastSeenTimestamp

Displays when listing was last updated with relative time.

**Features:**
- Relative format ("2 days ago")
- Tooltip with exact date/time
- Semantic HTML time element

### ListingProvenanceDisplay

Composite component combining all three badges.

## Props Reference

### ProvenanceBadge Props

```typescript
interface ProvenanceBadgeProps {
  provenance: 'ebay_api' | 'jsonld' | 'scraper' | 'excel';
  className?: string;
  showLabel?: boolean; // default: true
}
```

### QualityIndicator Props

```typescript
interface QualityIndicatorProps {
  quality: 'full' | 'partial';
  missingFields?: string[];
  className?: string;
  showLabel?: boolean; // default: true
}
```

### LastSeenTimestamp Props

```typescript
interface LastSeenTimestampProps {
  lastSeenAt: string; // ISO datetime
  className?: string;
  showIcon?: boolean; // default: true
  showLabel?: boolean; // default: true
}
```

### ListingProvenanceDisplay Props

```typescript
interface ListingProvenanceDisplayProps {
  provenance: ProvenanceSource;
  quality?: QualityLevel;
  lastSeenAt?: string;
  missingFields?: string[];
  className?: string;
  layout?: 'horizontal' | 'vertical'; // default: 'horizontal'
  showSource?: boolean; // default: true
  showQuality?: boolean; // default: true
  showTimestamp?: boolean; // default: true
  compact?: boolean; // default: false (icons only when true)
}
```

## Usage Examples

### In Listing Cards

```tsx
function ListingCard({ listing }) {
  return (
    <Card>
      <CardHeader>
        <h3>{listing.title}</h3>
        {listing.provenance && (
          <ListingProvenanceDisplay
            provenance={listing.provenance.source}
            quality={listing.provenance.quality}
            lastSeenAt={listing.provenance.lastSeenAt}
            missingFields={listing.provenance.missingFields}
          />
        )}
      </CardHeader>
      <CardContent>
        {/* ... */}
      </CardContent>
    </Card>
  );
}
```

### In Tables (Compact Mode)

```tsx
function ProvenanceCell({ listing }) {
  if (!listing.provenance) return null;

  return (
    <ListingProvenanceDisplay
      provenance={listing.provenance.source}
      quality={listing.provenance.quality}
      compact
      showTimestamp={false}
    />
  );
}
```

### In Detail Pages

```tsx
function ListingDetails({ listing }) {
  return (
    <div>
      <h1>{listing.title}</h1>

      <div className="flex items-center gap-3 mt-4">
        <span className="text-sm font-medium text-muted-foreground">
          Data Source:
        </span>
        {listing.provenance && (
          <>
            <ProvenanceBadge provenance={listing.provenance.source} />
            <QualityIndicator
              quality={listing.provenance.quality}
              missingFields={listing.provenance.missingFields}
            />
            <LastSeenTimestamp lastSeenAt={listing.provenance.lastSeenAt} />
          </>
        )}
      </div>
    </div>
  );
}
```

### Conditional Rendering

```tsx
import { hasProvenance, isPartialQuality, isStaleProvenance } from '@/components/listings';

function ListingMetadata({ listing }) {
  if (!hasProvenance(listing)) {
    return <Badge variant="outline">No provenance data</Badge>;
  }

  const needsRefresh =
    isPartialQuality(listing.provenance) ||
    isStaleProvenance(listing.provenance.lastSeenAt, 7);

  return (
    <div className="space-y-2">
      <ListingProvenanceDisplay {...listing.provenance} />

      {needsRefresh && (
        <Alert variant="warning">
          <AlertDescription>
            This listing may need a data refresh
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
```

## Type Definitions

```typescript
// Core types
type ProvenanceSource = 'ebay_api' | 'jsonld' | 'scraper' | 'excel';
type QualityLevel = 'full' | 'partial';

// Provenance metadata
interface ListingProvenance {
  source: ProvenanceSource;
  quality: QualityLevel;
  lastSeenAt: string;
  missingFields?: string[];
  sourceUrl?: string;
  ebayListingId?: string;
  confidenceScore?: number;
}

// Extended listing type
interface ListingWithProvenance {
  id: number;
  title: string;
  price: number;
  provenance?: ListingProvenance;
  // ... other fields
}

// Helper functions
hasProvenance(listing): boolean
isPartialQuality(provenance): boolean
isStaleProvenance(lastSeenAt, staleDays): boolean
```

## Accessibility

All components follow WCAG 2.1 AA standards:

- **Screen Readers**: Proper ARIA labels on all badges
- **Keyboard Navigation**: Tooltips accessible via Tab key
- **Color Independence**: Icons accompany all colors
- **Contrast**: Compliant in light and dark modes
- **Semantic HTML**: Proper time elements with datetime attributes

**Screen Reader Example:**
```
"Data source: eBay API, Quality: Full, Last seen 2 days ago"
```

## Performance

All components are memoized with `React.memo()` to prevent unnecessary re-renders when props haven't changed.

## Dark Mode

Components automatically adapt to dark mode using Tailwind's `dark:` variants with proper color contrast maintained.

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
    "missingFields": [],
    "sourceUrl": "https://www.ebay.com/itm/...",
    "ebayListingId": "295813456789"
  }
}
```

## File Locations

- Components: `/apps/web/components/listings/`
  - `provenance-badge.tsx` - Source badge
  - `quality-indicator.tsx` - Quality indicator
  - `last-seen-timestamp.tsx` - Timestamp display
  - `listing-provenance-display.tsx` - Composite component
  - `provenance-types.ts` - TypeScript types
  - `index.ts` - Export barrel

- Documentation:
  - `/apps/web/components/listings/PROVENANCE_README.md` - Full documentation
  - `/docs/components/provenance-badges.md` - This file

- Examples:
  - `/apps/web/components/listings/provenance-examples.tsx` - Demo component

- Tests:
  - `/apps/web/components/listings/__tests__/provenance-badge.test.tsx`

## Implementation Status

**Phase 4, Task ID-024: Complete**

- [x] ProvenanceBadge component
- [x] QualityIndicator component
- [x] LastSeenTimestamp component
- [x] ListingProvenanceDisplay composite component
- [x] TypeScript type definitions
- [x] Accessibility compliance (WCAG 2.1 AA)
- [x] Dark mode support
- [x] Documentation
- [x] Test suite
- [x] Usage examples

## Next Steps

To integrate into listing pages:

1. Add provenance field to Listing API response
2. Update listing cards to display provenance badges
3. Add provenance to listing detail pages
4. Implement filtering by provenance source
5. Add refresh actions for stale data

## Related Documentation

- Implementation Plan: `/docs/project_plans/url-ingest/implementation-plan.md`
- Phase 4 Tasks: Search for "ID-024" in implementation plan
- Deal Brain Architecture: `/CLAUDE.md`
