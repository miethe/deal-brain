---
name: symbols
description: Token-efficient codebase navigation through intelligent symbol loading and querying. Use this skill when implementing new features (find existing patterns), exploring codebase structure, searching for components/functions/types, or understanding architectural layers. Reduces token usage by 60-95% compared to loading full files. Layer split enables 50-80% additional backend efficiency.
---

# Symbols - Intelligent Codebase Symbol Analysis

## Overview

Enable token-efficient navigation through pre-generated symbol graphs chunked by domain and separated from test files. Query symbols by name, kind, path, layer tag, or architectural layer without loading entire files. Load only the context needed for the current task. Reduces token usage by 95-99% compared to loading full files.

**Key Benefits:**
- 60-95% reduction in token usage vs loading full codebase
- Progressive loading strategy (load only what's needed)
- Domain-specific chunking for targeted context (configured per project)
- Layer split for 50-80% token reduction in backend work (load only specific architectural layers)
- Architectural layer tags for precise filtering (router, service, repository, component, hook, etc.)
- Architectural layer awareness for validating patterns
- Test file separation (loaded only when debugging)
- Precise code references with file paths and line numbers
- Complete codebase coverage including frontend and backend

## When to Use

Use this skill when:
- **Before implementing new features** - Find existing patterns to follow
- **Exploring codebase structure** - Understand how code is organized
- **Searching for code** - Locate components, functions, hooks, services, or types
- **Token-efficient context loading** - Avoid loading entire files or directories
- **Understanding architectural layers** - Verify Router → Service → Repository patterns
- **Cross-domain development** - Work across UI, API, and Shared code
- **Debugging** - Load relevant symbols including tests

Do NOT use this skill for:
- Reading actual file contents (use Read tool instead)
- Making code changes (symbols are read-only references)
- Runtime analysis (symbols are static analysis only)

## Key Capabilities

### Token-Efficient Layer Access

**Layer Split:**
- Backend domains can be divided into architectural layers for targeted loading
- Load only the layer you need: routers, services, repositories, schemas, cores (or project-specific layers)
- 50-80% token reduction vs loading entire domain

**Common Layer Types:**
- Routers/Controllers - HTTP endpoints and route handlers
- Services - Business logic layer
- Repositories - Data access layer
- Schemas/DTOs - Data transfer objects and request/response types
- Cores/Models - Domain models, core utilities, database entities

**Benefits:**
- Backend service dev: Load only service symbols instead of entire backend
- API endpoint work: Load only router symbols instead of entire backend
- DTO/schema work: Load only schema symbols instead of entire backend
- Typical reduction: 80-90% token savings

### Schema Standardization

**All symbols include:**
- Required fields: name, kind, path, line, signature, summary, layer
- Optional fields: parent, docstring, category
- Architectural layer tags for precise filtering

### Complete Coverage

Symbol files provide complete codebase coverage organized by domain:

**Frontend domains:**
- UI components and primitives
- Web/mobile application code (pages, routes, app-specific features)

**Backend domains:**
- API with layer-based access (targeted loading by architectural layer)
- Separate test file loading for debugging

Domain structure is configured in `symbols.config.json` and tailored to your project architecture.

## Core Capabilities

### 1. Query Symbols

Query symbols by name, kind, domain, or path without loading the entire symbol graph.

**When to use**: Find specific symbols, search by partial name, filter by type or location.

**How to use**:

Execute the Python function from `scripts/symbol_tools.py`:

```python
from symbol_tools import query_symbols

# Find all React components with "Card" in the name
results = query_symbols(name="Card", kind="component", domain="ui", limit=10)

# Find authentication-related functions
results = query_symbols(name="auth", kind="function", path="services")

# Get all custom hooks (summary only for quick scan)
results = query_symbols(kind="hook", domain="ui", summary_only=True)
```

**Parameters**:
- `name` (optional) - Symbol name (supports partial/fuzzy matching)
- `kind` (optional) - Symbol kind: component, hook, function, class, interface, type, method
- `domain` (optional) - Domain filter (configured per project: e.g., ui, web, api, shared, mobile)
- `path` (optional) - File path pattern (e.g., "components", "hooks", "services")
- `limit` (optional) - Maximum results to return (default: 20)
- `summary_only` (optional) - Return only name and summary (default: false)

**Returns**: List of matching symbols with file path, line number, domain, and summary.

### 2. Load Domain

Load complete symbol set for a specific domain (UI, Web, API, or Shared).

**When to use**: Need broader context for a domain, implementing features that touch multiple files within a domain.

**How to use**:

```python
from symbol_tools import load_domain

# Load UI symbols for UI component work (excludes tests)
ui_context = load_domain(domain="ui", include_tests=False, max_symbols=100)

# Load Web symbols for frontend app development
web_context = load_domain(domain="web", include_tests=False, max_symbols=100)

# Load API symbols with tests for debugging
api_context = load_domain(domain="api", include_tests=True)

# Load first 50 shared symbols for quick reference
shared_context = load_domain(domain="shared", max_symbols=50)
```

**Parameters**:
- `domain` (required) - Domain to load (configured per project: e.g., ui, web, api, shared, mobile)
- `include_tests` (optional) - Include test file symbols (default: false)
- `max_symbols` (optional) - Limit number of symbols returned (default: all)

**Returns**: Dict with domain, type, totalSymbols count, and symbols array.

**Token efficiency**: Load 50-100 symbols (~10-15KB) instead of full domain (~250KB)

**Note for Backend Domains:** For token efficiency, consider using `load_api_layer()` instead to load only the specific architectural layer you need (e.g., routers, services, repositories, schemas).

### 2.1. Load API Layer

Load symbols from a specific architectural layer for token-efficient backend development.

**When to use**: Backend development requiring only one architectural layer (e.g., routers, services, repositories, schemas). Provides 50-80% token reduction vs loading entire backend domain.

**How to use**:

```python
from symbol_tools import load_api_layer

# Load only service layer for backend development
services = load_api_layer("services")

# Load schemas for DTO work
schemas = load_api_layer("schemas", max_symbols=100)

# Load routers for endpoint development
routers = load_api_layer("routers")

# Load repositories for data access patterns
repositories = load_api_layer("repositories")

# Load cores for models and utilities
cores = load_api_layer("cores", max_symbols=200)
```

**Parameters**:
- `layer` (required) - Architectural layer to load (configured per project: e.g., routers, services, repositories, schemas, cores)
- `max_symbols` (optional) - Limit number of symbols returned (default: all)

**Returns**: Dict with layer, totalSymbols count, and symbols array.

**Token efficiency examples**:
- Backend service development: Load only service symbols instead of entire backend = **80-85% reduction**
- API endpoint work: Load only router symbols instead of entire backend = **85-90% reduction**
- DTO/schema work: Load only schema symbols instead of entire backend = **85-90% reduction**

**Common Layer Types** (configured per project):
- `routers` / `controllers` - HTTP endpoints, route handlers, validation
- `services` - Business logic, DTO mapping, orchestration
- `repositories` - Database operations, data access patterns
- `schemas` / `dtos` - Request/response data transfer objects
- `cores` / `models` - Domain models, core utilities, database entities

### 3. Search Patterns

Advanced pattern-based search with architectural layer tags for precise filtering.

**When to use**: Find symbols matching regex patterns, filter by architectural layer tag, validate layered architecture patterns.

**How to use**:

```python
from symbol_tools import search_patterns

# Find all service layer classes
services = search_patterns(pattern="Service", layer="service", domain="api")

# Find router endpoints
routers = search_patterns(pattern="router|Router", layer="router")

# Find React components following naming pattern
components = search_patterns(pattern="^[A-Z].*Card", layer="component", domain="ui")

# Find middleware implementations
middleware = search_patterns(layer="middleware", domain="api")

# Find all observability-tagged code
telemetry = search_patterns(layer="observability", domain="api")
```

**Parameters**:
- `pattern` (optional) - Search pattern (supports regex)
- `layer` (optional) - Architectural layer tag (configured per project, common types: router, service, repository, schema, model, component, hook, page, util, test)
- `priority` (optional) - Priority filter: high, medium, low
- `domain` (optional) - Domain filter (configured per project: e.g., ui, web, api, shared, mobile)
- `limit` (optional) - Maximum results (default: 30)

**Returns**: List of matching symbols with layer tag, domain, and summary.

**Layer Tags**: All symbols include a `layer` field enabling precise architectural filtering. Common backend layers: router, service, repository, schema, model, core, auth, middleware. Common frontend layers: component, hook, page, util. Test layer: test.

### 4. Get Symbol Context

Get full context for a specific symbol including definition location and related symbols.

**When to use**: Need detailed information about a specific symbol, want to find related symbols (props interfaces, same-file symbols).

**How to use**:

```python
from symbol_tools import get_symbol_context

# Get full context for a component (includes props interface)
context = get_symbol_context(name="Button", include_related=True)

# Get service definition with related symbols
service = get_symbol_context(
    name="UserService",
    file="backend/services/user_service.py",
    include_related=True
)
```

**Parameters**:
- `name` (required) - Exact symbol name
- `file` (optional) - File path if name is ambiguous
- `include_related` (optional) - Include related symbols (imports, usages, props) (default: false)

**Returns**: Dict with symbol info and optionally related symbols array.

**Relationship detection**: Automatically finds props interfaces for components, same-file symbols.

### 5. Update Symbols

Trigger symbol graph regeneration or incremental update (delegated to symbols-engineer agent).

**When to use**: After significant code changes, when symbol files are out of sync with codebase.

**Primary approach - Use symbols-engineer agent**:

```markdown
Task("symbols-engineer", "Update symbols for the API domain after schema changes")
Task("symbols-engineer", "Perform incremental symbol update for recent file changes")
Task("symbols-engineer", "Regenerate full symbol graph and re-chunk by domain")
```

The `symbols-engineer` agent handles:
- Analyzing code changes and determining scope of updates
- Running programmatic symbol extraction using domain-specific scripts
- Merging extracted symbols into existing graphs
- Re-chunking symbols by domain for optimal loading
- Validation of symbol accuracy and completeness

**Alternative - Manual slash commands**:

If using slash commands directly (less recommended):
- `/symbols-update` - Trigger incremental or full update
- `/symbols-chunk` - Re-chunk updated symbols by domain

**Programmatic approach** (for advanced use):

Symbol extraction can also be done programmatically using scripts:

```python
from symbol_tools import update_symbols

# Incremental update for recent changes
result = update_symbols(mode="incremental")

# Full regeneration (use sparingly)
result = update_symbols(mode="full", chunk=True)

# Update specific domain only
result = update_symbols(mode="domain", domain="ui")
```

**Parameters**:
- `mode` (optional) - Update mode: full, incremental, domain (default: incremental)
- `domain` (optional) - Specific domain to update (for domain mode)
- `files` (optional) - Specific files to update (for incremental mode)
- `chunk` (optional) - Re-chunk symbols after update (default: true)

**Note**: This function provides the interface but delegates to symbols-engineer agent for orchestration.

## Quick Start Workflow

### Frontend Development Workflow

```python
from symbol_tools import query_symbols, load_domain, get_symbol_context

# 1. Find existing React hooks in frontend app
hooks = query_symbols(kind="hook", domain="web", limit=20)

# 2. Find similar components in UI library
similar = query_symbols(name="Card", kind="component", domain="ui", limit=10)

# 3. Load web domain context for frontend patterns
web_symbols = load_domain(domain="web", max_symbols=100)

# 4. Find existing API hooks (useQuery, useMutation, etc)
api_hooks = query_symbols(path="hooks/queries", domain="web")

# 5. Check shared types and interfaces
types = query_symbols(path="types", kind="interface", domain="web")
```

**Result**: ~100 symbols loaded (~15KB) instead of full codebase = 95-97% reduction

### Backend Development Workflow

```python
from symbol_tools import load_api_layer, search_patterns, query_symbols

# Targeted layer loading (recommended)

# 1. Load only service layer for backend development
services = load_api_layer("services", max_symbols=50)

# 2. Load schemas for DTO patterns
schemas = load_api_layer("schemas", max_symbols=30)

# 3. Find similar routers in router layer
routers = load_api_layer("routers", max_symbols=20)

# Alternative: Pattern-based search across layers

# 4. Find service layer patterns
service_patterns = search_patterns(pattern="Service", layer="service", domain="api")

# 5. Find router endpoints
router_patterns = search_patterns(pattern="router", layer="router", domain="api")
```

**Result**: ~100 symbols loaded (~20KB) for targeted backend context = **80-90% token reduction** vs loading full backend domain

### Debugging Workflow

```python
from symbol_tools import get_symbol_context, load_domain, query_symbols

# 1. Load component and related symbols
component = get_symbol_context(name="Button", include_related=True)

# 2. Load test context to understand test cases
tests = load_domain(domain="ui", include_tests=True, max_symbols=30)

# 3. Search for related hooks in frontend app
hooks = query_symbols(path="hooks", name="user", kind="hook", domain="web")

# 4. Find state management patterns
state = query_symbols(path="contexts", kind="function", domain="web")

# 5. Find API client integration points
api_clients = query_symbols(path="lib/api", kind="function", domain="web")
```

**Result**: Full context including tests and frontend patterns loaded (~20KB instead of reading all files)

## Progressive Loading Strategy

Follow this three-tier approach for optimal token efficiency:

**Tier 1: Essential Context (25-30% of budget)**
- Load 10-20 symbols directly related to current task
- Focus on interfaces, types, and primary components/services
- Use: `query_symbols(name="Button", limit=10)`

**Tier 2: Supporting Context (15-20% of budget)**
- Load related patterns and utilities
- Include cross-domain interfaces
- Use: `load_domain(domain="shared", max_symbols=50)`

**Tier 3: On-Demand Context (remaining budget)**
- Specific lookups when needed
- Deep dependency analysis
- Use: `get_symbol_context(name="Service", include_related=True)`

## Programmatic Symbol Extraction

Symbol graph updates can be performed programmatically using domain-specific extraction scripts. These scripts reduce manual work by automatically pulling structural information and summaries from code, allowing the symbols-engineer agent to focus on refinement.

### Available Extraction Scripts

**Python Symbol Extractor** (`scripts/extract_symbols_python.py`):
- Extracts Python modules, classes, functions, methods
- Pulls function signatures and docstrings
- Filters out test files and internal imports
- Supports batch processing for entire directories
- Output: JSON-compatible symbol metadata

Usage:
```bash
python .claude/skills/symbols/scripts/extract_symbols_python.py path/to/backend/app
```

**TypeScript/JavaScript Symbol Extractor** (`scripts/extract_symbols_typescript.py`):
- Extracts TypeScript interfaces, types, functions, classes
- Extracts React components and hooks
- Parses JSDoc comments for summaries
- Handles monorepo structures and nested directories
- Output: JSON-compatible symbol metadata

Usage:
```bash
python .claude/skills/symbols/scripts/extract_symbols_typescript.py path/to/frontend/src
```

**Symbol Merger** (`scripts/merge_symbols.py`):
- Merges programmatically extracted symbols into existing graphs
- Handles incremental updates
- Maintains symbol relationships and cross-references
- Validates for consistency and duplicates

Usage:
```bash
python .claude/skills/symbols/scripts/merge_symbols.py --domain=api --input=extracted_symbols.json
```

### Workflow: Programmatic Updates

1. **Analyze changes**: Determine which domains/files changed
2. **Extract symbols**: Run domain-specific extractor on changed files
3. **Merge results**: Use symbol merger to integrate with existing graph
4. **Validate**: Verify accuracy and completeness
5. **Chunk**: Re-chunk symbols by domain for optimal loading

**Recommended**: Use `symbols-engineer` agent to orchestrate this workflow.

## Symbol Structure Reference

Symbols are stored in domain-specific JSON files in the `ai/` directory. All symbols include a `layer` field for architectural filtering.

**Symbol files are organized by domain as configured in `symbols.config.json`. Common domains include:**

- **UI/Frontend Components** - UI primitives, design system components
- **Web/Mobile Application** - Application-specific code (pages, routes, features)
- **Backend API** - Backend code, optionally split by architectural layer
- **Shared/Common** - Shared utilities, types, and helpers

**Backend Layer Files** (when using layer-based split for token efficiency):
- `symbols-{domain}-routers.json` - HTTP endpoints and route handlers
- `symbols-{domain}-services.json` - Business logic layer
- `symbols-{domain}-repositories.json` - Data access layer
- `symbols-{domain}-schemas.json` - DTOs and request/response types
- `symbols-{domain}-cores.json` - Domain models, core utilities, database entities

**Test symbol files** (loaded separately, on-demand for debugging):
- `symbols-{domain}-tests.json` - Test helpers, fixtures, and test cases

**Note**: Actual file names, symbol counts, and organization depend on your project configuration in `symbols.config.json`.

**Symbol structure example**:
```json
{
  "name": "Button",
  "kind": "component",
  "file": "src/components/Button.tsx",
  "line": 15,
  "domain": "frontend",
  "layer": "component",
  "summary": "Reusable button component with variants"
}
```

**Symbol kinds**:
- `component` - React components
- `hook` - React hooks (useState, useEffect, custom hooks)
- `function` - Regular functions and arrow functions
- `class` - Class declarations
- `method` - Class methods
- `interface` - TypeScript interfaces
- `type` - TypeScript type aliases

**Layer tags** (all symbols include one, configured per project):
- Common backend layers: `router`, `service`, `repository`, `schema`, `model`, `core`, `auth`, `middleware`
- Common frontend layers: `component`, `hook`, `page`, `util`
- Test layer: `test`

## Resources

### scripts/symbol_tools.py

Python implementation of all symbol query functions. Contains:
- `query_symbols()` - Query by name, kind, domain, path
- `load_domain()` - Load complete domain context
- `load_api_layer()` - Load specific API architectural layer
- `search_patterns()` - Pattern-based search with layer awareness
- `get_symbol_context()` - Get specific symbol with related symbols
- `update_symbols()` - Trigger regeneration

Execute directly or import functions as needed:

```bash
# Run examples
python .claude/skills/symbols/scripts/symbol_tools.py
```

```python
# Import in code
from symbol_tools import query_symbols, load_domain, load_api_layer
```

### references/usage_patterns.md

Detailed examples and patterns for common development scenarios:
- Frontend development examples
- Backend API development examples
- Cross-domain development patterns
- Debugging workflows
- Token efficiency guidelines
- Integration patterns with agents

Read this reference for comprehensive examples of each workflow type.

### references/architecture_integration.md

Deep dive into architecture integration:
- Symbol structure specification
- Layered architecture mapping (e.g., Router → Service → Repository → DB)
- Symbol relationship analysis
- Development workflow integration
- Regeneration and update strategies
- Slash command integration
- Agent integration patterns
- Configuration reference

Read this reference to understand how symbols map to your project's architectural patterns.

## Project Integration

### Slash Commands

The symbols skill can integrate with project-specific slash commands:
- `/symbols-query` - Query implementation
- `/symbols-search` - Search implementation
- `/load-symbols` - Domain loading implementation
- `/symbols-update` - Update implementation
- `/symbols-chunk` - Chunking implementation

### Related Agents

Common agent patterns that use symbols:
- `symbols-engineer` - Expert in symbol optimization and graph management
- `codebase-explorer` - Uses symbols for efficient code discovery
- Frontend/backend engineers - Use symbols for targeted context loading

### Architecture Integration

Symbols understand and validate project-specific layered architectures. Common patterns include:

**Backend layers:**
- **Router/Controller layer** - HTTP endpoints, validation, request handling
- **Service layer** - Business logic, orchestration, DTO mapping
- **Repository layer** - Database operations, data access patterns
- **Schema/DTO layer** - Request/response data structures
- **Model layer** - Domain models and database entities

**Frontend layers:**
- **Component layer** - UI components and design system primitives
- **Hook layer** - React hooks, state management, data fetching
- **Page layer** - Application pages, routes, views
- **Util layer** - Shared utilities and helpers

Use `search_patterns()` with `layer` parameter to filter by architectural layer.

## Performance

**Symbol Coverage** (varies by project):
- Symbol counts and file sizes depend on codebase size and configuration
- All symbols include layer tags for precise filtering
- Domain-specific organization enables targeted loading
- Test symbols separated for on-demand debugging

**Token Efficiency Gains**:
- Full codebase loading: Large (avoid when possible)
- Domain-specific files: Targeted to your task (50-80% reduction)
- Layer-specific files: Even more targeted (70-90% reduction vs full domain)
- Typical query: 10-20 symbols (~2-5KB, 95-99% reduction)
- Layer-filtered queries: 5-15 symbols (~1-3KB, 99%+ reduction)

**Progressive Loading Example**:
1. Essential context: 20 symbols = ~5KB (95-99% reduction vs full codebase)
2. Supporting context: +30 symbols = ~12KB total (95-97% reduction)
3. On-demand lookup: +10 symbols = ~15KB total (95-97% reduction)

**Backend Development Example**:
- Loading entire backend domain: Large
- Loading single layer (e.g., services): 70-90% smaller
- **Typical efficiency gain: 80-90% token reduction**

**Comparison to loading full files**:
- Loading full files for context: ~200KB+
- Using domain-specific symbols: ~15KB (93% reduction)
- Using layer-specific symbols: ~10KB (95% reduction)
