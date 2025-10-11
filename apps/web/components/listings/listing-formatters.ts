import type { ListingRecord, StorageProfileRecord } from "@/types/listings";

const formatMedium = (value?: string | null): string | null => {
  if (!value) return null;
  const normalized = value.replace(/_/g, " ");
  return normalized.toUpperCase();
};

export const formatRamSummary = (listing: ListingRecord): string | null => {
  const spec = listing.ram_spec ?? null;
  const totalCapacity = spec?.total_capacity_gb ?? listing.ram_gb ?? null;
  const generation = spec?.ddr_generation ?? listing.ram_type ?? null;
  const speed = spec?.speed_mhz ?? listing.ram_speed_mhz ?? null;
  const moduleDescriptor = spec?.module_count && spec?.capacity_per_module_gb
    ? `${spec.module_count}x${spec.capacity_per_module_gb}GB`
    : null;

  const segments: string[] = [];
  if (totalCapacity) segments.push(`${totalCapacity}GB`);
  if (generation) segments.push(formatMedium(generation) ?? generation);
  if (speed) segments.push(`${speed}MHz`);

  if (!segments.length) {
    return null;
  }

  const joined = segments.join(" · ");
  return moduleDescriptor ? `${joined} (${moduleDescriptor})` : joined;
};

export const formatStorageSummary = (
  profile: StorageProfileRecord | null | undefined,
  fallbackCapacity: number | null | undefined,
  fallbackType: string | null | undefined,
): string | null => {
  const capacity = profile?.capacity_gb ?? fallbackCapacity ?? null;
  const medium = profile?.medium ?? fallbackType ?? null;
  const interfaceName = profile?.interface ?? null;
  const formFactor = profile?.form_factor ?? null;

  const segments: string[] = [];
  if (medium) segments.push(formatMedium(medium) ?? medium);
  if (capacity) segments.push(`${capacity}GB`);
  if (interfaceName) segments.push(interfaceName);
  if (formFactor) segments.push(formFactor);

  return segments.length ? segments.join(" · ") : null;
};
