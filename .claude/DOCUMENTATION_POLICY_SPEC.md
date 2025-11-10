# Documentation Policy Implementation Specification

**Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Complete Reference Implementation

This specification provides a complete, self-contained guide to implementing a comprehensive documentation policy in any project. It prevents documentation sprawl, enforces quality, and maintains an organized system for both permanent documentation and internal tracking documents.

---

## Table of Contents

1. [Overview & Philosophy](#overview--philosophy)
2. [CLAUDE.md Implementation](#claudemd-implementation)
3. [Agent Updates Required](#agent-updates-required)
4. [Directory Structure](#directory-structure)
5. [Frontmatter Specifications](#frontmatter-specifications)
6. [Implementation Checklist](#implementation-checklist)
7. [Example Documents](#example-documents)
8. [Troubleshooting & Anti-Patterns](#troubleshooting--anti-patterns)

---

## Overview & Philosophy

### What This Policy Solves

This policy addresses three critical problems in technical projects:

1. **Documentation Sprawl**: Teams create scattered, unorganized documentation that becomes outdated and hard to maintain
2. **Quality Debt**: Ad-hoc documents and worknotes get promoted to permanent documentation without proper structure
3. **Storage Confusion**: Developers don't know where tracking documents belong vs. permanent documentation

### Core Principles

1. **Document Only When Explicitly Needed**: Create documentation when tasked or when absolutely necessary to provide essential information
2. **Quality Over Quantity**: One well-organized document is better than five scattered ones
3. **Permanent vs. Temporary**: Distinguish clearly between permanent documentation (`/docs/`) and working documents (`.claude/`)
4. **Structured Tracking**: When tracking documents are needed, they follow strict naming and directory patterns
5. **No Ad-Hoc Creation**: Documentation is never created spontaneously; it's either explicitly tasked or structured tracking

### Key Insight

Documentation debt accumulates when teams:
- Create multiple scattered progress documents per phase
- Convert debugging notes into permanent documentation
- Store worknotes outside organized directories
- Create ad-hoc observation logs without time-boundaries
- Treat session notes as official documentation

This policy prevents all of these through clear, enforceable rules.

---

## CLAUDE.md Implementation

Add the following sections to your project's `CLAUDE.md` file. This establishes the policy as official guidance for AI agents and developers.

### Section 1: Documentation Policy Header (After Overview)

```markdown
## Documentation Policy

### Core Principle: Document Only When Explicitly Needed

Documentation should **ONLY** be created when:
1. Explicitly tasked in an implementation plan, PRD, or user request
2. Absolutely necessary to provide essential information to users or developers
3. Part of a defined allowed documentation bucket (see below)

**More documentation ≠ better.** Unnecessary documentation creates debt, becomes outdated, and misleads future developers. When in doubt, ask: "Is this in an allowed bucket?" If not, don't create it.
```

### Section 2: Strictly Prohibited Documentation

```markdown
### Strictly Prohibited Documentation

**DO NOT Create:**
- **Debugging Summaries**: Never document encountered bugs, errors, or debugging sessions as standalone docs
- **Unstructured Progress Docs**: Never create MULTIPLE scattered progress docs per phase (one per phase is allowed, see "Allowed Tracking Documentation")
- **Unorganized Context Files**: Never create context files outside the structured directories (see "Directory Structure")
- **Ad-Hoc Observation Logs**: Never create observation logs outside the monthly structure (use `.claude/worknotes/observations/observation-log-MM-YY.md`)
- **Session Notes as Docs**: Never publish personal notes, exploration logs, or investigation results as permanent documentation
- **Temporary Context as Docs**: Don't convert worknotes into permanent documentation without explicit need
- **Daily/Weekly Status Reports**: Don't create status update documents (use git commits and phase progress docs)

**Examples of What NOT to Create:**
```
❌ "2025-11-03-celery-event-loop-fix-context.md" - debugging summary (use git commit)
❌ "phase-1-3-progress.md" - consolidated multi-phase progress (use one per phase)
❌ "observations-week-1.md" - weekly observations (use monthly observation log)
❌ "issues-encountered-during-refactor.md" - debugging notes (use worknotes or commits)
❌ "why-we-changed-the-architecture.md" - exploration summary (use ADR or phase context)
❌ "random-context-notes.md" - unstructured notes (use organized structure)
```

**What IS Allowed (See "Allowed Tracking Documentation"):**
```
✅ ".claude/progress/listings-enhancements-v3/phase-2-progress.md" - ONE per phase
✅ ".claude/worknotes/listings-enhancements-v3/phase-2-context.md" - ONE per phase
✅ ".claude/worknotes/observations/observation-log-11-25.md" - monthly observations
✅ ".claude/worknotes/fixes/bug-fixes-tracking-11-25.md" - monthly bug fix tracking
```

**The Key Difference:**
- ❌ Multiple scattered files per phase → Creates documentation sprawl
- ✅ ONE structured file per phase → Organized, maintainable tracking
- ❌ Ad-hoc debugging summaries → Should be in git commits
- ✅ Structured monthly logs → Brief, organized, time-bounded
```

### Section 3: Allowed Tracking Documentation

```markdown
### Allowed Tracking Documentation

While permanent documentation should be minimized, **structured tracking documentation** is allowed when following these strict patterns:

**Progress Tracking (One Per Phase):**
- **Purpose**: Track implementation progress, completed tasks, blockers, and next steps for a specific phase of work
- **Location**: `.claude/progress/[prd-name]/phase-[N]-progress.md`
- **Limit**: ONE progress document per phase, not multiple scattered files
- **Required**: Only when working on multi-phase implementations from a PRD
- **Audience**: AI agents continuing work across sessions
- **Example**: `.claude/progress/listings-enhancements-v3/phase-2-progress.md`

**Context/Notes Documentation (One Per Phase):**
- **Purpose**: Document implementation decisions, technical notes, architecture considerations discovered during a phase
- **Location**: `.claude/worknotes/[prd-name]/phase-[N]-context.md`
- **Limit**: ONE context document per phase, organized by PRD name
- **Content**: Technical decisions, integration patterns, gotchas, architectural notes
- **Audience**: AI agents and developers who need to understand implementation choices
- **Example**: `.claude/worknotes/listings-enhancements-v3/phase-2-context.md`

**Monthly Observation Logs (Limited Exception):**
- **Purpose**: Track observations, learnings, patterns, and insights discovered during development
- **Location**: `.claude/worknotes/observations/observation-log-MM-YY.md`
- **Format**: Brief bullet points (1-2 lines per observation), one file per month
- **Content**: Pattern discoveries, performance insights, architectural learnings
- **Similar to**: Bug-fix tracking structure (monthly, concise, organized)
- **Example**: `.claude/worknotes/observations/observation-log-11-25.md`

**Monthly Bug-Fix Tracking (Limited Exception):**
- **Purpose**: Brief reference of significant bug fixes completed in a month
- **Location**: `.claude/worknotes/fixes/bug-fixes-tracking-MM-YY.md`
- **Format**: Very brief bullet points (1-2 lines per fix), one file per month
- **Content**: Brief fix descriptions with commit references
- **Example**: `.claude/worknotes/fixes/bug-fixes-tracking-11-25.md`

**Other Changelog-Type Documents:**
- **When Allowed**: Only if explicitly called out in PRD, implementation plan, or user request
- **Examples**: CHANGELOG.md updates, release notes, version history
- **Requirement**: Must be part of the planned work, not created ad-hoc
- **Location**: Project root or `/docs/` as specified in the plan

**Key Principles for Tracking Docs:**
1. **One Per Phase**: Don't create multiple progress or context docs for the same phase
2. **Organized Structure**: Use consistent directory structure (see below)
3. **Explicit Need**: Only create when working on multi-phase implementations
4. **Concise Content**: Keep notes brief and actionable, not verbose essays
5. **Temporary Nature**: These are working documents, not permanent documentation

**When to Create Tracking Docs:**
- ✅ Working on multi-phase PRD implementation and need to track progress across sessions
- ✅ Documenting architectural decisions made during implementation (context notes)
- ✅ Recording monthly observations to improve future development patterns
- ❌ NOT for debugging sessions (use git commits instead)
- ❌ NOT for bug fix summaries (use monthly bug-fix tracking)
- ❌ NOT for exploration or investigation notes (keep in temporary worknotes)
```

### Section 4: Directory Structure for Tracking Docs

```markdown
### Directory Structure for Tracking Docs

When creating allowed tracking documentation, follow this **exact structure**:

```
.claude/
├── progress/                                    # Phase progress tracking
│   └── [prd-name]/                             # Organized by PRD
│       ├── phase-1-progress.md                 # ONE per phase
│       ├── phase-2-progress.md
│       └── phase-3-progress.md
│
├── worknotes/                                   # Implementation context & notes
│   ├── [prd-name]/                             # Organized by PRD
│   │   ├── phase-1-context.md                  # ONE per phase
│   │   ├── phase-2-context.md
│   │   └── phase-3-context.md
│   │
│   ├── fixes/                                   # Bug fix tracking
│   │   └── bug-fixes-tracking-MM-YY.md         # ONE per month
│   │
│   └── observations/                            # Development observations
│       └── observation-log-MM-YY.md            # ONE per month
│
└── agents/                                      # Agent-specific configurations
    └── [agent-name]/                           # Agent prompts and configs
```

**Naming Conventions:**

| Document Type | Naming Pattern | Example |
|--------------|----------------|---------|
| Phase Progress | `phase-[N]-progress.md` | `phase-2-progress.md` |
| Phase Context | `phase-[N]-context.md` | `phase-2-context.md` |
| Bug Fix Tracking | `bug-fixes-tracking-MM-YY.md` | `bug-fixes-tracking-11-25.md` |
| Observation Log | `observation-log-MM-YY.md` | `observation-log-11-25.md` |

**Directory Organization Rules:**

1. **By PRD Name**: Group all progress and context docs by the PRD they implement
2. **By Month**: Group bug fixes and observations by month (MM-YY format, e.g., 11-25 for November 2025)
3. **One Per Phase**: Never create multiple progress or context docs for the same phase
4. **Consistent Naming**: Follow the exact naming patterns above
5. **No Nesting**: Don't create subdirectories within PRD folders (flat structure)

**Anti-Patterns to Avoid:**

```
❌ .claude/worknotes/2025-11-02-celery-event-loop-fix-context.md
   → Should be: git commit message or bug-fixes-tracking-11-25.md entry

❌ .claude/progress/listings-enhancements-v3/phase-1-progress-updated.md
   → Should be: Update existing phase-1-progress.md, not create new file

❌ .claude/worknotes/listings-enhancements-v3/phase-2-context-notes.md
   → Should be: phase-2-context.md (follow naming convention)

❌ .claude/worknotes/observations/nov-3-observations.md
   → Should be: observation-log-11-25.md (monthly, not daily)
```

**When Uncertain:**
- Ask: "Does this fit the allowed tracking structure?"
- If yes: Use the exact structure and naming above
- If no: It probably belongs in a git commit message or shouldn't be created
```

### Section 5: Allowed Documentation Buckets

```markdown
### Allowed Documentation Buckets

Only create documentation that falls into one of these categories:

**1. User Documentation**
- **Purpose**: Help end users accomplish tasks
- **Examples**: Setup guides, tutorials, how-to guides, troubleshooting, user walkthroughs
- **Location**: `/docs/guides/`, `/docs/user-guides/`

**2. Developer Documentation**
- **Purpose**: Help developers understand code and integrate with systems
- **Examples**: API documentation, SDK usage guides, integration guides, development setup
- **Location**: `/docs/api/`, `/docs/development/`, `/docs/integrations/`

**3. Architecture & Design Specifications**
- **Purpose**: Explain system design decisions and architecture
- **Examples**: Architecture Decision Records (ADRs), system diagrams, component specifications, design system docs
- **Location**: `/docs/architecture/`, `/docs/design/`

**4. README Files**
- **Purpose**: Document projects, packages, modules, and directories
- **Examples**: Project READMEs, package READMEs, feature READMEs
- **Location**: Root of project/package/module directory

**5. Configuration Documentation**
- **Purpose**: Explain how to configure and deploy systems
- **Examples**: Environment setup, deployment guides, configuration file documentation
- **Location**: `/docs/configuration/`, `/docs/deployment/`

**6. Test Documentation**
- **Purpose**: Document testing strategies and approaches
- **Examples**: Test plans, testing strategies, coverage goals, test data setup
- **Location**: `/docs/testing/`

**7. Product Documentation**
- **Purpose**: Define product requirements and implementation plans
- **Examples**: PRDs, implementation plans, feature specifications
- **Location**: `/docs/project_plans/`, `/docs/product/`

**8. Tracking Documentation (Limited Exception)**
- **Purpose**: Structured tracking of progress, context, observations, and bug fixes across development work
- **Location**: `.claude/progress/`, `.claude/worknotes/fixes/`, `.claude/worknotes/observations/`
- **Format**: Follows exact directory structure and naming conventions (see "Directory Structure for Tracking Docs")
- **Requirement**: ONLY allowed when following exact structured patterns; ad-hoc tracking documents are prohibited
```

### Section 6: Frontmatter Requirements

```markdown
### Frontmatter Requirements

**ALL new markdown documentation MUST include YAML frontmatter** (except tracking docs in `.claude/`):

```yaml
---
title: "Clear, Descriptive Title"
description: "Brief summary of what this documentation covers (1-2 sentences)"
audience: [ai-agents, developers, users, design, pm, qa]
tags: [relevant, tags, for, searchability]
created: 2025-11-03
updated: 2025-11-03
category: "documentation-category"
status: draft|review|published|deprecated
related:
  - /docs/path/to/related/doc.md
  - /docs/another/related/doc.md
---
```

**Frontmatter Fields:**

| Field | Purpose | Example |
|-------|---------|---------|
| `title` | Clear, searchable title | "Authentication API Documentation" |
| `description` | 1-2 sentence summary | "Comprehensive guide to auth endpoints and flows" |
| `audience` | Who should read this | `[developers, ai-agents]` or `[users, design]` |
| `tags` | Keywords for search | `[api, authentication, security, endpoints]` |
| `created` | Creation date | `2025-11-03` |
| `updated` | Last modification date | `2025-11-03` |
| `category` | Documentation bucket | `developer-documentation`, `user-guides`, `architecture` |
| `status` | Current state | `draft`, `review`, `published`, `deprecated` |
| `related` | Links to related docs | Array of relative file paths |

**Category Options**: `user-documentation`, `developer-documentation`, `architecture-design`, `api-documentation`, `configuration-deployment`, `test-documentation`, `product-planning`, `worknotes`

**Audience Options**: `users`, `developers`, `ai-agents`, `design`, `pm`, `qa`, `devops`
```

### Section 7: Documentation vs. Worknotes

```markdown
### Documentation vs. Worknotes

**Use `.claude/worknotes/` For:**
- Exploration and investigation logs
- Debugging sessions and findings
- Temporary implementation context
- Notes on things to remember
- Status updates and progress tracking
- Day-to-day session notes

**Use `/docs/` For:**
- Permanent, published documentation in allowed buckets
- Content meant to be read by users or future developers
- Stable information unlikely to become outdated
- Officially supported guides and references

**Never mix the two**: Don't store worknotes in `/docs/`, and don't treat worknotes as permanent documentation.
```

### Section 8: When to Ask Before Documenting

```markdown
### When to Ask Before Documenting

1. **Is this in an allowed bucket?** If not, don't create it.
2. **Is this explicitly tasked?** If it wasn't requested, is it absolutely necessary?
3. **Will this become outdated?** If it documents a temporary state or debugging, it doesn't belong.
4. **Is there already documentation?** Update existing docs instead of creating new ones.
5. **Is this a worknote instead?** If it's exploration or debugging, it belongs in `.claude/worknotes/`.

**Rule of Thumb**: If you have to ask whether documentation should be created, the answer is usually "no" unless it was explicitly tasked.
```

---

## Agent Updates Required

Update your AI agent configuration files to enforce the documentation policy. Each agent that creates documentation should include this section.

### Agent 1: Documentation Writer

**File Location**: `.claude/agents/tech-writers/documentation-writer.md`

Add this section to the agent's instructions (after the initial description):

```markdown
## Documentation Policy Enforcement

**CRITICAL**: As the primary documentation agent, you MUST enforce the project's documentation policy strictly.

### Core Principle: Document Only When Explicitly Needed

**ONLY create documentation when:**
1. Explicitly tasked in an implementation plan, PRD, or user request
2. Absolutely necessary to provide essential information to users or developers
3. It fits into a defined allowed documentation bucket (see CLAUDE.md)

**More documentation ≠ better.** Unnecessary documentation creates debt, becomes outdated, and misleads future developers.

### Before Creating ANY Documentation

Ask yourself:
1. **Is this in an allowed bucket?** (User, Developer, Architecture, README, Configuration, Test, Product, Tracking)
2. **Is this explicitly tasked?** Or is it absolutely necessary?
3. **Will this become outdated?** If documenting temporary state, it shouldn't be created
4. **Does existing documentation cover this?** Update existing docs instead

**Policy Check**: All documentation MUST fall into an allowed bucket (as defined in CLAUDE.md) OR be structured tracking documentation following the exact patterns in CLAUDE.md.

### Tracking Documentation Rules

If creating tracking documentation (progress, context, observations, bug fixes):

**ONLY these patterns are allowed:**
- `.claude/progress/[prd-name]/phase-[N]-progress.md` (ONE per phase)
- `.claude/worknotes/[prd-name]/phase-[N]-context.md` (ONE per phase)
- `.claude/worknotes/observations/observation-log-MM-YY.md` (ONE per month)
- `.claude/worknotes/fixes/bug-fixes-tracking-MM-YY.md` (ONE per month)

**NEVER create:**
- Scattered progress docs (use ONE per phase)
- Ad-hoc context files with date prefixes
- Weekly/daily observation logs (use monthly)
- Debugging summaries as docs (use git commits)

### Frontmatter Requirements

All documentation in `/docs/` MUST include complete YAML frontmatter:
- `title`, `description`, `audience`, `tags`, `created`, `updated`, `category`, `status`, `related`
- Tracking docs in `.claude/` do NOT require frontmatter

### When in Doubt

If uncertain whether documentation should be created, the answer is usually "no" unless explicitly tasked. Ask the user rather than creating documentation speculatively.
```

### Agent 2: Lead Architect (or primary implementation agent)

**File Location**: `.claude/agents/architects/lead-architect.md`

Add this section:

```markdown
## Documentation Policy Adherence

When delegating documentation tasks to the documentation-writer agent:

**Always explicitly task documentation work:**
```markdown
Task("documentation-writer", "Create API documentation for [endpoint] with examples")
Task("documentation-writer", "Write setup guide for [feature]")
```

**DO NOT allow undirected documentation creation.**

**For tracking documentation during implementation:**
- Use `.claude/progress/[prd-name]/phase-[N]-progress.md` for progress tracking
- Use `.claude/worknotes/[prd-name]/phase-[N]-context.md` for implementation notes
- Use `.claude/worknotes/fixes/bug-fixes-tracking-MM-YY.md` for bug fixes
- Use `.claude/worknotes/observations/observation-log-MM-YY.md` for observations
- Never create multiple scattered progress docs or ad-hoc context files

**Verify documentation fits allowed buckets** before delegating (User, Developer, Architecture, README, Configuration, Test, Product).
```

### Agent 3: Any Other Agents Creating Documentation

Add this general enforcement section to any agent that creates documentation:

```markdown
## Documentation Policy Compliance

When creating documentation as part of your work:

1. **Verify it's allowed**: Must fall into User, Developer, Architecture, README, Configuration, Test, or Product documentation buckets
2. **Is it tasked?**: Only create if explicitly tasked or absolutely necessary
3. **Use proper structure**: If tracking doc, follow exact patterns from CLAUDE.md
4. **Include frontmatter**: All `/docs/` documentation must have complete YAML frontmatter
5. **When in doubt**: Ask the user before creating documentation

See CLAUDE.md "Documentation Policy" section for complete guidelines.
```

---

## Directory Structure

### Complete Directory Layout

When implementing this policy, create this directory structure:

```
project-root/
├── .claude/
│   ├── progress/                           # Phase progress tracking
│   │   └── [prd-name]/                    # One folder per multi-phase PRD
│   │       ├── phase-1-progress.md
│   │       ├── phase-2-progress.md
│   │       └── phase-3-progress.md
│   │
│   ├── worknotes/                          # Implementation context & tracking
│   │   ├── [prd-name]/                    # Implementation decision context
│   │   │   ├── phase-1-context.md         # ONE per phase
│   │   │   ├── phase-2-context.md
│   │   │   └── phase-3-context.md
│   │   │
│   │   ├── fixes/                         # Bug fix tracking
│   │   │   └── bug-fixes-tracking-MM-YY.md
│   │   │
│   │   └── observations/                  # Development observations
│   │       └── observation-log-MM-YY.md
│   │
│   └── agents/                            # Agent configurations
│       └── [agent-name]/
│           └── agent-file.md
│
├── docs/
│   ├── api/                               # API documentation
│   │   ├── endpoints.md
│   │   └── schemas.md
│   │
│   ├── guides/                            # User and developer guides
│   │   ├── setup-guide.md
│   │   ├── getting-started.md
│   │   └── tutorials/
│   │
│   ├── development/                       # Developer documentation
│   │   ├── architecture.md
│   │   ├── setup.md
│   │   └── testing.md
│   │
│   ├── architecture/                      # Architecture & design docs
│   │   ├── adr/
│   │   └── design-system.md
│   │
│   ├── configuration/                     # Config and deployment docs
│   │   ├── environment-setup.md
│   │   └── deployment.md
│   │
│   ├── testing/                           # Test documentation
│   │   ├── test-strategy.md
│   │   └── test-data.md
│   │
│   └── project_plans/                     # PRDs and implementation plans
│       └── [prd-name]/
│           ├── PRD.md
│           └── IMPLEMENTATION_PLAN.md
│
└── CLAUDE.md                              # Project guidance (includes policy)
```

### Naming Conventions Quick Reference

| Item | Pattern | Example |
|------|---------|---------|
| Progress Docs | `phase-[N]-progress.md` | `phase-3-progress.md` |
| Context Docs | `phase-[N]-context.md` | `phase-2-context.md` |
| Bug Tracking | `bug-fixes-tracking-MM-YY.md` | `bug-fixes-tracking-11-25.md` |
| Observations | `observation-log-MM-YY.md` | `observation-log-11-25.md` |
| PRD Folders | `[prd-name]` | `listings-enhancements-v3` |

**Important**: No date prefixes in tracking doc filenames (except MM-YY for monthly files). Use directory organization instead.

---

## Frontmatter Specifications

### Complete Frontmatter Template for Permanent Documentation

All permanent documentation in `/docs/` MUST include this frontmatter at the beginning of the file:

```yaml
---
title: "Clear, Descriptive Title"
description: "Brief one or two sentence summary of what this documentation covers"
audience:
  - developers
  - ai-agents
tags:
  - relevant
  - searchable
  - keywords
created: YYYY-MM-DD
updated: YYYY-MM-DD
category: api | guide | architecture | configuration | testing | product | readme
status: draft | active | deprecated
related:
  - /docs/path/to/related/doc.md
  - /docs/another/related/doc.md
---
```

### Field Definitions

**title** (required, string)
- Clear, concise, searchable title
- Example: "Authentication API Reference"
- Guides: Use imperative format ("Setting up local development", not "Local development setup")

**description** (required, string)
- 1-2 sentence summary of content
- What should the reader understand after reading this?
- Example: "Complete API reference for authentication endpoints including OAuth, JWT, and API key authentication methods"

**audience** (required, array of strings)
- Who should read this documentation?
- Options: `developers`, `users`, `ai-agents`, `design`, `pm`, `qa`, `devops`, `maintainers`
- Use multiple if applicable: `[developers, ai-agents]`

**tags** (required, array of strings)
- Searchable keywords for finding this documentation
- 3-5 tags minimum, 8 maximum
- Use lowercase, hyphens for multi-word tags
- Examples: `[authentication, jwt, api, security, oauth]`

**created** (required, string)
- Date documentation was created in YYYY-MM-DD format
- Example: `2025-11-03`

**updated** (required, string)
- Date documentation was last updated in YYYY-MM-DD format
- Update this every time you modify the document
- Example: `2025-11-03`

**category** (required, string)
- Documentation type/bucket
- Options: `api`, `guide`, `architecture`, `configuration`, `testing`, `product`, `readme`
- Use exactly one category

**status** (required, string)
- Current state of documentation
- Options: `draft` (not ready), `active` (published), `deprecated` (outdated, keep for reference)
- Use `draft` for work-in-progress, `active` for published, `deprecated` if superseded

**related** (optional, array of strings)
- Paths to related documentation
- Use relative paths from project root: `/docs/api/endpoints.md`
- Omit if no related documentation

### Category Reference

| Category | Purpose | Location | Examples |
|----------|---------|----------|----------|
| `api` | API endpoint documentation | `/docs/api/` | Endpoint specs, schema references, error codes |
| `guide` | Step-by-step instructions | `/docs/guides/` | Setup guides, how-to docs, tutorials |
| `architecture` | System design and decisions | `/docs/architecture/` | ADRs, system diagrams, design decisions |
| `configuration` | Setup and deployment | `/docs/configuration/` | Environment setup, deployment guides, config files |
| `testing` | Test documentation | `/docs/testing/` | Test strategies, test data setup, coverage goals |
| `product` | Product planning | `/docs/project_plans/` | PRDs, implementation plans, feature specs |
| `readme` | Module/package documentation | `[module-root]/` | Package READMEs, feature READMEs |

### Example Frontmatter for Different Document Types

**API Documentation:**
```yaml
---
title: "Listings API Reference"
description: "Complete API reference for listings endpoints including CRUD operations, filtering, and search capabilities"
audience:
  - developers
  - ai-agents
tags:
  - api
  - listings
  - endpoints
  - rest
created: 2025-11-03
updated: 2025-11-03
category: api
status: active
related:
  - /docs/guides/listings-setup.md
  - /docs/development/authentication.md
---
```

**Setup Guide:**
```yaml
---
title: "Setting Up Local Development"
description: "Step-by-step guide to setting up the development environment including dependencies, database, and running services"
audience:
  - developers
tags:
  - setup
  - development
  - getting-started
  - docker
created: 2025-11-03
updated: 2025-11-03
category: guide
status: active
related:
  - /docs/configuration/environment-variables.md
  - /CLAUDE.md
---
```

**Architecture Decision Record:**
```yaml
---
title: "ADR-001: Database Schema Design for Multi-Tenant Architecture"
description: "Decision record documenting the choice to use row-level security (RLS) in PostgreSQL for multi-tenancy implementation"
audience:
  - developers
  - architects
tags:
  - adr
  - architecture
  - database
  - multi-tenant
  - rls
created: 2025-11-03
updated: 2025-11-03
category: architecture
status: active
related:
  - /docs/architecture/security-model.md
---
```

**Component/Package README:**
```yaml
---
title: "@project/ui - Component Library"
description: "React component library with reusable UI components, hooks, and utilities for the project"
audience:
  - developers
tags:
  - component-library
  - react
  - ui
  - package
created: 2025-11-03
updated: 2025-11-03
category: readme
status: active
related: []
---
```

### Important: Tracking Documents in .claude/

**Tracking documents in `.claude/` directories do NOT require frontmatter:**
- `.claude/progress/[prd-name]/phase-[N]-progress.md` - No frontmatter needed
- `.claude/worknotes/[prd-name]/phase-[N]-context.md` - No frontmatter needed
- `.claude/worknotes/fixes/bug-fixes-tracking-MM-YY.md` - No frontmatter needed
- `.claude/worknotes/observations/observation-log-MM-YY.md` - No frontmatter needed

These are working documents for internal use and should focus on concise, actionable content.

---

## Implementation Checklist

Follow these steps to implement the documentation policy in a new project:

### Phase 1: Setup (1-2 hours)

- [ ] Copy this specification to `.claude/DOCUMENTATION_POLICY_SPEC.md`
- [ ] Update CLAUDE.md with all 8 sections from "CLAUDE.md Implementation"
- [ ] Review and confirm CLAUDE.md sections match your project conventions
- [ ] Create directory structure in `.claude/`:
  - [ ] `.claude/progress/`
  - [ ] `.claude/worknotes/`
  - [ ] `.claude/worknotes/fixes/`
  - [ ] `.claude/worknotes/observations/`
- [ ] Ensure `/docs/` directory exists with subdirectories:
  - [ ] `/docs/api/`
  - [ ] `/docs/guides/`
  - [ ] `/docs/development/`
  - [ ] `/docs/architecture/`
  - [ ] `/docs/configuration/`
  - [ ] `/docs/testing/`
  - [ ] `/docs/project_plans/`

### Phase 2: Agent Updates (1-2 hours)

- [ ] Update documentation-writer agent (`.claude/agents/tech-writers/documentation-writer.md`)
  - [ ] Add "Documentation Policy Enforcement" section
  - [ ] Add policy check reminders to output format section
  - [ ] Add explicit anti-patterns section
- [ ] Update lead-architect or primary implementation agent
  - [ ] Add "Documentation Policy Adherence" section
  - [ ] Add task delegation guidelines
- [ ] Update any other agents that create documentation
  - [ ] Add "Documentation Policy Compliance" section

### Phase 3: Verification (30 minutes)

- [ ] Test directory structure exists and is accessible
- [ ] Create sample files to verify naming conventions:
  - [ ] `.claude/progress/sample-prd/phase-1-progress.md`
  - [ ] `.claude/worknotes/sample-prd/phase-1-context.md`
  - [ ] `.claude/worknotes/fixes/bug-fixes-tracking-11-25.md`
  - [ ] `.claude/worknotes/observations/observation-log-11-25.md`
- [ ] Verify frontmatter template works in a sample `/docs/` file
- [ ] Confirm CLAUDE.md is accessible and policy sections are clear

### Phase 4: Documentation Review (30 minutes)

- [ ] Audit existing documentation in `/docs/`
  - [ ] Check if all files have frontmatter (if not, add it)
  - [ ] Identify and remove scattered tracking documents
  - [ ] Move any tracking docs from `/docs/` to `.claude/` with proper naming
- [ ] Audit `.claude/` directory
  - [ ] Rename or consolidate scattered progress/context files to new structure
  - [ ] Archive old documentation that doesn't fit the policy

### Phase 5: Team Communication (1 hour)

- [ ] Share CLAUDE.md with team
- [ ] Explain core principle: "Document only when explicitly needed"
- [ ] Highlight prohibited patterns (especially scattered progress docs)
- [ ] Show directory structure examples
- [ ] Demonstrate frontmatter template
- [ ] Establish when to ask: "Is this tasked or absolutely necessary?"

### Phase 6: Ongoing Enforcement (Continuous)

- [ ] During code reviews: Check that documentation follows policy
- [ ] Before merging: Verify new documentation has proper frontmatter
- [ ] Monthly: Review `.claude/` directory for policy violations
- [ ] Quarterly: Audit `/docs/` for outdated or sprawl

---

## Example Documents

### Example 1: Phase Progress Document

**File**: `.claude/progress/listings-enhancements-v3/phase-2-progress.md`

```markdown
# Listings Enhancements v3 - Phase 2 Progress

**Phase:** 2 - Adjusted Value Renaming & Tooltips
**Status:** In Progress
**Started:** 2025-11-01
**Target Completion:** 2025-11-15

## Overview

Implementing global find-and-replace for "Adjusted Price" terminology and adding comprehensive valuation tooltips throughout the UI.

## Completed Tasks

- [x] UX-001: Global find-and-replace for "Adjusted Price" → "Adjusted Value"
  - Completed: 2025-11-02
  - Files modified: 12
  - Testing: Verified in staging

## In Progress

- [ ] UX-002: Create Valuation Tooltip Component
  - Status: 60% complete
  - Blockers: None
  - Target: 2025-11-08

- [ ] UX-003: Integrate Tooltip in Detail Page
  - Status: Not started
  - Dependencies: UX-002
  - Target: 2025-11-12

## Remaining Tasks

- [ ] Phase 2 Testing & QA
  - Estimated: 8 hours
  - Target: 2025-11-14

## Blockers

None currently.

## Key Decisions Made

1. Using Recharts for tooltip rendering (performance optimization)
2. Tooltip triggers on hover, not click (better UX)

## Next Steps

1. Complete UX-002 component implementation
2. Integrate into detail page
3. Comprehensive testing
4. Prepare for Phase 3 kickoff

---

**Last Updated:** 2025-11-03
**Updated By:** [AI Agent Name]
```

### Example 2: Phase Context Notes

**File**: `.claude/worknotes/listings-enhancements-v3/phase-2-context.md`

```markdown
# Phase 2 Implementation Context

**Phase:** 2 - Adjusted Value Renaming & Tooltips
**PRD:** `/docs/project_plans/listings-enhancements-v3/PRD.md`

## Terminology Changes

**Problem**: "Adjusted Price" is ambiguous; customers thought it was the actual selling price.

**Decision**: Rename all instances to "Adjusted Value"
- More accurately reflects that it's a valuation metric
- Includes all components' value adjustments
- Distinct from actual listing price

**Implementation Notes**:
- Used global find-and-replace (12 files affected)
- Verified in component tests (all passing)
- Updated Storybook documentation

## Valuation Tooltip Component

**Architecture Decision**:
- Component: `ValuationTooltip` in `apps/web/components/valuation/`
- Uses React Popover from shadcn/ui (already in deps)
- Displays: Component breakdown, applied rules, final value
- Triggered: On hover (not click, for better UX)

**Integration Points**:
- DetailPageLayout
- ListingCard (future phase)
- ComparisonTable (future phase)

**Data Source**:
- Fetches `listing.valuation_breakdown` JSON from API
- Computed server-side (no client-side recalculation)

## Performance Considerations

- Tooltip data is already loaded in listing query (no extra fetch)
- Uses React.memo to prevent re-renders
- Popover is lazy-mounted (only on hover)

## Testing Strategy

- Unit tests: Component rendering, data formatting
- Integration tests: Tooltip + detail page interaction
- E2E tests: Hover triggers tooltip, close button works

## Known Issues

None identified yet.

## Related Files

- `/apps/web/components/valuation/ValuationTooltip.tsx`
- `/apps/web/app/listings/[id]/page.tsx`
- `/docs/project_plans/listings-enhancements-v3/IMPLEMENTATION_PLAN.md`

---

**Created:** 2025-11-01
**Last Updated:** 2025-11-03
```

### Example 3: Monthly Bug-Fix Tracking

**File**: `.claude/worknotes/fixes/bug-fixes-tracking-11-25.md`

```markdown
# Bug Fixes - November 2025

## 2025-11-01: FastAPI DELETE Endpoint 204 Response Issue

**Issue**: API failed to start with `AssertionError: Status code 204 must not have a response body`

**Fix**: Added `response_model=None` to DELETE endpoint decorator
**Location**: `apps/api/dealbrain_api/api/listings.py:351`
**Commit**: 0e1cf35

## 2025-11-02: Celery AsyncIO Event Loop Conflict

**Issue**: Celery task `admin.recalculate_cpu_mark_metrics` failing with event loop conflicts

**Fix**: Replaced `asyncio.run()` with explicit event loop management and engine disposal
**Files**: `apps/api/dealbrain_api/tasks/admin.py`, `apps/api/dealbrain_api/tasks/baseline.py`
**Commit**: 8f93897

## 2025-11-03: Missing Delete Buttons & URL Path Issues

**Issue 1**: Delete buttons missing from listing cards and overview modal
**Fix**: Added delete buttons with proper error handling and confirmation dialogs
**Commit**: 4fd0263

**Issue 2**: DELETE endpoint requests failing with 404
**Fix**: Corrected API URL path (removed `/api` prefix)
**Commit**: 7bf9c52

**Issue 3**: Nested anchor tag warnings in React
**Fix**: Implemented `disableLink` prop pattern for EntityLink
**Commit**: 4fd0263
```

### Example 4: Monthly Observations Log

**File**: `.claude/worknotes/observations/observation-log-11-25.md`

```markdown
# Development Observations - November 2025

## Performance Patterns

- Virtual scrolling is critical for tables with 500+ rows (>40% performance gain observed)
- Debounced search at 200ms hits sweet spot between responsiveness and server load
- Memoization of components with complex valuation logic prevents unnecessary recalculations

## Code Patterns

- Async/await with proper event loop cleanup prevents Celery worker crashes
- Explicit `response_model=None` needed for 204 No Content in FastAPI 0.100+
- Component prop patterns (like `disableLink`) solve React DOM warnings elegantly

## Testing Insights

- Comprehensive E2E testing of delete operations prevents subtle routing bugs
- Integration tests catch event loop issues earlier than runtime

## Architecture Learnings

- Shared domain logic in `packages/core/` reduces duplicate validation logic by ~30%
- Repository pattern with async sessions scales better than synchronous queries

## Team Productivity

- Clear phase tracking docs reduce re-discovery work by ~25%
- Explicit context documentation accelerates agent context building

## Next Month Priorities

- Document performance optimization patterns as architectural guidelines
- Create detailed async/await patterns guide for Celery tasks
```

---

## Troubleshooting & Anti-Patterns

### Common Mistakes and How to Avoid Them

#### Mistake 1: Creating Multiple Progress Docs Per Phase

**Anti-Pattern:**
```
.claude/progress/listings-enhancements-v3/
├── phase-2-progress.md
├── phase-2-progress-updated-nov-2.md  ❌ WRONG
├── phase-2-progress-nov-3-update.md   ❌ WRONG
└── phase-2-notes.md                   ❌ WRONG
```

**Correct Pattern:**
```
.claude/progress/listings-enhancements-v3/
└── phase-2-progress.md                ✅ UPDATE THIS FILE
```

**Why**: Multiple files create confusion about which is current. Update one file instead.

**Fix**: Delete all but one, consolidate content, use exact naming.

---

#### Mistake 2: Date-Prefixed Context Files

**Anti-Pattern:**
```
.claude/worknotes/
├── 2025-11-02-celery-event-loop-fix-context.md    ❌ WRONG
├── 2025-11-03-delete-endpoint-fix-context.md      ❌ WRONG
└── 2025-11-04-nested-anchors-fix-context.md       ❌ WRONG
```

**Correct Pattern:**
```
.claude/worknotes/fixes/
└── bug-fixes-tracking-11-25.md                     ✅ CORRECT
```

**Why**: Debugging fixes shouldn't have separate context docs. Use monthly bug-fix tracking instead.

**Fix**: Delete scattered files, consolidate into `bug-fixes-tracking-MM-YY.md`.

---

#### Mistake 3: Weekly/Daily Observation Logs

**Anti-Pattern:**
```
.claude/worknotes/observations/
├── observation-log-nov-1.md     ❌ WRONG (daily)
├── observation-log-nov-2.md     ❌ WRONG (daily)
└── observation-log-week-1.md    ❌ WRONG (weekly)
```

**Correct Pattern:**
```
.claude/worknotes/observations/
└── observation-log-11-25.md     ✅ CORRECT (monthly)
```

**Why**: Monthly consolidation prevents fragmentation; time-bound observations force prioritization.

**Fix**: Consolidate all observations from a month into one file.

---

#### Mistake 4: Storing Worknotes in /docs/

**Anti-Pattern:**
```
docs/
├── worknotes/
│   └── implementation-notes.md           ❌ WRONG LOCATION
└── sessions/
    └── 2025-11-03-session-summary.md    ❌ WRONG LOCATION
```

**Correct Pattern:**
```
.claude/
└── worknotes/
    └── [organized by PRD and phase]      ✅ CORRECT LOCATION
```

**Why**: Permanent docs in `/docs/` should be published documentation, not internal working notes.

**Fix**: Move files to `.claude/worknotes/` with proper directory structure.

---

#### Mistake 5: Debugging Summaries as Documentation

**Anti-Pattern:**
```
docs/development/
└── encountered-event-loop-issues-nov-2.md    ❌ WRONG
```

**Correct Method:**
- Debugging findings → git commit message
- Pattern discovery → `.claude/worknotes/observations/observation-log-MM-YY.md`
- Implementation decisions → `.claude/worknotes/[prd-name]/phase-[N]-context.md`

**Why**: Debugging notes become outdated; permanent documentation should explain current systems, not past problems.

**Fix**: Convert to git commit, observation log entry, or context note as appropriate.

---

#### Mistake 6: Missing or Incomplete Frontmatter

**Anti-Pattern:**
```markdown
# API Documentation

Some documentation here...
```

**Correct Pattern:**
```markdown
---
title: "API Reference"
description: "Complete API reference including endpoints and schemas"
audience: [developers, ai-agents]
tags: [api, endpoints, reference]
created: 2025-11-03
updated: 2025-11-03
category: api
status: active
related:
  - /docs/guides/authentication.md
---

# API Documentation

Some documentation here...
```

**Why**: Frontmatter enables discoverability, version tracking, and audience targeting.

**Fix**: Add complete YAML frontmatter to all documentation files in `/docs/`.

---

#### Mistake 7: Consolidated Multi-Phase Progress Doc

**Anti-Pattern:**
```
.claude/progress/
└── phase-1-3-progress.md    ❌ WRONG (consolidates multiple phases)
```

**Correct Pattern:**
```
.claude/progress/[prd-name]/
├── phase-1-progress.md       ✅ ONE per phase
├── phase-2-progress.md
└── phase-3-progress.md
```

**Why**: One-per-phase tracking allows accurate phase completion dates and prevents confusion about which phase you're in.

**Fix**: Split into separate files, one per phase.

---

### Policy Enforcement Checklist for Code Reviews

Use this checklist when reviewing code or documentation:

**Before Merging Any Documentation:**
- [ ] Is documentation explicitly tasked or absolutely necessary?
- [ ] Does it fit an allowed bucket? (User, Developer, Architecture, README, Config, Test, Product, Tracking)
- [ ] If tracking doc: Does it follow exact structure? (Right directory, correct naming, one per phase/month)
- [ ] If permanent doc: Does it have complete frontmatter?
- [ ] No ad-hoc files created (check for date prefixes, unorganized worknotes, etc.)?
- [ ] No multiple scattered docs for same phase?
- [ ] No debugging summaries treated as permanent documentation?
- [ ] Directory structure matches specification?

**If Any Checks Fail:**
- Request changes before merging
- Point to CLAUDE.md policy section
- Provide example of correct structure

---

### Validation Testing

To verify policy implementation, run these quick checks:

**Check 1: Directory Structure**
```bash
# Verify required directories exist
ls -la .claude/progress/
ls -la .claude/worknotes/fixes/
ls -la .claude/worknotes/observations/
ls -la docs/api/
ls -la docs/guides/
```

**Check 2: Naming Compliance**
```bash
# Find non-conforming filenames
find .claude/progress -name "*progress*.md" | grep -v "phase-"
find .claude/worknotes -name "*.md" | grep -E "^[0-9]{4}-[0-9]{2}-"
find .claude/worknotes/observations -name "*.md" | grep -v "observation-log-"
```

**Check 3: Frontmatter Presence**
```bash
# Check for frontmatter in docs/
for f in docs/**/*.md; do
  if ! head -1 "$f" | grep -q "^---"; then
    echo "Missing frontmatter: $f"
  fi
done
```

**Check 4: Multiple Progress Docs Per Phase**
```bash
# Find PRDs with multiple progress docs
for prd in .claude/progress/*/; do
  count=$(ls -1 "$prd"phase-*-progress.md 2>/dev/null | wc -l)
  if [ "$count" -gt 3 ]; then
    echo "Multiple progress docs in $prd"
  fi
done
```

---

### Quick Reference: When to Create What

```
Task Type              → Document Type         → Location                  → Naming Pattern
────────────────────────────────────────────────────────────────────────────────────────
Setup instructions     → Guide                 → /docs/guides/             → explicit naming
API endpoints          → API reference        → /docs/api/                → explicit naming
Architecture decision  → ADR                   → /docs/architecture/       → adr-NNN.md
Implementation notes   → Context doc          → .claude/worknotes/[prd]/  → phase-N-context.md
Phase progress         → Progress tracker     → .claude/progress/[prd]/   → phase-N-progress.md
Bug fixes (1 month)    → Bug tracking         → .claude/worknotes/fixes/  → bug-fixes-tracking-MM-YY.md
Observations (1 month) → Observation log      → .claude/worknotes/obs/    → observation-log-MM-YY.md
Debugging notes        → Git commit message   → (commit history)          → detailed message
Session notes          → Temporary worknotes  → .claude/worknotes/temp/   → (keep temporary)
```

---

### Support & Questions

**Q: Can I create documentation if it wasn't explicitly tasked?**
A: Only if it's absolutely necessary to provide essential information to users or developers. When in doubt, ask rather than create.

**Q: How long should I keep tracking documents?**
A: Phase progress docs: Archive after phase complete. Context docs: Keep for 1 quarter, then decide if it becomes permanent. Monthly logs: Keep indefinitely for reference.

**Q: Can I have multiple observation logs?**
A: No. One per month only. Consolidate daily observations into monthly log.

**Q: What if documentation is outdated?**
A: Update it or mark status as `deprecated`. Don't create new docs; update existing ones.

**Q: Who enforces this policy?**
A: Everyone. AI agents through CLAUDE.md, humans through code review. Policy should be part of PR checklist.

---

## Summary

This specification provides everything needed to implement a professional, scalable documentation policy in any project. Key takeaways:

1. **Document Only When Explicitly Needed**: Reduces documentation debt, improves maintainability
2. **Strict Directory Structure**: Eliminates confusion about where things belong
3. **Clear Naming Conventions**: One-per-phase/month prevents fragmentation
4. **Frontmatter Requirements**: Enables discoverability and versioning
5. **Enforcement Points**: AI agents and code review enforce consistency
6. **Clear Anti-Patterns**: Team knows exactly what NOT to do

Implement this systematically, following the checklist in Phase-by-phase order. Once in place, documentation becomes a strength, not a source of technical debt.
