import { notFound } from "next/navigation";
import { apiFetch } from "@/lib/utils";
import { StorageProfileDetailLayout } from "@/components/catalog/storage-profile-detail-layout";

interface StorageProfile {
  id: number;
  capacity_gb: number;
  type?: string | null;
  interface?: string | null;
  form_factor?: string | null;
  sequential_read_mb_s?: number | null;
  sequential_write_mb_s?: number | null;
  random_read_iops?: number | null;
  random_write_iops?: number | null;
  manufacturer?: string | null;
  model?: string | null;
  generation?: string | null;
  notes?: string | null;
}

interface Listing {
  id: number;
  title: string;
  price_usd: number;
  adjusted_price_usd: number | null;
  manufacturer?: string | null;
  model_number?: string | null;
  form_factor?: string | null;
  condition: string;
  status: string;
  cpu_name?: string | null;
  ram_gb?: number | null;
  primary_storage_gb?: number | null;
  primary_storage_type?: string | null;
}

interface PageProps {
  params: { id: string };
}

async function getStorageProfile(id: string): Promise<StorageProfile | null> {
  try {
    const storageProfile = await apiFetch<StorageProfile>(`/v1/catalog/storage-profiles/${id}`);
    return storageProfile;
  } catch (error) {
    return null;
  }
}

async function getStorageProfileListings(id: string): Promise<Listing[]> {
  try {
    const listings = await apiFetch<Listing[]>(`/v1/catalog/storage-profiles/${id}/listings?limit=50`);
    return listings;
  } catch (error) {
    return [];
  }
}

export default async function StorageProfileDetailPage({ params }: PageProps) {
  const storageProfile = await getStorageProfile(params.id);

  if (!storageProfile) {
    notFound();
  }

  const listings = await getStorageProfileListings(params.id);

  return <StorageProfileDetailLayout storageProfile={storageProfile} listings={listings} />;
}

export async function generateMetadata({ params }: PageProps) {
  const storageProfile = await getStorageProfile(params.id);

  if (!storageProfile) {
    return {
      title: "Storage Profile Not Found | Deal Brain",
    };
  }

  const capacityDisplay = storageProfile.capacity_gb >= 1024
    ? `${(storageProfile.capacity_gb / 1024).toFixed(0)}TB`
    : `${storageProfile.capacity_gb}GB`;
  const title = `${capacityDisplay} ${storageProfile.type || "Storage"}`;

  return {
    title: `${title} - Storage Profile Details | Deal Brain`,
    description: `${title} specifications, performance metrics, and listings`,
  };
}
