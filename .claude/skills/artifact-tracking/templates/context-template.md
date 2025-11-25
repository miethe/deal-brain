---
# === CONTEXT TRACKING TEMPLATE ===
# Implementation decisions, architectural patterns, and integration context
# Copy this template and replace all [PLACEHOLDER] values

# Metadata: Identification and Scope
type: context
prd: "[PRD_ID]"                          # e.g., "blocks-v2-implementation"
phase: [PHASE_NUMBER]                    # Phase this context covers, or null for all-phases context
title: "[CONTEXT_TITLE]"                 # e.g., "Blocks V2 Implementation Context"
status: "in-progress"                    # complete|blocked|in-progress

# Phase Status (if covering multiple phases)
phase_status: []                         # Array of { phase: N, status: "...", label: "..." }
# Example:
# - { phase: 1, status: "complete", label: "Backend Foundation & DB Schema" }
# - { phase: 2, status: "in-progress", label: "Block CRUD Endpoints" }
# - { phase: 3, status: "blocked", label: "Block Library UI", reason: "Missing endpoints" }

# Critical Blockers (for AI agent queries)
blockers: []                             # Array of blocker objects with detailed info
# Example blocker:
# - id: "BLOCKER-001"
#   title: "Brief title"
#   description: "Detailed description of blocker"
#   severity: "critical|high|medium"
#   blocking: ["phase-2", "phase-3"]
#   root_cause: "Why this happened"
#   impact: "What is affected"
#   dependencies: ["endpoint1", "endpoint2"]
#   solution_path: "How to resolve"
#   assigned_to: null
#   created: "YYYY-MM-DD"
#   updated: "YYYY-MM-DD"

# Architecture Decisions (for understanding rationale)
decisions: []                            # Array of decision objects with rationale
# Example decision:
# - id: "DECISION-001"
#   question: "How should X be organized?"
#   decision: "As shared reusable components"
#   rationale: "Enables knowledge sharing and reduces duplication"
#   tradeoffs: "More complex model, requires versioning"
#   location: "path/to/file.py:45"
#   phase: 1
#   status: "implemented|designed-but-not-implemented|replaced"

# Integration Points (for understanding system interactions)
integrations: []                         # Array of integration objects
# Example integration:
# - id: "INTEGRATION-001"
#   from: "Frontend Component A"
#   to: "Backend Service B"
#   operation: "POST /api/v1/resource"
#   data_flow: "Request format, response format"
#   error_handling: "How errors are handled"
#   status: "implemented|pending|broken"
#   notes: "Additional context"

# Key Learnings (for future reference)
learnings: []                            # Array of learning objects
# Example learning:
# - title: "Brief lesson learned"
#   description: "Detailed explanation"
#   category: "performance|architecture|testing|frontend|backend"
#   impact: "How it affects future work"
#   reference: "path/to/file where this is relevant"
---

# [PRD_ID] - Implementation Context

**Phase**: [PHASE_NUMBER]
**Status**: [Status] (Last updated [DATE])
**Scope**: [Scope description - single phase or all phases]

---

## Overview

Clear summary of the implementation context this document covers. Include:
- What was built in this phase
- Key architectural decisions
- Critical integration points
- Gotchas and lessons learned

---

## Architecture Decisions

### Key Decisions Matrix

| Decision | Rationale | Tradeoffs | Status |
|----------|-----------|-----------|--------|
| Decision A | Why this choice | Cost of choice | Implemented |
| Decision B | Why this choice | Cost of choice | Pending |

### Decision Details

#### DECISION-001: [Question]

**Decision**: [What was decided]

**Rationale**: [Why this decision was made]
- Point 1: [Reasoning]
- Point 2: [Reasoning]

**Tradeoffs**: [What we gave up]
- Complexity: [What became more complex]
- Cost: [Performance or code maintenance impact]

**Alternatives Considered**:
- Alternative A: [Why rejected]
- Alternative B: [Why rejected]

**Implementation Location**: `path/to/file.tsx:45`

**Related Decisions**: DECISION-002, DECISION-003

**Status**: Implemented | Designed but not implemented | Replaced by DECISION-XYZ

---

#### DECISION-002: [Question]

[Follow same structure as DECISION-001]

---

## Integration Points

### Data Flows

#### Flow: [Component A] → [Component B]

```
Source: [Full path to component]
Target: [Full path to component]
Operation: POST /api/v1/endpoint
```

**Request Format**:
```json
{
  "field": "type and description"
}
```

**Response Format**:
```json
{
  "field": "type and description"
}
```

**Error Handling**:
- HTTP 400: [Validation error]
- HTTP 403: [Permission error]
- HTTP 500: [Server error]

**Status**: Implemented | Pending | Broken

**Notes**: [Additional context, known issues, workarounds]

---

### Service-to-Service Integration

#### [Service A] ↔ [Service B]

**Integration Points**:
1. **Endpoint**: `GET /api/v1/resource/{id}`
   - Used in: [Location in codebase]
   - Frequency: [How often called]
   - Performance: [Latency, caching strategy]

2. **Endpoint**: `POST /api/v1/resource`
   - Used in: [Location in codebase]
   - Error scenarios: [Common failures]

---

## Technical Patterns

### Pattern: [Name]

**Problem**: [What problem does this pattern solve?]

**Solution**: [How is it solved?]

**Implementation**:
```typescript
// Example code showing pattern in action
```

**Files Using This Pattern**:
- `path/to/file1.tsx`
- `path/to/file2.tsx`

**Variations**:
- Variation A: [When and why this variation is used]
- Variation B: [When and why this variation is used]

---

### Pattern: [Name]

[Follow same structure as previous pattern]

---

## Critical Gotchas & Learnings

### Gotcha 1: [Brief Title]

**What Happened**: [Description of the issue]

**Root Cause**: [Why it happened]

**Solution**: [How to fix/prevent it]

**Prevention**: [How to avoid in future]

**Impact**: [Severity and affected systems]

**Reference**: `path/to/affected/file.tsx:42`

---

### Gotcha 2: [Brief Title]

[Follow same structure as Gotcha 1]

---

## Performance Considerations

### Identified Bottlenecks

| Component | Bottleneck | Impact | Solution | Status |
|-----------|-----------|--------|----------|--------|
| [Name] | [Description] | [Perf impact] | [Solution] | Implemented |

### Optimization Opportunities

- **Opportunity 1**: [What could be optimized and why]
  - Current: [Current approach]
  - Proposed: [Better approach]
  - Estimated improvement: [Performance gain]

---

## Testing Strategy & Coverage

### Test Gaps

| Area | Gap | Impact | Priority |
|------|-----|--------|----------|
| [Component] | [Missing test] | [Impact] | High |

### Test Patterns Used

- **Pattern A**: [How and where it's used]
- **Pattern B**: [How and where it's used]

### Known Test Issues

- [Description of test that's flaky or incomplete]
  - Impact: [What does this affect?]
  - Workaround: [Current approach]
  - Permanent fix: [What needs to happen]

---

## State Management

### Data Flow

```
[Source] → [Processing] → [Storage] → [Consumer]
```

### State Synchronization

- **Frontend State**: [How state is managed]
- **Backend State**: [How persistence works]
- **Sync Strategy**: [How they stay in sync]
- **Edge Cases**: [What breaks sync and recovery]

---

## Security Considerations

### Authentication & Authorization

- **Entry Point**: [Where auth is validated]
- **Permission Model**: [How permissions work]
- **RLS Implementation**: [Row-level security details]
- **Known Issues**: [Security concerns and status]

### Data Protection

- **Sensitive Fields**: [What data needs protection]
- **Encryption**: [What's encrypted and how]
- **Audit Trail**: [What's logged]

---

## Accessibility & UI Compliance

### WCAG 2.1 AA Status

| Component | Compliance | Issues | Status |
|-----------|-----------|--------|--------|
| [Name] | AA | [Issues if any] | Compliant |

### Keyboard Navigation

- **Implementation**: [How keyboard nav works]
- **Gaps**: [What's missing]
- **Testing**: [How it's tested]

---

## Phase-Specific Context

### Phase 1: [Phase Title]

**Scope**: [What was accomplished]

**Key Components**:
- [Component]: [What it does]
- [Component]: [What it does]

**Dependencies Created For Later Phases**: [What downstream phases need]

**Known Incomplete Work**: [What wasn't finished and why]

---

### Phase 2: [Phase Title]

[Follow same structure as Phase 1]

---

## Migration Paths & Backward Compatibility

### Data Migrations

- **Migration 1**: [What changed and how users are handled]
  - Affected data: [What changed]
  - Migration strategy: [How it's migrated]
  - Rollback plan: [How to undo if needed]

### Breaking Changes

- **Change 1**: [What changed]
  - Affected users: [Who's affected]
  - Deprecation timeline: [When it's removed]
  - Migration guide: [How to update]

---

## Incomplete/Future Work

### Known Limitations

- **Limitation 1**: [What's not implemented]
  - Impact: [Why it matters]
  - Timeline: [When to address]
  - Blocker for: [What depends on this]

### Technical Debt

- **Debt 1**: [What needs refactoring]
  - Files affected: [list]
  - Reason to refactor: [Why it matters]
  - Estimated effort: [Time to address]

---

## Resources & References

### Key Files

| File | Purpose | Key Functions |
|------|---------|----------------|
| `path/to/file.tsx` | [Purpose] | `functionA`, `functionB` |

### External References

- [Link] - [What it documents]
- [Link] - [What it documents]

### Related Decisions & Docs

- **ADR-001**: [Architecture Decision Record]
- **Progress Doc**: `/path/to/progress-file.md`
- **Design Spec**: [Link to design]
