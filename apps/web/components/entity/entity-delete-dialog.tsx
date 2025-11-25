"use client";

import { useState, useEffect } from "react";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { EntityType } from "@/lib/schemas/entity-schemas";

// ============================================================================
// Types
// ============================================================================

interface EntityDeleteDialogProps {
  /** Type of entity being deleted (e.g., "cpu", "gpu") */
  entityType: EntityType;
  /** Unique identifier for the entity */
  entityId: number;
  /** Display name of the entity (used for confirmation matching) */
  entityName: string;
  /** Number of listings using this entity (triggers confirmation requirement) */
  usedInCount: number;
  /** Callback when deletion is confirmed */
  onConfirm: () => void | Promise<void>;
  /** Callback when dialog is cancelled */
  onCancel: () => void;
  /** Controls dialog visibility */
  isOpen: boolean;
}

// ============================================================================
// Helper Functions
// ============================================================================

const entityTypeLabels: Record<EntityType, string> = {
  cpu: "CPU",
  gpu: "GPU",
  "ram-spec": "RAM Specification",
  "storage-profile": "Storage Profile",
  "ports-profile": "Ports Profile",
  profile: "Profile",
};

/**
 * Validates if the confirmation input matches the entity name (case-insensitive)
 */
function validateConfirmation(input: string, entityName: string): boolean {
  return input.trim().toLowerCase() === entityName.trim().toLowerCase();
}

// ============================================================================
// Main Component
// ============================================================================

export function EntityDeleteDialog({
  entityType,
  entityId,
  entityName,
  usedInCount,
  onConfirm,
  onCancel,
  isOpen,
}: EntityDeleteDialogProps) {
  const [confirmationInput, setConfirmationInput] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  // Reset confirmation input when dialog opens/closes
  useEffect(() => {
    if (!isOpen) {
      setConfirmationInput("");
      setIsDeleting(false);
    }
  }, [isOpen]);

  const requiresConfirmation = usedInCount > 0;
  const isConfirmationValid = !requiresConfirmation || validateConfirmation(confirmationInput, entityName);

  const handleConfirm = async () => {
    if (!isConfirmationValid) return;

    setIsDeleting(true);
    try {
      await onConfirm();
      // Parent component handles success notification and dialog closing
    } catch (error) {
      console.error("Delete confirmation error:", error);
      // Parent component handles error notification
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCancel = () => {
    if (isDeleting) return;
    onCancel();
  };

  const entityLabel = entityTypeLabels[entityType];

  return (
    <AlertDialog open={isOpen} onOpenChange={(open) => !open && !isDeleting && handleCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            Delete {entityLabel}
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-3">
            <p>
              Are you sure you want to delete <strong className="font-semibold text-foreground">{entityName}</strong>?
            </p>

            {usedInCount > 0 && (
              <div className="space-y-2">
                <Badge
                  variant="destructive"
                  className="inline-flex"
                  aria-label={`Used in ${usedInCount} listing${usedInCount === 1 ? "" : "s"}`}
                >
                  Used in {usedInCount} Listing{usedInCount === 1 ? "" : "s"}
                </Badge>
                <p className="text-sm text-destructive">
                  This {entityLabel.toLowerCase()} is currently used in {usedInCount} listing{usedInCount === 1 ? "" : "s"}.
                  Deleting it may affect those listings.
                </p>
              </div>
            )}

            <p className="text-sm">
              This action cannot be undone.
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>

        {requiresConfirmation && (
          <div className="space-y-2">
            <Label htmlFor="confirmation-input">
              Type <strong>{entityName}</strong> to confirm deletion
            </Label>
            <Input
              id="confirmation-input"
              value={confirmationInput}
              onChange={(e) => setConfirmationInput(e.target.value)}
              placeholder={`Type "${entityName}" to confirm`}
              disabled={isDeleting}
              aria-invalid={confirmationInput.length > 0 && !isConfirmationValid}
              aria-describedby="confirmation-help"
              className={cn(
                confirmationInput.length > 0 && !isConfirmationValid && "border-destructive"
              )}
              autoFocus
            />
            <p id="confirmation-help" className="text-xs text-muted-foreground">
              Confirmation is required because this {entityLabel.toLowerCase()} is currently in use.
            </p>
          </div>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleCancel} disabled={isDeleting}>
            Cancel
          </AlertDialogCancel>
          <Button
            variant="destructive"
            onClick={handleConfirm}
            disabled={!isConfirmationValid || isDeleting}
            aria-label={`Confirm deletion of ${entityName}`}
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
