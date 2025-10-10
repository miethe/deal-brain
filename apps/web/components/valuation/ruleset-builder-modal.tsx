"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { useToast } from "../ui/use-toast";
import { Checkbox } from "../ui/checkbox";

import { createRuleset } from "../../lib/api/rules";

interface RulesetBuilderModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function RulesetBuilderModal({ open, onOpenChange, onSuccess }: RulesetBuilderModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [version, setVersion] = useState("1.0.0");
  const [priority, setPriority] = useState(10);
  const [isActive, setIsActive] = useState(true);

  const { toast } = useToast();
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: () =>
      createRuleset({
        name,
        description,
        version,
        priority,
        is_active: isActive,
      }),
    onSuccess: () => {
      toast({
        title: "Ruleset created",
        description: "The ruleset has been created successfully",
      });
      resetForm();
      onOpenChange(false);
      onSuccess();
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const resetForm = () => {
    setName("");
    setDescription("");
    setVersion("1.0.0");
    setPriority(10);
    setIsActive(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Ruleset</DialogTitle>
          <DialogDescription>
            Create a new collection of valuation rules
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 py-4">
          <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Ruleset Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Gaming PC Valuation Q4 2025"
              required
            />
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe this ruleset..."
              rows={3}
            />
          </div>

          <div>
            <Label htmlFor="version">Version</Label>
            <Input
              id="version"
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              placeholder="1.0.0"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="priority">Priority</Label>
              <Input
                id="priority"
                type="number"
                min={0}
                value={priority}
                onChange={(e) => setPriority(Number.parseInt(e.target.value, 10) || 0)}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Lower values evaluate before higher ones.
              </p>
            </div>
            <div className="flex items-center gap-2 pt-6">
              <Checkbox
                id="isActive"
                checked={isActive}
                onCheckedChange={(checked) => setIsActive(checked === true)}
              />
              <Label htmlFor="isActive" className="cursor-pointer select-none">
                Active
              </Label>
            </div>
          </div>

            <DialogFooter className="px-6 py-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!name}>
                Create Ruleset
              </Button>
            </DialogFooter>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
