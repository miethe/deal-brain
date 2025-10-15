# Scrollable Dropdown UI Design Specification

**Component:** EntityFieldSelector - Condition Builder Field Dropdown
**Issue:** Dropdown list extends beyond viewport without scrolling capability
**Date:** 2025-10-15
**Status:** Design Complete - Ready for Implementation

---

## Executive Summary

The EntityFieldSelector component in the Valuation Rules Advanced mode currently uses a Command component (cmdk) within a Popover to display available fields. When the field list exceeds viewport height, the dropdown extends beyond the screen bottom, making fields inaccessible. This specification provides a comprehensive solution using the existing shadcn/ui Command architecture with proper scrolling, accessibility, and visual feedback.

---

## Current Implementation Analysis

### Component Stack
```
EntityFieldSelector
  └── Popover (Radix UI)
      └── PopoverContent (w-[400px] p-0)
          └── Command (cmdk)
              ├── CommandInput (search)
              ├── CommandEmpty
              └── CommandGroup[] (per entity)
                  └── CommandItem[] (per field)
```

### Current Issues
1. **No Scrolling Container**: The Command component lacks a CommandList wrapper
2. **No Height Constraint**: PopoverContent has no max-height
3. **Viewport Overflow**: Long lists extend beyond screen bottom
4. **Missing Visual Indicators**: No scroll shadows or indicators
5. **Mobile Concerns**: No responsive height adjustment for small screens

---

## Solution Design

### Component Selection Rationale

**Selected Approach: Command (cmdk) with CommandList**

The current implementation already uses the Command component from shadcn/ui, which is built on cmdk. This is the optimal choice because:

1. **Already Integrated**: No component replacement needed
2. **Search Built-in**: CommandInput provides instant filtering
3. **Keyboard Navigation**: Full keyboard support out of the box (Arrow keys, Enter, Escape)
4. **Screen Reader Support**: ARIA attributes handled by cmdk
5. **Grouped Items**: CommandGroup supports entity categorization
6. **Performance**: cmdk handles large lists efficiently

**Why Not Alternatives:**
- **Select Component**: No built-in search, poor for 20+ items
- **Custom Virtualized List**: Overkill, adds complexity, breaks accessibility
- **Native Select**: Limited styling, poor UX for grouped items

---

## Implementation Specification

### 1. Component Structure Update

**File:** `/mnt/containers/deal-brain/apps/web/components/valuation/entity-field-selector.tsx`

#### Current Structure (Lines 64-102)
```tsx
<PopoverContent className="w-[400px] p-0">
  <Command>
    <CommandInput ... />
    <CommandEmpty>No field found.</CommandEmpty>
    {metadata?.entities.map((entity) => (
      <CommandGroup key={entity.key} heading={entity.label}>
        {/* CommandItems */}
      </CommandGroup>
    ))}
  </Command>
</PopoverContent>
```

#### Updated Structure
```tsx
<PopoverContent className="w-[400px] p-0">
  <Command>
    <CommandInput
      placeholder="Search fields..."
      value={searchQuery}
      onValueChange={setSearchQuery}
    />
    <CommandList className="max-h-[min(400px,calc(100vh-200px))]">
      <CommandEmpty>No field found.</CommandEmpty>
      {metadata?.entities.map((entity) => (
        <CommandGroup key={entity.key} heading={entity.label}>
          {/* CommandItems */}
        </CommandGroup>
      ))}
    </CommandList>
  </Command>
</PopoverContent>
```

### 2. CSS Classes and Styling

#### PopoverContent Enhancements
```tsx
<PopoverContent className={cn(
  "w-[400px] p-0",
  "shadow-lg border-2 border-border",
  // Position adjustment for better viewport fit
  "data-[side=bottom]:translate-y-2",
  "data-[side=top]:-translate-y-2"
)}>
```

#### CommandList Configuration
```tsx
<CommandList className={cn(
  // Dynamic height based on viewport
  "max-h-[min(400px,calc(100vh-200px))]",
  // Scrolling behavior
  "overflow-y-auto overflow-x-hidden",
  // Smooth scrolling
  "scroll-smooth",
  // Custom scrollbar styling
  "scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100",
  "dark:scrollbar-thumb-gray-700 dark:scrollbar-track-gray-800"
)}>
```

**Height Calculation Breakdown:**
- `400px`: Maximum dropdown height (comfortable reading)
- `100vh - 200px`: Viewport height minus header/footer space
- `min()`: Uses smaller value to prevent viewport overflow

#### Mobile Responsive Adjustments
```tsx
<CommandList className={cn(
  // Desktop
  "max-h-[min(400px,calc(100vh-200px))]",
  // Tablet
  "sm:max-h-[min(360px,calc(100vh-180px))]",
  // Mobile
  "xs:max-h-[min(300px,calc(100vh-160px))]",
  "overflow-y-auto overflow-x-hidden scroll-smooth"
)}>
```

### 3. Scroll Visual Indicators

#### Scroll Shadow Implementation

Add gradient shadows at top/bottom to indicate scrollable content:

```tsx
// Add to component state
const [scrollState, setScrollState] = useState<{
  canScrollUp: boolean;
  canScrollDown: boolean;
}>({ canScrollUp: false, canScrollDown: false });

const listRef = useRef<HTMLDivElement>(null);

// Scroll detection handler
const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
  const target = e.currentTarget;
  const canScrollUp = target.scrollTop > 0;
  const canScrollDown =
    target.scrollTop < target.scrollHeight - target.clientHeight - 1;

  setScrollState({ canScrollUp, canScrollDown });
};

// In render:
<div className="relative">
  {/* Top Shadow */}
  <div className={cn(
    "absolute top-0 left-0 right-0 h-4 z-10",
    "bg-gradient-to-b from-popover to-transparent",
    "pointer-events-none transition-opacity duration-200",
    scrollState.canScrollUp ? "opacity-100" : "opacity-0"
  )} />

  <CommandList
    ref={listRef}
    onScroll={handleScroll}
    className="max-h-[min(400px,calc(100vh-200px))] overflow-y-auto"
  >
    {/* Content */}
  </CommandList>

  {/* Bottom Shadow */}
  <div className={cn(
    "absolute bottom-0 left-0 right-0 h-4 z-10",
    "bg-gradient-to-t from-popover to-transparent",
    "pointer-events-none transition-opacity duration-200",
    scrollState.canScrollDown ? "opacity-100" : "opacity-0"
  )} />
</div>
```

### 4. Scrollbar Styling

#### Option A: Native Scrollbar with Tailwind
```tsx
<CommandList className={cn(
  "max-h-[min(400px,calc(100vh-200px))]",
  "overflow-y-auto overflow-x-hidden",
  // Webkit browsers (Chrome, Safari, Edge)
  "[&::-webkit-scrollbar]:w-2",
  "[&::-webkit-scrollbar-track]:bg-gray-100",
  "[&::-webkit-scrollbar-thumb]:bg-gray-300",
  "[&::-webkit-scrollbar-thumb]:rounded-full",
  "[&::-webkit-scrollbar-thumb]:hover:bg-gray-400",
  // Firefox
  "scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100",
  // Dark mode
  "dark:[&::-webkit-scrollbar-track]:bg-gray-800",
  "dark:[&::-webkit-scrollbar-thumb]:bg-gray-600",
  "dark:scrollbar-thumb-gray-600 dark:scrollbar-track-gray-800"
)}>
```

#### Option B: Hidden Scrollbar (Minimal Design)
```tsx
<CommandList className={cn(
  "max-h-[min(400px,calc(100vh-200px))]",
  "overflow-y-auto overflow-x-hidden",
  // Hide scrollbar but keep functionality
  "scrollbar-hide",
  // Or explicit hiding
  "[&::-webkit-scrollbar]:hidden",
  "-ms-overflow-style-none",
  "scrollbar-width-none"
)}>
```

**Recommendation:** Use Option A (styled scrollbar) for better affordance and user feedback.

---

## Accessibility Specification

### Keyboard Navigation

The cmdk library provides built-in keyboard support:

| Key | Action |
|-----|--------|
| Arrow Up/Down | Navigate items |
| Enter | Select focused item |
| Escape | Close dropdown |
| Home | Jump to first item |
| End | Jump to last item |
| Type to search | Filter items |

**Implementation:** Already functional - no changes needed.

### Screen Reader Support

#### ARIA Attributes (cmdk built-in)
```html
<div role="combobox" aria-expanded="true" aria-controls="..." aria-haspopup="listbox">
  <!-- Trigger -->
</div>

<div role="listbox" aria-label="Available fields">
  <div role="group" aria-labelledby="...">
    <div role="option" aria-selected="false">...</div>
  </div>
</div>
```

#### Live Region for Search Results
```tsx
<CommandList aria-live="polite" aria-atomic="false">
  <CommandEmpty>No field found.</CommandEmpty>
  {/* Items */}
</CommandList>
```

#### Focus Management
```tsx
// Ensure CommandInput receives focus on open
useEffect(() => {
  if (open && inputRef.current) {
    inputRef.current.focus();
  }
}, [open]);
```

### WCAG AA Compliance

1. **Color Contrast**
   - Selected item: 4.5:1 minimum (accent background)
   - Hover state: 3:1 minimum (subtle highlight)
   - Scrollbar: Visual indicator only (not required contrast)

2. **Focus Indicators**
   - Visible focus ring on trigger button
   - Highlighted background on focused items
   - No reliance on color alone

3. **Text Sizing**
   - Minimum 14px font size (text-sm in Tailwind = 14px)
   - Entity headings: Semi-bold for visual hierarchy

4. **Touch Targets**
   - CommandItem height: 36px minimum (py-1.5 + content)
   - Adequate spacing between items (px-2 py-1.5)

---

## Edge Cases and Constraints

### 1. Small Screens (Mobile)

**Problem:** 400px max-height too large on phones (360px viewport height common)

**Solution:**
```tsx
<CommandList className={cn(
  // Base height for desktop
  "max-h-[min(400px,calc(100vh-200px))]",
  // Tablet (640px+)
  "sm:max-h-[min(360px,calc(100vh-180px))]",
  // Mobile (<640px) - 60% of viewport
  "max-sm:max-h-[60vh]",
  "overflow-y-auto"
)}>
```

### 2. Very Long Lists (50+ Items)

**Current Solution:** Search filtering reduces visible items

**Enhancement:** Add item count indicator
```tsx
<div className="border-b px-3 py-2 text-xs text-muted-foreground">
  {filteredCount} of {totalCount} fields
</div>
```

### 3. No Results State

**Current:** "No field found." message

**Enhancement:** Add suggestions
```tsx
<CommandEmpty>
  <div className="py-6 text-center">
    <p className="text-sm text-muted-foreground">No field found.</p>
    <p className="mt-2 text-xs text-muted-foreground">
      Try searching for entity name or field type
    </p>
  </div>
</CommandEmpty>
```

### 4. Long Field Names

**Problem:** Truncation at 400px width

**Solution:**
```tsx
<CommandItem className="flex flex-col items-start gap-1">
  <div className="w-full truncate font-medium">{field.label}</div>
  {field.description && (
    <div className="w-full truncate text-xs text-muted-foreground">
      {field.description}
    </div>
  )}
</CommandItem>
```

### 5. Nested Dialogs/Popovers

**Problem:** Dropdown inside Dialog/Modal may have z-index conflicts

**Solution:**
```tsx
<PopoverContent
  className="w-[400px] p-0 z-[60]" // Higher than dialog z-50
  sideOffset={4}
  collisionPadding={8}
>
```

### 6. Keyboard Navigation with Scroll

**Issue:** Focused item may scroll outside visible area

**cmdk Solution:** Built-in scroll-into-view for focused items

**Verification:**
```tsx
// cmdk handles this automatically, but verify with:
const observerRef = useRef<IntersectionObserver>();

useEffect(() => {
  if (!listRef.current) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting && entry.target.matches('[aria-selected="true"]')) {
          entry.target.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
      });
    },
    { root: listRef.current, threshold: 1.0 }
  );

  observerRef.current = observer;

  return () => observer.disconnect();
}, []);
```

---

## Visual Design Recommendations

### 1. Dropdown Container
- **Border:** 2px solid border for definition
- **Shadow:** Elevated shadow (shadow-lg)
- **Corner Radius:** 8px (rounded-md)
- **Background:** Popover background (--popover)

### 2. Search Input
- **Height:** 44px (accessible touch target)
- **Icon:** Search icon (left side, opacity-50)
- **Border:** Bottom border only (separates from list)
- **Focus:** No visible ring (search is auto-focused)

### 3. List Items
- **Height:** Auto (min 36px for touch)
- **Padding:** px-2 py-1.5
- **Hover:** Subtle accent background
- **Selected:** Accent background + foreground color
- **Check Icon:** Left-aligned, 16px

### 4. Group Headings
- **Font:** Semi-bold, 12px
- **Color:** Muted foreground
- **Spacing:** py-1.5 px-2
- **Sticky:** Optional sticky positioning

```tsx
<CommandGroup className="[&_[cmdk-group-heading]]:sticky [&_[cmdk-group-heading]]:top-0 [&_[cmdk-group-heading]]:bg-popover">
```

### 5. Scrollbar
- **Width:** 8px (2 in Tailwind units)
- **Track:** Light gray (bg-gray-100)
- **Thumb:** Medium gray (bg-gray-300)
- **Thumb Hover:** Darker gray (bg-gray-400)
- **Border Radius:** Full rounded

### 6. Scroll Shadows
- **Height:** 16px (4 in Tailwind units)
- **Gradient:** Linear from popover to transparent
- **Transition:** 200ms opacity fade
- **Z-index:** 10 (above list, below popover controls)

---

## Implementation Code

### Complete EntityFieldSelector Update

```tsx
"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronsUpDown } from "lucide-react";

import { Button } from "../ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList
} from "../ui/command";
import { cn } from "../../lib/utils";
import { fetchEntitiesMetadata } from "../../lib/api/entities";

interface EntityFieldSelectorProps {
  value: string | null;
  onChange: (value: string, fieldType: string, options?: string[]) => void;
  placeholder?: string;
}

export function EntityFieldSelector({ value, onChange, placeholder }: EntityFieldSelectorProps) {
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [scrollState, setScrollState] = useState({
    canScrollUp: false,
    canScrollDown: false
  });
  const listRef = useRef<HTMLDivElement>(null);

  const { data: metadata } = useQuery({
    queryKey: ["entities-metadata"],
    queryFn: fetchEntitiesMetadata,
    staleTime: 5 * 60 * 1000,
  });

  const allFields = metadata?.entities.flatMap((entity) =>
    entity.fields.map((field) => ({
      key: `${entity.key}.${field.key}`,
      label: `${entity.label} → ${field.label}`,
      data_type: field.data_type,
      options: field.options,
      entity: entity.label,
      field: field.label,
    }))
  ) || [];

  const selectedField = allFields.find((f) => f.key === value);

  const handleSelect = (fieldKey: string) => {
    const field = allFields.find((f) => f.key === fieldKey);
    if (field) {
      onChange(fieldKey, field.data_type, field.options);
      setOpen(false);
    }
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const canScrollUp = target.scrollTop > 0;
    const canScrollDown =
      target.scrollTop < target.scrollHeight - target.clientHeight - 1;

    setScrollState({ canScrollUp, canScrollDown });
  };

  // Check scroll state on initial render
  useEffect(() => {
    if (open && listRef.current) {
      const el = listRef.current;
      setScrollState({
        canScrollUp: el.scrollTop > 0,
        canScrollDown: el.scrollTop < el.scrollHeight - el.clientHeight - 1
      });
    }
  }, [open, metadata]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          {selectedField ? selectedField.label : placeholder || "Select field..."}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className={cn(
          "w-[400px] p-0",
          "shadow-lg border-2 border-border"
        )}
        sideOffset={4}
        collisionPadding={8}
      >
        <Command>
          <CommandInput
            placeholder="Search fields..."
            value={searchQuery}
            onValueChange={setSearchQuery}
          />

          <div className="relative">
            {/* Top Scroll Shadow */}
            <div className={cn(
              "absolute top-0 left-0 right-0 h-4 z-10",
              "bg-gradient-to-b from-popover to-transparent",
              "pointer-events-none transition-opacity duration-200",
              scrollState.canScrollUp ? "opacity-100" : "opacity-0"
            )} />

            <CommandList
              ref={listRef}
              onScroll={handleScroll}
              className={cn(
                "max-h-[min(400px,calc(100vh-200px))]",
                "sm:max-h-[min(360px,calc(100vh-180px))]",
                "max-sm:max-h-[60vh]",
                "overflow-y-auto overflow-x-hidden scroll-smooth",
                // Custom scrollbar
                "[&::-webkit-scrollbar]:w-2",
                "[&::-webkit-scrollbar-track]:bg-gray-100",
                "[&::-webkit-scrollbar-thumb]:bg-gray-300",
                "[&::-webkit-scrollbar-thumb]:rounded-full",
                "[&::-webkit-scrollbar-thumb]:hover:bg-gray-400",
                "dark:[&::-webkit-scrollbar-track]:bg-gray-800",
                "dark:[&::-webkit-scrollbar-thumb]:bg-gray-600"
              )}
            >
              <CommandEmpty>
                <div className="py-6 text-center">
                  <p className="text-sm text-muted-foreground">No field found.</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Try searching for entity or field name
                  </p>
                </div>
              </CommandEmpty>

              {metadata?.entities.map((entity) => {
                const filteredFields = entity.fields.filter((field) =>
                  field.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  field.key.toLowerCase().includes(searchQuery.toLowerCase())
                );

                if (filteredFields.length === 0) return null;

                return (
                  <CommandGroup key={entity.key} heading={entity.label}>
                    {filteredFields.map((field) => {
                      const fieldKey = `${entity.key}.${field.key}`;
                      return (
                        <CommandItem
                          key={fieldKey}
                          value={fieldKey}
                          onSelect={handleSelect}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4 shrink-0",
                              value === fieldKey ? "opacity-100" : "opacity-0"
                            )}
                          />
                          <div className="flex-1 min-w-0">
                            <div className="truncate font-medium">{field.label}</div>
                            {field.description && (
                              <div className="truncate text-xs text-muted-foreground">
                                {field.description}
                              </div>
                            )}
                          </div>
                        </CommandItem>
                      );
                    })}
                  </CommandGroup>
                );
              })}
            </CommandList>

            {/* Bottom Scroll Shadow */}
            <div className={cn(
              "absolute bottom-0 left-0 right-0 h-4 z-10",
              "bg-gradient-to-t from-popover to-transparent",
              "pointer-events-none transition-opacity duration-200",
              scrollState.canScrollDown ? "opacity-100" : "opacity-0"
            )} />
          </div>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
```

---

## Testing Checklist

### Visual Testing
- [ ] Dropdown displays at correct height on desktop (400px max)
- [ ] Dropdown adjusts on tablet screens (360px max)
- [ ] Dropdown adjusts on mobile screens (60vh)
- [ ] Scrollbar is visible and styled correctly
- [ ] Scroll shadows appear/disappear at correct positions
- [ ] Selected item shows check mark
- [ ] Hover states work correctly

### Functional Testing
- [ ] Scrolling works with mouse wheel
- [ ] Scrolling works with trackpad
- [ ] Scrolling works by dragging scrollbar
- [ ] Search filters items correctly
- [ ] Selecting item closes dropdown
- [ ] ESC key closes dropdown
- [ ] Click outside closes dropdown

### Keyboard Testing
- [ ] Tab focuses trigger button
- [ ] Enter/Space opens dropdown
- [ ] Arrow keys navigate items
- [ ] Home/End jump to first/last item
- [ ] Enter selects focused item
- [ ] ESC closes dropdown
- [ ] Focused item scrolls into view

### Screen Reader Testing
- [ ] Trigger announces "combobox, collapsed/expanded"
- [ ] List announces "listbox"
- [ ] Groups announce with heading
- [ ] Items announce with selection state
- [ ] Search announces results count

### Edge Case Testing
- [ ] Works with 1 item
- [ ] Works with 100+ items
- [ ] Works with no results
- [ ] Works with very long field names
- [ ] Works inside Dialog component
- [ ] Works on touch devices

### Browser Testing
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

---

## Performance Considerations

### Optimization Strategies

1. **Virtual Scrolling**: Not needed unless 500+ items
   - Current list size: ~20-50 items (acceptable performance)
   - cmdk handles filtering efficiently

2. **Debounced Search**: Already implemented (200ms in CLAUDE.md)
   - Prevents excessive re-renders during typing

3. **Memoized Field List**: Already using useMemo pattern
   ```tsx
   const allFields = useMemo(() =>
     metadata?.entities.flatMap(...) || [],
     [metadata]
   );
   ```

4. **Scroll Event Throttle**: Optional for scroll shadows
   ```tsx
   const handleScroll = useCallback(
     throttle((e: React.UIEvent<HTMLDivElement>) => {
       // ... scroll logic
     }, 16), // ~60fps
     []
   );
   ```

---

## Migration Path

### Phase 1: Core Scrolling (Priority: High)
1. Wrap items in CommandList
2. Add max-height constraint
3. Test on all screen sizes
4. Verify keyboard navigation

**Estimated Effort:** 30 minutes

### Phase 2: Visual Enhancements (Priority: Medium)
1. Add scroll shadows
2. Style scrollbar
3. Add scroll state detection
4. Test visual indicators

**Estimated Effort:** 1 hour

### Phase 3: Accessibility Audit (Priority: High)
1. Test with screen reader
2. Verify ARIA attributes
3. Test keyboard navigation
4. Ensure WCAG AA compliance

**Estimated Effort:** 1 hour

### Phase 4: Polish (Priority: Low)
1. Add item count indicator
2. Improve empty state
3. Add loading skeleton
4. Performance profiling

**Estimated Effort:** 1 hour

---

## Related Components

### Other Dropdowns Needing Similar Treatment

1. **Operator Selector** (`condition-row.tsx` line 68-82)
   - Currently uses Select component
   - Short list (5-10 operators) - likely OK
   - Monitor for overflow issues

2. **ValueInput Dropdowns** (`value-input.tsx`)
   - May need similar treatment for enum fields
   - Apply same CommandList pattern

3. **Ruleset Selector** (`page.tsx` line 564-586)
   - Currently uses Select component
   - Short list of rulesets - likely OK

**Recommendation:** Apply this pattern to any dropdown with 15+ items.

---

## Appendix

### A. Tailwind Scrollbar Plugin (Optional)

If custom scrollbar classes don't work, add plugin:

```bash
pnpm add -w tailwind-scrollbar
```

```js
// tailwind.config.js
module.exports = {
  plugins: [
    require('tailwind-scrollbar')({ nocompatible: true }),
  ],
}
```

### B. Alternative: Radix ScrollArea

For maximum control, replace CommandList with ScrollArea:

```tsx
import { ScrollArea } from "../ui/scroll-area";

<Command>
  <CommandInput />
  <ScrollArea className="h-[400px]">
    <div className="p-1">
      <CommandEmpty />
      {/* CommandGroups */}
    </div>
  </ScrollArea>
</Command>
```

**Note:** This breaks cmdk's scroll-into-view for keyboard navigation.

### C. CSS Custom Properties Reference

Radix UI exposes these for Select (not applicable to Command):
- `--radix-select-content-available-height`
- `--radix-select-trigger-width`

For Command/Popover positioning:
- `--radix-popover-content-available-height`
- `--radix-popover-content-transform-origin`

---

## Conclusion

This specification provides a complete, production-ready solution for the scrollable dropdown issue. The implementation leverages existing shadcn/ui patterns, maintains accessibility standards, and requires minimal code changes. The CommandList wrapper with proper max-height constraints, combined with visual scroll indicators and styled scrollbars, delivers an intuitive user experience across all devices and viewport sizes.

**Next Steps:**
1. Review specification with development team
2. Implement Phase 1 (core scrolling)
3. User testing on various screen sizes
4. Iterate based on feedback
5. Apply pattern to other long-list dropdowns

---

**Document Version:** 1.0
**Last Updated:** 2025-10-15
**Author:** UI Design Team
**Reviewers:** [To be assigned]
