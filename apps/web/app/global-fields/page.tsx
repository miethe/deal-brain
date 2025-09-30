import { GlobalFieldsWorkspace } from "../../components/custom-fields/global-fields-workspace";

export default function GlobalFieldsPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-1">
        <h1 className="text-3xl font-semibold tracking-tight">Global catalog workspace</h1>
        <p className="text-sm text-muted-foreground">
          Define dynamic fields and manage catalog data across listings, CPUs, and supporting entities.
        </p>
      </div>
      <GlobalFieldsWorkspace />
    </div>
  );
}
