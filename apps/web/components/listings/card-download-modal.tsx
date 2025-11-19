"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Download, Loader2, Image as ImageIcon, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { API_URL, cn } from "@/lib/utils";
import type { ListingDetail } from "@/types/listing-detail";

interface CardDownloadModalProps {
  listing: ListingDetail;
  trigger?: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

type CardStyle = "light" | "dark";
type CardSize = "social" | "instagram" | "story";
type CardFormat = "png" | "jpeg";

interface CardOptions {
  style: CardStyle;
  size: CardSize;
  format: CardFormat;
}

const CARD_SIZES = {
  social: { width: 1200, height: 630, label: "Social (1200×630)" },
  instagram: { width: 1080, height: 1080, label: "Instagram (1080×1080)" },
  story: { width: 1080, height: 1920, label: "Story (1080×1920)" },
} as const;

const CARD_STYLES = {
  light: { label: "Light", preview: "bg-white text-black" },
  dark: { label: "Dark", preview: "bg-slate-900 text-white" },
} as const;

const CARD_FORMATS = {
  png: { label: "PNG (Lossless)", extension: "png" },
  jpeg: { label: "JPEG (Compressed)", extension: "jpg" },
} as const;

/**
 * Card Download Modal Component
 *
 * Modal for downloading listing card images with:
 * - Style selector (Light/Dark)
 * - Size selector (Social/Instagram/Story)
 * - Format selector (PNG/JPEG)
 * - Preview thumbnail
 * - Download functionality with loading states
 */
export function CardDownloadModal({
  listing,
  trigger,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
}: CardDownloadModalProps) {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  // Support both controlled and uncontrolled mode
  const open = controlledOpen !== undefined ? controlledOpen : uncontrolledOpen;
  const setOpen = controlledOnOpenChange || setUncontrolledOpen;

  const [options, setOptions] = useState<CardOptions>({
    style: "light",
    size: "social",
    format: "png",
  });

  const handleDownload = async () => {
    try {
      setIsGenerating(true);
      setError(null);

      // Build query params
      const params = new URLSearchParams({
        style: options.style,
        width: CARD_SIZES[options.size].width.toString(),
        height: CARD_SIZES[options.size].height.toString(),
        format: options.format,
      });

      // Fetch the card image
      const response = await fetch(
        `${API_URL}/v1/listings/${listing.id}/card-image?${params.toString()}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: "Failed to generate card image",
        }));
        throw new Error(errorData.detail || "Failed to generate card image");
      }

      // Get filename from Content-Disposition header or create one
      const contentDisposition = response.headers.get("Content-Disposition");
      const listingTitle = listing.title
        .replace(/[^a-zA-Z0-9-_]/g, "-")
        .substring(0, 50);
      const date = new Date().toISOString().split("T")[0];
      const extension = CARD_FORMATS[options.format].extension;
      let filename = `card-${listingTitle}-${date}.${extension}`;

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Card downloaded",
        description: `Downloaded ${filename}`,
      });

      // Close modal after successful download
      setOpen(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setError(errorMessage);
      toast({
        title: "Download failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const defaultTrigger = (
    <Button variant="outline" size="sm">
      <ImageIcon className="h-4 w-4 mr-2" />
      Download Card
    </Button>
  );

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {trigger ? <DialogTrigger asChild>{trigger}</DialogTrigger> : defaultTrigger}
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Download Card Image</DialogTitle>
          <DialogDescription>
            Generate a shareable card image for &ldquo;{listing.title}&rdquo;
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Style Selector */}
          <div className="space-y-3">
            <Label>Style</Label>
            <RadioGroup
              value={options.style}
              onValueChange={(value) =>
                setOptions({ ...options, style: value as CardStyle })
              }
              className="grid grid-cols-2 gap-4"
            >
              {(Object.entries(CARD_STYLES) as [CardStyle, typeof CARD_STYLES.light][]).map(
                ([key, { label, preview }]) => (
                  <label
                    key={key}
                    className={cn(
                      "flex items-center space-x-2 rounded-lg border-2 p-4 cursor-pointer transition-colors",
                      options.style === key
                        ? "border-primary bg-primary/5"
                        : "border-muted hover:border-primary/50"
                    )}
                  >
                    <RadioGroupItem value={key} id={`style-${key}`} />
                    <div className="flex-1">
                      <span className="text-sm font-medium">{label}</span>
                      <div
                        className={cn(
                          "mt-2 h-8 rounded border",
                          preview
                        )}
                      />
                    </div>
                  </label>
                )
              )}
            </RadioGroup>
          </div>

          <Separator />

          {/* Size Selector */}
          <div className="space-y-3">
            <Label>Size</Label>
            <RadioGroup
              value={options.size}
              onValueChange={(value) =>
                setOptions({ ...options, size: value as CardSize })
              }
            >
              {(Object.entries(CARD_SIZES) as [CardSize, typeof CARD_SIZES.social][]).map(
                ([key, { label }]) => (
                  <label
                    key={key}
                    className={cn(
                      "flex items-center space-x-2 rounded-lg border-2 p-3 cursor-pointer transition-colors",
                      options.size === key
                        ? "border-primary bg-primary/5"
                        : "border-muted hover:border-primary/50"
                    )}
                  >
                    <RadioGroupItem value={key} id={`size-${key}`} />
                    <span className="text-sm font-medium">{label}</span>
                  </label>
                )
              )}
            </RadioGroup>
          </div>

          <Separator />

          {/* Format Selector */}
          <div className="space-y-3">
            <Label>Format</Label>
            <RadioGroup
              value={options.format}
              onValueChange={(value) =>
                setOptions({ ...options, format: value as CardFormat })
              }
            >
              {(Object.entries(CARD_FORMATS) as [CardFormat, typeof CARD_FORMATS.png][]).map(
                ([key, { label }]) => (
                  <label
                    key={key}
                    className={cn(
                      "flex items-center space-x-2 rounded-lg border-2 p-3 cursor-pointer transition-colors",
                      options.format === key
                        ? "border-primary bg-primary/5"
                        : "border-muted hover:border-primary/50"
                    )}
                  >
                    <RadioGroupItem value={key} id={`format-${key}`} />
                    <span className="text-sm font-medium">{label}</span>
                  </label>
                )
              )}
            </RadioGroup>
          </div>

          <Separator />

          {/* Preview */}
          <div className="space-y-3">
            <Label>Preview</Label>
            <div className="rounded-lg border bg-muted/50 p-4">
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <ImageIcon className="h-5 w-5" />
                <div>
                  <p className="font-medium text-foreground">{listing.title}</p>
                  <p className="text-xs">
                    {CARD_SIZES[options.size].width}×{CARD_SIZES[options.size].height} •{" "}
                    {CARD_STYLES[options.style].label} •{" "}
                    {CARD_FORMATS[options.format].label}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-destructive">Error</p>
                <p className="text-sm text-destructive/90">{error}</p>
              </div>
            </div>
          )}

          {/* Download Button */}
          <Button
            onClick={handleDownload}
            disabled={isGenerating}
            className="w-full"
            size="lg"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating card...
              </>
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Download Card
              </>
            )}
          </Button>

          {error && (
            <Button
              onClick={handleDownload}
              variant="outline"
              className="w-full"
              disabled={isGenerating}
            >
              Retry
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
