"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronsUpDown } from "lucide-react";

import { Button } from "../ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "../ui/command";
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

  const { data: metadata } = useQuery({
    queryKey: ["entities-metadata"],
    queryFn: fetchEntitiesMetadata,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Flatten entities and fields for searchable list
  const allFields = metadata?.entities.flatMap((entity) =>
    entity.fields.map((field) => ({
      key: `${entity.key}.${field.key}`,
      label: `${entity.label} → ${field.label}`,
      data_type: field.data_type,
      options: field.options,
      entity: entity.label,
      field: field.label,
    }))
  ) || [];

  const selectedField = allFields.find((f) => f.key === value);

  const handleSelect = (fieldKey: string) => {
    const field = allFields.find((f) => f.key === fieldKey);
    if (field) {
      onChange(fieldKey, field.data_type, field.options);
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
          {selectedField ? selectedField.label : placeholder || "Select field..."}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0">
        <Command>
          <CommandInput placeholder="Search fields..." value={searchQuery} onValueChange={setSearchQuery} />
          <CommandEmpty>No field found.</CommandEmpty>
          {metadata?.entities.map((entity) => (
            <CommandGroup key={entity.key} heading={entity.label}>
              {entity.fields
                .filter((field) =>
                  field.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  field.key.toLowerCase().includes(searchQuery.toLowerCase())
                )
                .map((field) => {
                  const fieldKey = `${entity.key}.${field.key}`;
                  return (
                    <CommandItem
                      key={fieldKey}
                      value={fieldKey}
                      onSelect={handleSelect}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          value === fieldKey ? "opacity-100" : "opacity-0"
                        )}
                      />
                      <div>
                        <div>{field.label}</div>
                        {field.description && (
                          <div className="text-xs text-muted-foreground">{field.description}</div>
                        )}
                      </div>
                    </CommandItem>
                  );
                })}
            </CommandGroup>
          ))}
        </Command>
      </PopoverContent>
    </Popover>
  );
}
