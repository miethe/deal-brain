interface CpuInfoPanelProps {
  cpu: {
    name: string;
    cpu_mark_single?: number | null;
    cpu_mark_multi?: number | null;
    tdp_w?: number | null;
    release_year?: number | null;
    igpu_model?: string | null;
    igpu_mark?: number | null;
  } | null;
}

export function CpuInfoPanel({ cpu }: CpuInfoPanelProps) {
  if (!cpu) {
    return (
      <div className="rounded-lg border bg-muted/10 p-3 text-sm text-muted-foreground">
        No CPU selected
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-muted/20 p-3 space-y-2">
      <h4 className="text-sm font-semibold text-foreground">{cpu.name}</h4>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div>
          <span className="text-muted-foreground">Single-Thread:</span>{" "}
          <span className="font-medium text-foreground">
            {cpu.cpu_mark_single?.toLocaleString() || "—"}
          </span>
        </div>
        <div>
          <span className="text-muted-foreground">TDP:</span>{" "}
          <span className="font-medium text-foreground">
            {cpu.tdp_w ? `${cpu.tdp_w}W` : "—"}
          </span>
        </div>
        <div>
          <span className="text-muted-foreground">Multi-Thread:</span>{" "}
          <span className="font-medium text-foreground">
            {cpu.cpu_mark_multi?.toLocaleString() || "—"}
          </span>
        </div>
        <div>
          <span className="text-muted-foreground">Year:</span>{" "}
          <span className="font-medium text-foreground">
            {cpu.release_year || "—"}
          </span>
        </div>
        <div className="col-span-2 pt-1 border-t border-border">
          <span className="text-muted-foreground">iGPU:</span>{" "}
          <span className="font-medium text-foreground">
            {cpu.igpu_model
              ? `${cpu.igpu_model} ${cpu.igpu_mark ? `(G3D: ${cpu.igpu_mark.toLocaleString()})` : ""}`
              : "None"}
          </span>
        </div>
      </div>
    </div>
  );
}
