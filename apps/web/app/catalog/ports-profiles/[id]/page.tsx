import { notFound } from "next/navigation";
import { apiFetch } from "@/lib/utils";
import { PortsProfileDetailLayout } from "@/components/catalog/ports-profile-detail-layout";

interface Port {
  id: number;
  type: string;
  count: number;
  spec_notes?: string | null;
}

interface PortsProfile {
  id: number;
  name: string;
  description?: string | null;
  attributes?: Record<string, any>;
  ports: Port[];
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

async function getPortsProfile(id: string): Promise<PortsProfile | null> {
  try {
    const profile = await apiFetch<PortsProfile>(`/v1/catalog/ports-profiles/${id}`);
    return profile;
  } catch (error) {
    return null;
  }
}

async function getPortsProfileListings(id: string): Promise<Listing[]> {
  try {
    const listings = await apiFetch<Listing[]>(`/v1/catalog/ports-profiles/${id}/listings?limit=50`);
    return listings;
  } catch (error) {
    return [];
  }
}

export default async function PortsProfileDetailPage({ params }: PageProps) {
  const profile = await getPortsProfile(params.id);

  if (!profile) {
    notFound();
  }

  const listings = await getPortsProfileListings(params.id);

  return <PortsProfileDetailLayout profile={profile} listings={listings} />;
}

export async function generateMetadata({ params }: PageProps) {
  const profile = await getPortsProfile(params.id);

  if (!profile) {
    return {
      title: "Ports Profile Not Found | Deal Brain",
    };
  }

  return {
    title: `${profile.name} - Ports Profile Details | Deal Brain`,
    description: `${profile.name} ports profile specifications and listings`,
  };
}
