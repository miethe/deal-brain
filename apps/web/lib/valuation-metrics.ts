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
    value: "primary_storage_gb",
    label: "Primary Storage (GB)",
    aliases: ["storage.primary_gb", "per_tb"],
    description: "Primary drive capacity in gigabytes (automatically converts TB).",
  },
  {
    value: "secondary_storage_gb",
    label: "Secondary Storage (GB)",
    aliases: ["storage.secondary_gb"],
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
