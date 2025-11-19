"use client";

import { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Lock, Users, Globe } from "lucide-react";
import type { CollectionVisibility } from "@/types/collections";
import { useUpdateCollectionVisibility } from "@/hooks/use-collections";
import { cn } from "@/lib/utils";

interface VisibilityToggleProps {
  collectionId: number | string;
  currentVisibility: CollectionVisibility;
  onVisibilityChange?: (visibility: CollectionVisibility) => void;
  className?: string;
}

const visibilityOptions = [
  {
    value: "private" as CollectionVisibility,
    icon: Lock,
    label: "Private",
    description: "Only me",
    color: "text-muted-foreground",
  },
  {
    value: "unlisted" as CollectionVisibility,
    icon: Users,
    label: "Unlisted",
    description: "Anyone with link",
    color: "text-blue-600 dark:text-blue-400",
  },
  {
    value: "public" as CollectionVisibility,
    icon: Globe,
    label: "Public",
    description: "Everyone can discover",
    color: "text-green-600 dark:text-green-400",
  },
];

/**
 * Visibility Toggle Component
 *
 * Dropdown selector for collection visibility with warning modal
 * - Private: Only visible to owner
 * - Unlisted: Anyone with link can access
 * - Public: Discoverable by everyone (shows warning before switching)
 */
export function VisibilityToggle({
  collectionId,
  currentVisibility,
  onVisibilityChange,
  className,
}: VisibilityToggleProps) {
  const [pendingVisibility, setPendingVisibility] = useState<CollectionVisibility | null>(null);
  const [showPublicWarning, setShowPublicWarning] = useState(false);

  const updateMutation = useUpdateCollectionVisibility({
    collectionId,
    onSuccess: (collection) => {
      onVisibilityChange?.(collection.visibility);
      setPendingVisibility(null);
    },
  });

  const handleVisibilitySelect = (value: CollectionVisibility) => {
    // Show warning when switching to public
    if (value === "public" && currentVisibility !== "public") {
      setPendingVisibility(value);
      setShowPublicWarning(true);
      return;
    }

    // Otherwise update immediately
    updateMutation.mutate({ visibility: value });
  };

  const handleConfirmPublic = () => {
    if (pendingVisibility) {
      updateMutation.mutate({ visibility: pendingVisibility });
    }
    setShowPublicWarning(false);
  };

  const handleCancelPublic = () => {
    setPendingVisibility(null);
    setShowPublicWarning(false);
  };

  const currentOption = visibilityOptions.find((opt) => opt.value === currentVisibility);

  return (
    <>
      <Select
        value={currentVisibility}
        onValueChange={handleVisibilitySelect}
        disabled={updateMutation.isPending}
      >
        <SelectTrigger
          className={cn("w-[180px]", className)}
          aria-label="Collection visibility"
        >
          <SelectValue>
            {currentOption && (
              <div className="flex items-center gap-2">
                <currentOption.icon
                  className={cn("w-4 h-4", currentOption.color)}
                  aria-hidden="true"
                />
                <span>{currentOption.label}</span>
              </div>
            )}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {visibilityOptions.map((option) => {
            const Icon = option.icon;
            return (
              <SelectItem key={option.value} value={option.value}>
                <div className="flex items-start gap-3 py-1">
                  <Icon
                    className={cn("w-4 h-4 mt-0.5 shrink-0", option.color)}
                    aria-hidden="true"
                  />
                  <div className="flex flex-col gap-0.5">
                    <span className="font-medium">{option.label}</span>
                    <span className="text-xs text-muted-foreground">
                      {option.description}
                    </span>
                  </div>
                </div>
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>

      {/* Public Warning Modal */}
      <AlertDialog open={showPublicWarning} onOpenChange={setShowPublicWarning}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Make collection public?</AlertDialogTitle>
            <AlertDialogDescription className="space-y-2">
              <p>
                This collection will be discoverable by everyone and appear in the public
                collection directory.
              </p>
              <p className="font-medium">
                Anyone will be able to view this collection and copy it to their workspace.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelPublic}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmPublic}
              className="bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800"
            >
              Make Public
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
