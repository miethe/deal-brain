import { notFound } from "next/navigation";
import { apiFetch } from "@/lib/utils";
import { CPUDetailLayout } from "@/components/catalog/cpu-detail-layout";

interface CPU {
  id: number;
  model: string;
  manufacturer: string;
  generation?: string | null;
  cores?: number | null;
  threads?: number | null;
  base_clock_ghz?: number | null;
  boost_clock_ghz?: number | null;
  tdp_watts?: number | null;
  cpu_mark?: number | null;
  single_thread_rating?: number | null;
  igpu_mark?: number | null;
  socket?: string | null;
  igpu_model?: string | null;
  release_year?: number | null;
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

async function getCPU(id: string): Promise<CPU | null> {
  try {
    const cpu = await apiFetch<CPU>(`/v1/catalog/cpus/${id}`);
    return cpu;
  } catch (error) {
    return null;
  }
}

async function getCPUListings(id: string): Promise<Listing[]> {
  try {
    const listings = await apiFetch<Listing[]>(`/v1/catalog/cpus/${id}/listings?limit=50`);
    return listings;
  } catch (error) {
    return [];
  }
}

export default async function CPUDetailPage({ params }: PageProps) {
  const cpu = await getCPU(params.id);

  if (!cpu) {
    notFound();
  }

  const listings = await getCPUListings(params.id);

  return <CPUDetailLayout cpu={cpu} listings={listings} />;
}

export async function generateMetadata({ params }: PageProps) {
  const cpu = await getCPU(params.id);

  if (!cpu) {
    return {
      title: "CPU Not Found | Deal Brain",
    };
  }

  return {
    title: `${cpu.model} - CPU Details | Deal Brain`,
    description: `${cpu.manufacturer} ${cpu.model} specifications, benchmark scores, and listings`,
  };
}
