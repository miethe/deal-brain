"use client";

import { cn } from "@/lib/utils";
import { DollarSign, Calculator } from "lucide-react";

export type ValuationMode = "base" | "adjusted";

interface ValuationModeToggleProps {
  value: ValuationMode;
  onChange: (mode: ValuationMode) => void;
}

export function ValuationModeToggle({ value, onChange }: ValuationModeToggleProps) {
  return (
    <div
      className="inline-flex rounded-lg border bg-muted/20 p-1"
      role="tablist"
      aria-label="Valuation mode"
    >
      <button
        role="tab"
        aria-selected={value === "base"}
        aria-label="Show base prices"
        className={cn(
          "inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
          value === "base"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        )}
        onClick={() => onChange("base")}
      >
        <DollarSign className="h-4 w-4" />
        Base Price
      </button>
      <button
        role="tab"
        aria-selected={value === "adjusted"}
        aria-label="Show adjusted prices with component deductions"
        className={cn(
          "inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
          value === "adjusted"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        )}
        onClick={() => onChange("adjusted")}
      >
        <Calculator className="h-4 w-4" />
        Adjusted Price
      </button>
    </div>
  );
}
