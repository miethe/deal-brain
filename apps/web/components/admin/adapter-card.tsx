"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../ui/card";
import { Switch } from "../ui/switch";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { AdapterMetricsDisplay } from "./adapter-metrics-display";
import { updateAdapterConfig } from "../../lib/api/adapter-settings";
import { toast } from "../ui/use-toast";
import type { AdapterWithMetrics, AdapterConfigUpdate } from "../../lib/api/adapter-settings";

interface AdapterCardProps {
  adapter: AdapterWithMetrics;
}

export function AdapterCard({ adapter }: AdapterCardProps) {
  const queryClient = useQueryClient();
  const [enabled, setEnabled] = useState(adapter.config.enabled);
  const [timeoutS, setTimeoutS] = useState(adapter.config.timeout_s.toString());
  const [retries, setRetries] = useState(adapter.config.retries.toString());
  const [errors, setErrors] = useState<Record<string, string>>({});

  const updateMutation = useMutation({
    mutationFn: (update: AdapterConfigUpdate) => updateAdapterConfig(adapter.adapter_id, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adapters"] });
      toast({
        title: "Settings saved",
        description: `${adapter.name} configuration updated successfully.`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to save settings",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const validateAndSave = () => {
    const newErrors: Record<string, string> = {};

    const timeoutNum = parseInt(timeoutS, 10);
    if (isNaN(timeoutNum) || timeoutNum < 1 || timeoutNum > 60) {
      newErrors.timeout_s = "Timeout must be between 1 and 60 seconds";
    }

    const retriesNum = parseInt(retries, 10);
    if (isNaN(retriesNum) || retriesNum < 0 || retriesNum > 5) {
      newErrors.retries = "Retries must be between 0 and 5";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});

    const update: AdapterConfigUpdate = {};
    if (enabled !== adapter.config.enabled) {
      update.enabled = enabled;
    }
    if (timeoutNum !== adapter.config.timeout_s) {
      update.timeout_s = timeoutNum;
    }
    if (retriesNum !== adapter.config.retries) {
      update.retries = retriesNum;
    }

    if (Object.keys(update).length === 0) {
      toast({
        title: "No changes",
        description: "No configuration changes detected.",
      });
      return;
    }

    updateMutation.mutate(update);
  };

  const hasChanges =
    enabled !== adapter.config.enabled ||
    timeoutS !== adapter.config.timeout_s.toString() ||
    retries !== adapter.config.retries.toString();

  const isDisabled = adapter.adapter_id === "scraper" || adapter.adapter_id === "amazon";

  return (
    <Card className={!enabled ? "opacity-75" : undefined}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <CardTitle className="flex items-center gap-2">
              {adapter.name}
              {isDisabled && (
                <Badge variant="outline" className="font-normal">
                  P1 - Coming Soon
                </Badge>
              )}
            </CardTitle>
            <CardDescription>{adapter.description}</CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor={`${adapter.adapter_id}-enabled`} className="text-sm font-medium">
                Enable Adapter
              </Label>
              <p className="text-xs text-muted-foreground">
                {enabled ? "Adapter is active and will process URLs" : "Adapter is disabled"}
              </p>
            </div>
            <Switch
              id={`${adapter.adapter_id}-enabled`}
              checked={enabled}
              onCheckedChange={setEnabled}
              disabled={isDisabled || updateMutation.isPending}
              aria-label={`Enable ${adapter.name} adapter`}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor={`${adapter.adapter_id}-timeout`}>
                Timeout (seconds)
                <span className="ml-1 text-xs text-muted-foreground">1-60</span>
              </Label>
              <Input
                id={`${adapter.adapter_id}-timeout`}
                type="number"
                min="1"
                max="60"
                value={timeoutS}
                onChange={(e) => {
                  setTimeoutS(e.target.value);
                  if (errors.timeout_s) {
                    setErrors((prev) => {
                      const next = { ...prev };
                      delete next.timeout_s;
                      return next;
                    });
                  }
                }}
                disabled={isDisabled || updateMutation.isPending}
                aria-invalid={!!errors.timeout_s}
                aria-describedby={errors.timeout_s ? `${adapter.adapter_id}-timeout-error` : undefined}
              />
              {errors.timeout_s && (
                <p id={`${adapter.adapter_id}-timeout-error`} className="text-xs text-destructive" role="alert">
                  {errors.timeout_s}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor={`${adapter.adapter_id}-retries`}>
                Max Retries
                <span className="ml-1 text-xs text-muted-foreground">0-5</span>
              </Label>
              <Input
                id={`${adapter.adapter_id}-retries`}
                type="number"
                min="0"
                max="5"
                value={retries}
                onChange={(e) => {
                  setRetries(e.target.value);
                  if (errors.retries) {
                    setErrors((prev) => {
                      const next = { ...prev };
                      delete next.retries;
                      return next;
                    });
                  }
                }}
                disabled={isDisabled || updateMutation.isPending}
                aria-invalid={!!errors.retries}
                aria-describedby={errors.retries ? `${adapter.adapter_id}-retries-error` : undefined}
              />
              {errors.retries && (
                <p id={`${adapter.adapter_id}-retries-error`} className="text-xs text-destructive" role="alert">
                  {errors.retries}
                </p>
              )}
            </div>
          </div>

          {adapter.supported_domains.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Supported Domains</Label>
              <div className="flex flex-wrap gap-2">
                {adapter.supported_domains.map((domain) => (
                  <Badge key={domain} variant="outline" className="font-mono text-xs">
                    {domain}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <Label className="text-sm font-medium">Performance Metrics</Label>
          <AdapterMetricsDisplay metrics={adapter.metrics} />
        </div>
      </CardContent>

      <CardFooter className="flex justify-between">
        <p className="text-xs text-muted-foreground">
          {updateMutation.isPending ? "Saving changes..." : hasChanges ? "Unsaved changes" : "All changes saved"}
        </p>
        <Button
          onClick={validateAndSave}
          disabled={!hasChanges || isDisabled || updateMutation.isPending}
          aria-label={`Save ${adapter.name} settings`}
        >
          {updateMutation.isPending ? "Saving..." : "Save Settings"}
        </Button>
      </CardFooter>
    </Card>
  );
}
