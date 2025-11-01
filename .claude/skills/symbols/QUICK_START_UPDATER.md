# Quick Start: CLAUDE.md Updater

## One-Time Setup

If your CLAUDE.md already has symbols content, add markers:

```markdown
<!-- BEGIN SYMBOLS SECTION -->
## Agent Delegation Strategy

### Before Implementing: Explore First
...your existing symbols content...

<!-- END SYMBOLS SECTION -->
```

Place the `BEGIN` marker before your symbols section and `END` marker after it.

## Basic Usage

### Preview Changes (Recommended First)
```bash
python .claude/skills/symbols/scripts/update_claude_md.py --dry-run --verbose
```

### Apply Update
```bash
python .claude/skills/symbols/scripts/update_claude_md.py
```

### Common Scenarios

**Scenario 1: First Time Setup (No Symbols Content)**
```bash
# Script will auto-insert symbols section
python .claude/skills/symbols/scripts/update_claude_md.py

# ✓ Inserted: 'Agent Delegation Strategy' section
# ✓ Created backup: CLAUDE.md.bak
```

**Scenario 2: Update Existing Symbols Content (With Markers)**
```bash
# Script will replace content between markers
python .claude/skills/symbols/scripts/update_claude_md.py

# ✓ Updated: 'Agent Delegation Strategy' section
# ✓ Updated: 'Symbol Files' section
# ✓ Preserved: All other content
```

**Scenario 3: Symbols Content Exists But No Markers**
```bash
# Add markers manually (see "One-Time Setup" above)
# Then run:
python .claude/skills/symbols/scripts/update_claude_md.py
```

## After Symbol Extraction

Update CLAUDE.md with fresh symbol counts:

```bash
# 1. Extract symbols
python .claude/skills/symbols/scripts/extract_symbols_python.py
python .claude/skills/symbols/scripts/extract_symbols_typescript.py

# 2. Update CLAUDE.md
python .claude/skills/symbols/scripts/update_claude_md.py

# 3. Commit together
git add ai/*.json CLAUDE.md
git commit -m "chore: update symbols and documentation"
```

## Testing

Run the test suite:

```bash
cd .claude/skills/symbols/scripts
python test_update_claude_md.py

# Expected: 14/14 tests passing
```

## Troubleshooting

**"Configuration file not found"**
→ Ensure `.claude/skills/symbols/symbols.config.json` exists

**"Template file not found"**
→ Ensure `.claude/skills/symbols/templates/claude_md_integration.md` exists

**"Symbols guidance exists but no markers found"**
→ Add markers manually (see "One-Time Setup")

**"Could not find suitable insertion point"**
→ Add markers manually or use `--force`

## Full Documentation

See `README_UPDATE_CLAUDE_MD.md` for complete documentation.
