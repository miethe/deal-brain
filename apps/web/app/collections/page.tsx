"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Plus, Compass, Upload } from "lucide-react";
import Link from "next/link";
import { useCollections } from "@/hooks/use-collections";
import { CollectionCard } from "@/components/collections/collection-card";
import { CollectionsEmptyState } from "@/components/collections/collections-empty-state";
import { NewCollectionForm } from "@/components/collections/new-collection-form";
import { JsonImportButton } from "@/components/import-export/json-import-button";
import { useQueryClient } from "@tanstack/react-query";
import type { Collection } from "@/types/collections";

export default function CollectionsPage() {
  const [newCollectionOpen, setNewCollectionOpen] = useState(false);
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [allCollections, setAllCollections] = useState<Collection[]>([]);
  const queryClient = useQueryClient();

  const { data, isLoading } = useCollections({ limit, offset });

  const collections = data?.collections ?? [];
  const total = data?.total ?? 0;
  const hasMore = allCollections.length < total;

  // Accumulate collections when new data arrives
  useEffect(() => {
    if (collections.length > 0) {
      setAllCollections((prev) => {
        // If offset is 0, replace all (fresh load or refresh)
        if (offset === 0) {
          return collections;
        }
        // Otherwise, append new collections, avoiding duplicates
        const seen = new Set(prev.map((c) => c.id));
        const newCollections = collections.filter((c) => !seen.has(c.id));
        return [...prev, ...newCollections];
      });
    }
  }, [collections, offset]);

  const handleLoadMore = () => {
    setOffset((prev) => prev + limit);
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Collections</h1>
          <p className="text-sm text-muted-foreground">
            Organize and curate your favorite listings.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" asChild>
            <Link href="/collections/discover">
              <Compass className="w-4 h-4 mr-2" />
              Discover
            </Link>
          </Button>
          <JsonImportButton
            importType="collection"
            variant="outline"
            onSuccess={() => {
              queryClient.invalidateQueries({ queryKey: ["collections"] });
              setOffset(0); // Reset to first page
            }}
          />
          <Button onClick={() => setNewCollectionOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            New collection
          </Button>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && offset === 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-40 rounded-lg border bg-card animate-pulse"
              aria-label="Loading collection"
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && allCollections.length === 0 && offset === 0 && (
        <CollectionsEmptyState onCreateClick={() => setNewCollectionOpen(true)} />
      )}

      {/* Collections grid */}
      {allCollections.length > 0 && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allCollections.map((collection) => (
              <CollectionCard key={collection.id} collection={collection} />
            ))}
          </div>

          {/* Load more button */}
          {hasMore && (
            <div className="flex justify-center">
              <Button
                variant="outline"
                onClick={handleLoadMore}
                disabled={isLoading}
              >
                {isLoading ? "Loading..." : "Load more"}
              </Button>
            </div>
          )}

          {/* Total count */}
          <p className="text-center text-sm text-muted-foreground">
            Showing {allCollections.length} of {total} collections
          </p>
        </div>
      )}

      {/* New Collection Modal */}
      <NewCollectionForm
        open={newCollectionOpen}
        onOpenChange={setNewCollectionOpen}
      />
    </div>
  );
}
