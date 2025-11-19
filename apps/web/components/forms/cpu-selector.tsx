"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useDebounce } from "use-debounce";
import { Check, ChevronsUpDown, Loader2, X } from "lucide-react";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "cmdk";

import { apiFetch } from "../../lib/utils";
import { cn } from "../../lib/utils";
import { track } from "../../lib/analytics";
import { Button } from "../ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Badge } from "../ui/badge";

interface CpuOption {
  id: number;
  name: string;
  manufacturer?: string | null;
  cores?: number | null;
  threads?: number | null;
  base_clock_ghz?: number | null;
}

interface CpuSelectorProps {
  value: number | null | undefined;
  onChange: (cpuId: number | null) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

async function fetchCpus(search: string): Promise<CpuOption[]> {
  const params = new URLSearchParams();
  params.set("limit", "50");
  if (search) {
    params.set("search", search);
  }
  return apiFetch<CpuOption[]>(`/v1/catalog/cpus?${params.toString()}`);
}

function formatCpuLabel(cpu: CpuOption) {
  const parts: string[] = [cpu.name];
  if (cpu.manufacturer) {
    parts.push(`(${cpu.manufacturer})`);
  }
  return parts.join(" ");
}

function formatCpuMetadata(cpu: CpuOption) {
  const items: string[] = [];
  if (cpu.cores) {
    items.push(`${cpu.cores} cores`);
  }
  if (cpu.threads) {
    items.push(`${cpu.threads} threads`);
  }
  if (cpu.base_clock_ghz) {
    items.push(`${cpu.base_clock_ghz}GHz`);
  }
  return items.join(" • ");
}

export function CpuSelector({
  value,
  onChange,
  disabled = false,
  placeholder = "Select CPU",
  className,
}: CpuSelectorProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 250);

  const { data: cpus = [], isFetching } = useQuery({
    queryKey: ["catalog", "cpus", debouncedSearch],
    queryFn: () => fetchCpus(debouncedSearch),
    staleTime: 60 * 1000,
  });

  const selectedCpu = useMemo(() => {
    if (!value) return null;
    return cpus.find((cpu) => cpu.id === value);
  }, [cpus, value]);

  const selectedLabel = selectedCpu ? formatCpuLabel(selectedCpu) : placeholder;

  const handleSelect = (cpuId: number) => {
    const match = cpus.find((cpu) => cpu.id === cpuId);
    if (match) {
      onChange(match.id);
      track("cpu.select", {
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
            !selectedCpu && "text-muted-foreground",
            className
          )}
          disabled={disabled}
        >
          <span className="truncate">{selectedLabel}</span>
          <div className="flex items-center gap-1 ml-2">
            {selectedCpu && !disabled && (
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
              placeholder="Search CPUs..."
              value={search}
              onValueChange={setSearch}
              className="h-9 border-0 border-b"
            />
            {isFetching && (
              <Loader2 className="absolute right-3 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />
            )}
          </div>
          {cpus.length === 0 && !isFetching ? (
            <CommandEmpty className="py-6 text-center text-sm">
              No CPUs found.
            </CommandEmpty>
          ) : (
            <CommandGroup className="max-h-[300px] overflow-y-auto p-1">
              {cpus.map((cpu) => (
                <CommandItem
                  key={cpu.id}
                  value={String(cpu.id)}
                  onSelect={() => handleSelect(cpu.id)}
                  className="flex flex-col items-start gap-1 px-3 py-2 cursor-pointer"
                >
                  <div className="flex items-center gap-2 w-full">
                    <Check
                      className={cn(
                        "h-4 w-4 shrink-0",
                        value === cpu.id ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <div className="flex-1 flex items-center justify-between gap-2">
                      <span className="font-medium">{cpu.name}</span>
                      {cpu.manufacturer && (
                        <Badge variant="outline" className="text-xs">
                          {cpu.manufacturer}
                        </Badge>
                      )}
                    </div>
                  </div>
                  {formatCpuMetadata(cpu) && (
                    <div className="ml-6 text-xs text-muted-foreground">
                      {formatCpuMetadata(cpu)}
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
