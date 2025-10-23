# Phase 4 Working Context

**Purpose:** Token-efficient context for resuming work across AI turns

---

## Current State

**Branch:** valuation-rules-enhance
**Last Commit:** 18549fc (Phase 3 complete)
**Current Task:** P4-FEAT-001 - Formula Parser Enhancement

---

## Key Decisions

- **Architecture:** Formula Builder follows layered architecture - Backend validation API, Frontend visual builder, Core domain logic in packages/core
- **Patterns:** React Query for server state, Radix UI for accessible components, Pydantic validation for all API inputs
- **Trade-offs:** Visual mode for ease of use, text mode for power users - both generate same formula output

---

## Important Learnings

- **Formula Engine Location:** Core formula logic lives in packages/core/dealbrain_core/rules/formula.py
- **Validation Pattern:** Backend provides validation API, frontend validates in real-time with debounce (300ms)
- **Field References:** Use EntityFieldSelector component for consistent field selection across app

---

## Quick Reference

### Environment Setup
```bash
# Backend API
export PYTHONPATH="$PWD/apps/api"
poetry install

# Frontend Web
pnpm install
pnpm --filter "./apps/web" dev

# Database
make migrate

# Full stack
make up
```

### Key Files
- Formula Engine: packages/core/dealbrain_core/rules/formula.py
- Formula Validator: packages/core/dealbrain_core/rules/formula_validator.py (new)
- API Endpoint: apps/api/dealbrain_api/api/endpoints/rules.py
- Schemas: apps/api/dealbrain_api/schemas/rules.py
- UI Component: apps/web/components/valuation/formula-builder.tsx (new)
- Formula Editor: apps/web/components/valuation/formula-editor.tsx (new)
- Utils: apps/web/lib/formula-utils.ts (new)

---

## Phase Scope (From Plan)

Implement the advanced Formula Builder UI for creating and validating formula-based actions. This includes:
1. Enhanced formula parser with better error messages and security validation
2. Visual formula builder component with field selection, operation palette, and live preview
3. Backend validation API for real-time formula checking
4. Comprehensive documentation and help system

**Success Metric:** 95% reduction in formula syntax errors, 80% of users prefer visual builder over text mode
