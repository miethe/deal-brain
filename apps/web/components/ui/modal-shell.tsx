"use client";

import { ReactNode } from "react";
import { X } from "lucide-react";

import { DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogClose } from "./dialog";
import { cn } from "../../lib/utils";
import { Button } from "./button";

const MODAL_SIZES = {
  sm: "max-w-sm",   // 400px - confirmations
  md: "max-w-2xl",  // 640px - standard forms (default)
  lg: "max-w-4xl",  // 800px - complex forms
  xl: "max-w-6xl",  // 1200px - data tables
  full: "max-w-[90vw]" // 90% viewport
} as const;

interface ModalShellProps {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  size?: keyof typeof MODAL_SIZES;
  onClose?: () => void;
  preventClose?: boolean;
  showCloseButton?: boolean;
}

export function ModalShell({
  title,
  description,
  children,
  footer,
  className,
  size = "md",
  onClose,
  preventClose = false,
  showCloseButton = true,
}: ModalShellProps) {
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
      className={cn(sizeClass, "gap-6 p-6 shadow-2xl sm:px-8", className)}
      onInteractOutside={handleInteractOutside}
      onEscapeKeyDown={handleEscapeKeyDown}
    >
      <DialogHeader className="space-y-1 text-left">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <DialogTitle className="text-xl font-semibold tracking-tight">{title}</DialogTitle>
            {description ? <DialogDescription className="mt-1.5">{description}</DialogDescription> : null}
          </div>
          {showCloseButton && !preventClose && (
            <DialogClose asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 -mr-2 -mt-1"
                onClick={onClose}
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Close</span>
              </Button>
            </DialogClose>
          )}
        </div>
      </DialogHeader>
      <div className="max-h-[70vh] overflow-y-auto pr-1">{children}</div>
      {footer ? (
        <DialogFooter className="sticky bottom-0 flex justify-between gap-3 border-t bg-background/95 px-0 pt-4">
          {footer}
        </DialogFooter>
      ) : null}
    </DialogContent>
  );
}
