# Template Index

Quick reference for all available symbol configuration templates.

## Templates at a Glance

| Template | Framework | Type | Domains | API Layers | Size |
|----------|-----------|------|---------|------------|------|
| `react-typescript-fullstack.json` | React + FastAPI | Fullstack | 4 | 5 | 3.3KB |
| `python-fastapi.json` | FastAPI | Backend | 2 | 6 | 2.8KB |
| `nextjs-monorepo.json` | Next.js | Frontend | 4 | 0 | 2.2KB |
| `vue-typescript.json` | Vue 3 | Frontend | 3 | 0 | 2.0KB |
| `python-django.json` | Django | Backend | 2 | 6 | 2.9KB |

## Quick Selection

### I have a fullstack monorepo
→ **`react-typescript-fullstack.json`**
- React/Next.js frontend
- FastAPI backend
- Shared component library
- Monorepo structure

### I have a Python backend only
→ **`python-fastapi.json`** or **`python-django.json`**
- FastAPI: Modern async API
- Django: Traditional ORM + DRF

### I have a Next.js frontend only
→ **`nextjs-monorepo.json`**
- App Router
- Shared packages
- Server/Client components

### I have a Vue 3 frontend only
→ **`vue-typescript.json`**
- Composition API
- Pinia stores
- Vue Router

## Domain Coverage

| Domain | react-ts-fullstack | fastapi | nextjs | vue | django |
|--------|-------------------|---------|--------|-----|--------|
| ui | ✓ | - | ✓ | ✓ | - |
| web | ✓ | - | ✓ | ✓ | - |
| api | ✓ | ✓ | ✓ | - | ✓ |
| shared | ✓ | ✓ | ✓ | ✓ | ✓ |

## API Layer Coverage

| Layer | react-ts-fullstack | fastapi | nextjs | vue | django |
|-------|-------------------|---------|--------|-----|--------|
| routers | ✓ | ✓ | - | - | - |
| services | ✓ | ✓ | - | - | ✓ |
| repositories | ✓ | ✓ | - | - | - |
| schemas | ✓ | ✓ | - | - | - |
| models | - | ✓ | - | - | ✓ |
| views | - | - | - | - | ✓ |
| serializers | - | - | - | - | ✓ |
| urls | - | - | - | - | ✓ |
| cores | ✓ | ✓ | - | - | ✓ |

## Language Support

| Template | TypeScript | Python |
|----------|-----------|--------|
| `react-typescript-fullstack.json` | ✓ | ✓ |
| `python-fastapi.json` | placeholder | ✓ |
| `nextjs-monorepo.json` | ✓ | placeholder |
| `vue-typescript.json` | ✓ | placeholder |
| `python-django.json` | placeholder | ✓ |

**Note:** "placeholder" means template includes minimal config to satisfy schema, but extraction will skip if directories don't exist.

## Test Support

| Template | UI Tests | API Tests |
|----------|----------|-----------|
| `react-typescript-fullstack.json` | ✓ | ✓ |
| `python-fastapi.json` | - | ✓ |
| `nextjs-monorepo.json` | ✓ | - |
| `vue-typescript.json` | ✓ | - |
| `python-django.json` | - | ✓ |

## Documentation

- **`README.md`** - Complete usage guide with customization examples
- **`QUICK_START.md`** - 3-step quick start guide
- **`INDEX.md`** - This file (quick reference)
- **Schema**: `../symbols-config-schema.json`

## Validation

```bash
# Validate all templates
python validate_templates.py --verbose

# Validate your config
python ../scripts/validate_config.py symbols.config.json
```

## Usage Example

```bash
# 1. Copy template
cp .claude/skills/symbols/templates/react-typescript-fullstack.json symbols.config.json

# 2. Edit config (replace {{PROJECT_NAME}} and {{SYMBOLS_DIR}})
nano symbols.config.json

# 3. Validate
python .claude/skills/symbols/scripts/validate_config.py symbols.config.json

# 4. Generate symbols
python .claude/skills/symbols/scripts/extract_typescript_symbols.py
python .claude/skills/symbols/scripts/extract_python_symbols.py
```

## Template Details

### react-typescript-fullstack.json
- **Domains**: ui, web, api, shared
- **API Layers**: routers, services, repositories, schemas, cores
- **TypeScript**: apps/web, apps/mobile, packages/ui, packages/shared
- **Python**: services/api, packages/backend
- **Use Cases**: Turborepo/Nx monorepos, Next.js + FastAPI

### python-fastapi.json
- **Domains**: api, shared
- **API Layers**: routers, services, repositories, schemas, models, cores
- **Python**: app, src, api
- **Use Cases**: Microservices, REST APIs, async endpoints

### nextjs-monorepo.json
- **Domains**: web, ui, api, shared
- **TypeScript**: apps/web/app, apps/web/src, packages/ui, packages/shared
- **Use Cases**: Next.js 13+ App Router, Server Components

### vue-typescript.json
- **Domains**: ui, web, shared
- **TypeScript**: src/components, src/views, src/composables, src/stores
- **Use Cases**: Vue 3 Composition API, Pinia, Vue Router

### python-django.json
- **Domains**: api, shared
- **API Layers**: models, views, serializers, urls, services, cores
- **Python**: apps, src, api, core, common
- **Use Cases**: Django REST Framework, class-based views

## Files

```
templates/
├── react-typescript-fullstack.json   - Fullstack monorepo
├── python-fastapi.json               - FastAPI backend
├── nextjs-monorepo.json              - Next.js frontend
├── vue-typescript.json               - Vue 3 frontend
├── python-django.json                - Django backend
├── README.md                         - Complete guide
├── QUICK_START.md                    - Quick reference
├── INDEX.md                          - This file
└── validate_templates.py             - Validation script
```

## Contributing

To add a new template:
1. Create `[name].json` in this directory
2. Ensure it validates against `../symbols-config-schema.json`
3. Include descriptive comments in all domains/layers
4. Use `{{PROJECT_NAME}}` and `{{SYMBOLS_DIR}}` placeholders
5. Run `python validate_templates.py` to verify
6. Update this INDEX.md
7. Update README.md with usage example

## Support

- Main docs: `../.claude/skills/symbols/SKILL.md`
- Config guide: `../CONFIG_README.md`
- Schema: `../symbols-config-schema.json`
