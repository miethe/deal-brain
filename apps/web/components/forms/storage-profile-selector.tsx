"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDebounce } from "use-debounce";
import { Check, ChevronsUpDown, Loader2, Plus, X } from "lucide-react";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "cmdk";

import { apiFetch } from "../../lib/utils";
import { cn } from "../../lib/utils";
import { STORAGE_MEDIUM_OPTIONS, getStorageMediumLabel } from "../../lib/component-catalog";
import { track } from "../../lib/analytics";
import { StorageProfileRecord } from "../../types/listings";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";

interface StorageProfileSelectorProps {
  value: StorageProfileRecord | null | undefined;
  onChange: (profile: StorageProfileRecord | null) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  context?: "primary" | "secondary";
}

interface StorageProfileCreateInput {
  label?: string;
  medium: string;
  interface?: string | null;
  form_factor?: string | null;
  capacity_gb: number;
  performance_tier?: string | null;
}

const STORAGE_PERFORMANCE_OPTIONS = [
  { value: "performance", label: "Performance" },
  { value: "standard", label: "Standard" },
  { value: "budget", label: "Budget" },
  { value: "archive", label: "Archive" },
];

function formatStorageProfileLabel(profile: StorageProfileRecord) {
  if (profile.label) return profile.label;
  const parts: string[] = [];
  if (profile.medium) parts.push(getStorageMediumLabel(profile.medium));
  if (profile.interface) parts.push(profile.interface);
  if (profile.capacity_gb) parts.push(`${profile.capacity_gb}GB`);
  if (profile.form_factor) parts.push(profile.form_factor);
  return parts.join(" · ");
}

async function fetchStorageProfiles(search: string, medium: string | null) {
  const params = new URLSearchParams();
  params.set("limit", "30");
  if (search) params.set("search", search);
  if (medium) params.set("medium", medium);
  return apiFetch<StorageProfileRecord[]>(`/v1/catalog/storage-profiles?${params.toString()}`);
}

export function StorageProfileSelector({
  value,
  onChange,
  disabled = false,
  placeholder = "Select storage profile",
  className,
  context = "primary",
}: StorageProfileSelectorProps) {
  const [open, setOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedMedium, setSelectedMedium] = useState<string | null>(null);
  const [debouncedSearch] = useDebounce(search, 250);
  const queryClient = useQueryClient();

  const { data: profiles = [], isFetching } = useQuery({
    queryKey: ["catalog", "storage-profiles", debouncedSearch, selectedMedium, context],
    queryFn: () => fetchStorageProfiles(debouncedSearch, selectedMedium),
    staleTime: 60 * 1000,
  });

  const createMutation = useMutation({
    mutationFn: async (input: StorageProfileCreateInput) => {
      return apiFetch<StorageProfileRecord>("/v1/catalog/storage-profiles", {
        method: "POST",
        body: JSON.stringify(input),
      });
    },
    onSuccess: (profile) => {
      queryClient.invalidateQueries({ queryKey: ["catalog", "storage-profiles"] });
      onChange(profile);
      track("storage_profile.create", {
        id: profile.id,
        medium: profile.medium,
        capacity_gb: profile.capacity_gb,
        performance_tier: profile.performance_tier,
      });
      setOpen(false);
    },
  });

  const options = useMemo(() => {
    if (!value) return profiles;
    return profiles.some((profile) => profile.id === value.id) ? profiles : [value, ...profiles];
  }, [profiles, value]);

  const selectedLabel = value ? formatStorageProfileLabel(value) : placeholder;

  const handleSelect = (profileId: number) => {
    const match = options.find((profile) => profile.id === profileId);
    if (match) {
      onChange(match);
      track("storage_profile.select", {
        id: match.id,
        medium: match.medium,
        capacity_gb: match.capacity_gb,
        performance_tier: match.performance_tier,
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
        <PopoverContent className="w-[340px] p-0" align="start">
          <Command shouldFilter={false}>
            <div className="flex items-center gap-2 border-b px-3 py-2">
              <CommandInput
                value={search}
                onValueChange={setSearch}
                placeholder="Search interface, capacity, or label…"
                className="h-9 flex-1 text-sm"
              />
              <Select
                value={selectedMedium ?? "all"}
                onValueChange={(value) => setSelectedMedium(value === "all" ? null : value)}
              >
                <SelectTrigger className="h-9 w-[120px]">
                  <SelectValue placeholder="Medium" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All media</SelectItem>
                  {STORAGE_MEDIUM_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <CommandEmpty>
              <div className="p-4 text-sm text-muted-foreground">
                {isFetching ? "Loading storage profiles…" : "No storage profiles found."}
              </div>
            </CommandEmpty>
            <CommandGroup className="max-h-64 overflow-y-auto">
              {options.map((profile) => (
                <CommandItem
                  key={profile.id}
                  value={String(profile.id)}
                  onSelect={() => handleSelect(profile.id)}
                  className="flex flex-col gap-1 px-3 py-2 text-left"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-sm">{formatStorageProfileLabel(profile)}</span>
                    {value?.id === profile.id && <Check className="h-4 w-4 text-primary" />}
                  </div>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    {profile.medium && <Badge variant="outline">{getStorageMediumLabel(profile.medium)}</Badge>}
                    {profile.capacity_gb && <span>{profile.capacity_gb}GB</span>}
                    {profile.performance_tier && <span className="capitalize">{profile.performance_tier}</span>}
                    {profile.interface && <span>{profile.interface}</span>}
                    {profile.form_factor && <span>{profile.form_factor}</span>}
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
                Create new storage profile
              </Button>
            </div>
          </Command>
        </PopoverContent>
      </Popover>

      <StorageProfileCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        isSubmitting={createMutation.isPending}
        onCreate={async (input) => {
          await createMutation.mutateAsync(input);
          setCreateOpen(false);
          setSearch("");
        }}
        presetMedium={selectedMedium ?? undefined}
      />
    </>
  );
}

interface StorageProfileCreateDialogProps {
  open: boolean;
  onOpenChange: (value: boolean) => void;
  isSubmitting: boolean;
  onCreate: (input: StorageProfileCreateInput) => Promise<void>;
  presetMedium?: string;
}

function StorageProfileCreateDialog({
  open,
  onOpenChange,
  isSubmitting,
  onCreate,
  presetMedium,
}: StorageProfileCreateDialogProps) {
  const [formState, setFormState] = useState({
    label: "",
    medium: presetMedium ?? "nvme",
    capacity_gb: "",
    interface: "",
    form_factor: "",
    performance_tier: "performance",
  });
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const capacity = Number(formState.capacity_gb);
    if (Number.isNaN(capacity) || capacity <= 0) {
      setError("Capacity must be a positive number.");
      return;
    }

    const payload: StorageProfileCreateInput = {
      label: formState.label.trim() || undefined,
      medium: formState.medium,
      capacity_gb: capacity,
      interface: formState.interface.trim() || null,
      form_factor: formState.form_factor.trim() || null,
      performance_tier: formState.performance_tier.trim() || null,
    };

    try {
      await onCreate(payload);
      setFormState({
        label: "",
        medium: formState.medium,
        capacity_gb: "",
        interface: "",
        form_factor: "",
        performance_tier: formState.performance_tier,
      });
    } catch (exc) {
      const message = exc instanceof Error ? exc.message : "Failed to create storage profile.";
      setError(message);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Create storage profile</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="storage-profile-label">Label (optional)</Label>
            <Input
              id="storage-profile-label"
              placeholder="NVMe PCIe 4.0 1TB"
              value={formState.label}
              onChange={(event) => setFormState((prev) => ({ ...prev, label: event.target.value }))}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="storage-profile-medium">Medium</Label>
            <Select
              value={formState.medium}
              onValueChange={(value) => setFormState((prev) => ({ ...prev, medium: value }))}
            >
              <SelectTrigger id="storage-profile-medium">
                <SelectValue placeholder="Select medium" />
              </SelectTrigger>
              <SelectContent>
                {STORAGE_MEDIUM_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="storage-profile-capacity">Capacity (GB)</Label>
            <Input
              id="storage-profile-capacity"
              type="number"
              min="1"
              value={formState.capacity_gb}
              onChange={(event) => setFormState((prev) => ({ ...prev, capacity_gb: event.target.value }))}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="storage-profile-interface">Interface</Label>
              <Input
                id="storage-profile-interface"
                placeholder="PCIe 4.0 x4"
                value={formState.interface}
                onChange={(event) => setFormState((prev) => ({ ...prev, interface: event.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="storage-profile-form-factor">Form factor</Label>
              <Input
                id="storage-profile-form-factor"
                placeholder='M.2 2280'
                value={formState.form_factor}
                onChange={(event) => setFormState((prev) => ({ ...prev, form_factor: event.target.value }))}
              />
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="storage-profile-tier">Performance tier</Label>
            <Select
              value={formState.performance_tier}
              onValueChange={(value) => setFormState((prev) => ({ ...prev, performance_tier: value }))}
            >
              <SelectTrigger id="storage-profile-tier">
                <SelectValue placeholder="Select tier" />
              </SelectTrigger>
              <SelectContent>
                {STORAGE_PERFORMANCE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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
                "Create storage profile"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function useStorageProfileLabel(profile: StorageProfileRecord | null | undefined): string {
  if (!profile) return "No storage profile selected";
  const label = formatStorageProfileLabel(profile);
  const meta: string[] = [];
  if (profile.performance_tier) meta.push(profile.performance_tier);
  if (profile.interface) meta.push(profile.interface);
  return meta.length ? `${label} • ${meta.join(" • ")}` : label;
}
