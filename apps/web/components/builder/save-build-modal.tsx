"use client";

import { useState } from "react";
import { useBuilder } from "./builder-provider";
import {
  saveBuild,
  type SaveBuildRequest,
  type BuildVisibility,
} from "@/lib/api/builder";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";

interface SaveBuildModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved?: () => void;
}

export function SaveBuildModal({
  open,
  onOpenChange,
  onSaved,
}: SaveBuildModalProps) {
  const { state } = useBuilder();
  const { toast } = useToast();
  const [name, setName] = useState("");
  const [visibility, setVisibility] = useState<BuildVisibility>("private");
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) {
      toast({
        title: "Name required",
        description: "Please enter a name for your build",
        variant: "destructive",
      });
      return;
    }

    if (!state.components.cpu_id) {
      toast({
        title: "CPU required",
        description: "Please select a CPU before saving",
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);
    try {
      const components: SaveBuildRequest["components"] = {
        cpu_id: state.components.cpu_id!,
      };

      if (state.components.gpu_id) {
        components.gpu_id = state.components.gpu_id;
      }
      if (state.components.ram_spec_id) {
        components.ram_spec_id = state.components.ram_spec_id;
      }
      if (state.components.storage_spec_id) {
        components.storage_spec_id = state.components.storage_spec_id;
      }
      if (state.components.psu_spec_id) {
        components.psu_spec_id = state.components.psu_spec_id;
      }
      if (state.components.case_spec_id) {
        components.case_spec_id = state.components.case_spec_id;
      }

      const buildData: SaveBuildRequest = {
        name: name.trim(),
        components,
        visibility,
      };

      await saveBuild(buildData);

      toast({
        title: "Build saved!",
        description: `"${name}" has been saved successfully`,
      });

      onSaved?.();
      onOpenChange(false);

      // Reset form
      setName("");
      setVisibility("private");
    } catch (error) {
      toast({
        title: "Save failed",
        description: error instanceof Error ? error.message : "Failed to save build",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Save Build</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Build Name *</Label>
            <Input
              id="name"
              placeholder="My Gaming PC"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={255}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="visibility">Visibility</Label>
            <Select
              value={visibility}
              onValueChange={(value) => setVisibility(value as BuildVisibility)}
            >
              <SelectTrigger id="visibility">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="private">Private (only you)</SelectItem>
                <SelectItem value="public">Public (shareable link)</SelectItem>
                <SelectItem value="unlisted">Unlisted (link required)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? "Saving..." : "Save Build"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
