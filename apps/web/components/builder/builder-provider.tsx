"use client";

import React, { createContext, useContext, useReducer, ReactNode } from "react";
import type { ValuationBreakdown, BuildMetrics } from "@/lib/api/builder";

/**
 * Component selection state
 */
export interface BuildComponents {
  cpu_id: number | null;
  gpu_id: number | null;
  ram_spec_id: number | null;
  storage_spec_id: number | null;
  psu_spec_id: number | null;
  case_spec_id: number | null;
}

/**
 * Global builder state
 */
export interface BuilderState {
  components: BuildComponents;
  valuation: ValuationBreakdown | null;
  metrics: BuildMetrics | null;
  isCalculating: boolean;
  lastCalculated: Date | null;
  error: string | null;
}

/**
 * Actions for state updates
 */
export type BuilderAction =
  | {
      type: "SELECT_COMPONENT";
      payload: { componentType: keyof BuildComponents; id: number };
    }
  | { type: "REMOVE_COMPONENT"; payload: { componentType: keyof BuildComponents } }
  | {
      type: "SET_CALCULATIONS";
      payload: { valuation: ValuationBreakdown; metrics: BuildMetrics };
    }
  | { type: "SET_CALCULATING"; payload: boolean }
  | { type: "SET_ERROR"; payload: string | null }
  | { type: "RESET_BUILD" };

/**
 * Initial state for new builds
 */
const initialState: BuilderState = {
  components: {
    cpu_id: null,
    gpu_id: null,
    ram_spec_id: null,
    storage_spec_id: null,
    psu_spec_id: null,
    case_spec_id: null,
  },
  valuation: null,
  metrics: null,
  isCalculating: false,
  lastCalculated: null,
  error: null,
};

/**
 * Reducer for builder state management
 */
function builderReducer(state: BuilderState, action: BuilderAction): BuilderState {
  switch (action.type) {
    case "SELECT_COMPONENT":
      return {
        ...state,
        components: {
          ...state.components,
          [action.payload.componentType]: action.payload.id,
        },
        // Clear calculations when components change
        valuation: null,
        metrics: null,
        lastCalculated: null,
      };

    case "REMOVE_COMPONENT":
      return {
        ...state,
        components: {
          ...state.components,
          [action.payload.componentType]: null,
        },
        // Clear calculations when components change
        valuation: null,
        metrics: null,
        lastCalculated: null,
      };

    case "SET_CALCULATIONS":
      return {
        ...state,
        valuation: action.payload.valuation,
        metrics: action.payload.metrics,
        isCalculating: false,
        lastCalculated: new Date(),
        error: null,
      };

    case "SET_CALCULATING":
      return {
        ...state,
        isCalculating: action.payload,
        error: action.payload ? null : state.error,
      };

    case "SET_ERROR":
      return {
        ...state,
        error: action.payload,
        isCalculating: false,
      };

    case "RESET_BUILD":
      return initialState;

    default:
      return state;
  }
}

/**
 * Context for builder state
 */
const BuilderContext = createContext<
  | {
      state: BuilderState;
      dispatch: React.Dispatch<BuilderAction>;
    }
  | undefined
>(undefined);

/**
 * Provider component for builder state
 */
export function BuilderProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(builderReducer, initialState);

  return (
    <BuilderContext.Provider value={{ state, dispatch }}>
      {children}
    </BuilderContext.Provider>
  );
}

/**
 * Hook to access builder context
 */
export function useBuilder() {
  const context = useContext(BuilderContext);
  if (!context) {
    throw new Error("useBuilder must be used within BuilderProvider");
  }
  return context;
}
