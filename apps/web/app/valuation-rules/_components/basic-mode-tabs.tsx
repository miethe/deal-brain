"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Loader2 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { BaselineFieldCard } from "@/components/valuation/baseline-field-card";
import { PreviewImpactPanel } from "@/components/valuation/preview-impact-panel";
import { useBaselineOverrides } from "@/hooks/use-baseline-overrides";
import { getBaselineMetadata } from "@/lib/api/baseline";
import type { BaselineEntity } from "@/types/baseline";

const ENTITY_TABS = [
  { key: "Listing", label: "Listing", description: "Base listing properties" },
  { key: "CPU", label: "CPU", description: "Processor valuation" },
  { key: "GPU", label: "GPU", description: "Graphics card valuation" },
  { key: "RamSpec", label: "RAM", description: "Memory valuation" },
  { key: "StorageProfile", label: "Storage", description: "Storage device valuation" },
  { key: "PortsProfile", label: "Ports", description: "Connectivity valuation" },
];

export function BasicModeTabs() {
  const [activeTab, setActiveTab] = useState<string>("Listing");

  // Fetch baseline metadata
  const {
    data: baselineMetadata,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["baseline-metadata"],
    queryFn: getBaselineMetadata,
    staleTime: 60000, // 1 minute
  });

  // Get overrides for active entity
  const {
    overrides,
    isLoading: isLoadingOverrides,
    hasUnsavedChanges,
    isSaving,
    applyOverride,
    resetField,
    resetAllFields,
    saveOverrides,
    discardChanges,
    hasOverride,
  } = useBaselineOverrides({ entityKey: activeTab });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Loading baseline metadata...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error loading baseline</AlertTitle>
        <AlertDescription>
          {error instanceof Error ? error.message : "Failed to load baseline metadata"}
        </AlertDescription>
      </Alert>
    );
  }

  if (!baselineMetadata || !baselineMetadata.entities.length) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="flex flex-col items-center gap-4">
            <AlertCircle className="h-12 w-12 text-muted-foreground" />
            <div>
              <h3 className="text-lg font-semibold">No baseline configured</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Please instantiate a baseline configuration first.
              </p>
            </div>
            <Button variant="outline" onClick={() => window.location.reload()}>
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentEntity = baselineMetadata.entities.find((e) => e.entity_key === activeTab);
  const overrideCount = overrides.size;

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        {/* Tabs List - Responsive */}
        <div className="overflow-x-auto">
          <TabsList className="inline-flex h-auto w-full min-w-max gap-1 bg-muted/40 p-1 sm:w-auto">
            {ENTITY_TABS.map((tab) => {
              const entity = baselineMetadata.entities.find((e) => e.entity_key === tab.key);
              const fieldCount = entity?.fields.length ?? 0;

              return (
                <TabsTrigger
                  key={tab.key}
                  value={tab.key}
                  className="flex flex-col items-start gap-0.5 px-3 py-2 data-[state=active]:bg-background"
                  disabled={!entity}
                >
                  <span className="text-sm font-medium">{tab.label}</span>
                  <span className="text-xs text-muted-foreground">
                    {fieldCount} field{fieldCount !== 1 ? "s" : ""}
                  </span>
                </TabsTrigger>
              );
            })}
          </TabsList>
        </div>

        {/* Tab Content */}
        {ENTITY_TABS.map((tab) => (
          <TabsContent key={tab.key} value={tab.key} className="mt-6 space-y-6">
            {currentEntity && tab.key === activeTab && (
              <>
                {/* Entity Header */}
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold">{currentEntity.entity_name}</h2>
                    <p className="text-sm text-muted-foreground">
                      {currentEntity.description}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {overrideCount > 0 && (
                      <>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={resetAllFields}
                          disabled={isSaving}
                        >
                          Reset All ({overrideCount})
                        </Button>
                        {hasUnsavedChanges && (
                          <>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={discardChanges}
                              disabled={isSaving}
                            >
                              Discard
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              onClick={saveOverrides}
                              disabled={isSaving}
                            >
                              {isSaving ? "Saving..." : "Save Changes"}
                            </Button>
                          </>
                        )}
                      </>
                    )}
                  </div>
                </div>

                {/* Field Cards Grid */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {currentEntity.fields.map((field) => {
                    const override = overrides.get(field.name);
                    return (
                      <BaselineFieldCard
                        key={field.name}
                        field={field}
                        override={override}
                        onOverrideChange={(overrideData) => {
                          applyOverride(field.name, overrideData);
                        }}
                        onReset={() => resetField(field.name)}
                        disabled={isSaving}
                      />
                    );
                  })}
                </div>

                {/* Empty state if no fields */}
                {currentEntity.fields.length === 0 && (
                  <Card>
                    <CardContent className="py-12 text-center">
                      <p className="text-sm text-muted-foreground">
                        No fields configured for this entity.
                      </p>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </TabsContent>
        ))}
      </Tabs>

      {/* Preview Impact Panel */}
      <PreviewImpactPanel entityKey={activeTab} />
    </div>
  );
}
