# Automatic Codebase Detection Guide

The `init_symbols.py` script now includes powerful automatic codebase detection capabilities that can analyze your project structure and suggest the most appropriate configuration.

## Features

### 1. Package Manager Detection

Automatically detects your package manager:

- **pnpm** (via `pnpm-lock.yaml`)
- **npm** (via `package-lock.json`)
- **yarn** (via `yarn.lock`)
- **bun** (via `bun.lockb`)
- **uv/pip** (via `uv.lock` or `pyproject.toml`)
- **pipenv** (via `Pipfile.lock`)
- **poetry** (via `poetry.lock`)
- **cargo** (via `Cargo.lock`)

### 2. Monorepo Type Detection

Identifies monorepo structures:

- **pnpm-workspace** (via `pnpm-workspace.yaml`)
- **turborepo** (via `turbo.json`)
- **lerna** (via `lerna.json`)
- **npm-workspaces** (via `workspaces` in `package.json`)

### 3. Code Location Detection

Scans for code in common directory patterns:

**Backend (Python/Node.js):**

- `api/`, `backend/`, `server/`, `services/`
- `services/api`, `apps/api`, `packages/api`
- `src/api`, `src/server`

**Frontend (React/Next.js/Vue):**

- `web/`, `frontend/`, `client/`, `app/`
- `apps/web`, `apps/frontend`, `packages/web`
- `src/`, `src/client`

**Mobile (React Native/Expo):**

- `mobile/`, `apps/mobile`, `packages/mobile`
- `ios/`, `android/`, `react-native`

**Shared Packages:**

- `packages/ui`, `packages/shared`, `packages/common`
- `libs/shared`, `libs/common`
- `shared/`, `common/`

### 4. Framework Detection

Identifies specific frameworks:

- **Next.js** (via `next.config.js` or `next.config.mjs`)
- **Vue** (via `.vue` files)
- **React** (via `.tsx/.jsx` files)
- **Expo** (via `app.json` + `package.json`)
- **React Native** (via `ios/` + `android/` directories)

### 5. Confidence Scoring

Each detected path receives a confidence score:

- **High**: Strong indicators (10+ files, framework config present)
- **Medium**: Moderate indicators (3-10 files or framework config)
- **Low**: Weak indicators (1-3 files)

## Usage

### Interactive Mode with Auto-Detection (Recommended)

```bash
python .claude/skills/symbols/scripts/init_symbols.py
```

**Flow:**

1. Welcome screen
2. Auto-detection runs and shows results
3. You choose:
   - Use detected structure (recommended)
   - Customize paths interactively
   - Load from custom config file
4. Customize project name and symbols directory
5. Preview and confirm
6. Write configuration

### Fully Automatic Mode

```bash
python .claude/skills/symbols/scripts/init_symbols.py --auto-detect
```

Automatically detects, configures, and creates symbols config without any prompts.

### Auto-Detection with Dry Run

```bash
python .claude/skills/symbols/scripts/init_symbols.py --auto-detect --dry-run
```

See what would be configured without writing files.

### Verbose Detection

```bash
python .claude/skills/symbols/scripts/init_symbols.py --auto-detect --verbose
```

Shows detailed detection information including:

- Project root path
- Package manager found
- Monorepo type found
- Number of paths detected for each category

### Non-Interactive with Detection

```bash
python .claude/skills/symbols/scripts/init_symbols.py --no-interactive
```

Uses detected structure but still runs detection (no template prompts).

## Custom Config File Support

### Create Custom Configuration

Create a JSON file with your custom paths:

```json
{
  "$schema": "../symbols-config-schema.json",
  "projectName": "MyProject",
  "symbolsDir": "ai",
  "codeLocations": {
    "backend": {
      "language": "python",
      "paths": ["src/api", "src/core"],
      "exclude": ["src/api/tests"]
    },
    "frontend": {
      "language": "typescript",
      "paths": ["client/src", "shared/components"],
      "exclude": ["**/*.test.*"]
    }
  }
}
```

See `example-custom-config.json` for a complete example.

### Load Custom Config

```bash
python .claude/skills/symbols/scripts/init_symbols.py --config-file=paths.json
```

**Features:**

- Validates that specified paths exist
- Warns about missing directories
- Prompts to continue if issues found (use `--force` to skip)
- Dry run supported: `--config-file=paths.json --dry-run`

## Detection Examples

### Example 1: MeatyPrompts (Full Stack Monorepo)

**Detected:**

```text
Package Manager: pnpm
Monorepo: Yes (pnpm-workspace)

Backend:
  services/api - python [high confidence, 4142 files]

Frontend:
  apps/web - typescript (nextjs) [high confidence, 1130 files]

Mobile:
  apps/mobile - typescript (expo) [high confidence, 46 files]

Shared:
  packages/ui - typescript [high confidence, 1069 files]

Suggested Template: React + TypeScript Fullstack
```

**Result:** Perfectly matched template with all paths configured.

### Example 2: Python-Only Backend

**Detected:**

```text
Package Manager: uv/pip
Monorepo: No

Backend:
  api/ - python [high confidence, 250 files]

Frontend: not detected
Mobile: not detected
Shared: not detected

Suggested Template: Python FastAPI
```

**Result:** Backend-only template selected.

### Example 3: Next.js Frontend

**Detected:**

```text
Package Manager: pnpm
Monorepo: No

Backend: not detected

Frontend:
  app/ - typescript (nextjs) [high confidence, 85 files]

Mobile: not detected
Shared: not detected

Suggested Template: Next.js Monorepo
```

**Result:** Frontend-only template with Next.js optimization.

## Advanced Usage

### Combine Detection with Customization

```bash
# Detect, but customize interactively
python .claude/skills/symbols/scripts/init_symbols.py
# Choose option 2: "Customize paths interactively"
```

### Override Detection with Template

```bash
# Force specific template despite detection
python .claude/skills/symbols/scripts/init_symbols.py --template=vue-typescript
```

### Validate Existing Config

```bash
# Check if paths in config file exist
python .claude/skills/symbols/scripts/init_symbols.py --config-file=symbols.config.json --dry-run
```

## Troubleshooting

### Detection Not Finding Paths

**Problem:** Auto-detection doesn't find your code directories.

**Solutions:**

1. Use `--verbose` to see what was scanned
2. Use custom config file if paths are non-standard
3. Use interactive mode and select "Customize paths interactively"

### Wrong Template Suggested

**Problem:** Detection suggests wrong template.

**Solutions:**

1. Override with `--template=<correct-template>`
2. Use `--list` to see available templates
3. Use custom config file for full control

### Path Validation Warnings

**Problem:** "directory does not exist" warnings.

**Solutions:**

1. Check that paths in config are relative to project root
2. Verify directories exist: `ls <path>`
3. Update config file with correct paths
4. Use `--force` to ignore warnings (not recommended)

## Migration from Manual Configuration

If you previously configured symbols manually:

1. **Backup existing config:**

   ```bash
   cp .claude/skills/symbols/symbols.config.json symbols.config.json.backup
   ```

2. **Run detection:**

   ```bash
   python .claude/skills/symbols/scripts/init_symbols.py --auto-detect --dry-run
   ```

3. **Compare with existing config:**
   - Check if detected paths match your manual paths
   - Verify template selection is appropriate
   - Ensure all custom domains/layers are present

4. **Update if needed:**
   - If detection is accurate: `--auto-detect` (without `--dry-run`)
   - If manual config is better: keep existing config
   - If hybrid needed: use custom config file

## Best Practices

1. **Start with auto-detection:** Let the tool analyze your codebase first
2. **Use verbose mode initially:** Understand what's being detected
3. **Dry run before committing:** Preview configuration before writing
4. **Validate paths:** Check that detected paths are correct
5. **Customize when needed:** Use interactive mode or config file for edge cases
6. **Document custom configs:** Add comments in custom JSON files explaining choices

## CLI Reference

```text
Options:
  --auto-detect      Automatically detect and use structure (skip prompts)
  --config-file PATH Load configuration from JSON file
  --no-interactive   Use detected structure without prompting
  --verbose          Show detailed detection information
  --dry-run          Show what would be configured without creating files
  --template TMPL    Force specific template (overrides detection)
  --name NAME        Project name
  --symbols-dir DIR  Symbols directory (default: ai)
  --output PATH      Output path for configuration file
  --force            Overwrite existing configuration without prompting
  --list             List available templates and exit
```

## See Also

- `QUICK_START.md` - Quick start guide for symbols system
- `README.md` - Comprehensive symbols documentation
- `symbols-config-schema.json` - Configuration schema reference
- Template files in `templates/` directory
