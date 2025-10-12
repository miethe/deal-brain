# ADR — Adopt “System Baseline Ruleset” (Alt 1)

## Context

We need to incorporate a curated set of baseline valuation ranges and formulas into the existing rules engine and `/valuation-rules` UX, while keeping evaluations explainable and maintainable.

## Decision

Adopt **Alt 1**: materialize the baseline JSON into a **read-only, versioned ruleset** (`System: Baseline vX.Y`) with per-entity groups and rules, and create a writable **“Basic · Adjustments”** group for low-code overrides. The evaluator remains unchanged and processes all rules in deterministic order: **Baseline → Basic → Advanced**.

## Status

**Accepted** — Implement for the next minor release.

## Rationale

* **Single source of truth** in the evaluator → simpler reasoning, debugging, and breakdowns.
* **Versioned baseline** → safer updates with clear diffs and rollbacks.
* **UX symmetry** → both Basic and Advanced manipulate the same primitives (rules), avoiding a parallel valuation path.
* **Performance** → no runtime lookups into an external catalog; uses the existing rule engine.

## Alternatives Considered

### Alt 2 — On-the-fly fallback baseline (catalog lookup in evaluator)

* **Pros**: Lowest migration effort; small footprint.
* **Cons**: Two evaluation paths; reduced explainability; harder preview/diff; more branching in evaluator.
* **Why not**: Violates “one engine, one breakdown”; makes audits brittle.

### Alt 3 — Embed baseline constants in code/config (YAML/ENV)

* **Pros**: Very simple deploy; no new rulesets.
* **Cons**: Opaque to users; no per-field tooltips/versioned metadata; requires app redeploy for changes.
* **Why not**: Blocks the Basic UX and governance needs.

### Alt 4 — Replace Advanced with a unified “Basic++” editor

* **Pros**: Single editor conceptually.
* **Cons**: Large scope; alienates power users; increases short-term delivery risk.
* **Why not**: Unnecessary change; we already have a capable Advanced editor.

## Consequences

* **Positive**: Clear provenance of adjustments; smooth admin workflow for updates; consistent evaluator.
* **Negative**: Initial ingestion complexity (JSON→rule construction); need for a Diff & Adopt UI.
* **Mitigations**: Provide CLI + APIs; seed scripts; progressive rollout.

## Implementation Sketch

* CLI: `db:baseline:ingest --file rules.json --version 1.0`
* Data: `rulesets.metadata.system_baseline=true`, `rules.modifiers_json={min,max,clamp,explanation}`
* UI: Basic tabs pull `GET /baseline/meta`; writes go to `Basic · Adjustments`.
* Evaluator: uses current engine with group ordering config.

## Rollback Plan

* Disable `system_baseline` ruleset (feature flag) and revert to current custom ruleset.
* Keep Basic UI read-only until ingestion issues fixed.
