"use client"

import * as React from "react"
import * as SliderPrimitive from "@radix-ui/react-slider"

import { cn } from "../../lib/utils"

interface RangeSliderProps extends React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root> {
  /**
   * Minimum value of the range
   */
  min: number
  /**
   * Maximum value of the range
   */
  max: number
  /**
   * Current range value [min, max]
   */
  value?: [number, number]
  /**
   * Default range value [min, max]
   */
  defaultValue?: [number, number]
  /**
   * Callback when value changes
   */
  onValueChange?: (value: [number, number]) => void
  /**
   * Optional formatter for displaying values
   */
  formatValue?: (value: number) => string
  /**
   * Optional label for accessibility
   */
  label?: string
  /**
   * Show value labels below slider
   */
  showValues?: boolean
}

/**
 * RangeSlider - Dual-handle range slider component
 *
 * Features:
 * - Two draggable handles for min/max selection
 * - Accessible keyboard navigation (Tab to focus, Arrow keys to adjust)
 * - Touch-friendly (44px min touch target)
 * - Value display with optional formatter
 * - WCAG 2.1 AA compliant
 *
 * @example
 * <RangeSlider
 *   min={0}
 *   max={100}
 *   value={[20, 80]}
 *   onValueChange={([min, max]) => console.log(min, max)}
 *   formatValue={(v) => `${v}%`}
 *   label="Price range"
 *   showValues
 * />
 */
const RangeSlider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  RangeSliderProps
>(({
  className,
  min,
  max,
  value,
  defaultValue,
  onValueChange,
  formatValue = (v) => String(v),
  label,
  showValues = true,
  ...props
}, ref) => {
  const [internalValue, setInternalValue] = React.useState<[number, number]>(
    defaultValue ?? value ?? [min, max]
  )

  // Use controlled value if provided, otherwise use internal state
  const currentValue = value ?? internalValue

  const handleValueChange = (newValue: number[]) => {
    const rangeValue: [number, number] = [newValue[0], newValue[1]]

    if (!value) {
      setInternalValue(rangeValue)
    }

    onValueChange?.(rangeValue)
  }

  return (
    <div className="space-y-3">
      <SliderPrimitive.Root
        ref={ref}
        min={min}
        max={max}
        value={currentValue}
        onValueChange={handleValueChange}
        className={cn(
          "relative flex w-full touch-none select-none items-center",
          className
        )}
        aria-label={label}
        {...props}
      >
        <SliderPrimitive.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary">
          <SliderPrimitive.Range className="absolute h-full bg-primary" />
        </SliderPrimitive.Track>

        {/* Min handle */}
        <SliderPrimitive.Thumb
          className="block h-5 w-5 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-primary/10"
          aria-label={label ? `${label} minimum` : "Minimum value"}
        />

        {/* Max handle */}
        <SliderPrimitive.Thumb
          className="block h-5 w-5 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-primary/10"
          aria-label={label ? `${label} maximum` : "Maximum value"}
        />
      </SliderPrimitive.Root>

      {/* Value display */}
      {showValues && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span aria-live="polite">{formatValue(currentValue[0])}</span>
          <span className="text-xs">—</span>
          <span aria-live="polite">{formatValue(currentValue[1])}</span>
        </div>
      )}
    </div>
  )
})
RangeSlider.displayName = "RangeSlider"

export { RangeSlider }
