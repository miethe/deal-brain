# Valuation Rules System Implementation Plan

## Overview

This implementation plan addresses critical bugs and enhancements for the Valuation Rules System, organized into four phases over 7 weeks. The plan follows a phased approach prioritizing critical bug fixes first, followed by UX improvements, new feats, and finally the advanced formula builder.

## Project Metadata

- **Total Duration**: 7 weeks
- **Team Size**: 2-3 developers
- **Risk Level**: Medium (existing system modifications)
- **Dependencies**: FastAPI, SQLAlchemy, Next.js 14, React Query, shadcn/ui

## Phase Structure

```
Week 1: Phase 1 - Critical Bug Fixes
Week 2: Phase 2 - UX Improvements
Weeks 3-4: Phase 3 - Action Multipliers
Weeks 5-7: Phase 4 - Formula Builder
```

---

## Phase 1: Critical Bug Fixes (Week 1)

- [Implementation Plan](./valuation-rules-phase-1.md)

## Phase 2: UX Improvements (Week 2)

- [Implementation Plan](./valuation-rules-phase-2.md)

## Phase 3: Action Multipliers System (Weeks 3-4)

- [Implementation Plan](./valuation-rules-phase-3.md)

## Phase 4: Formula Builder (Weeks 5-7)

- [Implementation Plan](./valuation-rules-phase-4.md)

## Implementation Guidelines

### Code Style and Standards

#### Python Backend
- Use async/await for all database operations
- Follow PEP 8 with 100 character line limit
- Use type hints for all function signatures
- Add comprehensive docstrings
- Use logging instead of print statements

#### TypeScript Frontend
- Use functional components with hooks
- Implement proper error boundaries
- Use React Query for server state
- Follow accessibility guidelines (WCAG AA)
- Implement proper loading and error states

### Error Handling

#### Backend
```python
try:
    result = await operation()
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

#### Frontend
```typescript
const mutation = useMutation({
  mutationFn: createRule,
  onError: (error) => {
    console.error('Rule creation failed:', error);
    toast.error(
      error.response?.data?.detail ||
      'Failed to create rule. Please try again.'
    );
  }
});
```

---

## Git Strategy

### Branch Naming Convention
```
feat:P1-BUG-001-fix-rulegroup-modal
feat:P2-UX-001-scrollable-dropdown
feat:P3-FEAT-001-action-multipliers
feat:P4-FEAT-001-formula-builder
```

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>

Types: feat, fix, docs, style, refactor, test, chore
Scope: api, web, core, db

Example:
fix(web): correct modal opening for RuleGroup creation

- Fixed state management issue causing wrong modal to open
- Added validation to prevent multiple modals
- Updated event handlers

Fixes P1-BUG-001
```

### Pull Request Strategy

#### When to Create PRs
- One PR per task (P1-BUG-001, etc.)
- Create draft PR early for visibility
- Request review when acceptance criteria met

#### PR Checklist
```markdown
## Description
Brief description of changes

## Task Reference
Fixes P1-BUG-001

## Type of Change
- [ ] Bug fix
- [ ] New feat
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] No console errors

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No commented-out code
- [ ] No console.log statements

## Screenshots
(if applicable)
```

---

## Testing Strategy

### Unit Testing

#### Backend (pytest)
```python
# tests/test_action_multipliers.py
import pytest
from dealbrain_core.rules.action_engine import ActionEngine

class TestActionMultipliers:
    @pytest.mark.asyncio
    async def test_single_multiplier(self):
        engine = ActionEngine()
        action = create_test_action_with_multiplier()
        context = {"ram_spec.ddr_generation": "ddr3"}

        result = engine.execute_action(action, context)
        assert result == expected_value

    @pytest.mark.parametrize("generation,expected", [
        ("ddr3", 0.7),
        ("ddr4", 1.0),
        ("ddr5", 1.3),
    ])
    async def test_generation_multipliers(self, generation, expected):
        # Test each generation
        pass
```

#### Frontend (Jest/React Testing Library)
```typescript
// tests/ActionMultipliers.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ActionMultipliers } from '@/components/valuation/action-multipliers';

describe('ActionMultipliers', () => {
  it('should add new multiplier when button clicked', () => {
    const onChange = jest.fn();
    render(
      <ActionMultipliers
        multipliers={[]}
        onChange={onChange}
        availableFields={mockFields}
      />
    );

    fireEvent.click(screen.getByText('Add Multiplier'));
    expect(onChange).toHaveBeenCalledWith([
      expect.objectContaining({
        name: 'New Multiplier',
        field: '',
        conditions: []
      })
    ]);
  });
});
```

### Integration Testing

#### API Integration Tests
```python
# tests/integration/test_rules_api.py
async def test_create_rule_with_multipliers(client, db_session):
    rule_data = {
        "name": "RAM Value",
        "actions": [{
            "action_type": "per_unit",
            "metric": "ram_gb",
            "value_usd": 2.5,
            "modifiers_json": {
                "multipliers": [{
                    "name": "Generation Multiplier",
                    "field": "ram_spec.ddr_generation",
                    "conditions": [
                        {"value": "ddr4", "multiplier": 1.0}
                    ]
                }]
            }
        }]
    }

    response = await client.post("/api/v1/valuation-rules", json=rule_data)
    assert response.status_code == 201
```

### E2E Testing (Playwright)

```typescript
// e2e/formula-builder.spec.ts
test('should create rule with formula action', async ({ page }) => {
  await page.goto('/valuation-rules');
  await page.click('text=Add Rule');

  // Select formula action type
  await page.selectOption('select[name="actionType"]', 'formula');

  // Use formula builder
  await page.click('text=cpu_mark_single');
  await page.click('text=×');
  await page.type('input[name="formula"]', '0.05');

  // Verify preview
  await expect(page.locator('.preview')).toContainText('$52.50');

  // Save rule
  await page.click('text=Create Rule');
  await expect(page.locator('.toast')).toContainText('Rule created');
});
```

### Manual Testing Checklists

#### Phase 1 - Bug Fixes
- [ ] RuleGroup modal opens correctly
- [ ] New RuleGroups appear in list
- [ ] Formula actions calculate correctly
- [ ] Baseline rules hydrate properly
- [ ] Foreign key rules hidden

#### Phase 2 - UX
- [ ] Dropdown scrolls smoothly
- [ ] Field search works
- [ ] Keyboard navigation works
- [ ] Value autocomplete works

#### Phase 3 - Multipliers
- [ ] Can add/remove multipliers
- [ ] Field selection works
- [ ] Conditions save correctly
- [ ] Multipliers apply to calculations

#### Phase 4 - Formula Builder
- [ ] Fields insert correctly
- [ ] Operations work
- [ ] Validation shows errors
- [ ] Preview updates live
- [ ] Templates work

---

## Rollout Plan

### Development Environment

#### Setup
```bash
# Create feat branch
git checkout -b feat/P1-BUG-001-fix-rulegroup-modal

# Install dependencies
make setup

# Run migrations
make migrate

# Start services
make up
```

#### Testing
```bash
# Run backend tests
poetry run pytest tests/test_rules.py -v

# Run frontend tests
cd apps/web && pnpm test

# Run E2E tests
cd apps/web && pnpm test:e2e
```

### Staging Deployment

#### Pre-deployment Checklist
- [ ] All tests passing
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Migration tested on staging data copy

#### Deployment Steps
1. Backup staging database
2. Deploy backend with migrations
3. Run migrations: `alembic upgrade head`
4. Deploy frontend
5. Clear caches
6. Smoke test critical paths

### Production Deployment

#### Pre-deployment
- [ ] Staging testing complete
- [ ] Performance benchmarks acceptable
- [ ] Rollback plan documented
- [ ] Maintenance window scheduled

### Monitoring and Alerts

#### Key Metrics
- API response times
- Rule evaluation performance
- Error rates
- Database query times

#### Alert Thresholds
- API latency > 500ms
- Error rate > 1%
- Rule evaluation > 100ms
- Database connections > 80%

---

## Documentation Updates

### Architecture Documentation
- [ ] Update `/docs/architecture/valuation-rules.md` with:
  - Action Multipliers system
  - Formula Builder architecture
  - Performance optimizations

### API Documentation
- [ ] Update OpenAPI schema
- [ ] Document new endpoints
- [ ] Add example requests/responses

### User Guide
- [ ] Create Formula Builder guide
- [ ] Update Valuation Rules guide
- [ ] Add troubleshooting section

### CHANGELOG Entry
```markdown
## [2.1.0] - 2024-XX-XX

### Added
- Action Multipliers system for complex condition-to-action mappings
- Advanced Formula Builder UI for creating formula-based actions
- Field value autocomplete in condition builder
- Scrollable dropdown for long field lists

### Fixed
- RuleGroup modal opening incorrect modal when no groups exist
- New RuleGroups not appearing in list after creation
- Formula actions not evaluating correctly
- Baseline rules not hydrating with proper conditions/actions
- Foreign key rules visible in Advanced Mode

### Changed
- Improved formula parser with better error messages
- Enhanced field selector with virtual scrolling
- Optimized rule evaluation performance

### Technical
- Added multipliers_json support to ValuationRuleAction
- Implemented FormulaValidator for syntax checking
- Added React virtual scrolling for large lists
```

---

## Risk Management

### Technical Risks

#### Risk: Formula evaluation performance
**Mitigation**:
- Cache parsed formulas
- Limit formula complexity
- Add timeouts

#### Risk: Migration failures
**Mitigation**:
- Test on staging first
- Create rollback migrations
- Backup before deployment

#### Risk: UI complexity
**Mitigation**:
- Progressive disclosure
- Good defaults
- Comprehensive help

### Timeline Risks

#### Risk: Scope creep
**Mitigation**:
- Strict phase boundaries
- feat flags for partial releases
- Regular stakeholder updates

#### Risk: Testing delays
**Mitigation**:
- Parallel test development
- Automated test suite
- Early QA involvement

---

## Success Metrics

### Technical Metrics
- [ ] All critical bugs fixed (Phase 1)
- [ ] Rule evaluation < 50ms average
- [ ] Formula validation < 200ms
- [ ] 90% test coverage

### Business Metrics
- [ ] User can create RAM multiplier rules
- [ ] Formula creation success rate > 80%
- [ ] Support tickets reduced by 30%
- [ ] Advanced Mode adoption > 50%

### Quality Metrics
- [ ] Zero critical bugs in production
- [ ] < 1% error rate
- [ ] Page load time < 2 seconds
- [ ] Accessibility score > 90

---

## Appendix

### File Path Reference

```
Backend:
- Models: apps/api/dealbrain_api/models/core.py
- Services: apps/api/dealbrain_api/services/
- API: apps/api/dealbrain_api/api/endpoints/
- Core: packages/core/dealbrain_core/rules/
- Tests: tests/

Frontend:
- Pages: apps/web/app/
- Components: apps/web/components/
- Hooks: apps/web/hooks/
- Utils: apps/web/lib/
- Tests: apps/web/tests/
```

---

This implementation plan provides a complete roadmap for fixing bugs and implementing enhancements to the Valuation Rules System. Each task is clearly defined with acceptance criteria, implementation notes, and testing requirements to ensure successful delivery.