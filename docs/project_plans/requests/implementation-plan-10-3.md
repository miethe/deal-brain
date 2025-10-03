# Implementation Plan: October 3 UX/Data Enhancements

**Version:** 1.0
**Date:** October 3, 2025
**Related PRD:** [prd-10-3-enhancements.md](./prd-10-3-enhancements.md)
**Related Tracking:** [tracking-ui-enhancements.md](../valuation-rules/tracking-ui-enhancements.md)

---

## Overview

This implementation plan delivers the October 3 enhancements across **5 focused phases** targeting listings valuation display, dropdown workflows, global fields management, and CPU data enrichment.

**Timeline:** 3 weeks
**Complexity:** Medium
**Risk Level:** Low (builds on existing patterns)

---

## Phase 1: Valuation Display Enhancement (Days 1-4)

### Goals
- Replace messy valuation text with clean, color-coded display
- Add interactive breakdown modal
- Implement configurable threshold system

### Tasks

#### 1.1 Backend: Settings Infrastructure

**File:** `apps/api/dealbrain_api/models/core.py`
- Add `ApplicationSettings` model:
```python
class ApplicationSettings(Base, TimestampMixin):
    __tablename__ = "application_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
```

**File:** `apps/api/alembic/versions/xxx_add_application_settings.py`
- Create migration for ApplicationSettings table
- Seed default valuation thresholds:
```python
{
    "valuation_thresholds": {
        "good_deal": 15.0,
        "great_deal": 25.0,
        "premium_warning": 10.0
    }
}
```

**File:** `apps/api/dealbrain_api/services/settings.py` (new)
- Create `SettingsService` class:
  - `get_setting(key: str) -> dict`
  - `update_setting(key: str, value: dict) -> dict`
- Add caching layer (Redis or in-memory)

**File:** `apps/api/dealbrain_api/api/settings.py` (new)
- Endpoints:
  - `GET /api/settings/{key}`
  - `PUT /api/settings/{key}`
- Mount in main router

**Acceptance Criteria:**
- [ ] Migration creates settings table and seeds thresholds
- [ ] API returns thresholds at `/api/settings/valuation_thresholds`
- [ ] Settings update persists and returns updated values

---

#### 1.2 Frontend: Valuation Cell Component

**File:** `apps/web/components/listings/valuation-cell.tsx` (new)
- Component structure:
```tsx
interface ValuationCellProps {
  adjustedPrice: number;
  listPrice: number;
  thresholds: ValuationThresholds;
  onDetailsClick: () => void;
}

export function ValuationCell({ adjustedPrice, listPrice, thresholds, onDetailsClick }: ValuationCellProps) {
  const delta = listPrice - adjustedPrice;
  const deltaPercent = (delta / listPrice) * 100;

  const { color, intensity, icon } = getValuationStyle(deltaPercent, thresholds);

  return (
    <div className="flex items-center gap-2">
      <span className="text-lg font-semibold">{formatCurrency(adjustedPrice)}</span>
      <DeltaBadge
        delta={delta}
        percent={deltaPercent}
        color={color}
        intensity={intensity}
        icon={icon}
      />
      <Button variant="ghost" size="sm" onClick={onDetailsClick}>
        <InfoIcon className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

**File:** `apps/web/components/listings/delta-badge.tsx` (new)
- Badge component with color variants:
  - Green variants: `bg-green-100 text-green-800` (light), `bg-green-600 text-white` (medium), `bg-green-800 text-white` (dark)
  - Red variants: `bg-red-100 text-red-800` (light), `bg-red-600 text-white` (dark)
  - Gray: `bg-gray-100 text-gray-600` (neutral)
- Icons: `ArrowDown` (savings), `ArrowUp` (premium), `Minus` (neutral)

**File:** `apps/web/lib/valuation-utils.ts` (new)
- Utility functions:
```typescript
export interface ValuationThresholds {
  good_deal: number;
  great_deal: number;
  premium_warning: number;
}

export function getValuationStyle(deltaPercent: number, thresholds: ValuationThresholds) {
  if (deltaPercent >= thresholds.great_deal) {
    return { color: 'green', intensity: 'dark', icon: 'arrow-down' };
  }
  if (deltaPercent >= thresholds.good_deal) {
    return { color: 'green', intensity: 'medium', icon: 'arrow-down' };
  }
  if (deltaPercent > 0) {
    return { color: 'green', intensity: 'light', icon: 'arrow-down' };
  }
  if (deltaPercent < 0 && Math.abs(deltaPercent) >= thresholds.premium_warning) {
    return { color: 'red', intensity: 'dark', icon: 'arrow-up' };
  }
  if (deltaPercent < 0) {
    return { color: 'red', intensity: 'light', icon: 'arrow-up' };
  }
  return { color: 'gray', intensity: 'light', icon: 'minus' };
}
```

**File:** `apps/web/hooks/use-valuation-thresholds.ts` (new)
- React Query hook:
```typescript
export function useValuationThresholds() {
  return useQuery({
    queryKey: ['settings', 'valuation_thresholds'],
    queryFn: async () => {
      const response = await apiFetch('/api/settings/valuation_thresholds');
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
```

**Acceptance Criteria:**
- [ ] ValuationCell renders with proper color coding
- [ ] Icons display correctly for savings/premium/neutral
- [ ] Component memoized to prevent re-renders
- [ ] Accessible (color + icon + text labels)

---

#### 1.3 Frontend: Enhanced Breakdown Modal

**File:** `apps/web/components/listings/valuation-breakdown-modal.tsx` (update existing)
- Enhancements:
  - Add grouped rule display (by category)
  - Show thumbnails if available
  - Improve layout with clear visual hierarchy
  - Add "Great Deal" or "Premium" badge based on thresholds

**Example Structure:**
```tsx
<ModalShell size="medium" title="Valuation Breakdown" onClose={onClose}>
  <div className="space-y-4">
    <div className="flex items-center gap-4">
      {listing.thumbnail_url && <img src={listing.thumbnail_url} className="w-20 h-20 rounded" />}
      <div>
        <h3 className="font-semibold">{listing.title}</h3>
        <ValuationCell {...cellProps} />
      </div>
    </div>

    <Separator />

    <div>
      <h4 className="font-medium mb-2">Base Price</h4>
      <p className="text-2xl">{formatCurrency(listing.list_price_usd)}</p>
    </div>

    <div>
      <h4 className="font-medium mb-2">Applied Rules</h4>
      {groupedRules.map(group => (
        <RuleGroupSection key={group.category} group={group} />
      ))}
    </div>

    <Separator />

    <div className="flex justify-between items-center">
      <span className="font-semibold">Adjusted Price</span>
      <span className="text-2xl font-bold">{formatCurrency(breakdown.adjusted_price_usd)}</span>
    </div>

    <Button asChild variant="link">
      <Link href={`/listings/${listing.id}/breakdown`}>View Full Breakdown →</Link>
    </Button>
  </div>
</ModalShell>
```

**Acceptance Criteria:**
- [ ] Modal groups rules by category
- [ ] Thumbnails display when available
- [ ] Responsive layout (mobile-friendly)
- [ ] Link to full breakdown page works

---

#### 1.4 Frontend: Integrate into Listings Table

**File:** `apps/web/components/listings/listings-table.tsx`
- Update valuation column definition:
```tsx
{
  accessorKey: "adjusted_price_usd",
  header: "Valuation",
  cell: ({ row }) => {
    const [showModal, setShowModal] = useState(false);
    const { data: thresholds } = useValuationThresholds();

    return (
      <>
        <ValuationCell
          adjustedPrice={row.original.adjusted_price_usd ?? 0}
          listPrice={row.original.list_price_usd ?? 0}
          thresholds={thresholds ?? DEFAULT_THRESHOLDS}
          onDetailsClick={() => setShowModal(true)}
        />
        {showModal && (
          <ValuationBreakdownModal
            listing={row.original}
            onClose={() => setShowModal(false)}
          />
        )}
      </>
    );
  },
  meta: {
    tooltip: "Adjusted price based on active ruleset. Click for breakdown.",
    filterType: "number",
  },
}
```

**File:** `apps/web/components/ui/data-grid.tsx`
- Verify number range filter works for valuation column
- Add percentage filter option (future enhancement)

**Acceptance Criteria:**
- [ ] Valuation column displays with new component
- [ ] Click opens breakdown modal
- [ ] Sorting by adjusted_price works
- [ ] Number filter works (min/max)

---

### Testing Checklist (Phase 1)

- [ ] Unit tests for `getValuationStyle` utility
- [ ] Integration test for settings API endpoints
- [ ] Visual regression test for ValuationCell variants
- [ ] Accessibility test (keyboard nav, screen reader, color blindness simulation)
- [ ] Performance test with 100+ row table

---

## Phase 2: Dropdown Inline Creation (Days 5-8)

### Goals
- Enable creating new dropdown options without leaving current context
- Clean up dropdown search field styling
- Apply to all dropdown fields (listings, CPUs, custom entities)

### Tasks

#### 2.1 Backend: Field Options Management

**File:** `apps/api/dealbrain_api/services/custom_fields.py`
- Add methods to `CustomFieldService`:
```python
async def add_field_option(
    self,
    session: AsyncSession,
    field_id: int,
    option_value: str
) -> CustomFieldDefinition:
    """Add new option to dropdown field."""
    field = await self.get_field_by_id(session, field_id)
    if field.data_type not in ("enum", "multi_select"):
        raise ValueError("Can only add options to dropdown fields")

    options = field.options or []
    if option_value in options:
        raise ValueError(f"Option '{option_value}' already exists")

    options.append(option_value)
    field.options = options
    await session.commit()
    return field

async def remove_field_option(
    self,
    session: AsyncSession,
    field_id: int,
    option_value: str,
    force: bool = False
) -> dict:
    """Remove option from dropdown field."""
    field = await self.get_field_by_id(session, field_id)

    # Check if option is used
    affected_count = await self._count_option_usage(session, field, option_value)
    if affected_count > 0 and not force:
        raise ValueError(f"Option is used by {affected_count} records. Use force=true to delete.")

    options = field.options or []
    if option_value not in options:
        raise ValueError(f"Option '{option_value}' not found")

    options.remove(option_value)
    field.options = options
    await session.commit()
    return {"success": True, "affected_records": affected_count}
```

**File:** `apps/api/dealbrain_api/api/fields.py`
- Add endpoints:
```python
@router.post("/{field_id}/options", response_model=FieldResponse)
async def add_field_option(
    field_id: int,
    request: FieldOptionRequest,
    session: AsyncSession = Depends(get_session)
):
    service = CustomFieldService()
    field = await service.add_field_option(session, field_id, request.value)
    return field

@router.delete("/{field_id}/options/{option_value}")
async def remove_field_option(
    field_id: int,
    option_value: str,
    force: bool = Query(False),
    session: AsyncSession = Depends(get_session)
):
    service = CustomFieldService()
    result = await service.remove_field_option(session, field_id, option_value, force)
    return result
```

**File:** `apps/api/dealbrain_api/api/schemas/fields.py`
- Add schema:
```python
class FieldOptionRequest(BaseModel):
    value: str = Field(..., min_length=1, max_length=255)
```

**Acceptance Criteria:**
- [ ] POST endpoint adds option and returns updated field
- [ ] Duplicate options rejected with 400 error
- [ ] DELETE endpoint removes option
- [ ] DELETE with force=true removes even if used
- [ ] Proper error messages for invalid operations

---

#### 2.2 Frontend: Enhanced ComboBox Component

**File:** `apps/web/components/forms/combobox.tsx` (update existing)
- Add props:
```tsx
interface ComboBoxProps {
  // ...existing props
  fieldId?: number; // For automatic option creation
  fieldName?: string; // For confirmation dialog
  enableInlineCreate?: boolean; // Default true for dropdown fields
}
```

- Enhance create option flow:
```tsx
const handleCreateOption = async () => {
  if (!search || !onCreateOption) return;

  // Show confirmation dialog
  const confirmed = await showConfirmation({
    title: `Add "${search}" to ${fieldName}?`,
    message: fieldId
      ? "This will add the option to Global Fields and make it available everywhere."
      : "This will add the option to this field only.",
    confirmText: "Add Option",
    cancelText: "Cancel"
  });

  if (!confirmed) return;

  setCreating(true);
  try {
    if (fieldId) {
      // Add to Global Fields
      await apiFetch(`/api/fields/${fieldId}/options`, {
        method: 'POST',
        body: JSON.stringify({ value: search })
      });
    } else {
      // Use custom handler
      await onCreateOption(search);
    }
    onChange(search);
    setOpen(false);
    setSearch("");

    // Invalidate options cache
    queryClient.invalidateQueries(['fields', fieldId]);
  } catch (error) {
    console.error("Failed to create option:", error);
    // Show error toast
  } finally {
    setCreating(false);
  }
};
```

**File:** `apps/web/hooks/use-field-options.ts` (update existing)
- Add mutation for creating options:
```typescript
export function useFieldOptions(fieldId: number) {
  const queryClient = useQueryClient();

  const createOptionMutation = useMutation({
    mutationFn: async (value: string) => {
      const response = await apiFetch(`/api/fields/${fieldId}/options`, {
        method: 'POST',
        body: JSON.stringify({ value })
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['fields', fieldId]);
      queryClient.invalidateQueries(['fields']); // Refresh fields list
    }
  });

  return { createOption: createOptionMutation.mutateAsync };
}
```

**Acceptance Criteria:**
- [ ] Typing non-existent value shows "Create" option
- [ ] Confirmation dialog displays with correct field name
- [ ] New option immediately available in dropdown
- [ ] Optimistic UI shows option before API confirms
- [ ] Error handling with toast notification

---

#### 2.3 Frontend: Clean Search Field Styling

**File:** `apps/web/components/forms/combobox.tsx`
- Update CommandInput styling:
```tsx
<CommandInput
  placeholder="" // Remove placeholder text
  value={search}
  onValueChange={setSearch}
  className="border-0 focus:ring-0 px-3 py-2" // Clean margins
/>
```

**File:** `apps/web/components/ui/command.tsx` (if not using shadcn directly)
- Verify styling matches option list:
  - Same horizontal padding as CommandItem
  - No visible border (or match option hover border)
  - Consistent font size and height

**Acceptance Criteria:**
- [ ] Search field has no placeholder text (or only icon)
- [ ] Margins match dropdown options below
- [ ] No visual jump when typing
- [ ] Consistent with rest of dropdown UI

---

#### 2.4 Frontend: Apply to Listings Table

**File:** `apps/web/components/listings/editable-cell.tsx` (update existing)
- Update ComboBox usage:
```tsx
<ComboBox
  options={fieldOptions}
  value={value}
  onChange={handleChange}
  fieldId={field.id}
  fieldName={field.label}
  enableInlineCreate={true}
  placeholder={`Select ${field.label}...`}
/>
```

**File:** `apps/web/components/listings/listings-table.tsx`
- Verify all dropdown columns use editable-cell with ComboBox
- Test with RAM, Storage Type, and custom dropdown fields

**Acceptance Criteria:**
- [ ] Inline creation works in listings table
- [ ] New options persist across page refresh
- [ ] Multiple users see new options (cache invalidation)

---

### Testing Checklist (Phase 2)

- [ ] API test for adding/removing options
- [ ] Test duplicate option prevention
- [ ] Test option deletion with force flag
- [ ] UI test for inline creation flow
- [ ] Test cache invalidation across components

---

## Phase 3: Global Fields Enhancements (Days 9-12)

### Goals
- Rename "Enum" to "Dropdown" throughout UI
- Add options builder to field creation/edit forms
- Enable default value configuration for all field types
- Allow editing core field metadata (labels, descriptions, options)

### Tasks

#### 3.1 Frontend: Terminology Update

**File:** `apps/web/app/global-fields/page.tsx`
- Update all references:
  - "Enum" → "Dropdown"
  - "Multi-select" → "Multi-Select Dropdown" (where standalone type)

**File:** `apps/web/components/global-fields/field-form.tsx`
- Update Type dropdown options:
```tsx
const FIELD_TYPES = [
  { value: 'string', label: 'Text' },
  { value: 'number', label: 'Number' },
  { value: 'boolean', label: 'Checkbox' },
  { value: 'enum', label: 'Dropdown' }, // Changed from "Enum"
  { value: 'multi_select', label: 'Multi-Select Dropdown' },
  { value: 'date', label: 'Date' },
  { value: 'json', label: 'JSON' },
];
```

**File:** `apps/web/types/fields.ts`
- Update type labels in TypeScript interfaces (display only, keep DB values)

**Acceptance Criteria:**
- [ ] No user-facing "Enum" text visible
- [ ] "Dropdown" terminology consistent across app
- [ ] Database values unchanged (still "enum" internally)

---

#### 3.2 Frontend: Options Builder Component

**File:** `apps/web/components/global-fields/options-builder.tsx` (new)
- Component for managing dropdown options:
```tsx
interface OptionsBuilderProps {
  options: string[];
  onChange: (options: string[]) => void;
  disabled?: boolean;
}

export function OptionsBuilder({ options, onChange, disabled }: OptionsBuilderProps) {
  const [localOptions, setLocalOptions] = useState(options);
  const [newOption, setNewOption] = useState("");

  const handleAddOption = () => {
    if (!newOption.trim()) return;
    const updated = [...localOptions, newOption.trim()];
    setLocalOptions(updated);
    onChange(updated);
    setNewOption("");
  };

  const handleRemoveOption = (index: number) => {
    const updated = localOptions.filter((_, i) => i !== index);
    setLocalOptions(updated);
    onChange(updated);
  };

  const handleImportCSV = (csvText: string) => {
    const imported = csvText.split(',').map(s => s.trim()).filter(Boolean);
    const updated = [...new Set([...localOptions, ...imported])]; // Dedupe
    setLocalOptions(updated);
    onChange(updated);
  };

  return (
    <div className="space-y-3">
      <Label>Field Options</Label>
      <p className="text-sm text-muted-foreground">
        Define the available options for this dropdown field.
      </p>

      {/* Existing options */}
      <div className="space-y-2">
        {localOptions.map((option, index) => (
          <div key={index} className="flex items-center gap-2">
            <Input
              value={option}
              onChange={(e) => {
                const updated = [...localOptions];
                updated[index] = e.target.value;
                setLocalOptions(updated);
                onChange(updated);
              }}
              disabled={disabled}
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => handleRemoveOption(index)}
              disabled={disabled || localOptions.length === 1}
            >
              <TrashIcon className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>

      {/* Add new option */}
      <div className="flex items-center gap-2">
        <Input
          value={newOption}
          onChange={(e) => setNewOption(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAddOption()}
          placeholder="New option..."
          disabled={disabled}
        />
        <Button
          type="button"
          onClick={handleAddOption}
          disabled={disabled || !newOption.trim()}
        >
          <PlusIcon className="h-4 w-4 mr-1" />
          Add
        </Button>
      </div>

      {/* Import CSV */}
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => {
          const csv = prompt("Enter comma-separated values:");
          if (csv) handleImportCSV(csv);
        }}
        disabled={disabled}
      >
        Import from CSV
      </Button>
    </div>
  );
}
```

**Acceptance Criteria:**
- [ ] Can add/remove options dynamically
- [ ] CSV import works and deduplicates
- [ ] Inline editing of existing options
- [ ] Disabled state when field locked

---

#### 3.3 Frontend: Default Value Input Component

**File:** `apps/web/components/global-fields/default-value-input.tsx` (new)
- Polymorphic input based on field type:
```tsx
interface DefaultValueInputProps {
  fieldType: string;
  options?: string[];
  value: any;
  onChange: (value: any) => void;
  disabled?: boolean;
}

export function DefaultValueInput({ fieldType, options, value, onChange, disabled }: DefaultValueInputProps) {
  switch (fieldType) {
    case 'string':
      return <Input value={value ?? ''} onChange={(e) => onChange(e.target.value)} disabled={disabled} />;

    case 'number':
      return <Input type="number" value={value ?? ''} onChange={(e) => onChange(Number(e.target.value))} disabled={disabled} />;

    case 'boolean':
      return <Checkbox checked={value ?? false} onCheckedChange={onChange} disabled={disabled} />;

    case 'enum':
      return (
        <ComboBox
          options={options?.map(o => ({ label: o, value: o })) ?? []}
          value={value ?? ''}
          onChange={onChange}
          disabled={disabled}
          placeholder="Select default..."
        />
      );

    case 'multi_select':
      return (
        <MultiComboBox
          options={options?.map(o => ({ label: o, value: o })) ?? []}
          value={value ?? []}
          onChange={onChange}
          disabled={disabled}
          placeholder="Select defaults..."
        />
      );

    case 'date':
      return <Input type="date" value={value ?? ''} onChange={(e) => onChange(e.target.value)} disabled={disabled} />;

    default:
      return <Input value={value ?? ''} onChange={(e) => onChange(e.target.value)} disabled={disabled} />;
  }
}
```

**Acceptance Criteria:**
- [ ] Correct input type for each field type
- [ ] Dropdown types show options from OptionsBuilder
- [ ] Value persists in form state
- [ ] Disabled when field locked

---

#### 3.4 Frontend: Field Form Integration

**File:** `apps/web/components/global-fields/field-form.tsx`
- Add to form fields:
```tsx
{/* Type selector */}
<FormField name="data_type">
  <Label>Type</Label>
  <Select value={type} onValueChange={setType} disabled={isEditMode && field.is_locked}>
    {FIELD_TYPES.map(t => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
  </Select>
  {isEditMode && field.is_locked && (
    <div className="flex items-center gap-1 text-xs text-muted-foreground">
      <LockIcon className="h-3 w-3" />
      Type cannot be changed
    </div>
  )}
</FormField>

{/* Options builder (conditional) */}
{(type === 'enum' || type === 'multi_select') && (
  <OptionsBuilder
    options={formData.options ?? []}
    onChange={(opts) => setFormData({ ...formData, options: opts })}
    disabled={false} // Always allow editing options
  />
)}

{/* Default value */}
<FormField name="default_value">
  <Label>Default Value (Optional)</Label>
  <DefaultValueInput
    fieldType={type}
    options={formData.options}
    value={formData.default_value}
    onChange={(val) => setFormData({ ...formData, default_value: val })}
  />
</FormField>

{/* Core field banner */}
{isEditMode && field.is_locked && (
  <Alert>
    <InfoIcon className="h-4 w-4" />
    <AlertTitle>Core Field</AlertTitle>
    <AlertDescription>
      This is a core field managed by the schema. Entity, Key, and Type are locked to maintain data integrity.
      You can still edit the label, description, options, and other properties.
    </AlertDescription>
  </Alert>
)}
```

**Acceptance Criteria:**
- [ ] Options builder appears when Type is Dropdown
- [ ] Default value input adapts to field type
- [ ] Core field banner displays correctly
- [ ] Locked fields show lock icon with tooltip
- [ ] Editable fields (label, description) work on core fields

---

#### 3.5 Backend: Validation & Constraints

**File:** `apps/api/dealbrain_api/services/custom_fields.py`
- Update field update validation:
```python
async def update_field(
    self,
    session: AsyncSession,
    field_id: int,
    updates: dict
) -> CustomFieldDefinition:
    field = await self.get_field_by_id(session, field_id)

    # Prevent changing locked properties on core fields
    if field.is_locked:
        locked_keys = {'entity', 'key', 'data_type'}
        attempted_changes = set(updates.keys()) & locked_keys
        if attempted_changes:
            raise ValueError(f"Cannot modify {', '.join(attempted_changes)} on locked field")

    # Validate options for dropdown fields
    if updates.get('data_type') in ('enum', 'multi_select'):
        if 'options' in updates and not updates['options']:
            raise ValueError("Dropdown fields must have at least one option")

    # Apply updates
    for key, value in updates.items():
        setattr(field, key, value)

    await session.commit()
    return field
```

**Acceptance Criteria:**
- [ ] API rejects changes to locked properties
- [ ] Clear error messages for invalid updates
- [ ] Options validation for dropdown fields

---

### Testing Checklist (Phase 3)

- [ ] Test field creation with options and default value
- [ ] Test editing core field metadata (allow) vs. locked properties (block)
- [ ] Test CSV import with various formats
- [ ] Test default value applies when creating entity
- [ ] Accessibility test for new components

---

## Phase 4: CPU Data Enrichment (Days 13-16)

### Goals
- Add benchmark score fields to CPU model/form
- Convert free-text fields to dropdowns (Manufacturer, Series, Cores, Threads)
- Create migration script for existing data

### Tasks

#### 4.1 Backend: CPU Model Updates

**File:** `apps/api/dealbrain_api/models/core.py`
- Verify fields exist (already in schema):
  - `cpu_mark_multi` (INTEGER NULL)
  - `cpu_mark_single` (INTEGER NULL)
- Add field if missing:
  - `igpu_mark` (INTEGER NULL)

**File:** `apps/api/alembic/versions/xxx_add_cpu_igpu_mark.py`
- Migration to add `igpu_mark` column if not present:
```python
def upgrade():
    op.add_column('cpu', sa.Column('igpu_mark', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('cpu', 'igpu_mark')
```

**Acceptance Criteria:**
- [ ] Migration adds igpu_mark column
- [ ] Existing cpu_mark fields verified

---

#### 4.2 Backend: Create Dropdown Fields for CPU

**File:** `apps/api/dealbrain_api/seeds.py` (or new migration)
- Seed custom field definitions for CPU:
```python
CPU_DROPDOWN_FIELDS = [
    {
        "entity": "cpu",
        "key": "manufacturer",
        "label": "Manufacturer",
        "data_type": "enum",
        "options": ["Intel", "AMD", "Apple", "Qualcomm", "MediaTek", "Other"],
        "default_value": None,
        "is_locked": False,
    },
    {
        "entity": "cpu",
        "key": "series",
        "label": "Series",
        "data_type": "enum",
        "options": [
            # Intel
            "Core i3", "Core i5", "Core i7", "Core i9", "Xeon", "Pentium", "Celeron",
            # AMD
            "Ryzen 3", "Ryzen 5", "Ryzen 7", "Ryzen 9", "Threadripper", "EPYC", "Athlon",
        ],
        "default_value": None,
        "is_locked": False,
    },
    {
        "entity": "cpu",
        "key": "cores",
        "label": "Cores",
        "data_type": "enum",
        "options": ["1", "2", "4", "6", "8", "10", "12", "14", "16", "20", "24", "32", "64", "128"],
        "default_value": None,
        "is_locked": False,
    },
    {
        "entity": "cpu",
        "key": "threads",
        "label": "Threads",
        "data_type": "enum",
        "options": ["2", "4", "8", "12", "16", "20", "24", "28", "32", "40", "48", "64", "128", "256"],
        "default_value": None,
        "is_locked": False,
    },
]

async def seed_cpu_dropdown_fields():
    async with session_scope() as session:
        service = CustomFieldService()
        for field_data in CPU_DROPDOWN_FIELDS:
            existing = await service.get_field_by_key(session, field_data["entity"], field_data["key"])
            if not existing:
                await service.create_field(session, field_data)
```

**Note:** Since CPU already has `manufacturer`, `cores`, `threads` as schema columns (not custom fields), this may require a different approach:
- Option A: Migrate to use attributes_json + custom fields
- Option B: Keep as schema columns but add UI dropdowns with options from custom field definitions
- **Recommendation:** Option B for backward compatibility

**Acceptance Criteria:**
- [ ] Dropdown options available for CPU fields
- [ ] Existing data preserved
- [ ] UI shows dropdowns instead of text inputs

---

#### 4.3 Frontend: CPU Form Updates

**File:** `apps/web/components/cpus/cpu-form.tsx`
- Add benchmark score fields:
```tsx
<FormField name="cpu_mark_multi">
  <Label>
    CPU Mark (Multi-Core)
    <InfoTooltip>
      Multi-threaded benchmark score from <a href="https://cpubenchmark.net" target="_blank">cpubenchmark.net</a>
    </InfoTooltip>
  </Label>
  <Input type="number" min="0" max="100000" {...register('cpu_mark_multi')} />
</FormField>

<FormField name="cpu_mark_single">
  <Label>
    CPU Mark (Single-Thread)
    <InfoTooltip>
      Single-threaded benchmark score from cpubenchmark.net
    </InfoTooltip>
  </Label>
  <Input type="number" min="0" max="10000" {...register('cpu_mark_single')} />
</FormField>

<FormField name="igpu_mark">
  <Label>
    iGPU Mark (Optional)
    <InfoTooltip>
      Integrated graphics benchmark score (if applicable)
    </InfoTooltip>
  </Label>
  <Input type="number" min="0" max="5000" {...register('igpu_mark')} />
</FormField>
```

- Convert to dropdowns:
```tsx
<FormField name="manufacturer">
  <Label>Manufacturer</Label>
  <ComboBox
    options={MANUFACTURER_OPTIONS}
    value={manufacturer}
    onChange={setManufacturer}
    enableInlineCreate={true}
    fieldName="Manufacturer"
  />
</FormField>

<FormField name="series">
  <Label>Series</Label>
  <ComboBox
    options={getSeriesOptions(manufacturer)} // Filter by manufacturer
    value={series}
    onChange={setSeries}
    enableInlineCreate={true}
    fieldName="Series"
  />
</FormField>

<FormField name="cores">
  <Label>Cores</Label>
  <ComboBox
    options={CORES_OPTIONS}
    value={cores?.toString()}
    onChange={(val) => setCores(Number(val))}
    enableInlineCreate={true}
    allowCustom={true} // Allow exotic core counts
    fieldName="Cores"
  />
</FormField>

<FormField name="threads">
  <Label>Threads</Label>
  <ComboBox
    options={THREADS_OPTIONS}
    value={threads?.toString()}
    onChange={(val) => setThreads(Number(val))}
    enableInlineCreate={true}
    allowCustom={true}
    fieldName="Threads"
  />
</FormField>
```

**File:** `apps/web/lib/cpu-options.ts` (new)
- Define option arrays:
```typescript
export const MANUFACTURER_OPTIONS = [
  { label: 'Intel', value: 'Intel' },
  { label: 'AMD', value: 'AMD' },
  { label: 'Apple', value: 'Apple' },
  { label: 'Qualcomm', value: 'Qualcomm' },
  { label: 'MediaTek', value: 'MediaTek' },
  { label: 'Other', value: 'Other' },
];

export const SERIES_OPTIONS_INTEL = [
  { label: 'Core i3', value: 'Core i3' },
  { label: 'Core i5', value: 'Core i5' },
  { label: 'Core i7', value: 'Core i7' },
  { label: 'Core i9', value: 'Core i9' },
  { label: 'Xeon', value: 'Xeon' },
  { label: 'Pentium', value: 'Pentium' },
  { label: 'Celeron', value: 'Celeron' },
];

export const SERIES_OPTIONS_AMD = [
  { label: 'Ryzen 3', value: 'Ryzen 3' },
  { label: 'Ryzen 5', value: 'Ryzen 5' },
  { label: 'Ryzen 7', value: 'Ryzen 7' },
  { label: 'Ryzen 9', value: 'Ryzen 9' },
  { label: 'Threadripper', value: 'Threadripper' },
  { label: 'EPYC', value: 'EPYC' },
  { label: 'Athlon', value: 'Athlon' },
];

export function getSeriesOptions(manufacturer: string) {
  if (manufacturer === 'Intel') return SERIES_OPTIONS_INTEL;
  if (manufacturer === 'AMD') return SERIES_OPTIONS_AMD;
  return [];
}

export const CORES_OPTIONS = [
  '1', '2', '4', '6', '8', '10', '12', '14', '16', '20', '24', '32', '64', '128'
].map(v => ({ label: v, value: v }));

export const THREADS_OPTIONS = [
  '2', '4', '8', '12', '16', '20', '24', '28', '32', '40', '48', '64', '128', '256'
].map(v => ({ label: v, value: v }));
```

**Acceptance Criteria:**
- [ ] Benchmark fields appear in CPU form
- [ ] Dropdowns show for Manufacturer, Series, Cores, Threads
- [ ] Series options filter based on Manufacturer
- [ ] Custom values allowed for Cores/Threads
- [ ] Form validation works (Threads >= Cores)

---

#### 4.4 Data Migration Script

**File:** `scripts/migrate_cpu_data.py` (new)
- Script to populate benchmark scores and standardize dropdown values:
```python
import asyncio
from sqlalchemy import select
from apps.api.dealbrain_api.db import session_scope
from apps.api.dealbrain_api.models.core import Cpu

# Mapping of known CPU names to benchmark scores (manual or scraped)
BENCHMARK_DATA = {
    "Intel Core i5-8500T": {
        "cpu_mark_multi": 8500,
        "cpu_mark_single": 2100,
        "igpu_mark": 850,
    },
    # ... more mappings
}

async def migrate_cpu_benchmarks():
    async with session_scope() as session:
        cpus = await session.execute(select(Cpu))
        for cpu in cpus.scalars():
            if cpu.name in BENCHMARK_DATA:
                data = BENCHMARK_DATA[cpu.name]
                cpu.cpu_mark_multi = data.get("cpu_mark_multi")
                cpu.cpu_mark_single = data.get("cpu_mark_single")
                cpu.igpu_mark = data.get("igpu_mark")
        await session.commit()

if __name__ == "__main__":
    asyncio.run(migrate_cpu_benchmarks())
```

**Note:** This is a manual/semi-automated process. For full automation, consider web scraping cpubenchmark.net (check robots.txt and terms of service).

**Acceptance Criteria:**
- [ ] Script runs without errors
- [ ] Benchmark scores populated for known CPUs
- [ ] Report generated showing coverage (% of CPUs with scores)

---

### Testing Checklist (Phase 4)

- [ ] Test CPU creation with benchmark scores
- [ ] Test dropdown filtering (Series by Manufacturer)
- [ ] Test data migration script on staging data
- [ ] Validate existing CPUs still display correctly
- [ ] Test inline creation for CPU dropdowns

---

## Phase 5: Polish & Integration (Days 17-18)

### Goals
- Cross-component integration testing
- Performance optimization
- Accessibility audit
- Documentation updates

### Tasks

#### 5.1 Integration Testing

**Test Scenarios:**
1. **End-to-End Listing Creation:**
   - Create listing with custom dropdown values (inline creation)
   - Verify valuation calculates with color coding
   - Click valuation breakdown modal
   - Verify data persists

2. **Global Fields Workflow:**
   - Create dropdown field with options and default value
   - Use field in listing creation (default pre-filled)
   - Add new option inline
   - Verify option appears in Global Fields

3. **CPU Enrichment:**
   - Create CPU with benchmark scores
   - Use CPU in listing
   - Verify valuation uses benchmark scores in rules

**Acceptance Criteria:**
- [ ] All workflows complete successfully
- [ ] No console errors or warnings
- [ ] Data consistency across components

---

#### 5.2 Performance Optimization

**Targets:**
- Valuation cell rendering: <100ms for 100 rows
- Dropdown option loading: <200ms
- Modal open/close: <150ms

**Optimizations:**
1. Memoize ValuationCell component
2. Virtualize dropdown option lists if >100 options
3. Debounce search input in ComboBox
4. Cache field options in React Query (5min stale time)

**Acceptance Criteria:**
- [ ] Performance metrics meet targets
- [ ] No unnecessary re-renders (React DevTools Profiler)

---

#### 5.3 Accessibility Audit

**Checklist:**
- [ ] Color contrast ratios meet WCAG AA (4.5:1 for text)
- [ ] Keyboard navigation works for all new components
- [ ] Screen reader announces dynamic content (toast notifications, modal open/close)
- [ ] Focus trap in modals
- [ ] Focus restoration on modal close
- [ ] ARIA labels on interactive elements
- [ ] High-contrast mode support (icons + text, not just color)

**Tools:**
- axe DevTools Chrome extension
- WAVE accessibility evaluation
- Manual keyboard testing (no mouse)
- VoiceOver/NVDA screen reader testing

---

#### 5.4 Documentation Updates

**Files to Update:**
1. **CLAUDE.md** - Add new features to overview:
   - Valuation display enhancements
   - Inline dropdown creation
   - CPU benchmark fields

2. **README.md** - Update setup instructions if needed

3. **docs/architecture.md** - Document new settings system

4. **API Documentation** - Add new endpoints:
   - `/api/settings/{key}`
   - `/api/fields/{field_id}/options`

5. **User Guide** (if exists) - Add sections:
   - Understanding valuation color coding
   - Creating dropdown options inline
   - Setting default field values

**Acceptance Criteria:**
- [ ] All documentation current and accurate
- [ ] Examples provided for new features
- [ ] API endpoints documented with request/response examples

---

### Testing Checklist (Phase 5)

- [ ] Full regression test suite passes
- [ ] Performance benchmarks meet targets
- [ ] Accessibility audit complete with 0 critical issues
- [ ] Documentation reviewed and approved

---

## Deployment Strategy

### Pre-Deployment Checklist

- [ ] All migrations tested on staging database
- [ ] Backup production database
- [ ] Performance tests pass
- [ ] Accessibility tests pass
- [ ] User acceptance testing complete

### Deployment Steps

1. **Database Migrations:**
   ```bash
   make migrate
   ```

2. **Seed Settings:**
   ```bash
   poetry run python -m apps.api.dealbrain_api.seeds
   ```

3. **Build Frontend:**
   ```bash
   pnpm run build
   ```

4. **Deploy Services:**
   ```bash
   make up
   ```

5. **Verify Deployment:**
   - Check health endpoints
   - Smoke test critical workflows
   - Monitor error logs

### Rollback Plan

If issues arise:
1. Revert migrations: `alembic downgrade -1`
2. Deploy previous frontend build
3. Restart services
4. Investigate logs and fix issues

---

## Success Criteria

### Functional Completeness
- [ ] All FR requirements implemented
- [ ] All acceptance criteria met
- [ ] No critical bugs in new features

### Quality Metrics
- [ ] Test coverage >85% for new code
- [ ] 0 critical accessibility issues
- [ ] Performance targets met

### User Acceptance
- [ ] User testing feedback positive (if applicable)
- [ ] No major usability concerns
- [ ] Documentation sufficient for self-service

---

## Post-Implementation Tasks

### Phase 6: Data Enrichment (Ongoing)

**CPU Benchmark Data Collection:**
1. Identify top 100 most common CPUs in catalog
2. Manually populate benchmark scores from cpubenchmark.net
3. Expand to cover 90% of CPUs over 1 month
4. Document process for adding new CPUs

**Quality Assurance:**
- [ ] Audit dropdown field migrations for data accuracy
- [ ] Review valuation calculations with new benchmark data
- [ ] Collect user feedback on color thresholds (adjust if needed)

---

## Appendix: Code Examples

### A. ValuationCell Component (Complete)

```tsx
// apps/web/components/listings/valuation-cell.tsx
import { formatCurrency } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowDown, ArrowUp, Minus, Info } from "lucide-react";

interface ValuationThresholds {
  good_deal: number;
  great_deal: number;
  premium_warning: number;
}

interface ValuationCellProps {
  adjustedPrice: number;
  listPrice: number;
  thresholds: ValuationThresholds;
  onDetailsClick: () => void;
}

export function ValuationCell({
  adjustedPrice,
  listPrice,
  thresholds,
  onDetailsClick
}: ValuationCellProps) {
  const delta = listPrice - adjustedPrice;
  const deltaPercent = listPrice > 0 ? (delta / listPrice) * 100 : 0;

  const style = getValuationStyle(deltaPercent, thresholds);

  return (
    <div className="flex items-center gap-2">
      <span className="text-lg font-semibold tabular-nums">
        {formatCurrency(adjustedPrice)}
      </span>
      <Badge
        variant={style.variant}
        className={`flex items-center gap-1 ${style.className}`}
      >
        {style.icon === 'down' && <ArrowDown className="h-3 w-3" />}
        {style.icon === 'up' && <ArrowUp className="h-3 w-3" />}
        {style.icon === 'neutral' && <Minus className="h-3 w-3" />}
        <span className="tabular-nums">
          {delta >= 0 ? '-' : '+'}{formatCurrency(Math.abs(delta))}
        </span>
        <span className="text-xs opacity-75">
          ({Math.abs(deltaPercent).toFixed(1)}%)
        </span>
      </Badge>
      <Button
        variant="ghost"
        size="sm"
        onClick={onDetailsClick}
        className="h-6 w-6 p-0"
        aria-label="View valuation breakdown"
      >
        <Info className="h-4 w-4" />
      </Button>
    </div>
  );
}

function getValuationStyle(deltaPercent: number, thresholds: ValuationThresholds) {
  if (deltaPercent >= thresholds.great_deal) {
    return {
      variant: 'default' as const,
      className: 'bg-green-800 text-white',
      icon: 'down' as const
    };
  }
  if (deltaPercent >= thresholds.good_deal) {
    return {
      variant: 'default' as const,
      className: 'bg-green-600 text-white',
      icon: 'down' as const
    };
  }
  if (deltaPercent > 0) {
    return {
      variant: 'secondary' as const,
      className: 'bg-green-100 text-green-800',
      icon: 'down' as const
    };
  }
  if (Math.abs(deltaPercent) >= thresholds.premium_warning) {
    return {
      variant: 'destructive' as const,
      className: 'bg-red-600 text-white',
      icon: 'up' as const
    };
  }
  if (deltaPercent < 0) {
    return {
      variant: 'secondary' as const,
      className: 'bg-red-100 text-red-800',
      icon: 'up' as const
    };
  }
  return {
    variant: 'secondary' as const,
    className: 'bg-gray-100 text-gray-600',
    icon: 'neutral' as const
  };
}
```

### B. Field Options API Endpoint (Complete)

```python
# apps/api/dealbrain_api/api/fields.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..services.custom_fields import CustomFieldService
from .schemas.fields import FieldResponse, FieldOptionRequest

router = APIRouter(prefix="/fields", tags=["fields"])

@router.post("/{field_id}/options", response_model=FieldResponse)
async def add_field_option(
    field_id: int,
    request: FieldOptionRequest,
    session: AsyncSession = Depends(get_session)
):
    """Add a new option to a dropdown field."""
    service = CustomFieldService()
    try:
        field = await service.add_field_option(session, field_id, request.value)
        return field
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{field_id}/options/{option_value}")
async def remove_field_option(
    field_id: int,
    option_value: str,
    force: bool = Query(False, description="Delete even if option is used"),
    session: AsyncSession = Depends(get_session)
):
    """Remove an option from a dropdown field."""
    service = CustomFieldService()
    try:
        result = await service.remove_field_option(session, field_id, option_value, force)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Summary

This implementation plan delivers all October 3 enhancements in **18 days** across 5 focused phases:

1. **Valuation Display** - Clean, color-coded pricing with interactive breakdowns
2. **Dropdown Workflows** - Inline option creation eliminates context switching
3. **Global Fields** - User-friendly terminology, options builder, default values, core field editing
4. **CPU Enrichment** - Benchmark scores and controlled dropdowns for quality data
5. **Polish** - Integration testing, performance, accessibility, documentation

**Key Outcomes:**
- Users identify best deals in <10 seconds
- Data entry time reduced by 40%
- Zero "What is Enum?" support requests
- 90% CPU benchmark coverage within 1 month

**Next Steps:**
1. Review and approve this plan
2. Create Phase 1 tracking document
3. Begin backend settings infrastructure
4. Proceed with implementation
