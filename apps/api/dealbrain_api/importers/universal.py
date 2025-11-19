"""Universal file-based importer for seeding Deal Brain entities."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from pydantic import ValidationError

from dealbrain_core.schemas import (
    CpuCreate,
    GpuCreate,
    ListingCreate,
    PortsProfileCreate,
    ProfileCreate,
    RamSpecCreate,
    SpreadsheetSeed,
    StorageProfileCreate,
)

JSONLike = dict[str, Any] | list[Any]


@dataclass(frozen=True)
class EntityConfig:
    """Configuration describing how to map a payload into a seed list."""

    field_name: str
    factory: Callable[[dict[str, Any]], Any]
    json_fields: frozenset[str] = frozenset()


SUPPORTED_ENTITIES: dict[str, EntityConfig] = {
    "cpu": EntityConfig(
        "cpus", lambda payload: CpuCreate.model_validate(payload), frozenset({"attributes"})
    ),
    "gpu": EntityConfig(
        "gpus", lambda payload: GpuCreate.model_validate(payload), frozenset({"attributes"})
    ),
    "profile": EntityConfig(
        "profiles",
        lambda payload: ProfileCreate.model_validate(payload),
        frozenset({"weights_json", "rule_group_weights"}),
    ),
    "ports_profile": EntityConfig(
        "ports_profiles",
        lambda payload: PortsProfileCreate.model_validate(payload),
        frozenset({"attributes", "ports"}),
    ),
    "listing": EntityConfig(
        "listings",
        lambda payload: ListingCreate.model_validate(payload),
        frozenset({"attributes", "components", "other_components"}),
    ),
    "ram_spec": EntityConfig(
        "ram_specs",
        lambda payload: RamSpecCreate.model_validate(payload),
        frozenset({"attributes"}),
    ),
    "storage_profile": EntityConfig(
        "storage_profiles",
        lambda payload: StorageProfileCreate.model_validate(payload),
        frozenset({"attributes"}),
    ),
}


class ImporterError(Exception):
    """Raised when universal importer fails to parse or validate the payload."""


def load_seed_from_file(path: Path, entity: str) -> tuple[SpreadsheetSeed, int]:
    """Load entities from *path* and return a populated ``SpreadsheetSeed``.

    Parameters
    ----------
    path:
        Relative or absolute file path pointing to a ``.json`` or ``.csv`` file.
    entity:
        Entity key (``cpu``, ``gpu``, ``profile``, ``ports_profile``, ``listing``).

    Returns
    -------
    tuple[SpreadsheetSeed, int]
        Seed object populated with the imported entities and the number of
        records validated for the requested entity.
    """

    normalized = entity.lower().strip()
    if normalized not in SUPPORTED_ENTITIES:
        options = ", ".join(sorted(SUPPORTED_ENTITIES))
        raise ImporterError(f"Unsupported entity '{entity}'. Choose one of: {options}.")

    config = SUPPORTED_ENTITIES[normalized]
    records = _read_records(path, normalized)
    if not records:
        raise ImporterError(f"No records found in {path} for entity '{normalized}'.")

    validated: list[Any] = []
    errors: list[str] = []
    for index, raw_record in enumerate(records, start=1):
        processed = _normalize_payload(raw_record, config.json_fields)
        try:
            validated.append(config.factory(processed))
        except ValidationError as exc:
            errors.append(f"Row {index}: {exc}")

    if errors:
        raise ImporterError("\n".join(errors))

    seed = SpreadsheetSeed()
    getattr(seed, config.field_name).extend(validated)  # type: ignore[arg-type]
    return seed, len(validated)


def _read_records(path: Path, entity: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise ImporterError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        return _load_json(path, entity)
    if suffix == ".csv":
        return _load_csv(path)

    raise ImporterError(f"Unsupported file type '{suffix}'. Provide a JSON or CSV file.")


def _load_json(path: Path, entity: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ImporterError(f"Invalid JSON in {path}: {exc}") from exc

    if isinstance(payload, list):
        return [_ensure_object(item, index) for index, item in enumerate(payload, start=1)]

    if isinstance(payload, dict):
        # Accept either {"items": [...]} or {"<entity>": [...]} payloads.
        for key in ("items", entity):
            if key in payload:
                value = payload[key]
                if isinstance(value, list):
                    return [
                        _ensure_object(item, index) for index, item in enumerate(value, start=1)
                    ]
                raise ImporterError(
                    f"Expected array for key '{key}' in {path}, received {type(value).__name__}."
                )

    raise ImporterError(
        "JSON payload must be a list of records or contain an 'items' array matching the entity."
    )


def _load_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            return [{key: value for key, value in row.items() if key} for row in reader]
    except csv.Error as exc:
        raise ImporterError(f"Invalid CSV in {path}: {exc}") from exc


def _ensure_object(item: Any, index: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ImporterError(f"Expected object at index {index}, received {type(item).__name__}.")
    return item


def _normalize_payload(payload: dict[str, Any], json_fields: Iterable[str]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    json_field_set = {field.lower() for field in json_fields}

    for key, value in payload.items():
        if isinstance(key, str):
            normalized_key = key.strip()
        else:
            raise ImporterError("All keys must be strings.")

        if isinstance(value, str):
            value = value.strip()
            if value == "":
                value = None

        if value is not None and normalized_key.lower() in json_field_set:
            value = _parse_json_field(value, field=normalized_key)

        normalized[normalized_key] = value

    return normalized


def _parse_json_field(value: Any, *, field: str) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ImporterError(f"Field '{field}' must be valid JSON: {exc}") from exc
        return parsed
    raise ImporterError(f"Field '{field}' must be an object, array, or JSON string.")


__all__ = ["ImporterError", "SUPPORTED_ENTITIES", "load_seed_from_file"]
