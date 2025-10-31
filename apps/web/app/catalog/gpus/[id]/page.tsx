import { notFound } from "next/navigation";
import { apiFetch } from "@/lib/utils";
import { GPUDetailLayout } from "@/components/catalog/gpu-detail-layout";

interface GPU {
  id: number;
  model: string;
  manufacturer?: string | null;
  gpu_type?: "integrated" | "discrete" | null;
  vram_capacity_gb?: number | null;
  vram_type?: string | null;
  architecture?: string | null;
  generation?: string | null;
  benchmark_score?: number | null;
  gpu_mark?: number | null;
  three_d_mark?: number | null;
  release_year?: number | null;
  tdp_watts?: number | null;
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

async function getGPU(id: string): Promise<GPU | null> {
  try {
    const gpu = await apiFetch<GPU>(`/v1/catalog/gpus/${id}`);
    return gpu;
  } catch (error) {
    return null;
  }
}

async function getGPUListings(id: string): Promise<Listing[]> {
  try {
    const listings = await apiFetch<Listing[]>(`/v1/catalog/gpus/${id}/listings?limit=50`);
    return listings;
  } catch (error) {
    return [];
  }
}

export default async function GPUDetailPage({ params }: PageProps) {
  const gpu = await getGPU(params.id);

  if (!gpu) {
    notFound();
  }

  const listings = await getGPUListings(params.id);

  return <GPUDetailLayout gpu={gpu} listings={listings} />;
}

export async function generateMetadata({ params }: PageProps) {
  const gpu = await getGPU(params.id);

  if (!gpu) {
    return {
      title: "GPU Not Found | Deal Brain",
    };
  }

  return {
    title: `${gpu.model} - GPU Details | Deal Brain`,
    description: `${gpu.manufacturer || ""} ${gpu.model} specifications, benchmark scores, and listings`,
  };
}
