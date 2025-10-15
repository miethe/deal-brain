# Formula-Type Actions Bug Analysis & Fix Strategy

## Executive Summary

Formula-type Actions in the Valuation Rules system are not being applied correctly to Listings. Despite having valid baseline rules with formula definitions like `"clamp((cpu_mark_single/100)*5.2, 0, 80)"`, these formulas are not producing any valuation adjustments. This document provides a root cause analysis, investigation steps, and implementation strategy for fixing the issue and enhancing the system with a visual formula builder.

## Current Implementation Overview

### Formula Processing Flow
1. **Baseline Data** (`/data/baselines/baseline-v1.0.json`): Contains human-readable formula strings
2. **Hydration Service** (`baseline_hydration.py`): Converts baseline rules to executable rules
3. **Formula Engine** (`formula.py`): Parses and evaluates Python AST-compatible formulas
4. **Action Engine** (`actions.py`): Executes formula actions during rule evaluation
5. **Rule Evaluation Service** (`rule_evaluation.py`): Orchestrates rule evaluation for listings

## Root Cause Analysis

### Hypothesis 1: Formula Syntax Mismatch (MOST LIKELY)
**Issue**: The baseline formulas use a non-Python syntax that isn't compatible with the FormulaEngine's AST parser.

**Evidence**:
- Baseline formula: `"clamp((cpu_mark_single/100)*5.2, 0, 80)"`
- The `clamp` function is not in the `ALLOWED_FUNCTIONS` list in `formula.py`
- The FormulaEngine expects Python-compatible syntax like `"min(max((cpu_mark_single/100)*5.2, 0), 80)"`

**Impact**: Formula parsing fails silently or returns 0.0, resulting in no valuation adjustment.

### Hypothesis 2: Missing Context Fields
**Issue**: The formula references fields that aren't present in the evaluation context.

**Evidence**:
- Formula references `cpu_mark_single` directly
- Context might need `cpu.cpu_mark_single` or a flattened version
- The `build_context_from_listing` function may not be including all necessary fields

**Impact**: Field lookup fails, causing formula evaluation to error or return 0.0.

### Hypothesis 3: Silent Error Handling
**Issue**: Errors during formula evaluation are being suppressed without proper logging.

**Evidence**:
- In `actions.py` line 79: Formula evaluation can raise `ValueError`
- In `actions.py` lines 220-226: Errors are caught but only added to breakdown, not logged
- No error telemetry or logging for formula parsing failures

**Impact**: Failures go unnoticed, making debugging difficult.

### Hypothesis 4: Hydration Process Issues
**Issue**: The baseline hydration process isn't correctly transferring formula text to the action.

**Evidence**:
- `_hydrate_formula` method (line 242) checks for `formula_text` in metadata
- If missing, it falls back to `_hydrate_fixed` with no formula
- The baseline data uses `"Formula"` key, not `"formula_text"`

**Impact**: Formula actions are created without actual formulas, defaulting to 0.0 adjustments.

## Investigation Steps

### 1. Immediate Debugging
```python
# Add logging to baseline_hydration.py:_hydrate_formula
logger.info(f"Hydrating formula rule: {rule.name}")
logger.info(f"Formula text from metadata: {rule.metadata_json.get('formula_text')}")
logger.info(f"Full metadata: {rule.metadata_json}")

# Add logging to actions.py:calculate (formula branch)
elif self.action_type == ActionType.FORMULA:
    logger.debug(f"Evaluating formula: {self.formula}")
    logger.debug(f"Context keys: {list(context.keys())}")
    try:
        result = formula_engine.evaluate(self.formula or "", context)
        logger.debug(f"Formula result: {result}")
    except Exception as e:
        logger.error(f"Formula evaluation failed: {e}", exc_info=True)
        raise
```

### 2. Test Formula Directly
```python
# Create a test script to verify formula evaluation
from dealbrain_core.rules.formula import FormulaEngine

engine = FormulaEngine()

# Test current formula (will fail)
try:
    result = engine.evaluate("clamp((cpu_mark_single/100)*5.2, 0, 80)", {"cpu_mark_single": 2500})
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")

# Test corrected formula
result = engine.evaluate("min(max((cpu_mark_single/100)*5.2, 0), 80)", {"cpu_mark_single": 2500})
print(f"Corrected result: {result}")  # Should output 80.0
```

### 3. Database Inspection
```sql
-- Check hydrated formula actions
SELECT
    r.name,
    r.metadata_json->>'formula_text' as original_formula,
    a.formula as action_formula,
    a.action_type
FROM valuation_rules_v2 r
JOIN valuation_rule_actions a ON a.rule_id = r.id
WHERE a.action_type = 'formula';

-- Check if formulas are being stored
SELECT
    name,
    metadata_json
FROM valuation_rules_v2
WHERE metadata_json->>'field_type' = 'formula';
```

## Proposed Fix Implementation

### Phase 1: Immediate Fixes (2-3 days)

#### 1.1 Formula Syntax Translation
```python
# Add to baseline_hydration.py
def _translate_formula_syntax(self, formula_text: str) -> str:
    """Translate human-readable formula to Python AST-compatible syntax."""
    translations = {
        "clamp(": "min(max(",  # Handle clamp(value, min, max)
        "usd ≈ ": "",  # Remove approximation symbols
        " with cohort guardrails": "",  # Remove human-readable suffixes
    }

    result = formula_text
    for old, new in translations.items():
        result = result.replace(old, new)

    # Fix clamp syntax: clamp(val, min, max) -> min(max(val, min), max)
    import re
    clamp_pattern = r'min\(max\(([^,]+),\s*([^,]+),\s*([^)]+)\)'
    clamp_replacement = r'min(max(\1, \2), \3)'
    result = re.sub(clamp_pattern, clamp_replacement, result)

    return result.strip()
```

#### 1.2 Enhanced Error Logging
```python
# Update formula.py:FormulaEngine.evaluate
def evaluate(self, formula: str, context: dict[str, Any]) -> float:
    if not formula:
        logger.warning("Empty formula provided")
        return 0.0

    try:
        tree = self.parser.parse(formula)
    except ValueError as e:
        logger.error(f"Formula parse error for '{formula}': {e}")
        # Store error for debugging
        self._last_error = str(e)
        raise ValueError(f"Formula validation failed: {e}")

    eval_context = self._build_eval_context(context)
    logger.debug(f"Evaluating formula '{formula}' with context keys: {list(eval_context.keys())[:10]}")

    try:
        result = eval(compile(tree, '<formula>', 'eval'), {"__builtins__": {}}, eval_context)
        logger.debug(f"Formula result: {result}")
        return float(result)
    except Exception as e:
        logger.error(f"Formula evaluation error: {e}", extra={"formula": formula, "context_sample": list(eval_context.keys())[:5]})
        self._last_error = str(e)
        raise ValueError(f"Formula evaluation failed: {e}")
```

#### 1.3 Fix Baseline Data Key Mapping
```python
# Update baseline_hydration.py:_hydrate_formula
async def _hydrate_formula(
    self, session: AsyncSession, rule: ValuationRuleV2, actor: str
) -> list[ValuationRuleV2]:
    # Check both possible keys for formula text
    formula_text = (
        rule.metadata_json.get("formula_text") or
        rule.metadata_json.get("Formula") or
        rule.metadata_json.get("formula")
    )

    if not formula_text:
        logger.warning(f"No formula found for rule {rule.name}, falling back to fixed value")
        return await self._hydrate_fixed(session, rule, actor)

    # Translate formula syntax
    translated_formula = self._translate_formula_syntax(formula_text)
    logger.info(f"Translated formula for {rule.name}: '{formula_text}' -> '{translated_formula}'")
```

#### 1.4 Add Clamp Function Support
```python
# Update formula.py:FormulaParser.ALLOWED_FUNCTIONS
ALLOWED_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "int": int,
    "float": float,
    "sum": sum,
    "sqrt": math.sqrt,
    "pow": pow,
    "floor": math.floor,
    "ceil": math.ceil,
    # Add clamp function
    "clamp": lambda value, min_val, max_val: min(max(value, min_val), max_val),
}
```

### Phase 2: Enhanced Testing (1-2 days)

#### 2.1 Unit Tests for Formula Translation
```python
# tests/test_formula_translation.py
import pytest
from apps.api.dealbrain_api.services.baseline_hydration import BaselineHydrationService

@pytest.mark.parametrize("input_formula,expected", [
    ("clamp((cpu_mark_single/100)*5.2, 0, 80)", "min(max((cpu_mark_single/100)*5.2, 0), 80)"),
    ("usd ≈ (cpu_mark_multi/1000)*3.6", "(cpu_mark_multi/1000)*3.6"),
    ("ram_gb * 2.5 with cohort guardrails", "ram_gb * 2.5"),
])
def test_formula_translation(input_formula, expected):
    service = BaselineHydrationService()
    result = service._translate_formula_syntax(input_formula)
    assert result == expected
```

#### 2.2 Integration Test for Formula Actions
```python
# tests/test_formula_action_evaluation.py
async def test_formula_action_evaluation(db_session):
    # Create listing with CPU data
    listing = create_test_listing(cpu_mark_single=2500)

    # Create formula rule
    rule = create_formula_rule(
        formula="min(max((cpu_mark_single/100)*5.2, 0), 80)"
    )

    # Evaluate
    service = RuleEvaluationService()
    result = await service.evaluate_listing(db_session, listing.id, rule.ruleset_id)

    assert result["total_adjustment"] == 80.0  # Clamped at max
```

### Phase 3: Visual Formula Builder UI (5-7 days)

#### 3.1 Design Specification
```typescript
// Formula Builder Component Structure
interface FormulaBuilderProps {
  entityType: 'Listing' | 'CPU' | 'GPU' | 'RAM';
  onFormulaChange: (formula: string) => void;
  initialFormula?: string;
}

interface FormulaElement {
  type: 'field' | 'operator' | 'function' | 'constant';
  value: string;
  display: string;
}

// Visual representation of formula as draggable blocks
const FormulaBuilder: React.FC<FormulaBuilderProps> = ({...}) => {
  // Drag-and-drop formula construction
  // Real-time validation
  // Preview with sample data
  // Syntax highlighting
}
```

#### 3.2 Backend Validation API
```python
# New endpoint for formula validation
@router.post("/valuation/rules/validate-formula")
async def validate_formula(
    formula: str,
    entity_type: str,
    sample_context: dict[str, Any] | None = None
) -> dict:
    """
    Validate formula syntax and optionally evaluate with sample data.

    Returns:
        - is_valid: bool
        - errors: list[str]
        - translated_formula: str (Python AST version)
        - sample_result: float | None
        - available_fields: list[str] (for autocomplete)
    """
```

#### 3.3 UI Mockup Components
```typescript
// Field Selector with Autocomplete
<FieldSelector
  entity={entityType}
  onSelect={(field) => addFormulaElement({type: 'field', value: field})}
  availableFields={['cpu_mark_single', 'cpu_mark_multi', 'ram_gb', ...]}
/>

// Operator Palette
<OperatorPalette
  operators={['+', '-', '*', '/', '(', ')']}
  functions={['min', 'max', 'clamp', 'round', 'sqrt']}
/>

// Formula Preview with Syntax Highlighting
<FormulaPreview
  formula={currentFormula}
  validationErrors={errors}
  sampleResult={evaluationResult}
/>

// Test Data Input
<TestDataPanel
  fields={requiredFields}
  onEvaluate={(data) => testFormula(formula, data)}
/>
```

## Testing Strategy

### 1. Unit Tests
- Formula syntax translation
- Formula parsing validation
- Context building from listings
- Error handling in formula evaluation

### 2. Integration Tests
- End-to-end baseline hydration with formulas
- Rule evaluation with formula actions
- Listing valuation calculation
- Error propagation and logging

### 3. Regression Tests
- Ensure existing fixed_value, per_unit, multiplier actions still work
- Verify backward compatibility with legacy valuation
- Check performance with complex formulas

### 4. UI Tests
- Formula builder drag-and-drop
- Real-time validation feedback
- Sample evaluation preview
- Error state handling

## Monitoring & Observability

### 1. Metrics to Track
```python
# Add Prometheus metrics
formula_evaluation_errors = Counter(
    'valuation_formula_errors_total',
    'Total number of formula evaluation errors',
    ['formula_type', 'error_type']
)

formula_evaluation_duration = Histogram(
    'valuation_formula_duration_seconds',
    'Time spent evaluating formulas',
    ['complexity_bucket']
)
```

### 2. Logging Enhancement
```python
# Structured logging for formula debugging
logger.info("formula_evaluation", extra={
    "formula_id": rule.id,
    "formula_text": formula,
    "translated": translated_formula,
    "context_fields": list(context.keys()),
    "result": result,
    "duration_ms": duration
})
```

### 3. Debug Dashboard
- Formula success/failure rates
- Most common formula errors
- Performance by formula complexity
- Field usage frequency

## Rollout Plan

### Week 1: Immediate Fixes
- Day 1-2: Implement formula translation and logging
- Day 3: Deploy fixes to staging
- Day 4: Verify baseline rules are working
- Day 5: Production deployment with monitoring

### Week 2: Testing & Refinement
- Day 1-2: Write comprehensive tests
- Day 3-4: Performance optimization
- Day 5: Documentation update

### Week 3: Visual Formula Builder
- Day 1-2: Backend API development
- Day 3-4: Frontend component implementation
- Day 5-7: Integration and testing

## Success Criteria

1. **Immediate**: All baseline formula rules produce non-zero valuations
2. **Short-term**: 100% of formula evaluations succeed without errors
3. **Long-term**: Visual formula builder reduces syntax errors by 95%
4. **User Experience**: Formula creation time reduced from 10 minutes to 2 minutes

## Appendix: Common Formula Patterns

### Benchmark-based Valuation
```python
# Original: "usd ≈ (cpu_mark_single/100)*5.2 with cohort guardrails"
# Translated: "(cpu_mark_single/100)*5.2"
# With clamp: "clamp((cpu_mark_single/100)*5.2, 0, 80)"
```

### Capacity-based Pricing
```python
# RAM: "ram_gb * 2.5"
# Storage: "(storage_gb/1000) * 45"  # Per TB
```

### Conditional Formulas
```python
# Premium for high-performance
"base_value * (1.2 if cpu_mark_single > 3000 else 1.0)"
```

### Complex Calculations
```python
# Combined metrics
"(cpu_mark_multi/1000*3.6 + cpu_mark_single/100*5.2) * condition_multiplier"
```

## References

- Formula Engine: `/packages/core/dealbrain_core/rules/formula.py`
- Baseline Hydration: `/apps/api/dealbrain_api/services/baseline_hydration.py`
- Action Engine: `/packages/core/dealbrain_core/rules/actions.py`
- Baseline Data: `/data/baselines/baseline-v1.0.json`
- Bug Report: `/docs/project_plans/requests/10-15-bugs.md`