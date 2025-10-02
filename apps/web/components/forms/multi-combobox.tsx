"use client";

import * as React from "react";
import { Check, ChevronsUpDown, Plus, X } from "lucide-react";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "cmdk";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { cn } from "../../lib/utils";
import { ComboBoxOption } from "./combobox";

interface MultiComboBoxProps {
  options: ComboBoxOption[];
  value: string[];
  onChange: (values: string[]) => void;
  onCreateOption?: (value: string) => Promise<void>;
  placeholder?: string;
  allowCustom?: boolean;
  disabled?: boolean;
  className?: string;
}

export function MultiComboBox({
  options,
  value,
  onChange,
  onCreateOption,
  placeholder = "Select options...",
  allowCustom = false,
  disabled = false,
  className,
}: MultiComboBoxProps) {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const [creating, setCreating] = React.useState(false);

  const selectedOptions = options.filter((option) => value.includes(option.value));

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
    const newValue = value.includes(selectedValue)
      ? value.filter((v) => v !== selectedValue)
      : [...value, selectedValue];
    onChange(newValue);
  };

  const handleRemove = (valueToRemove: string, e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(value.filter((v) => v !== valueToRemove));
  };

  const handleCreateOption = async () => {
    if (!search || !onCreateOption) return;

    setCreating(true);
    try {
      await onCreateOption(search);
      onChange([...value, search]);
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
          <div className="flex flex-1 flex-wrap gap-1">
            {selectedOptions.length > 0 ? (
              selectedOptions.map((option) => (
                <Badge key={option.value} variant="secondary" className="mr-1">
                  {option.label}
                  <button
                    className="ml-1 rounded-full outline-none ring-offset-background focus:ring-2 focus:ring-ring focus:ring-offset-2"
                    onMouseDown={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                    }}
                    onClick={(e) => handleRemove(option.value, e)}
                  >
                    <X className="h-3 w-3 text-muted-foreground hover:text-foreground" />
                  </button>
                </Badge>
              ))
            ) : (
              <span className="text-muted-foreground">{placeholder}</span>
            )}
          </div>
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
                    value.includes(option.value) ? "opacity-100" : "opacity-0"
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
