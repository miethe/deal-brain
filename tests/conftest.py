"""Pytest configuration for path setup."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
paths_to_add = [
    ROOT,
    ROOT / "apps",
    ROOT / "apps" / "api",
    ROOT / "packages" / "core",
]
for path in paths_to_add:
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.insert(0, str_path)
