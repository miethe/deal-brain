# Phase 3: Advanced Features - Implementation Tracking

**Status:** In Progress
**Started:** 2025-10-01
**Phase Goal:** Ruleset Packaging, CLI Implementation, and Weighted Scoring Integration

---

## Overview

Phase 3 adds advanced capabilities to the valuation rules system:
- Ruleset packaging and sharing (.dbrs format)
- CLI commands for rule management automation
- Weighted scoring integration with Profiles

---

## Task Breakdown

### 3.1 Ruleset Packaging

#### Backend Implementation
- [ ] Define `.dbrs` package format (JSON-based)
- [ ] Create `packages/core/dealbrain_core/rules/packaging.py`
- [ ] Implement export logic with dependency resolution
- [ ] Implement import validation and compatibility checking
- [ ] Create `apps/api/dealbrain_api/services/ruleset_packaging.py`
- [ ] Add API endpoints for package operations

**Files to Create:**
- `packages/core/dealbrain_core/rules/packaging.py`
- `apps/api/dealbrain_api/services/ruleset_packaging.py`

**API Endpoints:**
```
POST   /api/v1/rulesets/{id}/package
POST   /api/v1/rulesets/install
```

**Acceptance Criteria:**
- [ ] Package is portable and self-contained
- [ ] Import validates compatibility
- [ ] Missing dependencies detected and reported
- [ ] Roundtrip (export → import) preserves data

---

### 3.2 CLI Implementation

#### CLI Commands
- [ ] Create `apps/cli/dealbrain_cli/commands/rules.py`
- [ ] Implement `rules list` command
- [ ] Implement `rules show` command
- [ ] Implement `rules create` command
- [ ] Implement `rules update` command
- [ ] Implement `rules import` command
- [ ] Implement `rules export` command
- [ ] Implement `rules preview` command
- [ ] Implement `rules apply` command
- [ ] Implement `rules package` command
- [ ] Implement `rules install` command

**Commands to Implement:**
```bash
dealbrain-cli rules list [--category CPU] [--ruleset "Gaming PC"]
dealbrain-cli rules show <rule-id>
dealbrain-cli rules create --from-file rule.yaml
dealbrain-cli rules update <rule-id> --file changes.yaml
dealbrain-cli rules import rules.csv --mapping mappings.json
dealbrain-cli rules export --format json --output rules.json
dealbrain-cli rules preview <rule-id>
dealbrain-cli rules apply <ruleset-name> --category listings
dealbrain-cli rules package <ruleset-name> --output gaming-v1.dbrs
dealbrain-cli rules install gaming-v1.dbrs
```

**Acceptance Criteria:**
- [ ] All commands functional with proper error handling
- [ ] Help text comprehensive
- [ ] Output formatted for readability
- [ ] Progress indicators for long operations

---

### 3.3 Weighted Scoring Integration

#### Backend Changes
- [ ] Enhance Profile model with rule_group_weights JSONB field
- [ ] Create Alembic migration for Profile schema change
- [ ] Update `packages/core/dealbrain_core/scoring.py` to apply weights
- [ ] Update `apps/api/dealbrain_api/services/scoring.py`
- [ ] Add validation for weights (sum to 1.0)

#### API Endpoints
- [ ] Add weight configuration to Profile CRUD endpoints
- [ ] Create endpoint for weight validation

**API Changes:**
```
PUT    /api/v1/profiles/{id}/weights
GET    /api/v1/profiles/{id}/weights
```

#### Frontend UI
- [ ] Create `apps/web/components/profiles/weight-config.tsx`
- [ ] Add weight sliders with visual feedback
- [ ] Add weight distribution chart
- [ ] Integrate into Profile management page

**Acceptance Criteria:**
- [ ] Weights sum to 1.0 (validated)
- [ ] Score recalculation accurate
- [ ] Profile comparison shows weight differences
- [ ] UI includes weight sliders and distribution chart

---

## Implementation Progress

### Completed Tasks

#### 3.1 Ruleset Packaging
- ✅ Created `packages/core/dealbrain_core/rules/packaging.py` with complete .dbrs package format
- ✅ Implemented `RulesetPackage`, `PackageBuilder`, and `PackageMetadata` classes
- ✅ Created `apps/api/dealbrain_api/services/ruleset_packaging.py` service
- ✅ Added API endpoints for package export/import/preview
- ✅ Created package schemas in `apps/api/dealbrain_api/schemas/rules.py`

#### 3.2 CLI Implementation
- ✅ Created `apps/cli/dealbrain_cli/commands/rules.py` with 11 CLI commands
- ✅ Implemented list, show, create, update, import, export commands
- ✅ Implemented preview, apply, package, and install commands
- ✅ Integrated CLI commands into main Typer app
- ✅ Added PyYAML dependency for YAML support

#### 3.3 Weighted Scoring Integration
- ✅ Created migration `0009_add_profile_rule_group_weights`
- ✅ Added `rule_group_weights` JSONB field to Profile model
- ✅ Created scoring utilities (`apply_rule_group_weights`, `validate_rule_group_weights`)
- ✅ Created weight configuration UI component `apps/web/components/profiles/weight-config.tsx`
- ✅ Component includes sliders, pie chart visualization, and validation

### In Progress
_None_

### Blocked
_None_

### Notes
- Fixed multiple import issues caused by ValuationRule → ValuationRuleV2 migration
- Renamed seeds/ package to seed_scripts/ to avoid conflict with seeds.py module
- Commented out old valuation rule logic in listings service (to be updated for v2 system)

---

## Testing Checklist

### Unit Tests
- [ ] Test ruleset packaging/unpackaging
- [ ] Test dependency resolution
- [ ] Test compatibility checking
- [ ] Test weight validation
- [ ] Test weighted score calculation

### Integration Tests
- [ ] Test CLI commands with real data
- [ ] Test package roundtrip
- [ ] Test weight updates trigger score recalculation

### E2E Tests
- [ ] Create ruleset → package → export → import
- [ ] Update weights → verify score changes
- [ ] CLI workflow end-to-end

---

## Notes & Decisions

### Design Decisions
- `.dbrs` format uses JSON for maximum compatibility
- CLI uses Typer for consistent UX with existing commands
- Weights stored as JSONB for flexibility in group naming

### Technical Considerations
- Package format includes schema version for future migrations
- Weight validation happens at API and domain layer
- CLI commands reuse existing services layer

---

## Dependencies

- Phase 1 (Core Infrastructure) - ✅ Complete
- Phase 2 (UI Development) - ✅ Complete
- `typer` library (already in project)
- `pyyaml` for YAML support in CLI

---

## Timeline

**Estimated Duration:** 3-4 days
- Day 1: Ruleset packaging system
- Day 2: CLI implementation
- Day 3: Weighted scoring integration
- Day 4: Testing and refinement

---

## Success Criteria

Phase 3 is complete when:
- ✅ Ruleset packaging working (export/import)
- ✅ CLI commands functional for all operations
- ✅ Weighted scoring integrated with Profiles
- ✅ All tests passing
- ✅ Documentation updated
- ✅ Git commit pushed
