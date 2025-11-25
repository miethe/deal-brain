---
title: "Unified Entity Detail Views & CRUD Operations - PRD"
description: "Enable comprehensive CRUD operations and consistent detail views across all catalog entities with centralized management on /global-fields"
audience: [ai-agents, developers]
tags: [entity-management, crud, global-fields, catalog, ui-enhancement]
created: 2025-11-12
updated: 2025-11-12
category: "product-planning"
status: draft
related:
  - /docs/project_plans/requests/needs-designed/entity-detail-views.md
---

# Unified Entity Detail Views & CRUD Operations - PRD

**Feature Name**: Unified Entity Detail Views & CRUD Operations
**Date**: 2025-11-12
**Author**: Claude (Sonnet 4.5)
**Priority**: High
**Target Release**: Q1 2025

## 1. Executive Summary

Enable complete CRUD (Create, Read, Update, Delete) operations for all catalog entities (CPU, GPU, RAM Spec, Storage Profile, Ports Profile, Scoring Profile) through unified interfaces. Currently, only Listings and CPUs appear on the /global-fields page, and most entities lack update/delete capabilities. This enhancement will provide a consistent, centralized management experience across all entity types, allowing administrators to correct mistakes and manage catalog data effectively.

**Key Outcomes**:
- All 7 entity types accessible via /global-fields workspace
- Complete CRUD operations for all catalog entities via API and UI
- Edit and Delete functionality added to all catalog detail views
- Dedicated detail views created for Ports Profile and Scoring Profile
- "Used In" validation preventing accidental data loss

## 2. Context & Background

### Current State

Deal Brain manages 7 primary catalog entity types:
1. **CPU** - Processor specifications with benchmarks
2. **GPU** - Graphics card specifications with benchmarks
3. **RAM Spec** - Memory configurations (DDR generation, capacity, speed)
4. **Storage Profile** - Storage specifications (medium, interface, capacity)
5. **Ports Profile** - Connectivity specifications (USB, HDMI, DisplayPort, etc.)
6. **Scoring Profile** - Valuation scoring weights and rules
7. **Listing** - PC listings that reference catalog entities

### Architecture Overview

**Backend**:
- **Catalog API** (`/api/catalog.py`) - Entity-specific endpoints
  - Currently: GET list/detail, POST create
  - Missing: PUT/PATCH update, DELETE
- **Fields-Data API** (`/api/field_data.py`) - Generic entity operations
  - Has PATCH update for Listing and CPU only
  - No DELETE endpoint
- **FieldRegistry** (`/services/field_registry.py`) - Entity registration for unified management
  - Currently registered: Listing, CPU only
  - Not registered: GPU, RAM Spec, Storage Profile, Ports Profile, Scoring Profile

**Frontend**:
- **Global Fields Page** (`/app/global-fields/page.tsx`) - Centralized entity management
  - Currently shows: Listing, CPU only
- **Catalog Detail Views** (`/app/catalog/{entity}/[id]/page.tsx`) - Entity-specific pages
  - Exist for: CPU, GPU, RAM Spec, Storage Profile
  - Missing: Ports Profile, Scoring Profile
  - Feature: Read-only views with "Used In Listings"
  - Missing: Edit and Delete functionality

### Key Problems

1. **Inconsistent Entity Access**: Only 2 of 7 entities appear on /global-fields
2. **Incomplete CRUD**: Missing UPDATE and DELETE operations for most entities
3. **Data Integrity Issues**: Can't fix mistakes in RAM Specs, Storage Specs once created
4. **UI Inconsistency**: Some entities have detail views, others don't
5. **Fragmented Management**: No central location to manage all catalog data
6. **API Gaps**: Dual API pattern (Catalog vs Fields-Data) with incomplete coverage

### User Pain Points

**Current Workflow (Broken)**:
1. User creates RAM Spec with typo in label → Can't edit it
2. User creates duplicate Storage Profile → Can't delete it
3. User needs to update GPU benchmark scores → Must manually update database
4. User wants to manage Ports Profiles → No UI exists
5. Administrator needs to audit all entities → Must visit multiple pages

## 3. Problem Statement

**Primary Problem**: Administrators and power users cannot effectively manage catalog data due to missing CRUD operations and inconsistent UI coverage across entity types.

**Impact**:
- Data quality degradation from uncorrectable mistakes
- Database bloat from inability to delete duplicates
- Increased support burden (manual DB updates required)
- User frustration from inconsistent management interfaces
- Reduced confidence in catalog data accuracy

**Business Impact**:
- Slower data curation workflows
- Higher maintenance costs
- Reduced platform scalability
- Potential data integrity issues affecting valuations

## 4. Goals & Success Metrics

### Goals

1. **Unified Entity Management**: All 7 entity types accessible via /global-fields workspace
2. **Complete CRUD Operations**: Full create, read, update, delete for all entities
3. **Consistent UI Experience**: Standardized detail views with edit/delete across all entities
4. **Data Integrity Protection**: Validation preventing cascading data issues
5. **Improved User Efficiency**: Centralized management reducing task time by 60%

### Success Metrics

**Functional Metrics**:
- ✅ 7/7 entities registered in FieldRegistry and visible on /global-fields
- ✅ 7/7 entities have UPDATE endpoints (PUT/PATCH)
- ✅ 7/7 entities have DELETE endpoints with cascade checks
- ✅ 7/7 entities have dedicated detail views with Edit/Delete buttons
- ✅ 0 errors from deleting entities with dependent listings (validation works)

**Performance Metrics**:
- Update entity: < 500ms response time
- Delete entity: < 1s with cascade check
- List entities on /global-fields: < 2s initial load

**User Experience Metrics**:
- Time to fix entity typo: 60 seconds (down from "impossible")
- Time to delete duplicate entity: 30 seconds (down from "manual DB access")
- User satisfaction score: > 4.5/5 for entity management workflows

**Business Metrics**:
- 80% reduction in support requests for "fix my entity" issues
- 50% reduction in database clutter from duplicates
- 100% of catalog data auditable via UI

## 5. Requirements

### 5.1 Functional Requirements

#### FR-1: FieldRegistry Entity Registration
- **FR-1.1**: Register GPU entity in FieldRegistry with core fields mapping
- **FR-1.2**: Register RamSpec entity in FieldRegistry with core fields mapping
- **FR-1.3**: Register StorageProfile entity in FieldRegistry with core fields mapping
- **FR-1.4**: Register PortsProfile entity in FieldRegistry with core fields mapping
- **FR-1.5**: Register Profile (scoring profile) entity in FieldRegistry with core fields mapping
- **FR-1.6**: Support attributes_json custom fields for all registered entities

#### FR-2: Backend UPDATE Operations
- **FR-2.1**: Add `PUT /v1/catalog/cpus/{id}` endpoint for full CPU updates
- **FR-2.2**: Add `PATCH /v1/catalog/cpus/{id}` endpoint for partial CPU updates
- **FR-2.3**: Add `PUT/PATCH /v1/catalog/gpus/{id}` endpoints for GPU updates
- **FR-2.4**: Add `PUT/PATCH /v1/catalog/ram-specs/{id}` endpoints for RAM Spec updates
- **FR-2.5**: Add `PUT/PATCH /v1/catalog/storage-profiles/{id}` endpoints for Storage Profile updates
- **FR-2.6**: Add `PUT/PATCH /v1/catalog/ports-profiles/{id}` endpoints for Ports Profile updates
- **FR-2.7**: Add `PUT/PATCH /v1/catalog/profiles/{id}` endpoints for Scoring Profile updates
- **FR-2.8**: Validate unique constraints on update (prevent duplicate specs)
- **FR-2.9**: Update modified timestamps on successful updates
- **FR-2.10**: Return updated entity DTOs with computed fields

#### FR-3: Backend DELETE Operations
- **FR-3.1**: Add `DELETE /v1/catalog/cpus/{id}` endpoint with cascade checks
- **FR-3.2**: Add `DELETE /v1/catalog/gpus/{id}` endpoint with cascade checks
- **FR-3.3**: Add `DELETE /v1/catalog/ram-specs/{id}` endpoint with cascade checks
- **FR-3.4**: Add `DELETE /v1/catalog/storage-profiles/{id}` endpoint with cascade checks
- **FR-3.5**: Add `DELETE /v1/catalog/ports-profiles/{id}` endpoint with cascade checks
- **FR-3.6**: Add `DELETE /v1/catalog/profiles/{id}` endpoint with cascade checks
- **FR-3.7**: Check for dependent listings before deletion (return 409 Conflict if in use)
- **FR-3.8**: Provide "Used In" count in error message for transparency
- **FR-3.9**: Support soft delete (is_active flag) as alternative to hard delete (optional phase 2)

#### FR-4: Frontend Detail View Enhancements
- **FR-4.1**: Add "Edit" button to CPU detail layout with inline edit modal
- **FR-4.2**: Add "Delete" button to CPU detail layout with confirmation dialog
- **FR-4.3**: Add "Edit" and "Delete" buttons to GPU detail layout
- **FR-4.4**: Add "Edit" and "Delete" buttons to RAM Spec detail layout
- **FR-4.5**: Add "Edit" and "Delete" buttons to Storage Profile detail layout
- **FR-4.6**: Display "Used In X Listings" count prominently in all detail views
- **FR-4.7**: Disable delete button with tooltip when entity is in use (based on cascade check)

#### FR-5: New Detail Views for Missing Entities
- **FR-5.1**: Create `/catalog/ports-profiles/[id]` page with detail layout
- **FR-5.2**: Create `PortsProfileDetailLayout` component showing:
  - Name, description, attributes
  - List of ports (type, count, spec_notes) in table
  - "Used In Listings" card with listing previews
  - Edit and Delete buttons
- **FR-5.3**: Create `/catalog/profiles/[id]` page with detail layout
- **FR-5.4**: Create `ProfileDetailLayout` component showing:
  - Name, description, is_default flag
  - Scoring weights breakdown (weights_json visualization)
  - Rule group weights table
  - "Used In Listings" card
  - Edit and Delete buttons

#### FR-6: Global Fields Workspace Expansion
- **FR-6.1**: Update GlobalFieldsWorkspace to fetch all 7 entities from FieldRegistry
- **FR-6.2**: Add sidebar navigation items for:
  - GPU (icon: video card)
  - RAM Spec (icon: memory chip)
  - Storage Profile (icon: hard drive)
  - Ports Profile (icon: plug)
  - Scoring Profile (icon: target)
- **FR-6.3**: Support entity-specific data grids in GlobalFieldsDataTab for all entities
- **FR-6.4**: Add entity-specific create/edit modals with field validation

#### FR-7: Delete Confirmation & Safety
- **FR-7.1**: Show confirmation dialog before any delete operation
- **FR-7.2**: Display "Used In X Listings" count in confirmation dialog
- **FR-7.3**: Require typing entity name for confirmation if entity is in use (extra safety)
- **FR-7.4**: Show error toast if delete fails due to cascade constraints
- **FR-7.5**: Provide "View Listings" link in error to help user understand dependencies

### 5.2 Non-Functional Requirements

#### NFR-1: Performance
- **NFR-1.1**: Entity list queries return < 2s for 10,000+ entities
- **NFR-1.2**: Update operations complete < 500ms
- **NFR-1.3**: Delete cascade checks complete < 1s
- **NFR-1.4**: Detail view loads < 1.5s including "Used In" listings

#### NFR-2: Data Integrity
- **NFR-2.1**: All updates validate unique constraints (prevent duplicates)
- **NFR-2.2**: Cascade checks prevent orphaned foreign key references
- **NFR-2.3**: Optimistic locking prevents concurrent update conflicts (optional)
- **NFR-2.4**: Audit trail for all update/delete operations (optional phase 2)

#### NFR-3: Usability
- **NFR-3.1**: Edit modals pre-populate with current entity values
- **NFR-3.2**: Inline validation shows errors before submission
- **NFR-3.3**: Success/error toasts provide clear feedback
- **NFR-3.4**: Keyboard navigation (Tab, Enter, Esc) fully supported
- **NFR-3.5**: Screen readers announce all interactive elements

#### NFR-4: Security
- **NFR-4.1**: UPDATE/DELETE operations require admin role (future auth integration)
- **NFR-4.2**: Rate limiting on destructive operations (5 deletes/min per user)
- **NFR-4.3**: Audit log records user, timestamp, old/new values for compliance

#### NFR-5: Maintainability
- **NFR-5.1**: Consistent code patterns across all entity endpoints
- **NFR-5.2**: Reusable React components for edit/delete UI
- **NFR-5.3**: Centralized validation logic in services layer
- **NFR-5.4**: Unit test coverage > 80% for new CRUD operations

## 6. Scope

### In Scope

**Phase 1: Backend CRUD Completion**
- ✅ UPDATE endpoints (PUT/PATCH) for all 6 catalog entities (CPU, GPU, RamSpec, StorageProfile, PortsProfile, Profile)
- ✅ DELETE endpoints with cascade validation for all 6 entities
- ✅ FieldRegistry registration for GPU, RamSpec, StorageProfile, PortsProfile, Profile
- ✅ "Used In" listing count queries for cascade checks

**Phase 2: Frontend Edit/Delete UI**
- ✅ Edit/Delete buttons added to existing 4 detail views (CPU, GPU, RamSpec, StorageProfile)
- ✅ Edit modals with form validation for all entity types
- ✅ Delete confirmation dialogs with "Used In" warnings
- ✅ Toast notifications for success/error feedback

**Phase 3: New Detail Views**
- ✅ PortsProfile detail view at `/catalog/ports-profiles/[id]`
- ✅ Profile (scoring) detail view at `/catalog/profiles/[id]`
- ✅ Layouts with Edit/Delete functionality

**Phase 4: Global Fields Integration**
- ✅ All 7 entities visible in GlobalFieldsWorkspace sidebar
- ✅ Entity-specific data grids in GlobalFieldsDataTab
- ✅ Create/Edit modals for each entity type

### Out of Scope

**Deferred to Phase 2 (Future Enhancement)**
- ❌ Soft delete with is_active flag (currently hard delete only)
- ❌ Audit trail UI showing update/delete history
- ❌ Bulk operations (bulk delete, bulk update)
- ❌ Entity versioning and rollback
- ❌ Advanced cascade options (e.g., "delete and reassign listings")

**Explicitly Not Included**
- ❌ Listing entity CRUD (already fully functional)
- ❌ Custom field definition management (already exists)
- ❌ Import/export of catalog entities
- ❌ Entity merge functionality
- ❌ Role-based permissions (auth system not yet implemented)

## 7. User Stories & Acceptance Criteria

### US-1: Edit Entity Specification (All Entity Types)

**As an** administrator
**I want to** edit entity specifications after creation
**So that** I can correct mistakes without manual database access

**Acceptance Criteria**:
- [ ] AC-1.1: "Edit" button visible on all catalog detail views
- [ ] AC-1.2: Clicking "Edit" opens modal pre-populated with current values
- [ ] AC-1.3: Modal validates input before allowing submission
- [ ] AC-1.4: Successful update shows success toast and refreshes detail view
- [ ] AC-1.5: Validation errors display inline with field-specific messages
- [ ] AC-1.6: Canceling edit discards changes and closes modal

**Test Scenarios**:
```
Given: User views CPU detail page for "Intel i7-12700"
When: User clicks "Edit" button
Then: Modal opens with current CPU specs pre-filled

Given: User edits CPU label from "Intel i7-12700" to "Intel Core i7-12700"
When: User clicks "Save Changes"
Then: API calls PATCH /v1/catalog/cpus/{id}
And: Success toast shows "CPU updated successfully"
And: Detail view refreshes with new label

Given: User enters duplicate CPU name (already exists)
When: User clicks "Save Changes"
Then: Validation error shows "CPU with this name already exists"
And: Modal remains open for correction
```

### US-2: Delete Unused Entity

**As an** administrator
**I want to** delete duplicate or incorrect entities
**So that** I can maintain clean catalog data

**Acceptance Criteria**:
- [ ] AC-2.1: "Delete" button visible on all catalog detail views
- [ ] AC-2.2: Delete button shows tooltip with "Used In X Listings" count
- [ ] AC-2.3: Clicking "Delete" opens confirmation dialog
- [ ] AC-2.4: Confirmation dialog requires user acknowledgment
- [ ] AC-2.5: Successful delete redirects to entity list page
- [ ] AC-2.6: Delete fails with error toast if entity is in use

**Test Scenarios**:
```
Given: User views RAM Spec detail page for unused spec
And: Spec is not referenced by any listings
When: User clicks "Delete" button
Then: Confirmation dialog shows "Delete RAM Spec?"
And: Dialog displays "This spec is not currently used in any listings"

Given: User confirms deletion
When: User clicks "Confirm Delete"
Then: API calls DELETE /v1/catalog/ram-specs/{id}
And: Success toast shows "RAM Spec deleted successfully"
And: User redirected to /catalog/ram-specs

Given: User views GPU detail page for GPU used in 15 listings
When: User clicks "Delete" button
Then: Delete button tooltip shows "Used in 15 listings"
And: Confirmation dialog shows "This GPU is used in 15 listings. Deletion is not allowed."
And: Delete action is blocked
```

### US-3: Manage All Entities from /global-fields

**As an** administrator
**I want to** manage all entity types from the /global-fields page
**So that** I have a centralized workflow for catalog management

**Acceptance Criteria**:
- [ ] AC-3.1: GlobalFieldsWorkspace sidebar shows all 7 entity types
- [ ] AC-3.2: Clicking entity in sidebar loads entity-specific data grid
- [ ] AC-3.3: Data grid supports filtering, sorting, column resizing
- [ ] AC-3.4: "Add Entry" button opens entity-specific create modal
- [ ] AC-3.5: Row actions include "Edit" and "View Details" for all entities
- [ ] AC-3.6: Pagination works correctly for large entity lists (1000+ items)

**Test Scenarios**:
```
Given: User navigates to /global-fields
When: User views sidebar
Then: Sidebar shows: Listing, CPU, GPU, RAM Spec, Storage Profile, Ports Profile, Scoring Profile

Given: User clicks "RAM Spec" in sidebar
When: Data grid loads
Then: Grid shows all RAM specs with columns: Label, DDR Gen, Speed, Capacity, Actions

Given: User clicks "Add Entry" button on RAM Spec grid
When: Modal opens
Then: Form shows fields: Label, DDR Generation, Speed MHz, Module Count, Capacity per Module, Notes

Given: User fills form and clicks "Create"
When: API calls POST /v1/catalog/ram-specs
Then: Success toast shows "RAM Spec created successfully"
And: Data grid refreshes showing new spec
```

### US-4: View Entity Usage Before Deletion

**As an** administrator
**I want to** see which listings use an entity before deleting
**So that** I understand the impact of deletion

**Acceptance Criteria**:
- [ ] AC-4.1: Detail view shows "Used In X Listings" count prominently
- [ ] AC-4.2: "Used In Listings" card shows preview of affected listings
- [ ] AC-4.3: Delete confirmation dialog repeats "Used In X Listings" warning
- [ ] AC-4.4: If entity is in use, confirmation requires typing entity name
- [ ] AC-4.5: Error message includes "View Listings" link if delete fails

**Test Scenarios**:
```
Given: User views Storage Profile detail page
When: Page loads
Then: Header shows "Used in 27 listings" badge
And: "Used In Listings" card shows first 5 listings with titles and links

Given: User clicks "Delete" on Storage Profile used in 27 listings
When: Confirmation dialog opens
Then: Dialog shows "This Storage Profile is used in 27 listings"
And: Dialog shows "Type 'Samsung 970 EVO 1TB NVMe' to confirm deletion"
And: Delete button disabled until correct text entered

Given: User types correct entity name and confirms
When: API calls DELETE /v1/catalog/storage-profiles/{id}
Then: API returns 409 Conflict error
And: Error toast shows "Cannot delete: Storage Profile is used in 27 listings. View Listings >"
And: Clicking "View Listings" navigates to /catalog/storage-profiles/{id}#used-in
```

### US-5: Create Dedicated Detail Views for Missing Entities

**As an** administrator
**I want to** view detailed information for Ports Profiles and Scoring Profiles
**So that** I have consistent entity management across all types

**Acceptance Criteria**:
- [ ] AC-5.1: `/catalog/ports-profiles/[id]` page exists with full layout
- [ ] AC-5.2: Ports Profile detail shows name, description, ports table, "Used In" listings
- [ ] AC-5.3: `/catalog/profiles/[id]` page exists with full layout
- [ ] AC-5.4: Scoring Profile detail shows name, weights, rule groups, "Used In" listings
- [ ] AC-5.5: Both detail views have Edit and Delete buttons
- [ ] AC-5.6: Breadcrumb navigation works correctly for new routes

**Test Scenarios**:
```
Given: User navigates to /catalog/ports-profiles/1
When: Page loads
Then: Layout shows:
  - Breadcrumb: Home > Catalog > Ports Profiles > [Name]
  - Header with "Edit" and "Delete" buttons
  - "Specifications" card with name, description, attributes
  - "Ports" card with table of ports (type, count, spec notes)
  - "Used In Listings" card with listing previews

Given: User navigates to /catalog/profiles/1
When: Page loads
Then: Layout shows:
  - Breadcrumb: Home > Catalog > Scoring Profiles > [Name]
  - Header with "Edit" and "Delete" buttons
  - "Profile Details" card with name, description, is_default flag
  - "Scoring Weights" card with table of metric weights
  - "Rule Group Weights" card with table of rule priorities
  - "Used In Listings" card
```

## 8. Dependencies & Assumptions

### Dependencies

**Technical Dependencies**:
- Existing FieldRegistry service (`field_registry.py`) for entity registration
- Existing catalog API structure (`catalog.py`) for endpoint patterns
- Existing React Query setup for API calls
- Existing detail layout components as UI patterns
- SQLAlchemy relationships for cascade checks

**Data Dependencies**:
- Database foreign key relationships between Listing and catalog entities
- Unique constraints on entity specifications (must not break on update)
- `attributes_json` JSONB column for custom fields

### Assumptions

**Technical Assumptions**:
- Existing database schema supports updates (no immutable columns)
- Unique constraints are defined correctly in models
- Foreign key relationships have proper on_delete behavior
- API authentication/authorization will be added later (currently open access)

**User Assumptions**:
- Users understand the impact of deleting entities with dependencies
- Users have database-level access for emergency rollback if needed
- Administrators will not delete entities in use (UI blocks this)

**Business Assumptions**:
- Catalog data quality issues are causing significant friction
- Centralized management is more important than entity-specific workflows
- Users prefer inline editing over navigating to separate edit pages

## 9. Risks & Mitigations

### Risk 1: Accidental Data Loss from Deletions

**Severity**: High
**Probability**: Medium

**Mitigation**:
- Implement "Used In" cascade checks blocking deletes of in-use entities
- Require explicit confirmation with entity name typing for entities with dependencies
- Add audit trail logging all delete operations (phase 2)
- Provide soft delete option preserving data (phase 2)

### Risk 2: Unique Constraint Violations on Update

**Severity**: Medium
**Probability**: Medium

**Mitigation**:
- Validate unique constraints in service layer before database update
- Return clear error messages identifying conflicting entity
- Use database transactions for atomicity
- Add integration tests covering duplicate scenarios

### Risk 3: Performance Degradation on "Used In" Checks

**Severity**: Medium
**Probability**: Low

**Mitigation**:
- Use COUNT(*) queries instead of loading full listings
- Add database indexes on foreign key columns
- Cache "Used In" counts with 5-minute TTL
- Monitor query performance with OpenTelemetry

### Risk 4: Concurrent Update Conflicts

**Severity**: Low
**Probability**: Low

**Mitigation**:
- Implement optimistic locking with version field (optional phase 2)
- Return 409 Conflict if entity modified by another user
- Add last_modified timestamp comparison
- Show conflict resolution UI (phase 2)

### Risk 5: UI Complexity from 7 Entity Types

**Severity**: Low
**Probability**: Medium

**Mitigation**:
- Reuse common components (EditModal, DeleteDialog) across entities
- Use entity-specific form schemas for validation
- Implement progressive disclosure (show advanced fields in accordion)
- Provide entity-specific help text and examples

## 10. Target State

### Post-Implementation State

**Backend**:
- ✅ All 7 entities registered in FieldRegistry
- ✅ Complete CRUD endpoints for CPU, GPU, RamSpec, StorageProfile, PortsProfile, Profile
- ✅ Cascade validation preventing orphaned listings
- ✅ Unified API patterns across all entities
- ✅ Audit trail foundation for compliance (phase 2)

**Frontend**:
- ✅ GlobalFieldsWorkspace shows all 7 entities in sidebar
- ✅ Entity-specific data grids with full CRUD operations
- ✅ Detail views for all 6 catalog entities with Edit/Delete buttons
- ✅ Consistent UI patterns across all entity types
- ✅ Accessible, keyboard-navigable interfaces

**User Experience**:
- ✅ Single workflow for managing all catalog data
- ✅ Self-service entity corrections (no DB access needed)
- ✅ Clear feedback on entity usage and deletion impact
- ✅ 60% reduction in time to fix entity mistakes

### Future State (Phase 2)

**Deferred Enhancements**:
- Soft delete with is_active flag for recoverability
- Audit trail UI showing update/delete history per entity
- Bulk operations (bulk delete, bulk update)
- Entity versioning and rollback capability
- Advanced cascade options (reassign listings on delete)
- Role-based access control for destructive operations

## 11. Implementation Plan

See: `docs/project_plans/implementation_plans/enhancements/entity-detail-views-v1.md`

Progress Tracking: `.claude/progress/entity-detail-views-v1/all-phases-progress.md`

### High-Level Phase Breakdown

**Phase 1: Backend CRUD - UPDATE Operations** (8 story points)
- Add UPDATE endpoints (PUT/PATCH) to catalog API for all 6 entities
- Implement update validation and unique constraint checks
- Add integration tests for update scenarios

**Phase 2: Backend CRUD - DELETE Operations** (8 story points)
- Add DELETE endpoints to catalog API for all 6 entities
- Implement cascade checks with "Used In" queries
- Add integration tests for delete scenarios and cascade validation

**Phase 3: FieldRegistry Expansion** (5 story points)
- Register GPU, RamSpec, StorageProfile, PortsProfile, Profile in FieldRegistry
- Map core fields and attributes_json for each entity
- Update fields-data API to support new entities

**Phase 4: Frontend Edit UI** (8 story points)
- Add Edit buttons to existing 4 detail views
- Create entity-specific edit modals with validation
- Implement optimistic updates with React Query
- Add success/error toast notifications

**Phase 5: Frontend Delete UI** (8 story points)
- Add Delete buttons to all detail views
- Create delete confirmation dialogs with "Used In" warnings
- Implement conditional delete (block if in use)
- Handle error states gracefully

**Phase 6: New Detail Views** (8 story points)
- Create PortsProfile detail view and layout component
- Create Profile (scoring) detail view and layout component
- Add Edit/Delete functionality to new views
- Implement breadcrumb navigation

**Phase 7: Global Fields Integration** (8 story points)
- Update GlobalFieldsWorkspace to show all 7 entities
- Create entity-specific data grids for new entities
- Add create/edit modals for each entity type
- Test end-to-end workflows

**Phase 8: Testing & Validation** (5 story points)
- Integration tests covering full CRUD workflows
- E2E tests for user stories
- Performance testing for large entity lists
- Accessibility audit (WCAG AA compliance)

**Phase 9: Documentation & Deployment** (3 story points)
- API documentation for new endpoints
- User guide for entity management workflows
- Deployment with feature flags
- Monitoring dashboard setup

**Total Effort**: 61 story points (~3 sprints)

## 12. Open Questions

### Technical Questions

1. **Q**: Should we implement soft delete (is_active flag) or hard delete?
   **A**: Start with hard delete + cascade checks. Add soft delete in phase 2 if needed.

2. **Q**: Should UPDATE be PUT (full replacement) or PATCH (partial update)?
   **A**: Support both: PUT for full replacement, PATCH for partial. Use PATCH in UI.

3. **Q**: Should we add optimistic locking (version field) to prevent concurrent updates?
   **A**: Optional for MVP. Add if concurrent edit conflicts occur in practice.

4. **Q**: Should cascade checks query actual listings or use cached counts?
   **A**: Query actual listings. Add caching if performance issues arise.

### UX Questions

5. **Q**: Should Edit be inline (modal) or navigate to separate edit page?
   **A**: Use modal for consistency with existing GlobalFieldsDataTab pattern.

6. **Q**: Should delete confirmation require typing entity name for all deletes or only if in use?
   **A**: Only require typing if entity is in use (extra safety for risky deletes).

7. **Q**: Should we allow "force delete" that removes entity and orphans listings?
   **A**: No. Always require users to re-assign listings before deletion.

### Business Questions

8. **Q**: Should we add role-based access control now or defer to auth implementation?
   **A**: Defer. Auth system not yet implemented. Add when RBAC is available.

9. **Q**: Should we support bulk delete operations?
   **A**: Defer to phase 2. Focus on single-entity operations for MVP.

10. **Q**: Should we create audit trail UI or just log to database?
    **A**: Log to database now. UI in phase 2 if compliance requirements emerge.

## 13. Appendices

### Appendix A: Entity Field Mappings

**CPU Core Fields**:
- name, manufacturer, socket, cores, threads, tdp_w, igpu_model
- cpu_mark_multi, cpu_mark_single, igpu_mark
- release_year, notes, passmark_slug
- attributes_json (custom fields)

**GPU Core Fields**:
- name, manufacturer, gpu_mark, metal_score, notes
- attributes_json (custom fields)

**RamSpec Core Fields**:
- label, ddr_generation, speed_mhz, module_count
- capacity_per_module_gb, total_capacity_gb
- notes, attributes_json (custom fields)

**StorageProfile Core Fields**:
- label, medium, interface, form_factor
- capacity_gb, performance_tier
- notes, attributes_json (custom fields)

**PortsProfile Core Fields**:
- name, description, attributes_json
- Related: Port entities (type, count, spec_notes)

**Profile Core Fields**:
- name, description, is_default
- weights_json, rule_group_weights

### Appendix B: API Endpoint Matrix

| Entity | GET List | GET Detail | POST Create | PUT Update | PATCH Update | DELETE | Used In |
|--------|----------|------------|-------------|------------|--------------|--------|---------|
| CPU | ✅ | ✅ | ✅ | ➕ NEW | ➕ NEW | ➕ NEW | ✅ |
| GPU | ✅ | ✅ | ✅ | ➕ NEW | ➕ NEW | ➕ NEW | ✅ |
| RamSpec | ✅ | ✅ | ✅ | ➕ NEW | ➕ NEW | ➕ NEW | ✅ |
| StorageProfile | ✅ | ✅ | ✅ | ➕ NEW | ➕ NEW | ➕ NEW | ✅ |
| PortsProfile | ✅ | ❌ ➕ | ✅ | ➕ NEW | ➕ NEW | ➕ NEW | ➕ NEW |
| Profile | ✅ | ❌ ➕ | ✅ | ➕ NEW | ➕ NEW | ➕ NEW | ➕ NEW |

**Legend**:
- ✅ Exists
- ❌ Missing
- ➕ NEW To be implemented

### Appendix C: UI Component Reusability

**Reusable Components**:
- `EntityEditModal` - Generic edit modal accepting entity schema
- `EntityDeleteDialog` - Delete confirmation with "Used In" warning
- `EntityDetailHeader` - Header with breadcrumb, Edit/Delete buttons
- `EntitySpecsCard` - Collapsible specs display
- `UsedInListingsCard` - Listing previews with pagination
- `EntityDataGrid` - Generic data grid with CRUD actions

**Entity-Specific Components**:
- `CPUEditForm`, `GPUEditForm`, `RamSpecEditForm`, etc.
- `CPUDetailLayout`, `GPUDetailLayout`, etc. (already exist, need enhancement)

### Appendix D: Test Coverage Goals

**Backend Tests**:
- Unit tests: Services, validation logic (80% coverage)
- Integration tests: API endpoints, cascade checks (90% coverage)
- Repository tests: CRUD operations, unique constraints (85% coverage)

**Frontend Tests**:
- Component tests: Edit modals, delete dialogs (75% coverage)
- Integration tests: React Query mutations, form validation (70% coverage)
- E2E tests: Full user workflows (80% coverage of critical paths)

### Appendix E: Performance Benchmarks

**Baseline (Current)**:
- List entities: ~1.8s for 5,000 entities
- Load detail view: ~1.2s including "Used In" listings
- (No update/delete benchmarks - operations don't exist)

**Target (Post-Implementation)**:
- List entities: < 2s for 10,000 entities
- Load detail view: < 1.5s including "Used In" listings
- Update entity: < 500ms
- Delete with cascade check: < 1s

**Monitoring Metrics**:
- OpenTelemetry spans for all CRUD operations
- Prometheus metrics: request_duration, error_rate, cascade_check_duration
- Grafana dashboard: Entity CRUD Operations

---

**End of PRD**

**Next Steps**:
1. Review and approve PRD with stakeholders
2. Create detailed Implementation Plan with task breakdown
3. Set up progress tracking in `.claude/progress/entity-detail-views-v1/`
4. Begin Phase 1: Backend CRUD - UPDATE Operations
