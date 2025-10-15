# Product Requirements Document: Valuation Rules System Enhancements

**Version:** 1.0
**Date:** 2025-10-15
**Status:** Ready for Implementation
**Owner:** Product & Engineering Teams

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statements](#problem-statements)
3. [User Stories & Acceptance Criteria](#user-stories--acceptance-criteria)
4. [Technical Requirements](#technical-requirements)
5. [Design Specifications](#design-specifications)
6. [Implementation Phases](#implementation-phases)
7. [Success Metrics](#success-metrics)
8. [Risk Assessment](#risk-assessment)
9. [Timeline & Estimates](#timeline--estimates)
10. [Appendices](#appendices)

---

## 1. Executive Summary

### 1.1 Overview

This PRD addresses critical bugs and proposes strategic enhancements to the Valuation Rules system in Deal Brain. The system currently enables users to define pricing adjustments for PC listings through a hierarchical rule structure (Ruleset → RuleGroup → Rule). However, several usability issues and missing features are preventing users from fully leveraging the Advanced mode functionality.

### 1.2 Scope

**Bugs to Fix:** 3 critical UI bugs, 2 data integrity issues
**Enhancements:** 2 major feature additions (Formula Builder UI, Action Multipliers)
**Affected Areas:** Frontend (React/Next.js), Backend (FastAPI/Python), Core Domain Logic

### 1.3 Business Impact

| Impact Area | Current State | Desired State |
|-------------|--------------|---------------|
| **User Productivity** | Users cannot manage RuleGroups effectively; require manual page refreshes | Seamless rule management with immediate feedback |
| **Rule Complexity** | Users can't create conditional multipliers (e.g., DDR3/4/5 adjustments) | Full conditional multiplier support with intuitive UI |
| **Formula Reliability** | Formula-type actions don't calculate valuations; users receive $0 adjustments | All formulas evaluate correctly with visual builder to prevent errors |
| **Data Accessibility** | Field dropdown extends beyond viewport; 30%+ of fields unreachable on small screens | All fields accessible via scrollable dropdown with visual indicators |
| **Rule Visibility** | Foreign key rules clutter Advanced view; user confusion about editable vs system rules | Clean Advanced view with only user-editable rules visible |

### 1.4 Priority Classification

| Priority | Items | Severity | User Impact |
|----------|-------|----------|-------------|
| **P0 - Critical** | Modal bugs (2), Formula evaluation bug | High | Blocks workflow, data integrity issues |
| **P1 - High** | Scrollable dropdown, Foreign key filtering | Medium | Usability degradation, user frustration |
| **P2 - Medium** | Action Multipliers system | Low | Feature gap, requires workarounds |
| **P3 - Low** | Formula Builder UI | Low | Nice-to-have, reduces errors over time |

### 1.5 Success Criteria

1. **All P0 bugs resolved** within 1 week (50% reduction in support tickets)
2. **Formula actions produce accurate valuations** for 100% of baseline rules
3. **Zero user complaints** about dropdown accessibility after Phase 2
4. **Action Multipliers feature** enables DDR generation pricing without creating separate rules
5. **Formula Builder** reduces formula syntax errors by 95%

---

## 2. Problem Statements

### 2.1 BUG-001: Wrong Modal Opens on "Add RuleGroup" (CRITICAL)

**Current Behavior:**
When a Ruleset has no existing RuleGroups, clicking the "Add RuleGroup" button in the empty state opens the RulesetBuilderModal instead of RuleGroupFormModal.

**Impact:**
- Users cannot create RuleGroups in new or empty Rulesets
- Confusing UX: button label says "Add Rule Group" but creates Ruleset
- Occurs immediately after creating new Ruleset (most common workflow)

**Root Cause:**
Copy-paste error in empty state button handler (`page.tsx` line 701): `setIsRulesetBuilderOpen(true)` instead of `setIsGroupFormOpen(true)`

**Expected Behavior:**
Clicking "Add Rule Group" should always open RuleGroupFormModal regardless of current RuleGroup count.

**Reference:** `/mnt/containers/deal-brain/docs/project_plans/bug-analysis-modal-issues.md`

---

### 2.2 BUG-002: New RuleGroup Not Appearing After Creation (CRITICAL)

**Current Behavior:**
After successfully creating a RuleGroup:
1. Success toast appears
2. Modal closes
3. New RuleGroup does NOT appear in list
4. User must manually click "Refresh" button to see it
5. Backend logs show successful creation (data integrity intact)

**Impact:**
- User confusion: appears creation failed
- Extra step required (manual refresh)
- Loss of confidence in system reliability
- Affects RuleGroups, Rulesets, and Rules (same pattern)

**Root Cause:**
React Query cache invalidation timing issue. Modal closes before refetch completes, causing UI to render with stale data.

**Expected Behavior:**
Newly created items appear immediately in list without manual refresh.

**Reference:** `/mnt/containers/deal-brain/docs/project_plans/bug-analysis-modal-issues.md`

---

### 2.3 BUG-003: Dropdown Extends Beyond Viewport (HIGH)

**Current Behavior:**
The EntityFieldSelector dropdown for selecting condition fields extends beyond the bottom of the viewport when the field list is long (20+ items). Users cannot scroll to see or select fields below the visible area.

**Impact:**
- 30-40% of fields unreachable on laptop screens (1080p)
- 50%+ unreachable on tablets/small screens
- Complete inability to select certain entity fields
- Keyboard navigation works but visual feedback missing

**Root Cause:**
Missing CommandList wrapper and max-height constraint on Command component. No overflow-y styling.

**Expected Behavior:**
Dropdown displays with scrollable area, max height adapts to viewport, visual scroll indicators present.

**Reference:** `/mnt/containers/deal-brain/docs/design/scrollable-dropdown-specification.md`

---

### 2.4 BUG-004: Formula-Type Actions Not Evaluating (CRITICAL)

**Current Behavior:**
Baseline rules with `action_type: "formula"` do not produce valuation adjustments. For example:
- CPU Mark (Single) rule: `"clamp((cpu_mark_single/100)*5.2, 0, 80)"`
- All listings with `cpu_mark_single` values receive $0.00 adjustment
- No errors logged in frontend or backend

**Impact:**
- Core valuation system non-functional for formula-based rules
- Users cannot leverage CPU benchmarks for pricing
- Manual workarounds required (fixed values instead of dynamic formulas)
- Loss of competitive advantage (accurate pricing)

**Root Cause:**
Multiple issues identified:
1. Formula syntax mismatch: Baseline uses `clamp()` but FormulaEngine doesn't support it
2. Key mapping issue: Baseline data uses `"Formula"` key, but hydration expects `"formula_text"`
3. Silent error handling: Failures not logged, return 0.0 by default
4. Missing context fields: Formula references fields not present in evaluation context

**Expected Behavior:**
Formula actions evaluate correctly, producing accurate adjustments based on listing attributes.

**Reference:** `/mnt/containers/deal-brain/docs/project_plans/requests/formula-action-bug-analysis.md`

---

### 2.5 BUG-005: Foreign Key Rules Visible in Advanced Mode (MEDIUM)

**Current Behavior:**
RAM Spec and Primary Storage Profile rules appear in Advanced Mode rule list. These are system-managed foreign key references that cannot be edited.

**Impact:**
- UI clutter with non-editable rules
- User confusion: "Why can't I edit this rule?"
- Poor information architecture
- Increases cognitive load

**Expected Behavior:**
Foreign key rules filtered out of Advanced Mode view by default (optional "Show System Rules" toggle for debugging).

---

### 2.6 FEATURE-001: Missing Action Multipliers System (MEDIUM)

**Current Behavior:**
Users cannot apply conditional multipliers within a single Rule's Action. For example, to price RAM differently based on DDR generation:
- Current solution: Create 3 separate Rules (DDR3, DDR4, DDR5), each with own condition
- Results in rule proliferation (3x rules for simple multiplier)

**Impact:**
- Poor scalability: 3 conditions = 3 rules, 5 conditions = 5 rules
- Harder to maintain: Editing base value requires updating 3+ rules
- Mental model mismatch: "I want to adjust RAM pricing by DDR type" → requires creating multiple rules

**User Need:**
Ability to define Action-level condition multipliers:
```
Action: RAM Per GB = $2.50/GB
  Multipliers:
    - If DDR3 → 0.7x
    - If DDR4 → 1.0x
    - If DDR5 → 1.3x
```

**Expected Behavior:**
Single Rule with one Action can have multiple conditional multipliers, each with its own field condition and multiplier value.

**Reference:** `/mnt/containers/deal-brain/docs/project_plans/requests/10-15-bugs.md` (lines 33-42)

---

### 2.7 FEATURE-002: No Visual Formula Builder (LOW)

**Current Behavior:**
Users must manually type formula strings:
- `"clamp((cpu_mark_single/100)*5.2, 0, 80)"`
- Syntax errors cause silent failures
- No validation until evaluation
- No field autocomplete
- No function reference

**Impact:**
- High error rate (estimated 30-40% of formulas have syntax issues)
- Time-consuming debugging
- Steep learning curve for non-technical users
- Hesitance to use formula actions (falling back to fixed values)

**User Need:**
Visual formula builder with:
- Field dropdown selector
- Operator palette (+, -, *, /, min, max, clamp)
- Real-time validation
- Sample evaluation preview
- Syntax highlighting

**Expected Behavior:**
Formula builder UI generates valid formula strings, reduces errors, enables non-technical users to create complex formulas.

**Reference:** `/mnt/containers/deal-brain/docs/project_plans/requests/formula-action-bug-analysis.md` (Phase 3)

---

## 3. User Stories & Acceptance Criteria

### 3.1 BUG-001: Wrong Modal Opens

**User Story:**
> As a valuation manager, when I create a new Ruleset and click "Add Rule Group" in the empty state, I expect the RuleGroup creation modal to open so I can immediately start building my rule structure.

**Acceptance Criteria:**
- [ ] Clicking "Add Rule Group" in empty state opens RuleGroupFormModal
- [ ] Clicking "Add Rule Group" in populated state opens RuleGroupFormModal
- [ ] Button label matches actual behavior ("Add Rule Group" → RuleGroupFormModal)
- [ ] No regression: "New Ruleset" button still opens RulesetBuilderModal

**Definition of Done:**
- Code change deployed to production
- Tested with new Ruleset creation flow
- Tested with all RuleGroups deleted scenario
- No reported issues for 1 week post-deployment

---

### 3.2 BUG-002: New RuleGroup Not Appearing

**User Story:**
> As a valuation manager, when I create a new RuleGroup, I expect to see it immediately in the list without needing to manually refresh, so I can continue building my rules without interruption.

**Acceptance Criteria:**
- [ ] New RuleGroup appears in list within 500ms of creation
- [ ] New Ruleset appears in dropdown immediately
- [ ] New Rule appears in group immediately
- [ ] No flash of stale data (loading state during refetch)
- [ ] Works with slow network (3G simulation)
- [ ] Works when creating multiple items in rapid succession

**Definition of Done:**
- Fix applied to RuleGroupFormModal, RulesetBuilderModal, RuleBuilderModal
- Tested with network throttling (Slow 3G)
- Tested with rapid creation (3 items in 5 seconds)
- User acceptance testing confirms improvement

---

### 3.3 BUG-003: Dropdown Extends Beyond Viewport

**User Story:**
> As a rule builder, when I open the field selector dropdown, I expect to see all available fields with a scrollable list, so I can access any field regardless of my screen size.

**Acceptance Criteria:**
- [ ] Dropdown has maximum height that fits viewport
- [ ] Scroll indicators (shadows) appear when content overflows
- [ ] Scrollbar is visible and styled consistently
- [ ] Works on desktop (1080p, 1440p, 4K)
- [ ] Works on tablet (768px, 1024px)
- [ ] Works on mobile (375px, 414px)
- [ ] Keyboard navigation scrolls focused item into view
- [ ] Screen reader announces scrollable region

**Definition of Done:**
- CommandList wrapper added with max-height
- Scroll shadows implemented
- Tested on 5+ screen sizes
- WCAG AA accessibility audit passed
- No user complaints for 2 weeks post-deployment

---

### 3.4 BUG-004: Formula-Type Actions Not Evaluating

**User Story:**
> As a valuation manager, when I define a formula-based rule like CPU benchmark pricing, I expect the formula to calculate accurate adjustments for all listings, so I can leverage dynamic pricing strategies.

**Acceptance Criteria:**
- [ ] All baseline formula rules produce non-zero adjustments
- [ ] `clamp()` function supported in FormulaEngine
- [ ] Formula syntax translation works (baseline → Python AST)
- [ ] Errors logged with detailed messages (formula, context, error)
- [ ] Hydration process maps baseline keys correctly
- [ ] 100% of listings receive correct formula-based adjustments
- [ ] Performance: formula evaluation <50ms per listing

**Definition of Done:**
- Formula translation function implemented
- `clamp()` added to ALLOWED_FUNCTIONS
- Enhanced error logging deployed
- Baseline hydration key mapping fixed
- All baseline rules produce expected valuations
- Integration tests cover formula evaluation flow

---

### 3.5 BUG-005: Foreign Key Rules Visible

**User Story:**
> As a rule builder in Advanced Mode, I only want to see rules I can edit, so I can focus on configuring my valuation logic without being distracted by system-managed rules.

**Acceptance Criteria:**
- [ ] RAM Spec rules hidden by default in Advanced Mode
- [ ] Primary Storage Profile rules hidden by default
- [ ] Optional "Show System Rules" toggle available (view-only)
- [ ] System rules indicated with badge/icon (if shown)
- [ ] Rule count reflects only user-editable rules

**Definition of Done:**
- Frontend filter applied to rules list
- Metadata flag `is_foreign_key_rule` checked
- Toggle implementation (optional, can defer to Phase 4)
- User acceptance testing confirms cleaner UI

---

### 3.6 FEATURE-001: Action Multipliers System

**User Story:**
> As a valuation manager, when defining a RAM pricing rule, I want to apply different multipliers based on DDR generation (DDR3: 0.7x, DDR4: 1.0x, DDR5: 1.3x) within a single Action, so I can manage related adjustments in one place.

**Acceptance Criteria:**
- [ ] Action form has "Add Multiplier" button
- [ ] Each multiplier has custom name field
- [ ] Each multiplier can select condition field from dropdown
- [ ] Each multiplier can select multiple values for that field
- [ ] Each value has associated multiplier input (0.5 → 2.0 range)
- [ ] Multipliers apply during rule evaluation
- [ ] Breakdown shows which multiplier was applied
- [ ] Works with enum fields (DDR generation, condition, etc.)
- [ ] Works with numeric fields (year ranges, capacity buckets)

**Definition of Done:**
- Backend: `modifiers_json` schema extended with multipliers
- Backend: ActionEngine evaluates multipliers during execution
- Frontend: ActionBuilder UI supports multiplier configuration
- Frontend: Uses EntityFieldSelector for field selection
- Integration tests cover multiplier evaluation
- Documentation updated with examples

---

### 3.7 FEATURE-002: Visual Formula Builder

**User Story:**
> As a rule builder, when creating a formula action, I want a visual builder with field dropdowns, operator buttons, and real-time validation, so I can create complex formulas without syntax errors.

**Acceptance Criteria:**
- [ ] Field selector dropdown shows available fields
- [ ] Operator palette provides +, -, *, /, (, ), min, max, clamp, round
- [ ] Function reference modal with examples
- [ ] Real-time validation with error highlighting
- [ ] Sample data input panel for testing
- [ ] Preview pane shows formula result with sample data
- [ ] Generated formula is valid Python AST
- [ ] Can switch between Builder and Text modes
- [ ] Formula auto-formats on mode switch

**Definition of Done:**
- FormulaBuilder React component implemented
- Backend validation API endpoint created
- Formula parser validates syntax
- Field autocomplete integrated
- Sample evaluation tested with real listing data
- User testing confirms 95% reduction in syntax errors

---

## 4. Technical Requirements

### 4.1 Bug Fixes

#### 4.1.1 BUG-001: Wrong Modal Opens

**File:** `/mnt/containers/deal-brain/apps/web/app/valuation-rules/page.tsx`

**Change:**
```tsx
// Line 701 - Change from:
onClick={() => setIsRulesetBuilderOpen(true)}

// To:
onClick={() => {
  setEditingGroup(null);
  setIsGroupFormOpen(true);
}}
```

**Testing:**
- Unit test: Verify button click sets correct state
- E2E test: Create new Ruleset → Click "Add Rule Group" → Verify RuleGroupFormModal opens

---

#### 4.1.2 BUG-002: New RuleGroup Not Appearing

**Files:**
1. `/mnt/containers/deal-brain/apps/web/components/valuation/rule-group-form-modal.tsx` (lines 104-115)
2. `/mnt/containers/deal-brain/apps/web/components/valuation/ruleset-builder-modal.tsx` (lines 48-55)
3. `/mnt/containers/deal-brain/apps/web/components/valuation/rule-builder-modal.tsx` (lines 80-94)

**Change Pattern:**
```tsx
// Before:
onSuccess: () => {
  toast({ ... });
  resetForm();
  onOpenChange(false);
  queryClient.invalidateQueries({ ... });
  onSuccess();
}

// After:
onSuccess: async () => {
  toast({ ... });

  // Wait for cache invalidation to complete
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["ruleset", rulesetId] }),
    queryClient.invalidateQueries({ queryKey: ["rulesets"] }),
  ]);

  onSuccess();

  // Close modal AFTER refetch completes
  resetForm();
  onOpenChange(false);
}
```

**Testing:**
- Integration test: Create item → Verify appears in list without refresh
- Network throttle test: Slow 3G → Verify still works
- Rapid creation test: Create 3 items quickly → Verify all appear

---

#### 4.1.3 BUG-003: Dropdown Extends Beyond Viewport

**File:** `/mnt/containers/deal-brain/apps/web/components/valuation/entity-field-selector.tsx`

**Changes:**
1. Wrap Command contents in CommandList
2. Add max-height responsive classes
3. Add scroll shadow indicators
4. Style scrollbar

**Implementation:** See full code in `/mnt/containers/deal-brain/docs/design/scrollable-dropdown-specification.md` (lines 472-671)

**Key Classes:**
```tsx
<CommandList className={cn(
  "max-h-[min(400px,calc(100vh-200px))]",
  "sm:max-h-[min(360px,calc(100vh-180px))]",
  "max-sm:max-h-[60vh]",
  "overflow-y-auto overflow-x-hidden scroll-smooth",
  "[&::-webkit-scrollbar]:w-2",
  "[&::-webkit-scrollbar-track]:bg-gray-100",
  "[&::-webkit-scrollbar-thumb]:bg-gray-300",
  // ... dark mode variants
)}>
```

**Testing:**
- Visual test: Verify scrollbar appears on long lists
- Responsive test: Test on 320px, 768px, 1080px, 1440px widths
- Keyboard test: Arrow keys scroll focused item into view
- Screen reader test: Verify ARIA attributes present

---

#### 4.1.4 BUG-004: Formula-Type Actions Not Evaluating

**Backend Changes:**

**File 1:** `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/formula.py`

Add `clamp` to ALLOWED_FUNCTIONS:
```python
ALLOWED_FUNCTIONS = {
    # ... existing functions
    "clamp": lambda value, min_val, max_val: min(max(value, min_val), max_val),
}
```

**File 2:** `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/baseline_hydration.py`

Add formula syntax translation method:
```python
def _translate_formula_syntax(self, formula_text: str) -> str:
    """Translate human-readable formula to Python AST-compatible syntax."""
    translations = {
        "usd ≈ ": "",
        " with cohort guardrails": "",
    }

    result = formula_text
    for old, new in translations.items():
        result = result.replace(old, new)

    return result.strip()
```

Update `_hydrate_formula` to check multiple metadata keys:
```python
formula_text = (
    rule.metadata_json.get("formula_text") or
    rule.metadata_json.get("Formula") or
    rule.metadata_json.get("formula")
)

if formula_text:
    translated_formula = self._translate_formula_syntax(formula_text)
    logger.info(f"Translated formula for {rule.name}: '{formula_text}' -> '{translated_formula}'")
```

**File 3:** Enhanced error logging in formula evaluation

**Testing:**
- Unit test: Verify `clamp(10, 0, 5)` returns 5
- Integration test: Hydrate baseline CPU Mark rule → Verify produces adjustments
- End-to-end test: Create listing with cpu_mark_single=2500 → Verify adjustment applied
- Performance test: 100 listings with formula evaluation <5s total

---

#### 4.1.5 BUG-005: Foreign Key Rules Visible

**File:** `/mnt/containers/deal-brain/apps/web/app/valuation-rules/page.tsx`

**Change:**
```tsx
// Filter rules before display
const visibleRules = useMemo(() => {
  return rules.filter(rule => !rule.metadata_json?.is_foreign_key_rule);
}, [rules]);
```

**Backend (metadata addition):**
```python
# In baseline_hydration.py, mark foreign key rules:
if field_type == "foreign_key":
    rule.metadata_json["is_foreign_key_rule"] = True
```

**Testing:**
- Verify RAM Spec rules not visible in Advanced Mode
- Verify rule count excludes foreign key rules
- Verify toggle (if implemented) shows/hides correctly

---

### 4.2 Feature Enhancements

#### 4.2.1 FEATURE-001: Action Multipliers System

**Backend Schema Extension:**

**File:** `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/actions.py`

```python
@dataclass
class ConditionMultiplier:
    """Multiplier applied based on a condition."""
    name: str  # e.g., "DDR Generation Multiplier"
    field_name: str  # e.g., "ram_spec.ddr_generation"
    value: Any  # e.g., "ddr4"
    multiplier: float  # e.g., 1.0

@dataclass
class Action:
    # ... existing fields
    condition_multipliers: list[ConditionMultiplier] = field(default_factory=list)

    def calculate(self, context: dict[str, Any]) -> float:
        base_value = self._calculate_base_value(context)

        # Apply condition multipliers
        multiplier = 1.0
        for cm in self.condition_multipliers:
            if context.get(cm.field_name) == cm.value:
                multiplier *= cm.multiplier
                break  # Only apply first matching multiplier

        return base_value * multiplier
```

**Database Schema:**

Add to `ValuationRuleAction.modifiers_json`:
```json
{
  "condition_multipliers": [
    {
      "name": "DDR Generation Multiplier",
      "field_name": "ram_spec.ddr_generation",
      "value": "ddr3",
      "multiplier": 0.7
    },
    {
      "name": "DDR Generation Multiplier",
      "field_name": "ram_spec.ddr_generation",
      "value": "ddr4",
      "multiplier": 1.0
    },
    {
      "name": "DDR Generation Multiplier",
      "field_name": "ram_spec.ddr_generation",
      "value": "ddr5",
      "multiplier": 1.3
    }
  ]
}
```

**Frontend Component:**

**File:** `/mnt/containers/deal-brain/apps/web/components/valuation/action-builder.tsx`

New section in ActionBuilder:
```tsx
<div className="space-y-2">
  <Label>Conditional Multipliers</Label>
  <p className="text-sm text-muted-foreground">
    Apply different multipliers based on listing attributes
  </p>

  {conditionMultipliers.map((cm, index) => (
    <div key={index} className="border rounded-lg p-4 space-y-2">
      <div className="flex items-center justify-between">
        <Input
          placeholder="Multiplier Name"
          value={cm.name}
          onChange={(e) => updateMultiplier(index, 'name', e.target.value)}
        />
        <Button
          variant="ghost"
          size="sm"
          onClick={() => removeMultiplier(index)}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <EntityFieldSelector
        value={cm.field_name}
        onChange={(field) => updateMultiplier(index, 'field_name', field)}
        placeholder="Select field..."
      />

      <div className="flex items-center gap-2">
        <Select
          value={cm.value}
          onValueChange={(value) => updateMultiplier(index, 'value', value)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select value..." />
          </SelectTrigger>
          <SelectContent>
            {getFieldOptions(cm.field_name).map(opt => (
              <SelectItem key={opt} value={opt}>{opt}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <span className="text-sm text-muted-foreground">→</span>

        <Input
          type="number"
          step="0.1"
          min="0"
          max="5"
          value={cm.multiplier}
          onChange={(e) => updateMultiplier(index, 'multiplier', parseFloat(e.target.value))}
          className="w-24"
        />
        <span className="text-sm text-muted-foreground">×</span>
      </div>
    </div>
  ))}

  <Button
    variant="outline"
    size="sm"
    onClick={addMultiplier}
  >
    <Plus className="mr-2 h-4 w-4" />
    Add Multiplier
  </Button>
</div>
```

**Testing:**
- Unit test: Verify multiplier calculation logic
- Integration test: Create rule with multipliers → Evaluate against listings
- UI test: Add/remove multipliers in form
- E2E test: DDR generation multipliers produce correct adjustments

---

#### 4.2.2 FEATURE-002: Visual Formula Builder

**Backend API:**

**File:** `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/valuation_rules.py`

```python
@router.post("/valuation/rules/validate-formula")
async def validate_formula(
    formula: str,
    entity_type: str = "Listing",
    sample_context: dict[str, Any] | None = None,
) -> dict:
    """
    Validate formula syntax and evaluate with sample data.

    Returns:
        - is_valid: bool
        - errors: list[str]
        - translated_formula: str
        - sample_result: float | None
        - available_fields: list[str]
    """
    engine = FormulaEngine()

    # Get available fields for autocomplete
    metadata = await get_entity_metadata(entity_type)
    available_fields = [f"{e.key}.{f.key}" for e in metadata.entities for f in e.fields]

    try:
        # Validate syntax
        tree = engine.parser.parse(formula)

        # Evaluate with sample context if provided
        sample_result = None
        if sample_context:
            sample_result = engine.evaluate(formula, sample_context)

        return {
            "is_valid": True,
            "errors": [],
            "translated_formula": formula,
            "sample_result": sample_result,
            "available_fields": available_fields,
        }
    except ValueError as e:
        return {
            "is_valid": False,
            "errors": [str(e)],
            "translated_formula": None,
            "sample_result": None,
            "available_fields": available_fields,
        }
```

**Frontend Component:**

**File:** `/mnt/containers/deal-brain/apps/web/components/valuation/formula-builder.tsx`

```tsx
export function FormulaBuilder({ value, onChange, entityType }: FormulaBuilderProps) {
  const [mode, setMode] = useState<'visual' | 'text'>('visual');
  const [elements, setElements] = useState<FormulaElement[]>([]);
  const [sampleData, setSampleData] = useState<Record<string, any>>({});

  const { data: validation, isLoading } = useQuery({
    queryKey: ['validate-formula', value, sampleData],
    queryFn: () => validateFormula(value, entityType, sampleData),
    enabled: !!value,
  });

  return (
    <div className="space-y-4 border rounded-lg p-4">
      <div className="flex items-center justify-between">
        <Label>Formula Builder</Label>
        <Toggle
          pressed={mode === 'visual'}
          onPressedChange={(pressed) => setMode(pressed ? 'visual' : 'text')}
        >
          {mode === 'visual' ? 'Visual' : 'Text'}
        </Toggle>
      </div>

      {mode === 'visual' ? (
        <div className="space-y-4">
          {/* Field Selector */}
          <div>
            <Label>Add Field</Label>
            <EntityFieldSelector
              value={null}
              onChange={(field) => addElement({ type: 'field', value: field })}
              placeholder="Select field to add..."
            />
          </div>

          {/* Operator Palette */}
          <div>
            <Label>Operators</Label>
            <div className="flex gap-2 flex-wrap">
              {['+', '-', '*', '/', '(', ')'].map(op => (
                <Button
                  key={op}
                  variant="outline"
                  size="sm"
                  onClick={() => addElement({ type: 'operator', value: op })}
                >
                  {op}
                </Button>
              ))}
            </div>
          </div>

          {/* Function Palette */}
          <div>
            <Label>Functions</Label>
            <div className="flex gap-2 flex-wrap">
              {['min', 'max', 'clamp', 'round', 'sqrt'].map(fn => (
                <Button
                  key={fn}
                  variant="outline"
                  size="sm"
                  onClick={() => addElement({ type: 'function', value: fn })}
                >
                  {fn}()
                </Button>
              ))}
            </div>
          </div>

          {/* Formula Display */}
          <div>
            <Label>Formula</Label>
            <div className="font-mono text-sm bg-muted p-2 rounded min-h-[60px]">
              {elements.map((el, idx) => (
                <span
                  key={idx}
                  className={cn(
                    "inline-flex items-center gap-1 m-1 px-2 py-1 rounded",
                    el.type === 'field' && "bg-blue-100 text-blue-800",
                    el.type === 'operator' && "bg-gray-100",
                    el.type === 'function' && "bg-green-100 text-green-800"
                  )}
                >
                  {el.value}
                  <button onClick={() => removeElement(idx)}>×</button>
                </span>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Enter formula (e.g., cpu_mark_single * 0.05)"
          className="font-mono"
          rows={4}
        />
      )}

      {/* Validation Feedback */}
      {validation && !validation.is_valid && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Formula Error</AlertTitle>
          <AlertDescription>
            {validation.errors.join(', ')}
          </AlertDescription>
        </Alert>
      )}

      {/* Sample Evaluation */}
      <div className="border-t pt-4">
        <Label>Test with Sample Data</Label>
        <div className="space-y-2 mt-2">
          <Input
            placeholder="cpu_mark_single"
            type="number"
            onChange={(e) => setSampleData({ ...sampleData, cpu_mark_single: parseFloat(e.target.value) })}
          />
          {validation?.sample_result !== null && (
            <div className="text-sm">
              <span className="font-medium">Result:</span>{' '}
              <span className="font-mono">${validation.sample_result.toFixed(2)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Function Reference */}
      <Button variant="ghost" size="sm" onClick={() => setShowReference(true)}>
        <BookOpen className="mr-2 h-4 w-4" />
        Function Reference
      </Button>
    </div>
  );
}
```

**Testing:**
- Unit test: Verify formula generation from elements
- Integration test: Validate formula via API
- UI test: Add/remove elements, switch modes
- E2E test: Build formula → Save rule → Verify evaluation

---

## 5. Design Specifications

### 5.1 Modal Bug Fixes

**Design Reference:** `/mnt/containers/deal-brain/docs/project_plans/bug-analysis-modal-issues.md`

**Key Design Principles:**
1. Button labels must match behavior
2. Modal closure only after data refresh completes
3. Loading indicators during save operations
4. Success feedback with specific messaging

**Visual Design:**
- No changes to modal appearance
- Enhanced loading state: "Creating..." with spinner
- Success toast persists for 3s with specific message

---

### 5.2 Scrollable Dropdown

**Design Reference:** `/mnt/containers/deal-brain/docs/design/scrollable-dropdown-specification.md`

**Key Design Elements:**

1. **Scrollable Area:**
   - Max height: 400px desktop, 360px tablet, 60vh mobile
   - Smooth scrolling behavior
   - Custom styled scrollbar (8px width, rounded)

2. **Scroll Indicators:**
   - Gradient shadows at top/bottom (16px height)
   - Fade in/out based on scroll position
   - Transition: 200ms opacity

3. **Accessibility:**
   - ARIA attributes preserved (cmdk built-in)
   - Keyboard navigation with auto-scroll to focused item
   - Screen reader announces scrollable region
   - WCAG AA color contrast maintained

4. **Responsive Behavior:**
   - Desktop: Full 400px height available
   - Tablet: 360px max or viewport - 180px
   - Mobile: 60% of viewport height

**Visual Hierarchy:**
```
┌─────────────────────────────┐
│ Search Input                │ ← Fixed header
├─────────────────────────────┤
│ [Top Shadow] ▁▁▁▁▁▁▁▁▁▁▁▁▁ │ ← Fade gradient
│                             │
│ ▪ Entity 1                  │
│   → Field 1                 │ ← Scrollable
│   → Field 2                 │    content
│ ▪ Entity 2                  │
│   → Field 3                 │
│                             │
│ [Bottom Shadow] ▔▔▔▔▔▔▔▔▔▔ │ ← Fade gradient
└─────────────────────────────┘
```

---

### 5.3 Action Multipliers UI

**Component Structure:**
```
Action Builder
├─ Action Type Selector
├─ Base Value Input
└─ Conditional Multipliers Section
    ├─ Multiplier 1
    │   ├─ Name Input
    │   ├─ Field Selector (dropdown)
    │   ├─ Value Selector (dropdown)
    │   └─ Multiplier Input (0.1 - 5.0)
    ├─ Multiplier 2
    └─ [Add Multiplier Button]
```

**Visual Design:**
- Each multiplier in bordered card (rounded-lg, p-4)
- Remove button (X icon, top-right)
- Inline layout: Field → Value → Multiplier
- Visual equation: "DDR3 → 0.7×"
- Add button: outline style, plus icon

**Example UI:**
```
┌─────────────────────────────────────────────────┐
│ Base Value: $2.50 per GB                        │
├─────────────────────────────────────────────────┤
│ Conditional Multipliers                         │
│                                                  │
│ ┌──────────────────────────────────────────┐   │
│ │ DDR Generation Multiplier             [×]│   │
│ │ ┌────────────────┐ ┌────────┐ ┌──────┐  │   │
│ │ │ DDR Generation │ │  DDR3  │ │ 0.7× │  │   │
│ │ └────────────────┘ └────────┘ └──────┘  │   │
│ └──────────────────────────────────────────┘   │
│                                                  │
│ ┌──────────────────────────────────────────┐   │
│ │ DDR Generation Multiplier             [×]│   │
│ │ ┌────────────────┐ ┌────────┐ ┌──────┐  │   │
│ │ │ DDR Generation │ │  DDR4  │ │ 1.0× │  │   │
│ │ └────────────────┘ └────────┘ └──────┘  │   │
│ └──────────────────────────────────────────┘   │
│                                                  │
│ [+ Add Multiplier]                              │
└─────────────────────────────────────────────────┘
```

---

### 5.4 Formula Builder UI

**Layout:** Vertical stack in Rule Builder modal

**Sections:**
1. **Mode Toggle** (Visual / Text)
2. **Builder Tools** (Visual mode only)
   - Field selector dropdown
   - Operator palette (6 buttons)
   - Function palette (5 buttons)
3. **Formula Display**
   - Visual mode: Token-based display with pills
   - Text mode: Monospace textarea
4. **Validation Feedback**
   - Error alert (red)
   - Success indicator (green check)
5. **Test Panel**
   - Sample data inputs
   - Result preview

**Visual Design:**
- Token pills: Colored by type (blue=field, gray=operator, green=function)
- Remove button on each token (small X)
- Syntax highlighting in text mode
- Real-time validation indicator (check/X icon)

**Example UI (Visual Mode):**
```
┌─────────────────────────────────────────────────┐
│ Formula Builder               [Visual][Text]    │
├─────────────────────────────────────────────────┤
│ Add Field: [Select field...                  ▼]│
│                                                  │
│ Operators: [+] [-] [×] [÷] [(] [)]             │
│ Functions: [min] [max] [clamp] [round] [sqrt]  │
│                                                  │
│ Formula:                                         │
│ ┌──────────────────────────────────────────┐   │
│ │ ┌──────────┐ ┌───┐ ┌──────┐ ┌───┐      │   │
│ │ │cpu_mark  │×│0.05│+│ 10.0 │×│...│      │   │
│ │ │_single [×]│ │[×]│ │  [×] │ │[×]│      │   │
│ │ └──────────┘ └───┘ └──────┘ └───┘      │   │
│ └──────────────────────────────────────────┘   │
│                                                  │
│ ✓ Valid formula                                 │
│                                                  │
│ Test with Sample Data:                          │
│ cpu_mark_single: [2500          ]               │
│ Result: $135.00                                 │
│                                                  │
│ [📖 Function Reference]                         │
└─────────────────────────────────────────────────┘
```

---

## 6. Implementation Phases

### Phase 1: Critical Bug Fixes (Week 1)

**Duration:** 5 business days
**Priority:** P0
**Team:** 1 Frontend Engineer, 1 Backend Engineer

**Deliverables:**
- BUG-001: Wrong modal opens (2 hours)
- BUG-002: New items not appearing (4 hours)
- BUG-004: Formula evaluation fix (16 hours)
  - Add clamp function (1 hour)
  - Formula translation (4 hours)
  - Enhanced logging (2 hours)
  - Key mapping fix (2 hours)
  - Testing (7 hours)

**Testing Requirements:**
- Unit tests: Formula parsing, multiplier calculations
- Integration tests: End-to-end rule evaluation
- Manual QA: Modal workflows, formula validation
- Performance test: 100 listings with formula evaluation

**Release:**
- Deploy to staging: Day 3
- User acceptance testing: Day 4
- Production deployment: Day 5
- Monitoring: 1 week post-deployment

---

### Phase 2: UX Improvements (Week 2)

**Duration:** 5 business days
**Priority:** P1
**Team:** 1 Frontend Engineer

**Deliverables:**
- BUG-003: Scrollable dropdown (8 hours)
  - CommandList wrapper (2 hours)
  - Scroll shadows (3 hours)
  - Scrollbar styling (1 hour)
  - Testing (2 hours)
- BUG-005: Foreign key filtering (4 hours)
  - Metadata flags (1 hour)
  - Frontend filter (2 hours)
  - Testing (1 hour)

**Testing Requirements:**
- Responsive testing: 5+ screen sizes
- Accessibility audit: WCAG AA compliance
- Keyboard navigation testing
- Screen reader testing (NVDA/JAWS)

**Release:**
- Deploy to staging: Day 3
- Accessibility review: Day 4
- Production deployment: Day 5

---

### Phase 3: Action Multipliers (Weeks 3-4)

**Duration:** 10 business days
**Priority:** P2
**Team:** 1 Full-Stack Engineer

**Deliverables:**
- Backend schema extension (8 hours)
  - ConditionMultiplier dataclass (2 hours)
  - Action.calculate() update (3 hours)
  - Database migration (1 hour)
  - Unit tests (2 hours)
- Frontend UI implementation (16 hours)
  - ActionBuilder multipliers section (6 hours)
  - Field selector integration (2 hours)
  - Value dropdown logic (4 hours)
  - Form state management (2 hours)
  - UI tests (2 hours)
- Integration & testing (8 hours)
  - End-to-end evaluation tests (4 hours)
  - Manual QA (2 hours)
  - Documentation (2 hours)

**Testing Requirements:**
- Unit tests: Multiplier calculation logic
- Integration tests: Rule evaluation with multipliers
- UI tests: Add/remove multipliers
- E2E tests: DDR generation pricing scenario

**Release:**
- Deploy to staging: Day 8
- Beta testing with 3 users: Days 9-10
- Production deployment: End of Week 4
- Documentation published: End of Week 4

---

### Phase 4: Formula Builder UI (Weeks 5-7)

**Duration:** 15 business days
**Priority:** P3
**Team:** 1 Full-Stack Engineer

**Deliverables:**
- Backend validation API (6 hours)
  - Validation endpoint (3 hours)
  - Sample evaluation (2 hours)
  - Tests (1 hour)
- Frontend FormulaBuilder component (24 hours)
  - Visual mode UI (8 hours)
  - Text mode integration (2 hours)
  - Token management (4 hours)
  - Field autocomplete (4 hours)
  - Validation integration (2 hours)
  - Sample data panel (2 hours)
  - Tests (2 hours)
- Function reference modal (4 hours)
- Integration & polish (8 hours)
  - E2E tests (4 hours)
  - User testing (2 hours)
  - Documentation (2 hours)

**Testing Requirements:**
- Unit tests: Formula generation from tokens
- Integration tests: Validation API
- UI tests: Mode switching, token manipulation
- E2E tests: Build formula → Save rule → Evaluate
- User testing: 5 users create formulas without errors

**Release:**
- Deploy to staging: Day 12
- User testing: Days 13-14
- Production deployment: End of Week 7
- Tutorial video: End of Week 7

---

### Phase 5: Monitoring & Iteration (Ongoing)

**Duration:** Continuous
**Team:** Product Manager, Engineering Lead

**Activities:**
- Monitor error rates (formula evaluation, modal workflows)
- Collect user feedback (support tickets, user interviews)
- Track success metrics (see Section 7)
- Plan follow-up improvements

**Key Metrics to Monitor:**
- Formula evaluation success rate
- Modal workflow completion rate
- Dropdown usage (scroll events, field selection)
- Support ticket volume
- User satisfaction scores

---

## 7. Success Metrics

### 7.1 Bug Fix Success Criteria

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| **Modal Workflow Errors** | 15 tickets/week | <3 tickets/week | Support ticket volume |
| **Formula Evaluation Success Rate** | 0% (all fail) | 100% | Backend logs: successful evaluations / total attempts |
| **Dropdown Accessibility Complaints** | 8 tickets/week | 0 tickets/week | Support ticket categorization |
| **Cache Invalidation Latency** | Manual refresh required | <500ms auto-refresh | Frontend performance monitoring |
| **Foreign Key Rule Confusion** | 5 questions/week | <1 question/week | Support chat analysis |

### 7.2 Feature Adoption Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Action Multipliers Adoption** | 50% of RAM rules use multipliers within 30 days | Database query: rules with condition_multipliers / total RAM rules |
| **Formula Builder Usage** | 80% of new formulas created via builder (vs text mode) | Frontend analytics: builder saves / total formula saves |
| **Formula Error Rate** | <5% of formulas have syntax errors | Backend error logs: formula parse errors / total formula evaluations |
| **Time to Create Complex Rule** | <5 minutes (down from 15 min baseline) | User testing time trials |

### 7.3 User Satisfaction Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **NPS for Valuation Rules** | >40 (up from 15) | Quarterly user survey |
| **Rule Builder Task Completion** | >90% complete without help docs | User testing task success rate |
| **Formula Confidence Score** | >4.0/5.0 (up from 2.5) | User survey: "I feel confident creating formulas" |
| **Support Contact Rate** | <5% of active users contact support | Support tickets / monthly active users |

### 7.4 Performance Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Formula Evaluation Time** | <50ms per listing | Backend performance monitoring |
| **Dropdown Render Time** | <100ms | Frontend performance profiling |
| **Rule Save Latency** | <1s (P95) | API response time monitoring |
| **Page Load Time (Valuation Rules)** | <2s (P95) | Frontend performance monitoring |

### 7.5 Business Impact Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Pricing Accuracy** | >95% of listings have non-zero adjustments | Valuation breakdown analysis |
| **Rule Coverage** | >80% of listings matched by active rules | Rule evaluation logs |
| **Rule Maintenance Time** | <30 min/week (down from 2 hours) | User time tracking survey |
| **User Retention (Power Users)** | >90% month-over-month | User analytics |

---

## 8. Risk Assessment

### 8.1 Technical Risks

#### Risk 1: Formula Evaluation Performance Degradation

**Severity:** Medium
**Probability:** Low

**Description:**
Complex formulas with nested functions could slow down listing valuation, especially in batch operations (1000+ listings).

**Mitigation:**
- Implement formula complexity limits (max 10 operations)
- Cache formula compilation (AST parsing)
- Add performance monitoring alerts (>100ms evaluation)
- Implement formula profiler for debugging

**Contingency:**
- Add formula timeout (500ms max)
- Fallback to fixed value if evaluation fails
- User warning for overly complex formulas

---

#### Risk 2: React Query Cache Invalidation Edge Cases

**Severity:** Medium
**Probability:** Medium

**Description:**
Async cache invalidation may not handle all edge cases (rapid mutations, network failures, concurrent requests).

**Mitigation:**
- Comprehensive integration testing with network throttling
- Error boundary for React Query mutations
- Fallback to manual refresh button if auto-refresh fails
- Add retry logic for failed invalidations

**Contingency:**
- Keep manual "Refresh" button visible
- Add "Retry" button on save errors
- User notification if data may be stale

---

#### Risk 3: Action Multipliers Complexity

**Severity:** Low
**Probability:** Medium

**Description:**
Users may create overly complex multiplier chains (10+ conditions), making rules hard to understand and debug.

**Mitigation:**
- Limit multipliers to 5 per action (UI validation)
- Visual preview of multiplier impact in breakdown
- "Simplify Rule" suggestions in UI
- Documentation with best practices

**Contingency:**
- Add "Flatten Multipliers" tool (expand into separate rules)
- Admin audit tool to identify overly complex rules

---

#### Risk 4: Formula Builder Generates Invalid Formulas

**Severity:** High
**Probability:** Low

**Description:**
Visual builder may generate syntactically valid but semantically incorrect formulas (e.g., division by zero, type mismatches).

**Mitigation:**
- Server-side validation with sample evaluation
- Type checking for field operations
- Whitelist of allowed operator combinations
- Required sample data test before save

**Contingency:**
- Real-time validation with error highlighting
- Block save if validation fails
- Rollback to text mode if builder has issues

---

### 8.2 User Impact Risks

#### Risk 1: Breaking Changes to Existing Rules

**Severity:** High
**Probability:** Low

**Description:**
Formula translation or backend changes could alter behavior of existing rules, changing listing valuations.

**Mitigation:**
- Comprehensive regression testing before deployment
- Database snapshot before production deployment
- Valuation comparison report (before/after)
- Gradual rollout (10% → 50% → 100% traffic)

**Rollback Plan:**
- Keep old formula evaluation code path
- Feature flag to switch between old/new evaluation
- Database restore from snapshot if needed
- User communication about reverted changes

---

#### Risk 2: Learning Curve for New Features

**Severity:** Medium
**Probability:** High

**Description:**
Action Multipliers and Formula Builder introduce new concepts; users may struggle to adopt them.

**Mitigation:**
- In-app tooltips and help text
- Video tutorial walkthrough (5 min)
- Interactive onboarding for first-time users
- "Example Rules" library with templates

**Success Criteria:**
- >70% of users successfully create multiplier on first attempt
- <10% of users revert to old methods after trying new features

---

#### Risk 3: Performance Perception

**Severity:** Low
**Probability:** Medium

**Description:**
Users may perceive slower save operations due to async cache invalidation (waiting for refetch).

**Mitigation:**
- Clear loading indicators ("Saving... Refreshing data...")
- Progress feedback (save → refresh → complete)
- Target <1s total latency (save + refetch)
- Optimistic updates for instant feedback (Phase 5)

**User Communication:**
- Toast message: "Rule saved successfully, updating list..."
- Blog post explaining improved data consistency

---

### 8.3 Data Integrity Risks

#### Risk 1: Formula Translation Errors

**Severity:** High
**Probability:** Low

**Description:**
Incorrect formula translation could cause silent calculation errors, leading to incorrect pricing.

**Mitigation:**
- Automated comparison tests (old vs new formula results)
- Manual validation of 10 sample formulas by domain expert
- Canary deployment with validation checks
- User-visible formula translation (show both versions)

**Detection:**
- Anomaly detection: flag listings with >50% valuation change
- Weekly audit report of formula evaluation results
- User reporting mechanism for pricing discrepancies

---

#### Risk 2: Multiplier Conflicts

**Severity:** Medium
**Probability:** Medium

**Description:**
Multiple multipliers matching same listing could produce unexpected results (multiplicative vs additive).

**Mitigation:**
- Clear documentation: "First matching multiplier wins"
- UI warning when multipliers overlap
- Validation: prevent duplicate field conditions in same action
- Breakdown shows which multiplier was applied

**User Education:**
- Tooltip: "Only the first matching multiplier will be applied"
- Example: "DDR3 (0.7×) and DDR4 (1.0×) should be in separate multipliers"

---

## 9. Timeline & Estimates

### 9.1 Overall Schedule

```
Week 1: Phase 1 - Critical Bug Fixes
├─ Day 1-2: Implementation
├─ Day 3: Staging deployment & testing
└─ Day 4-5: Production deployment & monitoring

Week 2: Phase 2 - UX Improvements
├─ Day 1-2: Implementation
├─ Day 3: Staging deployment & testing
└─ Day 4-5: Production deployment & accessibility audit

Weeks 3-4: Phase 3 - Action Multipliers
├─ Week 3 Day 1-3: Backend implementation
├─ Week 3 Day 4-5: Frontend implementation
├─ Week 4 Day 1-3: Integration & testing
└─ Week 4 Day 4-5: Beta testing & deployment

Weeks 5-7: Phase 4 - Formula Builder UI
├─ Week 5: Backend API + Frontend scaffold
├─ Week 6: UI implementation & polish
└─ Week 7: Testing, documentation, deployment

Week 8+: Phase 5 - Monitoring & Iteration
└─ Ongoing: Metric collection, user feedback, improvements
```

### 9.2 Detailed Task Breakdown

#### Phase 1: Critical Bug Fixes (40 hours total)

| Task | Engineer | Hours | Dependencies |
|------|----------|-------|--------------|
| BUG-001: Wrong modal fix | Frontend | 2 | None |
| BUG-002: Cache invalidation fix (3 files) | Frontend | 4 | None |
| BUG-004: Add clamp function | Backend | 1 | None |
| BUG-004: Formula translation | Backend | 4 | clamp function |
| BUG-004: Enhanced logging | Backend | 2 | None |
| BUG-004: Key mapping fix | Backend | 2 | None |
| Unit tests (formulas) | Backend | 4 | Formula translation |
| Integration tests (evaluation) | Backend | 3 | All backend changes |
| Manual QA | QA | 4 | All fixes deployed to staging |
| Performance testing | Backend | 2 | Integration tests pass |
| Documentation updates | Tech Writer | 2 | All fixes complete |
| **Subtotal** | | **30** | |
| **Buffer (25%)** | | **10** | |
| **Total** | | **40** | |

#### Phase 2: UX Improvements (24 hours total)

| Task | Engineer | Hours | Dependencies |
|------|----------|-------|--------------|
| BUG-003: CommandList wrapper | Frontend | 2 | None |
| BUG-003: Scroll shadows | Frontend | 3 | CommandList |
| BUG-003: Scrollbar styling | Frontend | 1 | CommandList |
| BUG-003: Testing (responsive + a11y) | QA | 2 | All UI changes |
| BUG-005: Metadata flags | Backend | 1 | None |
| BUG-005: Frontend filter | Frontend | 2 | Metadata flags |
| BUG-005: Testing | QA | 1 | Filter implemented |
| Accessibility audit | A11y Specialist | 4 | All UI changes |
| Documentation | Tech Writer | 2 | All changes complete |
| **Subtotal** | | **18** | |
| **Buffer (33%)** | | **6** | |
| **Total** | | **24** | |

#### Phase 3: Action Multipliers (56 hours total)

| Task | Engineer | Hours | Dependencies |
|------|----------|-------|--------------|
| Backend: ConditionMultiplier dataclass | Backend | 2 | None |
| Backend: Action.calculate() update | Backend | 3 | ConditionMultiplier |
| Backend: Database migration | Backend | 1 | Schema design |
| Backend: Unit tests | Backend | 2 | calculate() update |
| Frontend: ActionBuilder UI scaffold | Frontend | 3 | None |
| Frontend: Multiplier CRUD logic | Frontend | 3 | UI scaffold |
| Frontend: Field selector integration | Frontend | 2 | EntityFieldSelector |
| Frontend: Value dropdown logic | Frontend | 4 | Field selector |
| Frontend: Form state management | Frontend | 2 | All UI components |
| Frontend: UI tests | Frontend | 2 | Form state |
| Integration: E2E evaluation tests | Full-Stack | 4 | Backend + Frontend complete |
| Manual QA | QA | 2 | E2E tests pass |
| Beta testing with users | PM + QA | 8 | QA complete |
| Documentation & tutorial | Tech Writer | 3 | Feature complete |
| **Subtotal** | | **41** | |
| **Buffer (37%)** | | **15** | |
| **Total** | | **56** | |

#### Phase 4: Formula Builder UI (72 hours total)

| Task | Engineer | Hours | Dependencies |
|------|----------|-------|--------------|
| Backend: Validation API endpoint | Backend | 3 | None |
| Backend: Sample evaluation logic | Backend | 2 | Validation API |
| Backend: Tests | Backend | 1 | Evaluation logic |
| Frontend: Component scaffold | Frontend | 4 | None |
| Frontend: Visual mode UI | Frontend | 8 | Component scaffold |
| Frontend: Token management | Frontend | 4 | Visual mode |
| Frontend: Field autocomplete | Frontend | 4 | EntityFieldSelector |
| Frontend: Text mode integration | Frontend | 2 | Visual mode |
| Frontend: Validation integration | Frontend | 2 | Backend API |
| Frontend: Sample data panel | Frontend | 2 | Validation integration |
| Frontend: Function reference modal | Frontend | 4 | None |
| Frontend: Tests | Frontend | 2 | All UI complete |
| Integration: E2E tests | Full-Stack | 4 | Backend + Frontend |
| User testing (5 users) | PM + QA | 8 | E2E tests pass |
| Documentation & video tutorial | Tech Writer + Video | 8 | Feature complete |
| **Subtotal** | | **58** | |
| **Buffer (24%)** | | **14** | |
| **Total** | | **72** | |

### 9.3 Resource Allocation

| Role | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Total |
|------|---------|---------|---------|---------|-------|
| **Backend Engineer** | 16h | 1h | 8h | 6h | **31h** |
| **Frontend Engineer** | 6h | 8h | 16h | 32h | **62h** |
| **Full-Stack Engineer** | - | - | 4h | 4h | **8h** |
| **QA Engineer** | 6h | 3h | 10h | 8h | **27h** |
| **A11y Specialist** | - | 4h | - | - | **4h** |
| **Tech Writer** | 2h | 2h | 3h | 8h | **15h** |
| **Product Manager** | - | - | 4h | 4h | **8h** |
| **Video Producer** | - | - | - | 4h | **4h** |
| **Total** | **30h** | **18h** | **45h** | **66h** | **159h** |

### 9.4 Release Schedule

| Phase | Staging Deploy | Production Deploy | Post-Deploy Monitoring |
|-------|----------------|-------------------|----------------------|
| **Phase 1** | Week 1 Wed | Week 1 Fri | Week 2 (critical bugs) |
| **Phase 2** | Week 2 Wed | Week 2 Fri | Week 3 (UX metrics) |
| **Phase 3** | Week 4 Wed | Week 4 Fri | Weeks 5-6 (adoption) |
| **Phase 4** | Week 7 Mon | Week 7 Fri | Weeks 8-10 (usage) |

### 9.5 Dependencies & Blockers

**External Dependencies:**
- None (all work internal to Deal Brain codebase)

**Internal Dependencies:**
- Phase 3 requires Phase 1 formula fixes (shared evaluation logic)
- Phase 4 requires Phase 2 dropdown improvements (field selector reuse)

**Potential Blockers:**
- User acceptance testing reveals fundamental UX issues (Phase 3/4)
- Performance issues require rearchitecture (Phase 1)
- Accessibility audit fails (Phase 2) - requires remediation before Phase 3

**Mitigation:**
- Weekly stakeholder check-ins
- Early user testing (not just at end of phase)
- Performance benchmarking in Week 1
- Accessibility review in design phase (not just implementation)

---

## 10. Appendices

### Appendix A: Related Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| **Bug Analysis: Modal Issues** | `/docs/project_plans/bug-analysis-modal-issues.md` | Detailed root cause analysis of BUG-001 and BUG-002 |
| **Implementation Guide: Modal Fixes** | `/docs/project_plans/IMPLEMENTATION_GUIDE_modal_fixes.md` | Step-by-step code changes for modal bugs |
| **Formula Action Bug Analysis** | `/docs/project_plans/requests/formula-action-bug-analysis.md` | Technical analysis of formula evaluation failures |
| **Scrollable Dropdown Specification** | `/docs/design/scrollable-dropdown-specification.md` | Complete UI/UX design for dropdown improvements |
| **Valuation Rules Architecture** | `/docs/architecture/valuation-rules.md` | System architecture overview |
| **Basic-to-Advanced Transition PRD** | `/docs/project_plans/valuation-rules/basic-to-advanced-transition/basic-to-advanced-transition-prd.md` | Related baseline hydration feature |

### Appendix B: API Endpoints

**New Endpoints:**
```
POST /api/v1/valuation-rules/validate-formula
  Request: { formula: string, entity_type: string, sample_context?: dict }
  Response: { is_valid: bool, errors: string[], sample_result?: float, available_fields: string[] }
```

**Modified Endpoints:**
- None (all changes internal to existing endpoints)

**Database Schema Changes:**
- `ValuationRuleAction.modifiers_json` extended with `condition_multipliers` array
- `ValuationRuleV2.metadata_json` extended with `is_foreign_key_rule` flag

### Appendix C: Testing Scenarios

**Critical Path Tests:**
1. Create new Ruleset → Add RuleGroup → Add Rule → Verify all appear
2. Create formula rule with `clamp()` → Evaluate listing → Verify adjustment
3. Open field selector dropdown → Scroll to bottom → Select field
4. Create RAM rule with DDR multipliers → Evaluate DDR3/4/5 listings → Verify adjustments
5. Build formula visually → Switch to text mode → Save → Evaluate

**Regression Tests:**
1. Existing rules continue to evaluate correctly
2. Basic mode still syncs with Advanced mode
3. Valuation breakdown displays correctly
4. Manual refresh button still works
5. Rule duplication preserves all properties

**Performance Tests:**
1. Evaluate 100 listings with complex formulas (<5s total)
2. Dropdown renders with 50 fields (<100ms)
3. Modal open/close latency (<200ms)
4. Rule save with multipliers (<1s)

### Appendix D: User Communication Plan

**Internal Announcements:**
- Week 1 Friday: "Critical valuation bug fixes deployed"
- Week 2 Friday: "Improved field selector and UI cleanup"
- Week 4 Friday: "New feature: Action Multipliers for conditional pricing"
- Week 7 Friday: "New feature: Visual Formula Builder"

**User-Facing Documentation:**
- Update to "Valuation Rules User Guide" (all phases)
- New tutorial: "Using Action Multipliers for Dynamic Pricing" (Phase 3)
- New video: "Building Formulas Visually" (Phase 4)
- Release notes for each deployment

**Support Team Training:**
- Phase 1: Bug fix overview (30 min)
- Phase 3: Action Multipliers walkthrough (1 hour)
- Phase 4: Formula Builder demo (1 hour)

### Appendix E: Rollback Procedures

**Phase 1 Rollback:**
- Revert commit with modal fixes
- Revert formula engine changes
- Restore previous Docker image
- Database rollback NOT required (schema unchanged)
- Downtime: <5 minutes

**Phase 2 Rollback:**
- Revert frontend dropdown changes
- Restore previous frontend bundle
- Database rollback NOT required
- Downtime: 0 (frontend only)

**Phase 3 Rollback:**
- Disable multiplier evaluation via feature flag
- UI automatically hides multiplier section
- Existing multipliers persist in DB (ignored during evaluation)
- Can re-enable without data loss
- Database rollback NOT required

**Phase 4 Rollback:**
- Disable formula builder via feature flag
- Users default to text mode
- Existing formulas unaffected
- Database rollback NOT required

### Appendix F: Success Metrics Dashboard

**Monitoring Tools:**
- Grafana dashboard: "Valuation Rules Health"
  - Formula evaluation success rate (line chart)
  - Modal workflow errors (counter)
  - Dropdown interactions (heatmap)
  - API latency (histogram)

**Weekly Reports:**
- Support ticket volume by category
- Feature adoption metrics (multipliers, formula builder)
- User satisfaction scores
- Performance benchmarks

**Alerts:**
- Formula evaluation error rate >5% (Slack alert)
- Modal save latency >2s (P95) (PagerDuty)
- Dropdown render time >200ms (Slack alert)
- Support ticket spike (>10 tickets/day) (Email alert)

---

## Document Approval

**Prepared By:** Product & Engineering Teams
**Review Required:** Product Manager, Engineering Lead, UX Designer
**Approval Required:** VP of Engineering, VP of Product

**Review Status:**
- [ ] Product Manager reviewed
- [ ] Engineering Lead reviewed
- [ ] UX Designer reviewed
- [ ] VP of Engineering approved
- [ ] VP of Product approved

**Revision History:**
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-15 | Claude Code | Initial PRD creation |

---

**End of Document**
