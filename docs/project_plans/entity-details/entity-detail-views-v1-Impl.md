---
title: "Unified Entity Detail Views & CRUD Operations - Implementation Plan"
description: "Detailed phased implementation plan for complete CRUD operations across all catalog entities"
audience: [ai-agents, developers]
tags: [implementation, planning, phases, entity-crud, global-fields]
created: 2025-11-12
updated: 2025-11-12
category: "product-planning"
status: draft
related:
  - /docs/project_plans/PRDs/enhancements/entity-detail-views-v1.md
---

# Unified Entity Detail Views & CRUD Operations - Implementation Plan

**Feature**: Unified Entity Detail Views & CRUD Operations
**PRD**: `/docs/project_plans/PRDs/enhancements/entity-detail-views-v1.md`
**Total Effort**: 61 story points (~3 sprints)
**Target Completion**: Q1 2025

## Executive Summary

This implementation plan delivers complete CRUD operations for all 7 catalog entity types (CPU, GPU, RAM Spec, Storage Profile, Ports Profile, Scoring Profile, Listing) with unified management interfaces. The plan follows Deal Brain's layered architecture (routers → services → models) and prioritizes backend completeness before frontend integration.

**Key Deliverables**:
- UPDATE and DELETE endpoints for 6 catalog entities (CPU, GPU, RamSpec, StorageProfile, PortsProfile, Profile)
- FieldRegistry registration for 5 previously unregistered entities
- Edit/Delete UI added to 4 existing detail views
- 2 new detail views created (PortsProfile, Profile)
- Global Fields workspace expanded to show all 7 entities

**Implementation Strategy**:
- Backend-first approach: Complete API layer (Phases 1-3) before frontend
- Incremental entity rollout: Test with CPU/GPU before expanding to all entities
- Reusable component patterns: Single EditModal/DeleteDialog for all entity types
- Cascading validation: Block deletes of entities with dependent listings

**Success Criteria**:
- ✅ All 7 entities have complete CRUD operations via API and UI
- ✅ Zero errors from deleting entities with dependencies
- ✅ Update operations complete in < 500ms
- ✅ Delete cascade checks complete in < 1s
- ✅ 80%+ test coverage for new CRUD operations

## Phase Overview

| Phase | Title | Effort | Duration | Dependencies |
|-------|-------|--------|----------|--------------|
| 1 | Backend CRUD - UPDATE Endpoints | 8 pts | 3 days | None |
| 2 | Backend CRUD - DELETE Endpoints | 8 pts | 3 days | Phase 1 |
| 3 | FieldRegistry Expansion | 5 pts | 2 days | None (parallel with 1-2) |
| 4 | Frontend Edit UI | 8 pts | 3 days | Phase 1, 3 |
| 5 | Frontend Delete UI | 8 pts | 3 days | Phase 2, 4 |
| 6 | New Detail Views (PortsProfile, Profile) | 8 pts | 3 days | Phase 1, 2 |
| 7 | Global Fields Integration | 8 pts | 3 days | Phase 3, 4, 5 |
| 8 | Testing & Validation | 5 pts | 2 days | Phase 7 |
| 9 | Documentation & Deployment | 3 pts | 1 day | Phase 8 |

**Critical Path**: Phases 1 → 2 → 4 → 5 → 7 → 8 → 9

**Parallel Work Opportunities**:
- Phase 3 can run parallel with Phases 1-2 (different files)
- Phase 6 can start after Phases 1-2 complete (independent of 4-5)

---

## Phase 1: Backend CRUD - UPDATE Endpoints

**Objective**: Add PUT and PATCH endpoints to catalog API for updating all 6 catalog entities.

**Duration**: 3 days
**Effort**: 8 story points
**Dependencies**: None
**Assigned Subagent(s)**: python-backend-engineer, backend-architect

### Tasks

| Task ID | Task Name | Description | Acceptance Criteria | Estimate | Assignee |
|---------|-----------|-------------|---------------------|----------|----------|
| UP-001 | Add CPU UPDATE endpoints | Add `PUT /v1/catalog/cpus/{id}` and `PATCH /v1/catalog/cpus/{id}` endpoints to catalog API | - PUT accepts full CPUUpdate schema<br>- PATCH accepts partial CPUUpdate schema<br>- Returns updated CPU DTO<br>- Validates unique constraints<br>- Updates modified_at timestamp | 1 pt | python-backend-engineer |
| UP-002 | Add GPU UPDATE endpoints | Add `PUT/PATCH /v1/catalog/gpus/{id}` endpoints | - Same as UP-001 for GPU entity<br>- Validates unique GPU name | 1 pt | python-backend-engineer |
| UP-003 | Add RamSpec UPDATE endpoints | Add `PUT/PATCH /v1/catalog/ram-specs/{id}` endpoints | - Same as UP-001 for RamSpec<br>- Validates unique constraint on (ddr_generation, speed_mhz, module_count, capacity_per_module_gb) | 1 pt | python-backend-engineer |
| UP-004 | Add StorageProfile UPDATE endpoints | Add `PUT/PATCH /v1/catalog/storage-profiles/{id}` endpoints | - Same as UP-001 for StorageProfile<br>- Validates unique constraint on (medium, interface, form_factor, capacity_gb) | 1 pt | python-backend-engineer |
| UP-005 | Add PortsProfile UPDATE endpoints | Add `PUT/PATCH /v1/catalog/ports-profiles/{id}` endpoints | - Same as UP-001 for PortsProfile<br>- Updates related Port entities if provided<br>- Maintains referential integrity | 1.5 pts | python-backend-engineer, backend-architect |
| UP-006 | Add Profile UPDATE endpoints | Add `PUT/PATCH /v1/catalog/profiles/{id}` endpoints | - Same as UP-001 for Profile (scoring)<br>- Validates weights_json schema<br>- Prevents removing is_default from only default profile | 1 pt | python-backend-engineer |
| UP-007 | Create Update Pydantic schemas | Create `CPUUpdate`, `GPUUpdate`, `RamSpecUpdate`, etc. schemas for request validation | - Schemas allow partial updates (all fields optional)<br>- Include validation rules (min/max, regex)<br>- Support attributes_json merging | 1 pt | python-backend-engineer |
| UP-008 | Add UPDATE integration tests | Write integration tests for all UPDATE endpoints | - Test successful full update (PUT)<br>- Test successful partial update (PATCH)<br>- Test unique constraint validation<br>- Test 404 for non-existent entity<br>- Test 422 for invalid input | 1.5 pts | python-backend-engineer |

**Files Modified**:
- `/apps/api/dealbrain_api/api/catalog.py` - Add UPDATE endpoints
- `/apps/api/dealbrain_api/schemas/catalog.py` - Add Update schemas
- `/tests/test_catalog_api.py` - Add integration tests

**Quality Gates**:
- [ ] All UPDATE endpoints return 200 OK with updated entity
- [ ] Unique constraint violations return 422 Unprocessable Entity
- [ ] PATCH merges attributes_json correctly (doesn't overwrite)
- [ ] Integration tests pass with 100% coverage
- [ ] OpenTelemetry spans created for all UPDATE operations

### Success Criteria

- ✅ 6 entities have PUT and PATCH endpoints implemented
- ✅ Update operations complete in < 500ms (measured via OpenTelemetry)
- ✅ Unique constraint validation prevents duplicates
- ✅ Integration tests achieve > 90% coverage for update logic

---

## Phase 2: Backend CRUD - DELETE Endpoints

**Objective**: Add DELETE endpoints with cascade validation to prevent orphaning listings.

**Duration**: 3 days
**Effort**: 8 story points
**Dependencies**: Phase 1 (same files being modified)
**Assigned Subagent(s)**: python-backend-engineer, data-layer-expert

### Tasks

| Task ID | Task Name | Description | Acceptance Criteria | Estimate | Assignee |
|---------|-----------|-------------|---------------------|----------|----------|
| DEL-001 | Implement "Used In" count service | Create service method to count listings using each entity type | - `get_cpu_usage_count(cpu_id)` returns listing count<br>- Similar methods for GPU, RamSpec, StorageProfile, PortsProfile, Profile<br>- Uses COUNT(*) query (not loading full listings)<br>- Query completes in < 500ms | 1.5 pts | data-layer-expert, python-backend-engineer |
| DEL-002 | Add CPU DELETE endpoint | Add `DELETE /v1/catalog/cpus/{id}` with cascade check | - Returns 204 No Content on success<br>- Returns 409 Conflict if CPU in use (includes count in error)<br>- Hard deletes entity from database<br>- Cascade check completes in < 1s | 1 pt | python-backend-engineer |
| DEL-003 | Add GPU DELETE endpoint | Add `DELETE /v1/catalog/gpus/{id}` with cascade check | - Same as DEL-002 for GPU entity | 1 pt | python-backend-engineer |
| DEL-004 | Add RamSpec DELETE endpoint | Add `DELETE /v1/catalog/ram-specs/{id}` with cascade check | - Same as DEL-002 for RamSpec<br>- Checks both primary_ram_spec_id and secondary_ram_spec_id usage | 1 pt | python-backend-engineer |
| DEL-005 | Add StorageProfile DELETE endpoint | Add `DELETE /v1/catalog/storage-profiles/{id}` with cascade check | - Same as DEL-002 for StorageProfile<br>- Checks both primary_storage_profile_id and secondary_storage_profile_id usage | 1 pt | python-backend-engineer |
| DEL-006 | Add PortsProfile DELETE endpoint | Add `DELETE /v1/catalog/ports-profiles/{id}` with cascade check | - Same as DEL-002 for PortsProfile<br>- Cascade deletes related Port entities | 1.5 pts | python-backend-engineer, data-layer-expert |
| DEL-007 | Add Profile DELETE endpoint | Add `DELETE /v1/catalog/profiles/{id}` with cascade check | - Same as DEL-002 for Profile (scoring)<br>- Prevents deleting is_default=True profile if only default | 1 pt | python-backend-engineer |
| DEL-008 | Add DELETE integration tests | Write integration tests for all DELETE endpoints | - Test successful delete of unused entity<br>- Test 409 Conflict when entity in use<br>- Test 404 for non-existent entity<br>- Test cascade delete of related entities (PortsProfile → Ports)<br>- Test error message includes usage count | 2 pts | python-backend-engineer |

**Files Modified**:
- `/apps/api/dealbrain_api/api/catalog.py` - Add DELETE endpoints
- `/apps/api/dealbrain_api/services/catalog.py` - Add usage count methods (or create new file)
- `/tests/test_catalog_api.py` - Add delete integration tests

**Quality Gates**:
- [ ] DELETE endpoints return 204 No Content for unused entities
- [ ] DELETE endpoints return 409 Conflict with usage count for entities in use
- [ ] Cascade checks complete in < 1s (measured via OpenTelemetry)
- [ ] Zero listing orphans after delete operations
- [ ] Integration tests pass with 100% coverage

### Success Criteria

- ✅ 6 entities have DELETE endpoints with cascade validation
- ✅ Zero accidental deletions of entities with dependencies
- ✅ Error messages clearly communicate usage count
- ✅ Delete operations complete in < 1s including cascade check
- ✅ Integration tests achieve > 90% coverage for delete logic

---

## Phase 3: FieldRegistry Expansion

**Objective**: Register GPU, RamSpec, StorageProfile, PortsProfile, Profile in FieldRegistry to enable unified management.

**Duration**: 2 days
**Effort**: 5 story points
**Dependencies**: None (parallel with Phases 1-2)
**Assigned Subagent(s)**: python-backend-engineer, backend-architect

### Tasks

| Task ID | Task Name | Description | Acceptance Criteria | Estimate | Assignee |
|---------|-----------|-------------|---------------------|----------|----------|
| REG-001 | Register GPU in FieldRegistry | Add GPU entity registration to FieldRegistry with core fields mapping | - `FieldRegistry.register("gpu", Gpu)` called on init<br>- Core fields mapped: name, manufacturer, gpu_mark, metal_score, notes<br>- attributes_json mapped for custom fields<br>- GET /v1/fields-data/gpu/schema returns complete schema | 1 pt | python-backend-engineer |
| REG-002 | Register RamSpec in FieldRegistry | Add RamSpec entity registration with core fields mapping | - Similar to REG-001<br>- Core fields: label, ddr_generation, speed_mhz, module_count, capacity_per_module_gb, total_capacity_gb, notes | 1 pt | python-backend-engineer |
| REG-003 | Register StorageProfile in FieldRegistry | Add StorageProfile entity registration with core fields mapping | - Similar to REG-001<br>- Core fields: label, medium, interface, form_factor, capacity_gb, performance_tier, notes | 1 pt | python-backend-engineer |
| REG-004 | Register PortsProfile in FieldRegistry | Add PortsProfile entity registration with core fields mapping | - Similar to REG-001<br>- Core fields: name, description<br>- Handle nested Port entities (related objects)<br>- Support creating/updating ports with profile | 1.5 pts | python-backend-engineer, backend-architect |
| REG-005 | Register Profile in FieldRegistry | Add Profile (scoring) entity registration with core fields mapping | - Similar to REG-001<br>- Core fields: name, description, is_default, weights_json, rule_group_weights<br>- Validate weights_json schema on create/update | 1 pt | python-backend-engineer |
| REG-006 | Update GET /v1/fields-data/entities | Ensure new entities appear in entities list endpoint | - GET /v1/fields-data/entities returns all 7 entities<br>- Response includes: id, name, label, field count | 0.5 pts | python-backend-engineer |

**Files Modified**:
- `/apps/api/dealbrain_api/services/field_registry.py` - Add registrations
- `/apps/api/dealbrain_api/api/field_data.py` - Verify endpoints work with new entities
- `/tests/test_field_registry.py` - Add tests for new registrations

**Quality Gates**:
- [ ] All 7 entities returned by GET /v1/fields-data/entities
- [ ] Schema endpoints return correct core + custom fields for each entity
- [ ] Create/update operations work via fields-data API for new entities
- [ ] Unit tests verify registration metadata correctness

### Success Criteria

- ✅ 5 new entities registered in FieldRegistry (GPU, RamSpec, StorageProfile, PortsProfile, Profile)
- ✅ GET /v1/fields-data/entities returns all 7 entities
- ✅ Schema endpoints return accurate field metadata
- ✅ Fields-data API CRUD operations work for all entities

---

## Phase 4: Frontend Edit UI

**Objective**: Add Edit buttons and modals to existing detail views (CPU, GPU, RamSpec, StorageProfile).

**Duration**: 3 days
**Effort**: 8 story points
**Dependencies**: Phase 1 (UPDATE endpoints), Phase 3 (FieldRegistry for schemas)
**Assigned Subagent(s)**: ui-engineer-enhanced, frontend-developer

### Tasks

| Task ID | Task Name | Description | Acceptance Criteria | Estimate | Assignee |
|---------|-----------|-------------|---------------------|----------|----------|
| EDIT-001 | Create EntityEditModal component | Create reusable modal component accepting entity schema and onSubmit callback | - Generic modal accepts: entityType, entityId, initialValues, schema, onSubmit<br>- Uses React Hook Form with Zod validation<br>- Pre-populates form with initialValues<br>- Shows inline validation errors<br>- Disables submit until valid<br>- Calls PATCH endpoint on submit | 2 pts | ui-engineer-enhanced |
| EDIT-002 | Create entity-specific edit forms | Create form schemas for CPU, GPU, RamSpec, StorageProfile using Zod | - CPUEditSchema, GPUEditSchema, RamSpecEditSchema, StorageProfileEditSchema<br>- Map to backend Update schemas<br>- Include validation rules (required, min/max, regex)<br>- Support attributes_json as dynamic fields | 1.5 pts | ui-engineer-enhanced |
| EDIT-003 | Add Edit button to CPU detail layout | Add "Edit" button to CPUDetailLayout opening EntityEditModal | - Button in header next to breadcrumb<br>- Clicking opens modal pre-filled with current CPU data<br>- Successful edit shows success toast and refetches CPU detail<br>- Error shows error toast with message | 1 pt | frontend-developer |
| EDIT-004 | Add Edit button to GPU detail layout | Add "Edit" button to GPUDetailLayout opening EntityEditModal | - Same as EDIT-003 for GPU entity | 1 pt | frontend-developer |
| EDIT-005 | Add Edit button to RamSpec detail layout | Add "Edit" button to RamSpecDetailLayout opening EntityEditModal | - Same as EDIT-003 for RamSpec entity | 1 pt | frontend-developer |
| EDIT-006 | Add Edit button to StorageProfile detail layout | Add "Edit" button to StorageProfileDetailLayout opening EntityEditModal | - Same as EDIT-003 for StorageProfile entity | 1 pt | frontend-developer |
| EDIT-007 | Implement optimistic updates | Use React Query's optimistic update pattern for instant UI feedback | - UI updates immediately on submit<br>- Rolls back on error<br>- Refetches data to sync with server | 1 pt | frontend-developer |
| EDIT-008 | Add success/error toast notifications | Use toast library for user feedback on edit operations | - Success toast: "CPU updated successfully"<br>- Error toast: Shows backend error message<br>- Toast auto-dismisses after 5s | 0.5 pts | frontend-developer |

**Files Modified**:
- `/apps/web/components/entity/entity-edit-modal.tsx` - NEW reusable modal
- `/apps/web/lib/schemas/entity-schemas.ts` - NEW Zod schemas
- `/apps/web/components/catalog/cpu-detail-layout.tsx` - Add Edit button
- `/apps/web/components/catalog/gpu-detail-layout.tsx` - Add Edit button
- `/apps/web/components/catalog/ram-spec-detail-layout.tsx` - Add Edit button
- `/apps/web/components/catalog/storage-profile-detail-layout.tsx` - Add Edit button
- `/apps/web/hooks/use-entity-mutations.ts` - NEW React Query mutations

**Quality Gates**:
- [ ] Edit modal opens with current entity data pre-filled
- [ ] Form validation prevents invalid submissions
- [ ] Successful edit updates UI and shows success toast
- [ ] Error responses show clear error messages
- [ ] Component tests verify modal behavior
- [ ] Accessibility: Modal keyboard navigable, screen reader friendly

### Success Criteria

- ✅ 4 detail views have functioning Edit buttons
- ✅ Edit modal reusable across all entity types
- ✅ Form validation matches backend validation
- ✅ Optimistic updates provide instant feedback
- ✅ > 75% component test coverage

---

## Phase 5: Frontend Delete UI

**Objective**: Add Delete buttons and confirmation dialogs to all detail views with "Used In" warnings.

**Duration**: 3 days
**Effort**: 8 story points
**Dependencies**: Phase 2 (DELETE endpoints), Phase 4 (Edit UI patterns)
**Assigned Subagent(s)**: ui-engineer-enhanced, frontend-developer

### Tasks

| Task ID | Task Name | Description | Acceptance Criteria | Estimate | Assignee |
|---------|-----------|-------------|---------------------|----------|----------|
| DEL-UI-001 | Create EntityDeleteDialog component | Create reusable confirmation dialog with "Used In" warning | - Accepts: entityType, entityId, entityName, usedInCount, onConfirm<br>- Shows "Used In X Listings" badge<br>- Requires typing entity name if usedInCount > 0<br>- Disables confirm button until validation passes<br>- Calls DELETE endpoint on confirm | 2 pts | ui-engineer-enhanced |
| DEL-UI-002 | Add "Used In" count to detail views | Fetch and display listing count for each entity in detail header | - Calls GET /v1/catalog/{entity}/{id}/listings with count=true<br>- Displays badge: "Used in 15 listings"<br>- Badge links to "Used In Listings" section on page<br>- Updates after edit operations | 1 pt | frontend-developer |
| DEL-UI-003 | Add Delete button to CPU detail layout | Add "Delete" button to CPUDetailLayout opening EntityDeleteDialog | - Button in header next to Edit button<br>- Button shows tooltip with "Used in X listings"<br>- Successful delete redirects to /catalog/cpus<br>- Error shows toast with "Cannot delete: CPU is used in X listings" | 1 pt | frontend-developer |
| DEL-UI-004 | Add Delete button to GPU detail layout | Add "Delete" button to GPUDetailLayout opening EntityDeleteDialog | - Same as DEL-UI-003 for GPU entity<br>- Redirects to /catalog/gpus | 1 pt | frontend-developer |
| DEL-UI-005 | Add Delete button to RamSpec detail layout | Add "Delete" button to RamSpecDetailLayout opening EntityDeleteDialog | - Same as DEL-UI-003 for RamSpec entity<br>- Redirects to /catalog/ram-specs | 1 pt | frontend-developer |
| DEL-UI-006 | Add Delete button to StorageProfile detail layout | Add "Delete" button to StorageProfileDetailLayout opening EntityDeleteDialog | - Same as DEL-UI-003 for StorageProfile entity<br>- Redirects to /catalog/storage-profiles | 1 pt | frontend-developer |
| DEL-UI-007 | Implement delete mutation with error handling | Use React Query mutation for delete with 409 Conflict handling | - DELETE mutation invalidates entity list cache<br>- 409 Conflict shows error toast with usage count<br>- 404 shows "Entity not found"<br>- Success redirects to entity list page | 1 pt | frontend-developer |
| DEL-UI-008 | Add confirmation step for in-use entities | Require typing entity name to confirm deletion of entities with dependencies | - If usedInCount > 0, dialog shows text input<br>- User must type exact entity name to enable confirm button<br>- Case-insensitive comparison<br>- Provides extra safety against accidental deletes | 1 pt | ui-engineer-enhanced |

**Files Modified**:
- `/apps/web/components/entity/entity-delete-dialog.tsx` - NEW reusable dialog
- `/apps/web/components/catalog/cpu-detail-layout.tsx` - Add Delete button
- `/apps/web/components/catalog/gpu-detail-layout.tsx` - Add Delete button
- `/apps/web/components/catalog/ram-spec-detail-layout.tsx` - Add Delete button
- `/apps/web/components/catalog/storage-profile-detail-layout.tsx` - Add Delete button
- `/apps/web/hooks/use-entity-mutations.ts` - Add delete mutation

**Quality Gates**:
- [ ] Delete dialog shows accurate "Used In" count
- [ ] Deletion blocked if entity has dependencies (409 Conflict)
- [ ] Confirmation requires typing entity name for in-use entities
- [ ] Successful delete redirects to entity list page
- [ ] Error messages clearly communicate why delete failed
- [ ] Accessibility: Dialog keyboard navigable, announces state changes

### Success Criteria

- ✅ 4 detail views have functioning Delete buttons
- ✅ Delete dialog reusable across all entity types
- ✅ Zero accidental deletions of entities with dependencies
- ✅ Error handling provides clear guidance
- ✅ > 75% component test coverage

---

## Phase 6: New Detail Views (PortsProfile, Profile)

**Objective**: Create dedicated detail views for Ports Profile and Scoring Profile with Edit/Delete functionality.

**Duration**: 3 days
**Effort**: 8 story points
**Dependencies**: Phase 1 (UPDATE endpoints), Phase 2 (DELETE endpoints)
**Assigned Subagent(s)**: ui-engineer-enhanced, frontend-developer

### Tasks

| Task ID | Task Name | Description | Acceptance Criteria | Estimate | Assignee |
|---------|-----------|-------------|---------------------|----------|----------|
| VIEW-001 | Create PortsProfile detail page | Create `/app/catalog/ports-profiles/[id]/page.tsx` with server component | - Fetches ports profile by ID from API<br>- Returns 404 page if not found<br>- Passes data to PortsProfileDetailLayout<br>- Uses existing page patterns (CPU/GPU detail) | 1 pt | frontend-developer |
| VIEW-002 | Create PortsProfileDetailLayout component | Create detail layout showing ports profile specs and used-in listings | - Header with breadcrumb, Edit, Delete buttons<br>- "Specifications" card: name, description, attributes<br>- "Ports" card: table of ports (type, count, spec_notes)<br>- "Used In Listings" card with listing previews<br>- Uses EntityEditModal and EntityDeleteDialog | 2 pts | ui-engineer-enhanced |
| VIEW-003 | Create Profile (scoring) detail page | Create `/app/catalog/profiles/[id]/page.tsx` with server component | - Fetches scoring profile by ID from API<br>- Returns 404 page if not found<br>- Passes data to ProfileDetailLayout | 1 pt | frontend-developer |
| VIEW-004 | Create ProfileDetailLayout component | Create detail layout showing scoring profile weights and used-in listings | - Header with breadcrumb, Edit, Delete buttons<br>- "Profile Details" card: name, description, is_default badge<br>- "Scoring Weights" card: table visualizing weights_json<br>- "Rule Group Weights" card: table of rule priorities<br>- "Used In Listings" card<br>- Uses EntityEditModal and EntityDeleteDialog | 2 pts | ui-engineer-enhanced |
| VIEW-005 | Add PortsProfile edit form | Create PortsProfileEditSchema and form component | - Schema validates: name (required), description, attributes_json<br>- Form supports editing nested Port entities<br>- Add/remove port rows dynamically<br>- Validates port count > 0 | 1.5 pts | ui-engineer-enhanced |
| VIEW-006 | Add Profile edit form | Create ProfileEditSchema and form component | - Schema validates: name (required), description, weights_json, rule_group_weights<br>- Weights UI shows sliders/inputs for each metric<br>- Validates weights sum to 1.0 (or 100%)<br>- Shows is_default toggle with warning | 1.5 pts | ui-engineer-enhanced |

**Files Modified**:
- `/apps/web/app/catalog/ports-profiles/[id]/page.tsx` - NEW detail page
- `/apps/web/components/catalog/ports-profile-detail-layout.tsx` - NEW layout component
- `/apps/web/app/catalog/profiles/[id]/page.tsx` - NEW detail page
- `/apps/web/components/catalog/profile-detail-layout.tsx` - NEW layout component
- `/apps/web/lib/schemas/entity-schemas.ts` - Add PortsProfile and Profile schemas
- `/apps/web/hooks/use-entity-mutations.ts` - Add mutations for new entities

**Quality Gates**:
- [ ] Detail pages load successfully with data from API
- [ ] Breadcrumb navigation works correctly
- [ ] Edit/Delete buttons function identically to existing detail views
- [ ] "Used In Listings" card shows correct listings
- [ ] 404 page shown for non-existent IDs
- [ ] Responsive design matches existing detail views

### Success Criteria

- ✅ 2 new detail views created and accessible at /catalog/{entity}/[id]
- ✅ Edit/Delete functionality works identically to existing views
- ✅ UI patterns consistent across all 6 detail views
- ✅ Component tests verify new layouts

---

## Phase 7: Global Fields Integration

**Objective**: Update GlobalFieldsWorkspace to show all 7 entities with full CRUD operations.

**Duration**: 3 days
**Effort**: 8 story points
**Dependencies**: Phase 3 (FieldRegistry), Phase 4 (Edit UI), Phase 5 (Delete UI)
**Assigned Subagent(s)**: ui-engineer-enhanced, frontend-developer

### Tasks

| Task ID | Task Name | Description | Acceptance Criteria | Estimate | Assignee |
|---------|-----------|-------------|---------------------|----------|----------|
| GF-001 | Update GlobalFieldsWorkspace entity list | Fetch all 7 entities from GET /v1/fields-data/entities and display in sidebar | - Sidebar shows: Listing, CPU, GPU, RAM Spec, Storage Profile, Ports Profile, Scoring Profile<br>- Each entity has icon and label<br>- Active entity highlighted<br>- Clicking entity loads data grid | 1 pt | frontend-developer |
| GF-002 | Add GPU to GlobalFieldsDataTab | Enable GPU entity data grid in GlobalFieldsDataTab | - Grid shows GPU columns: Name, Manufacturer, GPU Mark, Metal Score, Actions<br>- "Add Entry" button opens GPU create modal<br>- Row "Edit" action opens GPU edit modal<br>- Data fetched from GET /v1/fields-data/gpu/records | 1 pt | frontend-developer |
| GF-003 | Add RamSpec to GlobalFieldsDataTab | Enable RamSpec entity data grid | - Grid shows: Label, DDR Gen, Speed, Capacity, Actions<br>- Create/Edit modals for RamSpec | 1 pt | frontend-developer |
| GF-004 | Add StorageProfile to GlobalFieldsDataTab | Enable StorageProfile entity data grid | - Grid shows: Label, Medium, Interface, Form Factor, Capacity, Actions<br>- Create/Edit modals for StorageProfile | 1 pt | frontend-developer |
| GF-005 | Add PortsProfile to GlobalFieldsDataTab | Enable PortsProfile entity data grid | - Grid shows: Name, Description, Port Count, Actions<br>- Create/Edit modals for PortsProfile (with nested ports)<br>- "View Details" action links to /catalog/ports-profiles/{id} | 1.5 pts | ui-engineer-enhanced |
| GF-006 | Add Profile to GlobalFieldsDataTab | Enable Profile (scoring) entity data grid | - Grid shows: Name, Description, Is Default, Actions<br>- Create/Edit modals for Profile<br>- "View Details" action links to /catalog/profiles/{id} | 1.5 pts | ui-engineer-enhanced |
| GF-007 | Update GlobalFieldsDataTab to support all entities | Refactor data grid to dynamically render based on entity schema | - Single data grid component handles all entity types<br>- Columns generated from entity schema<br>- Create/Edit modals use entity-specific forms<br>- Pagination, filtering, sorting work for all entities | 2 pts | ui-engineer-enhanced, frontend-developer |

**Files Modified**:
- `/apps/web/components/custom-fields/global-fields-workspace.tsx` - Update entity list
- `/apps/web/components/custom-fields/global-fields-data-tab.tsx` - Add entity support
- `/apps/web/components/entity/entity-data-grid.tsx` - NEW generic data grid (optional refactor)

**Quality Gates**:
- [ ] All 7 entities appear in GlobalFieldsWorkspace sidebar
- [ ] Data grids load correctly for each entity
- [ ] Create/Edit modals work for all entity types
- [ ] Pagination handles large entity lists (1000+ items)
- [ ] Filtering and sorting work correctly
- [ ] "View Details" links navigate to correct detail pages

### Success Criteria

- ✅ GlobalFieldsWorkspace shows all 7 entities in sidebar
- ✅ Data grids functional for all entities with CRUD operations
- ✅ Unified UI patterns across all entity data grids
- ✅ Performance: < 2s load time for entity lists up to 10,000 items

---

## Phase 8: Testing & Validation

**Objective**: Comprehensive testing of all CRUD operations and user workflows.

**Duration**: 2 days
**Effort**: 5 story points
**Dependencies**: Phase 7 (all features complete)
**Assigned Subagent(s)**: python-backend-engineer, frontend-developer, ui-engineer-enhanced

### Tasks

| Task ID | Task Name | Description | Acceptance Criteria | Estimate | Assignee |
|---------|-----------|-------------|---------------------|----------|----------|
| TEST-001 | Backend integration tests | Ensure all CRUD endpoints have full integration test coverage | - Update tests: PUT/PATCH success, validation errors, unique constraints<br>- Delete tests: Success, cascade blocked, 404 not found<br>- Coverage > 90% for catalog API<br>- All tests pass in CI pipeline | 1.5 pts | python-backend-engineer |
| TEST-002 | Frontend component tests | Write component tests for new UI components | - EntityEditModal tests: Opens, validates, submits, cancels<br>- EntityDeleteDialog tests: Confirmation flow, "Used In" handling<br>- Detail layout tests: Renders, Edit/Delete buttons work<br>- Coverage > 75% for new components | 1.5 pts | frontend-developer, ui-engineer-enhanced |
| TEST-003 | End-to-end user workflow tests | Write E2E tests covering critical user stories | - US-1: Edit entity specification (success and validation error)<br>- US-2: Delete unused entity (success)<br>- US-2: Attempt delete in-use entity (blocked)<br>- US-3: Manage entities from /global-fields<br>- US-4: View entity usage before deletion | 1.5 pts | frontend-developer |
| TEST-004 | Performance testing | Validate performance benchmarks for CRUD operations | - Update entity: < 500ms (P95)<br>- Delete with cascade check: < 1s (P95)<br>- List entities on /global-fields: < 2s (10,000 items)<br>- Detail view load: < 1.5s including "Used In"<br>- Use OpenTelemetry traces to measure | 0.5 pts | python-backend-engineer |
| TEST-005 | Accessibility audit | Ensure WCAG AA compliance for new UI components | - Keyboard navigation works (Tab, Enter, Esc)<br>- Screen readers announce modals, dialogs, toasts<br>- Color contrast meets AA standards<br>- Focus indicators visible<br>- Use axe-core or similar tool | 0.5 pts | ui-engineer-enhanced |

**Files Modified**:
- `/tests/test_catalog_api.py` - Add integration tests
- `/apps/web/components/**/__tests__/` - Add component tests
- `/apps/web/tests/e2e/` - Add E2E tests (Playwright or Cypress)

**Quality Gates**:
- [ ] All backend integration tests pass with > 90% coverage
- [ ] All frontend component tests pass with > 75% coverage
- [ ] All E2E tests pass for critical user workflows
- [ ] Performance benchmarks met (< 500ms update, < 1s delete)
- [ ] Zero WCAG AA violations in accessibility audit

### Success Criteria

- ✅ > 90% backend test coverage for CRUD operations
- ✅ > 75% frontend test coverage for new components
- ✅ E2E tests cover all user stories in PRD
- ✅ Performance benchmarks met
- ✅ WCAG AA compliant

---

## Phase 9: Documentation & Deployment

**Objective**: Document new functionality and deploy with feature flags.

**Duration**: 1 day
**Effort**: 3 story points
**Dependencies**: Phase 8 (testing complete)
**Assigned Subagent(s)**: documentation-writer, python-backend-engineer

### Tasks

| Task ID | Task Name | Description | Acceptance Criteria | Estimate | Assignee |
|---------|-----------|-------------|---------------------|----------|----------|
| DOC-001 | Update API documentation | Document new UPDATE and DELETE endpoints in OpenAPI spec | - OpenAPI spec includes PUT/PATCH/DELETE for all 6 entities<br>- Request/response schemas documented<br>- Error responses documented (409 Conflict, 422 Validation)<br>- Examples provided for each endpoint | 1 pt | documentation-writer |
| DOC-002 | Create user guide for entity management | Write guide for administrators on managing catalog entities | - Guide covers: Editing entities, Deleting entities, Using /global-fields<br>- Screenshots of Edit/Delete workflows<br>- Troubleshooting section for common issues<br>- Published at /docs/guides/entity-management.md | 1 pt | documentation-writer |
| DOC-003 | Add feature flags for phased rollout | Implement feature flags for entity CRUD functionality | - `enable_entity_updates` flag controls UPDATE endpoints<br>- `enable_entity_deletes` flag controls DELETE endpoints<br>- Flags configurable via environment variables<br>- UI conditionally shows Edit/Delete buttons based on flags | 0.5 pts | python-backend-engineer |
| DOC-004 | Set up monitoring dashboard | Create Grafana dashboard for entity CRUD operations | - Dashboard tracks: Update/delete request rate, error rate, latency (P50/P95/P99)<br>- Alerts for high error rates (> 5%)<br>- Cascade check duration metric<br>- Dashboard accessible at Grafana /d/entity-crud | 0.5 pts | python-backend-engineer |
| DOC-005 | Deployment and smoke testing | Deploy to staging, run smoke tests, then deploy to production | - Deploy to staging with feature flags OFF<br>- Enable flags and test critical workflows<br>- Monitor for errors/performance issues<br>- Deploy to production with flags OFF initially<br>- Gradually enable flags for users | 0.5 pts | python-backend-engineer |

**Files Modified**:
- `/docs/api/catalog-endpoints.md` - API documentation
- `/docs/guides/entity-management.md` - NEW user guide
- `/apps/api/dealbrain_api/settings.py` - Add feature flag settings
- `/infra/grafana/dashboards/entity-crud.json` - NEW dashboard config

**Quality Gates**:
- [ ] OpenAPI spec validates successfully
- [ ] User guide reviewed and approved
- [ ] Feature flags tested in staging
- [ ] Monitoring dashboard shows accurate metrics
- [ ] Deployment checklist completed

### Success Criteria

- ✅ API documentation complete and published
- ✅ User guide accessible to administrators
- ✅ Feature flags enable gradual rollout
- ✅ Monitoring dashboard tracks CRUD operations
- ✅ Successful deployment to production with zero downtime

---

## Risk Mitigation

### Technical Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Accidental data loss from deletions | High | - Implement cascade checks blocking in-use entities<br>- Require confirmation with name typing<br>- Add feature flags for gradual rollout |
| Unique constraint violations on update | Medium | - Validate constraints in service layer before DB update<br>- Return clear error messages<br>- Add integration tests for duplicate scenarios |
| Performance issues with cascade checks | Medium | - Use COUNT(*) queries, not loading full listings<br>- Add indexes on foreign key columns<br>- Cache "Used In" counts with 5-minute TTL |
| Concurrent update conflicts | Low | - Use database transactions<br>- Consider optimistic locking (phase 2) |
| UI complexity from 7 entity types | Low | - Reuse EntityEditModal and EntityDeleteDialog<br>- Use entity-specific form schemas<br>- Progressive disclosure for advanced fields |

### Schedule Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Backend delays blocking frontend work | Medium | - Parallelize Phase 3 with Phases 1-2<br>- Start Phase 6 (new views) after Phases 1-2 only |
| Testing uncovers major issues | Medium | - Allocate buffer in Phase 8<br>- Prioritize critical path (UPDATE/DELETE) over nice-to-haves |
| FieldRegistry registration issues | Low | - Phase 3 is independent and low-risk<br>- Test with existing Listing/CPU patterns |

---

## Resource Requirements

### Team Composition

**Backend Development**:
- python-backend-engineer (primary) - 12 story points
- backend-architect (supporting) - 4 story points
- data-layer-expert (supporting) - 4 story points

**Frontend Development**:
- ui-engineer-enhanced (primary) - 18 story points
- frontend-developer (supporting) - 14 story points

**QA & Documentation**:
- testing specialists - 3 story points
- documentation-writer - 2 story points

### Infrastructure Requirements

- Staging environment for testing
- Feature flag system (environment variables)
- Grafana dashboard for monitoring
- CI/CD pipeline for automated testing

---

## Success Metrics

### Delivery Metrics

- ✅ All 9 phases completed on schedule (61 story points over 3 sprints)
- ✅ Zero production incidents from new CRUD operations
- ✅ Feature flags enable gradual rollout with zero downtime

### Business Metrics

- ✅ 80% reduction in support requests for "fix my entity" issues (tracked via support tickets)
- ✅ 50% reduction in database clutter from duplicates (entity count audit)
- ✅ 100% of catalog data auditable via UI (no manual DB access needed)

### Technical Metrics

- ✅ Update operations complete in < 500ms (P95)
- ✅ Delete cascade checks complete in < 1s (P95)
- ✅ > 90% backend test coverage for CRUD operations
- ✅ > 75% frontend test coverage for new components
- ✅ Zero listing orphans from delete operations
- ✅ WCAG AA compliant UI

### User Experience Metrics

- ✅ Time to fix entity typo: 60 seconds (down from "impossible")
- ✅ Time to delete duplicate entity: 30 seconds (down from "manual DB access")
- ✅ User satisfaction score: > 4.5/5 for entity management workflows

---

## Communication Plan

### Status Reporting

- **Daily Standups**: Quick progress updates on current phase
- **Weekly Status Report**: Phase completion, blockers, upcoming work
- **Phase Completion Reviews**: Demo completed functionality to stakeholders

### Escalation Path

- **Blocker**: Notify tech lead immediately
- **Schedule Risk**: Escalate to project manager within 24 hours
- **Scope Change**: Requires stakeholder approval before proceeding

---

## Post-Implementation Plan

### Monitoring

- **OpenTelemetry Spans**: All CRUD operations instrumented
- **Prometheus Metrics**: Request rate, error rate, latency (P50/P95/P99)
- **Grafana Dashboard**: Entity CRUD Operations (entity-crud.json)
- **Alerts**: High error rate (> 5%), slow cascade checks (> 2s)

### Maintenance

- **Quarterly Review**: Audit entity data quality, review delete patterns
- **Performance Tuning**: Optimize slow queries identified in telemetry
- **User Feedback**: Collect feedback on entity management workflows

### Future Enhancements (Phase 2)

- Soft delete with is_active flag for recoverability
- Audit trail UI showing update/delete history per entity
- Bulk operations (bulk delete, bulk update)
- Entity versioning and rollback capability
- Advanced cascade options (reassign listings on delete)
- Role-based access control for destructive operations

---

## Appendix: File Reference

### Backend Files

**API Layer**:
- `/apps/api/dealbrain_api/api/catalog.py` - UPDATE/DELETE endpoints
- `/apps/api/dealbrain_api/api/field_data.py` - Fields-data generic CRUD

**Service Layer**:
- `/apps/api/dealbrain_api/services/field_registry.py` - Entity registration
- `/apps/api/dealbrain_api/services/catalog.py` - "Used In" count methods (new)

**Schema Layer**:
- `/apps/api/dealbrain_api/schemas/catalog.py` - CPUUpdate, GPUUpdate, etc. schemas

**Tests**:
- `/tests/test_catalog_api.py` - Integration tests for CRUD
- `/tests/test_field_registry.py` - Unit tests for registration

### Frontend Files

**Pages**:
- `/apps/web/app/catalog/cpus/[id]/page.tsx` - CPU detail (enhanced)
- `/apps/web/app/catalog/gpus/[id]/page.tsx` - GPU detail (enhanced)
- `/apps/web/app/catalog/ram-specs/[id]/page.tsx` - RamSpec detail (enhanced)
- `/apps/web/app/catalog/storage-profiles/[id]/page.tsx` - StorageProfile detail (enhanced)
- `/apps/web/app/catalog/ports-profiles/[id]/page.tsx` - NEW PortsProfile detail
- `/apps/web/app/catalog/profiles/[id]/page.tsx` - NEW Profile detail
- `/apps/web/app/global-fields/page.tsx` - Global fields page (enhanced)

**Components**:
- `/apps/web/components/entity/entity-edit-modal.tsx` - NEW reusable edit modal
- `/apps/web/components/entity/entity-delete-dialog.tsx` - NEW reusable delete dialog
- `/apps/web/components/catalog/cpu-detail-layout.tsx` - Enhanced with Edit/Delete
- `/apps/web/components/catalog/gpu-detail-layout.tsx` - Enhanced with Edit/Delete
- `/apps/web/components/catalog/ram-spec-detail-layout.tsx` - Enhanced with Edit/Delete
- `/apps/web/components/catalog/storage-profile-detail-layout.tsx` - Enhanced with Edit/Delete
- `/apps/web/components/catalog/ports-profile-detail-layout.tsx` - NEW layout
- `/apps/web/components/catalog/profile-detail-layout.tsx` - NEW layout
- `/apps/web/components/custom-fields/global-fields-workspace.tsx` - Enhanced entity list
- `/apps/web/components/custom-fields/global-fields-data-tab.tsx` - Enhanced data grids

**Hooks & Utils**:
- `/apps/web/hooks/use-entity-mutations.ts` - NEW React Query mutations (update, delete)
- `/apps/web/lib/schemas/entity-schemas.ts` - NEW Zod validation schemas

**Tests**:
- `/apps/web/components/**/__tests__/` - Component tests
- `/apps/web/tests/e2e/` - E2E tests (Playwright or Cypress)

---

**End of Implementation Plan**

**Next Steps**:
1. Review and approve implementation plan with tech lead
2. Set up progress tracking: `.claude/progress/entity-detail-views-v1/all-phases-progress.md`
3. Assign developers to phases
4. Begin Phase 1: Backend CRUD - UPDATE Endpoints
