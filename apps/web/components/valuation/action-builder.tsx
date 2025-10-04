"use client";

import { Plus, X } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Textarea } from "../ui/textarea";

const ACTION_TYPES = [
  { value: "fixed_value", label: "Fixed Value" },
  { value: "per_unit", label: "Per Unit" },
  { value: "percentage", label: "Percentage" },
  { value: "benchmark_based", label: "Benchmark Based" },
  { value: "formula", label: "Formula" },
];

interface ActionBuilderProps {
  actions: any[];
  onActionsChange: (actions: any[]) => void;
}

export function ActionBuilder({ actions, onActionsChange }: ActionBuilderProps) {
  const addAction = () => {
    onActionsChange([
      ...actions,
      {
        id: crypto.randomUUID(),
        action_type: "fixed_value",
        value_usd: 0,
        modifiers: {
          condition_multipliers: {
            new: 1.0,
            refurb: 0.75,
            used: 0.6,
          },
        },
      },
    ]);
  };

  const updateAction = (index: number, updates: any) => {
    const newActions = [...actions];
    newActions[index] = { ...newActions[index], ...updates };
    onActionsChange(newActions);
  };

  const removeAction = (index: number) => {
    onActionsChange(actions.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      {actions.map((action, index) => (
        <div key={action.id} className="rounded-lg border p-4 space-y-3">
          <div className="flex items-center justify-between">
            <Label>Action Type</Label>
            <Button type="button" variant="ghost" size="sm" onClick={() => removeAction(index)}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          <Select
            value={action.action_type}
            onValueChange={(value) => updateAction(index, { action_type: value })}
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

          {/* Action-specific inputs */}
          {(action.action_type === "fixed_value" ||
            action.action_type === "per_unit" ||
            action.action_type === "benchmark_based") && (
            <div>
              <Label>Value (USD)</Label>
              <Input
                type="number"
                step="0.01"
                value={action.value_usd || ""}
                onChange={(e) =>
                  updateAction(index, { value_usd: parseFloat(e.target.value) || 0 })
                }
              />
            </div>
          )}

          {action.action_type === "percentage" && (
            <div>
              <Label>Percentage (%)</Label>
              <Input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={action.percentage || ""}
                onChange={(e) =>
                  updateAction(index, { percentage: parseFloat(e.target.value) || 0 })
                }
              />
            </div>
          )}

          {action.action_type === "formula" && (
            <div>
              <Label>Formula</Label>
              <Textarea
                placeholder="e.g., ram_gb * 2.5 + storage_gb * 0.1"
                value={action.formula || ""}
                onChange={(e) => updateAction(index, { formula: e.target.value })}
                rows={3}
              />
            </div>
          )}

          {/* Condition Multipliers */}
          <div className="space-y-2">
            <Label>Condition Multipliers</Label>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <Label className="text-xs">New</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  max="2"
                  value={action.modifiers?.condition_multipliers?.new || 1.0}
                  onChange={(e) =>
                    updateAction(index, {
                      modifiers: {
                        ...action.modifiers,
                        condition_multipliers: {
                          ...action.modifiers?.condition_multipliers,
                          new: parseFloat(e.target.value) || 1.0,
                        },
                      },
                    })
                  }
                />
              </div>
              <div>
                <Label className="text-xs">Refurbished</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  max="2"
                  value={action.modifiers?.condition_multipliers?.refurb || 0.75}
                  onChange={(e) =>
                    updateAction(index, {
                      modifiers: {
                        ...action.modifiers,
                        condition_multipliers: {
                          ...action.modifiers?.condition_multipliers,
                          refurb: parseFloat(e.target.value) || 0.75,
                        },
                      },
                    })
                  }
                />
              </div>
              <div>
                <Label className="text-xs">Used</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  max="2"
                  value={action.modifiers?.condition_multipliers?.used || 0.6}
                  onChange={(e) =>
                    updateAction(index, {
                      modifiers: {
                        ...action.modifiers,
                        condition_multipliers: {
                          ...action.modifiers?.condition_multipliers,
                          used: parseFloat(e.target.value) || 0.6,
                        },
                      },
                    })
                  }
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Adjust action value based on listing condition (1.0 = 100%)
            </p>
          </div>
        </div>
      ))}

      <Button type="button" variant="outline" onClick={addAction}>
        <Plus className="mr-2 h-4 w-4" />
        Add Action
      </Button>
    </div>
  );
}
