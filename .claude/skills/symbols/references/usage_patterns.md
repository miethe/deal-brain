# Symbol Usage Patterns

Detailed examples and patterns for using symbol tools effectively.

## Frontend Development

### Before Creating a New Component

```python
# 1. Find existing similar components
similar = query_symbols(name="Card", kind="component", domain="ui", limit=10)

# 2. Load UI context for pattern reference
ui_symbols = load_domain(domain="ui", max_symbols=100)

# 3. Check for related types/interfaces
types = query_symbols(path="types", kind="interface", domain="shared")

# 4. Search for specific hooks you might need
hooks = query_symbols(kind="hook", domain="ui", summary_only=True)
```

**Result**: ~100 symbols loaded (~15KB) instead of full 447KB graph = 97% reduction

### Component Development Example

**Scenario**: Need to create a new "TagSelector" component

```python
# 1. Find similar components
selectors = query_symbols(name="Selector", kind="component", domain="ui")
# Returns: PromptSelector, CategorySelector, etc.

# 2. Get detailed context for reference
context = get_symbol_context(name="PromptSelector", include_related=True)
# Returns: Component + Props interface + related types

# 3. Check for existing tag-related code
tags = query_symbols(name="tag", domain="ui", limit=15)
# Returns: TagInput, TagList, useTagsQuery, etc.
```

**Result**: Found 3 similar components to reference, avoiding duplicate implementation

## Backend Development

### Before Implementing a New API Endpoint

```python
# 1. Load API layer symbols
api_symbols = load_domain(domain="api", include_tests=False)

# 2. Find similar routers
routers = search_patterns(pattern="router", layer="router", domain="api")

# 3. Find service layer patterns
services = search_patterns(pattern="Service", layer="service", domain="api")

# 4. Load shared DTOs and types
dtos = query_symbols(path="schemas", kind="class", domain="api")
```

**Result**: ~50 symbols loaded (~8KB) for API context

### API Development Example

**Scenario**: Add new collaboration API endpoints

```python
# 1. Load API context
api_symbols = load_domain(domain="api", max_symbols=50)

# 2. Find existing routers for patterns
routers = search_patterns(pattern="router", layer="router")
# Returns: prompt_router, user_router, etc.

# 3. Find services to understand business logic patterns
services = search_patterns(layer="service", domain="api")
# Returns: PromptService, UserService, etc.

# 4. Get specific service context
service = get_symbol_context(name="PromptService", include_related=True)
# Returns: Service + Repository + DTOs
```

**Result**: Understand MeatyPrompts patterns: Router → Service → Repository → DB

## Cross-Domain Development

### For Full-Stack Features

```python
# 1. Load essential shared types first
shared = load_domain(domain="shared", max_symbols=50)

# 2. Query UI components needed
components = query_symbols(name="Prompt", kind="component", domain="ui", limit=5)

# 3. Find API services
services = query_symbols(name="prompt", kind="class", domain="api")

# 4. Get context for specific symbols
card_context = get_symbol_context(name="PromptCard", include_related=True)
```

### Full-Stack Example

**Scenario**: Add user avatar support across web and API

```python
# 1. Load shared types for consistency
shared = load_domain(domain="shared", max_symbols=50)

# 2. Find UI components for avatars
avatars = query_symbols(name="avatar", kind="component", domain="ui")

# 3. Find API user-related symbols
user_api = query_symbols(name="user", domain="api")

# 4. Get user service context
user_service = get_symbol_context(name="UserService", include_related=True)
```

**Result**: Complete cross-domain understanding without loading full codebase

## Debugging and Testing

### When Debugging Issues

```python
# 1. Load main context
main_symbols = load_domain(domain="ui", include_tests=False)

# 2. Load test context for debugging
test_symbols = load_domain(domain="ui", include_tests=True)

# 3. Search for test patterns
tests = search_patterns(pattern="test.*Card", domain="ui")
```

### Debugging Example

**Scenario**: Component not rendering correctly

```python
# 1. Load component and related symbols
component = get_symbol_context(name="PromptCard", include_related=True)

# 2. Load test context to understand test cases
tests = load_domain(domain="ui", include_tests=True, max_symbols=30)

# 3. Search for related hooks
hooks = query_symbols(path="hooks", name="prompt", kind="hook")

# 4. Find state management patterns
state = query_symbols(path="contexts", kind="function", domain="ui")
```

**Result**: Full context including tests loaded (~20KB instead of reading all files)

## Architectural Analysis

### Understanding Layer Dependencies

```python
# Find all routers
routers = search_patterns(layer="router", domain="api")

# Find services they depend on
services = search_patterns(layer="service", domain="api")

# Find repositories used
repos = search_patterns(layer="repository", domain="api")

# Validate layered architecture: Router → Service → Repository → DB
```

### Pattern Detection

```python
# Find all custom hooks
hooks = query_symbols(kind="hook", domain="ui")

# Find naming pattern violations
components = search_patterns(pattern="^[a-z]", kind="component")  # Should be PascalCase

# Find service classes
services = search_patterns(pattern="Service$", layer="service")
```

## Token Efficiency Guidelines

### Progressive Loading Strategy

**Tier 1: Essential Context (25-30% of budget)**
- Load 10-20 symbols directly related to current task
- Focus on interfaces, types, and primary components/services
- Example: `query_symbols(name="PromptCard", limit=10)`

**Tier 2: Supporting Context (15-20% of budget)**
- Load related patterns and utilities
- Include cross-domain interfaces
- Example: `load_domain(domain="shared", max_symbols=50)`

**Tier 3: On-Demand Context (remaining budget)**
- Specific lookups when needed
- Deep dependency analysis
- Historical pattern analysis
- Example: `get_symbol_context(name="Service", include_related=True)`

### Token Budget Management

| Domain | Typical Size | Recommended Initial Load | Token Usage |
|--------|--------------|-------------------------|-------------|
| UI | 252KB, 1291 symbols | 50-100 symbols | ~10-15KB |
| API | 12KB, 150 symbols | 30-50 symbols | ~5-8KB |
| Shared | 100KB, 800 symbols | 30-75 symbols | ~8-12KB |
| Tests | 85KB total | Load on-demand only | 0KB initially |

### Best Practices

1. **Start narrow, expand contextually**: Begin with specific queries, expand domain load as needed
2. **Use summary_only for quick scans**: Get overview without full details
3. **Separate test context**: Load tests only when debugging
4. **Query incrementally vs loading entire domains**: More targeted = fewer tokens
5. **Cache results in conversation context**: Avoid re-querying same symbols

## Integration Patterns

### With Agents

**UI Engineer Integration:**
```python
# Before component work
ui_context = load_domain(domain="ui", max_symbols=100)
shared_types = query_symbols(kind="interface", domain="shared", path="types")
```

**Backend Architect Integration:**
```python
# Before API design
api_patterns = search_patterns(layer="service", domain="api")
dtos = query_symbols(path="schemas", kind="class")
```

**Code Reviewer Integration:**
```python
# Load context for review
file_symbols = query_symbols(path="components/PromptCard", domain="ui")
related = get_symbol_context(name="PromptCard", include_related=True)
```

### With Other Skills

**With Code Search:**
- Use symbols to find candidates, then read specific files
- Symbols provide overview, code search provides details

**With Documentation:**
- Generate API docs from symbol summaries
- Create component catalogs from UI symbols

**With Testing:**
- Load test symbols to understand coverage
- Find test patterns for new features

## Performance Metrics

### Token Efficiency Gains

- Full graph: 447KB
- UI domain only: 252KB (44% reduction)
- API domain only: 12KB (97% reduction)
- Shared domain only: 100KB (78% reduction)
- Typical query: 10-20 symbols (~2-5KB, 99% reduction)

### Progressive Loading Example

1. Essential context: 20 symbols = ~5KB (99% reduction)
2. Supporting context: +30 symbols = ~12KB total (97% reduction)
3. On-demand lookup: +10 symbols = ~15KB total (97% reduction)

### Comparison

- Loading full files for context: ~200KB+
- Using symbol skill: ~15KB
- **Efficiency gain: 93%**
