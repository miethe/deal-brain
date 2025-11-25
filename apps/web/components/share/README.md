# Share Components

Components for sharing listings via public links or with specific users.

## Components

### ShareButton

A button that opens the share modal when clicked.

**Props:**
- `listingId: number` - ID of the listing to share
- `listingName: string` - Name/title of the listing (for display)
- `variant?: "default" | "ghost" | "outline" | "secondary"` - Button variant (default: "ghost")
- `size?: "default" | "sm" | "lg" | "icon"` - Button size (default: "sm")
- `className?: string` - Additional CSS classes

**Example:**
```tsx
import { ShareButton } from "@/components/share";

<ShareButton
  listingId={123}
  listingName="Intel NUC 11 Pro"
  variant="ghost"
  size="sm"
/>
```

### ShareModal

Modal dialog with tabs for two sharing methods:
1. **Copy Link** - Generate and copy a public shareable link
2. **Share with User** - Send listing to a specific user with optional message

**Props:**
- `open: boolean` - Whether the modal is open
- `onOpenChange: (open: boolean) => void` - Callback when modal open state changes
- `listingId: number` - ID of the listing to share
- `listingName: string` - Name/title of the listing (for display)

**Example:**
```tsx
import { ShareModal } from "@/components/share";

const [open, setOpen] = useState(false);

<ShareModal
  open={open}
  onOpenChange={setOpen}
  listingId={123}
  listingName="Intel NUC 11 Pro"
/>
```

## Hooks

### useShareListing

React Query mutation hook for generating public share links.

**Returns:** `UseMutationResult<ShareLinkResponse, Error, ShareLinkRequest>`

**Example:**
```tsx
import { useShareListing } from "@/hooks/use-share-listing";

const shareListing = useShareListing();

shareListing.mutate({
  listing_id: 123,
  expires_in_days: 180
});
```

### useShareWithUser

React Query mutation hook for sharing listings with specific users.

**Returns:** `UseMutationResult<UserShareResponse, Error, UserShareRequest>`

**Example:**
```tsx
import { useShareWithUser } from "@/hooks/use-share-with-user";

const shareWithUser = useShareWithUser();

shareWithUser.mutate({
  recipient_id: 456,
  listing_id: 123,
  message: "Check out this deal!"
});
```

### useUserSearch

React Query hook for searching users by username or email.

**Parameters:**
- `query: string` - Search query
- `enabled?: boolean` - Whether the query should run (default: true)

**Returns:** `UseQueryResult<UserSearchResponse, Error>`

**Example:**
```tsx
import { useUserSearch } from "@/hooks/use-user-search";

const [query, setQuery] = useState("");
const [debouncedQuery] = useDebounce(query, 200);
const userSearch = useUserSearch(debouncedQuery);

const users = userSearch.data?.users || [];
```

## Integration Examples

### Add to Listing Card

```tsx
// apps/web/app/listings/_components/grid-view/listing-card.tsx
import { ShareButton } from "@/components/share";

// In the header section, alongside other action buttons:
<CardHeader className="pb-3">
  <div className="flex items-start justify-between gap-2">
    <h3 className="font-semibold text-base line-clamp-2 flex-1">
      {listing.title}
    </h3>
    <div className="flex gap-1">
      {/* Existing buttons */}
      <ShareButton
        listingId={listing.id}
        listingName={listing.title}
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
      />
      {/* Other action buttons */}
    </div>
  </div>
</CardHeader>
```

### Add to Listing Details Page

```tsx
// In a listing details page or modal
import { ShareButton } from "@/components/share";

<div className="flex justify-end gap-2">
  <ShareButton
    listingId={listing.id}
    listingName={listing.title}
  />
</div>
```

## Features

### Copy Link Tab
- Automatically generates share link on mount
- One-click copy to clipboard with visual feedback
- Shows link expiration information
- Error handling with retry option
- Loading states

### Share with User Tab
- Debounced user search (200ms)
- Real-time search results dropdown
- User selection with display of selected user
- Optional message field
- Rate limit awareness (10 shares/hour)
- Success/error handling with toast notifications
- Form reset on success

## Accessibility

- Keyboard navigation (Tab, Escape)
- Focus management (auto-focus on inputs)
- ARIA labels for screen readers
- Proper dialog semantics
- High contrast support

## API Endpoints

### Generate Public Share Link
```
POST /v1/listings/{listing_id}/share
Body: { expires_in_days?: number }
Response: { share_token, share_url, expires_at }
```

### Create User-to-User Share
```
POST /v1/user-shares
Body: { recipient_id, listing_id, message? }
Response: { id, share_token, recipient_id, listing_id, message, created_at }
```

### Search Users
```
GET /v1/users/search?q={query}&limit=10
Response: { users: [{ id, username, email }] }
```

## Notes

- Share links expire after 180 days by default
- Rate limited to 10 shares per hour per user
- User search is debounced to reduce API calls
- Toast notifications on all success/error states
- Modal closes automatically on successful user share
