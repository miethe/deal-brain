# Basic to Advanced Mode Transition - Implementation Plan

**Date:** 2025-10-14
**Status:** Ready for Implementation
**Related:** PRD, ADR-0003
**Estimated Duration:** 5-6 days

## Overview

Implement baseline rule hydration to enable full editing of baseline rules in Advanced mode. This plan follows the hydration strategy defined in ADR-0003.

## Prerequisites

- ✅ Multiplier action bug fixed (value_usd: 0.0 handling)
- ✅ Duplicate dollar sign UI bug fixed
- ✅ PRD and ADR approved
- ⏳ Development environment running

## Phase 1: Backend - Hydration Service (2 days)

### Task 1.1: Create Hydration Service Foundation
**Location:** `apps/api/dealbrain_api/services/baseline_hydration.py`

**Implementation:**
```python
from dataclasses import dataclass
from typing import Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.core import ValuationRuleV2, ValuationRuleGroup
from .rules import RulesService

@dataclass
class HydrationResult:
    status: str
    ruleset_id: int
    hydrated_rule_count: int
    created_rule_count: int
    hydration_summary: list[dict[str, Any]]

class BaselineHydrationService:
    def __init__(self, rules_service: RulesService | None = None):
        self.rules_service = rules_service or RulesService()

    async def hydrate_baseline_rules(
        self,
        session: AsyncSession,
        ruleset_id: int,
        actor: str = "system"
    ) -> HydrationResult:
        """Hydrate all placeholder baseline rules in a ruleset."""
        # Implementation in Task 1.2

    async def hydrate_single_rule(
        self,
        session: AsyncSession,
        rule_id: int,
        actor: str = "system"
    ) -> list[ValuationRuleV2]:
        """Hydrate a single placeholder rule."""
        # Implementation in Task 1.3
```

**Acceptance Criteria:**
- [x] Service class created with proper typing
- [ ] Constructor initializes RulesService
- [ ] HydrationResult dataclass defined
- [ ] Method signatures match PRD specs

**Files:**
- Create: `apps/api/dealbrain_api/services/baseline_hydration.py`

---

### Task 1.2: Implement Ruleset-Level Hydration
**Location:** `BaselineHydrationService.hydrate_baseline_rules()`

**Implementation Steps:**
1. Query all rules in ruleset with `baseline_placeholder: true` in metadata
2. For each placeholder rule:
   - Call `hydrate_single_rule()`
   - Collect results
3. Deactivate original placeholder rules
4. Return HydrationResult with summary

**Code:**
```python
async def hydrate_baseline_rules(
    self,
    session: AsyncSession,
    ruleset_id: int,
    actor: str = "system"
) -> HydrationResult:
    # Find all placeholder rules
    stmt = select(ValuationRuleV2).join(ValuationRuleGroup).where(
        ValuationRuleGroup.ruleset_id == ruleset_id,
        ValuationRuleV2.metadata_json["baseline_placeholder"].as_boolean() == True
    )
    result = await session.execute(stmt)
    placeholder_rules = result.scalars().all()

    hydrated_count = 0
    created_count = 0
    summary = []

    for rule in placeholder_rules:
        # Skip if already hydrated
        if rule.metadata_json.get("hydrated"):
            continue

        # Hydrate single rule
        expanded_rules = await self.hydrate_single_rule(
            session, rule.id, actor=actor
        )

        # Mark original as hydrated
        rule.is_active = False
        rule.metadata_json = {
            **rule.metadata_json,
            "hydrated": True,
            "hydrated_at": datetime.utcnow().isoformat(),
            "hydrated_by": actor
        }

        hydrated_count += 1
        created_count += len(expanded_rules)

        summary.append({
            "original_rule_id": rule.id,
            "field_name": rule.name,
            "field_type": rule.metadata_json.get("field_type"),
            "expanded_rule_ids": [r.id for r in expanded_rules]
        })

    await session.commit()

    return HydrationResult(
        status="success",
        ruleset_id=ruleset_id,
        hydrated_rule_count=hydrated_count,
        created_rule_count=created_count,
        hydration_summary=summary
    )
```

**Acceptance Criteria:**
- [ ] Queries placeholder rules correctly
- [ ] Skips already-hydrated rules
- [ ] Calls hydrate_single_rule for each
- [ ] Marks originals as hydrated
- [ ] Returns complete summary

---

### Task 1.3: Implement Single Rule Hydration with Strategies
**Location:** `BaselineHydrationService.hydrate_single_rule()`

**Implementation Steps:**
1. Load rule and metadata
2. Determine field type from metadata
3. Route to appropriate strategy:
   - `_hydrate_enum_multiplier()` for enum fields
   - `_hydrate_formula()` for formula fields
   - `_hydrate_fixed()` for fixed fields
4. Return list of created rules

**Code:**
```python
async def hydrate_single_rule(
    self,
    session: AsyncSession,
    rule_id: int,
    actor: str = "system"
) -> list[ValuationRuleV2]:
    # Load rule
    stmt = select(ValuationRuleV2).where(ValuationRuleV2.id == rule_id)
    result = await session.execute(stmt)
    rule = result.scalar_one_or_none()

    if not rule:
        raise ValueError(f"Rule {rule_id} not found")

    if not rule.metadata_json.get("baseline_placeholder"):
        raise ValueError(f"Rule {rule_id} is not a baseline placeholder")

    # Determine field type
    field_type = rule.metadata_json.get("field_type", "fixed")

    # Route to strategy
    if field_type == "enum_multiplier":
        return await self._hydrate_enum_multiplier(session, rule, actor)
    elif field_type == "formula":
        return await self._hydrate_formula(session, rule, actor)
    else:  # fixed, additive, etc.
        return await self._hydrate_fixed(session, rule, actor)
```

**Acceptance Criteria:**
- [ ] Loads rule from database
- [ ] Validates placeholder status
- [ ] Routes to correct strategy
- [ ] Returns expanded rules

---

### Task 1.4: Implement Enum Multiplier Strategy
**Location:** `BaselineHydrationService._hydrate_enum_multiplier()`

**Implementation:**
```python
async def _hydrate_enum_multiplier(
    self,
    session: AsyncSession,
    rule: ValuationRuleV2,
    actor: str
) -> list[ValuationRuleV2]:
    """Create one rule per enum value with condition + multiplier action."""
    valuation_buckets = rule.metadata_json.get("valuation_buckets", {})
    field_path = rule.metadata_json.get("field_id")  # e.g., "ram_spec.ddr_generation"

    expanded_rules = []

    for enum_value, multiplier in valuation_buckets.items():
        # Create condition
        condition = {
            "field": field_path,
            "operator": "equals",
            "value": enum_value
        }

        # Create action (multiplier * 100 for percentage)
        action = {
            "action_type": "multiplier",
            "value_usd": float(multiplier) * 100.0,
            "modifiers": {
                "original_multiplier": multiplier
            }
        }

        # Create rule
        new_rule = await self.rules_service.create_rule(
            session=session,
            group_id=rule.group_id,
            name=f"{rule.name}: {enum_value}",
            description=f"{rule.description} - {enum_value}",
            priority=rule.priority,
            evaluation_order=rule.evaluation_order,
            conditions=[condition],
            actions=[action],
            created_by=actor,
            metadata={
                "hydration_source_rule_id": rule.id,
                "enum_value": enum_value,
                "field_type": "enum_multiplier"
            }
        )
        expanded_rules.append(new_rule)

    return expanded_rules
```

**Acceptance Criteria:**
- [ ] Creates one rule per enum value
- [ ] Conditions use correct field path and value
- [ ] Multipliers converted to percentage (×100)
- [ ] Original multiplier preserved in metadata
- [ ] Rules linked via hydration_source_rule_id

---

### Task 1.5: Implement Formula Strategy
**Location:** `BaselineHydrationService._hydrate_formula()`

**Implementation:**
```python
async def _hydrate_formula(
    self,
    session: AsyncSession,
    rule: ValuationRuleV2,
    actor: str
) -> list[ValuationRuleV2]:
    """Create single rule with formula action."""
    formula_text = rule.metadata_json.get("formula_text")

    if not formula_text:
        # No formula, return empty fixed rule
        return await self._hydrate_fixed(session, rule, actor)

    action = {
        "action_type": "formula",
        "formula": formula_text,
        "value_usd": None
    }

    new_rule = await self.rules_service.create_rule(
        session=session,
        group_id=rule.group_id,
        name=rule.name,
        description=rule.description,
        priority=rule.priority,
        evaluation_order=rule.evaluation_order,
        conditions=[],  # Always applies
        actions=[action],
        created_by=actor,
        metadata={
            "hydration_source_rule_id": rule.id,
            "field_type": "formula"
        }
    )

    return [new_rule]
```

**Acceptance Criteria:**
- [ ] Creates single rule with formula action
- [ ] Formula text copied from metadata
- [ ] No conditions (always applies)
- [ ] Metadata preserved

---

### Task 1.6: Implement Fixed Value Strategy
**Location:** `BaselineHydrationService._hydrate_fixed()`

**Implementation:**
```python
async def _hydrate_fixed(
    self,
    session: AsyncSession,
    rule: ValuationRuleV2,
    actor: str
) -> list[ValuationRuleV2]:
    """Create single rule with fixed value action."""
    # Extract value from metadata or use 0.0
    base_value = rule.metadata_json.get("default_value", 0.0)

    action = {
        "action_type": "fixed_value",
        "value_usd": float(base_value),
        "modifiers": {}
    }

    new_rule = await self.rules_service.create_rule(
        session=session,
        group_id=rule.group_id,
        name=rule.name,
        description=rule.description,
        priority=rule.priority,
        evaluation_order=rule.evaluation_order,
        conditions=[],
        actions=[action],
        created_by=actor,
        metadata={
            "hydration_source_rule_id": rule.id,
            "field_type": "fixed"
        }
    )

    return [new_rule]
```

**Acceptance Criteria:**
- [ ] Creates single rule with fixed action
- [ ] Value extracted from metadata
- [ ] Defaults to 0.0 if not specified

---

### Task 1.7: Write Unit Tests
**Location:** `tests/services/test_baseline_hydration.py`

**Test Cases:**
1. `test_hydrate_enum_multiplier_field()` - DDR Generation example
2. `test_hydrate_formula_field()` - RAM Capacity formula
3. `test_hydrate_fixed_field()` - Base depreciation
4. `test_hydrate_ruleset_all_types()` - Mixed field types
5. `test_skip_already_hydrated()` - Idempotency
6. `test_deactivate_original_rules()` - Placeholder deactivation
7. `test_foreign_key_rule_metadata()` - Mark foreign key rules
8. `test_hydration_summary()` - Return structure

**Coverage Target:** 95%+

**Acceptance Criteria:**
- [ ] All test cases passing
- [ ] Coverage >95%
- [ ] Edge cases covered (no buckets, empty formula, etc.)

---

## Phase 2: API Endpoints (1 day)

### Task 2.1: Create Hydration Endpoint
**Location:** `apps/api/dealbrain_api/api/baseline.py`

**Implementation:**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_async_session
from ..services.baseline_hydration import BaselineHydrationService, HydrationResult
from dealbrain_core.schemas.baseline import HydrateBaselineRequest, HydrateBaselineResponse

router = APIRouter(prefix="/baseline", tags=["baseline"])

@router.post("/rulesets/{ruleset_id}/hydrate", response_model=HydrateBaselineResponse)
async def hydrate_baseline_rules(
    ruleset_id: int,
    request: HydrateBaselineRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Hydrate placeholder baseline rules for Advanced mode editing."""
    service = BaselineHydrationService()

    try:
        result = await service.hydrate_baseline_rules(
            session=session,
            ruleset_id=ruleset_id,
            actor=request.actor or "system"
        )

        return HydrateBaselineResponse(
            status=result.status,
            ruleset_id=result.ruleset_id,
            hydrated_rule_count=result.hydrated_rule_count,
            created_rule_count=result.created_rule_count,
            hydration_summary=result.hydration_summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Schemas:**
```python
# In dealbrain_core/schemas/baseline.py

class HydrateBaselineRequest(BaseModel):
    actor: str | None = "system"

class HydrationSummaryItem(BaseModel):
    original_rule_id: int
    field_name: str
    field_type: str
    expanded_rule_ids: list[int]

class HydrateBaselineResponse(BaseModel):
    status: str
    ruleset_id: int
    hydrated_rule_count: int
    created_rule_count: int
    hydration_summary: list[HydrationSummaryItem]
```

**Acceptance Criteria:**
- [ ] Endpoint registered in router
- [ ] Request/response schemas defined
- [ ] Error handling implemented
- [ ] Returns proper HTTP status codes

---

### Task 2.2: Integration Tests
**Location:** `tests/test_baseline_hydration_api.py`

**Test Cases:**
1. `test_hydrate_endpoint_success()` - Full hydration flow
2. `test_hydrate_invalid_ruleset()` - 404 error
3. `test_hydrate_already_hydrated()` - Idempotency
4. `test_hydrate_response_structure()` - Schema validation

**Acceptance Criteria:**
- [ ] All API tests passing
- [ ] Status codes validated (200, 404, 500)
- [ ] Response structure matches schema

---

## Phase 3: Frontend Detection & UI (2 days)

### Task 3.1: Detect Placeholder Rules
**Location:** `apps/web/app/valuation-rules/page.tsx`

**Implementation:**
```typescript
// Add to page component
const { data: rules } = useQuery({
  queryKey: ["valuation-rules", rulesetId],
  queryFn: () => fetchRules(rulesetId)
});

const hasPlaceholderRules = useMemo(() => {
  return rules?.some(rule =>
    rule.metadata_json?.baseline_placeholder === true &&
    rule.metadata_json?.hydrated !== true
  );
}, [rules]);

const hasHydratedRules = useMemo(() => {
  return rules?.some(rule =>
    rule.metadata_json?.hydrated === true
  );
}, [rules]);
```

**Acceptance Criteria:**
- [ ] Detects placeholder rules via metadata
- [ ] Detects already-hydrated rules
- [ ] Memoized for performance

---

### Task 3.2: Create Hydration Banner Component
**Location:** `apps/web/app/valuation-rules/_components/hydration-banner.tsx`

**Implementation:**
```typescript
"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Info, Loader2 } from "lucide-react";

interface HydrationBannerProps {
  rulesetId: number;
  onHydrate: () => Promise<void>;
  isHydrating: boolean;
}

export function HydrationBanner({ rulesetId, onHydrate, isHydrating }: HydrationBannerProps) {
  return (
    <Alert className="mb-4">
      <Info className="h-4 w-4" />
      <AlertTitle>Baseline Rules Need Preparation</AlertTitle>
      <AlertDescription className="mt-2">
        <p className="mb-3">
          Baseline rules are currently in placeholder mode. To edit them in Advanced mode,
          they need to be converted to full rule structures.
        </p>
        <Button
          onClick={onHydrate}
          disabled={isHydrating}
          size="sm"
        >
          {isHydrating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isHydrating ? "Preparing Rules..." : "Prepare Baseline Rules for Editing"}
        </Button>
      </AlertDescription>
    </Alert>
  );
}
```

**Acceptance Criteria:**
- [ ] Shows when placeholder rules detected
- [ ] Button triggers hydration
- [ ] Loading state during hydration
- [ ] Dismisses after success

---

### Task 3.3: Implement Hydration Mutation
**Location:** `apps/web/lib/api/baseline.ts`

**Implementation:**
```typescript
export async function hydrateBaselineRules(
  rulesetId: number,
  actor: string = "system"
): Promise<HydrateBaselineResponse> {
  const response = await fetch(
    `${API_URL}/api/v1/baseline/rulesets/${rulesetId}/hydrate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor })
    }
  );

  if (!response.ok) {
    throw new Error(`Hydration failed: ${response.statusText}`);
  }

  return response.json();
}

// In page component
const hydrateMutation = useMutation({
  mutationFn: () => hydrateBaselineRules(rulesetId, currentUser?.email),
  onSuccess: (result) => {
    toast({
      title: "Baseline Rules Prepared",
      description: `Created ${result.created_rule_count} rules from ${result.hydrated_rule_count} baseline fields.`
    });
    queryClient.invalidateQueries(["valuation-rules", rulesetId]);
  },
  onError: (error) => {
    toast({
      title: "Hydration Failed",
      description: error.message,
      variant: "destructive"
    });
  }
});

const handleHydrate = async () => {
  await hydrateMutation.mutateAsync();
};
```

**Acceptance Criteria:**
- [ ] API client function created
- [ ] Mutation hook configured
- [ ] Success toast shows counts
- [ ] Error handling with toast
- [ ] Invalidates rules query on success

---

### Task 3.4: Filter Foreign Key Rules in Advanced Mode
**Location:** `apps/web/app/valuation-rules/_components/advanced-mode.tsx`

**Implementation:**
```typescript
// Filter rules before rendering
const visibleRules = useMemo(() => {
  return rules.filter(rule => {
    // Hide foreign key rules
    if (rule.metadata_json?.is_foreign_key_rule === true) {
      return false;
    }
    // Hide deactivated placeholders
    if (rule.metadata_json?.hydrated === true && !rule.is_active) {
      return false;
    }
    return true;
  });
}, [rules]);

// Optional: Show system rules toggle
const [showSystemRules, setShowSystemRules] = useState(false);

const displayRules = useMemo(() => {
  if (showSystemRules) {
    return rules;  // Show all
  }
  return visibleRules;  // Hide foreign key rules
}, [rules, visibleRules, showSystemRules]);
```

**Acceptance Criteria:**
- [ ] Foreign key rules filtered out
- [ ] Deactivated placeholders hidden
- [ ] Optional toggle to show system rules
- [ ] Filter memoized for performance

---

### Task 3.5: Integration with Existing Advanced Mode
**Location:** `apps/web/app/valuation-rules/page.tsx`

**Implementation:**
```typescript
return (
  <div>
    {/* Show banner in Advanced mode if placeholders exist */}
    {mode === "advanced" && hasPlaceholderRules && !hasHydratedRules && (
      <HydrationBanner
        rulesetId={rulesetId}
        onHydrate={handleHydrate}
        isHydrating={hydrateMutation.isPending}
      />
    )}

    {/* Mode-specific content */}
    {mode === "basic" ? (
      <BasicModeContent />
    ) : (
      <AdvancedModeContent rules={displayRules} />
    )}
  </div>
);
```

**Acceptance Criteria:**
- [ ] Banner shows only in Advanced mode
- [ ] Banner only for non-hydrated placeholders
- [ ] Rules filtered before passing to Advanced mode
- [ ] State updates trigger re-render

---

## Phase 4: Testing & Documentation (1 day)

### Task 4.1: E2E Tests
**Location:** `tests/e2e/test_baseline_hydration.spec.ts`

**Test Scenarios:**
1. Switch from Basic to Advanced - see hydration banner
2. Click "Prepare Rules" - see loading state
3. After hydration - banner disappears, rules visible
4. Edit hydrated rule in Advanced mode
5. Switch back to Basic mode - see "Managed in Advanced" message

**Tools:** Playwright or Cypress

**Acceptance Criteria:**
- [ ] All E2E scenarios passing
- [ ] Covers full user journey
- [ ] Screenshots captured for documentation

---

### Task 4.2: User Documentation
**Location:** `docs/user-guide/valuation-rules-mode-switching.md`

**Sections:**
1. Overview of Basic vs Advanced mode
2. When to use each mode
3. Preparing baseline rules for Advanced editing
4. Step-by-step hydration guide with screenshots
5. Understanding expanded rules
6. Best practices

**Acceptance Criteria:**
- [ ] Complete guide with screenshots
- [ ] FAQ section
- [ ] Troubleshooting tips

---

### Task 4.3: Update Architecture Documentation
**Location:** `docs/architecture/valuation-rules.md`

**Updates:**
- Add hydration service section
- Update data flow diagrams
- Add hydration examples
- Update API endpoint list

**Acceptance Criteria:**
- [ ] Architecture doc updated
- [ ] Diagrams include hydration flow
- [ ] Examples added

---

## Phase 5: Optional - Dehydration (1 day)

### Task 5.1: Implement Dehydration Service
**Location:** `BaselineHydrationService.dehydrate_rules()`

**Implementation:**
```python
async def dehydrate_rules(
    self,
    session: AsyncSession,
    ruleset_id: int,
    actor: str = "system"
) -> DehydrationResult:
    """Revert hydrated rules back to placeholders."""
    # Find all hydrated source rules
    stmt = select(ValuationRuleV2).join(ValuationRuleGroup).where(
        ValuationRuleGroup.ruleset_id == ruleset_id,
        ValuationRuleV2.metadata_json["hydrated"].as_boolean() == True
    )
    result = await session.execute(stmt)
    hydrated_rules = result.scalars().all()

    for rule in hydrated_rules:
        # Reactivate placeholder
        rule.is_active = True
        rule.metadata_json = {
            k: v for k, v in rule.metadata_json.items()
            if k not in ["hydrated", "hydrated_at", "hydrated_by"]
        }

        # Delete expanded rules
        delete_stmt = delete(ValuationRuleV2).where(
            ValuationRuleV2.metadata_json["hydration_source_rule_id"].as_integer() == rule.id
        )
        await session.execute(delete_stmt)

    await session.commit()
    return DehydrationResult(status="success", reverted_count=len(hydrated_rules))
```

**Acceptance Criteria:**
- [ ] Reactivates placeholder rules
- [ ] Deletes expanded rules
- [ ] Returns revert count

---

## Rollout Plan

### Week 1: Development
- Days 1-2: Phase 1 (Backend)
- Day 3: Phase 2 (API)
- Days 4-5: Phase 3 (Frontend)

### Week 2: Testing & Release
- Day 1: Phase 4 (Testing & Docs)
- Day 2: Code review and fixes
- Day 3: Deploy to staging
- Day 4: User acceptance testing
- Day 5: Production deployment

### Post-Release:
- Monitor error rates and performance
- Gather user feedback
- Iterate on UX improvements
- Consider Phase 5 (Dehydration) based on user requests

## Success Metrics

- [ ] 0 placeholder rules visible in Advanced mode after hydration
- [ ] All expanded rules have conditions and actions
- [ ] Users can edit hydrated rules without errors
- [ ] No valuation calculation changes pre/post hydration
- [ ] <2 second hydration time for typical ruleset (20 rules)
- [ ] 95%+ test coverage for hydration service

## Risk Mitigation

### Risk: Rule Proliferation
**Mitigation:** Group expanded rules by parent in UI, add collapse/expand

### Risk: Slow Hydration
**Mitigation:** Batch rule creation, add progress indicator

### Risk: User Confusion
**Mitigation:** Clear banners, tooltips, comprehensive documentation

## Commit Strategy

1. **Commit 1:** Backend hydration service + tests
2. **Commit 2:** API endpoints + integration tests
3. **Commit 3:** Frontend detection and banner UI
4. **Commit 4:** Advanced mode filtering and integration
5. **Commit 5:** Documentation updates
6. **Commit 6:** E2E tests

## Next Steps

1. Review and approve this implementation plan
2. Assign tasks to team (backend-architect, ui-engineer)
3. Create tracking issues in project management system
4. Kick off Phase 1 development
