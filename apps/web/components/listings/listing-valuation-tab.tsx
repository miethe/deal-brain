"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Checkbox } from "../ui/checkbox";
import { Label } from "../ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Separator } from "../ui/separator";
import { ListingRecord, ValuationBreakdown } from "../../types/listings";
import { fetchRulesets, type Ruleset } from "../../lib/api/rules";
import {
  updateListingValuationOverrides,
  type ListingValuationOverridePayload,
} from "../../lib/api/listings";
import { useToast } from "../ui/use-toast";
import { ValuationCell } from "./valuation-cell";
import { useValuationThresholds } from "@/hooks/use-valuation-thresholds";
import { formatCurrency } from "@/lib/valuation-utils";
import { ValuationBreakdownModal } from "./valuation-breakdown-modal";

type OverrideMode = "auto" | "static";

interface ListingValuationTabProps {
  listing: ListingRecord;
}

const DISABLED_RULESETS_ATTR = "valuation_disabled_rulesets";

function normalizeDisabled(values: unknown): number[] {
  if (!Array.isArray(values)) {
    return [];
  }
  const normalized = values
    .map((value) => {
      const parsed = Number(value);
      return Number.isFinite(parsed) && Number.isInteger(parsed) ? parsed : null;
    })
    .filter((value): value is number => value != null && value >= 0);
  return Array.from(new Set(normalized)).sort((a, b) => a - b);
}

function formatAdjustment(value: number | null | undefined): string {
  if (value == null) {
    return "—";
  }
  const formatted = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: Math.abs(value) < 1 ? 2 : 0,
    maximumFractionDigits: Math.abs(value) < 1 ? 2 : 0,
  }).format(value);
  return value > 0 ? `+${formatted}` : formatted;
}

export function ListingValuationTab({ listing }: ListingValuationTabProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { data: thresholds } = useValuationThresholds();
  const [isBreakdownOpen, setIsBreakdownOpen] = useState(false);

  const { data: rulesets = [], isLoading: isLoadingRulesets } = useQuery({
    queryKey: ["rulesets", "active"],
    queryFn: () => fetchRulesets(true),
  });

  const sortedRulesets: Ruleset[] = useMemo(
    () => [...rulesets].sort((a, b) => a.priority - b.priority),
    [rulesets]
  );

  const initialDisabled = useMemo(
    () => normalizeDisabled(listing.attributes?.[DISABLED_RULESETS_ATTR]),
    [listing.attributes]
  );

  const initialMode: OverrideMode = listing.ruleset_id ? "static" : "auto";
  const initialRulesetId = listing.ruleset_id ?? null;

  const [mode, setMode] = useState<OverrideMode>(initialMode);
  const [selectedRulesetId, setSelectedRulesetId] = useState<number | null>(initialRulesetId);
  const [disabledRulesets, setDisabledRulesets] = useState<number[]>(initialDisabled);
  const [baseline, setBaseline] = useState(() => ({
    mode: initialMode,
    rulesetId: initialRulesetId,
    disabled: [...initialDisabled],
  }));

  useEffect(() => {
    setMode(initialMode);
    setSelectedRulesetId(initialRulesetId);
    setDisabledRulesets(initialDisabled);
    setBaseline({
      mode: initialMode,
      rulesetId: initialRulesetId,
      disabled: [...initialDisabled],
    });
  }, [initialMode, initialRulesetId, initialDisabled, listing.id]);

  useEffect(() => {
    if (mode === "static" && !selectedRulesetId && sortedRulesets.length) {
      setSelectedRulesetId(sortedRulesets[0].id);
    }
  }, [mode, selectedRulesetId, sortedRulesets]);

  const normalizedDisabled = useMemo(
    () => [...disabledRulesets].sort((a, b) => a - b),
    [disabledRulesets]
  );
  const normalizedBaselineDisabled = useMemo(
    () => [...baseline.disabled].sort((a, b) => a - b),
    [baseline.disabled]
  );

  const disabledChanged =
    normalizedDisabled.length !== normalizedBaselineDisabled.length ||
    normalizedDisabled.some((value, index) => value !== normalizedBaselineDisabled[index]);
  const modeChanged = mode !== baseline.mode;
  const effectiveRulesetCurrent = mode === "static" ? selectedRulesetId ?? null : null;
  const effectiveRulesetInitial = baseline.mode === "static" ? baseline.rulesetId : null;
  const rulesetChanged = effectiveRulesetCurrent !== effectiveRulesetInitial;

  const hasChanges = disabledChanged || modeChanged || rulesetChanged;
  const disableSave =
    mode === "static" && !selectedRulesetId ? true : !hasChanges;

  const mutation = useMutation({
    mutationFn: (payload: ListingValuationOverridePayload) =>
      updateListingValuationOverrides(listing.id, payload),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ["listings", "single", listing.id] });
      queryClient.invalidateQueries({ queryKey: ["listings", "records"] });
      queryClient.invalidateQueries({ queryKey: ["valuation-breakdown", listing.id] });
      toast({
        title: "Valuation updated",
        description: "Listing overrides applied successfully.",
      });
      const nextDisabled = [...response.disabled_rulesets].sort((a, b) => a - b);
      const nextMode = response.mode as OverrideMode;
      const nextRulesetId = response.ruleset_id ?? null;
      setMode(nextMode);
      setSelectedRulesetId(nextRulesetId);
      setDisabledRulesets(nextDisabled);
      setBaseline({
        mode: nextMode,
        rulesetId: nextRulesetId,
        disabled: [...nextDisabled],
      });
    },
    onError: (error: unknown) => {
      toast({
        title: "Update failed",
        description: error instanceof Error ? error.message : "Unable to update valuation overrides.",
        variant: "destructive",
      });
    },
  });

  const breakdown: ValuationBreakdown | null = listing.valuation_breakdown ?? null;
  const adjustments = breakdown?.adjustments ?? [];
  const activeRulesetName =
    breakdown?.ruleset?.name ?? breakdown?.ruleset_name ?? (listing.ruleset_id ? "Static override" : "Auto");

  const handleToggleRuleset = (rulesetId: number, enabled: boolean) => {
    setDisabledRulesets((prev) => {
      const set = new Set(prev);
      if (enabled) {
        set.delete(rulesetId);
      } else {
        set.add(rulesetId);
      }
      return Array.from(set).sort((a, b) => a - b);
    });
  };

  const handleReset = () => {
    setMode(baseline.mode);
    setSelectedRulesetId(baseline.rulesetId);
    setDisabledRulesets([...baseline.disabled]);
  };

  const handleSave = () => {
    if (mode === "static" && !selectedRulesetId) {
      toast({
        title: "Select a ruleset",
        description: "Choose a ruleset before saving a static override.",
        variant: "destructive",
      });
      return;
    }

    const payload: ListingValuationOverridePayload = {
      mode,
      ruleset_id: mode === "static" ? selectedRulesetId ?? undefined : null,
      disabled_rulesets: disabledRulesets,
    };

    mutation.mutate(payload);
  };

  const renderOverrideControls = () => {
    if (isLoadingRulesets) {
      return (
        <div className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
          Loading rulesets…
        </div>
      );
    }

    if (!sortedRulesets.length) {
      return (
        <div className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
          No active rulesets available. Create an active ruleset to enable overrides.
        </div>
      );
    }

    if (mode === "static") {
      return (
        <div className="space-y-3">
          <Label htmlFor="static-ruleset">Choose ruleset</Label>
          <Select
            value={selectedRulesetId?.toString() ?? ""}
            onValueChange={(value) => setSelectedRulesetId(value ? Number(value) : null)}
          >
            <SelectTrigger id="static-ruleset" className="min-h-[52px] items-start py-3">
              <SelectValue placeholder="Select ruleset…" />
            </SelectTrigger>
            <SelectContent>
              {sortedRulesets.map((ruleset) => (
                <SelectItem key={ruleset.id} value={ruleset.id.toString()} className="py-3">
                  <div className="flex w-full items-start justify-between gap-3 text-left">
                    <span>{ruleset.name}</span>
                    <Badge variant="outline">Priority {ruleset.priority}</Badge>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">
          Disable rulesets to exclude them from automatic matching. Remaining rulesets will be evaluated by ascending priority.
        </p>
        <div className="space-y-2">
          {sortedRulesets.map((ruleset) => {
            const enabled = !disabledRulesets.includes(ruleset.id);
            return (
              <div
                key={ruleset.id}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="flex items-center gap-3">
                  <Checkbox
                    id={`ruleset-${ruleset.id}`}
                    checked={enabled}
                    onCheckedChange={(checked) =>
                      handleToggleRuleset(ruleset.id, checked === true)
                    }
                  />
                  <div>
                    <Label htmlFor={`ruleset-${ruleset.id}`} className="font-medium">
                      {ruleset.name}
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Priority {ruleset.priority}
                    </p>
                  </div>
                </div>
                <Badge variant={enabled ? "outline" : "secondary"}>
                  {enabled ? "Enabled" : "Disabled"}
                </Badge>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const basePrice = listing.price_usd ?? 0;
  const adjustedPrice = listing.adjusted_price_usd ?? basePrice;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="text-lg font-semibold">Current valuation</CardTitle>
            <p className="text-sm text-muted-foreground">
              {activeRulesetName
                ? `Calculated using ${activeRulesetName}.`
                : "Valuation summary for this listing."}
            </p>
          </div>
          {thresholds && (
            <ValuationCell
              adjustedPrice={adjustedPrice}
              listPrice={basePrice}
              thresholds={thresholds}
              onDetailsClick={() => setIsBreakdownOpen(true)}
            />
          )}
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-3">
            <SummaryTile label="Base price" value={basePrice} />
            <SummaryTile label="Adjusted price" value={adjustedPrice} />
            <SummaryTile
              label="Total adjustment"
              value={basePrice - adjustedPrice}
              tone={adjustedPrice <= basePrice ? "positive" : "negative"}
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Badge variant="secondary">
              {adjustments.length} rule{adjustments.length === 1 ? "" : "s"} applied
            </Badge>
            <Button variant="outline" size="sm" onClick={() => setIsBreakdownOpen(true)}>
              View breakdown
            </Button>
          </div>

          {adjustments.length > 0 ? (
            <ul className="space-y-2">
              {adjustments.slice(0, 4).map((adjustment) => (
                <li
                  key={`${adjustment.rule_id ?? adjustment.rule_name}`}
                  className="flex items-center justify-between rounded-md border p-3"
                >
                  <div>
                    <p className="font-medium text-sm">{adjustment.rule_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {adjustment.actions?.length ?? 0} action{adjustment.actions?.length === 1 ? "" : "s"}
                    </p>
                  </div>
                  <span
                    className={
                      adjustment.adjustment_amount < 0
                        ? "text-emerald-600 font-semibold"
                        : adjustment.adjustment_amount > 0
                        ? "text-red-600 font-semibold"
                        : "text-muted-foreground font-medium"
                    }
                  >
                    {formatAdjustment(adjustment.adjustment_amount)}
                  </span>
                </li>
              ))}
              {adjustments.length > 4 && (
                <li className="text-xs text-muted-foreground">
                  {adjustments.length - 4} more adjustment{adjustments.length - 4 === 1 ? "" : "s"} in breakdown
                </li>
              )}
            </ul>
          ) : (
            <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
              No rule-based adjustments were applied to this listing.
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Override controls</CardTitle>
          <p className="text-sm text-muted-foreground">
            Choose automatic assignment or lock this listing to a specific ruleset.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="inline-flex rounded-md border bg-muted/40 p-1 text-sm font-medium">
            <button
              type="button"
              className={`rounded-sm px-3 py-1.5 transition-colors ${
                mode === "auto" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setMode("auto")}
            >
              Auto select
            </button>
            <button
              type="button"
              className={`rounded-sm px-3 py-1.5 transition-colors ${
                mode === "static" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setMode("static")}
            >
              Static override
            </button>
          </div>

          <Separator />

          {renderOverrideControls()}

          <div className="flex items-center justify-between pt-2">
            <Button type="button" variant="ghost" size="sm" onClick={handleReset} disabled={!hasChanges}>
              Reset
            </Button>
            <Button
              type="button"
              onClick={handleSave}
              disabled={disableSave || mutation.isPending}
            >
              {mutation.isPending ? "Saving…" : "Save overrides"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <ValuationBreakdownModal
        open={isBreakdownOpen}
        onOpenChange={setIsBreakdownOpen}
        listingId={listing.id}
        listingTitle={listing.title}
        thumbnailUrl={listing.thumbnail_url}
      />
    </div>
  );
}

function SummaryTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "positive" | "negative";
}) {
  const formatted = formatCurrency(Math.abs(value));
  const isZero = Math.abs(value) < 0.01;
  const prefix = tone === "positive" ? "−" : tone === "negative" ? "+" : "";
  const display = isZero ? "$0" : `${tone ? prefix : ""}${formatted}`;

  return (
    <div className="rounded-md border p-3">
      <p className="text-xs uppercase text-muted-foreground tracking-wide">{label}</p>
      <p
        className={
          tone === "positive"
            ? "mt-1 text-lg font-semibold text-emerald-600"
            : tone === "negative"
            ? "mt-1 text-lg font-semibold text-red-600"
            : "mt-1 text-lg font-semibold"
        }
      >
        {display}
      </p>
    </div>
  );
}
