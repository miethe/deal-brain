import { ValuationRulesTable } from "../../components/valuation/valuation-rules-table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";

export default function ValuationRulesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Valuation rules</h1>
        <p className="text-sm text-muted-foreground">Control how RAM, storage, and extras are normalized to a barebones price.</p>
      </div>
      <ValuationRulesTable />
      <Card>
        <CardHeader>
          <CardTitle>Preview engine coming soon</CardTitle>
          <CardDescription>UI support for testing rule tweaks is on the roadmap.</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Today you can edit rules via the API or CLI. Once you adjust a rule, recalculating a listing will refresh its
          adjusted price and explainable breakdown immediately.
        </CardContent>
      </Card>
    </div>
  );
}
