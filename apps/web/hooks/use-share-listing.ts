"use client";

import { useMutation } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

interface ShareLinkResponse {
  share_token: string;
  share_url: string;
  expires_at: string;
}

interface ShareLinkRequest {
  listing_id: number;
  expires_in_days?: number;
}

/**
 * Hook to generate a public share link for a listing
 */
export function useShareListing() {
  const { toast } = useToast();

  return useMutation({
    mutationFn: async ({ listing_id, expires_in_days = 180 }: ShareLinkRequest) => {
      return apiFetch<ShareLinkResponse>(`/v1/listings/${listing_id}/share`, {
        method: "POST",
        body: JSON.stringify({ expires_in_days }),
      });
    },
    onError: (err) => {
      const errorMessage = err instanceof ApiError ? err.message : "Failed to generate share link";

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      toast({
        title: "Success",
        description: "Share link generated successfully",
      });
    },
  });
}
