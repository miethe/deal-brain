# Integration Example: Adding ShareButton to Listing Card

This document shows exactly how to add the ShareButton to the existing listing card component.

## File: `apps/web/app/listings/_components/grid-view/listing-card.tsx`

### Step 1: Add Import

Add this import at the top of the file:

```tsx
import { ShareButton } from "@/components/share";
```

### Step 2: Add ShareButton to Header

In the header section (around line 126-153), add the ShareButton before the "Open" and "Delete" buttons:

```tsx
<CardHeader className="pb-3">
  <div className="flex items-start justify-between gap-2">
    <h3 className="font-semibold text-base line-clamp-2 flex-1">
      {listing.title}
    </h3>
    <div className="flex gap-1">
      {/* NEW: Add ShareButton */}
      <ShareButton
        listingId={listing.id}
        listingName={listing.title}
        variant="ghost"
        size="icon"
        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
      />

      {/* Existing buttons */}
      {listing.listing_url && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={handleOpenExternal}
          aria-label="Open listing in new tab"
        >
          <ArrowUpRight className="h-4 w-4" />
        </Button>
      )}
      <Button
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={handleDelete}
        aria-label="Delete listing"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  </div>
</CardHeader>
```

## Complete Modified Section

Here's the complete modified header section with proper context:

```tsx
{/* Header */}
<CardHeader className="pb-3">
  <div className="flex items-start justify-between gap-2">
    <h3 className="font-semibold text-base line-clamp-2 flex-1">
      {listing.title}
    </h3>
    <div className="flex gap-1">
      {/* Share Button - NEW */}
      <ShareButton
        listingId={listing.id}
        listingName={listing.title}
        variant="ghost"
        size="icon"
        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
      />

      {/* Open External Link */}
      {listing.listing_url && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={handleOpenExternal}
          aria-label="Open listing in new tab"
        >
          <ArrowUpRight className="h-4 w-4" />
        </Button>
      )}

      {/* Delete Button */}
      <Button
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={handleDelete}
        aria-label="Delete listing"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  </div>
</CardHeader>
```

## Notes

1. The ShareButton uses `size="icon"` to match the other icon buttons
2. It has the same `opacity-0 group-hover:opacity-100` class to show on card hover
3. The button automatically handles modal opening/closing
4. The modal will handle all share functionality (copy link, share with user)

## Testing

After making these changes:

1. Hover over a listing card
2. The share button should appear alongside the open/delete buttons
3. Click the share button
4. The share modal should open with two tabs:
   - "Copy Link" - generates and allows copying a public share link
   - "Share with User" - allows searching for and sending to a specific user

## Alternative Placement Options

### In Card Footer (Alongside Quick Edit)

```tsx
<CardFooter className="pt-3 border-t flex items-center justify-between">
  {listing.manufacturer && (
    <Badge variant="outline" className="text-xs">
      {listing.manufacturer}
    </Badge>
  )}
  <div className="flex gap-2 ml-auto">
    <ShareButton
      listingId={listing.id}
      listingName={listing.title}
      variant="ghost"
      size="sm"
      className="h-8 opacity-0 group-hover:opacity-100 transition-opacity"
    />
    <Button
      variant="ghost"
      size="sm"
      className="h-8 opacity-0 group-hover:opacity-100 transition-opacity"
      onClick={handleQuickEdit}
    >
      <SquarePen className="h-4 w-4 mr-1" />
      Quick Edit
    </Button>
  </div>
</CardFooter>
```

### Always Visible (No Hover)

If you want the share button to always be visible instead of only on hover, simply remove the opacity classes:

```tsx
<ShareButton
  listingId={listing.id}
  listingName={listing.title}
  variant="ghost"
  size="icon"
  className="h-8 w-8 p-0"  // Removed opacity classes
/>
```
