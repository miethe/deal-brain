"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

interface UserShareResponse {
  id: number;
  share_token: string;
  recipient_id: number;
  listing_id: number;
  message?: string;
  created_at: string;
}

interface UserShareRequest {
  recipient_id: number;
  listing_id: number;
  message?: string;
}

/**
 * Hook to share a listing with a specific user
 */
export function useShareWithUser() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: UserShareRequest) => {
      return apiFetch<UserShareResponse>("/v1/user-shares", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onError: (err) => {
      let errorMessage = "Failed to share listing";

      if (err instanceof ApiError) {
        if (err.status === 429) {
          errorMessage = "Rate limit exceeded. Please try again later.";
        } else if (err.status === 404) {
          errorMessage = "User not found";
        } else {
          errorMessage = err.message;
        }
      }

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      // Invalidate user shares cache if it exists
      queryClient.invalidateQueries({ queryKey: ["user-shares"] });

      toast({
        title: "Success",
        description: "Listing shared successfully",
      });
    },
  });
}
