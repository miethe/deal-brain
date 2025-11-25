"use client";

import { useMemo, useState } from "react";
import { type ColumnDef, type SortingState, getCoreRowModel, getSortedRowModel, useReactTable } from "@tanstack/react-table";
import { DataGrid } from "../ui/data-grid";
import { ColumnSelector, type ColumnDefinition } from "../ui/column-selector";
import { useColumnPreferences } from "@/hooks/use-column-preferences";
import { Card, CardContent, CardHeader } from "../ui/card";
import { Button } from "../ui/button";
import type { CPUWithAnalytics } from "@/types/cpus";

interface CPUDataTableProps {
  cpus: CPUWithAnalytics[];
  isLoading?: boolean;
}

/**
 * CPU Data Table with Column Selection
 *
 * Features:
 * - Dynamic column visibility and ordering
 * - Persistent column preferences via localStorage
 * - Sortable columns
 * - Performance metrics display
 */
export function CPUDataTable({ cpus, isLoading }: CPUDataTableProps) {
  const [sorting, setSorting] = useState<SortingState>([{ id: "name", desc: false }]);

  // Define all available columns
  const allColumnDefinitions: ColumnDefinition[] = useMemo(() => [
    { id: "name", label: "CPU Name", defaultVisible: true, description: "Processor model name" },
    { id: "manufacturer", label: "Manufacturer", defaultVisible: true, description: "CPU manufacturer (Intel/AMD)" },
    { id: "series", label: "Series", defaultVisible: false, description: "Product series" },
    { id: "socket", label: "Socket", defaultVisible: false, description: "CPU socket type" },
    { id: "cores", label: "Cores", defaultVisible: true, description: "Number of physical cores" },
    { id: "threads", label: "Threads", defaultVisible: true, description: "Number of threads" },
    { id: "base_clock_ghz", label: "Base Clock (GHz)", defaultVisible: false, description: "Base clock speed" },
    { id: "boost_clock_ghz", label: "Boost Clock (GHz)", defaultVisible: false, description: "Maximum boost clock" },
    { id: "tdp_watts", label: "TDP (W)", defaultVisible: true, description: "Thermal design power" },
    { id: "cpu_mark", label: "CPU Mark", defaultVisible: true, description: "PassMark CPU benchmark score" },
    { id: "single_thread_rating", label: "Single Thread", defaultVisible: true, description: "Single-thread performance" },
    { id: "igpu_mark", label: "iGPU Mark", defaultVisible: false, description: "Integrated GPU benchmark score" },
    { id: "release_year", label: "Release Year", defaultVisible: false, description: "Year of release" },
    { id: "active_listings_count", label: "Listings", defaultVisible: true, description: "Number of active listings" },
    { id: "min_price_usd", label: "Min Price", defaultVisible: true, description: "Minimum listing price" },
    { id: "max_price_usd", label: "Max Price", defaultVisible: false, description: "Maximum listing price" },
    { id: "avg_price_usd", label: "Avg Price", defaultVisible: true, description: "Average listing price" },
  ], []);

  // Column preferences
  const { selectedColumns, updateColumns } = useColumnPreferences("cpus", allColumnDefinitions);

  // Build all column definitions
  const allColumns = useMemo<ColumnDef<CPUWithAnalytics>[]>(() => [
    {
      id: "name",
      accessorKey: "name",
      header: "CPU Name",
      cell: ({ getValue }) => <span className="font-medium">{getValue() as string}</span>,
      enableSorting: true,
      enableResizing: true,
      size: 260,
    },
    {
      id: "manufacturer",
      accessorKey: "manufacturer",
      header: "Manufacturer",
      cell: ({ getValue }) => <span className="text-sm">{getValue() as string || "—"}</span>,
      enableSorting: true,
      size: 120,
    },
    {
      id: "series",
      accessorKey: "series",
      header: "Series",
      cell: ({ getValue }) => <span className="text-sm">{getValue() as string || "—"}</span>,
      enableSorting: true,
      size: 140,
    },
    {
      id: "socket",
      accessorKey: "socket",
      header: "Socket",
      cell: ({ getValue }) => <span className="text-sm">{getValue() as string || "—"}</span>,
      enableSorting: true,
      size: 120,
    },
    {
      id: "cores",
      accessorKey: "cores",
      header: "Cores",
      cell: ({ getValue }) => <span className="text-sm text-right">{getValue() as number || "—"}</span>,
      enableSorting: true,
      size: 80,
    },
    {
      id: "threads",
      accessorKey: "threads",
      header: "Threads",
      cell: ({ getValue }) => <span className="text-sm text-right">{getValue() as number || "—"}</span>,
      enableSorting: true,
      size: 80,
    },
    {
      id: "base_clock_ghz",
      accessorKey: "base_clock_ghz",
      header: "Base Clock",
      cell: ({ getValue }) => {
        const val = getValue() as number | null;
        return <span className="text-sm text-right">{val ? `${val.toFixed(2)} GHz` : "—"}</span>;
      },
      enableSorting: true,
      size: 110,
    },
    {
      id: "boost_clock_ghz",
      accessorKey: "boost_clock_ghz",
      header: "Boost Clock",
      cell: ({ getValue }) => {
        const val = getValue() as number | null;
        return <span className="text-sm text-right">{val ? `${val.toFixed(2)} GHz` : "—"}</span>;
      },
      enableSorting: true,
      size: 110,
    },
    {
      id: "tdp_watts",
      accessorKey: "tdp_watts",
      header: "TDP",
      cell: ({ getValue }) => {
        const val = getValue() as number | null;
        return <span className="text-sm text-right">{val ? `${val}W` : "—"}</span>;
      },
      enableSorting: true,
      size: 80,
    },
    {
      id: "cpu_mark",
      accessorKey: "cpu_mark",
      header: "CPU Mark",
      cell: ({ getValue }) => {
        const val = getValue() as number | null;
        return <span className="text-sm text-right font-medium">{val ? val.toLocaleString() : "—"}</span>;
      },
      enableSorting: true,
      size: 120,
    },
    {
      id: "single_thread_rating",
      accessorKey: "single_thread_rating",
      header: "Single Thread",
      cell: ({ getValue }) => {
        const val = getValue() as number | null;
        return <span className="text-sm text-right">{val ? val.toLocaleString() : "—"}</span>;
      },
      enableSorting: true,
      size: 120,
    },
    {
      id: "igpu_mark",
      accessorKey: "igpu_mark",
      header: "iGPU Mark",
      cell: ({ getValue }) => {
        const val = getValue() as number | null;
        return <span className="text-sm text-right">{val ? val.toLocaleString() : "—"}</span>;
      },
      enableSorting: true,
      size: 110,
    },
    {
      id: "release_year",
      accessorKey: "release_year",
      header: "Year",
      cell: ({ getValue }) => <span className="text-sm">{getValue() as number || "—"}</span>,
      enableSorting: true,
      size: 80,
    },
    {
      id: "active_listings_count",
      accessorKey: "active_listings_count",
      header: "Listings",
      cell: ({ getValue }) => {
        const val = getValue() as number | undefined;
        return <span className="text-sm text-right">{val ?? 0}</span>;
      },
      enableSorting: true,
      size: 90,
    },
    {
      id: "min_price_usd",
      accessorKey: "min_price_usd",
      header: "Min Price",
      cell: ({ getValue }) => {
        const val = getValue() as number | null;
        return <span className="text-sm text-right">{val ? `$${val.toFixed(0)}` : "—"}</span>;
      },
      enableSorting: true,
      size: 100,
    },
    {
      id: "max_price_usd",
      accessorKey: "max_price_usd",
      header: "Max Price",
      cell: ({ getValue }) => {
        const val = getValue() as number | null;
        return <span className="text-sm text-right">{val ? `$${val.toFixed(0)}` : "—"}</span>;
      },
      enableSorting: true,
      size: 100,
    },
    {
      id: "avg_price_usd",
      accessorKey: "avg_price_usd",
      header: "Avg Price",
      cell: ({ getValue }) => {
        const val = getValue() as number | null;
        return <span className="text-sm text-right font-medium">{val ? `$${val.toFixed(0)}` : "—"}</span>;
      },
      enableSorting: true,
      size: 100,
    },
  ], []);

  // Filter and reorder columns based on preferences
  const visibleColumns = useMemo(() => {
    const columnMap = new Map<string, ColumnDef<CPUWithAnalytics>>();
    allColumns.forEach((col) => {
      const id = (col as any).id || (col as any).accessorKey;
      if (id) {
        columnMap.set(String(id), col);
      }
    });

    const ordered: ColumnDef<CPUWithAnalytics>[] = [];
    selectedColumns.forEach((id) => {
      const column = columnMap.get(id);
      if (column) {
        ordered.push(column);
      }
    });

    return ordered;
  }, [allColumns, selectedColumns]);

  const table = useReactTable({
    data: cpus,
    columns: visibleColumns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const resetView = () => {
    setSorting([{ id: "name", desc: false }]);
  };

  return (
    <Card className="w-full border-0 bg-background shadow-none">
      <CardHeader className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-2xl font-semibold tracking-tight">CPU Data Table</h2>
            <p className="text-sm text-muted-foreground">
              Sortable table view with performance metrics and pricing analytics.
            </p>
          </div>
          <div className="flex gap-2">
            <ColumnSelector
              columns={allColumnDefinitions}
              selectedColumns={selectedColumns}
              onColumnsChange={updateColumns}
              variant="outline"
              size="sm"
            />
            <Button variant="ghost" size="sm" onClick={resetView}>
              Reset view
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <DataGrid
          table={table}
          loading={isLoading}
          emptyLabel="No CPUs found"
          className="border"
          storageKey="cpu-data-table"
          estimatedRowHeight={44}
          virtualizationThreshold={100}
        />
      </CardContent>
    </Card>
  );
}
