"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/utils";

export interface User {
  id: number;
  username: string;
  email: string;
}

interface UserSearchResponse {
  users: User[];
}

/**
 * Hook to search for users by username or email
 */
export function useUserSearch(query: string, enabled = true) {
  return useQuery({
    queryKey: ["users", "search", query],
    queryFn: async () => {
      if (!query.trim()) {
        return { users: [] };
      }

      return apiFetch<UserSearchResponse>(`/v1/users/search?q=${encodeURIComponent(query)}&limit=10`);
    },
    enabled: enabled && query.trim().length > 0,
    staleTime: 30000, // Cache results for 30 seconds
  });
}
