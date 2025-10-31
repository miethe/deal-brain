# Symbols Configuration System

The symbols skill configuration system enables project-agnostic symbol extraction and analysis. It separates project-specific settings from the core symbol tools, making the skill reusable across different projects.

## Files

### Configuration Files

- **`symbols.config.json`** - Project configuration (MeatyPrompts-specific settings)
- **`symbols-config-schema.json`** - JSON Schema for validation and IDE support

### Python Modules

- **`scripts/config.py`** - Configuration loader with validation and helpers
- **`scripts/config_example.py`** - Usage examples and migration patterns

## Quick Start

### Using the Configuration

```python
from config import get_config

# Load configuration (singleton)
config = get_config()

# Get symbols directory
symbols_dir = config.get_symbols_dir()
# Returns: /path/to/project/ai

# Get domain file
ui_file = config.get_domain_file("ui")
# Returns: /path/to/project/ai/symbols-ui.json

# Get API layer file (token-efficient)
services_file = config.get_api_layer_file("services")
# Returns: /path/to/project/ai/symbols-api-services.json

# Get extraction config
python_config = config.get_extraction_config("python")
# Returns: ExtractionConfig with directories, extensions, excludes
```

### Configuration Structure

```json
{
  "$schema": "./symbols-config-schema.json",
  "projectName": "MeatyPrompts",
  "symbolsDir": "ai",
  "domains": {
    "ui": {
      "file": "symbols-ui.json",
      "description": "UI primitives",
      "testFile": "symbols-ui-tests.json",
      "enabled": true
    },
    "api": { ... }
  },
  "apiLayers": {
    "routers": {
      "file": "symbols-api-routers.json",
      "description": "API route handlers"
    },
    "services": { ... }
  },
  "extraction": {
    "python": {
      "directories": ["services/api"],
      "extensions": [".py"],
      "excludes": ["__pycache__", "*.pyc"]
    },
    "typescript": { ... }
  }
}
```

## Configuration Reference

### Required Fields

#### `projectName` (string)
Name of the project using this symbol system.

**Example:** `"MeatyPrompts"`

#### `symbolsDir` (string)
Directory where symbol files are stored, relative to project root.

**Example:** `"ai"`, `"symbols"`, `".symbols"`

#### `domains` (object)
Domain-specific symbol file configurations. At least one domain is required.

**Domain structure:**
- `file` (required): Symbol file name (must match pattern `symbols-*.json`)
- `description` (required): Human-readable description
- `testFile` (optional): Test symbol file name (pattern `symbols-*-tests.json`)
- `enabled` (optional): Whether domain is active (default: `true`)

**Example:**
```json
"domains": {
  "ui": {
    "file": "symbols-ui.json",
    "description": "UI primitives from packages/ui",
    "testFile": "symbols-ui-tests.json",
    "enabled": true
  }
}
```

#### `extraction` (object)
Symbol extraction configuration by language. Both `python` and `typescript` are required.

**Language structure:**
- `directories` (required): Array of directories to scan
- `extensions` (required): Array of file extensions (e.g., `[".py"]`)
- `excludes` (optional): Array of patterns to exclude
- `excludeTests` (optional): Exclude test files (default: `true`)
- `excludePrivate` (optional): Exclude private symbols (default: `false`)

**Example:**
```json
"extraction": {
  "python": {
    "directories": ["services/api"],
    "extensions": [".py"],
    "excludes": ["__pycache__", "*.pyc", ".venv"],
    "excludeTests": true,
    "excludePrivate": false
  }
}
```

### Optional Fields

#### `apiLayers` (object)
Layer-specific API symbol files for token-efficient access. Useful for large APIs.

**Layer structure:** Same as domains (file, description, enabled)

**Example:**
```json
"apiLayers": {
  "routers": {
    "file": "symbols-api-routers.json",
    "description": "API route handlers"
  },
  "services": {
    "file": "symbols-api-services.json",
    "description": "Business logic services"
  }
}
```

#### `metadata` (object)
Optional metadata about the configuration.

**Fields:**
- `version`: Configuration schema version
- `author`: Configuration author or maintainer
- `lastUpdated`: ISO 8601 date of last update
- `description`: Additional notes

## Python API Reference

### `SymbolConfig` Class

Main configuration class with validation and helpers.

#### Methods

##### `get_symbols_dir() -> Path`
Get absolute path to symbols directory.

##### `get_domain_file(domain: str) -> Path`
Get absolute path to domain symbol file.

**Raises:** `ConfigurationError` if domain not found or disabled

##### `get_test_file(domain: str) -> Optional[Path]`
Get absolute path to test symbol file, or None if not configured.

##### `get_api_layer_file(layer: str) -> Path`
Get absolute path to API layer symbol file.

**Raises:** `ConfigurationError` if layer not found or API layers not configured

##### `get_domains() -> List[str]`
Get list of all configured domain names (enabled and disabled).

##### `get_enabled_domains() -> List[str]`
Get list of enabled domain names only.

##### `get_api_layers() -> List[str]`
Get list of all configured API layer names, or empty list if not configured.

##### `get_enabled_api_layers() -> List[str]`
Get list of enabled API layer names, or empty list if not configured.

##### `get_extraction_config(language: Literal["python", "typescript"]) -> ExtractionConfig`
Get extraction configuration for a language.

**Returns:** `ExtractionConfig` dataclass with:
- `directories`: List of directory paths
- `extensions`: List of file extensions
- `excludes`: List of exclude patterns
- `exclude_tests`: Boolean flag
- `exclude_private`: Boolean flag

##### `get_extraction_directories(language: Literal["python", "typescript"]) -> List[Path]`
Get absolute paths to extraction directories for a language.

### Module Functions

#### `get_config(config_path: Optional[Path] = None, reload: bool = False) -> SymbolConfig`
Get the singleton configuration instance.

**Parameters:**
- `config_path`: Path to config file (default: auto-detect)
- `reload`: Force reload of configuration (default: False)

**Raises:** `ConfigurationError` if config is invalid or missing

#### `reset_config() -> None`
Reset the singleton configuration instance. Useful for testing.

### Exception Classes

#### `ConfigurationError`
Raised when configuration is invalid or missing. Provides detailed error messages.

## Validation

### JSON Schema Validation

The configuration is validated against `symbols-config-schema.json` for:
- Required field presence
- Property types and constraints
- Pattern validation for paths
- Domain and layer structure

### Runtime Validation

The `SymbolConfig` class performs additional validation:
- File existence checks
- Path resolution
- Domain/layer availability
- Circular reference detection

### Validation Script

Use the validation script for full JSON Schema validation:

```bash
python scripts/validate_schema.py
```

## Migration Guide

### From Hardcoded Paths

**Before (hardcoded):**
```python
from pathlib import Path

SYMBOLS_DIR = Path("ai")
SYMBOL_FILES = {
    "ui": SYMBOLS_DIR / "symbols-ui.json",
    "api": SYMBOLS_DIR / "symbols-api.json",
}

ui_file = SYMBOL_FILES["ui"]
```

**After (config-driven):**
```python
from config import get_config

config = get_config()
ui_file = config.get_domain_file("ui")
```

### Benefits

1. **Project-agnostic**: Works with any project structure
2. **Centralized**: Single source of truth for all paths
3. **Validated**: Schema validation prevents errors
4. **Flexible**: Easy to add new domains/layers
5. **Type-safe**: Full type hints and IDE support

## Error Handling

The configuration system provides clear error messages:

```python
from config import get_config, ConfigurationError

try:
    config = get_config()
    file = config.get_domain_file("nonexistent")
except ConfigurationError as e:
    print(f"Error: {e}")
    # Error: Domain 'nonexistent' not found in configuration.
    # Available domains: ui, web, api, shared
```

## Testing

Run the configuration tests:

```bash
# Basic configuration loading
python scripts/config.py

# Comprehensive examples
python scripts/config_example.py
```

## Project-Specific Configuration

### For MeatyPrompts

The current configuration supports:

**Domains:**
- `ui`: UI primitives from packages/ui (755 symbols)
- `web`: Next.js web application (1,088 symbols)
- `api`: Unified backend API (3,041 symbols)
- `shared`: Shared utilities (currently mapped to web)

**API Layers:**
- `routers`: API route handlers (241KB)
- `services`: Business logic services (284KB)
- `repositories`: Data access layer (278KB)
- `schemas`: DTOs and validation (259KB)
- `cores`: Core utilities and foundations (703KB)

**Extraction:**
- Python: `services/api` with `.py` files
- TypeScript: `apps/web`, `apps/mobile`, `packages/ui`, `packages/tokens` with `.ts`, `.tsx`, `.js`, `.jsx` files

### For Other Projects

To adapt this configuration for a different project:

1. Copy `symbols.config.json` to your project
2. Update `projectName` and `symbolsDir`
3. Configure your domains in the `domains` section
4. Update extraction paths in the `extraction` section
5. Optionally configure API layers if you have a large backend
6. Validate with `scripts/validate_schema.py`

## Next Steps

This configuration system is part of the symbols skill project-agnostic refactor:

- **Task 1** (Complete): Configuration system
- **Task 2** (Next): Update `symbol_tools.py` to use config
- **Task 3**: Update extraction scripts to use config
- **Task 4**: Update documentation
- **Task 5**: Create example for other projects

See the implementation plan for details.
