# Symbol Validation - Quick Reference

## CLI Commands

```bash
# Validate all domains
python .claude/skills/symbols/scripts/validate_symbols.py

# Validate specific domain
python .claude/skills/symbols/scripts/validate_symbols.py --domain=ui

# Verbose output
python .claude/skills/symbols/scripts/validate_symbols.py --verbose

# JSON output
python .claude/skills/symbols/scripts/validate_symbols.py --json

# Help
python .claude/skills/symbols/scripts/validate_symbols.py --help
```

## Programmatic API

```python
from symbol_tools import validate_symbols

# Validate all domains
report = validate_symbols()

# Validate specific domain
report = validate_symbols(domain="ui")

# Check status
if report['status'] == 'valid':
    print("All symbols valid!")
elif report['status'] == 'warnings':
    print(f"Found {report['summary']['total_warnings']} warnings")
else:
    print(f"Found {report['summary']['total_errors']} errors")

# Access domain details
ui_report = report['domains']['ui']
print(f"UI: {ui_report['symbols_count']} symbols, {ui_report['age_days']} days old")
```

## Exit Codes

- `0` = Valid (no errors or warnings)
- `1` = Warnings (stale files, minor issues)
- `2` = Errors (missing files, schema violations)

## Validation Checks

1. **File Existence** - Files exist and readable
2. **Schema Validity** - Required fields present and valid
3. **Freshness** - Warning at 7+ days, error at 14+ days
4. **Duplicates** - Same name+file+line detected
5. **Source Integrity** - Referenced files still exist
6. **Statistics** - Counts and metrics

## Report Structure

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
      "errors": [...],
      "warnings": [...],
      "duplicates": 0,
      "missing_sources": 0
    }
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

## Common Issues

### Invalid Layer Tag
```
Invalid layer 'other' in <file> symbol '<name>'
```
**Fix:** Update extractors to use valid layers, re-run extraction

### Invalid Kind Tag
```
Invalid kind 'async_method' in <file> symbol '<name>'
```
**Fix:** Use 'method' for async methods, re-run extraction

### Stale Files
```
Symbol file is 21 days old (threshold: 14 days)
```
**Fix:** `python scripts/extract_symbols.py`

### Missing Sources
```
Found 209 stale source references
```
**Fix:** Run extraction to update references

## CI/CD Integration

```bash
# Exit on errors (code 2)
python scripts/validate_symbols.py || exit $?

# Parse JSON in CI
python scripts/validate_symbols.py --json > report.json
ERRORS=$(cat report.json | jq '.summary.total_errors')
if [ "$ERRORS" -gt 0 ]; then
  echo "Found $ERRORS errors"
  exit 1
fi
```

## Performance

- **Speed:** ~277K symbols/sec (35ms for 9K symbols)
- **Domains:** Validates all enabled domains + API layers
- **Throughput:** Suitable for pre-commit hooks

## Documentation

Full guide: `.claude/skills/symbols/docs/validation-guide.md`
