"""Tests for formula reference generation script"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def reference_path():
    """Path to the formula reference JSON file."""
    return Path(__file__).parent.parent.parent / "data" / "formula_reference.json"


@pytest.fixture
def reference_data(reference_path):
    """Load the formula reference JSON."""
    if not reference_path.exists():
        pytest.skip(f"Formula reference not found at {reference_path}")

    with open(reference_path) as f:
        return json.load(f)


def test_reference_file_exists(reference_path):
    """Test that the reference file exists."""
    assert reference_path.exists(), f"Formula reference should exist at {reference_path}"


def test_reference_has_required_top_level_keys(reference_data):
    """Test that reference has all required top-level keys."""
    required_keys = {
        "version",
        "generated_at",
        "description",
        "entities",
        "custom_fields",
        "enums",
        "operators",
        "functions",
        "syntax_patterns",
        "examples",
        "notes",
    }

    assert required_keys.issubset(reference_data.keys()), \
        f"Reference missing required keys: {required_keys - set(reference_data.keys())}"


def test_entities_structure(reference_data):
    """Test entities section has correct structure."""
    entities = reference_data["entities"]

    # Should have at least core entities
    core_entities = {"listing", "cpu", "gpu", "ram_spec"}
    assert core_entities.issubset(entities.keys()), \
        f"Missing core entities: {core_entities - set(entities.keys())}"

    # Each entity should have required fields
    for entity_name, entity_data in entities.items():
        assert "description" in entity_data, f"Entity {entity_name} missing description"
        assert "access_pattern" in entity_data, f"Entity {entity_name} missing access_pattern"
        assert "nullable" in entity_data, f"Entity {entity_name} missing nullable"
        assert "fields" in entity_data, f"Entity {entity_name} missing fields"
        assert isinstance(entity_data["fields"], dict), f"Entity {entity_name} fields must be dict"

        # Each field should have required properties
        for field_name, field_data in entity_data["fields"].items():
            assert "type" in field_data, f"{entity_name}.{field_name} missing type"
            assert "description" in field_data, f"{entity_name}.{field_name} missing description"
            assert "nullable" in field_data, f"{entity_name}.{field_name} missing nullable"
            assert "example" in field_data, f"{entity_name}.{field_name} missing example"


def test_custom_fields_structure(reference_data):
    """Test custom_fields section has correct structure."""
    custom_fields = reference_data["custom_fields"]

    assert isinstance(custom_fields, dict), "custom_fields must be a dictionary"

    # Each entity's custom fields should be a list
    for entity, fields in custom_fields.items():
        assert isinstance(fields, list), f"Custom fields for {entity} must be a list"

        # Each custom field should have required properties
        for field in fields:
            assert "field_key" in field, f"Custom field missing field_key"
            assert "field_type" in field, f"Custom field missing field_type"
            assert "description" in field, f"Custom field missing description"
            assert "access_pattern" in field, f"Custom field missing access_pattern"
            assert "required" in field, f"Custom field missing required"


def test_enums_structure(reference_data):
    """Test enums section has correct structure."""
    enums = reference_data["enums"]

    # Should have core enums
    core_enums = {"Condition", "RamGeneration", "StorageMedium", "ListingStatus"}
    assert core_enums.issubset(enums.keys()), \
        f"Missing core enums: {core_enums - set(enums.keys())}"

    # Each enum should have required fields
    for enum_name, enum_data in enums.items():
        assert "description" in enum_data, f"Enum {enum_name} missing description"
        assert "values" in enum_data, f"Enum {enum_name} missing values"
        assert "usage" in enum_data, f"Enum {enum_name} missing usage"
        assert isinstance(enum_data["values"], list), f"Enum {enum_name} values must be list"
        assert len(enum_data["values"]) > 0, f"Enum {enum_name} must have at least one value"


def test_operators_structure(reference_data):
    """Test operators section has correct structure."""
    operators = reference_data["operators"]

    # Should have all operator categories
    assert "arithmetic" in operators, "Missing arithmetic operators"
    assert "comparison" in operators, "Missing comparison operators"
    assert "logical" in operators, "Missing logical operators"

    # Check specific operators
    assert "+" in operators["arithmetic"]
    assert "-" in operators["arithmetic"]
    assert "*" in operators["arithmetic"]
    assert "/" in operators["arithmetic"]

    assert "==" in operators["comparison"]
    assert "!=" in operators["comparison"]
    assert "<" in operators["comparison"]

    assert "and" in operators["logical"]
    assert "or" in operators["logical"]
    assert "not" in operators["logical"]


def test_functions_structure(reference_data):
    """Test functions section has correct structure."""
    functions = reference_data["functions"]

    # Should have core functions
    core_functions = {"abs", "min", "max", "round", "clamp", "floor", "ceil"}
    assert core_functions.issubset(functions.keys()), \
        f"Missing core functions: {core_functions - set(functions.keys())}"

    # Each function should have required fields
    for func_name, func_data in functions.items():
        assert "signature" in func_data, f"Function {func_name} missing signature"
        assert "description" in func_data, f"Function {func_name} missing description"
        assert "example" in func_data, f"Function {func_name} missing example"
        assert "returns" in func_data, f"Function {func_name} missing returns"


def test_syntax_patterns_structure(reference_data):
    """Test syntax_patterns section has correct structure."""
    patterns = reference_data["syntax_patterns"]

    # Should have core patterns
    core_patterns = {"ternary", "field_access", "arithmetic", "comparison"}
    assert core_patterns.issubset(patterns.keys()), \
        f"Missing core patterns: {core_patterns - set(patterns.keys())}"

    # Each pattern should have required fields
    for pattern_name, pattern_data in patterns.items():
        assert "syntax" in pattern_data, f"Pattern {pattern_name} missing syntax"
        assert "description" in pattern_data, f"Pattern {pattern_name} missing description"
        assert "examples" in pattern_data, f"Pattern {pattern_name} missing examples"
        assert isinstance(pattern_data["examples"], list), \
            f"Pattern {pattern_name} examples must be list"


def test_examples_structure(reference_data):
    """Test examples section has correct structure."""
    examples = reference_data["examples"]

    # Should have at least some examples
    assert len(examples) > 0, "Should have at least one example"

    # Each example should have required fields
    for example_name, example_data in examples.items():
        assert "formula" in example_data, f"Example {example_name} missing formula"
        assert "description" in example_data, f"Example {example_name} missing description"
        assert "use_case" in example_data, f"Example {example_name} missing use_case"

        # Formula should be non-empty string
        assert isinstance(example_data["formula"], str), \
            f"Example {example_name} formula must be string"
        assert len(example_data["formula"]) > 0, \
            f"Example {example_name} formula must not be empty"


def test_notes_section_exists(reference_data):
    """Test that notes section provides helpful guidance."""
    notes = reference_data["notes"]

    # Should have key guidance topics
    guidance_topics = {"null_safety", "field_access", "type_coercion", "operator_precedence"}
    assert guidance_topics.issubset(notes.keys()), \
        f"Missing guidance topics: {guidance_topics - set(notes.keys())}"

    # Each note should be non-empty
    for topic, content in notes.items():
        assert isinstance(content, str), f"Note {topic} must be string"
        assert len(content) > 0, f"Note {topic} must not be empty"


def test_listing_entity_has_key_fields(reference_data):
    """Test that listing entity has essential fields."""
    listing_fields = reference_data["entities"]["listing"]["fields"]

    essential_fields = {
        "price_usd",
        "condition",
        "ram_gb",
        "primary_storage_gb",
        "adjusted_price_usd",
    }

    assert essential_fields.issubset(listing_fields.keys()), \
        f"Listing missing essential fields: {essential_fields - set(listing_fields.keys())}"


def test_cpu_entity_has_benchmark_fields(reference_data):
    """Test that CPU entity has benchmark fields."""
    cpu_fields = reference_data["entities"]["cpu"]["fields"]

    benchmark_fields = {"cpu_mark_multi", "cpu_mark_single", "cores", "threads", "tdp_w"}

    assert benchmark_fields.issubset(cpu_fields.keys()), \
        f"CPU missing benchmark fields: {benchmark_fields - set(cpu_fields.keys())}"


def test_ram_spec_has_ddr_generation(reference_data):
    """Test that RAM spec has DDR generation field."""
    ram_spec_fields = reference_data["entities"]["ram_spec"]["fields"]

    assert "ddr_generation" in ram_spec_fields, "RAM spec must have ddr_generation field"

    ddr_field = ram_spec_fields["ddr_generation"]
    assert ddr_field["type"] == "enum", "ddr_generation must be enum type"
    assert "enum_type" in ddr_field, "ddr_generation must specify enum_type"
    assert ddr_field["enum_type"] == "RamGeneration", \
        "ddr_generation must use RamGeneration enum"


def test_storage_has_medium_field(reference_data):
    """Test that storage entities have medium field."""
    primary_storage = reference_data["entities"]["primary_storage"]["fields"]

    assert "medium" in primary_storage, "primary_storage must have medium field"

    medium_field = primary_storage["medium"]
    assert medium_field["type"] == "enum", "medium must be enum type"
    assert "enum_type" in medium_field, "medium must specify enum_type"


def test_examples_use_valid_field_references(reference_data):
    """Test that examples reference fields that exist in entities."""
    examples = reference_data["examples"]
    entities = reference_data["entities"]

    # Build set of all valid field references
    valid_fields = set()

    # Add listing fields (can be accessed directly)
    for field_name in entities["listing"]["fields"].keys():
        valid_fields.add(field_name)

    # Add related entity field references
    for entity_name, entity_data in entities.items():
        if entity_name != "listing":  # Already handled
            for field_name in entity_data["fields"].keys():
                valid_fields.add(f"{entity_name}.{field_name}")

    # Check each example (basic validation - doesn't parse formula)
    for example_name, example_data in examples.items():
        formula = example_data["formula"]

        # Should not be empty
        assert len(formula) > 0, f"Example {example_name} has empty formula"

        # Should not have obvious syntax errors
        assert formula.count("(") == formula.count(")"), \
            f"Example {example_name} has unmatched parentheses"


def test_version_is_semver(reference_data):
    """Test that version follows semantic versioning."""
    version = reference_data["version"]

    assert isinstance(version, str), "Version must be string"

    # Basic semver check (X.Y.Z format)
    parts = version.split(".")
    assert len(parts) == 3, "Version must be in X.Y.Z format"

    # Each part should be numeric
    for part in parts:
        assert part.isdigit(), f"Version part '{part}' must be numeric"
