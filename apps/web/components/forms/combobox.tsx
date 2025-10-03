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
          className={cn(
            "w-full justify-between h-9 px-3 font-normal",
            !selectedOption && "text-muted-foreground",
            className
          )}
          disabled={disabled}
        >
          <span className="truncate">{selectedOption ? selectedOption.label : placeholder}</span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Search..."
            value={search}
            onValueChange={setSearch}
            className="h-9"
          />
          <CommandEmpty>
            {showCreateOption ? (
              <button
                onClick={handleCreateOption}
                disabled={creating}
                className="flex w-full items-center gap-2 px-3 py-2.5 text-sm transition-colors hover:bg-accent hover:text-accent-foreground cursor-pointer rounded-sm"
              >
                <Plus className="h-4 w-4 shrink-0" />
                <span className="flex-1 text-left">
                  {creating ? "Creating..." : `Create "${search}"`}
                </span>
              </button>
            ) : (
              <div className="py-6 text-center text-sm text-muted-foreground">
                No options found.
              </div>
            )}
          </CommandEmpty>
          <CommandGroup className="max-h-64 overflow-y-auto p-1">
            {filteredOptions.map((option) => (
              <CommandItem
                key={option.value}
                value={option.value}
                onSelect={handleSelect}
                className="flex items-center gap-2 px-3 py-2.5 cursor-pointer rounded-sm transition-colors hover:bg-accent hover:text-accent-foreground aria-selected:bg-accent aria-selected:text-accent-foreground"
              >
                <Check
                  className={cn(
                    "h-4 w-4 shrink-0",
                    value === option.value ? "opacity-100" : "opacity-0"
                  )}
                />
                <span className="flex-1">{option.label}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
