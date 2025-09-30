"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useMemo, useRef, useState } from "react";

import { apiFetch } from "../../lib/utils";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Dialog, DialogTrigger } from "../ui/dialog";
import { ModalShell } from "../ui/modal-shell";

interface CpuOption {
  id: number;
  name: string;
  manufacturer?: string | null;
}

interface CpuCreatePayload {
  name: string;
  manufacturer: string;
  socket?: string | null;
  cores?: number | null;
  threads?: number | null;
  tdp_w?: number | null;
}

const CONDITIONS = [
  { value: "new", label: "New" },
  { value: "refurb", label: "Refurb" },
  { value: "used", label: "Used" }
];

const DEFAULT_RAM_OPTIONS = [4, 8, 16, 32, 64, 128, 192, 256, 384, 512];
const DEFAULT_STORAGE_CAPACITIES = [128, 256, 512, 1024, 2048, 4096];
const DEFAULT_STORAGE_TYPES = ["NVMe SSD", "SATA SSD", "SATA HDD", "Hybrid SSHD", "U.2 SSD"];

export function AddListingForm() {
  const queryClient = useQueryClient();
  const { data: cpus } = useQuery<CpuOption[]>({
    queryKey: ["cpus"],
    queryFn: () => apiFetch<CpuOption[]>("/v1/catalog/cpus"),
  });

  const [selectedCpuId, setSelectedCpuId] = useState<string>("");
  const [status, setStatus] = useState<string | null>(null);
  const [ramOptions, setRamOptions] = useState<number[]>(DEFAULT_RAM_OPTIONS);
  const [storageCapOptions, setStorageCapOptions] = useState<number[]>(DEFAULT_STORAGE_CAPACITIES);
  const [storageTypeOptions, setStorageTypeOptions] = useState<string[]>(DEFAULT_STORAGE_TYPES);

  const [isCpuModalOpen, setCpuModalOpen] = useState(false);
  const [newCpuForm, setNewCpuForm] = useState({
    name: "",
    manufacturer: "",
    socket: "",
    cores: "",
    threads: "",
    tdp_w: "",
  });

  const ramInputRef = useRef<HTMLInputElement | null>(null);
  const primaryStorageRef = useRef<HTMLInputElement | null>(null);
  const primaryTypeRef = useRef<HTMLInputElement | null>(null);
  const secondaryStorageRef = useRef<HTMLInputElement | null>(null);
  const secondaryTypeRef = useRef<HTMLInputElement | null>(null);

  const createListingMutation = useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      await apiFetch("/v1/listings", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
  });

  const createCpuMutation = useMutation({
    mutationFn: async (payload: CpuCreatePayload) => {
      return apiFetch<CpuOption>("/v1/catalog/cpus", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: (cpu) => {
      queryClient.invalidateQueries({ queryKey: ["cpus"] });
      setSelectedCpuId(String(cpu.id));
      setCpuModalOpen(false);
      setNewCpuForm({ name: "", manufacturer: "", socket: "", cores: "", threads: "", tdp_w: "" });
      setStatus(`CPU “${cpu.name}” created and selected.`);
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Unable to create CPU";
      setStatus(message);
    },
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const form = event.currentTarget;

    const payload = {
      title: formData.get("title"),
      price_usd: Number(formData.get("price_usd")) || 0,
      condition: formData.get("condition") || "used",
      cpu_id: selectedCpuId ? Number(selectedCpuId) : null,
      ram_gb: parseNullableNumber(formData.get("ram_gb")),
      primary_storage_gb: parseNullableNumber(formData.get("primary_storage_gb")) ?? 0,
      primary_storage_type: sanitizeString(formData.get("primary_storage_type")),
      secondary_storage_gb: parseNullableNumber(formData.get("secondary_storage_gb")),
      secondary_storage_type: sanitizeString(formData.get("secondary_storage_type")),
    };

    createListingMutation.mutate(payload, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["listings"] });
        setStatus("Listing created successfully");
        form.reset();
        setSelectedCpuId("");
      },
      onError: (error) => {
        const message = error instanceof Error ? error.message : "Unknown error";
        setStatus(`Failed to create listing: ${message}`);
      },
    });
  };

  const sortedCpus = useMemo(() => {
    return (cpus ?? []).slice().sort((a, b) => a.name.localeCompare(b.name));
  }, [cpus]);

  const addRamOption = () => {
    const value = prompt("New RAM capacity (GB)");
    if (!value) return;
    const numeric = Number(value);
    if (Number.isNaN(numeric) || numeric <= 0) {
      setStatus("RAM must be a positive number.");
      return;
    }
    setRamOptions((prev) => Array.from(new Set([...prev, numeric])).sort((a, b) => a - b));
    if (ramInputRef.current) {
      ramInputRef.current.value = String(numeric);
    }
  };

  const addStorageCapacityOption = (target: "primary" | "secondary") => {
    const value = prompt("New storage capacity (GB)");
    if (!value) return;
    const numeric = Number(value);
    if (Number.isNaN(numeric) || numeric <= 0) {
      setStatus("Storage capacity must be a positive number.");
      return;
    }
    setStorageCapOptions((prev) => Array.from(new Set([...prev, numeric])).sort((a, b) => a - b));
    const ref = target === "primary" ? primaryStorageRef : secondaryStorageRef;
    if (ref.current) {
      ref.current.value = String(numeric);
    }
  };

  const addStorageTypeOption = (target: "primary" | "secondary") => {
    const value = prompt("New storage type");
    if (!value) return;
    setStorageTypeOptions((prev) => Array.from(new Set([...prev, value.trim()])).sort());
    const ref = target === "primary" ? primaryTypeRef : secondaryTypeRef;
    if (ref.current) {
      ref.current.value = value.trim();
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add listing</CardTitle>
        <CardDescription>Complete the essentials—valuation recalculates immediately after submit.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="title">Title</Label>
            <Input id="title" name="title" required placeholder="Minisforum UM790 Pro - 32GB/512GB" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="price_usd">Listing price (USD)</Label>
            <Input id="price_usd" name="price_usd" required type="number" step="0.01" min="0" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="condition">Condition</Label>
            <select
              id="condition"
              name="condition"
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              defaultValue="used"
            >
              {CONDITIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="cpu_id">CPU</Label>
            <div className="flex items-center gap-2">
              <select
                id="cpu_id"
                name="cpu_id"
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={selectedCpuId}
                onChange={(event) => setSelectedCpuId(event.target.value)}
              >
                <option value="">Select CPU</option>
                {sortedCpus.map((cpu) => (
                  <option key={cpu.id} value={cpu.id}>
                    {cpu.name}
                  </option>
                ))}
              </select>
              <Dialog open={isCpuModalOpen} onOpenChange={setCpuModalOpen}>
                <DialogTrigger asChild>
                  <Button type="button" variant="secondary" size="sm">
                    Add CPU
                  </Button>
                </DialogTrigger>
                <ModalShell
                  title="Add CPU"
                  description="Create a lightweight CPU entry without leaving the form."
                  footer={
                    <div className="flex w-full justify-end gap-2">
                      <Button variant="ghost" type="button" onClick={() => setCpuModalOpen(false)}>
                        Cancel
                      </Button>
                      <Button
                        type="button"
                        disabled={createCpuMutation.isPending}
                        onClick={() => {
                          if (!newCpuForm.name || !newCpuForm.manufacturer) {
                            setStatus("CPU name and manufacturer are required.");
                            return;
                          }
                          createCpuMutation.mutate({
                            name: newCpuForm.name,
                            manufacturer: newCpuForm.manufacturer,
                            socket: newCpuForm.socket || undefined,
                            cores: newCpuForm.cores ? Number(newCpuForm.cores) : undefined,
                            threads: newCpuForm.threads ? Number(newCpuForm.threads) : undefined,
                            tdp_w: newCpuForm.tdp_w ? Number(newCpuForm.tdp_w) : undefined,
                          });
                        }}
                      >
                        {createCpuMutation.isPending ? "Saving…" : "Save CPU"}
                      </Button>
                    </div>
                  }
                >
                  <div className="grid gap-3">
                    <div className="grid gap-1">
                      <Label htmlFor="new-cpu-name">Name</Label>
                      <Input
                        id="new-cpu-name"
                        value={newCpuForm.name}
                        onChange={(event) => setNewCpuForm((prev) => ({ ...prev, name: event.target.value }))}
                        placeholder="AMD Ryzen 7 7840HS"
                      />
                    </div>
                    <div className="grid gap-1">
                      <Label htmlFor="new-cpu-manufacturer">Manufacturer</Label>
                      <Input
                        id="new-cpu-manufacturer"
                        value={newCpuForm.manufacturer}
                        onChange={(event) => setNewCpuForm((prev) => ({ ...prev, manufacturer: event.target.value }))}
                        placeholder="AMD"
                      />
                    </div>
                    <div className="grid gap-1">
                      <Label htmlFor="new-cpu-socket">Socket</Label>
                      <Input
                        id="new-cpu-socket"
                        value={newCpuForm.socket}
                        onChange={(event) => setNewCpuForm((prev) => ({ ...prev, socket: event.target.value }))}
                        placeholder="FP7"
                      />
                    </div>
                    <div className="grid gap-3 md:grid-cols-3">
                      <div className="grid gap-1">
                        <Label htmlFor="new-cpu-cores">Cores</Label>
                        <Input
                          id="new-cpu-cores"
                          type="number"
                          min="1"
                          value={newCpuForm.cores}
                          onChange={(event) => setNewCpuForm((prev) => ({ ...prev, cores: event.target.value }))}
                        />
                      </div>
                      <div className="grid gap-1">
                        <Label htmlFor="new-cpu-threads">Threads</Label>
                        <Input
                          id="new-cpu-threads"
                          type="number"
                          min="1"
                          value={newCpuForm.threads}
                          onChange={(event) => setNewCpuForm((prev) => ({ ...prev, threads: event.target.value }))}
                        />
                      </div>
                      <div className="grid gap-1">
                        <Label htmlFor="new-cpu-tdp">TDP (W)</Label>
                        <Input
                          id="new-cpu-tdp"
                          type="number"
                          min="1"
                          value={newCpuForm.tdp_w}
                          onChange={(event) => setNewCpuForm((prev) => ({ ...prev, tdp_w: event.target.value }))}
                        />
                      </div>
                    </div>
                  </div>
                </ModalShell>
              </Dialog>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="ram_gb">RAM (GB)</Label>
            <div className="flex items-center gap-2">
              <Input ref={ramInputRef} id="ram_gb" name="ram_gb" type="number" min="0" list="ram-options" placeholder="Select or type" />
              <Button type="button" size="sm" variant="ghost" onClick={addRamOption}>
                Add new…
              </Button>
            </div>
            <datalist id="ram-options">
              {ramOptions.map((value) => (
                <option key={value} value={value} />
              ))}
            </datalist>
          </div>
          <div className="space-y-2">
            <Label htmlFor="primary_storage_gb">Primary storage (GB)</Label>
            <div className="flex items-center gap-2">
              <Input
                ref={primaryStorageRef}
                id="primary_storage_gb"
                name="primary_storage_gb"
                type="number"
                min="0"
                list="primary-storage-options"
                placeholder="Select or type"
              />
              <Button type="button" size="sm" variant="ghost" onClick={() => addStorageCapacityOption("primary")}>
                Add new…
              </Button>
            </div>
            <datalist id="primary-storage-options">
              {storageCapOptions.map((value) => (
                <option key={`primary-${value}`} value={value} />
              ))}
            </datalist>
          </div>
          <div className="space-y-2">
            <Label htmlFor="primary_storage_type">Primary storage type</Label>
            <div className="flex items-center gap-2">
              <Input
                ref={primaryTypeRef}
                id="primary_storage_type"
                name="primary_storage_type"
                list="storage-type-options"
                placeholder="NVMe SSD"
              />
              <Button type="button" size="sm" variant="ghost" onClick={() => addStorageTypeOption("primary")}>
                Add new…
              </Button>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="secondary_storage_gb">Secondary storage (GB)</Label>
            <div className="flex items-center gap-2">
              <Input
                ref={secondaryStorageRef}
                id="secondary_storage_gb"
                name="secondary_storage_gb"
                type="number"
                min="0"
                list="secondary-storage-options"
                placeholder="Optional"
              />
              <Button type="button" size="sm" variant="ghost" onClick={() => addStorageCapacityOption("secondary")}>
                Add new…
              </Button>
            </div>
            <datalist id="secondary-storage-options">
              {storageCapOptions.map((value) => (
                <option key={`secondary-${value}`} value={value} />
              ))}
            </datalist>
          </div>
          <div className="space-y-2">
            <Label htmlFor="secondary_storage_type">Secondary storage type</Label>
            <div className="flex items-center gap-2">
              <Input
                ref={secondaryTypeRef}
                id="secondary_storage_type"
                name="secondary_storage_type"
                list="storage-type-options"
                placeholder="Optional"
              />
              <Button type="button" size="sm" variant="ghost" onClick={() => addStorageTypeOption("secondary")}>
                Add new…
              </Button>
            </div>
          </div>
          <datalist id="storage-type-options">
            {storageTypeOptions.map((value) => (
              <option key={value} value={value} />
            ))}
          </datalist>
          <div className="md:col-span-2 flex items-center justify-between">
            <Button type="submit" disabled={createListingMutation.isPending}>
              {createListingMutation.isPending ? "Saving…" : "Save listing"}
            </Button>
            {status && <span className="text-sm text-muted-foreground">{status}</span>}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function parseNullableNumber(value: FormDataEntryValue | null): number | null {
  if (value === null || value === "") return null;
  const numeric = Number(value);
  return Number.isNaN(numeric) ? null : numeric;
}

function sanitizeString(value: FormDataEntryValue | null): string | null {
  if (value === null) return null;
  const text = value.toString().trim();
  return text.length ? text : null;
}
