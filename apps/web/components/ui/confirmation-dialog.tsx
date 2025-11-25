"use client";

import * as React from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./alert-dialog";

/**
 * Props for the ConfirmationDialog component
 */
export interface ConfirmationDialogProps {
  /** Dialog open state */
  open: boolean;
  /** State change handler */
  onOpenChange: (open: boolean) => void;
  /** Dialog title */
  title: string;
  /** Dialog description/warning text */
  description: string;
  /** Confirm button text (default: "Confirm") */
  confirmText?: string;
  /** Cancel button text (default: "Cancel") */
  cancelText?: string;
  /** Confirm action handler */
  onConfirm: () => void;
  /** Cancel action handler (optional) */
  onCancel?: () => void;
  /** Visual variant (default: "default") */
  variant?: "default" | "destructive";
  /** Loading state for async operations */
  isLoading?: boolean;
}

/**
 * ConfirmationDialog - Reusable, accessible confirmation dialog for destructive actions
 *
 * Features:
 * - WCAG 2.1 AA compliant
 * - Keyboard navigation (Tab, Shift+Tab, Enter, Esc)
 * - Focus trap and restoration
 * - Loading state support
 * - Two variants: default and destructive
 *
 * @example
 * ```tsx
 * const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
 *
 * <ConfirmationDialog
 *   open={deleteConfirmOpen}
 *   onOpenChange={setDeleteConfirmOpen}
 *   title="Delete Listing?"
 *   description="This action cannot be undone. The listing and all related data will be permanently deleted."
 *   confirmText="Delete"
 *   cancelText="Cancel"
 *   variant="destructive"
 *   onConfirm={() => {
 *     deleteListing(listingId);
 *   }}
 *   isLoading={isDeleting}
 * />
 * ```
 */
export function ConfirmationDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmText = "Confirm",
  cancelText = "Cancel",
  variant = "default",
  onConfirm,
  onCancel,
  isLoading = false,
}: ConfirmationDialogProps) {
  const handleConfirm = () => {
    if (!isLoading) {
      onConfirm();
      // Don't auto-close - let the caller control this
      // This allows showing loading state during async operations
    }
  };

  const handleCancel = () => {
    if (!isLoading) {
      onCancel?.();
      onOpenChange(false);
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    // Prevent closing during loading
    if (!isLoading) {
      onOpenChange(newOpen);
      if (!newOpen) {
        onCancel?.();
      }
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={handleOpenChange}>
      <AlertDialogContent aria-busy={isLoading}>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleCancel} disabled={isLoading}>
            {cancelText}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={isLoading}
            className={
              variant === "destructive"
                ? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
                : ""
            }
          >
            {isLoading ? "Loading..." : confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

/**
 * Hook to use confirmation dialog imperatively
 *
 * @example
 * ```tsx
 * const { confirm, dialog } = useConfirmation();
 *
 * const handleDelete = async () => {
 *   const confirmed = await confirm({
 *     title: "Delete Item?",
 *     description: "This action cannot be undone.",
 *     variant: "destructive",
 *   });
 *
 *   if (confirmed) {
 *     await deleteItem();
 *   }
 * };
 *
 * return (
 *   <>
 *     <button onClick={handleDelete}>Delete</button>
 *     {dialog}
 *   </>
 * );
 * ```
 */
export function useConfirmation() {
  const [config, setConfig] = React.useState<{
    open: boolean;
    title: string;
    description: string;
    confirmText?: string;
    cancelText?: string;
    variant?: "default" | "destructive";
    isLoading?: boolean;
    onConfirm: () => void;
    onCancel?: () => void;
  }>({
    open: false,
    title: "",
    description: "",
    onConfirm: () => {},
  });

  const confirm = React.useCallback(
    (
      options: Omit<typeof config, "open" | "onConfirm" | "onCancel"> & {
        onConfirm?: () => void | Promise<void>;
        onCancel?: () => void;
      }
    ) => {
      return new Promise<boolean>((resolve) => {
        setConfig({
          ...options,
          open: true,
          onConfirm: async () => {
            if (options.onConfirm) {
              await options.onConfirm();
            }
            setConfig((prev) => ({ ...prev, open: false }));
            resolve(true);
          },
          onCancel: () => {
            options.onCancel?.();
            setConfig((prev) => ({ ...prev, open: false }));
            resolve(false);
          },
        });
      });
    },
    []
  );

  const dialog = (
    <ConfirmationDialog
      {...config}
      onOpenChange={(open) => {
        if (!open) {
          config.onCancel?.();
          setConfig((prev) => ({ ...prev, open: false }));
        }
      }}
    />
  );

  return { confirm, dialog };
}
