"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { apiFetch, cn } from "../../lib/utils";
import {
  ComponentMatch,
  ComponentOverridePayload,
  ConflictResolutionPayload,
  CpuConflict,
  EntityMapping,
  EntityPreview,
  FieldMapping,
  ImportSessionSnapshot,
  SheetMeta
} from "../../types/importer";
import { UploadDropzone } from "./upload-dropzone";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Label } from "../ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";

interface MappingDraftState {
  [entity: string]: EntityMapping;
}

type ConflictAction = "update" | "skip" | "keep";

type ConflictState = Record<string, ConflictAction>;

type ComponentOverrideState = Record<number, { cpu_match?: string | null; gpu_match?: string | null }>;

export function ImporterWorkspace() {
  const [session, setSession] = useState<ImportSessionSnapshot | null>(null);
  const [mappingsDraft, setMappingsDraft] = useState<MappingDraftState>({});
  const [activeEntity, setActiveEntity] = useState<string | null>(null);
  const [conflictState, setConflictState] = useState<ConflictState>({});
  const [overrideState, setOverrideState] = useState<ComponentOverrideState>({});
  const [isUploading, setIsUploading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const hasSession = session !== null;

  const cpuConflicts: CpuConflict[] = useMemo(() => {
    if (!session?.conflicts?.["cpu"]) return [];
    return session.conflicts["cpu"] as CpuConflict[];
  }, [session]);

  const listingPreviewMatches: ComponentMatch[] = useMemo(() => {
    const preview = session?.preview?.["listing"];
    if (!preview?.component_matches) return [];
    return preview.component_matches ?? [];
  }, [session]);

  const entityKeys = useMemo(() => (session ? Object.keys(session.mappings) : []), [session]);

  useEffect(() => {
    if (session) {
      setMappingsDraft(session.mappings);
      setActiveEntity((prev) => prev && session.mappings[prev] ? prev : Object.keys(session.mappings)[0] ?? null);
      const initialConflicts: ConflictState = {};
      cpuConflicts.forEach((conflict) => {
        initialConflicts[conflict.name] = "update";
      });
      setConflictState(initialConflicts);
      setOverrideState({});
    } else {
      setMappingsDraft({});
      setActiveEntity(null);
      setConflictState({});
      setOverrideState({});
    }
  }, [session, cpuConflicts]);

  const handleUpload = useCallback(
    async (file: File) => {
      setError(null);
      setSuccessMessage(null);
      setIsUploading(true);
      try {
        const formData = new FormData();
        formData.append("upload", file);
        const snapshot = await apiFetch<ImportSessionSnapshot>("/v1/imports/sessions", {
          method: "POST",
          body: formData
        });
        setSession(snapshot);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to upload workbook";
        setError(message);
      } finally {
        setIsUploading(false);
      }
    },
    []
  );

  const handleSelectColumn = (entityKey: string, fieldKey: string, column: string | null) => {
    setMappingsDraft((prev) => {
      const entity = prev[entityKey];
      if (!entity) return prev;
      const nextFields = {
        ...entity.fields,
        [fieldKey]: {
          ...entity.fields[fieldKey],
          column,
          status: column ? (entity.fields[fieldKey].status === "auto" ? "manual" : entity.fields[fieldKey].status) : "missing"
        } as FieldMapping
      };
      return {
        ...prev,
        [entityKey]: {
          ...entity,
          fields: nextFields
        }
      };
    });
  };

  const handleSaveMappings = async (entityKey: string) => {
    if (!session) return;
    const entityDraft = mappingsDraft[entityKey];
    if (!entityDraft) return;
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const payload = {
        mappings: {
          [entityKey]: {
            sheet: entityDraft.sheet,
            fields: Object.fromEntries(
              Object.entries(entityDraft.fields).map(([field, details]) => [
                field,
                {
                  column: details.column ?? null,
                  status: details.column ? (details.status === "auto" ? "manual" : details.status) : "missing",
                  confidence: details.column ? details.confidence ?? 1 : 0
                }
              ])
            )
          }
        }
      };
      const snapshot = await apiFetch<ImportSessionSnapshot>(`/v1/imports/sessions/${session.id}/mappings`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setSession(snapshot);
      setSuccessMessage("Mapping updated. Preview and conflicts refreshed.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to update mapping";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleConflictAction = (name: string, action: ConflictAction) => {
    setConflictState((prev) => ({
      ...prev,
      [name]: action
    }));
  };

  const handleOverrideChange = (rowIndex: number, cpuMatch: string | null) => {
    setOverrideState((prev) => ({
      ...prev,
      [rowIndex]: {
        ...prev[rowIndex],
        cpu_match: cpuMatch ?? undefined
      }
    }));
  };

  const handleReset = () => {
    setSession(null);
    setError(null);
    setSuccessMessage(null);
  };

  const canCommit = useMemo(() => {
    if (!session) return false;
    const unresolved = cpuConflicts.some((conflict) => !conflictState[conflict.name]);
    return !isSaving && !isUploading && !isCommitting && !unresolved;
  }, [session, cpuConflicts, conflictState, isSaving, isUploading, isCommitting]);

  const handleCommit = async () => {
    if (!session) return;
    setIsCommitting(true);
    setError(null);
    setSuccessMessage(null);
    const conflict_resolutions: ConflictResolutionPayload[] = Object.entries(conflictState).map(([identifier, action]) => ({
      entity: "cpu",
      identifier,
      action
    }));
    const component_overrides: ComponentOverridePayload[] = Object.entries(overrideState)
      .filter(([, override]) => override.cpu_match || override.gpu_match)
      .map(([rowIndex, override]) => ({
        entity: "listing",
        row_index: Number(rowIndex),
        cpu_match: override.cpu_match ?? null,
        gpu_match: override.gpu_match ?? null
      }));
    try {
      const response = await apiFetch(`/v1/imports/sessions/${session.id}/commit`, {
        method: "POST",
        body: JSON.stringify({
          conflict_resolutions,
          component_overrides,
          notes: null
        })
      });
      const typed = response as { session: ImportSessionSnapshot; counts: Record<string, number> };
      setSession(typed.session);
      setSuccessMessage("Import committed successfully.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to commit import";
      setError(message);
    } finally {
      setIsCommitting(false);
    }
  };

  const renderTabs = () => {
    if (!entityKeys.length || !activeEntity) return null;
    return (
      <div className="flex flex-wrap gap-2">
        {entityKeys.map((entityKey) => (
          <Button
            key={entityKey}
            type="button"
            variant={activeEntity === entityKey ? "default" : "outline"}
            onClick={() => setActiveEntity(entityKey)}
            className="capitalize"
          >
            {entityKey.replace(/_/g, " ")}
          </Button>
        ))}
      </div>
    );
  };

  const sheetMetaForEntity = (entityKey: string): SheetMeta | undefined =>
    session?.sheet_meta.find((meta) => meta.entity === entityKey);

  return (
    <div className="space-y-6">
      {!hasSession && <UploadDropzone onUpload={handleUpload} isUploading={isUploading} />}

      {hasSession && session && (
        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-xl">{session.filename}</CardTitle>
                <CardDescription>Session ID: {session.id}</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  className={cn(
                    "bg-secondary text-secondary-foreground",
                    session.status === "completed" && "bg-emerald-500/10 text-emerald-600"
                  )}
                >
                  {session.status}
                </Badge>
                <Button variant="outline" size="sm" onClick={handleReset}>
                  Start over
                </Button>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div>
                <Label className="text-xs uppercase text-muted-foreground">Detected Sheets</Label>
                <div className="mt-1 space-y-1 text-sm">
                  {session.sheet_meta.map((meta) => (
                    <div key={meta.sheet_name} className="flex items-center justify-between">
                      <span>{meta.sheet_name}</span>
                      <span className="text-muted-foreground">{meta.row_count} rows</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <Label className="text-xs uppercase text-muted-foreground">How it works</Label>
                <p className="mt-1 text-sm text-muted-foreground">
                  Review each entity tab, confirm the column mappings, resolve any conflicts, then commit. We keep a full session history so you can pick up again later.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Field mapping</CardTitle>
              <CardDescription>
                Auto detected mappings are marked accordingly. Update anything that looks off, then save the entity before moving on.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {renderTabs()}
              {activeEntity && mappingsDraft[activeEntity] ? (
                <MappingEditor
                  entityKey={activeEntity}
                  mapping={mappingsDraft[activeEntity]}
                  sheetMeta={sheetMetaForEntity(activeEntity)}
                  onColumnChange={handleSelectColumn}
                />
              ) : (
                <p className="text-sm text-muted-foreground">No mapping details available.</p>
              )}
              {activeEntity && (
                <div className="flex gap-3">
                  <Button type="button" disabled={isSaving} onClick={() => handleSaveMappings(activeEntity)}>
                    {isSaving ? "Saving…" : "Save mapping"}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {activeEntity && session.preview[activeEntity] && (
            <PreviewPanel entityKey={activeEntity} preview={session.preview[activeEntity]} />
          )}

          <ComponentMatchesPanel
            matches={listingPreviewMatches}
            overrides={overrideState}
            onChange={handleOverrideChange}
          />

          <ConflictPanel
            conflicts={cpuConflicts}
            selections={conflictState}
            onChange={handleConflictAction}
          />

          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1 text-sm">
              {error && <p className="text-destructive">{error}</p>}
              {successMessage && <p className="text-emerald-600">{successMessage}</p>}
            </div>
            <div className="flex gap-3">
              <Button type="button" onClick={handleCommit} disabled={!canCommit}>
                {isCommitting ? "Committing…" : "Commit import"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface MappingEditorProps {
  entityKey: string;
  mapping: EntityMapping;
  sheetMeta?: SheetMeta;
  onColumnChange: (entityKey: string, fieldKey: string, column: string | null) => void;
}

function MappingEditor({ entityKey, mapping, sheetMeta, onColumnChange }: MappingEditorProps) {
  const columns = sheetMeta?.columns ?? [];
  const missingFields = Object.values(mapping.fields).filter((field) => field.required && !field.column);

  return (
    <div className="space-y-2">
      {missingFields.length > 0 && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          Missing required fields: {missingFields.map((field) => field.label).join(", ")}
        </div>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-48">Field</TableHead>
            <TableHead>Mapped column</TableHead>
            <TableHead>Suggestions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Object.entries(mapping.fields).map(([fieldKey, field]) => (
            <TableRow key={fieldKey} className={field.required && !field.column ? "border-destructive/40 bg-destructive/5" : undefined}>
              <TableCell>
                <div className="flex flex-col">
                  <span className="font-medium">{field.label}</span>
                  <span className="text-xs text-muted-foreground">{field.required ? "Required" : "Optional"}</span>
                </div>
              </TableCell>
              <TableCell>
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={field.column ?? ""}
                  onChange={(event) => onColumnChange(entityKey, fieldKey, event.target.value || null)}
                >
                  <option value="">— Not mapped —</option>
                  {columns.map((column) => (
                    <option key={column.name} value={column.name}>
                      {column.name}
                    </option>
                  ))}
                </select>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {field.column ? (
                  <span>
                    {field.status === "auto" ? "Auto" : "Manual"} ({Math.round(field.confidence * 100)}%)
                  </span>
                ) : field.suggestions.length ? (
                  <span>
                    {field.suggestions
                      .slice(0, 2)
                      .map((suggestion) => `${suggestion.column} (${Math.round(suggestion.confidence * 100)}%)`)
                      .join(", ")}
                  </span>
                ) : (
                  <span>No suggestions</span>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

interface PreviewPanelProps {
  entityKey: string;
  preview: EntityPreview;
}

function PreviewPanel({ entityKey, preview }: PreviewPanelProps) {
  const rows = preview.rows ?? [];
  if (!rows.length) {
    return null;
  }
  const headers = Object.keys(rows[0]).filter((key) => key !== "__row");
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Preview – {entityKey.replace(/_/g, " ")}</CardTitle>
        <CardDescription>
          Showing the first {rows.length} rows ({preview.total_rows} total). Adjust mappings if values look incorrect.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="max-h-80 overflow-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                {headers.map((header) => (
                  <TableHead key={header} className="capitalize">
                    {header.replace(/_/g, " ")}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row, index) => (
                <TableRow key={index}>
                  <TableCell>{(row["__row"] as number) ?? index}</TableCell>
                  {headers.map((header) => (
                    <TableCell key={header} className="text-sm">
                      {String(row[header] ?? "")}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

interface ComponentMatchesPanelProps {
  matches: ComponentMatch[];
  overrides: ComponentOverrideState;
  onChange: (rowIndex: number, cpuMatch: string | null) => void;
}

function ComponentMatchesPanel({ matches, overrides, onChange }: ComponentMatchesPanelProps) {
  if (!matches.length) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Listing component matches</CardTitle>
        <CardDescription>
          We attempt to match CPUs automatically. Review anything flagged for manual review and override if needed.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {matches.map((match) => {
          const overrideValue = overrides[match.row_index]?.cpu_match ?? null;
          const currentValue = overrideValue ?? match.auto_match ?? "";
          return (
            <div key={match.row_index} className="flex flex-col gap-2 rounded-md border p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Row {match.row_index + 1}</p>
                  <p className="text-sm text-muted-foreground">Source value: {match.value || "(empty)"}</p>
                </div>
                <Badge
                  className={cn(
                    "bg-secondary text-secondary-foreground",
                    match.status === "auto" && "bg-emerald-500/10 text-emerald-600",
                    match.status === "review" && "bg-amber-500/10 text-amber-600",
                    match.status === "unmatched" && "bg-muted text-muted-foreground"
                  )}
                >
                  {match.status === "auto" ? "Auto" : match.status === "review" ? "Needs review" : "Unmatched"}
                </Badge>
              </div>
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div className="flex-1">
                  <Label className="text-xs uppercase text-muted-foreground">Assign CPU</Label>
                  <select
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={currentValue}
                    onChange={(event) => {
                      const value = event.target.value;
                      if (!value) {
                        onChange(match.row_index, null);
                      } else if (value === "__auto__") {
                        onChange(match.row_index, match.auto_match ?? null);
                      } else {
                        onChange(match.row_index, value);
                      }
                    }}
                  >
                    <option value="">Leave unmatched</option>
                    {match.auto_match && (
                      <option value="__auto__">Auto: {match.auto_match}</option>
                    )}
                    {match.suggestions.map((suggestion) => (
                      <option key={suggestion.match} value={suggestion.match}>
                        {suggestion.match} ({Math.round(suggestion.confidence * 100)}%)
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

interface ConflictPanelProps {
  conflicts: CpuConflict[];
  selections: ConflictState;
  onChange: (name: string, action: ConflictAction) => void;
}

function ConflictPanel({ conflicts, selections, onChange }: ConflictPanelProps) {
  if (!conflicts.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Conflicts</CardTitle>
          <CardDescription>No conflicts detected — great job!</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Conflicts</CardTitle>
        <CardDescription>Review existing CPUs and choose how to handle them.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {conflicts.map((conflict) => (
          <div key={conflict.name} className="rounded-md border p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-sm font-medium">{conflict.name}</p>
                <p className="text-xs text-muted-foreground">{conflict.fields.length} differing fields</p>
              </div>
              <div className="flex gap-4 text-sm">
                {(["update", "skip", "keep"] as ConflictAction[]).map((action) => (
                  <label key={action} className="flex items-center gap-2">
                    <input
                      type="radio"
                      name={`conflict-${conflict.name}`}
                      value={action}
                      checked={selections[conflict.name] === action}
                      onChange={() => onChange(conflict.name, action)}
                    />
                    <span className="capitalize">{action}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="mt-3 overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Field</TableHead>
                    <TableHead>Current</TableHead>
                    <TableHead>Incoming</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {conflict.fields.map((field) => (
                    <TableRow key={field.field}>
                      <TableCell className="capitalize">{field.field.replace(/_/g, " ")}</TableCell>
                      <TableCell className="text-sm">{String(field.existing ?? "")}</TableCell>
                      <TableCell className="text-sm">{String(field.incoming ?? "")}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
