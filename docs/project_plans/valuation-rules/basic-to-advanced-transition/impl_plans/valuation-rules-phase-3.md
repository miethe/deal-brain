# Phase 3: Action Multipliers System (Weeks 3-4)

## Implementation Plan

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
