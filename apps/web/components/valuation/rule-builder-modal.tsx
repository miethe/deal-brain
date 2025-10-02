"use client";

import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";

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
import { Badge } from "../ui/badge";
import { useToast } from "../ui/use-toast";

import { createRule, updateRule, type Rule, type Condition, type Action } from "../../lib/api/rules";

interface RuleBuilderModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groupId: number | null;
  rule?: Rule | null; // For editing
  onSuccess: () => void;
}

const OPERATORS = [
  { value: "equals", label: "Equals" },
  { value: "not_equals", label: "Not Equals" },
  { value: "greater_than", label: "Greater Than" },
  { value: "less_than", label: "Less Than" },
  { value: "gte", label: "Greater Than or Equal" },
  { value: "lte", label: "Less Than or Equal" },
  { value: "contains", label: "Contains" },
  { value: "in", label: "In List" },
];

const ACTION_TYPES = [
  { value: "fixed_value", label: "Fixed Value" },
  { value: "per_unit", label: "Per Unit" },
  { value: "benchmark_based", label: "Benchmark Based" },
  { value: "multiplier", label: "Multiplier" },
  { value: "additive", label: "Additive" },
  { value: "formula", label: "Formula" },
];

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
    mutationFn: () => {
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
    onSuccess: () => {
      toast({
        title: isEditing ? "Rule updated" : "Rule created",
        description: `The rule has been ${isEditing ? "updated" : "created"} successfully`,
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

  const addCondition = () => {
    setConditions([
      ...conditions,
      {
        field_name: "",
        field_type: "string",
        operator: "equals",
        value: "",
      },
    ]);
  };

  const updateCondition = (index: number, updates: Partial<Condition>) => {
    const newConditions = [...conditions];
    newConditions[index] = { ...newConditions[index], ...updates };
    setConditions(newConditions);
  };

  const removeCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const addAction = () => {
    setActions([
      ...actions,
      {
        action_type: "fixed_value",
        value_usd: 0,
      },
    ]);
  };

  const updateAction = (index: number, updates: Partial<Action>) => {
    const newActions = [...actions];
    newActions[index] = { ...newActions[index], ...updates };
    setActions(newActions);
  };

  const removeAction = (index: number) => {
    setActions(actions.filter((_, i) => i !== index));
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
              <Button type="button" variant="outline" size="sm" onClick={addCondition}>
                <Plus className="mr-2 h-4 w-4" />
                Add Condition
              </Button>
            </div>

            {conditions.length === 0 ? (
              <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                No conditions yet. Add a condition to specify when this rule applies.
              </div>
            ) : (
              <div className="space-y-3">
                {conditions.map((condition, index) => (
                  <div key={index} className="flex gap-2 rounded-lg border p-3">
                    <div className="flex-1 space-y-2">
                      <Input
                        placeholder="Field name (e.g., cpu.cpu_mark_multi)"
                        value={condition.field_name}
                        onChange={(e) =>
                          updateCondition(index, { field_name: e.target.value })
                        }
                      />
                      <div className="grid grid-cols-2 gap-2">
                        <Select
                          value={condition.operator}
                          onValueChange={(value) =>
                            updateCondition(index, { operator: value })
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {OPERATORS.map((op) => (
                              <SelectItem key={op.value} value={op.value}>
                                {op.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Input
                          placeholder="Value"
                          value={condition.value}
                          onChange={(e) =>
                            updateCondition(index, { value: e.target.value })
                          }
                        />
                      </div>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeCondition(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div>
            <div className="mb-3 flex items-center justify-between">
              <Label>Actions</Label>
              <Button type="button" variant="outline" size="sm" onClick={addAction}>
                <Plus className="mr-2 h-4 w-4" />
                Add Action
              </Button>
            </div>

            {actions.length === 0 ? (
              <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                No actions yet. Add an action to define what value adjustment to apply.
              </div>
            ) : (
              <div className="space-y-3">
                {actions.map((action, index) => (
                  <div key={index} className="flex gap-2 rounded-lg border p-3">
                    <div className="flex-1 space-y-2">
                      <Select
                        value={action.action_type}
                        onValueChange={(value) =>
                          updateAction(index, { action_type: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {ACTION_TYPES.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              {type.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>

                      {(action.action_type === "fixed_value" ||
                        action.action_type === "per_unit" ||
                        action.action_type === "benchmark_based") && (
                        <div className="grid grid-cols-2 gap-2">
                          <Input
                            type="number"
                            placeholder="Value USD"
                            value={action.value_usd || ""}
                            onChange={(e) =>
                              updateAction(index, {
                                value_usd: parseFloat(e.target.value) || 0,
                              })
                            }
                          />
                          {action.action_type !== "fixed_value" && (
                            <Input
                              placeholder="Metric/Unit"
                              value={action.metric || ""}
                              onChange={(e) =>
                                updateAction(index, { metric: e.target.value })
                              }
                            />
                          )}
                        </div>
                      )}

                      {action.action_type === "formula" && (
                        <Textarea
                          placeholder="Formula (e.g., ram_gb * 2.5)"
                          value={action.formula || ""}
                          onChange={(e) =>
                            updateAction(index, { formula: e.target.value })
                          }
                          rows={2}
                        />
                      )}
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeAction(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
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
