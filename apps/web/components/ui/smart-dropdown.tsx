"use client";

import { useState, useRef, useEffect } from "react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Command, CommandGroup, CommandItem } from "@/components/ui/command";
import { Check, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface SmartDropdownProps {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export function SmartDropdown({
  value,
  onChange,
  options,
  placeholder = "Select...",
  className,
  disabled = false,
}: SmartDropdownProps) {
  const [open, setOpen] = useState(false);
  const [dropdownWidth, setDropdownWidth] = useState(200);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // Calculate optimal dropdown width
  useEffect(() => {
    if (!options.length) return;

    const longestOption = options.reduce((max, opt) =>
      opt.label.length > max.label.length ? opt : max
    , options[0]);

    // Measure text width using hidden span
    const span = document.createElement("span");
    span.style.cssText = "position:absolute;visibility:hidden;white-space:nowrap;font:14px system-ui";
    span.textContent = longestOption.label;
    document.body.appendChild(span);

    const textWidth = span.offsetWidth;
    document.body.removeChild(span);

    // Calculate final width
    const triggerWidth = triggerRef.current?.offsetWidth || 0;
    const calculatedWidth = Math.max(
      200,  // min width
      triggerWidth,  // at least as wide as trigger
      textWidth + 64  // text + padding + icons
    );
    const finalWidth = Math.min(calculatedWidth, 400);  // max width

    setDropdownWidth(finalWidth);
  }, [options]);

  const selectedOption = options.find(opt => opt.value === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          ref={triggerRef}
          className={cn(
            "flex h-9 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background",
            "focus:outline-none focus:ring-1 focus:ring-ring",
            "disabled:cursor-not-allowed disabled:opacity-50",
            className
          )}
          aria-expanded={open}
          disabled={disabled}
        >
          <span className="truncate">
            {selectedOption?.label || placeholder}
          </span>
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        className="p-0"
        style={{ width: `${dropdownWidth}px` }}
        align="start"
        sideOffset={4}
      >
        <Command>
          <CommandGroup className="max-h-[300px] overflow-auto">
            {options.map((option) => (
              <CommandItem
                key={option.value}
                value={option.value}
                onSelect={() => {
                  onChange(option.value);
                  setOpen(false);
                }}
                className="flex items-center justify-between px-3 py-2"
              >
                <span>{option.label}</span>
                {value === option.value && (
                  <Check className="h-4 w-4 text-primary" />
                )}
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
