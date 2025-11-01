# CLAUDE.md Symbols Integration Updater

## Overview

`update_claude_md.py` is a safe, automated script for updating CLAUDE.md files with symbols skill integration guidance. It intelligently merges new symbols documentation without overwriting existing content.

## Features

- **Safe Merging**: Uses HTML comment markers for surgical updates
- **Preserves Content**: All non-symbols content remains untouched
- **Configuration-Driven**: Reads from `symbols.config.json` for project-specific details
- **Automatic Statistics**: Includes live symbol counts from symbol files
- **Dry Run Mode**: Preview changes before applying them
- **Automatic Backups**: Creates `.bak` files before modifications
- **Smart Detection**: Identifies best insertion point if markers don't exist
- **Detailed Reporting**: Clear feedback on what changed

## Usage

### Basic Usage

```bash
# Update CLAUDE.md in current project
python update_claude_md.py
```

### Common Options

```bash
# Preview changes without modifying files
python update_claude_md.py --dry-run

# Verbose output with detailed progress
python update_claude_md.py --verbose --dry-run

# Force update even if symbols content exists (use with caution)
python update_claude_md.py --force

# Specify custom project root
python update_claude_md.py --project-root /path/to/project

# Skip backup creation
python update_claude_md.py --no-backup
```

### Exit Codes

- `0`: Success (file updated)
- `1`: Warnings (skipped update - markers recommended)
- `2`: Errors (update failed)

## How It Works

### 1. Marker-Based Updates

The script uses HTML comment markers to identify the symbols section:

```markdown
<!-- BEGIN SYMBOLS SECTION -->
## Agent Delegation Strategy
...symbols content...
<!-- END SYMBOLS SECTION -->
```

**If markers exist**: Content between markers is replaced with updated guidance.

**If markers don't exist**: Script detects best insertion point (see Insertion Strategy below).

### 2. Insertion Strategy

When markers are not present, the script looks for insertion points in this order:

1. **After "Prime directives"** section (most common)
2. **After "Key Guidance"** section (alternative)
3. **After first level-2 heading** (fallback)

If symbols content already exists without markers, the script will warn you to add markers manually or use `--force`.

### 3. Template Population

The script loads the template from `.claude/skills/symbols/templates/claude_md_integration.md` and replaces these placeholders:

- `{{PROJECT_NAME}}`: From `symbols.config.json` (`projectName`)
- `{{SYMBOLS_DIR}}`: From `symbols.config.json` (`symbolsDir`)
- `{{SYMBOL_FILES_SECTION}}`: Auto-generated list of symbol files with counts
- `{{LAYER_TAGS}}`: Auto-generated layer tag documentation

### 4. Symbol Statistics

The script automatically loads symbol counts from each domain's symbol files:

```markdown
**Domain-Specific Files (Recommended):**
- `ai/symbols-api.json` - Backend API layer - 3,041 symbols
- `ai/symbols-ui.json` - Frontend components - 755 symbols
- `ai/symbols-web.json` - Next.js app router - 1,088 symbols
```

Counts are live and update each time the script runs.

## Configuration

### Prerequisites

1. **symbols.config.json** must exist at `.claude/skills/symbols/symbols.config.json`
2. **Template file** must exist at `.claude/skills/symbols/templates/claude_md_integration.md`
3. **CLAUDE.md** must exist in project root

### Template Format

The template uses simple placeholder syntax:

```markdown
## Agent Delegation Strategy

The {{PROJECT_NAME}} symbols system provides...

### Symbol Files

{{SYMBOL_FILES_SECTION}}

**Layer tags**:
{{LAYER_TAGS}}
```

See the template file for the complete structure.

## Safety Features

### 1. Backup Creation

By default, the script creates a backup before modifying:

```bash
CLAUDE.md.bak  # Created automatically
```

Disable with `--no-backup`.

### 2. Dry Run Mode

Always test changes first:

```bash
python update_claude_md.py --dry-run --verbose
```

This shows:
- What action would be taken (insert/update/skip)
- How many lines would change
- Preview of first 50 lines

### 3. Validation Checks

The script validates:

- Marker balance (equal BEGIN/END markers)
- Markdown structure (no broken sections)
- File readability and writability
- Configuration validity

### 4. Clear Error Messages

If something goes wrong, you get actionable feedback:

```text
Error: CLAUDE.md not found at /path/to/CLAUDE.md
Error: Template file not found at .claude/skills/symbols/templates/...
Warning: Symbols guidance exists but no markers found. Add markers or use --force.
```

## Example Workflow

### Initial Setup (Add Markers)

If your CLAUDE.md already has symbols content:

1. Find the symbols section (usually "Agent Delegation Strategy")

2. Add markers manually:

   ```markdown
   <!-- BEGIN SYMBOLS SECTION -->
   ## Agent Delegation Strategy
   ...existing symbols content...
   <!-- END SYMBOLS SECTION -->
   ```

3. Run the updater:

   ```bash
   python update_claude_md.py --dry-run
   ```

### Regular Updates

Once markers are in place:

```bash
# Check what would change
python update_claude_md.py --dry-run --verbose

# Apply the update
python update_claude_md.py

# Output:
# ✓ Updated symbols section (42 lines modified)
# ✓ Created backup: CLAUDE.md.bak
# ✓ Preserved 1,192 lines of existing content
```

### Fresh Installation

For new projects without symbols content:

```bash
# Script will auto-insert after "Prime directives" or "Key Guidance"
python update_claude_md.py

# Output:
# ✓ Inserted symbols section (45 lines added)
# ✓ Created backup: CLAUDE.md.bak
```

## Integration with CI/CD

Use in pre-commit hooks or CI pipelines:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Update symbols before committing
python .claude/skills/symbols/scripts/update_claude_md.py

# Exit code 0 = success, 1 = warnings, 2 = errors
if [ $? -eq 2 ]; then
    echo "Failed to update CLAUDE.md"
    exit 1
fi
```

Or as a GitHub Action:

```yaml
- name: Update CLAUDE.md
  run: |
    python .claude/skills/symbols/scripts/update_claude_md.py
    if [ $? -eq 2 ]; then
      echo "::error::Failed to update CLAUDE.md"
      exit 1
    fi
```

## Testing

Run the test suite:

```bash
python test_update_claude_md.py
```

Tests cover:

- Template loading and population
- Marker detection
- Insertion point detection
- Safe update operations
- Edge cases and error handling

All 14 tests should pass.

## Troubleshooting

### "Configuration file not found"

Ensure `symbols.config.json` exists:

```bash
ls .claude/skills/symbols/symbols.config.json
```

### "Template file not found"

Ensure template exists:

```bash
ls .claude/skills/symbols/templates/claude_md_integration.md
```

### "Symbols guidance exists but no markers found"

**Solution 1**: Add markers manually (recommended):

```markdown
<!-- BEGIN SYMBOLS SECTION -->
...existing content...
<!-- END SYMBOLS SECTION -->
```

**Solution 2**: Use `--force` to insert anyway (may create duplicates):

```bash
python update_claude_md.py --force
```

### "Could not find suitable insertion point"

Your CLAUDE.md might not have standard sections. Add markers manually or use `--force`.

### Backup file accumulation

The script overwrites the backup each time. Clean up old backups:

```bash
rm CLAUDE.md.bak
```

## Advanced Usage

### Custom Template

Create a custom template for specific projects:

1. Copy the template:

   ```bash
   cp .claude/skills/symbols/templates/claude_md_integration.md my-template.md
   ```

2. Edit `my-template.md`

3. Update the script to use your template (edit `TEMPLATE_FILE` constant)

### Multi-Project Updates

Update multiple projects:

```bash
for project in ~/projects/*; do
    cd "$project"
    python .claude/skills/symbols/scripts/update_claude_md.py
done
```

## Best Practices

1. **Always use dry-run first**: Preview changes before applying
2. **Keep markers in place**: Once added, don't remove them
3. **Update after symbol extraction**: Run after regenerating symbols
4. **Version control backups**: Backups are temporary - use git for history
5. **Test in CI**: Catch outdated documentation early

## Files Created/Modified

- **Modified**: `CLAUDE.md` (with updated symbols section)
- **Created**: `CLAUDE.md.bak` (backup of original)

## Dependencies

### Required

- Python 3.8+
- `config.py` (symbols configuration loader)

### Optional

- `colorama` (colored terminal output)

Install optional dependencies:

```bash
pip install colorama
```

## Related Documentation

- **Symbols Configuration**: `.claude/skills/symbols/symbols.config.json`
- **Template File**: `.claude/skills/symbols/templates/claude_md_integration.md`
- **Symbols Best Practices**: `/docs/development/symbols-best-practices.md`

## License

Part of the MeatyPrompts symbols skill system.
