"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateCollection } from "@/hooks/use-collections";
import type { CollectionVisibility } from "@/types/collections";

interface NewCollectionFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function NewCollectionForm({ open, onOpenChange }: NewCollectionFormProps) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState<CollectionVisibility>("private");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const createMutation = useCreateCollection({
    onSuccess: (collection) => {
      // Reset form
      setName("");
      setDescription("");
      setVisibility("private");
      setErrors({});

      // Close modal
      onOpenChange(false);

      // Navigate to collection workspace
      router.push(`/collections/${collection.id}`);
    },
  });

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Name validation
    const trimmedName = name.trim();
    if (!trimmedName) {
      newErrors.name = "Name is required";
    } else if (trimmedName.length < 1 || trimmedName.length > 100) {
      newErrors.name = "Name must be between 1 and 100 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const payload = {
      name: name.trim(),
      description: description.trim() || undefined,
      visibility,
    };

    createMutation.mutate(payload);
  };

  const handleCancel = () => {
    // Reset form
    setName("");
    setDescription("");
    setVisibility("private");
    setErrors({});

    // Close modal
    onOpenChange(false);
  };

  // Auto-focus name field when modal opens
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      handleCancel();
    } else {
      onOpenChange(newOpen);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create new collection</DialogTitle>
          <DialogDescription>
            Organize and curate your listings with collections.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* Name field */}
            <div className="space-y-2">
              <Label htmlFor="collection-name">
                Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="collection-name"
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
                placeholder="e.g., High-Performance Deals"
                maxLength={100}
                autoFocus
                disabled={createMutation.isPending}
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
              <Label htmlFor="collection-description">Description</Label>
              <Textarea
                id="collection-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description for this collection..."
                rows={3}
                disabled={createMutation.isPending}
              />
            </div>

            {/* Visibility field */}
            <div className="space-y-2">
              <Label htmlFor="collection-visibility">Visibility</Label>
              <Select
                value={visibility}
                onValueChange={(value) => setVisibility(value as CollectionVisibility)}
                disabled={createMutation.isPending}
              >
                <SelectTrigger id="collection-visibility">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="private">Private - Only you can see</SelectItem>
                  <SelectItem value="shared">Shared - Shared with specific users</SelectItem>
                  <SelectItem value="public">Public - Anyone can view</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create collection"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
