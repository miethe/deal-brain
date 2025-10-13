"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, FileJson, CheckCircle2, AlertCircle, ChevronRight, ChevronDown } from "lucide-react";
import { Button } from "../ui/button";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { Checkbox } from "../ui/checkbox";
import { Badge } from "../ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import { useToast } from "@/hooks/use-toast";
import { diffBaseline, adoptBaseline, validateBaseline } from "@/lib/api/baseline";
import type { BaselineMetadata, DiffResponse, DiffEntityChange, DiffFieldChange } from "@/types/baseline";

type WizardStep = "upload" | "diff" | "adopt" | "complete";

interface DiffAdoptWizardProps {
  onComplete?: () => void;
  className?: string;
}

export function DiffAdoptWizard({ onComplete, className }: DiffAdoptWizardProps) {
  const [step, setStep] = useState<WizardStep>("upload");
  const [candidateJson, setCandidateJson] = useState("");
  const [candidateMetadata, setCandidateMetadata] = useState<BaselineMetadata | null>(null);
  const [diffResult, setDiffResult] = useState<DiffResponse | null>(null);
  const [selectedChanges, setSelectedChanges] = useState<Set<string>>(new Set());
  const [recalculateValuations, setRecalculateValuations] = useState(true);
  const [adoptResult, setAdoptResult] = useState<any>(null);

  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Validation mutation
  const validateMutation = useMutation({
    mutationFn: (json: string) => {
      const parsed = JSON.parse(json);
      setCandidateMetadata(parsed);
      return validateBaseline(parsed);
    },
    onSuccess: (result) => {
      if (result.valid) {
        toast({
          title: "Validation successful",
          description: "Baseline JSON is valid",
        });
      } else {
        toast({
          title: "Validation errors",
          description: result.errors?.join(", "),
          variant: "destructive",
        });
      }
    },
    onError: (error: Error) => {
      toast({
        title: "Invalid JSON",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Diff mutation
  const diffMutation = useMutation({
    mutationFn: (json: string) => diffBaseline(json),
    onSuccess: (result) => {
      setDiffResult(result);
      setStep("diff");

      // Pre-select all changes
      const allChangeIds = new Set<string>();
      result.changes.forEach((entityChange) => {
        entityChange.fields.forEach((fieldChange) => {
          allChangeIds.add(`${entityChange.entity_key}:${fieldChange.field_name}`);
        });
      });
      setSelectedChanges(allChangeIds);

      toast({
        title: "Diff complete",
        description: `Found ${result.summary.added_count + result.summary.changed_count + result.summary.removed_count} changes`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Diff failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Adopt mutation
  const adoptMutation = useMutation({
    mutationFn: () => {
      if (!candidateMetadata) throw new Error("No candidate baseline");

      const selectedByEntity = new Map<string, string[]>();
      selectedChanges.forEach((changeId) => {
        const [entityKey, fieldName] = changeId.split(":");
        if (!selectedByEntity.has(entityKey)) {
          selectedByEntity.set(entityKey, []);
        }
        selectedByEntity.get(entityKey)!.push(fieldName);
      });

      return adoptBaseline({
        candidate_baseline: candidateMetadata,
        selected_changes: Array.from(selectedByEntity.entries()).map(([entity_key, field_names]) => ({
          entity_key,
          field_names,
        })),
        recalculate_valuations: recalculateValuations,
        backup_current: true,
      });
    },
    onSuccess: (result) => {
      setAdoptResult(result);
      setStep("complete");
      queryClient.invalidateQueries({ queryKey: ["baseline-metadata"] });
      queryClient.invalidateQueries({ queryKey: ["baseline-overrides"] });

      toast({
        title: "Baseline adopted",
        description: `${result.changes_applied} changes applied successfully`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Adoption failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setCandidateJson(content);
    };
    reader.readAsText(file);
  };

  const handleValidate = () => {
    if (!candidateJson) return;
    validateMutation.mutate(candidateJson);
  };

  const handleDiff = () => {
    if (!candidateJson) return;
    diffMutation.mutate(candidateJson);
  };

  const handleAdopt = () => {
    if (selectedChanges.size === 0) {
      toast({
        title: "No changes selected",
        description: "Please select at least one change to adopt",
        variant: "destructive",
      });
      return;
    }
    setStep("adopt");
  };

  const handleConfirmAdopt = () => {
    adoptMutation.mutate();
  };

  const toggleChange = (entityKey: string, fieldName: string) => {
    const changeId = `${entityKey}:${fieldName}`;
    setSelectedChanges((prev) => {
      const next = new Set(prev);
      if (next.has(changeId)) {
        next.delete(changeId);
      } else {
        next.add(changeId);
      }
      return next;
    });
  };

  const toggleEntityChanges = (entityKey: string, fields: DiffFieldChange[]) => {
    const entityChangeIds = fields.map((f) => `${entityKey}:${f.field_name}`);
    const allSelected = entityChangeIds.every((id) => selectedChanges.has(id));

    setSelectedChanges((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        entityChangeIds.forEach((id) => next.delete(id));
      } else {
        entityChangeIds.forEach((id) => next.add(id));
      }
      return next;
    });
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Diff & Adopt Baseline</CardTitle>
        <CardDescription>
          Compare and adopt changes from a candidate baseline configuration
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Step 1: Upload */}
        {step === "upload" && (
          <div className="space-y-6">
            <div>
              <Label htmlFor="json-file">Upload JSON File</Label>
              <div className="mt-2 flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => document.getElementById("json-file")?.click()}
                >
                  <Upload className="mr-2 h-4 w-4" />
                  Choose File
                </Button>
                <input
                  id="json-file"
                  type="file"
                  accept=".json"
                  className="hidden"
                  onChange={handleFileUpload}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="json-content">Or Paste JSON</Label>
              <Textarea
                id="json-content"
                value={candidateJson}
                onChange={(e) => setCandidateJson(e.target.value)}
                placeholder='{"schema_version": "1.0", "entities": [...]}'
                rows={10}
                className="mt-2 font-mono text-xs"
              />
            </div>

            {candidateMetadata && (
              <div className="rounded-md border bg-muted/50 p-4">
                <h4 className="mb-2 text-sm font-semibold">Metadata</h4>
                <dl className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Schema Version:</dt>
                    <dd className="font-medium">{candidateMetadata.schema_version}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Source:</dt>
                    <dd className="font-medium">{candidateMetadata.source}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Generated:</dt>
                    <dd className="font-medium">
                      {new Date(candidateMetadata.generated_at).toLocaleString()}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Entities:</dt>
                    <dd className="font-medium">{candidateMetadata.entities.length}</dd>
                  </div>
                </dl>
              </div>
            )}

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleValidate}
                disabled={!candidateJson || validateMutation.isPending}
              >
                {validateMutation.isPending ? "Validating..." : "Validate"}
              </Button>
              <Button
                type="button"
                onClick={handleDiff}
                disabled={!candidateJson || diffMutation.isPending}
              >
                {diffMutation.isPending ? "Comparing..." : "Compare & Continue"}
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Diff */}
        {step === "diff" && diffResult && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-lg border bg-card p-4">
                <div className="text-2xl font-semibold text-green-600">
                  {diffResult.summary.added_count}
                </div>
                <div className="text-xs text-muted-foreground">Added</div>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <div className="text-2xl font-semibold text-blue-600">
                  {diffResult.summary.changed_count}
                </div>
                <div className="text-xs text-muted-foreground">Changed</div>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <div className="text-2xl font-semibold text-red-600">
                  {diffResult.summary.removed_count}
                </div>
                <div className="text-xs text-muted-foreground">Removed</div>
              </div>
            </div>

            {/* Changes by Type */}
            <Tabs defaultValue="changed">
              <TabsList>
                <TabsTrigger value="added">Added ({diffResult.summary.added_count})</TabsTrigger>
                <TabsTrigger value="changed">Changed ({diffResult.summary.changed_count})</TabsTrigger>
                <TabsTrigger value="removed">Removed ({diffResult.summary.removed_count})</TabsTrigger>
              </TabsList>

              {["added", "changed", "removed"].map((changeType) => (
                <TabsContent key={changeType} value={changeType} className="space-y-4">
                  {diffResult.changes
                    .filter((ec) => ec.fields.some((f) => f.change_type === changeType))
                    .map((entityChange) => (
                      <DiffEntityCard
                        key={entityChange.entity_key}
                        entityChange={entityChange}
                        filterType={changeType as any}
                        selectedChanges={selectedChanges}
                        onToggleChange={toggleChange}
                        onToggleEntity={toggleEntityChanges}
                      />
                    ))}
                  {diffResult.changes.filter((ec) =>
                    ec.fields.some((f) => f.change_type === changeType)
                  ).length === 0 && (
                    <div className="py-8 text-center text-sm text-muted-foreground">
                      No {changeType} fields
                    </div>
                  )}
                </TabsContent>
              ))}
            </Tabs>

            <div className="flex items-center justify-between">
              <Button type="button" variant="outline" onClick={() => setStep("upload")}>
                Back
              </Button>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {selectedChanges.size} change(s) selected
                </span>
                <Button
                  type="button"
                  onClick={handleAdopt}
                  disabled={selectedChanges.size === 0}
                >
                  Review & Adopt
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Adopt Review */}
        {step === "adopt" && (
          <div className="space-y-6">
            <div className="rounded-md border border-yellow-500/50 bg-yellow-500/10 p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="mt-0.5 h-5 w-5 text-yellow-600" />
                <div>
                  <h4 className="font-semibold text-yellow-900 dark:text-yellow-100">
                    Review Changes
                  </h4>
                  <p className="mt-1 text-sm text-yellow-800 dark:text-yellow-200">
                    You are about to adopt {selectedChanges.size} change(s). This will update your
                    baseline configuration and may affect listing valuations.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="recalculate"
                checked={recalculateValuations}
                onCheckedChange={(checked) => setRecalculateValuations(checked === true)}
              />
              <Label htmlFor="recalculate" className="text-sm font-normal">
                Recalculate all listing valuations after adoption
              </Label>
            </div>

            <div className="flex items-center justify-between">
              <Button type="button" variant="outline" onClick={() => setStep("diff")}>
                Back to Diff
              </Button>
              <Button
                type="button"
                onClick={handleConfirmAdopt}
                disabled={adoptMutation.isPending}
                variant="default"
              >
                {adoptMutation.isPending ? "Adopting..." : "Confirm & Adopt"}
              </Button>
            </div>
          </div>
        )}

        {/* Step 4: Complete */}
        {step === "complete" && adoptResult && (
          <div className="space-y-6">
            <div className="flex flex-col items-center gap-4 py-8">
              <CheckCircle2 className="h-16 w-16 text-green-600" />
              <div className="text-center">
                <h3 className="text-xl font-semibold">Baseline Adopted Successfully</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  {adoptResult.changes_applied} changes have been applied
                </p>
              </div>
            </div>

            <div className="rounded-md border bg-muted/50 p-4">
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">New Version:</dt>
                  <dd className="font-medium">{adoptResult.new_version}</dd>
                </div>
                {adoptResult.backup_created && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Backup Created:</dt>
                    <dd className="font-medium">Yes</dd>
                  </div>
                )}
                {adoptResult.recalculation_job_id && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Recalculation Job:</dt>
                    <dd className="font-mono text-xs">{adoptResult.recalculation_job_id}</dd>
                  </div>
                )}
              </dl>
            </div>

            <div className="flex items-center justify-center">
              <Button
                type="button"
                onClick={() => {
                  setStep("upload");
                  setCandidateJson("");
                  setCandidateMetadata(null);
                  setDiffResult(null);
                  setSelectedChanges(new Set());
                  setAdoptResult(null);
                  onComplete?.();
                }}
              >
                Done
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface DiffEntityCardProps {
  entityChange: DiffEntityChange;
  filterType: "added" | "changed" | "removed";
  selectedChanges: Set<string>;
  onToggleChange: (entityKey: string, fieldName: string) => void;
  onToggleEntity: (entityKey: string, fields: DiffFieldChange[]) => void;
}

function DiffEntityCard({
  entityChange,
  filterType,
  selectedChanges,
  onToggleChange,
  onToggleEntity,
}: DiffEntityCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const filteredFields = entityChange.fields.filter((f) => f.change_type === filterType);

  if (filteredFields.length === 0) return null;

  const allSelected = filteredFields.every((f) =>
    selectedChanges.has(`${entityChange.entity_key}:${f.field_name}`)
  );

  return (
    <div className="rounded-lg border">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3">
          <Checkbox
            checked={allSelected}
            onCheckedChange={() => onToggleEntity(entityChange.entity_key, filteredFields)}
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-auto p-0"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? (
              <ChevronDown className="mr-2 h-4 w-4" />
            ) : (
              <ChevronRight className="mr-2 h-4 w-4" />
            )}
            <span className="font-semibold">{entityChange.entity_name}</span>
          </Button>
        </div>
        <Badge variant="outline">{filteredFields.length} field(s)</Badge>
      </div>

      {isExpanded && (
        <div className="border-t">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12"></TableHead>
                <TableHead>Field</TableHead>
                <TableHead>Current</TableHead>
                <TableHead>Candidate</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredFields.map((field) => (
                <TableRow key={field.field_name}>
                  <TableCell>
                    <Checkbox
                      checked={selectedChanges.has(
                        `${entityChange.entity_key}:${field.field_name}`
                      )}
                      onCheckedChange={() =>
                        onToggleChange(entityChange.entity_key, field.field_name)
                      }
                    />
                  </TableCell>
                  <TableCell className="font-medium">{field.field_name}</TableCell>
                  <TableCell className="text-sm">
                    {field.current_value !== undefined
                      ? String(field.current_value)
                      : field.current_formula
                      ? field.current_formula
                      : "—"}
                  </TableCell>
                  <TableCell className="text-sm">
                    {field.candidate_value !== undefined
                      ? String(field.candidate_value)
                      : field.candidate_formula
                      ? field.candidate_formula
                      : "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
