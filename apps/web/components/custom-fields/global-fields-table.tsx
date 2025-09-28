"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "../../lib/utils";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Label } from "../ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";

interface CustomFieldRecord {
  id: number;
  entity: string;
  key: string;
  label: string;
  data_type: string;
  required: boolean;
  is_active: boolean;
  options?: string[] | null;
  validation?: Record<string, unknown> | null;
  display_order: number;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

interface CustomFieldListResponse {
  fields: CustomFieldRecord[];
}

export function GlobalFieldsTable() {
  const { data, isLoading, error, refetch } = useQuery<CustomFieldListResponse>({
    queryKey: ["global-fields"],
    queryFn: () => apiFetch<CustomFieldListResponse>("/v1/reference/custom-fields?include_inactive=1")
  });

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading field definitions…</p>;
  }

  if (error) {
    const message = error instanceof Error ? error.message : "Unable to load custom fields";
    return (
      <Card>
        <CardHeader>
          <CardTitle>Global fields</CardTitle>
          <CardDescription>Service error</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-destructive">{message}</p>
          <Button size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const records = data?.fields ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Global fields</CardTitle>
        <CardDescription>All dynamic attributes available to the importer, listings, and reference workspaces.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <Label className="text-xs uppercase text-muted-foreground">Total fields</Label>
          <span className="rounded-md bg-muted px-2 py-1 text-xs font-medium text-foreground">{records.length}</span>
        </div>
        <div className="overflow-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Entity</TableHead>
                <TableHead>Label</TableHead>
                <TableHead>Key</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Required</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Validation</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {records.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-sm text-muted-foreground">
                    No custom fields defined yet.
                  </TableCell>
                </TableRow>
              ) : (
                records.map((field) => (
                  <TableRow key={field.id}>
                    <TableCell className="capitalize">{field.entity.replace(/_/g, " ")}</TableCell>
                    <TableCell className="font-medium">{field.label}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{field.key}</TableCell>
                    <TableCell className="capitalize">{field.data_type.replace(/_/g, " ")}</TableCell>
                    <TableCell>{field.required ? "Yes" : "No"}</TableCell>
                    <TableCell>{field.deleted_at ? "Deleted" : field.is_active ? "Active" : "Inactive"}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {renderValidation(field)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

function renderValidation(field: CustomFieldRecord) {
  const items: string[] = [];
  if (field.options && field.options.length) {
    items.push(`options: ${field.options.join(", ")}`);
  }
  if (field.validation) {
    for (const [key, value] of Object.entries(field.validation)) {
      items.push(`${key}: ${String(value)}`);
    }
  }
  if (!items.length) {
    return "—";
  }
  return items.join(" · ");
}
