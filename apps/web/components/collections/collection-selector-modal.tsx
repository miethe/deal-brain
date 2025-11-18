"use client";

import { useState, useEffect } from "react";
import { ArrowLeft, Folder, Loader2, Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useCollections, useCreateCollection } from "@/hooks/use-collections";
import { useAddToCollection } from "@/hooks/use-add-to-collection";
import { cn } from "@/lib/utils";
import type { Collection, CollectionVisibility } from "@/types/collections";

interface CollectionSelectorModalProps {
  listingId: number;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (collectionId: number) => void;
}

type ViewMode = "list" | "create";

export function CollectionSelectorModal({
  listingId,
  isOpen,
  onClose,
  onSuccess,
}: CollectionSelectorModalProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null);

  // Form state for creating new collection
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch recent collections (limit to 5 for quick selection)
  const {
    data: collectionsData,
    isLoading: isLoadingCollections,
  } = useCollections({ limit: 5 });

  // Track if we're currently adding to collection to prevent double-adds
  const [isAdding, setIsAdding] = useState(false);

  // Create collection mutation
  const createMutation = useCreateCollection({
    onSuccess: (newCollection) => {
      // After creating, immediately add the listing to it
      setSelectedCollectionId(newCollection.id);
    },
  });

  // Add to collection mutation - dynamically created when collection is selected
  const selectedCollection = collectionsData?.collections.find(
    (c) => c.id === selectedCollectionId
  );

  const addMutation = useAddToCollection({
    collectionId: selectedCollectionId || 0,
    collectionName: selectedCollection?.name,
    onSuccess: () => {
      // Auto-close after brief delay to show toast
      setTimeout(() => {
        handleClose();
        onSuccess?.(selectedCollectionId!);
      }, 500);
      setIsAdding(false);
    },
  });

  // When collection is selected (either existing or newly created), add the listing
  useEffect(() => {
    if (selectedCollectionId && !isAdding && !addMutation.isPending) {
      setIsAdding(true);
      addMutation.mutate({
        listing_id: listingId,
        status: "undecided",
      });
    }
  }, [selectedCollectionId, listingId, isAdding, addMutation]);

  // Reset state when modal closes
  const handleClose = () => {
    setViewMode("list");
    setSelectedCollectionId(null);
    setName("");
    setDescription("");
    setErrors({});
    onClose();
  };

  // Handle collection selection from list
  const handleSelectCollection = (collection: Collection) => {
    setSelectedCollectionId(collection.id);
  };

  // Handle create mode toggle
  const handleShowCreateForm = () => {
    setViewMode("create");
  };

  const handleBackToList = () => {
    setViewMode("list");
    setName("");
    setDescription("");
    setErrors({});
  };

  // Validate create form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    const trimmedName = name.trim();
    if (!trimmedName) {
      newErrors.name = "Name is required";
    } else if (trimmedName.length < 1 || trimmedName.length > 100) {
      newErrors.name = "Name must be between 1 and 100 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle create and add
  const handleCreateAndAdd = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const payload = {
      name: name.trim(),
      description: description.trim() || undefined,
      visibility: "private" as CollectionVisibility,
    };

    createMutation.mutate(payload);
  };

  // Auto-focus name field when switching to create mode
  useEffect(() => {
    if (viewMode === "create" && isOpen) {
      // Small delay to ensure dialog animation completes
      const timer = setTimeout(() => {
        document.getElementById("new-collection-name")?.focus();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [viewMode, isOpen]);

  const collections = collectionsData?.collections || [];
  const isCreating = createMutation.isPending;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="sm:max-w-[450px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {viewMode === "create" && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleBackToList}
                disabled={isCreating}
                className="h-8 w-8 p-0 -ml-2"
                aria-label="Back to collections list"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
            )}
            {viewMode === "list" ? "Add to Collection" : "Create New Collection"}
          </DialogTitle>
        </DialogHeader>

        {/* List View - Show recent collections */}
        {viewMode === "list" && (
          <div className="space-y-4">
            {isLoadingCollections ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : collections.length === 0 ? (
              <div className="text-center py-8 space-y-3">
                <Folder className="h-12 w-12 mx-auto text-muted-foreground opacity-50" />
                <div>
                  <p className="text-sm font-medium">No collections yet</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Create your first collection to get started
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground mb-3">
                  Select a collection to add this listing
                </p>
                <ScrollArea className="max-h-[280px]">
                  <div className="space-y-2 pr-3">
                    {collections.map((collection) => (
                      <button
                        key={collection.id}
                        onClick={() => handleSelectCollection(collection)}
                        disabled={isAdding}
                        className={cn(
                          "w-full p-3 rounded-lg border border-border bg-background",
                          "hover:bg-muted hover:border-muted-foreground/20 transition-colors",
                          "text-left focus-visible:outline-none focus-visible:ring-2",
                          "focus-visible:ring-ring focus-visible:ring-offset-2",
                          "disabled:opacity-50 disabled:cursor-not-allowed",
                          isAdding && selectedCollectionId === collection.id && "bg-muted"
                        )}
                        aria-label={`Add to ${collection.name}`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-sm truncate">
                              {collection.name}
                            </div>
                            {collection.description && (
                              <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                {collection.description}
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <span className="text-xs text-muted-foreground">
                              ({collection.item_count})
                            </span>
                            {isAdding && selectedCollectionId === collection.id && (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            )}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}

            <div className="pt-2 border-t">
              <Button
                variant="outline"
                onClick={handleShowCreateForm}
                disabled={isAdding}
                className="w-full"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create New Collection
              </Button>
            </div>

            <DialogFooter>
              <Button
                variant="ghost"
                onClick={handleClose}
                disabled={isAdding}
              >
                Cancel
              </Button>
            </DialogFooter>
          </div>
        )}

        {/* Create View - Inline form */}
        {viewMode === "create" && (
          <form onSubmit={handleCreateAndAdd}>
            <div className="space-y-4">
              {/* Name field */}
              <div className="space-y-2">
                <Label htmlFor="new-collection-name">
                  Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="new-collection-name"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (errors.name) {
                      setErrors((prev) => {
                        const next = { ...prev };
                        delete next.name;
                        return next;
                      });
                    }
                  }}
                  placeholder="e.g., Gaming Builds"
                  maxLength={100}
                  disabled={isCreating}
                  aria-invalid={!!errors.name}
                  aria-describedby={errors.name ? "name-error" : undefined}
                />
                {errors.name && (
                  <p id="name-error" className="text-xs text-destructive" role="alert">
                    {errors.name}
                  </p>
                )}
              </div>

              {/* Description field */}
              <div className="space-y-2">
                <Label htmlFor="new-collection-description">
                  Description <span className="text-muted-foreground text-xs">(optional)</span>
                </Label>
                <Textarea
                  id="new-collection-description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Brief description of this collection..."
                  rows={3}
                  disabled={isCreating}
                />
              </div>
            </div>

            <DialogFooter className="mt-6">
              <Button
                type="button"
                variant="outline"
                onClick={handleBackToList}
                disabled={isCreating}
              >
                Back
              </Button>
              <Button
                type="submit"
                disabled={isCreating}
              >
                {isCreating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create & Add"
                )}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
