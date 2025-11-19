"""Drop all tables and custom enums from the app's database."""

import sys
import os
from sqlalchemy import create_engine, MetaData, text

# Usage:
#   cd /mnt/containers/deal-brain/apps/api
#   python3 -m dealbrain_api.scripts.drop_db_objects
# Or run directly if imports work

# Ensure apps/api is in sys.path for module resolution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

try:
    from dealbrain_api.settings import get_settings
except ImportError:
    # Fallback for direct script execution
    from apps.api.dealbrain_api.settings import get_settings


def drop_all_tables(engine):
    meta = MetaData()
    meta.reflect(bind=engine)
    meta.drop_all(bind=engine)
    print("All tables dropped.")


def drop_all_enums(engine):
    # Only works for PostgreSQL
    with engine.connect() as conn:
        # Use PL/pgSQL block to properly drop all enums with proper quoting
        conn.execute(
            text(
                """
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT n.nspname, t.typname
                    FROM pg_type t
                    JOIN pg_enum e ON t.oid = e.enumtypid
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE n.nspname = current_schema()
                    GROUP BY n.nspname, t.typname
                ) LOOP
                    EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.nspname) || '.' || quote_ident(r.typname) || ' CASCADE';
                END LOOP;
            END $$;
        """
            )
        )
        conn.commit()
        print("All enum types dropped.")


def main():
    settings = get_settings()
    db_url = settings.sync_database_url or settings.database_url
    if db_url.startswith("postgresql+asyncpg"):
        # Convert asyncpg URL to sync psycopg2 URL
        db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    engine = create_engine(db_url)
    print("Dropping all tables...")
    drop_all_tables(engine)
    print("Dropping all enums...")
    drop_all_enums(engine)
    print("Done.")


if __name__ == "__main__":
    main()
