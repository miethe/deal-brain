# Phase 1: Critical Bug Fixes (Week 1)

## Implementation Plan

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
