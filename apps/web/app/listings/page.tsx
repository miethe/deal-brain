import { ListingsTable } from "../../components/listings/listings-table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import Link from "next/link";

export default function ListingsPage() {
  return (
    <div className="w-full space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Listings</h1>
          <p className="text-sm text-muted-foreground">Every deal, normalized and scored in one table.</p>
        </div>
        <Button asChild>
          <Link href="/listings/new">Add listing</Link>
        </Button>
      </div>
      <ListingsTable />
      <Card>
        <CardHeader>
          <CardTitle>How scoring works</CardTitle>
          <CardDescription>Composite scores update automatically after each valuation run.</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Adjusted price removes RAM, storage, and OS value using your valuation rules. Composite scores blend CPU, GPU,
          perf-per-watt, and RAM metrics according to the active profile, so the table is always ready for comparison.
        </CardContent>
      </Card>
    </div>
  );
}
