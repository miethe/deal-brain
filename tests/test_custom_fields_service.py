import pytest

from apps.api.dealbrain_api.services.custom_fields import CustomFieldService


def test_normalize_key_strips_and_snake_cases():
    service = CustomFieldService()
    assert service._normalize_key("  CPU Speed (Turbo)  ") == "cpu_speed_turbo"


def test_validate_field_type_rejects_unknown():
    service = CustomFieldService()
    with pytest.raises(ValueError):
        service._validate_field_type("uuid")


def test_normalize_options_requires_enum_options():
    service = CustomFieldService()
    with pytest.raises(ValueError):
        service._normalize_options("enum", [])

    assert service._normalize_options("enum", ["A", "B"]) == ["A", "B"]
    assert service._normalize_options("string", ["A", "B"]) is None


def test_normalize_options_supports_multi_select():
    service = CustomFieldService()
    assert service._normalize_options("multi_select", ["USB-C", "HDMI"]) == ["USB-C", "HDMI"]


def test_normalize_validation_numeric_bounds():
    service = CustomFieldService()
    rules = service._normalize_validation("number", {"min": 0, "max": 100})
    assert rules == {"min": 0.0, "max": 100.0}


def test_normalize_validation_rejects_unknown_keys():
    service = CustomFieldService()
    with pytest.raises(ValueError):
        service._normalize_validation("string", {"foo": "bar"})


def test_normalize_validation_rejects_numeric_bounds_for_strings():
    service = CustomFieldService()
    with pytest.raises(ValueError):
        service._normalize_validation("string", {"min": 0})


def test_normalize_validation_allows_allowed_values():
    service = CustomFieldService()
    rules = service._normalize_validation("string", {"allowed_values": ["A", "B"]})
    assert rules == {"allowed_values": ["A", "B"]}
