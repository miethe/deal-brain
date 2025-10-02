"use client";

import * as React from "react";
import { z } from "zod";
import { Input } from "../ui/input";
import { cn } from "../../lib/utils";

interface ValidatedInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  validation?: z.ZodType<any>;
  onValidChange?: (value: any) => void;
  error?: string;
}

export const ValidatedInput = React.forwardRef<HTMLInputElement, ValidatedInputProps>(
  ({ validation, onValidChange, error, className, onChange, ...props }, ref) => {
    const [localError, setLocalError] = React.useState<string | undefined>(error);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;

      // Call original onChange
      onChange?.(e);

      // Validate if validation schema provided
      if (validation) {
        try {
          const validated = validation.parse(value);
          setLocalError(undefined);
          onValidChange?.(validated);
        } catch (err) {
          if (err instanceof z.ZodError) {
            setLocalError(err.errors[0]?.message);
          }
        }
      } else {
        onValidChange?.(value);
      }
    };

    React.useEffect(() => {
      setLocalError(error);
    }, [error]);

    return (
      <div className="space-y-1">
        <Input
          ref={ref}
          className={cn(localError && "border-destructive", className)}
          onChange={handleChange}
          {...props}
        />
        {localError && (
          <p className="text-xs text-destructive" role="alert">
            {localError}
          </p>
        )}
      </div>
    );
  }
);

ValidatedInput.displayName = "ValidatedInput";
