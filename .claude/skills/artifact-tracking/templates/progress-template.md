---
# === PROGRESS TRACKING TEMPLATE ===
# Machine-readable metadata for AI agent queries and task tracking
# Copy this template and replace all [PLACEHOLDER] values

# Metadata: Identification and Classification
type: progress
prd: "[PRD_ID]"                          # e.g., "advanced-editing-v2", "blocks-v2-implementation"
phase: [PHASE_NUMBER]                    # e.g., 1, 2, 3 (integer, not string)
title: "[PHASE_TITLE]"                   # e.g., "Prompt Creation Modal Enhancements"
status: "planning"                       # planning|in-progress|review|complete|blocked
started: "[YYYY-MM-DD]"                  # Start date of this phase
completed: null                          # "YYYY-MM-DD" when complete, null if in progress

# Overall Progress: Status and Estimates
overall_progress: [0-100]                # 0-100, e.g., 35 for 35% complete
completion_estimate: "on-track"          # on-track|at-risk|blocked|ahead

# Task Counts: Machine-readable task state
total_tasks: [COUNT]                     # Total tasks in this phase, e.g., 4
completed_tasks: [COUNT]                 # Completed count, e.g., 1
in_progress_tasks: [COUNT]               # Currently in progress, e.g., 1
blocked_tasks: [COUNT]                   # Blocked by dependencies, e.g., 0
at_risk_tasks: [COUNT]                   # At risk of missing deadline, e.g., 2

# Ownership: Primary and secondary agents
owners: ["[AGENT_NAME]"]                 # Primary agent(s), e.g., ["ui-engineer"]
contributors: ["[AGENT_NAME]"]           # Secondary agents, e.g., ["code-reviewer", "a11y-sheriff"]

# Critical Blockers: For immediate visibility
blockers: []                             # Array of blocker objects (see blocked task example below)
# Example blocker:
# - id: "BLOCKER-001"
#   title: "Missing API endpoint"
#   severity: "critical"
#   blocking: ["T-003", "T-004"]
#   resolution: "Awaiting backend-engineer implementation"

# Success Criteria: Acceptance conditions for phase completion
success_criteria: [
  # Example:
  # { id: "SC-1", description: "Feature X displays correctly", status: "pending" },
  # { id: "SC-2", description: "All tests pass", status: "pending" }
]

# Files Modified: What's being changed in this phase
files_modified: [
  # Example:
  # "apps/web/src/components/modals/CreatePromptModal/CreatePromptForm.tsx",
  # "services/api/routers/prompts.py"
]
---

# [PRD_ID] - Phase [PHASE_NUMBER]: [PHASE_TITLE]

**Phase**: [PHASE_NUMBER] of [TOTAL_PHASES]
**Status**: [Status Emoji] [Status] ([PERCENT]% complete)
**Duration**: Started [START_DATE], estimated completion [EST_DATE]
**Owner**: [AGENT_NAME]
**Contributors**: [AGENT_NAME], [AGENT_NAME]

---

## Overview

Clear, concise description of what this phase accomplishes.

**Why This Phase**: Explain the strategic importance and what problem it solves.

**Scope**: Clearly delineate what is IN scope and what is OUT of scope.

---

## Success Criteria

| ID | Criterion | Status |
|----|-----------|--------|
| SC-1 | Clear acceptance condition | ⏳ Pending |
| SC-2 | Another acceptance condition | ⏳ Pending |

---

## Tasks

| ID | Task | Status | Agent | Est | Notes |
|----|------|--------|-------|-----|-------|
| T-001 | Task description | ⏳ | agent-name | 5pts | Brief context |
| T-002 | Task description | ✓ | agent-name | 3pts | Completed notes |
| T-003 | Task description | 🚫 | agent-name | 8pts | Blocked by BLOCKER-001 |
| T-004 | Task description | ⚠️ | agent-name | 5pts | At risk - needs focus |

**Status Legend**:
- `⏳` Not Started
- `🔄` In Progress
- `✓` Complete
- `🚫` Blocked
- `⚠️` At Risk

---

## Architecture Context

### Current State

Describe the current implementation state, existing patterns, and what's already in place.

**Key Files**:
- `path/to/file.tsx` - Current implementation pattern
- `path/to/service.py` - Existing service layer

### Reference Patterns

Call out similar implementations elsewhere that should be mirrored for consistency.

**Similar Features**:
- Feature X in [file] uses pattern [description]
- Feature Y in [file] shows integration point [description]

---

## Implementation Details

### Technical Approach

Step-by-step approach to implementation, including:
- Architecture decisions
- Data flow
- Integration points
- Dependencies

### Known Gotchas

Things to watch out for:
- Common mistakes to avoid
- Edge cases to handle
- Browser compatibility issues
- Accessibility considerations

### Development Setup

Any special setup, configuration, or prerequisites needed for this phase.

---

## Blockers

### Active Blockers

| ID | Title | Severity | Blocking | Resolution |
|----|-------|----------|----------|-----------|
| BLOCKER-001 | Brief title | critical | T-003, T-004 | Resolution path |

### Resolved Blockers

Document blockers that have been resolved in this phase.

---

## Dependencies

### External Dependencies

- **Dependency 1**: Required for [reason], assigned to [agent]
- **Dependency 2**: Must be completed before [task], status [status]

### Internal Integration Points

- **Component A** integrates with **Component B** at [location]
- **Service X** calls **Service Y** for [operation]

---

## Testing Strategy

| Test Type | Scope | Coverage | Status |
|-----------|-------|----------|--------|
| Unit | Individual functions | 80%+ | ⏳ |
| Integration | Component interaction | Core flows | ⏳ |
| E2E | Full user workflows | Happy path + error | ⏳ |
| A11y | WCAG 2.1 AA compliance | All interactive elements | ⏳ |

---

## Next Session Agenda

### Immediate Actions (Next Session)
1. [ ] Specific action with clear context
2. [ ] Next step in sequence
3. [ ] Critical path item

### Upcoming Critical Items

- **Week of [DATE]**: [Milestone or deadline]
- **Dependency update**: [When something external completes]

### Context for Continuing Agent

[Specific information that AI agent needs to continue this phase without re-reading all context]

---

## Session Notes

### 2025-11-[DATE]

**Completed**:
- T-001: Task description with outcome

**In Progress**:
- T-002: Current status and next step

**Blockers**:
- BLOCKER-001: Description and resolution path

**Next Session**:
- Action item with context

---

## Additional Resources

- **Design Reference**: [Link to design spec or component spec]
- **Architecture Decision**: [Link to ADR if applicable]
- **API Documentation**: [Link to API docs if applicable]
- **Test Plan**: [Link to test strategy doc]
