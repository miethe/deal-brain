"use client";

import { Input } from "../ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Checkbox } from "../ui/checkbox";

interface ValueInputProps {
  fieldType: string;
  options?: string[];
  value: any;
  onChange: (value: any) => void;
  operator?: string; // For multi-value operators like "in"
}

export function ValueInput({ fieldType, options, value, onChange, operator }: ValueInputProps) {
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

  // Dropdown fields
  if (fieldType === "enum" && options && options.length > 0) {
    return (
      <Select value={value?.toString()} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue placeholder="Select value..." />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
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
        <label htmlFor="boolean-value" className="text-sm">True</label>
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

  // Default: string input
  return (
    <Input
      type="text"
      placeholder="Enter value..."
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}
