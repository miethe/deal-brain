# Implementation Plan

Phase 1 – Design Confirmation: Inventory enum-backed columns (port.type, valuation_rule.component_type, valuation_rule.metric, listing.condition, listing.status, listing_component.component_type); agree that each will become String(32) (or tighter where safe) with application-level validation; document how Python enums (in dealbrain_core.enums) continue to provide canonical values while permitting rapid additions.

Phase 2 – Migration Scaffolding: Author a forward-only Alembic migration that batches ALTER TABLE ... ALTER COLUMN ... TYPE VARCHAR(32) USING <col>::text for every enum column; reset defaults as literal strings; drop the PostgreSQL enum types (DROP TYPE port_type, etc.) after conversions; implement a downgrade that recreates the enum types and casts columns back without data loss.

Phase 3 – Application Refactor: Update apps/api/dealbrain_api/models/core.py to use mapped_column(String(...)) instead of ENUM(..., create_type=True) and ensure defaults use .value; adjust any SQLAlchemy relationships, queries, or validators that expected Enum objects to treat values as strings (wrapping with the domain enums where needed); remove now-unused imports of ENUM.

Phase 4 – Domain & Validation Updates: Review services, schemas, and import flows (packages/core/dealbrain_core/schemas, apps/api/dealbrain_api/services/imports) to confirm they accept string inputs and, where they convert to enums, handle unexpected values gracefully; add lightweight validation helpers so new strings can be whitelisted or logged without blocking ingestion.

Phase 5 – Verification & Rollout: Run existing unit/integration tests plus targeted regression cases for listing creation, valuation rule management, and port profile imports; execute a dry-run migration against a staging snapshot to confirm type casts, defaults, and unique constraints remain intact; monitor API serialization/deserialization to ensure enums still round-trip as expected.

Phase 6 – Post-Migration Hygiene: Update developer docs (docs/db-types-report.md, importer guides) to explain the new string-backed fields and validation strategy; brief the team on how to introduce new component/port/status strings; schedule a follow-up audit after the first few additions to confirm no DB migrations are required and error rates stay flat.

## Current Status — 2025-09-22
- [x] Phase 1 – Schema audit and change design
- [x] Phase 2 – Alembic migration drafted and ready
- [x] Phase 3 – SQLAlchemy model refactor to string-backed fields
- [x] Phase 4 – Service-layer coercion ensuring enums stay resilient to string storage
- [ ] Phase 5 – Automated verification run (pending in this session)
- [ ] Phase 6 – Broader documentation rollout and team briefing
