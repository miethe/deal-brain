"use client";

import { FormEvent, useMemo, useState } from "react";

import {
  AdminTaskStatus,
  AdminTaskSubmission,
  fetchTaskStatus,
  triggerCpuMarkRecalc,
  triggerEntityImport,
  triggerMetricsRecalc,
  triggerPassmarkImport,
  triggerValuationRecalc,
} from "../../lib/api/admin";
import { ApiError } from "../../lib/utils";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import { Checkbox } from "../../components/ui/checkbox";

interface TrackedTask {
  info: AdminTaskSubmission;
  status?: AdminTaskStatus;
  loading?: boolean;
}

const ENTITY_OPTIONS = [
  { value: "cpu", label: "CPUs" },
  { value: "gpu", label: "GPUs" },
  { value: "profile", label: "Profiles" },
  { value: "ports_profile", label: "Ports Profiles" },
  { value: "listing", label: "Listings" },
];

function parseListingIds(input: string): number[] | undefined {
  const trimmed = input.trim();
  if (!trimmed) {
    return undefined;
  }
  const values = trimmed
    .split(/[,\s]+/)
    .map((token) => token.trim())
    .filter(Boolean);

  const numbers: number[] = [];
  for (const token of values) {
    const parsed = Number.parseInt(token, 10);
    if (!Number.isNaN(parsed) && parsed >= 0) {
      numbers.push(parsed);
    }
  }
  return numbers.length ? numbers : undefined;
}

export default function AdminActionsPage() {
  const [trackedTasks, setTrackedTasks] = useState<TrackedTask[]>([]);

  const [valuationIdsText, setValuationIdsText] = useState("");
  const [valuationRulesetId, setValuationRulesetId] = useState("");
  const [valuationReason, setValuationReason] = useState("");
  const [valuationIncludeInactive, setValuationIncludeInactive] = useState(false);
  const [valuationMessage, setValuationMessage] = useState<string | null>(null);
  const [valuationError, setValuationError] = useState<string | null>(null);
  const [valuationPending, setValuationPending] = useState(false);

  const [metricsIdsText, setMetricsIdsText] = useState("");
  const [metricsMessage, setMetricsMessage] = useState<string | null>(null);
  const [metricsError, setMetricsError] = useState<string | null>(null);
  const [metricsPending, setMetricsPending] = useState(false);

  const [cpuIdsText, setCpuIdsText] = useState("");
  const [cpuMessage, setCpuMessage] = useState<string | null>(null);
  const [cpuError, setCpuError] = useState<string | null>(null);
  const [cpuPending, setCpuPending] = useState(false);

  const [passmarkFile, setPassmarkFile] = useState<File | null>(null);
  const [passmarkMessage, setPassmarkMessage] = useState<string | null>(null);
  const [passmarkError, setPassmarkError] = useState<string | null>(null);
  const [passmarkPending, setPassmarkPending] = useState(false);

  const [entityFile, setEntityFile] = useState<File | null>(null);
  const [entityType, setEntityType] = useState("cpu");
  const [entityDryRun, setEntityDryRun] = useState(false);
  const [entityMessage, setEntityMessage] = useState<string | null>(null);
  const [entityError, setEntityError] = useState<string | null>(null);
  const [entityPending, setEntityPending] = useState(false);

  const listingIdsHelp = useMemo(
    () => "Optional comma or space separated list of listing IDs.",
    []
  );

  const pushTask = (submission: AdminTaskSubmission) => {
    setTrackedTasks((prev) => [
      { info: submission, status: undefined, loading: false },
      ...prev,
    ]);
  };

  const handleStatusRefresh = async (taskId: string) => {
    setTrackedTasks((prev) =>
      prev.map((item) =>
        item.info.task_id === taskId ? { ...item, loading: true } : item
      )
    );
    try {
      const status = await fetchTaskStatus(taskId);
      setTrackedTasks((prev) =>
        prev.map((item) =>
          item.info.task_id === taskId ? { ...item, status, loading: false } : item
        )
      );
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Failed to fetch task status.";
      setTrackedTasks((prev) =>
        prev.map((item) =>
          item.info.task_id === taskId
            ? {
                ...item,
                loading: false,
                status: {
                  task_id: taskId,
                  action: item.info.action,
                  status: "error",
                  state: "FAILURE",
                  error: message,
                },
              }
            : item
        )
      );
    }
  };

  const handleValuationSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setValuationPending(true);
    setValuationError(null);
    setValuationMessage(null);
    try {
      const payload = {
        listing_ids: parseListingIds(valuationIdsText),
        include_inactive: valuationIncludeInactive,
        reason: valuationReason || undefined,
        ruleset_id: valuationRulesetId ? Number.parseInt(valuationRulesetId, 10) : undefined,
      };
      const submission = await triggerValuationRecalc(payload);
      setValuationMessage(`Queued task ${submission.task_id}`);
      pushTask(submission);
    } catch (error) {
      setValuationError(
        error instanceof ApiError ? error.message : "Failed to queue valuation job."
      );
    } finally {
      setValuationPending(false);
    }
  };

  const handleMetricsSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setMetricsPending(true);
    setMetricsError(null);
    setMetricsMessage(null);
    try {
      const payload = { listing_ids: parseListingIds(metricsIdsText) };
      const submission = await triggerMetricsRecalc(payload);
      setMetricsMessage(`Queued task ${submission.task_id}`);
      pushTask(submission);
    } catch (error) {
      setMetricsError(
        error instanceof ApiError ? error.message : "Failed to queue metrics job."
      );
    } finally {
      setMetricsPending(false);
    }
  };

  const handleCpuSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setCpuPending(true);
    setCpuError(null);
    setCpuMessage(null);
    try {
      const payload = { listing_ids: parseListingIds(cpuIdsText) };
      const submission = await triggerCpuMarkRecalc(payload);
      setCpuMessage(`Queued task ${submission.task_id}`);
      pushTask(submission);
    } catch (error) {
      setCpuError(
        error instanceof ApiError ? error.message : "Failed to queue CPU mark job."
      );
    } finally {
      setCpuPending(false);
    }
  };

  const handlePassmarkSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!passmarkFile) {
      setPassmarkError("Select a CSV or JSON file before importing.");
      return;
    }
    setPassmarkPending(true);
    setPassmarkError(null);
    setPassmarkMessage(null);
    try {
      const submission = await triggerPassmarkImport(passmarkFile);
      setPassmarkMessage(`Queued task ${submission.task_id}`);
      pushTask(submission);
      setPassmarkFile(null);
    } catch (error) {
      setPassmarkError(
        error instanceof ApiError ? error.message : "Failed to queue PassMark import."
      );
    } finally {
      setPassmarkPending(false);
    }
  };

  const handleEntitySubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!entityFile) {
      setEntityError("Select a file to import.");
      return;
    }
    setEntityPending(true);
    setEntityError(null);
    setEntityMessage(null);
    try {
      const submission = await triggerEntityImport(entityType, entityFile, entityDryRun);
      setEntityMessage(`Queued task ${submission.task_id}`);
      pushTask(submission);
      if (!entityDryRun) {
        setEntityFile(null);
      }
    } catch (error) {
      setEntityError(
        error instanceof ApiError ? error.message : "Failed to queue entity import."
      );
    } finally {
      setEntityPending(false);
    }
  };

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-semibold">Admin Actions</h1>
        <p className="text-muted-foreground">
          Trigger backend maintenance jobs and imports. Track status of queued tasks below.
        </p>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <form onSubmit={handleValuationSubmit}>
            <CardHeader>
              <CardTitle>Recalculate Valuations</CardTitle>
              <CardDescription>
                Queue Celery job to rerun listing valuation rules. Leave listing IDs empty to
                process all active listings.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="valuation-ids">Listing IDs</Label>
                <Textarea
                  id="valuation-ids"
                  placeholder="e.g. 10, 25, 912"
                  value={valuationIdsText}
                  onChange={(event) => setValuationIdsText(event.target.value)}
                />
                <p className="text-xs text-muted-foreground">{listingIdsHelp}</p>
              </div>
              <div>
                <Label htmlFor="valuation-ruleset">Ruleset Override</Label>
                <Input
                  id="valuation-ruleset"
                  placeholder="Ruleset ID (optional)"
                  value={valuationRulesetId}
                  onChange={(event) => setValuationRulesetId(event.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="valuation-reason">Reason</Label>
                <Input
                  id="valuation-reason"
                  placeholder="Log reason for audit trail"
                  value={valuationReason}
                  onChange={(event) => setValuationReason(event.target.value)}
                />
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="valuation-include-inactive"
                  checked={valuationIncludeInactive}
                  onCheckedChange={(checked) => setValuationIncludeInactive(Boolean(checked))}
                />
                <Label htmlFor="valuation-include-inactive">Include inactive listings</Label>
              </div>
              {valuationError && <p className="text-sm text-destructive">{valuationError}</p>}
              {valuationMessage && <p className="text-sm text-emerald-600">{valuationMessage}</p>}
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={valuationPending}>
                {valuationPending ? "Queuing…" : "Queue Valuation Job"}
              </Button>
            </CardFooter>
          </form>
        </Card>

        <Card>
          <form onSubmit={handleMetricsSubmit}>
            <CardHeader>
              <CardTitle>Refresh Listing Metrics</CardTitle>
              <CardDescription>
                Recompute CPU/GPU metrics and dollar-per-mark fields across listings.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="metrics-ids">Listing IDs</Label>
                <Textarea
                  id="metrics-ids"
                  placeholder="e.g. 10 25 912"
                  value={metricsIdsText}
                  onChange={(event) => setMetricsIdsText(event.target.value)}
                />
                <p className="text-xs text-muted-foreground">{listingIdsHelp}</p>
              </div>
              {metricsError && <p className="text-sm text-destructive">{metricsError}</p>}
              {metricsMessage && <p className="text-sm text-emerald-600">{metricsMessage}</p>}
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={metricsPending}>
                {metricsPending ? "Queuing…" : "Queue Metrics Job"}
              </Button>
            </CardFooter>
          </form>
        </Card>

        <Card>
          <form onSubmit={handleCpuSubmit}>
            <CardHeader>
              <CardTitle>Recalculate CPU Mark Ratios</CardTitle>
              <CardDescription>
                Updates dollar-per-CPU-mark fields using current adjusted prices.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="cpu-ids">Listing IDs</Label>
                <Textarea
                  id="cpu-ids"
                  placeholder="Leave blank for all listings with CPUs"
                  value={cpuIdsText}
                  onChange={(event) => setCpuIdsText(event.target.value)}
                />
                <p className="text-xs text-muted-foreground">{listingIdsHelp}</p>
              </div>
              {cpuError && <p className="text-sm text-destructive">{cpuError}</p>}
              {cpuMessage && <p className="text-sm text-emerald-600">{cpuMessage}</p>}
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={cpuPending}>
                {cpuPending ? "Queuing…" : "Queue CPU Mark Job"}
              </Button>
            </CardFooter>
          </form>
        </Card>

        <Card>
          <form onSubmit={handlePassmarkSubmit}>
            <CardHeader>
              <CardTitle>Import PassMark Data</CardTitle>
              <CardDescription>
                Upload a PassMark CPU dataset (CSV or JSON) to merge into the catalog.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="passmark-file">PassMark File</Label>
                <Input
                  id="passmark-file"
                  type="file"
                  accept=".csv,.json"
                  onChange={(event) => {
                    const file = event.target.files?.item(0) ?? null;
                    setPassmarkFile(file);
                  }}
                />
              </div>
              {passmarkError && <p className="text-sm text-destructive">{passmarkError}</p>}
              {passmarkMessage && <p className="text-sm text-emerald-600">{passmarkMessage}</p>}
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={passmarkPending}>
                {passmarkPending ? "Queuing…" : "Queue PassMark Import"}
              </Button>
            </CardFooter>
          </form>
        </Card>

        <Card className="md:col-span-2">
          <form onSubmit={handleEntitySubmit}>
            <CardHeader>
              <CardTitle>Universal Entity Import</CardTitle>
              <CardDescription>
                Upload CSV or JSON payload for supported entities. Use dry-run to validate without
                persisting.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="entity-type">Entity Type</Label>
                  <select
                    id="entity-type"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    value={entityType}
                    onChange={(event) => setEntityType(event.target.value)}
                  >
                    {ENTITY_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="entity-file">Payload File</Label>
                  <Input
                    id="entity-file"
                    type="file"
                    accept=".csv,.json"
                    onChange={(event) => {
                      const file = event.target.files?.item(0) ?? null;
                      setEntityFile(file);
                    }}
                  />
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="entity-dry-run"
                  checked={entityDryRun}
                  onCheckedChange={(checked) => setEntityDryRun(Boolean(checked))}
                />
                <Label htmlFor="entity-dry-run">Dry run (validate only)</Label>
              </div>
              {entityError && <p className="text-sm text-destructive">{entityError}</p>}
              {entityMessage && <p className="text-sm text-emerald-600">{entityMessage}</p>}
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={entityPending}>
                {entityPending ? "Queuing…" : "Queue Entity Import"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>

      <section className="space-y-4">
        <div>
          <h2 className="text-2xl font-semibold">Queued Tasks</h2>
          <p className="text-sm text-muted-foreground">
            Use the refresh button to pull the latest status from Celery.
          </p>
        </div>
        {trackedTasks.length === 0 ? (
          <p className="text-sm text-muted-foreground">No tasks queued yet.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border">
            <table className="min-w-full divide-y divide-border text-sm">
              <thead className="bg-muted/60">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Task ID</th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Action</th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Status</th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">
                    Last Result
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border bg-background">
                {trackedTasks.map((task) => (
                  <tr key={task.info.task_id}>
                    <td className="px-3 py-2 font-mono text-xs">{task.info.task_id}</td>
                    <td className="px-3 py-2">{task.info.action}</td>
                    <td className="px-3 py-2">
                      {task.status?.state ?? task.info.status}
                      {task.status?.error && (
                        <span className="ml-2 text-xs text-destructive">{task.status.error}</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {task.status?.result
                        ? JSON.stringify(task.status.result)
                        : task.info.metadata
                        ? JSON.stringify(task.info.metadata)
                        : "—"}
                    </td>
                    <td className="px-3 py-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={task.loading}
                        onClick={() => handleStatusRefresh(task.info.task_id)}
                      >
                        {task.loading ? "Refreshing..." : "Refresh"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
