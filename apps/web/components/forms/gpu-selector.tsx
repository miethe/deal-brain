"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tantml:react-query";
import { useDebounce } from "use-debounce";
import { Check, ChevronsUpDown, Loader2, X } from "lucide-react";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "cmdk";

import { apiFetch } from "../../lib/utils";
import { cn } from "../../lib/utils";
import { track } from "../../lib/analytics";
import { Button } from "../ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Badge } from "../ui/badge";

interface GpuOption {
  id: number;
  name: string;
  manufacturer?: string | null;
  type?: string | null;
  memory_gb?: number | null;
  tdp_w?: number | null;
}

interface GpuSelectorProps {
  value: number | null | undefined;
  onChange: (gpuId: number | null) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

async function fetchGpus(search: string): Promise<GpuOption[]> {
  const params = new URLSearchParams();
  params.set("limit", "50");
  if (search) {
    params.set("search", search);
  }
  return apiFetch<GpuOption[]>(`/v1/catalog/gpus?${params.toString()}`);
}

function formatGpuLabel(gpu: GpuOption) {
  const parts: string[] = [gpu.name];
  if (gpu.manufacturer) {
    parts.push(`(${gpu.manufacturer})`);
  }
  return parts.join(" ");
}

function formatGpuMetadata(gpu: GpuOption) {
  const items: string[] = [];
  if (gpu.type) {
    items.push(gpu.type === "integrated" ? "Integrated" : "Discrete");
  }
  if (gpu.memory_gb) {
    items.push(`${gpu.memory_gb}GB VRAM`);
  }
  if (gpu.tdp_w) {
    items.push(`${gpu.tdp_w}W TDP`);
  }
  return items.join(" • ");
}

export function GpuSelector({
  value,
  onChange,
  disabled = false,
  placeholder = "Select GPU",
  className,
}: GpuSelectorProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 250);

  const { data: gpus = [], isFetching } = useQuery({
    queryKey: ["catalog", "gpus", debouncedSearch],
    queryFn: () => fetchGpus(debouncedSearch),
    staleTime: 60 * 1000,
  });

  const selectedGpu = useMemo(() => {
    if (!value) return null;
    return gpus.find((gpu) => gpu.id === value);
  }, [gpus, value]);

  const selectedLabel = selectedGpu ? formatGpuLabel(selectedGpu) : placeholder;

  const handleSelect = (gpuId: number) => {
    const match = gpus.find((gpu) => gpu.id === gpuId);
    if (match) {
      onChange(match.id);
      track("gpu.select", {
        id: match.id,
        name: match.name,
      });
    }
    setOpen(false);
    setSearch("");
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(null);
    setSearch("");
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "w-full justify-between font-normal",
            !selectedGpu && "text-muted-foreground",
            className
          )}
          disabled={disabled}
        >
          <span className="truncate">{selectedLabel}</span>
          <div className="flex items-center gap-1 ml-2">
            {selectedGpu && !disabled && (
              <X
                className="h-4 w-4 shrink-0 opacity-50 hover:opacity-100"
                onClick={handleClear}
              />
            )}
            <ChevronsUpDown className="h-4 w-4 shrink-0 opacity-50" />
          </div>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start">
        <Command shouldFilter={false}>
          <div className="relative">
            <CommandInput
              placeholder="Search GPUs..."
              value={search}
              onValueChange={setSearch}
              className="h-9 border-0 border-b"
            />
            {isFetching && (
              <Loader2 className="absolute right-3 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />
            )}
          </div>
          {gpus.length === 0 && !isFetching ? (
            <CommandEmpty className="py-6 text-center text-sm">
              No GPUs found.
            </CommandEmpty>
          ) : (
            <CommandGroup className="max-h-[300px] overflow-y-auto p-1">
              {gpus.map((gpu) => (
                <CommandItem
                  key={gpu.id}
                  value={String(gpu.id)}
                  onSelect={() => handleSelect(gpu.id)}
                  className="flex flex-col items-start gap-1 px-3 py-2 cursor-pointer"
                >
                  <div className="flex items-center gap-2 w-full">
                    <Check
                      className={cn(
                        "h-4 w-4 shrink-0",
                        value === gpu.id ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <div className="flex-1 flex items-center justify-between gap-2">
                      <span className="font-medium">{gpu.name}</span>
                      <div className="flex items-center gap-1">
                        {gpu.type === "integrated" && (
                          <Badge variant="outline" className="text-xs">
                            Integrated
                          </Badge>
                        )}
                        {gpu.manufacturer && (
                          <Badge variant="outline" className="text-xs">
                            {gpu.manufacturer}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  {formatGpuMetadata(gpu) && (
                    <div className="ml-6 text-xs text-muted-foreground">
                      {formatGpuMetadata(gpu)}
                    </div>
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
          )}
        </Command>
      </PopoverContent>
    </Popover>
  );
}
