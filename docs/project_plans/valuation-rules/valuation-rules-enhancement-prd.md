# Product Requirements Document: Advanced Valuation Rules System

**Version:** 1.0
**Date:** October 1, 2025
**Status:** Draft
**Author:** Technical Architecture Team

---

## Executive Summary

This PRD defines the comprehensive enhancement of Deal Brain's valuation rules system, transforming it from a simple component-based pricing engine into a sophisticated, flexible, and explainable hardware valuation platform. The enhancement enables users to create, manage, and apply complex valuation strategies through hierarchical rule structures, conditional logic, weighted scoring, and shareable rulesets.

### Strategic Goals

1. **Flexibility**: Support diverse valuation methodologies across different hardware categories
2. **Explainability**: Provide transparent, auditable valuation breakdowns
3. **Portability**: Enable ruleset sharing and reuse across use cases
4. **Scalability**: Handle complex conditional logic without performance degradation
5. **Usability**: Deliver intuitive UI/UX for rule creation and management

---

## Problem Statement

### Current Limitations

The existing valuation system operates with a flat, rigid structure:

- **Fixed Component Types**: Limited to predefined categories (RAM, SSD, HDD, etc.)
- **Simple Metrics**: Only supports per-GB, per-TB, or flat pricing
- **No Conditional Logic**: Cannot apply rules based on field combinations or ranges
- **Limited Hierarchy**: No grouping or organization of related rules
- **No Rule Composition**: Cannot combine multiple rules or apply modifiers
- **Poor Explainability**: Breakdown shows deductions but lacks context for why rules applied
- **No Portability**: Rules cannot be packaged, shared, or versioned

### User Impact

Users currently cannot:

- Differentiate CPU valuations by specific models or benchmark scores
- Apply RAM pricing that varies by speed, generation (DDR4 vs DDR5), or capacity
- Value storage with compound modifiers (type × capacity × speed)
- Create chassis valuations with base pricing plus per-port valuations
- Compare different valuation strategies (gaming vs. workstation vs. server)
- Share their valuation methodology with team members or community
- Preview rule impact before committing changes

---

## Target Users

### Primary Personas

1. **Hardware Resellers**
   - Need accurate, consistent pricing across inventory
   - Require quick adjustments based on market conditions
   - Value explainability for customer negotiations

2. **Deal Hunters**
   - Compare listings across multiple marketplaces
   - Need customizable valuation based on personal priorities
   - Seek value in specific component categories (e.g., GPU-focused)

3. **System Integrators**
   - Evaluate parts for custom builds
   - Need component-level price/performance analysis
   - Require different rulesets for different build types

### Secondary Personas

4. **Hardware Enthusiasts**
   - Share valuation strategies in communities
   - Experiment with different scoring methodologies
   - Create specialized rulesets (vintage hardware, enterprise gear)

---

## Requirements

### Functional Requirements

#### FR1: Hierarchical Rule Structure

**Priority:** P0 (Critical)

Rules must be organized hierarchically:

```
Ruleset (e.g., "Gaming PC Valuation Q4 2025")
  └── Rule Group (e.g., "CPU Valuation")
      ├── Rule (e.g., "Intel i7-14700K Specific Pricing")
      ├── Rule (e.g., "Passmark Score-Based Fallback")
      └── Rule (e.g., "Generation-Based Modifier")
```

**Acceptance Criteria:**
- Rulesets contain multiple rule groups
- Rule groups organize related rules by component category
- Rules within groups can have priority/order
- System evaluates rules in defined order (specific → general)

#### FR2: Advanced Conditional Logic

**Priority:** P0 (Critical)

Rules must support complex conditions:

**Operators:**
- Equality: `equals`, `not_equals`
- Comparison: `greater_than`, `less_than`, `between`
- String: `contains`, `starts_with`, `ends_with`, `regex`
- Set: `in`, `not_in`
- Logical: `and`, `or`, `not`

**Field Types:**
- Core fields: CPU, GPU, RAM, storage, condition, etc.
- Custom fields: User-defined attributes
- Derived fields: Calculated values (e.g., total storage capacity)
- Benchmark scores: Passmark, Metal, etc.

**Examples:**
```yaml
# Example 1: Range-based RAM pricing
condition:
  field: ram_gb
  operator: between
  value: [16, 32]
action:
  type: set_value
  value_per_gb: 2.50

# Example 2: Compound CPU valuation
condition:
  operator: and
  conditions:
    - field: cpu.manufacturer
      operator: equals
      value: "Intel"
    - field: cpu.cpu_mark_multi
      operator: greater_than
      value: 20000
action:
  type: benchmark_based
  metric: cpu_mark_multi
  value_per_1000_points: 5.00
```

**Acceptance Criteria:**
- Support all listed operators
- Enable nested condition groups (AND/OR combinations)
- Validate field types and operator compatibility
- Provide clear error messages for invalid conditions

#### FR3: Flexible Valuation Actions

**Priority:** P0 (Critical)

Rules must support diverse pricing actions:

**Action Types:**

1. **Fixed Value**: Assign specific dollar amount
2. **Per-Unit Pricing**: Value based on quantity (per-GB, per-core, etc.)
3. **Benchmark-Based**: Value proportional to performance metric
4. **Multiplier**: Apply percentage adjustment to base value
5. **Additive**: Add/subtract fixed amount
6. **Formula**: Custom calculation using field values

**Modifiers:**
- Condition multipliers (new/refurb/used)
- Age depreciation curves
- Brand/model premiums/discounts
- Quantity tiers (bulk discounts)

**Acceptance Criteria:**
- Support all action types
- Enable chaining of multiple actions
- Calculate and store intermediate values for explainability
- Handle edge cases (division by zero, negative values)

#### FR4: Rule Groups and Component Categories

**Priority:** P0 (Critical)

Organize rules by hardware category with category-specific behaviors:

**Core Categories:**
- **CPU**: Model-specific, benchmark-based, or generation-based
- **RAM**: Capacity, speed, generation (DDR3/4/5), ECC support
- **Storage**: Type (NVMe/SATA/HDD), capacity, speed
- **GPU**: Model-specific, benchmark-based, VRAM-based
- **Chassis**: Base value, form factor, condition, expandability
- **Ports/IO**: Per-port valuation with type-specific pricing
- **OS License**: Type (Windows Pro/Home, Linux), version
- **Peripherals**: Keyboard, mouse, WiFi, Bluetooth

**Acceptance Criteria:**
- Each category has default fields available for conditions
- Categories support custom fields
- UI organizes rules by category
- Import/export preserves category structure

#### FR5: Rule Preview and Impact Analysis

**Priority:** P1 (High)

Before saving, users must see rule impact:

**Preview Features:**
- Sample affected listings (5-10 examples)
- Before/after valuation comparison
- Count of listings affected
- Statistical summary (avg change, min/max impact)
- Warning for significant changes (>20% valuation shift)

**Acceptance Criteria:**
- Preview updates in real-time as conditions change
- Shows both positive and negative impacts
- Provides filtering to see specific listing types
- Includes confidence indicators for rule quality

#### FR6: Valuation Rules Management Page

**Priority:** P0 (Critical)

Comprehensive UI for rule management:

**Features:**
- List all rulesets with metadata (name, description, version, last modified)
- Expand ruleset to view rule groups
- Expand groups to view individual rules
- Quick actions: Edit, Duplicate, Delete, Export
- Filtering by category, condition, date modified
- Search across rule names, descriptions, conditions
- Bulk operations (enable/disable, delete)
- Rule validation status indicators

**Layout:**
```
┌─────────────────────────────────────────────────┐
│ Valuation Rules                    [+ New Rule] │
├─────────────────────────────────────────────────┤
│ Search: [________]  Filter: [All ▼] [Export All]│
├─────────────────────────────────────────────────┤
│ ▼ Gaming PC Ruleset (v1.2)       [⚙] [↓] [🗑]  │
│   │                                              │
│   ├─ ▼ CPU Valuation (12 rules)                │
│   │   ├─ Intel i7-14700K                [✓]    │
│   │   ├─ AMD Ryzen 7 7800X3D             [✓]    │
│   │   └─ Passmark Fallback               [✓]    │
│   │                                              │
│   ├─ ▶ RAM Valuation (8 rules)                 │
│   ├─ ▶ Storage Valuation (6 rules)             │
│   └─ ▶ GPU Valuation (15 rules)                │
│                                                  │
│ ▼ Workstation Ruleset (v2.0)     [⚙] [↓] [🗑]  │
│   └─ ...                                         │
└─────────────────────────────────────────────────┘
```

**Acceptance Criteria:**
- All CRUD operations functional
- Intuitive expand/collapse for hierarchy
- Responsive design for mobile/tablet
- Keyboard shortcuts for power users
- Undo/redo for destructive operations

#### FR7: Rule Creation Modal

**Priority:** P0 (Critical)

Modal dialog for creating/editing rules:

**Sections:**

1. **Basic Info**
   - Rule name (required)
   - Description (optional)
   - Category (dropdown)
   - Priority/order (numeric)

2. **Conditions**
   - Field selector (searchable dropdown)
   - Operator selector (context-aware)
   - Value input (type-appropriate)
   - Add condition group (AND/OR)
   - Preview matching listings count

3. **Actions**
   - Action type selector
   - Value inputs (context-aware)
   - Modifier configuration
   - Formula builder (for custom calculations)

4. **Preview**
   - Live preview of affected listings
   - Impact summary statistics
   - Validation warnings/errors

**Acceptance Criteria:**
- Form validation prevents invalid rules
- Field dropdown shows only relevant fields for category
- Preview updates without saving
- Can save as draft or publish immediately
- Supports keyboard navigation

#### FR8: Import/Export Rules

**Priority:** P1 (High)

Support importing and exporting valuation rules:

**Import Formats:**
- CSV: Flat structure for simple rules
- JSON: Full structure with nested conditions
- YAML: Human-readable rule definitions
- Excel: Workbook with sheets per category

**Export Formats:**
- Same as import formats
- Additional: PDF documentation of ruleset

**Import Process:**
1. Upload file
2. Parse and validate structure
3. Preview field mappings
4. Map custom fields (if applicable)
5. Preview impact on existing listings
6. Confirm and import
7. Audit log entry

**Acceptance Criteria:**
- Validates file structure before import
- Detects and resolves conflicts (duplicate rule names)
- Supports partial imports (skip invalid rows)
- Preserves rule relationships and hierarchy
- Generates import summary report

#### FR9: Packaged Rulesets

**Priority:** P1 (High)

Enable sharing complete valuation strategies:

**Ruleset Package Contains:**
- Metadata (name, version, author, description)
- All rules and rule groups
- Custom field definitions referenced
- Example listings for testing
- Documentation/README
- Changelog

**Ruleset Operations:**
- Create from existing rules
- Export as `.dbrs` file (Deal Brain Ruleset)
- Import from `.dbrs` file
- Apply ruleset to specific listing categories
- Version tracking and updates
- Community sharing (future: marketplace)

**Acceptance Criteria:**
- Package file is self-contained and portable
- Import validates compatibility (field requirements)
- Provides migration path for schema changes
- Tracks ruleset lineage (forked from, based on)

#### FR10: CLI and API Support

**Priority:** P1 (High)

Full programmatic access to rule management:

**CLI Commands:**
```bash
# List rules
dealbrain-cli rules list [--category CPU] [--ruleset "Gaming PC"]

# Create rule
dealbrain-cli rules create --from-file rule.yaml

# Import rules
dealbrain-cli rules import rules.csv --mapping mappings.json

# Export rules
dealbrain-cli rules export --format json --output rules.json

# Apply ruleset
dealbrain-cli rules apply "Gaming PC" --category listings --preview

# Package ruleset
dealbrain-cli rules package "Gaming PC" --output gaming-v1.dbrs
```

**API Endpoints:**
```
POST   /api/v1/valuation-rules
GET    /api/v1/valuation-rules
GET    /api/v1/valuation-rules/{id}
PUT    /api/v1/valuation-rules/{id}
DELETE /api/v1/valuation-rules/{id}
POST   /api/v1/valuation-rules/preview
POST   /api/v1/valuation-rules/import
GET    /api/v1/valuation-rules/export
POST   /api/v1/rulesets
GET    /api/v1/rulesets
GET    /api/v1/rulesets/{id}/apply
```

**Acceptance Criteria:**
- CLI matches web UI functionality
- API returns consistent response schemas
- Supports pagination for list endpoints
- Includes filtering and search
- Rate limiting for import/export operations

#### FR11: Weighted Scoring Integration

**Priority:** P2 (Medium)

Rules contribute to composite scoring:

**Weighting System:**
- Each rule group has configurable weight (0.0-1.0)
- Weights apply to overall valuation score
- Different profiles can use same rules with different weights

**Example:**
```yaml
profile: "Gaming Focus"
weights:
  cpu_valuation: 0.25
  gpu_valuation: 0.45  # Higher weight for gaming
  ram_valuation: 0.15
  storage_valuation: 0.10
  chassis_valuation: 0.05
```

**Acceptance Criteria:**
- Weights sum to 1.0 (validated)
- Weight changes recalculate all affected listings
- Profile comparison shows weight differences
- Historical weight changes tracked

#### FR12: Audit Trail and Versioning

**Priority:** P2 (Medium)

Track all rule changes:

**Audit Log Captures:**
- Who made the change
- When the change occurred
- What changed (field-level diff)
- Why (optional comment)
- Impact (listings affected)

**Version Control:**
- Each rule change creates new version
- Can view historical versions
- Can rollback to previous version
- Can compare versions side-by-side

**Acceptance Criteria:**
- Audit log immutable
- Searchable and filterable
- Exportable for compliance
- Retention policy configurable

---

### Non-Functional Requirements

#### NFR1: Performance

- Rule evaluation: <100ms for single listing
- Bulk evaluation: <5s for 1000 listings
- Preview generation: <2s for sample of 10 listings
- Rule list loading: <500ms
- Import processing: <30s for 1000 rules

#### NFR2: Scalability

- Support 10,000+ rules per instance
- Support 100,000+ listings
- Handle 50+ concurrent rule evaluations
- Efficiently query complex condition hierarchies

#### NFR3: Usability

- Rule creation completable in <5 minutes
- Intuitive for non-technical users
- Contextual help and examples
- Keyboard shortcuts for power users
- Mobile-responsive design

#### NFR4: Reliability

- 99.9% uptime for rule evaluation
- Graceful degradation (fallback to simple rules)
- Validation prevents invalid rules
- Transaction rollback on import failures

#### NFR5: Security

- Role-based access control (admin/editor/viewer)
- Audit log for all changes
- Input validation and sanitization
- Rate limiting on API endpoints
- Secure export (no sensitive data leakage)

---

## User Stories

### Epic 1: Rule Management

**US1.1: As a reseller, I want to view all my valuation rules organized by category, so I can quickly understand my pricing strategy.**

**US1.2: As a deal hunter, I want to create a new rule with conditional logic, so I can value hardware based on specific criteria.**

**US1.3: As a system integrator, I want to preview the impact of a rule before saving, so I can avoid unintended valuation changes.**

**US1.4: As a hardware enthusiast, I want to duplicate and modify existing rules, so I can experiment with different strategies.**

### Epic 2: Complex Valuation Logic

**US2.1: As a reseller, I want to value CPUs based on Passmark scores, so I can price unfamiliar models accurately.**

**US2.2: As a deal hunter, I want to apply different RAM pricing for DDR4 vs DDR5, so my valuations reflect current market premiums.**

**US2.3: As a system integrator, I want to value storage with modifiers for type and speed, so I can differentiate NVMe Gen4 from SATA SSDs.**

**US2.4: As a hardware enthusiast, I want to create chassis valuations that include per-port pricing, so I can reward systems with better IO.**

### Epic 3: Ruleset Management

**US3.1: As a reseller, I want to package my valuation rules as a shareable ruleset, so I can standardize pricing across my team.**

**US3.2: As a deal hunter, I want to maintain separate rulesets for gaming PCs and workstations, so I can apply appropriate valuations.**

**US3.3: As a system integrator, I want to export my ruleset to JSON, so I can version control it alongside my business processes.**

**US3.4: As a hardware enthusiast, I want to import a community ruleset, so I can benefit from shared expertise.**

### Epic 4: Import/Export

**US4.1: As a reseller, I want to import rules from Excel, so I can bulk-update pricing based on supplier data.**

**US4.2: As a deal hunter, I want to map imported fields to custom fields, so I can integrate external pricing sources.**

**US4.3: As a system integrator, I want to export rules to CSV for analysis in Excel, so I can visualize pricing strategies.**

### Epic 5: API and Automation

**US5.1: As a developer, I want to create rules via API, so I can automate rule management based on market data.**

**US5.2: As a system integrator, I want to apply rulesets via CLI, so I can integrate valuation into CI/CD pipelines.**

---

## Success Metrics

### Primary Metrics

1. **Adoption Rate**: % of users creating custom rules (Target: 60% within 3 months)
2. **Rule Complexity**: Average conditions per rule (Baseline: 1, Target: 3+)
3. **Valuation Accuracy**: User-reported accuracy improvement (Target: 25% reduction in manual adjustments)
4. **Ruleset Sharing**: # of rulesets exported/imported (Target: 500 shares in 6 months)

### Secondary Metrics

5. **Time to Create Rule**: Median time (Target: <5 minutes)
6. **Preview Usage**: % of rule creations using preview (Target: 80%)
7. **Import Volume**: Rules imported per month (Growth target: 20% MoM)
8. **API Adoption**: % of rules created via API (Target: 30%)

### Quality Metrics

9. **Rule Errors**: % of rules with validation errors (Target: <5%)
10. **Performance**: 95th percentile evaluation time (Target: <100ms)
11. **User Satisfaction**: NPS for valuation features (Target: 50+)

---

## Out of Scope (Future Phases)

### Phase 2 (Q1 2026)
- Machine learning-based rule suggestions
- Automated rule optimization based on market data
- Collaborative rule editing (team workspaces)
- Conditional rule activation (time-based, event-driven)

### Phase 3 (Q2 2026)
- Marketplace for ruleset sharing
- Paid premium rulesets
- Integration with external pricing APIs
- Mobile app for rule management

### Phase 4 (Q3 2026)
- Natural language rule creation ("Value DDR5 RAM 50% higher than DDR4")
- Visual rule builder (drag-and-drop conditions)
- A/B testing for valuation strategies
- Predictive pricing (forecast future values)

---

## Risks and Mitigations

### Technical Risks

**R1: Performance Degradation with Complex Rules**
- **Impact:** High
- **Probability:** Medium
- **Mitigation:**
  - Implement rule caching and memoization
  - Optimize database queries with proper indexing
  - Provide complexity warnings in UI
  - Load test with realistic rule sets

**R2: Data Migration Complexity**
- **Impact:** High
- **Probability:** Medium
- **Mitigation:**
  - Create comprehensive migration scripts
  - Support backward compatibility for 2 versions
  - Provide rollback mechanisms
  - Extensive testing in staging environment

**R3: Condition Evaluation Edge Cases**
- **Impact:** Medium
- **Probability:** High
- **Mitigation:**
  - Comprehensive test suite with edge cases
  - Validation layer prevents invalid rules
  - Clear error messaging for rule authors
  - Fallback to simple rules if complex rule fails

### Product Risks

**R4: Feature Complexity Overwhelms Users**
- **Impact:** High
- **Probability:** Medium
- **Mitigation:**
  - Progressive disclosure in UI
  - Provide templates for common scenarios
  - Comprehensive onboarding flow
  - Optional "simple mode" for basic rules

**R5: Import/Export Format Incompatibilities**
- **Impact:** Medium
- **Probability:** High
- **Mitigation:**
  - Strict schema validation on import
  - Clear documentation of formats
  - Provide example files
  - Import wizard with validation feedback

**R6: Ruleset Versioning Conflicts**
- **Impact:** Medium
- **Probability:** Medium
- **Mitigation:**
  - Semantic versioning for rulesets
  - Compatibility checking on import
  - Migration tools for format changes
  - Deprecation warnings for old formats

---

## Dependencies

### Internal Dependencies
- Custom fields system (already implemented)
- Import pipeline enhancements
- Database schema migrations
- UI component library updates

### External Dependencies
- None (self-contained feature)

---

## Timeline Estimate

### Phase 1: Core Infrastructure (Weeks 1-4)
- Database schema design and migration
- Enhanced valuation engine
- Rule evaluation framework
- API foundation

### Phase 2: UI Development (Weeks 5-8)
- Rules management page
- Rule creation/editing modal
- Preview functionality
- Import/export flows

### Phase 3: Advanced Features (Weeks 9-11)
- Ruleset packaging
- Weighted scoring integration
- CLI commands
- Audit trail

### Phase 4: Testing and Refinement (Weeks 12-14)
- Performance optimization
- User acceptance testing
- Documentation
- Bug fixes and polish

**Total Duration:** 14 weeks (3.5 months)

---

## Appendix

### A. Example Rule Definitions

#### Example 1: DDR5 RAM Premium Pricing
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

#### Example 2: High-End CPU Benchmark Pricing
```yaml
name: "High-End CPU (Passmark 20K+)"
category: cpu
priority: 5
conditions:
  operator: and
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
  value_per_1000_points: 5.00
  base_value: 50.00
```

#### Example 3: Storage Type Hierarchy
```yaml
name: "NVMe Gen4 Storage Premium"
category: storage
priority: 8
conditions:
  operator: and
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
  multiplier: 1.5  # 50% premium over base storage value
```

### B. Database Schema Overview

**Tables:**
- `valuation_ruleset`: Container for related rules
- `valuation_rule_group`: Organizes rules by category
- `valuation_rule_v2`: Individual rule definitions
- `valuation_rule_condition`: Condition logic
- `valuation_rule_action`: Pricing actions
- `valuation_rule_audit`: Change history
- `valuation_rule_version`: Version snapshots

### C. API Response Examples

**GET /api/v1/valuation-rules/{id}**
```json
{
  "id": 42,
  "name": "DDR5 RAM Premium",
  "category": "ram",
  "ruleset_id": 5,
  "priority": 10,
  "conditions": [
    {
      "field": "custom.ram_generation",
      "operator": "equals",
      "value": "DDR5"
    }
  ],
  "action": {
    "type": "per_unit",
    "metric": "per_gb",
    "value": 4.50,
    "modifiers": {
      "condition_new": 1.0,
      "condition_refurb": 0.80,
      "condition_used": 0.65
    }
  },
  "created_at": "2025-10-01T10:00:00Z",
  "updated_at": "2025-10-01T10:00:00Z",
  "created_by": "admin",
  "version": 1
}
```

---

## Approval

**Product Owner:** _____________________
**Engineering Lead:** _____________________
**Date:** _____________________
