import { ImportForm } from "../../components/import/import-form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";

export default function ImportPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Import workbook</h1>
        <p className="text-sm text-muted-foreground">
          Use your existing Excel workbook to populate CPUs, GPUs, valuation rules, and listings.
        </p>
      </div>
      <ImportForm />
      <Card>
        <CardHeader>
          <CardTitle>What the importer does</CardTitle>
          <CardDescription>Transforms the CPU, Reference, SFF PCs, and Macs sheets into normalized tables.</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Under the hood we run the spreadsheet importer defined in the FastAPI service. It uses pandas to parse each
          sheet, maps component types, and feeds the valuation engine. The CLI exposes the same workflow for headless
          usage.
        </CardContent>
      </Card>
    </div>
  );
}
