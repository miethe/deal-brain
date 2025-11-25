"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Loader2,
  Folder,
  Eye,
  Copy as CopyIcon,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { VisibilityBadge } from "@/components/collections/visibility-badge";
import { useDiscoverCollections, useCopyCollection } from "@/hooks/use-collections";
import type { Collection, DiscoverCollectionsParams } from "@/types/collections";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

/**
 * Collections Discovery Page
 *
 * Browse and discover public collections with:
 * - Search by name/description
 * - Filter by owner
 * - Sort by recent or popularity
 * - Copy collections to workspace
 * - Pagination
 */
export default function DiscoverPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [ownerFilter, setOwnerFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"recent" | "popular">("recent");
  const [page, setPage] = useState(0);
  const limit = 12;

  // Build query params
  const queryParams: DiscoverCollectionsParams = useMemo(
    () => ({
      search: searchQuery || undefined,
      owner_filter: ownerFilter !== "all" ? ownerFilter : undefined,
      sort: sortBy,
      limit,
      offset: page * limit,
    }),
    [searchQuery, ownerFilter, sortBy, page]
  );

  // Fetch discovered collections
  const {
    data: discoverData,
    isLoading,
    error,
  } = useDiscoverCollections(queryParams);

  const collections = discoverData?.collections || [];
  const total = discoverData?.total || 0;
  const hasMore = (page + 1) * limit < total;

  // Copy collection mutation
  const copyMutation = useCopyCollection({
    onSuccess: (newCollection) => {
      router.push(`/collections/${newCollection.id}`);
    },
  });

  // Extract unique owners for filter
  const uniqueOwners = useMemo(() => {
    const owners = new Set<string>();
    collections.forEach((c) => {
      if (c.owner_name) owners.add(c.owner_name);
    });
    return Array.from(owners).sort();
  }, [collections]);

  const handleCopyCollection = (collectionId: number, name: string) => {
    copyMutation.mutate({
      source_collection_id: collectionId,
      name: `Copy of ${name}`,
    });
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setPage(0); // Reset to first page on search
  };

  const handleOwnerFilter = (value: string) => {
    setOwnerFilter(value);
    setPage(0);
  };

  const handleSortChange = (value: "recent" | "popular") => {
    setSortBy(value);
    setPage(0);
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/collections">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to collections
          </Button>
        </Link>
      </div>

      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Discover Collections</h1>
        <p className="text-muted-foreground">
          Browse public collections shared by the community
        </p>
      </div>

      {/* Filters */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Search */}
        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="search">Search</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              id="search"
              placeholder="Search by name or description..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {/* Sort */}
        <div className="space-y-2">
          <Label htmlFor="sort">Sort by</Label>
          <Select value={sortBy} onValueChange={handleSortChange}>
            <SelectTrigger id="sort">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="recent">Most Recent</SelectItem>
              <SelectItem value="popular">Most Popular</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Owner Filter */}
        {uniqueOwners.length > 0 && (
          <div className="space-y-2 md:col-span-3">
            <Label htmlFor="owner">Filter by owner</Label>
            <Select value={ownerFilter} onValueChange={handleOwnerFilter}>
              <SelectTrigger id="owner" className="w-full md:w-[250px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All owners</SelectItem>
                {uniqueOwners.map((owner) => (
                  <SelectItem key={owner} value={owner}>
                    {owner}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* Results */}
      <div className="space-y-4">
        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Error State */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>
              {error instanceof Error ? error.message : "Failed to load collections"}
            </AlertDescription>
          </Alert>
        )}

        {/* Empty State */}
        {!isLoading && !error && collections.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <Folder className="h-16 w-16 text-muted-foreground opacity-50 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No collections found</h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery
                ? "Try adjusting your search or filters"
                : "No public collections available yet"}
            </p>
            {searchQuery && (
              <Button variant="outline" onClick={() => handleSearch("")}>
                Clear search
              </Button>
            )}
          </div>
        )}

        {/* Collection Grid */}
        {!isLoading && !error && collections.length > 0 && (
          <>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {collections.map((collection) => (
                <DiscoveryCard
                  key={collection.id}
                  collection={collection}
                  onCopy={() => handleCopyCollection(collection.id, collection.name)}
                  isCopying={copyMutation.isPending}
                />
              ))}
            </div>

            {/* Pagination */}
            {(page > 0 || hasMore) && (
              <div className="flex items-center justify-between pt-4">
                <p className="text-sm text-muted-foreground">
                  Showing {page * limit + 1}-{Math.min((page + 1) * limit, total)} of {total}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page === 0}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={!hasMore}
                  >
                    {hasMore ? "Load More" : "No More"}
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Discovery Card Component
 *
 * Card for displaying a discoverable collection
 */
interface DiscoveryCardProps {
  collection: Collection;
  onCopy: () => void;
  isCopying: boolean;
}

function DiscoveryCard({ collection, onCopy, isCopying }: DiscoveryCardProps) {
  const relativeTime = formatDistanceToNow(new Date(collection.created_at), {
    addSuffix: true,
  });

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg line-clamp-1">{collection.name}</CardTitle>
          <VisibilityBadge visibility={collection.visibility} showLabel={false} />
        </div>
        {collection.description && (
          <CardDescription className="line-clamp-2">
            {collection.description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-between gap-4">
        <div className="space-y-2">
          {/* Stats */}
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>
              {collection.item_count} {collection.item_count === 1 ? "item" : "items"}
            </span>
            {collection.view_count !== undefined && (
              <span className="flex items-center gap-1">
                <Eye className="w-3 h-3" />
                {collection.view_count}
              </span>
            )}
          </div>

          {/* Owner and Date */}
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            {collection.owner_name && <span>By {collection.owner_name}</span>}
            <span>{relativeTime}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="outline"
            size="sm"
            asChild
            className="w-full"
          >
            <Link href={`/collections/${collection.id}`}>
              View
            </Link>
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={onCopy}
            disabled={isCopying}
            className="w-full"
          >
            {isCopying ? (
              <>
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                Copying...
              </>
            ) : (
              <>
                <CopyIcon className="h-3 w-3 mr-1" />
                Copy
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
