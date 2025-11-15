"use client";

import { useEffect, useState, useCallback } from "react";
import { getUserBuilds, deleteBuild, type SavedBuild } from "@/lib/api/builder";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { Share2, Edit, Trash2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { ShareModal } from "./share-modal";
import { useBuilder } from "./builder-provider";

export function SavedBuildsSection() {
  const [builds, setBuilds] = useState<SavedBuild[]>([]);
  const [loading, setLoading] = useState(true);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [selectedBuild, setSelectedBuild] = useState<SavedBuild | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [buildToDelete, setBuildToDelete] = useState<SavedBuild | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const { dispatch } = useBuilder();
  const { toast } = useToast();

  const loadBuilds = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getUserBuilds(10, 0);
      setBuilds(response.items || []);
    } catch (error) {
      toast({
        title: "Failed to load builds",
        description: "Could not load your saved builds",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadBuilds();
  }, [loadBuilds]);

  const handleLoad = (build: SavedBuild) => {
    // Load build components into builder
    const components = build.build_snapshot.components;

    Object.entries(components).forEach(([type, id]) => {
      if (id) {
        dispatch({
          type: "SELECT_COMPONENT",
          payload: { componentType: type as any, id },
        });
      }
    });

    toast({
      title: "Build loaded",
      description: `"${build.name || 'Unnamed Build'}" loaded into builder`,
    });

    // Scroll to top
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleShare = (build: SavedBuild) => {
    setSelectedBuild(build);
    setShareModalOpen(true);
  };

  const handleDeleteClick = (build: SavedBuild) => {
    setBuildToDelete(build);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!buildToDelete) return;

    setIsDeleting(true);
    try {
      await deleteBuild(buildToDelete.id);
      toast({
        title: "Build deleted",
        description: "Build has been removed",
      });
      setDeleteConfirmOpen(false);
      setBuildToDelete(null);
      loadBuilds();
    } catch (error) {
      toast({
        title: "Delete failed",
        description: "Could not delete build",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Loading your builds...
      </div>
    );
  }

  if (builds.length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        <p>No saved builds yet</p>
        <p className="text-sm mt-2">
          Create a build above and save it to see it here
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {builds.map((build) => {
          const valuation = build.build_snapshot.valuation;
          const metrics = build.build_snapshot.metrics;
          const delta = valuation?.delta_percentage || 0;

          return (
            <Card key={build.id} className="relative">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">
                      {build.name || "Unnamed Build"}
                    </CardTitle>
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {build.is_public && (
                        <Badge variant="secondary" className="text-xs">
                          Public
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {valuation && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Base Price</span>
                      <span>${parseFloat(valuation.base_price.toString()).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm font-semibold">
                      <span>Adjusted Value</span>
                      <span>
                        ${parseFloat(valuation.adjusted_price.toString()).toFixed(2)}
                      </span>
                    </div>
                    <div
                      className={`text-center p-2 rounded ${
                        delta >= 25
                          ? "bg-green-50 text-green-700"
                          : delta >= 15
                          ? "bg-green-50 text-green-600"
                          : delta >= 0
                          ? "bg-yellow-50 text-yellow-700"
                          : "bg-red-50 text-red-700"
                      }`}
                    >
                      <span className="text-sm font-medium">
                        {delta > 0 ? "+" : ""}
                        {delta.toFixed(1)}%{" "}
                        {delta >= 25
                          ? "Great Deal"
                          : delta >= 15
                          ? "Good Deal"
                          : delta >= 0
                          ? "Fair"
                          : "Premium"}
                      </span>
                    </div>
                  </div>
                )}

                {metrics && (
                  <div className="space-y-1 text-sm">
                    {metrics.dollar_per_cpu_mark_multi && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">$/CPU Mark</span>
                        <span>
                          ${parseFloat(metrics.dollar_per_cpu_mark_multi.toString()).toFixed(4)}
                        </span>
                      </div>
                    )}
                    {metrics.composite_score && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Score</span>
                        <span className="text-blue-600 font-medium">
                          {metrics.composite_score}/100
                        </span>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleLoad(build)}
                  >
                    <Edit className="h-4 w-4 mr-1" />
                    Load
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleShare(build)}
                  >
                    <Share2 className="h-4 w-4 mr-1" />
                    Share
                  </Button>
                  <Button variant="destructive" size="sm" onClick={() => handleDeleteClick(build)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>

                <div className="text-xs text-muted-foreground">
                  Saved {new Date(build.created_at).toLocaleDateString()}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {selectedBuild && (
        <ShareModal
          open={shareModalOpen}
          onOpenChange={setShareModalOpen}
          build={selectedBuild}
        />
      )}

      <ConfirmationDialog
        open={deleteConfirmOpen}
        onOpenChange={setDeleteConfirmOpen}
        title="Delete Build?"
        description={`Are you sure you want to delete "${buildToDelete?.name || 'this build'}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="destructive"
        onConfirm={handleDeleteConfirm}
        isLoading={isDeleting}
      />
    </>
  );
}
