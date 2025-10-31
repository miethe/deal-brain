# Quick Start: Symbol Templates

Get started with symbol extraction in 3 steps:

## 1. Choose Your Template

```bash
# React + TypeScript Fullstack (monorepo with backend)
cp .claude/skills/symbols/templates/react-typescript-fullstack.json symbols.config.json

# Python FastAPI Backend (API-only)
cp .claude/skills/symbols/templates/python-fastapi.json symbols.config.json

# Next.js Monorepo (frontend-focused)
cp .claude/skills/symbols/templates/nextjs-monorepo.json symbols.config.json

# Vue 3 + TypeScript
cp .claude/skills/symbols/templates/vue-typescript.json symbols.config.json

# Django Backend
cp .claude/skills/symbols/templates/python-django.json symbols.config.json
```

## 2. Configure

Edit `symbols.config.json`:

```json
{
  "projectName": "MyAwesomeApp",        ← Replace {{PROJECT_NAME}}
  "symbolsDir": "ai",                   ← Replace {{SYMBOLS_DIR}} (e.g., "ai", "symbols")
  "domains": {
    "ui": {
      "file": "symbols-ui.json",
      "description": "...",
      "enabled": true                   ← Set to false to disable
    }
  },
  "extraction": {
    "typescript": {
      "directories": [
        "apps/web",                     ← Update to match your structure
        "packages/ui"
      ]
    }
  }
}
```

**Note:** Templates include placeholder directories for unused languages (e.g., `"backend"` for TypeScript-only projects, `"frontend"` for Python-only projects). Either:
- Remove the unused language section entirely from `symbols.config.json`, OR
- Update the directories to match your actual structure, OR
- Leave as-is (extraction scripts will skip if directories don't exist)

## 3. Generate Symbols

```bash
# Validate configuration
python .claude/skills/symbols/scripts/validate_config.py symbols.config.json

# Extract symbols
python .claude/skills/symbols/scripts/extract_typescript_symbols.py
python .claude/skills/symbols/scripts/extract_python_symbols.py
```

## Common Customizations

### Disable a Domain

```json
"domains": {
  "mobile": {
    "enabled": false
  }
}
```

### Add Custom Directories

```json
"extraction": {
  "typescript": {
    "directories": [
      "apps/web",
      "apps/admin",        ← Add new directory
      "packages/ui"
    ]
  }
}
```

### Exclude Additional Patterns

```json
"extraction": {
  "typescript": {
    "excludes": [
      "node_modules/",
      "*.test.*",
      "legacy/",           ← Add custom exclude
      "deprecated/"
    ]
  }
}
```

## Template Decision Tree

```
Do you have a backend?
├─ Yes
│  ├─ FastAPI? → react-typescript-fullstack.json or python-fastapi.json
│  └─ Django?  → python-django.json
└─ No
   ├─ Next.js? → nextjs-monorepo.json
   └─ Vue 3?   → vue-typescript.json
```

## Validation

Always validate before extracting:

```bash
python .claude/skills/symbols/templates/validate_templates.py
```

## Help

- Full guide: `README.md`
- Schema reference: `../symbols-config-schema.json`
- Configuration docs: `../CONFIG_README.md`
- Main docs: `../SKILL.md`
