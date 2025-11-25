# ADR-001: Product Image Component Architecture

**Date:** 2025-10-26
**Status:** Accepted
**Context:** Phase 3, TASK-010 - Create Product Image Component
**Decision Maker:** Lead Architect

---

## Context

The overview modal needs to display product images with a robust fallback hierarchy to handle missing or broken image URLs. The component must provide a good user experience even when listing images are unavailable.

## Decision

Implement a client-side `ProductImageDisplay` component with a 5-level fallback hierarchy, Next.js Image optimization, and Radix Dialog lightbox.

### Component Architecture

**Type:** Client-side component (`'use client'`)

**Rationale:**
- Image loading requires client-side state management for error tracking and loading states
- Lightbox interaction requires client-side event handling
- Error cascade through fallback hierarchy needs reactive state updates
- Next.js Image callbacks (`onError`, `onLoadingComplete`) only work client-side

### Fallback Hierarchy Strategy

**Approach:** Functional cascade with immediate fallback on error

**Hierarchy:**
1. `listing.thumbnail_url` or `listing.image_url` (external listing images)
2. `/public/images/manufacturers/{manufacturer}.svg` (manufacturer logo)
3. `/public/images/fallbacks/{cpu-manufacturer}-logo.svg` (Intel/AMD logo)
4. `/public/images/fallbacks/{form-factor}-icon.svg` (Mini PC, Desktop icon)
5. `/public/images/fallbacks/generic-pc.svg` (ultimate fallback)

**Implementation Pattern:**
```tsx
const [imageError, setImageError] = useState(false);

const getImageSrc = (): string => {
  // Level 1: Listing images (only if no error yet)
  if (!imageError && listing.thumbnail_url) return listing.thumbnail_url;
  if (!imageError && listing.image_url) return listing.image_url;

  // Level 2: Manufacturer logo
  if (listing.manufacturer) {
    return `/images/manufacturers/${slugify(listing.manufacturer)}.svg`;
  }

  // Level 3: CPU manufacturer logo
  if (listing.cpu?.manufacturer) {
    return `/images/fallbacks/${listing.cpu.manufacturer.toLowerCase()}-logo.svg`;
  }

  // Level 4: Form factor icon
  if (listing.form_factor) {
    return `/images/fallbacks/${slugify(listing.form_factor)}-icon.svg`;
  }

  // Level 5: Generic placeholder
  return '/images/fallbacks/generic-pc.svg';
};
```

**Rationale:**
- Simpler logic: compute fallback image synchronously based on error state
- Better performance: no sequential loading attempts (no cascade delays)
- Clearer code: single pure function determines image source
- Better UX: instant fallback, no waiting for cascading failures

**Alternative Considered:** State-based cascade with `currentLevel` counter
**Rejected Because:** Adds complexity, causes multiple re-renders, degrades UX with sequential loading delays

### Asset Management

**Asset Locations:**
- `/public/images/fallbacks/intel-logo.svg`
- `/public/images/fallbacks/amd-logo.svg`
- `/public/images/fallbacks/mini-pc-icon.svg`
- `/public/images/fallbacks/desktop-icon.svg`
- `/public/images/fallbacks/generic-pc.svg`
- `/public/images/manufacturers/{manufacturer}.svg` (dynamic)

**Naming Convention:**
- Lowercase, hyphen-separated slugs
- Consistent `.svg` format for scalability
- Manufacturer names transformed to slugs (e.g., "Lenovo IdeaCentre" → "lenovo-ideacentre.svg")

**Rationale:**
- Centralized fallback location for easy maintenance
- SVG format ensures crisp rendering at all sizes
- Predictable paths enable dynamic fallback construction

### Performance Strategy

**Optimization Techniques:**
- Next.js Image component with automatic WebP conversion
- Lazy loading for off-screen images
- `quality={85}` for balance between file size and visual quality
- `object-contain` to prevent distortion

**Configuration:**
```tsx
<Image
  src={imageSrc}
  alt={listing.title || 'Product image'}
  width={400}
  height={300}
  className="rounded-lg object-contain"
  loading="lazy"
  quality={85}
  onLoadingComplete={() => setIsLoading(false)}
  onError={() => setImageError(true)}
/>
```

**Performance Targets:**
- Lazy loading: Load only when in viewport
- WebP conversion: ~30-40% smaller than PNG/JPEG
- Core Web Vitals: No LCP impact from images
- < 200ms to display fallback on error

### Error Handling

**Approach:** Silent fallback cascade with optional development logging

**Pattern:**
```tsx
onError={() => {
  setImageError(true);
  if (process.env.NODE_ENV === 'development') {
    console.warn(`Image failed to load: ${imageSrc}`);
  }
}
```

**Rationale:**
- Users don't need error messages; they just need to see something
- Fallback cascade ensures a visual is always displayed
- Development logging helps identify missing assets
- Production analytics can track missing images for backfill

### Lightbox Interaction

**Approach:** Radix Dialog with full keyboard and accessibility support

**Pattern:**
```tsx
const [lightboxOpen, setLightboxOpen] = useState(false);

<div onClick={() => setLightboxOpen(true)} className="cursor-pointer">
  <Image ... />
</div>

<Dialog open={lightboxOpen} onOpenChange={setLightboxOpen}>
  <DialogContent className="max-w-4xl">
    <Image src={imageSrc} width={800} height={600} />
  </DialogContent>
</Dialog>
```

**Accessibility:**
- Radix Dialog provides WCAG-compliant keyboard navigation (Escape to close)
- Screen reader support built-in
- Backdrop click-outside to dismiss
- Focus trap within dialog when open

### Loading State

**Approach:** Skeleton loader with opacity transition

**Pattern:**
```tsx
{isLoading && <Skeleton className="w-full h-full absolute inset-0" />}
<Image
  className={cn("transition-opacity", isLoading && "opacity-0")}
  onLoadingComplete={() => setIsLoading(false)}
/>
```

**Rationale:**
- Reduces Cumulative Layout Shift (CLS metric)
- Provides visual feedback during load
- Smooth transition with CSS opacity animation
- Uses existing shadcn/ui Skeleton component

## Consequences

### Positive

- Robust fallback system ensures images always display
- Next.js Image optimization improves performance
- Accessible lightbox follows WCAG standards
- Development logging helps track missing assets
- Consistent with Deal Brain component patterns

### Negative

- Requires creation of fallback asset library (intel-logo.svg, etc.)
- Client-side component increases bundle size slightly
- Fallback assets must be maintained as new manufacturers are added

### Neutral

- Fallback hierarchy may show manufacturer logo for most listings (if external images are missing)
- Requires design team input for fallback SVG assets

## Implementation Files

**Created:**
- `apps/web/components/listings/product-image-display.tsx`

**Assets Required:**
- `public/images/fallbacks/intel-logo.svg`
- `public/images/fallbacks/amd-logo.svg`
- `public/images/fallbacks/mini-pc-icon.svg`
- `public/images/fallbacks/desktop-icon.svg`
- `public/images/fallbacks/generic-pc.svg`

**Modified:**
- `apps/web/components/listings/listing-overview-modal.tsx` (TASK-011)

## Related Documents

- **PRD:** `docs/project_plans/listings-facelift-enhancement/enhance-v2/prd-listings-facelift-v2.md` (FR-1)
- **Implementation Plan:** `docs/project_plans/listings-facelift-enhancement/enhance-v2/implementation-plan-v2-ph3-4.md` (TASK-010, TASK-011)
- **Next.js Image Docs:** https://nextjs.org/docs/app/api-reference/components/image

## Review Notes

- Approved by: Lead Architect
- Delegated to: `ui-engineer` subagent for implementation
- Blockers: Fallback SVG assets must be created before implementation can complete
