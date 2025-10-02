"use client";

import { useEffect } from "react";

/**
 * Hook to warn users about unsaved changes when they attempt to leave the page
 * @param isDirty - Whether there are unsaved changes
 * @param message - Optional custom warning message
 */
export function useUnsavedChanges(isDirty: boolean, message?: string) {
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        // Chrome requires returnValue to be set
        e.returnValue = message || "You have unsaved changes. Are you sure you want to leave?";
        return e.returnValue;
      }
    };

    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty, message]);
}
