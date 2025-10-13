"use client";

import { useState } from "react";
import { Minus, Plus, RotateCcw, Info } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Label } from "../ui/label";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../ui/tooltip";
import type { BaselineField, FieldOverride } from "@/types/baseline";

interface BaselineFieldCardProps {
  field: BaselineField;
  override?: FieldOverride;
  onOverrideChange: (override: Partial<FieldOverride>) => void;
  onReset: () => void;
  disabled?: boolean;
}

export function BaselineFieldCard({
  field,
  override,
  onOverrideChange,
  onReset,
  disabled = false,
}: BaselineFieldCardProps) {
  const hasOverride = override && override.is_enabled;
  const [localValue, setLocalValue] = useState<number | undefined>(
    override?.override_value ?? override?.override_min ?? field.min_value
  );

  const handleValueChange = (newValue: number) => {
    setLocalValue(newValue);

    if (field.field_type === "scalar" || field.field_type === "multiplier" || field.field_type === "USD") {
      onOverrideChange({ override_value: newValue, is_enabled: true });
    } else if (field.field_type === "presence") {
      onOverrideChange({ override_min: newValue, is_enabled: true });
    }
  };

  const handleIncrement = () => {
    const step = 1;
    const max = field.max_value;
    const newValue = (localValue ?? 0) + step;
    if (max !== undefined && newValue > max) return;
    handleValueChange(newValue);
  };

  const handleDecrement = () => {
    const step = 1;
    const min = field.min_value;
    const newValue = (localValue ?? 0) - step;
    if (min !== undefined && newValue < min) return;
    handleValueChange(newValue);
  };

  const calculateDelta = (): number | null => {
    if (!hasOverride) return null;

    const baselineValue = field.min_value ?? 0;
    const overrideValue = override?.override_value ?? override?.override_min ?? 0;

    return overrideValue - baselineValue;
  };

  const delta = calculateDelta();

  const renderControl = () => {
    switch (field.field_type) {
      case "scalar":
      case "multiplier":
        return (
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={handleDecrement}
              disabled={disabled}
              aria-label="Decrease value"
            >
              <Minus className="h-4 w-4" />
            </Button>
            <Input
              type="number"
              value={localValue ?? ""}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                if (!isNaN(val)) {
                  handleValueChange(val);
                }
              }}
              step={1}
              min={field.min_value}
              max={field.max_value}
              disabled={disabled}
              className="h-8 w-24 text-center"
              aria-label={`${field.proper_name || field.field_name} value`}
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={handleIncrement}
              disabled={disabled}
              aria-label="Increase value"
            >
              <Plus className="h-4 w-4" />
            </Button>
            {field.unit && (
              <span className="text-sm text-muted-foreground">{field.unit}</span>
            )}
          </div>
        );

      case "presence":
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor={`${field.field_name}-min`} className="text-xs">
                Min Range
              </Label>
              <Input
                id={`${field.field_name}-min`}
                type="number"
                value={override?.override_min ?? field.min_value ?? ""}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  if (!isNaN(val)) {
                    onOverrideChange({ override_min: val, is_enabled: true });
                  }
                }}
                disabled={disabled}
                className="h-8 w-24"
              />
            </div>
            <div className="flex items-center gap-2">
              <Label htmlFor={`${field.field_name}-max`} className="text-xs">
                Max Range
              </Label>
              <Input
                id={`${field.field_name}-max`}
                type="number"
                value={override?.override_max ?? field.max_value ?? ""}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  if (!isNaN(val)) {
                    onOverrideChange({ override_max: val, is_enabled: true });
                  }
                }}
                disabled={disabled}
                className="h-8 w-24"
              />
            </div>
          </div>
        );

      case "formula":
        return (
          <div className="space-y-2">
            <div className="rounded-md bg-muted p-3">
              <code className="text-xs">{field.formula}</code>
            </div>
            <p className="text-xs text-muted-foreground">
              Formula editing requires Advanced mode
            </p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Card className={hasOverride ? "border-primary/50 shadow-sm" : ""}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <CardTitle className="flex items-center gap-2 text-base">
              {field.proper_name || field.field_name}
              {field.explanation && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      <p className="text-sm">{field.explanation}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </CardTitle>
            <CardDescription className="text-xs">{field.description}</CardDescription>
          </div>
          {hasOverride && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7"
              onClick={onReset}
              disabled={disabled}
              aria-label="Reset to baseline"
            >
              <RotateCcw className="mr-1 h-3 w-3" />
              Reset
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Baseline Section */}
        <div className="rounded-md bg-muted/50 p-3">
          <Label className="mb-2 block text-xs font-medium text-muted-foreground">
            Baseline
          </Label>
          <div className="space-y-1 text-sm">
            {field.min_value !== undefined && field.max_value !== undefined ? (
              <div>
                Range: {field.min_value} - {field.max_value}
                {field.unit && ` ${field.unit}`}
              </div>
            ) : field.min_value !== undefined ? (
              <div>
                Value: {field.min_value}
                {field.unit && ` ${field.unit}`}
              </div>
            ) : null}
            {field.formula && (
              <div className="mt-2">
                <code className="text-xs">{field.formula}</code>
              </div>
            )}
          </div>
        </div>

        {/* Override Control Section */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <Label className="text-xs font-medium">Override</Label>
            {hasOverride && delta !== null && (
              <Badge variant={delta >= 0 ? "default" : "destructive"} className="text-xs">
                {delta >= 0 ? "+" : ""}
                {delta.toFixed(2)}
                {field.unit && ` ${field.unit}`}
              </Badge>
            )}
          </div>
          {renderControl()}
        </div>
      </CardContent>
    </Card>
  );
}
