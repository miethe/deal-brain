"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Plus, Edit, Copy, Trash2, Power, PowerOff } from "lucide-react";
import { useMutation, useQueryClient } from "@tantml:react-query";

import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";
import { useToast } from "../ui/use-toast";

import { type RuleGroup, type Rule, deleteRule, duplicateRule, updateRule } from "../../lib/api/rules";

interface RulesetCardProps {
  ruleGroup: RuleGroup;
  onCreateRule: () => void;
  onEditGroup: (group: RuleGroup) => void;
  onEditRule: (rule: Rule) => void;
  onRefresh: () => void;
}

export function RulesetCard({ ruleGroup, onCreateRule, onEditGroup, onEditRule, onRefresh }: RulesetCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [expandedRules, setExpandedRules] = useState<Set<number>>(new Set());
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [ruleToDelete, setRuleToDelete] = useState<Rule | null>(null);

  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Delete rule mutation
  const deleteMutation = useMutation({
    mutationFn: (ruleId: number) => deleteRule(ruleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ruleset"] });
      toast({
        title: "Rule deleted",
        description: "The rule has been deleted successfully",
      });
      setDeleteDialogOpen(false);
      setRuleToDelete(null);
      onRefresh();
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to delete rule",
        variant: "destructive",
      });
    },
  });

  // Duplicate rule mutation
  const duplicateMutation = useMutation({
    mutationFn: (ruleId: number) => duplicateRule(ruleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ruleset"] });
      toast({
        title: "Rule duplicated",
        description: "The rule has been duplicated successfully",
      });
      onRefresh();
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to duplicate rule",
        variant: "destructive",
      });
    },
  });

  // Toggle active mutation
  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) =>
      updateRule(id, { is_active: isActive }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["ruleset"] });
      toast({
        title: variables.isActive ? "Rule activated" : "Rule deactivated",
        description: `The rule has been ${variables.isActive ? "activated" : "deactivated"}`,
      });
      onRefresh();
    },
  });

  const handleDeleteClick = (rule: Rule) => {
    setRuleToDelete(rule);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (ruleToDelete) {
      deleteMutation.mutate(ruleToDelete.id);
    }
  };

  const toggleRuleExpansion = (ruleId: number) => {
    const newExpanded = new Set(expandedRules);
    if (newExpanded.has(ruleId)) {
      newExpanded.delete(ruleId);
    } else {
      newExpanded.add(ruleId);
    }
    setExpandedRules(newExpanded);
  };

  const formatCondition = (condition: any) => {
    const value = typeof condition.value === 'object'
      ? JSON.stringify(condition.value)
      : condition.value;
    return `${condition.field_name} ${condition.operator} ${value}`;
  };

  const formatAction = (action: any) => {
    if (action.action_type === 'fixed_value') {
      return `Fixed adjustment: $${action.value_usd}`;
    }
    if (action.action_type === 'per_unit') {
      return `${action.metric}: $${action.value_usd} per unit`;
    }
    if (action.action_type === 'formula') {
      return `Formula: ${action.formula}`;
    }
    return `${action.action_type}: ${action.metric || 'N/A'}`;
  };

  const categoryColors: Record<string, string> = {
    cpu: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    ram: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
    storage: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
    gpu: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300",
    default: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300",
  };

  const categoryColor = categoryColors[ruleGroup.category.toLowerCase()] || categoryColors.default;

  return (
    <>
      <Card>
        <CardHeader className="cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
              <div>
                <CardTitle className="flex items-center gap-2">
                  {ruleGroup.name}
                  <Badge className={categoryColor}>{ruleGroup.category}</Badge>
                  <Badge variant="outline">{ruleGroup.rules.length} rules</Badge>
                </CardTitle>
                {ruleGroup.description && (
                  <p className="mt-1 text-sm text-muted-foreground">{ruleGroup.description}</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onEditGroup(ruleGroup);
                }}
                title="Edit Group"
              >
                <Edit className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onCreateRule();
                }}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Rule
              </Button>
            </div>
          </div>
        </CardHeader>

        {isExpanded && (
          <CardContent className="space-y-2 pt-0">
            {ruleGroup.rules.length === 0 ? (
              <div className="py-8 text-center text-sm text-muted-foreground">
                No rules in this group yet. Click &ldquo;Add Rule&rdquo; to create one.
              </div>
            ) : (
              ruleGroup.rules
                .sort((a, b) => a.evaluation_order - b.evaluation_order)
                .map((rule) => {
                  const isRuleExpanded = expandedRules.has(rule.id);
                  return (
                    <div
                      key={rule.id}
                      className="rounded-lg border bg-card transition-colors hover:bg-accent/50"
                    >
                      <div className="group flex items-center justify-between p-4">
                        <div className="flex flex-1 items-start gap-3">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={() => toggleRuleExpansion(rule.id)}
                          >
                            {isRuleExpanded ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </Button>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{rule.name}</span>
                              {!rule.is_active && (
                                <Badge variant="secondary" className="text-xs">
                                  Inactive
                                </Badge>
                              )}
                              <Badge variant="outline" className="text-xs">
                                Priority: {rule.priority}
                              </Badge>
                            </div>
                            {rule.description && (
                              <p className="mt-1 text-sm text-muted-foreground">{rule.description}</p>
                            )}
                            <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                              <span>{rule.conditions.length} conditions</span>
                              <span>{rule.actions.length} actions</span>
                              <span>Version {rule.version}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onEditRule(rule)}
                            title="Edit"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              toggleActiveMutation.mutate({
                                id: rule.id,
                                isActive: !rule.is_active,
                              })
                            }
                            title={rule.is_active ? "Deactivate" : "Activate"}
                          >
                            {rule.is_active ? (
                              <PowerOff className="h-4 w-4" />
                            ) : (
                              <Power className="h-4 w-4" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => duplicateMutation.mutate(rule.id)}
                            title="Duplicate"
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteClick(rule)}
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      {/* Expanded Rule Details */}
                      {isRuleExpanded && (
                        <div className="border-t px-4 py-3 space-y-3 text-sm bg-muted/30">
                          {/* Conditions */}
                          <div>
                            <h5 className="font-medium text-xs uppercase text-muted-foreground mb-2">
                              Conditions
                            </h5>
                            {rule.conditions.length === 0 ? (
                              <p className="text-xs text-muted-foreground">No conditions</p>
                            ) : (
                              <div className="space-y-1">
                                {rule.conditions.map((condition, index) => (
                                  <div key={index} className="flex items-center gap-2">
                                    {index > 0 && condition.logical_operator && (
                                      <span className="text-xs font-medium text-muted-foreground">
                                        {condition.logical_operator}
                                      </span>
                                    )}
                                    <code className="text-xs bg-background px-2 py-1 rounded border">
                                      {formatCondition(condition)}
                                    </code>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Actions */}
                          <div>
                            <h5 className="font-medium text-xs uppercase text-muted-foreground mb-2">
                              Actions
                            </h5>
                            {rule.actions.length === 0 ? (
                              <p className="text-xs text-muted-foreground">No actions</p>
                            ) : (
                              <div className="space-y-1">
                                {rule.actions.map((action, index) => (
                                  <code
                                    key={index}
                                    className="text-xs bg-background px-2 py-1 rounded border block"
                                  >
                                    {formatAction(action)}
                                  </code>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })
            )}
          </CardContent>
        )}
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Rule</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &ldquo;{ruleToDelete?.name}&rdquo;? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
