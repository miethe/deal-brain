"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";
import { Button } from "./button";
import { Label } from "./label";
import { Input } from "./input";

interface BulkEditField {
  key: string;
  label: string;
  dataType: "string" | "number" | "boolean" | "enum" | "multi_select";
  options?: string[];
  value?: any;
}

interface BulkEditDrawerProps {
  open: boolean;
  onClose: () => void;
  selectedCount: number;
  fields: BulkEditField[];
  onApply: (changes: Record<string, any>) => Promise<void>;
  className?: string;
}

export function BulkEditDrawer({
  open,
  onClose,
  selectedCount,
  fields,
  onApply,
  className,
}: BulkEditDrawerProps) {
  const [changes, setChanges] = React.useState<Record<string, any>>({});
  const [applying, setApplying] = React.useState(false);

  const handleChange = (key: string, value: any) => {
    setChanges((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleApply = async () => {
    if (Object.keys(changes).length === 0) {
      return;
    }

    setApplying(true);
    try {
      await onApply(changes);
      setChanges({});
      onClose();
    } catch (error) {
      console.error("Bulk edit failed:", error);
    } finally {
      setApplying(false);
    }
  };

  const handleReset = () => {
    setChanges({});
  };

  if (!open) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      <div
        className={cn(
          "fixed right-0 top-0 z-50 h-full w-full max-w-md border-l border-border bg-background shadow-xl transition-transform",
          "animate-in slide-in-from-right duration-300",
          className
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border p-6">
            <div>
              <h2 className="text-lg font-semibold">Bulk Edit</h2>
              <p className="text-sm text-muted-foreground">
                {selectedCount} record{selectedCount !== 1 ? "s" : ""} selected
              </p>
            </div>
            <button
              onClick={onClose}
              className="rounded-md p-1 text-muted-foreground hover:bg-muted"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="space-y-4">
              {fields.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No editable fields available
                </p>
              ) : (
                fields.map((field) => (
                  <div key={field.key} className="space-y-2">
                    <Label htmlFor={`bulk-${field.key}`} className="text-sm font-medium">
                      {field.label}
                    </Label>
                    {renderFieldInput(field, changes[field.key], (value) =>
                      handleChange(field.key, value)
                    )}
                  </div>
                ))
              )}
            </div>

            {Object.keys(changes).length > 0 && (
              <div className="mt-6 rounded-md border border-border bg-muted/50 p-4">
                <h3 className="mb-2 text-sm font-medium">Preview Changes</h3>
                <ul className="space-y-1 text-sm">
                  {Object.entries(changes).map(([key, value]) => {
                    const field = fields.find((f) => f.key === key);
                    return (
                      <li key={key} className="text-muted-foreground">
                        <span className="font-medium text-foreground">{field?.label}:</span>{" "}
                        {formatValue(value, field?.dataType)}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-border p-6">
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={applying || Object.keys(changes).length === 0}
                className="flex-1"
              >
                Reset
              </Button>
              <Button
                onClick={handleApply}
                disabled={applying || Object.keys(changes).length === 0}
                className="flex-1"
              >
                {applying ? "Applying..." : "Apply Changes"}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function renderFieldInput(
  field: BulkEditField,
  value: any,
  onChange: (value: any) => void
) {
  const id = `bulk-${field.key}`;

  switch (field.dataType) {
    case "boolean":
      return (
        <select
          id={id}
          className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
          value={value ?? ""}
          onChange={(e) => {
            const val = e.target.value;
            onChange(val === "" ? undefined : val === "true");
          }}
        >
          <option value="">-- No change --</option>
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
      );

    case "number":
      return (
        <Input
          id={id}
          type="number"
          inputMode="decimal"
          value={value ?? ""}
          onChange={(e) => {
            const val = e.target.value;
            onChange(val === "" ? undefined : Number(val));
          }}
          placeholder="Enter value"
        />
      );

    case "enum":
      return (
        <select
          id={id}
          className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value || undefined)}
        >
          <option value="">-- No change --</option>
          {field.options?.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      );

    case "multi_select":
      return (
        <select
          id={id}
          multiple
          className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={Array.isArray(value) ? value : []}
          onChange={(e) => {
            const selected = Array.from(e.target.selectedOptions).map((opt) => opt.value);
            onChange(selected.length > 0 ? selected : undefined);
          }}
        >
          {field.options?.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      );

    default:
      return (
        <Input
          id={id}
          type="text"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value || undefined)}
          placeholder="Enter value"
        />
      );
  }
}

function formatValue(value: any, dataType?: string): string {
  if (value === undefined || value === null) return "—";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}
