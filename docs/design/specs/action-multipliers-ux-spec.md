# Action Multipliers UI/UX Design Specification

**Version:** 1.0
**Date:** 2025-10-15
**Feature:** Action Conditions with Multipliers for Valuation Rules
**Target:** Rule Builder Modal - Advanced Mode

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Design Principles](#design-principles)
3. [Visual Layout & Information Architecture](#visual-layout--information-architecture)
4. [Component Structure](#component-structure)
5. [User Flows](#user-flows)
6. [Interaction Patterns](#interaction-patterns)
7. [Visual Design System](#visual-design-system)
8. [Accessibility Specifications](#accessibility-specifications)
9. [Responsive Behavior](#responsive-behavior)
10. [States & Feedback](#states--feedback)
11. [Implementation Notes](#implementation-notes)
12. [Example Scenarios](#example-scenarios)

---

## Executive Summary

This specification defines the UI/UX for Action Multipliers, a feature that allows users to apply conditional multipliers to valuation rule actions based on specific field values. The primary use case is RAM valuation, where different DDR generations (DDR3, DDR4, DDR5) require different pricing multipliers.

**Key Requirements:**
- Each Action can have 0 or more Multipliers
- Each Multiplier has a custom name and 1 or more condition-value-multiplier rows
- Reuses existing field selection UI components
- Visually distinct from Rule-level Conditions
- Intuitive for non-technical users

---

## Design Principles

### 1. Progressive Disclosure
Start simple, reveal complexity only when needed. Default view shows no multipliers; users opt-in to add them.

### 2. Visual Hierarchy
Action Multipliers are nested under Actions, using visual indentation and containment to show hierarchy:
```
Rule
├── Conditions (Rule-level)
└── Actions
    ├── Action Configuration
    └── Multipliers (Action-level) ← New Feature
```

### 3. Consistent Patterns
Reuse existing Conditions Builder UI patterns for field selection and value input to reduce cognitive load.

### 4. Clear Relationships
Use color coding, labels, and spatial relationships to distinguish Action Multipliers from Rule Conditions.

### 5. Forgiving UX
Allow easy correction of mistakes with clear undo/remove actions and validation messaging.

---

## Visual Layout & Information Architecture

### Modal Structure (Advanced Mode)

```
┌─────────────────────────────────────────────────────────────┐
│ Create/Edit Valuation Rule                            [X]   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ [Basic Mode / Advanced Mode]  ← Tab Switcher                │
│                                                               │
│ ┌─ Rule Configuration ────────────────────────────────┐     │
│ │ Name: [Total RAM Capacity Valuation            ]    │     │
│ │ Description: [...]                                   │     │
│ │ Rule Group: [RamSpec ▼]                             │     │
│ └──────────────────────────────────────────────────────┘     │
│                                                               │
│ ┌─ Conditions ────────────────────────────────────────┐     │
│ │ Match: [All ▼] of the following conditions          │     │
│ │                                                       │     │
│ │ ┌─────────────────────────────────────────────────┐ │     │
│ │ │ [RAM Type ▼] [equals ▼] [DDR4 ▼]      [Remove] │ │     │
│ │ └─────────────────────────────────────────────────┘ │     │
│ │                                                       │     │
│ │ [+ Add Condition]                                    │     │
│ └──────────────────────────────────────────────────────┘     │
│                                                               │
│ ┌─ Actions ───────────────────────────────────────────┐     │
│ │                                                       │     │
│ │ Action Type: [Adjust Price ▼]                       │     │
│ │ Metric: [Total Capacity (GB) ▼]                     │     │
│ │ Per Unit: [$5.00]                                    │     │
│ │                                                       │     │
│ │ ┌─ Multipliers ─────────────────────────────────┐   │     │
│ │ │                                                │   │     │
│ │ │ Apply conditional multipliers to this action  │   │     │
│ │ │                                                │   │     │
│ │ │ ┏━ RAM Generation Multiplier ━━━━━━━━━━━━━┓  │   │     │
│ │ │ ┃                              [Rename][×] ┃  │   │     │
│ │ │ ┃                                           ┃  │   │     │
│ │ │ ┃ Field: [RAM Type ▼]                      ┃  │   │     │
│ │ │ ┃                                           ┃  │   │     │
│ │ │ ┃ ┌───────────────────────────────────┐   ┃  │   │     │
│ │ │ ┃ │ DDR3           × 0.7      [Remove] │   ┃  │   │     │
│ │ │ ┃ └───────────────────────────────────┘   ┃  │   │     │
│ │ │ ┃ ┌───────────────────────────────────┐   ┃  │   │     │
│ │ │ ┃ │ DDR4           × 1.0      [Remove] │   ┃  │   │     │
│ │ │ ┃ └───────────────────────────────────┘   ┃  │   │     │
│ │ │ ┃ ┌───────────────────────────────────┐   ┃  │   │     │
│ │ │ ┃ │ DDR5           × 1.3      [Remove] │   ┃  │   │     │
│ │ │ ┃ └───────────────────────────────────┘   ┃  │   │     │
│ │ │ ┃                                           ┃  │   │     │
│ │ │ ┃ [+ Add Condition Value]                  ┃  │   │     │
│ │ │ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │   │     │
│ │ │                                                │   │     │
│ │ │ [+ Add Multiplier]                            │   │     │
│ │ │                                                │   │     │
│ │ └────────────────────────────────────────────────┘   │     │
│ └──────────────────────────────────────────────────────┘     │
│                                                               │
│                                    [Cancel]  [Save Rule]     │
└─────────────────────────────────────────────────────────────┘
```

### Spatial Hierarchy

**Level 1: Modal Container**
- Outermost boundary, standard modal styling

**Level 2: Section Cards**
- Rule Configuration, Conditions, Actions
- Each in its own card with subtle border

**Level 3: Actions Card Content**
- Action configuration fields (Type, Metric, Per Unit)
- Multipliers subsection (nested)

**Level 4: Multipliers Container**
- Light background color to distinguish from parent
- Contains all multipliers + "Add Multiplier" button

**Level 5: Individual Multiplier Cards**
- Distinct border with accent color
- Contains field selector + condition value rows

**Level 6: Condition Value Rows**
- Individual rows within multiplier
- Value dropdown + multiplier input + remove button

---

## Component Structure

### Component Hierarchy

```
RuleBuilderModal
└── ActionsSection
    ├── ActionTypeSelect
    ├── MetricSelect
    ├── PerUnitInput
    └── ActionMultipliers ← NEW COMPONENT
        ├── MultipliersList
        │   └── MultiplierCard (repeatable) ← NEW COMPONENT
        │       ├── MultiplierHeader ← NEW COMPONENT
        │       │   ├── MultiplierNameInput
        │       │   ├── RenameButton
        │       │   └── RemoveMultiplierButton
        │       ├── FieldSelector (reused from Conditions)
        │       └── ConditionValuesList ← NEW COMPONENT
        │           └── ConditionValueRow (repeatable) ← NEW COMPONENT
        │               ├── ValueCombobox (reused/adapted)
        │               ├── MultiplierInput
        │               └── RemoveConditionButton
        └── AddMultiplierButton
```

### New Components Specifications

#### 1. ActionMultipliers

**File:** `/mnt/containers/deal-brain/apps/web/components/rules/ActionMultipliers.tsx`

**Purpose:** Container for all action multipliers with add functionality

**Props:**
```typescript
interface ActionMultipliersProps {
  multipliers: ActionMultiplier[];
  onMultipliersChange: (multipliers: ActionMultiplier[]) => void;
  ruleGroupId: string; // For field context
  disabled?: boolean;
}

interface ActionMultiplier {
  id: string; // UUID
  name: string; // e.g., "RAM Generation Multiplier"
  fieldId: string; // Selected field for this multiplier
  conditionValues: ConditionValue[];
}

interface ConditionValue {
  id: string; // UUID
  value: string; // e.g., "DDR3", "DDR4"
  multiplier: number; // e.g., 0.7, 1.0
}
```

**Visual Structure:**
```tsx
<div className="space-y-4 rounded-lg border border-blue-200 bg-blue-50/30 p-4">
  <div className="flex items-start justify-between">
    <div>
      <h4 className="text-sm font-medium text-gray-900">
        Multipliers
      </h4>
      <p className="text-xs text-gray-500 mt-1">
        Apply conditional multipliers to this action based on field values
      </p>
    </div>
  </div>

  {/* Multiplier Cards */}
  <div className="space-y-3">
    {multipliers.map((multiplier) => (
      <MultiplierCard key={multiplier.id} {...} />
    ))}
  </div>

  {/* Add Button */}
  <Button
    variant="outline"
    size="sm"
    onClick={handleAddMultiplier}
    className="w-full border-dashed"
  >
    <Plus className="h-4 w-4 mr-2" />
    Add Multiplier
  </Button>
</div>
```

**Styling Notes:**
- Blue-tinted background (blue-50/30) to distinguish from Rule Conditions
- Subtle border (blue-200) for containment
- Generous padding (p-4) for breathing room

---

#### 2. MultiplierCard

**File:** `/mnt/containers/deal-brain/apps/web/components/rules/MultiplierCard.tsx`

**Purpose:** Individual multiplier configuration with field selection and condition values

**Props:**
```typescript
interface MultiplierCardProps {
  multiplier: ActionMultiplier;
  onUpdate: (updated: ActionMultiplier) => void;
  onRemove: () => void;
  ruleGroupId: string;
  disabled?: boolean;
}
```

**Visual Structure:**
```tsx
<Card className="border-blue-300 bg-white shadow-sm">
  <CardHeader className="pb-3">
    <MultiplierHeader
      name={multiplier.name}
      onNameChange={handleNameChange}
      onRemove={onRemove}
      disabled={disabled}
    />
  </CardHeader>

  <CardContent className="space-y-4">
    {/* Field Selector */}
    <div>
      <Label htmlFor={`field-${multiplier.id}`} className="text-xs">
        Field
      </Label>
      <FieldSelector
        id={`field-${multiplier.id}`}
        value={multiplier.fieldId}
        onChange={handleFieldChange}
        ruleGroupId={ruleGroupId}
        disabled={disabled}
      />
    </div>

    {/* Condition Values List */}
    {multiplier.fieldId && (
      <ConditionValuesList
        fieldId={multiplier.fieldId}
        conditionValues={multiplier.conditionValues}
        onConditionValuesChange={handleConditionValuesChange}
        disabled={disabled}
      />
    )}
  </CardContent>
</Card>
```

**Styling Notes:**
- Border color (blue-300) matches parent container
- White background for contrast against blue parent
- Shadow-sm for subtle elevation

---

#### 3. MultiplierHeader

**File:** `/mnt/containers/deal-brain/apps/web/components/rules/MultiplierHeader.tsx`

**Purpose:** Header with editable name and remove button

**Props:**
```typescript
interface MultiplierHeaderProps {
  name: string;
  onNameChange: (name: string) => void;
  onRemove: () => void;
  disabled?: boolean;
}
```

**Visual Structure:**
```tsx
<div className="flex items-center justify-between gap-2">
  {/* Editable Name */}
  {isEditing ? (
    <Input
      value={name}
      onChange={(e) => onNameChange(e.target.value)}
      onBlur={() => setIsEditing(false)}
      onKeyDown={handleKeyDown} // Enter = save, Esc = cancel
      className="text-sm font-medium h-8 flex-1"
      autoFocus
      disabled={disabled}
    />
  ) : (
    <h5 className="text-sm font-medium text-gray-900 flex-1">
      {name || "Unnamed Multiplier"}
    </h5>
  )}

  {/* Actions */}
  <div className="flex items-center gap-1">
    <Button
      variant="ghost"
      size="sm"
      onClick={() => setIsEditing(true)}
      disabled={disabled}
      className="h-7 px-2"
    >
      <Pencil className="h-3 w-3" />
      <span className="sr-only">Rename multiplier</span>
    </Button>

    <Button
      variant="ghost"
      size="sm"
      onClick={onRemove}
      disabled={disabled}
      className="h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
    >
      <X className="h-3 w-3" />
      <span className="sr-only">Remove multiplier</span>
    </Button>
  </div>
</div>
```

**Interaction Notes:**
- Single-click on name or Rename button enters edit mode
- Enter key saves, Escape cancels
- Remove button has red accent for destructive action

---

#### 4. ConditionValuesList

**File:** `/mnt/containers/deal-brain/apps/web/components/rules/ConditionValuesList.tsx`

**Purpose:** List of condition value rows with add functionality

**Props:**
```typescript
interface ConditionValuesListProps {
  fieldId: string;
  conditionValues: ConditionValue[];
  onConditionValuesChange: (values: ConditionValue[]) => void;
  disabled?: boolean;
}
```

**Visual Structure:**
```tsx
<div className="space-y-2">
  {/* Header */}
  <div className="grid grid-cols-[1fr,auto,auto] gap-2 text-xs font-medium text-gray-500 px-2">
    <div>Value</div>
    <div className="w-24 text-center">Multiplier</div>
    <div className="w-8"></div> {/* Remove button column */}
  </div>

  {/* Condition Value Rows */}
  <div className="space-y-2">
    {conditionValues.map((cv) => (
      <ConditionValueRow
        key={cv.id}
        conditionValue={cv}
        fieldId={fieldId}
        onUpdate={handleUpdate}
        onRemove={handleRemove}
        disabled={disabled}
      />
    ))}
  </div>

  {/* Add Button */}
  <Button
    variant="ghost"
    size="sm"
    onClick={handleAddConditionValue}
    disabled={disabled}
    className="w-full h-8 text-xs border border-dashed border-gray-300"
  >
    <Plus className="h-3 w-3 mr-1" />
    Add Condition Value
  </Button>

  {/* Empty State */}
  {conditionValues.length === 0 && (
    <div className="text-center py-6 text-sm text-gray-500">
      No condition values yet. Click "Add Condition Value" to start.
    </div>
  )}
</div>
```

**Styling Notes:**
- Grid layout for consistent alignment
- Column headers for clarity
- Empty state encourages first action

---

#### 5. ConditionValueRow

**File:** `/mnt/containers/deal-brain/apps/web/components/rules/ConditionValueRow.tsx`

**Purpose:** Individual condition value with multiplier input

**Props:**
```typescript
interface ConditionValueRowProps {
  conditionValue: ConditionValue;
  fieldId: string;
  onUpdate: (updated: ConditionValue) => void;
  onRemove: () => void;
  disabled?: boolean;
}
```

**Visual Structure:**
```tsx
<div className="grid grid-cols-[1fr,auto,auto] gap-2 items-center rounded-md border border-gray-200 bg-gray-50/50 p-2">
  {/* Value Selector (Combobox) */}
  <div className="min-w-0">
    <ValueCombobox
      fieldId={fieldId}
      value={conditionValue.value}
      onChange={handleValueChange}
      disabled={disabled}
      placeholder="Select or type value..."
    />
  </div>

  {/* Multiplier Input */}
  <div className="flex items-center gap-1 w-24">
    <span className="text-xs text-gray-500">×</span>
    <Input
      type="number"
      step="0.1"
      min="0"
      value={conditionValue.multiplier}
      onChange={handleMultiplierChange}
      disabled={disabled}
      className="h-8 text-sm text-center"
    />
  </div>

  {/* Remove Button */}
  <Button
    variant="ghost"
    size="sm"
    onClick={onRemove}
    disabled={disabled}
    className="h-8 w-8 p-0 text-gray-400 hover:text-red-600 hover:bg-red-50"
  >
    <X className="h-4 w-4" />
    <span className="sr-only">Remove condition value</span>
  </Button>
</div>
```

**Interaction Notes:**
- Combobox supports both selecting existing values and typing new ones
- Multiplier input validates for positive numbers
- Remove button hover state indicates destructive action

---

#### 6. ValueCombobox

**File:** `/mnt/containers/deal-brain/apps/web/components/rules/ValueCombobox.tsx`

**Purpose:** Hybrid dropdown/text input for field values

**Props:**
```typescript
interface ValueComboboxProps {
  fieldId: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
}
```

**Implementation Pattern:**
Uses shadcn/ui Combobox component (built on Radix UI Popover + Command):

```tsx
<Popover open={open} onOpenChange={setOpen}>
  <PopoverTrigger asChild>
    <Button
      variant="outline"
      role="combobox"
      aria-expanded={open}
      className="w-full justify-between h-8 text-sm"
      disabled={disabled}
    >
      {value || placeholder}
      <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
    </Button>
  </PopoverTrigger>

  <PopoverContent className="w-[200px] p-0" align="start">
    <Command>
      <CommandInput
        placeholder="Search or type new value..."
        value={inputValue}
        onValueChange={setInputValue}
      />
      <CommandList>
        <CommandEmpty>
          <button
            onClick={() => handleCreateNew(inputValue)}
            className="w-full text-left px-2 py-1.5 text-sm hover:bg-gray-100"
          >
            Create "{inputValue}"
          </button>
        </CommandEmpty>
        <CommandGroup>
          {existingValues.map((option) => (
            <CommandItem
              key={option.value}
              value={option.value}
              onSelect={handleSelect}
            >
              <Check
                className={cn(
                  "mr-2 h-4 w-4",
                  value === option.value ? "opacity-100" : "opacity-0"
                )}
              />
              {option.label}
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </Command>
  </PopoverContent>
</Popover>
```

**Behavior:**
1. Fetch existing field values from API on mount
2. Show existing values in dropdown
3. Allow typing to filter
4. Allow creating new values if not found
5. Update parent state on selection or creation

---

## User Flows

### Flow 1: Creating a New Multiplier

**Scenario:** User wants to add a RAM Generation multiplier to a RAM capacity rule

**Steps:**

1. User is in Rule Builder Modal, Advanced Mode
2. User fills in Action configuration (Type: Adjust Price, Metric: Total Capacity, Per Unit: $5.00)
3. User sees "Multipliers" section below Action fields
4. User clicks "[+ Add Multiplier]" button
5. System creates new MultiplierCard with default name "Multiplier 1"
6. Card expands to show:
   - Editable name field (auto-focused)
   - Field selector (empty)
   - "Add Condition Value" button (disabled until field selected)
7. User types "RAM Generation Multiplier" in name field
8. User presses Enter or clicks outside to save name
9. User clicks Field dropdown
10. System shows fields from RamSpec rule group (RAM Type, Capacity, etc.)
11. User selects "RAM Type"
12. System enables "Add Condition Value" button
13. User clicks "[+ Add Condition Value]"
14. System adds first ConditionValueRow with:
    - Value dropdown (showing DDR3, DDR4, DDR5 if they exist)
    - Multiplier input (default: 1.0)
15. User selects "DDR3" from dropdown
16. User changes multiplier to 0.7
17. User clicks "[+ Add Condition Value]" again
18. User adds DDR4 with multiplier 1.0
19. User adds DDR5 with multiplier 1.3
20. User clicks "Save Rule"
21. System validates and saves

**Success Criteria:**
- Multiplier saved with all condition values
- Validation shows no errors
- User sees success message

**Error Scenarios:**
- If user tries to save without selecting field: Show error "Field is required"
- If user tries to save without any condition values: Show warning "At least one condition value recommended"
- If user enters negative multiplier: Show error "Multiplier must be positive"

---

### Flow 2: Editing an Existing Multiplier

**Scenario:** User needs to update multiplier values for existing rule

**Steps:**

1. User opens Rule Builder with existing rule
2. System loads rule data including multipliers
3. MultiplierCard displays with populated data:
   - Name: "RAM Generation Multiplier"
   - Field: RAM Type
   - Condition Values:
     - DDR3 × 0.7
     - DDR4 × 1.0
     - DDR5 × 1.3
4. User wants to change DDR5 multiplier to 1.5
5. User clicks in DDR5 multiplier input
6. User changes value from 1.3 to 1.5
7. Input shows updated value immediately (controlled component)
8. User clicks "Save Rule"
9. System validates and saves

**Success Criteria:**
- Changes persist correctly
- No data loss on other values

---

### Flow 3: Removing a Condition Value

**Scenario:** User added wrong condition value and wants to remove it

**Steps:**

1. User has MultiplierCard with 3 condition values
2. User realizes DDR4 entry is incorrect
3. User hovers over DDR4 row
4. Remove button (X) becomes more visible
5. User clicks Remove button on DDR4 row
6. System shows confirmation dialog:
   - "Remove condition value?"
   - "This will remove DDR4 (× 1.0) from this multiplier."
   - [Cancel] [Remove]
7. User clicks "Remove"
8. System removes row with fade-out animation
9. Remaining rows re-index smoothly

**Success Criteria:**
- Row removed without affecting others
- No orphaned data
- Smooth visual transition

**Alternative Flow:**
- User accidentally clicks Remove
- User clicks "Cancel" in confirmation
- Row remains unchanged

---

### Flow 4: Creating Value Not in Dropdown

**Scenario:** User needs to add a value that doesn't exist yet (e.g., future DDR6)

**Steps:**

1. User clicks "[+ Add Condition Value]"
2. New row appears
3. User clicks Value dropdown
4. Dropdown shows existing values: DDR3, DDR4, DDR5
5. User types "DDR6" in search/input field
6. System shows "No results found"
7. System shows option: "Create 'DDR6'"
8. User clicks "Create 'DDR6'"
9. System:
   - Closes dropdown
   - Sets value to "DDR6"
   - Optionally creates new field value in backend
10. User sets multiplier to 1.8
11. User saves rule

**Success Criteria:**
- New value created successfully
- Value available in dropdown for future selections
- Multiplier row works identically to existing values

---

### Flow 5: Keyboard Navigation

**Scenario:** Power user wants to create multiplier using keyboard only

**Steps:**

1. User tabs through modal fields
2. User reaches "[+ Add Multiplier]" button
3. User presses Enter
4. System creates multiplier and focuses name input
5. User types name, presses Tab
6. Focus moves to Field dropdown
7. User presses Enter to open dropdown
8. User presses Down arrow to navigate fields
9. User presses Enter to select "RAM Type"
10. User tabs to "[+ Add Condition Value]"
11. User presses Enter
12. Focus moves to Value dropdown
13. User types "DDR" to filter
14. User presses Down to navigate, Enter to select "DDR3"
15. User tabs to Multiplier input
16. User types "0.7", presses Tab
17. Focus moves to Remove button (user skips)
18. User presses Tab, reaches "[+ Add Condition Value]"
19. User repeats for DDR4 and DDR5
20. User presses Tab repeatedly to reach "Save Rule"
21. User presses Enter to save

**Success Criteria:**
- Entire flow completable without mouse
- Focus order logical and predictable
- No focus traps
- Visual focus indicators clear

---

## Interaction Patterns

### Adding Items

**Pattern:** Consistent "+ Add [Item]" buttons
- Always at bottom of their container
- Full-width with dashed border
- Ghost variant for secondary feel
- Icon + text label

**States:**
- Default: Gray border, gray text
- Hover: Border darkens, background subtle
- Disabled: Opacity 50%, cursor not-allowed
- Focus: Blue ring for keyboard users

### Removing Items

**Pattern:** Destructive icon buttons
- X icon, consistent sizing (h-4 w-4)
- Ghost variant, positioned at row end
- Hover changes to red accent
- Requires confirmation for multipliers (high-level), direct for rows (low-level)

**Confirmation Dialogs:**
```tsx
<AlertDialog>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Remove multiplier?</AlertDialogTitle>
      <AlertDialogDescription>
        This will remove "{multiplier.name}" and all its condition values.
        This action cannot be undone.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction
        onClick={handleConfirmedRemove}
        className="bg-red-600 hover:bg-red-700"
      >
        Remove
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

### Editing Names

**Pattern:** Inline editing with visual feedback
- Default: Name displayed as heading text
- Click anywhere on name OR Rename button enters edit mode
- Input auto-focused with current value selected
- Enter saves, Escape cancels
- Blur saves (unless Escape was pressed)

### Field Selection

**Pattern:** Reuse existing FieldSelector component
- Dropdown grouped by field type
- Search/filter capability
- Shows field label + type badge
- Only shows fields relevant to current rule group

### Value Selection

**Pattern:** Combobox (hybrid dropdown + input)
- Fetches existing values for selected field
- Allows filtering existing values
- Allows creating new values inline
- Visual distinction between existing and new values

---

## Visual Design System

### Color Palette

**Action Multipliers Theme:**
- Container Background: `bg-blue-50/30` (light blue tint, 30% opacity)
- Container Border: `border-blue-200`
- Card Border: `border-blue-300`
- Accent Blue: `text-blue-600`

**Rationale:** Blue theme distinguishes from:
- Rule Conditions: Gray/neutral theme
- Actions: Default white background
- Validation errors: Red theme
- Success states: Green theme

### Typography

**Hierarchy:**
```css
/* Section Title */
.section-title {
  font-size: 0.875rem;      /* text-sm */
  font-weight: 500;          /* font-medium */
  color: #111827;            /* text-gray-900 */
}

/* Section Description */
.section-description {
  font-size: 0.75rem;        /* text-xs */
  font-weight: 400;          /* font-normal */
  color: #6B7280;            /* text-gray-500 */
  margin-top: 0.25rem;       /* mt-1 */
}

/* Multiplier Name */
.multiplier-name {
  font-size: 0.875rem;       /* text-sm */
  font-weight: 500;          /* font-medium */
  color: #111827;            /* text-gray-900 */
}

/* Field Label */
.field-label {
  font-size: 0.75rem;        /* text-xs */
  font-weight: 500;          /* font-medium */
  color: #374151;            /* text-gray-700 */
}

/* Column Header */
.column-header {
  font-size: 0.75rem;        /* text-xs */
  font-weight: 500;          /* font-medium */
  color: #6B7280;            /* text-gray-500 */
}

/* Input Text */
.input-text {
  font-size: 0.875rem;       /* text-sm */
  font-weight: 400;          /* font-normal */
  color: #111827;            /* text-gray-900 */
}
```

### Spacing & Sizing

**Vertical Rhythm:**
- Section spacing: `space-y-4` (1rem)
- Card spacing: `space-y-3` (0.75rem)
- Row spacing: `space-y-2` (0.5rem)
- Label to input: `gap-1` (0.25rem)

**Padding:**
- Section container: `p-4` (1rem)
- Card header: `p-4` (1rem)
- Card content: `p-4` with `pt-0` on first child
- Row: `p-2` (0.5rem)

**Input Heights:**
- Standard input: `h-8` (2rem)
- Button (sm): `h-7` (1.75rem)
- Button (default): `h-9` (2.25rem)

### Borders & Shadows

```css
/* Container */
border: 1px solid rgb(191, 219, 254);  /* border-blue-200 */
border-radius: 0.5rem;                  /* rounded-lg */

/* Card */
border: 1px solid rgb(147, 197, 253);  /* border-blue-300 */
border-radius: 0.5rem;                  /* rounded-lg */
box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);  /* shadow-sm */

/* Row */
border: 1px solid rgb(229, 231, 235);  /* border-gray-200 */
border-radius: 0.375rem;                /* rounded-md */
background: rgb(249, 250, 251, 0.5);   /* bg-gray-50/50 */
```

### Icons

**Icon Library:** Lucide React

**Used Icons:**
- `Plus`: Add buttons
- `X`: Remove buttons
- `Pencil`: Rename button
- `ChevronsUpDown`: Combobox trigger
- `Check`: Selected state in dropdown

**Icon Sizing:**
- Standard: `h-4 w-4` (1rem)
- Small: `h-3 w-3` (0.75rem)
- Touch target minimum: 44x44px (via padding on parent button)

### Animations

**Transitions:**
```css
/* Default transition */
transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);

/* Hover states */
transition-property: background-color, border-color, color, transform;

/* Entry animations (new row) */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Exit animations (removed row) */
@keyframes slideOut {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(20px);
  }
}
```

**Usage:**
- Add animations: 200ms slide-in with fade
- Remove animations: 150ms slide-out with fade
- Hover transitions: 150ms for color/background changes
- Focus transitions: Instant (0ms) for accessibility

---

## Accessibility Specifications

### WCAG 2.1 AA Compliance

**Color Contrast:**
- Text on backgrounds: Minimum 4.5:1 ratio
- Large text (18pt+): Minimum 3:1 ratio
- Interactive elements: Minimum 3:1 against adjacent colors

**Tested Combinations:**
- Gray-900 on white: 19.8:1 ✓
- Gray-700 on white: 10.5:1 ✓
- Gray-500 on white: 4.6:1 ✓
- Blue-600 on blue-50: 8.2:1 ✓

### Keyboard Navigation

**Tab Order:**
```
1. Multipliers section description (if focusable)
2. [+ Add Multiplier] button
3. First Multiplier:
   a. Multiplier name (if editable) / Rename button
   b. Remove multiplier button
   c. Field dropdown
   d. First condition value row:
      - Value combobox
      - Multiplier input
      - Remove button
   e. Second condition value row...
   f. [+ Add Condition Value] button
4. Second Multiplier...
5. Continue through modal...
```

**Focus Management:**
- When adding multiplier: Focus name input
- When adding condition value: Focus value combobox
- When removing item: Focus previous sibling or parent's add button
- No focus traps in any dropdowns or dialogs

### Screen Reader Support

**ARIA Labels:**
```tsx
// Multipliers Container
<div
  role="region"
  aria-label="Action multipliers"
  aria-describedby="multipliers-description"
>
  <p id="multipliers-description" className="sr-only">
    Configure conditional multipliers for this action. Each multiplier
    applies different values based on selected field conditions.
  </p>

  {/* Multiplier Cards */}
  {multipliers.map((multiplier, index) => (
    <div
      key={multiplier.id}
      role="group"
      aria-labelledby={`multiplier-name-${multiplier.id}`}
    >
      <h5 id={`multiplier-name-${multiplier.id}`}>
        {multiplier.name}
      </h5>
      {/* ... */}
    </div>
  ))}
</div>

// Add Multiplier Button
<Button aria-label="Add new multiplier to this action">
  <Plus aria-hidden="true" />
  Add Multiplier
</Button>

// Remove Multiplier Button
<Button
  aria-label={`Remove ${multiplier.name} multiplier`}
  onClick={handleRemove}
>
  <X aria-hidden="true" />
  <span className="sr-only">Remove multiplier</span>
</Button>

// Condition Value Row
<div
  role="group"
  aria-label={`Condition value: ${cv.value} with multiplier ${cv.multiplier}`}
>
  {/* Value combobox */}
  <Combobox
    aria-label="Field value"
    aria-describedby={`multiplier-help-${cv.id}`}
  />

  {/* Multiplier input */}
  <Input
    aria-label="Multiplier value"
    aria-describedby={`multiplier-help-${cv.id}`}
  />

  <span id={`multiplier-help-${cv.id}`} className="sr-only">
    Enter the multiplier to apply when the field equals {cv.value}
  </span>

  {/* Remove button */}
  <Button aria-label={`Remove condition value ${cv.value}`}>
    <X aria-hidden="true" />
  </Button>
</div>
```

**Live Regions for Dynamic Content:**
```tsx
// Announce additions
<div role="status" aria-live="polite" className="sr-only">
  {announcementText}
</div>

// Usage:
function handleAddMultiplier() {
  const newMultiplier = createMultiplier();
  setMultipliers([...multipliers, newMultiplier]);
  setAnnouncement("Multiplier added. Name field focused.");
}

function handleRemoveConditionValue(id: string) {
  setConditionValues(cvs => cvs.filter(cv => cv.id !== id));
  setAnnouncement("Condition value removed.");
}
```

### Keyboard Shortcuts

**Global (within multipliers section):**
- `Tab` / `Shift+Tab`: Navigate between focusable elements
- `Enter` / `Space`: Activate buttons
- `Escape`: Close dropdowns, cancel inline editing

**In Combobox:**
- `ArrowDown` / `ArrowUp`: Navigate options
- `Home` / `End`: First / last option
- `Enter`: Select highlighted option
- `Escape`: Close without selecting

**In Number Input:**
- `ArrowUp` / `ArrowDown`: Increment/decrement by step (0.1)
- `PageUp` / `PageDown`: Increment/decrement by larger step (1.0)

---

## Responsive Behavior

### Breakpoints

Following Tailwind's default breakpoints:
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px

### Layout Adaptations

**Desktop (1024px+):**
```
┌─ ConditionValueRow ──────────────────────────────────────┐
│ [Value Dropdown (flex-1)] [× 0.7 (w-24)] [Remove (w-8)]  │
└───────────────────────────────────────────────────────────┘
Grid: grid-cols-[1fr,auto,auto]
```

**Tablet (768px - 1023px):**
- Same layout as desktop
- Modal width reduces to 90vw
- Font sizes remain same for readability

**Mobile (< 768px):**
```
┌─ ConditionValueRow ────────────────────┐
│ [Value Dropdown (full width)]          │
│ [× 0.7 (w-20)] [Remove (w-8)]         │
└─────────────────────────────────────────┘
Grid: grid-cols-1 with nested grid for multiplier + remove
```

**Responsive Classes:**
```tsx
<div className="
  grid
  grid-cols-1
  md:grid-cols-[1fr,auto,auto]
  gap-2
  items-start
  md:items-center
">
  {/* Value */}
  <div className="min-w-0">
    <ValueCombobox />
  </div>

  {/* Multiplier + Remove (nested on mobile) */}
  <div className="
    flex
    items-center
    gap-2
    md:contents
  ">
    <div className="flex items-center gap-1 w-20 md:w-24">
      <span>×</span>
      <Input />
    </div>

    <Button className="w-8" />
  </div>
</div>
```

### Touch Targets

**Minimum Sizes (following iOS/Android guidelines):**
- Touch target: 44x44px minimum
- Icon buttons: 40x40px (w-10 h-10)
- Standard buttons: 36px height (h-9)

**Implementation:**
```tsx
// Icon button with proper touch target
<Button
  variant="ghost"
  size="sm"
  className="
    h-8 w-8        // Visual size
    p-0            // No padding (icon centered)
    min-h-[44px]   // Touch target
    min-w-[44px]   // Touch target
  "
>
  <X className="h-4 w-4" />
</Button>
```

### Modal Behavior

**Desktop:**
- Fixed width: 800px
- Centered on screen
- Backdrop blur

**Tablet:**
- Width: 90vw
- Max width: 700px
- Centered on screen

**Mobile:**
- Full screen overlay
- Width: 100vw
- Height: 100vh
- Scrollable content area
- Fixed header/footer

---

## States & Feedback

### Component States

**MultiplierCard:**

1. **Empty (No Field Selected)**
   - Field dropdown: Default state
   - Condition values: Hidden
   - Add button: Disabled with tooltip "Select a field first"

2. **Field Selected, No Values**
   - Field dropdown: Shows selected field
   - Condition values: Empty state message
   - Add button: Enabled, primary CTA

3. **Populated**
   - Field dropdown: Shows selected field with check icon
   - Condition values: List of rows
   - Add button: Enabled, secondary prominence

4. **Disabled**
   - Entire card: Opacity 60%, cursor not-allowed
   - All inputs: Disabled attribute
   - All buttons: Disabled attribute

**ConditionValueRow:**

1. **Default**
   - Value: Selected or placeholder
   - Multiplier: Valid number
   - Remove: Visible on hover (desktop), always visible (mobile)

2. **Hover (Desktop)**
   - Background: Slight darkening (bg-gray-100)
   - Remove button: Opacity 100%, red tint

3. **Focus**
   - Active input: Blue ring (ring-2 ring-blue-500)
   - Other elements: Normal state

4. **Error**
   - Invalid multiplier: Red border, error message below
   - Missing value: Red border, error icon

5. **Disabled**
   - Opacity: 60%
   - Cursor: not-allowed
   - Inputs: Non-interactive

### Validation States

**Field-Level Validation:**

```tsx
// Multiplier Input Validation
const [errors, setErrors] = useState<Record<string, string>>({});

function validateMultiplier(value: number): string | null {
  if (value < 0) {
    return "Multiplier must be positive";
  }
  if (value === 0) {
    return "Multiplier cannot be zero";
  }
  if (!isFinite(value)) {
    return "Multiplier must be a valid number";
  }
  return null;
}

// Render with error state
<div>
  <Input
    type="number"
    value={multiplier}
    onChange={handleChange}
    onBlur={handleValidation}
    className={cn(
      "h-8 text-sm",
      errors[id] && "border-red-500 focus-visible:ring-red-500"
    )}
    aria-invalid={!!errors[id]}
    aria-describedby={errors[id] ? `error-${id}` : undefined}
  />
  {errors[id] && (
    <p
      id={`error-${id}`}
      className="text-xs text-red-600 mt-1"
      role="alert"
    >
      {errors[id]}
    </p>
  )}
</div>
```

**Form-Level Validation:**

On Save Rule click:
1. Validate all multipliers
2. Validate all condition values
3. Check for duplicate values within same multiplier
4. Show summary error if any failures

```tsx
interface ValidationResult {
  valid: boolean;
  errors: Array<{
    multiplierId: string;
    conditionValueId?: string;
    message: string;
  }>;
}

function validateMultipliers(multipliers: ActionMultiplier[]): ValidationResult {
  const errors = [];

  for (const multiplier of multipliers) {
    // Check field selected
    if (!multiplier.fieldId) {
      errors.push({
        multiplierId: multiplier.id,
        message: "Field is required for multiplier"
      });
    }

    // Check has values
    if (multiplier.conditionValues.length === 0) {
      errors.push({
        multiplierId: multiplier.id,
        message: "At least one condition value recommended"
      });
    }

    // Check for duplicates
    const values = multiplier.conditionValues.map(cv => cv.value);
    const duplicates = values.filter((v, i) => values.indexOf(v) !== i);
    if (duplicates.length > 0) {
      errors.push({
        multiplierId: multiplier.id,
        message: `Duplicate values found: ${duplicates.join(", ")}`
      });
    }

    // Validate each condition value
    for (const cv of multiplier.conditionValues) {
      const error = validateMultiplier(cv.multiplier);
      if (error) {
        errors.push({
          multiplierId: multiplier.id,
          conditionValueId: cv.id,
          message: error
        });
      }
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}
```

### Loading States

**Initial Load (Editing Existing Rule):**
```tsx
{isLoading ? (
  <div className="space-y-3">
    <Skeleton className="h-32 w-full" /> {/* Multiplier card skeleton */}
    <Skeleton className="h-32 w-full" />
  </div>
) : (
  <MultipliersList multipliers={multipliers} />
)}
```

**Fetching Field Values (In Combobox):**
```tsx
<CommandList>
  {isLoadingValues ? (
    <CommandEmpty>
      <Loader2 className="h-4 w-4 animate-spin mx-auto" />
      Loading values...
    </CommandEmpty>
  ) : (
    // ... values list
  )}
</CommandList>
```

**Saving Changes:**
```tsx
<Button
  onClick={handleSave}
  disabled={isSaving}
>
  {isSaving ? (
    <>
      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
      Saving...
    </>
  ) : (
    "Save Rule"
  )}
</Button>
```

### Success/Error Feedback

**Success Toast (After Save):**
```tsx
import { useToast } from "@/components/ui/use-toast";

const { toast } = useToast();

function handleSaveSuccess() {
  toast({
    title: "Rule saved",
    description: "Your valuation rule has been updated successfully.",
    variant: "default", // Green checkmark
  });
}
```

**Error Toast (After Save Failure):**
```tsx
function handleSaveError(error: Error) {
  toast({
    title: "Failed to save rule",
    description: error.message || "An unexpected error occurred.",
    variant: "destructive", // Red X
  });
}
```

**Inline Validation Feedback:**
- Appears immediately below input
- Red text (text-red-600)
- Small font (text-xs)
- Icon prefix (optional): AlertCircle

---

## Implementation Notes

### Data Structure (Frontend State)

```typescript
// apps/web/components/rules/types.ts

export interface ActionMultiplier {
  id: string;                    // UUID (client-generated)
  name: string;                  // e.g., "RAM Generation Multiplier"
  fieldId: string;               // Field to check (e.g., "ram_type")
  conditionValues: ConditionValue[];
}

export interface ConditionValue {
  id: string;                    // UUID (client-generated)
  value: string;                 // Field value (e.g., "DDR4")
  multiplier: number;            // Multiplier to apply (e.g., 1.0)
}

export interface RuleFormData {
  // ... existing fields
  multipliers: ActionMultiplier[];
}
```

### API Contract (Backend)

**Expected Payload Format:**
```json
{
  "name": "Total RAM Capacity Valuation",
  "rule_group_id": "uuid-here",
  "conditions": [...],
  "action": {
    "type": "adjust_price",
    "metric": "total_capacity_gb",
    "per_unit": 5.00,
    "multipliers": [
      {
        "name": "RAM Generation Multiplier",
        "field_id": "ram_type",
        "condition_values": [
          { "value": "DDR3", "multiplier": 0.7 },
          { "value": "DDR4", "multiplier": 1.0 },
          { "value": "DDR5", "multiplier": 1.3 }
        ]
      }
    ]
  }
}
```

**Backend Model (SQLAlchemy):**
```python
# apps/api/dealbrain_api/models/core.py

class ValuationRule(Base):
    # ... existing fields

    # Store multipliers as JSON
    action_multipliers = Column(JSON, nullable=True)

    # Example stored value:
    # [
    #   {
    #     "name": "RAM Generation Multiplier",
    #     "field_id": "ram_type",
    #     "condition_values": [
    #       {"value": "DDR3", "multiplier": 0.7},
    #       {"value": "DDR4", "multiplier": 1.0},
    #       {"value": "DDR5", "multiplier": 1.3}
    #     ]
    #   }
    # ]
```

### React Hook Form Integration

```typescript
// apps/web/components/rules/RuleBuilderModal.tsx

import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

const ruleSchema = z.object({
  // ... existing fields
  multipliers: z.array(
    z.object({
      id: z.string().uuid(),
      name: z.string().min(1, "Name is required"),
      fieldId: z.string().min(1, "Field is required"),
      conditionValues: z.array(
        z.object({
          id: z.string().uuid(),
          value: z.string().min(1, "Value is required"),
          multiplier: z.number().positive("Multiplier must be positive")
        })
      ).min(1, "At least one condition value required")
    })
  ).optional()
});

export function RuleBuilderModal() {
  const { control, handleSubmit, watch } = useForm({
    resolver: zodResolver(ruleSchema),
    defaultValues: {
      multipliers: []
    }
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* ... other fields */}

      <Controller
        control={control}
        name="multipliers"
        render={({ field }) => (
          <ActionMultipliers
            multipliers={field.value}
            onMultipliersChange={field.onChange}
            ruleGroupId={watchedRuleGroupId}
          />
        )}
      />
    </form>
  );
}
```

### Performance Optimizations

**1. Memoization:**
```typescript
import { memo, useMemo } from "react";

export const MultiplierCard = memo(function MultiplierCard(props: MultiplierCardProps) {
  // Component logic
});

export const ConditionValueRow = memo(function ConditionValueRow(props: ConditionValueRowProps) {
  // Component logic
}, (prev, next) => {
  // Custom comparison
  return (
    prev.conditionValue.value === next.conditionValue.value &&
    prev.conditionValue.multiplier === next.conditionValue.multiplier &&
    prev.disabled === next.disabled
  );
});
```

**2. Debounced Value Fetching:**
```typescript
import { useDebouncedCallback } from "use-debounce";

function ValueCombobox({ fieldId }: ValueComboboxProps) {
  const [searchTerm, setSearchTerm] = useState("");

  const fetchValues = useDebouncedCallback(
    async (term: string) => {
      const values = await api.getFieldValues(fieldId, term);
      setOptions(values);
    },
    300 // 300ms delay
  );

  useEffect(() => {
    fetchValues(searchTerm);
  }, [searchTerm, fetchValues]);

  // ...
}
```

**3. Virtual Scrolling (If Many Values):**
```typescript
import { useVirtualizer } from "@tanstack/react-virtual";

function ConditionValuesList({ conditionValues }: ConditionValuesListProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: conditionValues.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 48, // Row height
    overscan: 5
  });

  return (
    <div ref={parentRef} className="max-h-96 overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: "relative"
        }}
      >
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.key}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              transform: `translateY(${virtualRow.start}px)`
            }}
          >
            <ConditionValueRow
              conditionValue={conditionValues[virtualRow.index]}
              {...}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Testing Considerations

**Unit Tests:**
```typescript
// apps/web/components/rules/__tests__/MultiplierCard.test.tsx

describe("MultiplierCard", () => {
  it("should render with default values", () => {
    const multiplier = {
      id: "1",
      name: "Test Multiplier",
      fieldId: "",
      conditionValues: []
    };

    render(<MultiplierCard multiplier={multiplier} {...} />);

    expect(screen.getByText("Test Multiplier")).toBeInTheDocument();
    expect(screen.getByText("Select a field first")).toBeInTheDocument();
  });

  it("should enable add button when field selected", () => {
    const multiplier = {
      id: "1",
      name: "Test",
      fieldId: "ram_type",
      conditionValues: []
    };

    render(<MultiplierCard multiplier={multiplier} {...} />);

    const addButton = screen.getByText("Add Condition Value");
    expect(addButton).not.toBeDisabled();
  });

  it("should call onUpdate when name changed", async () => {
    const onUpdate = jest.fn();
    const multiplier = { id: "1", name: "Old Name", ... };

    render(<MultiplierCard multiplier={multiplier} onUpdate={onUpdate} {...} />);

    const renameButton = screen.getByLabelText("Rename multiplier");
    await userEvent.click(renameButton);

    const nameInput = screen.getByRole("textbox");
    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, "New Name");
    await userEvent.keyboard("{Enter}");

    expect(onUpdate).toHaveBeenCalledWith(
      expect.objectContaining({ name: "New Name" })
    );
  });
});
```

**Integration Tests:**
```typescript
// apps/web/components/rules/__tests__/ActionMultipliers.integration.test.tsx

describe("ActionMultipliers Integration", () => {
  it("should complete full multiplier creation flow", async () => {
    const onChange = jest.fn();

    render(<ActionMultipliers multipliers={[]} onMultipliersChange={onChange} {...} />);

    // Add multiplier
    await userEvent.click(screen.getByText("Add Multiplier"));

    // Set name
    const nameInput = screen.getByRole("textbox");
    await userEvent.type(nameInput, "RAM Gen");
    await userEvent.keyboard("{Enter}");

    // Select field
    const fieldDropdown = screen.getByRole("combobox", { name: /field/i });
    await userEvent.click(fieldDropdown);
    await userEvent.click(screen.getByText("RAM Type"));

    // Add condition value
    await userEvent.click(screen.getByText("Add Condition Value"));

    // Select value
    const valueDropdown = screen.getByRole("combobox", { name: /value/i });
    await userEvent.click(valueDropdown);
    await userEvent.click(screen.getByText("DDR4"));

    // Set multiplier
    const multiplierInput = screen.getByRole("spinbutton", { name: /multiplier/i });
    await userEvent.clear(multiplierInput);
    await userEvent.type(multiplierInput, "1.0");

    // Verify final state
    expect(onChange).toHaveBeenLastCalledWith([
      expect.objectContaining({
        name: "RAM Gen",
        fieldId: "ram_type",
        conditionValues: [
          expect.objectContaining({
            value: "DDR4",
            multiplier: 1.0
          })
        ]
      })
    ]);
  });
});
```

---

## Example Scenarios

### Scenario 1: Basic RAM Generation Multiplier

**Context:** Creating a rule for RAM capacity valuation with different multipliers per DDR generation

**Visual Representation:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ RAM Generation Multiplier                  [Edit][×] ┃
┃                                                       ┃
┃ Field: [RAM Type ▼]                                  ┃
┃                                                       ┃
┃ ┌─────────────────────────────────────────────────┐ ┃
┃ │ DDR3              × 0.7                [Remove] │ ┃
┃ └─────────────────────────────────────────────────┘ ┃
┃ ┌─────────────────────────────────────────────────┐ ┃
┃ │ DDR4              × 1.0                [Remove] │ ┃
┃ └─────────────────────────────────────────────────┘ ┃
┃ ┌─────────────────────────────────────────────────┐ ┃
┃ │ DDR5              × 1.3                [Remove] │ ┃
┃ └─────────────────────────────────────────────────┘ ┃
┃                                                       ┃
┃ [+ Add Condition Value]                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

**Calculation Logic:**
```
Base Price Adjustment = $5.00 per GB
Total RAM = 16GB
RAM Type = DDR4

Step 1: Base calculation
  16 GB × $5.00 = $80.00

Step 2: Apply multiplier
  Find matching condition value: DDR4 → 1.0
  $80.00 × 1.0 = $80.00

Final Adjustment: $80.00
```

**Alternative Calculation (DDR5):**
```
16 GB × $5.00 = $80.00
$80.00 × 1.3 = $104.00
```

### Scenario 2: Multiple Multipliers on Same Action

**Context:** Combining RAM generation multiplier with capacity range multiplier

**Visual Representation:**
```
┌─ Multipliers ──────────────────────────────────────┐
│                                                     │
│ ┏━ RAM Generation Multiplier ━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Field: [RAM Type ▼]                           ┃ │
│ ┃ DDR3 × 0.7, DDR4 × 1.0, DDR5 × 1.3            ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                     │
│ ┏━ Capacity Range Multiplier ━━━━━━━━━━━━━━━━━┓  │
│ ┃ Field: [Total Capacity (GB) ▼]                ┃ │
│ ┃ 8 × 0.9, 16 × 1.0, 32 × 1.1, 64 × 1.2        ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                     │
│ [+ Add Multiplier]                                 │
└─────────────────────────────────────────────────────┘
```

**Calculation Logic:**
```
Base: $5.00 per GB
Total: 32GB
Type: DDR5

Step 1: Base
  32 GB × $5.00 = $160.00

Step 2: RAM Generation Multiplier
  DDR5 → 1.3
  $160.00 × 1.3 = $208.00

Step 3: Capacity Range Multiplier
  32 GB → 1.1
  $208.00 × 1.1 = $228.80

Final: $228.80
```

**Note:** Backend must apply multipliers in defined order or use composition strategy.

### Scenario 3: Condition Multiplier for SSD Type

**Context:** Storage valuation with different multipliers for SSD types

**Visual Representation:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Storage Type Multiplier                    [Edit][×] ┃
┃                                                       ┃
┃ Field: [Storage Type ▼]                              ┃
┃                                                       ┃
┃ ┌─────────────────────────────────────────────────┐ ┃
┃ │ HDD               × 0.5                [Remove] │ ┃
┃ └─────────────────────────────────────────────────┘ ┃
┃ ┌─────────────────────────────────────────────────┐ ┃
┃ │ SATA SSD          × 1.0                [Remove] │ ┃
┃ └─────────────────────────────────────────────────┘ ┃
┃ ┌─────────────────────────────────────────────────┐ ┃
┃ │ NVMe SSD          × 1.4                [Remove] │ ┃
┃ └─────────────────────────────────────────────────┘ ┃
┃ ┌─────────────────────────────────────────────────┐ ┃
┃ │ NVMe Gen4         × 1.6                [Remove] │ ┃
┃ └─────────────────────────────────────────────────┘ ┃
┃ ┌─────────────────────────────────────────────────┐ ┃
┃ │ NVMe Gen5         × 1.8                [Remove] │ ┃
┃ └─────────────────────────────────────────────────┘ ┃
┃                                                       ┃
┃ [+ Add Condition Value]                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Scenario 4: Error State Example

**Context:** User attempts to save with invalid multiplier value

**Visual Representation:**
```
┌─────────────────────────────────────────────────┐
│ DDR4              × -0.5              [Remove] │
│                     ↑                           │
│              [!] Multiplier must be positive    │
└─────────────────────────────────────────────────┘
```

**Form-Level Error Summary:**
```
┌─ Validation Errors ────────────────────────────┐
│ ⚠ Cannot save rule. Please fix the following:  │
│                                                 │
│ • RAM Generation Multiplier:                   │
│   - DDR4 multiplier must be positive           │
│                                                 │
│ • Storage Type Multiplier:                     │
│   - Field is required                          │
└─────────────────────────────────────────────────┘
```

### Scenario 5: Empty State

**Context:** Action section before any multipliers added

**Visual Representation:**
```
┌─ Multipliers ──────────────────────────────────────┐
│                                                     │
│ Apply conditional multipliers to this action       │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │                                             │   │
│ │  No multipliers configured                  │   │
│ │                                             │   │
│ │  Multipliers allow you to apply different  │   │
│ │  values based on field conditions.         │   │
│ │                                             │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ [+ Add Multiplier]                                 │
└─────────────────────────────────────────────────────┘
```

---

## Visual Design Mockup (Detailed)

### Full Modal Layout with Multipliers

```
┌──────────────────────────────────────────────────────────────────┐
│ Create Valuation Rule                                      [X]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│ ┌──────────────┬──────────────┐                                  │
│ │ Basic Mode   │ Advanced Mode│ ← Active                         │
│ └──────────────┴──────────────┘                                  │
│                                                                    │
│ ┌─ Rule Configuration ─────────────────────────────────────────┐ │
│ │                                                               │ │
│ │ Name *                                                        │ │
│ │ [Total RAM Capacity Valuation                            ]   │ │
│ │                                                               │ │
│ │ Description                                                   │ │
│ │ [Adjusts price based on total RAM capacity                   │ │
│ │  with generation-specific multipliers               ]        │ │
│ │                                                               │ │
│ │ Rule Group *                                                  │ │
│ │ [RamSpec ▼]                                                   │ │
│ │                                                               │ │
│ └───────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ ┌─ Conditions ──────────────────────────────────────────────────┐ │
│ │                                                               │ │
│ │ Match [All ▼] of the following conditions:                   │ │
│ │                                                               │ │
│ │ ┌────────────────────────────────────────────────────────┐  │ │
│ │ │ [RAM Present ▼] [equals ▼] [Yes ▼]        [Remove]    │  │ │
│ │ └────────────────────────────────────────────────────────┘  │ │
│ │                                                               │ │
│ │ [+ Add Condition]                                            │ │
│ │                                                               │ │
│ └───────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ ┌─ Actions ─────────────────────────────────────────────────────┐ │
│ │                                                               │ │
│ │ Action Type *                                                 │ │
│ │ [Adjust Price ▼]                                             │ │
│ │                                                               │ │
│ │ Component Metric *                                            │ │
│ │ [Total Capacity (GB) ▼]                                      │ │
│ │                                                               │ │
│ │ Per Unit Value *                                              │ │
│ │ [$5.00                                              ]         │ │
│ │                                                               │ │
│ │ ┌─ Multipliers ────────────────────────────────────────────┐ │ │
│ │ │                                                           │ │ │
│ │ │ Multipliers                                              │ │ │
│ │ │ Apply conditional multipliers to this action based on    │ │ │
│ │ │ field values                                             │ │ │
│ │ │                                                           │ │ │
│ │ │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │ │ │
│ │ │ ┃ RAM Generation Multiplier            [Rename][×]  ┃  │ │ │
│ │ │ ┃                                                     ┃  │ │ │
│ │ │ ┃ Field                                               ┃  │ │ │
│ │ │ ┃ [RAM Type ▼]                                       ┃  │ │ │
│ │ │ ┃                                                     ┃  │ │ │
│ │ │ ┃ ┌──────────────────────────────────────────────┐  ┃  │ │ │
│ │ │ ┃ │ Value          Multiplier                    │  ┃  │ │ │
│ │ │ ┃ └──────────────────────────────────────────────┘  ┃  │ │ │
│ │ │ ┃                                                     ┃  │ │ │
│ │ │ ┃ ┌──────────────────────────────────────────────┐  ┃  │ │ │
│ │ │ ┃ │ [DDR3 ▼]       × [0.7    ]        [Remove]  │  ┃  │ │ │
│ │ │ ┃ └──────────────────────────────────────────────┘  ┃  │ │ │
│ │ │ ┃ ┌──────────────────────────────────────────────┐  ┃  │ │ │
│ │ │ ┃ │ [DDR4 ▼]       × [1.0    ]        [Remove]  │  ┃  │ │ │
│ │ │ ┃ └──────────────────────────────────────────────┘  ┃  │ │ │
│ │ │ ┃ ┌──────────────────────────────────────────────┐  ┃  │ │ │
│ │ │ ┃ │ [DDR5 ▼]       × [1.3    ]        [Remove]  │  ┃  │ │ │
│ │ │ ┃ └──────────────────────────────────────────────┘  ┃  │ │ │
│ │ │ ┃                                                     ┃  │ │ │
│ │ │ ┃ [+ Add Condition Value]                            ┃  │ │ │
│ │ │ ┃                                                     ┃  │ │ │
│ │ │ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │ │ │
│ │ │                                                           │ │ │
│ │ │ [+ Add Multiplier]                                       │ │ │
│ │ │                                                           │ │ │
│ │ └───────────────────────────────────────────────────────────┘ │ │
│ │                                                               │ │
│ └───────────────────────────────────────────────────────────────┘ │
│                                                                    │
│                                        [Cancel]  [Save Rule]      │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

### Color-Coded Hierarchy

```
Gray Background (bg-gray-50):
└─ Modal Content Area
    │
    ├─ White Cards (bg-white, border-gray-200):
    │  └─ Rule Config, Conditions, Actions sections
    │
    └─ Actions Card:
        └─ Blue-Tinted Section (bg-blue-50/30, border-blue-200):
            └─ Multipliers Container
                │
                └─ White Cards (bg-white, border-blue-300, shadow-sm):
                    └─ Individual Multiplier Cards
                        │
                        └─ Gray Rows (bg-gray-50/50, border-gray-200):
                            └─ Condition Value Rows
```

---

## Summary of Key Design Decisions

### 1. Visual Separation
- **Decision:** Blue color theme for multipliers (vs gray for conditions)
- **Rationale:** Prevents confusion between Rule Conditions and Action Multipliers
- **Impact:** Users can visually distinguish hierarchy at a glance

### 2. Progressive Disclosure
- **Decision:** Multipliers section starts collapsed/empty
- **Rationale:** Reduces cognitive load, doesn't intimidate new users
- **Impact:** Advanced users can add complexity when needed

### 3. Inline Editing
- **Decision:** Name editing in-place vs separate dialog
- **Rationale:** Faster workflow, fewer modals to manage
- **Impact:** Reduces clicks and context switching

### 4. Combobox for Values
- **Decision:** Hybrid dropdown + text input (vs strict dropdown)
- **Rationale:** Supports both existing values and creating new ones
- **Impact:** Future-proof (DDR6, new SSD types) without backend changes

### 5. Explicit Remove Confirmations
- **Decision:** Confirm multiplier removal, direct for rows
- **Rationale:** Multipliers are high-level (costly to recreate), rows are low-level (quick to recreate)
- **Impact:** Prevents accidental data loss while maintaining speed

### 6. Reusable Components
- **Decision:** Share FieldSelector with Conditions builder
- **Rationale:** Consistency, reduced code duplication, easier maintenance
- **Impact:** Users learn one pattern, applies in multiple contexts

### 7. Responsive Grid Layout
- **Decision:** CSS Grid with conditional columns (vs Flexbox)
- **Rationale:** Precise alignment, better responsive behavior
- **Impact:** Clean mobile layout without complex media queries

### 8. Accessibility First
- **Decision:** ARIA labels, keyboard navigation, focus management from start
- **Rationale:** WCAG compliance is requirement, not afterthought
- **Impact:** Inclusive product, better for all users (keyboard shortcuts benefit power users)

---

## Next Steps for Implementation

### Phase 1: Component Structure (Week 1)
1. Create base components without data binding:
   - `ActionMultipliers.tsx`
   - `MultiplierCard.tsx`
   - `MultiplierHeader.tsx`
   - `ConditionValuesList.tsx`
   - `ConditionValueRow.tsx`
   - `ValueCombobox.tsx`

2. Implement styling and layout
3. Add static data for visual testing

### Phase 2: State Management (Week 2)
1. Integrate React Hook Form
2. Implement add/remove logic
3. Connect to parent form state
4. Add validation rules

### Phase 3: API Integration (Week 3)
1. Implement field values fetching
2. Add save/load functionality
3. Handle optimistic updates
4. Add error handling

### Phase 4: Accessibility & Polish (Week 4)
1. Add ARIA labels and roles
2. Implement keyboard navigation
3. Add focus management
4. Test with screen readers
5. Add animations and transitions

### Phase 5: Testing & Documentation (Week 5)
1. Write unit tests
2. Write integration tests
3. Add Storybook stories
4. Document component APIs
5. Create user guide/help text

---

## Appendix

### A. Component File Paths

```
apps/web/components/rules/
├── ActionMultipliers.tsx          # Main container
├── MultiplierCard.tsx             # Individual multiplier
├── MultiplierHeader.tsx           # Editable name header
├── ConditionValuesList.tsx        # List of condition values
├── ConditionValueRow.tsx          # Single condition value row
├── ValueCombobox.tsx              # Value selector/creator
├── types.ts                       # TypeScript interfaces
└── __tests__/
    ├── ActionMultipliers.test.tsx
    ├── MultiplierCard.test.tsx
    ├── ConditionValueRow.test.tsx
    └── ActionMultipliers.integration.test.tsx
```

### B. API Endpoints Needed

```typescript
// Fetch field values for autocomplete
GET /api/fields/{fieldId}/values
Query params: ?search=DDR&limit=10
Response: { values: ["DDR3", "DDR4", "DDR5"] }

// Create new field value (optional, may happen automatically on save)
POST /api/fields/{fieldId}/values
Body: { value: "DDR6" }
Response: { id: "uuid", value: "DDR6", fieldId: "..." }

// Save rule with multipliers
PUT /api/rules/{ruleId}
Body: {
  action: {
    multipliers: [...]
  }
}
```

### C. Dependencies to Install

```bash
# Component libraries (likely already installed)
pnpm add @radix-ui/react-popover
pnpm add @radix-ui/react-dialog
pnpm add cmdk  # For Command palette (used in Combobox)

# Form handling
pnpm add react-hook-form
pnpm add @hookform/resolvers
pnpm add zod

# Utilities
pnpm add uuid
pnpm add use-debounce

# Dev dependencies
pnpm add -D @testing-library/react
pnpm add -D @testing-library/user-event
pnpm add -D @testing-library/jest-dom
```

### D. Storybook Stories

```typescript
// apps/web/components/rules/ActionMultipliers.stories.tsx

import type { Meta, StoryObj } from "@storybook/react";
import { ActionMultipliers } from "./ActionMultipliers";

const meta: Meta<typeof ActionMultipliers> = {
  title: "Rules/ActionMultipliers",
  component: ActionMultipliers,
  parameters: {
    layout: "padded"
  }
};

export default meta;
type Story = StoryObj<typeof ActionMultipliers>;

export const Empty: Story = {
  args: {
    multipliers: [],
    ruleGroupId: "ramspec"
  }
};

export const SingleMultiplier: Story = {
  args: {
    multipliers: [
      {
        id: "1",
        name: "RAM Generation Multiplier",
        fieldId: "ram_type",
        conditionValues: [
          { id: "1a", value: "DDR3", multiplier: 0.7 },
          { id: "1b", value: "DDR4", multiplier: 1.0 },
          { id: "1c", value: "DDR5", multiplier: 1.3 }
        ]
      }
    ],
    ruleGroupId: "ramspec"
  }
};

export const MultipleMultipliers: Story = {
  args: {
    multipliers: [
      {
        id: "1",
        name: "RAM Generation Multiplier",
        fieldId: "ram_type",
        conditionValues: [
          { id: "1a", value: "DDR3", multiplier: 0.7 },
          { id: "1b", value: "DDR4", multiplier: 1.0 },
          { id: "1c", value: "DDR5", multiplier: 1.3 }
        ]
      },
      {
        id: "2",
        name: "Capacity Range Multiplier",
        fieldId: "total_capacity_gb",
        conditionValues: [
          { id: "2a", value: "8", multiplier: 0.9 },
          { id: "2b", value: "16", multiplier: 1.0 },
          { id: "2c", value: "32", multiplier: 1.1 }
        ]
      }
    ],
    ruleGroupId: "ramspec"
  }
};

export const WithValidationErrors: Story = {
  args: {
    multipliers: [
      {
        id: "1",
        name: "",
        fieldId: "",
        conditionValues: []
      }
    ],
    ruleGroupId: "ramspec"
  }
};
```

### E. Backend Implementation Notes

**SQLAlchemy Migration:**
```python
# alembic/versions/xxx_add_action_multipliers.py

def upgrade():
    op.add_column(
        'valuation_rules',
        sa.Column('action_multipliers', sa.JSON(), nullable=True)
    )

def downgrade():
    op.drop_column('valuation_rules', 'action_multipliers')
```

**Validation Schema (Pydantic):**
```python
# packages/core/schemas/rules.py

from pydantic import BaseModel, Field
from typing import List, Optional

class ConditionValueSchema(BaseModel):
    value: str = Field(..., min_length=1)
    multiplier: float = Field(..., gt=0)

class ActionMultiplierSchema(BaseModel):
    name: str = Field(..., min_length=1)
    field_id: str
    condition_values: List[ConditionValueSchema] = Field(..., min_items=1)

class RuleActionSchema(BaseModel):
    type: str
    metric: Optional[str] = None
    per_unit: Optional[float] = None
    multipliers: Optional[List[ActionMultiplierSchema]] = None
```

**Application Logic:**
```python
# packages/core/valuation.py

def apply_action_multipliers(
    base_value: float,
    multipliers: List[ActionMultiplierSchema],
    listing_data: dict
) -> float:
    """
    Apply all multipliers to base value in sequence.

    Args:
        base_value: Initial calculated value
        multipliers: List of multiplier configurations
        listing_data: Listing data to match conditions against

    Returns:
        Final value after all multipliers applied
    """
    current_value = base_value

    for multiplier in multipliers:
        # Get field value from listing
        field_value = listing_data.get(multiplier.field_id)

        # Find matching condition value
        for cv in multiplier.condition_values:
            if str(field_value) == cv.value:
                current_value *= cv.multiplier
                break

    return current_value
```

---

## Document Metadata

**Author:** UI/UX Design Team
**Reviewers:** Frontend Engineering, Backend Engineering, Product
**Status:** Draft v1.0
**Last Updated:** 2025-10-15

**Change Log:**
- 2025-10-15: Initial draft created

**Related Documents:**
- Basic to Advanced Rules PRD
- Valuation Rules System Architecture
- Component Library Style Guide
- Accessibility Guidelines

---

*End of Specification*
