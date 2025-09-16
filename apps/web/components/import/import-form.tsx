"use client";

import { useState } from "react";

import { apiFetch } from "../../lib/utils";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { Label } from "../ui/label";

interface ImportResponse {
  status: string;
  path: string;
  counts: Record<string, number>;
}

export function ImportForm() {
  const [path, setPath] = useState("./data/imports/deal-brain.xlsx");
  const [result, setResult] = useState<ImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const response = await apiFetch<ImportResponse>("/v1/imports/workbook", {
        method: "POST",
        body: JSON.stringify({ path })
      });
      setResult(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Import your workbook</CardTitle>
        <CardDescription>Transforms the Excel sheet into seed data for CPUs, GPUs, valuation rules, and listings.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="path">Workbook path</Label>
            <Input
              id="path"
              name="path"
              value={path}
              onChange={(event) => setPath(event.target.value)}
              placeholder="./data/imports/deal-brain.xlsx"
            />
            <p className="text-xs text-muted-foreground">
              Drop the Excel file into <code>data/imports</code> and reference it here. The backend uses pandas + the importer to seed tables.
            </p>
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Importing…" : "Run import"}
          </Button>
        </form>
        {result && (
          <div className="mt-4 rounded-md border p-4 text-sm">
            <div className="font-medium text-foreground">Import complete</div>
            <div className="text-muted-foreground">Source: {result.path}</div>
            <ul className="mt-2 space-y-1">
              {Object.entries(result.counts).map(([key, value]) => (
                <li key={key} className="flex justify-between">
                  <span className="capitalize">{key.replace(/_/g, " ")}</span>
                  <span>{value}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {error && <p className="mt-4 text-sm text-destructive">{error}</p>}
      </CardContent>
    </Card>
  );
}
