/**
 * CPU field options for enhanced data entry
 */

export const MANUFACTURER_OPTIONS = [
  { label: "Intel", value: "Intel" },
  { label: "AMD", value: "AMD" },
  { label: "Apple", value: "Apple" },
  { label: "Qualcomm", value: "Qualcomm" },
  { label: "MediaTek", value: "MediaTek" },
  { label: "Other", value: "Other" },
];

export const SERIES_OPTIONS_INTEL = [
  { label: "Core i3", value: "Core i3" },
  { label: "Core i5", value: "Core i5" },
  { label: "Core i7", value: "Core i7" },
  { label: "Core i9", value: "Core i9" },
  { label: "Xeon", value: "Xeon" },
  { label: "Pentium", value: "Pentium" },
  { label: "Celeron", value: "Celeron" },
];

export const SERIES_OPTIONS_AMD = [
  { label: "Ryzen 3", value: "Ryzen 3" },
  { label: "Ryzen 5", value: "Ryzen 5" },
  { label: "Ryzen 7", value: "Ryzen 7" },
  { label: "Ryzen 9", value: "Ryzen 9" },
  { label: "Threadripper", value: "Threadripper" },
  { label: "EPYC", value: "EPYC" },
  { label: "Athlon", value: "Athlon" },
];

export function getSeriesOptions(manufacturer: string) {
  if (manufacturer === "Intel") return SERIES_OPTIONS_INTEL;
  if (manufacturer === "AMD") return SERIES_OPTIONS_AMD;
  return [];
}

export const CORES_OPTIONS = [
  { label: "1", value: "1" },
  { label: "2", value: "2" },
  { label: "4", value: "4" },
  { label: "6", value: "6" },
  { label: "8", value: "8" },
  { label: "10", value: "10" },
  { label: "12", value: "12" },
  { label: "14", value: "14" },
  { label: "16", value: "16" },
  { label: "20", value: "20" },
  { label: "24", value: "24" },
  { label: "32", value: "32" },
  { label: "64", value: "64" },
  { label: "128", value: "128" },
];

export const THREADS_OPTIONS = [
  { label: "2", value: "2" },
  { label: "4", value: "4" },
  { label: "8", value: "8" },
  { label: "12", value: "12" },
  { label: "16", value: "16" },
  { label: "20", value: "20" },
  { label: "24", value: "24" },
  { label: "28", value: "28" },
  { label: "32", value: "32" },
  { label: "40", value: "40" },
  { label: "48", value: "48" },
  { label: "64", value: "64" },
  { label: "128", value: "128" },
  { label: "256", value: "256" },
];
