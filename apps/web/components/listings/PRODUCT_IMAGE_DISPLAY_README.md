# ProductImageDisplay Component

A reusable React component for displaying product images with a robust 5-level fallback hierarchy and lightbox functionality.

## Overview

The `ProductImageDisplay` component is designed for the Deal Brain listings enhancement project (Phase 3, TASK-010). It provides a consistent way to display product images with graceful degradation when images are unavailable or fail to load.

## Features

- **5-Level Fallback Hierarchy**: Ensures an image always displays, even when primary sources fail
- **Lightbox Support**: Click-to-expand functionality using Radix Dialog
- **Loading States**: Skeleton loader during image load
- **Error Handling**: Silent cascade to fallback levels on error
- **Accessibility**: Keyboard navigation, WCAG-compliant, screen reader support
- **Performance**: Lazy loading, Next.js Image optimization, proper caching
- **Responsive**: Adapts to different screen sizes

## Usage

```tsx
import { ProductImageDisplay } from '@/components/listings/product-image-display';

function MyComponent() {
  return (
    <ProductImageDisplay
      listing={{
        id: 1,
        thumbnail_url: 'https://example.com/image.jpg',
        image_url: 'https://example.com/fallback.jpg',
        manufacturer: 'Lenovo',
        cpu: { manufacturer: 'Intel' },
        form_factor: 'Mini PC',
        title: 'Lenovo ThinkCentre M75q',
      }}
      className="w-full max-w-md"
    />
  );
}
```

## Props

### `listing` (required)

An object containing the listing data with the following optional properties:

```typescript
interface ListingData {
  id?: number;
  thumbnail_url?: string | null;    // Primary image URL
  image_url?: string | null;         // Secondary image URL
  manufacturer?: string | null;       // Product manufacturer
  cpu?: {
    manufacturer?: string | null;    // CPU manufacturer (Intel, AMD, etc.)
  } | null;
  form_factor?: string | null;       // Form factor (Mini PC, Desktop, etc.)
  title?: string | null;             // Product title for alt text
}
```

### `className` (optional)

Additional CSS classes to apply to the component wrapper.

```tsx
<ProductImageDisplay
  listing={listing}
  className="w-full h-64 rounded-xl shadow-lg"
/>
```

## Fallback Hierarchy

The component uses a 6-level fallback strategy:

1. **`listing.thumbnail_url`** - Primary product image (external URL)
2. **`listing.image_url`** - Secondary product image (external URL)
3. **Manufacturer logo** - `/images/manufacturers/{manufacturer-slug}.svg`
4. **CPU manufacturer logo** - `/images/fallbacks/{cpu-manufacturer}-logo.svg` (intel or amd)
5. **Form factor icon** - `/images/fallbacks/{form-factor-slug}-icon.svg`
6. **Generic fallback** - `/images/fallbacks/generic-pc.svg`

### How Fallbacks Work

1. The component attempts to load `thumbnail_url` or `image_url` first
2. If loading fails (404, network error, etc.), `imageError` state is set to `true`
3. The `getImageSrc()` function re-evaluates and returns the next available fallback
4. The process continues until a valid image is found (generic-pc.svg always exists)

### Example Scenarios

**Scenario 1: External image available**
```
Input: listing.thumbnail_url = "https://ebay.com/item/123.jpg"
Result: External image displayed
```

**Scenario 2: External image fails, manufacturer known**
```
Input:
  - listing.thumbnail_url fails to load
  - listing.manufacturer = "Lenovo"
Result: /images/manufacturers/lenovo.svg displayed
```

**Scenario 3: No external image, Intel CPU**
```
Input:
  - listing.thumbnail_url = null
  - listing.image_url = null
  - listing.manufacturer = null
  - listing.cpu.manufacturer = "Intel Core i5"
Result: /images/cpu-vendors/intel.svg displayed
```

**Scenario 4: Everything fails**
```
Input: All properties are null/undefined
Result: /images/fallbacks/generic-pc.svg displayed
```

## Lightbox Feature

Clicking the image opens a full-screen lightbox using Radix Dialog:

- **Keyboard**: Press `Escape` to close
- **Mouse**: Click outside or close button to dismiss
- **Accessibility**: Focus trap, screen reader announcements
- **Size**: Max width 4xl (1200px), height 80vh

```tsx
// Lightbox opens automatically on click
<ProductImageDisplay listing={listing} />
```

## Accessibility

The component follows WCAG 2.1 AA standards:

- **Keyboard Navigation**: Click handler also supports `Enter` and `Space` keys
- **Focus Indicators**: Visual focus states for keyboard users
- **Screen Readers**: Proper ARIA labels and alt text
- **Semantic HTML**: Uses `role="button"` for clickable image container

### Keyboard Shortcuts

- `Enter` or `Space`: Open lightbox
- `Escape`: Close lightbox (when open)
- `Tab`: Navigate to/from component

## Performance

### Optimization Techniques

1. **Lazy Loading**: Images load only when in viewport
2. **Quality**: Set to 85% for balance between size and quality
3. **Next.js Image**: Automatic WebP conversion and responsive sizing
4. **Skeleton Loader**: Prevents layout shift during load

### Configuration

```tsx
<Image
  src={imageSrc}
  loading="lazy"           // Lazy load for off-screen images
  quality={85}             // 85% quality (good balance)
  width={400}              // Intrinsic width
  height={300}             // Intrinsic height
  sizes="..."              // Responsive sizing
/>
```

### Performance Metrics

- **LCP (Largest Contentful Paint)**: < 2.5s (lazy loading prevents main thread blocking)
- **CLS (Cumulative Layout Shift)**: 0 (skeleton prevents shift)
- **FCP (First Contentful Paint)**: Not affected (lazy loaded)

## Styling

The component uses Tailwind CSS utility classes:

```tsx
// Container
className="relative cursor-pointer group rounded-lg overflow-hidden bg-muted/30 border border-border"

// Image
className="rounded-lg object-contain transition-all duration-200 group-hover:opacity-90 group-hover:scale-[1.02]"

// Skeleton
className="w-full h-full absolute inset-0 rounded-lg"
```

### Customization

Override styles using the `className` prop:

```tsx
<ProductImageDisplay
  listing={listing}
  className="w-64 h-48 shadow-2xl rounded-2xl"
/>
```

## Error Handling

### Development Logging

In development mode, failed image loads are logged to the console:

```
[ProductImageDisplay] Image failed to load: https://example.com/missing.jpg
```

### Production Behavior

In production, errors are silently handled by falling back to the next level. No user-facing error messages are shown.

### Error Cascade Example

```
1. Try thumbnail_url → 404 Error → Set imageError=true
2. Re-render with getImageSrc() → Returns manufacturer logo
3. Try manufacturer logo → 404 Error → Set imageError=true (again)
4. Re-render with getImageSrc() → Returns CPU manufacturer logo
5. Try CPU manufacturer logo → Success → Display image
```

## Integration with Listing Overview Modal

The component is designed to be integrated into the `listing-overview-modal.tsx`:

```tsx
import { ProductImageDisplay } from "./product-image-display";

// In ListingOverviewModalComponent, after DialogHeader:
<DialogHeader>
  <DialogTitle className="text-xl">{listing.title}</DialogTitle>
</DialogHeader>

<ProductImageDisplay
  listing={listing}
  className="w-full max-w-md mx-auto mb-6"
/>

<div className="space-y-4">
  {/* Rest of modal content */}
</div>
```

## Testing

### Unit Tests

See `__tests__/product-image-display.test.tsx` for basic unit tests.

### Manual Testing Checklist

- [ ] Component renders without errors
- [ ] Image displays with `thumbnail_url`
- [ ] Fallback to `image_url` works
- [ ] Fallback to manufacturer logo works
- [ ] Fallback to CPU manufacturer logo works
- [ ] Fallback to form factor icon works
- [ ] Generic fallback displays
- [ ] Loading skeleton appears and disappears
- [ ] Error handling triggers fallback cascade
- [ ] Lightbox opens on click
- [ ] Lightbox closes on Escape key
- [ ] Keyboard navigation works (Enter/Space)
- [ ] No console warnings in production
- [ ] Images are lazy-loaded
- [ ] No layout shift on load

### Integration Tests

For full integration testing:

1. Mock Next.js Image component
2. Mock image load/error events
3. Test fallback cascade through all levels
4. Verify accessibility with axe-core
5. Test keyboard navigation
6. Verify lightbox functionality

## Dependencies

- `next/image` - Next.js Image optimization
- `@radix-ui/react-dialog` - Accessible dialog/lightbox
- `@/components/ui/dialog` - Radix Dialog wrapper
- `@/components/ui/skeleton` - Loading skeleton
- `@/lib/utils` - `cn()` utility for class merging

## Related Files

- **Component**: `/components/listings/product-image-display.tsx`
- **Tests**: `/components/listings/__tests__/product-image-display.test.tsx`
- **Assets**: `/public/images/fallbacks/*.svg`
- **Config**: `/next.config.mjs` (remote image patterns)
- **ADR**: `/docs/project_plans/listings-facelift-enhancement/enhance-v2/adrs/adr-001-product-image-component.md`
- **Implementation Plan**: `/docs/project_plans/listings-facelift-enhancement/enhance-v2/implementation-plan-v2-ph3-4.md`

## Next Steps (TASK-011)

The next task is to integrate this component into the `listing-overview-modal.tsx`:

1. Import the component
2. Add it after the `DialogHeader`
3. Adjust spacing and layout
4. Test with various listing types

## Troubleshooting

### Issue: Images not loading from external URLs

**Cause**: Next.js Image requires remote patterns configuration

**Solution**: Ensure `next.config.mjs` includes:
```js
images: {
  remotePatterns: [
    { protocol: 'https', hostname: '**' },
    { protocol: 'http', hostname: '**' },
  ],
}
```

### Issue: Fallback SVGs return 404

**Cause**: Missing fallback assets in `/public/images/fallbacks/`

**Solution**: Ensure all required SVG files exist:
- `intel-logo.svg`
- `amd-logo.svg`
- `mini-pc-icon.svg`
- `desktop-icon.svg`
- `generic-pc.svg`

### Issue: Component causes layout shift

**Cause**: Missing width/height on container

**Solution**: Always provide explicit dimensions via `className`:
```tsx
<ProductImageDisplay listing={listing} className="w-full h-64" />
```

## Contributing

When modifying this component:

1. Update tests in `__tests__/product-image-display.test.tsx`
2. Update this documentation
3. Update ADR-001 if architectural decisions change
4. Ensure TypeScript compilation succeeds
5. Test all fallback levels manually
6. Verify accessibility with screen readers

## License

Part of the Deal Brain project. See project root for license information.
