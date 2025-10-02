# Implementation Plan: UI/UX Enhancements

**Version:** 1.0
**Date:** October 2, 2025
**Status:** Ready for Development
**Related PRD:** [prd-ui-enhancements.md](./prd-ui-enhancements.md)

---

## Overview

This implementation plan details the technical execution strategy for the UI/UX enhancements across Valuation Rules, Table Components, Global Fields, and Listings. The work is organized into 7 phases with clear dependencies and deliverables.

**Total Estimated Scope:** 7 development phases
**Critical Path:** Phase 1 → Phase 2 → Phase 3 (foundational components before feature implementation)

---

## Architecture Principles

### Frontend Architecture

1. **Component Composition:** All new UI components extend existing `shadcn/ui` patterns
2. **State Management:** React Query for server state, React Context for UI state (modals, filters)
3. **Form Handling:** React Hook Form for validation, Zod for schema validation
4. **Performance:** Virtualization for lists >100 items, debounced inputs, optimistic updates
5. **Accessibility:** ARIA labels, keyboard navigation, focus management

### Backend Architecture

1. **API Layer:** FastAPI endpoints in `apps/api/dealbrain_api/api/`
2. **Service Layer:** Business logic in `apps/api/dealbrain_api/services/`
3. **Domain Logic:** Shared valuation logic in `packages/core/`
4. **Database:** SQLAlchemy models (already exist), Alembic migrations for schema changes

### Design System

1. **Modal System:** Single `ModalShell` component with size variants
2. **Table System:** Enhanced `DataGrid` component with plugins (filters, locking, virtualization)
3. **Form System:** Reusable form field components with consistent validation patterns
4. **Toast System:** Centralized notification service for success/error feedback

---

## Phase 1: Foundation - Modal & Form System

**Goal:** Establish reusable modal and form infrastructure for all subsequent features

**Duration:** 3-4 development sessions

### 1.1 Enhanced Modal Shell Component

**Location:** `apps/web/components/ui/modal-shell.tsx`

**Changes:**

```typescript
// Extend existing ModalShell with size variants
interface ModalShellProps {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg" | "xl" | "full"; // NEW
  className?: string;
  onClose?: () => void; // NEW: Handle unsaved changes
  preventClose?: boolean; // NEW: Block close during operations
}

// Size mappings
const MODAL_SIZES = {
  sm: "max-w-sm",   // 400px - confirmations
  md: "max-w-2xl",  // 640px - standard forms (keep existing)
  lg: "max-w-4xl",  // 800px - complex forms
  xl: "max-w-6xl",  // 1200px - data tables
  full: "max-w-[90vw]" // 90% viewport
};
```

**Implementation Steps:**

1. Update `modal-shell.tsx`:
   - Add size prop with variant classes
   - Add unsaved changes detection hook
   - Add preventClose logic with confirmation dialog
   - Enhance accessibility (focus trap, ESC handling)

2. Create `useUnsavedChanges` hook:
   ```typescript
   // apps/web/hooks/use-unsaved-changes.ts
   function useUnsavedChanges(isDirty: boolean) {
     useEffect(() => {
       const handler = (e: BeforeUnloadEvent) => {
         if (isDirty) {
           e.preventDefault();
           e.returnValue = '';
         }
       };
       window.addEventListener('beforeunload', handler);
       return () => window.removeEventListener('beforeunload', handler);
     }, [isDirty]);
   }
   ```

3. Create confirmation dialog component:
   ```typescript
   // apps/web/components/ui/confirmation-dialog.tsx
   interface ConfirmationDialogProps {
     title: string;
     message: string;
     confirmLabel?: string;
     cancelLabel?: string;
     variant?: "default" | "destructive";
     onConfirm: () => void;
     onCancel: () => void;
   }
   ```

**Testing:**
- Unit tests for modal variants rendering
- Keyboard navigation tests (Tab, ESC, Enter)
- Unsaved changes warning tests
- Focus trap tests

**Deliverables:**
- ✅ Enhanced `ModalShell` component
- ✅ `useUnsavedChanges` hook
- ✅ `ConfirmationDialog` component
- ✅ Storybook stories for all variants
- ✅ Test coverage >90%

---

### 1.2 Form Field Components

**Goal:** Build reusable, validated form components

**Location:** `apps/web/components/forms/`

**Components to Create:**

1. **FormField Wrapper:**
   ```typescript
   // apps/web/components/forms/form-field.tsx
   interface FormFieldProps {
     label: string;
     name: string;
     required?: boolean;
     description?: string;
     error?: string;
     children: ReactNode;
   }
   ```

2. **Validated Input:**
   ```typescript
   // apps/web/components/forms/validated-input.tsx
   interface ValidatedInputProps extends InputHTMLAttributes<HTMLInputElement> {
     validation?: z.ZodType<any>;
     onValidChange?: (value: any) => void;
   }
   ```

3. **ComboBox (Editable Dropdown):**
   ```typescript
   // apps/web/components/forms/combobox.tsx
   interface ComboBoxProps {
     options: { label: string; value: string }[];
     value: string;
     onChange: (value: string) => void;
     onCreateOption?: (value: string) => Promise<void>; // NEW
     placeholder?: string;
     allowCustom?: boolean; // Enable inline creation
   }
   ```

4. **Multi-Select ComboBox:**
   ```typescript
   // apps/web/components/forms/multi-combobox.tsx
   interface MultiComboBoxProps extends Omit<ComboBoxProps, 'value' | 'onChange'> {
     value: string[];
     onChange: (values: string[]) => void;
   }
   ```

**Implementation Steps:**

1. Install dependencies (if not present):
   ```bash
   pnpm add react-hook-form zod @hookform/resolvers
   pnpm add cmdk @radix-ui/react-popover
   ```

2. Create form components with react-hook-form integration

3. Build ComboBox with create-on-type behavior:
   - Show "Create '{value}'" option when no match
   - Trigger `onCreateOption` callback
   - Optimistically add to options list

4. Create `useFieldOptions` hook for Global Fields integration:
   ```typescript
   // apps/web/hooks/use-field-options.ts
   function useFieldOptions(entity: string, fieldKey: string) {
     const queryClient = useQueryClient();

     const createOption = useMutation({
       mutationFn: async (value: string) => {
         // Call API to add option to field
         return apiFetch(`/v1/fields-data/${entity}/${fieldKey}/options`, {
           method: 'POST',
           body: JSON.stringify({ value })
         });
       },
       onSuccess: () => {
         queryClient.invalidateQueries(['field-options', entity, fieldKey]);
       }
     });

     return { createOption: createOption.mutate };
   }
   ```

**Testing:**
- Validation tests (valid/invalid inputs)
- ComboBox create-on-type tests
- Accessibility tests (ARIA labels, keyboard nav)

**Deliverables:**
- ✅ `FormField`, `ValidatedInput` components
- ✅ `ComboBox` with inline creation
- ✅ `MultiComboBox` component
- ✅ `useFieldOptions` hook
- ✅ Integration tests with react-hook-form
- ✅ Storybook stories

---

## Phase 2: Foundation - Table System Enhancements

**Goal:** Optimize table performance and add advanced features (locking, pagination, virtualization)

**Duration:** 4-5 development sessions

### 2.1 Performance Optimizations

**Location:** `apps/web/components/ui/data-grid.tsx`

**Changes:**

1. **Debounced Column Resizing:**
   ```typescript
   // Add debounce utility
   import { useDebouncedCallback } from 'use-debounce';

   const handleColumnResize = useDebouncedCallback(
     (columnSizing: ColumnSizingState) => {
       table.setColumnSizing(columnSizing);
       if (storageKey) {
         localStorage.setItem(`${storageKey}:sizing`, JSON.stringify(columnSizing));
       }
     },
     150 // 150ms debounce
   );
   ```

2. **Pagination:**
   ```typescript
   interface DataGridProps<TData> {
     // ... existing props
     pagination?: {
       pageSize?: number;
       pageSizeOptions?: number[];
       defaultPageIndex?: number;
     };
   }

   // Add pagination state
   const [pagination, setPagination] = useState({
     pageIndex: 0,
     pageSize: props.pagination?.pageSize ?? 50
   });
   ```

3. **Virtualization (for "All" page size or >100 rows):**
   ```typescript
   import { useVirtualizer } from '@tanstack/react-virtual';

   const rowVirtualizer = useVirtualizer({
     count: table.getRowModel().rows.length,
     getScrollElement: () => tableContainerRef.current,
     estimateSize: () => estimatedRowHeight ?? DEFAULT_ROW_HEIGHT,
     overscan: OVERSCAN_ROWS,
     enabled: enableVirtualization // When pagination.pageSize === 'all' and rows > 100
   });
   ```

**Implementation Steps:**

1. Install virtualization library:
   ```bash
   pnpm add @tanstack/react-virtual use-debounce
   ```

2. Refactor column sizing to use debounced callback

3. Add pagination UI component:
   ```typescript
   // apps/web/components/ui/pagination-controls.tsx
   interface PaginationControlsProps {
     pageIndex: number;
     pageSize: number;
     totalRows: number;
     pageSizeOptions: number[];
     onPageChange: (pageIndex: number) => void;
     onPageSizeChange: (pageSize: number) => void;
   }
   ```

4. Implement conditional virtualization:
   - Enable when `pageSize === 'all'` and `rows.length > 100`
   - Render virtual items only
   - Add padding top/bottom for scroll height

5. Add text wrapping constraints:
   ```typescript
   // Prevent column from shrinking below min width
   const MIN_COLUMN_WIDTH = 80;

   const handleColumnSizeChange = (columnId: string, size: number) => {
     const minWidth = MIN_COLUMN_WIDTH;
     const constrainedSize = Math.max(size, minWidth);
     // Visual indicator when at min width
     if (constrainedSize === minWidth) {
       setLockedWidthColumns(prev => [...prev, columnId]);
     }
   };
   ```

**Testing:**
- Performance tests with 1,000+ row datasets
- Pagination navigation tests
- Virtualization scroll tests
- Column resize boundary tests

**Deliverables:**
- ✅ Debounced column resizing
- ✅ Pagination component and logic
- ✅ Virtualization for large datasets
- ✅ Min width constraints with wrapping
- ✅ Performance benchmarks (before/after)
- ✅ Test coverage >85%

---

### 2.2 Column Locking

**Location:** `apps/web/components/ui/data-grid.tsx`

**Implementation:**

1. **Sticky Column State:**
   ```typescript
   interface StickyColumnConfig {
     columnId: string;
     position: 'left' | 'right';
   }

   const [stickyColumns, setStickyColumns] = useState<StickyColumnConfig[]>([
     { columnId: 'select', position: 'left' },
     { columnId: 'title', position: 'left' },
     { columnId: 'actions', position: 'right' }
   ]);
   ```

2. **Column Settings Dropdown:**
   ```typescript
   // apps/web/components/ui/column-settings-menu.tsx
   interface ColumnSettingsMenuProps {
     columns: Column<any>[];
     stickyColumns: StickyColumnConfig[];
     onToggleSticky: (columnId: string, position?: 'left' | 'right') => void;
   }

   // UI: Dropdown with checkboxes per column
   // - "Lock to Left"
   // - "Lock to Right"
   // - "Unlock"
   ```

3. **Sticky Styling:**
   ```typescript
   const getStickyStyles = (columnId: string): CSSProperties => {
     const config = stickyColumns.find(c => c.columnId === columnId);
     if (!config) return {};

     return {
       position: 'sticky',
       [config.position]: calculateOffset(columnId, config.position),
       zIndex: config.position === 'left' ? 10 : 11,
       backgroundColor: 'var(--background)',
       borderRight: config.position === 'left' ? '1px solid var(--border)' : 'none',
       borderLeft: config.position === 'right' ? '1px solid var(--border)' : 'none'
     };
   };

   // Calculate cumulative width offset for multiple locked columns
   const calculateOffset = (columnId: string, position: 'left' | 'right') => {
     const lockedCols = stickyColumns.filter(c => c.position === position);
     const index = lockedCols.findIndex(c => c.columnId === columnId);
     if (index === -1) return 0;

     return lockedCols
       .slice(0, index)
       .reduce((acc, col) => acc + (columnSizing[col.columnId] || 100), 0);
   };
   ```

4. **Persistence:**
   ```typescript
   useEffect(() => {
     if (storageKey) {
       localStorage.setItem(
         `${storageKey}:stickyColumns`,
         JSON.stringify(stickyColumns)
       );
     }
   }, [stickyColumns, storageKey]);
   ```

**Implementation Steps:**

1. Add sticky column state management
2. Create column settings dropdown UI
3. Apply CSS sticky positioning with dynamic offsets
4. Persist configuration to localStorage
5. Handle edge cases (horizontal scroll, window resize)

**Testing:**
- Sticky column rendering tests
- Offset calculation tests
- Persistence tests
- Responsive behavior tests

**Deliverables:**
- ✅ Sticky column state management
- ✅ Column settings UI
- ✅ Dynamic sticky styling
- ✅ localStorage persistence
- ✅ Test coverage >80%

---

### 2.3 Dropdown Field Integration

**Location:** `apps/web/components/listings/listings-table.tsx`

**Changes:**

1. **Add Dropdown Fields for RAM/Storage:**
   ```typescript
   const RAM_OPTIONS = [4, 8, 16, 24, 32, 48, 64, 96, 128].map(gb => ({
     label: `${gb} GB`,
     value: String(gb)
   }));

   const STORAGE_OPTIONS = [128, 256, 512, 1024, 2048, 4096].map(gb => ({
     label: `${gb} GB`,
     value: String(gb)
   }));
   ```

2. **Update EditableCell Component:**
   ```typescript
   function EditableCell({ field, value, onSave }: EditableCellProps) {
     // ... existing logic

     // NEW: Detect if field should use dropdown
     const isDropdownField = ['ram_gb', 'primary_storage_gb', 'storage_type'].includes(field.key);
     const options = getOptionsForField(field.key);

     if (isDropdownField) {
       return (
         <ComboBox
           options={options}
           value={String(value)}
           onChange={(newValue) => onSave(field, newValue)}
           allowCustom
           onCreateOption={async (customValue) => {
             // Inline creation
             await handleCreateOption(field.key, customValue);
           }}
         />
       );
     }

     // ... existing field rendering
   }
   ```

3. **Create Option Handler:**
   ```typescript
   const handleCreateOption = async (fieldKey: string, value: string) => {
     // Show confirmation modal
     const confirmed = await showConfirmation({
       title: `Add "${value}" to ${fieldKey}?`,
       message: 'This will add the option to Global Fields and make it available everywhere.',
       confirmLabel: 'Add Option'
     });

     if (!confirmed) return;

     // Call API to add option
     await apiFetch(`/v1/fields-data/listing/${fieldKey}/options`, {
       method: 'POST',
       body: JSON.stringify({ value })
     });

     // Invalidate queries to refresh options
     queryClient.invalidateQueries(['field-options', 'listing', fieldKey]);

     // Show success toast
     toast.success(`Added "${value}" to ${fieldKey}`);
   };
   ```

**Implementation Steps:**

1. Define option arrays for RAM/Storage fields
2. Update `EditableCell` to use `ComboBox` for dropdown fields
3. Implement `handleCreateOption` with API integration
4. Add confirmation dialog before creating
5. Update backend API (see Phase 3.2)

**Testing:**
- Dropdown rendering tests
- Inline option creation tests
- API integration tests
- Toast notification tests

**Deliverables:**
- ✅ RAM/Storage dropdown fields
- ✅ Inline option creation
- ✅ Confirmation flow
- ✅ API integration
- ✅ Test coverage >85%

---

## Phase 3: Backend API Extensions

**Goal:** Create/extend API endpoints to support new UI features

**Duration:** 3-4 development sessions

### 3.1 Field Options Management

**Endpoint:** `POST /v1/fields-data/{entity}/{field_key}/options`

**Location:** `apps/api/dealbrain_api/api/fields_data.py`

**Request:**
```python
from pydantic import BaseModel

class AddFieldOptionRequest(BaseModel):
    value: str
```

**Response:**
```python
class FieldOptionResponse(BaseModel):
    entity: str
    field_key: str
    options: list[str]
```

**Service Layer:**

```python
# apps/api/dealbrain_api/services/custom_fields.py

async def add_field_option(
    session: AsyncSession,
    entity: str,
    field_key: str,
    value: str
) -> list[str]:
    """Add an option to a dropdown field."""
    # Get field
    field = await get_field(session, entity, field_key)
    if not field:
        raise ValueError(f"Field {field_key} not found for entity {entity}")

    # Validate field type
    if field.data_type not in ['enum', 'multi_select']:
        raise ValueError(f"Cannot add options to field of type {field.data_type}")

    # Get current options
    options = field.options or []

    # Add if not exists
    if value not in options:
        options.append(value)
        field.options = options
        await session.commit()

    return options
```

**Implementation Steps:**

1. Add route to `fields_data.py`:
   ```python
   @router.post("/{entity}/{field_key}/options", response_model=FieldOptionResponse)
   async def add_field_option(
       entity: str,
       field_key: str,
       request: AddFieldOptionRequest,
       session: AsyncSession = Depends(get_session)
   ):
       options = await custom_fields_service.add_field_option(
           session, entity, field_key, request.value
       )
       return FieldOptionResponse(
           entity=entity,
           field_key=field_key,
           options=options
       )
   ```

2. Add service method to `custom_fields.py`

3. Add unit tests for service layer

4. Add integration tests for endpoint

**Testing:**
- Service layer tests (add to existing, add duplicate)
- Endpoint tests (valid, invalid field type)
- Error handling tests

**Deliverables:**
- ✅ `POST /v1/fields-data/{entity}/{field_key}/options` endpoint
- ✅ Service layer method
- ✅ Unit tests
- ✅ Integration tests
- ✅ Test coverage >90%

---

### 3.2 Valuation Rules CRUD Endpoints

**Goal:** Full CRUD for Rulesets, Rule Groups, and Rules

**Location:** `apps/api/dealbrain_api/api/valuation_rules.py`

**New Endpoints:**

1. **Rulesets:**
   - `GET /v1/valuation/rulesets` - List all rulesets
   - `GET /v1/valuation/rulesets/{id}` - Get ruleset with groups/rules
   - `POST /v1/valuation/rulesets` - Create ruleset
   - `PATCH /v1/valuation/rulesets/{id}` - Update ruleset
   - `DELETE /v1/valuation/rulesets/{id}` - Delete ruleset

2. **Rule Groups:**
   - `GET /v1/valuation/rulesets/{ruleset_id}/groups` - List groups
   - `POST /v1/valuation/rulesets/{ruleset_id}/groups` - Create group
   - `PATCH /v1/valuation/groups/{id}` - Update group
   - `DELETE /v1/valuation/groups/{id}` - Delete group

3. **Rules:**
   - `GET /v1/valuation/groups/{group_id}/rules` - List rules
   - `GET /v1/valuation/rules/{id}` - Get rule with conditions/actions
   - `POST /v1/valuation/groups/{group_id}/rules` - Create rule
   - `PATCH /v1/valuation/rules/{id}` - Update rule
   - `DELETE /v1/valuation/rules/{id}` - Delete rule

**Schemas:**

```python
# apps/api/dealbrain_api/schemas/valuation_rules.py

from pydantic import BaseModel, Field
from datetime import datetime

# Rulesets
class ValuationRulesetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    version: str = "1.0.0"
    is_active: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)

class ValuationRulesetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    version: str | None = None
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None

class ValuationRulesetResponse(BaseModel):
    id: int
    name: str
    description: str | None
    version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    rule_group_count: int
    rule_count: int

class ValuationRulesetDetail(ValuationRulesetResponse):
    rule_groups: list[ValuationRuleGroupResponse]

# Rule Groups
class ValuationRuleGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    category: str = Field(..., regex="^(component|condition|market|custom)$")
    description: str | None = None
    display_order: int = 100
    weight: float = 1.0

class ValuationRuleGroupUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    display_order: int | None = None
    weight: float | None = None

class ValuationRuleGroupResponse(BaseModel):
    id: int
    ruleset_id: int
    name: str
    category: str
    description: str | None
    display_order: int
    weight: float
    created_at: datetime
    updated_at: datetime
    rule_count: int

class ValuationRuleGroupDetail(ValuationRuleGroupResponse):
    rules: list[ValuationRuleResponse]

# Rules
class RuleConditionCreate(BaseModel):
    field_name: str
    field_type: str
    operator: str
    value_json: dict | list | str | int | float
    logical_operator: str | None = None
    group_order: int = 0

class RuleActionCreate(BaseModel):
    action_type: str
    metric: str | None = None
    value_usd: float | None = None
    unit_type: str | None = None
    formula: str | None = None
    modifiers_json: dict[str, Any] = Field(default_factory=dict)
    display_order: int = 0

class ValuationRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    priority: int = 100
    is_active: bool = True
    evaluation_order: int = 100
    conditions: list[RuleConditionCreate] = []
    actions: list[RuleActionCreate] = []

class ValuationRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    priority: int | None = None
    is_active: bool | None = None
    evaluation_order: int | None = None
    conditions: list[RuleConditionCreate] | None = None
    actions: list[RuleActionCreate] | None = None

class ValuationRuleResponse(BaseModel):
    id: int
    group_id: int
    name: str
    description: str | None
    priority: int
    is_active: bool
    evaluation_order: int
    created_at: datetime
    updated_at: datetime
    condition_count: int
    action_count: int

class ValuationRuleDetail(ValuationRuleResponse):
    conditions: list[RuleConditionResponse]
    actions: list[RuleActionResponse]

class RuleConditionResponse(BaseModel):
    id: int
    field_name: str
    field_type: str
    operator: str
    value_json: dict | list | str | int | float
    logical_operator: str | None
    group_order: int

class RuleActionResponse(BaseModel):
    id: int
    action_type: str
    metric: str | None
    value_usd: float | None
    unit_type: str | None
    formula: str | None
    modifiers_json: dict[str, Any]
    display_order: int
```

**Service Layer:**

```python
# apps/api/dealbrain_api/services/valuation_rules.py

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.core import (
    ValuationRuleset,
    ValuationRuleGroup,
    ValuationRuleV2,
    ValuationRuleCondition,
    ValuationRuleAction
)
from ..schemas.valuation_rules import *

async def list_rulesets(session: AsyncSession) -> list[ValuationRulesetResponse]:
    """List all rulesets with counts."""
    result = await session.execute(
        select(ValuationRuleset).order_by(ValuationRuleset.created_at.desc())
    )
    rulesets = result.scalars().all()

    response = []
    for ruleset in rulesets:
        # Count groups and rules
        group_count = len(ruleset.rule_groups)
        rule_count = sum(len(group.rules) for group in ruleset.rule_groups)

        response.append(ValuationRulesetResponse(
            id=ruleset.id,
            name=ruleset.name,
            description=ruleset.description,
            version=ruleset.version,
            is_active=ruleset.is_active,
            created_at=ruleset.created_at,
            updated_at=ruleset.updated_at,
            rule_group_count=group_count,
            rule_count=rule_count
        ))

    return response

async def get_ruleset(session: AsyncSession, ruleset_id: int) -> ValuationRulesetDetail | None:
    """Get ruleset with all groups and rules."""
    result = await session.execute(
        select(ValuationRuleset)
        .where(ValuationRuleset.id == ruleset_id)
        .options(selectinload(ValuationRuleset.rule_groups))
    )
    ruleset = result.scalar_one_or_none()
    if not ruleset:
        return None

    # Build response with counts
    groups = []
    total_rules = 0
    for group in ruleset.rule_groups:
        rule_count = len(group.rules)
        total_rules += rule_count
        groups.append(ValuationRuleGroupResponse(
            id=group.id,
            ruleset_id=group.ruleset_id,
            name=group.name,
            category=group.category,
            description=group.description,
            display_order=group.display_order,
            weight=group.weight,
            created_at=group.created_at,
            updated_at=group.updated_at,
            rule_count=rule_count
        ))

    return ValuationRulesetDetail(
        id=ruleset.id,
        name=ruleset.name,
        description=ruleset.description,
        version=ruleset.version,
        is_active=ruleset.is_active,
        created_at=ruleset.created_at,
        updated_at=ruleset.updated_at,
        rule_group_count=len(groups),
        rule_count=total_rules,
        rule_groups=groups
    )

async def create_ruleset(
    session: AsyncSession,
    data: ValuationRulesetCreate
) -> ValuationRulesetResponse:
    """Create new ruleset."""
    ruleset = ValuationRuleset(**data.model_dump())
    session.add(ruleset)
    await session.commit()
    await session.refresh(ruleset)

    return ValuationRulesetResponse(
        id=ruleset.id,
        name=ruleset.name,
        description=ruleset.description,
        version=ruleset.version,
        is_active=ruleset.is_active,
        created_at=ruleset.created_at,
        updated_at=ruleset.updated_at,
        rule_group_count=0,
        rule_count=0
    )

async def update_ruleset(
    session: AsyncSession,
    ruleset_id: int,
    data: ValuationRulesetUpdate
) -> ValuationRulesetResponse | None:
    """Update ruleset."""
    result = await session.execute(
        select(ValuationRuleset).where(ValuationRuleset.id == ruleset_id)
    )
    ruleset = result.scalar_one_or_none()
    if not ruleset:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ruleset, field, value)

    await session.commit()
    await session.refresh(ruleset)

    # Get counts
    group_count = len(ruleset.rule_groups)
    rule_count = sum(len(group.rules) for group in ruleset.rule_groups)

    return ValuationRulesetResponse(
        id=ruleset.id,
        name=ruleset.name,
        description=ruleset.description,
        version=ruleset.version,
        is_active=ruleset.is_active,
        created_at=ruleset.created_at,
        updated_at=ruleset.updated_at,
        rule_group_count=group_count,
        rule_count=rule_count
    )

async def delete_ruleset(session: AsyncSession, ruleset_id: int) -> bool:
    """Delete ruleset (cascades to groups and rules)."""
    result = await session.execute(
        select(ValuationRuleset).where(ValuationRuleset.id == ruleset_id)
    )
    ruleset = result.scalar_one_or_none()
    if not ruleset:
        return False

    await session.delete(ruleset)
    await session.commit()
    return True

# Similar methods for Rule Groups and Rules...
# (create_rule_group, update_rule_group, delete_rule_group, etc.)
```

**Implementation Steps:**

1. Create schemas in `schemas/valuation_rules.py`
2. Create service layer in `services/valuation_rules.py`
3. Create router in `api/valuation_rules.py`
4. Add unit tests for services
5. Add integration tests for endpoints
6. Update API documentation

**Testing:**
- Service layer tests for all CRUD operations
- Endpoint tests for all routes
- Cascade delete tests (ruleset → groups → rules)
- Validation tests (unique names, required fields)
- Error handling tests (404, 400, 500)

**Deliverables:**
- ✅ All valuation rules endpoints
- ✅ Service layer methods
- ✅ Request/response schemas
- ✅ Unit tests
- ✅ Integration tests
- ✅ API documentation
- ✅ Test coverage >90%

---

### 3.3 Listings Valuation Endpoint

**Endpoint:** `GET /v1/listings/{id}/valuation-breakdown`

**Location:** `apps/api/dealbrain_api/api/listings.py`

**Response:**
```python
class ValuationBreakdownResponse(BaseModel):
    listing_id: int
    listing_title: str
    base_price_usd: float
    adjusted_price_usd: float
    total_adjustment: float
    active_ruleset: str
    applied_rules: list[AppliedRuleDetail]

class AppliedRuleDetail(BaseModel):
    rule_group_name: str
    rule_name: str
    rule_description: str | None
    adjustment_amount: float
    conditions_met: list[str]  # Human-readable condition descriptions
    actions_applied: list[str]  # Human-readable action descriptions
```

**Service Layer:**

```python
# apps/api/dealbrain_api/services/listings.py

async def get_valuation_breakdown(
    session: AsyncSession,
    listing_id: int
) -> ValuationBreakdownResponse | None:
    """Get detailed valuation breakdown for a listing."""
    # Get listing with valuation_breakdown JSON
    result = await session.execute(
        select(Listing).where(Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        return None

    # Parse valuation_breakdown JSON (already computed during valuation)
    breakdown = listing.valuation_breakdown or {}

    # Format applied rules
    applied_rules = []
    for rule_data in breakdown.get('applied_rules', []):
        applied_rules.append(AppliedRuleDetail(
            rule_group_name=rule_data['group_name'],
            rule_name=rule_data['rule_name'],
            rule_description=rule_data.get('description'),
            adjustment_amount=rule_data['adjustment'],
            conditions_met=rule_data.get('conditions_met', []),
            actions_applied=rule_data.get('actions_applied', [])
        ))

    return ValuationBreakdownResponse(
        listing_id=listing.id,
        listing_title=listing.title,
        base_price_usd=listing.list_price_usd or 0,
        adjusted_price_usd=listing.adjusted_price_usd or 0,
        total_adjustment=breakdown.get('total_adjustment', 0),
        active_ruleset=breakdown.get('ruleset_name', 'Unknown'),
        applied_rules=applied_rules
    )
```

**Note:** The `valuation_breakdown` JSON is already populated during valuation computation (see `packages/core/valuation.py`). This endpoint just formats it for display.

**Implementation Steps:**

1. Add schema to `schemas/listings.py`
2. Add service method to `services/listings.py`
3. Add route to `api/listings.py`
4. Add tests

**Testing:**
- Service layer tests
- Endpoint tests
- Edge case tests (no breakdown data, empty rules)

**Deliverables:**
- ✅ `GET /v1/listings/{id}/valuation-breakdown` endpoint
- ✅ Service method
- ✅ Schema
- ✅ Tests
- ✅ Test coverage >90%

---

## Phase 4: Global Fields UI Enhancements

**Goal:** Implement multi-select checkbox and options builder

**Duration:** 2-3 development sessions

### 4.1 Multi-Select Checkbox

**Location:** `apps/web/components/custom-fields/global-fields-table.tsx`

**Changes:**

1. **Update Field Type Dropdown:**
   ```typescript
   // Remove "multi_select" from type options
   const FIELD_TYPES = [
     { label: 'Text', value: 'text' },
     { label: 'Number', value: 'number' },
     { label: 'Boolean', value: 'boolean' },
     { label: 'Dropdown', value: 'enum' },
     // REMOVED: { label: 'Multi-select', value: 'multi_select' }
   ];
   ```

2. **Add Multi-Select Checkbox:**
   ```typescript
   // Show checkbox when type === 'enum'
   {fieldType === 'enum' && (
     <div className="flex items-center gap-2">
       <Checkbox
         id="allow-multiple"
         checked={allowMultiple}
         onCheckedChange={setAllowMultiple}
       />
       <Label htmlFor="allow-multiple">
         Allow Multiple Selections
       </Label>
     </div>
   )}
   ```

3. **Form Submission Logic:**
   ```typescript
   const handleSubmit = async (data: FieldFormData) => {
     // Convert enum + allowMultiple to multi_select
     const dataType = data.type === 'enum' && allowMultiple
       ? 'multi_select'
       : data.type;

     await apiFetch('/v1/fields-data/fields', {
       method: 'POST',
       body: JSON.stringify({
         ...data,
         data_type: dataType
       })
     });
   };
   ```

4. **Edit Mode Pre-Population:**
   ```typescript
   // When editing existing field
   useEffect(() => {
     if (editingField) {
       setFieldType(editingField.data_type === 'multi_select' ? 'enum' : editingField.data_type);
       setAllowMultiple(editingField.data_type === 'multi_select');
     }
   }, [editingField]);
   ```

**Implementation Steps:**

1. Update field type options
2. Add checkbox component (conditionally rendered)
3. Update form submission logic
4. Update edit mode logic
5. Add tests

**Testing:**
- Checkbox visibility tests (only shows for dropdown type)
- Submission tests (converts to multi_select)
- Edit mode tests (pre-populates from multi_select)

**Deliverables:**
- ✅ Updated field type dropdown
- ✅ Multi-select checkbox
- ✅ Conversion logic
- ✅ Tests
- ✅ Test coverage >85%

---

### 4.2 Dropdown Options Builder

**Location:** `apps/web/components/custom-fields/global-fields-table.tsx`

**New Component:**

```typescript
// apps/web/components/custom-fields/dropdown-options-builder.tsx

interface DropdownOptionsBuilderProps {
  options: string[];
  onChange: (options: string[]) => void;
}

export function DropdownOptionsBuilder({ options, onChange }: DropdownOptionsBuilderProps) {
  const [newOption, setNewOption] = useState('');

  const handleAddOption = () => {
    if (!newOption.trim()) return;
    if (options.includes(newOption.trim())) {
      toast.error('Option already exists');
      return;
    }
    onChange([...options, newOption.trim()]);
    setNewOption('');
  };

  const handleRemoveOption = (index: number) => {
    onChange(options.filter((_, i) => i !== index));
  };

  const handleReorder = (fromIndex: number, toIndex: number) => {
    const reordered = [...options];
    const [moved] = reordered.splice(fromIndex, 1);
    reordered.splice(toIndex, 0, moved);
    onChange(reordered);
  };

  const handleImportCSV = (csv: string) => {
    const imported = csv.split(',').map(s => s.trim()).filter(Boolean);
    const unique = Array.from(new Set([...options, ...imported]));
    onChange(unique);
  };

  return (
    <div className="space-y-3">
      <Label>Options</Label>

      {/* Current options list */}
      <div className="space-y-2">
        <DndContext onDragEnd={handleDragEnd}>
          <SortableContext items={options}>
            {options.map((option, index) => (
              <SortableOption
                key={option}
                option={option}
                onRemove={() => handleRemoveOption(index)}
              />
            ))}
          </SortableContext>
        </DndContext>
      </div>

      {/* Add new option */}
      <div className="flex gap-2">
        <Input
          value={newOption}
          onChange={(e) => setNewOption(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              handleAddOption();
            }
          }}
          placeholder="Add option..."
        />
        <Button type="button" onClick={handleAddOption}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Import CSV */}
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => {
          const csv = prompt('Paste comma-separated values:');
          if (csv) handleImportCSV(csv);
        }}
      >
        Import from CSV
      </Button>

      {/* Validation */}
      {options.length === 0 && (
        <p className="text-sm text-destructive">At least one option is required for dropdown fields</p>
      )}
    </div>
  );
}

function SortableOption({ option, onRemove }: { option: string; onRemove: () => void }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: option });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center gap-2 rounded-md border bg-background px-3 py-2"
    >
      <GripVertical className="h-4 w-4 cursor-grab text-muted-foreground" {...attributes} {...listeners} />
      <span className="flex-1 text-sm">{option}</span>
      <Button type="button" variant="ghost" size="sm" onClick={onRemove}>
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

**Integration:**

```typescript
// In global-fields-table.tsx modal form

{(fieldType === 'enum' || fieldType === 'multi_select') && (
  <DropdownOptionsBuilder
    options={options}
    onChange={setOptions}
  />
)}
```

**Implementation Steps:**

1. Install drag-and-drop library:
   ```bash
   pnpm add @dnd-kit/core @dnd-kit/sortable
   ```

2. Create `DropdownOptionsBuilder` component
3. Integrate into field creation/edit modal
4. Add validation (at least 1 option required)
5. Add tests

**Testing:**
- Add/remove option tests
- Reorder tests (drag and drop)
- CSV import tests
- Validation tests (empty options array)

**Deliverables:**
- ✅ `DropdownOptionsBuilder` component
- ✅ Drag-and-drop reordering
- ✅ CSV import
- ✅ Validation
- ✅ Tests
- ✅ Test coverage >85%

---

### 4.3 Core Field Editability

**Location:** `apps/web/components/custom-fields/global-fields-table.tsx`

**Changes:**

1. **Detect Core vs Custom Fields:**
   ```typescript
   const isCoreField = field.origin === 'core'; // Assuming schema includes origin
   ```

2. **Lock Core Field Properties:**
   ```typescript
   <FormField label="Entity">
     <Input value={entity} disabled={isCoreField} />
     {isCoreField && (
       <p className="text-xs text-muted-foreground flex items-center gap-1">
         <Lock className="h-3 w-3" />
         Core field property cannot be changed
       </p>
     )}
   </FormField>

   <FormField label="Key">
     <Input value={key} disabled={isCoreField} />
     {isCoreField && <LockedFieldMessage />}
   </FormField>

   <FormField label="Type">
     <Select value={type} disabled={isCoreField}>
       {/* options */}
     </Select>
     {isCoreField && <LockedFieldMessage />}
   </FormField>
   ```

3. **Allow Editing Metadata:**
   ```typescript
   // Always editable (even for core fields)
   <FormField label="Label">
     <Input value={label} onChange={setLabel} />
   </FormField>

   <FormField label="Description">
     <Textarea value={description} onChange={setDescription} />
   </FormField>

   <FormField label="Required">
     <Checkbox
       checked={required}
       onCheckedChange={setRequired}
     />
     {required && hasReferences && (
       <p className="text-xs text-amber-600">
         Warning: 23 listings have this field empty. Setting to required may cause validation errors.
       </p>
     )}
   </FormField>
   ```

4. **Backend Update:**

No backend changes needed—existing API should handle partial updates. Just ensure:

```python
# apps/api/dealbrain_api/api/fields_data.py

@router.patch("/fields/{field_id}")
async def update_field(
    field_id: int,
    request: FieldUpdateRequest,
    session: AsyncSession = Depends(get_session)
):
    # Service layer checks:
    # - If field is core, only allow updating: label, description, required, validation, options
    # - Block updates to: entity, key, data_type
    pass
```

**Implementation Steps:**

1. Add `origin` field to field schema (if not present)
2. Update modal to lock core field properties
3. Add lock icons and tooltips
4. Add warning for required field changes
5. Add backend validation (if needed)
6. Add tests

**Testing:**
- Core field edit tests (locked properties)
- Custom field edit tests (all properties editable)
- Required field warning tests
- Backend validation tests

**Deliverables:**
- ✅ Core field detection
- ✅ Locked field UI
- ✅ Warning messages
- ✅ Backend validation
- ✅ Tests
- ✅ Test coverage >85%

---

## Phase 5: Valuation Rules UI Implementation

**Goal:** Build full CRUD interface for Valuation Rules page

**Duration:** 5-6 development sessions

### 5.1 Hierarchical Display Component

**Location:** `apps/web/app/valuation-rules/page.tsx`

**New Component Structure:**

```typescript
// apps/web/components/valuation/valuation-rules-workspace.tsx

export function ValuationRulesWorkspace() {
  const { data: rulesets, isLoading } = useQuery({
    queryKey: ['valuation-rulesets'],
    queryFn: () => apiFetch<ValuationRuleset[]>('/v1/valuation/rulesets')
  });

  const [expandedRulesets, setExpandedRulesets] = useState<Set<number>>(new Set([rulesets?.[0]?.id]));
  const [expandedGroups, setExpandedGroups] = useState<Set<number>>(new Set());
  const [expandedRules, setExpandedRules] = useState<Set<number>>(new Set());

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Valuation Rules</h1>
          <p className="text-sm text-muted-foreground">
            Manage rulesets, groups, and individual valuation rules
          </p>
        </div>
        <Button onClick={() => setCreateRulesetOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Ruleset
        </Button>
      </div>

      <div className="space-y-4">
        {rulesets?.map(ruleset => (
          <RulesetCard
            key={ruleset.id}
            ruleset={ruleset}
            expanded={expandedRulesets.has(ruleset.id)}
            onToggle={() => toggleExpanded(expandedRulesets, setExpandedRulesets, ruleset.id)}
            expandedGroups={expandedGroups}
            onToggleGroup={(groupId) => toggleExpanded(expandedGroups, setExpandedGroups, groupId)}
            expandedRules={expandedRules}
            onToggleRule={(ruleId) => toggleExpanded(expandedRules, setExpandedRules, ruleId)}
          />
        ))}
      </div>
    </div>
  );
}
```

**RulesetCard Component:**

```typescript
// apps/web/components/valuation/ruleset-card.tsx

interface RulesetCardProps {
  ruleset: ValuationRuleset;
  expanded: boolean;
  onToggle: () => void;
  expandedGroups: Set<number>;
  onToggleGroup: (groupId: number) => void;
  expandedRules: Set<number>;
  onToggleRule: (ruleId: number) => void;
}

export function RulesetCard({ ruleset, expanded, onToggle, ... }: RulesetCardProps) {
  const { data: detail } = useQuery({
    queryKey: ['valuation-ruleset', ruleset.id],
    queryFn: () => apiFetch<ValuationRulesetDetail>(`/v1/valuation/rulesets/${ruleset.id}`),
    enabled: expanded
  });

  return (
    <Card>
      <CardHeader className="cursor-pointer" onClick={onToggle}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {expanded ? (
              <ChevronDown className="h-5 w-5 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-5 w-5 text-muted-foreground" />
            )}
            <div>
              <CardTitle>{ruleset.name}</CardTitle>
              <CardDescription>
                {ruleset.rule_group_count} groups • {ruleset.rule_count} rules
                {ruleset.is_active && (
                  <Badge variant="default" className="ml-2">Active</Badge>
                )}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                // Open edit modal
              }}
            >
              <Pencil className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                // Open delete confirmation
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      {expanded && detail && (
        <CardContent className="space-y-3">
          {detail.rule_groups.map(group => (
            <RuleGroupCard
              key={group.id}
              group={group}
              rulesetId={ruleset.id}
              expanded={expandedGroups.has(group.id)}
              onToggle={() => onToggleGroup(group.id)}
              expandedRules={expandedRules}
              onToggleRule={onToggleRule}
            />
          ))}

          <Button
            variant="outline"
            size="sm"
            onClick={() => {/* Open create group modal */}}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Group
          </Button>
        </CardContent>
      )}
    </Card>
  );
}
```

**RuleGroupCard Component:**

```typescript
// apps/web/components/valuation/rule-group-card.tsx

export function RuleGroupCard({ group, expanded, onToggle, ... }: RuleGroupCardProps) {
  const { data: detail } = useQuery({
    queryKey: ['valuation-group', group.id],
    queryFn: () => apiFetch<ValuationRuleGroupDetail>(`/v1/valuation/groups/${group.id}`),
    enabled: expanded
  });

  return (
    <div className="rounded-md border bg-muted/30 p-4">
      <div className="flex items-center justify-between cursor-pointer" onClick={onToggle}>
        <div className="flex items-center gap-2">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          <div>
            <h4 className="font-medium">{group.name}</h4>
            <p className="text-xs text-muted-foreground">
              {group.category} • {group.rule_count} rules • weight {group.weight}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm">
            <Pencil className="h-3 w-3" />
          </Button>
          <Button variant="ghost" size="sm">
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {expanded && detail && (
        <div className="mt-4 space-y-2">
          {detail.rules.map(rule => (
            <RuleCard
              key={rule.id}
              rule={rule}
              expanded={expandedRules.has(rule.id)}
              onToggle={() => onToggleRule(rule.id)}
            />
          ))}

          <Button variant="outline" size="sm">
            <Plus className="mr-2 h-3 w-3" />
            Add Rule
          </Button>
        </div>
      )}
    </div>
  );
}
```

**RuleCard Component:**

```typescript
// apps/web/components/valuation/rule-card.tsx

export function RuleCard({ rule, expanded, onToggle }: RuleCardProps) {
  const { data: detail } = useQuery({
    queryKey: ['valuation-rule', rule.id],
    queryFn: () => apiFetch<ValuationRuleDetail>(`/v1/valuation/rules/${rule.id}`),
    enabled: expanded
  });

  return (
    <div className="rounded-md border bg-background p-3">
      <div className="flex items-center justify-between cursor-pointer" onClick={onToggle}>
        <div className="flex items-center gap-2">
          {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          <span className="text-sm font-medium">{rule.name}</span>
          {!rule.is_active && (
            <Badge variant="secondary" className="text-xs">Inactive</Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm">
            <Pencil className="h-3 w-3" />
          </Button>
          <Button variant="ghost" size="sm">
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {expanded && detail && (
        <div className="mt-3 space-y-3 text-sm">
          {/* Conditions */}
          <div>
            <h5 className="font-medium text-xs uppercase text-muted-foreground mb-2">Conditions</h5>
            <div className="space-y-1">
              {detail.conditions.map((condition, index) => (
                <div key={condition.id} className="flex items-center gap-2">
                  {index > 0 && (
                    <span className="text-xs font-medium text-muted-foreground">
                      {condition.logical_operator}
                    </span>
                  )}
                  <code className="text-xs bg-muted px-2 py-1 rounded">
                    {formatCondition(condition)}
                  </code>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div>
            <h5 className="font-medium text-xs uppercase text-muted-foreground mb-2">Actions</h5>
            <div className="space-y-1">
              {detail.actions.map(action => (
                <code key={action.id} className="text-xs bg-muted px-2 py-1 rounded block">
                  {formatAction(action)}
                </code>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper functions
function formatCondition(condition: RuleConditionResponse): string {
  const { field_name, operator, value_json } = condition;
  const value = typeof value_json === 'object' ? JSON.stringify(value_json) : value_json;
  return `${field_name} ${operator} ${value}`;
}

function formatAction(action: RuleActionResponse): string {
  const { action_type, metric, value_usd, unit_type } = action;
  if (action_type === 'adjust_price') {
    return `Adjust price: ${value_usd > 0 ? '+' : ''}$${value_usd} (${unit_type})`;
  }
  return `${action_type}: ${metric || 'N/A'}`;
}
```

**Implementation Steps:**

1. Create workspace component
2. Create ruleset/group/rule card components
3. Implement expand/collapse state management
4. Add lazy loading for detail views
5. Add action buttons (edit/delete)
6. Add tests

**Testing:**
- Expand/collapse tests
- Lazy loading tests
- Card rendering tests
- Action button tests

**Deliverables:**
- ✅ `ValuationRulesWorkspace` component
- ✅ `RulesetCard`, `RuleGroupCard`, `RuleCard` components
- ✅ Expand/collapse logic
- ✅ Lazy loading
- ✅ Tests
- ✅ Test coverage >80%

---

### 5.2 Create/Edit Modals

**Ruleset Modal:**

```typescript
// apps/web/components/valuation/ruleset-form-modal.tsx

interface RulesetFormModalProps {
  ruleset?: ValuationRuleset; // undefined = create mode
  open: boolean;
  onClose: () => void;
}

export function RulesetFormModal({ ruleset, open, onClose }: RulesetFormModalProps) {
  const form = useForm<RulesetFormData>({
    defaultValues: ruleset || {
      name: '',
      description: '',
      version: '1.0.0',
      is_active: true
    }
  });

  const mutation = useMutation({
    mutationFn: async (data: RulesetFormData) => {
      if (ruleset) {
        return apiFetch(`/v1/valuation/rulesets/${ruleset.id}`, {
          method: 'PATCH',
          body: JSON.stringify(data)
        });
      }
      return apiFetch('/v1/valuation/rulesets', {
        method: 'POST',
        body: JSON.stringify(data)
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['valuation-rulesets']);
      toast.success(ruleset ? 'Ruleset updated' : 'Ruleset created');
      onClose();
    }
  });

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <ModalShell
        title={ruleset ? 'Edit Ruleset' : 'Create Ruleset'}
        description="Configure ruleset metadata"
        size="md"
        footer={
          <>
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={form.handleSubmit(data => mutation.mutate(data))}>
              {mutation.isPending ? 'Saving...' : 'Save'}
            </Button>
          </>
        }
      >
        <form className="space-y-4">
          <FormField label="Name" required>
            <Input {...form.register('name', { required: true })} />
          </FormField>

          <FormField label="Description">
            <Textarea {...form.register('description')} rows={3} />
          </FormField>

          <FormField label="Version">
            <Input {...form.register('version')} />
          </FormField>

          <FormField label="Active">
            <Checkbox {...form.register('is_active')} />
          </FormField>
        </form>
      </ModalShell>
    </Dialog>
  );
}
```

**Rule Group Modal:**

```typescript
// apps/web/components/valuation/rule-group-form-modal.tsx

export function RuleGroupFormModal({ rulesetId, group, open, onClose }: RuleGroupFormModalProps) {
  // Similar structure to RulesetFormModal
  // Additional fields: category (dropdown), display_order, weight

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <ModalShell title={group ? 'Edit Group' : 'Create Group'} size="md">
        <form className="space-y-4">
          <FormField label="Name" required>
            <Input {...form.register('name')} />
          </FormField>

          <FormField label="Category" required>
            <Select {...form.register('category')}>
              <option value="component">Component</option>
              <option value="condition">Condition</option>
              <option value="market">Market</option>
              <option value="custom">Custom</option>
            </Select>
          </FormField>

          <FormField label="Description">
            <Textarea {...form.register('description')} rows={2} />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Display Order">
              <Input type="number" {...form.register('display_order')} />
            </FormField>

            <FormField label="Weight">
              <Input type="number" step="0.1" {...form.register('weight')} />
            </FormField>
          </div>
        </form>
      </ModalShell>
    </Dialog>
  );
}
```

**Rule Modal (Complex - Tabbed):**

```typescript
// apps/web/components/valuation/rule-form-modal.tsx

export function RuleFormModal({ groupId, rule, open, onClose }: RuleFormModalProps) {
  const [activeTab, setActiveTab] = useState<'details' | 'conditions' | 'actions'>('details');
  const [conditions, setConditions] = useState<RuleConditionCreate[]>(rule?.conditions || []);
  const [actions, setActions] = useState<RuleActionCreate[]>(rule?.actions || []);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <ModalShell
        title={rule ? 'Edit Rule' : 'Create Rule'}
        description="Configure rule details, conditions, and actions"
        size="lg"
      >
        {/* Tabs */}
        <div className="flex gap-2 border-b">
          <TabButton active={activeTab === 'details'} onClick={() => setActiveTab('details')}>
            Details
          </TabButton>
          <TabButton active={activeTab === 'conditions'} onClick={() => setActiveTab('conditions')}>
            Conditions ({conditions.length})
          </TabButton>
          <TabButton active={activeTab === 'actions'} onClick={() => setActiveTab('actions')}>
            Actions ({actions.length})
          </TabButton>
        </div>

        {/* Tab Content */}
        <div className="mt-4">
          {activeTab === 'details' && (
            <RuleDetailsForm form={form} />
          )}

          {activeTab === 'conditions' && (
            <RuleConditionsBuilder
              conditions={conditions}
              onChange={setConditions}
            />
          )}

          {activeTab === 'actions' && (
            <RuleActionsBuilder
              actions={actions}
              onChange={setActions}
            />
          )}
        </div>
      </ModalShell>
    </Dialog>
  );
}
```

**Condition Builder:**

```typescript
// apps/web/components/valuation/rule-conditions-builder.tsx

export function RuleConditionsBuilder({ conditions, onChange }: BuilderProps) {
  const handleAddCondition = () => {
    onChange([
      ...conditions,
      {
        field_name: '',
        field_type: 'string',
        operator: 'equals',
        value_json: '',
        logical_operator: conditions.length > 0 ? 'AND' : null,
        group_order: conditions.length
      }
    ]);
  };

  return (
    <div className="space-y-4">
      {conditions.map((condition, index) => (
        <ConditionForm
          key={index}
          condition={condition}
          index={index}
          showLogicalOperator={index > 0}
          onChange={(updated) => {
            const newConditions = [...conditions];
            newConditions[index] = updated;
            onChange(newConditions);
          }}
          onRemove={() => {
            onChange(conditions.filter((_, i) => i !== index));
          }}
        />
      ))}

      <Button type="button" variant="outline" onClick={handleAddCondition}>
        <Plus className="mr-2 h-4 w-4" />
        Add Condition
      </Button>
    </div>
  );
}

function ConditionForm({ condition, index, showLogicalOperator, onChange, onRemove }) {
  return (
    <Card className="p-4">
      {showLogicalOperator && (
        <div className="mb-3">
          <Label>Logical Operator</Label>
          <Select
            value={condition.logical_operator}
            onValueChange={(value) => onChange({ ...condition, logical_operator: value })}
          >
            <option value="AND">AND</option>
            <option value="OR">OR</option>
          </Select>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <FormField label="Field">
          <Input
            value={condition.field_name}
            onChange={(e) => onChange({ ...condition, field_name: e.target.value })}
            placeholder="e.g., ram_gb"
          />
        </FormField>

        <FormField label="Operator">
          <Select
            value={condition.operator}
            onValueChange={(value) => onChange({ ...condition, operator: value })}
          >
            <option value="equals">Equals</option>
            <option value="gt">Greater Than</option>
            <option value="gte">Greater Than or Equal</option>
            <option value="lt">Less Than</option>
            <option value="lte">Less Than or Equal</option>
            <option value="in_list">In List</option>
          </Select>
        </FormField>
      </div>

      <FormField label="Value">
        <Input
          value={String(condition.value_json)}
          onChange={(e) => onChange({ ...condition, value_json: e.target.value })}
        />
      </FormField>

      <Button type="button" variant="ghost" size="sm" onClick={onRemove}>
        <Trash2 className="mr-2 h-3 w-3" />
        Remove
      </Button>
    </Card>
  );
}
```

**Action Builder:**

```typescript
// apps/web/components/valuation/rule-actions-builder.tsx

export function RuleActionsBuilder({ actions, onChange }: BuilderProps) {
  // Similar structure to ConditionBuilder
  // Fields: action_type, metric, value_usd, unit_type, formula, display_order

  return (
    <div className="space-y-4">
      {actions.map((action, index) => (
        <ActionForm
          key={index}
          action={action}
          onChange={(updated) => {
            const newActions = [...actions];
            newActions[index] = updated;
            onChange(newActions);
          }}
          onRemove={() => onChange(actions.filter((_, i) => i !== index))}
        />
      ))}

      <Button type="button" variant="outline" onClick={handleAddAction}>
        <Plus className="mr-2 h-4 w-4" />
        Add Action
      </Button>
    </div>
  );
}
```

**Implementation Steps:**

1. Create modal components for each level
2. Implement form validation with zod schemas
3. Create condition/action builder components
4. Add mutation hooks for create/update
5. Add unsaved changes detection
6. Add tests

**Testing:**
- Form validation tests
- Submission tests (create/update)
- Unsaved changes tests
- Tab navigation tests
- Condition/action builder tests

**Deliverables:**
- ✅ Ruleset/Group/Rule modal components
- ✅ Condition builder
- ✅ Action builder
- ✅ Form validation
- ✅ Mutation hooks
- ✅ Tests
- ✅ Test coverage >85%

---

### 5.3 Delete Confirmations

**Location:** `apps/web/components/valuation/delete-confirmation.tsx`

**Component:**

```typescript
interface DeleteConfirmationProps {
  type: 'ruleset' | 'group' | 'rule';
  name: string;
  metadata?: {
    groupCount?: number;
    ruleCount?: number;
  };
  onConfirm: () => Promise<void>;
  open: boolean;
  onClose: () => void;
}

export function DeleteConfirmation({ type, name, metadata, onConfirm, open, onClose }: DeleteConfirmationProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirm = async () => {
    setIsDeleting(true);
    try {
      await onConfirm();
      toast.success(`${type} deleted successfully`);
      onClose();
    } catch (error) {
      toast.error(`Failed to delete ${type}`);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <ModalShell
        title={`Delete ${type}?`}
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={onClose} disabled={isDeleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirm} disabled={isDeleting}>
              {isDeleting ? 'Deleting...' : 'Delete'}
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-sm">
            Are you sure you want to delete <strong>{name}</strong>?
          </p>

          {type === 'ruleset' && metadata && (
            <p className="text-sm text-muted-foreground">
              This will permanently delete {metadata.groupCount} rule groups and {metadata.ruleCount} rules.
            </p>
          )}

          {type === 'group' && metadata && (
            <p className="text-sm text-muted-foreground">
              This will permanently delete {metadata.ruleCount} rules.
            </p>
          )}

          <p className="text-sm font-medium text-destructive">
            This action cannot be undone.
          </p>
        </div>
      </ModalShell>
    </Dialog>
  );
}
```

**Usage:**

```typescript
// In ruleset-card.tsx

const [deleteOpen, setDeleteOpen] = useState(false);

const deleteMutation = useMutation({
  mutationFn: () => apiFetch(`/v1/valuation/rulesets/${ruleset.id}`, { method: 'DELETE' }),
  onSuccess: () => {
    queryClient.invalidateQueries(['valuation-rulesets']);
  }
});

<Button onClick={() => setDeleteOpen(true)}>
  <Trash2 />
</Button>

<DeleteConfirmation
  type="ruleset"
  name={ruleset.name}
  metadata={{ groupCount: ruleset.rule_group_count, ruleCount: ruleset.rule_count }}
  onConfirm={async () => await deleteMutation.mutateAsync()}
  open={deleteOpen}
  onClose={() => setDeleteOpen(false)}
/>
```

**Implementation Steps:**

1. Create `DeleteConfirmation` component
2. Add delete mutations for each type
3. Integrate into card components
4. Add error handling
5. Add tests

**Testing:**
- Confirmation flow tests
- Deletion tests (success/error)
- Cascade deletion tests (backend)

**Deliverables:**
- ✅ `DeleteConfirmation` component
- ✅ Delete mutations
- ✅ Integration with cards
- ✅ Tests
- ✅ Test coverage >85%

---

## Phase 6: Listings Valuation Column

**Goal:** Add valuation column with breakdown modal

**Duration:** 2-3 development sessions

### 6.1 Valuation Column

**Location:** `apps/web/components/listings/listings-table.tsx`

**Changes:**

1. **Add Column Definition:**
   ```typescript
   const columns = useMemo<ColumnDef<ListingRow>[]>(() => {
     return [
       // ... existing columns (select, title)

       // NEW: Valuation column (after title, before CPU)
       {
         header: () => (
           <div className="flex items-center gap-2">
             Valuation
             <Tooltip content="Adjusted price based on active ruleset">
               <InfoIcon className="h-3 w-3 text-muted-foreground" />
             </Tooltip>
           </div>
         ),
         accessorKey: 'adjusted_price_usd',
         cell: ({ row }) => (
           <ValuationCell listing={row.original} />
         ),
         enableSorting: true,
         enableColumnFilter: true,
         meta: {
           filterType: 'number',
           tooltip: 'Adjusted price based on valuation rules'
         },
         filterFn: numericFilterFn,
         size: 160
       },

       // ... rest of columns
     ];
   }, [/* dependencies */]);
   ```

2. **Create ValuationCell Component:**
   ```typescript
   // apps/web/components/listings/valuation-cell.tsx

   interface ValuationCellProps {
     listing: ListingRow;
   }

   export function ValuationCell({ listing }: ValuationCellProps) {
     const [breakdownOpen, setBreakdownOpen] = useState(false);

     const adjusted = listing.adjusted_price_usd || 0;
     const base = listing.list_price_usd || 0;
     const delta = adjusted - base;

     return (
       <>
         <button
           className="flex flex-col items-start gap-1 hover:underline"
           onClick={() => setBreakdownOpen(true)}
         >
           <span className="font-medium text-foreground">
             {formatCurrency(adjusted)}
           </span>

           {delta !== 0 && (
             <Badge
               variant={delta < 0 ? 'default' : 'secondary'}
               className="text-xs"
             >
               {delta < 0 ? '-' : '+'}${Math.abs(delta).toFixed(0)}
               {delta < 0 ? ' savings' : ' premium'}
             </Badge>
           )}
         </button>

         <ValuationBreakdownModal
           listingId={listing.id}
           open={breakdownOpen}
           onClose={() => setBreakdownOpen(false)}
         />
       </>
     );
   }
   ```

**Implementation Steps:**

1. Add column definition after title column
2. Create `ValuationCell` component
3. Add delta badge logic
4. Add click handler to open modal
5. Add tests

**Testing:**
- Column rendering tests
- Delta calculation tests
- Badge styling tests (savings vs premium)
- Click handler tests

**Deliverables:**
- ✅ Valuation column
- ✅ `ValuationCell` component
- ✅ Delta badge
- ✅ Tests
- ✅ Test coverage >85%

---

### 6.2 Valuation Breakdown Modal

**Location:** `apps/web/components/listings/valuation-breakdown-modal.tsx`

**Component:**

```typescript
interface ValuationBreakdownModalProps {
  listingId: number;
  open: boolean;
  onClose: () => void;
}

export function ValuationBreakdownModal({ listingId, open, onClose }: ValuationBreakdownModalProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['listing-valuation-breakdown', listingId],
    queryFn: () => apiFetch<ValuationBreakdownResponse>(`/v1/listings/${listingId}/valuation-breakdown`),
    enabled: open
  });

  if (isLoading) {
    return (
      <Dialog open={open} onOpenChange={onClose}>
        <ModalShell title="Valuation Breakdown" size="md">
          <div className="flex items-center justify-center py-12">
            <Loader className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        </ModalShell>
      </Dialog>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <ModalShell
        title="Valuation Breakdown"
        description={data.listing_title}
        size="md"
        footer={
          <Button variant="outline" onClick={onClose}>Close</Button>
        }
      >
        <div className="space-y-6">
          {/* Summary */}
          <div className="grid grid-cols-2 gap-4 rounded-md border bg-muted/30 p-4">
            <div>
              <p className="text-xs text-muted-foreground">Base Price</p>
              <p className="text-lg font-semibold">{formatCurrency(data.base_price_usd)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Adjusted Price</p>
              <p className="text-lg font-semibold">{formatCurrency(data.adjusted_price_usd)}</p>
            </div>
            <div className="col-span-2">
              <p className="text-xs text-muted-foreground">Total Adjustment</p>
              <p className={cn(
                "text-lg font-semibold",
                data.total_adjustment < 0 ? "text-green-600" : "text-red-600"
              )}>
                {data.total_adjustment < 0 ? '-' : '+'}${Math.abs(data.total_adjustment).toFixed(2)}
              </p>
            </div>
          </div>

          {/* Applied Rules */}
          <div>
            <h4 className="mb-3 font-medium">Applied Rules</h4>
            <div className="space-y-3">
              {data.applied_rules.map((rule, index) => (
                <Card key={index} className="p-3">
                  <div className="space-y-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-sm">{rule.rule_name}</p>
                        <p className="text-xs text-muted-foreground">{rule.rule_group_name}</p>
                      </div>
                      <Badge variant={rule.adjustment_amount < 0 ? 'default' : 'secondary'}>
                        {rule.adjustment_amount < 0 ? '-' : '+'}${Math.abs(rule.adjustment_amount).toFixed(2)}
                      </Badge>
                    </div>

                    {rule.rule_description && (
                      <p className="text-xs text-muted-foreground">{rule.rule_description}</p>
                    )}

                    {/* Conditions */}
                    {rule.conditions_met.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-muted-foreground uppercase">Conditions</p>
                        <ul className="mt-1 space-y-1">
                          {rule.conditions_met.map((condition, i) => (
                            <li key={i} className="text-xs">
                              <code className="bg-muted px-1 py-0.5 rounded">{condition}</code>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Actions */}
                    {rule.actions_applied.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-muted-foreground uppercase">Actions</p>
                        <ul className="mt-1 space-y-1">
                          {rule.actions_applied.map((action, i) => (
                            <li key={i} className="text-xs">
                              <code className="bg-muted px-1 py-0.5 rounded">{action}</code>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Ruleset Info */}
          <div className="text-xs text-muted-foreground">
            Active ruleset: <strong>{data.active_ruleset}</strong>
          </div>
        </div>
      </ModalShell>
    </Dialog>
  );
}
```

**Implementation Steps:**

1. Create modal component
2. Add query hook for breakdown data
3. Implement summary section
4. Implement applied rules list
5. Add loading/error states
6. Add tests

**Testing:**
- Modal rendering tests
- Data fetching tests
- Loading state tests
- Empty rules tests

**Deliverables:**
- ✅ `ValuationBreakdownModal` component
- ✅ Query integration
- ✅ Summary and rules display
- ✅ Tests
- ✅ Test coverage >85%

---

### 6.3 Real-Time Updates

**Location:** `apps/web/components/listings/listings-table.tsx`

**Changes:**

1. **Query Invalidation on Rule Changes:**
   ```typescript
   // In valuation rules mutation hooks

   const updateRuleMutation = useMutation({
     mutationFn: async (data: RuleUpdateData) => {
       return apiFetch(`/v1/valuation/rules/${data.id}`, {
         method: 'PATCH',
         body: JSON.stringify(data)
       });
     },
     onSuccess: () => {
       // Invalidate valuation queries
       queryClient.invalidateQueries(['valuation-rulesets']);
       queryClient.invalidateQueries(['listings', 'records']); // Triggers recalc
       toast.success('Rule updated. Listings are being revalued...');
     }
   });
   ```

2. **Optimistic UI During Recalc:**
   ```typescript
   // In listings-table.tsx

   const { data: listings, isLoading, isFetching } = useQuery({
     queryKey: ['listings', 'records'],
     queryFn: () => apiFetch<ListingRecord[]>('/v1/listings'),
     refetchInterval: false // Don't poll, use invalidation
   });

   // Show loading indicator when refetching
   {isFetching && (
     <div className="flex items-center gap-2 text-sm text-muted-foreground">
       <Loader className="h-4 w-4 animate-spin" />
       Updating valuations...
     </div>
   )}
   ```

3. **Backend: Trigger Recalculation:**

Currently, valuations are calculated when listings are created/updated. To support real-time updates when rules change, add a background task:

```python
# apps/api/dealbrain_api/services/valuation_rules.py

async def update_rule(
    session: AsyncSession,
    rule_id: int,
    data: ValuationRuleUpdate
) -> ValuationRuleResponse | None:
    # ... existing update logic

    await session.commit()

    # Trigger background task to recalculate all listings
    # (Optional: Only if rule's ruleset is active)
    from ..tasks import recalculate_all_listings
    recalculate_all_listings.delay()

    return response
```

**OR** simpler approach: Recalculate on-demand when listings are fetched:

```python
# apps/api/dealbrain_api/api/listings.py

@router.get("/", response_model=list[ListingResponse])
async def list_listings(
    session: AsyncSession = Depends(get_session),
    force_recalc: bool = False  # Query param
):
    listings = await listings_service.list_listings(session)

    if force_recalc:
        # Recalculate valuations
        for listing in listings:
            await listings_service.recalculate_valuation(session, listing.id)
        await session.commit()

    return listings
```

Then frontend invalidates with `force_recalc=true`:

```typescript
queryClient.invalidateQueries({
  queryKey: ['listings', 'records'],
  refetchType: 'active',
  // Add force_recalc param to API call
});
```

**Implementation Steps:**

1. Add query invalidation to rule mutations
2. Add loading indicator during refetch
3. Choose recalc strategy (background task vs on-demand)
4. Implement chosen strategy
5. Add tests

**Testing:**
- Invalidation tests
- Recalc tests (valuations update)
- Loading state tests

**Deliverables:**
- ✅ Query invalidation
- ✅ Loading states
- ✅ Recalc strategy
- ✅ Tests
- ✅ Test coverage >80%

---

## Phase 7: Multi-Pane Layout & Static Nav

**Goal:** Optimize page layouts with resizable panes and static navigation

**Duration:** 2-3 development sessions

### 7.1 Resizable Pane System

**Location:** `apps/web/components/ui/resizable-pane.tsx`

**Component:**

```typescript
import { type ReactNode, useEffect, useRef, useState } from 'react';

interface ResizablePaneProps {
  id: string;
  children: ReactNode;
  defaultHeight?: number;
  minHeight?: number;
  maxHeight?: number;
  className?: string;
}

export function ResizablePane({
  id,
  children,
  defaultHeight = 400,
  minHeight = 300,
  maxHeight = 800,
  className
}: ResizablePaneProps) {
  const storageKey = `pane-height-${id}`;
  const [height, setHeight] = useState(() => {
    if (typeof window === 'undefined') return defaultHeight;
    const saved = localStorage.getItem(storageKey);
    return saved ? Number(saved) : defaultHeight;
  });

  const paneRef = useRef<HTMLDivElement>(null);
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    if (!isResizing) {
      localStorage.setItem(storageKey, String(height));
    }
  }, [height, isResizing, storageKey]);

  const handleMouseDown = () => {
    setIsResizing(true);
  };

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!paneRef.current) return;
      const rect = paneRef.current.getBoundingClientRect();
      const newHeight = e.clientY - rect.top;
      const constrained = Math.max(minHeight, Math.min(newHeight, maxHeight));
      setHeight(constrained);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, minHeight, maxHeight]);

  return (
    <div
      ref={paneRef}
      className={cn('relative overflow-hidden', className)}
      style={{ height: `${height}px` }}
      data-pane
    >
      <div className="h-full overflow-auto">
        {children}
      </div>

      {/* Resize handle */}
      <div
        className={cn(
          'absolute bottom-0 left-0 right-0 h-1 cursor-ns-resize bg-border hover:bg-primary/50 transition-colors',
          isResizing && 'bg-primary'
        )}
        onMouseDown={handleMouseDown}
      />
    </div>
  );
}
```

**Usage Example:**

```typescript
// Page with multiple tables

export default function MultiTablePage() {
  return (
    <div className="space-y-6">
      <ResizablePane id="table-1" defaultHeight={400} minHeight={300}>
        <DataGrid ... />
      </ResizablePane>

      <ResizablePane id="table-2" defaultHeight={400} minHeight={300}>
        <DataGrid ... />
      </ResizablePane>
    </div>
  );
}
```

**Implementation Steps:**

1. Create `ResizablePane` component
2. Add mouse event handlers for resize
3. Add localStorage persistence
4. Add visual resize handle
5. Add tests

**Testing:**
- Resize behavior tests
- Min/max height constraint tests
- Persistence tests
- Mouse event tests

**Deliverables:**
- ✅ `ResizablePane` component
- ✅ Resize logic
- ✅ Persistence
- ✅ Tests
- ✅ Test coverage >85%

---

### 7.2 Static Sidebar & Navbar

**Location:** `apps/web/components/layout/`

**Changes:**

1. **Update Navbar:**
   ```typescript
   // apps/web/components/layout/navbar.tsx

   export function Navbar() {
     return (
       <nav className="sticky top-0 z-100 border-b bg-background/95 backdrop-blur">
         {/* ... existing content */}
       </nav>
     );
   }
   ```

2. **Update Sidebar:**
   ```typescript
   // apps/web/components/layout/sidebar.tsx

   export function Sidebar() {
     return (
       <aside className="fixed left-0 top-[60px] z-90 h-[calc(100vh-60px)] w-64 border-r bg-background">
         <div className="h-full overflow-y-auto">
           {/* ... navigation items */}
         </div>
       </aside>
     );
   }
   ```

3. **Update Layout:**
   ```typescript
   // apps/web/app/layout.tsx

   export default function RootLayout({ children }: { children: ReactNode }) {
     return (
       <html>
         <body>
           <Navbar />
           <div className="flex">
             <Sidebar />
             <main className="ml-64 flex-1 p-6">
               {children}
             </main>
           </div>
         </body>
       </html>
     );
   }
   ```

4. **Responsive Behavior:**
   ```typescript
   // Sidebar with mobile toggle

   export function Sidebar() {
     const [open, setOpen] = useState(false);

     return (
       <>
         {/* Mobile toggle */}
         <Button
           className="fixed left-4 top-4 z-100 lg:hidden"
           onClick={() => setOpen(!open)}
         >
           <Menu className="h-5 w-5" />
         </Button>

         {/* Sidebar */}
         <aside className={cn(
           'fixed left-0 top-[60px] z-90 h-[calc(100vh-60px)] w-64 border-r bg-background transition-transform',
           'lg:translate-x-0', // Always visible on desktop
           open ? 'translate-x-0' : '-translate-x-full' // Toggle on mobile
         )}>
           {/* content */}
         </aside>

         {/* Overlay for mobile */}
         {open && (
           <div
             className="fixed inset-0 z-80 bg-black/50 lg:hidden"
             onClick={() => setOpen(false)}
           />
         )}
       </>
     );
   }
   ```

**Implementation Steps:**

1. Update navbar with `position: sticky`
2. Update sidebar with `position: fixed`
3. Adjust main content margin-left
4. Add responsive mobile behavior
5. Test scroll behavior
6. Add tests

**Testing:**
- Sticky navbar tests
- Fixed sidebar tests
- Scroll behavior tests
- Responsive tests (mobile/desktop)

**Deliverables:**
- ✅ Static navbar
- ✅ Static sidebar
- ✅ Responsive behavior
- ✅ Tests
- ✅ Test coverage >80%

---

## Testing Strategy

### Unit Tests

**Scope:** Individual components and functions
**Tools:** Jest, React Testing Library
**Target Coverage:** >85%

**Key Test Suites:**
- Form components (validation, submission)
- Modal components (open/close, unsaved changes)
- Table components (sorting, filtering, resizing)
- Utility functions (formatters, validators)

### Integration Tests

**Scope:** Component interactions and API integration
**Tools:** Jest, MSW (Mock Service Worker)
**Target Coverage:** >80%

**Key Test Suites:**
- Create/edit flows (modals → API → refetch)
- Table interactions (edit cell → API → update)
- Valuation breakdown (modal → fetch → display)
- Query invalidation (rule change → listing refresh)

### E2E Tests

**Scope:** Full user workflows
**Tools:** Playwright (if not already in use)
**Target Coverage:** Critical paths only

**Key Scenarios:**
- Create ruleset → add group → add rule → view in listings valuation
- Edit listing field → inline dropdown creation → field appears in Global Fields
- Resize column → reload page → size persisted

### Performance Tests

**Scope:** Large dataset handling
**Tools:** React Profiler, Lighthouse
**Metrics:**
- Table render time with 1,000 rows: <2s
- Column resize interaction: <100ms
- Modal open/close: <150ms
- Valuation recalc: <1s for 100 listings

---

## Migration Plan

### Data Migration

**Minimal migrations required—existing schema supports features.**

**Migration 1: Add `origin` field to EntityField (if needed)**

```sql
-- Only if EntityField doesn't have a way to distinguish core vs custom
ALTER TABLE entity_field ADD COLUMN origin VARCHAR(10) DEFAULT 'custom';
UPDATE entity_field SET origin = 'core' WHERE ... /* identify core fields */;
```

**Migration 2: No schema changes for valuation rules (already complete)**

### UI Migration

**Phase 1-2 (Foundations):**
- Deploy modal/form/table enhancements without breaking existing pages
- Gradual rollout: Update one page at a time

**Phase 3-6 (Features):**
- Valuation Rules page: Replace read-only view with new workspace
- Listings table: Add valuation column (additive, non-breaking)
- Global Fields: Update form (backward compatible)

**Phase 7 (Layout):**
- Wrap existing pages in `ResizablePane` (opt-in)
- Update layout component (affects all pages)

### Rollback Plan

**If critical bugs emerge:**

1. **Frontend:** Revert to previous build (Next.js supports instant rollbacks)
2. **Backend:** API endpoints are additive (no breaking changes), but can disable routes if needed
3. **Database:** No destructive migrations—no rollback needed

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (unit, integration, E2E)
- [ ] Performance benchmarks met
- [ ] Accessibility audit (WAVE, axe)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Code review completed
- [ ] Documentation updated

### Deployment Steps

1. **Backend:**
   - Run database migrations: `make migrate`
   - Deploy API: `make up` (Docker) or restart API service
   - Verify endpoints with Postman/curl

2. **Frontend:**
   - Build Next.js: `pnpm build`
   - Deploy: `make up` (Docker) or deploy to Vercel/hosting
   - Verify pages load correctly

3. **Post-Deployment:**
   - Smoke test critical paths
   - Monitor error logs (Sentry, CloudWatch)
   - Check performance metrics (Lighthouse, RUM)

### Rollback Triggers

- Critical bug affecting >50% of users
- Performance regression >2x baseline
- Data corruption or loss
- Security vulnerability

---

## Future Enhancements (Out of Scope for This Phase)

1. **Advanced Rule Features:**
   - Scheduled rule activation (e.g., "Enable on Black Friday")
   - Rule templates library
   - A/B testing between rulesets

2. **Collaboration:**
   - Real-time collaborative editing (WebSockets)
   - User permissions (admin, editor, viewer)
   - Change approval workflows

3. **Analytics:**
   - Rule effectiveness dashboard (which rules save most money)
   - Valuation trends over time
   - Component price history charts

4. **Mobile Optimization:**
   - Fully responsive tables (card view on mobile)
   - Touch-friendly modals and forms
   - Progressive Web App (PWA) support

5. **AI/ML Features:**
   - Suggested rules based on listing patterns
   - Anomaly detection (listings with unusual valuations)
   - Price prediction models

---

## Appendix

### A. Technology Stack

**Frontend:**
- Next.js 14 (App Router)
- React 18
- TypeScript
- TanStack Query (React Query)
- TanStack Table
- Radix UI (via shadcn/ui)
- Tailwind CSS

**Backend:**
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Alembic (migrations)
- Pydantic (schemas)

**Testing:**
- Jest
- React Testing Library
- MSW (mocking)
- Playwright (E2E)

### B. File Structure

```
apps/
├── web/
│   ├── app/
│   │   ├── valuation-rules/
│   │   │   └── page.tsx
│   │   └── global-fields/
│   │       └── page.tsx
│   ├── components/
│   │   ├── ui/
│   │   │   ├── modal-shell.tsx
│   │   │   ├── data-grid.tsx
│   │   │   ├── confirmation-dialog.tsx
│   │   │   └── resizable-pane.tsx
│   │   ├── forms/
│   │   │   ├── form-field.tsx
│   │   │   ├── combobox.tsx
│   │   │   └── multi-combobox.tsx
│   │   ├── valuation/
│   │   │   ├── valuation-rules-workspace.tsx
│   │   │   ├── ruleset-card.tsx
│   │   │   ├── rule-group-card.tsx
│   │   │   ├── rule-card.tsx
│   │   │   ├── ruleset-form-modal.tsx
│   │   │   ├── rule-group-form-modal.tsx
│   │   │   ├── rule-form-modal.tsx
│   │   │   ├── rule-conditions-builder.tsx
│   │   │   └── rule-actions-builder.tsx
│   │   ├── listings/
│   │   │   ├── listings-table.tsx
│   │   │   ├── valuation-cell.tsx
│   │   │   └── valuation-breakdown-modal.tsx
│   │   └── custom-fields/
│   │       ├── global-fields-workspace.tsx
│   │       └── dropdown-options-builder.tsx
│   └── hooks/
│       ├── use-unsaved-changes.ts
│       └── use-field-options.ts
├── api/
│   ├── dealbrain_api/
│   │   ├── api/
│   │   │   ├── valuation_rules.py
│   │   │   ├── fields_data.py
│   │   │   └── listings.py
│   │   ├── services/
│   │   │   ├── valuation_rules.py
│   │   │   ├── custom_fields.py
│   │   │   └── listings.py
│   │   └── schemas/
│   │       ├── valuation_rules.py
│   │       └── listings.py
└── ...
```

### C. API Endpoint Summary

**Valuation Rules:**
- `GET /v1/valuation/rulesets` - List rulesets
- `GET /v1/valuation/rulesets/{id}` - Get ruleset detail
- `POST /v1/valuation/rulesets` - Create ruleset
- `PATCH /v1/valuation/rulesets/{id}` - Update ruleset
- `DELETE /v1/valuation/rulesets/{id}` - Delete ruleset
- `POST /v1/valuation/rulesets/{ruleset_id}/groups` - Create group
- `PATCH /v1/valuation/groups/{id}` - Update group
- `DELETE /v1/valuation/groups/{id}` - Delete group
- `POST /v1/valuation/groups/{group_id}/rules` - Create rule
- `GET /v1/valuation/rules/{id}` - Get rule detail
- `PATCH /v1/valuation/rules/{id}` - Update rule
- `DELETE /v1/valuation/rules/{id}` - Delete rule

**Fields:**
- `POST /v1/fields-data/{entity}/{field_key}/options` - Add dropdown option

**Listings:**
- `GET /v1/listings/{id}/valuation-breakdown` - Get valuation breakdown

---

**Document End**
