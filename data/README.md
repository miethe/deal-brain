# Data Directory

This directory contains generated reference files, seed data, and import templates for the Deal Brain application.

## Files

### formula_reference.json

Comprehensive JSON schema documenting all entities, fields, operators, functions, and syntax patterns available for use in baseline rule formulas.

**Purpose:**
- AI Guidance: Token-efficient documentation for AI systems generating baseline rules
- User Documentation: Clear reference for users creating custom formulas
- Import Validation: Exact field paths and types for imported JSON

**Generation:**
```bash
poetry run python scripts/generate_formula_reference.py
```

**When to regenerate:**
- After database schema changes
- After adding/modifying custom fields
- After updating FormulaParser (new functions, operators)
- Before creating import templates or AI prompts

**Documentation:** See `docs/FORMULA_REFERENCE.md` for detailed usage guide.

**Structure:**
- `version`: Semantic version (X.Y.Z)
- `generated_at`: ISO timestamp
- `entities`: All data models and their fields
- `custom_fields`: Dynamic custom fields by entity
- `enums`: Enumeration types and values
- `operators`: Arithmetic, comparison, logical operators
- `functions`: Built-in functions (abs, min, max, clamp, etc.)
- `syntax_patterns`: Common formula patterns with examples
- `examples`: Real-world formula examples
- `notes`: Usage guidance and best practices

**Size:** ~38KB | ~1,200 lines

**Example Usage:**

Load into Python:
```python
import json

with open("data/formula_reference.json") as f:
    reference = json.load(f)

# Get all CPU fields
cpu_fields = reference["entities"]["cpu"]["fields"]

# Get all available functions
functions = reference["functions"]

# Get example formulas
examples = reference["examples"]
```

Load for AI context:
```
Use the formula reference at data/formula_reference.json to:
1. Understand available fields and their types
2. Generate valid formulas using documented operators and functions
3. Follow syntax patterns from examples
```

## Other Data Files

### passmark_cpus.csv (if present)

CPU benchmark data from PassMark for importing CPU specifications and scores.

**Import:**
```bash
poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv
```

### Sample Import Templates

Example workbooks and JSON files for importing listings, rules, and configurations.

## Maintenance

### Regenerating Reference

The formula reference should be regenerated whenever:

1. **Database Schema Changes**
   ```bash
   make migrate
   poetry run python scripts/generate_formula_reference.py
   ```

2. **Custom Field Changes**
   ```bash
   # After adding custom fields via UI or API
   poetry run python scripts/generate_formula_reference.py
   ```

3. **Formula Parser Updates**
   ```bash
   # After modifying FormulaParser or FormulaValidator
   poetry run python scripts/generate_formula_reference.py
   ```

### Verification

Run tests to verify reference integrity:
```bash
poetry run pytest tests/scripts/test_formula_reference_generation.py -v
```

### Version Management

Formula reference uses semantic versioning:

- **Patch (X.Y.Z+1)**: Documentation or description updates
- **Minor (X.Y+1.0)**: New fields, functions, or entities added
- **Major (X+1.0.0)**: Breaking changes to structure or access patterns

Update version in `scripts/generate_formula_reference.py` when making structural changes.

## Best Practices

1. **Keep reference up-to-date**: Regenerate after schema changes
2. **Version control**: Commit reference file with schema migrations
3. **Document changes**: Note significant updates in commit messages
4. **Test after generation**: Run test suite to verify integrity
5. **Reference in docs**: Link to reference in user documentation

## Related Files

- **Generation Script**: `scripts/generate_formula_reference.py`
- **Documentation**: `docs/FORMULA_REFERENCE.md`
- **Tests**: `tests/scripts/test_formula_reference_generation.py`
- **Formula Parser**: `packages/core/dealbrain_core/rules/formula.py`
- **Formula Validator**: `packages/core/dealbrain_core/rules/formula_validator.py`
