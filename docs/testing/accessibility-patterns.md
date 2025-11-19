---
title: "Accessibility Patterns Quick Reference"
description: "Common accessible component patterns used in Deal Brain"
audience: [developers, ai-agents]
tags: [accessibility, patterns, components, reference]
created: 2025-11-18
updated: 2025-11-18
category: "developer-documentation"
status: published
related:
  - /docs/testing/accessibility-testing-guide.md
  - /docs/testing/accessibility-checklist.md
---

# Accessibility Patterns Quick Reference

Common accessible component patterns for Deal Brain components.

---

## Buttons

### Icon-Only Button

```tsx
// ❌ Bad - No accessible name
<button>
  <ShareIcon />
</button>

// ✅ Good - aria-label provides name
<button aria-label="Share this listing">
  <ShareIcon />
</button>

// ✅ Also Good - visually hidden text
<button>
  <ShareIcon />
  <span className="sr-only">Share this listing</span>
</button>
```

### Button with Loading State

```tsx
<button
  disabled={isLoading}
  aria-busy={isLoading}
  aria-label={isLoading ? "Loading..." : "Save collection"}
>
  {isLoading ? <Spinner /> : "Save"}
</button>
```

### Toggle Button

```tsx
const [isTableView, setIsTableView] = useState(false);

<button
  onClick={() => setIsTableView(!isTableView)}
  aria-pressed={isTableView}
  aria-label="Toggle table view"
>
  <TableIcon />
</button>
```

---

## Links

### External Link

```tsx
// ✅ Good - indicates external link
<a
  href="https://example.com"
  target="_blank"
  rel="noopener noreferrer"
  aria-label="View product on Amazon (opens in new tab)"
>
  View product
  <ExternalLinkIcon aria-hidden="true" />
</a>
```

### Navigation Link

```tsx
// ✅ Good - clear destination
<Link href="/collections" aria-label="View all collections">
  Collections
</Link>
```

---

## Forms

### Text Input with Label

```tsx
// ✅ Good - explicit association
<div>
  <label htmlFor="collectionName">Collection Name</label>
  <input
    type="text"
    id="collectionName"
    name="name"
    aria-required="true"
  />
</div>
```

### Input with Error

```tsx
const [error, setError] = useState<string | null>(null);

<div>
  <label htmlFor="email">Email</label>
  <input
    type="email"
    id="email"
    aria-invalid={!!error}
    aria-describedby={error ? "email-error" : undefined}
  />
  {error && (
    <p id="email-error" role="alert" className="text-red-600">
      {error}
    </p>
  )}
</div>
```

### Checkbox with Label

```tsx
// ✅ Good - wrapping label
<label className="flex items-center gap-2 cursor-pointer">
  <input
    type="checkbox"
    checked={isSelected}
    onChange={(e) => setIsSelected(e.target.checked)}
  />
  <span>Add to wishlist</span>
</label>

// ✅ Also Good - explicit association
<div>
  <input
    type="checkbox"
    id="wishlist"
    checked={isSelected}
    onChange={(e) => setIsSelected(e.target.checked)}
  />
  <label htmlFor="wishlist">Add to wishlist</label>
</div>
```

### Select Dropdown

```tsx
<div>
  <label htmlFor="sortBy">Sort by</label>
  <select id="sortBy" name="sortBy" aria-label="Sort listings by">
    <option value="price">Price</option>
    <option value="score">Score</option>
    <option value="date">Date added</option>
  </select>
</div>
```

---

## Modals (Dialogs)

### Basic Modal (Radix UI)

```tsx
import { Dialog } from "@radix-ui/react-dialog";

<Dialog.Root open={open} onOpenChange={setOpen}>
  <Dialog.Trigger asChild>
    <button aria-label="Open share options">Share</button>
  </Dialog.Trigger>

  <Dialog.Portal>
    <Dialog.Overlay className="fixed inset-0 bg-black/50" />
    <Dialog.Content
      className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
      aria-describedby="dialog-description"
    >
      <Dialog.Title>Share Listing</Dialog.Title>
      <Dialog.Description id="dialog-description">
        Share this listing with others via link or email.
      </Dialog.Description>

      {/* Modal content */}

      <Dialog.Close asChild>
        <button aria-label="Close modal">
          <XIcon />
        </button>
      </Dialog.Close>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
```

**Note**: Radix UI Dialog automatically handles:
- `role="dialog"`
- `aria-modal="true"`
- Focus trapping
- Focus restoration on close
- Escape key to close

---

## Images

### Product Image

```tsx
// ✅ Good - meaningful alt text
<img
  src={listing.thumbnail_url}
  alt={`${listing.title} - ${listing.cpu_name}`}
/>
```

### Decorative Image

```tsx
// ✅ Good - empty alt for decorative images
<img
  src="/images/decorative-pattern.svg"
  alt=""
  aria-hidden="true"
/>
```

### Image with Fallback

```tsx
<img
  src={listing.thumbnail_url || "/images/fallbacks/generic-pc.svg"}
  alt={listing.title}
  onError={(e) => {
    e.currentTarget.src = "/images/fallbacks/generic-pc.svg";
  }}
/>
```

---

## Lists

### Collection List

```tsx
<div role="region" aria-label="Collections">
  <ul className="grid grid-cols-3 gap-4">
    {collections.map((collection) => (
      <li key={collection.id}>
        <article>
          <h3>
            <Link href={`/collections/${collection.id}`}>
              {collection.name}
            </Link>
          </h3>
          <p>{collection.item_count} items</p>
        </article>
      </li>
    ))}
  </ul>
</div>
```

---

## Tables

### Data Table

```tsx
<table>
  <caption className="sr-only">Collection items</caption>
  <thead>
    <tr>
      <th scope="col">Title</th>
      <th scope="col">CPU</th>
      <th scope="col">Price</th>
      <th scope="col">Score</th>
      <th scope="col">Actions</th>
    </tr>
  </thead>
  <tbody>
    {items.map((item) => (
      <tr key={item.id}>
        <td>{item.title}</td>
        <td>{item.cpu_name}</td>
        <td>${item.price_usd}</td>
        <td>{item.score_composite?.toFixed(2)}</td>
        <td>
          <button aria-label={`Remove ${item.title} from collection`}>
            <TrashIcon />
          </button>
        </td>
      </tr>
    ))}
  </tbody>
</table>
```

### Sortable Table Headers

```tsx
<th scope="col">
  <button
    onClick={() => handleSort('price')}
    aria-sort={sortColumn === 'price' ? sortDirection : 'none'}
    aria-label={`Sort by price ${sortColumn === 'price' ? sortDirection : ''}`}
  >
    Price
    {sortColumn === 'price' && (
      <SortIcon direction={sortDirection} aria-hidden="true" />
    )}
  </button>
</th>
```

---

## Loading States

### Loading Spinner

```tsx
<div role="status" aria-live="polite" aria-label="Loading collections">
  <Spinner aria-hidden="true" />
  <span className="sr-only">Loading collections...</span>
</div>
```

### Skeleton Loading

```tsx
<div
  className="h-40 rounded-lg border bg-card animate-pulse"
  aria-label="Loading collection"
  aria-busy="true"
/>
```

---

## Live Regions (Dynamic Content)

### Toast Notification

```tsx
import { Toast } from "@radix-ui/react-toast";

<Toast.Root>
  <Toast.Title>Success</Toast.Title>
  <Toast.Description>
    Collection created successfully
  </Toast.Description>
</Toast.Root>
```

**Note**: Radix UI Toast automatically uses `role="status"` and `aria-live="polite"`

### Error Message

```tsx
<div role="alert" aria-live="assertive">
  <AlertCircleIcon aria-hidden="true" />
  Failed to load collections. Please try again.
</div>
```

---

## Cards

### Collection Card

```tsx
<article className="border rounded-lg p-4">
  <h3 className="text-lg font-semibold">
    <Link
      href={`/collections/${collection.id}`}
      className="hover:underline focus:outline-none focus:ring-2 focus:ring-primary"
    >
      {collection.name}
    </Link>
  </h3>
  <p className="text-sm text-muted-foreground">
    {collection.item_count} items
  </p>
  <div className="mt-4 flex gap-2">
    <button aria-label={`Edit ${collection.name}`}>
      <EditIcon />
    </button>
    <button aria-label={`Delete ${collection.name}`}>
      <TrashIcon />
    </button>
  </div>
</article>
```

---

## Navigation

### Skip Links

```tsx
// Place at top of layout
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50"
>
  Skip to main content
</a>

// Main content
<main id="main-content">
  {/* Page content */}
</main>
```

### Breadcrumbs

```tsx
<nav aria-label="Breadcrumb">
  <ol className="flex items-center gap-2">
    <li>
      <Link href="/collections">Collections</Link>
    </li>
    <li aria-hidden="true">/</li>
    <li>
      <Link href={`/collections/${id}`} aria-current="page">
        {collection.name}
      </Link>
    </li>
  </ol>
</nav>
```

---

## Focus Management

### Focus Visible (Tailwind)

```tsx
// ✅ Good - visible focus indicator
<button className="
  px-4 py-2 rounded
  focus:outline-none
  focus:ring-2
  focus:ring-primary
  focus:ring-offset-2
">
  Click me
</button>
```

### Skip Focus for Mouse Users

```tsx
// ✅ Good - only show focus for keyboard users
<button className="
  px-4 py-2 rounded
  focus-visible:outline-none
  focus-visible:ring-2
  focus-visible:ring-primary
">
  Click me
</button>
```

---

## Screen Reader Only Content

### Visually Hidden Class

```css
/* globals.css or tailwind.config.js */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: inherit;
  margin: inherit;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

### Usage

```tsx
<button>
  <ShareIcon />
  <span className="sr-only">Share this listing</span>
</button>
```

---

## Color Contrast

### Tailwind Colors (WCAG AA Compliant)

```tsx
// ✅ Good contrast (4.5:1+)
<p className="text-gray-900 dark:text-gray-100">
  Body text with good contrast
</p>

// ✅ Good contrast for large text (3:1+)
<h1 className="text-2xl text-gray-700 dark:text-gray-300">
  Large heading
</h1>

// ❌ Bad contrast (avoid)
<p className="text-gray-400">
  This text is too light (3.2:1 contrast)
</p>
```

### Button Contrast

```tsx
// ✅ Primary button (good contrast)
<Button variant="primary">
  {/* background: hsl(var(--primary)), text: hsl(var(--primary-foreground)) */}
  Submit
</Button>

// ✅ Outline button (good contrast)
<Button variant="outline">
  {/* border: 3:1+, text: 4.5:1+ */}
  Cancel
</Button>
```

---

## Touch Targets (Mobile)

### Minimum Size Button

```tsx
// ✅ Good - 44x44px minimum
<button className="min-h-[44px] min-w-[44px] p-3">
  <Icon />
</button>

// ✅ Good - text provides adequate size
<button className="px-4 py-3">
  Add to Collection
</button>
```

### Checkbox Touch Target

```tsx
// ✅ Good - label increases touch area
<label className="flex items-center gap-2 p-2 min-h-[44px] cursor-pointer">
  <input type="checkbox" className="w-5 h-5" />
  <span>Collection name</span>
</label>
```

---

## Keyboard Shortcuts

### Common Patterns

```tsx
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    // Close modal on Escape
    if (e.key === 'Escape' && isOpen) {
      setIsOpen(false);
    }

    // Submit form on Cmd/Ctrl+Enter
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleSubmit();
    }
  };

  document.addEventListener('keydown', handleKeyDown);
  return () => document.removeEventListener('keydown', handleKeyDown);
}, [isOpen]);
```

---

## Landmarks

### Page Structure

```tsx
<body>
  <a href="#main-content" className="sr-only focus:not-sr-only">
    Skip to main content
  </a>

  <header>
    <nav aria-label="Main navigation">
      {/* Navigation links */}
    </nav>
  </header>

  <main id="main-content">
    {/* Main page content */}
  </main>

  <aside aria-label="Filters">
    {/* Sidebar filters */}
  </aside>

  <footer>
    {/* Footer content */}
  </footer>
</body>
```

---

## Motion and Animations

### Respect Reduced Motion

```tsx
// CSS (globals.css)
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

// React Hook
import { useReducedMotion } from 'framer-motion';

function Component() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, scale: 1 }}
      transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3 }}
    >
      Content
    </motion.div>
  );
}
```

---

## Resources

- **Radix UI Primitives**: https://www.radix-ui.com/ (Accessible by default)
- **Tailwind CSS**: https://tailwindcss.com/docs/screen-readers
- **ARIA Authoring Practices**: https://www.w3.org/WAI/ARIA/apg/
- **WebAIM**: https://webaim.org/

---

## Quick Checklist

Before committing new components:

- [ ] All interactive elements keyboard accessible
- [ ] All images have alt text
- [ ] All form inputs have labels
- [ ] All buttons have accessible names
- [ ] Focus indicators visible
- [ ] Color contrast meets 4.5:1 (text) / 3:1 (UI)
- [ ] Touch targets ≥ 44x44px (mobile)
- [ ] No color-only information
- [ ] Proper heading hierarchy
- [ ] ARIA attributes used correctly

Run automated tests:
```bash
pnpm test:e2e:a11y
```

See full checklist: `docs/testing/accessibility-checklist.md`
