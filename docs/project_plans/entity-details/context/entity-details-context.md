# Entity Detail Views Working Context

**Purpose:** Token-efficient context for resuming work across AI turns

---

## Current State

**Branch:** feat/entity-details-pages
**Last Commit:** 7532fe9 plan(collections-community): add feature requests for collections, sharing, and other community features
**Current Task:** Phase 3 - FieldRegistry Expansion (registering 5 new entities)

---

## Key Decisions

- **Architecture:** Following Deal Brain layered architecture (API → Services → Domain Logic → Database)
- **Patterns:** Backend-first approach - completing API layer before frontend work
- **Trade-offs:** Phase 3 runs parallel to Phases 1-2 (different files, no conflicts)

---

## Important Learnings

(To be populated as implementation progresses)

---

## Quick Reference

### Environment Setup
```bash
# Backend API
export PYTHONPATH="$PWD/apps/api"
poetry install

# Database
make migrate

# Full stack
make up
```

### Key Files
- FieldRegistry: apps/api/dealbrain_api/services/field_registry.py
- Field Data API: apps/api/dealbrain_api/api/field_data.py
- Models: apps/api/dealbrain_api/models/core.py
- Tests: tests/test_field_registry.py

---

## Phase Scope (From Plan)

**Objective:** Register GPU, RamSpec, StorageProfile, PortsProfile, Profile in FieldRegistry to enable unified management.

**Success Metric:** All 7 entities returned by GET /v1/fields-data/entities with accurate field metadata
