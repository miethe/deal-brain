"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDebounce } from "use-debounce";
import { Check, ChevronsUpDown, Loader2, Plus, X } from "lucide-react";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "cmdk";

import { apiFetch } from "../../lib/utils";
import { cn } from "../../lib/utils";
import { RAM_GENERATION_OPTIONS, getRamGenerationLabel } from "../../lib/component-catalog";
import { track } from "../../lib/analytics";
import { RamSpecRecord } from "../../types/listings";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";

interface RamSpecSelectorProps {
  value: RamSpecRecord | null | undefined;
  onChange: (spec: RamSpecRecord | null) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

interface RamSpecCreateInput {
  label?: string;
  ddr_generation: string;
  speed_mhz?: number | null;
  module_count?: number | null;
  capacity_per_module_gb?: number | null;
  total_capacity_gb: number;
}

function formatRamSpecLabel(spec: RamSpecRecord) {
  if (spec.label) return spec.label;
  const parts: string[] = [];
  if (spec.ddr_generation) {
    parts.push(getRamGenerationLabel(spec.ddr_generation));
  }
  if (spec.speed_mhz) {
    parts.push(`${spec.speed_mhz}MHz`);
  }
  if (spec.total_capacity_gb) {
    if (spec.module_count && spec.capacity_per_module_gb) {
      parts.push(`${spec.total_capacity_gb}GB (${spec.module_count}x${spec.capacity_per_module_gb}GB)`);
    } else {
      parts.push(`${spec.total_capacity_gb}GB`);
    }
  }
  return parts.join(" ");
}

function formatRamSpecMetadata(spec: RamSpecRecord) {
  const items: string[] = [];
  if (spec.module_count && spec.capacity_per_module_gb) {
    items.push(`${spec.module_count} modules`);
  }
  if (spec.speed_mhz) {
    items.push(`${spec.speed_mhz}MHz`);
  }
  return items.join(" • ");
}

async function fetchRamSpecs(search: string) {
  const params = new URLSearchParams();
  params.set("limit", "30");
  if (search) {
    params.set("search", search);
  }
  return apiFetch<RamSpecRecord[]>(`/v1/catalog/ram-specs?${params.toString()}`);
}

export function RamSpecSelector({
  value,
  onChange,
  disabled = false,
  placeholder = "Select RAM spec",
  className,
}: RamSpecSelectorProps) {
  const [open, setOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 250);
  const queryClient = useQueryClient();

  const { data: specs = [], isFetching } = useQuery({
    queryKey: ["catalog", "ram-specs", debouncedSearch],
    queryFn: () => fetchRamSpecs(debouncedSearch),
    staleTime: 60 * 1000,
  });

  const createMutation = useMutation({
    mutationFn: async (input: RamSpecCreateInput) => {
      return apiFetch<RamSpecRecord>("/v1/catalog/ram-specs", {
        method: "POST",
        body: JSON.stringify(input),
      });
    },
    onSuccess: (spec) => {
      queryClient.invalidateQueries({ queryKey: ["catalog", "ram-specs"] });
      onChange(spec);
      track("ram_spec.create", {
        id: spec.id,
        total_capacity_gb: spec.total_capacity_gb,
        ddr_generation: spec.ddr_generation,
      });
      setOpen(false);
    },
  });

  const options = useMemo(() => {
    if (!value) return specs;
    return specs.some((spec) => spec.id === value.id) ? specs : [value, ...specs];
  }, [specs, value]);
  const selectedLabel = value ? formatRamSpecLabel(value) : placeholder;

  const handleSelect = (specId: number) => {
    const match = options.find((spec) => spec.id === specId);
    if (match) {
      onChange(match);
      track("ram_spec.select", {
        id: match.id,
        total_capacity_gb: match.total_capacity_gb,
        ddr_generation: match.ddr_generation,
      });
    }
    setOpen(false);
    setSearch("");
  };

  const handleClear = () => {
    onChange(null);
    setOpen(false);
    setSearch("");
  };

  return (
    <>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={cn("w-full justify-between font-normal", !value && "text-muted-foreground", className)}
            disabled={disabled}
          >
            <span className="truncate">{selectedLabel}</span>
            <div className="flex items-center gap-1">
              {value && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5"
                  onClick={(event) => {
                    event.stopPropagation();
                    handleClear();
                  }}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
              <ChevronsUpDown className="h-4 w-4 opacity-60" />
            </div>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[320px] p-0" align="start">
          <Command shouldFilter={false}>
            <CommandInput
              value={search}
              onValueChange={setSearch}
              placeholder="Search capacity, speed, or generation…"
              className="h-9 px-3 text-sm"
            />
            <CommandEmpty>
              <div className="p-4 text-sm text-muted-foreground">
                {isFetching ? "Loading RAM specs…" : "No RAM specs found."}
              </div>
            </CommandEmpty>
            <CommandGroup className="max-h-64 overflow-y-auto">
              {options.map((spec) => (
                <CommandItem
                  key={spec.id}
                  value={String(spec.id)}
                  onSelect={() => handleSelect(spec.id)}
                  className="flex flex-col gap-1 px-3 py-2 text-left"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-sm">{formatRamSpecLabel(spec)}</span>
                    {value?.id === spec.id && <Check className="h-4 w-4 text-primary" />}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {spec.ddr_generation && <Badge variant="outline">{getRamGenerationLabel(spec.ddr_generation)}</Badge>}
                    {spec.total_capacity_gb !== null && (
                      <span>{spec.total_capacity_gb}GB total</span>
                    )}
                    {spec.module_count && spec.capacity_per_module_gb && (
                      <span>{spec.module_count}×{spec.capacity_per_module_gb}GB</span>
                    )}
                    {spec.speed_mhz && <span>{spec.speed_mhz}MHz</span>}
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
            <div className="border-t px-3 py-2">
              <Button
                variant="secondary"
                size="sm"
                className="w-full justify-center"
                onClick={() => setCreateOpen(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Create new RAM spec
              </Button>
            </div>
          </Command>
        </PopoverContent>
      </Popover>

      <RamSpecCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        isSubmitting={createMutation.isPending}
        onCreate={async (input) => {
          await createMutation.mutateAsync(input);
          setCreateOpen(false);
          setSearch("");
        }}
        initialSearch={search}
      />
    </>
  );
}

interface RamSpecCreateDialogProps {
  open: boolean;
  onOpenChange: (value: boolean) => void;
  isSubmitting: boolean;
  onCreate: (input: RamSpecCreateInput) => Promise<void>;
  initialSearch?: string;
}

function RamSpecCreateDialog({
  open,
  onOpenChange,
  isSubmitting,
  onCreate,
  initialSearch,
}: RamSpecCreateDialogProps) {
  const [formState, setFormState] = useState({
    label: initialSearch ?? "",
    ddr_generation: "ddr5",
    total_capacity_gb: "",
    module_count: "",
    capacity_per_module_gb: "",
    speed_mhz: "",
  });
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const totalCapacity = Number(formState.total_capacity_gb);
    if (Number.isNaN(totalCapacity) || totalCapacity <= 0) {
      setError("Total capacity must be a positive number.");
      return;
    }

    const payload: RamSpecCreateInput = {
      label: formState.label.trim() || undefined,
      ddr_generation: formState.ddr_generation,
      total_capacity_gb: totalCapacity,
      speed_mhz: formState.speed_mhz ? Number(formState.speed_mhz) : null,
      module_count: formState.module_count ? Number(formState.module_count) : null,
      capacity_per_module_gb: formState.capacity_per_module_gb ? Number(formState.capacity_per_module_gb) : null,
    };

    try {
      await onCreate(payload);
      setFormState({
        label: "",
        ddr_generation: formState.ddr_generation,
        total_capacity_gb: "",
        module_count: "",
        capacity_per_module_gb: "",
        speed_mhz: "",
      });
    } catch (exc) {
      const message = exc instanceof Error ? exc.message : "Failed to create RAM spec.";
      setError(message);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Create RAM specification</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="ram-spec-label">Label (optional)</Label>
            <Input
              id="ram-spec-label"
              placeholder="DDR5 32GB 5600MHz"
              value={formState.label}
              onChange={(event) => setFormState((prev) => ({ ...prev, label: event.target.value }))}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="ram-spec-generation">Generation</Label>
            <Select
              value={formState.ddr_generation}
              onValueChange={(value) => setFormState((prev) => ({ ...prev, ddr_generation: value }))}
            >
              <SelectTrigger id="ram-spec-generation">
                <SelectValue placeholder="Select generation" />
              </SelectTrigger>
              <SelectContent>
                {RAM_GENERATION_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="ram-spec-total">Total capacity (GB)</Label>
              <Input
                id="ram-spec-total"
                type="number"
                min="1"
                value={formState.total_capacity_gb}
                onChange={(event) => setFormState((prev) => ({ ...prev, total_capacity_gb: event.target.value }))}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="ram-spec-speed">Speed (MHz)</Label>
              <Input
                id="ram-spec-speed"
                type="number"
                min="0"
                value={formState.speed_mhz}
                onChange={(event) => setFormState((prev) => ({ ...prev, speed_mhz: event.target.value }))}
                placeholder="5600"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="ram-spec-modules">Modules</Label>
              <Input
                id="ram-spec-modules"
                type="number"
                min="1"
                value={formState.module_count}
                onChange={(event) => setFormState((prev) => ({ ...prev, module_count: event.target.value }))}
                placeholder="2"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="ram-spec-capacity-module">Capacity per module (GB)</Label>
              <Input
                id="ram-spec-capacity-module"
                type="number"
                min="1"
                value={formState.capacity_per_module_gb}
                onChange={(event) => setFormState((prev) => ({ ...prev, capacity_per_module_gb: event.target.value }))}
                placeholder="16"
              />
            </div>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <span className="inline-flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating…
                </span>
              ) : (
                "Create RAM spec"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function useRamSpecLabel(spec: RamSpecRecord | null | undefined): string {
  if (!spec) return "No RAM spec selected";
  const summary = formatRamSpecMetadata(spec);
  return summary ? `${formatRamSpecLabel(spec)} • ${summary}` : formatRamSpecLabel(spec);
}
