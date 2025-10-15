"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, Search, RefreshCw, Power, PowerOff, FileJson } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Separator } from "../../components/ui/separator";
import { Checkbox } from "../../components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Dialog, DialogContent, DialogTrigger } from "../../components/ui/dialog";
import { useToast } from "../../components/ui/use-toast";

import { fetchRulesets, fetchRuleset, updateRuleset, type Ruleset, type RuleGroup, type Rule, type Condition } from "../../lib/api/rules";
import { RulesetCard } from "../../components/valuation/ruleset-card";
import { RuleBuilderModal } from "../../components/valuation/rule-builder-modal";
import { RulesetBuilderModal } from "../../components/valuation/ruleset-builder-modal";
import { RuleGroupFormModal } from "../../components/valuation/rule-group-form-modal";
import { BasicValuationForm } from "../../components/valuation/basic-valuation-form";
import { ConditionGroup } from "../../components/valuation/condition-group";
import { BasicModeTabs } from "./_components/basic-mode-tabs";
import { DiffAdoptWizard } from "../../components/valuation/diff-adopt-wizard";
import { HydrationBanner } from "./_components/hydration-banner";
import { hydrateBaselineRules } from "../../lib/api/baseline";

type Mode = "basic" | "advanced";

type ConditionNode =
  | (Condition & {
      id: string;
      is_group?: false;
      children?: never;
      logical_operator?: string;
    })
  | {
      id: string;
      is_group: true;
      logical_operator?: string;
      children: ConditionNode[];
    };

function generateNodeId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `cond-${Math.random().toString(36).slice(2, 11)}`;
}

function normalizeLogicalUpper(value?: string): "AND" | "OR" {
  if (value && value.toLowerCase() === "or") {
    return "OR";
  }
  return "AND";
}

function normalizeLogicalLower(value?: string): "and" | "or" {
  return normalizeLogicalUpper(value) === "OR" ? "or" : "and";
}

function deserializeRulesetConditions(
  raw: Record<string, any> | null | undefined,
  fallback: "AND" | "OR" = "AND"
): ConditionNode[] {
  if (!raw || !Array.isArray(raw.conditions)) {
    return [];
  }

  const currentLogical = normalizeLogicalUpper(
    typeof raw.logical_operator === "string" ? raw.logical_operator : fallback
  );

  return raw.conditions
    .map((entry: any) => {
      if (entry && typeof entry === "object" && Array.isArray(entry.conditions)) {
        const nestedLogical = normalizeLogicalUpper(
          typeof entry.logical_operator === "string" ? entry.logical_operator : currentLogical
        );
        return {
          id: generateNodeId(),
          is_group: true,
          logical_operator: nestedLogical,
          children: deserializeRulesetConditions(entry, nestedLogical),
        };
      }

      if (!entry || typeof entry !== "object") {
        return null;
      }

      return {
        id: generateNodeId(),
        field_name: entry.field_name ?? "",
        field_type: entry.field_type ?? "string",
        operator: entry.operator ?? "equals",
        value: entry.value,
        logical_operator: currentLogical,
      } as ConditionNode;
    })
    .filter(Boolean) as ConditionNode[];
}

function serializeRulesetConditions(nodes: ConditionNode[]): Record<string, any> | null {
  if (!nodes.length) {
    return null;
  }

  const logical = normalizeLogicalLower(nodes[0]?.logical_operator);
  const conditions = nodes
    .map((node) => {
      if ("is_group" in node && node.is_group) {
        const childPayload = serializeRulesetConditions(node.children ?? []);
        if (!childPayload || !childPayload.conditions.length) {
          return null;
        }
        return {
          logical_operator: normalizeLogicalLower(node.logical_operator ?? childPayload.logical_operator),
          conditions: childPayload.conditions,
        };
      }

      if (!node.field_name) {
        return null;
      }

      return {
        field_name: node.field_name,
        field_type: node.field_type ?? "string",
        operator: node.operator ?? "equals",
        value: node.value,
      };
    })
    .filter(Boolean);

  if (!conditions.length) {
    return null;
  }

  return {
    logical_operator: logical,
    conditions,
  };
}

interface RulesetSettingsCardProps {
  ruleset: Ruleset | undefined;
  onRefresh: () => void;
}

function RulesetSettingsCard({ ruleset, onRefresh }: RulesetSettingsCardProps) {
  const { toast } = useToast();
  const [priority, setPriority] = useState(ruleset?.priority ?? 10);
  const [isActive, setIsActive] = useState(ruleset?.is_active ?? true);
  const initialNodes = useMemo(
    () => deserializeRulesetConditions(ruleset?.conditions),
    [ruleset?.id, ruleset?.conditions]
  );
  const [conditionNodes, setConditionNodes] = useState<ConditionNode[]>(initialNodes);

  useEffect(() => {
    setPriority(ruleset?.priority ?? 10);
    setIsActive(ruleset?.is_active ?? true);
    setConditionNodes(initialNodes);
  }, [ruleset?.id, ruleset?.priority, ruleset?.is_active, initialNodes]);

  const initialSerialized = useMemo(() => {
    const serialized = serializeRulesetConditions(initialNodes);
    return JSON.stringify(serialized ?? null);
  }, [initialNodes]);

  const currentSerialized = useMemo(() => {
    const serialized = serializeRulesetConditions(conditionNodes);
    return JSON.stringify(serialized ?? null);
  }, [conditionNodes]);

  const hasPriorityChange = priority !== (ruleset?.priority ?? 10);
  const hasActiveChange = isActive !== (ruleset?.is_active ?? true);
  const hasConditionChange = currentSerialized !== initialSerialized;
  const hasChanges = hasPriorityChange || hasActiveChange || hasConditionChange;

  const mutation = useMutation({
    mutationFn: (payload: Record<string, any>) => {
      if (!ruleset) {
        throw new Error("No ruleset selected");
      }
      return updateRuleset(ruleset.id, payload);
    },
    onSuccess: () => {
      toast({
        title: "Ruleset updated",
        description: "Priority and conditions saved successfully.",
      });
      onRefresh();
    },
    onError: (error: unknown) => {
      toast({
        title: "Update failed",
        description: error instanceof Error ? error.message : "Unable to update ruleset settings.",
        variant: "destructive",
      });
    },
  });

  const handleSave = () => {
    if (!ruleset || !hasChanges) {
      return;
    }

    const payload: Record<string, any> = {};
    if (hasPriorityChange) {
      payload.priority = priority;
    }
    if (hasActiveChange) {
      payload.is_active = isActive;
    }
    if (hasConditionChange) {
      payload.conditions = serializeRulesetConditions(conditionNodes) ?? {};
    }

    if (Object.keys(payload).length === 0) {
      return;
    }

    mutation.mutate(payload);
  };

  const handleReset = () => {
    setPriority(ruleset?.priority ?? 10);
    setIsActive(ruleset?.is_active ?? true);
    setConditionNodes(initialNodes);
  };

  if (!ruleset) {
    return null;
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            Ruleset Controls
            <Badge variant="outline">Priority {priority}</Badge>
            <Badge variant={isActive ? "secondary" : "destructive"}>
              {isActive ? "Enabled" : "Disabled"}
            </Badge>
          </CardTitle>
          <CardDescription>
            Configure when <span className="font-medium">{ruleset.name}</span> applies to listings.
          </CardDescription>
        </div>
        <Button
          type="button"
          variant={isActive ? "outline" : "default"}
          size="sm"
          onClick={() => setIsActive((value) => !value)}
        >
          {isActive ? (
            <>
              <PowerOff className="mr-2 h-4 w-4" />
              Disable
            </>
          ) : (
            <>
              <Power className="mr-2 h-4 w-4" />
              Enable
            </>
          )}
        </Button>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="max-w-xs">
          <Label htmlFor="ruleset-priority">Priority</Label>
          <Input
            id="ruleset-priority"
            type="number"
            min={0}
            value={priority}
            onChange={(event) => setPriority(Number.parseInt(event.target.value, 10) || 0)}
          />
          <p className="mt-1 text-xs text-muted-foreground">
            Lower numbers evaluate before higher ones when multiple rulesets are active.
          </p>
        </div>

        <Separator />

        <div>
          <div className="mb-3 flex items-center justify-between">
            <Label>Conditions</Label>
            <Badge variant="outline">
              {conditionNodes.length} item{conditionNodes.length === 1 ? "" : "s"}
            </Badge>
          </div>
          <ConditionGroup conditions={conditionNodes} onConditionsChange={setConditionNodes} />
        </div>

        <div className="flex items-center justify-between">
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
            {mutation.isPending ? "Saving…" : "Save settings"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function ValuationRulesPage() {
  const [selectedRulesetId, setSelectedRulesetId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isRuleBuilderOpen, setIsRuleBuilderOpen] = useState(false);
  const [isRulesetBuilderOpen, setIsRulesetBuilderOpen] = useState(false);
  const [isGroupFormOpen, setIsGroupFormOpen] = useState(false);
  const [isDiffWizardOpen, setIsDiffWizardOpen] = useState(false);
  const [editingGroupId, setEditingGroupId] = useState<number | null>(null);
  const [editingGroup, setEditingGroup] = useState<RuleGroup | null>(null);
  const [editingRule, setEditingRule] = useState<Rule | null>(null);
  const [mode, setMode] = useState<Mode>("basic");
  const [showSystemRules, setShowSystemRules] = useState(false);

  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch all rulesets
  const { data: rulesets = [], isLoading: isLoadingRulesets } = useQuery({
    queryKey: ["rulesets"],
    queryFn: () => fetchRulesets(false),
  });

  // Fetch selected ruleset details
  const { data: selectedRuleset, isLoading: isLoadingRuleset } = useQuery({
    queryKey: ["ruleset", selectedRulesetId],
    queryFn: () => fetchRuleset(selectedRulesetId!),
    enabled: !!selectedRulesetId,
  });

  // Extract all rules from rule groups
  const allRules = useMemo(() => {
    if (!selectedRuleset?.rule_groups) return [];
    return selectedRuleset.rule_groups.flatMap(group => group.rules);
  }, [selectedRuleset]);

  // Detect placeholder rules (not yet hydrated)
  const hasPlaceholderRules = useMemo(() => {
    return allRules.some(rule =>
      rule.metadata?.baseline_placeholder === true &&
      rule.metadata?.hydrated !== true
    );
  }, [allRules]);

  // Detect already-hydrated rules
  const hasHydratedRules = useMemo(() => {
    return allRules.some(rule =>
      rule.metadata?.hydrated === true
    );
  }, [allRules]);

  // Hydration mutation
  const hydrateMutation = useMutation({
    mutationFn: () => hydrateBaselineRules(selectedRulesetId!, "system"),
    onSuccess: (result) => {
      toast({
        title: "Baseline Rules Prepared",
        description: `Created ${result.created_rule_count} rules from ${result.hydrated_rule_count} baseline fields.`,
      });
      queryClient.invalidateQueries({ queryKey: ["ruleset", selectedRulesetId] });
      queryClient.invalidateQueries({ queryKey: ["rulesets"] });
    },
    onError: (error: Error) => {
      toast({
        title: "Hydration Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleHydrate = async () => {
    await hydrateMutation.mutateAsync();
  };

  // Auto-select active ruleset on load
  useEffect(() => {
    if (rulesets.length > 0 && !selectedRulesetId) {
      const activeRuleset = rulesets.find((r) => r.is_active) || rulesets[0];
      setSelectedRulesetId(activeRuleset.id);
    }
  }, [rulesets, selectedRulesetId]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem("valuationMode");
    if (stored === "advanced" || stored === "basic") {
      setMode(stored as Mode);
    }
  }, []);

  const handleModeChange = (nextMode: Mode) => {
    setMode(nextMode);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("valuationMode", nextMode);
    }
  };

  const handleCreateRule = (groupId: number) => {
    setEditingGroupId(groupId);
    setEditingRule(null);
    setIsRuleBuilderOpen(true);
  };

  const handleEditRule = (rule: Rule) => {
    setEditingRule(rule);
    setEditingGroupId(null);
    setIsRuleBuilderOpen(true);
  };

  const handleEditGroup = (group: RuleGroup) => {
    setEditingGroup(group);
    setIsGroupFormOpen(true);
  };

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ["rulesets"] });
    queryClient.invalidateQueries({ queryKey: ["ruleset", selectedRulesetId] });
    queryClient.invalidateQueries({ queryKey: ["baseline-metadata"] });
    queryClient.invalidateQueries({ queryKey: ["baseline-overrides"] });
    toast({
      title: "Refreshed",
      description: "Rules data has been refreshed",
    });
  };

  // Filter rule groups by search and apply rule filtering for Advanced mode
  const filteredRuleGroups = useMemo(() => {
    if (!selectedRuleset?.rule_groups) return [];

    return selectedRuleset.rule_groups
      .map((group) => {
        // Filter rules in Advanced mode
        let filteredRules = group.rules;

        if (mode === "advanced") {
          filteredRules = group.rules.filter((rule) => {
            // Hide foreign key rules unless toggle is on
            if (!showSystemRules && rule.metadata?.is_foreign_key_rule === true) {
              return false;
            }
            // Hide deactivated placeholders
            if (rule.metadata?.hydrated === true && !rule.is_active) {
              return false;
            }
            return true;
          });
        }

        // Apply search filter
        if (searchQuery) {
          const query = searchQuery.toLowerCase();
          const groupMatches =
            group.name.toLowerCase().includes(query) ||
            group.category.toLowerCase().includes(query);

          const ruleMatches = filteredRules.filter((rule) =>
            rule.name.toLowerCase().includes(query)
          );

          if (!groupMatches && ruleMatches.length === 0) {
            return null;
          }

          // If group matches, show all filtered rules; otherwise show only matching rules
          if (!groupMatches) {
            return { ...group, rules: ruleMatches };
          }
        }

        return { ...group, rules: filteredRules };
      })
      .filter((group): group is RuleGroup => group !== null && group.rules.length > 0);
  }, [selectedRuleset, searchQuery, mode, showSystemRules]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Valuation Rules</h1>
          <p className="text-sm text-muted-foreground">
            Manage hierarchical rules for component valuation and pricing adjustments
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ModeToggle mode={mode} onChange={handleModeChange} />
          <Dialog open={isDiffWizardOpen} onOpenChange={setIsDiffWizardOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <FileJson className="mr-2 h-4 w-4" />
                Diff & Adopt
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DiffAdoptWizard
                onComplete={() => {
                  setIsDiffWizardOpen(false);
                  handleRefresh();
                }}
              />
            </DialogContent>
          </Dialog>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          {mode === "advanced" && (
            <Button onClick={() => setIsRulesetBuilderOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              New Ruleset
            </Button>
          )}
        </div>
      </div>

      {/* Ruleset Selector & Stats (Only in Advanced Mode) */}
      {mode === "advanced" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <CardTitle className="flex flex-wrap items-center gap-2">
                  Active Ruleset
                  {selectedRuleset && (
                    <>
                      <Badge variant="outline">Priority {selectedRuleset.priority}</Badge>
                      <Badge variant={selectedRuleset.is_active ? "secondary" : "destructive"}>
                        {selectedRuleset.is_active ? "Enabled" : "Disabled"}
                      </Badge>
                    </>
                  )}
                </CardTitle>
                <CardDescription>
                  {selectedRuleset?.description || "Select a ruleset to manage rules"}
                </CardDescription>
              </div>
              <Select
                value={selectedRulesetId?.toString()}
                onValueChange={(value) => setSelectedRulesetId(parseInt(value))}
              >
                <SelectTrigger className="w-[300px]">
                  <SelectValue placeholder="Select ruleset..." />
                </SelectTrigger>
                <SelectContent>
                  {rulesets.map((ruleset) => (
                    <SelectItem key={ruleset.id} value={ruleset.id.toString()}>
                      <div className="flex flex-col">
                        <span className="font-medium">{ruleset.name}</span>
                        <div className="mt-1 flex items-center gap-2">
                          <Badge variant="outline">Priority {ruleset.priority}</Badge>
                          <Badge variant={ruleset.is_active ? "secondary" : "destructive"}>
                            {ruleset.is_active ? "Enabled" : "Disabled"}
                          </Badge>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          {selectedRuleset && (
            <CardContent>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Version</div>
                  <div className="text-2xl font-semibold">{selectedRuleset.version}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Rule Groups</div>
                  <div className="text-2xl font-semibold">
                    {selectedRuleset.rule_groups.length}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Total Rules</div>
                  <div className="text-2xl font-semibold">
                    {selectedRuleset.rule_groups.reduce(
                      (sum, group) => sum + group.rules.length,
                      0
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Active Rules</div>
                  <div className="text-2xl font-semibold">
                    {selectedRuleset.rule_groups.reduce(
                      (sum, group) =>
                        sum + group.rules.filter((r) => r.is_active).length,
                      0
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {mode === "advanced" && selectedRuleset && (
        <RulesetSettingsCard ruleset={selectedRuleset} onRefresh={handleRefresh} />
      )}

      {/* Hydration Banner - Show in Advanced mode when placeholders exist and not yet hydrated */}
      {mode === "advanced" && hasPlaceholderRules && !hasHydratedRules && selectedRulesetId && (
        <HydrationBanner
          rulesetId={selectedRulesetId}
          onHydrate={handleHydrate}
          isHydrating={hydrateMutation.isPending}
        />
      )}

      {mode === "basic" ? (
        <BasicModeTabs />
      ) : (
        <>
          {/* Search and Actions */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search rules, groups, or categories..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              {selectedRulesetId && (
                <Button
                  variant="outline"
                  onClick={() => {
                    setEditingGroup(null);
                    setIsGroupFormOpen(true);
                  }}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Group
                </Button>
              )}
            </div>

            {/* System Rules Toggle */}
            <div className="flex items-center gap-2 px-1">
              <Checkbox
                id="show-system-rules"
                checked={showSystemRules}
                onCheckedChange={(checked) => setShowSystemRules(checked === true)}
                aria-label="Show system rules"
              />
              <Label
                htmlFor="show-system-rules"
                className="text-sm text-muted-foreground cursor-pointer"
              >
                Show system rules (read-only foreign key rules)
              </Label>
            </div>
          </div>

          {/* Rule Groups */}
          {isLoadingRuleset ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                Loading rules...
              </CardContent>
            </Card>
          ) : filteredRuleGroups && filteredRuleGroups.length > 0 ? (
            <div className="space-y-4">
              {filteredRuleGroups.map((group) => (
                <RulesetCard
                  key={group.id}
                  ruleGroup={group}
                  onCreateRule={() => handleCreateRule(group.id)}
                  onEditGroup={handleEditGroup}
                  onEditRule={handleEditRule}
                  onRefresh={handleRefresh}
                  showSystemRules={showSystemRules}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <div className="text-muted-foreground">
                  {searchQuery
                    ? "No rules match your search"
                    : "No rule groups in this ruleset"}
                </div>
                {!searchQuery && selectedRulesetId && (
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={() => {
                      setEditingGroup(null);
                      setIsGroupFormOpen(true);
                    }}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add Rule Group
                  </Button>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Modals */}
      <RuleBuilderModal
        open={isRuleBuilderOpen}
        onOpenChange={(open) => {
          setIsRuleBuilderOpen(open);
          if (!open) {
            setEditingRule(null);
            setEditingGroupId(null);
          }
        }}
        groupId={editingGroupId}
        rule={editingRule}
        onSuccess={handleRefresh}
      />

      <RuleGroupFormModal
        open={isGroupFormOpen}
        onOpenChange={(open) => {
          setIsGroupFormOpen(open);
          if (!open) setEditingGroup(null);
        }}
        rulesetId={selectedRulesetId!}
        ruleGroup={editingGroup}
        onSuccess={handleRefresh}
      />

      <RulesetBuilderModal
        open={isRulesetBuilderOpen}
        onOpenChange={setIsRulesetBuilderOpen}
        onSuccess={handleRefresh}
      />
    </div>
  );
}

function ModeToggle({
  mode,
  onChange,
}: {
  mode: Mode;
  onChange: (mode: Mode) => void;
}) {
  return (
    <div className="inline-flex rounded-md border bg-muted/40 p-1 text-sm font-medium">
      <button
        type="button"
        className={`rounded-sm px-3 py-1.5 transition-colors ${
          mode === "basic"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
        onClick={() => onChange("basic")}
        aria-pressed={mode === "basic"}
      >
        Basic
      </button>
      <button
        type="button"
        className={`rounded-sm px-3 py-1.5 transition-colors ${
          mode === "advanced"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
        onClick={() => onChange("advanced")}
        aria-pressed={mode === "advanced"}
      >
        Advanced
      </button>
    </div>
  );
}
