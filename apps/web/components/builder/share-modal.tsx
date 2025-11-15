"use client";

import { useState } from "react";
import type { SavedBuild } from "@/lib/api/builder";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Check, Copy } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface ShareModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  build: SavedBuild;
}

export function ShareModal({ open, onOpenChange, build }: ShareModalProps) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const shareUrl =
    typeof window !== "undefined" && build.share_token
      ? `${window.location.origin}/builder/shared/${build.share_token}`
      : "";

  const handleCopy = async () => {
    if (!shareUrl) {
      toast({
        title: "Cannot share",
        description: "This build does not have a share token",
        variant: "destructive",
      });
      return;
    }

    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      toast({
        title: "Link copied!",
        description: "Share link copied to clipboard",
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        title: "Failed to copy",
        description: "Could not copy link to clipboard",
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Share Build</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {shareUrl ? (
            <div>
              <p className="text-sm text-muted-foreground mb-2">
                Anyone with this link can view your build
              </p>
              <div className="flex gap-2">
                <Input value={shareUrl} readOnly className="flex-1" />
                <Button onClick={handleCopy} size="icon">
                  {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-800">
                <strong>Note:</strong> This build does not have a share token. Try saving it as
                public to enable sharing.
              </p>
            </div>
          )}

          {build.visibility === "private" && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-800">
                <strong>Note:</strong> This build is private. Change visibility to "Public" to
                share it.
              </p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
