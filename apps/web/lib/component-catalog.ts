export const RAM_GENERATION_OPTIONS = [
  { value: "ddr3", label: "DDR3" },
  { value: "ddr4", label: "DDR4" },
  { value: "ddr5", label: "DDR5" },
  { value: "lpddr4", label: "LPDDR4" },
  { value: "lpddr4x", label: "LPDDR4X" },
  { value: "lpddr5", label: "LPDDR5" },
  { value: "lpddr5x", label: "LPDDR5X" },
  { value: "hbm2", label: "HBM2" },
  { value: "hbm3", label: "HBM3" },
  { value: "unknown", label: "Unknown" },
];

export function getRamGenerationLabel(value: string | null | undefined): string {
  if (!value) return "Unknown";
  const option = RAM_GENERATION_OPTIONS.find((item) => item.value === value.toLowerCase());
  return option ? option.label : value.toUpperCase();
}

export const STORAGE_MEDIUM_OPTIONS = [
  { value: "nvme", label: "NVMe" },
  { value: "sata_ssd", label: "SATA SSD" },
  { value: "hdd", label: "HDD" },
  { value: "hybrid", label: "Hybrid" },
  { value: "emmc", label: "eMMC" },
  { value: "ufs", label: "UFS" },
  { value: "unknown", label: "Unknown" },
];

export function getStorageMediumLabel(value: string | null | undefined): string {
  if (!value) return "Unknown";
  const normalized = value.toLowerCase();
  const option = STORAGE_MEDIUM_OPTIONS.find((item) => item.value === normalized);
  if (option) return option.label;
  switch (normalized) {
    case "ssd":
      return "SSD";
    case "sata":
      return "SATA SSD";
    case "nvme ssd":
      return "NVMe";
    case "hard drive":
    case "hard disk":
      return "HDD";
    default:
      return value.toUpperCase();
  }
}
