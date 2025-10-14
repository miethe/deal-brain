# Implementation Plan: Advanced Valuation Rules System

**Version:** 2.0
**Date:** October 1, 2025
**Status:** Ready for Development
**PRD Reference:** [valuation-rules-enhancement-prd.md](../prd/valuation-rules-enhancement-prd.md)

---

## Executive Summary

This implementation plan provides detailed technical specifications and development tasks for building the Advanced Valuation Rules System. As the lead architect and sole developer in active development with no existing users or data, we can move rapidly without migration concerns or staged rollouts.

**Key Deliverables:**
- Enhanced database schema with 7 new tables (direct replacement of existing ValuationRule)
- Core domain logic for rule evaluation (conditions, actions, formulas)
- Services layer for CRUD and evaluation orchestration
- RESTful API with 15+ endpoints
- Comprehensive UI for rule management, creation, and preview
- Import/Export functionality (CSV, JSON, YAML, Excel)
- CLI commands for automation
- Ruleset packaging and sharing
- Complete test coverage (unit, integration, E2E)

**Development Approach:** Rapid iteration with direct implementation. No backward compatibility or migration planning needed.

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
2. **Direct Replacement**: Replace existing `ValuationRule` with new v2 system immediately
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

**Note:** This migration will DROP the existing `valuation_rule` table and replace it with the new system. No data migration needed since we're in active development.

```python
"""Replace valuation rules with v2 system

Revision ID: xxx
Revises: yyy
Create Date: 2025-10-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Drop old table
    op.drop_table('valuation_rule')

    # Create new tables
    op.create_table('valuation_ruleset', ...)
    op.create_table('valuation_rule_group', ...)
    op.create_table('valuation_rule_v2', ...)
    op.create_table('valuation_rule_condition', ...)
    op.create_table('valuation_rule_action', ...)
    op.create_table('valuation_rule_version', ...)
    op.create_table('valuation_rule_audit', ...)

def downgrade():
    # Drop new tables
    op.drop_table('valuation_rule_audit')
    op.drop_table('valuation_rule_version')
    op.drop_table('valuation_rule_action')
    op.drop_table('valuation_rule_condition')
    op.drop_table('valuation_rule_v2')
    op.drop_table('valuation_rule_group')
    op.drop_table('valuation_ruleset')

    # Recreate old table
    op.create_table('valuation_rule', ...)
```

---

## Implementation Phases

### Phase 1: Core Infrastructure

**Goal:** Database, domain logic, services, and API foundation

#### 1.1 Database & Models

**Tasks:**
- Write Alembic migration (drop old, create new schema)
- Implement SQLAlchemy models in [models/core.py](../../apps/api/dealbrain_api/models/core.py)
- Create seed script with example rulesets

**Files:**
- `apps/api/alembic/versions/xxx_replace_valuation_rules.py`
- `apps/api/dealbrain_api/models/core.py` (add 7 new models)
- `apps/api/dealbrain_api/seeds/valuation_rules_v2.py`

**Acceptance Criteria:**
- Migration runs cleanly
- Models have proper relationships
- Seed data creates complete example

#### 1.2 Core Domain Logic

**Tasks:**
- Implement condition system (all operators, nested groups)
- Create action engine (6 action types + modifiers)
- Build formula parser (safe evaluation)
- Write rule evaluator (orchestration)

**Files to Create:**
- `packages/core/dealbrain_core/rules/__init__.py`
- `packages/core/dealbrain_core/rules/conditions.py`
- `packages/core/dealbrain_core/rules/actions.py`
- `packages/core/dealbrain_core/rules/evaluator.py`
- `packages/core/dealbrain_core/rules/formula.py`
- `tests/core/test_conditions.py`
- `tests/core/test_actions.py`
- `tests/core/test_evaluator.py`

**Condition Operators:**
- Equality: `equals`, `not_equals`
- Comparison: `greater_than`, `less_than`, `between`, `>=`, `<=`
- String: `contains`, `starts_with`, `ends_with`, `regex`
- Set: `in`, `not_in`
- Logical: `and`, `or`, `not`

**Action Types:**
1. `fixed_value`: Set specific dollar amount
2. `per_unit`: Value based on quantity (per-GB, per-core, etc.)
3. `benchmark_based`: Value proportional to performance score
4. `multiplier`: Apply percentage to base value
5. `additive`: Add/subtract fixed amount
6. `formula`: Custom calculation with safe eval

**Acceptance Criteria:**
- All operators functional with proper type handling
- Nested conditions (AND/OR groups) work correctly
- All action types calculate accurately
- Formula engine prevents code injection
- 90%+ test coverage

#### 1.3 Services Layer

**Tasks:**
- Create `RulesService` for CRUD operations
- Implement `RuleEvaluationService` with caching
- Build `RulePreviewService` for impact analysis
- Integrate with existing `ListingsService`

**Files to Create:**
- `apps/api/dealbrain_api/services/rules.py`
- `apps/api/dealbrain_api/services/rule_evaluation.py`
- `apps/api/dealbrain_api/services/rule_preview.py`
- `tests/services/test_rules_service.py`
- `tests/services/test_evaluation_service.py`

**RulesService Methods:**
- `create_ruleset()`, `get_ruleset()`, `list_rulesets()`, `update_ruleset()`, `delete_ruleset()`
- `create_rule_group()`, `get_rule_group()`, etc.
- `create_rule()`, `get_rule()`, `list_rules()`, `update_rule()`, `delete_rule()`
- Validation layer to prevent invalid rules

**Acceptance Criteria:**
- CRUD operations work with proper error handling
- Validation prevents invalid configurations
- Integration tests pass
- Caching improves performance

#### 1.4 API Endpoints

**Tasks:**
- Create Pydantic schemas for requests/responses
- Implement REST endpoints
- Add filtering, search, pagination
- Generate OpenAPI documentation

**Files to Create:**
- `apps/api/dealbrain_api/schemas/rules.py`
- `apps/api/dealbrain_api/api/rules.py`
- `tests/api/test_rules_api.py`

**Endpoints:**
```
# Rulesets
POST   /api/v1/rulesets
GET    /api/v1/rulesets
GET    /api/v1/rulesets/{id}
PUT    /api/v1/rulesets/{id}
DELETE /api/v1/rulesets/{id}

# Rule Groups
POST   /api/v1/rule-groups
GET    /api/v1/rule-groups
GET    /api/v1/rule-groups/{id}

# Rules
POST   /api/v1/valuation-rules
GET    /api/v1/valuation-rules
GET    /api/v1/valuation-rules/{id}
PUT    /api/v1/valuation-rules/{id}
DELETE /api/v1/valuation-rules/{id}
POST   /api/v1/valuation-rules/preview

# Import/Export
POST   /api/v1/valuation-rules/import
GET    /api/v1/valuation-rules/export
```

**Acceptance Criteria:**
- All endpoints return correct status codes
- Request/response schemas validated
- Error handling with clear messages
- API documentation complete

---

### Phase 2: UI Development

**Goal:** Complete user interface for rule management

#### 2.1 Rules Management Page

**Tasks:**
- Create hierarchical list view (Ruleset → Group → Rule)
- Implement expand/collapse functionality
- Add search and filtering
- Quick actions (edit, duplicate, delete)

**Files to Create:**
- `apps/web/app/valuation-rules/page.tsx`
- `apps/web/components/rules/rules-list.tsx`
- `apps/web/components/rules/ruleset-card.tsx`
- `apps/web/components/rules/rule-group-card.tsx`
- `apps/web/components/rules/rule-item.tsx`
- `apps/web/lib/api/rules.ts`

**Component Hierarchy:**
```tsx
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
- Responsive design (mobile/tablet/desktop)
- Keyboard navigation works
- Loading and empty states
- Optimistic updates with React Query

#### 2.2 Rule Builder Modal

**Tasks:**
- Create multi-step wizard modal
- Build condition builder with field selector
- Implement action configuration UI
- Add live preview panel

**Files to Create:**
- `apps/web/components/rules/rule-modal.tsx`
- `apps/web/components/rules/condition-builder.tsx`
- `apps/web/components/rules/field-selector.tsx`
- `apps/web/components/rules/action-builder.tsx`
- `apps/web/components/rules/rule-preview.tsx`

**Modal Steps:**
1. **Basic Info**: Name, description, category, priority
2. **Conditions**: Field + operator + value (with nested AND/OR)
3. **Actions**: Type selection + configuration + modifiers
4. **Preview**: Affected listings + impact stats

**Condition Builder Features:**
- Searchable field selector (core + custom fields)
- Context-aware operator dropdown
- Type-appropriate value inputs
- Add nested condition groups
- Visual grouping (indentation, brackets)

**Action Builder Features:**
- Action type selector with descriptions
- Dynamic form based on type
- Modifier configuration (condition multipliers, age curves)
- Formula editor with syntax highlighting

**Preview Panel Features:**
- Real-time updates as conditions change
- Sample of 5-10 affected listings
- Before/after valuation comparison
- Impact statistics (count, avg change, min/max)

**Acceptance Criteria:**
- Form validation prevents invalid rules
- Field selector shows only relevant fields
- Preview updates without saving
- Keyboard shortcuts functional

#### 2.3 Import/Export UI

**Tasks:**
- Create import wizard (upload → map → preview → confirm)
- Build export dialog with format selection
- Add progress indicators

**Files to Create:**
- `apps/web/components/rules/import-wizard.tsx`
- `apps/web/components/rules/import-mapping.tsx`
- `apps/web/components/rules/import-preview.tsx`
- `apps/web/components/rules/export-dialog.tsx`

**Import Flow:**
1. Upload file (CSV, JSON, YAML, Excel)
2. Parse and validate structure
3. Map fields to schema
4. Preview affected data
5. Confirm and execute import
6. Show results summary

**Export Features:**
- Format selection (CSV, JSON, YAML, Excel, PDF docs)
- Filter selection (export subset of rules)
- Include dependencies checkbox
- Download as file or copy to clipboard

**Acceptance Criteria:**
- Supports all listed formats
- Field mapping intuitive
- Validation provides clear errors
- Progress indicators accurate

#### 2.4 Ruleset Management

**Tasks:**
- Build ruleset packaging UI
- Create version comparison view
- Implement audit log viewer

**Files to Create:**
- `apps/web/components/rules/ruleset-package.tsx`
- `apps/web/components/rules/ruleset-apply.tsx`
- `apps/web/components/rules/version-compare.tsx`
- `apps/web/components/rules/audit-log.tsx`

**Ruleset Package Features:**
- Metadata editor (name, version, author, description)
- Include custom field definitions
- Dependency detection and inclusion
- Export as `.dbrs` file

**Version Comparison:**
- Side-by-side diff view
- Highlight added/changed/removed rules
- Show field-level changes
- Rollback capability

**Audit Log:**
- Filterable by action, actor, date
- Searchable by rule name
- Export to CSV
- Impact summary per change

**Acceptance Criteria:**
- Package export is self-contained
- Version comparison highlights all diffs
- Audit log searchable and exportable

---

### Phase 3: Advanced Features

**Goal:** CLI, packaging, and scoring integration

#### 3.1 Ruleset Packaging

**Tasks:**
- Define `.dbrs` package format (JSON-based)
- Implement export logic with dependency resolution
- Create import validation and compatibility checking

**Files to Create:**
- `packages/core/dealbrain_core/rules/packaging.py`
- `apps/api/dealbrain_api/services/ruleset_packaging.py`

**Package Format:**
```json
{
  "schema_version": "1.0",
  "metadata": {
    "name": "Gaming PC Ruleset",
    "version": "1.2.0",
    "author": "User Name",
    "description": "Optimized for gaming PC valuations",
    "created_at": "2025-10-01T10:00:00Z",
    "compatibility": {
      "min_app_version": "1.0.0",
      "required_custom_fields": ["ram_generation", "storage_gen"]
    }
  },
  "rulesets": [...],
  "rule_groups": [...],
  "rules": [...],
  "custom_field_definitions": [...],
  "examples": [...]
}
```

**Acceptance Criteria:**
- Package is portable and self-contained
- Import validates compatibility
- Missing dependencies detected and reported
- Roundtrip (export → import) preserves data

#### 3.2 CLI Implementation

**Tasks:**
- Add CLI commands for rule management
- Support import/export operations
- Enable preview and apply workflows

**Files to Create:**
- `apps/cli/dealbrain_cli/commands/rules.py`

**Commands:**
```bash
# List and view
dealbrain-cli rules list [--category CPU] [--ruleset "Gaming PC"]
dealbrain-cli rules show <rule-id>

# Create and edit
dealbrain-cli rules create --from-file rule.yaml
dealbrain-cli rules update <rule-id> --file changes.yaml

# Import/Export
dealbrain-cli rules import rules.csv --mapping mappings.json
dealbrain-cli rules export --format json --output rules.json

# Preview and apply
dealbrain-cli rules preview <rule-id>
dealbrain-cli rules apply <ruleset-name> --category listings

# Package management
dealbrain-cli rules package <ruleset-name> --output gaming-v1.dbrs
dealbrain-cli rules install gaming-v1.dbrs
```

**Acceptance Criteria:**
- All commands functional with proper error handling
- Help text comprehensive
- Output formatted for readability
- Progress indicators for long operations

#### 3.3 Weighted Scoring Integration

**Tasks:**
- Enhance Profile model with rule group weights
- Update scoring engine to apply weights
- Create weight configuration UI

**Files to Modify:**
- `packages/core/dealbrain_core/scoring.py`
- `apps/api/dealbrain_api/services/scoring.py`
- `apps/api/dealbrain_api/models/core.py` (Profile model)

**Files to Create:**
- `apps/web/components/profiles/weight-config.tsx`

**Weight Configuration:**
```json
{
  "profile_id": 1,
  "profile_name": "Gaming Focus",
  "rule_group_weights": {
    "cpu_valuation": 0.25,
    "gpu_valuation": 0.45,  // Higher for gaming
    "ram_valuation": 0.15,
    "storage_valuation": 0.10,
    "chassis_valuation": 0.05
  }
}
```

**Acceptance Criteria:**
- Weights sum to 1.0 (validated)
- Score recalculation accurate
- Profile comparison shows weight differences
- UI includes weight sliders and distribution chart

---

### Phase 4: Testing & Optimization

**Goal:** Ensure quality and performance

#### 4.1 Performance Optimization

**Tasks:**
- Profile rule evaluation performance
- Add Redis caching for rule definitions
- Optimize database queries
- Implement batch processing for bulk operations

**Performance Targets:**
- Single listing evaluation: <100ms
- Bulk evaluation (1000 listings): <5s
- Rule list loading: <500ms
- Preview generation: <2s

**Optimization Strategies:**
- Cache compiled rule definitions
- Use database query optimization (proper joins, indexes)
- Batch database operations
- Implement request coalescing

**Acceptance Criteria:**
- All performance targets met
- No N+1 query problems
- Caching reduces evaluation time by 60%+
- Load test passes at 50 concurrent users

#### 4.2 Testing

**Unit Tests (90%+ coverage):**
- Core domain logic (conditions, actions, evaluator)
- Formula parser edge cases
- All operators and action types

**Integration Tests:**
- Services layer (CRUD, evaluation, preview)
- Database operations
- API endpoints

**E2E Tests:**
- Create ruleset → Add rules → Apply to listings
- Import rules → Preview → Confirm
- Package ruleset → Export → Import

**Tools:**
- pytest + pytest-asyncio (backend)
- Playwright or Cypress (E2E)
- Locust or k6 (load testing)

**Acceptance Criteria:**
- All test suites pass
- Code coverage >90%
- E2E tests cover critical paths
- Load tests validate performance

#### 4.3 Documentation

**Tasks:**
- Write user guide with screenshots
- Create API documentation (OpenAPI)
- Document CLI commands
- Create example rule definitions
- Write FAQ and troubleshooting guide

**Deliverables:**
- User guide (Markdown)
- API reference (auto-generated)
- CLI reference (auto-generated)
- Example library (10+ rule templates)
- Video tutorial (optional)

**Acceptance Criteria:**
- All features documented
- Examples for common use cases
- Troubleshooting covers known issues
- API docs complete with examples

---

## Testing Strategy

### Unit Tests

**Coverage Target:** 90%+

**Core Domain Logic:**
```python
# tests/core/test_conditions.py
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

def test_nested_conditions():
    # AND group
    group = ConditionGroup(
        conditions=[
            Condition(...),
            Condition(...)
        ],
        logical_operator=LogicalOperator.AND
    )
    assert group.evaluate(context) == True
```

### Integration Tests

**Services Layer:**
```python
# tests/services/test_rules_service.py
@pytest.mark.asyncio
async def test_create_rule(db_session):
    service = RulesService()

    rule = await service.create_rule(
        session=db_session,
        group_id=1,
        name="Test Rule",
        conditions=[{
            "field_name": "ram_gb",
            "operator": "greater_than",
            "value": 16
        }],
        actions=[{
            "action_type": "per_unit",
            "metric": "per_gb",
            "value_usd": 3.50
        }]
    )

    assert rule.id is not None
    assert rule.name == "Test Rule"
```

### API Tests

**Endpoints:**
```python
# tests/api/test_rules_api.py
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

def test_preview_rule(client):
    response = client.post("/api/v1/valuation-rules/preview", json={
        "conditions": [...],
        "actions": [...],
        "sample_size": 10
    })

    assert response.status_code == 200
    data = response.json()
    assert len(data["sample_listings"]) <= 10
    assert "impact_stats" in data
```

### E2E Tests

**User Flows (Playwright):**
```typescript
// tests/e2e/rules.spec.ts
test('create and apply ruleset', async ({ page }) => {
  // Navigate to rules page
  await page.goto('/valuation-rules');

  // Create ruleset
  await page.click('button:has-text("New Ruleset")');
  await page.fill('input[name="name"]', 'Test Ruleset');
  await page.click('button:has-text("Create")');

  // Add rule
  await page.click('button:has-text("Add Rule")');
  // ... configure rule ...

  // Apply to listings
  await page.click('button:has-text("Apply to Listings")');
  await expect(page.locator('.success-message')).toBeVisible();
});
```

---

## Deployment Plan

### Pre-Deployment Checklist

- [ ] All tests pass (unit, integration, E2E)
- [ ] Performance targets met
- [ ] Code review complete
- [ ] Database migration tested
- [ ] Documentation complete
- [ ] Seed data prepared

### Deployment Steps

1. **Database Migration**
   - Backup database (just in case)
   - Run migration: `alembic upgrade head`
   - Verify new tables created
   - Run seed script for example data

2. **API Deployment**
   - Deploy updated API code
   - Restart API service
   - Verify endpoints responding

3. **Frontend Deployment**
   - Build frontend: `pnpm build`
   - Deploy static assets
   - Verify UI loads

4. **Validation**
   - Smoke test critical paths
   - Check monitoring dashboards
   - Verify no errors in logs

### Rollback Procedure

**If deployment fails:**

1. **Database Rollback**
   - Run: `alembic downgrade -1`
   - Verify old schema restored

2. **Code Rollback**
   - Revert API deployment
   - Revert frontend deployment
   - Restart services

3. **Validation**
   - Test existing functionality
   - Verify data integrity
   - Check error logs

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
- Most used condition operators
- Most used action types

**Health:**
- API uptime
- Database connection pool usage
- Error rate by endpoint
- Background job failures

### Alerts

**Critical:**
- API error rate >5%
- Database connection failures
- Rule evaluation time >500ms (p95)

**Warning:**
- Cache hit rate <80%
- Import job failures
- High memory usage (>80%)

### Dashboards

**Grafana Dashboards:**
1. **Rules Overview**: Rules created, active rulesets, evaluation time
2. **API Performance**: Request rate, response time, error rate
3. **Database Health**: Query time, connection pool, slow queries
4. **User Activity**: Rules created, imports, exports, preview usage

---

## Success Criteria

### Phase 1 Complete When:
- ✅ Database schema deployed
- ✅ Core domain logic functional (all operators/actions)
- ✅ Services layer operational
- ✅ API endpoints responding
- ✅ Unit tests passing (90%+ coverage)

### Phase 2 Complete When:
- ✅ Rules management UI functional
- ✅ Rule builder modal operational
- ✅ Import/export working
- ✅ Ruleset management complete

### Phase 3 Complete When:
- ✅ Ruleset packaging working
- ✅ CLI commands functional
- ✅ Weighted scoring integrated

### Phase 4 Complete When:
- ✅ Performance targets met
- ✅ All tests passing
- ✅ Documentation complete
- ✅ Ready for production use

---

## Appendix

### Example Rule Definitions

#### DDR5 RAM Premium Pricing (YAML)
```yaml
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
```

#### High-End CPU (Benchmark-Based)
```yaml
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
```

#### NVMe Gen4 Storage Premium
```yaml
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

### Tech Stack

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
- TanStack Query
- Tailwind CSS
- shadcn/ui

**Testing:**
- pytest + pytest-asyncio
- Playwright or Cypress
- Locust or k6

**DevOps:**
- Docker & Docker Compose
- Prometheus + Grafana
- OpenTelemetry

---

**End of Implementation Plan**
