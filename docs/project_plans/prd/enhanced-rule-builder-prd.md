# Product Requirements Document: Enhanced Rule Builder

**Version:** 1.0
**Date:** 2025-10-03
**Status:** Draft
**Owner:** Lead Architect

---

## Executive Summary

This PRD outlines enhancements to the Deal Brain valuation rule system, transforming the basic rule builder into a comprehensive, user-friendly interface for creating complex pricing rules. The enhanced Rule Builder will provide intuitive visual tools for constructing multi-condition rules with AND/OR logic, real-time validation against sample listings, and comprehensive versioning support.

The goal is to empower users to create sophisticated valuation logic without technical knowledge, while maintaining explainability and system performance.

---

## Business Context

### Problem Statement

The current rule builder interface allows basic rule creation but lacks:
- **Structured condition building** with proper field selection from available entities
- **Real-time preview** of rule impact on actual listings
- **Nested logic support** (AND/OR grouping) for complex scenarios
- **Field-aware value inputs** (dropdowns for enum fields, type validation)
- **Version management** for iterative rule refinement
- **Guided UX** that explains rule concepts to non-technical users

### Success Metrics

- **Adoption Rate**: 100% of new rules created through enhanced builder (vs. manual DB edits)
- **Rule Complexity**: Average conditions per rule increases from 1-2 to 3-5
- **Error Reduction**: 90% reduction in invalid rules created
- **User Efficiency**: Rule creation time reduced by 50%
- **Explainability**: All rules have complete documentation and example impact

---

## User Personas

### Primary: Business Analyst / Valuation Manager
- **Needs**: Create and maintain complex pricing rules based on market conditions
- **Technical Level**: Non-technical, understands business logic
- **Pain Points**: Current builder requires understanding field names, no preview of changes
- **Goals**: Quickly test rule variations, understand impact before deployment

### Secondary: System Administrator
- **Needs**: Audit rule changes, rollback problematic rules, understand system behavior
- **Technical Level**: Semi-technical, understands data structures
- **Pain Points**: No version history, difficult to trace pricing anomalies to specific rules
- **Goals**: Maintain system integrity, ensure explainable valuations

---

## Functional Requirements

### 1. Structured Condition Builder

#### 1.1 Three-Step Field Selection
- **Entity Selector**: Dropdown presenting available entities (Listing, Component, CPU, GPU, etc.)
- **Field Selector**: Dynamically populated based on entity, showing all core and custom fields
- **Operator Selector**: Context-aware operators based on field data type:
  - `string`: equals, not_equals, contains, starts_with, ends_with, in, not_in
  - `number`: equals, not_equals, greater_than, less_than, gte, lte, between
  - `boolean`: is, is_not
  - `enum`: equals, not_equals, in, not_in
  - `date`: before, after, between, within_last_days

#### 1.2 Value Input with Field Awareness
- **String fields**: Text input with autocomplete if field has common values
- **Number fields**: Numeric input with validation, unit display
- **Enum/Dropdown fields**: Select component showing available options
- **Boolean fields**: Toggle or checkbox
- **Multi-value operators** (in, not_in): Multi-select or comma-separated input

#### 1.3 Nested Condition Groups
- **Logical Operators**: AND/OR buttons to group conditions
- **Visual Nesting**: Indentation and colored borders for condition groups
- **Drag-and-Drop**: Reorder conditions within and between groups
- **Group Actions**: Add, remove, collapse/expand groups

**Example Structure:**
```
Rule: "High-End Gaming Discount"
IF (
  Listing.condition = "new" AND
  CPU.cpu_mark_multi > 20000 AND
  (GPU.gpu_mark > 10000 OR GPU.name contains "RTX 4")
) THEN deduct $50
```

### 2. Predefined Condition Library

#### 2.1 Common Condition Templates
- **CPU Performance Tiers**: Low (<5000), Mid (5000-15000), High (15000-25000), Premium (>25000)
- **Storage Configurations**: SSD vs HDD, capacity ranges
- **Condition-Based**: New, Refurbished, Used
- **Component Combinations**: Integrated vs Discrete GPU, RAM tiers

#### 2.2 Custom Condition Saving
- Users can save frequently used condition combinations as templates
- Templates appear in quick-add menu
- Shared across users (with permissions)

### 3. Action Configuration

#### 3.1 Action Types
- **Fixed Value**: Flat price adjustment (e.g., -$50)
- **Per Unit**: Price per quantity of component (e.g., $5 per GB RAM)
- **Percentage**: Percent of listing price (e.g., +10%)
- **Benchmark-Based**: Price per performance metric (e.g., $0.02 per CPU Mark point)
- **Formula**: Custom expression (e.g., `ram_gb * 2.5 + storage_gb * 0.1`)
- **Flag/Tag**: Mark listing for review (non-price action)

#### 3.2 Condition Multipliers
- Apply different action values based on listing condition:
  - New: 100% of action value
  - Refurbished: 75% of action value
  - Used: 60% of action value
- Configurable per action

#### 3.3 Multiple Actions per Rule
- Rules can trigger multiple actions simultaneously
- Actions ordered by display priority
- Visual indicator of cumulative impact

### 4. Real-Time Rule Preview

#### 4.1 Sample Listing Display
- **Live Listing Selector**: Choose an existing listing or use system-suggested representative sample
- **Before/After Comparison**: Side-by-side view of:
  - Original price
  - Applied adjustments (itemized)
  - Final adjusted price
  - Percentage change

#### 4.2 Match Indicator
- **Visual Feedback**: Clear indication if sample listing matches rule conditions
- **Condition Highlighting**: Show which specific conditions pass/fail
- **Partial Match Explanation**: If rule doesn't apply, explain why (e.g., "CPU Mark is 15000, needs >20000")

#### 4.3 Impact Statistics
- **Matched Listings Count**: How many listings in the database would match this rule
- **Average Adjustment**: Mean price change across matched listings
- **Distribution**: Histogram of adjustment amounts
- **Outliers**: Flag listings with extreme adjustments for review

### 5. Rule Versioning System

#### 5.1 Automatic Version Creation
- Every save creates new version entry
- Stores complete rule snapshot (conditions, actions, metadata)
- Tracks change author and timestamp

#### 5.2 Version Comparison
- **Side-by-Side Diff**: Visual comparison of two versions
  - Added/removed/modified conditions highlighted
  - Action changes shown with before/after values
- **Change Summary**: Auto-generated description (e.g., "Added GPU requirement, increased discount from $40 to $50")

#### 5.3 Version Rollback
- One-click restore to previous version
- Creates new version (doesn't delete history)
- Requires confirmation with impact warning

#### 5.4 Version Metadata
- **Change Notes**: Optional text field for describing why change was made
- **Impact Report**: System-generated summary of listings affected
- **Performance Metrics**: Before/after comparison of average pricing, outlier count

### 6. User Guidance & Documentation

#### 6.1 Contextual Help
- Inline tooltips explaining each field and operator
- Example values for field inputs
- "Learn More" links to documentation

#### 6.2 Validation & Error Prevention
- **Real-time validation**: Check for invalid operators, empty fields, circular logic
- **Warning indicators**: Flag potentially problematic rules (e.g., always-false conditions)
- **Suggestions**: Offer alternatives for common mistakes

#### 6.3 Rule Templates
- Pre-built rule sets for common use cases:
  - "Basic Component Valuation"
  - "Condition-Based Adjustments"
  - "Performance Tier Pricing"
  - "Storage Capacity Scaling"
- One-click import with customization

---

## Non-Functional Requirements

### Performance
- **Condition Evaluation**: <50ms per listing per rule
- **Preview Generation**: <500ms for sample of 10 listings
- **Bulk Evaluation**: Process 1000 listings in <30 seconds
- **UI Responsiveness**: All interactions <100ms

### Scalability
- Support 100+ rules per ruleset without performance degradation
- Handle 10+ nested condition groups
- Maintain performance with 10,000+ listings

### Usability
- **Learnability**: Non-technical users can create first rule within 5 minutes
- **Efficiency**: Experienced users can create complex rule in <2 minutes
- **Error Recovery**: All actions reversible, no data loss
- **Accessibility**: WCAG 2.1 AA compliant

### Security
- **Audit Trail**: All rule changes logged with user, timestamp, changes
- **Permissions**: Role-based access control for rule creation/editing
- **Validation**: Server-side validation prevents malicious formula injection

---

## Technical Constraints

### Data Model
- Must leverage existing `ValuationRuleV2`, `ValuationRuleCondition`, `ValuationRuleAction` tables
- `ValuationRuleVersion` table already supports versioning requirements
- Custom field integration via `FieldRegistry` service

### API Design
- RESTful endpoints for rule CRUD operations
- Separate `/preview` endpoint for real-time evaluation
- WebSocket support for live preview updates (future enhancement)

### Frontend Architecture
- React components built on existing `rule-builder-modal.tsx` foundation
- React Query for state management and caching
- Shadcn UI components for consistent design

---

## Dependencies & Integration Points

### Backend Services
- **FieldRegistry**: Provides entity and field metadata for condition builder
- **CustomFieldService**: Enables custom field conditions
- **RuleEvaluationService**: Executes rule logic against listings
- **RulePreviewService**: Generates sample listing evaluations

### Frontend Components
- **FormField**: Reusable field components from `components/forms/`
- **Combobox**: Entity/field selection with search
- **Select/Dropdown**: Operator and value selection
- **Modal**: Rule builder dialog wrapper

### Database Schema
- Existing `valuation_rule_v2` table structure supports all requirements
- `parent_condition_id` enables nested logic groups
- `logical_operator` field supports AND/OR grouping

---

## Out of Scope (V1)

- **AI-Suggested Rules**: ML-based rule recommendations based on listing patterns
- **Bulk Rule Operations**: Edit multiple rules simultaneously
- **Rule Conflict Detection**: Identify overlapping or contradictory rules
- **Historical Impact Analysis**: Retroactive "what-if" analysis of rule changes
- **Rule Marketplace**: Share/import rule packages from community
- **Advanced Formula Editor**: Syntax highlighting, autocomplete for custom formulas
- **WebSocket Live Preview**: Real-time updates as user types (defer to V2)

These features are acknowledged as valuable but deferred to future iterations to maintain focus on core functionality.

---

## User Stories

### US-1: Create Rule with Nested Conditions
**As a** valuation manager
**I want to** create a rule that applies different discounts based on CPU tier AND GPU presence
**So that** I can accurately price high-performance systems

**Acceptance Criteria:**
- Can select "Listing" entity and drill down to "cpu.cpu_mark_multi" field
- Can add OR condition group for GPU requirements
- Preview shows matched listings and price impact
- Rule saves successfully with nested structure

### US-2: Preview Rule Impact on Sample Listing
**As a** business analyst
**I want to** see how my rule would affect a specific listing before saving
**So that** I can verify the rule logic is correct

**Acceptance Criteria:**
- Can select an existing listing as sample
- UI shows before/after pricing with itemized adjustments
- Condition matching status is clearly indicated
- Can switch sample listings to test different scenarios

### US-3: Rollback Problematic Rule Version
**As a** system administrator
**I want to** restore a previous version of a rule that caused pricing issues
**So that** I can quickly fix valuation errors

**Acceptance Criteria:**
- Can view version history for any rule
- Can compare two versions side-by-side
- Can restore previous version with single click
- System confirms impact and creates new version entry

### US-4: Use Dropdown for Enum Field Values
**As a** valuation manager
**I want to** select "condition" values from a dropdown instead of typing
**So that** I avoid typos and ensure valid values

**Acceptance Criteria:**
- Condition field shows dropdown with "new", "refurb", "used"
- Invalid values cannot be entered
- Dropdown auto-closes after selection
- Works for all custom dropdown fields

### US-5: Clone and Modify Existing Rule
**As a** business analyst
**I want to** duplicate an existing rule and modify it
**So that** I can quickly create variations for testing

**Acceptance Criteria:**
- "Duplicate" button on rule list
- New rule opens in builder with original rule data
- Rule name auto-appends " (Copy)" to distinguish
- All conditions and actions copied correctly

---

## Design Considerations

### UI/UX Principles

**Progressive Disclosure**: Start with simple interface, reveal advanced options as needed
- Default view shows 1 condition, 1 action
- "Advanced" toggle reveals nested groups, multiple actions, condition multipliers

**Immediate Feedback**: Show impact of changes in real-time
- Preview updates as user modifies conditions
- Visual indicators for validation errors
- Loading states for async operations

**Guided Discovery**: Help users understand system through use
- Tooltips on first visit (dismissible)
- Placeholder text with examples
- Success messages explain what happened

**Error Prevention over Recovery**: Design to avoid mistakes
- Disable invalid operators for field types
- Warn before destructive actions
- Autosave drafts to prevent data loss

### Component Hierarchy

```
RuleBuilderModal (orchestrator)
├── RuleBasicInfo (name, description, priority)
├── ConditionBuilder
│   ├── ConditionGroup (supports nesting)
│   │   ├── ConditionRow
│   │   │   ├── EntitySelector
│   │   │   ├── FieldSelector
│   │   │   ├── OperatorSelector
│   │   │   └── ValueInput (polymorphic based on field type)
│   │   └── LogicalOperatorToggle
│   └── AddConditionButton
├── ActionBuilder
│   ├── ActionRow
│   │   ├── ActionTypeSelector
│   │   ├── ActionValueInputs (varies by type)
│   │   └── ConditionMultiplierEditor
│   └── AddActionButton
├── RulePreviewPanel
│   ├── SampleListingSelector
│   ├── BeforeAfterComparison
│   ├── ConditionMatchIndicators
│   └── ImpactStatistics
└── VersionHistory (collapsible drawer)
    ├── VersionListItem (per version)
    └── VersionComparison (side-by-side diff)
```

### Data Flow

1. **Rule Load**: Fetch rule + version history from API
2. **User Input**: Modify conditions/actions in builder
3. **Client-Side Validation**: Check for basic errors (required fields, valid types)
4. **Preview Request**: Send current rule state to `/rules/preview` endpoint
5. **Preview Response**: Update UI with matched listings, statistics
6. **Save**: POST/PATCH to `/rules` endpoint with complete rule payload
7. **Server-Side Validation**: Verify rule logic, save to database
8. **Version Creation**: Auto-generate version entry with snapshot
9. **Audit Log**: Record change in `valuation_rule_audit` table
10. **Response**: Return saved rule with new version number

---

## API Contract Enhancements

### New Endpoints

#### GET /api/entities/metadata
Returns metadata for condition builder field selection.

**Response:**
```json
{
  "entities": [
    {
      "key": "listing",
      "label": "Listing",
      "fields": [
        {
          "key": "condition",
          "label": "Condition",
          "data_type": "enum",
          "options": ["new", "refurb", "used"]
        },
        {
          "key": "price_usd",
          "label": "Price (USD)",
          "data_type": "number",
          "validation": {"min": 0, "max": 99999}
        }
      ]
    },
    {
      "key": "cpu",
      "label": "CPU",
      "fields": [
        {
          "key": "cpu_mark_multi",
          "label": "CPU Mark (Multi-Core)",
          "data_type": "number",
          "description": "PassMark multi-core benchmark score"
        }
      ]
    }
  ]
}
```

#### POST /api/rules/preview
Evaluates rule against sample listings without saving.

**Request:**
```json
{
  "conditions": [/* condition objects */],
  "actions": [/* action objects */],
  "sample_listing_ids": [123, 456, 789],
  "sample_size": 10
}
```

**Response:**
```json
{
  "statistics": {
    "total_listings": 1247,
    "matched_count": 87,
    "avg_adjustment": -42.50,
    "min_adjustment": -150.00,
    "max_adjustment": 0.00
  },
  "sample_matched": [
    {
      "id": 123,
      "title": "Dell OptiPlex 7070",
      "original_price": 599.99,
      "adjusted_price": 549.99,
      "adjustment": -50.00,
      "condition_results": [
        {"condition": "cpu.cpu_mark_multi > 10000", "matched": true},
        {"condition": "listing.condition = new", "matched": true}
      ]
    }
  ],
  "sample_non_matched": [
    {
      "id": 456,
      "title": "HP EliteDesk 800 G3",
      "original_price": 399.99,
      "reason": "CPU Mark is 7500, requires >10000"
    }
  ]
}
```

#### GET /api/rules/{rule_id}/versions
Returns version history for a rule.

**Response:**
```json
{
  "rule_id": 42,
  "current_version": 5,
  "versions": [
    {
      "version_number": 5,
      "created_at": "2025-10-03T14:23:11Z",
      "changed_by": "user@example.com",
      "change_summary": "Increased CPU threshold from 15000 to 20000",
      "snapshot": {/* full rule state */}
    },
    {
      "version_number": 4,
      "created_at": "2025-10-02T09:15:44Z",
      "changed_by": "user@example.com",
      "change_summary": "Added GPU requirement",
      "snapshot": {/* full rule state */}
    }
  ]
}
```

#### POST /api/rules/{rule_id}/rollback
Restores a previous version (creates new version with old snapshot).

**Request:**
```json
{
  "target_version": 3,
  "reason": "Reverting problematic pricing logic"
}
```

**Response:**
```json
{
  "success": true,
  "new_version": 6,
  "restored_from": 3,
  "message": "Rule restored to version 3 as new version 6"
}
```

### Enhanced Existing Endpoints

#### POST /api/rules (existing, enhancements)
Add support for nested conditions via `parent_condition_id`.

**Request Enhancement:**
```json
{
  "group_id": 5,
  "name": "High-End Gaming Discount",
  "conditions": [
    {
      "field_name": "listing.condition",
      "operator": "equals",
      "value": "new",
      "logical_operator": "AND",
      "group_order": 0
    },
    {
      "field_name": "cpu.cpu_mark_multi",
      "operator": "greater_than",
      "value": 20000,
      "logical_operator": "AND",
      "group_order": 1
    },
    {
      "parent_condition_id": null,
      "logical_operator": "OR",
      "group_order": 2,
      "children": [
        {
          "field_name": "gpu.gpu_mark",
          "operator": "greater_than",
          "value": 10000,
          "logical_operator": "OR",
          "group_order": 0
        },
        {
          "field_name": "gpu.name",
          "operator": "contains",
          "value": "RTX 4",
          "logical_operator": "OR",
          "group_order": 1
        }
      ]
    }
  ],
  "actions": [
    {
      "action_type": "fixed_value",
      "value_usd": -50.00,
      "modifiers": {
        "condition_multipliers": {
          "new": 1.0,
          "refurb": 0.75,
          "used": 0.6
        }
      }
    }
  ]
}
```

---

## Testing Strategy

### Unit Tests
- **Condition Parsing**: Verify nested conditions parse correctly
- **Operator Validation**: Ensure only valid operators for field types
- **Formula Evaluation**: Test custom formula expressions with edge cases
- **Version Diffing**: Confirm accurate change detection between versions

### Integration Tests
- **Rule Evaluation**: Test rule logic against known listing datasets
- **Preview Generation**: Verify statistics and sample selection accuracy
- **Version Rollback**: Ensure restored rules function identically to originals
- **Custom Field Integration**: Test conditions using custom fields

### E2E Tests
- **Complete Rule Creation Flow**: From opening modal to saving rule
- **Nested Condition Creation**: Build multi-level condition groups
- **Real-Time Preview**: Verify preview updates as conditions change
- **Version History Navigation**: View, compare, and restore versions

### Performance Tests
- **Rule Evaluation Benchmark**: 1000 listings against 50 rules in <30s
- **Preview Response Time**: <500ms for 10-listing sample
- **Concurrent Users**: 20 users creating rules simultaneously without degradation
- **Large Rule Sets**: 200+ rules in single ruleset without UI slowdown

---

## Rollout Plan

### Phase 1: Foundation (Week 1-2)
- Implement enhanced backend endpoints (`/preview`, `/versions`, `/metadata`)
- Build `ConditionBuilder` component with entity/field/operator selection
- Add basic real-time preview panel

### Phase 2: Advanced Logic (Week 3-4)
- Implement nested condition groups with drag-and-drop
- Add action configuration with condition multipliers
- Integrate custom field support via `FieldRegistry`

### Phase 3: Versioning (Week 5)
- Build version history UI component
- Implement version comparison and rollback
- Add audit logging for all rule changes

### Phase 4: Polish & Documentation (Week 6)
- Add contextual help and tooltips
- Create rule templates library
- Write user documentation and video tutorials
- Performance optimization and bug fixes

### Phase 5: User Testing & Iteration (Week 7)
- Beta testing with 3-5 users
- Collect feedback and iterate
- Fix critical issues, defer nice-to-haves

### Phase 6: Production Release (Week 8)
- Deploy to production
- Monitor usage and performance
- Provide user support and training

---

## Success Criteria

### MVP Launch (End of Phase 6)
- [ ] Users can create rules with 3+ nested conditions via UI
- [ ] Preview shows accurate before/after pricing for sample listings
- [ ] All field types have appropriate value inputs (dropdown for enums, etc.)
- [ ] Version history displays all past versions with change summaries
- [ ] Rollback functionality restores previous rule state
- [ ] No critical bugs or performance issues
- [ ] Documentation published and accessible

### 30-Day Post-Launch
- [ ] 80% of new rules created via enhanced builder
- [ ] Average rule complexity increased to 3+ conditions
- [ ] 90% reduction in invalid/broken rules
- [ ] User satisfaction score >4.0/5.0
- [ ] Zero data loss incidents
- [ ] <5 support tickets related to rule builder

### 90-Day Post-Launch
- [ ] 100% rule creation via builder (no manual DB edits)
- [ ] 50% reduction in rule creation time (measured via analytics)
- [ ] Version history accessed in 60% of rule editing sessions
- [ ] Template library has 10+ user-contributed rules
- [ ] Rule preview used in 90% of rule creation sessions

---

## Appendix

### A. Glossary

- **Entity**: Top-level data type (Listing, CPU, GPU, etc.)
- **Field**: Attribute of an entity (price_usd, cpu_mark_multi, etc.)
- **Condition**: Logical test (e.g., price_usd > 500)
- **Action**: Price adjustment or flag triggered by rule match
- **Ruleset**: Collection of rule groups with shared configuration
- **Rule Group**: Categorized collection of related rules
- **Version**: Snapshot of rule state at a point in time
- **Condition Multiplier**: Adjustment factor based on listing condition

### B. Field Type Reference

| Data Type | Valid Operators | Example Values |
|-----------|----------------|----------------|
| `string` | equals, not_equals, contains, starts_with, ends_with, in, not_in | "Dell OptiPlex", "RTX 4070" |
| `number` | equals, not_equals, gt, lt, gte, lte, between | 599.99, 16, 20000 |
| `boolean` | is, is_not | true, false |
| `enum` | equals, not_equals, in, not_in | "new", "refurb", "used" |
| `date` | before, after, between, within_last_days | "2025-01-15", 30 (days) |

### C. Action Type Reference

| Action Type | Parameters | Use Case |
|-------------|-----------|----------|
| `fixed_value` | value_usd | Flat discount/premium (e.g., -$50) |
| `per_unit` | value_usd, metric | Price per component unit (e.g., $5/GB RAM) |
| `percentage` | percentage | Percent of listing price (e.g., +10%) |
| `benchmark_based` | value_usd, unit_type | Price per performance metric (e.g., $0.02/CPU Mark) |
| `formula` | formula | Custom calculation (e.g., `ram_gb * 2.5 + storage_gb * 0.1`) |
| `flag` | tag | Non-price action, mark for review |

### D. References

- [Existing Architecture Documentation](../../architecture.md)
- [Custom Fields System Documentation](../technical/custom-fields.md)
- [Valuation Engine Design](../../packages/core/dealbrain_core/valuation.py)
- [Current Rule Builder UI](../../apps/web/components/valuation/rule-builder-modal.tsx)
