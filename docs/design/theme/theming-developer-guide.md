# Theming System - Developer Guide

**Version:** 1.0
**Last Updated:** 2025-10-04
**Maintainer:** Frontend Team

---

## Overview

Deal Brain implements a flexible, CSS variable-based theming system that supports multiple color themes with full dark mode support. The system is built on `next-themes` and uses HSL color values for maximum flexibility.

### Available Themes

1. **Light** (default) - Clean, bright interface with high contrast
2. **Dark** - High contrast dark theme for low-light environments
3. **Dark Soft** - Lower contrast dark theme, easier on eyes for extended use
4. **Light Blue** - Professional blue-tinted light theme
5. **System** - Automatically follows user's OS preference

---

## Architecture

### Technology Stack

- **Theme Provider**: `next-themes` v0.2.1
- **Styling**: Tailwind CSS v3.4.1 with CSS variables
- **Color Format**: HSL (Hue, Saturation, Lightness)
- **Component Library**: shadcn/ui with Radix UI primitives

### File Structure

```
apps/web/
├── app/
│   ├── globals.css           # Theme CSS variables and definitions
│   └── layout.tsx             # Root layout with suppressHydrationWarning
├── components/
│   ├── providers.tsx          # ThemeProvider setup
│   ├── app-shell.tsx          # Theme toggle integration
│   └── ui/
│       ├── theme-toggle.tsx   # Theme switcher component
│       └── dropdown-menu.tsx  # Menu component for theme selection
└── lib/
    └── valuation-utils.ts     # Theme-aware valuation colors
```

---

## Using the Theme System

### 1. Accessing Current Theme

```tsx
'use client';

import { useTheme } from 'next-themes';

export function MyComponent() {
  const { theme, setTheme, systemTheme } = useTheme();

  return (
    <div>
      <p>Current theme: {theme}</p>
      <p>System theme: {systemTheme}</p>
      <button onClick={() => setTheme('dark')}>Switch to Dark</button>
    </div>
  );
}
```

### 2. Using Semantic Colors

**Always prefer semantic color variables over hardcoded colors:**

```tsx
// ✅ Good - Uses semantic colors (adapts to theme)
<div className="bg-background text-foreground border-border">
  <h1 className="text-primary">Title</h1>
  <p className="text-muted-foreground">Subtitle</p>
</div>

// ❌ Bad - Hardcoded colors (won't adapt to theme)
<div className="bg-white text-gray-900 border-gray-200">
  <h1 className="text-blue-600">Title</h1>
  <p className="text-gray-500">Subtitle</p>
</div>
```

### 3. Available Semantic Colors

| Variable | Purpose | Example Usage |
|----------|---------|---------------|
| `--background` | Page background | `bg-background` |
| `--foreground` | Primary text | `text-foreground` |
| `--primary` | Primary actions | `bg-primary text-primary-foreground` |
| `--secondary` | Secondary actions | `bg-secondary text-secondary-foreground` |
| `--muted` | Muted backgrounds | `bg-muted text-muted-foreground` |
| `--accent` | Accent backgrounds | `bg-accent text-accent-foreground` |
| `--destructive` | Error states | `bg-destructive text-destructive-foreground` |
| `--success` | Success states | `bg-[hsl(var(--success))]` |
| `--border` | Borders | `border-border` |
| `--input` | Input borders | `border-input` |
| `--ring` | Focus rings | `ring-ring` |

### 4. Valuation Color System

Special CSS variables for pricing display:

```tsx
// Great deal colors (25%+ savings)
bg-[hsl(var(--valuation-great-deal-bg))]
text-[hsl(var(--valuation-great-deal-fg))]
border-[hsl(var(--valuation-great-deal-border))]

// Good deal colors (15-25% savings)
bg-[hsl(var(--valuation-good-deal-bg))]
text-[hsl(var(--valuation-good-deal-fg))]
border-[hsl(var(--valuation-good-deal-border))]

// Light savings (1-15%)
bg-[hsl(var(--valuation-light-saving-bg))]
text-[hsl(var(--valuation-light-saving-fg))]
border-[hsl(var(--valuation-light-saving-border))]

// Premium warning (10%+ markup)
bg-[hsl(var(--valuation-premium-bg))]
text-[hsl(var(--valuation-premium-fg))]
border-[hsl(var(--valuation-premium-border))]

// Light premium
bg-[hsl(var(--valuation-light-premium-bg))]
text-[hsl(var(--valuation-light-premium-fg))]
border-[hsl(var(--valuation-light-premium-border))]

// Neutral (no change)
bg-[hsl(var(--valuation-neutral-bg))]
text-[hsl(var(--valuation-neutral-fg))]
border-[hsl(var(--valuation-neutral-border))]
```

**Example usage:**

```tsx
import { getValuationStyle } from '@/lib/valuation-utils';

const style = getValuationStyle(deltaPercent, thresholds);
// Returns: className with theme-aware CSS variables
<Badge className={style.className}>-$50 (15%)</Badge>
```

---

## Adding Dark Mode Support to Components

### Method 1: Using Semantic Colors (Preferred)

```tsx
// Automatically adapts to all themes
<Card className="bg-card text-card-foreground border-border">
  <CardHeader>
    <CardTitle className="text-foreground">Title</CardTitle>
    <CardDescription className="text-muted-foreground">Description</CardDescription>
  </CardHeader>
</Card>
```

### Method 2: Tailwind Dark Variants (For Specific Colors)

```tsx
// Explicit dark mode override
<Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
  Active
</Badge>

// Multiple states
<Button className="bg-blue-500 hover:bg-blue-600 dark:bg-blue-700 dark:hover:bg-blue-800">
  Click Me
</Button>
```

### Method 3: CSS Variables (For Custom Colors)

```tsx
// Define in globals.css
:root {
  --custom-highlight: 45 100% 50%;
}

.dark {
  --custom-highlight: 45 80% 40%;
}

// Use in component
<div className="bg-[hsl(var(--custom-highlight))]">
  Custom colored element
</div>
```

---

## Creating a New Theme

### Step 1: Define Theme Variables

Add a new theme class in `apps/web/app/globals.css`:

```css
/* Example: High Contrast Theme */
.high-contrast {
  --background: 0 0% 100%;
  --foreground: 0 0% 0%;
  --muted: 0 0% 95%;
  --muted-foreground: 0 0% 20%;
  --accent: 0 0% 90%;
  --accent-foreground: 0 0% 10%;
  --popover: 0 0% 100%;
  --popover-foreground: 0 0% 0%;
  --card: 0 0% 100%;
  --card-foreground: 0 0% 0%;
  --border: 0 0% 0%;
  --input: 0 0% 0%;
  --primary: 221 100% 50%;
  --primary-foreground: 0 0% 100%;
  --secondary: 0 0% 85%;
  --secondary-foreground: 0 0% 0%;
  --destructive: 0 100% 50%;
  --destructive-foreground: 0 0% 100%;
  --success: 120 100% 40%;
  --success-foreground: 0 0% 100%;
  --ring: 221 100% 50%;

  /* Valuation colors */
  --valuation-great-deal-bg: 120 100% 30%;
  --valuation-great-deal-fg: 0 0% 100%;
  --valuation-great-deal-border: 120 100% 20%;

  /* ... define all valuation colors ... */
}
```

### Step 2: Add to Theme Toggle

Update `apps/web/components/ui/theme-toggle.tsx`:

```tsx
<DropdownMenuItem onClick={() => setTheme("high-contrast")}>
  <Contrast className="mr-2 h-4 w-4" />
  High Contrast
</DropdownMenuItem>
```

### Step 3: Test Accessibility

Verify WCAG AA contrast ratios:

```bash
# Minimum contrast ratios:
# - Normal text (< 18pt): 4.5:1
# - Large text (>= 18pt): 3:1
# - UI components: 3:1
```

Use browser DevTools or online tools:
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- Chrome DevTools > Accessibility > Contrast

---

## Best Practices

### 1. Always Use Semantic Colors

```tsx
// ✅ Adapts to all themes
className="bg-background text-foreground"

// ❌ Only works in light mode
className="bg-white text-black"
```

### 2. Provide Dark Variants for Fixed Colors

```tsx
// ✅ Works in all themes
className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200"

// ❌ Unreadable in dark mode
className="bg-emerald-100 text-emerald-800"
```

### 3. Use CSS Variables for Custom Colors

```tsx
// ✅ Theme-aware custom color
className="bg-[hsl(var(--custom-color))]"

// ❌ Not theme-aware
className="bg-[#3b82f6]"
```

### 4. Test All Themes

Before merging code, verify:
- [ ] Component displays correctly in Light theme
- [ ] Component displays correctly in Dark theme
- [ ] Component displays correctly in Dark Soft theme
- [ ] Component displays correctly in Light Blue theme
- [ ] Text is readable (contrast ratio ≥ 4.5:1)
- [ ] Focus states are visible
- [ ] Hover states are visible

### 5. Avoid Hardcoded Opacity

```tsx
// ✅ Theme-aware opacity
className="bg-primary/10"

// ✅ Explicit opacity with dark variant
className="bg-black/10 dark:bg-white/10"

// ❌ May not work in all themes
className="bg-black/10"
```

### 6. Handle Loading States

The theme may not be available during SSR. Use mounting check:

```tsx
'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export function ThemeAwareComponent() {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    // Return fallback or skeleton
    return <div className="h-10 w-10 bg-muted animate-pulse" />;
  }

  return <div>Current theme: {theme}</div>;
}
```

---

## Common Issues & Solutions

### Issue 1: Flash of Unstyled Content (FOUC)

**Problem:** Page flashes light theme before dark theme loads

**Solution:** Ensure `suppressHydrationWarning` is set in root layout:

```tsx
// apps/web/app/layout.tsx
<html lang="en" suppressHydrationWarning>
  {/* ... */}
</html>
```

### Issue 2: Theme Not Persisting

**Problem:** Theme resets to default on page reload

**Solution:** Verify `next-themes` is configured correctly:

```tsx
// apps/web/components/providers.tsx
<ThemeProvider attribute="class" defaultTheme="system" enableSystem>
  {children}
</ThemeProvider>
```

### Issue 3: Custom Colors Not Updating

**Problem:** Component colors don't change when switching themes

**Solution:** Use CSS variables instead of hardcoded Tailwind classes:

```tsx
// ❌ Won't update
className="bg-green-500"

// ✅ Updates with theme
className="bg-[hsl(var(--success))]"
```

### Issue 4: TypeScript Errors with useTheme

**Problem:** `'useTheme' can only be used in Client Components`

**Solution:** Add `'use client'` directive:

```tsx
'use client';

import { useTheme } from 'next-themes';
```

### Issue 5: Contrast Issues in Dark Mode

**Problem:** Text is hard to read in dark theme

**Solution:** Use proper foreground colors:

```tsx
// ❌ Low contrast in dark mode
className="text-gray-600"

// ✅ Theme-aware contrast
className="text-muted-foreground"
```

---

## API Reference

### `useTheme()` Hook

```tsx
import { useTheme } from 'next-themes';

const {
  theme,           // Current theme name ('light' | 'dark' | 'dark-soft' | 'light-blue' | 'system')
  setTheme,        // Function to change theme: (theme: string) => void
  systemTheme,     // User's system theme ('light' | 'dark')
  themes,          // Array of available theme names
  resolvedTheme,   // Resolved theme (if 'system', returns actual theme)
} = useTheme();
```

### ThemeProvider Props

```tsx
<ThemeProvider
  attribute="class"              // HTML attribute to set (class, data-theme, etc.)
  defaultTheme="system"          // Default theme if no preference stored
  enableSystem={true}            // Allow system theme
  enableColorScheme={false}      // Set color-scheme CSS property
  storageKey="theme"             // localStorage key
  themes={['light', 'dark']}     // Available themes (optional)
  disableTransitionOnChange      // Disable CSS transitions when changing theme
>
  {children}
</ThemeProvider>
```

---

## Migration Guide

### Migrating Existing Components

1. **Identify hardcoded colors**
   ```bash
   # Search for hardcoded Tailwind colors
   grep -r "bg-\(white\|black\|gray\|blue\|green\|red\)-[0-9]" apps/web/components/
   ```

2. **Replace with semantic colors**
   ```tsx
   // Before
   <div className="bg-white text-gray-900 border-gray-200">

   // After
   <div className="bg-background text-foreground border-border">
   ```

3. **Add dark variants for specific colors**
   ```tsx
   // Before
   <Badge className="bg-green-100 text-green-800">

   // After
   <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
   ```

4. **Test in all themes**
   - Use theme toggle to verify appearance
   - Check contrast ratios
   - Verify hover/focus states

---

## Performance Considerations

### CSS Variable Performance

CSS variables are extremely performant:
- ✅ Resolved at compile time (Tailwind JIT)
- ✅ No runtime JavaScript overhead
- ✅ Smooth theme transitions with CSS
- ✅ Browser-native implementation

### Bundle Size

Theme system impact:
- `next-themes`: ~2.3 KB gzipped
- CSS variables: ~1.5 KB (all themes)
- **Total overhead**: ~3.8 KB

### Optimization Tips

1. **Use arbitrary values sparingly**
   ```tsx
   // Good for theme-specific colors
   className="bg-[hsl(var(--custom-color))]"

   // Prefer Tailwind utilities when possible
   className="bg-primary"
   ```

2. **Avoid inline styles**
   ```tsx
   // ❌ No theme support
   <div style={{ backgroundColor: '#fff' }}>

   // ✅ Theme-aware
   <div className="bg-background">
   ```

3. **Memoize theme-dependent calculations**
   ```tsx
   const { theme } = useTheme();
   const themeConfig = useMemo(() => getConfigForTheme(theme), [theme]);
   ```

---

## Resources

### Internal Documentation
- [Theme Implementation Analysis](./theme-implementation-analysis.md)
- [Design Guidance](./design-guidance.md)

### External References
- [next-themes Documentation](https://github.com/pacocoursey/next-themes)
- [shadcn/ui Theming](https://ui.shadcn.com/docs/theming)
- [Tailwind CSS Dark Mode](https://tailwindcss.com/docs/dark-mode)
- [WCAG Color Contrast](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [HSL Color Picker](https://hslpicker.com/)

### Tools
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Accessible Colors](https://accessible-colors.com/)
- [Coolors Palette Generator](https://coolors.co/)

---

## Support

For questions or issues:
1. Check this documentation
2. Review [Theme Implementation Analysis](./theme-implementation-analysis.md)
3. Check existing components for patterns
4. Ask in #frontend-dev Slack channel

---

**Last Updated:** 2025-10-04
**Document Version:** 1.0
