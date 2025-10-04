# Implementation Plan: Q4 UX Refinements

**Version:** 1.0
**Date:** October 4, 2025
**Status:** Ready for Implementation
**Related PRD:** [prd-10-4-enhancements.md](./prd-10-4-enhancements.md)

---

## Overview

This implementation plan delivers critical UX refinements and bug fixes across five key areas:

1. **Bug Fixes** (Critical Priority) - Valuation rule update errors
2. **Managed Field Editing** - Enable editing for CPU, GPU, RAM, Storage in listings
3. **Column Tooltips** - Add field descriptions to all table headers
4. **Dropdown UX** - Standardize dropdown sizing and readability
5. **Basic Valuation View** - Simplified rule builder for common use cases

**Estimated Effort:** 3-4 days (solo developer)
**Risk Level:** Low (mostly frontend changes, minimal backend impact)

---

## Phase 1: Bug Fixes (Critical - 4 hours)

### 1.1 Fix React Key Warnings

**Files to Modify:**
- `apps/web/components/valuation/condition-group.tsx`
- `apps/web/components/valuation/action-builder.tsx`

**Changes:**

1. **condition-group.tsx (line 200-210):**
```tsx
// BEFORE (BUGGY)
{conditions.map((condition, index) => (
  <SortableCondition
    key={condition.id}  // Already correct! Verify this is being used
    id={condition.id}
    condition={condition}
    index={index}
    updateCondition={updateCondition}
    removeCondition={removeCondition}
    depth={depth}
  />
))}

// VERIFY: Check that condition.id is stable and unique
// If missing, add to addCondition() and addGroup():
id: crypto.randomUUID()  // or `cond-${Date.now()}-${Math.random()}`
```

2. **action-builder.tsx (line 54):**
```tsx
// BEFORE (BUGGY - using index as key implicitly)
{actions.map((action, index) => (
  <div key={action.id} className="rounded-lg border p-4 space-y-3">
    {/* ... */}
  </div>
))}

// FIX: Ensure action.id exists in addAction() function (line 24-39):
const addAction = () => {
  onActionsChange([
    ...actions,
    {
      id: crypto.randomUUID(), // ADD THIS LINE
      action_type: "fixed_value",
      value_usd: 0,
      modifiers: {
        condition_multipliers: {
          new: 1.0,
          refurb: 0.75,
          used: 0.6,
        },
      },
    },
  ]);
};
```

**Testing:**
- Open DevTools Console
- Navigate to Valuation Rules → Edit Rule
- Add/remove/reorder conditions and actions
- Verify: 0 key-related warnings

---

### 1.2 Fix AttributeError in Rule Update

**File to Modify:**
- `apps/api/dealbrain_api/api/rules.py` (lines 520-536)

**Current Code (BUGGY):**
```python
@router.put("/valuation-rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    request: RuleUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update a valuation rule"""
    service = RulesService()

    updates = {k: v for k, v in request.dict(exclude_unset=True).items() if v is not None}

    # BUG: updates["conditions"] is already a list of dicts after request.dict()
    if "conditions" in updates:
        updates["conditions"] = [c.dict() for c in updates["conditions"]]  # ❌ FAILS
    if "actions" in updates:
        updates["actions"] = [a.dict() for a in updates["actions"]]  # ❌ FAILS
```

**Root Cause Analysis:**
- `request.dict()` already converts Pydantic models to dicts
- Attempting `.dict()` on a dict raises AttributeError
- Similar bug at line 378-379 in `create_rule()` (but works because those ARE Pydantic objects)

**Fix Option A (Safe Check):**
```python
updates = {k: v for k, v in request.dict(exclude_unset=True).items() if v is not None}

# Safe conversion - check if already dicts
if "conditions" in updates and updates["conditions"]:
    if isinstance(updates["conditions"][0], dict):
        pass  # Already dicts, no conversion needed
    else:
        updates["conditions"] = [c.dict() for c in updates["conditions"]]

if "actions" in updates and updates["actions"]:
    if isinstance(updates["actions"][0], dict):
        pass  # Already dicts
    else:
        updates["actions"] = [a.dict() for a in updates["actions"]]
```

**Fix Option B (Remove Redundant Conversion - RECOMMENDED):**
```python
updates = {k: v for k, v in request.dict(exclude_unset=True).items() if v is not None}

# No conversion needed - request.dict() already handles it
# Just pass updates directly to service
rule = await service.update_rule(session, rule_id, updates)
```

**Verify Fix:**
```python
# Add logging to confirm data structure
import logging
logger = logging.getLogger(__name__)

updates = {k: v for k, v in request.dict(exclude_unset=True).items() if v is not None}
logger.info(f"Updates type check: conditions={type(updates.get('conditions'))}, "
            f"actions={type(updates.get('actions'))}")

# Then apply Option B (remove conversion)
```

**Testing:**
1. Create a valuation rule via UI
2. Edit the rule, modify conditions/actions
3. Click "Update"
4. Verify: Rule saves successfully, no AttributeError in logs
5. Check: Conditions/actions persist correctly in database

---

## Phase 2: Managed Field Editing (6 hours)

### 2.1 Enable Editing in Listings Table

**File to Modify:**
- `apps/web/components/listings/listings-table.tsx`

**Current State Analysis:**
```tsx
// Find column definitions around line 50-150
// Look for editable: false flags on managed fields
```

**Changes Required:**

1. **Remove editable restrictions:**
```tsx
// BEFORE
{
  accessorKey: "cpu.model_name",
  header: "CPU",
  editable: false,  // ❌ REMOVE THIS
  cell: ({ row }) => (
    <div className="max-w-[200px] truncate">
      {row.original.cpu?.model_name || "-"}
    </div>
  ),
}

// AFTER
{
  accessorKey: "cpu_id",  // Use ID for editing, not nested model_name
  header: "CPU",
  cell: ({ row }) => (
    <EditableCPUCell
      listing={row.original}
      onUpdate={(updates) => updateListing(row.original.id, updates)}
    />
  ),
}
```

2. **Create EditableCPUCell component:**
```tsx
// apps/web/components/listings/editable-cpu-cell.tsx
"use client";

import { useState } from "react";
import { CPUComboBox } from "@/components/forms/cpu-combobox";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { API_URL } from "@/lib/utils";

interface EditableCPUCellProps {
  listing: any;
  onUpdate: (updates: { cpu_id: number }) => void;
}

export function EditableCPUCell({ listing, onUpdate }: EditableCPUCellProps) {
  const [isEditing, setIsEditing] = useState(false);
  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: async (cpu_id: number) => {
      const res = await fetch(`${API_URL}/listings/${listing.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cpu_id }),
      });
      if (!res.ok) throw new Error("Failed to update CPU");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      setIsEditing(false);
    },
  });

  if (!isEditing) {
    return (
      <div
        className="cursor-pointer hover:bg-accent p-2 rounded"
        onClick={() => setIsEditing(true)}
      >
        {listing.cpu?.model_name || "Select CPU..."}
      </div>
    );
  }

  return (
    <CPUComboBox
      value={listing.cpu_id}
      onChange={(cpu_id) => updateMutation.mutate(cpu_id)}
      onBlur={() => setIsEditing(false)}
      autoFocus
    />
  );
}
```

3. **Similar components for other managed fields:**
   - `EditableGPUCell` (same pattern as CPU)
   - `EditableRAMCell` (numeric input with common values dropdown)
   - `EditableStorageCell` (numeric input with common values dropdown)
   - `EditableStorageTypeCell` (simple dropdown, already exists in EditableCell)

4. **Validation in EditableRAMCell:**
```tsx
// apps/web/components/listings/editable-ram-cell.tsx
export function EditableRAMCell({ listing, onUpdate }: EditableRAMCellProps) {
  const [value, setValue] = useState(listing.ram_gb?.toString() || "");
  const [error, setError] = useState("");

  const validateAndSave = () => {
    const numValue = parseInt(value);

    // Validation
    if (isNaN(numValue) || numValue <= 0) {
      setError("Must be a positive number");
      return;
    }
    if (numValue > 1024) {
      setError("Maximum 1024GB");
      return;
    }

    // Save
    setError("");
    updateMutation.mutate(numValue);
  };

  return (
    <div className="space-y-1">
      <ComboBox
        value={value}
        onChange={setValue}
        onBlur={validateAndSave}
        options={[4, 8, 16, 24, 32, 48, 64, 96, 128].map(v => ({
          value: v.toString(),
          label: `${v} GB`
        }))}
        allowCustom
      />
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
```

**Backend Verification:**
- Confirm `PATCH /api/v1/listings/{id}` accepts: `cpu_id`, `gpu_id`, `ram_gb`, `storage_gb`, `storage_type`
- Check if validation exists in backend (should already be in place)

**Testing Checklist:**
- [ ] Click CPU cell → opens combobox → select different CPU → saves successfully
- [ ] Click GPU cell → same workflow
- [ ] Click RAM cell → type custom value → validates correctly → saves
- [ ] Click Storage cell → same validation
- [ ] Click Storage Type cell → dropdown works
- [ ] Invalid inputs show error, don't save
- [ ] Optimistic UI: cell updates immediately, rolls back on error
- [ ] Check network tab: Only changed field sent in PATCH request

---

## Phase 3: Column Tooltips (4 hours)

### 3.1 Add Tooltip Support to DataGrid

**File to Modify:**
- `apps/web/components/ui/data-grid.tsx`

**Changes:**

1. **Update Column Type Definition:**
```tsx
// Add description field to column config
export interface DataGridColumn<T> {
  accessorKey: string;
  header: string;
  description?: string;  // NEW: Optional tooltip content
  cell?: (props: any) => React.ReactNode;
  editable?: boolean;
  sortable?: boolean;
  // ... existing fields
}
```

2. **Modify Header Rendering:**
```tsx
// Find header rendering section (around line 200-250)
// BEFORE
<TableHead key={header.id}>
  {header.isPlaceholder ? null : (
    <div className="flex items-center gap-2">
      {flexRender(header.column.columnDef.header, header.getContext())}
      {header.column.getCanSort() && <SortIcon />}
    </div>
  )}
</TableHead>

// AFTER
<TableHead key={header.id}>
  {header.isPlaceholder ? null : (
    <div className="flex items-center gap-2">
      {flexRender(header.column.columnDef.header, header.getContext())}
      {header.column.columnDef.meta?.description && (
        <InfoTooltip content={header.column.columnDef.meta.description} />
      )}
      {header.column.getCanSort() && <SortIcon />}
    </div>
  )}
</TableHead>
```

3. **Create InfoTooltip Component:**
```tsx
// apps/web/components/ui/info-tooltip.tsx
"use client";

import { Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface InfoTooltipProps {
  content: string;
}

export function InfoTooltip({ content }: InfoTooltipProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            className="inline-flex items-center justify-center"
            onClick={(e) => e.stopPropagation()}
            aria-label="Field description"
          >
            <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground transition-colors" />
          </button>
        </TooltipTrigger>
        <TooltipContent
          className="max-w-[320px] text-sm"
          side="top"
          align="center"
        >
          <p>{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
```

4. **Ensure Radix Tooltip is installed:**
```bash
pnpm --filter web add @radix-ui/react-tooltip
```

5. **Update column definitions with descriptions:**
```tsx
// In listings-table.tsx, add descriptions to columns
const columns: DataGridColumn<Listing>[] = [
  {
    accessorKey: "title",
    header: "Title",
    meta: {
      description: "The product title or name from the seller"
    }
  },
  {
    accessorKey: "cpu.model_name",
    header: "CPU",
    meta: {
      description: "The processor model (Intel/AMD) powering this system"
    }
  },
  {
    accessorKey: "ram_gb",
    header: "RAM (GB)",
    meta: {
      description: "System memory capacity in gigabytes"
    }
  },
  // ... etc for all columns
];
```

**Accessibility Checklist:**
- [ ] Tooltip has `aria-describedby` linking to content
- [ ] Tooltip trigger is keyboard accessible (focus with Tab)
- [ ] Tooltip shows on focus and hover
- [ ] Tooltip dismisses with Escape key
- [ ] Screen reader announces description when focused

**Testing:**
- [ ] Hover info icon → tooltip appears after 200ms delay
- [ ] Move mouse away → tooltip disappears
- [ ] Tab to info icon → tooltip appears
- [ ] Press Escape → tooltip disappears
- [ ] Click info icon → tooltip stays open (until click outside or Escape)
- [ ] Columns without description → no icon shown
- [ ] Test with screen reader (VoiceOver/NVDA) → description announced

---

## Phase 4: Dropdown UX Standardization (6 hours)

### 4.1 Create Dynamic Width Dropdown Component

**File to Create:**
- `apps/web/components/ui/smart-dropdown.tsx`

**Implementation:**

```tsx
"use client";

import { useState, useRef, useEffect } from "react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Command, CommandGroup, CommandItem } from "@/components/ui/command";
import { Check, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface SmartDropdownProps {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  className?: string;
}

export function SmartDropdown({
  value,
  onChange,
  options,
  placeholder = "Select...",
  className,
}: SmartDropdownProps) {
  const [open, setOpen] = useState(false);
  const [dropdownWidth, setDropdownWidth] = useState(200);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const measureRef = useRef<HTMLDivElement>(null);

  // Calculate optimal dropdown width
  useEffect(() => {
    if (!measureRef.current) return;

    const longestOption = options.reduce((max, opt) =>
      opt.label.length > max.label.length ? opt : max
    , options[0]);

    // Measure text width using hidden span
    const span = document.createElement("span");
    span.style.cssText = "position:absolute;visibility:hidden;white-space:nowrap;font:14px system-ui";
    span.textContent = longestOption.label;
    document.body.appendChild(span);

    const textWidth = span.offsetWidth;
    document.body.removeChild(span);

    // Calculate final width
    const triggerWidth = triggerRef.current?.offsetWidth || 0;
    const calculatedWidth = Math.max(
      200,  // min width
      triggerWidth,  // at least as wide as trigger
      textWidth + 64  // text + padding + icons
    );
    const finalWidth = Math.min(calculatedWidth, 400);  // max width

    setDropdownWidth(finalWidth);
  }, [options]);

  const selectedOption = options.find(opt => opt.value === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          ref={triggerRef}
          className={cn(
            "flex h-9 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background",
            "focus:outline-none focus:ring-1 focus:ring-ring",
            "disabled:cursor-not-allowed disabled:opacity-50",
            className
          )}
          aria-expanded={open}
        >
          <span className="truncate">
            {selectedOption?.label || placeholder}
          </span>
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        className="p-0"
        style={{ width: `${dropdownWidth}px` }}
        align="start"
        sideOffset={4}
      >
        <Command>
          <CommandGroup className="max-h-[300px] overflow-auto">
            {options.map((option) => (
              <CommandItem
                key={option.value}
                value={option.value}
                onSelect={() => {
                  onChange(option.value);
                  setOpen(false);
                }}
                className="flex items-center justify-between px-3 py-2"
              >
                <span>{option.label}</span>
                {value === option.value && (
                  <Check className="h-4 w-4 text-primary" />
                )}
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
      {/* Hidden measurement div */}
      <div ref={measureRef} className="sr-only" />
    </Popover>
  );
}
```

### 4.2 Replace Existing Dropdowns

**Files to Update:**
1. `apps/web/components/listings/editable-cell.tsx` (Storage Type dropdown)
2. `apps/web/components/forms/field-form.tsx` (Field Type dropdown)
3. Any other dropdowns in modals/forms

**Migration Example:**
```tsx
// BEFORE (using shadcn Select)
<Select value={storageType} onValueChange={setStorageType}>
  <SelectTrigger>
    <SelectValue placeholder="Select type" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="ssd">SSD</SelectItem>
    <SelectItem value="nvme">NVMe</SelectItem>
    <SelectItem value="hdd">HDD</SelectItem>
  </SelectContent>
</Select>

// AFTER (using SmartDropdown)
<SmartDropdown
  value={storageType}
  onChange={setStorageType}
  options={[
    { value: "ssd", label: "SSD (Solid State Drive)" },
    { value: "nvme", label: "NVMe (M.2 PCIe SSD)" },
    { value: "hdd", label: "HDD (Hard Disk Drive)" },
    { value: "emmc", label: "eMMC (Embedded Flash)" }
  ]}
  placeholder="Select storage type"
/>
```

**Testing:**
- [ ] Dropdown width matches longest option + padding
- [ ] Dropdown never narrower than trigger button
- [ ] Dropdown never wider than 400px
- [ ] Dropdown repositions if would overflow viewport
- [ ] Works in table cells with varying column widths
- [ ] Works in modal forms
- [ ] Keyboard navigation works (Arrow keys, Enter, Escape)

---

## Phase 5: Basic Valuation View (12 hours)

### 5.1 Design Basic View UI

**Files to Create:**
- `apps/web/components/valuation/basic-rule-builder.tsx`
- `apps/web/components/valuation/view-toggle.tsx`
- `apps/web/lib/valuation-conversion.ts` (conversion utilities)

### 5.2 View Toggle Component

```tsx
// apps/web/components/valuation/view-toggle.tsx
"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ViewMode = "basic" | "advanced";

interface ViewToggleProps {
  value: ViewMode;
  onChange: (mode: ViewMode) => void;
  canUseBasic: boolean;  // Whether current rule is Basic-compatible
}

export function ViewToggle({ value, onChange, canUseBasic }: ViewToggleProps) {
  useEffect(() => {
    // Load saved preference
    const saved = localStorage.getItem("valuationViewMode") as ViewMode;
    if (saved && saved !== value) {
      onChange(saved);
    }
  }, []);

  const handleChange = (mode: ViewMode) => {
    if (mode === "basic" && !canUseBasic) {
      // Show warning
      alert("This rule uses advanced features and cannot be edited in Basic view.");
      return;
    }
    localStorage.setItem("valuationViewMode", mode);
    onChange(mode);
  };

  return (
    <div className="inline-flex rounded-lg border p-1 gap-1">
      <Button
        variant={value === "basic" ? "default" : "ghost"}
        size="sm"
        onClick={() => handleChange("basic")}
        className={cn(
          "px-3 py-1 h-7 text-xs",
          !canUseBasic && "opacity-50 cursor-not-allowed"
        )}
        disabled={!canUseBasic}
      >
        Basic
      </Button>
      <Button
        variant={value === "advanced" ? "default" : "ghost"}
        size="sm"
        onClick={() => handleChange("advanced")}
        className="px-3 py-1 h-7 text-xs"
      >
        Advanced
      </Button>
    </div>
  );
}
```

### 5.3 Basic Rule Builder Component

```tsx
// apps/web/components/valuation/basic-rule-builder.tsx
"use client";

import { useState } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { SmartDropdown } from "@/components/ui/smart-dropdown";
import { Plus, X, AlertCircle } from "lucide-react";

interface BasicCondition {
  field: string;
  operator: string;
  value: string;
}

interface BasicRuleBuilderProps {
  conditions: BasicCondition[];
  onConditionsChange: (conditions: BasicCondition[]) => void;
  logicalOperator: "AND" | "OR";
  onLogicalOperatorChange: (op: "AND" | "OR") => void;
}

const FIELD_OPTIONS = [
  { value: "ram_gb", label: "RAM (GB)" },
  { value: "storage_gb", label: "Storage (GB)" },
  { value: "cpu.model_name", label: "CPU Model" },
  { value: "condition", label: "Condition" },
  { value: "list_price_usd", label: "List Price" },
];

const OPERATOR_OPTIONS = {
  number: [
    { value: "eq", label: "equals" },
    { value: "gt", label: "greater than" },
    { value: "lt", label: "less than" },
    { value: "gte", label: "greater than or equal" },
    { value: "lte", label: "less than or equal" },
  ],
  string: [
    { value: "equals", label: "equals" },
    { value: "contains", label: "contains" },
  ],
};

export function BasicRuleBuilder({
  conditions,
  onConditionsChange,
  logicalOperator,
  onLogicalOperatorChange,
}: BasicRuleBuilderProps) {
  const addCondition = () => {
    onConditionsChange([
      ...conditions,
      { field: "", operator: "eq", value: "" },
    ]);
  };

  const updateCondition = (index: number, updates: Partial<BasicCondition>) => {
    const newConditions = [...conditions];
    newConditions[index] = { ...newConditions[index], ...updates };
    onConditionsChange(newConditions);
  };

  const removeCondition = (index: number) => {
    onConditionsChange(conditions.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      <div>
        <Label>When these conditions match:</Label>
        <SmartDropdown
          value={logicalOperator}
          onChange={(v) => onLogicalOperatorChange(v as "AND" | "OR")}
          options={[
            { value: "AND", label: "Match ALL conditions" },
            { value: "OR", label: "Match ANY condition" },
          ]}
          className="mt-2 max-w-xs"
        />
      </div>

      <div className="space-y-2">
        {conditions.length === 0 && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground p-4 border border-dashed rounded-lg">
            <AlertCircle className="h-4 w-4" />
            <span>No conditions added. Rule will match all listings.</span>
          </div>
        )}

        {conditions.map((condition, index) => (
          <div key={index} className="flex gap-2 items-start p-3 border rounded-lg">
            <div className="flex-1 grid grid-cols-3 gap-2">
              <div>
                <Label className="text-xs">Field</Label>
                <SmartDropdown
                  value={condition.field}
                  onChange={(v) => updateCondition(index, { field: v })}
                  options={FIELD_OPTIONS}
                  placeholder="Select field"
                />
              </div>
              <div>
                <Label className="text-xs">Operator</Label>
                <SmartDropdown
                  value={condition.operator}
                  onChange={(v) => updateCondition(index, { operator: v })}
                  options={OPERATOR_OPTIONS.number}  // TODO: Dynamic based on field type
                  placeholder="Select operator"
                />
              </div>
              <div>
                <Label className="text-xs">Value</Label>
                <Input
                  value={condition.value}
                  onChange={(e) => updateCondition(index, { value: e.target.value })}
                  placeholder="Enter value"
                />
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => removeCondition(index)}
              className="mt-6"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ))}

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={addCondition}
          className="w-full"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Condition
        </Button>
      </div>
    </div>
  );
}
```

### 5.4 Basic Action Builder

```tsx
// apps/web/components/valuation/basic-action-builder.tsx
"use client";

import { useState } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

type ActionMode = "fixed" | "quantity";

interface BasicActionBuilderProps {
  mode: ActionMode;
  onModeChange: (mode: ActionMode) => void;
  // For quantity mode
  valuePerUnit: number;
  onValuePerUnitChange: (value: number) => void;
  // For fixed mode
  fixedValues: { quantity: number; condition: string; value: number }[];
  onFixedValuesChange: (values: any[]) => void;
}

export function BasicActionBuilder({
  mode,
  onModeChange,
  valuePerUnit,
  onValuePerUnitChange,
  fixedValues,
  onFixedValuesChange,
}: BasicActionBuilderProps) {
  return (
    <div className="space-y-4">
      <div>
        <Label>Set component value:</Label>
        <RadioGroup value={mode} onValueChange={(v) => onModeChange(v as ActionMode)} className="mt-2">
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="quantity" id="quantity" />
            <Label htmlFor="quantity" className="font-normal cursor-pointer">
              Quantity-Based (e.g., $3 per GB)
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="fixed" id="fixed" />
            <Label htmlFor="fixed" className="font-normal cursor-pointer">
              Fixed Values (e.g., 16GB = $50, 32GB = $100)
            </Label>
          </div>
        </RadioGroup>
      </div>

      {mode === "quantity" && (
        <div className="space-y-3 pl-6 border-l-2 border-primary/20">
          <div className="flex items-center gap-2">
            <span className="text-sm">$</span>
            <Input
              type="number"
              step="0.01"
              value={valuePerUnit}
              onChange={(e) => onValuePerUnitChange(parseFloat(e.target.value) || 0)}
              className="w-24"
            />
            <span className="text-sm">per 1 GB</span>
          </div>
          <div className="text-xs text-muted-foreground">
            Example: $3 per GB means 16GB = $48
          </div>

          <div className="space-y-2">
            <Label className="text-xs">Condition Multipliers:</Label>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div>New: 1.0 (100%)</div>
              <div>Refurbished: 0.75 (75%)</div>
              <div>Used: 0.6 (60%)</div>
            </div>
          </div>
        </div>
      )}

      {mode === "fixed" && (
        <div className="space-y-3 pl-6 border-l-2 border-primary/20">
          <p className="text-sm text-muted-foreground">
            Manually set value for each quantity and condition
          </p>
          {/* TODO: Table for fixed values */}
          <div className="text-sm italic">Fixed value table coming soon...</div>
        </div>
      )}
    </div>
  );
}
```

### 5.5 Integrate into Rule Modal

**File to Modify:**
- `apps/web/components/valuation/rule-builder-modal.tsx`

**Changes:**

1. Add view state:
```tsx
const [viewMode, setViewMode] = useState<"basic" | "advanced">("basic");
const [isBasicCompatible, setIsBasicCompatible] = useState(true);

// Check compatibility when rule data loads
useEffect(() => {
  if (existingRule) {
    const compatible = checkBasicCompatibility(existingRule);
    setIsBasicCompatible(compatible);
    if (!compatible) setViewMode("advanced");
  }
}, [existingRule]);
```

2. Add toggle to modal header:
```tsx
<DialogHeader>
  <div className="flex items-center justify-between">
    <DialogTitle>{rule ? "Edit Rule" : "Create Rule"}</DialogTitle>
    <ViewToggle
      value={viewMode}
      onChange={setViewMode}
      canUseBasic={isBasicCompatible}
    />
  </div>
</DialogHeader>
```

3. Conditional rendering:
```tsx
<DialogContent>
  {viewMode === "basic" ? (
    <BasicRuleBuilder
      conditions={basicConditions}
      onConditionsChange={setBasicConditions}
      // ... other props
    />
  ) : (
    <AdvancedRuleBuilder
      conditions={advancedConditions}
      onConditionsChange={setAdvancedConditions}
      // ... existing advanced builder
    />
  )}
</DialogContent>
```

4. Conversion utilities:
```tsx
// apps/web/lib/valuation-conversion.ts
export function checkBasicCompatibility(rule: any): boolean {
  // Check if rule can be displayed in Basic view
  const hasFormulas = rule.actions.some((a: any) => a.formula);
  const hasNestedConditions = rule.conditions.some((c: any) => c.is_group);
  const hasUnsupportedOperators = rule.conditions.some((c: any) =>
    !["equals", "gt", "lt", "gte", "lte", "contains"].includes(c.operator)
  );

  return !hasFormulas && !hasNestedConditions && !hasUnsupportedOperators;
}

export function convertBasicToAdvanced(basicData: any) {
  // Convert Basic view data to Advanced schema
  return {
    conditions: basicData.conditions.map((c: any) => ({
      id: crypto.randomUUID(),
      field_name: c.field,
      operator: c.operator,
      value: c.value,
      logical_operator: basicData.logicalOperator,
    })),
    actions: [{
      id: crypto.randomUUID(),
      action_type: basicData.mode === "quantity" ? "per_unit" : "fixed_value",
      value_usd: basicData.valuePerUnit,
      // ... rest of conversion
    }],
  };
}

export function convertAdvancedToBasic(advancedData: any) {
  // Only called if checkBasicCompatibility returns true
  return {
    conditions: advancedData.conditions.map((c: any) => ({
      field: c.field_name,
      operator: c.operator,
      value: c.value,
    })),
    logicalOperator: advancedData.conditions[0]?.logical_operator || "AND",
    mode: advancedData.actions[0]?.action_type === "per_unit" ? "quantity" : "fixed",
    valuePerUnit: advancedData.actions[0]?.value_usd || 0,
  };
}
```

**Testing:**
- [ ] Create rule in Basic view → saves correctly
- [ ] Edit rule in Basic view → updates correctly
- [ ] Switch Basic → Advanced → data preserved
- [ ] Switch Advanced → Basic (compatible rule) → data preserved
- [ ] Try to switch Advanced → Basic (incompatible) → warning shown, stays in Advanced
- [ ] Create complex rule in Advanced → toggle disabled for Basic
- [ ] localStorage persists view preference across sessions

---

## Testing Strategy

### Unit Tests (Jest/Vitest)

**Files to Test:**
```
apps/web/__tests__/valuation-conversion.test.ts
apps/web/__tests__/smart-dropdown.test.tsx
apps/web/__tests__/basic-rule-builder.test.tsx
```

**Example Test:**
```tsx
// valuation-conversion.test.ts
import { checkBasicCompatibility, convertBasicToAdvanced } from "@/lib/valuation-conversion";

describe("Valuation Conversion", () => {
  it("identifies Basic-compatible rules", () => {
    const simpleRule = {
      conditions: [{ field_name: "ram_gb", operator: "gte", value: 16 }],
      actions: [{ action_type: "per_unit", value_usd: 3 }],
    };
    expect(checkBasicCompatibility(simpleRule)).toBe(true);
  });

  it("identifies Advanced-only rules", () => {
    const complexRule = {
      conditions: [{ is_group: true, children: [...] }],
      actions: [{ action_type: "formula", formula: "ram_gb * 2 + cpu_score" }],
    };
    expect(checkBasicCompatibility(complexRule)).toBe(false);
  });

  it("converts Basic to Advanced format", () => {
    const basicData = {
      conditions: [{ field: "ram_gb", operator: "gte", value: "16" }],
      logicalOperator: "AND",
      mode: "quantity",
      valuePerUnit: 3,
    };
    const advanced = convertBasicToAdvanced(basicData);
    expect(advanced.conditions[0].field_name).toBe("ram_gb");
    expect(advanced.actions[0].action_type).toBe("per_unit");
  });
});
```

### Integration Tests (Playwright)

**Test Scenarios:**
1. **Managed Field Editing Flow:**
   - Navigate to Listings page
   - Click CPU cell → select different CPU → verify save
   - Check network request: `PATCH /api/v1/listings/123`
   - Verify: Cell shows new value, no errors

2. **Tooltip Flow:**
   - Navigate to Listings page
   - Hover RAM column header → tooltip appears
   - Tab to info icon → tooltip appears
   - Press Escape → tooltip disappears

3. **Dropdown UX Flow:**
   - Open Add Listing modal
   - Click Storage Type dropdown
   - Verify: Dropdown width ≥ longest option width
   - Verify: All options readable without scrolling

4. **Basic Valuation Flow:**
   - Navigate to Valuation Rules
   - Click "Add Rule"
   - Verify: Basic view shown by default
   - Add condition: RAM ≥ 16GB
   - Set action: $3 per GB
   - Save rule
   - Verify: Rule created successfully

5. **Bug Regression:**
   - Edit existing valuation rule
   - Modify conditions and actions
   - Click Update
   - Verify: No console errors, rule saves successfully

---

## Deployment Checklist

### Pre-Deployment

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] No TypeScript errors (`pnpm --filter web typecheck`)
- [ ] No ESLint warnings (`pnpm --filter web lint`)
- [ ] Build succeeds (`pnpm --filter web build`)
- [ ] Manual testing complete (see Testing Strategy)

### Database Migrations

- [ ] No migrations required (all changes use existing schema)
- [ ] Optional: Seed descriptions for managed fields:
  ```sql
  UPDATE entity_fields SET description = 'The processor model (Intel/AMD) powering this system' WHERE entity_type = 'listing' AND field_key = 'cpu';
  -- ... etc for other fields
  ```

### Environment Variables

- [ ] No new env vars required
- [ ] Verify existing vars still valid

### Feature Flags (Optional)

If using feature flags:
```typescript
// lib/feature-flags.ts
export const FEATURE_FLAGS = {
  MANAGED_FIELD_EDITING: process.env.NEXT_PUBLIC_ENABLE_MANAGED_FIELD_EDITING === "true",
  BASIC_VALUATION_VIEW: process.env.NEXT_PUBLIC_ENABLE_BASIC_VALUATION === "true",
};
```

Wrap features:
```tsx
{FEATURE_FLAGS.MANAGED_FIELD_EDITING && <EditableCPUCell />}
```

### Rollback Plan

If critical issues arise:
1. **Frontend Only:** Revert to previous commit, redeploy
2. **Backend Bug:** Apply hotfix to `apps/api/dealbrain_api/api/rules.py`
3. **Database Issue:** None (no schema changes)

### Monitoring

Post-deployment, monitor:
- Error rates in Sentry/logging service
- API response times for `/listings/{id}` PATCH endpoint
- React Query cache hit rates
- User feedback on new features

---

## Timeline Estimate

| Phase | Task | Hours | Dependencies |
|-------|------|-------|--------------|
| 1 | Fix React key warnings | 1 | None |
| 1 | Fix AttributeError bug | 2 | None |
| 1 | Test bug fixes | 1 | Phases 1.1, 1.2 |
| 2 | Enable managed field editing | 4 | Phase 1 complete |
| 2 | Create editable cell components | 2 | Phase 2.1 |
| 3 | Add tooltip support to DataGrid | 2 | None |
| 3 | Create InfoTooltip component | 1 | None |
| 3 | Update all column definitions | 1 | Phase 3.1 |
| 4 | Create SmartDropdown component | 3 | None |
| 4 | Replace existing dropdowns | 2 | Phase 4.1 |
| 4 | Test dropdown UX | 1 | Phase 4.2 |
| 5 | Create ViewToggle component | 1 | None |
| 5 | Create BasicRuleBuilder | 4 | None |
| 5 | Create BasicActionBuilder | 3 | None |
| 5 | Conversion utilities | 2 | None |
| 5 | Integrate into modal | 2 | Phases 5.1-5.4 |
| - | Integration testing | 4 | All phases |
| - | Bug fixes & polish | 4 | Testing |

**Total:** ~40 hours (~1 week for solo developer)

**Critical Path:** Phase 1 (bugs) → Phase 2 (managed fields) → Phase 5 (basic view)

---

## Success Criteria

### Functional Requirements Met
- ✅ Managed fields (CPU, GPU, RAM, Storage) are editable in listings table
- ✅ Column headers show info icon with descriptions
- ✅ Dropdowns size based on content, not column width
- ✅ Basic valuation view available with quantity-based pricing
- ✅ View toggle persists preference
- ✅ React key warnings eliminated
- ✅ AttributeError bug fixed

### Non-Functional Requirements Met
- ✅ Dropdown render <100ms
- ✅ Managed field save <300ms
- ✅ WCAG AA compliance maintained
- ✅ No new console errors/warnings
- ✅ All tests passing

### User Acceptance
- ✅ User can edit CPU without errors
- ✅ User understands column meanings via tooltips
- ✅ User can read all dropdown options without scrolling
- ✅ User creates basic valuation in <60 seconds
- ✅ User can switch between Basic/Advanced views without data loss

---

## Post-Implementation

### Documentation Updates

1. **Update CLAUDE.md:**
   - Add managed field editing section
   - Document Basic vs Advanced valuation views
   - Update tooltip usage patterns

2. **Update API docs:**
   - Confirm PATCH `/api/v1/listings/{id}` accepts managed fields
   - No new endpoints to document

3. **Create user guide:**
   - How to use Basic valuation view
   - When to use Advanced view
   - Managed field editing best practices

### Future Enhancements

Ideas for next iteration:
- **Basic View Improvements:**
  - Support for fixed value tables (current: quantity-based only)
  - Import/export valuation templates
  - Copy rule from existing

- **Dropdown Enhancements:**
  - Recently used options at top
  - Fuzzy search in large dropdowns
  - Keyboard shortcuts (e.g., type "nv" → jumps to "NVMe")

- **Tooltip Improvements:**
  - Rich tooltips with examples
  - Inline help documentation
  - Context-aware tips

---

## Appendix

### A. API Endpoint Reference

**Existing Endpoints Used:**

1. **Update Listing (Managed Fields):**
   ```
   PATCH /api/v1/listings/{id}
   Body: { cpu_id?: number, gpu_id?: number, ram_gb?: number, storage_gb?: number, storage_type?: string }
   Response: Listing
   ```

2. **List Entity Fields (For Descriptions):**
   ```
   GET /api/v1/entity-fields?entity_type=listing
   Response: EntityField[]
   ```

3. **Update Valuation Rule (Bug Fix):**
   ```
   PUT /api/v1/valuation-rules/{rule_id}
   Body: RuleUpdateRequest
   Response: RuleResponse
   ```

### B. Component Dependency Graph

```
SmartDropdown
├── Used by: EditableRAMCell
├── Used by: EditableStorageCell
├── Used by: BasicRuleBuilder
└── Used by: GlobalFieldModal

InfoTooltip
├── Used by: DataGrid (column headers)
└── Used by: Any component needing help text

BasicRuleBuilder
├── Uses: SmartDropdown
├── Uses: BasicActionBuilder
└── Used by: RuleBuilderModal

ViewToggle
└── Used by: RuleBuilderModal
```

### C. Migration Notes

**From Current State to New State:**

1. **Listings Table:**
   - Before: Managed fields read-only
   - After: All fields editable with inline editors
   - Breaking Changes: None
   - Data Migration: None required

2. **Dropdowns:**
   - Before: Fixed width based on column
   - After: Dynamic width based on content
   - Breaking Changes: None (visual only)
   - Migration: Gradually replace Select with SmartDropdown

3. **Valuation Rules:**
   - Before: Single complex builder
   - After: Basic/Advanced dual views
   - Breaking Changes: None (data model unchanged)
   - Migration: Existing rules work in Advanced view
