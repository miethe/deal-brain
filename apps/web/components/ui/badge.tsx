import type { HTMLAttributes } from "react";

import { cn } from "../../lib/utils";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "outline" | "destructive";
}

const variantClasses = {
  default: "bg-primary text-primary-foreground",
  secondary: "bg-secondary text-secondary-foreground",
  outline: "border border-input bg-background",
  destructive: "bg-destructive text-destructive-foreground",
};

export function Badge({ className, variant = "secondary", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variantClasses[variant],
        className
      )}
      {...props}
    />
  );
}
