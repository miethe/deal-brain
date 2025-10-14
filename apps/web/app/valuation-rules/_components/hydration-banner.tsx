"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Info, Loader2 } from "lucide-react";

interface HydrationBannerProps {
  rulesetId: number;
  onHydrate: () => Promise<void>;
  isHydrating: boolean;
}

export function HydrationBanner({ rulesetId, onHydrate, isHydrating }: HydrationBannerProps) {
  return (
    <Alert className="mb-4">
      <Info className="h-4 w-4" />
      <AlertTitle>Baseline Rules Need Preparation</AlertTitle>
      <AlertDescription className="mt-2">
        <p className="mb-3">
          Baseline rules are currently in placeholder mode. To edit them in Advanced mode,
          they need to be converted to full rule structures.
        </p>
        <Button
          onClick={onHydrate}
          disabled={isHydrating}
          size="sm"
          aria-label="Prepare baseline rules for editing"
        >
          {isHydrating && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
          {isHydrating ? "Preparing Rules..." : "Prepare Baseline Rules for Editing"}
        </Button>
      </AlertDescription>
    </Alert>
  );
}
