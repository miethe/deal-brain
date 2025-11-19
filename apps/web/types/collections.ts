/**
 * TypeScript types for Collections API
 */

import type { ListingRecord } from "./listings";

export type CollectionVisibility = "private" | "unlisted" | "public";

export type CollectionItemStatus = "undecided" | "shortlisted" | "rejected" | "bought";

export interface Collection {
  id: number;
  name: string;
  description?: string;
  visibility: CollectionVisibility;
  item_count: number;
  created_at: string;
  updated_at: string;
  // Sharing metadata
  share_url?: string;
  view_count?: number;
  owner_name?: string;
}

export interface CollectionItem {
  id: number;
  listing_id: number;
  status: CollectionItemStatus;
  notes?: string | null;
  position?: number | null;
  added_at: string;
  listing: ListingRecord;
  // Shared metadata (populated when item was added via share link)
  share_id?: number | null;
  shared_by_name?: string | null;
  shared_at?: string | null;
}

export interface CollectionWithItems extends Collection {
  items: CollectionItem[];
}

export interface CollectionsListResponse {
  collections: Collection[];
  total: number;
}

export interface CreateCollectionPayload {
  name: string;
  description?: string;
  visibility?: CollectionVisibility;
}

export interface UpdateCollectionItemPayload {
  status?: CollectionItemStatus;
  notes?: string;
  position?: number;
}

export interface UpdateCollectionVisibilityPayload {
  visibility: CollectionVisibility;
}

export interface DiscoverCollectionsParams {
  search?: string;
  owner_filter?: string;
  sort?: "recent" | "popular";
  limit?: number;
  offset?: number;
}

export interface DiscoverCollectionsResponse {
  collections: Collection[];
  total: number;
}

export interface CopyCollectionPayload {
  source_collection_id: number;
  name?: string;
}
