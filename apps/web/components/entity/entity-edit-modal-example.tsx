/**
 * Example Usage of EntityEditModal Component
 *
 * This file demonstrates how to integrate the EntityEditModal into detail views.
 * It is NOT used in production - it's a reference for EDIT-003 through EDIT-006.
 */

"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { EntityEditModal } from "./entity-edit-modal";
import { cpuEditSchema, type CPUEditFormData } from "@/lib/schemas/entity-schemas";
import { useToast } from "@/hooks/use-toast";
import { apiFetch } from "@/lib/utils";
import { Button } from "@/components/ui/button";

// Example: CPU Detail Layout Integration
interface CPUData {
  id: number;
  name: string;
  manufacturer: string | null;
  socket: string | null;
  cores: number | null;
  threads: number | null;
  tdp_w: number | null;
  igpu_model: string | null;
  cpu_mark_multi: number | null;
  cpu_mark_single: number | null;
  igpu_mark: number | null;
  release_year: number | null;
  notes: string | null;
  passmark_slug: string | null;
  passmark_category: string | null;
  passmark_id: string | null;
  attributes: Record<string, any>;
}

export function CPUDetailWithEditExample({ cpu }: { cpu: CPUData }) {
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Create mutation for updating CPU
  const updateMutation = useMutation({
    mutationFn: async (data: CPUEditFormData) => {
      // PATCH endpoint call
      return apiFetch(`/v1/catalog/cpus/${cpu.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      // Invalidate queries to refetch updated data
      queryClient.invalidateQueries({ queryKey: ["cpu", cpu.id] });
      queryClient.invalidateQueries({ queryKey: ["cpus"] });

      // Show success toast
      toast({
        title: "Success",
        description: "CPU updated successfully",
      });
    },
    onError: (error: unknown) => {
      // Show error toast
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update CPU",
        variant: "destructive",
      });
    },
  });

  const handleSubmit = async (data: CPUEditFormData) => {
    await updateMutation.mutateAsync(data);
  };

  return (
    <div>
      {/* Header with Edit button */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{cpu.name}</h1>
        <Button onClick={() => setIsEditModalOpen(true)}>
          Edit CPU
        </Button>
      </div>

      {/* CPU Details */}
      <div className="space-y-4">
        <p>Manufacturer: {cpu.manufacturer || "N/A"}</p>
        <p>Cores: {cpu.cores || "N/A"}</p>
        <p>Threads: {cpu.threads || "N/A"}</p>
        {/* ... more fields ... */}
      </div>

      {/* Edit Modal */}
      <EntityEditModal
        entityType="cpu"
        entityId={cpu.id}
        initialValues={{
          name: cpu.name,
          manufacturer: cpu.manufacturer,
          socket: cpu.socket,
          cores: cpu.cores,
          threads: cpu.threads,
          tdp_w: cpu.tdp_w,
          igpu_model: cpu.igpu_model,
          cpu_mark_multi: cpu.cpu_mark_multi,
          cpu_mark_single: cpu.cpu_mark_single,
          igpu_mark: cpu.igpu_mark,
          release_year: cpu.release_year,
          notes: cpu.notes,
          passmark_slug: cpu.passmark_slug,
          passmark_category: cpu.passmark_category,
          passmark_id: cpu.passmark_id,
          attributes: cpu.attributes,
        }}
        schema={cpuEditSchema}
        onSubmit={handleSubmit}
        onClose={() => setIsEditModalOpen(false)}
        isOpen={isEditModalOpen}
      />
    </div>
  );
}

/**
 * Usage Notes for EDIT-003 through EDIT-006:
 *
 * 1. Import the EntityEditModal and corresponding schema
 * 2. Create a state variable for modal open/close (useState)
 * 3. Create a mutation using useMutation from React Query
 * 4. The mutation should:
 *    - Call PATCH /v1/catalog/{entity}/{id}
 *    - Invalidate relevant queries on success
 *    - Show toast notifications
 * 5. Pass entity data as initialValues to the modal
 * 6. The modal will handle form validation and submission
 *
 * Repeat this pattern for:
 * - GPU (gpuEditSchema)
 * - RamSpec (ramSpecEditSchema)
 * - StorageProfile (storageProfileEditSchema)
 */
