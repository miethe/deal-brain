# Help Text Library

Centralized help text configuration for Deal Brain features. This directory contains all tooltips, empty states, error messages, and contextual help text used throughout the application.

## Purpose

- **Consistency**: Single source of truth for all help text across the application
- **Maintainability**: Easy to update help text without hunting through component files
- **i18n Ready**: Centralized strings make future internationalization straightforward
- **Type Safety**: TypeScript types ensure correct usage of help text keys
- **Documentation**: Self-documenting with clear descriptions and examples

## Files

### `cpu-catalog-help.ts`

Comprehensive help text for the CPU Catalog feature including:

- **Metric Tooltips**: Explanations for all performance metrics, specs, and badges
- **Filter Help**: Descriptions for all filter controls
- **Empty States**: Messages for no results, no data, etc.
- **Error Messages**: Actionable error messages with recovery options
- **Info Banners**: Contextual guidance and tips
- **View Descriptions**: Help text for different view modes
- **Chart Descriptions**: Explanations for analytics charts
- **Helper Functions**: Utilities for accessing help text

## Usage Examples

### Tooltips

```typescript
import { METRIC_TOOLTIPS, getMetricTooltip } from '@/lib/help-text/cpu-catalog-help';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

// Direct usage
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger>{cpuMark}</TooltipTrigger>
    <TooltipContent>
      <div>
        <strong>{METRIC_TOOLTIPS.cpuMark.title}</strong>
        <p>{METRIC_TOOLTIPS.cpuMark.content}</p>
      </div>
    </TooltipContent>
  </Tooltip>
</TooltipProvider>

// Using helper function
const tooltip = getMetricTooltip('cpuMark');
<TooltipContent>
  <div>
    <strong>{tooltip.title}</strong>
    <p>{tooltip.content}</p>
  </div>
</TooltipContent>
```

### Filter Help

```typescript
import { FILTER_HELP } from '@/lib/help-text/cpu-catalog-help';
import { HelpCircle } from 'lucide-react';

<div className="flex items-center gap-2">
  <Label>{FILTER_HELP.socket.label}</Label>
  <Tooltip>
    <TooltipTrigger>
      <HelpCircle className="h-4 w-4 text-muted-foreground" />
    </TooltipTrigger>
    <TooltipContent>
      <p>{FILTER_HELP.socket.help}</p>
    </TooltipContent>
  </Tooltip>
</div>
```

### Empty States

```typescript
import { EMPTY_STATES } from '@/lib/help-text/cpu-catalog-help';
import { Button } from '@/components/ui/button';

{cpus.length === 0 && (
  <div className="text-center py-12">
    <h3 className="text-lg font-semibold">{EMPTY_STATES.noResults.title}</h3>
    <p className="text-muted-foreground mt-2">{EMPTY_STATES.noResults.message}</p>
    {EMPTY_STATES.noResults.action && (
      <Button onClick={clearFilters} className="mt-4">
        {EMPTY_STATES.noResults.action}
      </Button>
    )}
  </div>
)}
```

### Error Messages

```typescript
import { ERROR_MESSAGES } from '@/lib/help-text/cpu-catalog-help';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

{error && (
  <Alert variant="destructive">
    <AlertTitle>{ERROR_MESSAGES.loadCPUsFailed.title}</AlertTitle>
    <AlertDescription>
      {ERROR_MESSAGES.loadCPUsFailed.message}
    </AlertDescription>
    <Button onClick={retry} className="mt-2">
      {ERROR_MESSAGES.loadCPUsFailed.action}
    </Button>
  </Alert>
)}
```

### Info Banners

```typescript
import { INFO_BANNERS } from '@/lib/help-text/cpu-catalog-help';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { InfoIcon } from 'lucide-react';

const banner = INFO_BANNERS.priceTargetsExplanation;

<Alert variant={banner.variant}>
  <InfoIcon className="h-4 w-4" />
  <AlertTitle>{banner.title}</AlertTitle>
  <AlertDescription>{banner.message}</AlertDescription>
</Alert>
```

### Helper Functions

```typescript
import {
  getConfidenceTooltip,
  getPerformanceValueTooltip,
} from '@/lib/help-text/cpu-catalog-help';

// Get confidence tooltip dynamically
const confidenceTooltip = getConfidenceTooltip(cpu.confidence);
<TooltipContent>
  <div>
    <strong>{confidenceTooltip.title}</strong>
    <p>{confidenceTooltip.content}</p>
  </div>
</TooltipContent>

// Get performance value tooltip dynamically
const valueTooltip = getPerformanceValueTooltip(cpu.performance_value_rating);
<TooltipContent>
  <div>
    <strong>{valueTooltip.title}</strong>
    <p>{valueTooltip.content}</p>
  </div>
</TooltipContent>
```

## Type Safety

All help text keys are exported as TypeScript types for type-safe usage:

```typescript
import type {
  MetricTooltipKey,
  FilterHelpKey,
  EmptyStateKey,
  ErrorMessageKey,
  InfoBannerKey,
} from '@/lib/help-text/cpu-catalog-help';

// Type-safe key usage
const tooltipKey: MetricTooltipKey = 'cpuMark'; // ✅ Valid
const tooltipKey: MetricTooltipKey = 'invalid'; // ❌ Type error

// Type-safe function parameters
function showTooltip(key: MetricTooltipKey) {
  const tooltip = METRIC_TOOLTIPS[key];
  // ...
}

showTooltip('cpuMark'); // ✅ Valid
showTooltip('invalid'); // ❌ Type error
```

## Adding New Help Text

### 1. Add to Appropriate Section

```typescript
// In cpu-catalog-help.ts

export const METRIC_TOOLTIPS = {
  // ... existing tooltips
  newMetric: {
    title: "New Metric Title",
    content: "Clear, concise explanation of the metric in 1-3 sentences.",
  },
} as const;
```

### 2. Update Types (Automatic)

TypeScript will automatically infer the new key in the exported types. No manual type updates needed!

### 3. Use in Components

```typescript
import { METRIC_TOOLTIPS } from '@/lib/help-text/cpu-catalog-help';

<TooltipContent>
  <div>
    <strong>{METRIC_TOOLTIPS.newMetric.title}</strong>
    <p>{METRIC_TOOLTIPS.newMetric.content}</p>
  </div>
</TooltipContent>
```

## Best Practices

### Writing Help Text

1. **Be Concise**: 1-3 sentences per help text
2. **Be Actionable**: Tell users what to do next, not just what went wrong
3. **Be Friendly**: Conversational tone, avoid jargon
4. **Be Informative**: Explain "why" not just "what"
5. **Be Consistent**: Use similar structure across all help texts

### Good Examples

```typescript
// ✅ Good: Concise, actionable, explains "why"
{
  title: "TDP (Thermal Design Power)",
  content: "Maximum heat output in watts. Lower TDP means less power consumption and heat, but may limit performance. Consider your cooling solution and power budget.",
}

// ❌ Bad: Too verbose, technical jargon
{
  title: "Thermal Design Power",
  content: "The thermal design power (TDP) is a metric used to quantify the maximum amount of heat generated by a CPU that the cooling system in a computer is required to dissipate under any workload.",
}

// ✅ Good: Actionable error with clear next step
{
  title: "Failed to Load CPUs",
  message: "Unable to load CPU catalog. Please check your connection and try again.",
  action: "Retry",
}

// ❌ Bad: Vague, not actionable
{
  title: "Error",
  message: "Something went wrong.",
  action: "OK",
}
```

### Tooltip Structure

All tooltips should follow this structure:

```typescript
{
  title: "Short Title (1-5 words)",
  content: "1-3 sentence explanation. Include context and actionable guidance. Explain why it matters.",
}
```

### Empty State Structure

All empty states should follow this structure:

```typescript
{
  title: "Short Title (2-4 words)",
  message: "1-2 sentence explanation of why state is empty and what user can do.",
  action: "Action Button Text" | null, // null if no action available
}
```

### Error Message Structure

All error messages should follow this structure:

```typescript
{
  title: "Error Title (2-4 words)",
  message: "1-2 sentence explanation and actionable guidance.",
  action: "Recovery Action Text", // What user should do next
}
```

### Info Banner Structure

All info banners should follow this structure:

```typescript
{
  variant: "info" | "warning" | "tip", // Determines styling
  title: "Banner Title (2-5 words)",
  message: "1-3 sentence explanation or guidance.",
}
```

## Future i18n Support

This centralized structure is ready for internationalization:

```typescript
// Future i18n implementation (example)
import { useTranslation } from 'next-i18n';

const { t } = useTranslation('cpu-catalog-help');

// Instead of:
METRIC_TOOLTIPS.cpuMark.title

// Use:
t('metric_tooltips.cpu_mark.title')

// The centralized structure makes this migration straightforward:
// 1. Convert TypeScript objects to i18n JSON files
// 2. Replace direct imports with translation hooks
// 3. Keys remain the same (e.g., 'cpuMark' -> 'cpu_mark')
```

## Testing Help Text

### Visual Testing

1. **Tooltip Delay**: All tooltips use 300ms delay for better UX
2. **Accessibility**: Test with keyboard navigation (Tab, Enter, Escape)
3. **Screen Readers**: Verify tooltips are announced by screen readers
4. **Dark Mode**: Ensure help text is readable in dark mode

### Content Testing

1. **Spell Check**: Run spell check on all help text
2. **Link Validation**: Verify any links in help text are valid
3. **Technical Accuracy**: Verify metrics and specs are accurately described
4. **User Testing**: Get feedback from real users on clarity

## Related Documentation

- [CPU Catalog Implementation Plan](../../../../docs/project_plans/listings-enhancements-v3/listings-enhancements-v3.md)
- [Component Documentation](../../../components/README.md)
- [Design System](../../../components/ui/README.md)
- [Accessibility Guidelines](../../../../docs/development/accessibility.md)

## Questions?

For questions about help text or suggestions for improvements, see:
- [CPU Catalog Feature Team](mailto:team@dealbrain.com)
- [Documentation Best Practices](../../../../docs/development/documentation.md)
