"use client";

import * as React from "react";
import { Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ShareModal } from "./share-modal";

interface ShareButtonProps {
  listingId: number;
  listingName: string;
  variant?: "default" | "ghost" | "outline" | "secondary";
  size?: "default" | "sm" | "lg" | "icon";
  className?: string;
}

/**
 * Share button that opens the share modal
 * Can be placed in listing cards, detail pages, etc.
 */
export function ShareButton({
  listingId,
  listingName,
  variant = "ghost",
  size = "sm",
  className,
}: ShareButtonProps) {
  const [open, setOpen] = React.useState(false);

  return (
    <>
      <Button
        variant={variant}
        size={size}
        onClick={() => setOpen(true)}
        className={className}
        aria-label={`Share ${listingName}`}
      >
        <Share2 className="h-4 w-4" />
        {size !== "icon" && <span className="ml-2">Share</span>}
      </Button>

      <ShareModal
        open={open}
        onOpenChange={setOpen}
        listingId={listingId}
        listingName={listingName}
      />
    </>
  );
}
