"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { AlertTriangle, CheckCircle2, XCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Import preview data types
 */
export interface DuplicateMatch {
  id: number;
  match_score: number; // 0.0 to 1.0
  match_type: "exact" | "high" | "medium" | "low";
  existing_data: Record<string, unknown>;
  differences: string[];
}

export interface ImportPreviewData {
  import_type: "listing" | "collection";
  new_data: Record<string, unknown>;
  duplicate_matches: DuplicateMatch[];
  validation_errors: string[];
  validation_warnings: string[];
}

interface ImportPreviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  previewData: ImportPreviewData | null;
  onConfirm: (data: {
    importData: Record<string, unknown>;
    duplicateAction: "skip" | "merge" | "create_new";
    selectedDuplicateId?: number;
  }) => Promise<void>;
  isConfirming?: boolean;
}

/**
 * Import Preview Modal
 *
 * Shows parsed import data with:
 * - Data preview and editing
 * - Duplicate detection with comparison
 * - Merge/skip/create new options
 * - Validation errors and warnings
 */
export function ImportPreviewModal({
  open,
  onOpenChange,
  previewData,
  onConfirm,
  isConfirming = false,
}: ImportPreviewModalProps) {
  const [editedData, setEditedData] = useState<Record<string, unknown>>({});
  const [duplicateAction, setDuplicateAction] = useState<"skip" | "merge" | "create_new">(
    "create_new"
  );
  const [selectedDuplicateId, setSelectedDuplicateId] = useState<number | undefined>();

  // Reset state when modal opens with new data
  useState(() => {
    if (previewData) {
      setEditedData(previewData.new_data);
      if (previewData.duplicate_matches.length > 0) {
        setSelectedDuplicateId(previewData.duplicate_matches[0].id);
        setDuplicateAction("merge");
      } else {
        setDuplicateAction("create_new");
      }
    }
  });

  if (!previewData) return null;

  const hasDuplicates = previewData.duplicate_matches.length > 0;
  const hasErrors = previewData.validation_errors.length > 0;
  const hasWarnings = previewData.validation_warnings.length > 0;

  const handleConfirm = async () => {
    await onConfirm({
      importData: editedData,
      duplicateAction,
      selectedDuplicateId: duplicateAction === "merge" ? selectedDuplicateId : undefined,
    });
  };

  const getMatchScoreColor = (score: number) => {
    if (score >= 0.9) return "text-red-600 dark:text-red-400";
    if (score >= 0.7) return "text-orange-600 dark:text-orange-400";
    if (score >= 0.5) return "text-yellow-600 dark:text-yellow-400";
    return "text-blue-600 dark:text-blue-400";
  };

  const getMatchTypeLabel = (type: string) => {
    const labels = {
      exact: "Exact Match",
      high: "High Confidence",
      medium: "Medium Confidence",
      low: "Low Confidence",
    };
    return labels[type as keyof typeof labels] || type;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            Import Preview - {previewData.import_type === "listing" ? "Listing" : "Collection"}
          </DialogTitle>
          <DialogDescription>
            Review the imported data and resolve any duplicates before confirming.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Validation Errors */}
          {hasErrors && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>
                <div className="font-semibold mb-1">Validation Errors:</div>
                <ul className="list-disc list-inside space-y-1">
                  {previewData.validation_errors.map((error, i) => (
                    <li key={i} className="text-sm">
                      {error}
                    </li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {/* Validation Warnings */}
          {hasWarnings && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <div className="font-semibold mb-1">Warnings:</div>
                <ul className="list-disc list-inside space-y-1">
                  {previewData.validation_warnings.map((warning, i) => (
                    <li key={i} className="text-sm">
                      {warning}
                    </li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {/* Duplicate Detection */}
          {hasDuplicates && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  Potential Duplicates Detected
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <RadioGroup value={duplicateAction} onValueChange={(v) => setDuplicateAction(v as typeof duplicateAction)}>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="skip" id="skip" />
                    <Label htmlFor="skip" className="cursor-pointer">
                      Skip import (don't create or modify anything)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="merge" id="merge" />
                    <Label htmlFor="merge" className="cursor-pointer">
                      Merge with existing item
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="create_new" id="create_new" />
                    <Label htmlFor="create_new" className="cursor-pointer">
                      Create as new item
                    </Label>
                  </div>
                </RadioGroup>

                {duplicateAction === "merge" && (
                  <div className="space-y-3 mt-4">
                    <Label>Select item to merge with:</Label>
                    {previewData.duplicate_matches.map((match) => (
                      <Card
                        key={match.id}
                        className={cn(
                          "cursor-pointer transition-colors",
                          selectedDuplicateId === match.id
                            ? "border-primary bg-accent"
                            : "hover:border-primary/50"
                        )}
                        onClick={() => setSelectedDuplicateId(match.id)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className={getMatchScoreColor(match.match_score)}>
                                  {getMatchTypeLabel(match.match_type)} ({(match.match_score * 100).toFixed(0)}%)
                                </Badge>
                              </div>
                              <div className="text-sm space-y-1">
                                <div className="font-semibold">
                                  {String(match.existing_data.title || match.existing_data.name || "Untitled")}
                                </div>
                                {match.differences.length > 0 && (
                                  <div className="text-muted-foreground">
                                    <div className="font-medium">Differences:</div>
                                    <ul className="list-disc list-inside ml-2">
                                      {match.differences.slice(0, 3).map((diff, i) => (
                                        <li key={i} className="text-xs">
                                          {diff}
                                        </li>
                                      ))}
                                      {match.differences.length > 3 && (
                                        <li className="text-xs">
                                          +{match.differences.length - 3} more...
                                        </li>
                                      )}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            </div>
                            {selectedDuplicateId === match.id && (
                              <CheckCircle2 className="h-5 w-5 text-primary shrink-0" />
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Data Preview and Editing */}
          <Tabs defaultValue="preview" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="preview">Preview</TabsTrigger>
              <TabsTrigger value="edit">Edit Data</TabsTrigger>
            </TabsList>

            <TabsContent value="preview" className="space-y-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Import Data</CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="grid grid-cols-1 gap-3 text-sm">
                    {Object.entries(editedData).map(([key, value]) => (
                      <div key={key} className="grid grid-cols-3 gap-2">
                        <dt className="font-semibold text-muted-foreground capitalize">
                          {key.replace(/_/g, " ")}:
                        </dt>
                        <dd className="col-span-2">
                          {value === null || value === undefined
                            ? "—"
                            : typeof value === "object"
                            ? JSON.stringify(value)
                            : String(value)}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="edit" className="space-y-3">
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  You can edit the imported data before confirming. Changes will be saved when you confirm the import.
                </AlertDescription>
              </Alert>
              <Card>
                <CardContent className="pt-6 space-y-4">
                  {Object.entries(editedData).map(([key, value]) => (
                    <div key={key} className="space-y-2">
                      <Label htmlFor={`edit-${key}`} className="capitalize">
                        {key.replace(/_/g, " ")}
                      </Label>
                      {typeof value === "string" && value.length > 100 ? (
                        <Textarea
                          id={`edit-${key}`}
                          value={String(value || "")}
                          onChange={(e) =>
                            setEditedData((prev) => ({ ...prev, [key]: e.target.value }))
                          }
                          rows={3}
                        />
                      ) : (
                        <Input
                          id={`edit-${key}`}
                          value={value === null || value === undefined ? "" : String(value)}
                          onChange={(e) =>
                            setEditedData((prev) => ({ ...prev, [key]: e.target.value }))
                          }
                        />
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isConfirming}
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isConfirming || hasErrors || (duplicateAction === "merge" && !selectedDuplicateId)}
          >
            {isConfirming ? "Confirming..." : "Confirm Import"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
