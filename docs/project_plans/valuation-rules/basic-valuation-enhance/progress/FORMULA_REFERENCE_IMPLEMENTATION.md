# Formula Reference Implementation Summary

## Overview

A comprehensive JSON schema that documents all entities, fields, operators, functions, and syntax patterns available for use in baseline rule formulas. This reference serves as token-efficient documentation for AI systems, user documentation, and import validation.

## Implementation Date

2025-10-17

## Files Created

### 1. Generation Script
**Location:** `/mnt/containers/deal-brain/scripts/generate_formula_reference.py`
**Size:** 27KB
**Purpose:** Generates formula_reference.json from database schema and custom field definitions

**Key Features:**
- Extracts all fields from SQLAlchemy models using introspection
- Queries database for custom field definitions
- Documents enums, operators, functions, syntax patterns
- Provides real-world examples and usage notes
- Generates human-readable field descriptions
- Outputs pretty-printed JSON with semantic versioning

**Usage:**
```bash
poetry run python scripts/generate_formula_reference.py
```

**Dependencies:**
- SQLAlchemy inspection
- Async database session
- FormulaParser for function/operator lists
- Enum classes for valid values

### 2. Generated Reference
**Location:** `/mnt/containers/deal-brain/data/formula_reference.json`
**Size:** 38KB (1,172 lines)
**Format:** JSON

**Structure:**
```json
{
  "version": "1.0.0",
  "generated_at": "ISO timestamp",
  "description": "...",
  "entities": {
    "listing": { "fields": {...}, "description": "...", ... },
    "cpu": { "fields": {...}, ... },
    "gpu": { "fields": {...}, ... },
    "ram_spec": { "fields": {...}, ... },
    "primary_storage": { "fields": {...}, ... },
    "secondary_storage": { "fields": {...}, ... },
    "ports_profile": { "fields": {...}, ... }
  },
  "custom_fields": {
    "listing": [...],
    "cpu": [...],
    "gpu": [...]
  },
  "enums": {
    "Condition": {...},
    "RamGeneration": {...},
    "StorageMedium": {...},
    "ListingStatus": {...}
  },
  "operators": {
    "arithmetic": {...},
    "comparison": {...},
    "logical": {...}
  },
  "functions": {
    "abs": {...},
    "min": {...},
    "max": {...},
    "clamp": {...},
    ...
  },
  "syntax_patterns": {
    "ternary": {...},
    "field_access": {...},
    ...
  },
  "examples": {
    "basic_ram_valuation": {...},
    "cpu_performance_valuation": {...},
    ...
  },
  "notes": {
    "null_safety": "...",
    "field_access": "...",
    ...
  }
}
```

**Statistics:**
- 7 entities documented
- 94 standard fields
- 32 custom fields (from database)
- 12 built-in functions
- 10 example formulas
- 4 enum types
- 16 operators

### 3. Comprehensive Documentation
**Location:** `/mnt/containers/deal-brain/docs/FORMULA_REFERENCE.md`
**Size:** 13KB
**Purpose:** Complete user guide for formula reference

**Sections:**
- Overview and purpose
- Generating the reference
- Schema structure explanation
- Field access patterns
- Null safety guidance
- Operator precedence
- Common patterns and examples
- Best practices
- Validation process
- Limitations
- Maintenance procedures

### 4. Quick Reference Guide
**Location:** `/mnt/containers/deal-brain/docs/FORMULA_QUICK_REFERENCE.md`
**Size:** 7.6KB
**Purpose:** Concise cheat sheet for formula creation

**Sections:**
- Quick start examples
- Field access syntax
- All operators
- All functions
- Common patterns
- Entity reference table
- Enum values
- Best practices
- Common mistakes and fixes
- Testing guidance

### 5. Test Suite
**Location:** `/mnt/containers/deal-brain/tests/scripts/test_formula_reference_generation.py`
**Size:** 12KB
**Tests:** 16 comprehensive tests
**Status:** ✅ All passing

**Test Coverage:**
- File existence
- Schema structure validation
- Entity field structure
- Custom fields structure
- Enum structure
- Operators structure
- Functions structure
- Syntax patterns structure
- Examples structure
- Notes section
- Key field validation
- Enum type validation
- Semantic versioning

**Run tests:**
```bash
poetry run pytest tests/scripts/test_formula_reference_generation.py -v
```

### 6. Data Directory README
**Location:** `/mnt/containers/deal-brain/data/README.md`
**Size:** 4.1KB
**Purpose:** Documentation for data directory contents

**Covers:**
- Formula reference overview
- Generation instructions
- Maintenance procedures
- Version management
- Best practices
- Related files

### 7. Updated CLAUDE.md
**Location:** `/mnt/containers/deal-brain/CLAUDE.md`
**Changes:** Added formula reference generation to Data Seeding section

## Key Features

### 1. Comprehensive Entity Documentation
- All 7 entities with complete field information
- Field types, nullability, descriptions, examples
- Access patterns (direct vs dot notation)
- Default values where applicable
- Enum types with valid values

### 2. Dynamic Custom Fields
- Queries database for current custom field definitions
- Includes field type, description, options, defaults
- Organized by entity
- Full access pattern documentation

### 3. Operator & Function Reference
- All arithmetic operators (+, -, *, /, //, %, **)
- All comparison operators (==, !=, <, <=, >, >=)
- All logical operators (and, or, not)
- 12 built-in functions with signatures, descriptions, examples, return types

### 4. Syntax Pattern Examples
- Ternary expressions
- Field access (direct and nested)
- Nested field access (custom fields)
- Arithmetic operations
- Comparison operations
- Function calls

### 5. Real-World Examples
- Basic per-unit pricing
- Benchmark-based valuation
- Conditional penalties/bonuses
- Clamped values with bounds
- DDR generation bonuses
- Combined storage value
- Efficiency-based pricing
- Condition multipliers
- Null-safe formulas

### 6. Usage Notes
- Null safety guidance
- Field access patterns
- Type coercion behavior
- Operator precedence rules

## Usage Scenarios

### For AI Systems
```python
# Load reference into context
with open("data/formula_reference.json") as f:
    reference = json.load(f)

# Use for generating formulas
entities = reference["entities"]
functions = reference["functions"]
examples = reference["examples"]

# Generate formula based on requirements
# Validate against available fields
# Reference syntax patterns
```

### For Users Creating Formulas
1. Review available entities and fields
2. Check enum values for validity
3. Reference functions and operators
4. Follow syntax patterns from examples
5. Apply best practices (null safety, bounds checking)

### For Import Validation
1. Verify referenced fields exist
2. Validate enum values
3. Check function calls
4. Ensure operators are valid

## Maintenance

### When to Regenerate

1. **Database Schema Changes**
   - New models added
   - Fields added/removed/renamed
   - Field types changed
   ```bash
   make migrate
   poetry run python scripts/generate_formula_reference.py
   ```

2. **Custom Field Changes**
   - Custom fields added/removed via UI
   - Field types or options modified
   ```bash
   poetry run python scripts/generate_formula_reference.py
   ```

3. **Formula Parser Updates**
   - New functions added
   - New operators supported
   - Function signatures changed
   ```bash
   poetry run python scripts/generate_formula_reference.py
   poetry run pytest tests/scripts/test_formula_reference_generation.py
   ```

### Version Management

Semantic versioning (X.Y.Z):
- **Patch (X.Y.Z+1)**: Documentation updates, description improvements
- **Minor (X.Y+1.0)**: New fields, functions, entities added
- **Major (X+1.0.0)**: Breaking changes to structure or access patterns

Update version in `generate_formula_reference.py` before regenerating.

### Validation

Always run tests after regeneration:
```bash
poetry run pytest tests/scripts/test_formula_reference_generation.py -v
```

Expected: 16 tests passing

## Benefits

### For AI Systems
- **Token Efficient**: Comprehensive reference in single 38KB file
- **Structured**: JSON format easily parseable
- **Complete**: All entities, fields, operators, functions documented
- **Contextual**: Examples show real-world usage patterns

### For Users
- **Discoverable**: All available fields in one place
- **Educational**: Examples and patterns demonstrate best practices
- **Validatable**: Enum values and field types clearly documented
- **Accessible**: Both comprehensive and quick reference guides

### For Development
- **Automated**: Generated from source of truth (database schema)
- **Testable**: Comprehensive test suite ensures integrity
- **Maintainable**: Single script to regenerate after changes
- **Versioned**: Semantic versioning tracks changes over time

## Integration Points

### Existing Systems
- **FormulaParser**: Uses same function and operator definitions
- **FormulaValidator**: Validates against same field references
- **Custom Fields Service**: Queries same custom field definitions
- **SQLAlchemy Models**: Introspects same model definitions

### Future Enhancements
- API endpoint to serve reference dynamically
- Real-time validation against reference
- Formula builder UI using reference schema
- Import template generation from reference
- Auto-completion in formula editors

## Performance

### Generation Time
- Typical: 1-2 seconds
- Includes database query for custom fields
- Async database operations
- SQLAlchemy model introspection

### File Size
- 38KB JSON (1,172 lines)
- Compressed: ~8KB
- Easily loaded into memory
- Fast to parse

### Test Execution
- 16 tests run in ~0.12 seconds
- No database required for tests (reads generated file)
- Comprehensive validation coverage

## Documentation Structure

```
/mnt/containers/deal-brain/
├── data/
│   ├── formula_reference.json          # Generated reference (38KB)
│   └── README.md                        # Data directory guide (4.1KB)
├── docs/
│   ├── FORMULA_REFERENCE.md             # Comprehensive guide (13KB)
│   └── FORMULA_QUICK_REFERENCE.md       # Quick cheat sheet (7.6KB)
├── scripts/
│   └── generate_formula_reference.py    # Generation script (27KB)
├── tests/
│   └── scripts/
│       └── test_formula_reference_generation.py  # Test suite (12KB)
├── CLAUDE.md                            # Updated with generation command
└── FORMULA_REFERENCE_IMPLEMENTATION.md  # This document
```

## Dependencies

### Python Packages (already installed)
- sqlalchemy - Model introspection
- asyncpg - Async database queries
- pydantic - Type validation

### Internal Modules
- `apps.api.dealbrain_api.db` - Database session
- `apps.api.dealbrain_api.models.core` - SQLAlchemy models
- `dealbrain_core.enums` - Enum definitions
- `dealbrain_core.rules.formula` - FormulaParser

## Success Metrics

✅ **Complete**: All 7 entities documented with 94+ fields
✅ **Dynamic**: Custom fields pulled from database (32 fields)
✅ **Comprehensive**: 12 functions, 16 operators, 10 examples
✅ **Tested**: 16 tests all passing
✅ **Documented**: 20KB+ of user documentation
✅ **Automated**: Single command regeneration
✅ **Validated**: JSON structure integrity verified

## Next Steps

### Recommended Enhancements

1. **API Endpoint**
   ```python
   @router.get("/formulas/reference")
   async def get_formula_reference() -> dict:
       """Serve formula reference dynamically"""
   ```

2. **Formula Builder UI**
   - Use reference for field autocomplete
   - Validate formulas in real-time
   - Show available functions/operators

3. **Import Templates**
   - Generate baseline rule templates from reference
   - Include all documented fields and examples
   - Validate imports against reference schema

4. **Enhanced Validation**
   - Validate field references at formula creation time
   - Type-check operations against field types
   - Suggest corrections for undefined fields

5. **Version History**
   - Track reference versions over time
   - Show what changed between versions
   - Migrate formulas when structure changes

## Support

### Questions or Issues
- Review `docs/FORMULA_REFERENCE.md` for comprehensive guide
- Check `docs/FORMULA_QUICK_REFERENCE.md` for quick syntax
- Run generation script to update after schema changes
- Run tests to verify reference integrity
- Check `data/README.md` for maintenance procedures

### Related Documentation
- Formula Parser: `packages/core/dealbrain_core/rules/formula.py`
- Formula Validator: `packages/core/dealbrain_core/rules/formula_validator.py`
- Custom Fields: `apps/api/dealbrain_api/services/custom_fields.py`
- Models: `apps/api/dealbrain_api/models/core.py`

## Conclusion

The Formula Reference system provides a comprehensive, automatically-generated, well-tested, and thoroughly-documented schema for all formula capabilities in the Deal Brain system. It serves as a single source of truth for AI systems, users, and validation processes, ensuring consistency and discoverability across the platform.
