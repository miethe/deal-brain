"use client";

import { useState, useMemo } from "react";
import { Plus, X, ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Card } from "../ui/card";
import { EntityFieldSelector } from "./entity-field-selector";
import { FieldValueInput } from "./field-value-input";
import type { ActionMultiplier } from "../../lib/api/rules";
import type { FieldMetadata } from "../../lib/api/entities";

interface ActionMultipliersProps {
  multipliers: ActionMultiplier[];
  onChange: (multipliers: ActionMultiplier[]) => void;
  availableFields: FieldMetadata[];
}

export function ActionMultipliers({
  multipliers,
  onChange,
  availableFields,
}: ActionMultipliersProps) {
  const [expandedIndexes, setExpandedIndexes] = useState<Set<number>>(new Set([0]));

  const toggleExpanded = (index: number) => {
    setExpandedIndexes((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const addMultiplier = () => {
    const newMultiplier: ActionMultiplier = {
      name: `Multiplier ${multipliers.length + 1}`,
      field: "",
      conditions: [{ value: "", multiplier: 1.0 }],
    };
    onChange([...multipliers, newMultiplier]);
    setExpandedIndexes((prev) => new Set(prev).add(multipliers.length));
  };

  const removeMultiplier = (index: number) => {
    onChange(multipliers.filter((_, i) => i !== index));
    setExpandedIndexes((prev) => {
      const next = new Set(prev);
      next.delete(index);
      return next;
    });
  };

  const updateMultiplier = (index: number, updates: Partial<ActionMultiplier>) => {
    const updated = [...multipliers];
    updated[index] = { ...updated[index], ...updates };
    onChange(updated);
  };

  const addCondition = (multiplierIndex: number) => {
    const updated = [...multipliers];
    updated[multiplierIndex].conditions.push({ value: "", multiplier: 1.0 });
    onChange(updated);
  };

  const removeCondition = (multiplierIndex: number, conditionIndex: number) => {
    const updated = [...multipliers];
    updated[multiplierIndex].conditions = updated[multiplierIndex].conditions.filter(
      (_, i) => i !== conditionIndex
    );
    onChange(updated);
  };

  const updateCondition = (
    multiplierIndex: number,
    conditionIndex: number,
    updates: Partial<{ value: string; multiplier: number }>
  ) => {
    const updated = [...multipliers];
    updated[multiplierIndex].conditions[conditionIndex] = {
      ...updated[multiplierIndex].conditions[conditionIndex],
      ...updates,
    };
    onChange(updated);
  };

  const getFieldMetadata = (fieldKey: string): FieldMetadata | null => {
    return availableFields.find((f) => f.key === fieldKey) || null;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-base font-semibold">Action Multipliers</Label>
        <Button type="button" variant="outline" size="sm" onClick={addMultiplier}>
          <Plus className="h-4 w-4 mr-1" />
          Add Multiplier
        </Button>
      </div>

      {multipliers.length === 0 ? (
        <Card className="p-6 text-center">
          <p className="text-sm text-muted-foreground mb-2">
            No multipliers configured
          </p>
          <p className="text-xs text-muted-foreground mb-4">
            Add field-based multipliers to adjust action values dynamically based on listing properties
          </p>
          <Button type="button" variant="outline" size="sm" onClick={addMultiplier}>
            <Plus className="h-4 w-4 mr-1" />
            Add Your First Multiplier
          </Button>
        </Card>
      ) : (
        <div className="space-y-2">
          {multipliers.map((multiplier, multiplierIndex) => {
            const isExpanded = expandedIndexes.has(multiplierIndex);
            const fieldMetadata = getFieldMetadata(multiplier.field);
            const hasErrors =
              !multiplier.field ||
              multiplier.conditions.length === 0 ||
              multiplier.conditions.some((c) => !c.value || c.multiplier <= 0);

            return (
              <Card
                key={multiplierIndex}
                className={`transition-all ${hasErrors ? "border-destructive/50" : ""}`}
              >
                {/* Header */}
                <div
                  className="flex items-center justify-between p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => toggleExpanded(multiplierIndex)}
                  role="button"
                  tabIndex={0}
                  aria-expanded={isExpanded}
                  aria-controls={`multiplier-content-${multiplierIndex}`}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      toggleExpanded(multiplierIndex);
                    }
                  }}
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4 shrink-0" aria-hidden="true" />
                    ) : (
                      <ChevronRight className="h-4 w-4 shrink-0" aria-hidden="true" />
                    )}
                    <div className="flex flex-col flex-1 min-w-0">
                      <span className="font-medium text-sm truncate">
                        {multiplier.name || `Multiplier ${multiplierIndex + 1}`}
                      </span>
                      {multiplier.field && (
                        <span className="text-xs text-muted-foreground truncate">
                          {fieldMetadata?.label || multiplier.field} • {multiplier.conditions.length}{" "}
                          {multiplier.conditions.length === 1 ? "condition" : "conditions"}
                        </span>
                      )}
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeMultiplier(multiplierIndex);
                    }}
                    aria-label={`Remove ${multiplier.name || "multiplier"}`}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Content */}
                {isExpanded && (
                  <div
                    id={`multiplier-content-${multiplierIndex}`}
                    className="border-t p-4 space-y-4"
                  >
                    {/* Name Input */}
                    <div className="space-y-2">
                      <Label htmlFor={`multiplier-name-${multiplierIndex}`}>
                        Multiplier Name
                      </Label>
                      <Input
                        id={`multiplier-name-${multiplierIndex}`}
                        value={multiplier.name}
                        onChange={(e) =>
                          updateMultiplier(multiplierIndex, { name: e.target.value })
                        }
                        placeholder="e.g., RAM Generation Multiplier"
                      />
                    </div>

                    {/* Field Selector */}
                    <div className="space-y-2">
                      <Label htmlFor={`multiplier-field-${multiplierIndex}`}>
                        Field <span className="text-destructive">*</span>
                      </Label>
                      <EntityFieldSelector
                        value={multiplier.field}
                        onChange={(fieldKey, fieldType, options) =>
                          updateMultiplier(multiplierIndex, { field: fieldKey })
                        }
                        placeholder="Select field to apply multiplier..."
                      />
                      {!multiplier.field && (
                        <p className="text-xs text-destructive">Field is required</p>
                      )}
                    </div>

                    {/* Conditions */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>
                          Conditions <span className="text-destructive">*</span>
                        </Label>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => addCondition(multiplierIndex)}
                          disabled={!multiplier.field}
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Add Condition
                        </Button>
                      </div>

                      {multiplier.conditions.length === 0 ? (
                        <Card className="p-4 text-center bg-muted/50">
                          <p className="text-xs text-muted-foreground">
                            No conditions defined. Add at least one condition.
                          </p>
                        </Card>
                      ) : (
                        <div className="space-y-2">
                          {multiplier.conditions.map((condition, conditionIndex) => (
                            <div
                              key={conditionIndex}
                              className="flex items-start gap-2 p-3 rounded-md border bg-muted/20"
                            >
                              <div className="flex-1 grid grid-cols-[1fr,auto,100px] gap-2 items-center">
                                {/* Value Input */}
                                <div className="space-y-1">
                                  <Label
                                    htmlFor={`condition-value-${multiplierIndex}-${conditionIndex}`}
                                    className="text-xs"
                                  >
                                    Value
                                  </Label>
                                  <FieldValueInput
                                    field={fieldMetadata}
                                    value={condition.value}
                                    onChange={(value) =>
                                      updateCondition(multiplierIndex, conditionIndex, {
                                        value,
                                      })
                                    }
                                    placeholder="Enter value..."
                                  />
                                </div>

                                {/* Multiplier Symbol */}
                                <div className="flex items-center justify-center pt-6">
                                  <span className="text-lg font-semibold text-muted-foreground">
                                    ×
                                  </span>
                                </div>

                                {/* Multiplier Value */}
                                <div className="space-y-1">
                                  <Label
                                    htmlFor={`condition-multiplier-${multiplierIndex}-${conditionIndex}`}
                                    className="text-xs"
                                  >
                                    Multiplier
                                  </Label>
                                  <Input
                                    id={`condition-multiplier-${multiplierIndex}-${conditionIndex}`}
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    value={condition.multiplier}
                                    onChange={(e) =>
                                      updateCondition(multiplierIndex, conditionIndex, {
                                        multiplier: parseFloat(e.target.value) || 0,
                                      })
                                    }
                                    placeholder="1.0"
                                  />
                                </div>
                              </div>

                              {/* Remove Button */}
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => removeCondition(multiplierIndex, conditionIndex)}
                                className="mt-6"
                                aria-label="Remove condition"
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}

                      <p className="text-xs text-muted-foreground">
                        When the field matches a condition value, the action result will be
                        multiplied by the specified multiplier.
                      </p>
                    </div>

                    {/* Preview/Help Text */}
                    {multiplier.field && multiplier.conditions.length > 0 && (
                      <Card className="p-3 bg-muted/30">
                        <p className="text-xs font-medium mb-1">Preview:</p>
                        <p className="text-xs text-muted-foreground">
                          When <span className="font-mono">{fieldMetadata?.label || multiplier.field}</span>{" "}
                          is:
                        </p>
                        <ul className="text-xs text-muted-foreground ml-4 mt-1 space-y-0.5">
                          {multiplier.conditions.map((condition, idx) => (
                            <li key={idx}>
                              <span className="font-mono">{condition.value || "(empty)"}</span> →
                              multiply by{" "}
                              <span className="font-semibold">{condition.multiplier}×</span>
                            </li>
                          ))}
                        </ul>
                      </Card>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
