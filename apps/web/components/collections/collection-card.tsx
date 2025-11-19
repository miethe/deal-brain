"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDistanceToNow } from "date-fns";
import { Lock, Users, Globe, Eye, Share2 } from "lucide-react";
import type { Collection } from "@/types/collections";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface CollectionCardProps {
  collection: Collection;
}

const visibilityIcons = {
  private: Lock,
  unlisted: Users,
  public: Globe,
};

const visibilityLabels = {
  private: "Private",
  unlisted: "Unlisted",
  public: "Public",
};

export function CollectionCard({ collection }: CollectionCardProps) {
  const Icon = visibilityIcons[collection.visibility];
  const relativeTime = formatDistanceToNow(new Date(collection.created_at), {
    addSuffix: true,
  });

  const isShared = collection.visibility !== "private";
  const hasViews = collection.view_count !== undefined && collection.view_count > 0;

  return (
    <Link href={`/collections/${collection.id}`}>
      <Card className="h-full hover:border-primary/50 transition-colors cursor-pointer">
        <CardHeader>
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-lg line-clamp-1">{collection.name}</CardTitle>
            <Badge variant="outline" className="flex items-center gap-1 shrink-0">
              <Icon className="w-3 h-3" />
              {visibilityLabels[collection.visibility]}
            </Badge>
          </div>
          {collection.description && (
            <CardDescription className="line-clamp-2">
              {collection.description}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {collection.item_count} {collection.item_count === 1 ? "item" : "items"}
            </span>
            <span className="text-xs">{relativeTime}</span>
          </div>

          {/* Share Stats */}
          {(isShared || hasViews) && (
            <div className="flex items-center gap-3 text-xs text-muted-foreground pt-1 border-t">
              {isShared && (
                <div
                  className={cn(
                    "flex items-center gap-1",
                    collection.visibility === "public" && "text-green-600 dark:text-green-400",
                    collection.visibility === "unlisted" && "text-blue-600 dark:text-blue-400"
                  )}
                >
                  <Share2 className="w-3 h-3" />
                  <span className="font-medium">Shared</span>
                </div>
              )}
              {hasViews && (
                <div className="flex items-center gap-1">
                  <Eye className="w-3 h-3" />
                  <span>
                    {collection.view_count} {collection.view_count === 1 ? "view" : "views"}
                  </span>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
