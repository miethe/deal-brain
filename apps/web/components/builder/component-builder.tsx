"use client";

import { useMemo, useState } from "react";
import { ComponentCard, SelectedComponent } from "./component-card";
import {
  ComponentSelectorModal,
  ComponentItem,
} from "./component-selector-modal";
import { useBuilder } from "./builder-provider";
import {
  useCatalogCPUs,
  useCatalogGPUs,
  useCatalogRAMSpecs,
  useCatalogStorageProfiles,
} from "@/hooks/use-catalog";

/**
 * Component type identifiers
 */
type ComponentType =
  | "cpu_id"
  | "gpu_id"
  | "ram_spec_id"
  | "storage_spec_id";

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
 * Note: PSU and Case removed as those catalogs don't exist yet in the backend
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
];

/**
 * Main component builder interface with component selection
 */
export function ComponentBuilder() {
  const { state, dispatch } = useBuilder();
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedType, setSelectedType] = useState<ComponentMetadata | null>(null);

  // Fetch catalog data from API
  const { data: cpus, isLoading: cpusLoading, error: cpusError } = useCatalogCPUs();
  const { data: gpus, isLoading: gpusLoading, error: gpusError } = useCatalogGPUs();
  const { data: ramSpecs, isLoading: ramLoading, error: ramError } = useCatalogRAMSpecs();
  const { data: storageProfiles, isLoading: storageLoading, error: storageError } = useCatalogStorageProfiles();

  /**
   * Transform catalog data to ComponentItem format
   */
  const componentCatalog: Record<string, ComponentItem[]> = useMemo(() => {
    const catalog: Record<string, ComponentItem[]> = {
      cpu_id: [],
      gpu_id: [],
      ram_spec_id: [],
      storage_spec_id: [],
    };

    // Map CPUs
    if (cpus) {
      catalog.cpu_id = cpus.map((cpu) => ({
        id: cpu.id,
        name: cpu.name,
        manufacturer: cpu.manufacturer,
        specs: [
          cpu.cores ? `${cpu.cores} cores` : null,
          cpu.threads ? `${cpu.threads} threads` : null,
          cpu.cpu_mark_multi ? `Multi: ${cpu.cpu_mark_multi.toLocaleString()}` : null,
          cpu.cpu_mark_single ? `Single: ${cpu.cpu_mark_single.toLocaleString()}` : null,
        ]
          .filter(Boolean)
          .join(', '),
        price: undefined, // Price not available in catalog
      }));
    }

    // Map GPUs
    if (gpus) {
      catalog.gpu_id = gpus.map((gpu) => ({
        id: gpu.id,
        name: gpu.name,
        manufacturer: gpu.manufacturer,
        specs: gpu.gpu_mark ? `GPU Mark: ${gpu.gpu_mark.toLocaleString()}` : undefined,
        price: undefined, // Price not available in catalog
      }));
    }

    // Map RAM Specs
    if (ramSpecs) {
      catalog.ram_spec_id = ramSpecs.map((ram) => ({
        id: ram.id,
        name: ram.label || `${ram.total_capacity_gb || '?'}GB ${ram.ddr_generation}${ram.speed_mhz ? `-${ram.speed_mhz}` : ''}`,
        specs: [
          ram.module_count && ram.capacity_per_module_gb ? `${ram.module_count}x${ram.capacity_per_module_gb}GB` : null,
          ram.speed_mhz ? `${ram.speed_mhz}MHz` : null,
        ]
          .filter(Boolean)
          .join(', '),
        price: undefined, // Price not available in catalog
      }));
    }

    // Map Storage Profiles
    if (storageProfiles) {
      catalog.storage_spec_id = storageProfiles.map((storage) => ({
        id: storage.id,
        name: storage.label || `${storage.capacity_gb || '?'}GB ${storage.medium}`,
        specs: [
          storage.interface,
          storage.form_factor,
          storage.performance_tier,
        ]
          .filter(Boolean)
          .join(', '),
        price: undefined, // Price not available in catalog
      }));
    }

    return catalog;
  }, [cpus, gpus, ramSpecs, storageProfiles]);

  /**
   * Get loading state for a component type
   */
  const isComponentLoading = (componentType: ComponentType): boolean => {
    switch (componentType) {
      case 'cpu_id':
        return cpusLoading;
      case 'gpu_id':
        return gpusLoading;
      case 'ram_spec_id':
        return ramLoading;
      case 'storage_spec_id':
        return storageLoading;
      default:
        return false;
    }
  };

  /**
   * Get error state for a component type
   */
  const getComponentError = (componentType: ComponentType): Error | null => {
    switch (componentType) {
      case 'cpu_id':
        return cpusError;
      case 'gpu_id':
        return gpusError;
      case 'ram_spec_id':
        return ramError;
      case 'storage_spec_id':
        return storageError;
      default:
        return null;
    }
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

    // Find component in catalog data
    const componentList = componentCatalog[componentType] || [];
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
      {COMPONENT_TYPES.map((metadata) => {
        const error = getComponentError(metadata.key);

        return (
          <ComponentCard
            key={metadata.key}
            title={metadata.title}
            componentType={metadata.displayName}
            selectedComponent={getSelectedComponent(metadata.key)}
            onSelect={() => openModal(metadata)}
            onRemove={() => handleRemove(metadata.key)}
            required={metadata.required}
            disabled={state.isCalculating}
            error={error ? `Failed to load ${metadata.displayName} catalog: ${error.message}` : undefined}
          />
        );
      })}

      {selectedType && (
        <ComponentSelectorModal
          open={modalOpen}
          onOpenChange={setModalOpen}
          title={`Select ${selectedType.title}`}
          componentType={selectedType.displayName}
          components={componentCatalog[selectedType.key] || []}
          onSelect={handleSelect}
          isLoading={isComponentLoading(selectedType.key)}
        />
      )}
    </div>
  );
}
