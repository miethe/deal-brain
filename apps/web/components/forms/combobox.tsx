"use client";

import * as React from "react";
import { Check, ChevronsUpDown, Plus } from "lucide-react";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "cmdk";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";

export interface ComboBoxOption {
  label: string;
  value: string;
}

interface ComboBoxProps {
  options: ComboBoxOption[];
  value: string;
  onChange: (value: string) => void;
  onCreateOption?: (value: string) => Promise<void>;
  placeholder?: string;
  allowCustom?: boolean;
  disabled?: boolean;
  className?: string;
}

export function ComboBox({
  options,
  value,
  onChange,
  onCreateOption,
  placeholder = "Select option...",
  allowCustom = false,
  disabled = false,
  className,
}: ComboBoxProps) {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const [creating, setCreating] = React.useState(false);

  const selectedOption = options.find((option) => option.value === value);

  const filteredOptions = React.useMemo(() => {
    if (!search) return options;
    return options.filter(
      (option) =>
        option.label.toLowerCase().includes(search.toLowerCase()) ||
        option.value.toLowerCase().includes(search.toLowerCase())
    );
  }, [options, search]);

  const showCreateOption =
    allowCustom &&
    onCreateOption &&
    search &&
    !filteredOptions.some(
      (option) => option.label.toLowerCase() === search.toLowerCase()
    );

  const handleSelect = (selectedValue: string) => {
    onChange(selectedValue === value ? "" : selectedValue);
    setOpen(false);
    setSearch("");
  };

  const handleCreateOption = async () => {
    if (!search || !onCreateOption) return;

    setCreating(true);
    try {
      await onCreateOption(search);
      onChange(search);
      setOpen(false);
      setSearch("");
    } catch (error) {
      console.error("Failed to create option:", error);
    } finally {
      setCreating(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("w-full justify-between", className)}
          disabled={disabled}
        >
          {selectedOption ? selectedOption.label : placeholder}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Search..."
            value={search}
            onValueChange={setSearch}
          />
          <CommandEmpty>
            {showCreateOption ? (
              <button
                onClick={handleCreateOption}
                disabled={creating}
                className="flex w-full items-center gap-2 px-2 py-1.5 text-sm hover:bg-accent"
              >
                <Plus className="h-4 w-4" />
                {creating ? "Creating..." : `Create "${search}"`}
              </button>
            ) : (
              <span className="py-6 text-center text-sm">No options found.</span>
            )}
          </CommandEmpty>
          <CommandGroup className="max-h-64 overflow-y-auto">
            {filteredOptions.map((option) => (
              <CommandItem
                key={option.value}
                value={option.value}
                onSelect={handleSelect}
              >
                <Check
                  className={cn(
                    "mr-2 h-4 w-4",
                    value === option.value ? "opacity-100" : "opacity-0"
                  )}
                />
                {option.label}
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
