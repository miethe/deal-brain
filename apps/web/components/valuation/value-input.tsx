"use client";

import { useMemo } from "react";
import { Input } from "../ui/input";
import { Checkbox } from "../ui/checkbox";
import { ComboBox } from "../forms/combobox";
import { useFieldValues } from "@/hooks/use-field-values";

interface ValueInputProps {
  fieldType: string;
  fieldName?: string; // Full field name like "listing.condition"
  options?: string[];
  value: any;
  onChange: (value: any) => void;
  operator?: string; // For multi-value operators like "in"
}

export function ValueInput({
  fieldType,
  fieldName,
  options,
  value,
  onChange,
  operator,
}: ValueInputProps) {
  // Fetch field values for autocomplete (enum and string fields)
  // Always call hooks unconditionally at the top level
  const shouldFetchValues = (fieldType === "enum" || fieldType === "string") && !!fieldName;

  const { data: fieldValuesData, isLoading: isLoadingFieldValues } = useFieldValues({
    fieldName: fieldName || null,
    limit: 100,
    enabled: shouldFetchValues,
  });

  // Combine static options with fetched values
  const comboOptions = useMemo(() => {
    const values = new Set<string>();

    // Add static options (if provided)
    if (options) {
      options.forEach((opt) => values.add(opt));
    }

    // Add fetched values
    if (fieldValuesData?.values) {
      fieldValuesData.values.forEach((val) => values.add(val));
    }

    return Array.from(values).map((val) => ({
      label: val,
      value: val,
    }));
  }, [options, fieldValuesData?.values]);

  // Multi-value operators (in, not_in)
  if (operator === "in" || operator === "not_in") {
    return (
      <Input
        type="text"
        placeholder="Value1, Value2, Value3"
        value={Array.isArray(value) ? value.join(", ") : value}
        onChange={(e) => onChange(e.target.value.split(",").map((v) => v.trim()))}
      />
    );
  }

  // Enum fields or string fields with autocomplete
  if ((fieldType === "enum" || fieldType === "string") && comboOptions.length > 0) {
    return (
      <ComboBox
        options={comboOptions}
        value={value?.toString() || ""}
        onChange={onChange}
        placeholder={isLoadingFieldValues ? "Loading..." : "Select or type..."}
        enableInlineCreate={fieldType === "string"} // Allow custom values for string fields
        className="w-full"
      />
    );
  }

  // Boolean fields
  if (fieldType === "boolean") {
    return (
      <div className="flex items-center space-x-2">
        <Checkbox
          id="boolean-value"
          checked={value === true}
          onCheckedChange={(checked) => onChange(checked === true)}
        />
        <label htmlFor="boolean-value" className="text-sm">
          True
        </label>
      </div>
    );
  }

  // Number fields
  if (fieldType === "number") {
    return (
      <Input
        type="number"
        placeholder="Enter number..."
        value={value ?? ""}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
      />
    );
  }

  // Default: string input (fallback when no autocomplete data available)
  return (
    <Input
      type="text"
      placeholder="Enter value..."
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}
