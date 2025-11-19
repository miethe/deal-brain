"""Utility helpers for the importer services."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from pandas import DataFrame


NORMALIZE_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return NORMALIZE_PATTERN.sub(" ", value.lower()).strip()


def checksum_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_dataframe_preview(dataframe: DataFrame, *, limit: int = 5) -> list[dict[str, Any]]:
    if dataframe.empty:
        return []
    preview_df = dataframe.head(limit).fillna("")
    return [
        {key: (None if value == "" else value) for key, value in row.items()}
        for row in preview_df.to_dict(orient="records")
    ]


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


__all__ = [
    "normalize_text",
    "checksum_bytes",
    "load_dataframe_preview",
    "ensure_directory",
    "dumps_json",
]
