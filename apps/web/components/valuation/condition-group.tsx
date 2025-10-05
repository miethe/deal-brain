"use client";

import { useState } from "react";
import { Plus, X, GripVertical } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { ConditionRow } from "./condition-row";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

interface ConditionGroupProps {
  conditions: any[];
  onConditionsChange: (conditions: any[]) => void;
  depth?: number; // Nesting level for visual indentation
}

// Sortable wrapper for individual conditions
function SortableCondition({
  id,
  condition,
  index,
  updateCondition,
  removeCondition,
  depth
}: {
  id: string;
  condition: any;
  index: number;
  updateCondition: (index: number, updates: any) => void;
  removeCondition: (index: number) => void;
  depth: number;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className="flex gap-2">
      <div className="flex items-center" {...attributes} {...listeners}>
        <GripVertical className="h-4 w-4 text-muted-foreground cursor-move" />
      </div>

      {condition.is_group ? (
        <div className="flex-1 rounded-lg border-2 border-dashed border-primary/20 p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium">Condition Group</span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => removeCondition(index)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <ConditionGroup
            conditions={condition.children || []}
            onConditionsChange={(children) =>
              updateCondition(index, { children })
            }
            depth={depth + 1}
          />
        </div>
      ) : (
        <div className="flex-1">
          <ConditionRow
            condition={condition}
            onChange={(updates) => updateCondition(index, updates)}
            onRemove={() => removeCondition(index)}
          />
        </div>
      )}
    </div>
  );
}

export function ConditionGroup({ conditions, onConditionsChange, depth = 0 }: ConditionGroupProps) {
  const [logicalOperator, setLogicalOperator] = useState<"AND" | "OR">("AND");

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const addCondition = () => {
    onConditionsChange([
      ...conditions,
      {
        id: `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        field_name: "",
        operator: "equals",
        value: "",
        logical_operator: logicalOperator,
      },
    ]);
  };

  const addGroup = () => {
    onConditionsChange([
      ...conditions,
      {
        id: `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        is_group: true,
        logical_operator: "OR",
        children: [],
      },
    ]);
  };

  const updateCondition = (index: number, updates: any) => {
    const newConditions = [...conditions];
    newConditions[index] = { ...newConditions[index], ...updates };
    onConditionsChange(newConditions);
  };

  const removeCondition = (index: number) => {
    onConditionsChange(conditions.filter((_, i) => i !== index));
  };

  const toggleLogicalOperator = () => {
    const newOp = logicalOperator === "AND" ? "OR" : "AND";
    setLogicalOperator(newOp);
    // Update all conditions in this group
    onConditionsChange(
      conditions.map((c) => ({ ...c, logical_operator: newOp }))
    );
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = conditions.findIndex((c) => c.id === active.id);
      const newIndex = conditions.findIndex((c) => c.id === over.id);

      onConditionsChange(arrayMove(conditions, oldIndex, newIndex));
    }
  };

  return (
    <div
      className="space-y-2"
      style={{ paddingLeft: depth * 24 }}
    >
      {/* Logical Operator Toggle */}
      {conditions.length > 1 && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Join with:</span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={toggleLogicalOperator}
          >
            <Badge variant={logicalOperator === "AND" ? "default" : "secondary"}>
              {logicalOperator}
            </Badge>
          </Button>
        </div>
      )}

      {/* Conditions */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={conditions.map((c) => c.id)}
          strategy={verticalListSortingStrategy}
        >
          {conditions.map((condition, index) => (
            <SortableCondition
              key={condition.id}
              id={condition.id}
              condition={condition}
              index={index}
              updateCondition={updateCondition}
              removeCondition={removeCondition}
              depth={depth}
            />
          ))}
        </SortableContext>
      </DndContext>

      {/* Add Buttons */}
      <div className="flex gap-2">
        <Button type="button" variant="outline" size="sm" onClick={addCondition}>
          <Plus className="mr-2 h-4 w-4" />
          Add Condition
        </Button>
        {depth < 2 && ( // Limit nesting to 2 levels
          <Button type="button" variant="outline" size="sm" onClick={addGroup}>
            <Plus className="mr-2 h-4 w-4" />
            Add Group
          </Button>
        )}
      </div>
    </div>
  );
}
