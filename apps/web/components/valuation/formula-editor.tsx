"use client";

import { forwardRef, useEffect, useState, useImperativeHandle, useRef } from "react";
import { Textarea } from "../ui/textarea";
import { cn } from "../../lib/utils";
import { validateFormulaBasic } from "../../lib/formula-utils";

export interface FormulaEditorProps {
  value: string;
  onChange: (value: string) => void;
  onCursorPositionChange?: (position: number) => void;
  error?: string;
  placeholder?: string;
  disabled?: boolean;
  rows?: number;
  className?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
}

export const FormulaEditor = forwardRef<HTMLTextAreaElement, FormulaEditorProps>(
  function FormulaEditor(
    {
      value,
      onChange,
      onCursorPositionChange,
      error,
      placeholder = "e.g., ram_gb * 2.5 + storage_gb * 0.1",
      disabled = false,
      rows = 4,
      className,
      ariaLabel = "Formula input",
      ariaDescribedBy,
    },
    ref
  ) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [localError, setLocalError] = useState<string | undefined>();

    // Expose textarea ref to parent
    useImperativeHandle(ref, () => textareaRef.current as HTMLTextAreaElement);

    // Expose textarea ref for cursor manipulation
    useEffect(() => {
      if (textareaRef.current && onCursorPositionChange) {
        const handleSelectionChange = () => {
          if (textareaRef.current) {
            onCursorPositionChange(textareaRef.current.selectionStart || 0);
          }
        };

        const textarea = textareaRef.current;
        textarea.addEventListener("click", handleSelectionChange);
        textarea.addEventListener("keyup", handleSelectionChange);

        return () => {
          textarea.removeEventListener("click", handleSelectionChange);
          textarea.removeEventListener("keyup", handleSelectionChange);
        };
      }
    }, [onCursorPositionChange]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    onChange(newValue);

    // Basic client-side validation
    if (newValue.trim()) {
      const validation = validateFormulaBasic(newValue);
      setLocalError(validation.valid ? undefined : validation.error);
    } else {
      setLocalError(undefined);
    }
  };

  // Use external error if provided, otherwise use local error
  const displayError = error || localError;

    return (
      <div className="space-y-1">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          placeholder={placeholder}
          disabled={disabled}
          rows={rows}
          className={cn(
            "font-mono text-sm",
            displayError && "border-red-500 focus-visible:ring-red-500",
            className
          )}
          aria-label={ariaLabel}
          aria-describedby={ariaDescribedBy}
          aria-invalid={!!displayError}
        />
        {displayError && (
          <p
            className="text-xs text-red-500"
            role="alert"
            aria-live="polite"
          >
            {displayError}
          </p>
        )}
      </div>
    );
  }
);
