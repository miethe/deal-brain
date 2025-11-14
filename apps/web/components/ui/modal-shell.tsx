"use client";

import { ReactNode } from "react";

import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "./dialog";
import { cn } from "../../lib/utils";

const MODAL_SIZES = {
  sm: "max-w-sm",   // 400px - confirmations
  md: "max-w-2xl",  // 640px - standard forms (default)
  lg: "max-w-4xl",  // 800px - complex forms
  xl: "max-w-6xl",  // 1200px - data tables
  full: "max-w-[90vw]" // 90% viewport
} as const;

interface ModalContentProps {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  size?: keyof typeof MODAL_SIZES;
  preventClose?: boolean;
  hideClose?: boolean;
}

/**
 * ModalContent - Use inside an existing Dialog context (e.g., with DialogTrigger).
 * This provides modal structure without wrapping in Dialog.
 */
export function ModalContent({
  title,
  description,
  children,
  footer,
  className,
  size = "md",
  preventClose = false,
  hideClose = false,
}: ModalContentProps) {
  const sizeClass = MODAL_SIZES[size];

  const handleInteractOutside = (e: Event) => {
    if (preventClose) {
      e.preventDefault();
    }
  };

  const handleEscapeKeyDown = (e: KeyboardEvent) => {
    if (preventClose) {
      e.preventDefault();
    }
  };

  return (
    <DialogContent
      className={cn(sizeClass, "gap-6", className)}
      onInteractOutside={handleInteractOutside}
      onEscapeKeyDown={handleEscapeKeyDown}
      hideClose={hideClose || preventClose}
    >
      <DialogHeader>
        <DialogTitle className="text-xl font-semibold tracking-tight">{title}</DialogTitle>
        {description && <DialogDescription className="mt-1.5">{description}</DialogDescription>}
      </DialogHeader>
      <div className="max-h-[70vh] overflow-y-auto px-1">{children}</div>
      {footer && (
        <DialogFooter className="mt-2 flex justify-between gap-3 border-t pt-4">
          {footer}
        </DialogFooter>
      )}
    </DialogContent>
  );
}

interface ModalShellProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  size?: keyof typeof MODAL_SIZES;
  preventClose?: boolean;
  hideClose?: boolean;
}

/**
 * ModalShell - Complete modal with Dialog wrapper.
 * Use when you control the open state directly.
 */
export function ModalShell({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  className,
  size = "md",
  preventClose = false,
  hideClose = false,
}: ModalShellProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <ModalContent
        title={title}
        description={description}
        footer={footer}
        className={className}
        size={size}
        preventClose={preventClose}
        hideClose={hideClose}
      >
        {children}
      </ModalContent>
    </Dialog>
  );
}
