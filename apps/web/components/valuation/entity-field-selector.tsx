"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronsUpDown } from "lucide-react";
import { useDebounce } from "use-debounce";

import { Button } from "../ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Command, CommandEmpty, CommandInput, CommandItem, CommandList } from "../ui/command";
import { VirtualizedCommandList } from "../ui/virtualized-command-list";
import { cn } from "../../lib/utils";
import { fetchEntitiesMetadata } from "../../lib/api/entities";

interface EntityFieldSelectorProps {
  value: string | null; // Format: "entity.field" (e.g., "listing.price_usd")
  onChange: (value: string, fieldType: string, options?: string[]) => void;
  placeholder?: string;
}

export function EntityFieldSelector({ value, onChange, placeholder }: EntityFieldSelectorProps) {
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const { data: metadata, isLoading } = useQuery({
    queryKey: ["entities-metadata"],
    queryFn: fetchEntitiesMetadata,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Debounce search input to reduce filtering operations (200ms delay)
  const [debouncedSearchQuery] = useDebounce(searchQuery, 200);

  // Flatten entities and fields for searchable list with memoization
  const allFields = useMemo(() => {
    if (!metadata?.entities) return [];

    return metadata.entities.flatMap((entity) =>
      entity.fields.map((field) => ({
        key: `${entity.key}.${field.key}`,
        label: field.label,
        entityLabel: entity.label,
        entityKey: entity.key,
        fieldKey: field.key,
        type: field.data_type,
        options: field.options || undefined,
        description: field.description,
      }))
    );
  }, [metadata?.entities]);

  // Filter fields based on debounced search query
  const filteredFields = useMemo(() => {
    if (!debouncedSearchQuery) return allFields;

    const query = debouncedSearchQuery.toLowerCase();
    return allFields.filter(
      (field) =>
        field.label.toLowerCase().includes(query) ||
        field.key.toLowerCase().includes(query) ||
        field.entityLabel.toLowerCase().includes(query)
    );
  }, [allFields, debouncedSearchQuery]);

  const selectedField = allFields.find((f) => f.key === value);

  const handleSelect = (fieldKey: string) => {
    const field = allFields.find((f) => f.key === fieldKey);
    if (field) {
      onChange(fieldKey, field.type, field.options);
      setOpen(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          {selectedField ? (
            <span className="truncate">
              {selectedField.entityLabel} → {selectedField.label}
            </span>
          ) : (
            placeholder || "Select field..."
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0">
        <Command shouldFilter={false}>
          <CommandInput placeholder="Search fields..." value={searchQuery} onValueChange={setSearchQuery} />
          <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
            {filteredFields.length} {filteredFields.length === 1 ? "field" : "fields"} found
          </div>
          <CommandList className="max-h-[400px] overflow-hidden">
            {isLoading ? (
              <div className="p-4 text-sm text-muted-foreground text-center">
                Loading fields...
              </div>
            ) : filteredFields.length === 0 ? (
              <CommandEmpty>No fields found.</CommandEmpty>
            ) : (
              <VirtualizedCommandList
                items={filteredFields}
                itemHeight={64}
                maxHeight={400}
                renderItem={(field) => (
                  <CommandItem
                    key={field.key}
                    value={field.key}
                    onSelect={() => {
                      onChange(field.key, field.type, field.options);
                      setOpen(false);
                    }}
                    className="flex items-center justify-between gap-2 cursor-pointer"
                  >
                    <div className="flex flex-col flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium truncate">{field.label}</span>
                        {value === field.key && (
                          <Check className="h-4 w-4 shrink-0" />
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {field.entityLabel} • {field.type}
                      </span>
                      {field.description && (
                        <span className="text-xs text-muted-foreground truncate">
                          {field.description}
                        </span>
                      )}
                    </div>
                  </CommandItem>
                )}
              />
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
