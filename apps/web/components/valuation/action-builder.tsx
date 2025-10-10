"use client";

import { useEffect, useRef } from "react";
import { Plus, X } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Textarea } from "../ui/textarea";
import { PER_UNIT_METRIC_OPTIONS, normalizePerUnitMetric } from "../../lib/valuation-metrics";

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

const CUSTOM_METRIC_VALUE = "__custom__";

const generateId = () => {
  const cryptoApi = typeof globalThis !== "undefined" ? (globalThis as { crypto?: Crypto }).crypto : undefined;
  if (cryptoApi?.randomUUID) {
    return cryptoApi.randomUUID();
  }
  return `id-${Math.random().toString(36).slice(2, 11)}`;
};

export function ActionBuilder({ actions, onActionsChange }: ActionBuilderProps) {
  const fallbackIds = useRef(new WeakMap<any, string>());

  const getActionId = (action: any) => {
    if (action?.id) {
      return action.id;
    }

    if (!fallbackIds.current.has(action)) {
      fallbackIds.current.set(action, generateId());
    }

    return fallbackIds.current.get(action)!;
  };

  useEffect(() => {
    if (!Array.isArray(actions)) {
      return;
    }

    const needsUpdate = actions.some(
      (action) => !action?.id || !action?.action_type
    );

    if (needsUpdate) {
      onActionsChange(
        actions.map((action) => ({
          value_usd: 0,
          modifiers: {
            condition_multipliers: {
              new: 1.0,
              refurb: 0.75,
              used: 0.6,
            },
          },
          ...action,
          id: action?.id ?? generateId(),
          action_type: action?.action_type ?? "fixed_value",
        }))
      );
    }
  }, [actions, onActionsChange]);

  const addAction = () => {
    onActionsChange([
      ...actions,
      {
        id: generateId(),
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
    const previous = newActions[index] ?? {};
    const next = { ...previous, ...updates };

    if ("action_type" in updates) {
      if (updates.action_type === "per_unit") {
        const normalizedMetric = normalizePerUnitMetric(next.metric);
        next.metric = normalizedMetric ?? PER_UNIT_METRIC_OPTIONS[0]?.value ?? "";
      } else if (previous.action_type === "per_unit" && updates.action_type !== "per_unit") {
        next.metric = undefined;
      }
    }

    if (next.action_type === "per_unit" && !next.metric) {
      next.metric = PER_UNIT_METRIC_OPTIONS[0]?.value ?? "";
    }

    newActions[index] = next;
    onActionsChange(newActions);
  };

  const removeAction = (index: number) => {
    onActionsChange(actions.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      {actions.map((action, index) => {
        const actionId = getActionId(action);
        return (
          <div key={actionId} className="rounded-lg border p-4 space-y-3">
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

          {action.action_type === "per_unit" && (
            <div className="space-y-2">
              <Label>Metric</Label>
              {(() => {
                const normalizedMetric = normalizePerUnitMetric(action.metric);
                const metricInOptions = PER_UNIT_METRIC_OPTIONS.some(
                  (option) => option.value === normalizedMetric,
                );
                const selectedValue = metricInOptions
                  ? normalizedMetric
                  : action.metric
                    ? CUSTOM_METRIC_VALUE
                    : "";

                return (
                  <>
                    <Select
                      value={selectedValue ?? ""}
                      onValueChange={(value) => {
                        if (value === CUSTOM_METRIC_VALUE) {
                          updateAction(index, { metric: action.metric ?? "" });
                          return;
                        }
                        updateAction(index, { metric: value });
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select metric" />
                      </SelectTrigger>
                      <SelectContent>
                        {PER_UNIT_METRIC_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                        <SelectItem value={CUSTOM_METRIC_VALUE}>Custom field…</SelectItem>
                      </SelectContent>
                    </Select>
                    {selectedValue === CUSTOM_METRIC_VALUE && (
                      <Input
                        value={action.metric ?? ""}
                        placeholder="Enter custom metric (e.g., custom.screen_size)"
                        onChange={(event) => updateAction(index, { metric: event.target.value })}
                        className="mt-2"
                      />
                    )}
                  </>
                );
              })()}
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
              <div key="new">
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
              <div key="refurb">
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
              <div key="used">
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
        );
      })}

      <Button type="button" variant="outline" onClick={addAction}>
        <Plus className="mr-2 h-4 w-4" />
        Add Action
      </Button>
    </div>
  );
}
