"use client";

import { Button } from "@/components/ui/button";
import { FolderOpen } from "lucide-react";

interface CollectionsEmptyStateProps {
  onCreateClick: () => void;
}

export function CollectionsEmptyState({ onCreateClick }: CollectionsEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="rounded-full bg-muted p-6 mb-4">
        <FolderOpen className="w-12 h-12 text-muted-foreground" />
      </div>
      <h2 className="text-2xl font-semibold mb-2">No collections yet</h2>
      <p className="text-muted-foreground mb-6 max-w-md">
        Collections help you organize and curate your listings. Create your first collection to get started.
      </p>
      <Button onClick={onCreateClick}>
        Create your first collection
      </Button>
    </div>
  );
}
