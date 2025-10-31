# Architecture Integration

How symbols integrate with MeatyPrompts layered architecture and development workflow.

## Symbol Structure

Symbols are stored in domain-specific JSON files:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "domain": "UI|API|SHARED",
  "type": "MAIN|TESTS",
  "totalFiles": 163,
  "totalSymbols": 1291,
  "modules": [
    {
      "path": "apps/web/src/components/PromptCard.tsx",
      "symbols": [
        {
          "kind": "interface|function|class|method|type|hook|component",
          "name": "PromptCard",
          "line": 24,
          "summary": "React component that renders prompt card with title, description, tags..."
        }
      ]
    }
  ]
}
```

## Symbol Kinds

- `component` - React components
- `hook` - React hooks (useState, useEffect, custom hooks)
- `function` - Regular functions and arrow functions
- `class` - Class declarations
- `method` - Class methods
- `interface` - TypeScript interfaces
- `type` - TypeScript type aliases

## Available Symbol Files

Located in `ai/` directory:

- `ai/symbols-ui.json` (252KB) - UI components, hooks, pages
- `ai/symbols-api.json` (12KB) - Services, routers, repositories
- `ai/symbols-shared.json` (100KB) - Utilities, types, configs
- `ai/symbols-ui-tests.json` (77KB) - UI test files
- `ai/symbols-api-tests.json` (1KB) - API test files
- `ai/symbols-shared-tests.json` (6.6KB) - Shared test files
- `ai/symbols.graph.json` (447KB) - Complete codebase reference

## Layered Architecture Mapping

MeatyPrompts follows strict layered architecture: **Router → Service → Repository → DB**

### Layer Detection

The `search_patterns()` function automatically detects architectural layers:

```python
layer_mapping = {
    "router": {"kinds": ["function", "class"], "paths": ["router", "routes"]},
    "service": {"kinds": ["class", "function"], "paths": ["service"]},
    "repository": {"kinds": ["class"], "paths": ["repository", "repo"]},
    "component": {"kinds": ["component"], "paths": ["component"]},
    "hook": {"kinds": ["hook"], "paths": ["hook"]},
    "util": {"kinds": ["function", "class"], "paths": ["util", "helper"]},
}
```

### Validating Architecture Compliance

Use symbols to verify layered architecture:

```python
# Find all routers
routers = search_patterns(layer="router", domain="api")

# Find services they depend on
services = search_patterns(layer="service", domain="api")

# Find repositories used
repos = search_patterns(layer="repository", domain="api")

# Check for violations (e.g., router directly accessing repository)
```

## Symbol Relationship Analysis

### Component Relationships

Find a component and its related symbols:

```python
# Find component and its props interface
component = get_symbol_context(name="PromptCard", include_related=True)

# Returns:
# {
#   "symbol": {
#     "kind": "component",
#     "name": "PromptCard",
#     ...
#   },
#   "related": [
#     {
#       "kind": "interface",
#       "name": "PromptCardProps",
#       "relation": "props-interface"
#     }
#   ]
# }
```

### Service Relationships

Find a service and its dependencies:

```python
# Find service and its repository dependencies
service = get_symbol_context(name="PromptService", include_related=True)
```

## Integration with Development Workflow

### 1. Before Implementation (Exploration Phase)

Use symbols to understand existing patterns:

```python
# Find similar implementations
existing = query_symbols(name="similar_feature", limit=10)

# Load domain context
context = load_domain(domain="ui", max_symbols=100)

# Check architectural layer
layer_symbols = search_patterns(layer="service", domain="api")
```

### 2. During Implementation (Development Phase)

Reference symbols for consistency:

```python
# Get specific symbol context
reference = get_symbol_context(name="ExistingComponent", include_related=True)

# Find related utilities
utils = query_symbols(path="utils", domain="shared")
```

### 3. After Implementation (Review Phase)

Verify implementation follows patterns:

```python
# Check layer compliance
new_symbols = search_patterns(pattern="NewFeature", layer="service")

# Verify naming conventions
components = search_patterns(pattern="^[A-Z]", kind="component")
```

### 4. Maintenance (Debugging Phase)

Load test context for debugging:

```python
# Load main and test symbols
main = load_domain(domain="ui", include_tests=False)
tests = load_domain(domain="ui", include_tests=True)
```

## Regeneration and Updates

### Full Regeneration

Regenerate all symbol files:

```bash
/symbols-update --mode=full
/symbols-chunk
```

Or programmatically:

```python
update_symbols(mode="full", chunk=True)
```

### Incremental Updates

Update only changed files after git commits:

```python
# After git changes
changed_files = git.diff("HEAD~1", "HEAD", name_only=True)
update_symbols(mode="incremental", files=changed_files)
```

### Domain-Specific Updates

Update a specific domain:

```bash
/symbols-update --mode=domain --domain=ui
```

Or programmatically:

```python
update_symbols(mode="domain", domain="ui", chunk=True)
```

## Slash Command Integration

The symbols skill wraps these MeatyPrompts slash commands:

- `/symbols-query` - Query implementation
- `/symbols-search` - Search implementation
- `/load-symbols` - Domain loading implementation
- `/symbols-update` - Update implementation
- `/symbols-chunk` - Chunking implementation

## Agent Integration

### Specialized Agents Using Symbols

- `symbols-engineer` - Expert in symbol optimization
- `ui-engineer-enhanced` - Uses symbols for frontend work
- `codebase-explorer` - Uses symbols for code discovery

### Example Agent Workflow

```python
# UI Engineer agent workflow
1. Load UI symbols: load_domain(domain="ui", max_symbols=100)
2. Find existing patterns: query_symbols(name="Card", kind="component")
3. Get component context: get_symbol_context(name="PromptCard", include_related=True)
4. Implement feature following patterns
5. Update symbols if needed: update_symbols(mode="incremental")
```

## Configuration

Symbol chunking configuration is stored in `ai/chunking.config.json`:

```json
{
  "domains": {
    "ui": {
      "patterns": ["apps/web/**", "apps/mobile/**"],
      "exclude_tests": true
    },
    "api": {
      "patterns": ["services/api/**"],
      "exclude_tests": true
    },
    "shared": {
      "patterns": ["packages/**"],
      "exclude_tests": true
    }
  },
  "test_separation": true,
  "max_chunk_size": "250KB"
}
```

## Best Practices

1. **Domain Separation**: Load only the domain needed for current task
2. **Test Separation**: Load test symbols only when debugging
3. **Progressive Loading**: Start with queries, expand to domain loads as needed
4. **Layer Awareness**: Use layer filters to understand architectural patterns
5. **Regular Updates**: Update symbols after significant code changes
6. **Cache Results**: Store symbol results in conversation context to avoid re-querying
