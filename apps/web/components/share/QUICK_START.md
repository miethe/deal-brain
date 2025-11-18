# Quick Start Guide - Share Components

## 1. Basic Usage

The simplest way to add sharing to a listing:

```tsx
import { ShareButton } from "@/components/share";

function MyComponent() {
  return (
    <ShareButton
      listingId={123}
      listingName="Intel NUC 11 Pro"
    />
  );
}
```

That's it! The button will:
- Show a share icon
- Open a modal when clicked
- Handle all sharing logic internally

## 2. Add to Existing Listing Card

### File: `apps/web/app/listings/_components/grid-view/listing-card.tsx`

**Step 1:** Add import at the top:
```tsx
import { ShareButton } from "@/components/share";
```

**Step 2:** Add button in the header (around line 131):
```tsx
<div className="flex gap-1">
  {/* Add this before existing buttons */}
  <ShareButton
    listingId={listing.id}
    listingName={listing.title}
    variant="ghost"
    size="icon"
    className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
  />

  {/* Existing open/delete buttons stay here */}
  {listing.listing_url && (
    <Button ...>
      <ArrowUpRight className="h-4 w-4" />
    </Button>
  )}
  {/* ... rest of buttons */}
</div>
```

Done! The share button will now appear when hovering over listing cards.

## 3. Customization Options

### Different Variants
```tsx
{/* Ghost (default) */}
<ShareButton listingId={123} listingName="PC" variant="ghost" />

{/* Outline */}
<ShareButton listingId={123} listingName="PC" variant="outline" />

{/* Default (colored) */}
<ShareButton listingId={123} listingName="PC" variant="default" />
```

### Different Sizes
```tsx
{/* Small */}
<ShareButton listingId={123} listingName="PC" size="sm" />

{/* Icon only */}
<ShareButton listingId={123} listingName="PC" size="icon" />

{/* Large */}
<ShareButton listingId={123} listingName="PC" size="lg" />
```

### Always Visible (No Hover)
```tsx
<ShareButton
  listingId={123}
  listingName="PC"
  className="h-8 w-8 p-0"  {/* No opacity classes */}
/>
```

## 4. Advanced Usage - Direct Modal Control

If you need more control:

```tsx
import { useState } from "react";
import { ShareModal } from "@/components/share";
import { Button } from "@/components/ui/button";

function MyComponent() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setOpen(true)}>
        Custom Share Button
      </Button>

      <ShareModal
        open={open}
        onOpenChange={setOpen}
        listingId={123}
        listingName="Intel NUC 11 Pro"
      />
    </>
  );
}
```

## 5. Using Hooks Directly

For custom implementations:

```tsx
import { useShareListing } from "@/hooks/use-share-listing";
import { useShareWithUser } from "@/hooks/use-share-with-user";
import { useUserSearch } from "@/hooks/use-user-search";

function CustomShareComponent() {
  // Generate public link
  const shareListing = useShareListing();

  const handleShareLink = () => {
    shareListing.mutate({
      listing_id: 123,
      expires_in_days: 180
    });
  };

  // Share with user
  const shareWithUser = useShareWithUser();

  const handleShareWithUser = () => {
    shareWithUser.mutate({
      recipient_id: 456,
      listing_id: 123,
      message: "Check this out!"
    });
  };

  // Search users
  const [query, setQuery] = useState("");
  const [debouncedQuery] = useDebounce(query, 200);
  const userSearch = useUserSearch(debouncedQuery);

  const users = userSearch.data?.users || [];

  return (
    <div>
      {/* Your custom UI */}
    </div>
  );
}
```

## 6. Testing the Implementation

### Dev Environment

1. Start the dev server:
   ```bash
   make web  # or cd apps/web && pnpm dev
   ```

2. Navigate to listings page

3. Hover over a listing card

4. Click the share button (Share2 icon)

5. Test both tabs:
   - **Copy Link**: Verify link generates and copy works
   - **Share with User**: Search for a user and send

### Expected Behavior

**Copy Link Tab:**
- Link generates automatically (spinner shows briefly)
- Link appears in a read-only input field
- Click copy button → Check icon appears for 2 seconds
- Expiry info shows (e.g., "Expires in 180 days")

**Share with User Tab:**
- Type in search box → wait 200ms → results appear
- Click a user → dropdown closes, user info displays
- Type optional message
- Click Send → loading spinner → success toast → modal closes

## 7. Troubleshooting

### "Failed to generate share link"
- Check backend is running (`make api`)
- Verify API endpoint exists: `POST /v1/listings/{id}/share`
- Check browser console for errors

### "Failed to share listing" or "User not found"
- Verify backend user-shares endpoint: `POST /v1/user-shares`
- Check user search endpoint: `GET /v1/users/search?q=...`
- Ensure users exist in database

### Share button doesn't appear
- Check import path: `import { ShareButton } from "@/components/share"`
- Verify component is inside the card's action button group
- Check hover styles (might need to remove opacity for always-visible)

### TypeScript errors
- Ensure all dependencies are installed: `pnpm install`
- Check `@tanstack/react-query`, `lucide-react`, `use-debounce` are in package.json

## 8. Next Steps

1. **Add to listing cards** - Follow section 2 above
2. **Test functionality** - Follow section 6 above
3. **Add to detail pages** - Use section 1 pattern
4. **Customize styling** - Use section 3 options
5. **Add analytics** - Track share events (optional)

## Need Help?

See the full documentation:
- `README.md` - Complete API reference
- `INTEGRATION_EXAMPLE.md` - Detailed integration steps
- `IMPLEMENTATION_SUMMARY.md` - Architecture and patterns

## Summary

**Files Created:**
- ✅ `components/share/share-button.tsx` - Button component
- ✅ `components/share/share-modal.tsx` - Modal with tabs
- ✅ `hooks/use-share-listing.ts` - Public link hook
- ✅ `hooks/use-share-with-user.ts` - User sharing hook
- ✅ `hooks/use-user-search.ts` - User search hook

**Features:**
- ✅ Public link sharing (copy to clipboard)
- ✅ User-to-user sharing (with message)
- ✅ Debounced user search (200ms)
- ✅ Loading states and error handling
- ✅ Toast notifications
- ✅ Keyboard navigation and accessibility
- ✅ Mobile responsive

**Integration Time:** ~2 minutes (add 3 lines to listing-card.tsx)

Ready to use!
