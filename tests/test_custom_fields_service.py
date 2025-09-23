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

