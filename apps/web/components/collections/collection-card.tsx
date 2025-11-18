"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDistanceToNow } from "date-fns";
import { Lock, Users, Globe } from "lucide-react";
import type { Collection } from "@/types/collections";
import Link from "next/link";

interface CollectionCardProps {
  collection: Collection;
}

const visibilityIcons = {
  private: Lock,
  shared: Users,
  public: Globe,
};

const visibilityLabels = {
  private: "Private",
  shared: "Shared",
  public: "Public",
};

export function CollectionCard({ collection }: CollectionCardProps) {
  const Icon = visibilityIcons[collection.visibility];
  const relativeTime = formatDistanceToNow(new Date(collection.created_at), {
    addSuffix: true,
  });

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
        <CardContent>
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {collection.item_count} {collection.item_count === 1 ? "item" : "items"}
            </span>
            <span className="text-xs">{relativeTime}</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
