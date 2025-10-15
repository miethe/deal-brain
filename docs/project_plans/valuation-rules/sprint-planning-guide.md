# Valuation Rules System Enhancements - Sprint Planning Guide

**Project Duration:** 7 weeks (4 sprints)
**Total Effort:** 159 hours
**Team Composition:**
- Backend Engineer: 31 hours
- Frontend Engineer: 62 hours
- Full-Stack Engineer: 8 hours
- QA Engineer: 27 hours

**Last Updated:** 2025-10-15

---

## Table of Contents

1. [Sprint Overview](#sprint-overview)
2. [Story Point Estimation Guide](#story-point-estimation-guide)
3. [Sprint 1: Critical Bugs](#sprint-1-critical-bugs-weeks-1-2)
4. [Sprint 2: UX Improvements & Basic-to-Advanced Foundation](#sprint-2-ux-improvements--basic-to-advanced-foundation-weeks-2-3)
5. [Sprint 3: Action Multipliers Part 1](#sprint-3-action-multipliers-part-1-weeks-3-4)
6. [Sprint 4: Action Multipliers Part 2 & Formula Builder](#sprint-4-action-multipliers-part-2--formula-builder-weeks-5-7)
7. [Daily Standup Format](#daily-standup-format)
8. [Sprint Ceremonies](#sprint-ceremonies)
9. [Task Status Workflow](#task-status-workflow)
10. [Resource Allocation Strategy](#resource-allocation-strategy)
11. [Risk Management](#risk-management)

---

## Sprint Overview

### Sprint Structure

This project follows a **2-week sprint cadence** with overlapping development phases:

| Sprint | Duration | Focus Area | Priority |
|--------|----------|------------|----------|
| Sprint 1 | Weeks 1-2 | Critical bug fixes + Foundation | P0 |
| Sprint 2 | Weeks 2-3 | UX improvements + Hydration backend | P0/P1 |
| Sprint 3 | Weeks 3-4 | Action Multipliers (Backend + Frontend Phase 1) | P1 |
| Sprint 4 | Weeks 5-7 | Action Multipliers Phase 2 + Formula Builder | P2 |

### Key Milestones

- **End of Sprint 1:** All critical bugs resolved, valuation system stable
- **End of Sprint 2:** Basic-to-Advanced hydration backend complete, UX improvements shipped
- **End of Sprint 3:** Action Multipliers MVP functional (single multiplier type)
- **End of Sprint 4:** Full Action Multipliers system + Formula Builder launched

---

## Story Point Estimation Guide

### Fibonacci Scale

| Story Points | Effort | Duration | Complexity | Risk |
|--------------|--------|----------|------------|------|
| 1 | Trivial | 1-2 hours | Straightforward, no unknowns | None |
| 2 | Small | 2-4 hours | Minor unknowns, simple testing | Low |
| 3 | Medium | 4-8 hours | Some research needed, moderate testing | Low |
| 5 | Large | 1-2 days | Multiple components, integration needed | Medium |
| 8 | Very Large | 2-3 days | Cross-team dependencies, complex testing | Medium-High |
| 13 | Extra Large | 3-5 days | Architectural changes, extensive testing | High |
| 21 | Massive | 1-2 weeks | Should be broken down into smaller stories | Very High |

### Velocity Tracking

**Target Velocity per Sprint:**
- Sprint 1: 30-35 story points (foundation sprint, expect slower velocity)
- Sprint 2-4: 40-45 story points (team at full speed)

**Velocity Calculation:**
```
Completed Story Points / Sprint Duration = Sprint Velocity
Track cumulative velocity to predict remaining work
```

### Burndown Chart Structure

**X-Axis:** Sprint days (Day 1 through Day 10 for 2-week sprint)
**Y-Axis:** Remaining story points

**Ideal Line:** Linear decline from total points to 0
**Actual Line:** Track daily completed points

**Warning Indicators:**
- Actual line > 20% above ideal: Risk of incomplete sprint
- Flat line for 2+ days: Blockers present, needs intervention
- Steep drop in last 2 days: Quality risk, rushing work

---

## Sprint 1: Critical Bugs (Weeks 1-2)

### Sprint Goal

> "Resolve all critical valuation rule bugs to stabilize the system and establish a solid foundation for advanced features."

### User Stories

#### US-1.1: Fix Add RuleGroup Modal Issue (Critical)

**Priority:** P0 - Critical Bug
**Story Points:** 5
**Assignee:** Frontend Engineer

**Description:**
On the `/valuation-rules` page in Advanced mode, clicking "Add RuleGroup" button opens the RuleSet creation modal instead of the RuleGroup creation modal.

**Acceptance Criteria:**
- [ ] "Add RuleGroup" button opens correct RuleGroup creation modal
- [ ] Modal context is correctly set based on which button is clicked
- [ ] Modal state is properly reset between opens
- [ ] Works when RuleSet has 0 existing RuleGroups
- [ ] Works when RuleSet has 1+ existing RuleGroups

**Technical Details:**
- Files: `apps/web/app/valuation-rules/_components/advanced-mode.tsx`
- Likely issue: Modal state management or event handler wiring
- Check: `handleAddRuleGroup` vs `handleAddRuleSet` handlers

**Testing Requirements:**
- [ ] Unit test: Modal selection logic
- [ ] Integration test: Button click handlers
- [ ] Manual test: Create RuleGroup in empty RuleSet
- [ ] Manual test: Create RuleGroup in populated RuleSet

**Dependencies:** None

---

#### US-1.2: Fix RuleGroup Not Appearing After Creation (Critical)

**Priority:** P0 - Critical Bug
**Story Points:** 8
**Assignee:** Full-Stack Engineer

**Description:**
After creating a RuleGroup via "Add Group" button, the new RuleGroup is not displayed in the list. No errors appear in frontend or backend logs.

**Acceptance Criteria:**
- [ ] New RuleGroups appear immediately after creation
- [ ] RuleGroup list refreshes correctly
- [ ] Backend persists RuleGroup successfully
- [ ] Frontend cache is invalidated properly
- [ ] Error handling and logging improved for debugging

**Technical Investigation Tasks:**
1. [ ] Verify backend creates RuleGroup record (check database)
2. [ ] Verify API response includes new RuleGroup
3. [ ] Check React Query cache invalidation
4. [ ] Verify UI state update logic
5. [ ] Add debug logging at each step

**Technical Details:**
- Backend: `apps/api/dealbrain_api/services/valuation_rules.py`
- Frontend: `apps/web/app/valuation-rules/_components/advanced-mode.tsx`
- API: React Query mutation hooks
- Likely causes:
  - Cache not invalidating
  - Parent RuleSet ID not passed correctly
  - UI filtering out new RuleGroup

**Testing Requirements:**
- [ ] Backend unit test: RuleGroup creation service
- [ ] API integration test: POST `/api/v1/valuation/rulegroups`
- [ ] Frontend integration test: Create and verify RuleGroup appears
- [ ] End-to-end test: Full flow from button click to list update
- [ ] Add logging at: API endpoint, service layer, frontend mutation

**Dependencies:** None (can start immediately)

---

#### US-1.3: Fix Condition Builder Dropdown Scrolling (High)

**Priority:** P1 - High Bug
**Story Points:** 3
**Assignee:** Frontend Engineer

**Description:**
The Condition builder dropdown for field selection extends beyond the bottom of the screen when the field list is long. Users cannot scroll to see or select fields at the bottom of the list.

**Acceptance Criteria:**
- [ ] Dropdown is vertically scrollable when content exceeds viewport
- [ ] Dropdown has max-height constraint
- [ ] Scroll behavior is smooth and accessible
- [ ] Keyboard navigation works (arrow keys, enter, escape)
- [ ] Dropdown stays within viewport bounds

**Technical Details:**
- File: `apps/web/components/valuation/condition-builder.tsx`
- Component: Field selection dropdown (likely using Radix UI Select)
- Fix: Add `max-height` and `overflow-y: auto` to dropdown content
- Consider: Virtual scrolling if list is extremely long (50+ fields)

**Code Change Example:**
```tsx
<SelectContent className="max-h-[300px] overflow-y-auto">
  {fieldOptions.map(field => (
    <SelectItem key={field.value} value={field.value}>
      {field.label}
    </SelectItem>
  ))}
</SelectContent>
```

**Testing Requirements:**
- [ ] Visual test: Dropdown with 10 fields (should not scroll)
- [ ] Visual test: Dropdown with 30+ fields (should scroll)
- [ ] Accessibility test: Keyboard navigation
- [ ] Accessibility test: Screen reader announces scrollable region

**Dependencies:** None

---

#### US-1.4: Hide Foreign Key Rules in Advanced Mode (High)

**Priority:** P1 - High Bug
**Story Points:** 3
**Assignee:** Frontend Engineer

**Description:**
Foreign Key Rules (e.g., "RAM Spec", "Primary Storage Profile") are currently visible in Advanced mode but cannot be edited. These should be hidden as they serve no direct function in Advanced editing.

**Acceptance Criteria:**
- [ ] Foreign Key Rules are filtered from Advanced mode UI
- [ ] Rules with `is_foreign_key_rule: true` metadata are hidden
- [ ] Non-foreign-key rules display normally
- [ ] Optional: Add "Show System Rules" toggle for debugging
- [ ] No impact on rule execution or valuation calculations

**Technical Details:**
- Backend: Add `is_foreign_key_rule` flag to rule metadata (if not exists)
- Frontend: Filter rules before rendering in Advanced mode
- Files:
  - Backend: `apps/api/dealbrain_api/services/baseline_loader.py`
  - Frontend: `apps/web/app/valuation-rules/_components/advanced-mode.tsx`

**Implementation Steps:**
1. [ ] Identify all foreign key rules in baseline loader
2. [ ] Add `is_foreign_key_rule: true` to their `metadata_json`
3. [ ] Update API to include metadata in rule responses
4. [ ] Add filter in Advanced mode component
5. [ ] (Optional) Add "Show System Rules" toggle

**Testing Requirements:**
- [ ] Unit test: Foreign key rules have correct metadata
- [ ] Integration test: API returns metadata
- [ ] Frontend test: Filter logic works correctly
- [ ] Manual test: Verify RAM Spec and Storage Profile rules hidden
- [ ] Manual test: Toggle "Show System Rules" (if implemented)

**Dependencies:** None

---

### Sprint 1 Task Board

| Task ID | Task | Assignee | Status | Story Points | Day Started | Day Completed |
|---------|------|----------|--------|--------------|-------------|---------------|
| US-1.1 | Fix Add RuleGroup Modal | FE | To Do | 5 | | |
| US-1.2 | Fix RuleGroup Not Appearing | FS | To Do | 8 | | |
| US-1.3 | Fix Dropdown Scrolling | FE | To Do | 3 | | |
| US-1.4 | Hide Foreign Key Rules | FE | To Do | 3 | | |
| **Total** | | | | **19** | | |

### Sprint 1 Definition of Done

**Story Level:**
- [ ] All acceptance criteria met
- [ ] Code reviewed and approved by 1+ team member
- [ ] Unit tests written and passing (90%+ coverage for new code)
- [ ] Integration tests passing
- [ ] No new console errors or warnings
- [ ] Documented in code comments
- [ ] QA tested and approved

**Sprint Level:**
- [ ] All P0 bugs resolved
- [ ] All P1 bugs resolved or moved to Sprint 2 with justification
- [ ] Demo completed and stakeholder approval received
- [ ] Retrospective completed with action items
- [ ] Sprint metrics recorded (velocity, burndown)

### Sprint 1 Testing Requirements

**QA Engineer Focus (8 hours):**
1. **Regression Testing (3 hours):**
   - Verify existing valuation calculations unchanged
   - Test all RuleSet/RuleGroup CRUD operations
   - Verify Basic mode still functional

2. **Bug Fix Verification (3 hours):**
   - Test each bug fix against acceptance criteria
   - Exploratory testing around fixed areas
   - Cross-browser testing (Chrome, Firefox, Safari)

3. **Documentation (2 hours):**
   - Update test cases
   - Document known issues (if any)
   - Create bug fix release notes

### Sprint 1 Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| US-1.2 root cause unclear | High | Medium | Allocate Full-Stack engineer (both BE/FE skills) |
| Bugs reveal deeper architecture issues | High | Low | Timebox investigation to 4 hours, then escalate |
| Testing discovers new critical bugs | Medium | Medium | Reserve 20% sprint capacity for new issues |

---

## Sprint 2: UX Improvements & Basic-to-Advanced Foundation (Weeks 2-3)

### Sprint Goal

> "Complete UX improvements for condition builder, implement backend hydration service for Basic-to-Advanced transition, and establish foundation for advanced features."

### User Stories

#### US-2.1: Baseline Rules Hydration Service (Critical)

**Priority:** P0 - Foundation Feature
**Story Points:** 13
**Assignee:** Backend Engineer

**Description:**
Implement the backend hydration service to convert placeholder baseline rules into fully executable Advanced mode rules with conditions and actions.

**Acceptance Criteria:**
- [ ] `BaselineHydrationService` created with core hydration methods
- [ ] Enum multiplier strategy implemented (creates 1 rule per enum value)
- [ ] Formula strategy implemented (creates single rule with formula action)
- [ ] Fixed value strategy implemented (creates single rule with fixed action)
- [ ] Hydration metadata tracked (`hydrated`, `hydration_source_rule_id`)
- [ ] Original placeholder rules marked as hydrated and deactivated
- [ ] Hydration is idempotent (can run multiple times safely)
- [ ] Service handles edge cases (missing metadata, invalid formulas)
- [ ] Comprehensive unit tests (95%+ coverage)

**Technical Details:**
- File: `apps/api/dealbrain_api/services/baseline_hydration.py`
- Dependencies: `valuation_rules.py`, `models/core.py`
- Database: No schema changes needed (use existing `metadata_json`)

**API Design:**
```python
class BaselineHydrationService:
    async def hydrate_ruleset_baseline_rules(
        self, session: AsyncSession, ruleset_id: int, actor: str = "system"
    ) -> HydrationResult:
        """Hydrate all placeholder baseline rules in a ruleset."""

    async def hydrate_single_rule(
        self, session: AsyncSession, rule_id: int, actor: str = "system"
    ) -> list[ValuationRuleV2]:
        """Hydrate a single placeholder rule (may return multiple expanded rules)."""

    def _hydrate_enum_multiplier_rule(
        self, rule: ValuationRuleV2, metadata: dict
    ) -> list[dict]:
        """Strategy for enum_multiplier field type."""

    def _hydrate_formula_rule(
        self, rule: ValuationRuleV2, metadata: dict
    ) -> list[dict]:
        """Strategy for formula field type."""

    def _hydrate_fixed_value_rule(
        self, rule: ValuationRuleV2, metadata: dict
    ) -> list[dict]:
        """Strategy for fixed field type."""
```

**Subtasks:**
1. [ ] Create service class structure (2 hours)
2. [ ] Implement enum multiplier strategy (4 hours)
3. [ ] Implement formula strategy (3 hours)
4. [ ] Implement fixed value strategy (2 hours)
5. [ ] Add metadata handling and tracking (2 hours)
6. [ ] Write unit tests (4 hours)
7. [ ] Write integration tests (3 hours)
8. [ ] Code review and refinement (2 hours)

**Testing Requirements:**
- [ ] Unit test: Each hydration strategy
- [ ] Unit test: Metadata tracking
- [ ] Unit test: Idempotency (run twice, same result)
- [ ] Unit test: Edge cases (missing metadata, null values)
- [ ] Integration test: Hydrate full ruleset
- [ ] Integration test: Verify expanded rules execute correctly
- [ ] Performance test: Hydrate ruleset with 50+ rules

**Dependencies:** None (uses existing models and schemas)

---

#### US-2.2: Hydration API Endpoints (High)

**Priority:** P1 - Foundation Feature
**Story Points:** 5
**Assignee:** Backend Engineer

**Description:**
Create REST API endpoints to trigger baseline rule hydration from the frontend.

**Acceptance Criteria:**
- [ ] `POST /api/v1/valuation/rulesets/{ruleset_id}/hydrate-baseline` endpoint created
- [ ] `POST /api/v1/valuation/rules/{rule_id}/hydrate` endpoint created
- [ ] Endpoints validate input parameters
- [ ] Endpoints return detailed hydration results
- [ ] Proper error handling and status codes
- [ ] OpenAPI documentation updated
- [ ] Integration tests cover happy path and error cases

**Technical Details:**
- File: `apps/api/dealbrain_api/api/valuation_rules.py`
- Auth: Requires authenticated user
- Rate limiting: Consider adding for expensive hydration operations

**Request/Response Schemas:**

```python
# POST /api/v1/valuation/rulesets/{ruleset_id}/hydrate-baseline
class HydrateBaselineRequest(BaseModel):
    actor: str = "system"  # Optional, defaults to current user

class HydrateBaselineResponse(BaseModel):
    status: str  # "success" | "partial" | "failed"
    ruleset_id: int
    hydrated_rule_count: int
    created_rule_count: int
    hydration_summary: list[HydrationRuleSummary]
    errors: list[str]  # Any non-fatal errors

class HydrationRuleSummary(BaseModel):
    original_rule_id: int
    field_name: str
    field_type: str
    expanded_rule_ids: list[int]
    status: str  # "success" | "skipped" | "error"
    error_message: str | None
```

**Subtasks:**
1. [ ] Create endpoint routes (1 hour)
2. [ ] Implement request/response schemas (1 hour)
3. [ ] Add validation and error handling (1 hour)
4. [ ] Write integration tests (1.5 hours)
5. [ ] Update OpenAPI docs (0.5 hours)

**Testing Requirements:**
- [ ] Integration test: Successful hydration
- [ ] Integration test: Hydrate non-existent ruleset (404)
- [ ] Integration test: Hydrate already-hydrated ruleset (idempotent)
- [ ] Integration test: Unauthorized access (401)
- [ ] Load test: Concurrent hydration requests

**Dependencies:** US-2.1 (Hydration Service)

---

#### US-2.3: Condition Builder Dropdown Value Selection (High)

**Priority:** P1 - UX Improvement
**Story Points:** 5
**Assignee:** Frontend Engineer

**Description:**
Enhance the Condition builder's value field to support dropdown selection from existing field values (for enum fields) in addition to free text entry.

**Acceptance Criteria:**
- [ ] Value field detects if selected field is an enum type
- [ ] For enum fields, shows dropdown with existing values
- [ ] Dropdown allows selecting multiple existing values
- [ ] Dropdown allows adding new custom values inline
- [ ] For non-enum fields, shows free text input as before
- [ ] Selected values are validated against field type
- [ ] UI clearly indicates whether field is enum or free-form

**Technical Details:**
- File: `apps/web/components/valuation/condition-builder.tsx`
- Need: API endpoint to fetch distinct values for a field
- UI Component: Combobox (searchable dropdown) or Multi-select

**Implementation Approach:**

1. **Detect Field Type:**
```typescript
const fieldMetadata = useFieldMetadata(selectedField);
const isEnumField = fieldMetadata?.type === 'enum' || fieldMetadata?.has_options;
```

2. **Fetch Existing Values:**
```typescript
const { data: fieldValues } = useQuery({
  queryKey: ['field-values', selectedField],
  queryFn: () => api.get(`/fields/${selectedField}/distinct-values`),
  enabled: isEnumField
});
```

3. **Render Appropriate Input:**
```tsx
{isEnumField ? (
  <Combobox
    options={fieldValues}
    allowCustomValue={true}
    onValueChange={handleValueChange}
  />
) : (
  <Input
    type="text"
    value={value}
    onChange={handleValueChange}
  />
)}
```

**Backend Support Needed:**
- [ ] New endpoint: `GET /api/v1/fields/{field_name}/distinct-values`
- [ ] Endpoint returns list of unique values for that field across all entities
- [ ] Cache results for performance (Redis, 5-minute TTL)

**Subtasks:**
1. [ ] Backend: Create distinct values endpoint (2 hours) - Backend Engineer
2. [ ] Frontend: Field type detection logic (1 hour)
3. [ ] Frontend: Combobox component integration (1.5 hours)
4. [ ] Frontend: Handle custom value input (0.5 hours)
5. [ ] Testing: Unit and integration tests (1 hour)

**Testing Requirements:**
- [ ] Backend test: Distinct values endpoint returns correct data
- [ ] Frontend test: Enum field shows dropdown
- [ ] Frontend test: Non-enum field shows text input
- [ ] Frontend test: Can select existing value
- [ ] Frontend test: Can add custom value
- [ ] Manual test: Verify with DDR Generation field (enum)
- [ ] Manual test: Verify with CPU Model field (free-form)

**Dependencies:** None

---

#### US-2.4: Frontend Hydration Detection & Banner (High)

**Priority:** P1 - UX Feature
**Story Points:** 5
**Assignee:** Frontend Engineer

**Description:**
Detect placeholder baseline rules in Advanced mode and display a banner prompting users to hydrate rules for editing.

**Acceptance Criteria:**
- [ ] Advanced mode detects if any rules have `baseline_placeholder: true`
- [ ] Banner appears at top of Advanced mode when placeholders detected
- [ ] Banner explains what hydration does and why it's needed
- [ ] "Prepare for Advanced Editing" button triggers hydration
- [ ] Progress indicator shows during hydration
- [ ] Success message displays hydration results
- [ ] Error handling if hydration fails
- [ ] Banner dismisses after successful hydration
- [ ] Advanced mode refreshes to show hydrated rules

**Technical Details:**
- File: `apps/web/app/valuation-rules/_components/advanced-mode.tsx`
- UI Component: Alert banner with call-to-action button
- State: Track hydration progress (idle → loading → success → error)

**UI Design:**

```tsx
{hasPlaceholderRules && !isHydrated && (
  <Alert variant="info" className="mb-4">
    <InfoIcon className="h-4 w-4" />
    <AlertTitle>Baseline Rules Need Preparation</AlertTitle>
    <AlertDescription>
      To edit baseline rules in Advanced mode, they need to be converted
      into detailed rule structures. This one-time process will expand
      placeholder rules into fully editable conditions and actions.
    </AlertDescription>
    <Button
      onClick={handleHydrate}
      disabled={isHydrating}
      className="mt-2"
    >
      {isHydrating ? "Preparing Rules..." : "Prepare for Advanced Editing"}
    </Button>
  </Alert>
)}
```

**Hydration Flow:**
```typescript
const hydrateMutation = useMutation({
  mutationFn: (rulesetId: number) =>
    api.post(`/valuation/rulesets/${rulesetId}/hydrate-baseline`),
  onSuccess: (result) => {
    toast.success(`Hydrated ${result.created_rule_count} rules`);
    queryClient.invalidateQueries(['valuation-rules', rulesetId]);
  },
  onError: (error) => {
    toast.error(`Hydration failed: ${error.message}`);
  }
});
```

**Subtasks:**
1. [ ] Add placeholder detection logic (1 hour)
2. [ ] Create banner component (1 hour)
3. [ ] Implement hydration mutation (1.5 hours)
4. [ ] Add progress and error states (1 hour)
5. [ ] Write tests (0.5 hours)

**Testing Requirements:**
- [ ] Unit test: Placeholder detection logic
- [ ] Integration test: Banner appears when placeholders exist
- [ ] Integration test: Banner hidden after hydration
- [ ] Integration test: Hydration mutation success path
- [ ] Integration test: Hydration mutation error handling
- [ ] Manual test: Full user flow from banner to hydrated rules

**Dependencies:** US-2.2 (Hydration API Endpoints)

---

### Sprint 2 Task Board

| Task ID | Task | Assignee | Status | Story Points | Day Started | Day Completed |
|---------|------|----------|--------|--------------|-------------|---------------|
| US-2.1 | Baseline Hydration Service | BE | To Do | 13 | | |
| US-2.2 | Hydration API Endpoints | BE | To Do | 5 | | |
| US-2.3 | Dropdown Value Selection | FE | To Do | 5 | | |
| US-2.4 | Hydration Detection Banner | FE | To Do | 5 | | |
| **Total** | | | | **28** | | |

### Sprint 2 Definition of Done

**Story Level:**
- [ ] All acceptance criteria met
- [ ] Backend: 95%+ test coverage for hydration service
- [ ] Frontend: Unit tests for new components
- [ ] Integration tests passing for hydration flow
- [ ] Code reviewed and approved
- [ ] QA tested and approved
- [ ] Performance validated (hydration < 5 seconds for typical ruleset)
- [ ] Documentation updated (API docs, user guide)

**Sprint Level:**
- [ ] Backend hydration service complete and tested
- [ ] Frontend can trigger and display hydration results
- [ ] End-to-end flow works: detect → prompt → hydrate → display
- [ ] No regressions in existing functionality
- [ ] Demo completed with stakeholder approval
- [ ] Retrospective completed

### Sprint 2 Testing Requirements

**QA Engineer Focus (7 hours):**

1. **Hydration Service Testing (3 hours):**
   - Test enum multiplier hydration (DDR Generation)
   - Test formula hydration (RAM Capacity formula)
   - Test fixed value hydration
   - Verify expanded rules execute correctly
   - Test idempotency (run hydration twice)

2. **User Flow Testing (2 hours):**
   - Test full Basic → Advanced transition
   - Verify banner appears correctly
   - Test hydration button and progress indicator
   - Verify hydrated rules display properly

3. **UX Testing (1 hour):**
   - Test dropdown value selection
   - Verify custom value input works
   - Test keyboard navigation

4. **Regression Testing (1 hour):**
   - Verify existing valuation calculations unchanged
   - Test Basic mode functionality
   - Verify Sprint 1 bug fixes still working

### Sprint 2 Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Hydration creates too many rules (performance) | High | Medium | Batch creation, add pagination to UI |
| Formula parsing fails for complex formulas | High | Medium | Add validation, detailed error messages |
| Frontend/backend schema mismatch | Medium | Low | Define clear API contract upfront |
| Hydration reveals valuation calculation bugs | High | Low | Extensive testing, compare before/after |

### Sprint 2 Success Metrics

- [ ] 95%+ test coverage for hydration service
- [ ] Hydration completes in < 5 seconds for ruleset with 30 rules
- [ ] Zero valuation calculation changes before/after hydration
- [ ] User can successfully hydrate and edit rules in Advanced mode
- [ ] No P0 or P1 bugs discovered during testing

---

## Sprint 3: Action Multipliers Part 1 (Weeks 3-4)

### Sprint Goal

> "Implement the foundation for Action Multipliers system, enabling single multiplier attachment to actions with condition-based value adjustments."

### User Stories

#### US-3.1: Action Multipliers Data Model (Critical)

**Priority:** P0 - Foundation Feature
**Story Points:** 8
**Assignee:** Backend Engineer

**Description:**
Extend the data model to support Action Multipliers - a system where each action can have attached multipliers that adjust the action value based on specific conditions.

**Acceptance Criteria:**
- [ ] `ActionMultiplier` data structure added to action schema
- [ ] Each multiplier has: name, field, conditions (field values → multiplier value)
- [ ] Multipliers stored in `ValuationRuleV2.actions[].modifiers.multipliers`
- [ ] Database migration created (if schema changes needed)
- [ ] Validation ensures multiplier values are numeric
- [ ] Validation ensures conditions reference valid fields
- [ ] Backward compatible with existing actions (multipliers optional)

**Technical Details:**

**Data Structure:**
```python
class ActionMultiplier(BaseModel):
    name: str  # e.g., "RAM Generation Multiplier"
    field: str  # e.g., "ram_spec.ddr_generation"
    conditions: dict[str, float]  # e.g., {"ddr3": 0.7, "ddr4": 1.0, "ddr5": 1.3}

class RuleAction(BaseModel):
    action_type: str
    metric: str | None
    value_usd: float
    unit_type: str | None
    formula: str | None
    modifiers: dict
    multipliers: list[ActionMultiplier] = []  # NEW
```

**Storage:**
```json
{
  "action_type": "per_unit",
  "value_usd": 15.0,
  "metric": "total_capacity_gb",
  "multipliers": [
    {
      "name": "RAM Generation Multiplier",
      "field": "ram_spec.ddr_generation",
      "conditions": {
        "ddr3": 0.7,
        "ddr4": 1.0,
        "ddr5": 1.3
      }
    }
  ]
}
```

**Database Changes:**
- No schema migration needed (store in existing JSON columns)
- Consider adding index on `actions` JSONB column for performance

**Subtasks:**
1. [ ] Define Pydantic schemas for ActionMultiplier (2 hours)
2. [ ] Update RuleAction schema to include multipliers (1 hour)
3. [ ] Add validation logic (2 hours)
4. [ ] Update database migration (if needed) (1 hour)
5. [ ] Write unit tests for schemas (1 hour)
6. [ ] Code review (1 hour)

**Testing Requirements:**
- [ ] Unit test: ActionMultiplier schema validation
- [ ] Unit test: Invalid multiplier values rejected
- [ ] Unit test: Invalid field references rejected
- [ ] Unit test: Backward compatibility (actions without multipliers)
- [ ] Integration test: Save and load actions with multipliers

**Dependencies:** None

---

#### US-3.2: Multiplier Evaluation Engine (Critical)

**Priority:** P0 - Foundation Feature
**Story Points:** 13
**Assignee:** Backend Engineer

**Description:**
Implement the evaluation engine that applies action multipliers during valuation calculations. The engine must resolve multiplier conditions and adjust action values accordingly.

**Acceptance Criteria:**
- [ ] Evaluation engine resolves entity field values for multiplier conditions
- [ ] Engine applies correct multiplier based on matching condition
- [ ] Default multiplier (1.0) used if no condition matches
- [ ] Handles nested field references (e.g., `ram_spec.ddr_generation`)
- [ ] Multiple multipliers can be applied to single action (multiplicative)
- [ ] Engine handles missing fields gracefully
- [ ] Performance: < 10ms per action evaluation
- [ ] Comprehensive unit tests (95%+ coverage)

**Technical Details:**

**Evaluation Logic:**
```python
class ActionMultiplierEvaluator:
    def evaluate_action_with_multipliers(
        self,
        action: RuleAction,
        entity: Listing,  # or ListingComponent
        context: dict
    ) -> float:
        """
        Evaluate action value with multipliers applied.

        Returns: Adjusted value (base_value * multiplier1 * multiplier2 ...)
        """
        base_value = action.value_usd

        for multiplier in action.multipliers:
            field_value = self._resolve_field_value(entity, multiplier.field)
            multiplier_value = multiplier.conditions.get(field_value, 1.0)
            base_value *= multiplier_value

        return base_value

    def _resolve_field_value(self, entity: BaseModel, field_path: str) -> Any:
        """
        Resolve nested field value from entity.
        Example: "ram_spec.ddr_generation" → entity.ram_spec.ddr_generation
        """
        parts = field_path.split('.')
        value = entity
        for part in parts:
            value = getattr(value, part, None)
            if value is None:
                return None
        return value
```

**Integration with Valuation Engine:**
```python
# In valuation.py
def apply_rule_action(
    action: RuleAction,
    entity: Listing,
    context: dict
) -> float:
    # Existing logic...
    base_value = calculate_base_value(action, entity)

    # NEW: Apply multipliers if present
    if action.multipliers:
        evaluator = ActionMultiplierEvaluator()
        adjusted_value = evaluator.evaluate_action_with_multipliers(
            action, entity, context
        )
        return adjusted_value

    return base_value
```

**Subtasks:**
1. [ ] Create ActionMultiplierEvaluator class (3 hours)
2. [ ] Implement field resolution logic (2 hours)
3. [ ] Implement multiplier evaluation logic (2 hours)
4. [ ] Integrate with existing valuation engine (3 hours)
5. [ ] Write unit tests (2 hours)
6. [ ] Write integration tests (1 hour)

**Testing Requirements:**
- [ ] Unit test: Single multiplier evaluation
- [ ] Unit test: Multiple multipliers (multiplicative)
- [ ] Unit test: Missing field handling
- [ ] Unit test: No matching condition (default 1.0)
- [ ] Unit test: Nested field resolution
- [ ] Integration test: Full valuation with multipliers
- [ ] Integration test: Compare valuation with/without multipliers
- [ ] Performance test: 1000 evaluations < 10 seconds

**Dependencies:** US-3.1 (Action Multipliers Data Model)

---

#### US-3.3: Multiplier UI Components (High)

**Priority:** P1 - UI Feature
**Story Points:** 8
**Assignee:** Frontend Engineer

**Description:**
Create React components for adding, editing, and displaying action multipliers in the Rule Builder UI.

**Acceptance Criteria:**
- [ ] "Add Multiplier" button in action form
- [ ] Multiplier editor modal/panel with:
  - Multiplier name input
  - Field selector (dropdown of available fields)
  - Conditions editor (field value → multiplier value pairs)
  - Add/remove condition buttons
- [ ] Display existing multipliers in action card
- [ ] Edit and delete multiplier functionality
- [ ] Validation: Multiplier name required, at least 1 condition
- [ ] Validation: Multiplier values must be numeric
- [ ] Visual feedback for active multipliers

**Technical Details:**

**Component Structure:**
```
ActionForm
├── ActionTypeSelector
├── ValueInput
├── MultipliersList          ← NEW
│   ├── MultiplierCard
│   │   ├── MultiplierHeader (name, edit, delete)
│   │   └── ConditionsList
│   └── AddMultiplierButton
└── MultiplierEditorModal     ← NEW
    ├── NameInput
    ├── FieldSelector
    └── ConditionsEditor
        └── ConditionRow (field value → multiplier value)
```

**MultiplierEditorModal Component:**
```tsx
interface MultiplierEditorProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (multiplier: ActionMultiplier) => void;
  initialMultiplier?: ActionMultiplier;
}

function MultiplierEditor({ isOpen, onClose, onSave, initialMultiplier }: MultiplierEditorProps) {
  const [name, setName] = useState(initialMultiplier?.name ?? '');
  const [field, setField] = useState(initialMultiplier?.field ?? '');
  const [conditions, setConditions] = useState(initialMultiplier?.conditions ?? {});

  const handleAddCondition = () => {
    setConditions({ ...conditions, '': 1.0 });
  };

  const handleSave = () => {
    onSave({ name, field, conditions });
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {initialMultiplier ? 'Edit' : 'Add'} Action Multiplier
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label>Multiplier Name</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., RAM Generation Multiplier"
            />
          </div>

          <div>
            <Label>Field</Label>
            <FieldSelector value={field} onChange={setField} />
          </div>

          <div>
            <Label>Conditions</Label>
            {Object.entries(conditions).map(([fieldValue, multiplier]) => (
              <ConditionRow
                key={fieldValue}
                fieldValue={fieldValue}
                multiplier={multiplier}
                onChange={(newValue, newMultiplier) => {
                  const newConditions = { ...conditions };
                  delete newConditions[fieldValue];
                  newConditions[newValue] = newMultiplier;
                  setConditions(newConditions);
                }}
                onRemove={() => {
                  const newConditions = { ...conditions };
                  delete newConditions[fieldValue];
                  setConditions(newConditions);
                }}
              />
            ))}
            <Button onClick={handleAddCondition} variant="outline" size="sm">
              Add Condition
            </Button>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave}>Save Multiplier</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

**Subtasks:**
1. [ ] Create MultiplierCard component (2 hours)
2. [ ] Create MultiplierEditorModal component (3 hours)
3. [ ] Create ConditionRow component (1 hour)
4. [ ] Integrate with ActionForm (1 hour)
5. [ ] Add validation logic (0.5 hours)
6. [ ] Write component tests (0.5 hours)

**Testing Requirements:**
- [ ] Unit test: MultiplierCard renders correctly
- [ ] Unit test: MultiplierEditor validation
- [ ] Integration test: Add multiplier flow
- [ ] Integration test: Edit multiplier flow
- [ ] Integration test: Delete multiplier flow
- [ ] Manual test: Visual appearance and UX
- [ ] Accessibility test: Keyboard navigation

**Dependencies:** US-3.1 (Data Model)

---

#### US-3.4: Multiplier API Integration (High)

**Priority:** P1 - Integration Feature
**Story Points:** 5
**Assignee:** Frontend Engineer

**Description:**
Connect the Multiplier UI components to the backend API, enabling saving and loading of actions with multipliers.

**Acceptance Criteria:**
- [ ] Frontend sends multipliers in action payload to backend
- [ ] Frontend correctly parses multipliers from API responses
- [ ] TypeScript types match backend schemas
- [ ] React Query mutations handle multiplier updates
- [ ] Optimistic updates for better UX
- [ ] Error handling for invalid multiplier data
- [ ] Cache invalidation after multiplier changes

**Technical Details:**

**TypeScript Types:**
```typescript
// apps/web/types/valuation-rules.ts
export interface ActionMultiplier {
  name: string;
  field: string;
  conditions: Record<string, number>;
}

export interface RuleAction {
  action_type: string;
  metric?: string;
  value_usd: number;
  unit_type?: string;
  formula?: string;
  modifiers: Record<string, any>;
  multipliers?: ActionMultiplier[];  // NEW
}
```

**API Mutation:**
```typescript
const updateActionMutation = useMutation({
  mutationFn: async (payload: { ruleId: number; action: RuleAction }) => {
    return api.put(`/valuation/rules/${payload.ruleId}/actions`, {
      actions: [payload.action]
    });
  },
  onSuccess: () => {
    queryClient.invalidateQueries(['valuation-rules']);
    toast.success('Action multiplier saved');
  },
  onError: (error) => {
    toast.error(`Failed to save multiplier: ${error.message}`);
  }
});
```

**Subtasks:**
1. [ ] Define TypeScript types (1 hour)
2. [ ] Create API mutation hooks (1 hour)
3. [ ] Integrate with MultiplierEditor (1 hour)
4. [ ] Add error handling (1 hour)
5. [ ] Write integration tests (1 hour)

**Testing Requirements:**
- [ ] Integration test: Save action with multipliers
- [ ] Integration test: Load action with multipliers
- [ ] Integration test: Update existing multiplier
- [ ] Integration test: Delete multiplier
- [ ] Integration test: Error handling for invalid data

**Dependencies:** US-3.2 (Multiplier Evaluation Engine), US-3.3 (Multiplier UI)

---

### Sprint 3 Task Board

| Task ID | Task | Assignee | Status | Story Points | Day Started | Day Completed |
|---------|------|----------|--------|--------------|-------------|---------------|
| US-3.1 | Action Multipliers Data Model | BE | To Do | 8 | | |
| US-3.2 | Multiplier Evaluation Engine | BE | To Do | 13 | | |
| US-3.3 | Multiplier UI Components | FE | To Do | 8 | | |
| US-3.4 | Multiplier API Integration | FE | To Do | 5 | | |
| **Total** | | | | **34** | | |

### Sprint 3 Definition of Done

**Story Level:**
- [ ] All acceptance criteria met
- [ ] Backend: 95%+ test coverage for evaluation engine
- [ ] Frontend: Unit tests for all new components
- [ ] Integration tests cover full multiplier flow
- [ ] Code reviewed and approved
- [ ] QA tested and approved
- [ ] Performance validated (< 10ms per evaluation)
- [ ] Documentation updated

**Sprint Level:**
- [ ] Users can add single multiplier to actions
- [ ] Multipliers correctly adjust valuation calculations
- [ ] UI is intuitive and accessible
- [ ] No regressions in existing functionality
- [ ] Demo completed with stakeholder approval

### Sprint 3 Testing Requirements

**QA Engineer Focus (7 hours):**

1. **Functional Testing (3 hours):**
   - Test adding multipliers to actions
   - Test editing multipliers
   - Test deleting multipliers
   - Verify valuation calculations with multipliers

2. **Edge Case Testing (2 hours):**
   - Test missing field references
   - Test no matching conditions
   - Test multiple multipliers on same action
   - Test very large/small multiplier values

3. **UX Testing (1 hour):**
   - Test multiplier editor workflow
   - Verify error messages are clear
   - Test keyboard navigation

4. **Regression Testing (1 hour):**
   - Verify actions without multipliers still work
   - Test existing valuation calculations
   - Verify Sprint 1 & 2 features still working

### Sprint 3 Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Multiplier evaluation performance issues | High | Low | Performance testing, optimization if needed |
| Complex nested field resolution fails | Medium | Medium | Extensive testing, clear error messages |
| UI too complex for users | Medium | Medium | User testing, iterate on design |
| Multiple multipliers cause unexpected results | High | Low | Clear documentation, examples, tests |

---

## Sprint 4: Action Multipliers Part 2 & Formula Builder (Weeks 5-7)

### Sprint Goal

> "Complete the Action Multipliers system with multiple multiplier support, and implement the Formula Builder UI for creating formula actions without syntax errors."

### User Stories

#### US-4.1: Multiple Multipliers per Action (High)

**Priority:** P1 - Feature Enhancement
**Story Points:** 8
**Assignee:** Backend Engineer + Frontend Engineer

**Description:**
Enable actions to have multiple multipliers that are applied multiplicatively. For example, a RAM action could have both "DDR Generation" and "Condition" multipliers.

**Acceptance Criteria:**
- [ ] Backend: Actions can have unlimited multipliers
- [ ] Backend: Multipliers applied in order defined
- [ ] Backend: Multiplicative combination (value * m1 * m2 * m3)
- [ ] Frontend: UI supports adding multiple multipliers
- [ ] Frontend: Multipliers displayed in list with reordering
- [ ] Validation: Prevent duplicate field multipliers (same field twice)
- [ ] Testing: Verify correct calculation with 2+ multipliers

**Technical Details:**

**Backend Changes:**
```python
# Already supported in Sprint 3 data model
# Just need to ensure evaluation handles multiple multipliers correctly

class ActionMultiplierEvaluator:
    def evaluate_action_with_multipliers(
        self,
        action: RuleAction,
        entity: Listing,
        context: dict
    ) -> float:
        base_value = action.value_usd
        applied_multipliers = []

        for multiplier in action.multipliers:
            field_value = self._resolve_field_value(entity, multiplier.field)
            multiplier_value = multiplier.conditions.get(field_value, 1.0)
            base_value *= multiplier_value
            applied_multipliers.append({
                'name': multiplier.name,
                'field': multiplier.field,
                'matched_value': field_value,
                'multiplier': multiplier_value
            })

        # Store for debugging/explanation
        context['applied_multipliers'] = applied_multipliers
        return base_value
```

**Frontend Changes:**
```tsx
// MultipliersList component supports drag-and-drop reordering
import { DndContext, closestCenter } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';

function MultipliersList({ multipliers, onReorder, onEdit, onDelete }) {
  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={multipliers} strategy={verticalListSortingStrategy}>
        {multipliers.map(multiplier => (
          <SortableMultiplierCard
            key={multiplier.id}
            multiplier={multiplier}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
      </SortableContext>
    </DndContext>
  );
}
```

**Subtasks:**
1. [ ] Backend: Verify multiple multiplier evaluation (2 hours)
2. [ ] Backend: Add validation for duplicate fields (1 hour)
3. [ ] Frontend: Add drag-and-drop reordering (2 hours)
4. [ ] Frontend: Add duplicate field validation (1 hour)
5. [ ] Testing: Multiple multiplier scenarios (2 hours)

**Testing Requirements:**
- [ ] Unit test: 2 multipliers applied correctly
- [ ] Unit test: 3+ multipliers applied correctly
- [ ] Unit test: Duplicate field validation
- [ ] Integration test: Reorder multipliers affects calculation
- [ ] Integration test: Full valuation with multiple multipliers

**Dependencies:** Sprint 3 (US-3.1 through US-3.4)

---

#### US-4.2: Multiplier Debugging & Explanation (High)

**Priority:** P1 - Feature Enhancement
**Story Points:** 5
**Assignee:** Frontend Engineer

**Description:**
Add UI elements to help users understand which multipliers were applied and how they affected the final valuation.

**Acceptance Criteria:**
- [ ] Valuation breakdown modal shows applied multipliers
- [ ] Shows: Multiplier name, matched field value, multiplier value
- [ ] Shows calculation steps (base * m1 * m2 = final)
- [ ] Highlights which multipliers matched vs used default
- [ ] Accessible and easy to understand for non-technical users

**Technical Details:**

**Backend: Return Applied Multipliers:**
```python
# In valuation breakdown response
{
  "rule_id": 42,
  "rule_name": "RAM Capacity Valuation",
  "base_value": 60.0,
  "applied_multipliers": [
    {
      "name": "DDR Generation Multiplier",
      "field": "ram_spec.ddr_generation",
      "matched_value": "ddr4",
      "multiplier": 1.0,
      "is_default": false
    },
    {
      "name": "Condition Multiplier",
      "field": "condition",
      "matched_value": "used_like_new",
      "multiplier": 0.95,
      "is_default": false
    }
  ],
  "final_value": 57.0,
  "calculation": "60.0 × 1.0 (DDR4) × 0.95 (Like New) = 57.0"
}
```

**Frontend: Multiplier Breakdown Component:**
```tsx
function MultiplierBreakdown({ baseValue, appliedMultipliers, finalValue }) {
  return (
    <div className="space-y-2">
      <div className="text-sm font-medium">Calculation Steps:</div>

      <div className="bg-gray-50 p-3 rounded space-y-1">
        <div className="flex justify-between">
          <span>Base Value:</span>
          <span className="font-mono">${baseValue.toFixed(2)}</span>
        </div>

        {appliedMultipliers.map((mult, idx) => (
          <div key={idx} className="flex justify-between text-sm">
            <span>
              × {mult.multiplier}
              <span className="text-gray-600 ml-1">
                ({mult.name}: {mult.matched_value})
              </span>
              {mult.is_default && (
                <Badge variant="outline" className="ml-1">default</Badge>
              )}
            </span>
          </div>
        ))}

        <Separator className="my-2" />

        <div className="flex justify-between font-semibold">
          <span>Final Value:</span>
          <span className="font-mono">${finalValue.toFixed(2)}</span>
        </div>
      </div>

      <div className="text-xs text-gray-600">
        {appliedMultipliers.length === 0
          ? "No multipliers applied"
          : `${appliedMultipliers.length} multiplier(s) applied`}
      </div>
    </div>
  );
}
```

**Subtasks:**
1. [ ] Backend: Include applied multipliers in breakdown (2 hours)
2. [ ] Frontend: Create MultiplierBreakdown component (2 hours)
3. [ ] Frontend: Integrate with valuation modal (0.5 hours)
4. [ ] Testing: Verify breakdown accuracy (0.5 hours)

**Testing Requirements:**
- [ ] Integration test: Breakdown includes multipliers
- [ ] Unit test: MultiplierBreakdown renders correctly
- [ ] Manual test: Verify calculation steps are accurate
- [ ] Accessibility test: Screen reader announces calculation

**Dependencies:** US-4.1 (Multiple Multipliers)

---

#### US-4.3: Formula Builder UI - Phase 1 (Critical)

**Priority:** P0 - Major Feature
**Story Points:** 13
**Assignee:** Frontend Engineer

**Description:**
Create a visual Formula Builder UI that allows users to construct formula actions without writing text formulas, reducing syntax errors.

**Acceptance Criteria:**
- [ ] Formula Builder component with drag-and-drop interface
- [ ] Supports basic operations: +, -, *, /, ()
- [ ] Field selector to add entity fields to formula
- [ ] Constant value input
- [ ] Real-time formula preview (text representation)
- [ ] Validation: Ensures formula is syntactically correct
- [ ] Integration with action form (replaces text input for formulas)

**Technical Details:**

**Formula Builder Architecture:**

```
FormulaBuilder
├── FormulaCanvas             ← Drag-and-drop workspace
│   ├── FormulaNode           ← Field, constant, or operation
│   │   ├── FieldNode
│   │   ├── ConstantNode
│   │   └── OperationNode
│   └── ConnectionLine        ← Visual connections between nodes
├── ComponentPalette          ← Draggable components
│   ├── FieldList
│   ├── OperationList
│   └── ConstantInput
└── FormulaPreview            ← Text representation
```

**Formula Representation:**
```typescript
// Abstract Syntax Tree (AST) representation
interface FormulaNode {
  id: string;
  type: 'field' | 'constant' | 'operation';
}

interface FieldNode extends FormulaNode {
  type: 'field';
  field: string;  // e.g., 'ram_capacity_gb'
}

interface ConstantNode extends FormulaNode {
  type: 'constant';
  value: number;
}

interface OperationNode extends FormulaNode {
  type: 'operation';
  operator: '+' | '-' | '*' | '/';
  left: FormulaNode;
  right: FormulaNode;
}

// Example: ram_capacity_gb * 5.2
const exampleFormula: OperationNode = {
  id: '1',
  type: 'operation',
  operator: '*',
  left: { id: '2', type: 'field', field: 'ram_capacity_gb' },
  right: { id: '3', type: 'constant', value: 5.2 }
};
```

**Formula Generator:**
```typescript
class FormulaGenerator {
  generateText(node: FormulaNode): string {
    if (node.type === 'field') {
      return node.field;
    } else if (node.type === 'constant') {
      return node.value.toString();
    } else if (node.type === 'operation') {
      const left = this.generateText(node.left);
      const right = this.generateText(node.right);
      return `(${left} ${node.operator} ${right})`;
    }
  }

  validate(node: FormulaNode): { valid: boolean; errors: string[] } {
    // Validate structure, field references, etc.
  }
}
```

**UI Component (Simplified):**
```tsx
function FormulaBuilder({ initialFormula, onFormulaChange }) {
  const [ast, setAst] = useState<FormulaNode>(initialFormula);
  const [formulaText, setFormulaText] = useState('');

  useEffect(() => {
    const generator = new FormulaGenerator();
    const text = generator.generateText(ast);
    setFormulaText(text);
    onFormulaChange(text);
  }, [ast]);

  return (
    <div className="space-y-4">
      <div className="border rounded p-4">
        <h3 className="text-sm font-medium mb-2">Formula Canvas</h3>
        <FormulaCanvas ast={ast} onAstChange={setAst} />
      </div>

      <ComponentPalette />

      <div className="bg-gray-50 p-3 rounded">
        <h3 className="text-sm font-medium mb-1">Formula Preview</h3>
        <code className="text-sm">{formulaText || 'Empty formula'}</code>
      </div>
    </div>
  );
}
```

**Subtasks:**
1. [ ] Design formula AST structure (2 hours)
2. [ ] Create FormulaCanvas component (4 hours)
3. [ ] Create ComponentPalette (2 hours)
4. [ ] Implement formula text generator (2 hours)
5. [ ] Add validation logic (2 hours)
6. [ ] Write component tests (1 hour)

**Testing Requirements:**
- [ ] Unit test: AST to text conversion
- [ ] Unit test: Validation logic
- [ ] Integration test: Build simple formula (a * b)
- [ ] Integration test: Build complex formula ((a + b) * c)
- [ ] Manual test: Drag-and-drop UX
- [ ] Accessibility test: Keyboard navigation

**Dependencies:** None (standalone feature)

**Note:** This is Phase 1 - basic operations only. Advanced features (functions, conditionals) can be added in future sprints.

---

#### US-4.4: Formula Builder Backend Integration (High)

**Priority:** P1 - Integration Feature
**Story Points:** 5
**Assignee:** Backend Engineer

**Description:**
Ensure the backend formula engine can parse and execute formulas generated by the Formula Builder UI.

**Acceptance Criteria:**
- [ ] Backend parses Formula Builder generated formulas
- [ ] Formulas execute correctly in valuation calculations
- [ ] Validation endpoint for real-time formula checking
- [ ] Error messages are user-friendly
- [ ] Performance: Formula evaluation < 10ms

**Technical Details:**

**Formula Validation Endpoint:**
```python
# POST /api/v1/valuation/formulas/validate
class FormulaValidationRequest(BaseModel):
    formula: str
    entity_type: str  # 'listing', 'listing_component', etc.

class FormulaValidationResponse(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str]
    estimated_complexity: str  # 'simple', 'moderate', 'complex'

@router.post('/formulas/validate')
async def validate_formula(request: FormulaValidationRequest):
    try:
        engine = FormulaEngine()
        result = engine.validate(request.formula, request.entity_type)
        return FormulaValidationResponse(
            valid=True,
            errors=[],
            warnings=result.warnings,
            estimated_complexity=result.complexity
        )
    except FormulaParseError as e:
        return FormulaValidationResponse(
            valid=False,
            errors=[str(e)],
            warnings=[],
            estimated_complexity='unknown'
        )
```

**Formula Engine Updates:**
```python
# packages/core/valuation/formula.py
class FormulaEngine:
    def validate(self, formula: str, entity_type: str) -> ValidationResult:
        """
        Validate formula syntax and field references.
        """
        # Parse formula
        ast = self._parse(formula)

        # Check field references are valid for entity type
        fields = self._extract_field_references(ast)
        schema = get_entity_schema(entity_type)
        invalid_fields = [f for f in fields if f not in schema]

        if invalid_fields:
            raise FormulaParseError(f"Invalid fields: {invalid_fields}")

        # Check for common issues
        warnings = []
        if self._has_division_by_zero_risk(ast):
            warnings.append("Formula may divide by zero")

        return ValidationResult(
            valid=True,
            warnings=warnings,
            complexity=self._calculate_complexity(ast)
        )
```

**Subtasks:**
1. [ ] Create validation endpoint (2 hours)
2. [ ] Update FormulaEngine with validation logic (2 hours)
3. [ ] Add error handling and user-friendly messages (0.5 hours)
4. [ ] Write tests (0.5 hours)

**Testing Requirements:**
- [ ] Unit test: Validate simple formula
- [ ] Unit test: Validate complex formula
- [ ] Unit test: Reject invalid formula
- [ ] Integration test: Validation endpoint
- [ ] Integration test: Execute formula in valuation

**Dependencies:** US-4.3 (Formula Builder UI)

---

#### US-4.5: Formula Builder Advanced Features (Optional)

**Priority:** P2 - Nice-to-Have
**Story Points:** 8
**Assignee:** Frontend Engineer

**Description:**
Add advanced features to Formula Builder: functions (min, max, abs), conditionals, and cohort guardrails.

**Acceptance Criteria:**
- [ ] Support for functions: min(), max(), abs(), round()
- [ ] Support for conditional expressions: if-then-else
- [ ] Cohort guardrails integration (percentile-based limits)
- [ ] Function documentation in UI
- [ ] Examples and templates

**Technical Details:**

**Extended AST:**
```typescript
interface FunctionNode extends FormulaNode {
  type: 'function';
  name: 'min' | 'max' | 'abs' | 'round';
  arguments: FormulaNode[];
}

interface ConditionalNode extends FormulaNode {
  type: 'conditional';
  condition: ConditionNode;
  thenBranch: FormulaNode;
  elseBranch: FormulaNode;
}
```

**UI Additions:**
- Function palette with drag-and-drop
- Conditional builder (similar to condition builder)
- Template library with common formulas

**Subtasks:**
1. [ ] Extend AST to support functions (2 hours)
2. [ ] Add function palette to UI (2 hours)
3. [ ] Implement conditional builder (2 hours)
4. [ ] Create template library (1 hour)
5. [ ] Write tests (1 hour)

**Testing Requirements:**
- [ ] Unit test: Function AST generation
- [ ] Unit test: Conditional AST generation
- [ ] Integration test: Formula with functions executes
- [ ] Integration test: Formula with conditionals executes

**Dependencies:** US-4.3, US-4.4

**Note:** This is optional and can be deferred to a future sprint if time is limited.

---

### Sprint 4 Task Board

| Task ID | Task | Assignee | Status | Story Points | Day Started | Day Completed |
|---------|------|----------|--------|--------------|-------------|---------------|
| US-4.1 | Multiple Multipliers per Action | BE + FE | To Do | 8 | | |
| US-4.2 | Multiplier Debugging & Explanation | FE | To Do | 5 | | |
| US-4.3 | Formula Builder UI - Phase 1 | FE | To Do | 13 | | |
| US-4.4 | Formula Builder Backend Integration | BE | To Do | 5 | | |
| US-4.5 | Formula Builder Advanced Features | FE | To Do | 8 | | |
| **Total** | | | | **39** | | |

**Note:** US-4.5 is optional and can be descoped if needed.

### Sprint 4 Definition of Done

**Story Level:**
- [ ] All acceptance criteria met
- [ ] Code reviewed and approved
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] QA tested and approved
- [ ] Documentation updated
- [ ] Performance validated

**Sprint Level:**
- [ ] Action Multipliers fully functional (single and multiple)
- [ ] Formula Builder usable for creating formula actions
- [ ] Valuation calculations correct with new features
- [ ] No regressions in existing functionality
- [ ] User documentation and examples created
- [ ] Demo completed with stakeholder approval

### Sprint 4 Testing Requirements

**QA Engineer Focus (12 hours):**

1. **Multiple Multipliers Testing (3 hours):**
   - Test 2, 3, 4+ multipliers per action
   - Verify multiplicative combination
   - Test reordering multipliers
   - Verify calculation accuracy

2. **Formula Builder Testing (4 hours):**
   - Test building simple formulas
   - Test building complex formulas
   - Test validation (valid and invalid)
   - Test formula execution in valuations
   - Verify error messages

3. **Integration Testing (2 hours):**
   - Test Action Multipliers + Formula Builder together
   - Test complete valuation flow with all features
   - Verify breakdown explanations

4. **Regression Testing (2 hours):**
   - Full regression suite (all previous features)
   - Performance testing (load time, calculation speed)
   - Cross-browser testing

5. **Documentation Testing (1 hour):**
   - Verify examples work correctly
   - Test user documentation accuracy
   - Create release notes

### Sprint 4 Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Formula Builder too complex for MVP | High | Medium | Start with simple operations, defer advanced features |
| Backend formula parsing doesn't match UI | High | Medium | Validate formulas in real-time, extensive testing |
| Performance issues with complex formulas | Medium | Low | Performance testing, optimization if needed |
| Users find Formula Builder confusing | Medium | Medium | User testing, iterate on UX, provide templates |

---

## Daily Standup Format

### Time & Duration
- **When:** Daily at 9:30 AM
- **Duration:** 15 minutes (strictly timeboxed)
- **Format:** Round-robin (each person speaks in turn)

### 3 Questions per Team Member

1. **What did I complete yesterday?**
   - List completed tasks/stories
   - Reference task IDs from sprint board

2. **What will I work on today?**
   - List planned tasks/stories
   - Mention any dependencies

3. **Any blockers or concerns?**
   - Technical blockers
   - Waiting on others
   - Need clarification
   - Scope creep concerns

### Standup Template

```markdown
## Daily Standup - [Date]

### [Team Member Name] - [Role]
**Yesterday:**
- ✅ [Task ID] [Task name] - Status
- ✅ [Task ID] [Task name] - Status

**Today:**
- 🚧 [Task ID] [Task name]
- 📝 [Task ID] [Task name]

**Blockers:**
- 🚫 [Blocker description] - [Who can help]
- None

---

### [Next Team Member]
...
```

### Example Standup

```markdown
## Daily Standup - 2025-10-16

### Alice Chen - Frontend Engineer
**Yesterday:**
- ✅ US-1.1 Fixed Add RuleGroup modal issue
- ✅ Started US-1.3 dropdown scrolling fix

**Today:**
- 🚧 US-1.3 Complete dropdown scrolling fix
- 📝 US-1.4 Hide foreign key rules

**Blockers:**
- None

---

### Bob Martinez - Backend Engineer
**Yesterday:**
- ✅ US-2.1 Created BaselineHydrationService structure
- ✅ US-2.1 Implemented enum multiplier strategy

**Today:**
- 🚧 US-2.1 Implement formula strategy
- 🚧 US-2.1 Write unit tests

**Blockers:**
- 🚫 Need clarification on formula validation logic - @ProductOwner

---

### Carol Wu - QA Engineer
**Yesterday:**
- ✅ Completed Sprint 1 regression testing
- ✅ Verified US-1.1 bug fix

**Today:**
- 🚧 Test US-1.3 and US-1.4 bug fixes
- 📝 Update test cases for Sprint 2

**Blockers:**
- None

---

### David Kim - Full-Stack Engineer
**Yesterday:**
- ✅ US-1.2 Root cause analysis completed
- ✅ US-1.2 Fixed cache invalidation issue

**Today:**
- 🚧 US-1.2 Write integration tests
- 🚧 US-1.2 Add debug logging

**Blockers:**
- None
```

### Parking Lot

If discussions exceed 15 minutes or go off-topic:
- Note the topic in "Parking Lot"
- Schedule separate meeting after standup
- Keep standup on track

**Parking Lot Topics:**
```markdown
- [Topic 1] - [Who needs to be involved] - [Urgency]
- Formula validation approach - BE, FE, PM - Schedule for today 2pm
```

---

## Sprint Ceremonies

### 1. Sprint Planning

**When:** First day of sprint
**Duration:** 2 hours (for 2-week sprint)
**Participants:** Entire team + Product Owner

**Agenda:**

1. **Review Sprint Goal (15 min)**
   - Product Owner presents sprint objective
   - Team discusses and aligns on priority

2. **Review User Stories (45 min)**
   - Product Owner presents each story
   - Team asks clarifying questions
   - Team estimates story points (Planning Poker)
   - Team identifies dependencies and risks

3. **Capacity Planning (15 min)**
   - Calculate team capacity (hours available)
   - Account for PTO, meetings, other commitments
   - Determine target velocity

4. **Task Breakdown (30 min)**
   - Break stories into technical tasks
   - Assign tasks to team members
   - Identify parallel vs sequential work

5. **Sprint Commitment (15 min)**
   - Team commits to sprint scope
   - Finalize sprint board
   - Discuss potential risks

**Outputs:**
- Sprint backlog populated
- Sprint goal documented
- Task assignments complete
- Initial sprint board snapshot

---

### 2. Daily Standup

**When:** Every day at 9:30 AM
**Duration:** 15 minutes
**Participants:** Entire team

**Format:** See [Daily Standup Format](#daily-standup-format) above

---

### 3. Sprint Review (Demo)

**When:** Last day of sprint (afternoon)
**Duration:** 1 hour
**Participants:** Team + Stakeholders + Product Owner

**Agenda:**

1. **Sprint Summary (5 min)**
   - Review sprint goal
   - Present completed vs planned work
   - Show velocity and burndown chart

2. **Demo (40 min)**
   - Demo each completed user story
   - Show working software (not slides)
   - Explain value delivered
   - Address stakeholder questions

3. **Feedback & Discussion (10 min)**
   - Stakeholder feedback on features
   - Discuss potential changes to backlog
   - Identify new requirements

4. **Next Sprint Preview (5 min)**
   - Preview upcoming sprint goal
   - Highlight key features planned

**Demo Script Template:**

```markdown
## Sprint [N] Review - [Date]

### Sprint Goal
> [Sprint goal statement]

### Metrics
- Planned story points: [X]
- Completed story points: [Y]
- Velocity: [Y] points
- Sprint completion: [Y/X * 100]%

### Completed User Stories

#### US-X.X: [Story Title]
**Demo:**
1. [Step 1 - show feature]
2. [Step 2 - show feature]
3. [Step 3 - show value]

**Value Delivered:**
- [Business value 1]
- [Business value 2]

---

[Repeat for each story]

### Upcoming: Sprint [N+1]
- [Preview key feature 1]
- [Preview key feature 2]
```

---

### 4. Sprint Retrospective

**When:** Last day of sprint (after review)
**Duration:** 1 hour
**Participants:** Entire team (no stakeholders)

**Agenda:**

1. **Set the Stage (5 min)**
   - Review retrospective purpose
   - Establish safe environment
   - Review previous action items

2. **Gather Data (15 min)**
   - Team members share observations
   - Use framework: What went well / What didn't / Ideas

3. **Generate Insights (20 min)**
   - Identify patterns and root causes
   - Discuss most impactful issues
   - Vote on top issues to address

4. **Decide Actions (15 min)**
   - Create specific, actionable items
   - Assign owners to each action
   - Set deadline for completion

5. **Close (5 min)**
   - Summarize action items
   - Appreciate team contributions

**Retrospective Template:**

```markdown
## Sprint [N] Retrospective - [Date]

### Previous Action Items Review
- [x] [Action 1] - Status: Complete / In Progress / Not Started
- [ ] [Action 2] - Status: ...

### What Went Well 🎉
- [Item 1]
- [Item 2]
- [Item 3]

### What Didn't Go Well 😞
- [Item 1]
- [Item 2]
- [Item 3]

### Ideas for Improvement 💡
- [Idea 1]
- [Idea 2]
- [Idea 3]

### Top Issues (by vote)
1. [Issue 1] - [X] votes
2. [Issue 2] - [Y] votes
3. [Issue 3] - [Z] votes

### Action Items for Next Sprint
1. **[Action 1]**
   - Owner: [Name]
   - Deadline: [Date]
   - Success criteria: [How to measure]

2. **[Action 2]**
   - Owner: [Name]
   - Deadline: [Date]
   - Success criteria: [How to measure]

### Team Appreciation
- Shoutout to [Person] for [accomplishment]
- Great job by [Person] on [achievement]
```

**Retrospective Techniques:**

1. **Start-Stop-Continue**
   - Start: What should we start doing?
   - Stop: What should we stop doing?
   - Continue: What should we keep doing?

2. **4Ls**
   - Liked
   - Learned
   - Lacked
   - Longed for

3. **Sailboat**
   - Wind (helps us go faster)
   - Anchor (slows us down)
   - Rocks (potential risks)
   - Island (goal/vision)

---

### 5. Backlog Refinement (Mid-Sprint)

**When:** Middle of sprint (Day 5-6)
**Duration:** 1 hour
**Participants:** Team + Product Owner

**Purpose:**
- Refine upcoming sprint stories
- Break down large stories
- Estimate new stories
- Clarify acceptance criteria

**Agenda:**

1. **Review Next Sprint Stories (30 min)**
   - Product Owner presents stories
   - Team asks questions
   - Refine acceptance criteria

2. **Estimation (20 min)**
   - Estimate story points for new stories
   - Re-estimate stories if needed

3. **Dependencies (10 min)**
   - Identify cross-story dependencies
   - Discuss technical approach

---

## Task Status Workflow

### Status Definitions

| Status | Definition | Owner Actions |
|--------|------------|---------------|
| **To Do** | Story ready to be worked on, all info available | None |
| **In Progress** | Actively being worked on | Update daily, move to Review when done |
| **Review** | Code complete, awaiting review | Request review, address feedback |
| **Testing** | In QA testing | Fix bugs, provide info to QA |
| **Done** | All acceptance criteria met, tested, deployed | None |

### Status Transitions

```
To Do → In Progress → Review → Testing → Done
           ↓            ↓         ↓
        Blocked    Needs Info   Bug Found
           ↓            ↓         ↓
     [Resolve blocker] ↓    [Fix & retest]
           ↓            ↓         ↓
        In Progress ← ───────── ─┘
```

### Blocker Handling

**When a task is blocked:**

1. **Immediately notify team** (Slack, standup)
2. **Update task status** to "Blocked"
3. **Add blocker tag** with reason
4. **Assign owner** to resolve blocker
5. **Set deadline** for resolution
6. **Pick up different task** while blocked

**Blocker Template:**
```markdown
🚫 **BLOCKED**
- Reason: [Why blocked]
- Needs: [What's needed to unblock]
- Owner: [Who can help]
- Deadline: [When must be resolved]
```

### Definition of Done Checklist

**Code Level:**
- [ ] Code written and self-reviewed
- [ ] No commented-out code or debug statements
- [ ] No console errors or warnings
- [ ] Code follows style guide

**Testing Level:**
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] Manual testing completed
- [ ] Edge cases tested
- [ ] Accessibility tested (if UI)

**Review Level:**
- [ ] Code reviewed by 1+ team members
- [ ] Feedback addressed
- [ ] Approved by reviewer

**QA Level:**
- [ ] QA tested and approved
- [ ] Acceptance criteria verified
- [ ] No critical or high bugs
- [ ] Regression tests passing

**Documentation Level:**
- [ ] Code comments added where needed
- [ ] User documentation updated (if user-facing)
- [ ] API documentation updated (if API changes)
- [ ] Release notes drafted

---

## Resource Allocation Strategy

### Team Capacity

**Assumptions:**
- 8-hour workday
- 20% reserved for meetings, email, etc.
- 6.4 productive hours per day

**2-Week Sprint Capacity:**
- Per person: 10 days × 6.4 hours = 64 hours
- Team (4 people): 256 hours

### Role-Based Allocation

**Backend Engineer (31 hours total):**
- Sprint 1: 5 hours (bug fixes, foundation)
- Sprint 2: 18 hours (hydration service + API)
- Sprint 3: 21 hours (multiplier data model + engine)
- Sprint 4: 5 hours (formula backend integration)

**Frontend Engineer (62 hours total):**
- Sprint 1: 11 hours (bug fixes)
- Sprint 2: 10 hours (hydration UI + dropdown improvements)
- Sprint 3: 13 hours (multiplier UI + API integration)
- Sprint 4: 28 hours (formula builder + advanced features)

**Full-Stack Engineer (8 hours total):**
- Sprint 1: 8 hours (complex bug investigation)
- Sprint 2-4: Available for ad-hoc issues

**QA Engineer (27 hours total):**
- Sprint 1: 8 hours (bug verification + regression)
- Sprint 2: 7 hours (hydration testing)
- Sprint 3: 7 hours (multiplier testing)
- Sprint 4: 12 hours (formula builder + full regression)

### Parallel vs Sequential Work

**Sprint 1: Mostly Parallel**
```
FE: US-1.1 (Modal fix) ─────────┐
                                 ├─→ [All complete]
FE: US-1.3 (Dropdown) ──────────┤
                                 │
FS: US-1.2 (RuleGroup bug) ─────┤
                                 │
FE: US-1.4 (Hide FK rules) ─────┘
```

**Sprint 2: Mix of Parallel & Sequential**
```
BE: US-2.1 (Hydration service) ──→ US-2.2 (API endpoints) ──┐
                                                             ├→ Integration
FE: US-2.3 (Dropdown values) ────────────────────────────┐  │
                                                          ├──┤
FE: US-2.4 (Hydration banner) ←[wait for US-2.2]────────┘  │
                                                             │
                                    [All complete] ←─────────┘
```

**Sprint 3: Parallel Development**
```
BE: US-3.1 (Data model) ──→ US-3.2 (Evaluation engine) ──┐
                                                          ├→ Integration
FE: US-3.3 (Multiplier UI) ──→ US-3.4 (API integration) ─┘
```

**Sprint 4: Parallel + Optional Work**
```
BE+FE: US-4.1 (Multiple multipliers) ──┐
                                        ├→ Integration
FE: US-4.2 (Debugging UI) ──────────────┤
                                        │
FE: US-4.3 (Formula builder) ──→ US-4.4 (Backend) ──┤
                                                     │
FE: US-4.5 (Advanced features - OPTIONAL) ──────────┘
```

### Pair Programming Opportunities

**Recommended Pairing:**

1. **US-1.2: RuleGroup Bug** (Sprint 1)
   - Pair: Full-Stack + Frontend
   - Reason: Complex debugging across stack
   - Duration: 4 hours

2. **US-3.4: Multiplier API Integration** (Sprint 3)
   - Pair: Backend + Frontend
   - Reason: Ensure schema alignment
   - Duration: 2 hours

3. **US-4.1: Multiple Multipliers** (Sprint 4)
   - Pair: Backend + Frontend
   - Reason: Coordinate backend evaluation with UI
   - Duration: 3 hours

### Knowledge Transfer Plan

**Week 1-2 (Sprint 1):**
- Document valuation rule architecture
- Create developer onboarding guide
- Record video walkthrough of codebase

**Week 3-4 (Sprint 2-3):**
- Knowledge sharing sessions (1 hour/week)
- Topics: Hydration service, multiplier system
- Record sessions for future reference

**Week 5-7 (Sprint 4):**
- Formula builder architecture documentation
- Code walkthrough with full team
- Create troubleshooting guide

**Knowledge Transfer Sessions:**
```markdown
## Session 1: Valuation Rules Architecture (Week 1)
- Presenter: Backend Engineer
- Duration: 1 hour
- Topics:
  - RuleSet → RuleGroup → Rule hierarchy
  - Conditions and Actions structure
  - Valuation calculation flow
  - Database schema overview

## Session 2: Hydration Service Deep Dive (Week 3)
- Presenter: Backend Engineer
- Duration: 1 hour
- Topics:
  - Hydration strategies (enum, formula, fixed)
  - Metadata structure and usage
  - API integration
  - Testing approach

## Session 3: Action Multipliers System (Week 4)
- Presenter: Full-Stack Engineer
- Duration: 1 hour
- Topics:
  - Data model design
  - Evaluation engine logic
  - UI components architecture
  - End-to-end flow

## Session 4: Formula Builder Architecture (Week 6)
- Presenter: Frontend Engineer
- Duration: 1 hour
- Topics:
  - AST representation
  - Component structure
  - Formula generation
  - Validation approach
```

---

## Risk Management

### Risk Register

| Risk ID | Risk Description | Impact | Probability | Mitigation Strategy | Owner |
|---------|------------------|--------|-------------|---------------------|-------|
| R1 | Backend formula parsing fails for complex formulas | High | Medium | Extensive testing, real-time validation, detailed error messages | BE |
| R2 | Hydration creates too many rules (performance) | High | Medium | Batch creation, pagination, caching | BE |
| R3 | Users find Formula Builder too complex | Medium | Medium | User testing, templates, simplified MVP | FE |
| R4 | Sprint 1 bugs reveal deeper architecture issues | High | Low | Timebox investigation (4 hours), then escalate | FS |
| R5 | Multiplier evaluation performance issues | High | Low | Performance testing, optimization, caching | BE |
| R6 | Scope creep during sprints | Medium | High | Strict change control, defer to backlog | PM |
| R7 | Key team member unavailable (PTO, sick) | Medium | Medium | Cross-training, documentation, pairing | All |
| R8 | Integration issues between frontend/backend | Medium | Medium | Clear API contracts, integration tests | BE+FE |

### Risk Response Plans

#### R1: Formula Parsing Failures

**If risk occurs:**
1. Immediately add detailed logging to formula engine
2. Create fallback to safe default valuation
3. Display user-friendly error message with example
4. Schedule bug fix for next sprint if critical

**Prevention:**
- Implement real-time validation in UI
- Test with diverse formula examples
- Provide formula templates

---

#### R2: Rule Proliferation Performance

**If risk occurs:**
1. Implement pagination for rule lists (50 rules per page)
2. Add database indexes on frequently queried columns
3. Cache hydrated rule structures in Redis
4. Consider background job for large hydrations

**Prevention:**
- Performance test with 100+ rule rulesets
- Monitor database query times
- Set up alerts for slow queries

---

#### R6: Scope Creep

**Change Control Process:**

1. **New request received**
   - Log in "Parking Lot" document
   - Don't commit immediately

2. **Evaluate request**
   - Product Owner assesses priority
   - Team estimates effort
   - Compare to remaining capacity

3. **Decision matrix:**
   - **Critical bug:** Add immediately, descope something else
   - **High value, small effort:** Consider adding if capacity allows
   - **High value, large effort:** Defer to next sprint
   - **Low value:** Add to backlog for future consideration

4. **Communication**
   - Notify stakeholders of decision
   - Update sprint board if changes made
   - Document reasoning

---

### Issue Escalation Path

**Level 1: Team (0-4 hours)**
- Team attempts to resolve internally
- Use standups and Slack for coordination
- Try pairing or mob programming

**Level 2: Team Lead (4-24 hours)**
- Escalate to team lead or senior engineer
- Request technical guidance
- May need to adjust sprint scope

**Level 3: Product Owner (1-2 days)**
- Escalate if requires scope change
- Product Owner decides priorities
- May need stakeholder input

**Level 4: Management (2+ days)**
- Escalate if blocking entire sprint
- May need additional resources
- Consider extending timeline

---

## Agile Practices

### How to Handle Scope Changes

**During Sprint:**

1. **Receive Change Request**
   - Document: What, Why, Who requested
   - Tag as "Unplanned work"

2. **Quick Assessment**
   - Team estimates effort (< 30 minutes)
   - Product Owner assesses priority

3. **Decision Framework**

   **Add to current sprint IF:**
   - Critical bug (P0) affecting production
   - < 5 story points effort
   - Team has capacity (< 80% committed)
   - Aligns with sprint goal

   **Defer to next sprint IF:**
   - Nice-to-have enhancement
   - > 5 story points effort
   - Team at capacity
   - Doesn't align with sprint goal

4. **If adding to sprint:**
   - Remove equal story points from sprint
   - Get team agreement
   - Update sprint board
   - Notify stakeholders

5. **If deferring:**
   - Add to product backlog
   - Prioritize for next sprint planning
   - Communicate decision to requestor

---

### Bug Triage Process

**When bug reported:**

1. **Initial Triage (< 1 hour)**
   - Assign severity: Critical, High, Medium, Low
   - Assign priority: P0, P1, P2, P3
   - Determine if regression or new issue

2. **Severity Definitions**

   | Severity | Definition | Example |
   |----------|------------|---------|
   | Critical | System down, data loss, security breach | Database corruption, authentication broken |
   | High | Major feature broken, significant UX issue | Valuation calculations wrong, can't create rules |
   | Medium | Minor feature broken, workaround exists | UI glitch, tooltip wrong |
   | Low | Cosmetic issue, minimal impact | Typo, alignment off |

3. **Priority Assignment**

   | Priority | Timeline | Criteria |
   |----------|----------|----------|
   | P0 | Fix immediately (same day) | Critical severity, affects all users |
   | P1 | Fix this sprint | High severity, affects many users |
   | P2 | Fix next sprint | Medium severity, affects some users |
   | P3 | Fix when capacity allows | Low severity, minimal impact |

4. **Assignment**
   - P0/P1: Assign immediately to available engineer
   - P2/P3: Add to sprint backlog or product backlog

5. **Communication**
   - Notify affected users of bug status
   - Update stakeholders on P0/P1 bugs
   - Log in bug tracking system

---

### Code Review Expectations

**Review Timing:**
- Submit review request by 3 PM
- Reviewers respond within 4 hours (same day)
- If urgent, notify reviewer directly

**Review Checklist:**

**Functionality:**
- [ ] Code does what PR description says
- [ ] Edge cases handled
- [ ] Error handling present
- [ ] No obvious bugs

**Code Quality:**
- [ ] Follows style guide (Black, ESLint)
- [ ] Functions are small and focused
- [ ] Variable names are clear
- [ ] No unnecessary complexity

**Testing:**
- [ ] Tests cover new code
- [ ] Tests cover edge cases
- [ ] All tests passing
- [ ] Test names are descriptive

**Security:**
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevented
- [ ] XSS prevented (frontend)

**Performance:**
- [ ] No N+1 queries
- [ ] Appropriate indexes used
- [ ] Large datasets handled efficiently

**Documentation:**
- [ ] Complex logic explained
- [ ] API changes documented
- [ ] User-facing changes noted

**Review Sizes:**
- Target: < 400 lines changed
- Large PRs (> 400 lines): Break into smaller PRs or schedule walkthrough

**Review Tone:**
- Be kind and constructive
- Explain the "why" behind feedback
- Ask questions rather than demand changes
- Praise good solutions

---

### Documentation Requirements

**Code Documentation:**
- Docstrings for all public functions/classes
- Comments for complex logic
- Type hints for Python, TypeScript types for TS

**API Documentation:**
- OpenAPI/Swagger for all endpoints
- Request/response examples
- Error code descriptions

**User Documentation:**
- Feature guides for new functionality
- Screenshots or videos for complex UI
- FAQs for common questions

**Architecture Documentation:**
- ADRs for significant decisions
- System diagrams for new components
- Data flow diagrams

**Process Documentation:**
- Onboarding guide for new developers
- Deployment procedures
- Troubleshooting guides

---

## Progress Tracking

### Sprint Board Example

```markdown
## Sprint 1: Critical Bugs

### To Do (0 points)

### In Progress (13 points)
- [US-1.2] Fix RuleGroup Not Appearing - @david - Day 3
- [US-1.3] Fix Dropdown Scrolling - @alice - Day 2

### Review (5 points)
- [US-1.1] Fix Add RuleGroup Modal - @alice - Awaiting review from @bob

### Testing (0 points)

### Done (6 points)
- [US-1.4] Hide Foreign Key Rules - @alice - Completed Day 2

---

**Sprint Progress:**
- Completed: 6 / 19 points (32%)
- In Progress: 13 / 19 points (68%)
- Remaining: 0 / 19 points (0%)
- Days Elapsed: 3 / 10
- Days Remaining: 7

**Burndown:**
Day 1: 19 points remaining
Day 2: 16 points remaining
Day 3: 13 points remaining
Ideal: 16.3 points remaining ← **Ahead of schedule**
```

### Velocity Tracking

```markdown
## Project Velocity

| Sprint | Planned Points | Completed Points | Velocity | Team Notes |
|--------|----------------|------------------|----------|------------|
| Sprint 1 | 19 | TBD | TBD | Critical bugs |
| Sprint 2 | 28 | TBD | TBD | Hydration foundation |
| Sprint 3 | 34 | TBD | TBD | Multipliers MVP |
| Sprint 4 | 39 | TBD | TBD | Formula builder |

**Average Velocity:** TBD (calculate after Sprint 1)
**Predictability:** TBD (calculate after Sprint 2)
```

---

## Success Metrics per Sprint

### Sprint 1 Success Metrics

**Quantitative:**
- [ ] 4/4 critical bugs resolved
- [ ] 0 P0 bugs introduced
- [ ] 95%+ test coverage for bug fixes
- [ ] All tests passing
- [ ] Sprint velocity: 18-20 points (allowing for unknowns)

**Qualitative:**
- [ ] Stakeholder approval in sprint review
- [ ] QA sign-off on bug fixes
- [ ] No new critical issues discovered
- [ ] Team confidence in foundation for Sprint 2

**User Acceptance:**
- [ ] Users can create RuleGroups without errors
- [ ] Dropdown is scrollable and usable
- [ ] Foreign key rules no longer confusing in Advanced mode

---

### Sprint 2 Success Metrics

**Quantitative:**
- [ ] Hydration service: 95%+ test coverage
- [ ] Hydration completes < 5 seconds for 30-rule ruleset
- [ ] 0 valuation calculation changes after hydration
- [ ] Sprint velocity: 26-28 points

**Qualitative:**
- [ ] Backend hydration logic clear and maintainable
- [ ] Frontend hydration flow intuitive
- [ ] Team confident in architecture

**User Acceptance:**
- [ ] Users can switch Basic → Advanced without data loss
- [ ] Hydrated rules are editable and understandable
- [ ] Dropdown value selection improves UX

---

### Sprint 3 Success Metrics

**Quantitative:**
- [ ] Multiplier evaluation < 10ms per action
- [ ] 95%+ test coverage for multiplier system
- [ ] Users can create actions with multipliers
- [ ] Sprint velocity: 32-34 points

**Qualitative:**
- [ ] Multiplier UI intuitive and easy to use
- [ ] Multiplier calculations clearly explained
- [ ] Team confident in data model and engine

**User Acceptance:**
- [ ] Users can add multipliers to adjust valuations
- [ ] Multipliers correctly affect final valuations
- [ ] Breakdown modal clearly shows multiplier effects

---

### Sprint 4 Success Metrics

**Quantitative:**
- [ ] Formula builder generates syntactically correct formulas
- [ ] Formula evaluation < 10ms per formula
- [ ] Users can create formula actions without text input
- [ ] Sprint velocity: 31-39 points (lower if US-4.5 descoped)

**Qualitative:**
- [ ] Formula builder UX is intuitive
- [ ] Formula validation prevents errors
- [ ] Multiple multipliers work correctly together
- [ ] Complete system is production-ready

**User Acceptance:**
- [ ] Users can build formulas visually
- [ ] Formulas execute correctly in valuations
- [ ] Multiple multipliers provide needed flexibility
- [ ] System is reliable and performant

---

## Project Success Criteria

**At Project Completion:**

**Functional:**
- [ ] All 3 critical bugs resolved
- [ ] All 2 high-priority bugs resolved
- [ ] Basic-to-Advanced hydration functional
- [ ] Action Multipliers system functional
- [ ] Formula Builder functional (Phase 1 minimum)

**Quality:**
- [ ] 90%+ test coverage overall
- [ ] 0 P0 or P1 bugs in production
- [ ] Performance benchmarks met (< 5s hydration, < 10ms evaluation)
- [ ] Accessibility standards met (WCAG AA)

**Process:**
- [ ] All sprints completed on time
- [ ] Documentation complete and accurate
- [ ] Knowledge transfer completed
- [ ] Team retrospectives completed with action items

**User:**
- [ ] Stakeholder approval on all features
- [ ] User testing completed with positive feedback
- [ ] Production deployment successful
- [ ] User documentation published

---

## Adapting to Project Management Tools

This sprint planning guide can be adapted to various PM tools:

### Jira

**Sprint Board:**
- Use Jira's built-in Sprint board
- Story points → Jira estimate field
- Task status → Jira workflow states
- Burndown → Jira Reports → Burndown Chart

**Custom Fields:**
- Add "Acceptance Criteria" custom field
- Add "Testing Requirements" custom field
- Add "Dependencies" link field

**Automation:**
- Auto-transition to "Testing" when PR merged
- Auto-notify QA when task enters "Testing"
- Auto-create sub-tasks for common patterns

---

### Linear

**Sprint Views:**
- Create Cycle for each sprint
- Use Linear's built-in estimates
- Labels for: Critical, High, Frontend, Backend, QA
- Use Projects for cross-sprint features

**Automation:**
- Auto-assign to QA when "Ready for Testing"
- Auto-update status from GitHub PR status
- Auto-create Linear issues from Sentry errors

---

### GitHub Projects

**Project Board:**
- Columns: To Do, In Progress, Review, Testing, Done
- Use GitHub Issues for user stories
- Task lists within issues for subtasks
- Labels for story points, priority, role

**Automation:**
- Auto-move to "Review" when PR opened
- Auto-move to "Done" when PR merged
- Link issues to PRs automatically

---

## Conclusion

This sprint planning guide provides a comprehensive framework for managing the Valuation Rules System enhancements project. Key takeaways:

1. **Clear Structure:** 4 sprints with specific goals and deliverables
2. **Detailed Stories:** Each user story has acceptance criteria, technical details, and testing requirements
3. **Resource Management:** Clear allocation of backend, frontend, QA, and full-stack resources
4. **Risk Management:** Identified risks with mitigation strategies
5. **Agile Practices:** Defined ceremonies, workflows, and processes
6. **Flexibility:** Adaptable to different PM tools and team structures

**Next Steps:**
1. Review this guide with the team
2. Customize for your specific team needs
3. Set up your chosen PM tool
4. Begin Sprint 1 planning
5. Execute and iterate!

**Remember:** This is a living document. Update it based on team feedback and lessons learned during sprints.

---

## Appendix: Quick Reference

### Story Point Reference
- 1 point = 1-2 hours
- 2 points = 2-4 hours
- 3 points = 4-8 hours
- 5 points = 1-2 days
- 8 points = 2-3 days
- 13 points = 3-5 days

### Priority Definitions
- **P0:** Critical, fix immediately
- **P1:** High, fix this sprint
- **P2:** Medium, fix next sprint
- **P3:** Low, fix when capacity allows

### Status Workflow
To Do → In Progress → Review → Testing → Done

### Key Contacts
- Product Owner: [Name]
- Scrum Master: [Name]
- Backend Lead: [Name]
- Frontend Lead: [Name]
- QA Lead: [Name]

### Important Links
- Sprint Board: [URL]
- API Documentation: [URL]
- Design System: [URL]
- Test Cases: [URL]
- Slack Channel: #valuation-rules-project
