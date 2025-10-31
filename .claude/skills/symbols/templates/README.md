# Symbols Configuration Templates

This directory contains ready-to-use configuration templates for the MeatyPrompts symbols skill. These templates cover the most common project types and provide a starting point for symbol extraction configuration.

## Available Templates

### 1. React + TypeScript Fullstack (`react-typescript-fullstack.json`)

**Best for:** Modern monorepo projects with React frontend and FastAPI backend

**Key Features:**
- Domain separation: UI components, Web app, API backend, Shared utilities
- API layer breakdown: routers, services, repositories, schemas, cores
- TypeScript extraction for frontend (React, hooks, utilities)
- Python extraction for backend (FastAPI, SQLAlchemy, Pydantic)
- Pre-configured for common patterns: Radix UI, React Query, Tailwind

**Typical Structure:**
```
apps/
  web/          → Next.js App Router
  mobile/       → React Native / Expo
packages/
  ui/           → Shared React components
  shared/       → Shared types and utilities
services/
  api/          → FastAPI backend
```

### 2. Python FastAPI Backend (`python-fastapi.json`)

**Best for:** Standalone FastAPI backend applications

**Key Features:**
- Focused on backend architecture layers
- API layers: routers, services, repositories, schemas, models, cores
- SQLAlchemy ORM models and repositories
- Pydantic schemas for validation
- Excludes Alembic migration files

**Typical Structure:**
```
app/
  routers/      → API endpoints
  services/     → Business logic
  repositories/ → Data access
  schemas/      → Pydantic models
  models/       → SQLAlchemy ORM
  core/         → Auth, middleware, config
```

### 3. Next.js Monorepo (`nextjs-monorepo.json`)

**Best for:** Next.js App Router projects with shared component libraries

**Key Features:**
- Domain separation: Web app, UI components, API routes, Shared utilities
- TypeScript extraction only
- Pre-configured for App Router structure (app/, src/, lib/, components/)
- Excludes Storybook stories and type definition files

**Typical Structure:**
```
apps/
  web/
    app/        → App Router pages and layouts
    components/ → App-specific components
    lib/        → App utilities
packages/
  ui/           → Shared component library
  shared/       → Shared hooks and utilities
```

### 4. Vue 3 + TypeScript (`vue-typescript.json`)

**Best for:** Vue 3 applications using Composition API and TypeScript

**Key Features:**
- Domain separation: UI components, Web app, Shared composables
- Extracts from .vue Single File Components
- Pre-configured for common Vue 3 patterns: Composition API, Pinia stores, Vue Router

**Typical Structure:**
```
src/
  components/   → Vue components (.vue)
  views/        → Page components
  composables/  → Composition API functions
  stores/       → Pinia stores
  router/       → Vue Router config
  types/        → TypeScript definitions
```

**Note:** TypeScript extractor captures exports from .vue files but not template/style sections.

### 5. Django Backend (`python-django.json`)

**Best for:** Django and Django REST Framework applications

**Key Features:**
- API layers: models, views, serializers, urls, services, cores
- Django ORM models and querysets
- DRF serializers and viewsets
- Excludes migration files, static, and media directories

**Typical Structure:**
```
apps/
  users/
    models.py      → Django models
    views.py       → Views/viewsets
    serializers.py → DRF serializers
    urls.py        → URL patterns
core/
  middleware/      → Custom middleware
  permissions/     → Permission classes
common/            → Shared utilities
```

## Using a Template

### Step 1: Choose Your Template

Select the template that best matches your project architecture:
- Fullstack monorepo? → `react-typescript-fullstack.json`
- FastAPI-only backend? → `python-fastapi.json`
- Next.js frontend? → `nextjs-monorepo.json`
- Vue 3 app? → `vue-typescript.json`
- Django backend? → `python-django.json`

### Step 2: Copy and Customize

1. Copy the template to your project root as `symbols.config.json`:
   ```bash
   cp .claude/skills/symbols/templates/react-typescript-fullstack.json symbols.config.json
   ```

2. Replace placeholder values:
   - `{{PROJECT_NAME}}` → Your project name (e.g., "MyAwesomeApp")
   - `{{SYMBOLS_DIR}}` → Directory for symbol files (e.g., "ai", "symbols", ".symbols")

3. Customize directories in the `extraction` section to match your project structure:
   ```json
   "extraction": {
     "typescript": {
       "directories": [
         "apps/web",      ← Update to match your structure
         "packages/ui"    ← Add/remove as needed
       ]
     }
   }
   ```

   **Note about unused languages:** Templates include placeholder directories for unused languages to satisfy schema validation (e.g., `"backend"` for TypeScript-only projects, `"frontend"` for Python-only projects). You can:
   - Remove the unused language section entirely from your config
   - Update the directories to match your actual structure
   - Leave as-is (extraction scripts will skip if directories don't exist)

4. Enable/disable domains and layers based on what you need:
   ```json
   "domains": {
     "mobile": {
       "enabled": false  ← Disable if you don't have mobile app
     }
   }
   ```

### Step 3: Validate Configuration

Run the validation script to ensure your configuration is valid:

```bash
python .claude/skills/symbols/scripts/validate_config.py symbols.config.json
```

### Step 4: Generate Symbols

Run the extraction scripts to generate your symbol files:

```bash
# Extract TypeScript symbols
python .claude/skills/symbols/scripts/extract_typescript_symbols.py

# Extract Python symbols
python .claude/skills/symbols/scripts/extract_python_symbols.py
```

## Common Customizations

### Adding a New Domain

```json
"domains": {
  "admin": {
    "file": "symbols-admin.json",
    "description": "Admin dashboard - Admin-specific components and utilities",
    "enabled": true
  }
}
```

### Adding Custom Excludes

```json
"extraction": {
  "typescript": {
    "excludes": [
      "node_modules/",
      "*.test.*",
      "legacy/",           ← Add custom exclude
      "deprecated/"        ← Add custom exclude
    ]
  }
}
```

### Disabling Test Symbol Extraction

```json
"domains": {
  "api": {
    "file": "symbols-api.json",
    "description": "Backend API",
    "testFile": "symbols-api-tests.json",  ← Remove this line
    "enabled": true
  }
}
```

Or keep the main config but disable test extraction:

```json
"extraction": {
  "python": {
    "excludeTests": true  ← Set to true to skip test files
  }
}
```

### Customizing API Layers

```json
"apiLayers": {
  "controllers": {         ← Rename layer
    "file": "symbols-api-controllers.json",
    "description": "API controllers - Your custom layer description",
    "enabled": true
  },
  "middleware": {          ← Add custom layer
    "file": "symbols-api-middleware.json",
    "description": "Middleware functions",
    "enabled": true
  }
}
```

## Template Selection Guide

| Project Type | Template | Why |
|-------------|----------|-----|
| Monorepo with React + Backend | `react-typescript-fullstack.json` | Full domain separation, both TS and Python |
| FastAPI microservice | `python-fastapi.json` | Backend-focused, layer-based organization |
| Next.js SPA/SSR | `nextjs-monorepo.json` | Frontend-focused, App Router patterns |
| Vue 3 application | `vue-typescript.json` | Vue-specific patterns, composables |
| Django REST API | `python-django.json` | Django ORM, DRF patterns |

## Validation and Testing

All templates have been validated against the schema (`symbols-config-schema.json`). You can validate your customized configuration:

```bash
# Validate configuration
python .claude/skills/symbols/scripts/validate_config.py symbols.config.json

# Test extraction (dry run)
python .claude/skills/symbols/scripts/extract_typescript_symbols.py --dry-run
python .claude/skills/symbols/scripts/extract_python_symbols.py --dry-run
```

## Best Practices

1. **Start with the closest template** - Choose the template that most closely matches your architecture
2. **Customize incrementally** - Start with basic customization, then refine as you use the system
3. **Use descriptive domain names** - Domain names should clearly indicate what they contain
4. **Match your architecture** - Configure layers to match your actual project structure
5. **Exclude intelligently** - Exclude test files, generated code, and third-party code
6. **Validate often** - Run validation after making changes to catch errors early
7. **Document customizations** - Add notes in `metadata.description` explaining your changes

## Troubleshooting

### Configuration fails validation

- Check that all required fields are present (`projectName`, `symbolsDir`, `domains`, `extraction`)
- Verify domain names match pattern: `^[a-z][a-z0-9-]*$` (lowercase, hyphens allowed)
- Ensure file names match pattern: `symbols-*.json`
- Check that directory paths don't start or end with `/`

### No symbols extracted

- Verify `directories` in `extraction` section match your actual project structure
- Check that `extensions` include the file types you want to extract
- Review `excludes` - you might be excluding too much
- Run with `--dry-run` to see what files would be processed

### Missing symbols from specific files

- Check if files are in the configured `directories`
- Verify file extensions are in the `extensions` list
- Check if files match any `excludes` patterns
- For test files, ensure `excludeTests` is set correctly

## Schema Reference

All templates conform to the JSON Schema defined in `../symbols-config-schema.json`. See that file for complete field documentation and validation rules.

## Contributing Templates

If you create a template for a common project type not covered here, consider contributing it back! Templates should:
- Cover a common, well-defined project architecture
- Include helpful descriptions for all domains and layers
- Use placeholder values for project-specific settings
- Be validated against the schema
- Include documentation of common patterns

## Support

For questions, issues, or suggestions:
- See main documentation: `../.claude/skills/symbols/SKILL.md`
- Check schema reference: `../symbols-config-schema.json`
- Review configuration guide: `../CONFIG_README.md`
