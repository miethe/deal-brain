# Symbols Initialization Wizard

Interactive CLI wizard for creating symbols configuration for your project.

## Quick Start

```bash
# Interactive mode (recommended for first-time setup)
python .claude/skills/symbols/scripts/init_symbols.py

# Quick setup with defaults
python .claude/skills/symbols/scripts/init_symbols.py --quick

# List available templates
python .claude/skills/symbols/scripts/init_symbols.py --list
```

## Features

- **Interactive CLI** - User-friendly prompts with validation
- **5 Project Templates** - Pre-configured for common tech stacks
- **Customizable** - Adjust domains, layers, and extraction paths
- **Schema Validation** - Ensures configuration correctness
- **Color Output** - Enhanced UX with colorama (optional)
- **Non-Interactive Mode** - Automation-friendly CLI arguments

## Available Templates

### 1. React + TypeScript Fullstack
**File:** `react-typescript-fullstack.json`

Full-stack monorepo with React frontend and FastAPI backend.

**Frameworks:** React, Next.js, FastAPI, SQLAlchemy
**Best for:** Full-stack applications with Python backend

**Domains:**
- `ui` - React component library
- `web` - Next.js application
- `api` - FastAPI backend (with layers)
- `shared` - Shared utilities and types

**API Layers:**
- `routers` - FastAPI endpoints
- `services` - Business logic
- `repositories` - Data access
- `schemas` - Pydantic models
- `cores` - Core utilities

---

### 2. Next.js Monorepo
**File:** `nextjs-monorepo.json`

Next.js monorepo with App Router and shared packages.

**Frameworks:** Next.js 14+, React, Tailwind, Turborepo
**Best for:** Next.js applications with multiple apps

**Domains:**
- `web` - Next.js App Router application
- `ui` - Shared UI components
- `api` - API routes and handlers
- `shared` - Utilities and types

---

### 3. Python FastAPI
**File:** `python-fastapi.json`

FastAPI backend with layered architecture.

**Frameworks:** FastAPI, SQLAlchemy, Pydantic, Alembic
**Best for:** Python API services

**Domains:**
- `api` - Main FastAPI application (with layers)
- `shared` - Shared utilities

**API Layers:**
- `routers` - Route handlers
- `services` - Business logic
- `repositories` - Data access
- `schemas` - Pydantic schemas
- `models` - SQLAlchemy models
- `cores` - Core infrastructure

---

### 4. Python Django
**File:** `python-django.json`

Django web framework with MVT architecture.

**Frameworks:** Django, Django REST Framework
**Best for:** Django applications

**Domains:**
- `web` - Django application
- `api` - Django REST Framework APIs
- `shared` - Shared utilities

---

### 5. Vue + TypeScript
**File:** `vue-typescript.json`

Vue 3 application with TypeScript and modern tooling.

**Frameworks:** Vue 3, Composition API, Pinia, Vite
**Best for:** Vue applications with TypeScript

**Domains:**
- `web` - Vue application
- `components` - Vue components
- `stores` - Pinia stores
- `shared` - Utilities and types

---

## Usage Modes

### Interactive Mode (Recommended)

Step-by-step wizard with prompts and validation.

```bash
python .claude/skills/symbols/scripts/init_symbols.py
```

**Steps:**
1. Welcome screen with benefits explanation
2. Template selection (choose from 5 templates)
3. Project customization (name, symbols directory)
4. Configuration preview
5. Confirmation and file creation
6. Next steps guidance

---

### Quick Mode

Fast setup with defaults and minimal prompts.

```bash
# Use default template (React + TypeScript Fullstack)
python .claude/skills/symbols/scripts/init_symbols.py --quick

# Specify template
python .claude/skills/symbols/scripts/init_symbols.py \
  --quick \
  --template=python-fastapi
```

**Defaults:**
- Template: `react-typescript-fullstack`
- Symbols directory: `ai`
- Project name: Detected from git/directory

---

### Non-Interactive Mode

Fully automated with CLI arguments (for scripts/CI).

```bash
python .claude/skills/symbols/scripts/init_symbols.py \
  --template=react-typescript-fullstack \
  --name="MyProject" \
  --symbols-dir="ai" \
  --output=".claude/skills/symbols/symbols.config.json" \
  --force
```

**Required arguments:**
- `--template` - Template to use
- `--name` - Project name
- `--symbols-dir` - Symbols directory

**Optional arguments:**
- `--output` - Output path (default: auto-detect)
- `--force` - Overwrite existing configuration

---

### Dry Run Mode

Preview configuration without writing files.

```bash
python .claude/skills/symbols/scripts/init_symbols.py \
  --template=python-fastapi \
  --name="TestProject" \
  --symbols-dir="symbols" \
  --dry-run
```

**Output:**
- Step-by-step preview
- Full configuration JSON
- No file modifications

---

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--help` | Show help message | - |
| `--list` | List available templates | - |
| `--template` | Project template to use | Interactive prompt |
| `--name` | Project name | Auto-detect from git/directory |
| `--symbols-dir` | Symbols directory | `ai` |
| `--output` | Output path for config file | Auto-detect |
| `--force` | Overwrite existing config | `false` |
| `--dry-run` | Preview without writing | `false` |
| `--quick` | Quick setup with defaults | `false` |

---

## Configuration Output

### Default Location

The wizard writes configuration to:

```
<project-root>/.claude/skills/symbols/symbols.config.json
```

### Custom Location

Specify custom output path:

```bash
python .claude/skills/symbols/scripts/init_symbols.py \
  --output=/custom/path/symbols.config.json
```

---

## Validation

### Schema Validation

Configuration is automatically validated against `symbols-config-schema.json`.

**Requirements:**
- Install `jsonschema`: `pip install jsonschema`
- Schema file must exist in `.claude/skills/symbols/`

**Validation checks:**
- Required fields present
- Domain structure valid
- Extraction configuration complete
- File naming conventions followed

### Project Name Validation

Project names must match: `^[a-zA-Z0-9_-]+$`

- ✓ Valid: `MyProject`, `my-project`, `my_project123`
- ✗ Invalid: `my project`, `my/project`, `my.project`

### Directory Validation

Directories must not have leading/trailing slashes.

- ✓ Valid: `ai`, `symbols`, `.symbols`
- ✗ Invalid: `/ai`, `symbols/`, `/ai/`

---

## Examples

### Example 1: First-time setup (Interactive)

```bash
$ python .claude/skills/symbols/scripts/init_symbols.py

================================================================================
                   Symbols Skill Configuration Wizard
================================================================================

Welcome to the Symbols Configuration Wizard!

This wizard will help you set up symbol extraction for your project.

What are symbols?
  • Pre-generated metadata about your codebase
  • Enable token-efficient code navigation
  • 95-99% token reduction

Would you like to continue? [Y/n]: y

Step 1: Template Selection

Available templates:

1. React + TypeScript Fullstack
   React + TypeScript monorepo with FastAPI backend
   Frameworks: React, Next.js, FastAPI, SQLAlchemy

2. Next.js Monorepo
   ...

Select a template (1-5) [1]: 1
✓ Selected: React + TypeScript Fullstack

Step 2: Project Customization

ℹ Detected project name from git/directory: meatyprompts
Project name [meatyprompts]: MyProject

ℹ The symbols directory will store all symbol files
Symbols directory [ai]: ai

✓ Project: MyProject
✓ Symbols directory: ai

Step 3: Configuration Preview

Project Configuration:
  Project Name: MyProject
  Symbols Directory: ai

Domains:
  ✓ ui: symbols-ui.json
  ✓ web: symbols-web.json
  ...

Proceed with this configuration? [Y/n]: y

Step 4: Writing Configuration
✓ Configuration validated against schema
✓ Configuration written to: .claude/skills/symbols/symbols.config.json

--------------------------------------------------------------------------------
                                 Next Steps
--------------------------------------------------------------------------------

1. Generate Symbols:
   python .claude/skills/symbols/scripts/extract_symbols_typescript.py
   python .claude/skills/symbols/scripts/extract_symbols_python.py
   ...
```

---

### Example 2: Quick setup with Python FastAPI

```bash
$ python .claude/skills/symbols/scripts/init_symbols.py \
    --quick \
    --template=python-fastapi \
    --name="MyAPI"

Step 1: Template Selection
✓ Using template: Python FastAPI

Step 2: Project Customization
✓ Project: MyAPI
✓ Symbols directory: ai

Step 4: Writing Configuration
✓ Configuration validated against schema
✓ Configuration written to: .claude/skills/symbols/symbols.config.json

Next Steps:
1. Generate Symbols:
   python .claude/skills/symbols/scripts/extract_symbols_python.py
...
```

---

### Example 3: CI/CD automation

```bash
#!/bin/bash
# setup-symbols.sh - Automated symbols setup for CI

python .claude/skills/symbols/scripts/init_symbols.py \
  --template=react-typescript-fullstack \
  --name="${PROJECT_NAME}" \
  --symbols-dir="ai" \
  --output=".claude/skills/symbols/symbols.config.json" \
  --force

# Generate symbols
python .claude/skills/symbols/scripts/extract_symbols_typescript.py
python .claude/skills/symbols/scripts/extract_symbols_python.py

# Validate
python .claude/skills/symbols/scripts/validate_symbols.py
```

---

### Example 4: Preview before committing

```bash
$ python .claude/skills/symbols/scripts/init_symbols.py \
    --template=nextjs-monorepo \
    --name="MyMonorepo" \
    --symbols-dir="ai" \
    --dry-run

Step 1: Template Selection
✓ Using template: Next.js Monorepo

...

Step 4: Dry Run
✓ Configuration validated against schema

ℹ Dry run mode - configuration not written

Configuration preview:
{
  "$schema": "../symbols-config-schema.json",
  "projectName": "MyMonorepo",
  "symbolsDir": "ai",
  ...
}
```

---

## Next Steps After Setup

### 1. Generate Symbols

**TypeScript/JavaScript:**
```bash
python .claude/skills/symbols/scripts/extract_symbols_typescript.py
```

**Python:**
```bash
python .claude/skills/symbols/scripts/extract_symbols_python.py
```

### 2. Validate Symbols

```bash
python .claude/skills/symbols/scripts/validate_symbols.py
```

### 3. Query Symbols

```bash
python .claude/skills/symbols/scripts/symbol_tools.py
```

### 4. Read Documentation

- **Configuration Guide:** `.claude/skills/symbols/CONFIG_README.md`
- **Best Practices:** `/docs/development/symbols-best-practices.md`
- **API Reference:** `.claude/skills/symbols/scripts/config.py`

---

## Troubleshooting

### Configuration File Exists

**Error:**
```
⚠ Configuration file already exists: symbols.config.json
Overwrite existing configuration? [y/N]:
```

**Solutions:**
- Answer `y` to overwrite
- Use `--force` to skip prompt: `--force`
- Use different output path: `--output=/path/to/config.json`

---

### Schema Validation Failed

**Error:**
```
✗ Configuration validation failed: Schema validation failed: ...
```

**Solutions:**
1. Install jsonschema: `pip install jsonschema`
2. Check schema file exists: `.claude/skills/symbols/symbols-config-schema.json`
3. Review error message for specific field issues

---

### Invalid Project Name

**Error:**
```
✗ Invalid project name. Use only letters, numbers, hyphens, and underscores.
```

**Solutions:**
- Use alphanumeric characters: `a-z A-Z 0-9`
- Use hyphens or underscores: `-` `_`
- Avoid spaces and special characters

---

### Template Not Found

**Error:**
```
✗ Template file not found: .claude/skills/symbols/templates/...
```

**Solutions:**
1. Verify templates directory exists: `.claude/skills/symbols/templates/`
2. Check template files are present (5 templates)
3. Re-clone repository if files are missing

---

## Testing

Run the comprehensive test suite:

```bash
python .claude/skills/symbols/scripts/test_init_symbols.py
```

**Tests:**
1. Help output
2. List templates
3. Dry run with Python FastAPI
4. Quick mode with React template
5. Force overwrite with Next.js
6. Vue TypeScript template
7. Django template

**Expected output:**
```
Total tests: 7
Passed: 7
Failed: 0

✓ All tests passed!
```

---

## Advanced Usage

### Custom Template

Create a custom template in `.claude/skills/symbols/templates/`:

```json
{
  "$schema": "../symbols-config-schema.json",
  "projectName": "{{PROJECT_NAME}}",
  "symbolsDir": "{{SYMBOLS_DIR}}",
  "domains": { ... },
  "extraction": { ... }
}
```

Add to `TEMPLATES` dict in `init_symbols.py`:

```python
TEMPLATES = {
    "my-custom-template": {
        "name": "My Custom Template",
        "description": "Custom project setup",
        "file": "my-custom-template.json",
        "frameworks": "...",
        "best_for": "...",
    },
}
```

---

### Environment Variables

Set defaults via environment:

```bash
export SYMBOLS_PROJECT_NAME="MyProject"
export SYMBOLS_DIR="ai"
export SYMBOLS_TEMPLATE="react-typescript-fullstack"

python .claude/skills/symbols/scripts/init_symbols.py --quick
```

---

### Integration with Setup Scripts

```bash
# setup.sh - Project initialization script

# Install dependencies
npm install
pip install -r requirements.txt

# Initialize symbols
python .claude/skills/symbols/scripts/init_symbols.py \
  --quick \
  --template=react-typescript-fullstack \
  --force

# Generate initial symbols
python .claude/skills/symbols/scripts/extract_symbols_typescript.py
python .claude/skills/symbols/scripts/extract_symbols_python.py

echo "✓ Project setup complete!"
```

---

## Resources

- **Configuration Schema:** `.claude/skills/symbols/symbols-config-schema.json`
- **Templates Directory:** `.claude/skills/symbols/templates/`
- **Config Loader:** `.claude/skills/symbols/scripts/config.py`
- **Validation Script:** `.claude/skills/symbols/scripts/validate_schema.py`
- **Symbol Tools:** `.claude/skills/symbols/scripts/symbol_tools.py`

---

## Support

For issues or questions:

1. Check documentation: `.claude/skills/symbols/CONFIG_README.md`
2. Review templates: `--list`
3. Test with dry run: `--dry-run`
4. Run test suite: `test_init_symbols.py`
5. Read best practices: `/docs/development/symbols-best-practices.md`
