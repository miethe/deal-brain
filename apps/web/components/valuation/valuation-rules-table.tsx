"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "../../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";

interface ValuationRule {
  id: number;
  name: string;
  component_type: string;
  metric: string;
  unit_value_usd: number;
  condition_new: number;
  condition_refurb: number;
  condition_used: number;
}

export function ValuationRulesTable() {
  const { data, isLoading, error } = useQuery<ValuationRule[]>({
    queryKey: ["valuation-rules"],
    queryFn: () => apiFetch<ValuationRule[]>("/v1/catalog/valuation-rules")
  });

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading valuation rules…</p>;
  }

  if (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return <p className="text-sm text-destructive">Error loading valuation rules: {message}</p>;
  }

  if (!data?.length) {
    return <p className="text-sm text-muted-foreground">No valuation rules found. Import your Reference sheet to seed them.</p>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Valuation rules</CardTitle>
        <CardDescription>These deductions normalize RAM, storage, OS licenses, and more.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Component</TableHead>
              <TableHead>Metric</TableHead>
              <TableHead className="text-right">Unit value</TableHead>
              <TableHead className="text-right">New</TableHead>
              <TableHead className="text-right">Refurb</TableHead>
              <TableHead className="text-right">Used</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((rule) => (
              <TableRow key={rule.id}>
                <TableCell className="font-medium">{rule.name}</TableCell>
                <TableCell className="capitalize">{rule.component_type.replace(/_/g, " ")}</TableCell>
                <TableCell className="capitalize">{rule.metric.replace(/_/g, " ")}</TableCell>
                <TableCell className="text-right">${rule.unit_value_usd.toFixed(2)}</TableCell>
                <TableCell className="text-right">{rule.condition_new.toFixed(2)}</TableCell>
                <TableCell className="text-right">{rule.condition_refurb.toFixed(2)}</TableCell>
                <TableCell className="text-right">{rule.condition_used.toFixed(2)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
