import { DashboardSummary } from "../components/dashboard/dashboard-summary";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">Today&apos;s snapshot</h1>
        <p className="text-sm text-muted-foreground">
          Live metrics sourced from the FastAPI backend. Import your sheet or add a listing and the dashboard updates instantly.
        </p>
      </div>
      <DashboardSummary />
      <Card>
        <CardHeader>
          <CardTitle>Next steps</CardTitle>
          <CardDescription>Jump into the primary workflows as you continue building the MVP.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button asChild>
            <Link href="/listings">Add or review listings</Link>
          </Button>
          <Button asChild variant="secondary">
            <Link href="/profiles">Tune scoring profiles</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/valuation-rules">Adjust valuation rules</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
