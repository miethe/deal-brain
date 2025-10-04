"use client";

import {
  type ColumnDef,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable
} from "@tanstack/react-table";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { Lock } from "lucide-react";

import { track } from "../../lib/analytics";
import { ApiError, apiFetch, cn } from "../../lib/utils";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog";
import { ModalShell } from "../ui/modal-shell";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { DropdownOptionsBuilder } from "./dropdown-options-builder";
import { DefaultValueInput } from "../global-fields/default-value-input";

interface FieldValidation {
  pattern?: string;
  min?: number;
  max?: number;
  min_length?: number;
  max_length?: number;
  [key: string]: unknown;
}

interface FieldRecord {
  id: number;
  entity: string;
  key: string;
  label: string;
  data_type: string;
  description?: string | null;
  required: boolean;
  default_value?: unknown;
  options?: string[] | null;
  is_active: boolean;
  is_locked: boolean;
  visibility: string;
  created_by?: string | null;
  validation?: FieldValidation | null;
  display_order: number;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

interface FieldListResponse {
  fields: FieldRecord[];
}

interface FieldUsageItem {
  field_id: number;
  entity: string;
  key: string;
  total: number;
  counts: Record<string, number>;
}

interface FieldUsageResponse {
  usage: FieldUsageItem[];
}

interface FieldSchemaDefinition {
  key: string;
  label: string;
  data_type: string;
  origin: string;
  required?: boolean;
  description?: string | null;
  options?: string[] | null;
}

interface EntitySchemaResponse {
  entity: string;
  label: string;
  primary_key: string;
  fields: FieldSchemaDefinition[];
}

interface FieldAuditEntry {
  id: number;
  field_id: number;
  action: string;
  actor?: string | null;
  payload?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

interface FieldAuditResponse {
  events: FieldAuditEntry[];
}

type FieldStatus = "active" | "inactive" | "deleted";

interface FieldRow extends FieldRecord {
  status: FieldStatus;
}

interface FieldUsageMap {
  [fieldId: number]: { total: number; counts: Record<string, number> };
}

interface FieldFormValues {
  entity: string;
  label: string;
  key: string;
  data_type: string;
  description: string;
  required: boolean;
  visibility: string;
  is_active: boolean;
  display_order: number;
  default_value: string;
  optionsText: string;
  allowMultiple: boolean;
  validationMin: string;
  validationMax: string;
  validationMinLength: string;
  validationMaxLength: string;
  validationPattern: string;
}

type WizardMode = "create" | "edit";

interface WizardState {
  mode: WizardMode;
  field?: FieldRow;
}

const ENTITY_LABELS: Record<string, string> = {
  listing: "Listings",
  cpu: "CPUs",
  gpu: "GPUs",
  ports_profile: "Ports",
  valuation_rule: "Valuation Rules"
};

const DATA_TYPE_LABELS: Record<string, string> = {
  string: "String",
  text: "Long Text",
  number: "Number",
  boolean: "Boolean",
  enum: "Dropdown",
  multi_select: "Multi-Select Dropdown",
  json: "JSON"
};

const ENTITY_OPTIONS = Object.keys(ENTITY_LABELS);
const TYPE_OPTIONS = ["string", "text", "number", "boolean", "enum", "json"];

const STATUS_OPTIONS: FieldStatus[] = ["active", "inactive", "deleted"];

const DEFAULT_FORM: FieldFormValues = {
  entity: "listing",
  label: "",
  key: "",
  data_type: "string",
  description: "",
  required: false,
  visibility: "public",
  is_active: true,
  display_order: 100,
  default_value: "",
  optionsText: "",
  allowMultiple: false,
  validationMin: "",
  validationMax: "",
  validationMinLength: "",
  validationMaxLength: "",
  validationPattern: ""
};

interface GlobalFieldsTableProps {
  entity?: string;
  hideEntityPicker?: boolean;
}

export function GlobalFieldsTable({ entity, hideEntityPicker = false }: GlobalFieldsTableProps) {
  const queryClient = useQueryClient();
  const [entityFilter, setEntityFilter] = useState<string>(entity ?? "all");
  const [statusFilter, setStatusFilter] = useState<Set<FieldStatus>>(new Set(["active" ]));
  const [searchTerm, setSearchTerm] = useState("");
  const [sorting, setSorting] = useState<SortingState>([{ id: "entity", desc: false }]);
  const [wizardState, setWizardState] = useState<WizardState | null>(null);
  const [auditField, setAuditField] = useState<FieldRow | null>(null);
  const [deleteField, setDeleteField] = useState<FieldRow | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [forceDelete, setForceDelete] = useState(false);

  const fieldsKey = ["fields", "definitions"] as const;
  const usageKey = ["fields", "usage"] as const;

  const {
    data: fieldResponse,
    isLoading,
    error: fieldsError
  } = useQuery<FieldListResponse>({
    queryKey: fieldsKey,
    queryFn: () => apiFetch<FieldListResponse>("/v1/fields?include_inactive=1&include_deleted=1")
  });

  const { data: usageResponse } = useQuery<FieldUsageResponse>({
    queryKey: usageKey,
    queryFn: () => apiFetch<FieldUsageResponse>("/v1/fields/usage"),
    staleTime: 15_000
  });

  const { data: schemaResponse } = useQuery<EntitySchemaResponse>({
    queryKey: ["fields-data", entity ?? entityFilter, "schema"],
    queryFn: () => apiFetch<EntitySchemaResponse>(`/v1/fields-data/${entity ?? entityFilter}/schema`),
    enabled: Boolean(entity ?? (entityFilter !== "all" && entityFilter !== "")),
  });

  const usageMap: FieldUsageMap = useMemo(() => {
    if (!usageResponse) return {};
    return usageResponse.usage.reduce((acc, item) => {
      acc[item.field_id] = { total: item.total, counts: item.counts };
      return acc;
    }, {} as FieldUsageMap);
  }, [usageResponse]);

  const rows: FieldRow[] = useMemo(() => {
    const records = fieldResponse?.fields ?? [];
    const customRows = records.map((field) => ({
      ...field,
      status: resolveStatus(field)
    }));
    if (!entity && (entityFilter === "all" || !schemaResponse)) {
      return customRows;
    }
    const targetEntity = entity ?? entityFilter;
    const coreRows = (schemaResponse?.fields ?? [])
      .filter((field) => field.origin === "core")
      .map((field, index) => ({
        id: -1 - index,
        entity: targetEntity,
        key: field.key,
        label: field.label,
        data_type: field.data_type,
        description: field.description ?? "",
        required: Boolean(field.required),
        default_value: null,
        options: field.options ?? null,
        is_active: true,
        is_locked: true,
        visibility: "system",
        created_by: "system",
        validation: null,
        display_order: index,
        created_at: new Date(0).toISOString(),
        updated_at: new Date(0).toISOString(),
        deleted_at: null,
        status: "active" as FieldStatus
      }) as FieldRow);
    return [...coreRows, ...customRows];
  }, [entity, entityFilter, fieldResponse, schemaResponse]);

  useEffect(() => {
    if (!entity) return;
    setEntityFilter(entity);
  }, [entity]);

  const filteredRows = useMemo(() => {
    return rows.filter((row) => {
      if (entityFilter !== "all" && row.entity !== entityFilter) {
        return false;
      }
      if (statusFilter.size && !statusFilter.has(row.status)) {
        return false;
      }
      if (searchTerm) {
        const normalized = searchTerm.toLowerCase();
        const haystack = `${row.label} ${row.key} ${row.description ?? ""}`.toLowerCase();
        if (!haystack.includes(normalized)) {
          return false;
        }
      }
      return true;
    });
  }, [rows, entityFilter, statusFilter, searchTerm]);

  const columns = useMemo<ColumnDef<FieldRow>[]>(() => {
    return [
      {
        accessorKey: "entity",
        header: "Entity",
        cell: ({ row }) => <Badge className="bg-muted text-xs font-medium text-foreground">{ENTITY_LABELS[row.original.entity] ?? row.original.entity}</Badge>
      },
      {
        accessorKey: "label",
        header: "Label",
        cell: ({ row }) => (
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="font-medium">{row.original.label}</span>
              {row.original.id < 0 ? <Badge variant="outline" className="text-[10px] uppercase">System</Badge> : null}
              {row.original.is_locked ? (
                <div className="flex items-center gap-1 text-muted-foreground" title="Core field - entity, key, and type cannot be changed">
                  <Lock className="h-3 w-3" />
                </div>
              ) : null}
            </div>
            <span className="text-xs text-muted-foreground">{row.original.description || "No description"}</span>
          </div>
        )
      },
      {
        accessorKey: "key",
        header: "Key",
        cell: ({ row }) => <code className="rounded bg-muted px-1.5 py-0.5 text-xs">{row.original.key}</code>
      },
      {
        accessorKey: "data_type",
        header: "Type",
        cell: ({ row }) => <span className="text-sm capitalize">{DATA_TYPE_LABELS[row.original.data_type] ?? row.original.data_type}</span>
      },
      {
        accessorKey: "required",
        header: "Required",
        cell: ({ row }) => <span className="text-sm">{row.original.required ? "Yes" : "No"}</span>
      },
      {
        id: "status",
        header: "Status",
        cell: ({ row }) => <StatusBadge status={row.original.status} />
      },
      {
        id: "usage",
        header: "Usage",
        cell: ({ row }) => {
          if (row.original.id < 0) {
            return <span className="text-xs text-muted-foreground">—</span>;
          }
          const usage = usageMap[row.original.id]?.total ?? 0;
          return <Badge className="bg-secondary text-secondary-foreground">{usage}</Badge>;
        }
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => setWizardState({ mode: "edit", field: row.original })}>
              Edit
            </Button>
            {row.original.id >= 0 && (
              <>
                <Button variant="ghost" size="sm" onClick={() => setAuditField(row.original)}>
                  Audit
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-destructive"
                  onClick={() => {
                    setDeleteField(row.original);
                    setDeleteError(null);
                    setForceDelete(false);
                  }}
                >
                  Delete
                </Button>
              </>
            )}
          </div>
        )
      }
    ];
  }, [usageMap]);

  const table = useReactTable({
    data: filteredRows,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel()
  });

  const createMutation = useMutation({
    mutationFn: async (payload: FieldCreatePayload) => {
      const result = await apiFetch<FieldRecord>("/v1/fields", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      track("field_definition.created", { field_id: result.id, entity: result.entity });
      return result;
    },
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: fieldsKey });
    },
    onSuccess: (record) => {
      queryClient.setQueryData<FieldListResponse | undefined>(fieldsKey, (previous) => {
        if (!previous) return { fields: [record] };
        return { fields: [...previous.fields, record] };
      });
      queryClient.invalidateQueries({ queryKey: usageKey });
    }
  });

  const updateMutation = useMutation({
    mutationFn: async ({ fieldId, payload, force }: { fieldId: number; payload: FieldUpdatePayload; force: boolean }) => {
      const result = await apiFetch<FieldRecord>(`/v1/fields/${fieldId}?force=${force ? 1 : 0}`, {
        method: "PATCH",
        body: JSON.stringify(payload)
      });
      track("field_definition.updated", { field_id: result.id, entity: result.entity });
      return result;
    },
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: fieldsKey });
    },
    onSuccess: (record) => {
      queryClient.setQueryData<FieldListResponse | undefined>(fieldsKey, (previous) => {
        if (!previous) return previous;
        return {
          fields: previous.fields.map((item) => (item.id === record.id ? record : item))
        };
      });
      queryClient.invalidateQueries({ queryKey: usageKey });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async ({ fieldId, hard_delete, force }: { fieldId: number; hard_delete: boolean; force: boolean }) => {
      const query = new URLSearchParams({ hard_delete: hard_delete ? "1" : "0", force: force ? "1" : "0" });
      const result = await apiFetch<FieldUsageItem>(`/v1/fields/${fieldId}?${query.toString()}`, {
        method: "DELETE"
      });
      track("field_definition.deleted", { field_id: fieldId, hard_delete, force });
      return result;
    },
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: fieldsKey });
    },
    onSuccess: (_, variables) => {
      queryClient.setQueryData<FieldListResponse | undefined>(fieldsKey, (previous) => {
        if (!previous) return previous;
        return {
          fields: previous.fields.filter((field) => field.id !== variables.fieldId)
        };
      });
      queryClient.invalidateQueries({ queryKey: usageKey });
    }
  });

  const creationOpen = wizardState?.mode === "create";
  const editingOpen = wizardState?.mode === "edit";

  useEffect(() => {
    if (fieldsError) {
      // eslint-disable-next-line no-console
      console.error("Unable to load fields", fieldsError);
    }
  }, [fieldsError]);

  return (
    <Card className="w-full border-0 shadow-none">
      <CardHeader className="gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>
              {hideEntityPicker && entity ? `${ENTITY_LABELS[entity] ?? entity} fields` : "Global fields"}
            </CardTitle>
            <CardDescription>
              Manage dynamic attributes and audit change history across catalog entities.
            </CardDescription>
          </div>
          <Button onClick={() => setWizardState({ mode: "create" })}>New field</Button>
        </div>
        <FilterBar
          entityFilter={entityFilter}
          onEntityFilterChange={setEntityFilter}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          searchTerm={searchTerm}
          onSearchTermChange={setSearchTerm}
          totalCount={rows.length}
          filteredCount={filteredRows.length}
          showEntityFilter={!hideEntityPicker}
        />
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading field definitions…</p>
        ) : fieldsError ? (
          <ErrorBanner error={fieldsError} />
        ) : (
          <div className="overflow-hidden rounded-md border">
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead
                        key={header.id}
                        className={cn("text-xs font-semibold uppercase", header.column.getCanSort() && "cursor-pointer select-none")}
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getIsSorted() === "asc" && <span className="ml-1 text-[10px]">↑</span>}
                        {header.column.getIsSorted() === "desc" && <span className="ml-1 text-[10px]">↓</span>}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={columns.length} className="h-24 text-center text-sm text-muted-foreground">
                      No fields match the current filters.
                    </TableCell>
                  </TableRow>
                ) : (
                  table.getRowModel().rows.map((row) => (
                    <TableRow key={row.id} className="hover:bg-muted/50">
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id} className="align-top text-sm">
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>

      <FieldWizard
        title={wizardState?.mode === "edit" ? "Edit field" : "Create field"}
        open={Boolean(wizardState)}
        mode={wizardState?.mode ?? "create"}
        field={wizardState?.field}
        lockedEntity={hideEntityPicker ? entity ?? null : null}
        onOpenChange={(open) => {
          if (!open) {
            setWizardState(null);
          }
        }}
        onSubmit={async (values, options) => {
          if (wizardState?.mode === "edit" && wizardState.field) {
            await updateMutation.mutateAsync({
              fieldId: wizardState.field.id,
              payload: values,
              force: options.force
            });
          } else {
            await createMutation.mutateAsync(values as FieldCreatePayload);
          }
          setWizardState(null);
        }}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
        error={
          (createMutation.error as Error | undefined)?.message || (updateMutation.error as Error | undefined)?.message || null
        }
      />

      <AuditDrawer field={auditField} onClose={() => setAuditField(null)} />

      <DeleteDialog
        field={deleteField}
        usage={deleteField ? usageMap[deleteField.id] : undefined}
        force={forceDelete}
        onForceChange={setForceDelete}
        error={deleteError}
        isSubmitting={deleteMutation.isPending}
        onCancel={() => {
          setDeleteField(null);
          setDeleteError(null);
          setForceDelete(false);
        }}
        onConfirm={async (options) => {
          if (!deleteField) return;
          try {
            await deleteMutation.mutateAsync({
              fieldId: deleteField.id,
              hard_delete: options.hardDelete,
              force: options.force
            });
            setDeleteField(null);
            setDeleteError(null);
            setForceDelete(false);
          } catch (error) {
            if (error instanceof ApiError && error.payload && typeof error.payload === "object") {
              const detail = (error.payload as Record<string, unknown>).detail ?? (error.payload as Record<string, unknown>).message;
              setDeleteError(typeof detail === "string" ? detail : "Unable to delete field");
            } else {
              setDeleteError(error instanceof Error ? error.message : "Unable to delete field");
            }
          }
        }}
      />
    </Card>
  );
}

function resolveStatus(field: FieldRecord): FieldStatus {
  if (field.deleted_at) return "deleted";
  if (!field.is_active) return "inactive";
  return "active";
}

function StatusBadge({ status }: { status: FieldStatus }) {
  const styles: Record<FieldStatus, string> = {
    active: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
    inactive: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
    deleted: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
  };
  return <Badge className={cn("text-xs", styles[status])}>{status.toUpperCase()}</Badge>;
}

function FilterBar({
  entityFilter,
  onEntityFilterChange,
  statusFilter,
  onStatusFilterChange,
  searchTerm,
  onSearchTermChange,
  totalCount,
  filteredCount,
  showEntityFilter
}: {
  entityFilter: string;
  onEntityFilterChange: (value: string) => void;
  statusFilter: Set<FieldStatus>;
  onStatusFilterChange: (value: Set<FieldStatus>) => void;
  searchTerm: string;
  onSearchTermChange: (value: string) => void;
  totalCount: number;
  filteredCount: number;
  showEntityFilter: boolean;
}) {
  const toggleStatus = (status: FieldStatus) => {
    const next = new Set(statusFilter);
    if (next.has(status)) {
      next.delete(status);
    } else {
      next.add(status);
    }
    onStatusFilterChange(next);
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {showEntityFilter ? (
        <div className="flex items-center gap-2">
          <Label htmlFor="entity-filter" className="text-xs uppercase text-muted-foreground">
            Entity
          </Label>
          <select
            id="entity-filter"
            className="h-9 rounded-md border border-input bg-background px-2 text-sm"
            value={entityFilter}
            onChange={(event) => onEntityFilterChange(event.target.value)}
          >
            <option value="all">All</option>
            {ENTITY_OPTIONS.map((entity) => (
              <option key={entity} value={entity}>
                {ENTITY_LABELS[entity] ?? entity}
              </option>
            ))}
          </select>
        </div>
      ) : null}

      <div className="flex items-center gap-2">
        <span className="text-xs uppercase text-muted-foreground">Status</span>
        <div className="flex gap-1">
          {STATUS_OPTIONS.map((status) => {
            const isActive = statusFilter.has(status);
            return (
              <button
                key={status}
                type="button"
                className={cn(
                  "rounded-full px-3 py-1 text-xs font-medium",
                  isActive ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                )}
                onClick={() => toggleStatus(status)}
              >
                {status.toUpperCase()}
              </button>
            );
          })}
        </div>
      </div>

      <Input
        value={searchTerm}
        onChange={(event) => onSearchTermChange(event.target.value)}
        placeholder="Search label, key, description"
        className="max-w-xs"
      />

      <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
        <span>
          Showing {filteredCount} of {totalCount}
        </span>
      </div>
    </div>
  );
}

function ErrorBanner({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : "An unexpected error occurred";
  return (
    <div className="rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
      {message}
    </div>
  );
}

type FieldCreatePayload = Pick<
  FieldRecord,
  | "entity"
  | "key"
  | "label"
  | "data_type"
  | "description"
  | "required"
  | "default_value"
  | "options"
  | "is_active"
  | "visibility"
  | "created_by"
  | "validation"
  | "display_order"
>;

type FieldUpdatePayload = Partial<Omit<FieldCreatePayload, "entity" | "key">> & {
  display_order?: number;
};

interface WizardProps {
  title: string;
  open: boolean;
  mode: WizardMode;
  field?: FieldRow;
  lockedEntity?: string | null;
  onOpenChange: (open: boolean) => void;
  onSubmit: (payload: FieldCreatePayload | FieldUpdatePayload, options: { force: boolean }) => Promise<void>;
  isSubmitting: boolean;
  error: string | null;
}

function FieldWizard({ title, open, mode, field, lockedEntity, onOpenChange, onSubmit, isSubmitting, error }: WizardProps) {
  const [step, setStep] = useState(0);
  const [values, setValues] = useState<FieldFormValues>({ ...DEFAULT_FORM });
  const [forceUpdate, setForceUpdate] = useState(false);

  useEffect(() => {
    if (field && open) {
      setValues(fromFieldRecord(field));
      setStep(0);
      setForceUpdate(false);
    } else if (open) {
      const base = { ...DEFAULT_FORM };
      if (lockedEntity) {
        base.entity = lockedEntity;
      }
      setValues(base);
      setStep(0);
      setForceUpdate(false);
    }
  }, [field, open, lockedEntity]);

  const isEdit = mode === "edit" && Boolean(field);

  const handleNext = () => setStep((prev) => Math.min(prev + 1, 2));
  const handlePrev = () => setStep((prev) => Math.max(prev - 1, 0));

  const handleSubmit = async () => {
    const payload = mode === "edit" ? toPayload(values, true) : toPayload(values, false);
    try {
      await onSubmit(payload, { force: forceUpdate });
    } catch (error) {
      // swallow to keep modal open; error is surfaced via props
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <ModalShell
        title={title}
        description={mode === "create" ? "Define label, type, and validation for the new field." : "Edit metadata and validation."}
        footer={
          <div className="flex w-full items-center justify-end gap-2">
            {step > 0 && (
              <Button variant="ghost" type="button" onClick={handlePrev}>
                Back
              </Button>
            )}
            {step < 2 ? (
              <Button type="button" onClick={handleNext} disabled={!canProceed(values, step)}>
                Continue
              </Button>
            ) : (
              <Button type="button" onClick={handleSubmit} disabled={isSubmitting}>
                {isSubmitting ? "Saving…" : "Save field"}
              </Button>
            )}
          </div>
        }
      >
        <div className="space-y-4">
          <StepIndicator currentStep={step} />
          {step === 0 && <WizardBasics values={values} onChange={setValues} isEdit={isEdit} lockedEntity={lockedEntity ?? null} isLocked={field?.is_locked} />}
          {step === 1 && <WizardValidation values={values} onChange={setValues} />}
          {step === 2 && <WizardReview values={values} />}
          {error && <ErrorBanner error={new Error(error)} />}
          {isEdit && !field?.is_locked && (
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={forceUpdate}
                onChange={(event) => setForceUpdate(event.target.checked)}
              />
              Force update (override dependency guardrails)
            </label>
          )}
        </div>
      </ModalShell>
    </Dialog>
  );
}

function WizardBasics({
  values,
  onChange,
  isEdit,
  lockedEntity,
  isLocked
}: {
  values: FieldFormValues;
  onChange: (value: FieldFormValues) => void;
  isEdit: boolean;
  lockedEntity: string | null;
  isLocked?: boolean;
}) {
  return (
    <div className="grid gap-4">
      <div className="grid gap-2">
        <Label>Entity</Label>
        <select
          className="h-9 rounded-md border border-input bg-background px-2 text-sm"
          value={lockedEntity ?? values.entity}
          disabled={isEdit || Boolean(lockedEntity) || isLocked}
          onChange={(event) => onChange({ ...values, entity: event.target.value })}
        >
          {ENTITY_OPTIONS.map((entity) => (
            <option key={entity} value={entity}>
              {ENTITY_LABELS[entity] ?? entity}
            </option>
          ))}
        </select>
        {isLocked && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Lock className="h-3 w-3" />
            Entity cannot be changed for system fields
          </div>
        )}
      </div>
      <div className="grid gap-2">
        <Label>Label</Label>
        <Input
          value={values.label}
          onChange={(event) => {
            const label = event.target.value;
            const key = values.key || slugify(label);
            onChange({ ...values, label, key });
          }}
        />
      </div>
      <div className="grid gap-2">
        <Label>Key</Label>
        <Input
          value={values.key}
          readOnly={isEdit || isLocked}
          onChange={(event) => onChange({ ...values, key: slugify(event.target.value) })}
        />
        <p className="text-xs text-muted-foreground">Unique identifier used in APIs and attributes payloads.</p>
        {isLocked && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Lock className="h-3 w-3" />
            Key cannot be changed for system fields
          </div>
        )}
      </div>
      <div className="grid gap-2">
        <Label>Type</Label>
        <select
          className="h-9 rounded-md border border-input bg-background px-2 text-sm"
          value={values.data_type}
          disabled={isEdit || isLocked}
          onChange={(event) => onChange({ ...values, data_type: event.target.value })}
        >
          {TYPE_OPTIONS.map((type) => (
            <option key={type} value={type}>
              {DATA_TYPE_LABELS[type] ?? type}
            </option>
          ))}
        </select>
        {(isEdit || isLocked) && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Lock className="h-3 w-3" />
            Type cannot be changed to maintain data integrity
          </div>
        )}
        {values.data_type === "enum" && (
          <label className="flex items-center gap-2 text-sm mt-2">
            <input
              type="checkbox"
              checked={values.allowMultiple}
              onChange={(event) => onChange({ ...values, allowMultiple: event.target.checked })}
            />
            Allow Multiple Selections
          </label>
        )}
      </div>
      <div className="grid gap-2">
        <Label>Description</Label>
        <textarea
          className="min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={values.description}
          onChange={(event) => onChange({ ...values, description: event.target.value })}
          placeholder="Explain how this field should be used"
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={values.required}
            onChange={(event) => onChange({ ...values, required: event.target.checked })}
          />
          Required
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={values.is_active}
            onChange={(event) => onChange({ ...values, is_active: event.target.checked })}
          />
          Active
        </label>
      </div>
      <div className="grid gap-2">
        <Label>Visibility</Label>
        <select
          className="h-9 rounded-md border border-input bg-background px-2 text-sm"
          value={values.visibility}
          onChange={(event) => onChange({ ...values, visibility: event.target.value })}
        >
          <option value="public">Public</option>
          <option value="internal">Internal</option>
        </select>
      </div>
      <div className="grid gap-2">
        <Label>Display order</Label>
        <Input
          type="number"
          value={values.display_order}
          onChange={(event) => onChange({ ...values, display_order: Number(event.target.value) })}
        />
      </div>
      <div className="grid gap-2">
        <Label>Default value (Optional)</Label>
        <DefaultValueInput
          fieldType={values.data_type === "enum" && values.allowMultiple ? "multi_select" : values.data_type}
          options={values.optionsText.split(/\r?\n/).map((item) => item.trim()).filter(Boolean)}
          value={values.default_value}
          onChange={(val: any) => onChange({ ...values, default_value: val })}
        />
        <p className="text-xs text-muted-foreground">
          This value will be pre-filled when creating new records
        </p>
      </div>
    </div>
  );
}

function WizardValidation({ values, onChange }: { values: FieldFormValues; onChange: (value: FieldFormValues) => void }) {
  const handleOptionsChange = (options: string[]) => {
    onChange({ ...values, optionsText: options.join("\n") });
  };

  const isEnumerated = values.data_type === "enum" || values.data_type === "multi_select";
  const supportsLengths = values.data_type === "string" || values.data_type === "text";

  // Parse options from optionsText
  const currentOptions = values.optionsText
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);

  return (
    <div className="grid gap-4">
      {isEnumerated && (
        <DropdownOptionsBuilder
          options={currentOptions}
          onChange={handleOptionsChange}
        />
      )}

      {values.data_type === "number" && (
        <div className="grid grid-cols-2 gap-4">
          <div className="grid gap-2">
            <Label>Min</Label>
            <Input
              type="number"
              value={values.validationMin}
              onChange={(event) => onChange({ ...values, validationMin: event.target.value })}
            />
          </div>
          <div className="grid gap-2">
            <Label>Max</Label>
            <Input
              type="number"
              value={values.validationMax}
              onChange={(event) => onChange({ ...values, validationMax: event.target.value })}
            />
          </div>
        </div>
      )}

      {supportsLengths && (
        <div className="grid grid-cols-2 gap-4">
          <div className="grid gap-2">
            <Label>Min length</Label>
            <Input
              type="number"
              value={values.validationMinLength}
              onChange={(event) => onChange({ ...values, validationMinLength: event.target.value })}
            />
          </div>
          <div className="grid gap-2">
            <Label>Max length</Label>
            <Input
              type="number"
              value={values.validationMaxLength}
              onChange={(event) => onChange({ ...values, validationMaxLength: event.target.value })}
            />
          </div>
        </div>
      )}

      {values.data_type === "string" && (
        <div className="grid gap-2">
          <Label>Pattern</Label>
          <Input
            value={values.validationPattern}
            onChange={(event) => onChange({ ...values, validationPattern: event.target.value })}
            placeholder="Regular expression pattern"
          />
        </div>
      )}
    </div>
  );
}

function WizardReview({ values }: { values: FieldFormValues }) {
  const payload = toPayload(values, false);
  return (
    <div className="grid gap-4">
      <div className="rounded-md border border-input bg-muted/20 p-3 text-sm">
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
          <div>
            <dt className="text-xs uppercase text-muted-foreground">Entity</dt>
            <dd>{ENTITY_LABELS[payload.entity] ?? payload.entity}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase text-muted-foreground">Key</dt>
            <dd>{payload.key}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase text-muted-foreground">Type</dt>
            <dd>{DATA_TYPE_LABELS[payload.data_type] ?? payload.data_type}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase text-muted-foreground">Required</dt>
            <dd>{payload.required ? "Yes" : "No"}</dd>
          </div>
        </dl>
      </div>
      <div>
        <Label className="text-xs uppercase text-muted-foreground">Payload preview</Label>
        <pre className="mt-2 max-h-64 overflow-auto rounded-md bg-muted/40 p-3 text-xs">
          {JSON.stringify(payload, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function StepIndicator({ currentStep }: { currentStep: number }) {
  const steps = ["Basics", "Validation", "Review"];
  return (
    <ol className="flex items-center gap-6 text-sm">
      {steps.map((label, index) => {
        const isActive = index === currentStep;
        const isComplete = index < currentStep;
        return (
          <li key={label} className="flex items-center gap-2">
            <span
              className={cn(
                "flex h-6 w-6 items-center justify-center rounded-full border",
                isComplete && "bg-primary text-primary-foreground",
                isActive && !isComplete && "border-primary text-primary",
                !isActive && !isComplete && "border-muted text-muted-foreground"
              )}
            >
              {index + 1}
            </span>
            <span className={cn(isActive ? "font-medium" : "text-muted-foreground")}>{label}</span>
          </li>
        );
      })}
    </ol>
  );
}

function canProceed(values: FieldFormValues, step: number) {
  if (step === 0) {
    return Boolean(values.label && values.key);
  }
  if (step === 1 && (values.data_type === "enum" || values.data_type === "multi_select")) {
    return values.optionsText.trim().length > 0;
  }
  return true;
}

function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/_{2,}/g, "_")
    .replace(/^_+|_+$/g, "");
}

function fromFieldRecord(field: FieldRecord): FieldFormValues {
  const validation = (field.validation ?? {}) as FieldValidation;

  // Convert multi_select back to enum + allowMultiple checkbox
  const isMultiSelect = field.data_type === "multi_select";
  const dataType = isMultiSelect ? "enum" : field.data_type;

  return {
    entity: field.entity,
    label: field.label,
    key: field.key,
    data_type: dataType,
    description: field.description ?? "",
    required: field.required,
    visibility: field.visibility,
    is_active: field.is_active,
    display_order: field.display_order,
    default_value: field.default_value != null ? String(field.default_value) : "",
    optionsText: (field.options ?? []).join("\n"),
    allowMultiple: isMultiSelect,
    validationMin: validation.min != null ? String(validation.min) : "",
    validationMax: validation.max != null ? String(validation.max) : "",
    validationMinLength: validation.min_length != null ? String(validation.min_length) : "",
    validationMaxLength: validation.max_length != null ? String(validation.max_length) : "",
    validationPattern: validation.pattern != null ? String(validation.pattern) : ""
  };
}

function toPayload(values: FieldFormValues, isEdit: true): FieldUpdatePayload;
function toPayload(values: FieldFormValues, isEdit: false): FieldCreatePayload;
function toPayload(values: FieldFormValues, isEdit: boolean): FieldCreatePayload | FieldUpdatePayload {
  // Convert enum + allowMultiple to multi_select
  const dataType = values.data_type === "enum" && values.allowMultiple
    ? "multi_select"
    : values.data_type;

  const base: FieldCreatePayload = {
    entity: values.entity,
    key: values.key,
    label: values.label,
    data_type: dataType,
    description: values.description || null,
    required: values.required,
    default_value: parseDefault(values),
    options: parseOptions(values),
    is_active: values.is_active,
    visibility: values.visibility,
    created_by: undefined,
    validation: buildValidation(values),
    display_order: values.display_order
  };

  if (isEdit) {
    // entity and key cannot change on update
    const { entity: _skipEntity, key: _skipKey, ...rest } = base;
    return rest;
  }

  return base;
}

function parseOptions(values: FieldFormValues): string[] | null {
  if (values.data_type === "enum" || values.data_type === "multi_select") {
    const options = values.optionsText
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);
    return options.length ? options : null;
  }
  return null;
}

function parseDefault(values: FieldFormValues): unknown {
  if (!values.default_value) return null;
  const raw = values.default_value.trim();
  switch (values.data_type) {
    case "number":
      return Number(raw);
    case "boolean":
      return raw.toLowerCase() === "true";
    case "enum":
      return raw;
    case "multi_select":
      return raw.split(/\s*,\s*/).filter(Boolean);
    default:
      return raw;
  }
}

function buildValidation(values: FieldFormValues): Record<string, unknown> | null {
  const validation: Record<string, unknown> = {};

  if (values.data_type === "number") {
    if (values.validationMin) {
      validation.min = Number(values.validationMin);
    }
    if (values.validationMax) {
      validation.max = Number(values.validationMax);
    }
  }

  if (values.data_type === "string" || values.data_type === "text") {
    if (values.validationMinLength) {
      validation.min_length = Number(values.validationMinLength);
    }
    if (values.validationMaxLength) {
      validation.max_length = Number(values.validationMaxLength);
    }
  }

  if (values.data_type === "string" && values.validationPattern) {
    validation.pattern = values.validationPattern;
  }

  return Object.keys(validation).length ? validation : null;
}

interface DeleteDialogProps {
  field: FieldRow | null;
  usage?: { total: number; counts: Record<string, number> };
  force: boolean;
  onForceChange: (value: boolean) => void;
  error: string | null;
  isSubmitting: boolean;
  onCancel: () => void;
  onConfirm: (options: { force: boolean; hardDelete: boolean }) => Promise<void>;
}

function DeleteDialog({ field, usage, force, onForceChange, error, isSubmitting, onCancel, onConfirm }: DeleteDialogProps) {
  const [hardDelete, setHardDelete] = useState(false);

  useEffect(() => {
    if (!field) {
      setHardDelete(false);
    }
  }, [field]);

  return (
    <Dialog open={Boolean(field)} onOpenChange={(open) => (open ? null : onCancel())}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete field</DialogTitle>
        </DialogHeader>
        {field && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {usage?.total
                ? `Field "${field.label}" is currently used ${usage.total} time(s). You can deactivate it or force delete if you understand the impact.`
                : `Are you sure you want to delete "${field.label}"? This action cannot be undone.`}
            </p>
            {usage?.counts && Object.keys(usage.counts).length > 0 && (
              <div className="rounded-md border border-amber-400/60 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                <p className="font-medium">Usage breakdown</p>
                <ul className="mt-1 space-y-1">
                  {Object.entries(usage.counts).map(([entity, count]) => (
                    <li key={entity}>
                      {ENTITY_LABELS[entity] ?? entity}: {count}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={force} onChange={(event) => onForceChange(event.target.checked)} />
                Force delete (overrides dependency checks)
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={hardDelete} onChange={(event) => setHardDelete(event.target.checked)} />
                Permanently remove (hard delete)
              </label>
            </div>
            {error && <ErrorBanner error={new Error(error)} />}
          </div>
        )}
        <DialogFooter>
          <div className="flex gap-2">
            <Button variant="ghost" type="button" onClick={onCancel}>
              Cancel
            </Button>
            <Button
              variant="outline"
              type="button"
              className="text-destructive"
              disabled={!field || isSubmitting}
              onClick={() => field && onConfirm({ force, hardDelete })}
            >
              {isSubmitting ? "Deleting…" : "Confirm delete"}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function AuditDrawer({ field, onClose }: { field: FieldRow | null; onClose: () => void }) {
  const auditKey = ["fields", "history", field?.id] as const;
  const { data, isLoading, error } = useQuery<FieldAuditResponse>({
    queryKey: auditKey,
    queryFn: () => apiFetch<FieldAuditResponse>(`/v1/fields/${field?.id}/history`),
    enabled: Boolean(field)
  });

  return (
    <Dialog open={Boolean(field)} onOpenChange={(open) => (open ? null : onClose())}>
      <DialogContent className="ml-auto h-[80vh] max-w-2xl overflow-hidden">
        <DialogHeader>
          <DialogTitle>Audit history</DialogTitle>
          {field && <p className="text-sm text-muted-foreground">{field.label}</p>}
        </DialogHeader>
        <div className="h-full overflow-hidden">
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading audit entries…</p>
          ) : error ? (
            <ErrorBanner error={error} />
          ) : (
            <div className="h-full overflow-y-auto pr-2">
              <ul className="space-y-3 text-sm">
                {data?.events.map((event) => (
                  <li key={event.id} className="rounded-md border border-muted bg-background p-3">
                    <div className="flex items-center justify-between">
                      <span className="font-medium capitalize">{event.action.replace("_", " ")}</span>
                      <span className="text-xs text-muted-foreground">{new Date(event.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Actor: {event.actor ?? "system"}</p>
                    {event.payload && (
                      <pre className="mt-2 overflow-auto rounded bg-muted/40 p-2 text-xs">
                        {JSON.stringify(event.payload, null, 2)}
                      </pre>
                    )}
                  </li>
                ))}
                {!data?.events.length && <p className="text-sm text-muted-foreground">No audit activity yet.</p>}
              </ul>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="ghost" type="button" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
