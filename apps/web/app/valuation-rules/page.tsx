"use client";

import { useEffect, useState } from "react";
import { Plus, Search, RefreshCw } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { useToast } from "../../components/ui/use-toast";

import { fetchRulesets, fetchRuleset, type Ruleset, type RuleGroup, type Rule } from "../../lib/api/rules";
import { RulesetCard } from "../../components/valuation/ruleset-card";
import { RuleBuilderModal } from "../../components/valuation/rule-builder-modal";
import { RulesetBuilderModal } from "../../components/valuation/ruleset-builder-modal";
import { RuleGroupFormModal } from "../../components/valuation/rule-group-form-modal";

export default function ValuationRulesPage() {
  const [selectedRulesetId, setSelectedRulesetId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isRuleBuilderOpen, setIsRuleBuilderOpen] = useState(false);
  const [isRulesetBuilderOpen, setIsRulesetBuilderOpen] = useState(false);
  const [isGroupFormOpen, setIsGroupFormOpen] = useState(false);
  const [editingGroupId, setEditingGroupId] = useState<number | null>(null);
  const [editingGroup, setEditingGroup] = useState<RuleGroup | null>(null);
  const [editingRule, setEditingRule] = useState<Rule | null>(null);

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

  // Auto-select active ruleset on load
  useEffect(() => {
    if (rulesets.length > 0 && !selectedRulesetId) {
      const activeRuleset = rulesets.find((r) => r.is_active) || rulesets[0];
      setSelectedRulesetId(activeRuleset.id);
    }
  }, [rulesets, selectedRulesetId]);

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
    toast({
      title: "Refreshed",
      description: "Rules data has been refreshed",
    });
  };

  // Filter rule groups by search
  const filteredRuleGroups = selectedRuleset?.rule_groups.filter((group) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      group.name.toLowerCase().includes(query) ||
      group.category.toLowerCase().includes(query) ||
      group.rules.some((rule) => rule.name.toLowerCase().includes(query))
    );
  });

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
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={() => setIsRulesetBuilderOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Ruleset
          </Button>
        </div>
      </div>

      {/* Ruleset Selector & Stats */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <CardTitle className="flex items-center gap-2">
                Active Ruleset
                {selectedRuleset?.is_active && (
                  <Badge variant="default" className="ml-2">
                    Active
                  </Badge>
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
                    <div className="flex items-center gap-2">
                      {ruleset.name}
                      {ruleset.is_active && (
                        <Badge variant="outline" className="ml-2">
                          Active
                        </Badge>
                      )}
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

      {/* Search and Actions */}
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
                onClick={() => setIsRulesetBuilderOpen(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Rule Group
              </Button>
            )}
          </CardContent>
        </Card>
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
