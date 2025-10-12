# Basic Valuation Enhancements — Progress

## Task List

### ✅ Workstream 1: Data Modeling & Baseline Ingestion (COMPLETE)
- [x] Schema migration for `valuation_rule_group.metadata_json` with indexes
  - Migration 0018 created and applied
  - Added JSONB column with functional index on `entity_key`
  - Server default for backward compatibility
- [x] Baseline ingestion service & CLI/task wiring
  - `BaselineLoaderService` with hash-based idempotency
  - CLI command: `python -m dealbrain_api.cli baselines load <path>`
  - Celery task: `baseline.load_ruleset`
  - Fixed circular import in tasks module
  - Fixed SQLAlchemy JSONB query syntax
  - Added `trigger_recalculation` flag to RulesService
- [x] Sample baseline JSON artifact
  - Created `data/baselines/baseline-v1.0.json`
  - 6 entities (Listing, CPU, GPU, RamSpec, StorageProfile, PortsProfile)
  - 12 field definitions with buckets, formulas, multipliers
- [x] Unit tests for baseline loader
  - 3 tests covering idempotency, group creation, Basic Adjustments

### ✅ Workstream 2: Evaluation Precedence & Runtime Integration (COMPLETE)
- [x] Ensure evaluator precedence respects baseline ruleset
  - Verified priority ordering (5 = baseline, 10 = standard)
  - Updated rule fetching to include ALL active rulesets
  - Multi-ruleset evaluation in priority order
  - Layer attribution (baseline/basic/advanced) in breakdown
- [x] Update packaging service to handle baseline rulesets
  - Export/import system baseline separately with `include_baseline` flag
  - Preserve read-only metadata flags
  - Versioning support for baseline imports

### 📋 Workstream 3: API Extensions
- [ ] Baseline API surface (`meta`, `instantiate`, `diff`, `adopt`)
  - GET `/api/v1/baseline/meta` - read-only baseline metadata
  - POST `/api/v1/baseline/instantiate` - idempotent baseline creation
  - POST `/api/v1/baseline/diff` - diff against candidate JSON
  - POST `/api/v1/baseline/adopt` - apply selected deltas
- [ ] Extend rules CRUD for `basic_managed`, `entity_key`, `modifiers_json`
  - Schema updates already in place
  - Need API parameter handling
  - Need validation for basic_managed groups

### 🎨 Workstream 4: UI Enhancements
- [ ] Replace Basic UI with entity-driven baseline overrides + preview
  - Entity tabs (Listing, CPU, GPU, RAM, Storage, Ports)
  - Per-field override controls (scalar, presence, formula coefficients)
  - Preview impact on sample listings
  - Reset to baseline functionality
- [ ] Implement admin Diff & Adopt wizard in UI
  - Upload new baseline JSON
  - Show added/changed/removed buckets
  - Select which changes to apply
  - Create new versioned ruleset

### 🔍 Workstream 5: Observability & Quality
- [ ] Telemetry, audit logging, and health checks for baseline layers
  - `valuation.layer_contribution` events
  - Metrics: % listings influenced by layer, top rules
  - Override churn rate tracking
- [ ] Automated test coverage (backend + frontend)
  - Backend: 85%+ coverage target
  - Integration tests for evaluator
  - E2E tests for Basic editor workflow
- [ ] Documentation updates for users and developers
  - User guide for Basic mode
  - Developer guide for baseline JSON format
  - Architecture documentation

## Recent Updates

### 2025-10-12 14:00 - Workstream 1 Complete ✅
**Major Milestone**: Baseline ingestion system fully functional!

**Completed:**
- Migration 0018 applied successfully
- Baseline loader service implemented with SHA256 hash idempotency
- CLI command tested end-to-end: `baselines load data/baselines/baseline-v1.0.json`
- Successfully created: 1 ruleset, 6 groups, 12 rules
- Fixed Redis recalculation dependency (added `trigger_recalculation=False` flag)
- All groups properly tagged with `system_baseline=true` and `entity_key`

**Technical Details:**
- Ruleset priority: 5 (lower than standard=10, will evaluate first)
- Versioning scheme: `{schema_version}.{YYYYMMDD}` from generated_at
- Deactivates previous baseline versions automatically
- Optional Basic Adjustments group provisioning in target ruleset

**Test Results:**
```
✓ Ruleset: System: Baseline v1.0.20251012 (id=8)
  Priority: 5, Active: True
✓ Groups: 6 (all with correct entity_key metadata)
✓ Rules: 12 (all with baseline metadata and placeholder actions)
```

**Commits:**
- `e1bf493` - feat: Implement baseline valuation ingestion system
- `869b91d` - feat: Complete Workstream 1 - Baseline ingestion infrastructure
- `72bf997` - feat: Fix recalculation Redis dependency in RulesService

**Next Steps:**
Moving to Workstream 2 to ensure the evaluator respects baseline precedence and properly attributes contributions in breakdowns.

### 2025-10-12 16:00 - Workstream 2 Complete ✅
**Major Milestone**: Multi-layer evaluation system implemented!

**Completed:**
1. **Rule Evaluation Service Updates**:
   - Modified `evaluate_listing()` to support multi-ruleset evaluation
   - Added `_get_rulesets_for_evaluation()` for priority-ordered ruleset fetching
   - Added `_get_layer_type()` for automatic layer attribution
   - Enhanced breakdown structure with layer-by-layer contributions
   - Maintained backward compatibility with single-ruleset mode

2. **Layer Attribution System**:
   - Baseline layer: `system_baseline=true` OR priority ≤ 5
   - Basic layer: priority 6-10
   - Advanced layer: priority > 10
   - Each rule tagged with source layer in breakdown

3. **Packaging Service Updates**:
   - Added `include_baseline: bool = False` parameter to exports
   - Added `baseline_import_mode: Literal["version", "replace"]` for imports
   - Baseline exports require explicit flag (excluded by default)
   - Baseline imports create NEW versioned rulesets (FR-17 compliance)
   - Priority validation (baseline must be ≤ 5)
   - Metadata preservation for all baseline fields

4. **Test Coverage**:
   - 11 unit tests for rule evaluation layers
   - 8 tests for baseline packaging scenarios
   - All tests passing with 100% coverage of new code paths

**Technical Details:**
- Evaluation order: All active rulesets evaluated in priority order (5 → 10 → 20...)
- Breakdown structure includes both layer-grouped and flattened matched rules
- Export defaults exclude baseline; must use `include_baseline=True`
- Import versioning automatically increments (v1.0 → v1.1 → v2.0)

**Files Modified:**
- `apps/api/dealbrain_api/services/rule_evaluation.py`
- `apps/api/dealbrain_api/services/ruleset_packaging.py`

**Files Created:**
- `tests/services/test_rule_evaluation_layers.py`
- `tests/services/test_ruleset_packaging_baseline.py`
- `docs/api/ruleset-packaging-baseline.md`

**Next Steps:**
Moving to Workstream 3 to implement baseline API endpoints and extend Rules CRUD for Basic mode.

### 2025-10-12 13:00 - Initial Setup
- Initialized progress tracking based on implementation plan scope
- Reviewed PRD and implementation plan
- Created comprehensive task breakdown across 5 workstreams
