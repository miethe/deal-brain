# Entity Detail Views V1 - All Phases Progress

**PRD**: `/mnt/containers/deal-brain/docs/project_plans/PRDs/enhancements/entity-detail-views-v1.md`
**Implementation Plan**: `/mnt/containers/deal-brain/docs/project_plans/implementation_plans/enhancements/entity-detail-views-v1.md`
**Last Updated**: 2025-11-13

## Phase Overview

| Phase | Title | Status | Effort | Tasks | Complete |
|-------|-------|--------|--------|-------|----------|
| 1 | Backend CRUD - UPDATE Endpoints | ✅ COMPLETE | 8 pts | 8 | 8/8 |
| 2 | Backend CRUD - DELETE Endpoints | ✅ COMPLETE | 8 pts | 8 | 8/8 |
| 3 | FieldRegistry Expansion | NOT STARTED | 5 pts | 6 | 0/6 |
| 4 | Frontend Edit UI | 🔄 IN PROGRESS | 8 pts | 8 | 2/8 |
| 5 | Frontend Delete UI | NOT STARTED | 8 pts | 8 | 0/8 |
| 6 | New Detail Views (PortsProfile, Profile) | NOT STARTED | 8 pts | 6 | 0/6 |
| 7 | Global Fields Integration | NOT STARTED | 8 pts | 7 | 0/7 |
| 8 | Testing & Validation | NOT STARTED | 5 pts | 5 | 0/5 |
| 9 | Documentation & Deployment | NOT STARTED | 3 pts | 4 | 0/4 |
| **TOTAL** | | | **61 pts** | **60** | **18/60** |

---

## Phase 1: Backend CRUD - UPDATE Endpoints

**Status**: ✅ COMPLETE
**Duration**: 3 days | **Effort**: 8 story points
**Dependencies**: None
**Assigned**: python-backend-engineer, backend-architect
**Last Updated**: 2025-11-12

### Objective
Add PUT and PATCH endpoints to catalog API for updating all 6 catalog entities.

### Quality Gates
- [x] All UPDATE endpoints return 200 OK with updated entity
- [x] Unique constraint violations return 422 Unprocessable Entity
- [x] PATCH merges attributes_json correctly (doesn't overwrite)
- [x] Integration tests pass with 100% coverage
- [x] OpenTelemetry spans created for all UPDATE operations

### Tasks (8/8 Complete)

#### UP-001: Add CPU UPDATE endpoints
**Status**: ✅ COMPLETE | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add `PUT /v1/catalog/cpus/{id}` and `PATCH /v1/catalog/cpus/{id}` endpoints to catalog API

**Acceptance Criteria**:
- [x] PUT accepts full CPUUpdate schema
- [x] PATCH accepts partial CPUUpdate schema
- [x] Returns updated CPU DTO
- [x] Validates unique constraints
- [x] Updates modified_at timestamp

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`, `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/catalog.py`

---

#### UP-002: Add GPU UPDATE endpoints
**Status**: ✅ COMPLETE | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add `PUT/PATCH /v1/catalog/gpus/{id}` endpoints

**Acceptance Criteria**:
- [x] Same as UP-001 for GPU entity
- [x] Validates unique GPU name

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`, `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/catalog.py`

---

#### UP-003: Add RamSpec UPDATE endpoints
**Status**: ✅ COMPLETE | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add `PUT/PATCH /v1/catalog/ram-specs/{id}` endpoints

**Acceptance Criteria**:
- [x] Same as UP-001 for RamSpec
- [x] Validates unique constraint on (ddr_generation, speed_mhz, module_count, capacity_per_module_gb)

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`, `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/catalog.py`

---

#### UP-004: Add StorageProfile UPDATE endpoints
**Status**: ✅ COMPLETE | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add `PUT/PATCH /v1/catalog/storage-profiles/{id}` endpoints

**Acceptance Criteria**:
- [x] Same as UP-001 for StorageProfile
- [x] Validates unique constraint on (medium, interface, form_factor, capacity_gb)

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`, `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/catalog.py`

---

#### UP-005: Add PortsProfile UPDATE endpoints
**Status**: ✅ COMPLETE | **Estimate**: 1.5 pts | **Assigned**: python-backend-engineer, backend-architect

**Description**: Add `PUT/PATCH /v1/catalog/ports-profiles/{id}` endpoints

**Acceptance Criteria**:
- [x] Same as UP-001 for PortsProfile
- [x] Updates related Port entities if provided
- [x] Maintains referential integrity

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`, `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/catalog.py`

---

#### UP-006: Add Profile UPDATE endpoints
**Status**: ✅ COMPLETE | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add `PUT/PATCH /v1/catalog/profiles/{id}` endpoints

**Acceptance Criteria**:
- [x] Same as UP-001 for Profile (scoring)
- [x] Validates weights_json schema
- [x] Prevents removing is_default from only default profile

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`, `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/catalog.py`

---

#### UP-007: Create Update Pydantic schemas
**Status**: ✅ COMPLETE | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Create `CPUUpdate`, `GPUUpdate`, `RamSpecUpdate`, etc. schemas for request validation

**Acceptance Criteria**:
- [x] Schemas allow partial updates (all fields optional)
- [x] Include validation rules (min/max, regex)
- [x] Support attributes_json merging

**Files**: `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/catalog.py`

---

#### UP-008: Add UPDATE integration tests
**Status**: ✅ COMPLETE | **Estimate**: 1.5 pts | **Assigned**: python-backend-engineer

**Description**: Write integration tests for all UPDATE endpoints

**Acceptance Criteria**:
- [x] Test successful full update (PUT)
- [x] Test successful partial update (PATCH)
- [x] Test unique constraint validation
- [x] Test 404 for non-existent entity
- [x] Test 422 for invalid input

**Files**: `/mnt/containers/deal-brain/tests/test_catalog_api.py`

---

### Phase 1 Completion Summary

**Completed**: 2025-11-12
**Total Effort**: 8 story points
**Commit**: 9371bcb

**Deliverables:**
- 6 Update Pydantic schemas (CpuUpdate, GpuUpdate, RamSpecUpdate, StorageProfileUpdate, PortsProfileUpdate, ProfileUpdate)
- 12 UPDATE endpoints (PUT and PATCH for each entity)
- 32 integration tests
- OpenTelemetry instrumentation
- Comprehensive validation

**Files Modified:**
- `/apps/api/dealbrain_api/api/catalog.py` - Added UPDATE endpoints
- `/packages/core/dealbrain_core/schemas/catalog.py` - Added Update schemas
- `/packages/core/dealbrain_core/schemas/__init__.py` - Exported Update schemas
- `/tests/test_catalog_api.py` - Added integration tests

**Next Phase**: Phase 2 (Backend CRUD - DELETE Endpoints)

---

## Phase 2: Backend CRUD - DELETE Endpoints

**Status**: ✅ COMPLETE
**Duration**: 3 days | **Effort**: 8 story points
**Dependencies**: Phase 1 (same files being modified)
**Assigned**: python-backend-engineer, data-layer-expert
**Last Updated**: 2025-11-12

### Objective
Add DELETE endpoints with cascade validation to prevent orphaning listings.

### Quality Gates
- [x] DELETE endpoints return 204 No Content for unused entities
- [x] DELETE endpoints return 409 Conflict with usage count for entities in use
- [x] Cascade checks complete in < 1s (measured via OpenTelemetry)
- [x] Zero listing orphans after delete operations
- [x] Integration tests pass with 100% coverage

### Tasks (8/8 Complete)

#### DEL-001: Implement "Used In" count service
**Status**: ✅ COMPLETE | **Estimate**: 1.5 pts | **Assigned**: data-layer-expert, python-backend-engineer

**Description**: Create service method to count listings using each entity type

**Acceptance Criteria**:
- [x] `get_cpu_usage_count(cpu_id)` returns listing count
- [x] Similar methods for GPU, RamSpec, StorageProfile, PortsProfile, Profile
- [x] Uses COUNT(*) query (not loading full listings)
- [x] Query completes in < 500ms

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/catalog.py`

---

#### DEL-002: Add CPU DELETE endpoint
**Status**: ✅ COMPLETE | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add `DELETE /v1/catalog/cpus/{id}` with cascade check

**Acceptance Criteria**:
- [x] Returns 204 No Content on success
- [x] Returns 409 Conflict if CPU in use (includes count in error)
- [x] Hard deletes entity from database
- [x] Cascade check completes in < 1s

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`

---

#### DEL-003: Add GPU DELETE endpoint
**Status**: ✅ COMPLETE | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add `DELETE /v1/catalog/gpus/{id}` with cascade check

**Acceptance Criteria**:
- [x] Same as DEL-002 for GPU entity

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`

---

#### DEL-004: Add RamSpec DELETE endpoint
**Status**: ✅ COMPLETE | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add `DELETE /v1/catalog/ram-specs/{id}` with cascade check

**Acceptance Criteria**:
- [x] Same as DEL-002 for RamSpec
- [x] Checks both primary_ram_spec_id and secondary_ram_spec_id usage

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`

---

#### DEL-005: Add StorageProfile DELETE endpoint
**Status**: ✅ COMPLETE | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add `DELETE /v1/catalog/storage-profiles/{id}` with cascade check

**Acceptance Criteria**:
- [x] Same as DEL-002 for StorageProfile
- [x] Checks both primary_storage_profile_id and secondary_storage_profile_id usage

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`

---

#### DEL-006: Add PortsProfile DELETE endpoint
**Status**: ✅ COMPLETE | **Estimate**: 1.5 pts | **Assigned**: python-backend-engineer, data-layer-expert

**Description**: Add `DELETE /v1/catalog/ports-profiles/{id}` with cascade check

**Acceptance Criteria**:
- [x] Same as DEL-002 for PortsProfile
- [x] Cascade deletes related Port entities

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`

---

#### DEL-007: Add Profile DELETE endpoint
**Status**: ✅ COMPLETE | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add `DELETE /v1/catalog/profiles/{id}` with cascade check

**Acceptance Criteria**:
- [x] Same as DEL-002 for Profile (scoring)
- [x] Prevents deleting is_default=True profile if only default

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`

---

#### DEL-008: Add DELETE integration tests
**Status**: ✅ COMPLETE | **Estimate**: 2 pts | **Assigned**: python-backend-engineer

**Description**: Write integration tests for all DELETE endpoints

**Acceptance Criteria**:
- [x] Test successful delete of unused entity
- [x] Test 409 Conflict when entity in use
- [x] Test 404 for non-existent entity
- [x] Test cascade delete of related entities (PortsProfile → Ports)
- [x] Test error message includes usage count

**Files**: `/mnt/containers/deal-brain/tests/test_catalog_api.py`

---

### Phase 2 Completion Summary

**Completed**: 2025-11-12
**Total Effort**: 8 story points
**Commit**: ddd23d0

**Deliverables:**
- 6 usage count service methods (get_{entity}_usage_count)
- 6 DELETE endpoints with cascade validation
- 26 integration tests
- Cascade validation prevents orphaning listings
- Special handling for Profile default protection and PortsProfile cascade

**Files Modified:**
- `/apps/api/dealbrain_api/api/catalog.py` - Added DELETE endpoints
- `/apps/api/dealbrain_api/services/catalog.py` - NEW: Created usage count service
- `/tests/test_catalog_api.py` - Added DELETE integration tests
- `/tests/services/test_catalog.py` - NEW: Service layer tests

**Bug Fixes:**
- Fixed POST endpoints to properly map attributes → attributes_json for CPU, GPU, PortsProfile

**Next Phase**: Phase 3 (FieldRegistry Expansion)

---

## Phase 3: FieldRegistry Expansion

**Status**: NOT STARTED
**Duration**: 2 days | **Effort**: 5 story points
**Dependencies**: None (parallel with Phases 1-2)
**Assigned**: python-backend-engineer, backend-architect

### Objective
Register GPU, RamSpec, StorageProfile, PortsProfile, Profile in FieldRegistry to enable unified management.

### Quality Gates
- [ ] All 7 entities returned by GET /v1/fields-data/entities
- [ ] Schema endpoints return correct core + custom fields for each entity
- [ ] Create/update operations work via fields-data API for new entities
- [ ] Unit tests verify registration metadata correctness

### Tasks (0/6 Complete)

#### REG-001: Register GPU in FieldRegistry
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add GPU entity registration to FieldRegistry with core fields mapping

**Acceptance Criteria**:
- [ ] `FieldRegistry.register("gpu", Gpu)` called on init
- [ ] Core fields mapped: name, manufacturer, gpu_mark, metal_score, notes
- [ ] attributes_json mapped for custom fields
- [ ] GET /v1/fields-data/gpu/schema returns complete schema

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/field_registry.py`

---

#### REG-002: Register RamSpec in FieldRegistry
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add RamSpec entity registration with core fields mapping

**Acceptance Criteria**:
- [ ] Similar to REG-001
- [ ] Core fields: label, ddr_generation, speed_mhz, module_count, capacity_per_module_gb, total_capacity_gb, notes

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/field_registry.py`

---

#### REG-003: Register StorageProfile in FieldRegistry
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add StorageProfile entity registration with core fields mapping

**Acceptance Criteria**:
- [ ] Similar to REG-001
- [ ] Core fields: label, medium, interface, form_factor, capacity_gb, performance_tier, notes

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/field_registry.py`

---

#### REG-004: Register PortsProfile in FieldRegistry
**Status**: NOT STARTED | **Estimate**: 1.5 pts | **Assigned**: python-backend-engineer, backend-architect

**Description**: Add PortsProfile entity registration with core fields mapping

**Acceptance Criteria**:
- [ ] Similar to REG-001
- [ ] Core fields: name, description
- [ ] Handle nested Port entities (related objects)
- [ ] Support creating/updating ports with profile

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/field_registry.py`

---

#### REG-005: Register Profile in FieldRegistry
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Add Profile (scoring) entity registration with core fields mapping

**Acceptance Criteria**:
- [ ] Similar to REG-001
- [ ] Core fields: name, description, is_default, weights_json, rule_group_weights
- [ ] Validate weights_json schema on create/update

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/field_registry.py`

---

#### REG-006: Update GET /v1/fields-data/entities
**Status**: NOT STARTED | **Estimate**: 0.5 pts | **Assigned**: python-backend-engineer

**Description**: Ensure new entities appear in entities list endpoint

**Acceptance Criteria**:
- [ ] GET /v1/fields-data/entities returns all 7 entities
- [ ] Response includes: id, name, label, field count

**Files**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/field_data.py`

---

## Phase 4: Frontend Edit UI

**Status**: IN PROGRESS
**Duration**: 3 days | **Effort**: 8 story points
**Dependencies**: Phase 1 (UPDATE endpoints), Phase 3 (FieldRegistry for schemas)
**Assigned**: ui-engineer-enhanced, frontend-developer

### Objective
Add Edit buttons and modals to existing detail views (CPU, GPU, RamSpec, StorageProfile).

### Quality Gates
- [x] Edit modal opens with current entity data pre-filled
- [x] Form validation prevents invalid submissions
- [ ] Successful edit updates UI and shows success toast
- [ ] Error responses show clear error messages
- [ ] Component tests verify modal behavior
- [x] Accessibility: Modal keyboard navigable, screen reader friendly

### Tasks (2/8 Complete)

#### EDIT-001: Create EntityEditModal component
**Status**: ✅ COMPLETE | **Estimate**: 2 pts | **Assigned**: ui-engineer-enhanced | **Completed**: 2025-11-13

**Description**: Create reusable modal component accepting entity schema and onSubmit callback

**Acceptance Criteria**:
- [x] Generic modal accepts: entityType, entityId, initialValues, schema, onSubmit
- [x] Uses React Hook Form with Zod validation (@hookform/resolvers/zod)
- [x] Pre-populates form with initialValues
- [x] Shows inline validation errors
- [x] Disables submit until valid
- [x] Calls PATCH endpoint on submit (via onSubmit callback)
- [x] Keyboard accessible (Tab, Enter, Esc)
- [x] Screen reader friendly with proper ARIA labels
- [x] Supports different field types (text, number, textarea, select)

**Files Created**:
- `/apps/web/components/entity/entity-edit-modal.tsx` - Generic modal component with entity-specific form fields
- `/apps/web/components/entity/index.ts` - Barrel export

**Implementation Notes**:
- Uses ModalShell for consistent modal appearance
- Separate form field components for each entity type (CPUFormFields, GPUFormFields, etc.)
- Controller from react-hook-form for Select components
- Inline validation with error messages
- Submit button disabled when form invalid or submitting
- Prevents closing modal while submitting

---

#### EDIT-002: Create entity-specific edit forms
**Status**: ✅ COMPLETE | **Estimate**: 1.5 pts | **Assigned**: ui-engineer-enhanced | **Completed**: 2025-11-13

**Description**: Create form schemas for CPU, GPU, RamSpec, StorageProfile using Zod

**Acceptance Criteria**:
- [x] CPUEditSchema, GPUEditSchema, RamSpecEditSchema, StorageProfileEditSchema
- [x] Map to backend Update schemas (all fields optional for PATCH)
- [x] Include validation rules (required, min/max, regex)
- [x] Support attributes as dynamic fields (maps to attributes_json in backend)
- [x] PortsProfileEditSchema, ProfileEditSchema (basic structure)

**Files Created**:
- `/apps/web/lib/schemas/entity-schemas.ts` - All entity edit schemas with validation

**Schemas Implemented**:
1. **cpuEditSchema**: name, manufacturer, socket, cores, threads, tdp_w, igpu_model, cpu_mark_multi, cpu_mark_single, igpu_mark, release_year, notes, passmark fields, attributes
2. **gpuEditSchema**: name, manufacturer, gpu_mark, metal_score, notes, attributes
3. **ramSpecEditSchema**: label, ddr_generation (enum), speed_mhz, module_count, capacity_per_module_gb, total_capacity_gb, notes, attributes
4. **storageProfileEditSchema**: label, medium (enum), interface, form_factor, capacity_gb, performance_tier, notes, attributes
5. **portsProfileEditSchema**: name, description, attributes (ports handled separately)
6. **profileEditSchema**: name, description, weights_json, is_default

**Validation Rules**:
- Cores: 1-256
- Threads: 1-512
- TDP: 1-1000W
- Release Year: 1970-2100
- Speed MHz: 0-10000
- Module Count: 1-8
- Capacity: 1-256GB per module, 1-2048GB total
- Storage Capacity: 1-100000GB (100TB)
- All benchmark scores: ≥ 0

**Enums Defined**:
- ddrGenerationEnum: ddr3, ddr4, ddr5, lpddr4, lpddr4x, lpddr5, lpddr5x, hbm2, hbm3, unknown
- storageMediumEnum: nvme, sata_ssd, hdd, hybrid, emmc, ufs, unknown
- storageInterfaceEnum: sata, nvme, pcie, usb, emmc
- storageFormFactorEnum: m2, 2.5, 3.5, pcie_card, emmc_embedded
- performanceTierEnum: budget, mainstream, performance, enthusiast

---

#### EDIT-003: Add Edit button to CPU detail layout
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Add "Edit" button to CPUDetailLayout opening EntityEditModal

**Acceptance Criteria**:
- [ ] Button in header next to breadcrumb
- [ ] Clicking opens modal pre-filled with current CPU data
- [ ] Successful edit shows success toast and refetches CPU detail
- [ ] Error shows error toast with message

**Files**: `/mnt/containers/deal-brain/apps/web/components/catalog/cpu-detail-layout.tsx`

---

#### EDIT-004: Add Edit button to GPU detail layout
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Add "Edit" button to GPUDetailLayout opening EntityEditModal

**Acceptance Criteria**:
- [ ] Same as EDIT-003 for GPU entity

**Files**: `/mnt/containers/deal-brain/apps/web/components/catalog/gpu-detail-layout.tsx`

---

#### EDIT-005: Add Edit button to RamSpec detail layout
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Add "Edit" button to RamSpecDetailLayout opening EntityEditModal

**Acceptance Criteria**:
- [ ] Same as EDIT-003 for RamSpec entity

**Files**: `/mnt/containers/deal-brain/apps/web/components/catalog/ram-spec-detail-layout.tsx`

---

#### EDIT-006: Add Edit button to StorageProfile detail layout
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Add "Edit" button to StorageProfileDetailLayout opening EntityEditModal

**Acceptance Criteria**:
- [ ] Same as EDIT-003 for StorageProfile entity

**Files**: `/mnt/containers/deal-brain/apps/web/components/catalog/storage-profile-detail-layout.tsx`

---

#### EDIT-007: Implement optimistic updates
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Use React Query's optimistic update pattern for instant UI feedback

**Acceptance Criteria**:
- [ ] UI updates immediately on submit
- [ ] Rolls back on error
- [ ] Refetches data to sync with server

**Files**: `/mnt/containers/deal-brain/apps/web/hooks/use-entity-mutations.ts` (NEW)

---

#### EDIT-008: Add success/error toast notifications
**Status**: NOT STARTED | **Estimate**: 0.5 pts | **Assigned**: frontend-developer

**Description**: Use toast library for user feedback on edit operations

**Acceptance Criteria**:
- [ ] Success toast: "CPU updated successfully"
- [ ] Error toast: Shows backend error message
- [ ] Toast auto-dismisses after 5s

**Files**: `/mnt/containers/deal-brain/apps/web/hooks/use-entity-mutations.ts`

---

## Phase 5: Frontend Delete UI

**Status**: NOT STARTED
**Duration**: 3 days | **Effort**: 8 story points
**Dependencies**: Phase 2 (DELETE endpoints), Phase 4 (Edit UI patterns)
**Assigned**: ui-engineer-enhanced, frontend-developer

### Objective
Add Delete buttons and confirmation dialogs to all detail views with "Used In" warnings.

### Quality Gates
- [ ] Delete dialog shows accurate "Used In" count
- [ ] Deletion blocked if entity has dependencies (409 Conflict)
- [ ] Confirmation requires typing entity name for in-use entities
- [ ] Successful delete redirects to entity list page
- [ ] Error messages clearly communicate why delete failed
- [ ] Accessibility: Dialog keyboard navigable, announces state changes

### Tasks (0/8 Complete)

#### DEL-UI-001: Create EntityDeleteDialog component
**Status**: NOT STARTED | **Estimate**: 2 pts | **Assigned**: ui-engineer-enhanced

**Description**: Create reusable confirmation dialog with "Used In" warning

**Acceptance Criteria**:
- [ ] Accepts: entityType, entityId, entityName, usedInCount, onConfirm
- [ ] Shows "Used In X Listings" badge
- [ ] Requires typing entity name if usedInCount > 0
- [ ] Disables confirm button until validation passes
- [ ] Calls DELETE endpoint on confirm

**Files**: `/mnt/containers/deal-brain/apps/web/components/entity/entity-delete-dialog.tsx` (NEW)

---

#### DEL-UI-002: Add "Used In" count to detail views
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Fetch and display listing count for each entity in detail header

**Acceptance Criteria**:
- [ ] Calls GET /v1/catalog/{entity}/{id}/listings with count=true
- [ ] Displays badge: "Used in 15 listings"
- [ ] Badge links to "Used In Listings" section on page
- [ ] Updates after edit operations

**Files**: All detail layout components

---

#### DEL-UI-003: Add Delete button to CPU detail layout
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Add "Delete" button to CPUDetailLayout opening EntityDeleteDialog

**Acceptance Criteria**:
- [ ] Button in header next to Edit button
- [ ] Button shows tooltip with "Used in X listings"
- [ ] Successful delete redirects to /catalog/cpus
- [ ] Error shows toast with "Cannot delete: CPU is used in X listings"

**Files**: `/mnt/containers/deal-brain/apps/web/components/catalog/cpu-detail-layout.tsx`

---

#### DEL-UI-004: Add Delete button to GPU detail layout
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Add "Delete" button to GPUDetailLayout opening EntityDeleteDialog

**Acceptance Criteria**:
- [ ] Same as DEL-UI-003 for GPU entity
- [ ] Redirects to /catalog/gpus

**Files**: `/mnt/containers/deal-brain/apps/web/components/catalog/gpu-detail-layout.tsx`

---

#### DEL-UI-005: Add Delete button to RamSpec detail layout
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Add "Delete" button to RamSpecDetailLayout opening EntityDeleteDialog

**Acceptance Criteria**:
- [ ] Same as DEL-UI-003 for RamSpec entity
- [ ] Redirects to /catalog/ram-specs

**Files**: `/mnt/containers/deal-brain/apps/web/components/catalog/ram-spec-detail-layout.tsx`

---

#### DEL-UI-006: Add Delete button to StorageProfile detail layout
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Add "Delete" button to StorageProfileDetailLayout opening EntityDeleteDialog

**Acceptance Criteria**:
- [ ] Same as DEL-UI-003 for StorageProfile entity
- [ ] Redirects to /catalog/storage-profiles

**Files**: `/mnt/containers/deal-brain/apps/web/components/catalog/storage-profile-detail-layout.tsx`

---

#### DEL-UI-007: Implement delete mutation with error handling
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Use React Query mutation for delete with 409 Conflict handling

**Acceptance Criteria**:
- [ ] DELETE mutation invalidates entity list cache
- [ ] 409 Conflict shows error toast with usage count
- [ ] 404 shows "Entity not found"
- [ ] Success redirects to entity list page

**Files**: `/mnt/containers/deal-brain/apps/web/hooks/use-entity-mutations.ts`

---

#### DEL-UI-008: Add confirmation step for in-use entities
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: ui-engineer-enhanced

**Description**: Require typing entity name to confirm deletion of entities with dependencies

**Acceptance Criteria**:
- [ ] If usedInCount > 0, dialog shows text input
- [ ] User must type exact entity name to enable confirm button
- [ ] Case-insensitive comparison
- [ ] Provides extra safety against accidental deletes

**Files**: `/mnt/containers/deal-brain/apps/web/components/entity/entity-delete-dialog.tsx`

---

## Phase 6: New Detail Views (PortsProfile, Profile)

**Status**: NOT STARTED
**Duration**: 3 days | **Effort**: 8 story points
**Dependencies**: Phase 1 (UPDATE endpoints), Phase 2 (DELETE endpoints)
**Assigned**: ui-engineer-enhanced, frontend-developer

### Objective
Create dedicated detail views for Ports Profile and Scoring Profile with Edit/Delete functionality.

### Quality Gates
- [ ] Detail pages load successfully with data from API
- [ ] Breadcrumb navigation works correctly
- [ ] Edit/Delete buttons function identically to existing detail views
- [ ] "Used In Listings" card shows correct listings
- [ ] 404 page shown for non-existent IDs
- [ ] Responsive design matches existing detail views

### Tasks (0/6 Complete)

#### VIEW-001: Create PortsProfile detail page
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Create `/app/catalog/ports-profiles/[id]/page.tsx` with server component

**Acceptance Criteria**:
- [ ] Fetches ports profile by ID from API
- [ ] Returns 404 page if not found
- [ ] Passes data to PortsProfileDetailLayout
- [ ] Uses existing page patterns (CPU/GPU detail)

**Files**: `/mnt/containers/deal-brain/apps/web/app/catalog/ports-profiles/[id]/page.tsx` (NEW)

---

#### VIEW-002: Create PortsProfileDetailLayout component
**Status**: NOT STARTED | **Estimate**: 2 pts | **Assigned**: ui-engineer-enhanced

**Description**: Create detail layout showing ports profile specs and used-in listings

**Acceptance Criteria**:
- [ ] Header with breadcrumb, Edit, Delete buttons
- [ ] "Specifications" card: name, description, attributes
- [ ] "Ports" card: table of ports (type, count, spec_notes)
- [ ] "Used In Listings" card with listing previews
- [ ] Uses EntityEditModal and EntityDeleteDialog

**Files**: `/mnt/containers/deal-brain/apps/web/components/catalog/ports-profile-detail-layout.tsx` (NEW)

---

#### VIEW-003: Create Profile (scoring) detail page
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Create `/app/catalog/profiles/[id]/page.tsx` with server component

**Acceptance Criteria**:
- [ ] Fetches scoring profile by ID from API
- [ ] Returns 404 page if not found
- [ ] Passes data to ProfileDetailLayout

**Files**: `/mnt/containers/deal-brain/apps/web/app/catalog/profiles/[id]/page.tsx` (NEW)

---

#### VIEW-004: Create ProfileDetailLayout component
**Status**: NOT STARTED | **Estimate**: 2 pts | **Assigned**: ui-engineer-enhanced

**Description**: Create detail layout showing scoring profile weights and used-in listings

**Acceptance Criteria**:
- [ ] Header with breadcrumb, Edit, Delete buttons
- [ ] "Profile Details" card: name, description, is_default badge
- [ ] "Scoring Weights" card: table visualizing weights_json
- [ ] "Rule Group Weights" card: table of rule priorities
- [ ] "Used In Listings" card
- [ ] Uses EntityEditModal and EntityDeleteDialog

**Files**: `/mnt/containers/deal-brain/apps/web/components/catalog/profile-detail-layout.tsx` (NEW)

---

#### VIEW-005: Add PortsProfile edit form
**Status**: NOT STARTED | **Estimate**: 1.5 pts | **Assigned**: ui-engineer-enhanced

**Description**: Create PortsProfileEditSchema and form component

**Acceptance Criteria**:
- [ ] Schema validates: name (required), description, attributes_json
- [ ] Form supports editing nested Port entities
- [ ] Add/remove port rows dynamically
- [ ] Validates port count > 0

**Files**: `/mnt/containers/deal-brain/apps/web/lib/schemas/entity-schemas.ts`, `/mnt/containers/deal-brain/apps/web/components/entity/entity-edit-modal.tsx`

---

#### VIEW-006: Add Profile edit form
**Status**: NOT STARTED | **Estimate**: 1.5 pts | **Assigned**: ui-engineer-enhanced

**Description**: Create ProfileEditSchema and form component

**Acceptance Criteria**:
- [ ] Schema validates: name (required), description, weights_json, rule_group_weights
- [ ] Weights UI shows sliders/inputs for each metric
- [ ] Validates weights sum to 1.0 (or 100%)
- [ ] Shows is_default toggle with warning

**Files**: `/mnt/containers/deal-brain/apps/web/lib/schemas/entity-schemas.ts`, `/mnt/containers/deal-brain/apps/web/components/entity/entity-edit-modal.tsx`

---

## Phase 7: Global Fields Integration

**Status**: NOT STARTED
**Duration**: 3 days | **Effort**: 8 story points
**Dependencies**: Phase 3 (FieldRegistry), Phase 4 (Edit UI), Phase 5 (Delete UI)
**Assigned**: ui-engineer-enhanced, frontend-developer

### Objective
Update GlobalFieldsWorkspace to show all 7 entities with full CRUD operations.

### Quality Gates
- [ ] All 7 entities appear in GlobalFieldsWorkspace sidebar
- [ ] Data grids load correctly for each entity
- [ ] Create/Edit modals work for all entity types
- [ ] Pagination handles large entity lists (1000+ items)
- [ ] Filtering and sorting work correctly
- [ ] "View Details" links navigate to correct detail pages

### Tasks (0/7 Complete)

#### GF-001: Update GlobalFieldsWorkspace entity list
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Fetch all 7 entities from GET /v1/fields-data/entities and display in sidebar

**Acceptance Criteria**:
- [ ] Sidebar shows: Listing, CPU, GPU, RAM Spec, Storage Profile, Ports Profile, Scoring Profile
- [ ] Each entity has icon and label
- [ ] Active entity highlighted
- [ ] Clicking entity loads data grid

**Files**: `/mnt/containers/deal-brain/apps/web/components/custom-fields/global-fields-workspace.tsx`

---

#### GF-002: Add GPU to GlobalFieldsDataTab
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Enable GPU entity data grid in GlobalFieldsDataTab

**Acceptance Criteria**:
- [ ] Grid shows GPU columns: Name, Manufacturer, GPU Mark, Metal Score, Actions
- [ ] "Add Entry" button opens GPU create modal
- [ ] Row "Edit" action opens GPU edit modal
- [ ] Data fetched from GET /v1/fields-data/gpu/records

**Files**: `/mnt/containers/deal-brain/apps/web/components/custom-fields/global-fields-data-tab.tsx`

---

#### GF-003: Add RamSpec to GlobalFieldsDataTab
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Enable RamSpec entity data grid

**Acceptance Criteria**:
- [ ] Grid shows: Label, DDR Gen, Speed, Capacity, Actions
- [ ] Create/Edit modals for RamSpec

**Files**: `/mnt/containers/deal-brain/apps/web/components/custom-fields/global-fields-data-tab.tsx`

---

#### GF-004: Add StorageProfile to GlobalFieldsDataTab
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Enable StorageProfile entity data grid

**Acceptance Criteria**:
- [ ] Grid shows: Label, Medium, Interface, Form Factor, Capacity, Actions
- [ ] Create/Edit modals for StorageProfile

**Files**: `/mnt/containers/deal-brain/apps/web/components/custom-fields/global-fields-data-tab.tsx`

---

#### GF-005: Add PortsProfile to GlobalFieldsDataTab
**Status**: NOT STARTED | **Estimate**: 1.5 pts | **Assigned**: ui-engineer-enhanced

**Description**: Enable PortsProfile entity data grid

**Acceptance Criteria**:
- [ ] Grid shows: Name, Description, Port Count, Actions
- [ ] Create/Edit modals for PortsProfile (with nested ports)
- [ ] "View Details" action links to /catalog/ports-profiles/{id}

**Files**: `/mnt/containers/deal-brain/apps/web/components/custom-fields/global-fields-data-tab.tsx`

---

#### GF-006: Add Profile to GlobalFieldsDataTab
**Status**: NOT STARTED | **Estimate**: 1.5 pts | **Assigned**: ui-engineer-enhanced

**Description**: Enable Profile (scoring) entity data grid

**Acceptance Criteria**:
- [ ] Grid shows: Name, Description, Is Default, Actions
- [ ] Create/Edit modals for Profile
- [ ] "View Details" action links to /catalog/profiles/{id}

**Files**: `/mnt/containers/deal-brain/apps/web/components/custom-fields/global-fields-data-tab.tsx`

---

#### GF-007: Update GlobalFieldsDataTab to support all entities
**Status**: NOT STARTED | **Estimate**: 2 pts | **Assigned**: ui-engineer-enhanced, frontend-developer

**Description**: Refactor data grid to dynamically render based on entity schema

**Acceptance Criteria**:
- [ ] Single data grid component handles all entity types
- [ ] Columns generated from entity schema
- [ ] Create/Edit modals use entity-specific forms
- [ ] Pagination, filtering, sorting work for all entities

**Files**: `/mnt/containers/deal-brain/apps/web/components/custom-fields/global-fields-data-tab.tsx`

---

## Phase 8: Testing & Validation

**Status**: NOT STARTED
**Duration**: 2 days | **Effort**: 5 story points
**Dependencies**: Phase 7 (all features complete)
**Assigned**: python-backend-engineer, frontend-developer, ui-engineer-enhanced

### Objective
Comprehensive testing of all CRUD operations and user workflows.

### Quality Gates
- [ ] All backend integration tests pass in CI
- [ ] All frontend component tests pass
- [ ] E2E tests cover critical user workflows
- [ ] Performance metrics meet targets (< 500ms update, < 1s delete, < 2s list load)
- [ ] Accessibility audit passes WCAG AA compliance

### Tasks (0/5 Complete)

#### TEST-001: Backend integration tests
**Status**: NOT STARTED | **Estimate**: 1.5 pts | **Assigned**: python-backend-engineer

**Description**: Ensure all CRUD endpoints have full integration test coverage

**Acceptance Criteria**:
- [ ] Update tests: PUT/PATCH success, validation errors, unique constraints
- [ ] Delete tests: Success, cascade blocked, 404 not found
- [ ] Coverage > 90% for catalog API
- [ ] All tests pass in CI pipeline

**Files**: `/mnt/containers/deal-brain/tests/test_catalog_api.py`

---

#### TEST-002: Frontend component tests
**Status**: NOT STARTED | **Estimate**: 1.5 pts | **Assigned**: frontend-developer, ui-engineer-enhanced

**Description**: Write component tests for new UI components

**Acceptance Criteria**:
- [ ] EntityEditModal tests: Opens, validates, submits, cancels
- [ ] EntityDeleteDialog tests: Confirmation flow, "Used In" handling
- [ ] Detail layout tests: Renders, Edit/Delete buttons work
- [ ] Coverage > 75% for new components

**Files**: `/mnt/containers/deal-brain/apps/web/components/entity/*.test.tsx` (NEW)

---

#### TEST-003: End-to-end user workflow tests
**Status**: NOT STARTED | **Estimate**: 1.5 pts | **Assigned**: frontend-developer

**Description**: Write E2E tests covering critical user stories

**Acceptance Criteria**:
- [ ] US-1: Edit entity specification (success and validation errors)
- [ ] US-2: Delete unused entity (confirmation and redirect)
- [ ] US-3: Attempt delete entity in use (blocked with error)
- [ ] US-4: Manage entities from /global-fields (create, edit, view details)
- [ ] Tests run in Playwright/Cypress

**Files**: `/mnt/containers/deal-brain/tests/e2e/entity-crud.spec.ts` (NEW)

---

#### TEST-004: Performance validation
**Status**: NOT STARTED | **Estimate**: 0.5 pts | **Assigned**: python-backend-engineer

**Description**: Validate performance metrics meet targets

**Acceptance Criteria**:
- [ ] Update operations complete in < 500ms (measure with OpenTelemetry)
- [ ] Delete cascade checks complete in < 1s
- [ ] Entity list queries return < 2s for 10,000+ entities
- [ ] Document performance metrics in test report

**Files**: Performance testing scripts, OpenTelemetry dashboard

---

#### TEST-005: Accessibility audit
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: ui-engineer-enhanced

**Description**: Run accessibility audit on all new UI components

**Acceptance Criteria**:
- [ ] WCAG AA compliance verified with axe DevTools
- [ ] Keyboard navigation tested (Tab, Enter, Esc)
- [ ] Screen reader tested with NVDA/VoiceOver
- [ ] Focus management correct in modals/dialogs
- [ ] Document accessibility issues and fixes

**Files**: Accessibility audit report

---

## Phase 9: Documentation & Deployment

**Status**: NOT STARTED
**Duration**: 1 day | **Effort**: 3 story points
**Dependencies**: Phase 8 (testing complete)
**Assigned**: python-backend-engineer, frontend-developer

### Objective
Document new features and deploy with feature flags.

### Quality Gates
- [ ] API documentation updated with new endpoints
- [ ] User guide created for entity management workflows
- [ ] Deployment completed successfully
- [ ] Monitoring dashboards operational

### Tasks (0/4 Complete)

#### DOC-001: Update API documentation
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: python-backend-engineer

**Description**: Document all new CRUD endpoints in API docs

**Acceptance Criteria**:
- [ ] UPDATE endpoints documented with request/response examples
- [ ] DELETE endpoints documented with cascade behavior
- [ ] Error codes documented (404, 409, 422)
- [ ] OpenAPI spec updated

**Files**: API documentation (Swagger/OpenAPI)

---

#### DOC-002: Create user guide for entity management
**Status**: NOT STARTED | **Estimate**: 1 pt | **Assigned**: frontend-developer

**Description**: Write user guide explaining entity CRUD workflows

**Acceptance Criteria**:
- [ ] Guide covers: Creating entities, editing entities, deleting entities
- [ ] Screenshots of /global-fields workspace and detail views
- [ ] Explains "Used In Listings" validation
- [ ] Published to user documentation site

**Files**: `/mnt/containers/deal-brain/docs/guides/entity-management.md` (NEW)

---

#### DOC-003: Deploy to production
**Status**: NOT STARTED | **Estimate**: 0.5 pts | **Assigned**: python-backend-engineer

**Description**: Deploy backend and frontend changes to production

**Acceptance Criteria**:
- [ ] Database migrations applied successfully
- [ ] Backend deployed with zero downtime
- [ ] Frontend deployed and accessible
- [ ] Smoke tests pass in production

**Files**: Deployment scripts, CI/CD pipelines

---

#### DOC-004: Setup monitoring dashboards
**Status**: NOT STARTED | **Estimate**: 0.5 pts | **Assigned**: python-backend-engineer

**Description**: Create Grafana dashboards for entity CRUD operations

**Acceptance Criteria**:
- [ ] Dashboard shows: Update latency, Delete latency, Cascade check duration
- [ ] Alert created for slow operations (> 1s)
- [ ] Error rate tracking for 409 Conflicts, 422 Validation errors
- [ ] Dashboard linked in documentation

**Files**: Grafana dashboard configs

---

## Next Actions

**To Start Phase 1**:
1. Review current catalog API structure: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`
2. Review existing schemas: `/mnt/containers/deal-brain/apps/api/dealbrain_api/schemas/catalog.py`
3. Identify pattern from existing POST endpoints to replicate for PUT/PATCH
4. Begin with UP-001 (CPU UPDATE endpoints) as reference implementation

**Critical Dependencies to Verify**:
- Database models support updates (no immutable constraints)
- Unique constraints defined correctly in SQLAlchemy models
- Foreign key relationships configured for cascade checks

**Blockers**:
- None currently identified

**Questions for PM/Design**:
- Confirm soft delete vs hard delete preference (currently defaulting to hard delete)
- Confirm PUT vs PATCH preference for UI (currently using PATCH)
- Confirm "type entity name" confirmation only for in-use entities (currently yes)
