# PRD — System Baseline Valuation Ruleset (Alt 1)

Date: 2025-10-12
Author: GPT-5 Thinking

## 0. Summary

Implement a **read-only “System: Baseline” ruleset** generated from the supplied JSON artifact of valuation ranges/formulas. Expose a **Basic mode** UI that edits a sibling, writable **“Basic · Adjustments”** group while preserving a **single evaluation pipeline** used by the existing evaluator. Baseline updates are delivered as **versioned rulesets** with a **Diff & Adopt** flow.

---

## 1. Goals & Non-Goals

**Goals**

* Make baseline valuation data first-class in the rules engine (not a parallel code path).
* Provide a low-friction **Basic** UI to nudge min/max/coefficients without touching Advanced rules.
* Maintain full explainability in the valuation breakdown (Baseline → Basic → Advanced precedence).
* Ship baseline updates safely and audibly (versioned, diffable, reversible).

**Non-Goals**

* Replacing the existing Advanced editor.
* Per-listing customizations in Basic (future: can be layered as listing-scoped overrides).
* Building a new rule runtime or expression language.

---

## 2. User Stories

1. **As a valuation analyst**, I can view baseline recommendations (min/max, formulas, explanations) per entity/field and set simple overrides without writing rules manually.

* **AC**: Basic tab shows read-only baseline info and editable override controls; saving writes to “Basic · Adjustments”.

2. **As a power user**, I can inspect exactly which layer (baseline/basic/advanced) contributed to a listing’s value.

* **AC**: Breakdown modal shows ordered stack of contributions with group tags and rule IDs.

3. **As an admin**, I can import a new baseline version, see diffs, and adopt changes selectively.

* **AC**: “Diff & Adopt” wizard lists added/changed/removed buckets/coefficients and applies chosen deltas.

4. **As an engineer**, I can keep one evaluator and one breakdown system.

* **AC**: No evaluator fallback to “catalog”; all adjustments are rules.

---

## 3. Functional Requirements

### 3.1 Ingestion / Ruleset Generation

* **FR-1**: A backend task/CLI must load the baseline JSON and create a **Ruleset** named `System: Baseline v{X.Y}` if not present.
* **FR-2**: Create **RuleGroups** by entity (`Listing`, `CPU`, `GPU`, `RamSpec`, `StorageProfile`, `PortsProfile`).
* **FR-3**: For each field entry:

  * **Static bucket** → create one or more **fixed_value** actions (positive or negative).
  * **Presence feature** (e.g., Thunderbolt) → create a **conditioned rule** (predicate on context) with fixed_value min default; store full min/max in metadata.
  * **Formula** → create a **formula action** with expression string and clamp constraints persisted in `modifiers_json`.
  * **Multipliers/decay** (e.g., condition, age, DDR3 obsolescence) → create **multiplier actions** with their min/max range; annotate with unit=`multiplier`.
* **FR-4**: Tag ruleset and groups:

  * `metadata.system_baseline=true`, `metadata.source_version`, `metadata.source_hash`.
* **FR-5**: Create an **empty writable group** `Basic · Adjustments` under the active user ruleset (or the default “Standard Valuation” ruleset), flagged `basic_managed=true`.

### 3.2 Evaluation Precedence

* **FR-6**: Ensure evaluation order is: **Baseline** → **Basic · Adjustments** → **Advanced**.
* **FR-7**: Evaluator remains unchanged; it consumes rulesets/groups in order and produces a single breakdown.

### 3.3 API Endpoints

* **FR-8**: `GET /api/v1/baseline/meta` — read-only metadata derived from the JSON (for UI tooltips).
* **FR-9**: `POST /api/v1/baseline/instantiate` — idempotent creation of baseline ruleset.
* **FR-10**: **Rules CRUD** supports `basic_managed` flag and `modifiers_json` payloads (min/max/clamps, explanation, formula notes).
* **FR-11**: `POST /api/v1/baseline/diff` — compute diff between current baseline and a candidate JSON.
* **FR-12**: `POST /api/v1/baseline/adopt` — apply accepted deltas into a new versioned baseline ruleset (or sync metadata only, depending on chosen flow).

### 3.4 UI — `/valuation-rules` Basic Mode

* **FR-13**: **Tabs per entity**; each tab lists fields with:

  * Readable name, DB id, description, explanation, **min/max** (read-only), **Formula tooltip** if present.
  * Editable override:

    * Scalar add/penalty: numeric input with delta badge (vs. baseline default).
    * Presence features: toggle to **enable override** + numeric input (default = baseline min; show baseline max).
    * Formula coefficients: constrained inputs (editable constants only); optional “Advanced coefficients” toggle for full expression (guarded).
  * **Reset to Baseline** (per field/per tab).
* **FR-14**: **Preview Impact** runs RulePreviewService on a recent sample (e.g., last 200 Listings) and displays match %, min/avg/max delta vs. baseline only.
* **FR-15**: **Diff & Adopt** screen for admins when a new baseline JSON is uploaded.

### 3.5 Import/Export & Versioning

* **FR-16**: RulesetPackagingService exports/imports `System: Baseline v{X.Y}` separately from customer rulesets.
* **FR-17**: Baseline updates import as a **new versioned ruleset**; do not mutate in place.

---

## 4. Non-Functional Requirements

* **NFR-1**: Idempotent ingestion (safe to re-run).
* **NFR-2**: Evaluation latency unaffected (< existing P95).
* **NFR-3**: Full audit trail of rule changes (who/when/what).
* **NFR-4**: Backward compatible with Advanced editor/rules.
* **NFR-5**: Test coverage ≥ 85% on ingestion, evaluator integration, and diff/adopt.

---

## 5. Data Model Additions

* `rulesets.metadata: jsonb` (add `system_baseline`, `source_version`, `source_hash`)
* `rule_groups.metadata: jsonb` (add `basic_managed`, `entity_key`)
* `rules.modifiers_json: jsonb` (store min/max, clamps, explanations, unit)
* Optional: `baseline_catalog` table (materialized meta for UI/tooltips); can also be served on-the-fly from rules metadata.

---

## 6. Evaluation Mapping (JSON → Rules)

**Examples**

* **CPU cohort floor/ceiling**:
  `rule: type=formula, expr="clamp(max((cpu_multi/1000)*3.6, (cpu_single/100)*5.2), 160, 260)"`
  `modifiers_json: { min_usd:160, max_usd:260, clamp:true }`
* **iGPU uplift**:
  `rule: type=conditional_fixed, predicate="igpu_mark>=T or igpu_model in {RDNA3,Xe-LPG}"`
  `value_range: [10,30]`
* **Condition multiplier** (read from Listing):
  `rule: type=multiplier, predicate="condition=='used_a'"`
  `multiplier_range: [0.85,0.92]`

---

## 7. Telemetry & Observability

* Emit `valuation.layer_contribution` events: `{listing_id, layer: baseline|basic|advanced, rule_ids:[…], delta_usd, cumulative_usd}`.
* Metrics: % of listings influenced by each layer; top 10 rules by absolute contribution; override churn rate.

---

## 8. Security & RBAC

* Baseline ruleset is **read-only** to non-admin roles.
* “Basic · Adjustments” requires `rules:write_basic`.
* “Diff & Adopt” requires `baseline:admin`.

---

## 9. Risks & Mitigations

* **Risk**: Confusion about “where a number came from.”
  **Mitigation**: Breakdown shows layer tags and rule IDs; Basic editor shows delta vs baseline.
* **Risk**: Formula misuse in Basic.
  **Mitigation**: Constrain to coefficient editing; gated toggle for full expressions with validation.
* **Risk**: Baseline update breaking existing overrides.
  **Mitigation**: Versioned baseline + Diff & Adopt, no implicit overwrite.

---

## 10. Rollout Plan

Immediate rollout, as there are no active users or data.

---

## 11. Acceptance Criteria (System)

* Ingested baseline ruleset visible in Advanced with `system_baseline=true`.
* Basic edits persist as rules in `Basic · Adjustments`; evaluator uses them with correct precedence.
* Breakdown correctly shows layer source for contributions on at least 95% of sampled listings (remaining 5% allow for null/edge data).
* Diff & Adopt applies selected changes into a new versioned baseline with no evaluator changes.

---

## 12. Test Plan (high level)

* **Unit**: JSON→rules mapping, predicate building, clamp logic, coefficient validation.
* **Integration**: Evaluate N sample listings across varied hardware; assert identical totals pre/post enabling baseline (when Basic/Advanced empty).
* **E2E**: Edit a RAM uplift in Basic, preview impact, verify breakdown layer and totals; import new baseline, run diff, adopt, verify changes.
