# Backend Refactoring Tracker

**Last Updated**: 2025-11-11
**Status**: In Progress
**Branch**: claude/refactor-backend-monolithic-files-011CV2RkWAbkkhkSg6udF3pM

---

## Refactoring Goals

1. **Improve Maintainability**: Break monolithic files into focused, single-responsibility modules
2. **Optimize for AI Agents**: Reduce token overhead when analyzing service layers (target: 95%+ symbol efficiency)
3. **Enhance Code Organization**: Clear separation of concerns (routers, services, repositories, schemas)
4. **Maintain Test Coverage**: Preserve/improve test coverage during refactoring (>80% target)
5. **Document Architecture**: Clear integration points and data flow between modules

---

## Target Files

### Priority 0 - Critical (1400+ LOC each)
- [ ] `adapters/jsonld.py` (1703 LOC) → Split into extractors/, parsers/, normalizers/
- [ ] `services/listings.py` (1536 LOC) → Split into crud, valuation, metrics, components, pagination
- [ ] `services/ingestion.py` (1441 LOC) → Split into deduplication, normalizer, events, quality

### Priority 1 - High (1000+ LOC each)
- [ ] `services/imports/service.py` (1234 LOC) → Split into parser, mapper, matcher, validators, builders
- [ ] `api/rules.py` (1066 LOC) → Split into rulesets, groups, rules, evaluation, packaging
- [ ] `api/listings.py` (1060 LOC) → Split into crud, bulk_operations, valuation, ports, schema

### Priority 2 - Medium (700+ LOC)
- [ ] `models/core.py` (766 LOC) → Split by domain: catalog, listings, rules, ports, imports, settings

---

## Refactoring Strategy

### Approach: Break by Concern and Domain

1. **Analyze Current Structure**: Use codebase-explorer to identify all classes, functions, and dependencies
2. **Map Dependencies**: Create mental model of what depends on what
3. **Group by Concern**: Identify logical boundaries (business logic, database, API contracts, import logic)
4. **Extract Incrementally**: One concern/domain at a time, with tests passing after each extraction
5. **Update Imports**: Ensure all references update when files are reorganized
6. **Validate Symbols**: Regenerate symbol files after each major refactoring pass

### Principles

- **Single Responsibility**: Each file/module has one reason to change
- **Clear Boundaries**: Public interfaces are minimal and well-documented
- **Testability**: Each module can be tested independently
- **Token Efficiency**: Symbol files enable quick agent understanding without full file reads

---

## Progress Tracking

### Phase 1: Analysis & Planning
- [x] Run system-architect analysis on backend
- [x] Identify monolithic files and their concerns
- [x] Document dependency graph and priorities
- [x] Create refactoring plan with specific targets

### Phase 2: Service Layer Refactoring
- [ ] Refactor `listings.py` (metrics, components, scores)
- [ ] Refactor `imports/` pipeline (clarity, testability)
- [ ] Create repository layer if needed
- [ ] Verify tests pass after each extraction

### Phase 3: Model Layer Organization
- [ ] Review `models/core.py` organization
- [ ] Separate domain models if needed
- [ ] Ensure relationships are clear

### Phase 4: API Router Organization
- [ ] Review route organization by domain
- [ ] Ensure consistent request/response handling
- [ ] Verify error handling is consistent

### Phase 5: Validation & Symbol Generation
- [ ] Run full test suite
- [ ] Regenerate symbol files
- [ ] Verify symbol efficiency (token reduction)
- [ ] Final documentation pass

---

## Testing Status

### Before Refactoring
- [ ] Run full test suite: `make test`
- [ ] Record baseline coverage
- [ ] Identify fragile tests

### During Refactoring
- [ ] Run tests after each file extraction
- [ ] Update test imports as files move
- [ ] Maintain >80% coverage target

### After Refactoring
- [ ] Full test suite passes
- [ ] Coverage meets or exceeds baseline
- [ ] No regressions in behavior

---

## Commit Log

Track commits made during refactoring (reference only):

- [ ] Initial commit: Refactor planning & analysis
- [ ] [commit hash]: Service layer analysis
- [ ] [commit hash]: First extraction (TBD)
- [ ] [commit hash]: Integration validation
- [ ] [commit hash]: Final symbol generation

**Note**: Detailed commit messages in git log; this tracks high-level refactoring milestones.

---

## Observations

### Architecture Patterns
- [To be populated during analysis] Current pattern for service organization
- [To be populated during analysis] Dependency flow in models layer
- [To be populated during analysis] Import pipeline complexity points

### Token Efficiency Insights
- [To be populated after refactoring] Estimated token reduction from symbol optimization
- [To be populated after refactoring] File organization impact on agent understanding

### Technical Decisions
- [To be populated during refactoring] Rationale for specific extraction boundaries
- [To be populated during refactoring] Integration patterns chosen
- [To be populated during refactoring] Testing approach for extracted modules

### Gotchas & Learnings
- [To be populated during refactoring] Watch for circular dependencies
- [To be populated during refactoring] Import order matters in Python services
- [To be populated during refactoring] SQLAlchemy session scope handling critical

---

## Next Actions

1. **Immediate**: Run `Task("codebase-explorer", "Find all service layer functions and dependencies in apps/api/dealbrain_api/")`
2. **Then**: Analyze results to identify extraction candidates
3. **Then**: Start Phase 1 analysis with specific targets identified
4. **Finally**: Execute refactoring phases in order with testing after each step

---

## Related Context

- Implementation branch: `claude/refactor-backend-monolithic-files-011CV2RkWAbkkhkSg6udF3pM`
- Architecture guides: `/docs/architecture/` (if exists)
- Symbol system: `.claude/symbols/symbols-api.json` (for tracking refactored modules)
