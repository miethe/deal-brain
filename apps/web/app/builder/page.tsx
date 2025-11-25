"use client";

import { useState } from "react";
import { BuilderProvider } from "@/components/builder/builder-provider";
import { ComponentBuilder } from "@/components/builder/component-builder";
import { ValuationPanel } from "@/components/builder/valuation-panel";
import { SavedBuildsSection } from "@/components/builder/saved-builds-section";
import { SaveBuildModal } from "@/components/builder/save-build-modal";
import { Button } from "@/components/ui/button";
import { Save } from "lucide-react";

/**
 * PC Builder page - Configure custom PC builds and get real-time valuations
 *
 * Features:
 * - Component selection with modal interface
 * - Real-time valuation calculations (debounced 300ms)
 * - Performance metrics display
 * - Color-coded deal quality indicators
 * - Responsive layout (60/40 split on desktop)
 * - Sticky valuation panel on desktop
 * - Save and share builds
 * - Saved builds gallery
 */
export default function BuilderPage() {
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [savedBuildsKey, setSavedBuildsKey] = useState(0);

  const handleBuildSaved = () => {
    // Refresh saved builds section by updating key
    setSavedBuildsKey((prev) => prev + 1);
  };

  return (
    <BuilderProvider>
      <div className="container mx-auto p-4 md:p-6">
        {/* Page Header */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">PC Builder</h1>
            <p className="text-muted-foreground">
              Build your custom PC and get real-time valuation and performance metrics
            </p>
          </div>
          <Button onClick={() => setSaveModalOpen(true)} className="w-full sm:w-auto">
            <Save className="mr-2 h-4 w-4" />
            Save Build
          </Button>
        </div>

        {/* Main Layout: Component Selection + Valuation Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
          {/* Left: Component Selection (60% on desktop) */}
          <div className="lg:col-span-2">
            <ComponentBuilder />
          </div>

          {/* Right: Valuation Panel (40% on desktop) */}
          <div className="lg:col-span-1">
            <ValuationPanel />
          </div>
        </div>

        {/* Saved Builds Section */}
        <div className="mt-12">
          <h2 className="text-2xl font-bold mb-4">Your Saved Builds</h2>
          <SavedBuildsSection key={savedBuildsKey} />
        </div>

        {/* Save Build Modal */}
        <SaveBuildModal
          open={saveModalOpen}
          onOpenChange={setSaveModalOpen}
          onSaved={handleBuildSaved}
        />
      </div>
    </BuilderProvider>
  );
}
