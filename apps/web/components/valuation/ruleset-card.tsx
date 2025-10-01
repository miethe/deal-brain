"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Plus, Edit, Copy, Trash2, Power, PowerOff } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

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
  onRefresh: () => void;
}

export function RulesetCard({ ruleGroup, onCreateRule, onRefresh }: RulesetCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
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
                .map((rule) => (
                  <div
                    key={rule.id}
                    className="group flex items-center justify-between rounded-lg border bg-card p-4 transition-colors hover:bg-accent"
                  >
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

                    <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
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
                ))
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
