"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { apiFetch } from "../../lib/utils";
import { Button } from "../ui/button";
import { DataGrid } from "../ui/data-grid";
import { Dialog, DialogTrigger } from "../ui/dialog";
import { Badge } from "../ui/badge";
import { ModalShell } from "../ui/modal-shell";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { ColumnDef } from "@tanstack/react-table";

interface FieldDefinition {
  key: string;
  label: string;
  data_type: string;
  origin: "core" | "custom";
  required?: boolean;
  description?: string | null;
  options?: string[] | null;
  is_active?: boolean;
}

interface EntitySchemaResponse {
  entity: string;
  label: string;
  primary_key: string;
  fields: FieldDefinition[];
}

interface RecordResponse {
  id: number;
  fields: Record<string, unknown>;
  attributes: Record<string, unknown>;
}

interface RecordsListResponse {
  entity: string;
  label: string;
  records: RecordResponse[];
  pagination: {
    limit: number;
    offset: number;
    total: number;
  };
}

interface GlobalFieldsDataTabProps {
  entity: string;
}

export function GlobalFieldsDataTab({ entity }: GlobalFieldsDataTabProps) {
  const queryClient = useQueryClient();
  const [activeRecord, setActiveRecord] = useState<RecordResponse | null>(null);
  const [isModalOpen, setModalOpen] = useState(false);
  const [mode, setMode] = useState<"create" | "edit">("create");

  const { data: schema, isLoading: schemaLoading } = useQuery<EntitySchemaResponse>({
    queryKey: ["fields-data", entity, "schema"],
    queryFn: () => apiFetch<EntitySchemaResponse>(`/v1/fields-data/${entity}/schema`),
  });

  const { data: records, isLoading: recordsLoading } = useQuery<RecordsListResponse>({
    queryKey: ["fields-data", entity, "records"],
    queryFn: () => apiFetch<RecordsListResponse>(`/v1/fields-data/${entity}/records`),
    enabled: Boolean(schema),
  });

  const createMutation = useMutation({
    mutationFn: async (payload: RecordPayload) => {
      return apiFetch<RecordResponse>(`/v1/fields-data/${entity}/records`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fields-data", entity, "records"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ recordId, payload }: { recordId: number; payload: RecordPayload }) => {
      return apiFetch<RecordResponse>(`/v1/fields-data/${entity}/records/${recordId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fields-data", entity, "records"] });
    },
  });

  const columns = useMemo<ColumnDef<RecordResponse>[]>(() => {
    if (!schema) return [];
    const defs = schema.fields;

    const base: ColumnDef<RecordResponse>[] = [
      {
        header: "ID",
        accessorKey: "id",
        size: 60,
        cell: ({ row }) => <span className="font-mono text-xs text-muted-foreground">{row.original.id}</span>,
      },
    ];

    const dataColumns = defs.map((field) => ({
      id: field.key,
      header: () => (
        <div className="flex flex-col">
          <span>{field.label}</span>
          <span className="text-[10px] uppercase text-muted-foreground">{field.origin}</span>
        </div>
      ),
      accessorFn: (row: RecordResponse) => {
        return field.origin === "core" ? row.fields?.[field.key] ?? null : row.attributes?.[field.key] ?? null;
      },
      cell: ({ getValue }) => renderCellValue(getValue(), field),
    }));

    const actionColumn: ColumnDef<RecordResponse> = {
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            setActiveRecord(row.original);
            setMode("edit");
            setModalOpen(true);
          }}
        >
          Edit
        </Button>
      ),
    };

    return [...base, ...dataColumns, actionColumn];
  }, [schema]);

  const handleCreate = () => {
    setActiveRecord(null);
    setMode("create");
    setModalOpen(true);
  };

  const handleSubmit = async (payload: RecordPayload) => {
    if (mode === "create") {
      await createMutation.mutateAsync(payload);
    } else if (activeRecord) {
      await updateMutation.mutateAsync({ recordId: activeRecord.id, payload });
    }
    setModalOpen(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold tracking-tight">{schema?.label ?? "Fields"} data</h2>
          <p className="text-sm text-muted-foreground">Create and edit catalog records using the global field schema.</p>
        </div>
        <Dialog open={isModalOpen} onOpenChange={setModalOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleCreate}>Add entry</Button>
          </DialogTrigger>
          {schema ? (
            <RecordModal
              schema={schema}
              mode={mode}
              record={activeRecord}
              isSubmitting={createMutation.isPending || updateMutation.isPending}
              onSubmit={handleSubmit}
            />
          ) : null}
        </Dialog>
      </div>
      <DataGrid columns={columns} data={records?.records ?? []} loading={schemaLoading || recordsLoading} enableFilters />
    </div>
  );
}

interface RecordPayload {
  fields: Record<string, unknown>;
  attributes: Record<string, unknown>;
}

interface RecordModalProps {
  schema: EntitySchemaResponse;
  mode: "create" | "edit";
  record: RecordResponse | null;
  isSubmitting: boolean;
  onSubmit: (payload: RecordPayload) => Promise<void>;
}

function RecordModal({ schema, mode, record, isSubmitting, onSubmit }: RecordModalProps) {
  const [formErrors, setFormErrors] = useState<string | null>(null);

  return (
    <ModalShell
      title={mode === "create" ? `Add ${schema.label}` : `Edit ${schema.label}`}
      description="Core fields save directly to the catalog; custom fields persist in attributes."
      footer={
        <div className="flex w-full items-center justify-end gap-3">
          {formErrors ? <span className="text-sm text-destructive">{formErrors}</span> : null}
          <Button type="submit" form="record-modal-form" disabled={isSubmitting}>
            {isSubmitting ? "Saving…" : "Save"}
          </Button>
        </div>
      }
    >
      <form
        id="record-modal-form"
        className="grid gap-4"
        onSubmit={async (event) => {
          event.preventDefault();
          setFormErrors(null);
          const formData = new FormData(event.currentTarget);
          const payload: RecordPayload = { fields: {}, attributes: {} };
          try {
            for (const field of schema.fields) {
              const raw = formData.get(field.key);
              const value = raw instanceof File ? null : raw;
              if (value === null || value === "") {
                continue;
              }
              const parsed = parseFieldValue(field, value.toString());
              if (field.origin === "core") {
                payload.fields[field.key] = parsed;
              } else {
                payload.attributes[field.key] = parsed;
              }
            }
            await onSubmit(payload);
          } catch (error) {
            const message = error instanceof Error ? error.message : "Unable to save";
            setFormErrors(message);
          }
        }}
      >
        {schema.fields.map((field) => {
          const initialValue = record ? (field.origin === "core" ? record.fields?.[field.key] : record.attributes?.[field.key]) : undefined;
          return <FieldInput key={field.key} field={field} defaultValue={initialValue} />;
        })}
      </form>
    </ModalShell>
  );
}

function FieldInput({ field, defaultValue }: { field: FieldDefinition; defaultValue: unknown }) {
  const description = field.description;
  const required = Boolean(field.required);

  const value = formatDefaultValue(field, defaultValue);

  if (field.data_type === "boolean") {
    return (
      <div className="grid gap-1">
        <Label className="text-sm font-medium" htmlFor={`field-${field.key}`}>
          {field.label}
          {field.origin === "custom" ? <Badge className="ml-2" variant="secondary">Custom</Badge> : null}
        </Label>
        <select id={`field-${field.key}`} name={field.key} defaultValue={value ?? "false"} className="rounded-md border px-3 py-2 text-sm">
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
        {description ? <p className="text-xs text-muted-foreground">{description}</p> : null}
      </div>
    );
  }

  if (field.data_type === "enum" && field.options?.length) {
    return (
      <div className="grid gap-1">
        <Label className="text-sm font-medium" htmlFor={`field-${field.key}`}>
          {field.label}
          {field.origin === "custom" ? <Badge className="ml-2" variant="secondary">Custom</Badge> : null}
        </Label>
        <select id={`field-${field.key}`} name={field.key} defaultValue={value ?? ""} className="rounded-md border px-3 py-2 text-sm">
          <option value="">—</option>
          {field.options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        {description ? <p className="text-xs text-muted-foreground">{description}</p> : null}
      </div>
    );
  }

  if (field.data_type === "multi_select") {
    return (
      <div className="grid gap-1">
        <Label className="text-sm font-medium" htmlFor={`field-${field.key}`}>
          {field.label}
          {field.origin === "custom" ? <Badge className="ml-2" variant="secondary">Custom</Badge> : null}
        </Label>
        <textarea
          id={`field-${field.key}`}
          name={field.key}
          defaultValue={value ?? ""}
          rows={2}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
        {description ? <p className="text-xs text-muted-foreground">Comma separated values.</p> : null}
      </div>
    );
  }

  const inputType = field.data_type === "number" ? "number" : "text";

  return (
    <div className="grid gap-1">
      <Label className="text-sm font-medium" htmlFor={`field-${field.key}`}>
        {field.label}
        {required ? <span className="ml-1 text-xs text-destructive">*</span> : null}
        {field.origin === "custom" ? <Badge className="ml-2" variant="secondary">Custom</Badge> : null}
      </Label>
      <Input id={`field-${field.key}`} name={field.key} type={inputType} defaultValue={value ?? ""} />
      {description ? <p className="text-xs text-muted-foreground">{description}</p> : null}
    </div>
  );
}

function renderCellValue(value: unknown, field: FieldDefinition) {
  if (value === null || value === undefined || value === "") {
    return <span className="text-muted-foreground">—</span>;
  }
  if (Array.isArray(value)) {
    return <span>{value.join(", ")}</span>;
  }
  if (field.data_type === "boolean") {
    return <Badge variant={value ? "default" : "secondary"}>{value ? "True" : "False"}</Badge>;
  }
  if (field.data_type === "enum" && typeof value === "string") {
    return <Badge variant="outline">{value}</Badge>;
  }
  if (typeof value === "number") {
    return <span>{value}</span>;
  }
  return <span>{String(value)}</span>;
}

function parseFieldValue(field: FieldDefinition, value: string): unknown {
  if (value === "") return null;
  switch (field.data_type) {
    case "number":
      return Number(value);
    case "boolean":
      return value === "true";
    case "multi_select":
      return value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    default:
      return value;
  }
}

function formatDefaultValue(field: FieldDefinition, raw: unknown) {
  if (raw === null || raw === undefined) {
    if (field.data_type === "boolean") return "false";
    return "";
  }
  if (Array.isArray(raw)) {
    return raw.join(", ");
  }
  return String(raw);
}
