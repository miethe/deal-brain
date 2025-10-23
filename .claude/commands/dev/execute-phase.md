---
description: Execute phase development following Deal Brain implementation plan and tracking patterns
argument-hint: <phase-number> [--plan=path/to/plan.md]
allowed-tools: Read, Grep, Glob, Edit, MultiEdit, Write,
  Bash(git:*), Bash(gh:*), Bash(pnpm:*), Bash(poetry:*), Bash(pytest:*),
  Bash(uv:*), Bash(pre-commit:*), Bash(alembic:*), Bash(make:*)
---

# /dev:execute-phase

You are Claude Code executing Phase `$ARGUMENTS` following Deal Brain implementation standards and the layered architecture: **API Routes → Services → Domain Logic (packages/core) → Database**.

---

## Phase Execution Protocol

Remember that all documentation work MUST be delegated to the documentation-writer subagent. You MUST NOT write documentation yourself.

### Phase 0: Initialize Context & Tracking

Extract PRD name as `{PRD_NAME}` from attached plan or PRD and phase number from `$ARGUMENTS` and set up tracking infrastructure:

```bash
# Parse arguments
phase_num="${1}"
plan_path="${2}"

# Default plan path if not provided
if [ -z "$plan_path" ]; then
  plan_path="docs/project_plans/${PRD_NAME}/phase-${phase_num}-*-implementation-plan.md"
  plan_path=$(ls $plan_path 2>/dev/null | head -1)
fi

if [ ! -f "$plan_path" ]; then
  echo "ERROR: Implementation plan not found at $plan_path"
  echo "Specify plan with: /dev:execute-phase ${phase_num} --plan=<path>"
  exit 1
fi

# Set up tracking directories
mkdir -p docs/project_plans/${PRD_NAME}/{progress,context}

progress_file="docs/project_plans/${PRD_NAME}/progress/phase-${phase_num}-progress.md"
context_file="docs/project_plans/${PRD_NAME}/context/phase-${phase_num}-context.md"

echo "📋 Phase ${phase_num} Execution Started"
echo "Plan: $plan_path"
echo "Progress: $progress_file"
echo "Context: $context_file"
```

**Read the implementation plan thoroughly.** This is your execution blueprint. Note:
- **DO NOT** load the linked PRD into context unless specific clarification is needed
- The plan should contain all necessary details
- Reference PRD only for ambiguous requirements

### Phase 1: Initialize Progress & Context Documents

#### 1.1 Create Progress Tracker

Create `${progress_file}` if it doesn't exist, or resume from existing state:

```markdown
# Phase ${phase_num} Progress Tracker

**Plan:** ${plan_path}
**Started:** ${timestamp}
**Last Updated:** ${timestamp}
**Status:** In Progress

---

## Completion Status

### Success Criteria
- [ ] [Copy from plan - Performance/Accessibility/Testing requirements]
- [ ] [Update checkboxes as tasks complete]

### Development Checklist
- [ ] [Task 1 from implementation plan]
- [ ] [Task 2 from implementation plan]
- [ ] [Task 3 from implementation plan]

---

## Work Log

### ${date} - Session ${n}

**Completed:**
- Task X: Brief description
- Task Y: Brief description

**Subagents Used:**
- @python-backend-engineer - API design
- @ui-engineer - Component implementation
- @debugger - Fixed issue with X

**Commits:**
- abc1234 feat(api): implement X following Deal Brain architecture
- def5678 test(api): add tests for X with coverage

**Blockers/Issues:**
- None

**Next Steps:**
- Continue with Task Z
- Validate completion of milestone M

---

## Decisions Log

- **[${timestamp}]** Chose approach X over Y because Z
- **[${timestamp}]** Modified plan to account for constraint C

---

## Files Changed

### Created
- /path/to/new/file1.py - Brief purpose

### Modified
- /path/to/existing/file1.ts - What changed

### Deleted
- /path/to/obsolete/file.ts - Why removed
```

#### 1.2 Create Working Context Document

Create `${context_file}` with implementation-specific context (aim for <2000 tokens):

```markdown
# Phase ${phase_num} Working Context

**Purpose:** Token-efficient context for resuming work across AI turns

---

## Current State

**Branch:** ${branch_name}
**Last Commit:** ${commit_hash}
**Current Task:** [What you're working on now]

---

## Key Decisions

- **Architecture:** [Key architectural choices made]
- **Patterns:** [Deal Brain patterns being followed]
- **Trade-offs:** [Important trade-offs made]

---

## Important Learnings

- **Gotcha 1:** [Brief description + how to avoid]
- **Gotcha 2:** [Brief description + how to avoid]

---

## Quick Reference

### Environment Setup
\`\`\`bash
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
\`\`\`

### Key Files
- Schema: apps/api/dealbrain_api/schemas/X.py
- Service: apps/api/dealbrain_api/services/X.py
- Model: apps/api/dealbrain_api/models/core.py
- API: apps/api/dealbrain_api/api/X.py
- UI: apps/web/app/X/page.tsx
- Component: apps/web/components/X.tsx
- Domain Logic: packages/core/dealbrain_core/X.py

---

## Phase Scope (From Plan)

[Copy executive summary from plan - 2-3 sentences max]

**Success Metric:** [Copy key metric from plan]
```

### Phase 2: Execute Implementation Plan

Work through the plan's development checklist **sequentially**. For each major task:

#### 2.1 Identify Required Expertise

Determine which subagent(s) to use based on task type:

| Task Type | Subagent |
|-----------|----------|
| Orchestrate Work/Key Architecture Decisions | lead-architect |
| ALL Documentation | documentation-writer |
| Python/FastAPI Backend | python-backend-engineer |
| Database Design/Migrations | data-layer-expert |
| UI/Component Design | ui-designer |
| UI/React components | ui-engineer |
| Frontend analysis | frontend-architect |
| Frontend development | frontend-developer |
| Fixing issues | debugger |
| Code quality review | code-reviewer |
| Task Validation | task-completion-validator |
| Testing | Direct implementation (or test-engineer if complex) |

#### 2.2 Execute Task with Subagent

Delegate to appropriate subagent with clear context:

```
@{subagent-name}

Phase ${phase_num}, Task: {task_name}

Requirements:
- [Specific requirement from plan]
- [Specific requirement from plan]

Deal Brain Patterns to Follow:
- Layered architecture: API Routes → Services → Domain Logic (core) → Database
- Pydantic validation for all API inputs/outputs
- Async-first: All database operations use async SQLAlchemy
- Domain logic in packages/core, not in apps/api
- React Query for server state, Zustand for client state
- Radix UI for all base components (headless, accessible)

Files to modify:
- {file_path_1}
- {file_path_2}

Success criteria:
- [What defines completion]
```

**If subagent invocation fails:** Document in progress tracker and proceed with direct implementation.

#### 2.3 Validate Task Completion

After each major task, validate with the task-completion-validator:

```
@task-completion-validator

Phase ${phase_num}, Task: {task_name}

Expected outcomes:
- [Outcome 1 from plan]
- [Outcome 2 from plan]

Files changed:
- {list files}

Please validate:
1. All acceptance criteria met
2. Deal Brain architecture patterns followed
3. Tests exist and pass
4. No regression introduced
```

**Validation checklist per task:**
- [ ] Acceptance criteria met
- [ ] Code follows Deal Brain layered architecture
- [ ] Tests exist and pass
- [ ] Python/TypeScript types correct
- [ ] Error handling implemented (Pydantic + HTTP status codes)
- [ ] Async patterns used correctly (if backend)
- [ ] Accessibility implemented (if frontend)
- [ ] Documentation updated if needed

#### 2.4 Commit Frequently

After each completed task (or logical unit of work), commit:

```bash
# Add changed files
git add {files}

# Commit with conventional commits format
git commit -m "feat(api): implement {feature} following Deal Brain architecture

- Added {component/service/etc}
- Added Alembic migration for schema changes (if applicable)
- Added tests with {coverage}%

Refs: Phase ${phase_num}, Task {task_name}"
```

**Commit message guidelines:**
- Use conventional commits: `feat|fix|test|docs|refactor|perf|chore`
- Scope: `api|web|core|cli|infra`
- Reference phase and task
- Keep focused (1 task per commit preferred)
- Include what was tested

#### 2.5 Update Progress Document

After **every** completed task, update progress tracker:

```markdown
### ${date} - Session ${n}

**Completed:**
- ✅ Task X: Implemented Y with Z pattern

**Commits:**
- abc1234 feat(api): implement X

**Next:** Task Y
```

Update relevant checklists by changing `- [ ]` to `- [x]`.

### Phase 3: Continuous Testing

Run tests continuously throughout implementation:

#### Backend Tests

```bash
# Run specific test file
poetry run pytest apps/api/tests/test_X.py -v

# Run all backend tests
poetry run pytest apps/api/tests/

# Run with coverage
poetry run pytest apps/api/tests/ --cov=dealbrain_api --cov-report=html

# Type checking
poetry run mypy apps/api/dealbrain_api

# Linting
poetry run ruff check apps/api/dealbrain_api
```

#### Frontend Tests

```bash
# Run component tests
pnpm --filter "./apps/web" test -- --testPathPattern="ComponentName"

# Run all frontend tests
pnpm --filter "./apps/web" test

# Type checking
pnpm --filter "./apps/web" typecheck

# Linting
pnpm --filter "./apps/web" lint

# Build check
pnpm --filter "./apps/web" build
```

#### Database Migrations

```bash
# Generate migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
make migrate
# or
poetry run alembic upgrade head

# Rollback one version
poetry run alembic downgrade -1

# Check migration status
poetry run alembic current
```

**Test failure protocol:**
1. Fix immediately if related to current work
2. Document in progress tracker if unrelated
3. DO NOT proceed to next task if tests fail for current work

### Phase 4: Milestone Validation

At each major milestone (typically after completing a section in the plan):

#### 4.1 Run Full Validation

```bash
#!/bin/bash
set -euo pipefail

echo "🔍 Running Phase ${phase_num} validation..."

# Backend validation
echo "Backend validation..."
poetry run mypy apps/api/dealbrain_api
poetry run ruff check apps/api/dealbrain_api
poetry run pytest apps/api/tests/

# Frontend validation
echo "Frontend validation..."
pnpm --filter "./apps/web" typecheck
pnpm --filter "./apps/web" lint
pnpm --filter "./apps/web" test
pnpm --filter "./apps/web" build

# Database migrations check
echo "Migration check..."
poetry run alembic check

echo "✅ Validation complete"
```

#### 4.2 Validate with Subagent

```
@task-completion-validator

Phase ${phase_num} Milestone: {milestone_name}

Completed tasks:
- [Task 1]
- [Task 2]
- [Task 3]

Expected outcomes from plan:
- [Outcome 1]
- [Outcome 2]

Please validate:
1. All milestone tasks complete
2. Success criteria met
3. No regressions
4. Tests comprehensive
5. Documentation updated
```

#### 4.3 Update Context Document

Update `${context_file}` with learnings from milestone:

```markdown
## Important Learnings

- **[New learning]:** Description and how to handle
```

### Phase 5: Final Phase Validation

When ALL tasks in the implementation plan are complete:

#### 5.1 Review Success Criteria

Go through **every** success criterion in the plan and verify:

```markdown
## Success Criteria Review

### Performance Requirements (if applicable)
- [x] API response time <200ms - Measured: 150ms
- [x] Database query optimization applied - Confirmed
- [x] React Query caching configured - Validated
[etc...]

### Accessibility Requirements (if applicable)
- [x] WCAG 2.1 AA compliance - Validated with axe
- [x] Zero critical violations - Confirmed
- [x] Keyboard navigation working - Tested
[etc...]

### Testing Requirements
- [x] Backend coverage >80% - Coverage: 85%
- [x] Frontend coverage >70% - Coverage: 78%
- [x] Integration tests passing - Confirmed
[etc...]
```

#### 5.2 Final Validation with Subagent

```
@task-completion-validator

Phase ${phase_num} FINAL VALIDATION

Plan: ${plan_path}
Progress: ${progress_file}

Please perform comprehensive validation:
1. All tasks in plan completed
2. All success criteria met
3. All tests passing
4. No critical issues
5. Documentation complete
6. Ready for next phase
```

#### 5.3 Run Quality Gates

```bash
#!/bin/bash
set -euo pipefail

echo "🎯 Phase ${phase_num} Final Quality Gates"

# Backend quality gates
echo "Backend quality gates..."
poetry run pytest apps/api/tests/ || { echo "❌ Backend tests failed"; exit 1; }
poetry run mypy apps/api/dealbrain_api || { echo "❌ Type check failed"; exit 1; }
poetry run ruff check apps/api/dealbrain_api || { echo "❌ Lint failed"; exit 1; }

# Frontend quality gates
echo "Frontend quality gates..."
pnpm --filter "./apps/web" test || { echo "❌ Frontend tests failed"; exit 1; }
pnpm --filter "./apps/web" typecheck || { echo "❌ TypeScript check failed"; exit 1; }
pnpm --filter "./apps/web" lint || { echo "❌ ESLint failed"; exit 1; }
pnpm --filter "./apps/web" build || { echo "❌ Build failed"; exit 1; }

# Database migration check
echo "Migration check..."
poetry run alembic check || { echo "❌ Migration check failed"; exit 1; }

echo "✅ All quality gates passed"
```

#### 5.4 Final Progress Update

Update progress tracker with final status:

```markdown
**Status:** ✅ Complete

**Completion Date:** ${date}

---

## Phase Completion Summary

**Total Tasks:** X
**Completed:** X
**Success Criteria Met:** X/X
**Tests Passing:** ✅
**Quality Gates:** ✅

**Key Achievements:**
- [Achievement 1]
- [Achievement 2]

**Technical Debt Created:**
- [Any intentional shortcuts with tracking issue]

**Recommendations for Next Phase:**
- [Suggestion 1]
- [Suggestion 2]
```

#### 5.5 Push All Changes

```bash
# Ensure all commits are pushed
git push origin ${branch_name}

echo "✅ Phase ${phase_num} complete and pushed"
echo "Progress: ${progress_file}"
echo "Context: ${context_file}"
```

---

## Error Recovery Protocol

If ANY task fails or blocks:

### 1. Document the Issue

Update progress tracker immediately:

```markdown
**Blockers/Issues:**
- **[${timestamp}]** Task X blocked by Y
  - Error: {error message}
  - Attempted: {what you tried}
  - Status: {blocked|investigating|resolved}
```

### 2. Attempt Recovery

Common recovery strategies:

**Git conflicts:**
```bash
git stash
git pull --rebase origin ${branch_name}
git stash pop
# Resolve conflicts
git add .
git rebase --continue
```

**Test failures:**
- Fix immediately if related to current work
- Document and skip if unrelated (create tracking issue)
- Use debugger subagent for complex failures

**Build failures:**
```bash
# Backend clean
rm -rf .pytest_cache __pycache__
poetry install

# Frontend clean
rm -rf apps/web/.next apps/web/node_modules/.cache
pnpm install
pnpm --filter "./apps/web" build
```

**Database migration issues:**
```bash
# Check current state
poetry run alembic current

# Downgrade if needed
poetry run alembic downgrade -1

# Re-apply
poetry run alembic upgrade head
```

**Subagent failures:**
- Retry once
- If fails again, document and proceed with direct implementation
- Note in decisions log why direct approach was taken

### 3. If Unrecoverable

```markdown
**Status:** ⚠️ Blocked

**Blocker Details:**
- Task: {task_name}
- Issue: {description}
- Attempted Solutions: {list}
- Needs: {what's needed to unblock}
```

Stop execution and report to user with:
- Clear description of blocker
- What was attempted
- What's needed to proceed
- Current state of work (all committed)

---

## Deal Brain Architecture Compliance Checklist

Ensure every implementation follows Deal Brain patterns:

### Backend Implementation
- [ ] **Layered architecture:** API Routes → Services → Domain Logic (core) → Database
- [ ] **Domain logic** in packages/core, NOT in apps/api
- [ ] **Pydantic schemas** for all API requests/responses (apps/api/dealbrain_api/schemas/)
- [ ] **Async SQLAlchemy** for all database operations
- [ ] **Proper error handling** with HTTP status codes (400, 404, 409, 500)
- [ ] **session_dependency()** for FastAPI routes
- [ ] **session_scope()** for service-layer operations
- [ ] **Alembic migration** if schema changed
- [ ] **Tests** for services and API endpoints
- [ ] **Type hints** throughout (mypy compatible)

### Frontend Implementation
- [ ] **Radix UI** for all base components (no direct custom implementations)
- [ ] **React Query** for server state management
- [ ] **Zustand** for global client state
- [ ] **apiFetch()** utility for API calls
- [ ] **Error boundaries** around new components
- [ ] **Loading states** handled
- [ ] **Accessibility** checked (keyboard nav, ARIA, contrast)
- [ ] **Responsive design** (mobile, tablet, desktop)
- [ ] **TypeScript** strict mode, no `any`
- [ ] **Tests** for components and hooks

### Shared Domain Logic (packages/core)
- [ ] **Pure business logic** - no database, no HTTP, no UI
- [ ] **Pydantic models** for data validation
- [ ] **Type-safe** with comprehensive type hints
- [ ] **Testable** - unit tests without external dependencies
- [ ] **Reusable** - shared by API and CLI

### Testing Requirements
- [ ] **Unit tests** for business logic (packages/core)
- [ ] **Service tests** for database operations
- [ ] **API tests** for endpoints
- [ ] **Component tests** for UI (if applicable)
- [ ] **Negative test cases** included
- [ ] **Edge cases** covered
- [ ] **Coverage** meets phase requirements

---

## Phase Completion Definition

Phase is **ONLY** complete when:

1. ✅ **All tasks** in implementation plan completed
2. ✅ **All success criteria** met (verified)
3. ✅ **All tests** passing (backend + frontend)
4. ✅ **Quality gates** passed (types, lint, build)
5. ✅ **Documentation** updated (code comments, ADRs if needed)
6. ✅ **Database migrations** applied and working
7. ✅ **Progress tracker** shows complete status
8. ✅ **Context document** updated with learnings
9. ✅ **All commits** pushed to branch
10. ✅ **Validation** completed by task-completion-validator
11. ✅ **No critical blockers** or P0 issues

**DO NOT** mark phase complete if any of above are incomplete.

---

## Output Format

Provide clear, structured status updates throughout:

```
📋 Phase ${phase_num} Execution Update

Current Task: {task_name}
Status: {in_progress|completed|blocked}

Progress:
- ✅ Task A
- ✅ Task B
- 🔄 Task C (current)
- ⏳ Task D (pending)

Recent Commits:
- abc1234 feat(api): implement X

Subagents Used:
- @python-backend-engineer (API design)
- @ui-engineer (Component implementation)

Next Steps:
- Complete Task C
- Validate with task-completion-validator
- Begin Task D
```

---

## Quickstart Examples

```bash
# Execute phase 4 with default plan location
/dev:execute-phase 4

# Execute phase 1 with explicit plan path
/dev:execute-phase 1 --plan=docs/project_plans/valuation-rules-enhance/phase-1-foundation-implementation-plan.md

# Resume phase 2 (will pick up from progress tracker)
/dev:execute-phase 2
```

---

## Deal Brain Monorepo Structure Reference

```
deal-brain/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── dealbrain_api/
│   │   │   ├── api/           # API endpoints
│   │   │   ├── services/      # Business logic orchestration
│   │   │   ├── models/        # SQLAlchemy models
│   │   │   ├── schemas/       # Pydantic schemas
│   │   │   ├── db.py          # Database configuration
│   │   │   └── app.py         # FastAPI app factory
│   │   ├── alembic/           # Database migrations
│   │   └── tests/             # Backend tests
│   ├── cli/                    # Typer CLI tools
│   └── web/                    # Next.js frontend
│       ├── app/               # Next.js 14 App Router pages
│       ├── components/        # React components
│       ├── lib/               # Utilities and API clients
│       ├── hooks/             # Custom React hooks
│       └── stores/            # Zustand stores
├── packages/
│   └── core/                  # Shared domain logic
│       └── dealbrain_core/
│           ├── valuation.py   # Valuation logic
│           ├── scoring.py     # Scoring logic
│           ├── rule_evaluator.py
│           ├── schemas/       # Shared Pydantic models
│           └── enums.py       # Shared enums
├── infra/                     # Docker configs
├── docs/                      # Documentation
│   └── project_plans/         # PRDs and implementation plans
└── .claude/                   # Claude Code configuration
    ├── agents/                # Specialized agents
    └── commands/              # Custom slash commands
```

---

Remember: **Follow the plan, validate continuously, commit frequently, and track everything.**
