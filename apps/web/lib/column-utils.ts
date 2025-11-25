import type { ColumnDef } from "@tanstack/react-table";

/**
 * Apply column preferences to a columns array
 *
 * Filters and reorders columns based on selected column IDs.
 * This allows dynamic column visibility and ordering without
 * modifying the core table implementation.
 *
 * @param allColumns - All available column definitions
 * @param selectedColumnIds - IDs of selected columns in desired order
 * @returns Filtered and reordered columns array
 *
 * @example
 * ```tsx
 * const allColumns: ColumnDef<User>[] = [...];
 * const selectedColumnIds = ['name', 'email']; // Only show these, in this order
 *
 * const visibleColumns = applyColumnPreferences(allColumns, selectedColumnIds);
 * // Result: Only name and email columns, in that order
 * ```
 */
export function applyColumnPreferences<TData>(
  allColumns: ColumnDef<TData>[],
  selectedColumnIds: string[]
): ColumnDef<TData>[] {
  // Create a map for efficient column lookup
  const columnMap = new Map<string, ColumnDef<TData>>();
  allColumns.forEach((col) => {
    const id = (col as any).id || (col as any).accessorKey;
    if (id) {
      columnMap.set(String(id), col);
    }
  });

  // Filter and reorder based on selectedColumnIds
  const orderedColumns: ColumnDef<TData>[] = [];

  selectedColumnIds.forEach((id) => {
    const column = columnMap.get(id);
    if (column) {
      orderedColumns.push(column);
    }
  });

  return orderedColumns;
}

/**
 * Extract column IDs from a columns array
 *
 * @param columns - Array of column definitions
 * @returns Array of column IDs
 */
export function extractColumnIds<TData>(
  columns: ColumnDef<TData>[]
): string[] {
  return columns
    .map((col) => {
      const id = (col as any).id || (col as any).accessorKey;
      return id ? String(id) : null;
    })
    .filter((id): id is string => id !== null);
}
