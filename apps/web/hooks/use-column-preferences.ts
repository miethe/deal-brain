"use client";

import { useState, useEffect, useCallback } from "react";
import type { ColumnDefinition } from "@/components/ui/column-selector";

/**
 * Column order configuration stored in localStorage
 */
interface ColumnPreferences {
  /** Ordered list of column IDs (only visible columns) */
  columnOrder: string[];
  /** Version for future migration support */
  version: number;
}

const PREFERENCES_VERSION = 1;

/**
 * Hook for managing column visibility and order preferences with localStorage persistence
 *
 * Features:
 * - Persists column selection and order to localStorage
 * - Scoped by entity type (listings, cpus, gpus, etc.)
 * - Loads saved preferences on mount
 * - Provides reset function to restore defaults
 * - Handles versioning for future migrations
 *
 * @param entityType - Entity type identifier (e.g., 'listings', 'cpus', 'gpus')
 * @param columns - All available column definitions
 * @returns Column preferences state and update functions
 *
 * @example
 * ```tsx
 * const columns: ColumnDefinition[] = [
 *   { id: 'name', label: 'Name', defaultVisible: true },
 *   { id: 'email', label: 'Email', defaultVisible: true },
 *   { id: 'phone', label: 'Phone', defaultVisible: false },
 * ];
 *
 * function MyTable() {
 *   const { selectedColumns, updateColumns, resetToDefault } = useColumnPreferences('users', columns);
 *
 *   return (
 *     <div>
 *       <ColumnSelector
 *         columns={columns}
 *         selectedColumns={selectedColumns}
 *         onColumnsChange={updateColumns}
 *       />
 *       <DataTable columns={allColumns} visibleColumnIds={selectedColumns} />
 *     </div>
 *   );
 * }
 * ```
 */
export function useColumnPreferences(
  entityType: string,
  columns: ColumnDefinition[]
) {
  const storageKey = `column-preferences-${entityType}`;

  // Get default columns (those marked as defaultVisible)
  const getDefaultColumns = useCallback(() => {
    return columns
      .filter((col) => col.defaultVisible)
      .map((col) => col.id);
  }, [columns]);

  // Initialize state with default columns
  const [selectedColumns, setSelectedColumns] = useState<string[]>(() => getDefaultColumns());
  const [isLoaded, setIsLoaded] = useState(false);

  /**
   * Load preferences from localStorage on mount
   */
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (isLoaded) return;

    try {
      const stored = localStorage.getItem(storageKey);

      if (!stored) {
        // No saved preferences, use defaults
        setSelectedColumns(getDefaultColumns());
        setIsLoaded(true);
        return;
      }

      const parsed: ColumnPreferences = JSON.parse(stored);

      // Version check for future migrations
      if (parsed.version !== PREFERENCES_VERSION) {
        console.warn(
          `Column preferences version mismatch for ${entityType}. Expected ${PREFERENCES_VERSION}, got ${parsed.version}. Using defaults.`
        );
        setSelectedColumns(getDefaultColumns());
        setIsLoaded(true);
        return;
      }

      // Validate that all saved column IDs still exist
      const validColumnIds = new Set(columns.map((col) => col.id));
      const validatedOrder = parsed.columnOrder.filter((id) =>
        validColumnIds.has(id)
      );

      // Check if any new columns were added (not in saved preferences)
      const savedColumnIds = new Set(validatedOrder);
      const newColumns = columns
        .filter((col) => !savedColumnIds.has(col.id) && col.defaultVisible)
        .map((col) => col.id);

      // Merge new default-visible columns into the order
      const mergedOrder = [...validatedOrder, ...newColumns];

      if (mergedOrder.length > 0) {
        setSelectedColumns(mergedOrder);
      } else {
        // Fallback to defaults if validation resulted in empty array
        setSelectedColumns(getDefaultColumns());
      }

      setIsLoaded(true);
    } catch (error) {
      console.error(`Failed to load column preferences for ${entityType}:`, error);
      setSelectedColumns(getDefaultColumns());
      setIsLoaded(true);
    }
  }, [entityType, storageKey, columns, getDefaultColumns, isLoaded]);

  /**
   * Update column preferences and save to localStorage
   */
  const updateColumns = useCallback(
    (columnIds: string[]) => {
      // Validate column IDs
      const validColumnIds = new Set(columns.map((col) => col.id));
      const validatedIds = columnIds.filter((id) => validColumnIds.has(id));

      setSelectedColumns(validatedIds);

      // Save to localStorage
      if (typeof window === "undefined") return;

      try {
        const preferences: ColumnPreferences = {
          columnOrder: validatedIds,
          version: PREFERENCES_VERSION,
        };
        localStorage.setItem(storageKey, JSON.stringify(preferences));
      } catch (error) {
        console.error(`Failed to save column preferences for ${entityType}:`, error);
      }
    },
    [entityType, storageKey, columns]
  );

  /**
   * Reset to default column configuration
   */
  const resetToDefault = useCallback(() => {
    const defaultCols = getDefaultColumns();
    setSelectedColumns(defaultCols);

    // Clear localStorage
    if (typeof window === "undefined") return;

    try {
      localStorage.removeItem(storageKey);
    } catch (error) {
      console.error(`Failed to clear column preferences for ${entityType}:`, error);
    }
  }, [entityType, storageKey, getDefaultColumns]);

  /**
   * Get column visibility state for TanStack Table
   * Returns an object mapping column IDs to boolean visibility
   */
  const getColumnVisibility = useCallback(() => {
    const visibility: Record<string, boolean> = {};
    columns.forEach((col) => {
      visibility[col.id] = selectedColumns.includes(col.id);
    });
    return visibility;
  }, [columns, selectedColumns]);

  return {
    /** Currently selected/visible columns in order */
    selectedColumns,
    /** Update column selection and order */
    updateColumns,
    /** Reset to default configuration */
    resetToDefault,
    /** Get column visibility object for TanStack Table */
    getColumnVisibility,
    /** Whether preferences have been loaded from localStorage */
    isLoaded,
  };
}
