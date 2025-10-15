# Valuation Rules System Implementation Plan

## Overview

This implementation plan addresses critical bugs and enhancements for the Valuation Rules System, organized into four phases over 7 weeks. The plan follows a phased approach prioritizing critical bug fixes first, followed by UX improvements, new features, and finally the advanced formula builder.

## Project Metadata

- **Total Duration**: 7 weeks
- **Team Size**: 2-3 developers
- **Risk Level**: Medium (existing system modifications)
- **Dependencies**: FastAPI, SQLAlchemy, Next.js 14, React Query, shadcn/ui

## Phase Structure

```
Week 1: Phase 1 - Critical Bug Fixes
Week 2: Phase 2 - UX Improvements
Weeks 3-4: Phase 3 - Action Multipliers
Weeks 5-7: Phase 4 - Formula Builder
```

---

## Phase 1: Critical Bug Fixes (Week 1)

### Overview
Fix critical functionality issues preventing proper use of Advanced Mode and baseline rule hydration.

### Task List

#### P1-BUG-001: Fix RuleGroup Modal Opening Issue
**Priority**: Critical
**Time Estimate**: 4 hours
**Dependencies**: None

**Description**:
The "Add RuleGroup" button in the RuleGroup pane incorrectly opens the RuleSet creation modal instead of the RuleGroup creation modal when no existing RuleGroups exist.

**Acceptance Criteria**:
- [ ] "Add RuleGroup" button opens correct RuleGroup modal
- [ ] Modal opens correctly when no RuleGroups exist
- [ ] Modal opens correctly when RuleGroups exist
- [ ] Proper modal state management implemented

**Files to Modify**:
- `/mnt/containers/deal-brain/apps/web/app/valuation-rules/page.tsx`
- `/mnt/containers/deal-brain/apps/web/components/valuation/rule-group-form-modal.tsx`

**Implementation Notes**:
```typescript
// Fix modal handler in page.tsx
const handleAddRuleGroup = () => {
  // Ensure correct modal state is set
  setIsRuleGroupModalOpen(true);
  setIsRulesetModalOpen(false);
  setSelectedRuleset(currentRuleset);
};

// Add validation to prevent modal confusion
const validateModalState = () => {
  if (isRulesetModalOpen && isRuleGroupModalOpen) {
    console.error("Multiple modals open simultaneously");
    return false;
  }
  return true;
};
```

**Testing Requirements**:
- [ ] Unit test for modal state management
- [ ] E2E test for RuleGroup creation flow
- [ ] Manual testing with empty and populated RuleGroups

---

#### P1-BUG-002: Fix RuleGroup List Refresh After Creation
**Priority**: Critical
**Time Estimate**: 3 hours
**Dependencies**: P1-BUG-001

**Description**:
Newly created RuleGroups don't appear in the list after creation. No errors in logs indicate a state refresh issue.

**Acceptance Criteria**:
- [ ] New RuleGroups appear immediately after creation
- [ ] React Query cache properly invalidated
- [ ] List updates without full page refresh
- [ ] Proper optimistic updates implemented

**Files to Modify**:
- `/mnt/containers/deal-brain/apps/web/hooks/useRuleGroups.ts`
- `/mnt/containers/deal-brain/apps/web/components/valuation/rule-group-form-modal.tsx`

**Implementation Notes**:
```typescript
// In useRuleGroups.ts
const createRuleGroupMutation = useMutation({
  mutationFn: async (data: CreateRuleGroupData) => {
    return await api.createRuleGroup(data);
  },
  onSuccess: () => {
    // Invalidate and refetch
    queryClient.invalidateQueries(['ruleGroups', rulesetId]);
    queryClient.invalidateQueries(['ruleset', rulesetId]);
  },
  onError: (error) => {
    console.error('Failed to create rule group:', error);
    toast.error('Failed to create rule group');
  }
});
```

**Testing Requirements**:
- [ ] Unit test for React Query invalidation
- [ ] Integration test for API response handling
- [ ] Manual test with network throttling

---

#### P1-BUG-003: Fix Formula Action Evaluation
**Priority**: Critical
**Time Estimate**: 8 hours
**Dependencies**: None

**Description**:
Formula-type Actions are not being evaluated correctly, causing no valuation adjustments despite valid formulas.

**Acceptance Criteria**:
- [ ] Formula actions correctly parse and evaluate
- [ ] CPU Mark formulas apply proper adjustments
- [ ] Error handling for invalid formulas
- [ ] Debug logging for formula evaluation
- [ ] Validation feedback in UI

**Files to Modify**:
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/formula.py`
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/evaluator.py`
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/rule_evaluation.py`

**Implementation Notes**:
```python
# In formula.py - Add better error handling
class FormulaEngine:
    def evaluate(self, formula: str, context: dict[str, Any]) -> float:
        """Evaluate formula with comprehensive error handling."""
        try:
            # Parse formula
            parsed = self._parse_formula(formula)

            # Validate all variables exist in context
            missing_vars = self._check_missing_variables(parsed, context)
            if missing_vars:
                raise FormulaEvaluationError(
                    f"Missing variables in context: {missing_vars}"
                )

            # Evaluate with safety checks
            result = self._safe_evaluate(parsed, context)

            # Log successful evaluation
            logger.debug(f"Formula evaluated: {formula} = {result}")
            return result

        except Exception as e:
            logger.error(f"Formula evaluation failed: {formula}, Error: {e}")
            raise FormulaEvaluationError(str(e))

    def _parse_formula(self, formula: str) -> Any:
        """Parse formula text with validation."""
        # Handle special syntax like "usd ≈"
        formula = formula.replace("usd ≈", "").strip()
        formula = formula.replace("with cohort guardrails", "").strip()

        # Validate syntax
        if not self._validate_syntax(formula):
            raise FormulaParseError(f"Invalid formula syntax: {formula}")

        return ast.parse(formula, mode='eval')
```

**Testing Requirements**:
- [ ] Unit tests for formula parsing edge cases
- [ ] Integration tests with real listing data
- [ ] Test suite for all baseline formulas
- [ ] Performance tests for bulk evaluation

---

#### P1-BUG-004: Fix Baseline Rule Hydration Issues
**Priority**: Critical
**Time Estimate**: 6 hours
**Dependencies**: P1-BUG-003

**Description**:
Baseline rules not properly hydrating - missing conditions/actions, null values in Fixed adjustments.

**Acceptance Criteria**:
- [ ] All baseline rules hydrate with proper conditions
- [ ] Actions have correct values (not null)
- [ ] RAM rules properly expanded per DDR generation
- [ ] Formula actions correctly transferred

**Files to Modify**:
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/baseline_hydration.py`
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/endpoints/baseline.py`

**Implementation Notes**:
```python
# In baseline_hydration.py
async def _hydrate_enum_multiplier(
    self,
    session: AsyncSession,
    rule: ValuationRuleV2,
    actor: str
) -> list[ValuationRuleV2]:
    """Hydrate enum multiplier placeholder into multiple rules."""
    metadata = rule.metadata_json
    valuation_buckets = metadata.get("valuation_buckets", {})
    field_id = metadata.get("field_id")

    if not valuation_buckets or not field_id:
        logger.error(f"Invalid metadata for rule {rule.id}")
        return []

    expanded_rules = []

    for enum_value, multiplier in valuation_buckets.items():
        # Create condition for this enum value
        condition_data = {
            "field_name": field_id,
            "operator": "equals",
            "value_json": enum_value,
            "logical_operator": "AND"
        }

        # Create action with proper value (not null)
        action_data = {
            "action_type": "multiplier",
            "value_usd": multiplier * 100,  # Convert to percentage
            "modifiers_json": {
                "original_multiplier": multiplier
            }
        }

        # Create the expanded rule
        rule_data = {
            "name": f"{rule.name}: {enum_value.upper()}",
            "rule_group_id": rule.rule_group_id,
            "evaluation_order": rule.evaluation_order,
            "is_active": True,
            "conditions": [condition_data],
            "actions": [action_data],
            "metadata_json": {
                "hydration_source_rule_id": rule.id,
                "enum_value": enum_value,
                "field_type": "enum_multiplier"
            }
        }

        new_rule = await self.rules_service.create_rule(
            session,
            rule_data,
            actor=actor
        )
        expanded_rules.append(new_rule)

    return expanded_rules
```

**Testing Requirements**:
- [ ] Unit tests for each hydration strategy
- [ ] Integration test for full ruleset hydration
- [ ] Verification that valuations remain unchanged
- [ ] Test rollback on partial failure

---

#### P1-BUG-005: Hide Foreign Key Rules in Advanced Mode
**Priority**: High
**Time Estimate**: 2 hours
**Dependencies**: None

**Description**:
Foreign Key Rules (RAM Spec, Primary Storage Profile) should be hidden in Advanced Mode as they cannot be edited.

**Acceptance Criteria**:
- [ ] Foreign key rules not displayed by default
- [ ] Optional toggle to show system rules (view-only)
- [ ] Clear visual distinction for system rules
- [ ] Proper filtering in API and frontend

**Files to Modify**:
- `/mnt/containers/deal-brain/apps/web/app/valuation-rules/page.tsx`
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/endpoints/rules.py`

**Implementation Notes**:
```typescript
// In page.tsx
const filterSystemRules = (rules: ValuationRule[]) => {
  if (showSystemRules) {
    return rules;
  }
  return rules.filter(rule =>
    !rule.metadata_json?.is_foreign_key_rule
  );
};

// Add toggle in UI
<div className="flex items-center gap-2">
  <Switch
    checked={showSystemRules}
    onCheckedChange={setShowSystemRules}
  />
  <Label>Show system rules (read-only)</Label>
</div>
```

**Testing Requirements**:
- [ ] Unit test for rule filtering logic
- [ ] UI test for toggle functionality
- [ ] Verify system rules are read-only when shown

---

## Phase 2: UX Improvements (Week 2)

### Overview
Enhance user experience with scrollable dropdowns and improved field selection.

### Task List

#### P2-UX-001: Implement Scrollable Dropdown for Field Selection
**Priority**: High
**Time Estimate**: 6 hours
**Dependencies**: None

**Description**:
The Condition builder dropdown extends beyond viewport when list is long. Implement virtual scrolling.

**Acceptance Criteria**:
- [ ] Dropdown constrained to viewport height
- [ ] Smooth scrolling with 200+ items
- [ ] Keyboard navigation works
- [ ] Search/filter functionality
- [ ] Selected item remains visible
- [ ] Mobile responsive

**Files to Modify**:
- `/mnt/containers/deal-brain/apps/web/components/valuation/entity-field-selector.tsx`
- `/mnt/containers/deal-brain/apps/web/components/ui/command.tsx`
- `/mnt/containers/deal-brain/apps/web/components/valuation/condition-group.tsx`

**Implementation Notes**:
```typescript
// New ScrollableFieldSelector component
import { useVirtualizer } from '@tanstack/react-virtual';

export function ScrollableFieldSelector({
  fields,
  onSelect,
  maxHeight = 400
}: Props) {
  const parentRef = useRef<HTMLDivElement>(null);
  const [search, setSearch] = useState('');

  const filteredFields = useMemo(() =>
    fields.filter(f =>
      f.label.toLowerCase().includes(search.toLowerCase())
    ),
    [fields, search]
  );

  const virtualizer = useVirtualizer({
    count: filteredFields.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 35,
    overscan: 5
  });

  return (
    <Command className="border rounded-lg">
      <CommandInput
        placeholder="Search fields..."
        value={search}
        onValueChange={setSearch}
      />
      <CommandList
        ref={parentRef}
        className="max-h-[400px] overflow-y-auto"
      >
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative'
          }}
        >
          {virtualizer.getVirtualItems().map((virtualItem) => {
            const field = filteredFields[virtualItem.index];
            return (
              <CommandItem
                key={field.name}
                value={field.name}
                onSelect={() => onSelect(field)}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: `${virtualItem.size}px`,
                  transform: `translateY(${virtualItem.start}px)`
                }}
              >
                <div className="flex items-center justify-between w-full">
                  <span>{field.label}</span>
                  <Badge variant="outline" className="ml-2">
                    {field.type}
                  </Badge>
                </div>
              </CommandItem>
            );
          })}
        </div>
      </CommandList>
    </Command>
  );
}
```

**Testing Requirements**:
- [ ] Performance test with 500+ items
- [ ] Keyboard navigation test
- [ ] Mobile viewport test
- [ ] Accessibility audit (WCAG AA)

---

#### P2-UX-002: Add Field Value Autocomplete
**Priority**: Medium
**Time Estimate**: 5 hours
**Dependencies**: P2-UX-001

**Description**:
When selecting field values in conditions, provide autocomplete from existing values.

**Acceptance Criteria**:
- [ ] Fetch existing values for selected field
- [ ] Show autocomplete suggestions
- [ ] Allow free text input
- [ ] Cache field values for performance
- [ ] Handle enum fields specially

**Files to Modify**:
- `/mnt/containers/deal-brain/apps/web/components/valuation/value-input.tsx`
- `/mnt/containers/deal-brain/apps/web/hooks/useFieldValues.ts` (new)
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/endpoints/fields.py`

**Implementation Notes**:
```typescript
// New hook for field values
export function useFieldValues(fieldName: string) {
  return useQuery({
    queryKey: ['fieldValues', fieldName],
    queryFn: async () => {
      const response = await fetch(
        `${API_URL}/api/v1/fields/${fieldName}/values`
      );
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    enabled: !!fieldName
  });
}

// Enhanced ValueInput component
export function ValueInput({
  field,
  value,
  onChange
}: ValueInputProps) {
  const { data: fieldValues } = useFieldValues(field.name);
  const [isOpen, setIsOpen] = useState(false);

  if (field.type === 'enum' && fieldValues?.length > 0) {
    return (
      <Combobox
        options={fieldValues}
        value={value}
        onValueChange={onChange}
        placeholder="Select or type value..."
        allowCustomValue
      />
    );
  }

  // Fallback to appropriate input type
  return <Input ... />;
}
```

**Testing Requirements**:
- [ ] Test with enum fields
- [ ] Test with text fields
- [ ] Test with numeric fields
- [ ] Performance test with many values
- [ ] Test custom value entry

---

## Phase 3: Action Multipliers System (Weeks 3-4)

### Overview
Implement the Action Multipliers system for handling complex condition-to-action mappings, particularly for RAM generation multipliers.

### Task List

#### P3-FEAT-001: Database Schema for Action Multipliers
**Priority**: High
**Time Estimate**: 4 hours
**Dependencies**: None

**Description**:
Add database support for Action Multipliers attached to rule actions.

**Acceptance Criteria**:
- [ ] Migration adds multipliers_json to actions
- [ ] Schema supports multiple multipliers per action
- [ ] Backward compatible with existing actions
- [ ] Proper indexes for performance

**Files to Modify**:
- New migration file: `alembic revision -m "Add action multipliers support"`
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`

**Implementation Notes**:
```python
# Migration script
def upgrade():
    # The multipliers_json column already exists
    # Add validation and documentation
    op.execute("""
        COMMENT ON COLUMN valuation_rule_action.modifiers_json IS
        'Stores action multipliers and other modifiers. Structure:
        {
          "multipliers": [
            {
              "name": "RAM Generation Multiplier",
              "field": "ram_spec.ddr_generation",
              "conditions": [
                {"value": "ddr3", "multiplier": 0.7},
                {"value": "ddr4", "multiplier": 1.0},
                {"value": "ddr5", "multiplier": 1.3}
              ]
            }
          ]
        }';
    """)
```

**Testing Requirements**:
- [ ] Migration runs successfully
- [ ] Rollback works correctly
- [ ] Existing data preserved
- [ ] JSON validation works

---

#### P3-FEAT-002: Backend Action Multipliers Service
**Priority**: High
**Time Estimate**: 8 hours
**Dependencies**: P3-FEAT-001

**Description**:
Implement backend logic for evaluating and applying action multipliers.

**Acceptance Criteria**:
- [ ] Multipliers evaluated during rule execution
- [ ] Multiple multipliers can stack
- [ ] Proper calculation order
- [ ] Performance optimized
- [ ] Comprehensive logging

**Files to Modify**:
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/action_engine.py`
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/evaluator.py`
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/rules.py`

**Implementation Notes**:
```python
# In action_engine.py
class ActionEngine:
    def execute_action(
        self,
        action: ValuationRuleAction,
        context: dict[str, Any]
    ) -> float:
        """Execute action with multiplier support."""
        base_value = self._calculate_base_value(action, context)

        # Apply multipliers if present
        if action.modifiers_json and "multipliers" in action.modifiers_json:
            multiplier_value = self._apply_multipliers(
                action.modifiers_json["multipliers"],
                context
            )
            return base_value * multiplier_value

        return base_value

    def _apply_multipliers(
        self,
        multipliers: list[dict],
        context: dict[str, Any]
    ) -> float:
        """Apply all matching multipliers."""
        total_multiplier = 1.0

        for multiplier_config in multipliers:
            field_value = self._get_nested_value(
                context,
                multiplier_config["field"]
            )

            for condition in multiplier_config["conditions"]:
                if field_value == condition["value"]:
                    total_multiplier *= condition["multiplier"]
                    logger.debug(
                        f"Applied multiplier {condition['multiplier']} "
                        f"for {multiplier_config['name']}"
                    )
                    break

        return total_multiplier
```

**Testing Requirements**:
- [ ] Unit tests for multiplier calculations
- [ ] Integration tests with real rules
- [ ] Performance tests with many multipliers
- [ ] Edge case handling

---

#### P3-FEAT-003: Frontend Action Multipliers UI
**Priority**: High
**Time Estimate**: 12 hours
**Dependencies**: P3-FEAT-002, P2-UX-001

**Description**:
Build UI components for creating and managing action multipliers.

**Acceptance Criteria**:
- [ ] Add/remove multipliers in action builder
- [ ] Select field and values from dropdown
- [ ] Set multiplier values
- [ ] Visual preview of multiplier effects
- [ ] Validation and error handling
- [ ] Mobile responsive

**Files to Modify**:
- `/mnt/containers/deal-brain/apps/web/components/valuation/action-builder.tsx`
- `/mnt/containers/deal-brain/apps/web/components/valuation/action-multipliers.tsx` (new)
- `/mnt/containers/deal-brain/apps/web/components/valuation/rule-builder-modal.tsx`

**Implementation Notes**:
```typescript
// New ActionMultipliers component
interface ActionMultiplier {
  name: string;
  field: string;
  conditions: Array<{
    value: string;
    multiplier: number;
  }>;
}

export function ActionMultipliers({
  multipliers,
  onChange,
  availableFields
}: Props) {
  const [expanded, setExpanded] = useState<number[]>([]);

  const handleAddMultiplier = () => {
    const newMultiplier: ActionMultiplier = {
      name: 'New Multiplier',
      field: '',
      conditions: []
    };
    onChange([...multipliers, newMultiplier]);
  };

  const handleFieldChange = (index: number, field: string) => {
    const updated = [...multipliers];
    updated[index].field = field;
    // Reset conditions when field changes
    updated[index].conditions = [];
    onChange(updated);
  };

  const handleAddCondition = (index: number) => {
    const updated = [...multipliers];
    updated[index].conditions.push({
      value: '',
      multiplier: 1.0
    });
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label>Action Multipliers</Label>
        <Button
          variant="outline"
          size="sm"
          onClick={handleAddMultiplier}
        >
          <Plus className="h-4 w-4 mr-1" />
          Add Multiplier
        </Button>
      </div>

      {multipliers.map((multiplier, index) => (
        <Card key={index} className="p-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Input
                value={multiplier.name}
                onChange={(e) => handleNameChange(index, e.target.value)}
                placeholder="Multiplier name..."
                className="max-w-xs"
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleRemove(index)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="grid gap-3">
              <ScrollableFieldSelector
                fields={availableFields}
                value={multiplier.field}
                onSelect={(field) => handleFieldChange(index, field.name)}
                placeholder="Select field..."
              />

              {multiplier.field && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm">Conditions</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleAddCondition(index)}
                    >
                      <Plus className="h-3 w-3 mr-1" />
                      Add
                    </Button>
                  </div>

                  {multiplier.conditions.map((condition, condIdx) => (
                    <div key={condIdx} className="flex items-center gap-2">
                      <ValueInput
                        field={{ name: multiplier.field }}
                        value={condition.value}
                        onChange={(val) =>
                          handleConditionValueChange(index, condIdx, val)
                        }
                        className="flex-1"
                      />
                      <span>×</span>
                      <Input
                        type="number"
                        step="0.1"
                        value={condition.multiplier}
                        onChange={(e) =>
                          handleMultiplierChange(
                            index,
                            condIdx,
                            parseFloat(e.target.value)
                          )
                        }
                        className="w-24"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          handleRemoveCondition(index, condIdx)
                        }
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Card>
      ))}

      {multipliers.length === 0 && (
        <p className="text-muted-foreground text-sm text-center py-4">
          No multipliers configured. Add one to apply conditional adjustments.
        </p>
      )}
    </div>
  );
}
```

**Testing Requirements**:
- [ ] Component renders correctly
- [ ] Add/remove multipliers works
- [ ] Field selection works
- [ ] Condition management works
- [ ] Form validation works
- [ ] Accessibility compliance

---

#### P3-FEAT-004: Integration Testing for Action Multipliers
**Priority**: Medium
**Time Estimate**: 6 hours
**Dependencies**: P3-FEAT-003

**Description**:
Comprehensive testing of the Action Multipliers system end-to-end.

**Acceptance Criteria**:
- [ ] E2E tests for creating rules with multipliers
- [ ] Verify multipliers apply correctly to valuations
- [ ] Test edge cases and error conditions
- [ ] Performance benchmarks

**Files to Create**:
- `/mnt/containers/deal-brain/tests/test_action_multipliers.py`
- `/mnt/containers/deal-brain/apps/web/tests/action-multipliers.spec.ts`

**Testing Requirements**:
- [ ] Test single multiplier
- [ ] Test multiple multipliers stacking
- [ ] Test with missing field values
- [ ] Test with invalid multiplier values
- [ ] Test UI interaction flow
- [ ] Test API integration

---

## Phase 4: Formula Builder (Weeks 5-7)

### Overview
Implement the advanced Formula Builder UI for creating and validating formula-based actions.

### Task List

#### P4-FEAT-001: Formula Parser Enhancement
**Priority**: High
**Time Estimate**: 8 hours
**Dependencies**: P1-BUG-003

**Description**:
Enhance the formula parser to support more operations and provide better error messages.

**Acceptance Criteria**:
- [ ] Support for all basic math operations
- [ ] Support for field references
- [ ] Support for functions (min, max, round)
- [ ] Detailed parse error messages
- [ ] AST visualization for debugging

**Files to Modify**:
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/formula.py`
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/formula_validator.py` (new)

**Implementation Notes**:
```python
# Enhanced FormulaParser
class FormulaParser:
    SUPPORTED_FUNCTIONS = {
        'min': min,
        'max': max,
        'round': round,
        'abs': abs,
        'floor': math.floor,
        'ceil': math.ceil
    }

    def parse(self, formula: str) -> FormulaAST:
        """Parse formula into AST with validation."""
        try:
            # Preprocess formula
            formula = self._preprocess(formula)

            # Parse to Python AST
            tree = ast.parse(formula, mode='eval')

            # Validate AST
            self._validate_ast(tree)

            # Convert to our AST format
            return self._convert_ast(tree)

        except SyntaxError as e:
            raise FormulaParseError(
                f"Syntax error at position {e.offset}: {e.msg}"
            )

    def _validate_ast(self, tree: ast.AST) -> None:
        """Validate AST for security and correctness."""
        for node in ast.walk(tree):
            # Disallow dangerous operations
            if isinstance(node, (ast.Import, ast.Call)):
                if isinstance(node, ast.Call):
                    if not self._is_safe_function(node):
                        raise FormulaValidationError(
                            f"Unsafe function call: {ast.unparse(node)}"
                        )

            # Validate field references
            if isinstance(node, ast.Name):
                if not self._is_valid_field(node.id):
                    raise FormulaValidationError(
                        f"Unknown field: {node.id}"
                    )
```

**Testing Requirements**:
- [ ] Test all supported operations
- [ ] Test error messages
- [ ] Test security restrictions
- [ ] Performance benchmarks

---

#### P4-FEAT-002: Formula Builder UI Component
**Priority**: High
**Time Estimate**: 16 hours
**Dependencies**: P4-FEAT-001

**Description**:
Build an intuitive UI for creating formulas with field selection, operation buttons, and live preview.

**Acceptance Criteria**:
- [ ] Visual formula builder interface
- [ ] Drag-and-drop field selection
- [ ] Operation palette (math, functions)
- [ ] Live syntax highlighting
- [ ] Real-time validation
- [ ] Preview with sample data
- [ ] Formula history/templates

**Files to Create**:
- `/mnt/containers/deal-brain/apps/web/components/valuation/formula-builder.tsx`
- `/mnt/containers/deal-brain/apps/web/components/valuation/formula-editor.tsx`
- `/mnt/containers/deal-brain/apps/web/lib/formula-utils.ts`

**Implementation Notes**:
```typescript
// FormulaBuilder component
interface FormulaBuilderProps {
  value: string;
  onChange: (formula: string) => void;
  availableFields: Field[];
  onValidate?: (formula: string) => Promise<ValidationResult>;
}

export function FormulaBuilder({
  value,
  onChange,
  availableFields,
  onValidate
}: FormulaBuilderProps) {
  const [formula, setFormula] = useState(value);
  const [validation, setValidation] = useState<ValidationResult>();
  const [preview, setPreview] = useState<number>();
  const [selectedField, setSelectedField] = useState<Field>();

  // Formula operations
  const operations = [
    { label: '+', value: ' + ', type: 'operator' },
    { label: '-', value: ' - ', type: 'operator' },
    { label: '×', value: ' * ', type: 'operator' },
    { label: '÷', value: ' / ', type: 'operator' },
    { label: '()', value: '()', type: 'group' },
    { label: 'min', value: 'min()', type: 'function' },
    { label: 'max', value: 'max()', type: 'function' },
    { label: 'round', value: 'round()', type: 'function' }
  ];

  const handleFieldInsert = (field: Field) => {
    const cursorPos = getCursorPosition();
    const newFormula = insertAtCursor(formula, field.name, cursorPos);
    setFormula(newFormula);
    validateFormula(newFormula);
  };

  const handleOperationInsert = (op: Operation) => {
    const cursorPos = getCursorPosition();
    const newFormula = insertAtCursor(formula, op.value, cursorPos);
    setFormula(newFormula);
    validateFormula(newFormula);
  };

  const validateFormula = useDebounce(async (formula: string) => {
    if (onValidate) {
      const result = await onValidate(formula);
      setValidation(result);

      if (result.valid) {
        setPreview(result.preview);
      }
    }
  }, 300);

  return (
    <div className="space-y-4">
      {/* Field Selector */}
      <div className="border rounded-lg p-3">
        <Label className="text-sm mb-2">Available Fields</Label>
        <div className="grid grid-cols-3 gap-2">
          {availableFields.map(field => (
            <Button
              key={field.name}
              variant="outline"
              size="sm"
              onClick={() => handleFieldInsert(field)}
              className="text-xs"
            >
              {field.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Operation Palette */}
      <div className="border rounded-lg p-3">
        <Label className="text-sm mb-2">Operations</Label>
        <div className="flex flex-wrap gap-2">
          {operations.map(op => (
            <Button
              key={op.value}
              variant="outline"
              size="sm"
              onClick={() => handleOperationInsert(op)}
              className={cn(
                "text-xs",
                op.type === 'operator' && "w-10",
                op.type === 'function' && "px-3"
              )}
            >
              {op.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Formula Editor */}
      <div className="space-y-2">
        <Label>Formula</Label>
        <div className="relative">
          <Textarea
            value={formula}
            onChange={(e) => {
              setFormula(e.target.value);
              validateFormula(e.target.value);
            }}
            placeholder="Enter formula or use the buttons above..."
            className={cn(
              "font-mono",
              validation?.valid === false && "border-red-500"
            )}
            rows={4}
          />
          {validation && !validation.valid && (
            <div className="absolute -bottom-6 left-0 text-xs text-red-500">
              {validation.error}
            </div>
          )}
        </div>
      </div>

      {/* Live Preview */}
      {preview !== undefined && (
        <Alert>
          <AlertDescription>
            <div className="flex items-center justify-between">
              <span className="text-sm">Preview with sample data:</span>
              <Badge variant="outline">${preview.toFixed(2)}</Badge>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Formula Templates */}
      <Collapsible>
        <CollapsibleTrigger className="text-sm text-muted-foreground">
          Formula templates ▼
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="space-y-2 mt-2">
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start"
              onClick={() => setFormula('cpu_mark_single * 0.05')}
            >
              CPU Performance: cpu_mark_single * 0.05
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start"
              onClick={() => setFormula('ram_gb * 2.5')}
            >
              RAM Value: ram_gb * 2.5
            </Button>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
```

**Testing Requirements**:
- [ ] Unit tests for formula builder
- [ ] Integration tests with backend
- [ ] Accessibility testing
- [ ] Performance with complex formulas
- [ ] Mobile responsiveness

---

#### P4-FEAT-003: Formula Validation API
**Priority**: Medium
**Time Estimate**: 6 hours
**Dependencies**: P4-FEAT-001

**Description**:
API endpoint for validating formulas and providing preview calculations.

**Acceptance Criteria**:
- [ ] Validate formula syntax
- [ ] Check field availability
- [ ] Calculate preview with sample data
- [ ] Return helpful error messages
- [ ] Performance optimized

**Files to Modify**:
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/endpoints/rules.py`
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/schemas/rules.py`

**Implementation Notes**:
```python
# API Endpoint
@router.post("/valuation-rules/validate-formula")
async def validate_formula(
    request: FormulaValidationRequest,
    session: AsyncSession = Depends(get_session)
) -> FormulaValidationResponse:
    """Validate a formula and provide preview."""

    try:
        # Parse formula
        parser = FormulaParser()
        ast = parser.parse(request.formula)

        # Get available fields
        fields = await get_available_fields(
            session,
            request.entity_type
        )

        # Validate field references
        validator = FormulaValidator(fields)
        validation_errors = validator.validate(ast)

        if validation_errors:
            return FormulaValidationResponse(
                valid=False,
                errors=validation_errors
            )

        # Calculate preview with sample data
        sample_context = await get_sample_context(
            session,
            request.entity_type
        )

        evaluator = FormulaEngine()
        preview_value = evaluator.evaluate(
            request.formula,
            sample_context
        )

        return FormulaValidationResponse(
            valid=True,
            preview=preview_value,
            used_fields=ast.get_field_references()
        )

    except Exception as e:
        return FormulaValidationResponse(
            valid=False,
            errors=[str(e)]
        )
```

**Testing Requirements**:
- [ ] Test valid formulas
- [ ] Test invalid formulas
- [ ] Test with missing fields
- [ ] Performance test
- [ ] Security test (injection attempts)

---

#### P4-FEAT-004: Formula Documentation and Help
**Priority**: Low
**Time Estimate**: 4 hours
**Dependencies**: P4-FEAT-002

**Description**:
Create comprehensive documentation and in-app help for the formula system.

**Acceptance Criteria**:
- [ ] Formula syntax guide
- [ ] Available functions reference
- [ ] Example formulas
- [ ] Interactive tutorial
- [ ] Tooltips in UI

**Files to Create**:
- `/mnt/containers/deal-brain/docs/user-guide/formula-builder.md`
- `/mnt/containers/deal-brain/apps/web/components/valuation/formula-help.tsx`

**Testing Requirements**:
- [ ] Documentation accuracy
- [ ] Help component renders
- [ ] Links work correctly

---

## Implementation Guidelines

### Code Style and Standards

#### Python Backend
- Use async/await for all database operations
- Follow PEP 8 with 100 character line limit
- Use type hints for all function signatures
- Add comprehensive docstrings
- Use logging instead of print statements

#### TypeScript Frontend
- Use functional components with hooks
- Implement proper error boundaries
- Use React Query for server state
- Follow accessibility guidelines (WCAG AA)
- Implement proper loading and error states

### Error Handling

#### Backend
```python
try:
    result = await operation()
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

#### Frontend
```typescript
const mutation = useMutation({
  mutationFn: createRule,
  onError: (error) => {
    console.error('Rule creation failed:', error);
    toast.error(
      error.response?.data?.detail ||
      'Failed to create rule. Please try again.'
    );
  }
});
```

---

## Git Strategy

### Branch Naming Convention
```
feature/P1-BUG-001-fix-rulegroup-modal
feature/P2-UX-001-scrollable-dropdown
feature/P3-FEAT-001-action-multipliers
feature/P4-FEAT-001-formula-builder
```

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>

Types: feat, fix, docs, style, refactor, test, chore
Scope: api, web, core, db

Example:
fix(web): correct modal opening for RuleGroup creation

- Fixed state management issue causing wrong modal to open
- Added validation to prevent multiple modals
- Updated event handlers

Fixes P1-BUG-001
```

### Pull Request Strategy

#### When to Create PRs
- One PR per task (P1-BUG-001, etc.)
- Create draft PR early for visibility
- Request review when acceptance criteria met

#### PR Checklist
```markdown
## Description
Brief description of changes

## Task Reference
Fixes P1-BUG-001

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] No console errors

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No commented-out code
- [ ] No console.log statements

## Screenshots
(if applicable)
```

---

## Testing Strategy

### Unit Testing

#### Backend (pytest)
```python
# tests/test_action_multipliers.py
import pytest
from dealbrain_core.rules.action_engine import ActionEngine

class TestActionMultipliers:
    @pytest.mark.asyncio
    async def test_single_multiplier(self):
        engine = ActionEngine()
        action = create_test_action_with_multiplier()
        context = {"ram_spec.ddr_generation": "ddr3"}

        result = engine.execute_action(action, context)
        assert result == expected_value

    @pytest.mark.parametrize("generation,expected", [
        ("ddr3", 0.7),
        ("ddr4", 1.0),
        ("ddr5", 1.3),
    ])
    async def test_generation_multipliers(self, generation, expected):
        # Test each generation
        pass
```

#### Frontend (Jest/React Testing Library)
```typescript
// tests/ActionMultipliers.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ActionMultipliers } from '@/components/valuation/action-multipliers';

describe('ActionMultipliers', () => {
  it('should add new multiplier when button clicked', () => {
    const onChange = jest.fn();
    render(
      <ActionMultipliers
        multipliers={[]}
        onChange={onChange}
        availableFields={mockFields}
      />
    );

    fireEvent.click(screen.getByText('Add Multiplier'));
    expect(onChange).toHaveBeenCalledWith([
      expect.objectContaining({
        name: 'New Multiplier',
        field: '',
        conditions: []
      })
    ]);
  });
});
```

### Integration Testing

#### API Integration Tests
```python
# tests/integration/test_rules_api.py
async def test_create_rule_with_multipliers(client, db_session):
    rule_data = {
        "name": "RAM Value",
        "actions": [{
            "action_type": "per_unit",
            "metric": "ram_gb",
            "value_usd": 2.5,
            "modifiers_json": {
                "multipliers": [{
                    "name": "Generation Multiplier",
                    "field": "ram_spec.ddr_generation",
                    "conditions": [
                        {"value": "ddr4", "multiplier": 1.0}
                    ]
                }]
            }
        }]
    }

    response = await client.post("/api/v1/valuation-rules", json=rule_data)
    assert response.status_code == 201
```

### E2E Testing (Playwright)

```typescript
// e2e/formula-builder.spec.ts
test('should create rule with formula action', async ({ page }) => {
  await page.goto('/valuation-rules');
  await page.click('text=Add Rule');

  // Select formula action type
  await page.selectOption('select[name="actionType"]', 'formula');

  // Use formula builder
  await page.click('text=cpu_mark_single');
  await page.click('text=×');
  await page.type('input[name="formula"]', '0.05');

  // Verify preview
  await expect(page.locator('.preview')).toContainText('$52.50');

  // Save rule
  await page.click('text=Create Rule');
  await expect(page.locator('.toast')).toContainText('Rule created');
});
```

### Manual Testing Checklists

#### Phase 1 - Bug Fixes
- [ ] RuleGroup modal opens correctly
- [ ] New RuleGroups appear in list
- [ ] Formula actions calculate correctly
- [ ] Baseline rules hydrate properly
- [ ] Foreign key rules hidden

#### Phase 2 - UX
- [ ] Dropdown scrolls smoothly
- [ ] Field search works
- [ ] Keyboard navigation works
- [ ] Value autocomplete works

#### Phase 3 - Multipliers
- [ ] Can add/remove multipliers
- [ ] Field selection works
- [ ] Conditions save correctly
- [ ] Multipliers apply to calculations

#### Phase 4 - Formula Builder
- [ ] Fields insert correctly
- [ ] Operations work
- [ ] Validation shows errors
- [ ] Preview updates live
- [ ] Templates work

---

## Rollout Plan

### Development Environment

#### Setup
```bash
# Create feature branch
git checkout -b feature/P1-BUG-001-fix-rulegroup-modal

# Install dependencies
make setup

# Run migrations
make migrate

# Start services
make up
```

#### Testing
```bash
# Run backend tests
poetry run pytest tests/test_rules.py -v

# Run frontend tests
cd apps/web && pnpm test

# Run E2E tests
cd apps/web && pnpm test:e2e
```

### Staging Deployment

#### Pre-deployment Checklist
- [ ] All tests passing
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Migration tested on staging data copy

#### Deployment Steps
1. Backup staging database
2. Deploy backend with migrations
3. Run migrations: `alembic upgrade head`
4. Deploy frontend
5. Clear caches
6. Smoke test critical paths

### Production Deployment

#### Pre-deployment
- [ ] Staging testing complete
- [ ] Performance benchmarks acceptable
- [ ] Rollback plan documented
- [ ] Maintenance window scheduled

#### Deployment Steps
1. **Backup** production database
2. **Feature flags** - Enable for staff only initially
3. **Deploy backend**
   ```bash
   kubectl set image deployment/api api=dealbrain-api:v2.1.0
   ```
4. **Run migrations**
   ```bash
   kubectl exec -it api-pod -- alembic upgrade head
   ```
5. **Deploy frontend**
   ```bash
   kubectl set image deployment/web web=dealbrain-web:v2.1.0
   ```
6. **Clear caches**
   ```bash
   kubectl exec -it redis-pod -- redis-cli FLUSHDB
   ```
7. **Health checks**
8. **Enable feature flags** for all users

#### Rollback Procedure
```bash
# Rollback deployments
kubectl rollout undo deployment/api
kubectl rollout undo deployment/web

# Rollback migrations if needed
kubectl exec -it api-pod -- alembic downgrade -1

# Restore database backup if critical
pg_restore -d dealbrain backup.sql
```

### Monitoring and Alerts

#### Key Metrics
- API response times
- Rule evaluation performance
- Error rates
- Database query times

#### Alert Thresholds
- API latency > 500ms
- Error rate > 1%
- Rule evaluation > 100ms
- Database connections > 80%

---

## Documentation Updates

### Architecture Documentation
- [ ] Update `/docs/architecture/valuation-rules.md` with:
  - Action Multipliers system
  - Formula Builder architecture
  - Performance optimizations

### API Documentation
- [ ] Update OpenAPI schema
- [ ] Document new endpoints
- [ ] Add example requests/responses

### User Guide
- [ ] Create Formula Builder guide
- [ ] Update Valuation Rules guide
- [ ] Add troubleshooting section

### CHANGELOG Entry
```markdown
## [2.1.0] - 2024-XX-XX

### Added
- Action Multipliers system for complex condition-to-action mappings
- Advanced Formula Builder UI for creating formula-based actions
- Field value autocomplete in condition builder
- Scrollable dropdown for long field lists

### Fixed
- RuleGroup modal opening incorrect modal when no groups exist
- New RuleGroups not appearing in list after creation
- Formula actions not evaluating correctly
- Baseline rules not hydrating with proper conditions/actions
- Foreign key rules visible in Advanced Mode

### Changed
- Improved formula parser with better error messages
- Enhanced field selector with virtual scrolling
- Optimized rule evaluation performance

### Technical
- Added multipliers_json support to ValuationRuleAction
- Implemented FormulaValidator for syntax checking
- Added React virtual scrolling for large lists
```

---

## Risk Management

### Technical Risks

#### Risk: Formula evaluation performance
**Mitigation**:
- Cache parsed formulas
- Limit formula complexity
- Add timeouts

#### Risk: Migration failures
**Mitigation**:
- Test on staging first
- Create rollback migrations
- Backup before deployment

#### Risk: UI complexity
**Mitigation**:
- Progressive disclosure
- Good defaults
- Comprehensive help

### Timeline Risks

#### Risk: Scope creep
**Mitigation**:
- Strict phase boundaries
- Feature flags for partial releases
- Regular stakeholder updates

#### Risk: Testing delays
**Mitigation**:
- Parallel test development
- Automated test suite
- Early QA involvement

---

## Success Metrics

### Technical Metrics
- [ ] All critical bugs fixed (Phase 1)
- [ ] Rule evaluation < 50ms average
- [ ] Formula validation < 200ms
- [ ] 90% test coverage

### Business Metrics
- [ ] User can create RAM multiplier rules
- [ ] Formula creation success rate > 80%
- [ ] Support tickets reduced by 30%
- [ ] Advanced Mode adoption > 50%

### Quality Metrics
- [ ] Zero critical bugs in production
- [ ] < 1% error rate
- [ ] Page load time < 2 seconds
- [ ] Accessibility score > 90

---

## Appendix

### Quick Reference Commands

```bash
# Development
make setup          # Install all dependencies
make api           # Start API server
make web           # Start web server
make test          # Run all tests
make lint          # Lint code
make format        # Format code

# Database
make migrate       # Run migrations
make rollback      # Rollback last migration
make seed          # Seed test data

# Docker
make up            # Start all services
make down          # Stop all services
make logs          # View logs
make shell-api     # Shell into API container

# Git
git status         # Check status
git add .          # Stage changes
git commit -m ""   # Commit
git push           # Push to remote
git pull --rebase  # Update from remote
```

### File Path Reference

```
Backend:
- Models: apps/api/dealbrain_api/models/core.py
- Services: apps/api/dealbrain_api/services/
- API: apps/api/dealbrain_api/api/endpoints/
- Core: packages/core/dealbrain_core/rules/
- Tests: tests/

Frontend:
- Pages: apps/web/app/
- Components: apps/web/components/
- Hooks: apps/web/hooks/
- Utils: apps/web/lib/
- Tests: apps/web/tests/
```

### Contact Information

- **Technical Lead**: [Name]
- **Product Owner**: [Name]
- **QA Lead**: [Name]
- **DevOps**: [Name]

---

This implementation plan provides a complete roadmap for fixing bugs and implementing enhancements to the Valuation Rules System. Each task is clearly defined with acceptance criteria, implementation notes, and testing requirements to ensure successful delivery.