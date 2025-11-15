/**
 * Deal Builder components - Phase 5: Frontend Component Structure
 *
 * Component hierarchy:
 * - BuilderProvider: React Context for state management
 * - ComponentBuilder: Main layout with component cards
 * - ComponentCard: Individual component selection cards
 * - ComponentSelectorModal: Modal for searching/selecting components
 */

export { BuilderProvider, useBuilder } from "./builder-provider";
export type { BuilderState, BuilderAction, BuildComponents } from "./builder-provider";

export { ComponentBuilder } from "./component-builder";

export { ComponentCard } from "./component-card";
export type { ComponentCardProps, SelectedComponent } from "./component-card";

export { ComponentSelectorModal } from "./component-selector-modal";
export type {
  ComponentSelectorModalProps,
  ComponentItem,
} from "./component-selector-modal";
