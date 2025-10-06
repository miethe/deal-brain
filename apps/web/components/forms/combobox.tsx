"use client";

import * as React from "react";
import { Check, ChevronsUpDown, Plus } from "lucide-react";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "cmdk";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";
import { calculateDropdownWidth } from "../../lib/dropdown-utils";
import { useDebounce } from "use-debounce";

export interface ComboBoxOption {
  label: string;
  value: string;
}

interface ComboBoxProps {
  options: ComboBoxOption[];
  value: string;
  onChange: (value: string) => void;
  onCreateOption?: (value: string) => Promise<void>;
  fieldId?: number; // For automatic option creation via API
  fieldName?: string; // For confirmation dialog display
  placeholder?: string;
  allowCustom?: boolean;
  enableInlineCreate?: boolean;
  disabled?: boolean;
  className?: string;
}

export function ComboBox({
  options,
  value,
  onChange,
  onCreateOption,
  fieldId,
  fieldName,
  placeholder = "Select option...",
  allowCustom = false,
  enableInlineCreate = true,
  disabled = false,
  className,
}: ComboBoxProps) {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const [creating, setCreating] = React.useState(false);

  // Debounce search input to reduce filtering operations (200ms delay)
  const [debouncedSearch] = useDebounce(search, 200);

  const selectedOption = options.find((option) => option.value === value);

  // Calculate dropdown width based on longest option
  const dropdownWidth = React.useMemo(
    () => calculateDropdownWidth(options.map((o) => o.label)),
    [options]
  );

  const filteredOptions = React.useMemo(() => {
    if (!debouncedSearch) return options;
    return options.filter(
      (option) =>
        option.label.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
        option.value.toLowerCase().includes(debouncedSearch.toLowerCase())
    );
  }, [options, debouncedSearch]);

  // Show create option when search doesn't exactly match any existing option
  const showCreateOption =
    enableInlineCreate &&
    onCreateOption &&
    search &&
    !filteredOptions.some(
      (option) => option.label.toLowerCase() === search.toLowerCase()
    );

  // Calculate dynamic max height based on number of options (min 2, max 10 items visible)
  const itemHeight = 40; // py-2.5 + borders
  const visibleItems = Math.min(Math.max(filteredOptions.length, 2), 10);
  const maxHeight = visibleItems * itemHeight;

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
            "justify-between h-9 px-3 font-normal",
            !selectedOption && "text-muted-foreground",
            className
          )}
          style={{ width: `${dropdownWidth}px`, minWidth: "120px" }}
          disabled={disabled}
        >
          <span className="truncate">{selectedOption ? selectedOption.label : placeholder}</span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="p-0"
        align="start"
        style={{ width: `${dropdownWidth}px` }}
      >
        <Command shouldFilter={false}>
          <CommandInput
            placeholder=""
            value={search}
            onValueChange={setSearch}
            className="h-9 border-0 border-b bg-transparent px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus:ring-0"
          />
          {filteredOptions.length === 0 && !showCreateOption ? (
            <div className="py-6 text-center text-sm text-muted-foreground">
              No options found.
            </div>
          ) : (
            <CommandGroup
              className="overflow-y-auto p-1"
              style={{ maxHeight: `${maxHeight}px` }}
            >
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
              {showCreateOption && (
                <div className="border-t mt-1 pt-1">
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
                </div>
              )}
            </CommandGroup>
          )}
        </Command>
      </PopoverContent>
    </Popover>
  );
}
