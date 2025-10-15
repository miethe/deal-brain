"use client";

import { X } from "lucide-react";
import { Button } from "../ui/button";
import { EntityFieldSelector } from "./entity-field-selector";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { ValueInput } from "./value-input";
import { useQuery } from "@tanstack/react-query";
import { fetchEntitiesMetadata } from "../../lib/api/entities";
import { Checkbox } from "../ui/checkbox";
import { Label } from "../ui/label";

const NEGATION_OPERATOR_MAP: Record<string, string> = {
  equals: "not_equals",
  not_equals: "equals",
  in: "not_in",
  not_in: "in",
  is_null: "is_not_null",
  is_not_null: "is_null",
};

const NEGATED_OPERATORS = new Set(["not_equals", "not_in", "is_not_null"]);

interface ConditionRowProps {
  condition: any;
  onChange: (updates: any) => void;
  onRemove: () => void;
}

export function ConditionRow({ condition, onChange, onRemove }: ConditionRowProps) {
  const { data: metadata } = useQuery({
    queryKey: ["entities-metadata"],
    queryFn: fetchEntitiesMetadata,
    staleTime: 5 * 60 * 1000,
  });

  // Get valid operators for selected field type
  const fieldType = condition.field_type || "string";
  const validOperators =
    metadata?.operators.filter((op) => op.field_types.includes(fieldType)) || [];

  const operator = condition.operator || "equals";
  const canNegate = Boolean(NEGATION_OPERATOR_MAP[operator]);
  const isNegated = NEGATED_OPERATORS.has(operator);

  const handleNegateToggle = (nextState: boolean) => {
    if (!canNegate) return;
    if (nextState === isNegated) return;
    const toggledOperator = NEGATION_OPERATOR_MAP[operator] ?? operator;
    onChange({ operator: toggledOperator });
  };

  return (
    <div className="flex gap-2 rounded-lg border p-3">
      <div className="flex-1 space-y-2">
        {/* Entity.Field Selector */}
        <EntityFieldSelector
          value={condition.field_name}
          onChange={(fieldName, fieldType, options) =>
            onChange({ field_name: fieldName, field_type: fieldType, options })
          }
          placeholder="Select field..."
        />

        <div className="grid grid-cols-2 gap-2">
          {/* Operator Selector */}
          <div key="operator" className="flex items-center gap-2">
            <Select
              value={operator}
              onValueChange={(value) => onChange({ operator: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Operator" />
              </SelectTrigger>
              <SelectContent>
                {validOperators.map((op) => (
                  <SelectItem key={op.value} value={op.value}>
                    {op.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Checkbox
                id={`condition-not-${condition.id ?? operator}`}
                checked={isNegated}
                disabled={!canNegate}
                onCheckedChange={(checked) => handleNegateToggle(checked === true)}
              />
              <Label
                htmlFor={`condition-not-${condition.id ?? operator}`}
                className={canNegate ? "cursor-pointer select-none" : "opacity-60"}
              >
                NOT
              </Label>
            </div>
          </div>

          {/* Value Input */}
          <div key="value">
            <ValueInput
              fieldType={fieldType}
              fieldName={condition.field_name}
              options={condition.options}
              value={condition.value}
              onChange={(value) => onChange({ value })}
              operator={operator}
            />
          </div>
        </div>
      </div>

      {/* Remove Button */}
      <Button type="button" variant="ghost" size="sm" onClick={onRemove}>
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}
