# Implementation Plan: Enhanced Rule Builder

**Version:** 1.0
**Date:** 2025-10-03
**Status:** Ready for Development
**Lead:** Technical Architect

---

## Overview

This document provides the technical implementation plan for the Enhanced Rule Builder feature as defined in the PRD. The implementation is structured in 6 phases over 8 weeks, with clear milestones, technical specifications, and acceptance criteria for each phase.

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
├─────────────────────────────────────────────────────────────┤
│  RuleBuilderModal (Enhanced)                                 │
│  ├── ConditionBuilder (NEW)                                  │
│  │   ├── EntityFieldSelector (NEW)                           │
│  │   ├── OperatorSelector (Enhanced)                         │
│  │   ├── ValueInput (Polymorphic, NEW)                       │
│  │   └── ConditionGroup (Nested, NEW)                        │
│  ├── ActionBuilder (Enhanced)                                │
│  │   └── ConditionMultiplierEditor (NEW)                     │
│  ├── RulePreviewPanel (NEW)                                  │
│  │   ├── SampleListingSelector (NEW)                         │
│  │   ├── BeforeAfterComparison (NEW)                         │
│  │   └── ImpactStatistics (NEW)                              │
│  └── VersionHistoryDrawer (NEW)                              │
│      ├── VersionList (NEW)                                   │
│      └── VersionDiff (NEW)                                   │
└─────────────────────────────────────────────────────────────┘
                             ↕ REST API
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│  API Endpoints                                               │
│  ├── GET /api/entities/metadata (NEW)                        │
│  ├── POST /api/rules/preview (NEW)                           │
│  ├── GET /api/rules/{id}/versions (NEW)                      │
│  ├── POST /api/rules/{id}/rollback (NEW)                     │
│  └── POST/PATCH /api/rules (Enhanced)                        │
│                                                              │
│  Services Layer                                              │
│  ├── FieldMetadataService (NEW)                              │
│  ├── RulePreviewService (Enhanced)                           │
│  ├── RuleVersionService (NEW)                                │
│  └── RuleEvaluationService (Enhanced)                        │
│                                                              │
│  Domain Logic (packages/core)                                │
│  ├── valuation.py (Enhanced)                                 │
│  └── rule_evaluator.py (NEW)                                 │
└─────────────────────────────────────────────────────────────┘
                             ↕ SQLAlchemy
┌─────────────────────────────────────────────────────────────┐
│                    Database (PostgreSQL)                     │
├─────────────────────────────────────────────────────────────┤
│  valuation_rule_v2 (Existing)                                │
│  valuation_rule_condition (Enhanced w/ parent_condition_id)  │
│  valuation_rule_action (Enhanced w/ modifiers_json)          │
│  valuation_rule_version (Existing)                           │
│  valuation_rule_audit (Existing)                             │
│  custom_field_definition (Existing)                          │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow: Rule Creation with Preview

1. User opens Rule Builder Modal
2. Frontend fetches entity metadata from `/api/entities/metadata`
3. User selects Entity → Field → Operator → Value
4. On condition change, frontend debounces and calls `/api/rules/preview`
5. Backend evaluates rule against sample listings
6. Frontend displays before/after comparison and statistics
7. User adds actions with condition multipliers
8. Preview updates with action impacts
9. User saves rule via `POST /api/rules`
10. Backend creates rule, auto-generates version entry, logs audit
11. Frontend refreshes rule list and closes modal

---

## Phase 1: Foundation (Week 1-2)

### Goals
- Establish backend infrastructure for field metadata and rule preview
- Build core frontend components for entity/field selection
- Implement basic real-time preview

### Backend Tasks

#### Task 1.1: Create Field Metadata Service
**File:** `apps/api/dealbrain_api/services/field_metadata.py`

```python
"""Service for providing entity and field metadata to frontend."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .field_registry import FieldRegistry
from .custom_fields import CustomFieldService


@dataclass
class OperatorDefinition:
    """Operator metadata for frontend."""
    value: str
    label: str
    field_types: list[str]  # Applicable data types


@dataclass
class FieldMetadata:
    """Field metadata for condition builder."""
    key: str
    label: str
    data_type: str
    description: str | None = None
    options: list[str] | None = None  # For enum/dropdown fields
    validation: dict[str, Any] | None = None
    is_custom: bool = False


@dataclass
class EntityMetadata:
    """Entity metadata for condition builder."""
    key: str
    label: str
    fields: list[FieldMetadata]


class FieldMetadataService:
    """Provides structured metadata for rule builder UI."""

    OPERATORS = [
        OperatorDefinition("equals", "Equals", ["string", "number", "enum", "boolean"]),
        OperatorDefinition("not_equals", "Not Equals", ["string", "number", "enum", "boolean"]),
        OperatorDefinition("greater_than", "Greater Than", ["number", "date"]),
        OperatorDefinition("less_than", "Less Than", ["number", "date"]),
        OperatorDefinition("gte", "Greater Than or Equal", ["number", "date"]),
        OperatorDefinition("lte", "Less Than or Equal", ["number", "date"]),
        OperatorDefinition("contains", "Contains", ["string"]),
        OperatorDefinition("starts_with", "Starts With", ["string"]),
        OperatorDefinition("ends_with", "Ends With", ["string"]),
        OperatorDefinition("in", "In", ["string", "enum", "number"]),
        OperatorDefinition("not_in", "Not In", ["string", "enum", "number"]),
        OperatorDefinition("between", "Between", ["number", "date"]),
    ]

    def __init__(self, field_registry: FieldRegistry | None = None):
        self.field_registry = field_registry or FieldRegistry()

    async def get_entities_metadata(self, db: AsyncSession) -> list[EntityMetadata]:
        """Fetch all entities with their fields."""
        entities = []

        # Listing entity
        listing_schema = await self.field_registry.schema_for(db, "listing")
        listing_fields = [
            FieldMetadata(
                key=f["key"],
                label=f["label"],
                data_type=f["data_type"],
                description=f.get("description"),
                options=f.get("options"),
                is_custom=f.get("origin") == "custom",
            )
            for f in listing_schema["fields"]
        ]
        entities.append(EntityMetadata(key="listing", label="Listing", fields=listing_fields))

        # CPU entity (nested under listing.cpu)
        entities.append(
            EntityMetadata(
                key="cpu",
                label="CPU",
                fields=[
                    FieldMetadata("cpu_mark_multi", "CPU Mark (Multi-Core)", "number"),
                    FieldMetadata("cpu_mark_single", "CPU Mark (Single-Core)", "number"),
                    FieldMetadata("name", "CPU Name", "string"),
                    FieldMetadata("manufacturer", "Manufacturer", "enum", options=["Intel", "AMD"]),
                    FieldMetadata("cores", "Cores", "number"),
                    FieldMetadata("threads", "Threads", "number"),
                    FieldMetadata("tdp_w", "TDP (Watts)", "number"),
                ],
            )
        )

        # GPU entity
        entities.append(
            EntityMetadata(
                key="gpu",
                label="GPU",
                fields=[
                    FieldMetadata("gpu_mark", "GPU Mark", "number"),
                    FieldMetadata("metal_score", "Metal Score", "number"),
                    FieldMetadata("name", "GPU Name", "string"),
                    FieldMetadata("manufacturer", "Manufacturer", "enum", options=["NVIDIA", "AMD", "Intel"]),
                ],
            )
        )

        return entities

    def get_operators_for_field_type(self, field_type: str) -> list[OperatorDefinition]:
        """Get valid operators for a given field type."""
        return [op for op in self.OPERATORS if field_type in op.field_types]
```

**Migration Required:** None (uses existing tables)

**Tests:**
- `test_get_entities_metadata`: Verify all entities returned with correct fields
- `test_custom_field_integration`: Ensure custom fields included in listing entity
- `test_operators_for_field_type`: Validate operator filtering by type

---

#### Task 1.2: Create API Endpoint for Entity Metadata
**File:** `apps/api/dealbrain_api/api/entities.py` (NEW)

```python
"""Endpoints for entity and field metadata."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..services.field_metadata import FieldMetadataService


router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/metadata")
async def get_entities_metadata(
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Get metadata for all entities and fields for rule builder."""
    service = FieldMetadataService()
    entities = await service.get_entities_metadata(db)

    return {
        "entities": [
            {
                "key": entity.key,
                "label": entity.label,
                "fields": [
                    {
                        "key": field.key,
                        "label": field.label,
                        "data_type": field.data_type,
                        "description": field.description,
                        "options": field.options,
                        "is_custom": field.is_custom,
                        "validation": field.validation,
                    }
                    for field in entity.fields
                ],
            }
            for entity in entities
        ],
        "operators": [
            {
                "value": op.value,
                "label": op.label,
                "field_types": op.field_types,
            }
            for op in FieldMetadataService.OPERATORS
        ],
    }
```

**Register in main app:**
```python
# apps/api/dealbrain_api/main.py
from .api import entities

app.include_router(entities.router, prefix="/api")
```

**Tests:**
- `test_entities_metadata_endpoint`: GET request returns valid structure
- `test_operators_included`: Verify operators list in response
- `test_custom_fields_included`: Ensure custom fields appear in listing entity

---

#### Task 1.3: Enhance Rule Preview Service
**File:** `apps/api/dealbrain_api/services/rule_preview.py` (Enhance existing)

Add support for nested conditions and detailed match indicators.

```python
# Add to existing RulePreviewService

async def preview_rule_with_details(
    self,
    db: AsyncSession,
    conditions: list[dict],
    actions: list[dict],
    sample_listing_ids: list[int] | None = None,
    sample_size: int = 10,
) -> dict:
    """
    Preview rule with detailed match indicators for each condition.

    Returns:
        {
            "statistics": {...},
            "sample_matched": [
                {
                    "id": 123,
                    "title": "...",
                    "original_price": 599.99,
                    "adjusted_price": 549.99,
                    "adjustment": -50.00,
                    "condition_results": [
                        {"condition": "cpu.cpu_mark_multi > 10000", "matched": true, "value": 15000},
                        {"condition": "listing.condition = new", "matched": true, "value": "new"}
                    ]
                }
            ],
            "sample_non_matched": [
                {
                    "id": 456,
                    "title": "...",
                    "original_price": 399.99,
                    "reason": "CPU Mark is 7500, requires >10000",
                    "condition_results": [...]
                }
            ]
        }
    """
    # Implementation here - evaluate conditions individually
    # Track which conditions pass/fail for each listing
    # Return detailed breakdown for UI display
    pass
```

**Tests:**
- `test_preview_with_nested_conditions`: Verify OR/AND group evaluation
- `test_condition_match_details`: Ensure individual condition results tracked
- `test_non_match_reason_generation`: Validate helpful error messages

---

#### Task 1.4: Create API Endpoint for Rule Preview
**File:** `apps/api/dealbrain_api/api/rules.py` (Enhance existing)

```python
# Add to existing rules router

from ..services.rule_preview import RulePreviewService
from ..schemas.rules import RulePreviewRequest, RulePreviewResponse


@router.post("/rules/preview", response_model=RulePreviewResponse)
async def preview_rule(
    request: RulePreviewRequest,
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Preview rule against sample listings without saving."""
    service = RulePreviewService()
    return await service.preview_rule_with_details(
        db,
        conditions=request.conditions,
        actions=request.actions,
        sample_listing_ids=request.sample_listing_ids,
        sample_size=request.sample_size,
    )
```

**Tests:**
- `test_preview_endpoint_valid_request`: Valid preview returns statistics
- `test_preview_with_sample_ids`: Specific listings used when provided
- `test_preview_invalid_conditions`: Graceful error handling

---

### Frontend Tasks

#### Task 1.5: Create Entity/Field Selector Component
**File:** `apps/web/components/valuation/entity-field-selector.tsx` (NEW)

```tsx
"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronsUpDown } from "lucide-react";

import { Button } from "../ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "../ui/command";
import { cn } from "../../lib/utils";
import { fetchEntitiesMetadata } from "../../lib/api/entities";

interface EntityFieldSelectorProps {
  value: string | null; // Format: "entity.field" (e.g., "listing.price_usd")
  onChange: (value: string, fieldType: string, options?: string[]) => void;
  placeholder?: string;
}

export function EntityFieldSelector({ value, onChange, placeholder }: EntityFieldSelectorProps) {
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const { data: metadata } = useQuery({
    queryKey: ["entities-metadata"],
    queryFn: fetchEntitiesMetadata,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Flatten entities and fields for searchable list
  const allFields = metadata?.entities.flatMap((entity) =>
    entity.fields.map((field) => ({
      key: `${entity.key}.${field.key}`,
      label: `${entity.label} → ${field.label}`,
      data_type: field.data_type,
      options: field.options,
      entity: entity.label,
      field: field.label,
    }))
  ) || [];

  const selectedField = allFields.find((f) => f.key === value);

  const handleSelect = (fieldKey: string) => {
    const field = allFields.find((f) => f.key === fieldKey);
    if (field) {
      onChange(fieldKey, field.data_type, field.options);
      setOpen(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          {selectedField ? selectedField.label : placeholder || "Select field..."}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0">
        <Command>
          <CommandInput placeholder="Search fields..." value={searchQuery} onValueChange={setSearchQuery} />
          <CommandEmpty>No field found.</CommandEmpty>
          {metadata?.entities.map((entity) => (
            <CommandGroup key={entity.key} heading={entity.label}>
              {entity.fields
                .filter((field) =>
                  field.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  field.key.toLowerCase().includes(searchQuery.toLowerCase())
                )
                .map((field) => {
                  const fieldKey = `${entity.key}.${field.key}`;
                  return (
                    <CommandItem
                      key={fieldKey}
                      value={fieldKey}
                      onSelect={handleSelect}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          value === fieldKey ? "opacity-100" : "opacity-0"
                        )}
                      />
                      <div>
                        <div>{field.label}</div>
                        {field.description && (
                          <div className="text-xs text-muted-foreground">{field.description}</div>
                        )}
                      </div>
                    </CommandItem>
                  );
                })}
            </CommandGroup>
          ))}
        </Command>
      </PopoverContent>
    </Popover>
  );
}
```

**Tests:**
- `test_field_selector_renders`: Component displays correctly
- `test_field_selection`: Selection updates parent state
- `test_field_search`: Search filters fields correctly

---

#### Task 1.6: Create Polymorphic Value Input Component
**File:** `apps/web/components/valuation/value-input.tsx` (NEW)

```tsx
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

  // Enum/dropdown fields
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
```

**Tests:**
- `test_string_input`: Text input for string fields
- `test_number_input`: Numeric validation for number fields
- `test_enum_dropdown`: Dropdown displays options correctly
- `test_boolean_checkbox`: Checkbox for boolean fields
- `test_multi_value_input`: Comma-separated input for "in" operator

---

#### Task 1.7: Create Basic Preview Panel
**File:** `apps/web/components/valuation/rule-preview-panel.tsx` (NEW)

```tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { previewRule } from "../../lib/api/rules";

interface RulePreviewPanelProps {
  conditions: any[];
  actions: any[];
  sampleListingId?: number;
}

export function RulePreviewPanel({ conditions, actions, sampleListingId }: RulePreviewPanelProps) {
  const { data, isLoading } = useQuery({
    queryKey: ["rule-preview", conditions, actions, sampleListingId],
    queryFn: () => previewRule({ conditions, actions, sample_listing_ids: sampleListingId ? [sampleListingId] : undefined }),
    enabled: conditions.length > 0 && actions.length > 0,
  });

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading preview...</div>;
  }

  if (!data) {
    return <div className="text-sm text-muted-foreground">Add conditions and actions to see preview</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Rule Preview</CardTitle>
        <CardDescription>Impact on sample listings</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Statistics */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Matched</div>
              <div className="text-2xl font-semibold">{data.statistics.matched_count}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Avg Adjustment</div>
              <div className="text-2xl font-semibold">
                ${data.statistics.avg_adjustment.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Total Listings</div>
              <div className="text-2xl font-semibold">{data.statistics.total_listings}</div>
            </div>
          </div>

          {/* Sample matched listings */}
          {data.sample_matched.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium">Sample Matched Listings</h4>
              <div className="space-y-2">
                {data.sample_matched.slice(0, 3).map((listing: any) => (
                  <div key={listing.id} className="rounded-lg border p-3">
                    <div className="font-medium">{listing.title}</div>
                    <div className="mt-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        ${listing.original_price} → ${listing.adjusted_price}
                      </span>
                      <span className={listing.adjustment < 0 ? "text-green-600" : "text-red-600"}>
                        {listing.adjustment > 0 ? "+" : ""}${listing.adjustment.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

**Tests:**
- `test_preview_statistics_display`: Statistics render correctly
- `test_sample_listings_display`: Sample listings shown with before/after
- `test_empty_state`: Proper message when no conditions/actions

---

#### Task 1.8: API Client Functions
**File:** `apps/web/lib/api/entities.ts` (NEW)

```typescript
import { API_URL } from "../utils";

export interface FieldMetadata {
  key: string;
  label: string;
  data_type: string;
  description?: string;
  options?: string[];
  is_custom: boolean;
}

export interface EntityMetadata {
  key: string;
  label: string;
  fields: FieldMetadata[];
}

export interface EntitiesMetadataResponse {
  entities: EntityMetadata[];
  operators: OperatorDefinition[];
}

export interface OperatorDefinition {
  value: string;
  label: string;
  field_types: string[];
}

export async function fetchEntitiesMetadata(): Promise<EntitiesMetadataResponse> {
  const response = await fetch(`${API_URL}/api/entities/metadata`);
  if (!response.ok) {
    throw new Error("Failed to fetch entities metadata");
  }
  return response.json();
}
```

**File:** `apps/web/lib/api/rules.ts` (Enhance existing)

```typescript
// Add to existing rules.ts

export interface RulePreviewRequest {
  conditions: any[];
  actions: any[];
  sample_listing_ids?: number[];
  sample_size?: number;
}

export interface RulePreviewResponse {
  statistics: {
    total_listings: number;
    matched_count: number;
    avg_adjustment: number;
    min_adjustment: number;
    max_adjustment: number;
  };
  sample_matched: any[];
  sample_non_matched: any[];
}

export async function previewRule(request: RulePreviewRequest): Promise<RulePreviewResponse> {
  const response = await fetch(`${API_URL}/api/rules/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error("Failed to preview rule");
  }
  return response.json();
}
```

**Tests:**
- `test_fetch_entities_metadata`: API call returns expected structure
- `test_preview_rule_api`: Preview request/response handling
- `test_api_error_handling`: Graceful error handling for failed requests

---

### Phase 1 Acceptance Criteria

- [ ] `/api/entities/metadata` endpoint returns all entities with fields
- [ ] `/api/rules/preview` endpoint evaluates conditions and returns statistics
- [ ] `EntityFieldSelector` component displays searchable field list
- [ ] `ValueInput` component adapts to field type (text, number, dropdown, checkbox)
- [ ] `RulePreviewPanel` displays matched listings count and average adjustment
- [ ] React Query caches metadata for 5 minutes to reduce API calls
- [ ] All unit tests pass with >80% coverage
- [ ] Integration tests verify end-to-end preview flow

---

## Phase 2: Advanced Logic (Week 3-4)

### Goals
- Implement nested condition groups with visual hierarchy
- Add drag-and-drop reordering for conditions
- Enhance action builder with condition multipliers
- Integrate custom field support throughout

### Backend Tasks

#### Task 2.1: Enhance Rule Evaluation for Nested Conditions
**File:** `packages/core/dealbrain_core/rule_evaluator.py` (NEW)

```python
"""Core logic for evaluating rules with nested conditions."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ConditionNode:
    """Tree node representing a condition or condition group."""
    field_name: str | None  # None for group nodes
    operator: str | None
    value: Any | None
    logical_operator: str  # "AND" or "OR"
    children: list["ConditionNode"] | None = None

    def is_group(self) -> bool:
        return self.field_name is None and self.children is not None

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Recursively evaluate this condition/group against context."""
        if self.is_group():
            return self._evaluate_group(context)
        else:
            return self._evaluate_condition(context)

    def _evaluate_group(self, context: dict[str, Any]) -> bool:
        """Evaluate child conditions with logical operator."""
        if not self.children:
            return True

        if self.logical_operator == "AND":
            return all(child.evaluate(context) for child in self.children)
        elif self.logical_operator == "OR":
            return any(child.evaluate(context) for child in self.children)
        else:
            raise ValueError(f"Unknown logical operator: {self.logical_operator}")

    def _evaluate_condition(self, context: dict[str, Any]) -> bool:
        """Evaluate single condition."""
        # Extract value from context using field_name (supports dot notation)
        actual_value = self._get_nested_value(context, self.field_name)

        # Apply operator comparison
        if self.operator == "equals":
            return actual_value == self.value
        elif self.operator == "not_equals":
            return actual_value != self.value
        elif self.operator == "greater_than":
            return actual_value > self.value
        elif self.operator == "less_than":
            return actual_value < self.value
        elif self.operator == "gte":
            return actual_value >= self.value
        elif self.operator == "lte":
            return actual_value <= self.value
        elif self.operator == "contains":
            return self.value in str(actual_value)
        elif self.operator == "in":
            return actual_value in self.value
        elif self.operator == "not_in":
            return actual_value not in self.value
        else:
            raise ValueError(f"Unknown operator: {self.operator}")

    @staticmethod
    def _get_nested_value(context: dict, path: str) -> Any:
        """Extract value from nested dict using dot notation."""
        keys = path.split(".")
        value = context
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif hasattr(value, key):
                value = getattr(value, key)
            else:
                return None
        return value


def parse_conditions_tree(conditions: list[dict]) -> ConditionNode:
    """Parse flat condition list into tree structure."""
    # Group conditions by parent_condition_id
    root_conditions = [c for c in conditions if c.get("parent_condition_id") is None]
    child_conditions = [c for c in conditions if c.get("parent_condition_id") is not None]

    # Build tree recursively
    # Implementation details...
    pass
```

**Tests:**
- `test_simple_condition_evaluation`: Single condition passes/fails correctly
- `test_and_group_evaluation`: All conditions must pass
- `test_or_group_evaluation`: At least one condition must pass
- `test_nested_groups`: Multi-level nesting works correctly
- `test_dot_notation_access`: Field paths like "cpu.cpu_mark_multi" resolve

---

#### Task 2.2: Update Database Models for Nested Conditions
**File:** Already exists in `apps/api/dealbrain_api/models/core.py`

No changes needed - `ValuationRuleCondition` already has `parent_condition_id` field.

**Migration:** None required

---

#### Task 2.3: Enhance Rule Preview Service for Condition Details
**File:** `apps/api/dealbrain_api/services/rule_preview.py` (Enhance)

Update `preview_rule_with_details` to track individual condition results:

```python
async def preview_rule_with_details(self, db: AsyncSession, ...) -> dict:
    # For each listing, evaluate each condition individually
    # Track pass/fail status and actual vs expected values
    # Generate helpful "reason" text for non-matched listings

    condition_results = []
    for condition in conditions:
        result = {
            "condition": self._format_condition_display(condition),
            "matched": self._evaluate_single_condition(listing, condition),
            "actual_value": self._get_field_value(listing, condition["field_name"]),
            "expected": condition["value"],
        }
        condition_results.append(result)

    # Generate human-readable reason for non-match
    reason = self._generate_non_match_reason(condition_results)
```

**Tests:**
- `test_condition_results_tracking`: Individual conditions tracked per listing
- `test_non_match_reason_generation`: Helpful messages generated
- `test_nested_condition_display`: Groups displayed correctly

---

### Frontend Tasks

#### Task 2.4: Create Condition Group Component
**File:** `apps/web/components/valuation/condition-group.tsx` (NEW)

```tsx
"use client";

import { useState } from "react";
import { Plus, X, GripVertical } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { ConditionRow } from "./condition-row";

interface ConditionGroupProps {
  conditions: any[];
  onConditionsChange: (conditions: any[]) => void;
  depth?: number; // Nesting level for visual indentation
}

export function ConditionGroup({ conditions, onConditionsChange, depth = 0 }: ConditionGroupProps) {
  const [logicalOperator, setLogicalOperator] = useState<"AND" | "OR">("AND");

  const addCondition = () => {
    onConditionsChange([
      ...conditions,
      {
        id: `cond-${Date.now()}`,
        field_name: "",
        operator: "equals",
        value: "",
        logical_operator: logicalOperator,
      },
    ]);
  };

  const addGroup = () => {
    onConditionsChange([
      ...conditions,
      {
        id: `group-${Date.now()}`,
        is_group: true,
        logical_operator: "OR",
        children: [],
      },
    ]);
  };

  const updateCondition = (index: number, updates: any) => {
    const newConditions = [...conditions];
    newConditions[index] = { ...newConditions[index], ...updates };
    onConditionsChange(newConditions);
  };

  const removeCondition = (index: number) => {
    onConditionsChange(conditions.filter((_, i) => i !== index));
  };

  const toggleLogicalOperator = () => {
    const newOp = logicalOperator === "AND" ? "OR" : "AND";
    setLogicalOperator(newOp);
    // Update all conditions in this group
    onConditionsChange(
      conditions.map((c) => ({ ...c, logical_operator: newOp }))
    );
  };

  return (
    <div
      className="space-y-2"
      style={{ paddingLeft: depth * 24 }}
    >
      {/* Logical Operator Toggle */}
      {conditions.length > 1 && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Join with:</span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={toggleLogicalOperator}
          >
            <Badge variant={logicalOperator === "AND" ? "default" : "secondary"}>
              {logicalOperator}
            </Badge>
          </Button>
        </div>
      )}

      {/* Conditions */}
      {conditions.map((condition, index) => (
        <div key={condition.id} className="flex gap-2">
          <div className="flex items-center">
            <GripVertical className="h-4 w-4 text-muted-foreground cursor-move" />
          </div>

          {condition.is_group ? (
            <div className="flex-1 rounded-lg border-2 border-dashed border-primary/20 p-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-medium">Condition Group</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeCondition(index)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <ConditionGroup
                conditions={condition.children || []}
                onConditionsChange={(children) =>
                  updateCondition(index, { children })
                }
                depth={depth + 1}
              />
            </div>
          ) : (
            <div className="flex-1">
              <ConditionRow
                condition={condition}
                onChange={(updates) => updateCondition(index, updates)}
                onRemove={() => removeCondition(index)}
              />
            </div>
          )}
        </div>
      ))}

      {/* Add Buttons */}
      <div className="flex gap-2">
        <Button type="button" variant="outline" size="sm" onClick={addCondition}>
          <Plus className="mr-2 h-4 w-4" />
          Add Condition
        </Button>
        {depth < 2 && ( // Limit nesting to 2 levels
          <Button type="button" variant="outline" size="sm" onClick={addGroup}>
            <Plus className="mr-2 h-4 w-4" />
            Add Group
          </Button>
        )}
      </div>
    </div>
  );
}
```

**Tests:**
- `test_add_condition`: New condition added correctly
- `test_add_group`: Nested group created
- `test_toggle_logical_operator`: AND/OR toggle updates conditions
- `test_remove_condition`: Condition removed from list
- `test_nesting_depth_limit`: Prevents >2 levels of nesting

---

#### Task 2.5: Create Condition Row Component
**File:** `apps/web/components/valuation/condition-row.tsx` (NEW)

```tsx
"use client";

import { X } from "lucide-react";
import { Button } from "../ui/button";
import { EntityFieldSelector } from "./entity-field-selector";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { ValueInput } from "./value-input";
import { useQuery } from "@tanstack/react-query";
import { fetchEntitiesMetadata } from "../../lib/api/entities";

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
          <Select
            value={condition.operator}
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

          {/* Value Input */}
          <ValueInput
            fieldType={fieldType}
            options={condition.options}
            value={condition.value}
            onChange={(value) => onChange({ value })}
            operator={condition.operator}
          />
        </div>
      </div>

      {/* Remove Button */}
      <Button type="button" variant="ghost" size="sm" onClick={onRemove}>
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

**Tests:**
- `test_field_selection_updates_operators`: Operator list filters by field type
- `test_value_input_adapts_to_field`: Input type changes based on field
- `test_remove_button`: Calls onRemove callback

---

#### Task 2.6: Add Drag-and-Drop to Condition Group
**File:** Enhance `apps/web/components/valuation/condition-group.tsx`

Install `@dnd-kit/core` and `@dnd-kit/sortable`:

```bash
pnpm add @dnd-kit/core @dnd-kit/sortable
```

Update `ConditionGroup` component:

```tsx
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

// Wrap each condition in SortableCondition component
function SortableCondition({ condition, ...props }: any) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: condition.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      {/* Render ConditionRow or nested ConditionGroup */}
    </div>
  );
}

// In ConditionGroup component
const sensors = useSensors(
  useSensor(PointerSensor),
  useSensor(KeyboardSensor, {
    coordinateGetter: sortableKeyboardCoordinates,
  })
);

function handleDragEnd(event: any) {
  const { active, over } = event;
  if (active.id !== over.id) {
    const oldIndex = conditions.findIndex((c) => c.id === active.id);
    const newIndex = conditions.findIndex((c) => c.id === over.id);
    onConditionsChange(arrayMove(conditions, oldIndex, newIndex));
  }
}

return (
  <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
    <SortableContext items={conditions.map((c) => c.id)} strategy={verticalListSortingStrategy}>
      {/* Render conditions */}
    </SortableContext>
  </DndContext>
);
```

**Tests:**
- `test_drag_and_drop_reorder`: Conditions reorder correctly
- `test_keyboard_navigation`: Keyboard controls work for accessibility
- `test_drag_between_groups`: Cannot drag between different groups

---

#### Task 2.7: Add Condition Multipliers to Action Builder
**File:** `apps/web/components/valuation/action-builder.tsx` (NEW)

```tsx
"use client";

import { useState } from "react";
import { Plus, X } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Textarea } from "../ui/textarea";

const ACTION_TYPES = [
  { value: "fixed_value", label: "Fixed Value" },
  { value: "per_unit", label: "Per Unit" },
  { value: "percentage", label: "Percentage" },
  { value: "benchmark_based", label: "Benchmark Based" },
  { value: "formula", label: "Formula" },
];

interface ActionBuilderProps {
  actions: any[];
  onActionsChange: (actions: any[]) => void;
}

export function ActionBuilder({ actions, onActionsChange }: ActionBuilderProps) {
  const addAction = () => {
    onActionsChange([
      ...actions,
      {
        id: `action-${Date.now()}`,
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

  const updateAction = (index: number, updates: any) => {
    const newActions = [...actions];
    newActions[index] = { ...newActions[index], ...updates };
    onActionsChange(newActions);
  };

  const removeAction = (index: number) => {
    onActionsChange(actions.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      {actions.map((action, index) => (
        <div key={action.id} className="rounded-lg border p-4 space-y-3">
          <div className="flex items-center justify-between">
            <Label>Action Type</Label>
            <Button type="button" variant="ghost" size="sm" onClick={() => removeAction(index)}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          <Select
            value={action.action_type}
            onValueChange={(value) => updateAction(index, { action_type: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ACTION_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Action-specific inputs */}
          {(action.action_type === "fixed_value" ||
            action.action_type === "per_unit" ||
            action.action_type === "benchmark_based") && (
            <div>
              <Label>Value (USD)</Label>
              <Input
                type="number"
                step="0.01"
                value={action.value_usd || ""}
                onChange={(e) =>
                  updateAction(index, { value_usd: parseFloat(e.target.value) || 0 })
                }
              />
            </div>
          )}

          {action.action_type === "formula" && (
            <div>
              <Label>Formula</Label>
              <Textarea
                placeholder="e.g., ram_gb * 2.5 + storage_gb * 0.1"
                value={action.formula || ""}
                onChange={(e) => updateAction(index, { formula: e.target.value })}
                rows={3}
              />
            </div>
          )}

          {/* Condition Multipliers */}
          <div className="space-y-2">
            <Label>Condition Multipliers</Label>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <Label className="text-xs">New</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  max="2"
                  value={action.modifiers?.condition_multipliers?.new || 1.0}
                  onChange={(e) =>
                    updateAction(index, {
                      modifiers: {
                        ...action.modifiers,
                        condition_multipliers: {
                          ...action.modifiers?.condition_multipliers,
                          new: parseFloat(e.target.value) || 1.0,
                        },
                      },
                    })
                  }
                />
              </div>
              <div>
                <Label className="text-xs">Refurbished</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  max="2"
                  value={action.modifiers?.condition_multipliers?.refurb || 0.75}
                  onChange={(e) =>
                    updateAction(index, {
                      modifiers: {
                        ...action.modifiers,
                        condition_multipliers: {
                          ...action.modifiers?.condition_multipliers,
                          refurb: parseFloat(e.target.value) || 0.75,
                        },
                      },
                    })
                  }
                />
              </div>
              <div>
                <Label className="text-xs">Used</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  max="2"
                  value={action.modifiers?.condition_multipliers?.used || 0.6}
                  onChange={(e) =>
                    updateAction(index, {
                      modifiers: {
                        ...action.modifiers,
                        condition_multipliers: {
                          ...action.modifiers?.condition_multipliers,
                          used: parseFloat(e.target.value) || 0.6,
                        },
                      },
                    })
                  }
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Adjust action value based on listing condition (1.0 = 100%)
            </p>
          </div>
        </div>
      ))}

      <Button type="button" variant="outline" onClick={addAction}>
        <Plus className="mr-2 h-4 w-4" />
        Add Action
      </Button>
    </div>
  );
}
```

**Tests:**
- `test_add_action`: New action added with defaults
- `test_action_type_selection`: Action type updates correctly
- `test_condition_multipliers_update`: Multipliers update independently
- `test_formula_input`: Formula actions show textarea

---

### Phase 2 Acceptance Criteria

- [ ] Condition groups support unlimited nesting (UI limits to 2 levels)
- [ ] Drag-and-drop reordering works for conditions within same group
- [ ] AND/OR toggle updates all conditions in group
- [ ] Action builder includes condition multiplier inputs
- [ ] Custom fields from `FieldRegistry` appear in entity selector
- [ ] Nested conditions save correctly to database with `parent_condition_id`
- [ ] Preview evaluates nested logic correctly
- [ ] All unit and integration tests pass

---

## Phase 3: Versioning (Week 5)

### Goals
- Implement version history display
- Build version comparison UI
- Add rollback functionality
- Create audit logging for all rule changes

### Backend Tasks

#### Task 3.1: Create Rule Version Service
**File:** `apps/api/dealbrain_api/services/rule_version.py` (NEW)

```python
"""Service for managing rule versions and history."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ValuationRuleV2, ValuationRuleVersion, ValuationRuleAudit


class RuleVersionService:
    """Manages rule versioning, comparison, and rollback."""

    async def create_version(
        self,
        db: AsyncSession,
        rule: ValuationRuleV2,
        changed_by: str | None = None,
        change_summary: str | None = None,
    ) -> ValuationRuleVersion:
        """Create a version snapshot of the current rule state."""
        snapshot = {
            "name": rule.name,
            "description": rule.description,
            "priority": rule.priority,
            "is_active": rule.is_active,
            "conditions": [
                {
                    "field_name": c.field_name,
                    "operator": c.operator,
                    "value": c.value_json,
                    "logical_operator": c.logical_operator,
                    "parent_condition_id": c.parent_condition_id,
                }
                for c in rule.conditions
            ],
            "actions": [
                {
                    "action_type": a.action_type,
                    "value_usd": a.value_usd,
                    "metric": a.metric,
                    "formula": a.formula,
                    "modifiers": a.modifiers_json,
                }
                for a in rule.actions
            ],
        }

        version = ValuationRuleVersion(
            rule_id=rule.id,
            version_number=rule.version,
            snapshot_json=snapshot,
            change_summary=change_summary,
            changed_by=changed_by,
        )
        db.add(version)
        await db.flush()
        return version

    async def get_versions(
        self,
        db: AsyncSession,
        rule_id: int,
    ) -> list[ValuationRuleVersion]:
        """Get all versions for a rule, ordered by version number desc."""
        result = await db.execute(
            select(ValuationRuleVersion)
            .where(ValuationRuleVersion.rule_id == rule_id)
            .order_by(ValuationRuleVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def compare_versions(
        self,
        db: AsyncSession,
        rule_id: int,
        version_a: int,
        version_b: int,
    ) -> dict:
        """Compare two versions and return diff."""
        versions = await self.get_versions(db, rule_id)
        v_a = next((v for v in versions if v.version_number == version_a), None)
        v_b = next((v for v in versions if v.version_number == version_b), None)

        if not v_a or not v_b:
            raise ValueError("Version not found")

        return self._generate_diff(v_a.snapshot_json, v_b.snapshot_json)

    def _generate_diff(self, snapshot_a: dict, snapshot_b: dict) -> dict:
        """Generate detailed diff between two snapshots."""
        diff = {
            "basic_info": {},
            "conditions": {"added": [], "removed": [], "modified": []},
            "actions": {"added": [], "removed": [], "modified": []},
        }

        # Compare basic fields
        for field in ["name", "description", "priority", "is_active"]:
            if snapshot_a.get(field) != snapshot_b.get(field):
                diff["basic_info"][field] = {
                    "old": snapshot_a.get(field),
                    "new": snapshot_b.get(field),
                }

        # Compare conditions (simplified - would need proper matching logic)
        # Implementation here...

        # Compare actions
        # Implementation here...

        return diff

    async def rollback_to_version(
        self,
        db: AsyncSession,
        rule_id: int,
        target_version: int,
        actor: str | None = None,
        reason: str | None = None,
    ) -> ValuationRuleV2:
        """Restore rule to a previous version (creates new version)."""
        rule = await db.get(ValuationRuleV2, rule_id)
        if not rule:
            raise ValueError("Rule not found")

        versions = await self.get_versions(db, rule_id)
        target = next((v for v in versions if v.version_number == target_version), None)
        if not target:
            raise ValueError(f"Version {target_version} not found")

        # Delete current conditions and actions
        for condition in rule.conditions:
            await db.delete(condition)
        for action in rule.actions:
            await db.delete(action)
        await db.flush()

        # Restore from snapshot
        snapshot = target.snapshot_json
        rule.name = snapshot["name"]
        rule.description = snapshot["description"]
        rule.priority = snapshot["priority"]
        rule.is_active = snapshot["is_active"]
        rule.version += 1

        # Recreate conditions and actions from snapshot
        # Implementation here...

        # Create version entry for rollback
        await self.create_version(
            db,
            rule,
            changed_by=actor,
            change_summary=f"Rolled back to version {target_version}. Reason: {reason or 'Not specified'}",
        )

        # Create audit log
        audit = ValuationRuleAudit(
            rule_id=rule.id,
            action="rollback",
            actor=actor,
            changes_json={
                "from_version": rule.version - 1,
                "to_version": target_version,
                "reason": reason,
            },
        )
        db.add(audit)

        await db.flush()
        await db.refresh(rule)
        return rule
```

**Tests:**
- `test_create_version`: Version snapshot created correctly
- `test_get_versions`: Versions returned in correct order
- `test_compare_versions`: Diff generated accurately
- `test_rollback_to_version`: Rule restored to previous state
- `test_rollback_creates_new_version`: Rollback creates version entry

---

#### Task 3.2: Create API Endpoints for Versioning
**File:** `apps/api/dealbrain_api/api/rules.py` (Enhance)

```python
# Add to existing rules router

from ..services.rule_version import RuleVersionService
from ..schemas.rules import (
    RuleVersionResponse,
    RuleVersionComparisonResponse,
    RollbackRequest,
)


@router.get("/rules/{rule_id}/versions", response_model=list[RuleVersionResponse])
async def get_rule_versions(
    rule_id: int,
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Get version history for a rule."""
    service = RuleVersionService()
    versions = await service.get_versions(db, rule_id)
    return [
        {
            "version_number": v.version_number,
            "created_at": v.created_at,
            "changed_by": v.changed_by,
            "change_summary": v.change_summary,
            "snapshot": v.snapshot_json,
        }
        for v in versions
    ]


@router.get(
    "/rules/{rule_id}/versions/compare",
    response_model=RuleVersionComparisonResponse,
)
async def compare_rule_versions(
    rule_id: int,
    version_a: int,
    version_b: int,
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Compare two versions of a rule."""
    service = RuleVersionService()
    return await service.compare_versions(db, rule_id, version_a, version_b)


@router.post("/rules/{rule_id}/rollback")
async def rollback_rule(
    rule_id: int,
    request: RollbackRequest,
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Rollback rule to a previous version."""
    service = RuleVersionService()
    rule = await service.rollback_to_version(
        db,
        rule_id,
        request.target_version,
        actor=request.actor,
        reason=request.reason,
    )
    await db.commit()
    return {
        "success": True,
        "new_version": rule.version,
        "restored_from": request.target_version,
        "message": f"Rule restored to version {request.target_version} as new version {rule.version}",
    }
```

**Add schemas:**
```python
# apps/api/dealbrain_api/schemas/rules.py

class RuleVersionResponse(BaseModel):
    version_number: int
    created_at: datetime
    changed_by: str | None
    change_summary: str | None
    snapshot: dict[str, Any]

class RuleVersionComparisonResponse(BaseModel):
    basic_info: dict[str, Any]
    conditions: dict[str, list]
    actions: dict[str, list]

class RollbackRequest(BaseModel):
    target_version: int
    actor: str | None = None
    reason: str | None = None
```

**Tests:**
- `test_get_versions_endpoint`: Returns version list
- `test_compare_versions_endpoint`: Returns diff structure
- `test_rollback_endpoint`: Rollback successful and returns new version

---

### Frontend Tasks

#### Task 3.3: Create Version History Drawer
**File:** `apps/web/components/valuation/version-history-drawer.tsx` (NEW)

```tsx
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { History, ChevronRight, RotateCcw } from "lucide-react";

import { Button } from "../ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "../ui/sheet";
import { Badge } from "../ui/badge";
import { useToast } from "../ui/use-toast";
import { fetchRuleVersions, rollbackRule } from "../../lib/api/rules";
import { VersionDiff } from "./version-diff";

interface VersionHistoryDrawerProps {
  ruleId: number;
  currentVersion: number;
}

export function VersionHistoryDrawer({ ruleId, currentVersion }: VersionHistoryDrawerProps) {
  const [open, setOpen] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState<[number, number] | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: versions, isLoading } = useQuery({
    queryKey: ["rule-versions", ruleId],
    queryFn: () => fetchRuleVersions(ruleId),
    enabled: open,
  });

  const rollbackMutation = useMutation({
    mutationFn: (targetVersion: number) =>
      rollbackRule(ruleId, targetVersion, "User rollback via UI"),
    onSuccess: (data) => {
      toast({
        title: "Rollback successful",
        description: data.message,
      });
      queryClient.invalidateQueries({ queryKey: ["ruleset"] });
      setOpen(false);
    },
    onError: (error: Error) => {
      toast({
        title: "Rollback failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleRollback = (version: number) => {
    if (confirm(`Rollback to version ${version}? This will create a new version.`)) {
      rollbackMutation.mutate(version);
    }
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm">
          <History className="mr-2 h-4 w-4" />
          Version History
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-[600px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Version History</SheetTitle>
          <SheetDescription>
            View and restore previous versions of this rule
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-3">
          {isLoading ? (
            <div className="text-sm text-muted-foreground">Loading versions...</div>
          ) : versions && versions.length > 0 ? (
            versions.map((version: any) => (
              <div
                key={version.version_number}
                className="rounded-lg border p-4 hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">Version {version.version_number}</span>
                      {version.version_number === currentVersion && (
                        <Badge>Current</Badge>
                      )}
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      {new Date(version.created_at).toLocaleString()}
                    </div>
                    {version.changed_by && (
                      <div className="mt-1 text-sm text-muted-foreground">
                        By: {version.changed_by}
                      </div>
                    )}
                    {version.change_summary && (
                      <div className="mt-2 text-sm">{version.change_summary}</div>
                    )}
                  </div>

                  {version.version_number !== currentVersion && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRollback(version.version_number)}
                      disabled={rollbackMutation.isPending}
                    >
                      <RotateCcw className="mr-2 h-4 w-4" />
                      Restore
                    </Button>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="text-sm text-muted-foreground">No version history available</div>
          )}
        </div>

        {selectedVersions && (
          <div className="mt-6">
            <h3 className="mb-3 font-semibold">Version Comparison</h3>
            <VersionDiff
              ruleId={ruleId}
              versionA={selectedVersions[0]}
              versionB={selectedVersions[1]}
            />
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
```

**Tests:**
- `test_version_list_display`: Versions render correctly
- `test_current_version_badge`: Current version highlighted
- `test_rollback_confirmation`: Confirmation dialog appears
- `test_rollback_success`: Success message shown after rollback

---

#### Task 3.4: Create Version Diff Component
**File:** `apps/web/components/valuation/version-diff.tsx` (NEW)

```tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { Alert, AlertDescription } from "../ui/alert";
import { Badge } from "../ui/badge";
import { compareRuleVersions } from "../../lib/api/rules";

interface VersionDiffProps {
  ruleId: number;
  versionA: number;
  versionB: number;
}

export function VersionDiff({ ruleId, versionA, versionB }: VersionDiffProps) {
  const { data: diff, isLoading } = useQuery({
    queryKey: ["rule-version-diff", ruleId, versionA, versionB],
    queryFn: () => compareRuleVersions(ruleId, versionA, versionB),
  });

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Comparing versions...</div>;
  }

  if (!diff) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Basic Info Changes */}
      {Object.keys(diff.basic_info).length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium">Basic Information</h4>
          <div className="space-y-2">
            {Object.entries(diff.basic_info).map(([field, change]: [string, any]) => (
              <Alert key={field}>
                <AlertDescription>
                  <strong>{field}:</strong>
                  <div className="mt-1 flex items-center gap-2">
                    <Badge variant="outline" className="bg-red-50">
                      {String(change.old)}
                    </Badge>
                    <span>→</span>
                    <Badge variant="outline" className="bg-green-50">
                      {String(change.new)}
                    </Badge>
                  </div>
                </AlertDescription>
              </Alert>
            ))}
          </div>
        </div>
      )}

      {/* Condition Changes */}
      <div>
        <h4 className="mb-2 text-sm font-medium">Conditions</h4>
        {diff.conditions.added.length > 0 && (
          <div className="mb-2">
            <Badge variant="outline" className="mb-1 bg-green-50">
              Added
            </Badge>
            {diff.conditions.added.map((condition: any, i: number) => (
              <div key={i} className="ml-2 text-sm text-muted-foreground">
                + {condition.field_name} {condition.operator} {String(condition.value)}
              </div>
            ))}
          </div>
        )}
        {diff.conditions.removed.length > 0 && (
          <div className="mb-2">
            <Badge variant="outline" className="mb-1 bg-red-50">
              Removed
            </Badge>
            {diff.conditions.removed.map((condition: any, i: number) => (
              <div key={i} className="ml-2 text-sm text-muted-foreground line-through">
                - {condition.field_name} {condition.operator} {String(condition.value)}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action Changes */}
      <div>
        <h4 className="mb-2 text-sm font-medium">Actions</h4>
        {/* Similar structure to conditions */}
      </div>
    </div>
  );
}
```

**Tests:**
- `test_diff_display`: Diff renders correctly
- `test_no_changes_display`: Message shown when versions identical
- `test_added_removed_highlighted`: Color coding correct

---

#### Task 3.5: API Client Functions for Versioning
**File:** `apps/web/lib/api/rules.ts` (Enhance)

```typescript
// Add to existing rules.ts

export interface RuleVersion {
  version_number: number;
  created_at: string;
  changed_by: string | null;
  change_summary: string | null;
  snapshot: any;
}

export interface RuleVersionDiff {
  basic_info: Record<string, { old: any; new: any }>;
  conditions: {
    added: any[];
    removed: any[];
    modified: any[];
  };
  actions: {
    added: any[];
    removed: any[];
    modified: any[];
  };
}

export async function fetchRuleVersions(ruleId: number): Promise<RuleVersion[]> {
  const response = await fetch(`${API_URL}/api/rules/${ruleId}/versions`);
  if (!response.ok) {
    throw new Error("Failed to fetch rule versions");
  }
  return response.json();
}

export async function compareRuleVersions(
  ruleId: number,
  versionA: number,
  versionB: number
): Promise<RuleVersionDiff> {
  const response = await fetch(
    `${API_URL}/api/rules/${ruleId}/versions/compare?version_a=${versionA}&version_b=${versionB}`
  );
  if (!response.ok) {
    throw new Error("Failed to compare versions");
  }
  return response.json();
}

export async function rollbackRule(
  ruleId: number,
  targetVersion: number,
  reason?: string
): Promise<{ success: boolean; new_version: number; message: string }> {
  const response = await fetch(`${API_URL}/api/rules/${ruleId}/rollback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_version: targetVersion, reason }),
  });
  if (!response.ok) {
    throw new Error("Failed to rollback rule");
  }
  return response.json();
}
```

**Tests:**
- `test_fetch_versions_api`: Versions fetched correctly
- `test_compare_versions_api`: Diff returned correctly
- `test_rollback_api`: Rollback request successful

---

### Phase 3 Acceptance Criteria

- [ ] Version history drawer displays all versions in chronological order
- [ ] Current version clearly marked with badge
- [ ] Rollback button creates new version (doesn't delete history)
- [ ] Version comparison shows added/removed/modified conditions and actions
- [ ] All version operations logged in `valuation_rule_audit` table
- [ ] Rollback confirmation dialog prevents accidental rollbacks
- [ ] Version metadata includes timestamp, author, and change summary
- [ ] All tests pass with >80% coverage

---

## Phase 4: Polish & Documentation (Week 6)

### Goals
- Add contextual help and tooltips
- Create rule template library
- Write user documentation
- Performance optimization

### Tasks

#### Task 4.1: Add Contextual Help System
**File:** `apps/web/components/ui/help-tooltip.tsx` (NEW)

```tsx
"use client";

import { HelpCircle } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "./popover";

interface HelpTooltipProps {
  title: string;
  content: string;
  example?: string;
}

export function HelpTooltip({ title, content, example }: HelpTooltipProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button type="button" className="ml-1 inline-flex items-center text-muted-foreground hover:text-foreground">
          <HelpCircle className="h-4 w-4" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <div className="space-y-2">
          <h4 className="font-semibold">{title}</h4>
          <p className="text-sm text-muted-foreground">{content}</p>
          {example && (
            <div className="mt-2 rounded-lg bg-muted p-2">
              <div className="text-xs font-medium">Example:</div>
              <code className="text-xs">{example}</code>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
```

Add tooltips throughout `RuleBuilderModal`:
- Condition fields: Explain dot notation for nested fields
- Operators: Explain when to use each operator
- Actions: Provide examples of each action type
- Condition multipliers: Explain how they affect final value

**Tests:**
- `test_tooltip_display`: Tooltip renders on hover
- `test_tooltip_content`: Content and examples correct

---

#### Task 4.2: Create Rule Template Library
**File:** `apps/web/lib/rule-templates.ts` (NEW)

```typescript
export interface RuleTemplate {
  name: string;
  description: string;
  category: string;
  conditions: any[];
  actions: any[];
}

export const RULE_TEMPLATES: RuleTemplate[] = [
  {
    name: "Basic RAM Valuation",
    description: "Deduct value based on RAM capacity",
    category: "Components",
    conditions: [
      {
        field_name: "listing.ram_gb",
        operator: "greater_than",
        value: 0,
      },
    ],
    actions: [
      {
        action_type: "per_unit",
        metric: "ram_gb",
        value_usd: -5.0,
        modifiers: {
          condition_multipliers: { new: 1.0, refurb: 0.75, used: 0.6 },
        },
      },
    ],
  },
  {
    name: "High-End CPU Premium",
    description: "Add premium for high-performance CPUs",
    category: "Performance",
    conditions: [
      {
        field_name: "cpu.cpu_mark_multi",
        operator: "greater_than",
        value: 20000,
      },
    ],
    actions: [
      {
        action_type: "fixed_value",
        value_usd: -100.0,
        modifiers: {
          condition_multipliers: { new: 1.0, refurb: 0.8, used: 0.6 },
        },
      },
    ],
  },
  {
    name: "Gaming GPU Discount",
    description: "Discount for systems with high-end gaming GPUs",
    category: "Performance",
    conditions: [
      {
        field_name: "gpu.gpu_mark",
        operator: "greater_than",
        value: 10000,
      },
      {
        field_name: "listing.condition",
        operator: "equals",
        value: "new",
      },
    ],
    actions: [
      {
        action_type: "fixed_value",
        value_usd: -75.0,
      },
    ],
  },
  {
    name: "SSD Capacity Scaling",
    description: "Adjust value based on SSD capacity",
    category: "Components",
    conditions: [
      {
        field_name: "listing.primary_storage_type",
        operator: "equals",
        value: "SSD",
      },
      {
        field_name: "listing.primary_storage_gb",
        operator: "greater_than",
        value: 0,
      },
    ],
    actions: [
      {
        action_type: "per_unit",
        metric: "primary_storage_gb",
        value_usd: -0.1,
        modifiers: {
          condition_multipliers: { new: 1.0, refurb: 0.75, used: 0.6 },
        },
      },
    ],
  },
  // Add more templates...
];
```

Add template selector to `RuleBuilderModal`:
```tsx
<Button
  type="button"
  variant="outline"
  onClick={() => setShowTemplates(true)}
>
  Load from Template
</Button>

{showTemplates && (
  <div className="mt-4 space-y-2">
    {RULE_TEMPLATES.map((template) => (
      <div
        key={template.name}
        className="cursor-pointer rounded-lg border p-3 hover:bg-accent"
        onClick={() => {
          setConditions(template.conditions);
          setActions(template.actions);
          setShowTemplates(false);
        }}
      >
        <div className="font-medium">{template.name}</div>
        <div className="text-sm text-muted-foreground">{template.description}</div>
      </div>
    ))}
  </div>
)}
```

**Tests:**
- `test_template_loading`: Template populates conditions and actions
- `test_template_categories`: Templates grouped by category

---

#### Task 4.3: Write User Documentation
**File:** `docs/user-guide/rule-builder.md` (NEW)

Create comprehensive user guide covering:
1. Introduction to valuation rules
2. Accessing the Rule Builder
3. Creating your first rule
4. Understanding conditions and operators
5. Working with actions
6. Using nested condition groups
7. Previewing rule impact
8. Managing rule versions
9. Best practices and tips
10. Troubleshooting common issues

Include screenshots and step-by-step walkthroughs.

---

#### Task 4.4: Performance Optimization

1. **Frontend Optimizations**
   - Debounce preview API calls (500ms)
   - Memoize expensive component renders
   - Lazy load version history drawer
   - Virtualize long condition lists (if >50 conditions)

2. **Backend Optimizations**
   - Add database indexes on frequently queried fields:
     ```sql
     CREATE INDEX idx_rule_condition_field ON valuation_rule_condition (field_name);
     CREATE INDEX idx_rule_condition_parent ON valuation_rule_condition (parent_condition_id);
     CREATE INDEX idx_rule_version_rule_id ON valuation_rule_version (rule_id, version_number DESC);
     ```
   - Cache entity metadata in Redis (5 min TTL)
   - Optimize preview query with selective field loading
   - Add query result caching for common rule evaluations

3. **Profiling and Benchmarking**
   - Profile rule evaluation with 1000 listings
   - Benchmark preview generation with complex nested conditions
   - Load test API endpoints with concurrent users
   - Optimize slow queries identified in profiling

**Tests:**
- `test_preview_performance`: Preview completes in <500ms for 10 listings
- `test_bulk_evaluation_performance`: 1000 listings evaluated in <30s
- `test_concurrent_rule_creation`: 10 users creating rules simultaneously

---

### Phase 4 Acceptance Criteria

- [ ] Contextual help tooltips on all complex fields
- [ ] Rule template library with 10+ templates
- [ ] User documentation published and accessible
- [ ] Preview debouncing reduces API calls by >70%
- [ ] Database indexes improve query performance by >50%
- [ ] All performance benchmarks met
- [ ] No critical accessibility issues (WCAG 2.1 AA)

---

## Phase 5: User Testing & Iteration (Week 7)

### Goals
- Beta test with 3-5 users
- Collect feedback on UX and functionality
- Fix critical issues and pain points
- Iterate on UI based on feedback

### Process

1. **Recruit Beta Testers**: 3-5 users from target personas
2. **Onboarding Session**: 30-min guided walkthrough of features
3. **Testing Period**: 1 week of real-world usage
4. **Feedback Collection**:
   - Daily usage logs via analytics
   - End-of-week survey
   - Exit interview with each tester
5. **Iteration**: Fix top 5 issues identified
6. **Validation**: Re-test with same users

### Acceptance Criteria

- [ ] 80% of beta testers successfully create complex rule (3+ conditions) without assistance
- [ ] Average rule creation time <3 minutes
- [ ] User satisfaction score >4.0/5.0
- [ ] No critical bugs reported
- [ ] All high-priority feedback addressed

---

## Phase 6: Production Release (Week 8)

### Goals
- Deploy to production environment
- Monitor usage and performance
- Provide user support
- Iterate based on production feedback

### Tasks

#### Task 6.1: Production Deployment Checklist

- [ ] All tests passing (unit, integration, E2E)
- [ ] Performance benchmarks met
- [ ] Database migrations tested on staging
- [ ] Backup/rollback plan documented
- [ ] Monitoring and alerting configured
- [ ] User documentation published
- [ ] Support team trained on new features
- [ ] Announcement/changelog prepared

#### Task 6.2: Monitoring Setup

1. **Application Metrics** (Prometheus):
   - Rule creation success rate
   - Preview response times
   - API error rates
   - Database query performance

2. **User Analytics**:
   - Feature adoption rates
   - Average rule complexity
   - Preview usage frequency
   - Version history access rate

3. **Alerts**:
   - Preview response time >1s
   - API error rate >5%
   - Database query time >500ms
   - Disk space <20% free

#### Task 6.3: Post-Launch Support

- **Week 1-2**: Daily monitoring, immediate issue response
- **Week 3-4**: Review analytics, identify improvement areas
- **Month 2**: Iterate on top 3 user requests
- **Month 3**: Evaluate against success metrics

### Acceptance Criteria

- [ ] Deployment successful with zero downtime
- [ ] No critical issues in first 48 hours
- [ ] User adoption >50% within first week
- [ ] All monitoring dashboards active and reviewed daily
- [ ] Support ticket volume <5/day related to rule builder

---

## Testing Strategy

### Unit Tests (Target: 85% Coverage)

**Backend:**
- Service layer methods (FieldMetadataService, RuleVersionService, etc.)
- Domain logic (rule_evaluator.py condition evaluation)
- Database model constraints and relationships

**Frontend:**
- Component rendering and user interactions
- API client functions
- State management logic

### Integration Tests

**Backend:**
- API endpoint request/response handling
- Service + database interactions
- Rule evaluation pipeline (conditions → actions → adjusted price)

**Frontend:**
- Form submission flows
- API integration with React Query
- Multi-component interactions (e.g., condition builder + preview panel)

### End-to-End Tests (Playwright/Cypress)

1. **Create Simple Rule Flow**
   - Open rule builder modal
   - Add condition (select entity, field, operator, value)
   - Add action (select type, enter value)
   - Preview shows matched listings
   - Save rule successfully

2. **Create Nested Rule Flow**
   - Create condition group
   - Add multiple conditions with AND/OR
   - Nest second group inside first
   - Verify preview evaluates correctly
   - Save and verify in database

3. **Version Rollback Flow**
   - Edit existing rule
   - Open version history
   - Compare two versions
   - Rollback to previous version
   - Verify rule restored correctly

4. **Template Loading Flow**
   - Open rule builder
   - Select template from library
   - Customize template conditions
   - Save as new rule

### Performance Tests (k6/Locust)

1. **Preview Endpoint Load Test**
   - 100 concurrent users
   - Each user creates rule with preview
   - Target: <500ms p95 response time

2. **Bulk Evaluation Test**
   - Apply 50-rule ruleset to 1000 listings
   - Target: <30s total execution time

3. **Concurrent Rule Creation**
   - 20 users creating rules simultaneously
   - Target: No database deadlocks, <2s save time

---

## Database Migrations

### Migration 1: Add Indexes (Phase 4)
```sql
-- Add indexes for performance
CREATE INDEX idx_rule_condition_field ON valuation_rule_condition (field_name);
CREATE INDEX idx_rule_condition_parent ON valuation_rule_condition (parent_condition_id);
CREATE INDEX idx_rule_version_rule_id ON valuation_rule_version (rule_id, version_number DESC);
CREATE INDEX idx_rule_audit_rule_id ON valuation_rule_audit (rule_id, created_at DESC);
```

**No schema changes required** - existing tables support all features.

---

## Rollback Plan

### Phase Rollback Procedures

**Phase 1-2 (Foundation/Advanced Logic):**
- Remove new API endpoints from router registration
- Revert frontend to previous `rule-builder-modal.tsx`
- No database changes to revert

**Phase 3 (Versioning):**
- Disable version history drawer (hide button)
- Keep version creation (no negative impact)
- Rollback can continue to function

**Phase 4-6 (Polish/Testing/Release):**
- Feature flag to disable enhanced builder
- Fallback to basic builder if errors occur
- Database transactions ensure no partial state

### Emergency Rollback (Production)
```bash
# 1. Deploy previous version
git revert <commit-hash>
make deploy

# 2. Disable feature flag (if implemented)
curl -X POST https://api.dealbrain.com/admin/flags/enhanced-rule-builder/disable

# 3. Monitor for errors
make logs-follow
```

---

## Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Complex nested conditions slow performance | Medium | High | Limit nesting depth to 2 levels, optimize evaluation algorithm, add caching |
| Preview API overloaded by debounce failures | Low | Medium | Implement rate limiting, increase debounce timeout, add loading states |
| Version history consumes excessive storage | Low | Low | Archive old versions after 1 year, compress snapshot JSON |
| Custom field changes break existing rules | Medium | High | Validate field references on custom field deletion, show warnings |
| Formula injection security vulnerability | Low | Critical | Server-side validation, sandboxed evaluation, whitelist allowed functions |

### User Adoption Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Users find nested logic too complex | Medium | High | Provide templates, tooltips, and documentation; limit nesting depth |
| Users bypass builder and edit DB directly | Low | Medium | Make builder so easy that DB edits unnecessary; audit trail detects manual changes |
| Preview confuses users (too much data) | Low | Medium | Progressive disclosure: show summary by default, expand for details |
| Version history unused | Medium | Low | Highlight in onboarding, show "Recently changed" indicator on rules |

---

## Success Metrics (90-Day Review)

### Adoption Metrics
- **Rule Creation Method**: 95%+ rules created via builder (vs. manual DB)
- **Feature Usage**: 80%+ users use preview, 60%+ access version history
- **Average Rule Complexity**: 3-5 conditions per rule (up from 1-2)

### Performance Metrics
- **Rule Creation Time**: <2 min for experienced users (down from 5+ min)
- **Preview Response Time**: p95 <500ms
- **Bulk Evaluation**: 1000 listings in <30s

### Quality Metrics
- **Invalid Rules**: <5% of created rules have errors (down from 30%+)
- **Rollbacks**: <10% of rules rolled back within 48 hours
- **Support Tickets**: <2 rule builder issues per week

### User Satisfaction
- **NPS Score**: >50
- **User Satisfaction**: >4.0/5.0
- **Feature Completeness**: >4.5/5.0

---

## Appendix A: API Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/entities/metadata` | Fetch entity and field metadata |
| POST | `/api/rules/preview` | Preview rule against sample listings |
| GET | `/api/rules/{id}/versions` | Get version history for rule |
| GET | `/api/rules/{id}/versions/compare` | Compare two versions |
| POST | `/api/rules/{id}/rollback` | Rollback to previous version |
| POST | `/api/rules` | Create new rule (enhanced) |
| PATCH | `/api/rules/{id}` | Update existing rule (enhanced) |

---

## Appendix B: Component File Structure

```
apps/web/components/valuation/
├── rule-builder-modal.tsx (Enhanced orchestrator)
├── condition-builder.tsx (NEW - main condition UI)
├── condition-group.tsx (NEW - nested groups)
├── condition-row.tsx (NEW - single condition)
├── entity-field-selector.tsx (NEW - field picker)
├── value-input.tsx (NEW - polymorphic input)
├── action-builder.tsx (NEW - action configuration)
├── rule-preview-panel.tsx (NEW - live preview)
├── version-history-drawer.tsx (NEW - version UI)
└── version-diff.tsx (NEW - version comparison)

apps/web/lib/api/
├── entities.ts (NEW - entity metadata client)
└── rules.ts (Enhanced - versioning functions)

apps/web/lib/
└── rule-templates.ts (NEW - template library)
```

---

## Appendix C: Key Dependencies

**Backend:**
- FastAPI (existing)
- SQLAlchemy (existing)
- Alembic (existing)
- Pydantic (existing)

**Frontend:**
- React 18 (existing)
- Next.js 14 (existing)
- React Query / TanStack Query (existing)
- Shadcn UI components (existing)
- `@dnd-kit/core` v6+ (NEW - drag and drop)
- `@dnd-kit/sortable` v7+ (NEW - sortable lists)

**Database:**
- PostgreSQL 14+ (existing)

---

## Conclusion

This implementation plan provides a comprehensive roadmap for building the Enhanced Rule Builder feature over 8 weeks across 6 phases. Each phase has clear goals, technical specifications, acceptance criteria, and testing requirements.

The phased approach ensures:
1. **Incremental delivery** - Core functionality first, polish later
2. **Risk mitigation** - Early testing catches issues before production
3. **User feedback integration** - Beta testing validates UX decisions
4. **Maintainability** - Comprehensive testing and documentation
5. **Performance** - Optimization built into the plan, not afterthought

By following this plan, you will deliver a world-class rule builder that empowers users to create sophisticated valuation logic with confidence and ease.
