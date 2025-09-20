import { ImporterWorkspace } from "../../components/import/importer-workspace";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";

export default function ImportPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Import workbook</h1>
        <p className="text-sm text-muted-foreground">
          Upload a spreadsheet, confirm the mappings, resolve conflicts, and push the results into Deal Brain in minutes.
        </p>
      </div>
      <ImporterWorkspace />
      <Card>
        <CardHeader>
          <CardTitle>What the importer does</CardTitle>
          <CardDescription>Transforms CPUs, valuation references, component profiles, and listings into normalized tables with conflict-aware upserts.</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          The importer now runs through an interactive session: we inspect each sheet, auto map columns, surface
          conflicts (like existing CPUs), and let you confirm component matches before committing. Everything is logged
          for auditability and can be replayed from the session history.
        </CardContent>
      </Card>
    </div>
  );
}
