"use client";

import * as React from "react";
import { useState, useCallback, useMemo } from "react";
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, type DragEndEvent } from "@dnd-kit/core";
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Columns3 } from "lucide-react";
import { Button } from "./button";
import { Checkbox } from "./checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./dropdown-menu";
import { cn } from "../../lib/utils";

/**
 * Column definition for the column selector
 */
export interface ColumnDefinition {
  /** Unique column identifier */
  id: string;
  /** Display label for the column */
  label: string;
  /** Whether this column is visible by default */
  defaultVisible: boolean;
  /** Optional description for accessibility */
  description?: string;
}

export interface ColumnSelectorProps {
  /** All available columns */
  columns: ColumnDefinition[];
  /** IDs of currently selected/visible columns in order */
  selectedColumns: string[];
  /** Callback when column selection or order changes */
  onColumnsChange: (columnIds: string[]) => void;
  /** Optional button variant */
  variant?: "default" | "outline" | "ghost";
  /** Optional button size */
  size?: "default" | "sm" | "lg";
  /** Optional className for the trigger button */
  className?: string;
}

interface SortableItemProps {
  id: string;
  label: string;
  checked: boolean;
  onToggle: (id: string) => void;
  description?: string;
}

/**
 * Sortable column item with drag handle and checkbox
 */
function SortableItem({ id, label, checked, onToggle, description }: SortableItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "flex items-center gap-2 rounded-md px-2 py-2 transition-colors",
        "hover:bg-accent",
        isDragging && "opacity-50 shadow-lg"
      )}
      aria-label={`${label} column${description ? `: ${description}` : ""}`}
    >
      <button
        type="button"
        className="cursor-grab touch-none active:cursor-grabbing focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded p-1"
        {...attributes}
        {...listeners}
        aria-label={`Drag to reorder ${label}`}
      >
        <GripVertical className="h-4 w-4 text-muted-foreground" />
      </button>
      <Checkbox
        id={`column-${id}`}
        checked={checked}
        onCheckedChange={() => onToggle(id)}
        aria-label={`Toggle ${label} column visibility`}
      />
      <label
        htmlFor={`column-${id}`}
        className="flex-1 cursor-pointer text-sm select-none"
      >
        {label}
      </label>
    </div>
  );
}

/**
 * Column Selector Component
 *
 * Allows users to show/hide columns and reorder them via drag-and-drop.
 * Column preferences can be persisted using the onColumnsChange callback.
 *
 * Features:
 * - Checkbox to toggle column visibility
 * - Drag handles to reorder columns
 * - "Select All" / "Deselect All" quick actions
 * - "Reset to Default" to restore original configuration
 * - Keyboard accessible (Tab, Enter, Space, Arrow keys for drag-drop)
 * - Screen reader announcements
 *
 * @example
 * ```tsx
 * const columns = [
 *   { id: 'name', label: 'Name', defaultVisible: true },
 *   { id: 'email', label: 'Email', defaultVisible: true },
 *   { id: 'phone', label: 'Phone', defaultVisible: false },
 * ];
 *
 * function MyTable() {
 *   const { selectedColumns, updateColumns } = useColumnPreferences('users', columns);
 *
 *   return (
 *     <ColumnSelector
 *       columns={columns}
 *       selectedColumns={selectedColumns}
 *       onColumnsChange={updateColumns}
 *     />
 *   );
 * }
 * ```
 */
export function ColumnSelector({
  columns,
  selectedColumns,
  onColumnsChange,
  variant = "outline",
  size = "default",
  className,
}: ColumnSelectorProps) {
  // Local state for the column configuration (only committed on Apply)
  const [localColumns, setLocalColumns] = useState<string[]>(selectedColumns);
  const [open, setOpen] = useState(false);

  // Reset local state when dropdown opens
  React.useEffect(() => {
    if (open) {
      setLocalColumns(selectedColumns);
    }
  }, [open, selectedColumns]);

  // Configure drag-and-drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // Require 8px of movement before dragging starts
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  /**
   * Handle drag end event - reorder columns
   */
  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setLocalColumns((items) => {
        const oldIndex = items.indexOf(active.id as string);
        const newIndex = items.indexOf(over.id as string);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  }, []);

  /**
   * Toggle individual column visibility
   */
  const toggleColumn = useCallback((columnId: string) => {
    setLocalColumns((prev) => {
      if (prev.includes(columnId)) {
        // Hide column
        return prev.filter((id) => id !== columnId);
      } else {
        // Show column - add it in the correct position based on original order
        const columnIndex = columns.findIndex((col) => col.id === columnId);
        const newColumns = [...prev];

        // Find the correct insertion position
        let insertIndex = 0;
        for (let i = 0; i < columns.length; i++) {
          if (columns[i].id === columnId) break;
          if (newColumns.includes(columns[i].id)) {
            insertIndex++;
          }
        }

        newColumns.splice(insertIndex, 0, columnId);
        return newColumns;
      }
    });
  }, [columns]);

  /**
   * Reset to default column configuration
   */
  const resetToDefault = useCallback(() => {
    const defaultCols = columns
      .filter((col) => col.defaultVisible)
      .map((col) => col.id);
    setLocalColumns(defaultCols);
  }, [columns]);

  /**
   * Select all columns
   */
  const selectAll = useCallback(() => {
    setLocalColumns(columns.map((col) => col.id));
  }, [columns]);

  /**
   * Deselect all columns
   */
  const deselectAll = useCallback(() => {
    setLocalColumns([]);
  }, []);

  /**
   * Apply changes and close dropdown
   */
  const applyChanges = useCallback(() => {
    onColumnsChange(localColumns);
    setOpen(false);
  }, [localColumns, onColumnsChange]);

  /**
   * Cancel changes and close dropdown
   */
  const cancelChanges = useCallback(() => {
    setLocalColumns(selectedColumns);
    setOpen(false);
  }, [selectedColumns]);

  // Visible columns count for display
  const visibleCount = useMemo(() => localColumns.length, [localColumns]);
  const totalCount = useMemo(() => columns.length, [columns]);

  // Check if current state differs from saved state
  const hasChanges = useMemo(() => {
    if (localColumns.length !== selectedColumns.length) return true;
    return localColumns.some((id, index) => id !== selectedColumns[index]);
  }, [localColumns, selectedColumns]);

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant={variant}
          size={size}
          className={cn("gap-2", className)}
          aria-label={`Column selector: ${visibleCount} of ${totalCount} columns visible`}
        >
          <Columns3 className="h-4 w-4" />
          <span>Columns</span>
          <span className="text-xs text-muted-foreground">
            ({visibleCount}/{totalCount})
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-80"
        align="end"
        onEscapeKeyDown={cancelChanges}
      >
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Select Columns</span>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs"
              onClick={selectAll}
            >
              All
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs"
              onClick={deselectAll}
            >
              None
            </Button>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        <div className="max-h-96 overflow-y-auto p-2">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={localColumns}
              strategy={verticalListSortingStrategy}
            >
              {localColumns.map((columnId) => {
                const column = columns.find((col) => col.id === columnId);
                if (!column) return null;
                return (
                  <SortableItem
                    key={column.id}
                    id={column.id}
                    label={column.label}
                    checked={true}
                    onToggle={toggleColumn}
                    description={column.description}
                  />
                );
              })}
            </SortableContext>
          </DndContext>

          {/* Hidden columns (not in localColumns) */}
          {columns
            .filter((col) => !localColumns.includes(col.id))
            .map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-md px-2 py-2 opacity-60 transition-opacity hover:opacity-100"
              >
                <div className="w-6" /> {/* Spacer for drag handle */}
                <Checkbox
                  id={`column-${column.id}`}
                  checked={false}
                  onCheckedChange={() => toggleColumn(column.id)}
                  aria-label={`Show ${column.label} column`}
                />
                <label
                  htmlFor={`column-${column.id}`}
                  className="flex-1 cursor-pointer text-sm select-none"
                >
                  {column.label}
                </label>
              </div>
            ))}
        </div>

        <DropdownMenuSeparator />

        <div className="flex items-center justify-between gap-2 p-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={resetToDefault}
            className="text-xs"
          >
            Reset to Default
          </Button>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={cancelChanges}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={applyChanges}
              disabled={!hasChanges}
              className="text-xs"
            >
              Apply
            </Button>
          </div>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
