"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Label } from "../ui/label";
import { Input } from "../ui/input";
import { Separator } from "../ui/separator";
import { Badge } from "../ui/badge";
import { useToast } from "../ui/use-toast";
import {
  createRule,
  createRuleGroup,
  deleteRule,
  updateRule,
  type Rule,
  type RuleGroup,
  type Ruleset,
} from "@/lib/api/rules";

type ConditionKey = "new" | "refurbished" | "used" | "for_parts";

interface BasicConfig {
  ramPerGb: number;
  primaryStoragePer100Gb: number;
  secondaryStoragePer100Gb: number;
  baseAdjustment: number;
  conditionAdjustments: Record<ConditionKey, number>;
}

const DEFAULT_CONFIG: BasicConfig = {
  ramPerGb: 0,
  primaryStoragePer100Gb: 0,
  secondaryStoragePer100Gb: 0,
  baseAdjustment: 0,
  conditionAdjustments: {
    new: 0,
    refurbished: 0,
    used: 0,
    for_parts: 0,
  },
};

const CONDITION_LABELS: Record<ConditionKey, string> = {
  new: "New",
  refurbished: "Refurbished",
  used: "Used",
  for_parts: "For Parts",
};

const BASIC_GROUP_NAME = "Basic · Adjustments";
const BASIC_GROUP_CATEGORY = "baseline";
const BASIC_MANAGED_FLAG = "basic_managed";

interface BasicValuationFormProps {
  ruleset: Ruleset | undefined;
  onRefresh: () => void;
}

interface RuleSpec {
  name: string;
  priority: number;
  evaluationOrder: number;
  buildPayload: (config: BasicConfig) => {
    conditions: Rule["conditions"];
    actions: Rule["actions"];
    isActive: boolean;
  };
}

const CONDITION_KEYS: ConditionKey[] = ["new", "refurbished", "used", "for_parts"];

const RAM_RULE_NAME = "RAM · Per GB";
const PRIMARY_STORAGE_RULE_NAME = "Primary Storage · Per GB";
const SECONDARY_STORAGE_RULE_NAME = "Secondary Storage · Per GB";
const BASE_ADJUSTMENT_RULE_NAME = "Baseline Adjustment";

function conditionRuleName(condition: ConditionKey): string {
  return `Condition · ${CONDITION_LABELS[condition]}`;
}

function approximateEqual(a: number, b: number, tolerance = 0.0001): boolean {
  return Math.abs(a - b) < tolerance;
}

function deriveConfigFromRuleset(ruleset: Ruleset | undefined): BasicConfig {
  if (!ruleset) return DEFAULT_CONFIG;

  const group = ruleset.rule_groups.find((item) => item.name === BASIC_GROUP_NAME);
  if (!group) return DEFAULT_CONFIG;

  const managedRules = group.rules.filter((rule) => rule.metadata?.[BASIC_MANAGED_FLAG]);

  const config: BasicConfig = {
    ramPerGb: DEFAULT_CONFIG.ramPerGb,
    primaryStoragePer100Gb: DEFAULT_CONFIG.primaryStoragePer100Gb,
    secondaryStoragePer100Gb: DEFAULT_CONFIG.secondaryStoragePer100Gb,
    baseAdjustment: DEFAULT_CONFIG.baseAdjustment,
    conditionAdjustments: { ...DEFAULT_CONFIG.conditionAdjustments },
  };

  const findRule = (ruleName: string) => managedRules.find((rule) => rule.name === ruleName);

  const ramRule = findRule(RAM_RULE_NAME);
  if (ramRule?.actions?.[0]?.value_usd != null) {
    config.ramPerGb = ramRule.actions[0].value_usd;
  }

  const primaryRule = findRule(PRIMARY_STORAGE_RULE_NAME);
  if (primaryRule?.actions?.[0]?.value_usd != null) {
    config.primaryStoragePer100Gb = primaryRule.actions[0].value_usd * 100;
  }

  const secondaryRule = findRule(SECONDARY_STORAGE_RULE_NAME);
  if (secondaryRule?.actions?.[0]?.value_usd != null) {
    config.secondaryStoragePer100Gb = secondaryRule.actions[0].value_usd * 100;
  }

  const baseRule = findRule(BASE_ADJUSTMENT_RULE_NAME);
  if (baseRule?.actions?.[0]?.value_usd != null) {
    config.baseAdjustment = baseRule.actions[0].value_usd;
  }

  CONDITION_KEYS.forEach((conditionKey) => {
    const rule = findRule(conditionRuleName(conditionKey));
    if (rule?.actions?.[0]?.value_usd != null) {
      config.conditionAdjustments[conditionKey] = rule.actions[0].value_usd;
    } else {
      config.conditionAdjustments[conditionKey] = 0;
    }
  });

  return config;
}

function configsEqual(a: BasicConfig, b: BasicConfig): boolean {
  if (
    !approximateEqual(a.ramPerGb, b.ramPerGb) ||
    !approximateEqual(a.primaryStoragePer100Gb, b.primaryStoragePer100Gb) ||
    !approximateEqual(a.secondaryStoragePer100Gb, b.secondaryStoragePer100Gb) ||
    !approximateEqual(a.baseAdjustment, b.baseAdjustment)
  ) {
    return false;
  }

  return CONDITION_KEYS.every((key) =>
    approximateEqual(a.conditionAdjustments[key], b.conditionAdjustments[key])
  );
}

export function BasicValuationForm({ ruleset, onRefresh }: BasicValuationFormProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const initialConfig = useMemo(() => deriveConfigFromRuleset(ruleset), [ruleset]);
  const [config, setConfig] = useState<BasicConfig>(initialConfig);

  useEffect(() => {
    setConfig(initialConfig);
  }, [initialConfig]);

  const existingGroup = useMemo(() => {
    return ruleset?.rule_groups.find((group) => group.name === BASIC_GROUP_NAME);
  }, [ruleset]);

  const existingRulesByName = useMemo(() => {
    const map = new Map<string, Rule>();
    existingGroup?.rules
      ?.filter((rule) => rule.metadata?.[BASIC_MANAGED_FLAG])
      .forEach((rule) => map.set(rule.name, rule));
    return map;
  }, [existingGroup]);

  const ruleSpecs: RuleSpec[] = useMemo(() => {
    const specs: RuleSpec[] = [
      {
        name: BASE_ADJUSTMENT_RULE_NAME,
        priority: 5,
        evaluationOrder: 5,
        buildPayload: (current) => ({
          conditions: [],
          actions: [
            {
              action_type: "fixed_value",
              value_usd: current.baseAdjustment,
              modifiers: {},
            },
          ],
          isActive: !approximateEqual(current.baseAdjustment, 0),
        }),
      },
      {
        name: RAM_RULE_NAME,
        priority: 10,
        evaluationOrder: 10,
        buildPayload: (current) => ({
          conditions: [],
          actions: [
            {
              action_type: "per_unit",
              metric: "per_gb",
              value_usd: current.ramPerGb,
              modifiers: {},
            },
          ],
          isActive: !approximateEqual(current.ramPerGb, 0),
        }),
      },
      {
        name: PRIMARY_STORAGE_RULE_NAME,
        priority: 20,
        evaluationOrder: 20,
        buildPayload: (current) => ({
          conditions: [],
          actions: [
            {
              action_type: "per_unit",
              metric: "primary_storage_gb",
              value_usd: current.primaryStoragePer100Gb / 100,
              modifiers: {},
            },
          ],
          isActive: !approximateEqual(current.primaryStoragePer100Gb, 0),
        }),
      },
      {
        name: SECONDARY_STORAGE_RULE_NAME,
        priority: 30,
        evaluationOrder: 30,
        buildPayload: (current) => ({
          conditions: [],
          actions: [
            {
              action_type: "per_unit",
              metric: "secondary_storage_gb",
              value_usd: current.secondaryStoragePer100Gb / 100,
              modifiers: {},
            },
          ],
          isActive: !approximateEqual(current.secondaryStoragePer100Gb, 0),
        }),
      },
      ...CONDITION_KEYS.map<RuleSpec>((conditionKey, index) => ({
        name: conditionRuleName(conditionKey),
        priority: 40 + index,
        evaluationOrder: 40 + index,
        buildPayload: (current) => ({
          conditions: [
            {
              field_name: "condition",
              field_type: "string",
              operator: "equals",
              value: conditionKey,
              logical_operator: "AND",
              group_order: 0,
            },
          ],
          actions: [
            {
              action_type: "fixed_value",
              value_usd: current.conditionAdjustments[conditionKey],
              modifiers: {},
            },
          ],
          isActive: !approximateEqual(current.conditionAdjustments[conditionKey], 0),
        }),
      })),
    ];
    return specs;
  }, []);

  const mutation = useMutation({
    mutationFn: async (nextConfig: BasicConfig) => {
      if (!ruleset) {
        throw new Error("Ruleset is not loaded yet");
      }

      let groupId: number;
      if (existingGroup) {
        groupId = existingGroup.id;
      } else {
        const createdGroup = await createRuleGroup({
          ruleset_id: ruleset.id,
          name: BASIC_GROUP_NAME,
          category: BASIC_GROUP_CATEGORY,
          description: "Managed by Basic valuation mode",
          display_order: 0,
          weight: 1.0,
        });
        groupId = createdGroup.id;
      }

      const updates: Promise<unknown>[] = [];

      for (const spec of ruleSpecs) {
        const payload = spec.buildPayload(nextConfig);
        const metadata = { [BASIC_MANAGED_FLAG]: true, source: "basic_mode" };

        const existingRule = existingRulesByName.get(spec.name);
        if (existingRule) {
          if (!payload.isActive && !existingRule.is_active) {
            continue;
          }
          updates.push(
            updateRule(existingRule.id, {
              name: spec.name,
              description: existingRule.description ?? "Managed via Basic valuation mode",
              priority: spec.priority,
              evaluation_order: spec.evaluationOrder,
              is_active: payload.isActive,
              conditions: payload.conditions,
              actions: payload.actions,
              metadata: { ...existingRule.metadata, ...metadata },
            })
          );
          existingRulesByName.delete(spec.name);
        } else if (payload.isActive) {
          updates.push(
            createRule({
              group_id: groupId,
              name: spec.name,
              description: "Managed via Basic valuation mode",
              priority: spec.priority,
              evaluation_order: spec.evaluationOrder,
              is_active: payload.isActive,
              conditions: payload.conditions,
              actions: payload.actions,
              metadata,
            })
          );
        } else {
          existingRulesByName.delete(spec.name);
        }
      }

      // Remove stale managed rules no longer needed
      existingRulesByName.forEach((rule, ruleName) => {
        const spec = ruleSpecs.find((item) => item.name === ruleName);
        if (!spec) {
          updates.push(deleteRule(rule.id));
        }
      });

      await Promise.all(updates);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ruleset", ruleset?.id] });
      queryClient.invalidateQueries({ queryKey: ["rulesets"] });
      toast({
        title: "Basic adjustments saved",
        description: "Ruleset updated to reflect your Basic mode changes.",
      });
      onRefresh();
    },
    onError: (error: unknown) => {
      toast({
        title: "Unable to save Basic mode changes",
        description: error instanceof Error ? error.message : "Please try again.",
        variant: "destructive",
      });
    },
  });

  const handleConfigChange = (partial: Partial<BasicConfig>) => {
    setConfig((prev) => ({ ...prev, ...partial }));
  };

  const hasChanges = !configsEqual(config, initialConfig);

  const handleConditionChange = (condition: ConditionKey, value: number) => {
    setConfig((prev) => ({
      ...prev,
      conditionAdjustments: { ...prev.conditionAdjustments, [condition]: value },
    }));
  };

  const handleSave = () => {
    mutation.mutate(config);
  };

  const handleReset = () => {
    setConfig(initialConfig);
  };

  if (!ruleset) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Basic valuation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-10 text-center text-sm text-muted-foreground">
            Loading ruleset…
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <CardTitle className="text-xl">Basic valuation</CardTitle>
          <p className="text-sm text-muted-foreground">
            Adjust common valuation levers. Changes update the underlying ruleset instantly and can be refined in Advanced mode.
          </p>
        </div>
        <Badge variant="outline">Ruleset · {ruleset.name}</Badge>
      </CardHeader>
      <CardContent className="space-y-6">
        <section>
          <h3 className="text-sm font-semibold text-foreground">Baseline adjustments</h3>
          <p className="mb-4 text-xs text-muted-foreground">
            Enter how much value (USD) to add or subtract. Negative numbers deduct from the listing price.
          </p>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <NumberField
              id="base-adjustment"
              label="Base adjustment"
              value={config.baseAdjustment}
              step={5}
              onChange={(value) => handleConfigChange({ baseAdjustment: value })}
              hint="Applied once per listing."
            />
            <NumberField
              id="ram-adjustment"
              label="Per GB of RAM"
              value={config.ramPerGb}
              step={0.5}
              onChange={(value) => handleConfigChange({ ramPerGb: value })}
              hint="Adjust per GB of installed RAM."
            />
            <NumberField
              id="primary-storage"
              label="Primary storage (per 100 GB)"
              value={config.primaryStoragePer100Gb}
              step={1}
              onChange={(value) => handleConfigChange({ primaryStoragePer100Gb: value })}
              hint="Applies to the main storage device."
            />
            <NumberField
              id="secondary-storage"
              label="Secondary storage (per 100 GB)"
              value={config.secondaryStoragePer100Gb}
              step={1}
              onChange={(value) => handleConfigChange({ secondaryStoragePer100Gb: value })}
              hint="Applies if a secondary drive is present."
            />
          </div>
        </section>

        <Separator />

        <section>
          <h3 className="text-sm font-semibold text-foreground">Condition adjustments</h3>
          <p className="mb-4 text-xs text-muted-foreground">
            Specify premiums or deductions for each condition state. These stack with baseline adjustments.
          </p>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {CONDITION_KEYS.map((conditionKey) => (
              <NumberField
                key={conditionKey}
                id={`condition-${conditionKey}`}
                label={CONDITION_LABELS[conditionKey]}
                value={config.conditionAdjustments[conditionKey]}
                step={5}
                onChange={(value) => handleConditionChange(conditionKey, value)}
                hint="USD applied when this condition matches."
              />
            ))}
          </div>
        </section>

        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">
            Managed rules live in the “{BASIC_GROUP_NAME}” group. Switch to Advanced mode to inspect generated conditions.
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleReset}
              disabled={!hasChanges || mutation.isPending}
            >
              Reset
            </Button>
            <Button
              type="button"
              onClick={handleSave}
              disabled={!hasChanges || mutation.isPending}
            >
              {mutation.isPending ? "Saving…" : "Save adjustments"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function NumberField({
  id,
  label,
  value,
  step,
  onChange,
  hint,
}: {
  id: string;
  label: string;
  value: number;
  step?: number;
  onChange: (value: number) => void;
  hint?: string;
}) {
  return (
    <div>
      <Label htmlFor={id} className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </Label>
      <Input
        id={id}
        type="number"
        inputMode="decimal"
        step={step ?? 1}
        value={Number.isFinite(value) ? value : 0}
        onChange={(event) => {
          const next = parseFloat(event.target.value);
          onChange(Number.isNaN(next) ? 0 : next);
        }}
      />
      {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}
