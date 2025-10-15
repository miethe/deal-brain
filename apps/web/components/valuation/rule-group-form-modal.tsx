"use client";

import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { useToast } from "../ui/use-toast";

import { Checkbox } from "../ui/checkbox";

import { createRuleGroup, type RuleGroup, updateRuleGroup } from "../../lib/api/rules";

interface RuleGroupFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  rulesetId: number;
  ruleGroup?: RuleGroup | null; // For editing
  onSuccess: () => void;
}

const CATEGORIES = [
  { value: "cpu", label: "CPU" },
  { value: "gpu", label: "GPU" },
  { value: "ram", label: "RAM" },
  { value: "storage", label: "Storage" },
  { value: "condition", label: "Condition" },
  { value: "market", label: "Market" },
  { value: "custom", label: "Custom" },
];

export function RuleGroupFormModal({
  open,
  onOpenChange,
  rulesetId,
  ruleGroup,
  onSuccess,
}: RuleGroupFormModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("custom");
  const [displayOrder, setDisplayOrder] = useState(100);
  const [weight, setWeight] = useState(1.0);
  const [isActive, setIsActive] = useState(true);

  const { toast } = useToast();
  const queryClient = useQueryClient();

  const isEditing = !!ruleGroup;

  // Pre-fill form when editing
  useEffect(() => {
    if (ruleGroup) {
      setName(ruleGroup.name);
      setDescription(ruleGroup.description || "");
      setCategory(ruleGroup.category);
      setDisplayOrder(ruleGroup.display_order);
      setWeight(ruleGroup.weight);
      setIsActive(ruleGroup.is_active);
    } else {
      resetForm();
    }
  }, [ruleGroup, open]);

  const saveMutation = useMutation({
    mutationFn: () => {
      if (isEditing && ruleGroup) {
        return updateRuleGroup(ruleGroup.id, {
          name,
          description,
          category,
          display_order: displayOrder,
          weight,
          is_active: isActive,
        });
      }
      return createRuleGroup({
        ruleset_id: rulesetId,
        name,
        description,
        category,
        display_order: displayOrder,
        weight,
        is_active: isActive,
      });
    },
    onSuccess: async () => {
      toast({
        title: isEditing ? "Rule group updated" : "Rule group created",
        description: isEditing
          ? "The rule group has been updated successfully"
          : "The rule group has been created successfully",
      });
      resetForm();

      // Invalidate and refetch queries before closing the modal
      await queryClient.invalidateQueries({ queryKey: ["ruleset", rulesetId] });
      await queryClient.invalidateQueries({ queryKey: ["rulesets"] });

      // Wait a brief moment for the refetch to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      // Now close the modal and call onSuccess
      onOpenChange(false);
      onSuccess();
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const resetForm = () => {
    setName("");
    setDescription("");
    setCategory("custom");
    setDisplayOrder(100);
    setWeight(1.0);
    setIsActive(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveMutation.mutate();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit" : "Create"} Rule Group</DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Update the rule group details"
              : "Create a new group to organize related rules"}
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 py-4">
          <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Group Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., High Performance CPUs"
              required
            />
          </div>

          <div>
            <Label htmlFor="category">Category</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger id="category">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe this rule group..."
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="displayOrder">Display Order</Label>
              <Input
                id="displayOrder"
                type="number"
                value={displayOrder}
                onChange={(e) => setDisplayOrder(parseInt(e.target.value) || 100)}
                min={1}
                max={1000}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Lower numbers appear first
              </p>
            </div>

            <div>
              <Label htmlFor="weight">Weight</Label>
              <Input
                id="weight"
                type="number"
                step="0.1"
                value={weight}
                onChange={(e) => setWeight(parseFloat(e.target.value) || 1.0)}
                min={0}
                max={10}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Importance multiplier
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Checkbox
              id="isActive"
              checked={isActive}
              onCheckedChange={(checked) => setIsActive(checked === true)}
            />
            <Label htmlFor="isActive" className="cursor-pointer select-none">
              Active
            </Label>
          </div>

            <DialogFooter className="px-6 py-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!name || saveMutation.isPending}>
                {saveMutation.isPending
                  ? isEditing
                    ? "Saving..."
                    : "Creating..."
                  : isEditing
                  ? "Update Group"
                  : "Create Group"}
              </Button>
            </DialogFooter>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
