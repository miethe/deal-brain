export interface PerUnitMetricOption {
  value: string;
  label: string;
  description?: string;
  aliases?: string[];
}

export const PER_UNIT_METRIC_OPTIONS: PerUnitMetricOption[] = [
  {
    value: "ram_gb",
    label: "RAM (GB)",
    aliases: ["per_gb"],
    description: "Uses the listing's RAM capacity in gigabytes.",
  },
  {
    value: "ram_spec.total_capacity_gb",
    label: "RAM Spec Capacity (GB)",
    aliases: ["per_ram_spec_gb"],
    description: "Resolved RAM capacity from the linked RAM specification.",
  },
  {
    value: "ram_spec.speed_mhz",
    label: "RAM Speed (MHz)",
    aliases: ["per_ram_speed"],
    description: "Resolved RAM speed from the linked RAM specification.",
  },
  {
    value: "primary_storage_gb",
    label: "Primary Storage (GB)",
    aliases: ["storage.primary_gb", "per_tb"],
    description: "Primary drive capacity in gigabytes (automatically converts TB).",
  },
  {
    value: "storage.primary.capacity_gb",
    label: "Primary Storage Profile (GB)",
    aliases: ["per_primary_storage_gb"],
    description: "Primary storage capacity resolved from the linked profile.",
  },
  {
    value: "secondary_storage_gb",
    label: "Secondary Storage (GB)",
    aliases: ["storage.secondary_gb"],
  },
  {
    value: "storage.secondary.capacity_gb",
    label: "Secondary Storage Profile (GB)",
    aliases: ["per_secondary_storage_gb"],
  },
  {
    value: "cpu.cores",
    label: "CPU Cores",
    aliases: ["per_core"],
  },
  {
    value: "cpu.threads",
    label: "CPU Threads",
    aliases: ["per_thread"],
  },
  {
    value: "cpu.cpu_mark_multi",
    label: "CPU Mark (Multi)",
  },
  {
    value: "cpu.cpu_mark_single",
    label: "CPU Mark (Single)",
  },
  {
    value: "gpu.gpu_mark",
    label: "GPU Benchmark Score",
  },
  {
    value: "gpu.metal_score",
    label: "GPU Metal Score",
  },
  {
    value: "quantity",
    label: "Component Quantity",
    description: "Use when referencing the quantity field provided in action context.",
  },
];

const METRIC_ALIAS_LOOKUP = PER_UNIT_METRIC_OPTIONS.reduce<Record<string, PerUnitMetricOption>>(
  (accumulator, option) => {
    accumulator[option.value] = option;
    for (const alias of option.aliases ?? []) {
      accumulator[alias] = option;
    }
    return accumulator;
  },
  {},
);

export function normalizePerUnitMetric(metric: string | null | undefined): string | undefined {
  if (!metric) {
    return undefined;
  }
  const match = METRIC_ALIAS_LOOKUP[metric];
  return match ? match.value : metric;
}

export function getPerUnitMetricLabel(metric: string | null | undefined): string | undefined {
  if (!metric) {
    return undefined;
  }
  const match = METRIC_ALIAS_LOOKUP[metric] ?? PER_UNIT_METRIC_OPTIONS.find(
    (option) => option.value === metric,
  );
  return match?.label ?? metric;
}
