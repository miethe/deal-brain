from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Make the package importable when running alembic outside of Poetry/installed
# environments by adding the repository root and apps/api to sys.path. This
# mirrors what Poetry does when installing packages from the monorepo.
import sys
import os
from pathlib import Path

try:
    from dealbrain_api.db import Base
    from dealbrain_api.models import *  # noqa: F401,F403
    from dealbrain_api.settings import get_settings
except ModuleNotFoundError:
    # Compute likely project root (../../.. from this file -> repo root)
    env_path = Path(__file__).resolve()
    repo_root = env_path.parents[3]
    apps_api = repo_root / "apps" / "api"

    # Also add the packages/core folder so shared packages (dealbrain_core)
    # can be imported when running alembic from the repository root.
    packages_core = repo_root / "packages" / "core"

    # Prepend to sys.path so these take precedence over other installed packages
    sys.path.insert(0, str(packages_core))
    sys.path.insert(0, str(apps_api))
    sys.path.insert(0, str(repo_root))

    # Retry imports
    from dealbrain_api.db import Base
    from dealbrain_api.models import *  # noqa: F401,F403
    from dealbrain_api.settings import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_sync_url() -> str:
    settings = get_settings()
    if settings.sync_database_url:
        return settings.sync_database_url
    url = settings.database_url
    if url.startswith("postgresql+asyncpg"):
        return url.replace("postgresql+asyncpg", "postgresql+psycopg")
    return url


config.set_main_option("sqlalchemy.url", get_sync_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
