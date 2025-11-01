# Symbols Skill - Token-Efficient Codebase Navigation

A token-efficient codebase symbol analysis system for intelligent code discovery and exploration. Query and load pre-generated symbol graphs chunked by domain (UI, Web, API, Shared) instead of loading entire files. Reduce token usage by 60-95% compared to traditional codebase loading.

## What Is This?

The symbols skill enables you to navigate your codebase efficiently without loading full files or directories. It provides:

- **Token-Efficient Discovery**: Load only the symbols you need (5-20KB) instead of full files (200KB+) = 95%+ reduction
- **Domain-Specific Chunking**: Separate symbols by domain (UI primitives, Web app, API backend, Shared utilities)
- **API Layer Split**: For large backends, load only the layer you need (routers, services, repositories, schemas, cores)
- **Architectural Awareness**: All 8,888+ symbols tagged by architectural layer (router, service, repository, component, hook, etc.)
- **Precise References**: Get exact file paths and line numbers for immediate code lookup

## Quick Start

### 1. Initialize Configuration (First Time Only)

```bash
# Interactive setup wizard (recommended)
python .claude/skills/symbols/scripts/init_symbols.py

# Or select a template
cp .claude/skills/symbols/templates/react-typescript-fullstack.json symbols.config.json
```

### 2. Generate Symbols

```bash
# Extract all symbols
python .claude/skills/symbols/scripts/extract_symbols_typescript.py
python .claude/skills/symbols/scripts/extract_symbols_python.py
```

### 3. Query Symbols

```python
from scripts.symbol_tools import query_symbols, load_domain, load_api_layer

# Find React components with "Card" in name
cards = query_symbols(name="Card", kind="component", domain="ui", limit=10)

# Load entire UI domain for broader context
ui_context = load_domain(domain="ui", max_symbols=100)

# Load only service layer for backend development (50-80% token reduction)
services = load_api_layer("services", max_symbols=50)
```

## Documentation Index

### Getting Started

- **[SKILL.md](./SKILL.md)** - Complete skill reference
  - Overview, capabilities, when to use
  - All query functions and workflows
  - Symbol structure reference
  - Performance benchmarks

### Configuration

- **[CONFIG_README.md](./CONFIG_README.md)** - Configuration system
  - How to configure for your project
  - Configuration structure and options
  - Python API reference
  - Error handling and validation

- **[templates/](./templates/)** - Ready-to-use templates
  - [README.md](./templates/README.md) - Template guide
  - [QUICK_START.md](./templates/QUICK_START.md) - 3-step setup
  - 5 templates for common frameworks (React, Vue, Django, FastAPI, Next.js)

### Initialization

- **[scripts/INIT_README.md](./scripts/INIT_README.md)** - Initialization wizard
  - Interactive CLI setup
  - Template selection
  - Non-interactive automation

### Validation

- **[VALIDATION_QUICK_REF.md](./VALIDATION_QUICK_REF.md)** - Quick validation guide
  - CLI commands
  - Programmatic API
  - Exit codes

- **[docs/validation-guide.md](./docs/validation-guide.md)** - Complete validation documentation
  - Validation workflow
  - Troubleshooting
  - Report interpretation

### References

- **[references/usage_patterns.md](./references/usage_patterns.md)** - Detailed usage examples
  - Frontend development workflows
  - Backend API development workflows
  - Debugging patterns
  - Cross-domain development

- **[references/architecture_integration.md](./references/architecture_integration.md)** - Architecture guide
  - Symbol structure specification
  - Layered architecture mapping
  - Development workflow integration
  - Agent integration patterns

## Directory Structure

```
symbols/                              # Root skill directory
├── README.md                         # This file - start here!
├── SKILL.md                          # Complete skill reference
├── CONFIG_README.md                  # Configuration guide
├── VALIDATION_QUICK_REF.md          # Quick validation reference
├── symbols.config.json              # Configuration file (MeatyPrompts-specific)
├── symbols-config-schema.json       # JSON Schema for validation
│
├── scripts/                         # Python tools and utilities
│   ├── INIT_README.md              # Initialization wizard guide
│   ├── symbol_tools.py             # Core query and load functions
│   ├── init_symbols.py             # Interactive setup wizard
│   ├── extract_symbols_python.py   # Python symbol extractor
│   ├── extract_symbols_typescript.py # TypeScript symbol extractor
│   ├── merge_symbols.py            # Symbol merger for updates
│   ├── validate_symbols.py         # Symbol validation tool
│   ├── validate_schema.py          # Config schema validation
│   ├── add_layer_tags.py           # Add architectural layer tags
│   ├── split_api_by_layer.py       # Split API symbols by layer
│   ├── backfill_schema.py          # Backfill missing symbol fields
│   ├── config.py                   # Configuration loader
│   └── config_example.py           # Configuration usage examples
│
├── templates/                       # Configuration templates
│   ├── README.md                   # Template guide and selection criteria
│   ├── QUICK_START.md              # 3-step template setup
│   ├── INDEX.md                    # Template reference index
│   ├── react-typescript-fullstack.json  # Full-stack React + FastAPI
│   ├── python-fastapi.json         # FastAPI backend only
│   ├── nextjs-monorepo.json        # Next.js frontend monorepo
│   ├── vue-typescript.json         # Vue 3 application
│   ├── python-django.json          # Django backend
│   └── validate_templates.py       # Template validation utility
│
├── docs/                           # Detailed documentation
│   └── validation-guide.md         # Complete validation documentation
│
└── references/                     # Reference documentation
    ├── usage_patterns.md           # Detailed usage examples
    └── architecture_integration.md # Architecture integration guide
```

## Common Tasks

### Set Up Symbols for New Project

Use one of these approaches:

**Interactive Setup:**
```bash
python .claude/skills/symbols/scripts/init_symbols.py
```

**Template Selection:**
1. Choose template from `templates/` (see [selection guide](./templates/README.md))
2. Copy to project root: `cp templates/react-typescript-fullstack.json symbols.config.json`
3. Customize `projectName` and `symbolsDir`
4. Run extraction scripts

See: [templates/QUICK_START.md](./templates/QUICK_START.md)

### Generate Symbols for Existing Project

```bash
# Install validator
python .claude/skills/symbols/scripts/validate_schema.py

# Extract symbols
python .claude/skills/symbols/scripts/extract_symbols_typescript.py
python .claude/skills/symbols/scripts/extract_symbols_python.py

# Validate results
python .claude/skills/symbols/scripts/validate_symbols.py
```

### Query Symbols Programmatically

Frontend development:
```python
from symbol_tools import query_symbols, load_domain

# Find React components
components = query_symbols(kind="component", domain="ui", limit=20)

# Load web app context
web = load_domain(domain="web", max_symbols=100)
```

Backend development:
```python
from symbol_tools import load_api_layer

# Load only service layer for 84% token reduction
services = load_api_layer("services", max_symbols=50)

# Load schemas for DTO work
schemas = load_api_layer("schemas", max_symbols=50)
```

See: [references/usage_patterns.md](./references/usage_patterns.md)

### Validate Symbol Files

Quick check:
```bash
python .claude/skills/symbols/scripts/validate_symbols.py
```

Detailed report:
```bash
python .claude/skills/symbols/scripts/validate_symbols.py --verbose --json
```

See: [VALIDATION_QUICK_REF.md](./VALIDATION_QUICK_REF.md)

### Update Symbols After Code Changes

**Recommended approach** - Use symbols-engineer agent:
```markdown
Task("symbols-engineer", "Update symbols for the API domain after schema changes")
```

**Manual approach:**
```bash
python .claude/skills/symbols/scripts/extract_typescript_symbols.py
python .claude/skills/symbols/scripts/extract_python_symbols.py
python .claude/skills/symbols/scripts/merge_symbols.py
```

See: [SKILL.md](./SKILL.md#5-update-symbols)

## Key Capabilities

### Query Symbols

Find specific symbols by name, kind, domain, or layer:

```python
from symbol_tools import query_symbols

# Find all services
query_symbols(kind="function", name="Service", domain="api")

# Find components in UI domain
query_symbols(kind="component", domain="ui", limit=20)

# Find authentication layer
query_symbols(layer="auth", domain="api")
```

### Load Domains

Get complete symbol set for a specific domain:

```python
from symbol_tools import load_domain

# Load UI primitives
ui = load_domain(domain="ui", max_symbols=100)

# Load API with tests for debugging
api = load_domain(domain="api", include_tests=True)
```

### Load API Layers

For token efficiency, load only the backend layer you need:

```python
from symbol_tools import load_api_layer

# Services: 454 symbols, 284KB (84% reduction vs full API)
services = load_api_layer("services")

# Routers: 289 symbols, 241KB (87% reduction vs full API)
routers = load_api_layer("routers")

# Schemas: 570 symbols, 259KB (86% reduction vs full API)
schemas = load_api_layer("schemas")
```

### Search Patterns

Advanced pattern-based search with architectural filtering:

```python
from symbol_tools import search_patterns

# Find service layer patterns
search_patterns(layer="service", domain="api")

# Find router endpoints
search_patterns(pattern="router", layer="router")

# Find React components
search_patterns(pattern="^[A-Z].*", kind="component")
```

### Get Symbol Context

Get detailed information about a specific symbol:

```python
from symbol_tools import get_symbol_context

# Get component with props interface
context = get_symbol_context(
    name="PromptCard",
    include_related=True
)
```

## MeatyPrompts Configuration

This skill is pre-configured for MeatyPrompts with:

**Domains:**
- UI primitives (packages/ui): 755 symbols (191KB)
- Web app (apps/web): 1,088 symbols (629KB)
- API backend (services/api): 3,041 symbols (1.8MB)
- Shared utilities: Mapped to web domain

**API Layers** (for token-efficient backend work):
- Routers: 289 symbols (241KB) - HTTP endpoints
- Services: 454 symbols (284KB) - Business logic
- Repositories: 387 symbols (278KB) - Data access
- Schemas: 570 symbols (259KB) - DTOs and validation
- Cores: 1,341 symbols (703KB) - Models and utilities

**Test Files** (loaded separately):
- UI tests: 383 symbols (77KB)
- API tests: 3,621 symbols (1.8MB)

## Token Efficiency

Progressive loading strategy for optimal token usage:

| Approach | Token Usage | Efficiency |
|----------|-------------|-----------|
| Load full file | 200KB+ | Baseline |
| Load full domain | 191KB-1.8MB | 90% reduction |
| Load API layer | 241KB-703KB | 50-80% reduction |
| Query 20 symbols | 5KB | 97% reduction |
| Layer-filtered query | 1-3KB | 99%+ reduction |

**Example - Backend Development:**
- Full API domain: 1.8MB
- Service layer only: 284KB
- **Efficiency gain: 84% reduction**

See: [SKILL.md](./SKILL.md#performance) for detailed benchmarks.

## For Distribution

When sharing the symbols skill with other projects:

**Include:**
- All files in `scripts/`
- All files in `templates/`
- `symbols-config-schema.json`
- `SKILL.md`, `CONFIG_README.md`, `README.md` (documentation)
- `references/` (reference documentation)
- `docs/` (detailed guides)

**Exclude:**
- `symbols.config.json` (project-specific)
- `ai/symbols-*.json` (generated files)
- `.pytest_cache/`, `__pycache__/` (build artifacts)
- `.git/` (version control)

**For New Project:**
1. Copy all files listed above
2. Users run: `python scripts/init_symbols.py`
3. Users select their template
4. Users customize and generate symbols

See: [CONFIG_README.md](./CONFIG_README.md#project-specific-configuration) for migration guide.

## Performance Highlights

**Symbol Coverage:**
- Total symbols: 8,888+ (all include architectural layer tags)
- Complete codebase coverage: UI, Web, API, Shared

**Query Performance:**
- Symbol query: 0.1 seconds for ~20 results (~5KB context)
- Domain load: ~0.5 seconds for ~100 symbols (~15KB context)
- API layer load: ~0.3 seconds for ~50 symbols (~10KB context)

**Token Efficiency:**
- 95-99% reduction for targeted queries
- 84-87% reduction for API layer work
- 90%+ reduction for domain-specific work

**File Sizes:**
- UI domain: 191KB (755 symbols)
- Web domain: 629KB (1,088 symbols)
- API domain layers: 241KB-703KB each
- API tests: 1.8MB (3,621 symbols)
- UI tests: 77KB (383 symbols)

## Integration

### With MeatyPrompts

The symbols skill integrates with MeatyPrompts agents and commands:

- **codebase-explorer** - Uses symbols for efficient code discovery
- **symbols-engineer** - Expert in symbol updates and optimization
- **ui-engineer-enhanced** - Uses symbols for frontend work
- **documentation-writer** - Uses symbols for context-efficient docs

### Slash Commands

- `/symbols-query` - Query implementation
- `/symbols-search` - Search implementation
- `/load-symbols` - Domain loading
- `/symbols-update` - Symbol updates
- `/symbols-chunk` - Re-chunking symbols

See: [SKILL.md](./SKILL.md#integration-with-meatyprompts) for complete integration guide.

## Getting Help

### Understand the Skill

Start here: [SKILL.md](./SKILL.md)
- Complete overview and capabilities
- All query functions explained
- Workflows for different scenarios
- Performance and reference data

### Set Up Symbols

Quick setup: [templates/QUICK_START.md](./templates/QUICK_START.md)
Full guide: [CONFIG_README.md](./CONFIG_README.md)
Wizard: [scripts/INIT_README.md](./scripts/INIT_README.md)

### Use Symbols Effectively

Examples: [references/usage_patterns.md](./references/usage_patterns.md)
Architecture: [references/architecture_integration.md](./references/architecture_integration.md)

### Validate Symbols

Quick ref: [VALIDATION_QUICK_REF.md](./VALIDATION_QUICK_REF.md)
Detailed: [docs/validation-guide.md](./docs/validation-guide.md)

### Troubleshoot Issues

- Configuration: See [CONFIG_README.md](./CONFIG_README.md) "Error Handling"
- Templates: See [templates/README.md](./templates/README.md) "Troubleshooting"
- Validation: See [docs/validation-guide.md](./docs/validation-guide.md)
- Initialization: See [scripts/INIT_README.md](./scripts/INIT_README.md)

## Next Steps

1. **Understand the skill**: Read [SKILL.md](./SKILL.md)
2. **Configure for your project**: Use [templates/QUICK_START.md](./templates/QUICK_START.md)
3. **Generate symbols**: Run extraction scripts
4. **Start using symbols**: See [references/usage_patterns.md](./references/usage_patterns.md)

## Summary

The symbols skill provides **token-efficient codebase navigation** through smart symbol discovery:

- Query specific symbols instead of loading full files
- Load only what you need by domain or architectural layer
- Reduce token usage by 60-95% on development tasks
- Get precise code references with file:line locations
- Follow MeatyPrompts architectural patterns (Router → Service → Repository → DB)

Start with [SKILL.md](./SKILL.md) for complete documentation, or use [templates/QUICK_START.md](./templates/QUICK_START.md) to set up symbols for your project in 3 steps.
