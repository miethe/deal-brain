"use client";

import { useCallback, useMemo, useState } from "react";
import {
  type ColumnDef,
  type SortingState,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  flexRender,
} from "@tanstack/react-table";
import { ChevronDown, ChevronUp, ChevronsUpDown, Expand, Trash2, Share2, MoreVertical, Image as ImageIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useConfirmation } from "@/components/ui/confirmation-dialog";
import { useRemoveCollectionItem } from "@/hooks/use-collections";
import { CardDownloadModal } from "@/components/listings/card-download-modal";
import type { CollectionItem, CollectionItemStatus } from "@/types/collections";
import type { ListingDetail } from "@/types/listing-detail";

interface WorkspaceTableProps {
  collectionId: number | string;
  items: CollectionItem[];
  onItemExpand: (item: CollectionItem) => void;
}

const STATUS_COLORS: Record<
  CollectionItemStatus,
  { variant: "default" | "secondary" | "destructive" | "outline"; label: string }
> = {
  undecided: { variant: "default", label: "Undecided" },
  shortlisted: { variant: "secondary", label: "Shortlisted" },
  rejected: { variant: "outline", label: "Rejected" },
  bought: { variant: "default", label: "Bought" },
};

/**
 * Workspace Table View
 *
 * Sortable, filterable table for collection items with:
 * - Selectable rows (checkboxes)
 * - Sortable columns (price, score, CPU mark)
 * - Status badges
 * - Expand button for notes panel
 * - Remove item action
 */
export function WorkspaceTable({
  collectionId,
  items,
  onItemExpand,
}: WorkspaceTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [rowSelection, setRowSelection] = useState({});
  const { confirm, dialog } = useConfirmation();

  const removeItemMutation = useRemoveCollectionItem({ collectionId });

  const handleRemoveItem = useCallback(
    async (itemId: number, listingTitle: string) => {
      const confirmed = await confirm({
        title: "Remove item?",
        description: `Remove "${listingTitle}" from this collection?`,
        confirmText: "Remove",
        variant: "destructive",
      });

      if (confirmed) {
        removeItemMutation.mutate(itemId);
      }
    },
    [confirm, removeItemMutation]
  );

  const columns = useMemo<ColumnDef<CollectionItem>[]>(
    () => [
      {
        id: "select",
        header: ({ table }) => (
          <Checkbox
            checked={table.getIsAllPageRowsSelected()}
            onCheckedChange={(value) =>
              table.toggleAllPageRowsSelected(!!value)
            }
            aria-label="Select all"
          />
        ),
        cell: ({ row }) => (
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={(value) => row.toggleSelected(!!value)}
            aria-label="Select row"
          />
        ),
        enableSorting: false,
        size: 40,
      },
      {
        id: "image",
        header: "",
        cell: ({ row }) => {
          const listing = row.original.listing;
          return (
            <div className="w-16 h-16 bg-muted rounded flex items-center justify-center overflow-hidden">
              {listing.thumbnail_url ? (
                <img
                  src={listing.thumbnail_url}
                  alt={listing.title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="text-xs text-muted-foreground">No image</span>
              )}
            </div>
          );
        },
        enableSorting: false,
        size: 80,
      },
      {
        accessorKey: "listing.title",
        header: "Name",
        cell: ({ row }) => {
          const listing = row.original.listing;
          const item = row.original;
          const isShared = item.share_id && item.shared_by_name;

          return (
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="font-medium">{listing.title}</div>
                {isShared && (
                  <Badge variant="outline" className="text-xs gap-1">
                    <Share2 className="h-3 w-3" />
                    Shared
                  </Badge>
                )}
              </div>
              <div className="text-xs text-muted-foreground">
                {listing.cpu_name && <span>{listing.cpu_name}</span>}
                {listing.gpu_name && (
                  <span className="ml-2">• {listing.gpu_name}</span>
                )}
              </div>
              {isShared && item.shared_by_name && (
                <div className="text-xs text-muted-foreground italic">
                  Shared by {item.shared_by_name}
                </div>
              )}
            </div>
          );
        },
        size: 300,
      },
      {
        accessorKey: "listing.price_usd",
        header: ({ column }) => {
          return (
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="h-auto p-0 hover:bg-transparent"
            >
              Price
              {column.getIsSorted() === "asc" ? (
                <ChevronUp className="ml-2 h-4 w-4" />
              ) : column.getIsSorted() === "desc" ? (
                <ChevronDown className="ml-2 h-4 w-4" />
              ) : (
                <ChevronsUpDown className="ml-2 h-4 w-4" />
              )}
            </Button>
          );
        },
        cell: ({ row }) => {
          const listing = row.original.listing;
          return (
            <div>
              <div className="font-semibold">
                ${listing.price_usd.toLocaleString()}
              </div>
              {listing.adjusted_price_usd && (
                <div className="text-xs text-muted-foreground">
                  adj: ${listing.adjusted_price_usd.toLocaleString()}
                </div>
              )}
            </div>
          );
        },
        size: 120,
      },
      {
        accessorKey: "listing.cpu.cpu_mark_multi",
        header: ({ column }) => {
          return (
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="h-auto p-0 hover:bg-transparent"
            >
              CPU Mark
              {column.getIsSorted() === "asc" ? (
                <ChevronUp className="ml-2 h-4 w-4" />
              ) : column.getIsSorted() === "desc" ? (
                <ChevronDown className="ml-2 h-4 w-4" />
              ) : (
                <ChevronsUpDown className="ml-2 h-4 w-4" />
              )}
            </Button>
          );
        },
        cell: ({ row }) => {
          const cpuMark = row.original.listing.cpu?.cpu_mark_multi;
          return cpuMark ? cpuMark.toLocaleString() : "—";
        },
        size: 120,
      },
      {
        accessorKey: "listing.dollar_per_cpu_mark_multi",
        header: ({ column }) => {
          return (
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="h-auto p-0 hover:bg-transparent"
            >
              $/CPU Mark
              {column.getIsSorted() === "asc" ? (
                <ChevronUp className="ml-2 h-4 w-4" />
              ) : column.getIsSorted() === "desc" ? (
                <ChevronDown className="ml-2 h-4 w-4" />
              ) : (
                <ChevronsUpDown className="ml-2 h-4 w-4" />
              )}
            </Button>
          );
        },
        cell: ({ row }) => {
          const metric = row.original.listing.dollar_per_cpu_mark_multi;
          return metric ? `$${metric.toFixed(3)}` : "—";
        },
        size: 140,
      },
      {
        accessorKey: "listing.form_factor",
        header: "Form Factor",
        cell: ({ row }) => row.original.listing.form_factor || "—",
        size: 120,
      },
      {
        accessorKey: "listing.score_composite",
        header: ({ column }) => {
          return (
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="h-auto p-0 hover:bg-transparent"
            >
              Score
              {column.getIsSorted() === "asc" ? (
                <ChevronUp className="ml-2 h-4 w-4" />
              ) : column.getIsSorted() === "desc" ? (
                <ChevronDown className="ml-2 h-4 w-4" />
              ) : (
                <ChevronsUpDown className="ml-2 h-4 w-4" />
              )}
            </Button>
          );
        },
        cell: ({ row }) => {
          const score = row.original.listing.score_composite;
          return score ? score.toFixed(2) : "—";
        },
        size: 100,
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => {
          const status = row.original.status;
          const statusConfig = STATUS_COLORS[status];
          return (
            <Badge variant={statusConfig.variant} className="text-xs">
              {statusConfig.label}
            </Badge>
          );
        },
        size: 120,
      },
      {
        id: "actions",
        header: "Actions",
        cell: ({ row }) => {
          const item = row.original;
          // Convert CollectionItem listing to ListingDetail format
          const listingDetail: ListingDetail = {
            ...item.listing,
            cpu: item.listing.cpu || undefined,
            gpu: item.listing.gpu || undefined,
            ports_profile: item.listing.ports_profile || undefined,
          };

          return (
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onItemExpand(item)}
                aria-label="Expand notes"
              >
                <Expand className="h-4 w-4" />
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" aria-label="More actions">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <CardDownloadModal
                    listing={listingDetail}
                    trigger={
                      <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                        <ImageIcon className="h-4 w-4 mr-2" />
                        Download Card
                      </DropdownMenuItem>
                    }
                  />
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() =>
                      handleRemoveItem(item.id, item.listing.title)
                    }
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Remove
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          );
        },
        enableSorting: false,
        size: 120,
      },
    ],
    [collectionId, onItemExpand, removeItemMutation, handleRemoveItem]
  );

  const table = useReactTable({
    data: items,
    columns,
    state: {
      sorting,
      rowSelection,
    },
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  if (items.length === 0) {
    return (
      <div className="border rounded-lg p-12 text-center">
        <p className="text-muted-foreground">No items in this collection yet.</p>
        <p className="text-sm text-muted-foreground mt-2">
          Add listings from the main listings view.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} style={{ width: header.getSize() }}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                data-state={row.getIsSelected() && "selected"}
                className="hover:bg-muted/50"
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Confirmation Dialog */}
      {dialog}
    </>
  );
}
