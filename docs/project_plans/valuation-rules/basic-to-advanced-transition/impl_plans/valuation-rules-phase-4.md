# Phase 4: Formula Builder (Weeks 5-7)

## Implementation Plan

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
