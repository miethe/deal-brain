"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "../../lib/utils";
import { Badge } from "../ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";

interface Profile {
  id: number;
  name: string;
  description?: string | null;
  weights_json: Record<string, number>;
  is_default: boolean;
}

export function ProfileList() {
  const { data, isLoading, error } = useQuery<Profile[]>({
    queryKey: ["profiles"],
    queryFn: () => apiFetch<Profile[]>("/v1/catalog/profiles")
  });

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading profiles…</p>;
  }

  if (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return <p className="text-sm text-destructive">Error loading profiles: {message}</p>;
  }

  if (!data?.length) {
    return <p className="text-sm text-muted-foreground">No profiles yet—import your sheet or add one via the API.</p>;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {data.map((profile) => (
        <Card key={profile.id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{profile.name}</CardTitle>
                <CardDescription>{profile.description ?? "No description provided."}</CardDescription>
              </div>
              {profile.is_default && <Badge>Default</Badge>}
            </div>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm text-muted-foreground">
              {Object.entries(profile.weights_json).map(([metric, weight]) => (
                <li key={metric} className="flex justify-between">
                  <span className="capitalize">{metric.replace(/_/g, " ")}</span>
                  <span className="font-medium text-foreground">{weight.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
