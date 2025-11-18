"use client";

import { useState } from "react";
import { Download, Settings, Grid3x3, List } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { API_URL } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import type { CollectionWithItems } from "@/types/collections";

interface WorkspaceHeaderProps {
  collection: CollectionWithItems;
  viewMode: "table" | "cards";
  onViewModeChange: (mode: "table" | "cards") => void;
}

/**
 * Workspace Header
 *
 * Top section with:
 * - Collection name (editable inline)
 * - Item count
 * - Edit button (settings modal)
 * - Export button (CSV/JSON dropdown)
 * - View toggle (table/cards)
 */
export function WorkspaceHeader({
  collection,
  viewMode,
  onViewModeChange,
}: WorkspaceHeaderProps) {
  const { toast } = useToast();
  const [isEditingName, setIsEditingName] = useState(false);
  const [name, setName] = useState(collection.name);

  const handleExport = async (format: "csv" | "json") => {
    try {
      const response = await fetch(
        `${API_URL}/v1/collections/${collection.id}/export?format=${format}`
      );

      if (!response.ok) {
        throw new Error("Export failed");
      }

      // Get the filename from Content-Disposition header or create one
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = `collection-${collection.id}.${format}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Export successful",
        description: `Collection exported as ${format.toUpperCase()}`,
      });
    } catch (error) {
      toast({
        title: "Export failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    }
  };

  const handleNameSave = async () => {
    // TODO: Implement collection name update API call
    setIsEditingName(false);
    toast({
      title: "Name updated",
      description: "Collection name has been updated (feature coming soon)",
    });
  };

  return (
    <div className="space-y-4">
      {/* Title and Actions Row */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {isEditingName ? (
            <div className="flex items-center gap-2">
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                onBlur={handleNameSave}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleNameSave();
                  } else if (e.key === "Escape") {
                    setName(collection.name);
                    setIsEditingName(false);
                  }
                }}
                className="text-2xl font-semibold h-auto py-1"
                autoFocus
              />
            </div>
          ) : (
            <h1
              className="text-3xl font-bold cursor-pointer hover:text-muted-foreground transition-colors"
              onClick={() => setIsEditingName(true)}
              title="Click to edit"
            >
              {collection.name}
            </h1>
          )}
          <p className="text-sm text-muted-foreground mt-1">
            {collection.item_count} {collection.item_count === 1 ? "item" : "items"}
          </p>
          {collection.description && (
            <p className="text-sm text-muted-foreground mt-2">
              {collection.description}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Export Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => handleExport("csv")}>
                Export as CSV
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport("json")}>
                Export as JSON
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Edit/Settings Button */}
          <Button variant="outline" size="sm" disabled>
            <Settings className="h-4 w-4 mr-2" />
            Edit
          </Button>
        </div>
      </div>

      {/* View Controls */}
      <div className="flex items-center justify-between gap-4 border-t pt-4">
        <div className="text-sm text-muted-foreground">
          Showing {collection.items.length} of {collection.item_count} items
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">View:</span>
          <div className="flex border rounded-md">
            <Button
              variant={viewMode === "table" ? "default" : "ghost"}
              size="sm"
              onClick={() => onViewModeChange("table")}
              className="rounded-r-none"
            >
              <List className="h-4 w-4 mr-1" />
              Table
            </Button>
            <Button
              variant={viewMode === "cards" ? "default" : "ghost"}
              size="sm"
              onClick={() => onViewModeChange("cards")}
              className="rounded-l-none border-l"
            >
              <Grid3x3 className="h-4 w-4 mr-1" />
              Cards
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
