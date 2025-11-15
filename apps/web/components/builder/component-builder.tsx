"use client";

import { useState } from "react";
import { ComponentCard, SelectedComponent } from "./component-card";
import {
  ComponentSelectorModal,
  ComponentItem,
} from "./component-selector-modal";
import { useBuilder } from "./builder-provider";

/**
 * Component type identifiers
 */
type ComponentType =
  | "cpu_id"
  | "gpu_id"
  | "ram_spec_id"
  | "storage_spec_id"
  | "psu_spec_id"
  | "case_spec_id";

/**
 * Component metadata for display
 */
interface ComponentMetadata {
  key: ComponentType;
  title: string;
  displayName: string;
  required: boolean;
}

/**
 * Configuration for all component types
 */
const COMPONENT_TYPES: ComponentMetadata[] = [
  { key: "cpu_id", title: "CPU", displayName: "CPU", required: true },
  { key: "gpu_id", title: "GPU", displayName: "GPU", required: false },
  {
    key: "ram_spec_id",
    title: "RAM",
    displayName: "Memory",
    required: false,
  },
  {
    key: "storage_spec_id",
    title: "Storage",
    displayName: "Storage",
    required: false,
  },
  { key: "psu_spec_id", title: "PSU", displayName: "Power Supply", required: false },
  { key: "case_spec_id", title: "Case", displayName: "Case", required: false },
];

/**
 * Main component builder interface with component selection
 */
export function ComponentBuilder() {
  const { state, dispatch } = useBuilder();
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedType, setSelectedType] = useState<ComponentMetadata | null>(null);

  // Mock component data - will be replaced with API calls in Phase 6
  const mockComponents: Record<string, ComponentItem[]> = {
    cpu_id: [
      {
        id: 1,
        name: "Intel Core i5-12400",
        manufacturer: "Intel",
        specs: "6 cores, 12 threads, 2.5 GHz base",
        price: 150,
      },
      {
        id: 2,
        name: "AMD Ryzen 5 5600X",
        manufacturer: "AMD",
        specs: "6 cores, 12 threads, 3.7 GHz base",
        price: 180,
      },
    ],
    gpu_id: [
      {
        id: 1,
        name: "NVIDIA RTX 3060",
        manufacturer: "NVIDIA",
        specs: "12GB GDDR6",
        price: 350,
      },
      {
        id: 2,
        name: "AMD RX 6600",
        manufacturer: "AMD",
        specs: "8GB GDDR6",
        price: 280,
      },
    ],
    ram_spec_id: [
      {
        id: 1,
        name: "16GB DDR4-3200",
        specs: "2x8GB, CL16",
        price: 60,
      },
      {
        id: 2,
        name: "32GB DDR4-3600",
        specs: "2x16GB, CL18",
        price: 110,
      },
    ],
    storage_spec_id: [
      {
        id: 1,
        name: "1TB NVMe SSD",
        specs: "PCIe 3.0, 3500MB/s read",
        price: 80,
      },
      {
        id: 2,
        name: "2TB NVMe SSD",
        specs: "PCIe 4.0, 7000MB/s read",
        price: 160,
      },
    ],
    psu_spec_id: [
      {
        id: 1,
        name: "650W 80+ Gold",
        specs: "Modular, 90% efficiency",
        price: 90,
      },
      {
        id: 2,
        name: "750W 80+ Platinum",
        specs: "Fully modular, 92% efficiency",
        price: 130,
      },
    ],
    case_spec_id: [
      {
        id: 1,
        name: "Mid Tower ATX",
        specs: "Tempered glass, 3 fans included",
        price: 70,
      },
      {
        id: 2,
        name: "Compact Mini-ITX",
        specs: "Small form factor, mesh front",
        price: 100,
      },
    ],
  };

  /**
   * Open modal for component selection
   */
  const openModal = (metadata: ComponentMetadata) => {
    setSelectedType(metadata);
    setModalOpen(true);
  };

  /**
   * Handle component selection from modal
   */
  const handleSelect = (component: ComponentItem) => {
    if (!selectedType) return;

    dispatch({
      type: "SELECT_COMPONENT",
      payload: {
        componentType: selectedType.key,
        id: component.id,
      },
    });
  };

  /**
   * Handle component removal
   */
  const handleRemove = (componentType: ComponentType) => {
    dispatch({
      type: "REMOVE_COMPONENT",
      payload: { componentType },
    });
  };

  /**
   * Get selected component display info
   */
  const getSelectedComponent = (
    componentType: ComponentType
  ): SelectedComponent | null => {
    const componentId = state.components[componentType];
    if (!componentId) return null;

    // Find component in mock data
    const componentList = mockComponents[componentType] || [];
    const component = componentList.find((c) => c.id === componentId);

    if (!component) return null;

    return {
      id: component.id,
      name: component.name,
      price: component.price,
      specs: component.specs,
    };
  };

  return (
    <div className="space-y-4">
      {COMPONENT_TYPES.map((metadata) => (
        <ComponentCard
          key={metadata.key}
          title={metadata.title}
          componentType={metadata.displayName}
          selectedComponent={getSelectedComponent(metadata.key)}
          onSelect={() => openModal(metadata)}
          onRemove={() => handleRemove(metadata.key)}
          required={metadata.required}
          disabled={state.isCalculating}
        />
      ))}

      {selectedType && (
        <ComponentSelectorModal
          open={modalOpen}
          onOpenChange={setModalOpen}
          title={`Select ${selectedType.title}`}
          componentType={selectedType.displayName}
          components={mockComponents[selectedType.key] || []}
          onSelect={handleSelect}
          isLoading={false}
        />
      )}
    </div>
  );
}
