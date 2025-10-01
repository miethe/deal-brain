# Implementation Plan: Advanced Valuation Rules System

**Version:** 1.0
**Date:** October 1, 2025
**Status:** Ready for Development
**PRD Reference:** [valuation-rules-enhancement-prd.md](../prd/valuation-rules-enhancement-prd.md)

---

## Executive Summary

This implementation plan provides detailed technical specifications, sprint breakdowns, and development tasks for building the Advanced Valuation Rules System. The plan is structured to deliver incrementally over 14 weeks, with each phase building on the previous one to minimize risk and enable early feedback.

**Key Deliverables:**
- Enhanced database schema with 7 new tables
- Core domain logic for rule evaluation (conditions, actions, formulas)
- Services layer for CRUD and evaluation orchestration
- RESTful API with 15+ endpoints
- Comprehensive UI for rule management, creation, and preview
- Import/Export functionality (CSV, JSON, YAML, Excel)
- CLI commands for automation
- Ruleset packaging and sharing
- Complete test coverage (unit, integration, E2E)

**Timeline:** 14 weeks (3.5 months)
**Team Size:** 2-3 full-stack engineers + 1 QA engineer

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Rules Mgmt UI  │  │ Rule Builder │  │ Preview Panel  │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │ React Query (HTTP)
┌───────────────────────────────▼─────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Rules CRUD API │  │ Preview API  │  │ Import/Export  │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   Services Layer (Async)                     │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ RulesService   │  │ EvalEngine   │  │ ImportService  │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│              Core Domain Logic (packages/core)               │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ RuleEvaluator  │  │ Condition    │  │ ActionEngine   │  │
│  │                │  │ Parser       │  │                │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                  Database (PostgreSQL)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  valuation_ruleset, valuation_rule_v2,                 │ │
│  │  valuation_rule_condition, valuation_rule_action,      │ │
│  │  valuation_rule_audit, valuation_rule_version          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Domain logic in `packages/core`, orchestration in services
2. **Backward Compatibility**: Maintain existing `ValuationRule` model during migration
3. **Performance First**: Caching, indexing, async operations throughout
4. **Extensibility**: Plugin architecture for custom operators and actions

---

## Database Schema Design

### New Tables

#### 1. valuation_ruleset

Container for related rules (e.g., "Gaming PC Valuation Q4 2025")

```sql
CREATE TABLE valuation_ruleset (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL UNIQUE,
    description TEXT,
    version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by VARCHAR(128),
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ruleset_active ON valuation_ruleset(is_active);
CREATE INDEX idx_ruleset_created_by ON valuation_ruleset(created_by);
```

#### 2. valuation_rule_group

Organizes rules by component category (CPU, RAM, Storage, etc.)

```sql
CREATE TABLE valuation_rule_group (
    id SERIAL PRIMARY KEY,
    ruleset_id INTEGER NOT NULL REFERENCES valuation_ruleset(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 100,
    weight DECIMAL(5,4) DEFAULT 1.0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(ruleset_id, name)
);

CREATE INDEX idx_rule_group_ruleset ON valuation_rule_group(ruleset_id);
CREATE INDEX idx_rule_group_category ON valuation_rule_group(category);
```

#### 3. valuation_rule_v2

Individual rule definitions with priority and evaluation order

```sql
CREATE TABLE valuation_rule_v2 (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES valuation_rule_group(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    priority INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    evaluation_order INTEGER NOT NULL DEFAULT 100,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_by VARCHAR(128),
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(group_id, name)
);

CREATE INDEX idx_rule_v2_group ON valuation_rule_v2(group_id);
CREATE INDEX idx_rule_v2_active ON valuation_rule_v2(is_active);
CREATE INDEX idx_rule_v2_eval_order ON valuation_rule_v2(group_id, evaluation_order);
```

#### 4. valuation_rule_condition

Condition logic supporting nested conditions and multiple operators

```sql
CREATE TABLE valuation_rule_condition (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES valuation_rule_v2(id) ON DELETE CASCADE,
    parent_condition_id INTEGER REFERENCES valuation_rule_condition(id) ON DELETE CASCADE,
    field_name VARCHAR(128) NOT NULL,
    field_type VARCHAR(32) NOT NULL,
    operator VARCHAR(32) NOT NULL,
    value_json JSONB NOT NULL,
    logical_operator VARCHAR(8),
    group_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_condition_rule ON valuation_rule_condition(rule_id);
CREATE INDEX idx_condition_parent ON valuation_rule_condition(parent_condition_id);
```

#### 5. valuation_rule_action

Action definitions (fixed value, per-unit, benchmark-based, formula, etc.)

```sql
CREATE TABLE valuation_rule_action (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES valuation_rule_v2(id) ON DELETE CASCADE,
    action_type VARCHAR(32) NOT NULL,
    metric VARCHAR(32),
    value_usd DECIMAL(10,2),
    unit_type VARCHAR(32),
    formula TEXT,
    modifiers_json JSONB NOT NULL DEFAULT '{}',
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_action_rule ON valuation_rule_action(rule_id);
```

#### 6. valuation_rule_version

Version snapshots for rollback and comparison

```sql
CREATE TABLE valuation_rule_version (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES valuation_rule_v2(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    snapshot_json JSONB NOT NULL,
    change_summary TEXT,
    changed_by VARCHAR(128),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(rule_id, version_number)
);

CREATE INDEX idx_version_rule ON valuation_rule_version(rule_id);
```

#### 7. valuation_rule_audit

Immutable audit trail for compliance

```sql
CREATE TABLE valuation_rule_audit (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES valuation_rule_v2(id) ON DELETE SET NULL,
    action VARCHAR(32) NOT NULL,
    actor VARCHAR(128),
    changes_json JSONB,
    impact_summary JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_rule ON valuation_rule_audit(rule_id);
CREATE INDEX idx_audit_created ON valuation_rule_audit(created_at);
```

### Migration File

**Location:** `apps/api/alembic/versions/xxx_add_valuation_rules_v2.py`

```python
"""Add valuation rules v2 schema

Revision ID: xxx
Revises: yyy
Create Date: 2025-10-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create tables in dependency order
    op.create_table('valuation_ruleset', ...)
    op.create_table('valuation_rule_group', ...)
    op.create_table('valuation_rule_v2', ...)
    op.create_table('valuation_rule_condition', ...)
    op.create_table('valuation_rule_action', ...)
    op.create_table('valuation_rule_version', ...)
    op.create_table('valuation_rule_audit', ...)

def downgrade():
    # Drop in reverse order
    op.drop_table('valuation_rule_audit')
    op.drop_table('valuation_rule_version')
    op.drop_table('valuation_rule_action')
    op.drop_table('valuation_rule_condition')
    op.drop_table('valuation_rule_v2')
    op.drop_table('valuation_rule_group')
    op.drop_table('valuation_ruleset')
```

---

## Phase Breakdown

### Phase 1: Core Infrastructure (Weeks 1-4)

#### Sprint 1: Database & Models (Week 1)

**Goals:**
- Create database schema and migrations
- Implement SQLAlchemy models
- Write seed data script

**Tasks:**

1. **Design Schema Review (1 day)**
   - Review ERD with team
   - Validate relationships and constraints
   - Finalize field types and indexes

2. **Create Migration (2 days)**
   - Write Alembic migration file
   - Test upgrade/downgrade
   - Validate on clean database

3. **Implement Models (1 day)**
   - Add models to [models/core.py](../../apps/api/dealbrain_api/models/core.py)
   - Define relationships
   - Add validation

4. **Seed Script (1 day)**
   - Create example ruleset
   - Add rules for CPU, RAM, Storage
   - Test data completeness

**Deliverables:**
- ✅ Migration file
- ✅ SQLAlchemy models
- ✅ Seed script
- ✅ Database tests

**Acceptance Criteria:**
- Migration runs without errors
- Rollback restores previous state
- Seed data creates complete example
- All tests pass

---

#### Sprint 2: Core Domain Logic (Week 2)

**Goals:**
- Implement condition parser and evaluator
- Create action engine
- Build rule evaluation orchestrator

**Tasks:**

1. **Condition System (2 days)**
   - Create `packages/core/dealbrain_core/rules/conditions.py`
   - Implement all operators (equals, greater_than, between, contains, etc.)
   - Support nested conditions (AND/OR groups)
   - Write unit tests

2. **Action System (2 days)**
   - Create `packages/core/dealbrain_core/rules/actions.py`
   - Implement all action types (fixed, per_unit, benchmark, formula)
   - Add modifier support (condition, age)
   - Write unit tests

3. **Formula Engine (1 day)**
   - Create `packages/core/dealbrain_core/rules/formula.py`
   - Implement safe expression evaluator
   - Add math functions (min, max, avg, etc.)
   - Write unit tests

**Files to Create:**
- `packages/core/dealbrain_core/rules/__init__.py`
- `packages/core/dealbrain_core/rules/conditions.py`
- `packages/core/dealbrain_core/rules/actions.py`
- `packages/core/dealbrain_core/rules/evaluator.py`
- `packages/core/dealbrain_core/rules/formula.py`
- `tests/core/test_conditions.py`
- `tests/core/test_actions.py`
- `tests/core/test_evaluator.py`

**Acceptance Criteria:**
- All condition operators functional
- All action types functional
- Nested conditions evaluate correctly
- Formula parser handles edge cases
- 90%+ test coverage

---

#### Sprint 3: Services Layer (Week 3)

**Goals:**
- Create services for CRUD operations
- Implement evaluation service
- Build preview service

**Tasks:**

1. **RulesService (2 days)**
   - Create `apps/api/dealbrain_api/services/rules.py`
   - Implement CRUD for rulesets, groups, rules
   - Add validation layer
   - Write integration tests

2. **EvaluationService (2 days)**
   - Create `apps/api/dealbrain_api/services/rule_evaluation.py`
   - Integrate with core evaluator
   - Add caching for performance
   - Write integration tests

3. **PreviewService (1 day)**
   - Create `apps/api/dealbrain_api/services/rule_preview.py`
   - Generate sample affected listings
   - Calculate impact statistics
   - Write integration tests

**Files to Create:**
- `apps/api/dealbrain_api/services/rules.py`
- `apps/api/dealbrain_api/services/rule_evaluation.py`
- `apps/api/dealbrain_api/services/rule_preview.py`
- `tests/services/test_rules_service.py`
- `tests/services/test_evaluation_service.py`

**Acceptance Criteria:**
- CRUD operations work with error handling
- Evaluation integrates with domain logic
- Preview generates accurate samples
- All tests pass

---

#### Sprint 4: API Endpoints (Week 4)

**Goals:**
- Create REST endpoints
- Implement schemas and validation
- Write API tests

**Tasks:**

1. **Schemas (1 day)**
   - Create `apps/api/dealbrain_api/schemas/rules.py`
   - Define request/response models
   - Add validation rules

2. **Endpoints (3 days)**
   - Create `apps/api/dealbrain_api/api/rules.py`
   - Implement all CRUD endpoints
   - Add filtering, search, pagination
   - Write API tests

3. **Documentation (1 day)**
   - Generate OpenAPI docs
   - Add endpoint descriptions
   - Include example requests/responses

**Endpoints to Implement:**
```
POST   /api/v1/rulesets
GET    /api/v1/rulesets
GET    /api/v1/rulesets/{id}
PUT    /api/v1/rulesets/{id}
DELETE /api/v1/rulesets/{id}

POST   /api/v1/rule-groups
GET    /api/v1/rule-groups
GET    /api/v1/rule-groups/{id}

POST   /api/v1/valuation-rules
GET    /api/v1/valuation-rules
GET    /api/v1/valuation-rules/{id}
PUT    /api/v1/valuation-rules/{id}
DELETE /api/v1/valuation-rules/{id}
POST   /api/v1/valuation-rules/preview
```

**Acceptance Criteria:**
- All endpoints return correct status codes
- Schemas validated
- Error handling returns clear messages
- API tests pass
- Documentation complete

---

### Phase 2: UI Development (Weeks 5-8)

#### Sprint 5: Rules Management Page (Week 5)

**Goals:**
- Create rules list view with hierarchy
- Implement expand/collapse
- Add filtering and search

**Tasks:**

1. **Page Layout (1 day)**
   - Create `apps/web/app/valuation-rules/page.tsx`
   - Add header with search and filters
   - Implement responsive grid

2. **Components (3 days)**
   - Create `apps/web/components/rules/rules-list.tsx`
   - Create `apps/web/components/rules/ruleset-card.tsx`
   - Create `apps/web/components/rules/rule-group-card.tsx`
   - Create `apps/web/components/rules/rule-item.tsx`

3. **State Management (1 day)**
   - Set up React Query hooks
   - Create `apps/web/lib/api/rules.ts`
   - Add optimistic updates

**Component Hierarchy:**
```
<RulesPage>
  <RulesHeader>
    <SearchBar />
    <FilterDropdown />
    <CreateButton />
  </RulesHeader>
  <RulesetsList>
    <RulesetCard>
      <RulesetHeader />
      <RuleGroupsList>
        <RuleGroupCard>
          <RulesList>
            <RuleItem />
          </RulesList>
        </RuleGroupCard>
      </RuleGroupsList>
    </RulesetCard>
  </RulesetsList>
</RulesPage>
```

**Acceptance Criteria:**
- Responsive on mobile/tablet/desktop
- Keyboard navigation works
- Loading states smooth
- Empty states helpful

---

#### Sprint 6: Rule Builder Modal (Week 6)

**Goals:**
- Create multi-step modal
- Build condition builder
- Add live preview

**Tasks:**

1. **Modal Structure (1 day)**
   - Create `apps/web/components/rules/rule-modal.tsx`
   - Implement multi-step wizard
   - Add progress indicator

2. **Condition Builder (2 days)**
   - Create `apps/web/components/rules/condition-builder.tsx`
   - Create `apps/web/components/rules/field-selector.tsx`
   - Add operator selector
   - Support nested conditions (AND/OR)

3. **Action Builder (1 day)**
   - Create `apps/web/components/rules/action-builder.tsx`
   - Support all action types
   - Add modifier configuration

4. **Preview Panel (1 day)**
   - Create `apps/web/components/rules/rule-preview.tsx`
   - Show affected listings
   - Display impact statistics
   - Update in real-time

**Modal Steps:**
1. Basic Info (name, description, category)
2. Conditions (field + operator + value)
3. Actions (type + configuration)
4. Preview (impact summary)

**Acceptance Criteria:**
- Form validation prevents invalid rules
- Field selector shows relevant fields
- Preview updates in real-time
- Keyboard shortcuts work

---

#### Sprint 7: Import/Export UI (Week 7)

**Goals:**
- Create import wizard
- Build export dialog
- Add progress indicators

**Tasks:**

1. **Import Wizard (3 days)**
   - Create `apps/web/components/rules/import-wizard.tsx`
   - Create `apps/web/components/rules/import-mapping.tsx`
   - Create `apps/web/components/rules/import-preview.tsx`
   - Support CSV, JSON, YAML

2. **Export Dialog (1 day)**
   - Create `apps/web/components/rules/export-dialog.tsx`
   - Add format selection
   - Implement download

3. **Progress Indicators (1 day)**
   - Add upload progress
   - Add parsing progress
   - Add import progress

**Import Flow:**
1. Upload file
2. Parse and validate
3. Map fields
4. Preview impact
5. Confirm and import
6. Show results

**Acceptance Criteria:**
- Supports multiple formats
- Field mapping intuitive
- Preview shows affected listings
- Error handling clear

---

#### Sprint 8: Ruleset Management (Week 8)

**Goals:**
- Build ruleset packaging UI
- Add version comparison
- Create audit log viewer

**Tasks:**

1. **Packaging UI (2 days)**
   - Create `apps/web/components/rules/ruleset-package.tsx`
   - Add metadata editor
   - Implement export to .dbrs

2. **Version Comparison (2 days)**
   - Create `apps/web/components/rules/version-compare.tsx`
   - Show side-by-side diff
   - Highlight changes

3. **Audit Log (1 day)**
   - Create `apps/web/components/rules/audit-log.tsx`
   - Add filtering
   - Make searchable

**Acceptance Criteria:**
- Package export includes dependencies
- Version comparison highlights diffs
- Audit log filterable

---

### Phase 3: Advanced Features (Weeks 9-11)

#### Sprint 9: Ruleset Packaging (Week 9)

**Goals:**
- Implement .dbrs format
- Add dependency resolution
- Version compatibility checking

**Tasks:**

1. **Packaging Service (3 days)**
   - Create `packages/core/dealbrain_core/rules/packaging.py`
   - Define .dbrs format (JSON-based)
   - Implement export logic
   - Implement import logic

2. **API Integration (1 day)**
   - Add package endpoints
   - Validate on import
   - Resolve dependencies

3. **Testing (1 day)**
   - Test export/import roundtrip
   - Test version compatibility
   - Test missing dependencies

**Package Format:**
```json
{
  "schema_version": "1.0",
  "metadata": {
    "name": "Gaming PC Ruleset",
    "version": "1.2.0",
    "author": "User Name",
    "compatibility": {
      "min_app_version": "1.0.0"
    }
  },
  "rulesets": [...],
  "custom_fields": [...]
}
```

**Acceptance Criteria:**
- Package is self-contained
- Import validates compatibility
- Dependencies resolved

---

#### Sprint 10: CLI Implementation (Week 10)

**Goals:**
- Add CLI commands
- Support import/export
- Enable automation

**Tasks:**

1. **CLI Commands (3 days)**
   - Create `apps/cli/dealbrain_cli/commands/rules.py`
   - Implement list, create, update, delete
   - Add import/export commands
   - Add preview and apply commands

2. **Documentation (1 day)**
   - Write CLI reference
   - Add examples
   - Create man pages

3. **Testing (1 day)**
   - Test all commands
   - Test error handling
   - Test output formatting

**Commands:**
```bash
dealbrain-cli rules list
dealbrain-cli rules create --from-file rule.yaml
dealbrain-cli rules import rules.csv
dealbrain-cli rules export --format json
dealbrain-cli rules apply "Gaming PC" --preview
dealbrain-cli rules package "Gaming PC" --output gaming.dbrs
```

**Acceptance Criteria:**
- All commands functional
- Help text comprehensive
- Error messages clear

---

#### Sprint 11: Weighted Scoring (Week 11)

**Goals:**
- Integrate with Profile system
- Add weight configuration
- Update scoring engine

**Tasks:**

1. **Domain Logic (2 days)**
   - Update `packages/core/dealbrain_core/scoring.py`
   - Add weight support
   - Update composite calculation

2. **Services (1 day)**
   - Update `apps/api/dealbrain_api/services/scoring.py`
   - Integrate with rules evaluation
   - Add weight validation

3. **UI (2 days)**
   - Create `apps/web/components/profiles/weight-config.tsx`
   - Add weight sliders
   - Show weight distribution chart
   - Add profile comparison

**Acceptance Criteria:**
- Weights sum to 1.0
- Score recalculation accurate
- Profile comparison works

---

### Phase 4: Testing & Refinement (Weeks 12-14)

#### Sprint 12: Performance Optimization (Week 12)

**Goals:**
- Profile performance
- Add caching
- Optimize queries

**Tasks:**

1. **Profiling (2 days)**
   - Profile rule evaluation
   - Profile database queries
   - Identify bottlenecks

2. **Optimization (2 days)**
   - Add Redis caching for rules
   - Optimize query joins
   - Add database indexes
   - Implement batch processing

3. **Load Testing (1 day)**
   - Create load test scenarios
   - Run with realistic data
   - Validate performance targets

**Performance Targets:**
- Single listing evaluation: <100ms
- Bulk (1000 listings): <5s
- Rule list loading: <500ms
- Preview generation: <2s

**Acceptance Criteria:**
- All targets met
- No N+1 queries
- Caching effective

---

#### Sprint 13: User Acceptance Testing (Week 13)

**Goals:**
- Conduct UAT with beta users
- Fix bugs
- Refine UX

**Tasks:**

1. **UAT Planning (1 day)**
   - Recruit beta users
   - Create test scenarios
   - Prepare environment

2. **UAT Execution (2 days)**
   - Guide users through scenarios
   - Collect feedback
   - Document issues

3. **Bug Fixes (2 days)**
   - Fix critical bugs
   - Refine UI based on feedback
   - Update documentation

**UAT Scenarios:**
1. Create simple rule
2. Create complex rule with nested conditions
3. Import rules from CSV
4. Package and export ruleset
5. Apply ruleset to listings

**Acceptance Criteria:**
- 90%+ task completion
- <3 critical bugs
- User satisfaction >4/5

---

#### Sprint 14: Launch Preparation (Week 14)

**Goals:**
- Complete documentation
- Final QA pass
- Prepare deployment

**Tasks:**

1. **Documentation (2 days)**
   - Write user guide
   - Create video tutorials
   - Update API docs
   - Write FAQ

2. **QA (2 days)**
   - Final regression testing
   - Test on production-like data
   - Validate all user flows

3. **Deployment Prep (1 day)**
   - Create deployment checklist
   - Test rollback procedure
   - Prepare release notes
   - Train support team

**Acceptance Criteria:**
- All docs complete
- No critical bugs
- Deployment plan approved
- Rollback tested

---

## Testing Strategy

### Unit Tests

**Coverage Target:** 90%+

**Core Domain Logic:**
- `tests/core/test_conditions.py`: Test all operators
- `tests/core/test_actions.py`: Test all action types
- `tests/core/test_evaluator.py`: Test rule evaluation
- `tests/core/test_formula.py`: Test formula parser

**Example Test:**
```python
def test_condition_greater_than():
    condition = Condition(
        field_name="cpu.cpu_mark_multi",
        field_type="integer",
        operator=ConditionOperator.GREATER_THAN,
        value=20000
    )

    context = {"cpu": {"cpu_mark_multi": 25000}}
    assert condition.evaluate(context) == True

    context = {"cpu": {"cpu_mark_multi": 15000}}
    assert condition.evaluate(context) == False
```

### Integration Tests

**Services Layer:**
- `tests/services/test_rules_service.py`: Test CRUD operations
- `tests/services/test_evaluation_service.py`: Test rule evaluation
- `tests/services/test_preview_service.py`: Test preview generation

**Example Test:**
```python
@pytest.mark.asyncio
async def test_create_rule(db_session):
    service = RulesService()

    rule = await service.create_rule(
        session=db_session,
        group_id=1,
        name="Test Rule",
        conditions=[...],
        actions=[...]
    )

    assert rule.id is not None
    assert rule.name == "Test Rule"
```

### API Tests

**Endpoints:**
- `tests/api/test_rules_api.py`: Test all endpoints
- `tests/api/test_preview_api.py`: Test preview endpoint

**Example Test:**
```python
def test_create_rule_api(client):
    response = client.post("/api/v1/valuation-rules", json={
        "group_id": 1,
        "name": "Test Rule",
        "conditions": [...],
        "actions": [...]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Rule"
```

### E2E Tests

**User Flows:**
- Create ruleset → Add rules → Apply to listings
- Import rules from CSV → Preview → Confirm
- Package ruleset → Export → Import in clean instance

**Tools:** Playwright or Cypress

---

## Migration Strategy

### Backward Compatibility

**Approach:** Run v1 and v2 systems in parallel during transition.

**Steps:**

1. **Deploy v2 Schema (Week 1)**
   - Add new tables alongside existing `valuation_rule`
   - No breaking changes to existing API

2. **Feature Flag (Week 2)**
   - Add `ENABLE_RULES_V2` flag
   - Default to `false` in production

3. **Gradual Migration (Weeks 3-8)**
   - Migrate existing rules to v2 format
   - Test v2 evaluation matches v1 results
   - Enable v2 for beta users

4. **Full Cutover (Week 9)**
   - Enable v2 for all users
   - Deprecate v1 endpoints (still functional)

5. **Cleanup (Week 14)**
   - Remove v1 code and tables
   - Update documentation

### Data Migration Script

```python
# apps/api/dealbrain_api/migrations/migrate_rules_v1_to_v2.py

async def migrate_rules():
    """Migrate existing rules to v2 format."""

    # Create default ruleset
    ruleset = await create_ruleset(
        name="Legacy Rules",
        description="Migrated from v1 system"
    )

    # Group rules by component type
    groups = {}
    for rule_v1 in get_all_v1_rules():
        category = rule_v1.component_type
        if category not in groups:
            groups[category] = await create_rule_group(
                ruleset_id=ruleset.id,
                name=f"{category.capitalize()} Rules",
                category=category
            )

        # Convert v1 rule to v2 format
        await create_rule_v2(
            group_id=groups[category].id,
            name=rule_v1.name,
            conditions=[...],  # Convert simple conditions
            actions=[...]      # Convert to per_unit action
        )
```

---

## Deployment Plan

### Pre-Deployment Checklist

- [ ] All tests pass (unit, integration, E2E)
- [ ] Performance targets met
- [ ] Security audit complete
- [ ] Documentation updated
- [ ] Release notes prepared
- [ ] Rollback plan tested
- [ ] Database backup created
- [ ] Monitoring alerts configured

### Deployment Steps

1. **Staging Deployment (Day 1)**
   - Deploy to staging environment
   - Run smoke tests
   - Validate migrations
   - Test rollback

2. **Production Deployment (Day 2)**
   - Create database backup
   - Deploy during low-traffic window
   - Run migrations
   - Deploy API changes
   - Deploy frontend changes
   - Validate deployment

3. **Post-Deployment (Day 3)**
   - Monitor error rates
   - Monitor performance metrics
   - Gather user feedback
   - Fix critical issues

### Rollback Procedure

**If deployment fails:**

1. **Immediate Rollback**
   - Revert frontend deployment
   - Revert API deployment
   - Run migration rollback: `alembic downgrade -1`
   - Restore database from backup (if needed)

2. **Validation**
   - Test existing functionality
   - Verify data integrity
   - Notify users of rollback

3. **Post-Mortem**
   - Document failure cause
   - Update deployment checklist
   - Plan re-deployment

---

## Monitoring & Observability

### Metrics to Track

**Performance:**
- Rule evaluation time (p50, p95, p99)
- API response time
- Database query time
- Cache hit rate

**Business:**
- Rules created per day
- Rulesets exported/imported
- Preview usage rate
- Error rate during import

**Health:**
- API uptime
- Database connection pool usage
- Background job queue depth
- Error logs

### Alerts

**Critical:**
- API error rate >5%
- Database connection failures
- Rule evaluation time >500ms (p95)

**Warning:**
- Cache hit rate <80%
- Import job failures
- High memory usage

### Dashboards

**Grafana Dashboards:**
1. **Rules Overview**: Rules created, active rulesets, evaluation time
2. **API Performance**: Request rate, response time, error rate
3. **Database Health**: Query time, connection pool, slow queries
4. **User Activity**: Rules created by user, import volume, preview usage

---

## Success Criteria

### Phase 1 Complete When:
- [x] Database schema deployed
- [x] Core domain logic functional
- [x] API endpoints operational
- [x] All tests passing

### Phase 2 Complete When:
- [x] Rules management UI functional
- [x] Rule builder modal operational
- [x] Import/export UI complete
- [x] Ruleset management UI functional

### Phase 3 Complete When:
- [x] Ruleset packaging working
- [x] CLI commands functional
- [x] Weighted scoring integrated
- [x] All features complete

### Phase 4 Complete When:
- [x] Performance targets met
- [x] UAT completed successfully
- [x] Documentation complete
- [x] Deployed to production

---

## Risk Mitigation

### Technical Risks

**R1: Performance degradation with complex rules**
- Mitigation: Early profiling, caching, load testing

**R2: Data migration complexity**
- Mitigation: Parallel systems, gradual rollout, extensive testing

**R3: Formula engine security**
- Mitigation: Restricted context, input validation, sandboxed execution

### Product Risks

**R4: Feature complexity overwhelms users**
- Mitigation: Progressive disclosure, templates, onboarding

**R5: Import format incompatibilities**
- Mitigation: Strict validation, clear error messages, examples

### Operational Risks

**R6: Database migration failure**
- Mitigation: Tested rollback, database backups, staging validation

**R7: Performance impact on existing features**
- Mitigation: Feature flag, gradual rollout, monitoring

---

## Appendix

### Example Rule Definitions (YAML)

```yaml
# DDR5 RAM Premium Pricing
name: "DDR5 RAM Premium"
category: ram
priority: 10
conditions:
  - field: custom.ram_generation
    operator: equals
    value: "DDR5"
action:
  type: per_unit
  metric: per_gb
  value: 4.50
  modifiers:
    condition_new: 1.0
    condition_refurb: 0.80
    condition_used: 0.65

---

# High-End CPU (Benchmark-Based)
name: "High-End CPU (Passmark 20K+)"
category: cpu
priority: 5
conditions:
  logical_operator: and
  conditions:
    - field: cpu.cpu_mark_multi
      operator: greater_than
      value: 20000
    - field: cpu.release_year
      operator: greater_than
      value: 2020
action:
  type: benchmark_based
  metric: cpu_mark_multi
  unit_type: per_1000_points
  value: 5.00
  base_value: 50.00

---

# NVMe Gen4 Storage Premium
name: "NVMe Gen4 Storage Premium"
category: storage
priority: 8
conditions:
  logical_operator: and
  conditions:
    - field: primary_storage_type
      operator: contains
      value: "NVMe"
    - field: custom.storage_gen
      operator: equals
      value: "Gen4"
action:
  type: per_unit
  metric: per_gb
  value: 0.15
  multiplier: 1.5
```

### Tech Stack Summary

**Backend:**
- Python 3.11+
- FastAPI (async)
- SQLAlchemy (async)
- Alembic (migrations)
- Redis (caching)
- PostgreSQL 14+

**Frontend:**
- Next.js 14 (App Router)
- React 18
- TypeScript
- TanStack Query (React Query)
- Tailwind CSS
- shadcn/ui components

**Testing:**
- pytest (backend)
- pytest-asyncio
- Playwright or Cypress (E2E)
- Locust or k6 (load testing)

**DevOps:**
- Docker & Docker Compose
- Prometheus (metrics)
- Grafana (dashboards)
- OpenTelemetry (tracing)

---

## Team Responsibilities

### Backend Engineer 1
- Database schema and migrations
- Core domain logic (conditions, actions)
- Services layer
- API endpoints

### Backend Engineer 2 (if available)
- Import/Export services
- CLI implementation
- Ruleset packaging
- Performance optimization

### Frontend Engineer
- Rules management UI
- Rule builder modal
- Import/Export UI
- Ruleset management UI

### QA Engineer
- Test planning
- Integration tests
- E2E tests
- UAT coordination
- Load testing

---

## Glossary

**Ruleset**: Container for related rules (e.g., "Gaming PC Valuation")

**Rule Group**: Organizes rules by component category (CPU, RAM, etc.)

**Rule**: Individual valuation logic with conditions and actions

**Condition**: Logical expression that determines if a rule applies

**Action**: Pricing calculation performed when conditions match

**Modifier**: Adjustment factor (condition, age, brand)

**Preview**: Sample of affected listings before saving rule

**Package (.dbrs)**: Portable ruleset file for sharing

---

**End of Implementation Plan**
