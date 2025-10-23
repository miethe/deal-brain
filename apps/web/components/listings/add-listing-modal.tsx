"use client";

import { useState, memo } from "react";
import { Maximize2, Minimize2, X } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Button } from "../ui/button";
import { AddListingForm } from "./add-listing-form";

interface AddListingModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (listingId: number) => void;
}

function AddListingModalComponent({ open, onOpenChange, onSuccess }: AddListingModalProps) {
  const [expanded, setExpanded] = useState(false);

  const handleSuccess = (listingId: number) => {
    if (onSuccess) {
      onSuccess(listingId);
    }
    onOpenChange(false);
    setExpanded(false);
  };

  if (expanded) {
    // Full-screen mode
    return (
      <div className="fixed inset-0 z-50 bg-background transition-all duration-200">
        <div className="flex h-full flex-col">
          <div className="border-b px-6 py-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Add New Listing</h2>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpanded(false)}
                aria-label="Collapse to modal"
                className="h-8 w-8 p-0"
              >
                <Minimize2 className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onOpenChange(false)}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="flex-1 overflow-auto p-6">
            <AddListingForm onSuccess={handleSuccess} />
          </div>
        </div>
      </div>
    );
  }

  // Modal mode
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <DialogTitle>Add New Listing</DialogTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(true)}
            aria-label="Expand to full screen"
            className="h-8 w-8 p-0 ml-auto"
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </DialogHeader>

        <div className="flex-1 overflow-auto -mx-6 px-6">
          <AddListingForm onSuccess={handleSuccess} />
        </div>
      </DialogContent>
    </Dialog>
  );
}

export const AddListingModal = memo(AddListingModalComponent);
