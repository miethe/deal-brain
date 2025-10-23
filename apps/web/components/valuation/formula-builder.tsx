"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, Info, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { useDebounce } from "use-debounce";

import { Button } from "../ui/button";
import { Label } from "../ui/label";
import { Alert, AlertDescription } from "../ui/alert";
import { ScrollArea } from "../ui/scroll-area";
import { cn } from "../../lib/utils";
import {
  MATH_OPERATIONS,
  COMPARISON_OPERATIONS,
  LOGICAL_OPERATIONS,
  FUNCTION_OPERATIONS,
  GROUP_OPERATIONS,
  FORMULA_TEMPLATES,
  insertAtCursor,
  getCursorPosition,
  setCursorPosition,
  type Operation,
  type FormulaTemplate,
} from "../../lib/formula-utils";
import { validateFormula, type FormulaValidationResponse } from "../../lib/api/rules";
import { fetchEntitiesMetadata, type FieldMetadata } from "../../lib/api/entities";
import { FormulaEditor } from "./formula-editor";

export interface FormulaBuilderProps {
  value: string;
  onChange: (formula: string) => void;
  entityType?: string;
  disabled?: boolean;
  className?: string;
}

interface FieldCategory {
  label: string;
  fields: FieldMetadata[];
}

export function FormulaBuilder({
  value,
  onChange,
  entityType = "Listing",
  disabled = false,
  className,
}: FormulaBuilderProps) {
  const [formula, setFormula] = useState(value);
  const [cursorPosition, setCursorPositionState] = useState(0);
  const [showTemplates, setShowTemplates] = useState(false);
  const [validationResult, setValidationResult] = useState<FormulaValidationResponse | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Debounce formula changes for validation (300ms)
  const [debouncedFormula] = useDebounce(formula, 300);

  // Fetch available fields metadata
  const { data: metadata, isLoading: isLoadingFields } = useQuery({
    queryKey: ["entities-metadata"],
    queryFn: fetchEntitiesMetadata,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Validation mutation
  const validationMutation = useMutation({
    mutationFn: (formulaToValidate: string) =>
      validateFormula({
        formula: formulaToValidate,
        entity_type: entityType,
      }),
    onSuccess: (data) => {
      setValidationResult(data);
    },
    onError: () => {
      setValidationResult({
        valid: false,
        errors: [{ message: "Validation request failed", severity: "error" }],
        preview: undefined,
        used_fields: [],
        available_fields: [],
      });
    },
  });

  // Trigger validation when debounced formula changes
  useEffect(() => {
    if (debouncedFormula.trim()) {
      validationMutation.mutate(debouncedFormula);
    } else {
      setValidationResult(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedFormula]);

  // Sync formula with parent component
  useEffect(() => {
    if (formula !== value) {
      onChange(formula);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formula]);

  // Sync external value changes
  useEffect(() => {
    if (value !== formula) {
      setFormula(value);
    }
  }, [value]);

  // Organize fields by entity for better UX
  const fieldCategories: FieldCategory[] = metadata?.entities
    .filter((entity) => {
      // For Listing entity type, include all fields
      // For other entity types, only include that specific entity's fields
      if (entityType === "Listing") {
        return true;
      }
      return entity.key.toLowerCase() === entityType.toLowerCase();
    })
    .map((entity) => ({
      label: entity.label,
      fields: entity.fields,
    })) || [];

  const handleFieldInsert = useCallback((fieldName: string) => {
    if (disabled) return;

    const textarea = textareaRef.current;
    const currentCursor = textarea ? getCursorPosition(textarea) : cursorPosition;

    const { newValue, newCursorPosition } = insertAtCursor(
      formula,
      fieldName,
      currentCursor,
      0
    );

    setFormula(newValue);

    // Set cursor position after state update
    if (textarea) {
      setCursorPosition(textarea, newCursorPosition);
    }
  }, [formula, cursorPosition, disabled]);

  const handleOperationInsert = useCallback((operation: Operation) => {
    if (disabled) return;

    const textarea = textareaRef.current;
    const currentCursor = textarea ? getCursorPosition(textarea) : cursorPosition;

    const { newValue, newCursorPosition } = insertAtCursor(
      formula,
      operation.value,
      currentCursor,
      operation.insertCursorOffset || 0
    );

    setFormula(newValue);

    // Set cursor position after state update
    if (textarea) {
      setCursorPosition(textarea, newCursorPosition);
    }
  }, [formula, cursorPosition, disabled]);

  const handleTemplateApply = useCallback((template: FormulaTemplate) => {
    if (disabled) return;
    setFormula(template.formula);
    setShowTemplates(false);
  }, [disabled]);

  const handleCursorPositionChange = useCallback((position: number) => {
    setCursorPositionState(position);
  }, []);

  // Get first error for display
  const firstError = validationResult?.errors.find((e) => e.severity === "error");
  const firstWarning = validationResult?.errors.find((e) => e.severity === "warning");

  return (
    <div className={cn("space-y-4", className)}>
      {/* Available Fields */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">Available Fields</Label>
        <ScrollArea className="h-32 rounded-lg border bg-muted/30">
          <div className="p-3 space-y-3">
            {isLoadingFields ? (
              <div className="flex items-center justify-center py-4 text-sm text-muted-foreground">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading fields...
              </div>
            ) : fieldCategories.length === 0 ? (
              <div className="text-sm text-muted-foreground text-center py-4">
                No fields available
              </div>
            ) : (
              fieldCategories.map((category) => (
                <div key={category.label} className="space-y-1">
                  <div className="text-xs font-medium text-muted-foreground px-1">
                    {category.label}
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {category.fields.map((field) => (
                      <Button
                        key={field.key}
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => handleFieldInsert(field.key)}
                        disabled={disabled}
                        className="h-7 text-xs"
                        title={field.description || `Insert ${field.label}`}
                      >
                        {field.label}
                      </Button>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Operation Palette */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">Operations</Label>
        <div className="space-y-2">
          {/* Math Operations */}
          <div className="space-y-1">
            <div className="text-xs font-medium text-muted-foreground px-1">Math</div>
            <div className="flex flex-wrap gap-1">
              {MATH_OPERATIONS.map((op) => (
                <Button
                  key={op.value}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleOperationInsert(op)}
                  disabled={disabled}
                  className="h-7 text-xs font-mono"
                  title={op.description}
                >
                  {op.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Comparison Operations */}
          <div className="space-y-1">
            <div className="text-xs font-medium text-muted-foreground px-1">Comparison</div>
            <div className="flex flex-wrap gap-1">
              {COMPARISON_OPERATIONS.map((op) => (
                <Button
                  key={op.value}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleOperationInsert(op)}
                  disabled={disabled}
                  className="h-7 text-xs font-mono"
                  title={op.description}
                >
                  {op.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Logical Operations */}
          <div className="space-y-1">
            <div className="text-xs font-medium text-muted-foreground px-1">Logical</div>
            <div className="flex flex-wrap gap-1">
              {LOGICAL_OPERATIONS.map((op) => (
                <Button
                  key={op.value}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleOperationInsert(op)}
                  disabled={disabled}
                  className="h-7 text-xs"
                  title={op.description}
                >
                  {op.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Functions */}
          <div className="space-y-1">
            <div className="text-xs font-medium text-muted-foreground px-1">Functions</div>
            <div className="flex flex-wrap gap-1">
              {FUNCTION_OPERATIONS.map((op) => (
                <Button
                  key={op.value}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleOperationInsert(op)}
                  disabled={disabled}
                  className="h-7 text-xs font-mono"
                  title={op.description}
                >
                  {op.label}
                </Button>
              ))}
              {GROUP_OPERATIONS.map((op) => (
                <Button
                  key={op.value}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleOperationInsert(op)}
                  disabled={disabled}
                  className="h-7 text-xs font-mono"
                  title={op.description}
                >
                  {op.label}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Formula Editor */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="formula-input" className="text-sm font-medium">
            Formula
          </Label>
          {validationMutation.isPending && (
            <div className="flex items-center text-xs text-muted-foreground">
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              Validating...
            </div>
          )}
          {validationResult && !validationMutation.isPending && (
            <div className="flex items-center text-xs">
              {validationResult.valid ? (
                <div className="flex items-center text-green-600">
                  <CheckCircle2 className="mr-1 h-3 w-3" />
                  Valid
                </div>
              ) : (
                <div className="flex items-center text-red-600">
                  <AlertCircle className="mr-1 h-3 w-3" />
                  Invalid
                </div>
              )}
            </div>
          )}
        </div>

        <FormulaEditor
          ref={textareaRef}
          value={formula}
          onChange={setFormula}
          onCursorPositionChange={handleCursorPositionChange}
          error={firstError?.message}
          disabled={disabled}
          rows={4}
          ariaLabel="Formula input"
          ariaDescribedBy="formula-help"
        />

        <p id="formula-help" className="text-xs text-muted-foreground">
          Use field names, operators, and functions to build your formula. Click fields or operations above to insert them.
        </p>
      </div>

      {/* Validation Messages */}
      {firstWarning && !firstError && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription className="text-sm">
            {firstWarning.message}
            {firstWarning.suggestion && (
              <span className="block mt-1 text-muted-foreground">
                {firstWarning.suggestion}
              </span>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Live Preview */}
      {validationResult?.valid && validationResult.preview !== undefined && (
        <Alert>
          <AlertDescription className="text-sm">
            <div className="flex items-center justify-between">
              <span className="font-medium">Preview with sample data:</span>
              <span className="text-lg font-semibold">
                ${validationResult.preview.toFixed(2)}
              </span>
            </div>
            {validationResult.used_fields.length > 0 && (
              <div className="mt-2 text-xs text-muted-foreground">
                Using fields: {validationResult.used_fields.join(", ")}
              </div>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Formula Templates */}
      <div className="space-y-2">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setShowTemplates(!showTemplates)}
          disabled={disabled}
          className="w-full justify-between"
        >
          <span className="text-sm font-medium">Formula Templates</span>
          {showTemplates ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>

        {showTemplates && (
          <ScrollArea className="h-48 rounded-lg border bg-muted/30">
            <div className="p-3 space-y-2">
              {FORMULA_TEMPLATES.map((template) => (
                <button
                  key={template.name}
                  type="button"
                  onClick={() => handleTemplateApply(template)}
                  disabled={disabled}
                  className="w-full text-left p-2 rounded-md hover:bg-muted transition-colors focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">{template.name}</div>
                      <div className="text-xs text-muted-foreground mt-0.5">
                        {template.description}
                      </div>
                      <code className="block mt-1 text-xs font-mono bg-background/50 px-2 py-1 rounded">
                        {template.formula}
                      </code>
                    </div>
                    <span className="text-xs font-medium text-muted-foreground shrink-0">
                      {template.category}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </ScrollArea>
        )}
      </div>

      {/* Help Text */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription className="text-xs">
          <div className="space-y-1">
            <div>
              <strong>Examples:</strong>
            </div>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li><code className="text-xs">ram_gb * 2.5</code> - Simple multiplication</li>
              <li><code className="text-xs">cpu.cpu_mark_single / 1000 * 5.0</code> - Nested fields</li>
              <li><code className="text-xs">max(ram_gb * 2.5, 50)</code> - Minimum value enforcement</li>
              <li><code className="text-xs">ram_gb * 3.0 if ram_gb &gt;= 32 else ram_gb * 2.5</code> - Conditional</li>
            </ul>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  );
}
