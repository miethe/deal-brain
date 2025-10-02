"use client";

import { useState } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Plus, X } from "lucide-react";

import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";

interface DropdownOptionsBuilderProps {
  options: string[];
  onChange: (options: string[]) => void;
}

function SortableOption({
  option,
  onRemove,
}: {
  option: string;
  onRemove: () => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: option });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center gap-2 rounded-md border bg-background px-3 py-2"
    >
      <div
        {...attributes}
        {...listeners}
        className="cursor-grab active:cursor-grabbing"
      >
        <GripVertical className="h-4 w-4 text-muted-foreground" />
      </div>
      <span className="flex-1 text-sm">{option}</span>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={onRemove}
        className="h-auto p-1"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}

export function DropdownOptionsBuilder({
  options,
  onChange,
}: DropdownOptionsBuilderProps) {
  const [newOption, setNewOption] = useState("");
  const [error, setError] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = options.indexOf(String(active.id));
      const newIndex = options.indexOf(String(over.id));
      onChange(arrayMove(options, oldIndex, newIndex));
    }
  };

  const handleAddOption = () => {
    const trimmed = newOption.trim();

    if (!trimmed) {
      setError("Option cannot be empty");
      return;
    }

    if (options.includes(trimmed)) {
      setError("Option already exists");
      return;
    }

    onChange([...options, trimmed]);
    setNewOption("");
    setError(null);
  };

  const handleRemoveOption = (index: number) => {
    onChange(options.filter((_, i) => i !== index));
  };

  const handleImportCSV = () => {
    const csv = prompt("Paste comma-separated values:");
    if (!csv) return;

    const imported = csv
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    // Merge with existing options, removing duplicates
    const unique = Array.from(new Set([...options, ...imported]));
    onChange(unique);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddOption();
    }
  };

  return (
    <div className="space-y-3">
      <Label>Options</Label>

      {/* Current options list */}
      <div className="space-y-2">
        {options.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No options yet. Add options below.
          </p>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={options}
              strategy={verticalListSortingStrategy}
            >
              {options.map((option, index) => (
                <SortableOption
                  key={option}
                  option={option}
                  onRemove={() => handleRemoveOption(index)}
                />
              ))}
            </SortableContext>
          </DndContext>
        )}
      </div>

      {/* Add new option */}
      <div className="grid gap-2">
        <div className="flex gap-2">
          <Input
            value={newOption}
            onChange={(e) => {
              setNewOption(e.target.value);
              if (error) setError(null);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Add option..."
            className={error ? "border-destructive" : ""}
          />
          <Button type="button" onClick={handleAddOption} size="sm">
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      {/* Import CSV */}
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={handleImportCSV}
      >
        Import from CSV
      </Button>

      {/* Validation */}
      {options.length === 0 && (
        <p className="text-sm text-destructive">
          At least one option is required for dropdown fields
        </p>
      )}
    </div>
  );
}
