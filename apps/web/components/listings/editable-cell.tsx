"use client";

import * as React from "react";
import { ComboBox, type ComboBoxOption } from "../forms/combobox";
import { Input } from "../ui/input";
import { useToast } from "../ui/use-toast";
import { useConfirmation } from "../ui/confirmation-dialog";

interface EditableCellProps {
  value: any;
  fieldKey: string;
  fieldType: string;
  options?: string[];
  onSave: (value: any) => Promise<void>;
  onCreateOption?: (value: string) => Promise<void>;
}

const RAM_OPTIONS = [4, 8, 16, 24, 32, 48, 64, 96, 128].map((gb) => ({
  label: `${gb} GB`,
  value: String(gb),
}));

const STORAGE_OPTIONS = [128, 256, 512, 1024, 2048, 4096].map((gb) => ({
  label: `${gb} GB`,
  value: String(gb),
}));

const STORAGE_TYPE_OPTIONS = [
  { label: "HDD", value: "HDD" },
  { label: "SSD", value: "SSD" },
  { label: "NVMe", value: "NVMe" },
  { label: "eMMC", value: "eMMC" },
];

function getOptionsForField(fieldKey: string): ComboBoxOption[] {
  switch (fieldKey) {
    case "ram_gb":
      return RAM_OPTIONS;
    case "primary_storage_gb":
    case "secondary_storage_gb":
      return STORAGE_OPTIONS;
    case "storage_type":
      return STORAGE_TYPE_OPTIONS;
    default:
      return [];
  }
}

const DROPDOWN_FIELDS = ["ram_gb", "primary_storage_gb", "secondary_storage_gb", "storage_type"];

export function EditableCell({
  value,
  fieldKey,
  fieldType,
  options,
  onSave,
  onCreateOption,
}: EditableCellProps) {
  const [isEditing, setIsEditing] = React.useState(false);
  const [editValue, setEditValue] = React.useState(String(value ?? ""));
  const [isSaving, setIsSaving] = React.useState(false);
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmation();

  const isDropdownField = DROPDOWN_FIELDS.includes(fieldKey);
  const fieldOptions = isDropdownField ? getOptionsForField(fieldKey) : options?.map(opt => ({ label: String(opt), value: String(opt) })) || [];

  const handleSave = async () => {
    if (editValue === String(value ?? "")) {
      setIsEditing(false);
      return;
    }

    setIsSaving(true);
    try {
      await onSave(editValue);
      setIsEditing(false);
      toast({
        title: "Success",
        description: "Field updated successfully",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update field",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateOption = async (newValue: string) => {
    if (!onCreateOption) return;

    const confirmed = await confirm({
      title: `Add "${newValue}" to ${fieldKey}?`,
      description: "This will add the option to Global Fields and make it available everywhere.",
      confirmText: "Add Option",
      onConfirm: () => {},
    });

    if (!confirmed) {
      throw new Error("User cancelled");
    }

    try {
      await onCreateOption(newValue);
      toast({
        title: "Success",
        description: `Added "${newValue}" to ${fieldKey}`,
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create option",
      });
      throw error;
    }
  };

  if (!isEditing) {
    return (
      <div
        className="cursor-pointer hover:bg-accent/50 rounded px-2 py-1 -mx-2 -my-1"
        onClick={() => setIsEditing(true)}
      >
        {value ?? <span className="text-muted-foreground italic">Empty</span>}
      </div>
    );
  }

  if (isDropdownField || (fieldType === "enum" && fieldOptions.length > 0)) {
    return (
      <>
        <ComboBox
          options={fieldOptions}
          value={editValue}
          onChange={(newValue) => {
            setEditValue(newValue);
            setIsEditing(false);
            onSave(newValue);
          }}
          allowCustom={!!onCreateOption}
          onCreateOption={onCreateOption ? handleCreateOption : undefined}
          placeholder="Select value..."
        />
        {dialog}
      </>
    );
  }

  return (
    <Input
      value={editValue}
      onChange={(e) => setEditValue(e.target.value)}
      onBlur={handleSave}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          handleSave();
        } else if (e.key === "Escape") {
          setEditValue(String(value ?? ""));
          setIsEditing(false);
        }
      }}
      disabled={isSaving}
      autoFocus
      className="h-8"
    />
  );
}
