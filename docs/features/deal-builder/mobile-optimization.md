---
title: "Deal Builder - Mobile Optimization"
description: "Responsive design documentation for Deal Builder including breakpoints, touch targets, and mobile-specific features"
audience: [developers, ai-agents, design]
tags: [mobile, responsive, ux, deal-builder, accessibility]
created: 2025-11-14
updated: 2025-11-14
category: "user-documentation"
status: published
related:
  - /docs/features/deal-builder/testing-guide.md
  - /docs/features/deal-builder/accessibility.md
---

# Deal Builder - Mobile Optimization

## Responsive Breakpoints

```css
/* Mobile: <768px */
- Single column layout
- Full-screen modals
- Scrollable valuation panel (not sticky)
- Saved builds 1 column grid

/* Tablet: 768px-1024px */
- 2 column layout for component selection
- 2 column saved builds grid
- Valuation panel still scrolls

/* Desktop: >1024px */
- 60/40 component/valuation split
- Sticky valuation panel (lg:sticky lg:top-6)
- 3 column saved builds grid
```

## Breakpoint Implementation

### Tailwind CSS Classes Used

**Mobile-First Approach**:
```tsx
// Default (mobile) → md (tablet) → lg (desktop)

// Example: Component Card Grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Single column mobile, 2 tablet, 3 desktop */}
</div>

// Example: Valuation Panel Sticky
<div className="lg:sticky lg:top-6">
  {/* Only sticky on large screens */}
</div>

// Example: Modal Full-Screen
<Dialog className="sm:max-w-[600px] w-full">
  {/* Full-width mobile, max-width tablet+ */}
</Dialog>
```

## Mobile-Specific Features

### Touch Targets
- All buttons minimum 44×44px (WCAG AA requirement)
- Adequate spacing between interactive elements (8px minimum)
- Large touch areas for component selection (full card clickable)
- Touch-friendly dropdowns and selects

**Implementation**:
```tsx
// Minimum touch target size
<Button className="min-h-[44px] min-w-[44px]">
  Click Me
</Button>

// Spacious component cards
<div className="p-4 rounded-lg border space-y-3">
  {/* Adequate padding for touch */}
</div>
```

### Component Selector Modal
- Full-screen on mobile (<768px)
- Scrollable component list with momentum scrolling
- Sticky search bar at top (position-sticky)
- Large, tappable component cards (min 60px height)
- Bottom sheet-style animation on mobile

**Modal Behavior**:
- Mobile: Slides up from bottom, full viewport height
- Tablet+: Centered dialog, max-width constrained
- Close button always accessible (top-right)
- Background overlay prevents accidental clicks

### Valuation Panel
- **Desktop**: Sticky right column (follows scroll)
- **Mobile**: Normal scroll flow (no sticky positioning)
- All content accessible without horizontal scroll
- Collapsible sections for space efficiency

**Responsive Layout**:
```tsx
// Desktop: Sidebar layout
<div className="lg:flex lg:gap-6">
  {/* Component selection - 60% width */}
  <div className="lg:w-3/5">
    {componentCards}
  </div>

  {/* Valuation panel - 40% width, sticky */}
  <div className="lg:w-2/5 lg:sticky lg:top-6">
    {valuationPanel}
  </div>
</div>

// Mobile: Stacked layout
// valuation panel appears below component cards
```

## Mobile Performance Optimizations

### Image Loading
- Lazy loading for component images: `loading="lazy"`
- Responsive image sizes with `srcset`
- WebP format with fallback

### Debouncing & Throttling
- Search input: 200ms debounce
- Calculation API: 300ms debounce
- Scroll events: 100ms throttle (if used)

### Code Splitting
- Component modals lazy-loaded with `React.lazy()`
- Heavy libraries loaded on-demand
- Route-based code splitting via Next.js

### Network Efficiency
- API responses gzipped
- Minimal payload sizes (<10KB per request)
- Request batching where possible

## Testing Mobile Devices

### Recommended Test Devices
**iOS**:
- iPhone 13/14 Pro (Safari)
- iPhone SE (small screen test)
- iPad Pro (tablet test)

**Android**:
- Samsung Galaxy S21 (Chrome)
- Google Pixel 6 (Chrome)
- Various screen sizes (small, medium, large)

### Chrome DevTools Mobile Emulation
1. Open DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M / Cmd+Shift+M)
3. Select device preset:
   - iPhone 12 Pro (390×844)
   - iPad Air (820×1180)
   - Samsung Galaxy S20 (360×800)
4. Test touch events (enable touch simulation)
5. Throttle network (Fast 3G, Slow 3G)
6. Verify viewport meta tag

### Viewport Configuration
```html
<!-- apps/web/app/layout.tsx -->
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
```

## Mobile-Specific UI Patterns

### Bottom Sheet Modals
Component selection modal uses bottom sheet pattern on mobile:
- Slides up from bottom
- Dismissible via swipe down (future enhancement)
- Close button always visible
- Overlay backdrop

### Collapsible Sections
Valuation breakdown uses collapsible accordions:
- Conserves vertical space
- Tap header to expand/collapse
- Chevron icon indicates state
- Smooth animation

### Mobile Navigation
- Hamburger menu for app navigation (if applicable)
- Back button in header for sub-pages
- Breadcrumbs hidden on mobile (space constrained)

## Accessibility on Mobile

### Screen Reader Support
- iOS VoiceOver tested
- Android TalkBack tested
- Swipe gestures work with screen readers
- Focus order logical (top to bottom)

### High Contrast Mode
- Respects system preferences
- Borders visible in high contrast
- Text remains readable

### Text Sizing
- Supports iOS Dynamic Type
- Text scales to 200% without breaking layout
- Minimum 16px font size (prevents zoom on iOS)

## Known Mobile Issues

None currently. All layouts tested and responsive.

## Mobile-Specific Edge Cases

### Keyboard Behavior
- Input focus doesn't scroll content off-screen
- Keyboard dismisses when tapping outside
- Done/Next buttons work correctly
- No viewport shifting when keyboard appears

### Orientation Changes
- Portrait → Landscape: Layout adapts
- No content cut off
- Sticky elements recalculate position
- Modals remain centered

### Touch vs. Click
- All hover states have touch equivalents
- No hover-only UI (e.g., tooltips on hover)
- Tooltips appear on tap/focus
- Long-press gestures avoided (conflicts with system)

## Future Mobile Enhancements

1. **PWA Support**:
   - Add service worker
   - Offline capability
   - Add to home screen
   - Push notifications

2. **Touch Gestures**:
   - Swipe to dismiss modals
   - Pull to refresh saved builds
   - Swipe between component types

3. **Native App Feel**:
   - Haptic feedback on interactions
   - Smooth animations (60fps)
   - Bottom tab navigation
   - Native-like transitions

4. **Mobile-Specific Features**:
   - Camera barcode scanner (for components)
   - Voice input for search
   - Share via native share sheet
   - Copy to clipboard with native toast

## Testing Checklist

- [ ] All breakpoints tested (mobile, tablet, desktop)
- [ ] Touch targets ≥44px
- [ ] No horizontal scroll
- [ ] Modals full-screen on mobile
- [ ] Sticky elements work correctly
- [ ] Images load efficiently
- [ ] Text readable at all sizes
- [ ] Forms usable with on-screen keyboard
- [ ] Orientation changes handled
- [ ] Performance acceptable on 3G

## Performance Targets (Mobile)

- First Contentful Paint: <2s
- Time to Interactive: <3s
- Largest Contentful Paint: <2.5s
- Cumulative Layout Shift: <0.1
- First Input Delay: <100ms

**Tested on**: iPhone 13 Pro, Samsung Galaxy S21, Slow 3G throttle

---

**Last Updated**: 2025-11-14
**Mobile Support**: iOS 14+, Android 10+
**Status**: Production ready
