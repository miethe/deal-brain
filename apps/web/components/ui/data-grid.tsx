"use client";

import {
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
  type Table as TableInstance,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable
} from "@tanstack/react-table";
import { useMemo, useState } from "react";

import { cn } from "../../lib/utils";
import { Input } from "./input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./table";

interface DataGridProps<TData> {
  columns?: ColumnDef<TData, any>[];
  data?: TData[];
  table?: TableInstance<TData>;
  loading?: boolean;
  emptyLabel?: string;
  className?: string;
  enableFilters?: boolean;
}

export function DataGrid<TData>({ columns, data, table, loading, emptyLabel = "No records.", className, enableFilters }: DataGridProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  const internalTable = useReactTable({
    data: data ?? [],
    columns: columns ?? [],
    state: {
      sorting,
      columnFilters
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: enableFilters ? getFilteredRowModel() : undefined
  });

  const resolvedTable = table ?? internalTable;
  const headerGroups = resolvedTable.getHeaderGroups();

  const filterRow = useMemo(() => {
    if (!enableFilters) return null;
    const headers = headerGroups[0]?.headers ?? [];
    if (!headers.length) return null;
    return (
      <TableRow>
        {headers.map((header) => (
          <TableHead key={header.id} className="bg-muted/30">
            {header.column.getCanFilter() ? (
              <Input
                placeholder="Filter"
                value={(header.column.getFilterValue() as string) ?? ""}
                onChange={(event) => header.column.setFilterValue(event.target.value)}
                className="h-8 text-xs"
              />
            ) : null}
          </TableHead>
        ))}
      </TableRow>
    );
  }, [enableFilters, headerGroups]);

  return (
    <div className={cn("overflow-hidden rounded-xl border bg-background shadow-sm", className)}>
      <div className="max-h-[480px] overflow-auto">
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-background shadow-sm">
            {headerGroups.map((group) => (
              <TableRow key={group.id}>
                {group.headers.map((header) => (
                  <TableHead key={header.id} className="whitespace-nowrap text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
            {filterRow}
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={resolvedTable.getAllLeafColumns().length || 1} className="h-24 text-center text-sm text-muted-foreground">
                  Loading…
                </TableCell>
              </TableRow>
            ) : resolvedTable.getRowModel().rows.length ? (
              resolvedTable.getRowModel().rows.map((row) => (
                <TableRow key={row.id} data-state={row.getIsSelected() ? "selected" : undefined} className="hover:bg-muted/40">
                  {row.getVisibleCells().map((cell) => {
                    if (cell.getIsPlaceholder()) {
                      return null;
                    }

                    if (cell.getIsGrouped()) {
                      return (
                        <TableCell key={cell.id} className="align-top text-sm">
                          <button
                            type="button"
                            className="mr-2 inline-flex h-5 w-5 items-center justify-center rounded border border-input text-xs"
                            onClick={row.getToggleExpandedHandler()}
                            aria-label={row.getIsExpanded() ? "Collapse group" : "Expand group"}
                          >
                            {row.getIsExpanded() ? "−" : "+"}
                          </button>
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                          <span className="ml-2 text-xs text-muted-foreground">({row.subRows?.length ?? 0})</span>
                        </TableCell>
                      );
                    }

                    if (cell.getIsAggregated()) {
                      return (
                        <TableCell key={cell.id} className="align-top text-sm font-medium">
                          {flexRender(cell.column.columnDef.aggregatedCell ?? cell.column.columnDef.cell, cell.getContext())}
                        </TableCell>
                      );
                    }

                    return (
                      <TableCell key={cell.id} className="align-top text-sm">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={resolvedTable.getAllLeafColumns().length || 1} className="h-24 text-center text-sm text-muted-foreground">
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
