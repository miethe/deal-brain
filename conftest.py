"""Repository-wide pytest defaults needed by modules imported during collection."""

from __future__ import annotations

import os

# Some application modules construct Settings at import time. Keep local collection
# independent of a developer's .env while allowing CI and callers to override these.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://dealbrain:dealbrain@localhost:5442/dealbrain_test",
)
os.environ.setdefault(
    "SYNC_DATABASE_URL",
    "postgresql+psycopg://dealbrain:dealbrain@localhost:5442/dealbrain_test",
)
