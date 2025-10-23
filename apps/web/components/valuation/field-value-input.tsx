"use client";

import { Input } from "../ui/input";
import { Checkbox } from "../ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import type { FieldMetadata } from "../../lib/api/entities";

interface FieldValueInputProps {
  field: FieldMetadata | null;
  value: string;
  onChange: (value: string) => void;
  className?: string;
  placeholder?: string;
}

export function FieldValueInput({
  field,
  value,
  onChange,
  className,
  placeholder = "Enter value...",
}: FieldValueInputProps) {
  if (!field) {
    return (
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={className}
        placeholder={placeholder}
      />
    );
  }

  switch (field.data_type) {
    case "enum":
      if (field.options && field.options.length > 0) {
        return (
          <Select value={value} onValueChange={onChange}>
            <SelectTrigger className={className}>
              <SelectValue placeholder={placeholder} />
            </SelectTrigger>
            <SelectContent>
              {field.options.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      }
      return (
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={className}
          placeholder={placeholder}
        />
      );

    case "number":
    case "integer":
    case "float":
      return (
        <Input
          type="number"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={className}
          placeholder={placeholder}
        />
      );

    case "boolean":
      return (
        <div className={`flex items-center space-x-2 ${className || ""}`}>
          <Checkbox
            id={`boolean-${field.key}`}
            checked={value === "true" || value === "1"}
            onCheckedChange={(checked) => onChange(checked ? "true" : "false")}
          />
          <label
            htmlFor={`boolean-${field.key}`}
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            {value === "true" || value === "1" ? "True" : "False"}
          </label>
        </div>
      );

    case "string":
    case "text":
    default:
      return (
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={className}
          placeholder={placeholder}
        />
      );
  }
}
