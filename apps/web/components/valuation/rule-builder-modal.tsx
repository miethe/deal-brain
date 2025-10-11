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
import { useToast } from "../ui/use-toast";

import { createRule, updateRule, type Rule, type Condition, type Action } from "../../lib/api/rules";
import { track } from "../../lib/analytics";
import { ConditionGroup } from "./condition-group";
import { ActionBuilder } from "./action-builder";

interface RuleBuilderModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groupId: number | null;
  rule?: Rule | null; // For editing
  onSuccess: () => void;
}

export function RuleBuilderModal({ open, onOpenChange, groupId, rule, onSuccess }: RuleBuilderModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState(100);
  const [conditions, setConditions] = useState<Condition[]>([]);
  const [actions, setActions] = useState<Action[]>([]);

  const { toast } = useToast();
  const queryClient = useQueryClient();

  const isEditing = !!rule;

  // Pre-fill form when editing
  useEffect(() => {
    if (rule) {
      setName(rule.name);
      setDescription(rule.description || "");
      setPriority(rule.priority);
      setConditions(rule.conditions || []);
      setActions(rule.actions || []);
    } else {
      resetForm();
    }
  }, [rule, open]);

  const saveMutation = useMutation({
    mutationFn: (): Promise<Rule> => {
      if (isEditing && rule) {
        return updateRule(rule.id, {
          name,
          description,
          priority,
          conditions,
          actions,
        });
      } else {
        if (!groupId) throw new Error("No group selected");
        return createRule({
          group_id: groupId,
          name,
          description,
          priority,
          conditions,
          actions,
        });
      }
    },
    onSuccess: (savedRule) => {
      toast({
        title: isEditing ? "Rule updated" : "Rule created",
        description: `The rule has been ${isEditing ? "updated" : "created"} successfully`,
      });
      track(isEditing ? "valuation_rule.updated" : "valuation_rule.created", {
        rule_id: savedRule.id,
        group_id: savedRule.group_id,
        conditions: savedRule.conditions?.length ?? 0,
        actions: savedRule.actions?.length ?? 0,
      });
      resetForm();
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
    setPriority(100);
    setConditions([]);
    setActions([]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveMutation.mutate();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit" : "Create New"} Rule</DialogTitle>
          <DialogDescription>
            {isEditing ? "Update" : "Define"} conditions and actions for this valuation rule
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 py-4">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info */}
            <div className="space-y-4">
            <div>
              <Label htmlFor="name">Rule Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., High-End CPU Premium"
                required
              />
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what this rule does..."
                rows={2}
              />
            </div>

            <div>
              <Label htmlFor="priority">Priority</Label>
              <Input
                id="priority"
                type="number"
                value={priority}
                onChange={(e) => setPriority(parseInt(e.target.value))}
                min={1}
                max={1000}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Lower numbers = higher priority (evaluated first)
              </p>
            </div>
          </div>

          {/* Conditions */}
          <div>
            <div className="mb-3 flex items-center justify-between">
              <Label>Conditions</Label>
            </div>

            {conditions.length === 0 ? (
              <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                No conditions yet. Use the buttons below to add conditions or groups.
              </div>
            ) : null}

            <ConditionGroup
              conditions={conditions}
              onConditionsChange={setConditions}
            />
          </div>

          {/* Actions */}
          <div>
            <div className="mb-3 flex items-center justify-between">
              <Label>Actions</Label>
            </div>

            {actions.length === 0 ? (
              <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                No actions yet. Use the button below to add an action.
              </div>
            ) : null}

            <ActionBuilder
              actions={actions}
              onActionsChange={setActions}
            />
          </div>

            <DialogFooter className="px-6 py-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!name || (!groupId && !isEditing) || saveMutation.isPending}>
                {saveMutation.isPending
                  ? (isEditing ? "Updating..." : "Creating...")
                  : (isEditing ? "Update Rule" : "Create Rule")}
              </Button>
            </DialogFooter>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
