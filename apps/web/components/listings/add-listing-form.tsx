"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiFetch } from "../../lib/utils";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { Label } from "../ui/label";

interface CpuOption {
  id: number;
  name: string;
}

const CONDITIONS = [
  { value: "new", label: "New" },
  { value: "refurb", label: "Refurb" },
  { value: "used", label: "Used" }
];

export function AddListingForm() {
  const queryClient = useQueryClient();
  const { data: cpus } = useQuery<CpuOption[]>({
    queryKey: ["cpus"],
    queryFn: () => apiFetch<CpuOption[]>("/v1/catalog/cpus")
  });

  const [status, setStatus] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async (formData: Record<string, any>) => {
      await apiFetch("/v1/listings", {
        method: "POST",
        body: JSON.stringify(formData)
      });
    }
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const form = event.currentTarget;
    const payload = {
      title: formData.get("title"),
      price_usd: Number(formData.get("price_usd")),
      condition: formData.get("condition"),
      cpu_id: formData.get("cpu_id") ? Number(formData.get("cpu_id")) : null,
      ram_gb: Number(formData.get("ram_gb")) || 0,
      primary_storage_gb: Number(formData.get("primary_storage_gb")) || 0,
      primary_storage_type: formData.get("primary_storage_type") || null,
      secondary_storage_gb: Number(formData.get("secondary_storage_gb")) || null,
      secondary_storage_type: formData.get("secondary_storage_type") || null
    };
    mutation.mutate(payload, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["listings"] });
        setStatus("Listing created successfully");
        form.reset();
      },
      onError: (error) => {
        const message = error instanceof Error ? error.message : "Unknown error";
        setStatus(`Failed to create listing: ${message}`);
      }
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add listing</CardTitle>
        <CardDescription>Just the essentials—valuation runs right after submit.</CardDescription>
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
            <select
              id="cpu_id"
              name="cpu_id"
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="">Select CPU</option>
              {cpus?.map((cpu) => (
                <option key={cpu.id} value={cpu.id}>
                  {cpu.name}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="ram_gb">RAM (GB)</Label>
            <Input id="ram_gb" name="ram_gb" type="number" min="0" step="1" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="primary_storage_gb">Primary storage (GB)</Label>
            <Input id="primary_storage_gb" name="primary_storage_gb" type="number" min="0" step="1" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="primary_storage_type">Primary storage type</Label>
            <Input id="primary_storage_type" name="primary_storage_type" placeholder="NVMe SSD" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="secondary_storage_gb">Secondary storage (GB)</Label>
            <Input id="secondary_storage_gb" name="secondary_storage_gb" type="number" min="0" step="1" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="secondary_storage_type">Secondary storage type</Label>
            <Input id="secondary_storage_type" name="secondary_storage_type" placeholder="2.5&quot; SATA" />
          </div>
          <div className="md:col-span-2 flex items-center justify-between">
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Saving…" : "Save listing"}
            </Button>
            {status && <span className="text-sm text-muted-foreground">{status}</span>}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
