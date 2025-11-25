"use client"

import { useState } from "react"
import { RangeSlider } from "./range-slider"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./card"

/**
 * RangeSlider Examples
 *
 * Demonstrates different use cases of the RangeSlider component
 */
export function RangeSliderExamples() {
  const [priceRange, setPriceRange] = useState<[number, number]>([200, 800])
  const [speedRange, setSpeedRange] = useState<[number, number]>([1.5, 4.2])
  const [ramRange, setRamRange] = useState<[number, number]>([8, 64])

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Price Range Filter</CardTitle>
          <CardDescription>
            Select a price range for filtering listings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <RangeSlider
            min={0}
            max={1000}
            value={priceRange}
            onValueChange={setPriceRange}
            formatValue={(v) => `$${v}`}
            label="Price range"
            showValues
          />
          <p className="text-sm text-muted-foreground">
            Current range: ${priceRange[0]} - ${priceRange[1]}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>CPU Speed Range (GHz)</CardTitle>
          <CardDescription>
            Filter by CPU clock speed range
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <RangeSlider
            min={1.0}
            max={5.0}
            step={0.1}
            value={speedRange}
            onValueChange={setSpeedRange}
            formatValue={(v) => `${v.toFixed(1)} GHz`}
            label="Clock speed range"
            showValues
          />
          <p className="text-sm text-muted-foreground">
            Current range: {speedRange[0].toFixed(1)} GHz - {speedRange[1].toFixed(1)} GHz
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>RAM Capacity Range (GB)</CardTitle>
          <CardDescription>
            Filter by RAM capacity
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <RangeSlider
            min={4}
            max={128}
            step={4}
            value={ramRange}
            onValueChange={setRamRange}
            formatValue={(v) => `${v} GB`}
            label="RAM capacity range"
            showValues
          />
          <p className="text-sm text-muted-foreground">
            Current range: {ramRange[0]} GB - {ramRange[1]} GB
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Keyboard Navigation Test</CardTitle>
          <CardDescription>
            Press Tab to focus handles, Arrow keys to adjust values
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RangeSlider
            min={0}
            max={100}
            defaultValue={[25, 75]}
            formatValue={(v) => `${v}%`}
            label="Keyboard test range"
            showValues
          />
          <p className="mt-4 text-xs text-muted-foreground">
            Accessibility: WCAG 2.1 AA compliant with keyboard navigation
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
