"use client";

import {
  type ColumnDef,
  type ColumnFiltersState,
  type ColumnSizingState,
  type PaginationState,
  type Row,
  type SortingState,
  type Table as TableInstance,
  type VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable
} from "@tanstack/react-table";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useDebouncedCallback } from "use-debounce";
import { useVirtualizer } from "@tanstack/react-virtual";

import { cn } from "../../lib/utils";
import { telemetry } from "../../lib/telemetry";
import { Input } from "./input";
import { Button } from "./button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./table";
import { InfoTooltip } from "./info-tooltip";

const DEFAULT_ROW_HEIGHT = 44;
const COMPACT_ROW_HEIGHT = 36;
const HEADER_HEIGHT = 52;
const MIN_TABLE_HEIGHT = 240;
const MAX_TABLE_HEIGHT = 640;
const VIRTUALIZATION_THRESHOLD = 100;
const OVERSCAN_ROWS = 10;
const DEFAULT_PAGE_SIZE = 50;
const PAGE_SIZE_OPTIONS = [25, 50, 100, 200];
const MIN_COLUMN_WIDTH = 80;
const COLUMN_RESIZE_DEBOUNCE_MS = 150;

interface ColumnOption {
  label: string;
  value: string;
}

interface ColumnMetaConfig {
  tooltip?: string;
  description?: string;
  filterType?: "text" | "number" | "select" | "multi-select" | "boolean";
  options?: ColumnOption[];
  minWidth?: number;
  enableTextWrap?: boolean;
}

interface PaginationConfig {
  pageSize?: number;
  pageSizeOptions?: number[];
  defaultPageIndex?: number;
}

interface StickyColumnConfig {
  columnId: string;
  position: "left" | "right";
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
  enableInlineEdit?: boolean;
  onCellEdit?: (rowId: string | number, columnId: string, value: any) => Promise<void>;
  enableRowSelection?: boolean;
  onRowSelectionChange?: (selectedRows: TData[]) => void;
  pagination?: PaginationConfig | false;
  stickyColumns?: StickyColumnConfig[];
  highlightedRowId?: number | null;
  highlightedRef?: React.RefObject<HTMLTableRowElement>;
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

  // Debounced save to localStorage
  const debouncedSave = useDebouncedCallback(
    (sizing: ColumnSizingState) => {
      if (!storageKey || typeof window === "undefined") return;
      const key = `${storageKey}:columnSizing`;
      window.localStorage.setItem(key, JSON.stringify(sizing));
    },
    COLUMN_RESIZE_DEBOUNCE_MS
  );

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
      // Filter out any saved sizes for columns that no longer exist
      const valid = new Set(table.getAllLeafColumns().map((c) => c.id));
      const filtered: ColumnSizingState = {};
      for (const [colId, size] of Object.entries(parsed)) {
        if (valid.has(colId)) filtered[colId] = size as number;
      }
      table.setColumnSizing(filtered);
    } catch (error) {
      telemetry.error("frontend.datagrid.hydration_failed", {
        message: (error as Error)?.message ?? "Unknown error",
      });
    }
    hydratedRef.current = true;
  }, [storageKey, table]);

  useEffect(() => {
    if (!table || !storageKey) return;
    if (typeof window === "undefined" || !hydratedRef.current) return;

    debouncedSave(columnSizing);
  }, [columnSizing, storageKey, table, debouncedSave]);
}

function useVirtualization<TData>(
  rows: Row<TData>[],
  rowHeight: number,
  containerRef: React.RefObject<HTMLDivElement>,
  threshold: number
): VirtualizationState<TData> {
  const total = rows.length;
  const enabled = total > threshold;

  // Use @tanstack/react-virtual for virtualization
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => rowHeight,
    overscan: OVERSCAN_ROWS,
    enabled,
  });

  const virtualItems = enabled ? rowVirtualizer.getVirtualItems() : [];
  const visibleRows = enabled
    ? virtualItems.map(item => rows[item.index])
    : rows;

  const paddingTop = enabled && virtualItems.length > 0
    ? virtualItems[0].start
    : 0;

  const paddingBottom = enabled && virtualItems.length > 0
    ? rowVirtualizer.getTotalSize() - virtualItems[virtualItems.length - 1].end
    : 0;

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

function getStickyColumnStyles(
  columnId: string,
  stickyColumns: StickyColumnConfig[],
  columnSizing: ColumnSizingState
): React.CSSProperties {
  const config = stickyColumns.find((c) => c.columnId === columnId);
  if (!config) return {};

  // Calculate offset based on columns before this one
  const samePositionCols = stickyColumns.filter((c) => c.position === config.position);
  const index = samePositionCols.findIndex((c) => c.columnId === columnId);

  let offset = 0;
  for (let i = 0; i < index; i++) {
    const colId = samePositionCols[i].columnId;
    offset += columnSizing[colId] || 150; // Default width if not sized
  }

  return {
    position: "sticky",
    [config.position]: offset,
    zIndex: config.position === "left" ? 10 : 11,
    backgroundColor: "hsl(var(--background))",
    borderRight: config.position === "left" ? "1px solid hsl(var(--border))" : "none",
    borderLeft: config.position === "right" ? "1px solid hsl(var(--border))" : "none",
  };
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
          value={value !== null && value !== undefined ? String(value) : ""}
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
          value={value !== null && value !== undefined ? String(value) : ""}
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
          value={value !== null && value !== undefined ? String(value) : ""}
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

      // Calculate dynamic height based on number of options
      const optionCount = options.length;
      const hasSearch = (meta?.options ?? []).length > 5;
      // Each option is ~28px (checkbox + padding), search input is ~32px, padding is ~16px
      const contentHeight = optionCount * 28 + (hasSearch ? 32 : 0) + 16;
      const maxHeight = 320; // Max height in pixels (equivalent to max-h-80)
      const dropdownHeight = Math.min(contentHeight, maxHeight);
      const needsScroll = contentHeight > maxHeight;

      return (
        <div className="flex h-full flex-col gap-1">
          {hasSearch && (
            <Input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search"
              className="h-8 w-full text-xs"
            />
          )}
          <div
            className={cn(
              "grid gap-1 rounded-md border border-input bg-background p-2 text-xs",
              needsScroll && "overflow-y-auto"
            )}
            style={{ maxHeight: `${dropdownHeight}px` }}
          >
            {options.length ? (
              options.map((option) => {
                const checked = selections.includes(option.value);
                return (
                  <label key={option.value} className="flex cursor-pointer items-center gap-2 whitespace-nowrap">
                    <input
                      type="checkbox"
                      className="h-3 w-3 flex-shrink-0"
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
  pagination,
  stickyColumns = [],
  highlightedRowId,
  highlightedRef,
}: DataGridProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [columnSizing, setColumnSizing] = useState<ColumnSizingState>({});
  const [filterSearch, setFilterSearch] = useState<Record<string, string>>({});
  const [constrainedColumns, setConstrainedColumns] = useState<Set<string>>(new Set());

  const paginationConfig = pagination === false ? null : pagination;
  const [paginationState, setPaginationState] = useState<PaginationState>({
    pageIndex: paginationConfig?.defaultPageIndex ?? 0,
    pageSize: paginationConfig?.pageSize ?? DEFAULT_PAGE_SIZE,
  });

  // Constrained column sizing handler
  const handleColumnSizingChange = useCallback((updater: any) => {
    setColumnSizing((prev) => {
      const next = typeof updater === 'function' ? updater(prev) : updater;
      const constrainedSizing = { ...next };
      const newConstrainedCols = new Set<string>();

      Object.entries(constrainedSizing).forEach(([colId, size]) => {
        const column = (table ?? internalTable)?.getColumn(colId);
        const meta = column?.columnDef.meta as ColumnMetaConfig | undefined;
        const minWidth = meta?.minWidth || MIN_COLUMN_WIDTH;

        if ((size as number) < minWidth) {
          constrainedSizing[colId] = minWidth;
          newConstrainedCols.add(colId);
        }
      });

      setConstrainedColumns(newConstrainedCols);
      return constrainedSizing;
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const internalTable = useReactTable({
    data: data ?? [],
    columns: columns ?? [],
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      columnSizing,
      ...(paginationConfig && { pagination: paginationState }),
    },
    columnResizeMode: "onChange",
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onColumnSizingChange: handleColumnSizingChange,
    ...(paginationConfig && { onPaginationChange: setPaginationState }),
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: enableFilters ? getFilteredRowModel() : undefined,
    ...(paginationConfig && { getPaginationRowModel: getPaginationRowModel() }),
    manualPagination: false,
  });

  const resolvedTable = table ?? internalTable;
  const containerRef = useRef<HTMLDivElement>(null);

  const rowHeight = resolveRowHeight(density, estimatedRowHeight);
  const rows = resolvedTable.getRowModel().rows;
  const virtualization = useVirtualization(rows, rowHeight, containerRef, virtualizationThreshold);
  const containerHeight = computeContainerHeight(rows.length, rowHeight);
  const columnSizingState = resolvedTable.getState().columnSizing;

  useColumnSizingPersistence(resolvedTable, columnSizingState, storageKey);

  const gridClassName = cn("flex h-full w-full flex-col overflow-hidden rounded-xl border bg-background shadow-sm", className);
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
        className="listings-table-container relative flex-1 overflow-x-auto overflow-y-auto"
      >
        <Table className="listings-table" style={{ width: resolvedTable.getTotalSize(), minWidth: "100%" }}>
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
                  const description = meta?.description;
                  const stickyStyles = getStickyColumnStyles(header.column.id, stickyColumns, columnSizingState);
                  const minWidth = meta?.minWidth || MIN_COLUMN_WIDTH;
                  const isConstrained = constrainedColumns.has(header.column.id);

                  return (
                    <TableHead
                      key={header.id}
                      className={cn(
                        "whitespace-nowrap border-b border-border bg-background px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground",
                        isConstrained && "border-r-2 border-dashed border-amber-400"
                      )}
                      style={{ width: header.getSize(), minWidth, ...stickyStyles }}
                      title={tooltipContent}
                    >
                      <div className="flex items-center gap-2">
                        <span className="truncate">
                          {flexRender(header.column.columnDef.header, header.getContext())}
                        </span>
                        {description && <InfoTooltip content={description} />}
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
                            className="ml-auto h-6 w-[3px] cursor-col-resize rounded bg-border/30 transition-colors hover:bg-border"
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
                  const stickyStyles = getStickyColumnStyles(header.column.id, stickyColumns, columnSizingState);
                  if (!header.column.getCanFilter()) {
                    return <TableHead key={header.id} className="p-0" style={{ width: header.getSize(), ...stickyStyles }} />;
                  }
                  const meta = header.column.columnDef.meta as ColumnMetaConfig | undefined;
                  const filterValue = header.column.getFilterValue();
                  const searchValue = filterSearch[header.column.id] ?? "";
                  return (
                    <TableHead key={header.id} className="bg-muted/20 px-2 py-2" style={{ width: header.getSize(), ...stickyStyles }}>
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
                {virtualization.rows.map((row) => {
                  const rowId = (row.original as any).id;
                  const isHighlighted = highlightedRowId !== null && highlightedRowId !== undefined && rowId === highlightedRowId;

                  return (
                    <TableRow
                      key={row.id}
                      ref={isHighlighted ? highlightedRef : null}
                      data-state={row.getIsSelected() ? "selected" : undefined}
                      data-highlighted={isHighlighted}
                      data-listings-table-row={true}
                      tabIndex={isHighlighted ? -1 : undefined}
                      aria-label={isHighlighted ? "Newly created listing" : undefined}
                      className="hover:bg-muted/40 outline-none"
                      style={{ minHeight: rowHeight }}
                    >
                      {row.getVisibleCells().map((cell) => {
                        const stickyStyles = getStickyColumnStyles(cell.column.id, stickyColumns, columnSizingState);
                        const meta = cell.column.columnDef.meta as ColumnMetaConfig | undefined;
                        const minWidth = meta?.minWidth || MIN_COLUMN_WIDTH;
                        const isConstrained = constrainedColumns.has(cell.column.id);

                        return (
                          <TableCell
                            key={cell.id}
                            style={{ width: cell.column.getSize(), minWidth, ...stickyStyles }}
                            className={cn(
                              "align-top text-sm",
                              meta?.enableTextWrap && "whitespace-normal break-words",
                              isConstrained && "border-r-2 border-dashed border-amber-400"
                            )}
                          >
                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  );
                })}
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
      {paginationConfig && (
        <PaginationControls
          table={resolvedTable}
          pageSizeOptions={paginationConfig.pageSizeOptions ?? PAGE_SIZE_OPTIONS}
        />
      )}
    </div>
  );
}

interface PaginationControlsProps<TData> {
  table: TableInstance<TData>;
  pageSizeOptions: number[];
}

function PaginationControls<TData>({
  table,
  pageSizeOptions,
}: PaginationControlsProps<TData>) {
  const pageCount = table.getPageCount();
  const pageIndex = table.getState().pagination.pageIndex;
  const pageSize = table.getState().pagination.pageSize;
  const totalRows = table.getFilteredRowModel().rows.length;

  const startRow = pageIndex * pageSize + 1;
  const endRow = Math.min((pageIndex + 1) * pageSize, totalRows);

  return (
    <div className="flex items-center justify-between gap-4 border-t bg-background px-4 py-3">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>
          Showing {startRow} to {endRow} of {totalRows} rows
        </span>
      </div>
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Rows per page:</span>
          <select
            className="h-8 rounded-md border border-input bg-background px-2 text-sm"
            value={pageSize}
            onChange={(e) => {
              table.setPageSize(Number(e.target.value));
            }}
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          >
            {"<<"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            {"<"}
          </Button>
          <span className="flex items-center gap-1 px-2 text-sm">
            <span>Page</span>
            <strong>
              {pageIndex + 1} of {pageCount}
            </strong>
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            {">"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.setPageIndex(pageCount - 1)}
            disabled={!table.getCanNextPage()}
          >
            {">>"}
          </Button>
        </div>
      </div>
    </div>
  );
}

export type { ColumnMetaConfig, PaginationConfig, StickyColumnConfig };
