import { notFound } from "next/navigation";
import { apiFetch } from "@/lib/utils";
import { ProfileDetailLayout } from "@/components/catalog/profile-detail-layout";
import { fetchRuleGroups, type RuleGroup } from "@/lib/api/rules";

interface Profile {
  id: number;
  name: string;
  description?: string | null;
  weights_json: Record<string, number>;
  is_default: boolean;
  created_at: string;
  updated_at: string;
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

async function getProfile(id: string): Promise<Profile | null> {
  try {
    const profile = await apiFetch<Profile>(`/v1/catalog/profiles/${id}`);
    return profile;
  } catch (error) {
    return null;
  }
}

async function getProfileListings(id: string): Promise<Listing[]> {
  try {
    const listings = await apiFetch<Listing[]>(`/v1/catalog/profiles/${id}/listings?limit=50`);
    return listings;
  } catch (error) {
    return [];
  }
}

async function getRuleGroups(): Promise<RuleGroup[]> {
  try {
    const ruleGroups = await fetchRuleGroups();
    return ruleGroups;
  } catch (error) {
    console.error("Failed to fetch rule groups:", error);
    return [];
  }
}

export default async function ProfileDetailPage({ params }: PageProps) {
  const profile = await getProfile(params.id);

  if (!profile) {
    notFound();
  }

  const [listings, ruleGroups] = await Promise.all([
    getProfileListings(params.id),
    getRuleGroups(),
  ]);

  return <ProfileDetailLayout profile={profile} listings={listings} ruleGroups={ruleGroups} />;
}

export async function generateMetadata({ params }: PageProps) {
  const profile = await getProfile(params.id);

  if (!profile) {
    return {
      title: "Profile Not Found | Deal Brain",
    };
  }

  return {
    title: `${profile.name} - Scoring Profile | Deal Brain`,
    description: profile.description || `${profile.name} scoring profile configuration`,
  };
}
