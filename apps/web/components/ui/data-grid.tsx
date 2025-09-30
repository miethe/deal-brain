"use client";

import {
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
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
  columns: ColumnDef<TData, any>[];
  data: TData[];
  loading?: boolean;
  emptyLabel?: string;
  className?: string;
  enableFilters?: boolean;
}

export function DataGrid<TData>({ columns, data, loading, emptyLabel = "No records.", className, enableFilters }: DataGridProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  const table = useReactTable({
    data,
    columns,
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

  const headerGroups = table.getHeaderGroups();
  const filterableHeaders = enableFilters ? headerGroups[0]?.headers ?? [] : [];

  const filterRow = useMemo(() => {
    if (!enableFilters || !filterableHeaders.length) return null;
    return (
      <TableRow>
        {filterableHeaders.map((header) => (
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
  }, [enableFilters, filterableHeaders]);

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
                <TableCell colSpan={columns.length} className="h-24 text-center text-sm text-muted-foreground">
                  Loading…
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} className="hover:bg-muted/40">
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="align-top text-sm">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center text-sm text-muted-foreground">
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
