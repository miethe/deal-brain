"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Check, Copy, Download, ExternalLink, Eye } from "lucide-react";
import { VisibilityToggle } from "./visibility-toggle";
import { VisibilityBadge } from "./visibility-badge";
import type { Collection } from "@/types/collections";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

interface ShareModalProps {
  collection: Collection;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onVisibilityChange?: (visibility: Collection) => void;
}

/**
 * Share Modal Component
 *
 * Modal for sharing collections with:
 * - Copy-to-clipboard link functionality
 * - Visibility selector
 * - Export option
 * - Share preview
 */
export function ShareModal({
  collection,
  open,
  onOpenChange,
  onVisibilityChange,
}: ShareModalProps) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const shareUrl = collection.share_url || `${window.location.origin}/collections/${collection.id}`;
  const isShareable = collection.visibility !== "private";

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      toast({
        title: "Link copied",
        description: "Share link has been copied to clipboard.",
      });

      // Reset copied state after 2 seconds
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        title: "Failed to copy",
        description: "Could not copy link to clipboard.",
        variant: "destructive",
      });
    }
  };

  const handleExport = () => {
    // Trigger export by navigating to export endpoint
    const exportUrl = `/api/v1/collections/${collection.id}/export`;
    window.open(exportUrl, "_blank");
  };

  const handleViewPublic = () => {
    window.open(shareUrl, "_blank");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Share Collection</DialogTitle>
          <DialogDescription>
            Share "{collection.name}" with others or export the data
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Visibility Selector */}
          <div className="space-y-3">
            <Label>Visibility</Label>
            <VisibilityToggle
              collectionId={collection.id}
              currentVisibility={collection.visibility}
              onVisibilityChange={(visibility) => {
                onVisibilityChange?.({ ...collection, visibility });
              }}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              {collection.visibility === "private" && (
                "Change to unlisted or public to generate a shareable link"
              )}
              {collection.visibility === "unlisted" && (
                "Only people with the link can access this collection"
              )}
              {collection.visibility === "public" && (
                "Anyone can discover and view this collection"
              )}
            </p>
          </div>

          {/* Shareable Link */}
          {isShareable && (
            <>
              <Separator />
              <div className="space-y-3">
                <Label htmlFor="share-link">Shareable Link</Label>
                <div className="flex gap-2">
                  <Input
                    id="share-link"
                    value={shareUrl}
                    readOnly
                    className="font-mono text-sm"
                    onClick={(e) => e.currentTarget.select()}
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={handleCopyLink}
                    aria-label="Copy link"
                  >
                    {copied ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>

                {/* View Count */}
                {collection.view_count !== undefined && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Eye className="w-4 h-4" />
                    <span>
                      {collection.view_count} {collection.view_count === 1 ? "view" : "views"}
                    </span>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Share Preview */}
          {isShareable && (
            <>
              <Separator />
              <div className="space-y-3">
                <Label>Preview</Label>
                <div className="rounded-lg border bg-muted/50 p-4 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-sm truncate">
                        {collection.name}
                      </h4>
                      {collection.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                          {collection.description}
                        </p>
                      )}
                    </div>
                    <VisibilityBadge visibility={collection.visibility} />
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>
                      {collection.item_count} {collection.item_count === 1 ? "item" : "items"}
                    </span>
                    {collection.owner_name && (
                      <span>By {collection.owner_name}</span>
                    )}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleViewPublic}
                  className="w-full"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View as public
                </Button>
              </div>
            </>
          )}

          {/* Export Option */}
          <Separator />
          <div className="space-y-3">
            <Label>Export</Label>
            <Button
              variant="outline"
              onClick={handleExport}
              className="w-full"
            >
              <Download className="w-4 h-4 mr-2" />
              Export Collection Data
            </Button>
            <p className="text-xs text-muted-foreground">
              Download all items and metadata as JSON
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
