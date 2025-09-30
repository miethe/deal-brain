"use client";

import {
  type ColumnDef,
  type ColumnFiltersState,
  type ColumnSizingState,
  type Row,
  type SortingState,
  type Table as TableInstance,
  type VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable
} from "@tanstack/react-table";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { cn } from "../../lib/utils";
import { Input } from "./input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./table";

const DEFAULT_ROW_HEIGHT = 44;
const COMPACT_ROW_HEIGHT = 36;
const HEADER_HEIGHT = 52;
const MIN_TABLE_HEIGHT = 240;
const MAX_TABLE_HEIGHT = 640;
const VIRTUALIZATION_THRESHOLD = 80;
const OVERSCAN_ROWS = 8;

interface ColumnOption {
  label: string;
  value: string;
}

interface ColumnMetaConfig {
  tooltip?: string;
  filterType?: "text" | "number" | "select" | "multi-select" | "boolean";
  options?: ColumnOption[];
}

interface DataGridProps<TData> {
  columns?: ColumnDef<TData, any>[];
  data?: TData[];
  table?: TableInstance<TData>;
  storageKey?: string;
  loading?: boolean;
  emptyLabel?: string;
  className?: string;
  enableFilters?: boolean;
  estimatedRowHeight?: number;
  virtualizationThreshold?: number;
  density?: "comfortable" | "compact";
}

interface VirtualizationState<TData> {
  rows: Row<TData>[];
  paddingTop: number;
  paddingBottom: number;
  enabled: boolean;
}

function computeContainerHeight(rowCount: number, rowHeight: number): number {
  if (rowCount <= 0) {
    return MIN_TABLE_HEIGHT;
  }
  const bodyHeight = rowCount * rowHeight + HEADER_HEIGHT;
  return Math.max(MIN_TABLE_HEIGHT, Math.min(bodyHeight, MAX_TABLE_HEIGHT));
}

function useColumnSizingPersistence<TData>(
  table: TableInstance<TData> | undefined,
  columnSizing: ColumnSizingState,
  storageKey?: string
) {
  const hydratedRef = useRef(false);

  useEffect(() => {
    if (!table || !storageKey) return;
    if (typeof window === "undefined" || hydratedRef.current) return;

    const key = `${storageKey}:columnSizing`;
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      hydratedRef.current = true;
      return;
    }
    try {
      const parsed = JSON.parse(raw) as ColumnSizingState;
      table.setColumnSizing(parsed);
    } catch (error) {
      console.error("Failed to hydrate column sizing state", error);
    } finally {
      hydratedRef.current = true;
    }
  }, [storageKey, table]);

  useEffect(() => {
    if (!table || !storageKey) return;
    if (typeof window === "undefined" || !hydratedRef.current) return;

    const key = `${storageKey}:columnSizing`;
    window.localStorage.setItem(key, JSON.stringify(columnSizing));
  }, [columnSizing, storageKey, table]);
}

function useVirtualization<TData>(
  rows: Row<TData>[],
  rowHeight: number,
  containerRef: React.RefObject<HTMLDivElement>,
  threshold: number
): VirtualizationState<TData> {
  const [range, setRange] = useState(() => ({ start: 0, end: Math.min(rows.length, threshold) }));
  const total = rows.length;
  const enabled = total > threshold;

  useEffect(() => {
    if (!enabled) {
      setRange({ start: 0, end: total });
      return;
    }

    const element = containerRef.current;
    if (!element) return;

    const handleScroll = () => {
      const scrollTop = element.scrollTop;
      const viewportHeight = element.clientHeight || MAX_TABLE_HEIGHT;
      const start = Math.max(0, Math.floor(scrollTop / rowHeight) - OVERSCAN_ROWS);
      const end = Math.min(total, Math.ceil((scrollTop + viewportHeight) / rowHeight) + OVERSCAN_ROWS);
      setRange({ start, end });
    };

    handleScroll();
    element.addEventListener("scroll", handleScroll, { passive: true });
    return () => element.removeEventListener("scroll", handleScroll);
  }, [containerRef, enabled, rowHeight, total]);

  useEffect(() => {
    if (!enabled) {
      setRange({ start: 0, end: total });
    }
  }, [enabled, total]);

  const visibleRows = enabled ? rows.slice(range.start, range.end) : rows;
  const paddingTop = enabled ? range.start * rowHeight : 0;
  const paddingBottom = enabled ? Math.max(total - range.end, 0) * rowHeight : 0;

  return {
    rows: visibleRows,
    paddingTop,
    paddingBottom,
    enabled,
  };
}

function resolveRowHeight(density: "comfortable" | "compact", estimated?: number): number {
  if (estimated) return estimated;
  return density === "compact" ? COMPACT_ROW_HEIGHT : DEFAULT_ROW_HEIGHT;
}

function renderFilterControl<TData>(
  column: ReturnType<TableInstance<TData>["getAllLeafColumns"]>[number],
  meta: ColumnMetaConfig | undefined,
  value: unknown,
  setValue: (next: unknown) => void,
  searchQuery: string,
  setSearchQuery: (next: string) => void
) {
  const filterType = meta?.filterType ?? "text";

  switch (filterType) {
    case "number":
      return (
        <Input
          type="number"
          inputMode="decimal"
          value={value ?? ""}
          onChange={(event) => {
            const raw = event.target.value;
            setValue(raw ? Number(raw) : undefined);
          }}
          className="h-8 w-full text-xs"
          placeholder="Filter"
        />
      );
    case "boolean":
      return (
        <select
          className="h-8 w-full rounded-md border border-input bg-background px-2 text-xs text-foreground"
          value={value ?? ""}
          onChange={(event) => {
            const raw = event.target.value;
            if (!raw) {
              setValue(undefined);
            } else {
              setValue(raw === "true");
            }
          }}
        >
          <option value="">Any</option>
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
      );
    case "select":
      return (
        <select
          className="h-8 w-full rounded-md border border-input bg-background px-2 text-xs text-foreground"
          value={value ?? ""}
          onChange={(event) => {
            const raw = event.target.value;
            setValue(raw || undefined);
          }}
        >
          <option value="">All</option>
          {(meta?.options ?? []).map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    case "multi-select": {
      const selections = Array.isArray(value) ? (value as string[]) : [];
      const options = (meta?.options ?? []).filter((option) =>
        option.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        option.value.toLowerCase().includes(searchQuery.toLowerCase())
      );
      const toggleSelection = (optionValue: string) => {
        if (selections.includes(optionValue)) {
          setValue(selections.filter((item) => item !== optionValue));
        } else {
          setValue([...selections, optionValue]);
        }
      };

      return (
        <div className="flex h-full flex-col gap-1">
          <Input
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search"
            className="h-8 w-full text-xs"
          />
          <div className="grid max-h-40 gap-1 overflow-y-auto rounded-md border border-input bg-background p-2 text-xs">
            {options.length ? (
              options.map((option) => {
                const checked = selections.includes(option.value);
                return (
                  <label key={option.value} className="flex cursor-pointer items-center gap-2">
                    <input
                      type="checkbox"
                      className="h-3 w-3"
                      checked={checked}
                      onChange={() => toggleSelection(option.value)}
                    />
                    <span className="truncate" title={option.label}>
                      {option.label}
                    </span>
                  </label>
                );
              })
            ) : (
              <span className="text-muted-foreground">No matches</span>
            )}
          </div>
        </div>
      );
    }
    default:
      return (
        <Input
          value={(value as string) ?? ""}
          onChange={(event) => setValue(event.target.value || undefined)}
          className="h-8 w-full text-xs"
          placeholder="Filter"
        />
      );
  }
}

export function DataGrid<TData>({
  columns,
  data,
  table,
  storageKey,
  loading,
  emptyLabel = "No records.",
  className,
  enableFilters,
  estimatedRowHeight,
  virtualizationThreshold = VIRTUALIZATION_THRESHOLD,
  density = "comfortable",
}: DataGridProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [columnSizing, setColumnSizing] = useState<ColumnSizingState>({});
  const [filterSearch, setFilterSearch] = useState<Record<string, string>>({});

  const internalTable = useReactTable({
    data: data ?? [],
    columns: columns ?? [],
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      columnSizing,
    },
    columnResizeMode: "onChange",
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onColumnSizingChange: setColumnSizing,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: enableFilters ? getFilteredRowModel() : undefined,
  });

  const resolvedTable = table ?? internalTable;
  const containerRef = useRef<HTMLDivElement>(null);

  const rowHeight = resolveRowHeight(density, estimatedRowHeight);
  const rows = resolvedTable.getRowModel().rows;
  const virtualization = useVirtualization(rows, rowHeight, containerRef, virtualizationThreshold);
  const containerHeight = computeContainerHeight(rows.length, rowHeight);
  const columnSizingState = resolvedTable.getState().columnSizing;

  useColumnSizingPersistence(resolvedTable, columnSizingState, storageKey);

  const gridClassName = cn("flex h-full flex-col overflow-hidden rounded-xl border bg-background shadow-sm", className);
  const headerGroups = resolvedTable.getHeaderGroups();

  const renderFilterRow = enableFilters && headerGroups.length > 0;

  const updateFilterValue = useCallback(
    (columnId: string, value: unknown) => {
      const targetColumn = resolvedTable.getColumn(columnId);
      if (!targetColumn) return;
      targetColumn.setFilterValue(value);
    },
    [resolvedTable]
  );

  return (
    <div className={gridClassName}>
      <div
        ref={containerRef}
        className="relative overflow-auto"
        style={{ maxHeight: containerHeight }}
      >
        <Table style={{ width: resolvedTable.getTotalSize() || "100%" }}>
          <TableHeader className="sticky top-0 z-10 bg-background shadow-sm">
            {headerGroups.map((headerGroup) => (
              <TableRow key={headerGroup.id} className="border-0">
                {headerGroup.headers.map((header) => {
                  if (header.isPlaceholder) {
                    return (
                      <TableHead key={header.id} className="p-0" style={{ width: header.getSize() }} />
                    );
                  }
                  const meta = header.column.columnDef.meta as ColumnMetaConfig | undefined;
                  const tooltipContent = meta?.tooltip ?? (typeof header.column.columnDef.header === "string"
                    ? header.column.columnDef.header
                    : undefined);
                  return (
                    <TableHead
                      key={header.id}
                      className="whitespace-nowrap border-b border-border bg-background px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
                      style={{ width: header.getSize() }}
                      title={tooltipContent}
                    >
                      <div className="flex items-center gap-2">
                        <span className="truncate">
                          {flexRender(header.column.columnDef.header, header.getContext())}
                        </span>
                        {header.column.getCanSort() ? (
                          <button
                            type="button"
                            className="text-[10px] uppercase text-muted-foreground"
                            onClick={header.column.getToggleSortingHandler()}
                          >
                            {header.column.getIsSorted() === "asc"
                              ? "▲"
                              : header.column.getIsSorted() === "desc"
                              ? "▼"
                              : "⇅"}
                          </button>
                        ) : null}
                        {header.column.getCanResize() ? (
                          <div
                            role="separator"
                            onMouseDown={header.getResizeHandler()}
                            onTouchStart={header.getResizeHandler()}
                            className="ml-auto h-6 w-[2px] cursor-col-resize rounded bg-transparent transition-colors hover:bg-muted"
                          />
                        ) : null}
                      </div>
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
            {renderFilterRow ? (
              <TableRow key="filters" className="border-0">
                {headerGroups[0]?.headers.map((header) => {
                  if (!header.column.getCanFilter()) {
                    return <TableHead key={header.id} className="p-0" style={{ width: header.getSize() }} />;
                  }
                  const meta = header.column.columnDef.meta as ColumnMetaConfig | undefined;
                  const filterValue = header.column.getFilterValue();
                  const searchValue = filterSearch[header.column.id] ?? "";
                  return (
                    <TableHead key={header.id} className="bg-muted/20 px-2 py-2" style={{ width: header.getSize() }}>
                      {renderFilterControl(
                        header.column,
                        meta,
                        filterValue,
                        (next) => updateFilterValue(header.column.id, next),
                        searchValue,
                        (next) => setFilterSearch((prev) => ({ ...prev, [header.column.id]: next }))
                      )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ) : null}
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell
                  colSpan={resolvedTable.getAllLeafColumns().length || 1}
                  className="h-24 text-center text-sm text-muted-foreground"
                >
                  Loading…
                </TableCell>
              </TableRow>
            ) : virtualization.rows.length ? (
              <>
                {virtualization.enabled && virtualization.paddingTop > 0 ? (
                  <TableRow aria-hidden="true" style={{ height: virtualization.paddingTop }}>
                    <TableCell colSpan={resolvedTable.getAllLeafColumns().length} className="p-0" />
                  </TableRow>
                ) : null}
                {virtualization.rows.map((row) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() ? "selected" : undefined}
                    className="hover:bg-muted/40"
                    style={{ minHeight: rowHeight }}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id} style={{ width: cell.column.getSize() }} className="align-top text-sm">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
                {virtualization.enabled && virtualization.paddingBottom > 0 ? (
                  <TableRow aria-hidden="true" style={{ height: virtualization.paddingBottom }}>
                    <TableCell colSpan={resolvedTable.getAllLeafColumns().length} className="p-0" />
                  </TableRow>
                ) : null}
              </>
            ) : (
              <TableRow>
                <TableCell
                  colSpan={resolvedTable.getAllLeafColumns().length || 1}
                  className="h-24 text-center text-sm text-muted-foreground"
                >
                  {emptyLabel}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

export type { ColumnMetaConfig };
