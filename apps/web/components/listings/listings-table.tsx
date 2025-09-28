"use client";

import {
  type Column,
  type ColumnDef,
  type ColumnFiltersState,
  type GroupingState,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getExpandedRowModel,
  getFilteredRowModel,
  getGroupedRowModel,
  getSortedRowModel,
  useReactTable
} from "@tanstack/react-table";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { apiFetch, cn } from "../../lib/utils";
import { ListingFieldSchema, ListingRecord, ListingSchemaResponse } from "../../types/listings";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader } from "../ui/card";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";

interface ListingRow extends ListingRecord {
  cpu_name?: string | null;
  gpu_name?: string | null;
}

interface BulkEditState {
  fieldKey: string;
  value: string;
}

interface FieldConfig extends ListingFieldSchema {
  origin: "core" | "custom";
  options: string[] | null | undefined;
}

const DEFAULT_BULK_STATE: BulkEditState = {
  fieldKey: "",
  value: ""
};

export function ListingsTable() {
  const queryClient = useQueryClient();
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [sorting, setSorting] = useState<SortingState>([{ id: "created_at", desc: true }]);
  const [grouping, setGrouping] = useState<GroupingState>([]);
  const [rowSelection, setRowSelection] = useState({});
  const [bulkState, setBulkState] = useState<BulkEditState>({ ...DEFAULT_BULK_STATE });
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [bulkMessage, setBulkMessage] = useState<string | null>(null);
  const [isBulkSubmitting, setIsBulkSubmitting] = useState(false);

  const { data: schema, isLoading: isSchemaLoading, error: schemaError } = useQuery<ListingSchemaResponse>({
    queryKey: ["listings", "schema"],
    queryFn: () => apiFetch<ListingSchemaResponse>("/v1/listings/schema")
  });

  const fieldConfigs: FieldConfig[] = useMemo(() => {
    if (!schema) return [];
    const core = schema.core_fields.map((field) => ({
      ...field,
      origin: "core" as const,
      options: field.options ?? null
    }));
    const custom = (schema.custom_fields || [])
      .filter((field) => field.is_active && !field.deleted_at)
      .map((field) => ({
        key: field.key,
        label: field.label,
        data_type: field.data_type,
        required: field.required,
        editable: true,
        description: field.description,
        options: field.options ?? null,
        validation: field.validation ?? null,
        origin: "custom" as const
      }));
    return [...core, ...custom];
  }, [schema]);

  const fieldMap = useMemo(() => {
    const map = new Map<string, FieldConfig>();
    fieldConfigs.forEach((field) => {
      map.set(field.key, field);
    });
    return map;
  }, [fieldConfigs]);

  const { data: listingsData, isLoading: isListingsLoading, error: listingsError } = useQuery<ListingRecord[]>({
    queryKey: ["listings", "records"],
    queryFn: () => apiFetch<ListingRecord[]>("/v1/listings"),
    enabled: !!schema
  });

  const listings: ListingRow[] = useMemo(() => {
    if (!listingsData) return [];
    return listingsData.map((item) => ({
      ...item,
      attributes: item.attributes ?? {},
      cpu_name: item.cpu?.name ?? null,
      gpu_name: item.gpu?.name ?? null
    }));
  }, [listingsData]);

  const inlineMutation = useMutation({
    mutationFn: async ({ listingId, field, value }: { listingId: number; field: FieldConfig; value: unknown }) => {
      const payload = buildUpdatePayload(field, value);
      return apiFetch<ListingRecord>(`/v1/listings/${listingId}`, {
        method: "PATCH",
        body: JSON.stringify(payload)
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings", "records"] });
      setInlineError(null);
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Unable to save changes";
      setInlineError(message);
    }
  });

  const handleInlineSave = useCallback(
    (listingId: number, field: FieldConfig, rawValue: string | string[] | boolean | null) => {
      const parsed = parseFieldValue(field, rawValue);
      inlineMutation.mutate({ listingId, field, value: parsed });
    },
    [inlineMutation]
  );

  const handleBulkSubmit = async () => {
    if (!bulkState.fieldKey || !listings.length) return;
    const field = fieldConfigs.find((item) => item.key === bulkState.fieldKey);
    if (!field) return;

    const selectedIds = Object.entries(rowSelection)
      .filter(([, value]) => value)
      .map(([key]) => Number(key));
    if (!selectedIds.length) return;

    setIsBulkSubmitting(true);
    setBulkMessage(null);
    try {
      const parsedValue = parseFieldValue(field, bulkState.value);
      const payload = buildBulkPayload(field, parsedValue, selectedIds);
      await apiFetch("/v1/listings/bulk-update", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      queryClient.invalidateQueries({ queryKey: ["listings", "records"] });
      setBulkMessage(`Applied changes to ${selectedIds.length} listing(s).`);
      setRowSelection({});
      setBulkState({ ...DEFAULT_BULK_STATE });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Bulk update failed";
      setBulkMessage(message);
    } finally {
      setIsBulkSubmitting(false);
    }
  };

  const columns = useMemo<ColumnDef<ListingRow>[]>(() => {
    const titleConfig = fieldMap.get("title");

    const baseColumns: ColumnDef<ListingRow>[] = [
      {
        id: "select",
        header: ({ table }) => (
          <input
            type="checkbox"
            aria-label="Select all"
            checked={table.getIsAllPageRowsSelected()}
            onChange={table.getToggleAllPageRowsSelectedHandler()}
          />
        ),
        cell: ({ row }) => (
          <input
            type="checkbox"
            aria-label="Select row"
            checked={row.getIsSelected()}
            disabled={!row.getCanSelect()}
            onChange={row.getToggleSelectedHandler()}
          />
        ),
        enableSorting: false,
        enableColumnFilter: false,
        size: 32
      },
      {
        header: "Title",
        accessorKey: "title",
        cell: ({ row }) => (
          <div className="flex flex-col gap-1">
            {titleConfig ? (
              <EditableCell
                listingId={row.original.id}
                field={titleConfig}
                value={row.original.title}
                onSave={handleInlineSave}
                isSaving={inlineMutation.isPending}
              />
            ) : (
              <span className="font-medium text-foreground">{row.original.title}</span>
            )}
            <span className="text-xs text-muted-foreground">{row.original.gpu_name ?? "No dedicated GPU"}</span>
          </div>
        ),
        size: 240
      },
      {
        header: "CPU",
        accessorKey: "cpu_name",
        enableSorting: true,
        size: 150
      },
      {
        header: "Adjusted",
        accessorKey: "adjusted_price_usd",
        cell: ({ getValue }) => formatCurrency(Number(getValue() ?? 0)),
        meta: { isNumeric: true },
        size: 120
      },
      {
        header: "$/CPU Mark",
        accessorKey: "dollar_per_cpu_mark",
        cell: ({ getValue }) => formatNumber(getValue() as number | null | undefined),
        meta: { isNumeric: true },
        size: 120
      },
      {
        header: "Composite",
        accessorKey: "score_composite",
        cell: ({ getValue }) => formatNumber(getValue() as number | null | undefined),
        meta: { isNumeric: true },
        size: 120
      }
    ];

    const hiddenEditableKeys = new Set(["title"]);

    const editableColumns: ColumnDef<ListingRow>[] = fieldConfigs
      .filter((config) => config.editable && !hiddenEditableKeys.has(config.key))
      .map((config) => ({
        id: config.key,
        header: config.label,
        accessorFn: (row) => (config.origin === "core" ? (row as any)[config.key] : row.attributes?.[config.key]),
        cell: ({ row, getValue }) => (
          <EditableCell
            listingId={row.original.id}
            field={config}
            value={getValue() as unknown}
            onSave={handleInlineSave}
            isSaving={inlineMutation.isPending}
          />
        ),
        meta: { origin: config.origin, dataType: config.data_type },
        size: 160
      }));

    return [...baseColumns, ...editableColumns];
  }, [fieldConfigs, fieldMap, inlineMutation.isPending, handleInlineSave]);

  const table = useReactTable({
    data: listings,
    columns,
    state: {
      columnFilters,
      sorting,
      grouping,
      rowSelection
    },
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    onColumnFiltersChange: setColumnFilters,
    onSortingChange: setSorting,
    onGroupingChange: setGrouping,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel()
  });

  if (isSchemaLoading || isListingsLoading) {
    return <p className="text-sm text-muted-foreground">Loading listings…</p>;
  }

  if (schemaError || listingsError) {
    const message = schemaError || listingsError;
    const text = message instanceof Error ? message.message : "Failed to load listings";
    return (
      <Card>
        <CardHeader>
          <div className="space-y-1 text-sm text-muted-foreground">
            <span>Unable to load listings or schema</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-destructive">{text}</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ["listings"] })} size="sm">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const groupedColumn = grouping[0] ?? "";

  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="space-y-1 text-sm text-muted-foreground">
            <span>Inline edit, bulk update, filter, sort, and group any field.</span>
          </div>
          <Button asChild size="sm">
            <Link href="/listings/new">Add listing</Link>
          </Button>
        </div>
          <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Label htmlFor="group-by" className="text-xs uppercase text-muted-foreground">
              Group by
            </Label>
            <select
              id="group-by"
              className="rounded-md border border-input bg-background px-3 py-1 text-sm"
              value={groupedColumn}
              onChange={(event) => {
                const value = event.target.value;
                setGrouping(value ? [value] : []);
              }}
            >
              <option value="">None</option>
              {fieldConfigs.map((field) => (
                <option key={field.key} value={field.key}>
                  {field.label}
                </option>
              ))}
            </select>
          </div>
          {inlineError && <span className="text-sm text-destructive">{inlineError}</span>}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="overflow-auto rounded-md border">
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead key={header.id} className="whitespace-nowrap">
                      {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
              <TableRow>
                {table.getHeaderGroups()[0]?.headers.map((header) => (
                  <TableHead key={`${header.id}-filter`}>
                    {header.column.getCanFilter() && header.column.id !== "select" ? (
                      <ColumnFilter column={header.column} />
                    ) : null}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow key={row.id} data-state={row.getIsSelected() ? "selected" : undefined}>
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={columns.length} className="text-center text-sm text-muted-foreground">
                    No listings match the current filters.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {Object.keys(rowSelection).length > 0 && (
          <BulkEditPanel
            fieldConfigs={fieldConfigs}
            state={bulkState}
            onChange={setBulkState}
            onSubmit={handleBulkSubmit}
            isSubmitting={isBulkSubmitting}
            message={bulkMessage}
            selectionCount={Object.values(rowSelection).filter(Boolean).length}
          />
        )}
      </CardContent>
    </Card>
  );
}

interface EditableCellProps {
  listingId: number;
  field: FieldConfig;
  value: unknown;
  isSaving: boolean;
  onSave: (listingId: number, field: FieldConfig, value: string | string[] | boolean | null) => void;
}

function EditableCell({ listingId, field, value, isSaving, onSave }: EditableCellProps) {
  const [draft, setDraft] = useState<string>(() => toEditableString(field, value));

  useEffect(() => {
    setDraft(toEditableString(field, value));
  }, [field, value]);

  const handleBlur = () => {
    if (draft === toEditableString(field, value)) return;
    onSave(listingId, field, draft);
  };

  const handleSelectChange = (raw: string) => {
    setDraft(raw);
    onSave(listingId, field, raw);
  };

  const handleCheckbox = (checked: boolean) => {
    setDraft(String(checked));
    onSave(listingId, field, checked);
  };

  if (!field.editable) {
    return <span className="text-sm">{toDisplayValue(value)}</span>;
  }

  if (field.data_type === "boolean") {
    return (
      <select
        className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        value={draft || "false"}
        onChange={(event) => handleSelectChange(event.target.value)}
        disabled={isSaving}
      >
        <option value="true">True</option>
        <option value="false">False</option>
      </select>
    );
  }

  if (field.data_type === "enum" || field.data_type === "multi_select") {
    const options = field.options ?? [];
    return field.data_type === "multi_select" ? (
      <textarea
        className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        rows={2}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={handleBlur}
        disabled={isSaving}
        placeholder="Comma-separated values"
      />
    ) : (
      <select
        className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        value={draft}
        onChange={(event) => handleSelectChange(event.target.value)}
        disabled={isSaving}
      >
        <option value="">—</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    );
  }

  if (field.data_type === "number") {
    return (
      <input
        type="number"
        className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={handleBlur}
        disabled={isSaving}
      />
    );
  }

  return (
    <input
      type="text"
      className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
      value={draft}
      onChange={(event) => setDraft(event.target.value)}
      onBlur={handleBlur}
      disabled={isSaving}
    />
  );
}

interface BulkEditPanelProps {
  fieldConfigs: FieldConfig[];
  state: BulkEditState;
  onChange: (state: BulkEditState) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
  message: string | null;
  selectionCount: number;
}

function BulkEditPanel({ fieldConfigs, state, onChange, onSubmit, isSubmitting, message, selectionCount }: BulkEditPanelProps) {
  const selectedField = fieldConfigs.find((field) => field.key === state.fieldKey);
  return (
    <div className="rounded-md border border-primary/30 bg-primary/5 p-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-2">
          <Label className="text-xs uppercase text-muted-foreground">Field</Label>
          <select
            className="w-56 rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={state.fieldKey}
            onChange={(event) => onChange({ ...state, fieldKey: event.target.value })}
          >
            <option value="">Select field…</option>
            {fieldConfigs.map((field) => (
              <option key={field.key} value={field.key}>
                {field.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-1 flex-col gap-2">
          <Label className="text-xs uppercase text-muted-foreground">Value</Label>
          {selectedField?.data_type === "number" ? (
            <input
              type="number"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={state.value}
              onChange={(event) => onChange({ ...state, value: event.target.value })}
            />
          ) : selectedField?.data_type === "boolean" ? (
            <select
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={state.value || "false"}
              onChange={(event) => onChange({ ...state, value: event.target.value })}
            >
              <option value="true">True</option>
              <option value="false">False</option>
            </select>
          ) : selectedField?.data_type === "enum" ? (
            <select
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={state.value}
              onChange={(event) => onChange({ ...state, value: event.target.value })}
            >
              <option value="">—</option>
              {(selectedField?.options ?? []).map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={state.value}
              onChange={(event) => onChange({ ...state, value: event.target.value })}
              placeholder={selectedField?.data_type === "multi_select" ? "Comma-separated" : undefined}
            />
          )}
        </div>
        <Button type="button" onClick={onSubmit} disabled={!state.fieldKey || isSubmitting}>
          {isSubmitting ? "Applying…" : `Apply to ${selectionCount} selected`}
        </Button>
      </div>
      {message && <p className="mt-2 text-sm text-muted-foreground">{message}</p>}
    </div>
  );
}

function ColumnFilter({ column }: { column: Column<ListingRow, unknown> }) {
  const columnFilterValue = column.getFilterValue() as string;
  const uniqueValues = Array.from(column.getFacetedUniqueValues().keys()) as string[];
  const isBoolean = uniqueValues.every((value) => value === "true" || value === "false");

  if (uniqueValues.length > 0 && uniqueValues.length <= 6 && !isBoolean) {
    return (
      <select
        className="w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
        value={columnFilterValue ?? ""}
        onChange={(event) => column.setFilterValue(event.target.value || undefined)}
      >
        <option value="">All</option>
        {uniqueValues.map((value) => (
          <option key={value} value={value}>
            {value || "(empty)"}
          </option>
        ))}
      </select>
    );
  }

  return (
    <Input
      value={columnFilterValue ?? ""}
      onChange={(event) => column.setFilterValue(event.target.value)}
      placeholder="Filter…"
      className="h-8"
    />
  );
}

function parseFieldValue(field: FieldConfig, value: string | string[] | boolean | null): unknown {
  if (value === null || value === "") {
    return null;
  }
  if (field.data_type === "number") {
    return Number(value);
  }
  if (field.data_type === "boolean") {
    if (typeof value === "boolean") return value;
    return String(value).toLowerCase() === "true";
  }
  if (field.data_type === "multi_select") {
    const raw = typeof value === "string" ? value : Array.isArray(value) ? value.join(",") : "";
    return raw
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return value;
}

function buildUpdatePayload(field: FieldConfig, value: unknown) {
  if (field.origin === "core") {
    return { fields: { [field.key]: value } };
  }
  return { attributes: { [field.key]: value } };
}

function buildBulkPayload(field: FieldConfig, value: unknown, listingIds: number[]) {
  if (field.origin === "core") {
    return { listing_ids: listingIds, fields: { [field.key]: value }, attributes: {} };
  }
  return { listing_ids: listingIds, fields: {}, attributes: { [field.key]: value } };
}

function toDisplayValue(value: unknown) {
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  return String(value);
}

function toEditableString(field: FieldConfig, value: unknown): string {
  if (value === null || value === undefined) {
    if (field.data_type === "boolean") return "false";
    return "";
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  return String(value);
}

function formatCurrency(value: number | null | undefined) {
  if (!value) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toFixed(2);
}

function statusTone(condition: string) {
  switch (condition.toLowerCase()) {
    case "new":
      return "bg-emerald-100 text-emerald-700";
    case "refurb":
    case "refurbished":
      return "bg-amber-100 text-amber-700";
    default:
      return "bg-slate-200 text-slate-700";
  }
}
