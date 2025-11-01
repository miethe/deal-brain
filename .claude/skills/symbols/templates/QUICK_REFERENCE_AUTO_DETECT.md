# Auto-Detection Quick Reference

## Quick Start

### Easiest: Full Auto

```bash
python .claude/skills/symbols/scripts/init_symbols.py --auto-detect
```

One command, zero prompts, done!

### Safe: Preview First

```bash
python .claude/skills/symbols/scripts/init_symbols.py --auto-detect --dry-run
```

See what will be configured without writing files.

### Detailed: Verbose Mode

```bash
python .claude/skills/symbols/scripts/init_symbols.py --auto-detect --verbose
```

See detection details (package manager, monorepo type, file counts).

## Common Workflows

### Interactive with Detection (Recommended for First Time)

```bash
python .claude/skills/symbols/scripts/init_symbols.py
```

**Flow:**

1. Shows detected structure
2. You choose: use detected, customize, or load config
3. Customize project name if needed
4. Preview and confirm
5. Done!

### Fully Automated CI/CD

```bash
python .claude/skills/symbols/scripts/init_symbols.py --auto-detect --force
```

No prompts, overwrites existing config.

### Custom Configuration

```bash
python .claude/skills/symbols/scripts/init_symbols.py --config-file=my-config.json
```

Use custom paths for non-standard structures.

## What Gets Detected

| Category | Detection | Confidence Factors |
|----------|-----------|-------------------|
| **Package Manager** | pnpm, npm, yarn, bun, uv, poetry, cargo | Lock files |
| **Monorepo Type** | pnpm-workspace, turborepo, lerna, npm-workspaces | Config files |
| **Backend** | Python (FastAPI, Django), Node.js | .py files, package.json |
| **Frontend** | React, Next.js, Vue | .tsx/.vue files, framework configs |
| **Mobile** | React Native, Expo | ios/android dirs, app.json |
| **Shared** | TypeScript, Python packages | packages/* dirs with code |

## Confidence Scores

- **High** (green): 10+ files + framework config → Use with confidence
- **Medium** (yellow): 3-10 files OR config only → Review detected paths
- **Low** (red): 1-3 files, no config → Probably not main code

## Template Selection

| Your Stack | Suggested Template |
|------------|-------------------|
| Monorepo + Python backend + React frontend | `react-typescript-fullstack` |
| Next.js app (with or without monorepo) | `nextjs-monorepo` |
| Python backend only | `python-fastapi` |
| Vue frontend | `vue-typescript` |

## Troubleshooting

### "Could not auto-detect appropriate template"

**Solution 1:** Use verbose mode to see what was found

```bash
python .claude/skills/symbols/scripts/init_symbols.py --auto-detect --verbose
```

**Solution 2:** Manually select template

```bash
python .claude/skills/symbols/scripts/init_symbols.py --template=react-typescript-fullstack
```

**Solution 3:** Use custom config

```bash
python .claude/skills/symbols/scripts/init_symbols.py --config-file=custom.json
```

### "directory does not exist" warnings

**Cause:** Paths in config don't exist in your project

**Solution 1:** Fix paths in custom config file

**Solution 2:** Use auto-detection instead

**Solution 3:** Force anyway (not recommended)

```bash
python .claude/skills/symbols/scripts/init_symbols.py --config-file=custom.json --force
```

### Wrong paths detected

**Cause:** Non-standard directory structure

**Solution 1:** Use custom config file

```bash
# Create custom-paths.json with correct paths
python .claude/skills/symbols/scripts/init_symbols.py --config-file=custom-paths.json
```

**Solution 2:** Interactive customization

```bash
python .claude/skills/symbols/scripts/init_symbols.py
# Choose option 2: "Customize paths interactively"
```

## CLI Cheat Sheet

| Flag | Purpose | Example |
|------|---------|---------|
| `--auto-detect` | Full automation | `--auto-detect` |
| `--verbose` | Show detection details | `--auto-detect --verbose` |
| `--dry-run` | Preview without writing | `--dry-run` |
| `--config-file` | Load custom config | `--config-file=paths.json` |
| `--force` | Skip confirmation prompts | `--force` |
| `--template` | Override detection | `--template=python-fastapi` |
| `--list` | Show available templates | `--list` |
| `--no-interactive` | Use detection, no prompts | `--no-interactive` |

## Custom Config File Format

**Minimal example:**

```json
{
  "$schema": "../symbols-config-schema.json",
  "projectName": "MyProject",
  "symbolsDir": "ai",
  "extraction": {
    "python": {
      "directories": ["src/api"],
      "extensions": [".py"],
      "excludes": ["__pycache__", "*.pyc"]
    }
  }
}
```

See `example-custom-config.json` for complete example.

## Tips

1. **First time?** Use interactive mode: `python init_symbols.py`
2. **CI/CD?** Use full auto: `--auto-detect --force`
3. **Complex structure?** Create custom config file
4. **Not sure?** Use dry run: `--dry-run`
5. **Want details?** Add verbose: `--verbose`

## Next Steps After Configuration

```bash
# 1. Generate symbols
python .claude/skills/symbols/scripts/extract_symbols_typescript.py
python .claude/skills/symbols/scripts/extract_symbols_python.py

# 2. Validate
python .claude/skills/symbols/scripts/validate_symbols.py

# 3. Query
python .claude/skills/symbols/scripts/symbol_tools.py
```

## Links

- **Full Guide:** `AUTO_DETECTION_GUIDE.md`
- **Templates:** `.claude/skills/symbols/templates/*.json`
- **Schema:** `.claude/skills/symbols/symbols-config-schema.json`
- **Quick Start:** `QUICK_START.md`
