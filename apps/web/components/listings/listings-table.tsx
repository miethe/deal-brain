"use client";

import {
  type ColumnDef,
  type ColumnFiltersState,
  type ColumnSizingState,
  type FilterFn,
  type GroupingState,
  type SortingState,
  getCoreRowModel,
  getExpandedRowModel,
  getFilteredRowModel,
  getGroupedRowModel,
  getSortedRowModel,
  useReactTable
} from "@tanstack/react-table";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { apiFetch, ApiError } from "../../lib/utils";
import { CpuRecord, ListingFieldSchema, ListingRecord, ListingSchemaResponse, RamSpecRecord, StorageProfileRecord } from "../../types/listings";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader } from "../ui/card";
import { DataGrid, type ColumnMetaConfig } from "../ui/data-grid";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Badge } from "../ui/badge";
import { TableRow } from "../ui/table";
import { ValuationBreakdownModal } from "./valuation-breakdown-modal";
import { ValuationCell } from "./valuation-cell";
import { DualMetricCell } from "./dual-metric-cell";
import { PortsDisplay } from "./ports-display";
import { ComboBox } from "../forms/combobox";
import { useConfirmation } from "../ui/confirmation-dialog";
import { useValuationThresholds } from "@/hooks/use-valuation-thresholds";
import { EntityTooltip } from "./entity-tooltip";
import { CpuTooltipContent } from "./tooltips/cpu-tooltip-content";
import { GpuTooltipContent } from "./tooltips/gpu-tooltip-content";
import { fetchEntityData } from "@/lib/api/entities";
import { RamSpecSelector } from "../forms/ram-spec-selector";
import { StorageProfileSelector } from "../forms/storage-profile-selector";
import { getStorageMediumLabel } from "../../lib/component-catalog";

// ListingRow is just an alias for ListingRecord - all fields come from the API
export type ListingRow = ListingRecord;

interface BulkEditState {
  fieldKey: string;
  value: string;
}

interface FieldConfig extends ListingFieldSchema {
  origin: "core" | "custom";
  options: string[] | null | undefined;
  id?: number; // Only present for custom fields
}

const DEFAULT_BULK_STATE: BulkEditState = {
  fieldKey: "",
  value: ""
};

const STORAGE_KEY = "dealbrain_listings_table_state_v1";

// Dropdown field configurations
const DROPDOWN_FIELD_CONFIGS: Record<string, string[]> = {
  'ram_gb': ['4', '8', '16', '24', '32', '48', '64', '96', '128'],
  'primary_storage_gb': ['128', '256', '512', '1024', '2048', '4096'],
  'secondary_storage_gb': ['128', '256', '512', '1024', '2048', '4096'],
  'storage_type': ['SSD', 'HDD', 'NVMe', 'eMMC'],
};

function deriveListingFilterType(field: FieldConfig | undefined): ColumnMetaConfig["filterType"] {
  if (!field) return "text";
  if (field.data_type === "boolean") return "boolean";
  if (field.data_type === "number") return "number";
  if (field.data_type === "enum" || field.data_type === "multi_select" || (field.options?.length ?? 0) > 0) {
    return "multi-select";
  }
  return "text";
}

function buildListingMeta(field: FieldConfig): ColumnMetaConfig {
  const filterType = deriveListingFilterType(field);
  return {
    tooltip: field.description ?? undefined,
    description: field.description ?? undefined,
    filterType,
    options: field.options?.map((option) => ({ label: option, value: option })),
  };
}

function buildListingFilterFn(field: FieldConfig | undefined): FilterFn<ListingRow> | undefined {
  const filterType = deriveListingFilterType(field);
  if (filterType === "multi-select") {
    return (row, columnId, filterValue) => {
      const selections = Array.isArray(filterValue) ? (filterValue as string[]) : [];
      if (!selections.length) return true;
      const raw = row.getValue<unknown>(columnId);
      if (Array.isArray(raw)) {
        return raw.some((item) => selections.includes(String(item)));
      }
      if (raw === null || raw === undefined) return false;
      return selections.includes(String(raw));
    };
  }
  if (filterType === "boolean") {
    return (row, columnId, filterValue) => {
      if (filterValue === undefined || filterValue === null || filterValue === "") return true;
      const raw = row.getValue<unknown>(columnId);
      if (raw === null || raw === undefined) return false;
      return Boolean(raw) === Boolean(filterValue);
    };
  }
  if (filterType === "number") {
    return (row, columnId, filterValue) => {
      if (filterValue === undefined || filterValue === null || filterValue === "") return true;
      const raw = row.getValue<unknown>(columnId);
      if (raw === null || raw === undefined) return false;
      const numeric = Number(filterValue);
      if (Number.isNaN(numeric)) return true;
      return Number(raw) === numeric;
    };
  }
  return undefined;
}

const numericFilterFn: FilterFn<ListingRow> = (row, columnId, filterValue) => {
  if (filterValue === undefined || filterValue === null || filterValue === "") return true;
  const raw = row.getValue<unknown>(columnId);
  if (raw === null || raw === undefined) return false;
  const numeric = Number(filterValue);
  if (Number.isNaN(numeric)) return true;
  return Number(raw) === numeric;
};

export function ListingsTable() {
  const queryClient = useQueryClient();
  const { confirm, dialog: confirmationDialog } = useConfirmation();
  const { data: thresholds } = useValuationThresholds();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [sorting, setSorting] = useState<SortingState>([{ id: "title", desc: false }]);
  const [grouping, setGrouping] = useState<GroupingState>([]);
  const [columnSizing, setColumnSizing] = useState<ColumnSizingState>({});
  const [quickSearch, setQuickSearch] = useState("");
  const [rowSelection, setRowSelection] = useState({});
  const [bulkState, setBulkState] = useState<BulkEditState>({ ...DEFAULT_BULK_STATE });
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [bulkMessage, setBulkMessage] = useState<string | null>(null);
  const [isBulkSubmitting, setIsBulkSubmitting] = useState(false);
  const [breakdownModalOpen, setBreakdownModalOpen] = useState(false);
  const [selectedListingForBreakdown, setSelectedListingForBreakdown] = useState<{
    id: number;
    title: string;
    thumbnailUrl?: string | null;
  } | null>(null);

  // Highlighted row tracking
  const highlightedRef = useRef<HTMLTableRowElement>(null);
  const highlightedId = useMemo(() => {
    const param = searchParams.get('highlight');
    return param ? parseInt(param, 10) : null;
  }, [searchParams]);

  // Load saved table state on mount (will be validated when table initializes)
  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
    if (!saved) return;

    try {
      const parsed = JSON.parse(saved);
      // Set state optimistically - invalid columns will be filtered by React Table
      if (parsed.sorting) setSorting(parsed.sorting);
      if (parsed.filters) setColumnFilters(parsed.filters);
      if (parsed.grouping) setGrouping(parsed.grouping);
      if (parsed.search) setQuickSearch(parsed.search);
    } catch (
      // eslint-disable-next-line no-empty
      _error
    ) {}
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const payload = JSON.stringify({ sorting, filters: columnFilters, grouping, search: quickSearch });
    localStorage.setItem(STORAGE_KEY, payload);
  }, [sorting, columnFilters, grouping, quickSearch]);

  // Handle highlighting and scrolling
  useEffect(() => {
    if (highlightedId && highlightedRef.current) {
      // Scroll into view with smooth behavior
      highlightedRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });

      // Focus for accessibility
      highlightedRef.current.focus();

      // Clear highlight param after 2 seconds
      const timer = setTimeout(() => {
        const params = new URLSearchParams(window.location.search);
        params.delete('highlight');
        const newSearch = params.toString();
        router.replace(
          `${window.location.pathname}${newSearch ? `?${newSearch}` : ''}`,
          { scroll: false }
        );
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [highlightedId, router]);

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
    const coreKeys = new Set(core.map((f) => f.key));
    const custom = (schema.custom_fields || [])
      .filter((field) => field.is_active && !field.deleted_at)
      .filter((field) => !coreKeys.has(field.key))
      .map((field) => ({
        key: field.key,
        label: field.label,
        data_type: field.data_type,
        required: field.required,
        editable: true,
        description: field.description,
        options: field.options ?? null,
        validation: field.validation ?? null,
        origin: "custom" as const,
        id: field.id
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

  const filteredListings = useMemo(() => {
    if (!quickSearch) return listings;
    const term = quickSearch.toLowerCase();
    return listings.filter((listing) => {
      if (listing.title?.toLowerCase().includes(term)) return true;
      if ((listing.cpu_name ?? "").toLowerCase().includes(term)) return true;
      if ((listing.gpu_name ?? "").toLowerCase().includes(term)) return true;
      return Object.values(listing.attributes ?? {}).some((value) =>
        value !== null && value !== undefined && String(value).toLowerCase().includes(term)
      );
    });
  }, [listings, quickSearch]);

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
      if (error instanceof ApiError && error.status === 409) {
        setInlineError("Another change landed first. Reloaded the latest data.");
        queryClient.invalidateQueries({ queryKey: ["listings", "records"] });
        return;
      }
      const message = error instanceof Error ? error.message : "Unable to save changes";
      setInlineError(message);
    }
  });

  const handleInlineSave = useCallback(
    (
      listingId: number,
      field: FieldConfig,
      rawValue: string | string[] | boolean | number | RamSpecRecord | StorageProfileRecord | null
    ) => {
      const parsed = parseFieldValue(field, rawValue);
      inlineMutation.mutate({ listingId, field, value: parsed });
    },
    [inlineMutation]
  );

  const handleCreateOption = useCallback(
    async (fieldKey: string, value: string) => {
      const field = fieldConfigs.find(f => f.key === fieldKey);
      if (!field?.id) {
        throw new Error("Field not found");
      }

      // Show confirmation dialog
      const confirmed = await confirm({
        title: `Add "${value}" to ${field.label}?`,
        message: 'This will add the option globally for all listings.',
        confirmLabel: 'Add Option',
        onConfirm: () => {},
      });

      if (!confirmed) {
        throw new Error("Cancelled");
      }

      try {
        await apiFetch(`/v1/reference/custom-fields/${field.id}/options`, {
          method: 'POST',
          body: JSON.stringify({ value })
        });

        // Invalidate queries to refresh options
        queryClient.invalidateQueries({ queryKey: ['listings', 'schema'] });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to add option";
        setInlineError(message);
        throw error;
      }
    },
    [fieldConfigs, confirm, queryClient]
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

  const cpuOptions = useMemo(() => {
    const unique = new Set<string>();
    listings.forEach((listing) => {
      if (listing.cpu_name) unique.add(listing.cpu_name);
    });
    return Array.from(unique).map((value) => ({ label: value, value }));
  }, [listings]);

  const columns = useMemo<ColumnDef<ListingRow>[]>(() => {
    const titleConfig = fieldMap.get("title");
    const titleMeta = titleConfig ? buildListingMeta(titleConfig) : undefined;

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
        enableResizing: false,
        size: 36,
      },
      {
        header: "Title",
        accessorKey: "title",
        cell: ({ row }) => {
          const gpuConfig = fieldMap.get("gpu_id");
          const gpu = row.original.gpu;
          const gpuName = row.original.gpu_name;

          return (
            <div className="flex flex-col gap-1">
              {titleConfig ? (
                <EditableCell
                  listingId={row.original.id}
                  field={titleConfig}
                  value={row.original.title}
                  onSave={handleInlineSave}
                  isSaving={inlineMutation.isPending}
                  onCreateOption={handleCreateOption}
                  listing={row.original}
                />
              ) : (
                <span className="font-medium text-foreground">{row.original.title}</span>
              )}
              {gpuConfig && gpuConfig.editable ? (
                <div className="text-xs">
                  <EditableCell
                    listingId={row.original.id}
                    field={gpuConfig}
                    value={row.original.gpu_id}
                    onSave={handleInlineSave}
                    isSaving={inlineMutation.isPending}
                    listing={row.original}
                  />
                </div>
              ) : gpu?.id ? (
                <div className="text-xs">
                  <EntityTooltip
                    entityType="gpu"
                    entityId={gpu.id}
                    tooltipContent={(gpuData) => <GpuTooltipContent gpu={gpuData} />}
                    fetchData={fetchEntityData}
                    variant="inline"
                  >
                    {gpuName || gpu.name || "Unknown GPU"}
                  </EntityTooltip>
                </div>
              ) : (
                <span className="text-xs text-muted-foreground">
                  {gpuName || "No dedicated GPU"}
                </span>
              )}
            </div>
          );
        },
        meta: {
          ...titleMeta,
          description: "Product title or name from the seller listing",
          minWidth: 200,
          enableTextWrap: true,
        },
        enableResizing: true,
        enableColumnFilter: true,
        size: 260,
      },
      {
        header: "CPU",
        accessorKey: "cpu_name",
        cell: ({ row }) => {
          const cpuConfig = fieldMap.get("cpu_id");
          const cpu = row.original.cpu;
          const cpuName = row.original.cpu_name;

          // If editable, show the selector
          if (cpuConfig && cpuConfig.editable) {
            return (
              <EditableCell
                listingId={row.original.id}
                field={cpuConfig}
                value={row.original.cpu_id}
                onSave={handleInlineSave}
                isSaving={inlineMutation.isPending}
                listing={row.original}
              />
            );
          }

          // No CPU attached
          if (!cpu && !cpuName) {
            return <span className="text-sm text-muted-foreground">—</span>;
          }

          // CPU with ID - show with tooltip
          if (cpu?.id) {
            return (
              <EntityTooltip
                entityType="cpu"
                entityId={cpu.id}
                tooltipContent={(cpuData) => <CpuTooltipContent cpu={cpuData} />}
                fetchData={fetchEntityData}
                variant="inline"
              >
                {cpuName || cpu.name || "Unknown"}
              </EntityTooltip>
            );
          }

          // Fallback: CPU name without ID (shouldn't happen with Phase 1 changes)
          return <span className="text-sm">{cpuName}</span>;
        },
        enableSorting: true,
        enableResizing: true,
        enableColumnFilter: true,
        meta: {
          filterType: "multi-select",
          options: cpuOptions,
          tooltip: "CPU associated with the listing (hover for details)",
          description: "The processor model (Intel/AMD) powering this system",
        },
        filterFn: (row, columnId, filterValue) => {
          const selections = Array.isArray(filterValue) ? (filterValue as string[]) : [];
          if (!selections.length) return true;
          const name = row.getValue<string | null | undefined>(columnId);
          if (!name) return false;
          return selections.includes(name);
        },
        size: 180,
      },
      {
        header: "Valuation",
        accessorKey: "adjusted_price_usd",
        cell: ({ row }) => {
          const adjustedPrice = Number(row.original.adjusted_price_usd ?? 0);
          const listPrice = Number(row.original.price_usd ?? 0);

          if (!thresholds) {
            // Fallback while loading thresholds
            return <span className="font-medium">{formatCurrency(adjustedPrice)}</span>;
          }

          return (
            <ValuationCell
              adjustedPrice={adjustedPrice}
              listPrice={listPrice}
              thresholds={thresholds}
              onDetailsClick={() => {
                setSelectedListingForBreakdown({
                  id: row.original.id,
                  title: row.original.title || "Untitled",
                  thumbnailUrl: row.original.thumbnail_url,
                });
                setBreakdownModalOpen(true);
              }}
            />
          );
        },
        enableSorting: true,
        enableResizing: true,
        enableColumnFilter: true,
        meta: {
          filterType: "number",
          tooltip: "Adjusted price based on active ruleset. Click for breakdown.",
          description: "Final valuation after applying active ruleset rules",
        },
        filterFn: numericFilterFn,
        size: 200,
      },
      {
        header: "$/CPU Mark",
        accessorKey: "dollar_per_cpu_mark",
        cell: ({ getValue }) => formatNumber(getValue() as number | null | undefined),
        enableResizing: true,
        enableColumnFilter: true,
        meta: {
          filterType: "number",
          tooltip: "Dollars per CPU mark",
          description: "Price efficiency metric: dollars per CPU benchmark point",
        },
        filterFn: numericFilterFn,
        size: 140,
      },
      {
        id: 'dollar_per_cpu_mark_single',
        header: '$/CPU Mark (Single)',
        accessorKey: 'dollar_per_cpu_mark_single',
        cell: ({ row }) => (
          <DualMetricCell
            raw={row.original.dollar_per_cpu_mark_single}
            adjusted={row.original.dollar_per_cpu_mark_single_adjusted}
            prefix="$"
            decimals={3}
          />
        ),
        meta: {
          tooltip: 'Single-thread price efficiency. Lower = better value.',
          description: 'Cost per PassMark single-thread point. Adjusted value uses price after RAM/storage deductions.',
          filterType: 'number',
          minWidth: 160,
        },
        enableSorting: true,
        enableResizing: true,
        enableColumnFilter: true,
        filterFn: numericFilterFn,
        size: 160,
      },
      {
        id: 'dollar_per_cpu_mark_multi',
        header: '$/CPU Mark (Multi)',
        accessorKey: 'dollar_per_cpu_mark_multi',
        cell: ({ row }) => (
          <DualMetricCell
            raw={row.original.dollar_per_cpu_mark_multi}
            adjusted={row.original.dollar_per_cpu_mark_multi_adjusted}
            prefix="$"
            decimals={3}
          />
        ),
        meta: {
          tooltip: 'Multi-thread price efficiency. Lower = better value.',
          description: 'Cost per PassMark multi-thread point. Adjusted value uses price after RAM/storage deductions.',
          filterType: 'number',
          minWidth: 160,
        },
        enableSorting: true,
        enableResizing: true,
        enableColumnFilter: true,
        filterFn: numericFilterFn,
        size: 160,
      },
      {
        id: 'manufacturer',
        header: 'Manufacturer',
        accessorKey: 'manufacturer',
        cell: ({ getValue }) => {
          const val = getValue() as string | null;
          return <span className="text-sm">{val || "—"}</span>;
        },
        meta: {
          tooltip: 'PC manufacturer or builder',
          filterType: 'multi-select',
          options: [
            { label: 'Dell', value: 'Dell' },
            { label: 'HP', value: 'HP' },
            { label: 'Lenovo', value: 'Lenovo' },
            { label: 'Apple', value: 'Apple' },
            { label: 'ASUS', value: 'ASUS' },
            { label: 'Acer', value: 'Acer' },
            { label: 'MSI', value: 'MSI' },
            { label: 'Custom Build', value: 'Custom Build' },
            { label: 'Other', value: 'Other' },
          ],
        },
        enableSorting: true,
        enableResizing: true,
        size: 140,
      },
      {
        id: 'form_factor',
        header: 'Form Factor',
        accessorKey: 'form_factor',
        cell: ({ getValue }) => {
          const val = getValue() as string | null;
          return <span className="text-sm">{val || "—"}</span>;
        },
        meta: {
          tooltip: 'PC form factor classification',
          filterType: 'multi-select',
          options: [
            { label: 'Desktop', value: 'Desktop' },
            { label: 'Laptop', value: 'Laptop' },
            { label: 'Server', value: 'Server' },
            { label: 'Mini-PC', value: 'Mini-PC' },
            { label: 'All-in-One', value: 'All-in-One' },
            { label: 'Other', value: 'Other' },
          ],
        },
        enableSorting: true,
        enableResizing: true,
        size: 120,
      },
      {
        id: 'ports',
        header: 'Ports',
        accessorFn: (row) => row.ports_profile?.ports || [],
        cell: ({ row }) => (
          <PortsDisplay ports={row.original.ports_profile?.ports || []} />
        ),
        meta: {
          tooltip: 'Connectivity ports',
          description: 'Available ports and quantities',
        },
        enableSorting: false,
        enableResizing: true,
        size: 200,
      },
      {
        header: "Composite",
        accessorKey: "score_composite",
        cell: ({ getValue }) => formatNumber(getValue() as number | null | undefined),
        enableResizing: true,
        enableColumnFilter: true,
        meta: {
          filterType: "number",
          tooltip: "Composite performance score",
          description: "Overall system performance score based on weighted metrics",
        },
        filterFn: numericFilterFn,
        size: 140,
      },
    ];

    // Exclude fields that have custom column implementations above
    const hiddenEditableKeys = new Set([
      "title",
      "cpu_id",
      "gpu_id",
      "manufacturer",
      "form_factor",
      "adjusted_price_usd",
      "score_composite",
      "dollar_per_cpu_mark",
      "dollar_per_cpu_mark_single",
      "dollar_per_cpu_mark_multi",
    ]);

    const editableColumns: ColumnDef<ListingRow>[] = fieldConfigs
      .filter((config) => config.editable && !hiddenEditableKeys.has(config.key))
      .map((config) => {
        const meta = buildListingMeta(config);
        return {
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
              onCreateOption={handleCreateOption}
              listing={row.original}
            />
          ),
          meta,
          enableResizing: true,
          enableSorting: true,
          enableColumnFilter: true,
          filterFn: buildListingFilterFn(config),
          size: config.data_type === "text" ? 220 : 170,
        };
      });

    return [...baseColumns, ...editableColumns];
  }, [cpuOptions, fieldConfigs, fieldMap, handleInlineSave, handleCreateOption, inlineMutation.isPending, thresholds]);

  const table = useReactTable({
    data: filteredListings,
    columns,
    state: {
      columnFilters,
      sorting,
      grouping,
      columnSizing,
      rowSelection
    },
    enableRowSelection: true,
    columnResizeMode: "onChange",
    onRowSelectionChange: setRowSelection,
    onColumnFiltersChange: setColumnFilters,
    onSortingChange: setSorting,
    onGroupingChange: setGrouping,
    onColumnSizingChange: setColumnSizing,
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

  const resetView = () => {
    setColumnFilters([]);
    setSorting([{ id: "title", desc: false }]);
    setGrouping([]);
    setQuickSearch("");
    setRowSelection({});
    setBulkState({ ...DEFAULT_BULK_STATE });
    setBulkMessage(null);
  };

  return (
    <Card className="w-full border-0 bg-background shadow-none">
      <CardHeader className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <h2 className="text-2xl font-semibold tracking-tight">Listings workspace</h2>
            <p className="text-sm text-muted-foreground">Inline edits, bulk updates, filters, and grouping with a consistent data grid design.</p>
          </div>
          <Button asChild size="sm">
            <Link href="/listings/new">Add listing</Link>
          </Button>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex w-full max-w-xs items-center gap-2">
            <Label htmlFor="listings-search" className="text-xs uppercase text-muted-foreground">
              Search
            </Label>
            <Input
              id="listings-search"
              value={quickSearch}
              onChange={(event) => setQuickSearch(event.target.value)}
              placeholder="Title, CPU, custom fields…"
            />
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="group-by" className="text-xs uppercase text-muted-foreground">
              Group by
            </Label>
            <select
              id="group-by"
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
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
          <Button variant="ghost" size="sm" onClick={resetView}>
            Reset view
          </Button>
          {inlineError ? <span className="text-sm text-destructive">{inlineError}</span> : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <DataGrid
          table={table}
          enableFilters
          className="border"
          storageKey="listings-grid"
          highlightedRowId={highlightedId}
          highlightedRef={highlightedRef}
        />

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

      {/* Valuation Breakdown Modal */}
      {selectedListingForBreakdown && (
        <ValuationBreakdownModal
          open={breakdownModalOpen}
          onOpenChange={setBreakdownModalOpen}
          listingId={selectedListingForBreakdown.id}
          listingTitle={selectedListingForBreakdown.title}
          thumbnailUrl={selectedListingForBreakdown.thumbnailUrl}
        />
      )}

      {/* Confirmation Dialog */}
      {confirmationDialog}
    </Card>
  );
}

interface EditableCellProps {
  listingId: number;
  field: FieldConfig;
  value: unknown;
  isSaving: boolean;
  onSave: (
    listingId: number,
    field: FieldConfig,
    value: string | string[] | boolean | number | RamSpecRecord | StorageProfileRecord | null
  ) => void;
  onCreateOption?: (fieldKey: string, value: string) => Promise<void>;
  listing?: ListingRecord;
}

function EditableCell({ listingId, field, value, isSaving, onSave, onCreateOption, listing }: EditableCellProps) {
  const [draft, setDraft] = useState<string>(() => toEditableString(field, value));

  // Query for CPU/GPU options if this is a reference field
  const { data: cpuOptions } = useQuery<Array<{ id: number; name: string }>>({
    queryKey: ["cpus"],
    queryFn: () => apiFetch("/v1/catalog/cpus"),
    enabled: field.data_type === "reference" && field.key === "cpu_id"
  });

  const { data: gpuOptions } = useQuery<Array<{ id: number; name: string }>>({
    queryKey: ["gpus"],
    queryFn: () => apiFetch("/v1/catalog/gpus"),
    enabled: field.data_type === "reference" && field.key === "gpu_id"
  });

  useEffect(() => {
    setDraft(toEditableString(field, value));
  }, [field, value]);

  const handleBlur = () => {
    if (draft === toEditableString(field, value)) return;
    onSave(listingId, field, draft);
  };

  const handleSelectChange = (raw: string) => {
    setDraft(raw);
    // Convert to number for reference fields (cpu_id, gpu_id)
    if (field.data_type === "reference") {
      const numValue = raw === "" ? null : parseInt(raw, 10);
      onSave(listingId, field, numValue);
    } else {
      onSave(listingId, field, raw);
    }
  };

  const handleCheckbox = (checked: boolean) => {
    setDraft(String(checked));
    onSave(listingId, field, checked);
  };

  if (!field.editable) {
    return <span className="text-sm">{toDisplayValue(value)}</span>;
  }

  // Handle reference fields (CPU/GPU)
  if (field.data_type === "reference") {
    if (field.key === "ram_spec_id") {
      const currentSpec = listing?.ram_spec ?? (value && typeof value === "object" ? (value as RamSpecRecord) : null);
      return (
        <RamSpecSelector
          value={currentSpec ?? null}
          onChange={(spec) => onSave(listingId, field, spec ?? null)}
          disabled={isSaving}
        />
      );
    }

    if (field.key === "primary_storage_profile_id" || field.key === "secondary_storage_profile_id") {
      const currentProfile = field.key === "primary_storage_profile_id"
        ? listing?.primary_storage_profile ?? (value && typeof value === "object" ? (value as StorageProfileRecord) : null)
        : listing?.secondary_storage_profile ?? (value && typeof value === "object" ? (value as StorageProfileRecord) : null);

      return (
        <StorageProfileSelector
          value={currentProfile ?? null}
          onChange={(profile) => onSave(listingId, field, profile ?? null)}
          disabled={isSaving}
          context={field.key === "primary_storage_profile_id" ? "primary" : "secondary"}
        />
      );
    }

    const options = field.key === "cpu_id" ? cpuOptions : field.key === "gpu_id" ? gpuOptions : [];
    if (!options) {
      return <span className="text-sm text-muted-foreground">Loading...</span>;
    }

    return (
      <select
        className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        value={value != null ? String(value) : ""}
        onChange={(event) => handleSelectChange(event.target.value)}
        disabled={isSaving}
      >
        <option value="">—</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.name}
          </option>
        ))}
      </select>
    );
  }

  // Check if this field should use a dropdown (either in DROPDOWN_FIELD_CONFIGS or has options)
  const dropdownOptions = DROPDOWN_FIELD_CONFIGS[field.key] || field.options;
  const useDropdown = dropdownOptions && dropdownOptions.length > 0;

  if (field.data_type === "boolean") {
    return (
      <select
        className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        value={draft ? draft : "false"}
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
    ) : onCreateOption ? (
      <ComboBox
        options={options.map(v => ({ label: v, value: v }))}
        value={value != null ? String(value) : ""}
        onChange={(newValue) => onSave(listingId, field, newValue)}
        onCreateOption={async (customValue) => {
          await onCreateOption(field.key, customValue);
          onSave(listingId, field, customValue);
        }}
        allowCustom={true}
        disabled={isSaving}
        className="text-sm"
      />
    ) : (
      <select
        className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        value={draft ? draft : ""}
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

  // Use simple select for number fields with dropdown configs (RAM, Storage)
  if (field.data_type === "number" && useDropdown) {
    return (
      <select
        className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        value={value != null ? String(value) : ""}
        onChange={(event) => handleSelectChange(event.target.value)}
        disabled={isSaving}
      >
        <option value="">—</option>
        {dropdownOptions.map((option) => (
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

function parseFieldValue(
  field: FieldConfig,
  value: string | string[] | boolean | number | RamSpecRecord | StorageProfileRecord | null
): unknown {
  if (value === null || value === "") {
    return null;
  }
  // If already a number, return as-is (for reference fields like cpu_id)
  if (typeof value === "number") {
    return value;
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
  if (field.key === "ram_spec_id") {
    const spec = value as RamSpecRecord | null;
    return {
      fields: {
        ram_spec_id: spec ? spec.id : null,
        ram_gb: spec?.total_capacity_gb ?? null,
      },
    };
  }

  if (field.key === "primary_storage_profile_id" || field.key === "secondary_storage_profile_id") {
    const profile = value as StorageProfileRecord | null;
    const profileId = profile ? profile.id : null;
    const capacityKey = field.key === "primary_storage_profile_id" ? "primary_storage_gb" : "secondary_storage_gb";
    const typeKey = field.key === "primary_storage_profile_id" ? "primary_storage_type" : "secondary_storage_type";

    return {
      fields: {
        [field.key]: profileId,
        [capacityKey]: profile?.capacity_gb ?? null,
        [typeKey]: profile ? getStorageMediumLabel(profile.medium ?? null) : null,
      },
    };
  }

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
