# Symbols Skill - Documentation Index

Welcome to the symbols skill documentation hub. This directory contains detailed guides for working with symbol files, validation, and symbol-based codebase exploration.

## Documentation Organization

### Validation Documentation

**[validation-guide.md](./validation-guide.md)** — Complete validation documentation
Comprehensive guide to symbol file validation including:
- File existence and readability checks
- Schema validation (required fields, data types)
- Freshness checks (stale file detection)
- Duplicate detection and source integrity
- CLI commands and programmatic API
- Exit codes and error interpretation
- JSON output format for CI/CD integration

**[validation-quick-ref.md](./validation-quick-ref.md)** — Quick reference card
Fast lookup guide for symbol validation including:
- Common CLI commands
- Programmatic API snippets
- Exit codes at a glance
- Troubleshooting quick tips

### Related Documentation (Parent Directory)

**[../CONFIG_README.md](../CONFIG_README.md)** — Configuration system guide
How to configure symbol generation, domains, and exclusion patterns.

**[../scripts/INIT_README.md](../scripts/INIT_README.md)** — Initialization wizard guide
Using the automated setup wizard to generate initial symbol files.

**[../references/architecture_integration.md](../references/architecture_integration.md)** — Architecture patterns
Symbol system architecture and integration with the codebase.

**[../references/usage_patterns.md](../references/usage_patterns.md)** — Usage examples
Practical examples and patterns for using symbols in your workflow.

**[../SKILL.md](../SKILL.md)** — Skill overview
Complete skill documentation and capabilities.

## Quick Navigation by Goal

| Goal | Document |
|------|----------|
| I want to validate my symbols | [validation-guide.md](./validation-guide.md) |
| I need quick validation commands | [validation-quick-ref.md](./validation-quick-ref.md) |
| I'm fixing validation errors | [validation-guide.md](./validation-guide.md#understanding-errors) (see error reference) |
| I want to configure symbols | [../CONFIG_README.md](../CONFIG_README.md) |
| I want to set up symbols from scratch | [../scripts/INIT_README.md](../scripts/INIT_README.md) |
| I want to understand symbol architecture | [../references/architecture_integration.md](../references/architecture_integration.md) |
| I want to see symbol usage examples | [../references/usage_patterns.md](../references/usage_patterns.md) |

## Common Tasks

### Validate Symbol Files

```bash
# Validate all domains
python .claude/skills/symbols/scripts/validate_symbols.py

# Validate specific domain (ui, web, api, shared)
python .claude/skills/symbols/scripts/validate_symbols.py --domain=api

# Verbose output with progress
python .claude/skills/symbols/scripts/validate_symbols.py --verbose

# JSON output for CI/CD
python .claude/skills/symbols/scripts/validate_symbols.py --json
```

For detailed information, see [validation-guide.md](./validation-guide.md).

### Understand Validation Errors

1. Review the error output from the validation script
2. Cross-reference error code with [validation-guide.md](./validation-guide.md#error-codes)
3. Apply the suggested fix
4. Re-run validation to confirm

### Configure Symbol Generation

See [../CONFIG_README.md](../CONFIG_README.md) for:
- Adding new domains
- Configuring exclusion patterns
- Adjusting freshness thresholds
- Custom output paths

## Adding New Documentation

When creating new documentation for the symbols skill:

1. **Placement**: Store in this directory (`docs/`) for skill-specific guides
2. **Naming**: Use descriptive names with hyphens (e.g., `my-feature-guide.md`)
3. **Structure**: Follow standard markdown with clear sections and headers
4. **Links**: Use relative paths (e.g., `./validation-guide.md` for same directory)
5. **Index Update**: Add entry to this README with brief description

### Documentation Categories

- **guides/**: Comprehensive how-to documentation (>300 lines)
- **quick-ref/**: Quick reference cards and cheat sheets
- **api/**: API reference documentation
- **troubleshooting/**: Problem diagnosis and solutions

## Navigation Tips

- Use the **Quick Navigation by Goal** table to find what you need
- Check **Related Documentation** for context beyond validation
- See **Common Tasks** for immediate solution examples
- Each document has a table of contents for quick scanning

## Need Help?

- **Validation problems?** → [validation-guide.md](./validation-guide.md)
- **Configuration questions?** → [../CONFIG_README.md](../CONFIG_README.md)
- **General overview?** → [../SKILL.md](../SKILL.md)
- **Architecture details?** → [../references/architecture_integration.md](../references/architecture_integration.md)
