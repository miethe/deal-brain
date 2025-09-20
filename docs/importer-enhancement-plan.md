# Deal Brain Importer Revamp

## 1. Goals & Success Metrics
- Deliver a frictionless import flow that supports non-technical users uploading arbitrary catalog exports.
- Ensure mapping coverage across all supported entity types (CPUs, GPUs, Listings, Valuation Rules, Ports Profiles) with automated suggestions achieving >90% accuracy on canonical spreadsheets.
- Provide deterministic, auditable import commits with conflict handling and rollback safety.
- Maintain sub-60s perceived latency for large workbooks (<10k rows) by deferring heavy work to background tasks and streaming previews incrementally.

## 2. Experience Flow
1. **Landing / Upload**
   - Drag-and-drop zone or file selector accepting `.xlsx`, `.csv`, `.tsv`.
   - On upload we create an import session and kick off sheet sniffing in the background; progress indicator shows parsing status.
   - Display detected sheets with inferred data types ("CPUs", "Listings", etc.) once ready.
2. **Field Mapping**
   - Tabbed interface per detected data type. Each tab shows target schema fields on the left and source columns on the right with automatic matches pre-populated.
   - Missing required fields highlighted in red with suggestions ranked by fuzzy ratio; optional fields tagged accordingly.
   - Column preview (first 5 rows) updates live as the user adjusts mappings. Surfaces warnings when data must be transformed (e.g., storage capacity normalization, condition enum mapping).
   - Allow saving partial mappings for reuse; persist defaults per tenant.
3. **Data Review & Conflict Resolution**
   - Summary table per entity showing counts: `new`, `updates`, `skipped`, `invalid`.
   - Dedicated Conflict tab lists collisions (e.g., CPUs with matching name) and diff of attributes. Users choose per-row strategy: `Update`, `Skip`, or `Keep existing` with selective field override.
   - Listings preview includes best-effort component matches (CPU/GPU) with confidence badges; unresolved matches flagged for manual selection.
4. **Commit & Tracking**
   - Final confirmation summarizing actions and optional notes.
   - Submit triggers background import job; UI transitions to status view with progress (rows processed, errors). Users can navigate away and revisit via history list.
   - Post-completion digest: counts, warnings, downloadable error CSV, link to newly created records.

## 3. Backend Architecture
- **Import Sessions**
  - New table `import_session` storing `id`, `filename`, `status`, `content_type`, `sheet_meta_json`, `mappings_json`, `conflicts_json`, `created_by`, timestamps.
  - Uploaded files stored under `data/uploads/{session_id}/source` (support future S3 swap). Metadata persisted immediately; file checksum recorded for deduping.
- **Parsing Pipeline**
  - `SpreadsheetInspector` reads workbook headers, detects sheets, and infers column semantics using heuristics (normalized strings, keyword dictionary, fuzzy ratio via `rapidfuzz.process`).
  - Results cached in Redis keyed by session to avoid re-reading large files during mapping adjustments.
- **Mapping Engine**
  - Declarative schema definitions (`ImportSchema` dataclasses) enumerate required/optional fields, data types, normalizers, and custom validators per entity.
  - Generate auto-mapping suggestions by scoring source columns against each target field (direct match > alias > fuzzy > embedding fallback).
  - `MappingPreviewService` materializes typed records for a limited preview window (first 100 rows) and aggregates validation errors.
- **Conflict Detection**
  - For each entity, compute natural keys (`cpu.name`, `gpu.name`, `valuation_rule.name`, composite keys for listings). Query DB with `IN` batches and produce diff payloads (field-level).
  - Provide merge strategies: `skip`, `overwrite_all`, `update_non_null`, future-friendly for custom merge rules.
- **Commit Execution**
  - `ImportJob` worker orchestrates batch upserts via SQLAlchemy bulk operations wrapped in transaction per entity. Honors conflict strategy selections.
  - Emits progress events to Redis pub/sub; FastAPI exposes SSE/WS endpoint consumed by frontend for live updates.
  - Detailed audit log persisted to `import_session_audit` capturing row-level actions and errors for replay/debug.

## 4. Component Matching Strategy
- Build `ComponentMatcher` utility leveraging normalized lookups + fuzzy match thresholds.
- Precompute lookup dictionaries for CPUs/GPUs (name, aliases, marketing strings) refreshed on import start.
- For each listing row, attempt direct match; if fuzzy score >= 90, auto-assign; between 75-89 flagged for user review with top 3 suggestions; below 75 left unresolved.
- Persist user overrides back into session mapping so final commit respects manual selections.

## 5. API Surface
- `POST /v1/imports/sessions` — multipart upload; returns `session_id` and initial sheet detection.
- `GET /v1/imports/sessions/{id}` — session snapshot (status, auto-mappings, pending actions, progress metrics).
- `POST /v1/imports/sessions/{id}/mappings` — accept mapping adjustments; responds with validation summary and preview data.
- `POST /v1/imports/sessions/{id}/conflicts` — resolves selections for conflicts (updates, skips) and recalculates tallies.
- `POST /v1/imports/sessions/{id}/commit` — finalize import; enqueues background job.
- `GET /v1/imports/sessions/{id}/events` — SSE/WS stream for progress updates.
- `GET /v1/imports/history` — list past sessions with status, counts, errors.

## 6. Frontend Implementation Blueprint
- Replace `ImportForm` with `ImportWizard` client component using TanStack Query + React Hook Form for state.
- Reusable UI primitives:
  - `FileDropzone` (drag/drop + click).
  - `MappingTable` (left column target fields, right column select + auto chip, chip color-coded for match confidence).
  - `ConflictDiff` (shows before/after, toggle group for resolution choice).
  - `ProgressDrawer` (live updates using SSE client; fallback to polling).
- Use `Tabs` to separate entity types; nested `Accordion` for optional sections (e.g., Ports Profiles advanced mapping).
- Persist wizard context in URL (`?session=<id>`) enabling deep links/resume.
- Visual language: glassmorphism cards, subtle gradients, progress timeline along top to reinforce step state.
- Motion & polish: micro-interactions on hover/drop, spring physics for modal transitions, and adaptive theming that echoes Apple-level craftsmanship while respecting accessibility contrast ratios.

## 7. Validation & Testing
- Backend unit tests for mapping heuristics, conflict diffing, and commit flows (pytest, factory-generated fixtures).
- Integration test simulating end-to-end import session (upload fixture workbook, adjust mapping, commit, assert DB state).
- Frontend component tests (Vitest/RTL) for mapping UI interactions and conflict resolution logic.
- Playwright scenario covering upload → mapping adjustments → conflict resolution with mocked API responses.

## 8. Delivery Plan & Workstreams
1. **Foundation**
   - Define import schema descriptors & heuristics utilities.
   - Create `import_session` table + models; implement file storage helpers.
2. **Session Lifecycle APIs**
   - Upload endpoint, inspector service, preview/mapping endpoints.
   - Redis caching + SSE channel for progress.
3. **Conflict Engine & Commit Worker**
   - Conflict detection queries, diff payloads, merge strategies.
   - Celery task for commit honoring user selections; auditing.
4. **Frontend Wizard**
   - Upload/stepper shell, tabs, mapping tables, conflict UI, progress view.
   - Integrate with new APIs via TanStack Query + SSE hookup.
5. **Testing & Polish**
   - Automated tests, UX refinements, accessibility pass, docs update.

## 9. Design Decisions & Assumptions
- **Access control**: Import sessions are scoped per tenant; creators and users with the `import.manage` role can edit or commit. Other authenticated users retain read-only visibility for auditability, and admins may reassign ownership when needed.
- **CPU conflict defaults**: We default to a field-level `update_non_null` merge, preserving existing data unless the upload supplies a new value. The Conflict tab lets users escalate to full-row overwrite or skip on a per-record basis.
- **File storage**: The MVP persists uploads on the application filesystem under `data/uploads/{session_id}` with streamed writes and SHA256 checksum verification. The storage provider is abstracted so we can swap in S3 by configuring an environment flag without touching the API surface.
- **Mapping templates**: Templates are versioned per tenant with optional user overrides. Each save increments a semantic version and keeps the last five revisions; admins can promote a user’s template to the tenant default for shared use.

## 11. Detailed Task Breakdown

### Backend
1. Draft Alembic migration for `import_session` (+ optional `import_session_audit`).
2. Implement SQLAlchemy models & Pydantic schemas for import session resources.
3. Build `SpreadsheetInspector` utility with header normalization + sheet typing heuristics (unit tests).
4. Implement file upload endpoint storing payload to disk and creating session rows.
5. Integrate Redis caching for inspector outputs (fallback to in-memory if Redis unavailable in tests).
6. Create mapping preview endpoint utilizing schema descriptors + limited row materialization.
7. Implement conflict detection service with DB batch queries and diff formatting.
8. Extend Celery worker to run commit task honoring merge strategies; emit progress events.
9. Surface SSE/WS endpoint bridging Redis pub/sub to clients; ensure graceful degradation to polling.
10. Write backend tests covering inspector, mapping validation, conflict resolution, commit flows.

### Frontend
1. Replace `ImportForm` with `ImportWizard` page (stepper scaffold + query hooks).
2. Implement `FileDropzone` component with drag/drop + upload progress UI.
3. Build mapping tab experience (`MappingTable`, suggestions, validation badges, preview grid).
4. Add conflict resolution UI (`ConflictDiff`, `ResolutionToggle`, list virtualization for large sets).
5. Wire up SSE client (or React Query polling fallback) to render job progress timeline.
6. Persist wizard state to URL/session storage for resume experience; handle existing session retrieval.
7. Incorporate accessibility + keyboard support (focus management, ARIA labels, color contrast checks).
8. Write frontend tests (component + integration) using mocked API handlers.

### Documentation & Ops
1. Update `docs/implementation-plan.md` and `docs/setup.md` with new importer flow.
2. Provide runbook snippet for regenerating mapping templates and interpreting audit logs.
3. Prepare Loom/animated walkthrough for stakeholders post-implementation (optional).

## 12. Implementation Notes (September 2025)
- FastAPI now persists import sessions/audit logs and exposes `/v1/imports/sessions` endpoints for upload, mapping updates, conflict refresh, and commit.
- The mapping engine uses RapidFuzz-driven heuristics to pre-populate columns for CPUs, GPUs, valuation rules, ports profiles, and listings while flagging missing required fields.
- Listing previews include component match suggestions (auto, needs review, unmatched) and capture overrides that flow into the commit payload.
- The Next.js importer view delivers the drag-and-drop upload experience, tabbed field mapping workspace, conflict controls, and commit confirmation described above.
- For day-to-day operator guidance see `docs/importer-usage-guide.md`.
