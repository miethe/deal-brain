# Collections Components

This directory contains React components for the Collections feature, which allows users to organize and curate listings.

## Components

### `collection-selector-modal.tsx`

A reusable modal for quickly adding listings to collections. Used throughout the application for quick collection management.

**Features:**
- Two-state UI: list view and create view
- Shows 5 most recent collections for quick selection
- Inline collection creation without modal cascade
- Optimistic updates with React Query
- Handles 409 Conflict errors gracefully
- Auto-closes after successful addition
- Keyboard accessible

**Props:**
```typescript
interface CollectionSelectorModalProps {
  listingId: number;        // The listing to add
  isOpen: boolean;          // Control modal visibility
  onClose: () => void;      // Called when modal closes
  onSuccess?: (collectionId: number) => void; // Optional callback after add
}
```

**Usage Example:**
```tsx
import { CollectionSelectorModal } from "@/components/collections/collection-selector-modal";

function MyComponent() {
  const [showSelector, setShowSelector] = useState(false);

  return (
    <>
      <Button onClick={() => setShowSelector(true)}>
        Add to Collection
      </Button>

      <CollectionSelectorModal
        listingId={123}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onSuccess={(collectionId) => {
          console.log(`Added to collection ${collectionId}`);
        }}
      />
    </>
  );
}
```

**Integration Points:**
- Public deal pages (share links)
- Listings search/browse view
- Listing detail pages
- Import flows

**Dependencies:**
- `@/hooks/use-collections` - Fetching and creating collections
- `@/hooks/use-add-to-collection` - Adding items to collections
- `@/hooks/use-toast` - Toast notifications
- Radix UI Dialog components
- shadcn/ui form components

---

### `new-collection-form.tsx`

A standalone modal form for creating new collections with full field options.

**Features:**
- Name, description, and visibility fields
- Form validation
- Auto-navigation to new collection after creation
- Used in collections list pages

---

### `collection-card.tsx`

A card component for displaying collection summaries in grid/list views.

**Features:**
- Collection name, description, item count
- Quick actions (view, edit, delete)
- Responsive design

---

### `item-details-panel.tsx`

Side panel showing detailed information about a collection item.

**Features:**
- Listing details
- Status management (undecided, shortlisted, rejected, bought)
- Notes editing
- Quick actions

---

### `workspace-*.tsx`

Components for the collection workspace view:
- `workspace-header.tsx` - Collection header with actions
- `workspace-table.tsx` - Table view of collection items
- `workspace-cards.tsx` - Card/grid view of items
- `workspace-filters.tsx` - Filtering and sorting controls

---

### `collections-empty-state.tsx`

Empty state component shown when user has no collections.

---

## Hooks

### `use-add-to-collection.ts`

React Query mutation hook for adding listings to collections.

**Features:**
- Automatic cache invalidation
- Toast notifications on success/error
- Handles 409 Conflict (duplicate items)
- Optimistic updates support

**Usage:**
```tsx
const addMutation = useAddToCollection({
  collectionId: 123,
  collectionName: "Gaming Builds",
  onSuccess: (item) => {
    console.log("Added:", item);
  },
});

addMutation.mutate({
  listing_id: 456,
  status: "undecided",
  notes: "Looks promising",
});
```

---

## API Endpoints Used

**Get Collections:**
```
GET /v1/collections?limit=5
Response: { collections: Collection[], total: number }
```

**Add Item to Collection:**
```
POST /v1/collections/{id}/items
Body: { listing_id: number, status?: string, notes?: string }
Response: CollectionItem
```

**Create Collection:**
```
POST /v1/collections
Body: { name: string, description?: string, visibility?: string }
Response: Collection
```

---

## Testing

Tests are located in `__tests__/collection-selector-modal.test.tsx`.

**Run tests:**
```bash
cd apps/web
pnpm test collection-selector-modal
```

**Test coverage:**
- Modal opening/closing
- Collections list display
- Adding to existing collection
- Creating new collection
- Form validation
- Error handling
- Loading states
- Keyboard navigation
- Accessibility

---

## Design Patterns

**State Management:**
- React Query for server state
- Local state for UI (view mode, form values)
- Controlled modal (open state from parent)

**Error Handling:**
- 409 Conflict: "Already in collection" message
- Network errors: Generic error toast
- Validation errors: Inline field errors

**UX Optimizations:**
- Auto-focus on form inputs
- Loading states on buttons
- Disabled state during operations
- Auto-close after success (500ms delay)
- Keyboard navigation support

**Accessibility:**
- ARIA labels on all interactive elements
- Proper focus management
- Error messages with role="alert"
- Keyboard-friendly (Escape to close, Tab navigation)

---

## Future Enhancements

- [ ] Keyboard shortcuts (1-5 for quick collection selection)
- [ ] Search/filter collections when list is long
- [ ] Bulk add (multiple listings at once)
- [ ] Recent collections based on usage, not just creation date
- [ ] Collection preview on hover
- [ ] Drag-and-drop to add to collection
