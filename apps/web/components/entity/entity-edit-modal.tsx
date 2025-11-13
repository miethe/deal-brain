"use client";

import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { z } from "zod";
import { ModalShell } from "@/components/ui/modal-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  type EntityType,
  type EntityEditFormData,
  ddrGenerationEnum,
  storageMediumEnum,
  storageInterfaceEnum,
  storageFormFactorEnum,
  performanceTierEnum,
} from "@/lib/schemas/entity-schemas";

// ============================================================================
// Types
// ============================================================================

interface EntityEditModalProps<T extends z.ZodType> {
  entityType: EntityType;
  entityId: number;
  initialValues: z.infer<T>;
  schema: T;
  onSubmit: (data: z.infer<T>) => Promise<void>;
  onClose: () => void;
  isOpen: boolean;
}

// ============================================================================
// Field Components
// ============================================================================

interface FieldErrorProps {
  error?: { message?: string };
}

function FieldError({ error }: FieldErrorProps) {
  if (!error?.message) return null;
  return (
    <p className="text-sm text-destructive mt-1" role="alert">
      {error.message}
    </p>
  );
}

interface FormFieldProps {
  label: string;
  htmlFor: string;
  required?: boolean;
  error?: { message?: string };
  helpText?: string;
  children: React.ReactNode;
}

function FormField({ label, htmlFor, required, error, helpText, children }: FormFieldProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={htmlFor}>
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      {children}
      {error && <FieldError error={error} />}
      {helpText && !error && (
        <p className="text-xs text-muted-foreground">{helpText}</p>
      )}
    </div>
  );
}

// ============================================================================
// Entity Form Renderers
// ============================================================================

interface EntityFormFieldsProps {
  entityType: EntityType;
  register: any;
  errors: any;
  control: any;
}

function CPUFormFields({ register, errors, control }: Omit<EntityFormFieldsProps, 'entityType'>) {
  return (
    <div className="space-y-4">
      <FormField label="Name" htmlFor="name" required error={errors.name}>
        <Input
          id="name"
          {...register("name")}
          aria-invalid={!!errors.name}
          className={cn(errors.name && "border-destructive")}
        />
      </FormField>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="Manufacturer" htmlFor="manufacturer" error={errors.manufacturer}>
          <Input
            id="manufacturer"
            {...register("manufacturer")}
            aria-invalid={!!errors.manufacturer}
            className={cn(errors.manufacturer && "border-destructive")}
          />
        </FormField>

        <FormField label="Socket" htmlFor="socket" error={errors.socket}>
          <Input
            id="socket"
            {...register("socket")}
            placeholder="e.g., LGA1700, AM5"
            aria-invalid={!!errors.socket}
            className={cn(errors.socket && "border-destructive")}
          />
        </FormField>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="Cores" htmlFor="cores" error={errors.cores}>
          <Input
            id="cores"
            type="number"
            {...register("cores", { valueAsNumber: true })}
            placeholder="e.g., 8"
            aria-invalid={!!errors.cores}
            className={cn(errors.cores && "border-destructive")}
          />
        </FormField>

        <FormField label="Threads" htmlFor="threads" error={errors.threads}>
          <Input
            id="threads"
            type="number"
            {...register("threads", { valueAsNumber: true })}
            placeholder="e.g., 16"
            aria-invalid={!!errors.threads}
            className={cn(errors.threads && "border-destructive")}
          />
        </FormField>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="TDP (Watts)" htmlFor="tdp_w" error={errors.tdp_w}>
          <Input
            id="tdp_w"
            type="number"
            {...register("tdp_w", { valueAsNumber: true })}
            placeholder="e.g., 65"
            aria-invalid={!!errors.tdp_w}
            className={cn(errors.tdp_w && "border-destructive")}
          />
        </FormField>

        <FormField label="Release Year" htmlFor="release_year" error={errors.release_year}>
          <Input
            id="release_year"
            type="number"
            {...register("release_year", { valueAsNumber: true })}
            placeholder="e.g., 2023"
            aria-invalid={!!errors.release_year}
            className={cn(errors.release_year && "border-destructive")}
          />
        </FormField>
      </div>

      <FormField label="iGPU Model" htmlFor="igpu_model" error={errors.igpu_model}>
        <Input
          id="igpu_model"
          {...register("igpu_model")}
          placeholder="e.g., Intel UHD Graphics 770"
          aria-invalid={!!errors.igpu_model}
          className={cn(errors.igpu_model && "border-destructive")}
        />
      </FormField>

      <div className="grid grid-cols-3 gap-4">
        <FormField label="CPU Mark (Multi)" htmlFor="cpu_mark_multi" error={errors.cpu_mark_multi}>
          <Input
            id="cpu_mark_multi"
            type="number"
            {...register("cpu_mark_multi", { valueAsNumber: true })}
            placeholder="e.g., 25000"
            aria-invalid={!!errors.cpu_mark_multi}
            className={cn(errors.cpu_mark_multi && "border-destructive")}
          />
        </FormField>

        <FormField label="CPU Mark (Single)" htmlFor="cpu_mark_single" error={errors.cpu_mark_single}>
          <Input
            id="cpu_mark_single"
            type="number"
            {...register("cpu_mark_single", { valueAsNumber: true })}
            placeholder="e.g., 3500"
            aria-invalid={!!errors.cpu_mark_single}
            className={cn(errors.cpu_mark_single && "border-destructive")}
          />
        </FormField>

        <FormField label="iGPU Mark" htmlFor="igpu_mark" error={errors.igpu_mark}>
          <Input
            id="igpu_mark"
            type="number"
            {...register("igpu_mark", { valueAsNumber: true })}
            placeholder="e.g., 1500"
            aria-invalid={!!errors.igpu_mark}
            className={cn(errors.igpu_mark && "border-destructive")}
          />
        </FormField>
      </div>

      <FormField label="Notes" htmlFor="notes" error={errors.notes}>
        <Textarea
          id="notes"
          {...register("notes")}
          placeholder="Additional notes about this CPU..."
          rows={3}
          aria-invalid={!!errors.notes}
          className={cn(errors.notes && "border-destructive")}
        />
      </FormField>
    </div>
  );
}

function GPUFormFields({ register, errors }: Omit<EntityFormFieldsProps, 'entityType' | 'control'>) {
  return (
    <div className="space-y-4">
      <FormField label="Name" htmlFor="name" required error={errors.name}>
        <Input
          id="name"
          {...register("name")}
          aria-invalid={!!errors.name}
          className={cn(errors.name && "border-destructive")}
        />
      </FormField>

      <FormField label="Manufacturer" htmlFor="manufacturer" error={errors.manufacturer}>
        <Input
          id="manufacturer"
          {...register("manufacturer")}
          placeholder="e.g., NVIDIA, AMD, Intel"
          aria-invalid={!!errors.manufacturer}
          className={cn(errors.manufacturer && "border-destructive")}
        />
      </FormField>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="GPU Mark" htmlFor="gpu_mark" error={errors.gpu_mark}>
          <Input
            id="gpu_mark"
            type="number"
            {...register("gpu_mark", { valueAsNumber: true })}
            placeholder="e.g., 15000"
            aria-invalid={!!errors.gpu_mark}
            className={cn(errors.gpu_mark && "border-destructive")}
          />
        </FormField>

        <FormField label="Metal Score" htmlFor="metal_score" error={errors.metal_score}>
          <Input
            id="metal_score"
            type="number"
            {...register("metal_score", { valueAsNumber: true })}
            placeholder="e.g., 75000"
            aria-invalid={!!errors.metal_score}
            className={cn(errors.metal_score && "border-destructive")}
          />
        </FormField>
      </div>

      <FormField label="Notes" htmlFor="notes" error={errors.notes}>
        <Textarea
          id="notes"
          {...register("notes")}
          placeholder="Additional notes about this GPU..."
          rows={3}
          aria-invalid={!!errors.notes}
          className={cn(errors.notes && "border-destructive")}
        />
      </FormField>
    </div>
  );
}

function RamSpecFormFields({ register, errors, control }: Omit<EntityFormFieldsProps, 'entityType'>) {
  return (
    <div className="space-y-4">
      <FormField label="Label" htmlFor="label" required error={errors.label}>
        <Input
          id="label"
          {...register("label")}
          placeholder="e.g., 32GB DDR5-4800"
          aria-invalid={!!errors.label}
          className={cn(errors.label && "border-destructive")}
        />
      </FormField>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="DDR Generation" htmlFor="ddr_generation" error={errors.ddr_generation}>
          <Controller
            name="ddr_generation"
            control={control}
            render={({ field }) => (
              <Select
                onValueChange={field.onChange}
                defaultValue={field.value}
              >
                <SelectTrigger id="ddr_generation" aria-label="DDR Generation">
                  <SelectValue placeholder="Select generation" />
                </SelectTrigger>
                <SelectContent>
                  {ddrGenerationEnum.options.map((gen) => (
                    <SelectItem key={gen} value={gen}>
                      {gen.toUpperCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>

        <FormField label="Speed (MHz)" htmlFor="speed_mhz" error={errors.speed_mhz}>
          <Input
            id="speed_mhz"
            type="number"
            {...register("speed_mhz", { valueAsNumber: true })}
            placeholder="e.g., 4800"
            aria-invalid={!!errors.speed_mhz}
            className={cn(errors.speed_mhz && "border-destructive")}
          />
        </FormField>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="Module Count" htmlFor="module_count" error={errors.module_count}>
          <Input
            id="module_count"
            type="number"
            {...register("module_count", { valueAsNumber: true })}
            placeholder="e.g., 2"
            aria-invalid={!!errors.module_count}
            className={cn(errors.module_count && "border-destructive")}
          />
        </FormField>

        <FormField label="Capacity per Module (GB)" htmlFor="capacity_per_module_gb" error={errors.capacity_per_module_gb}>
          <Input
            id="capacity_per_module_gb"
            type="number"
            {...register("capacity_per_module_gb", { valueAsNumber: true })}
            placeholder="e.g., 16"
            aria-invalid={!!errors.capacity_per_module_gb}
            className={cn(errors.capacity_per_module_gb && "border-destructive")}
          />
        </FormField>
      </div>

      <FormField label="Total Capacity (GB)" htmlFor="total_capacity_gb" error={errors.total_capacity_gb}>
        <Input
          id="total_capacity_gb"
          type="number"
          {...register("total_capacity_gb", { valueAsNumber: true })}
          placeholder="e.g., 32"
          aria-invalid={!!errors.total_capacity_gb}
          className={cn(errors.total_capacity_gb && "border-destructive")}
        />
      </FormField>

      <FormField label="Notes" htmlFor="notes" error={errors.notes}>
        <Textarea
          id="notes"
          {...register("notes")}
          placeholder="Additional notes about this RAM spec..."
          rows={3}
          aria-invalid={!!errors.notes}
          className={cn(errors.notes && "border-destructive")}
        />
      </FormField>
    </div>
  );
}

function StorageProfileFormFields({ register, errors, control }: Omit<EntityFormFieldsProps, 'entityType'>) {
  return (
    <div className="space-y-4">
      <FormField label="Label" htmlFor="label" required error={errors.label}>
        <Input
          id="label"
          {...register("label")}
          placeholder="e.g., 1TB NVMe SSD"
          aria-invalid={!!errors.label}
          className={cn(errors.label && "border-destructive")}
        />
      </FormField>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="Medium" htmlFor="medium" error={errors.medium}>
          <Controller
            name="medium"
            control={control}
            render={({ field }) => (
              <Select
                onValueChange={field.onChange}
                defaultValue={field.value}
              >
                <SelectTrigger id="medium" aria-label="Storage Medium">
                  <SelectValue placeholder="Select medium" />
                </SelectTrigger>
                <SelectContent>
                  {storageMediumEnum.options.map((medium) => (
                    <SelectItem key={medium} value={medium}>
                      {medium.toUpperCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>

        <FormField label="Interface" htmlFor="interface" error={errors.interface}>
          <Controller
            name="interface"
            control={control}
            render={({ field }) => (
              <Select
                onValueChange={field.onChange}
                defaultValue={field.value || undefined}
              >
                <SelectTrigger id="interface" aria-label="Storage Interface">
                  <SelectValue placeholder="Select interface" />
                </SelectTrigger>
                <SelectContent>
                  {storageInterfaceEnum.options.map((iface) => (
                    <SelectItem key={iface} value={iface}>
                      {iface.toUpperCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="Form Factor" htmlFor="form_factor" error={errors.form_factor}>
          <Controller
            name="form_factor"
            control={control}
            render={({ field }) => (
              <Select
                onValueChange={field.onChange}
                defaultValue={field.value || undefined}
              >
                <SelectTrigger id="form_factor" aria-label="Form Factor">
                  <SelectValue placeholder="Select form factor" />
                </SelectTrigger>
                <SelectContent>
                  {storageFormFactorEnum.options.map((ff) => (
                    <SelectItem key={ff} value={ff}>
                      {ff.toUpperCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>

        <FormField label="Capacity (GB)" htmlFor="capacity_gb" error={errors.capacity_gb}>
          <Input
            id="capacity_gb"
            type="number"
            {...register("capacity_gb", { valueAsNumber: true })}
            placeholder="e.g., 1000"
            aria-invalid={!!errors.capacity_gb}
            className={cn(errors.capacity_gb && "border-destructive")}
          />
        </FormField>
      </div>

      <FormField label="Performance Tier" htmlFor="performance_tier" error={errors.performance_tier}>
        <Controller
          name="performance_tier"
          control={control}
          render={({ field }) => (
            <Select
              onValueChange={field.onChange}
              defaultValue={field.value || undefined}
            >
              <SelectTrigger id="performance_tier" aria-label="Performance Tier">
                <SelectValue placeholder="Select tier" />
              </SelectTrigger>
              <SelectContent>
                {performanceTierEnum.options.map((tier) => (
                  <SelectItem key={tier} value={tier}>
                    {tier.charAt(0).toUpperCase() + tier.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </FormField>

      <FormField label="Notes" htmlFor="notes" error={errors.notes}>
        <Textarea
          id="notes"
          {...register("notes")}
          placeholder="Additional notes about this storage profile..."
          rows={3}
          aria-invalid={!!errors.notes}
          className={cn(errors.notes && "border-destructive")}
        />
      </FormField>
    </div>
  );
}

function EntityFormFields(props: EntityFormFieldsProps) {
  switch (props.entityType) {
    case "cpu":
      return <CPUFormFields {...props} />;
    case "gpu":
      return <GPUFormFields {...props} />;
    case "ram-spec":
      return <RamSpecFormFields {...props} />;
    case "storage-profile":
      return <StorageProfileFormFields {...props} />;
    case "ports-profile":
    case "profile":
      // TODO: Implement in future phases
      return <div>Form not yet implemented for {props.entityType}</div>;
    default:
      return <div>Unknown entity type</div>;
  }
}

// ============================================================================
// Main Component
// ============================================================================

const entityTypeLabels: Record<EntityType, string> = {
  cpu: "CPU",
  gpu: "GPU",
  "ram-spec": "RAM Specification",
  "storage-profile": "Storage Profile",
  "ports-profile": "Ports Profile",
  profile: "Profile",
};

export function EntityEditModal<T extends z.ZodType>({
  entityType,
  entityId,
  initialValues,
  schema,
  onSubmit,
  onClose,
  isOpen,
}: EntityEditModalProps<T>) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isValid },
  } = useForm<z.infer<T>>({
    resolver: zodResolver(schema),
    defaultValues: initialValues,
    mode: "onChange", // Validate on change for better UX
  });

  const handleFormSubmit = async (data: z.infer<T>) => {
    setIsSubmitting(true);
    try {
      await onSubmit(data);
      onClose();
    } catch (error) {
      console.error("Form submission error:", error);
      // Error handling will be done by the parent component (via toast)
    } finally {
      setIsSubmitting(false);
    }
  };

  const footer = (
    <>
      <Button
        type="button"
        variant="outline"
        onClick={onClose}
        disabled={isSubmitting}
      >
        Cancel
      </Button>
      <Button
        type="submit"
        onClick={handleSubmit(handleFormSubmit)}
        disabled={!isValid || isSubmitting}
      >
        {isSubmitting ? "Saving..." : "Save Changes"}
      </Button>
    </>
  );

  return (
    <ModalShell
      open={isOpen}
      onOpenChange={(open) => {
        if (!open && !isSubmitting) {
          onClose();
        }
      }}
      title={`Edit ${entityTypeLabels[entityType]}`}
      description={`Update the details for this ${entityTypeLabels[entityType].toLowerCase()}.`}
      footer={footer}
      size="lg"
      preventClose={isSubmitting}
    >
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
        <EntityFormFields
          entityType={entityType}
          register={register}
          errors={errors}
          control={control}
        />
      </form>
    </ModalShell>
  );
}
