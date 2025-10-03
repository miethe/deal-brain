"use client";

import { Input } from "../ui/input";
import { Checkbox } from "../ui/checkbox";
import { ComboBox } from "../forms/combobox";

interface DefaultValueInputProps {
  fieldType: string;
  options?: string[];
  value: any;
  onChange: (value: any) => void;
  disabled?: boolean;
}

export function DefaultValueInput({
  fieldType,
  options,
  value,
  onChange,
  disabled
}: DefaultValueInputProps) {
  switch (fieldType) {
    case "string":
    case "text":
      return (
        <Input
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder="Optional default value"
        />
      );

    case "number":
      return (
        <Input
          type="number"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
          disabled={disabled}
          placeholder="Optional default value"
        />
      );

    case "boolean":
      return (
        <div className="flex items-center space-x-2">
          <Checkbox
            id="default-boolean"
            checked={value === true}
            onCheckedChange={(checked) => onChange(checked === true)}
            disabled={disabled}
          />
          <label
            htmlFor="default-boolean"
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            Default to true
          </label>
        </div>
      );

    case "enum":
      return (
        <ComboBox
          options={(options ?? []).map((o) => ({ label: o, value: o }))}
          value={value ?? ""}
          onChange={onChange}
          disabled={disabled}
          placeholder="Select default..."
          enableInlineCreate={false}
        />
      );

    case "multi_select":
      // For multi-select, we'll use a simple comma-separated input
      // A proper MultiComboBox component could be used here if it exists
      return (
        <Input
          value={Array.isArray(value) ? value.join(", ") : value ?? ""}
          onChange={(e) => {
            const values = e.target.value
              .split(",")
              .map((v) => v.trim())
              .filter(Boolean);
            onChange(values.length > 0 ? values : null);
          }}
          disabled={disabled}
          placeholder="Option1, Option2, Option3"
        />
      );

    case "date":
      return (
        <Input
          type="date"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value || null)}
          disabled={disabled}
        />
      );

    default:
      return (
        <Input
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder="Optional default value"
        />
      );
  }
}
