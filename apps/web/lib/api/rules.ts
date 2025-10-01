/**
 * API client for Valuation Rules v2
 */

import { API_URL } from "../utils";

// Types
export interface Condition {
  field_name: string;
  field_type: string;
  operator: string;
  value: any;
  logical_operator?: string;
  group_order?: number;
}

export interface Action {
  action_type: string;
  metric?: string;
  value_usd?: number;
  unit_type?: string;
  formula?: string;
  modifiers?: Record<string, any>;
}

export interface Rule {
  id: number;
  group_id: number;
  name: string;
  description?: string;
  priority: number;
  is_active: boolean;
  evaluation_order: number;
  version: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
  conditions: Condition[];
  actions: Action[];
  metadata: Record<string, any>;
}

export interface RuleGroup {
  id: number;
  ruleset_id: number;
  name: string;
  category: string;
  description?: string;
  display_order: number;
  weight: number;
  created_at: string;
  updated_at: string;
  rules: Rule[];
}

export interface Ruleset {
  id: number;
  name: string;
  description?: string;
  version: string;
  is_active: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
  rule_groups: RuleGroup[];
}

export interface RulePreviewResult {
  statistics: {
    total_listings_checked: number;
    matched_count: number;
    match_percentage: number;
    non_matched_count: number;
    avg_adjustment?: number;
    min_adjustment?: number;
    max_adjustment?: number;
    total_adjustment?: number;
  };
  sample_matched_listings: Array<{
    id: number;
    title: string;
    original_price: number;
    adjustment: number;
    adjusted_price: number;
    price_change_pct: number;
  }>;
  sample_non_matched_listings: Array<{
    id: number;
    title: string;
    price_usd: number;
  }>;
}

// API Functions

export async function fetchRulesets(activeOnly = false): Promise<Ruleset[]> {
  const params = new URLSearchParams();
  if (activeOnly) params.set("active_only", "true");

  const response = await fetch(`${API_URL}/api/v1/rulesets?${params}`);
  if (!response.ok) throw new Error("Failed to fetch rulesets");
  return response.json();
}

export async function fetchRuleset(id: number): Promise<Ruleset> {
  const response = await fetch(`${API_URL}/api/v1/rulesets/${id}`);
  if (!response.ok) throw new Error("Failed to fetch ruleset");
  return response.json();
}

export async function createRuleset(data: {
  name: string;
  description?: string;
  version?: string;
  metadata?: Record<string, any>;
}): Promise<Ruleset> {
  const response = await fetch(`${API_URL}/api/v1/rulesets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to create ruleset");
  return response.json();
}

export async function updateRuleset(
  id: number,
  data: Partial<Ruleset>
): Promise<Ruleset> {
  const response = await fetch(`${API_URL}/api/v1/rulesets/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to update ruleset");
  return response.json();
}

export async function deleteRuleset(id: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/rulesets/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to delete ruleset");
}

// Rule Groups

export async function fetchRuleGroups(
  rulesetId?: number,
  category?: string
): Promise<RuleGroup[]> {
  const params = new URLSearchParams();
  if (rulesetId) params.set("ruleset_id", rulesetId.toString());
  if (category) params.set("category", category);

  const response = await fetch(`${API_URL}/api/v1/rule-groups?${params}`);
  if (!response.ok) throw new Error("Failed to fetch rule groups");
  return response.json();
}

export async function createRuleGroup(data: {
  ruleset_id: number;
  name: string;
  category: string;
  description?: string;
  display_order?: number;
  weight?: number;
}): Promise<RuleGroup> {
  const response = await fetch(`${API_URL}/api/v1/rule-groups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to create rule group");
  return response.json();
}

// Rules

export async function fetchRules(
  groupId?: number,
  activeOnly = false
): Promise<Rule[]> {
  const params = new URLSearchParams();
  if (groupId) params.set("group_id", groupId.toString());
  if (activeOnly) params.set("active_only", "true");

  const response = await fetch(`${API_URL}/api/v1/valuation-rules?${params}`);
  if (!response.ok) throw new Error("Failed to fetch rules");
  return response.json();
}

export async function fetchRule(id: number): Promise<Rule> {
  const response = await fetch(`${API_URL}/api/v1/valuation-rules/${id}`);
  if (!response.ok) throw new Error("Failed to fetch rule");
  return response.json();
}

export async function createRule(data: {
  group_id: number;
  name: string;
  description?: string;
  priority?: number;
  evaluation_order?: number;
  is_active?: boolean;
  conditions?: Condition[];
  actions?: Action[];
  metadata?: Record<string, any>;
}): Promise<Rule> {
  const response = await fetch(`${API_URL}/api/v1/valuation-rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to create rule");
  return response.json();
}

export async function updateRule(
  id: number,
  data: Partial<Rule>
): Promise<Rule> {
  const response = await fetch(`${API_URL}/api/v1/valuation-rules/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to update rule");
  return response.json();
}

export async function deleteRule(id: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/valuation-rules/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to delete rule");
}

export async function duplicateRule(ruleId: number): Promise<Rule> {
  const rule = await fetchRule(ruleId);
  return createRule({
    group_id: rule.group_id,
    name: `${rule.name} (Copy)`,
    description: rule.description,
    priority: rule.priority + 1,
    evaluation_order: rule.evaluation_order + 1,
    is_active: false, // Start duplicates as inactive
    conditions: rule.conditions,
    actions: rule.actions,
    metadata: rule.metadata,
  });
}

// Preview & Evaluation

export async function previewRule(data: {
  conditions: Condition[];
  actions: Action[];
  sample_size?: number;
  category_filter?: Record<string, any>;
}): Promise<RulePreviewResult> {
  const response = await fetch(`${API_URL}/api/v1/valuation-rules/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to preview rule");
  return response.json();
}

export async function evaluateListing(
  listingId: number,
  rulesetId?: number
): Promise<any> {
  const params = new URLSearchParams();
  if (rulesetId) params.set("ruleset_id", rulesetId.toString());

  const response = await fetch(
    `${API_URL}/api/v1/valuation-rules/evaluate/${listingId}?${params}`,
    { method: "POST" }
  );
  if (!response.ok) throw new Error("Failed to evaluate listing");
  return response.json();
}

export async function applyRuleset(data: {
  ruleset_id?: number;
  listing_ids?: number[];
}): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/valuation-rules/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to apply ruleset");
  return response.json();
}

// Audit

export async function fetchAuditLog(
  ruleId?: number,
  limit = 100
): Promise<any[]> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (ruleId) params.set("rule_id", ruleId.toString());

  const response = await fetch(
    `${API_URL}/api/v1/valuation-rules/audit-log?${params}`
  );
  if (!response.ok) throw new Error("Failed to fetch audit log");
  return response.json();
}
