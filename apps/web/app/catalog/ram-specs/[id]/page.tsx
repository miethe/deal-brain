import { notFound } from "next/navigation";
import { apiFetch } from "@/lib/utils";
import { RAMSpecDetailLayout } from "@/components/catalog/ram-spec-detail-layout";

interface RAMSpec {
  id: number;
  capacity_gb: number;
  type?: string | null;
  speed_mhz?: number | null;
  latency?: string | null;
  voltage?: number | null;
  configuration?: string | null;
  manufacturer?: string | null;
  form_factor?: string | null;
  ecc_support?: boolean | null;
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

async function getRAMSpec(id: string): Promise<RAMSpec | null> {
  try {
    const ramSpec = await apiFetch<RAMSpec>(`/v1/catalog/ram-specs/${id}`);
    return ramSpec;
  } catch (error) {
    return null;
  }
}

async function getRAMSpecListings(id: string): Promise<Listing[]> {
  try {
    const listings = await apiFetch<Listing[]>(`/v1/catalog/ram-specs/${id}/listings?limit=50`);
    return listings;
  } catch (error) {
    return [];
  }
}

export default async function RAMSpecDetailPage({ params }: PageProps) {
  const ramSpec = await getRAMSpec(params.id);

  if (!ramSpec) {
    notFound();
  }

  const listings = await getRAMSpecListings(params.id);

  return <RAMSpecDetailLayout ramSpec={ramSpec} listings={listings} />;
}

export async function generateMetadata({ params }: PageProps) {
  const ramSpec = await getRAMSpec(params.id);

  if (!ramSpec) {
    return {
      title: "RAM Spec Not Found | Deal Brain",
    };
  }

  const title = `${ramSpec.capacity_gb}GB ${ramSpec.type || "RAM"}`;

  return {
    title: `${title} - RAM Spec Details | Deal Brain`,
    description: `${title} specifications and listings`,
  };
}
