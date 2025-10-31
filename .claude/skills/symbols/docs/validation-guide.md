# Symbol Validation Guide

Comprehensive health checks for symbol files with detailed reporting and actionable error messages.

## Overview

The symbol validation system performs comprehensive checks on all symbol files:

- **File Existence & Readability**: Ensures files exist and are valid JSON
- **Schema Validation**: Checks required fields (name, kind, line, signature, summary, layer)
- **Freshness Checks**: Warns about stale files (>7 days) and errors for old files (>14 days)
- **Duplicate Detection**: Finds symbols with same name+file+line
- **Source Integrity**: Detects stale references to deleted source files
- **Layer/Kind Validation**: Ensures valid architectural layer and symbol kind values

## Quick Start

```bash
# Validate all domains
python .claude/skills/symbols/scripts/validate_symbols.py

# Validate specific domain
python .claude/skills/symbols/scripts/validate_symbols.py --domain=ui

# Verbose output (shows progress)
python .claude/skills/symbols/scripts/validate_symbols.py --verbose

# JSON output (for CI/CD integration)
python .claude/skills/symbols/scripts/validate_symbols.py --json
```

## CLI Usage

### Basic Commands

```bash
# Validate all enabled domains
python scripts/validate_symbols.py

# Validate specific domain (ui, web, api, shared)
python scripts/validate_symbols.py --domain=ui

# Verbose output with progress
python scripts/validate_symbols.py --verbose

# JSON output for programmatic consumption
python scripts/validate_symbols.py --json
```

### Exit Codes

The validation script returns specific exit codes for CI/CD integration:

- `0` = Valid (no errors or warnings)
- `1` = Warnings present (stale files, minor issues)
- `2` = Errors present (missing files, schema violations, missing sources)

### CI/CD Integration

```bash
# Fail build on errors (exit code 2)
python scripts/validate_symbols.py || exit $?

# Fail build on errors or warnings (exit code 1 or 2)
python scripts/validate_symbols.py
if [ $? -ne 0 ]; then
  echo "Symbol validation failed"
  exit 1
fi

# JSON output for parsing
REPORT=$(python scripts/validate_symbols.py --json)
ERRORS=$(echo "$REPORT" | jq '.summary.total_errors')
if [ "$ERRORS" -gt 0 ]; then
  echo "Found $ERRORS errors"
  exit 1
fi
```

## Programmatic API

Use the `validate_symbols()` function from `symbol_tools.py` for programmatic validation:

```python
from symbol_tools import validate_symbols

# Validate all domains
report = validate_symbols()
print(f"Status: {report['status']}")
print(f"Total Symbols: {report['summary']['total_symbols']}")
print(f"Errors: {report['summary']['total_errors']}")

# Validate specific domain
report = validate_symbols(domain="ui")
if report['status'] == 'valid':
    print("UI symbols are valid!")
else:
    print(f"Found issues: {report['summary']['total_errors']} errors")

# Access domain details
ui_report = report['domains']['ui']
print(f"UI Symbols: {ui_report['symbols_count']}")
print(f"Age: {ui_report['age_days']} days")
print(f"Errors: {len(ui_report['errors'])}")
print(f"Warnings: {len(ui_report['warnings'])}")
```

## Validation Report Structure

```python
{
    "status": "valid|warnings|errors",
    "domains": {
        "ui": {
            "exists": true,
            "readable": true,
            "symbols_count": 755,
            "last_modified": "2025-10-31T10:30:00",
            "age_days": 3,
            "errors": [],
            "warnings": ["Symbols 5 days old"],
            "duplicates": 0,
            "missing_sources": 0
        },
        "web": {...},
        "api": {...},
        "api-routers": {...},  # API layer files
        "api-services": {...},
        ...
    },
    "summary": {
        "total_symbols": 8888,
        "total_errors": 0,
        "total_warnings": 1,
        "domains_checked": 9,
        "validation_time": "42ms"
    }
}
```

## Validation Checks

### 1. File Existence & Readability

Ensures symbol files exist and can be parsed as valid JSON.

**Errors:**
- `Symbol file not found: <path>`
- `Invalid JSON in <path>: <error>`
- `Failed to read <path>: <error>`

**Resolution:** Run symbol extraction to regenerate files.

### 2. Schema Validation

Checks that all symbols have required fields per Schema v2.0:
- `name` - Symbol name
- `kind` - Symbol type (function, class, component, hook, etc.)
- `line` - Line number in source file
- `signature` - Full signature/declaration
- `summary` - Brief description
- `layer` - Architectural layer tag

**Errors:**
- `Missing fields in <file> symbol '<name>': <fields>`
- `Invalid kind '<kind>' in <file> symbol '<name>'`
- `Invalid layer '<layer>' in <file> symbol '<name>'`
- `Invalid line number '<line>' in <file> symbol '<name>'`

**Valid Kinds:**
`function`, `class`, `method`, `component`, `hook`, `interface`, `type`, `variable`

**Valid Layers:**
- **API:** `router`, `service`, `repository`, `schema`, `model`, `core`, `auth`, `middleware`, `observability`
- **Frontend:** `component`, `hook`, `page`, `util`
- **Test:** `test`
- **Other:** `unknown`

**Resolution:** Re-run symbol extraction with updated extractors that comply with Schema v2.0.

### 3. Freshness Checks

Monitors symbol file age to ensure they stay synchronized with source code.

**Warnings:**
- `Symbol file is <days> days old (threshold: 7 days). Consider running symbol extraction.`

**Errors:**
- `Symbol file is <days> days old (threshold: 14 days). Run symbol extraction to update.`

**Resolution:** Run symbol extraction to refresh files:
```bash
python scripts/extract_symbols.py
```

### 4. Duplicate Detection

Detects symbols with identical name, file path, and line number.

**Warnings:**
- `Found <count> duplicate symbols: <examples>...`

**Common Causes:**
- Extraction bug creating duplicates
- Multiple extractors processing same file
- Malformed symbol file

**Resolution:**
1. Check extraction logs for errors
2. Delete affected symbol file
3. Re-run extraction for that domain

### 5. Source File Integrity

Verifies that source files referenced in symbols still exist.

**Warnings:**
- `Found <count> stale source references: <files>...`

**Common Causes:**
- Files moved or renamed
- Files deleted from codebase
- Outdated symbol data

**Resolution:**
1. Review if files were intentionally moved/deleted
2. Run symbol extraction to update references:
   ```bash
   python scripts/extract_symbols.py
   ```

## Common Validation Failures

### Invalid Layer Tag: "other"

**Error:**
```
Invalid layer 'other' in <file> symbol '<name>'.
Valid layers: router, service, repository, schema, component, hook, page, util, ...
```

**Cause:** Symbol extractor using legacy "other" layer instead of Schema v2.0 layers.

**Resolution:**
1. Update symbol extractors to use valid layer tags
2. Re-run extraction:
   ```bash
   python scripts/extract_symbols.py
   ```

### Invalid Kind: "async_method"

**Error:**
```
Invalid kind 'async_method' in <file> symbol '<name>'.
Valid kinds: function, class, method, component, hook, interface, type, variable
```

**Cause:** Extractor creating non-standard kind values.

**Resolution:**
1. Update extractor to use `method` for async methods
2. Re-run extraction for affected domain

### Stale Symbol Files (14+ days old)

**Error:**
```
Symbol file is 21 days old (threshold: 14 days).
Run symbol extraction to update.
```

**Cause:** Symbol files haven't been updated recently.

**Resolution:**
```bash
# Update all domains
python scripts/extract_symbols.py

# Update specific domain
python scripts/extract_symbols.py --domain=api
```

### Many Stale Source References

**Warning:**
```
Found 209 stale source references: test-setup.ts, types.ts, ...
```

**Cause:** Files have been moved, renamed, or deleted since last extraction.

**Resolution:**
1. Review if file changes were intentional
2. Update symbol files:
   ```bash
   python scripts/extract_symbols.py
   ```

## Best Practices

### 1. Regular Validation

Run validation regularly to catch issues early:

```bash
# In pre-commit hook
python scripts/validate_symbols.py
if [ $? -eq 2 ]; then
  echo "Symbol validation errors detected. Please update symbols."
  exit 1
fi

# In CI/CD pipeline
- name: Validate Symbols
  run: python scripts/validate_symbols.py --verbose
```

### 2. Update After Refactoring

After major refactoring or file moves:

```bash
# Update symbols
python scripts/extract_symbols.py

# Validate
python scripts/validate_symbols.py
```

### 3. Monitor Freshness

Set up automated reminders to update symbols weekly:

```bash
# Check if symbols need update (warnings only)
python scripts/validate_symbols.py
if [ $? -eq 1 ]; then
  echo "Symbol files are getting stale. Consider updating."
fi
```

### 4. Domain-Specific Validation

When working on specific domains, validate just that domain:

```bash
# Working on UI components
python scripts/validate_symbols.py --domain=ui --verbose

# Working on API backend
python scripts/validate_symbols.py --domain=api
```

### 5. CI/CD Integration

Add validation to your CI/CD pipeline:

```yaml
# .github/workflows/validate-symbols.yml
name: Validate Symbols
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'

      - name: Validate Symbol Files
        run: |
          python .claude/skills/symbols/scripts/validate_symbols.py --verbose
        continue-on-error: true  # Allow warnings

      - name: Check for Errors
        run: |
          python .claude/skills/symbols/scripts/validate_symbols.py --json > report.json
          ERRORS=$(cat report.json | jq '.summary.total_errors')
          if [ "$ERRORS" -gt 0 ]; then
            echo "Found $ERRORS symbol validation errors"
            exit 1
          fi
```

## Troubleshooting

### Validation Script Not Found

**Error:**
```
python: can't open file 'validate_symbols.py': [Errno 2] No such file or directory
```

**Solution:**
```bash
# Run from project root
python .claude/skills/symbols/scripts/validate_symbols.py

# Or cd to scripts directory
cd .claude/skills/symbols/scripts
python validate_symbols.py
```

### Configuration Not Found

**Error:**
```
Configuration file not found. Expected symbols.config.json at:
  - .claude/skills/symbols/symbols.config.json
```

**Solution:** Ensure `symbols.config.json` exists in the correct location.

### Import Errors

**Error:**
```
ImportError: config.py not found
```

**Solution:** Ensure `config.py` is in the same directory as `validate_symbols.py`.

### Permission Denied

**Error:**
```
PermissionError: [Errno 13] Permission denied: '<path>'
```

**Solution:**
```bash
# Make script executable
chmod +x .claude/skills/symbols/scripts/validate_symbols.py

# Or run with python
python .claude/skills/symbols/scripts/validate_symbols.py
```

## See Also

- [Symbol System Best Practices](/docs/development/symbols-best-practices.md)
- [Configuration Guide](configuration-guide.md)
- [Symbol Extraction Guide](extraction-guide.md)
- [Schema v2.0 Specification](schema-v2.0-spec.md)
