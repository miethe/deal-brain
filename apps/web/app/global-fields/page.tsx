import { GlobalFieldsTable } from "../../components/custom-fields/global-fields-table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";

export default function GlobalFieldsPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-semibold tracking-tight">Global fields</h1>
        <p className="text-sm text-muted-foreground">
          Define, review, and audit dynamic attributes available across listings, CPUs, GPUs, ports, and valuation rules.
        </p>
      </div>
      <GlobalFieldsTable />
      <Card>
        <CardHeader>
          <CardTitle>How to add new fields</CardTitle>
          <CardDescription>Use the importer or API to create and manage custom fields.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            During a mapping session, click <strong>Add field</strong> to launch the builder modal. Fields can also be
            created via <code>POST /v1/reference/custom-fields</code> if you want to seed them programmatically.
          </p>
          <p>
            Soft delete a field from the API when it should disappear from forms and grids. Historical data remains in
            `attributes_json` until you remove it explicitly.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
